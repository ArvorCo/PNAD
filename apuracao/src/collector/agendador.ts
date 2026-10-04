// Agendador: fila única por (prioridade, due), até N requisições em voo, baldes de taxa,
// cadências por camada, varredura em lotes e pausa global.
import type { EventoNovo } from "../db/escrita.ts";
import type { FetchResult, Job } from "../types.ts";
import { cadenciaS, motivoPeriodico, prioridadePeriodica } from "./cadencia.ts";
import type { CtxProc, JobNovo } from "./contexto.ts";
import { evento } from "./contexto.ts";
import type { FileState } from "./estado-arquivos.ts";
import { Fila } from "./fila.ts";
import type { Limitador } from "./limitador.ts";
import { backoffMs, processar } from "./processar.ts";
import { intervaloResondagemS, isoDe } from "./relogio.ts";
import type { Relogio } from "./relogio.ts";
import { Metricas } from "./saude.ts";
import { Varredura } from "./varredura.ts";

export type Fetcher = (job: Job, fs: FileState) => Promise<FetchResult>;

export interface OpcoesAgendador {
  relogio: Relogio;
  fetcher: Fetcher;
  ctx: CtxProc;
  limitador: Limitador;
  concurrencyMin?: number;
  /** "unico" = uma passada (sweep-once): sem periódicos nem jobs derivados */
  modo?: "continuo" | "unico";
  metricas?: Metricas;
  log?: (o: Record<string, unknown>) => void;
}

interface Gancho {
  ms: number;
  ultimo: number;
  fn: (agora: number) => void;
}

export class Agendador {
  readonly fila = new Fila();
  readonly metricas: Metricas;
  readonly varredura: Varredura;
  private readonly voo = new Map<number, Promise<void>>();
  private readonly ganchos: Gancho[] = [];
  private readonly modo: "continuo" | "unico";
  private readonly minConc: number;
  private rodando = false;
  concorrencia: number;

  constructor(private readonly o: OpcoesAgendador) {
    this.modo = o.modo ?? "continuo";
    this.minConc = o.concurrencyMin ?? 8;
    this.concorrencia = o.ctx.knobs.concurrency;
    this.metricas = o.metricas ?? new Metricas();
    this.varredura = new Varredura(o.ctx, this.fila, o.relogio, (ev) => this.registrarEvento(ev));
  }

  get emVoo(): number {
    return this.voo.size;
  }

  private get ctx(): CtxProc {
    return this.o.ctx;
  }

  registrarEvento(ev: EventoNovo): void {
    this.ctx.lote.adicionar([{ k: "evento", row: ev }]);
  }

  jobDe(fs: FileState, n: Omit<JobNovo, "arquivoId">): Job {
    return { arquivoId: fs.id, chave: fs.chave, url: fs.url, prioridade: n.prioridade, due: n.due, motivo: n.motivo };
  }

  /** Enfileira T0/T1 e sondas agora; inativos de T2/T3 na re-sondagem. */
  semear(agora: number = this.o.relogio.agora()): void {
    for (const fs of this.ctx.estado.porId.values()) {
      if (cadenciaS(fs) !== null) {
        this.fila.agendar(this.jobDe(fs, { prioridade: prioridadePeriodica(fs), due: agora, motivo: motivoPeriodico(fs) }));
      } else if (!fs.ativo) {
        this.fila.agendar(this.jobDe(fs, { prioridade: "probe", due: agora + intervaloResondagemS(agora) * 1000, motivo: "probe" }));
      }
    }
  }

  /** Despacha jobs vencidos até encher a concorrência ou faltar ficha. */
  tick(): number {
    const agora = this.o.relogio.agora();
    const lim = this.o.limitador;
    if (lim.atualizar(agora)) this.concorrencia = this.ctx.knobs.concurrency;
    if (lim.pausado(agora)) return 0;
    let n = 0;
    while (this.voo.size < this.concorrencia) {
      const job = this.fila.popDue(agora);
      if (!job) break;
      const fs = this.ctx.estado.porId.get(job.arquivoId);
      if (!fs) continue;
      if (fs.emVoo) {
        this.fila.agendar({ ...job, due: agora + 1000 });
        continue;
      }
      if (fs.backoffAte !== null && fs.backoffAte > agora && job.prioridade !== "final") {
        this.fila.agendar({ ...job, due: fs.backoffAte });
        continue;
      }
      const varredura = job.prioridade === "sweep" || (job.prioridade === "probe" && (fs.tier === 2 || fs.tier === 3));
      if (!lim.tentar(varredura)) {
        this.fila.agendar(job);
        break;
      }
      fs.emVoo = true;
      const p = this.executar(job, fs, agora).finally(() => {
        fs.emVoo = false;
        this.voo.delete(fs.id);
      });
      this.voo.set(fs.id, p);
      n++;
    }
    return n;
  }

  private async executar(job: Job, fs: FileState, inicio: number): Promise<void> {
    let r: FetchResult;
    try {
      r = await this.o.fetcher(job, fs);
    } catch (err) {
      r = falhaInterna(inicio, err);
    }
    const agora = this.o.relogio.agora();
    try {
      const saida = processar(this.ctx, job, fs, r, inicio);
      this.metricas.registrar(saida.classe, agora, saida.mudou, r.bytes);
      this.metricas.registrarSkew(r.servidorDate, r.iniciadoEm, r.duracaoMs);
      if (saida.classe !== "ok" && saida.classe !== "igual" && saida.classe !== "nao_modificado" && saida.classe !== "nao_existe") {
        this.metricas.ultimoErro = { em: isoDe(agora), classe: saida.classe, chave: fs.chave, erro: r.erro };
      }
      if (this.modo === "continuo") for (const j of saida.jobs) this.agendarNovo(j);
      if (saida.pausar) this.pausar(job, fs, saida.pausar.retryAfterS, saida.classe);
      else if (saida.retryEm !== null && (this.modo === "continuo" || fs.errosSeguidos <= 3)) {
        this.fila.agendar({ ...job, due: saida.retryEm, motivo: "retry" });
      }
    } catch (err) {
      const msg = err instanceof Error ? `${err.message}\n${err.stack ?? ""}`.slice(0, 2000) : String(err);
      fs.errosSeguidos++;
      fs.backoffAte = agora + backoffMs(fs.errosSeguidos, this.ctx.aleatorio);
      this.metricas.ultimoErro = { em: isoDe(agora), classe: "interno", chave: fs.chave, erro: msg };
      this.ctx.lote.adicionar([evento(fs, isoDe(agora), "erro_interno", "error", { erro: msg })]);
      this.o.log?.({ t: "erro_interno", chave: fs.chave, erro: msg });
      if (this.modo === "continuo") this.fila.agendar({ ...job, due: fs.backoffAte, motivo: "retry" });
    }
    this.varredura.concluir(fs.id);
    if (this.modo === "continuo") {
      const cad = cadenciaS(fs);
      if (cad !== null) {
        this.fila.agendar(this.jobDe(fs, { prioridade: prioridadePeriodica(fs), due: inicio + cad * 1000, motivo: motivoPeriodico(fs) }));
      }
    }
    if (this.ctx.lote.precisaGravar()) this.ctx.lote.gravar();
  }

  private agendarNovo(j: JobNovo): void {
    const fs = this.ctx.estado.porId.get(j.arquivoId);
    if (fs) this.fila.agendar(this.jobDe(fs, j));
  }

  private pausar(job: Job, fs: FileState, retryAfterS: number | null, classe: string): void {
    const lim = this.o.limitador;
    const novo = !lim.pausado();
    const ate = lim.pausar(retryAfterS);
    if (novo) {
      this.concorrencia = Math.max(this.minConc, Math.floor(this.concorrencia / 2));
      const em = isoDe(this.o.relogio.agora());
      this.ctx.lote.adicionar([
        evento(fs, em, "pausa_global", "warn", { classe, ate: isoDe(ate), nivel: lim.nivel, concorrencia: this.concorrencia, retry_after_s: retryAfterS }),
      ]);
      this.o.log?.({ t: "pausa_global", classe, ate: isoDe(ate), concorrencia: this.concorrencia });
    }
    this.fila.agendar({ ...job, due: ate, motivo: "retry" });
  }

  /** Registra uma tarefa periódica executada no laço principal. */
  aCada(ms: number, fn: (agora: number) => void, imediato = false): void {
    this.ganchos.push({ ms, ultimo: imediato ? Number.NEGATIVE_INFINITY : this.o.relogio.agora(), fn });
  }

  /** Um passo do laço: ganchos, varredura, despacho e lote. */
  passo(): number {
    const agora = this.o.relogio.agora();
    for (const g of this.ganchos) {
      if (agora - g.ultimo >= g.ms) {
        g.ultimo = agora;
        g.fn(agora);
      }
    }
    this.varredura.verificar(agora);
    const n = this.tick();
    if (this.ctx.lote.precisaGravar(agora)) this.ctx.lote.gravar();
    return n;
  }

  async esperarVoo(): Promise<void> {
    while (this.voo.size > 0) await Promise.allSettled([...this.voo.values()]);
  }

  /** Nada na fila nem em voo (fim da passada única). */
  ocioso(): boolean {
    return this.voo.size === 0 && this.fila.tamanho === 0 && !this.varredura.ativa;
  }

  private sonoMs(): number {
    if (this.voo.size >= this.concorrencia) return 10;
    const prox = this.fila.proximoDue();
    if (prox === null) return 50;
    const espera = prox - this.o.relogio.agora();
    if (espera > 0) return Math.min(50, Math.max(2, espera));
    return Math.min(50, Math.max(2, this.o.limitador.esperaMs(true)));
  }

  async rodar(ateOcioso = false): Promise<void> {
    this.rodando = true;
    while (this.rodando) {
      this.passo();
      if (ateOcioso && this.ocioso()) break;
      await Bun.sleep(this.sonoMs());
    }
    this.rodando = false;
  }

  /** Para de despachar, espera até `timeoutMs` pelos jobs em voo e grava o lote. */
  async parar(timeoutMs = 10_000): Promise<void> {
    this.rodando = false;
    await Promise.race([this.esperarVoo(), Bun.sleep(timeoutMs)]);
    this.ctx.lote.gravar();
  }

  resumoSweep(): unknown {
    return this.varredura.resumo();
  }
}

function falhaInterna(inicio: number, err: unknown): FetchResult {
  return {
    classe: "erro_rede", iniciadoEm: isoDe(inicio), duracaoMs: 0, condicional: false, httpStatus: null, etag: null,
    lastModified: null, servidorDate: null, cacheHdr: null, age: null, retryAfterS: null, bytes: 0, body: null,
    bodySha256: null, erro: err instanceof Error ? err.message : String(err),
  };
}
