// Varredura completa de T2+T3 (a cada APURACAO_SWEEP_MIN), enfileirada em lotes de 500
// com prioridade sweep, pulando o que foi lido há menos de 300 s.
import { INTERVALOS_S } from "../config.ts";
import type { EventoNovo } from "../db/escrita.ts";
import type { Tier } from "../types.ts";
import type { CtxProc } from "./contexto.ts";
import type { Fila } from "./fila.ts";
import { isoDe } from "./relogio.ts";
import type { Relogio } from "./relogio.ts";

export const LOTE_VARREDURA = 500;

export interface OpcoesVarredura {
  tiers: readonly Tier[];
  /** 0 = não pula nada */
  pularRecentesS: number;
  /** inclui arquivos inativos (passada única) */
  incluirInativos: boolean;
}

export class Varredura {
  ativa = false;
  private ids: number[] = [];
  private cursor = 0;
  private readonly pendentes = new Set<number>();
  private inicio = 0;
  private pulados = 0;
  private enfileirados = 0;
  private concluidos = 0;
  private n = 0;
  private proximaEm: number;
  private opts: OpcoesVarredura = { tiers: [2, 3], pularRecentesS: INTERVALOS_S.sweepPularRecentes, incluirInativos: false };
  /** desliga o disparo periódico (passada única controla na mão) */
  automatica = true;

  constructor(
    private readonly ctx: CtxProc,
    private readonly fila: Fila,
    private readonly relogio: Relogio,
    private readonly emitir: (ev: EventoNovo) => void,
  ) {
    this.proximaEm = relogio.agora();
  }

  iniciar(agora: number, opts: Partial<OpcoesVarredura> = {}): void {
    this.opts = { ...this.opts, ...opts };
    const tiers = new Set<Tier>(this.opts.tiers);
    this.ids = [];
    for (const fs of this.ctx.estado.porId.values()) if (tiers.has(fs.tier)) this.ids.push(fs.id);
    this.ids.sort((a, b) => this.ctx.estado.get(a).tier - this.ctx.estado.get(b).tier || a - b);
    this.cursor = 0;
    this.pendentes.clear();
    this.inicio = agora;
    this.pulados = 0;
    this.enfileirados = 0;
    this.concluidos = 0;
    this.n++;
    this.ativa = true;
    this.emitir({ em: isoDe(agora), tipo: "sweep_inicio", detalhe: { n: this.n, arquivos: this.ids.length, tiers: [...tiers] } });
  }

  private abastecer(agora: number): void {
    const zonasFinal = this.ctx.knobs.zonas === "final";
    let postos = 0;
    while (postos < LOTE_VARREDURA && this.cursor < this.ids.length) {
      const id = this.ids[this.cursor++] as number;
      const fs = this.ctx.estado.get(id);
      const recente = this.opts.pularRecentesS > 0 && fs.ultimoFetchEm !== null && agora - fs.ultimoFetchEm < this.opts.pularRecentesS * 1000;
      if ((!fs.ativo && !this.opts.incluirInativos) || recente || (zonasFinal && fs.key.nivel === "zona" && !this.opts.incluirInativos)) {
        this.pulados++;
        continue;
      }
      this.pendentes.add(id);
      this.fila.agendar({ arquivoId: id, chave: fs.chave, url: fs.url, prioridade: "sweep", due: agora, motivo: "sweep" });
      this.enfileirados++;
      postos++;
    }
  }

  verificar(agora: number): void {
    if (!this.ativa) {
      const min = this.ctx.knobs.sweepMin;
      if (this.automatica && min > 0 && agora >= this.proximaEm) this.iniciar(agora);
      if (!this.ativa) return;
    }
    if (this.pendentes.size < LOTE_VARREDURA / 2) this.abastecer(agora);
    if (this.cursor >= this.ids.length && this.pendentes.size === 0) {
      this.ativa = false;
      this.proximaEm = this.inicio + Math.max(1, this.ctx.knobs.sweepMin) * 60_000;
      this.emitir({
        em: isoDe(agora), tipo: "sweep_fim",
        detalhe: { n: this.n, arquivos: this.ids.length, enfileirados: this.enfileirados, pulados: this.pulados, duracao_s: Math.round((agora - this.inicio) / 1000) },
      });
    }
  }

  concluir(id: number): void {
    if (this.pendentes.delete(id)) this.concluidos++;
  }

  resumo(): unknown {
    return {
      ativa: this.ativa, n: this.n, arquivos: this.ids.length, cursor: this.cursor, enfileirados: this.enfileirados,
      concluidos: this.concluidos, pulados: this.pulados, pendentes: this.pendentes.size,
      inicio: this.n > 0 ? isoDe(this.inicio) : null, proxima: isoDe(this.proximaEm),
    };
  }
}

