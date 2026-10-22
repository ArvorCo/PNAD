// Amostra ao vivo de seções do 2º turno: aux.json → hash → BU do arquivo-urna, com balde de
// fichas próprio (teto em APURACAO_SECOES_RPS e APURACAO_SECOES_CONCORRENCIA), separado da fila
// e do balde do coletor principal, e parado enquanto o coletor principal estiver em pausa global
// por 403/429. Seções da totalização paralela entram com prioridade. Grava `secao_2t` pelo lote
// do coletor (escritor único).
import type { Database } from "bun:sqlite";
import { existsSync, mkdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { UA_PADRAO } from "../config.ts";
import { HeapIndexado } from "../collector/heap.ts";
import { classificar, retryAfterS } from "../collector/http.ts";
import { Limitador } from "../collector/limitador.ts";
import type { Relogio } from "../collector/relogio.ts";
import { isoDe } from "../collector/relogio.ts";
import type { ConfigSecoes } from "../collector/turno2-config.ts";
import type { EventoNovo, ItemLote, LinhaSecao2t } from "../db/escrita.ts";
import { corrigirTotalizadoEm, hhmmDeMinutos, minutosDesde17h, REGIOES } from "../turno2/comum.ts";
import type { ClasseFetch } from "../types.ts";
import { desenharUf } from "./amostra.ts";
import type { BuComparavel } from "./boletim.ts";
import { AuxSchema, escolherHash, minutosEntre, recebidoIso, resumoBu } from "./boletim.ts";
import { decodificarBu } from "./bu-decode.ts";
import { lerCs, quadroDoCs } from "./cs.ts";
import type { SecaoChave, UrlsUrna } from "./urls.ts";
import { chaveSecao, urlsUrna } from "./urls.ts";

export interface RespostaHttp {
  status: number | null;
  corpo: Uint8Array<ArrayBuffer> | null;
  retryAfter: number | null;
  erro: string | null;
}

export type Obter = (url: string) => Promise<RespostaHttp>;

/** UFs da amostra nacional (o exterior fica fora: a hora da urna segue o fuso do país). */
export const UFS_AMOSTRA: readonly string[] = Object.entries(REGIOES)
  .filter(([r]) => r !== "ZZ")
  .flatMap(([, l]) => l.map((u) => u.toLowerCase()))
  .sort();

export interface OpcoesAmostra {
  cfg: ConfigSecoes;
  pleito: number;
  eleFederal: number;
  t0Ms: number;
  /** conexão do escritor: estado na partida e totalização do município (ab_estado) */
  db: Database;
  gravar: (itens: ItemLote[]) => void;
  relogio: Relogio;
  urls?: UrlsUrna;
  obter?: Obter;
  /** pausa global do coletor principal (403/429) */
  pausaPrincipal?: () => boolean;
  dormir?: (ms: number) => Promise<void>;
  log?: (o: Record<string, unknown>) => void;
  ufs?: readonly string[];
  ua?: string;
}

interface Alvo {
  id: number;
  s: SecaoChave;
  chave: string;
  linha: LinhaSecao2t;
  due: number;
  paralela: boolean;
  feito: boolean;
  votos: BuComparavel | null;
  falhas: number;
}

export interface EstadoSecao {
  feito: boolean;
  status: string | null;
  erro: string | null;
  linha: LinhaSecao2t;
  votos: BuComparavel | null;
}

const ERROS_TRANSITORIOS: ReadonlySet<ClasseFetch> = new Set(["erro_servidor", "timeout", "erro_rede", "corpo_invalido"]);

export function obterPadrao(ua: string, timeoutMs: number): Obter {
  return async (url) => {
    try {
      const res = await fetch(url, {
        headers: { "User-Agent": ua, "Accept-Encoding": "gzip", Accept: "*/*" },
        signal: AbortSignal.timeout(timeoutMs),
      });
      const corpo = new Uint8Array(await res.arrayBuffer());
      return { status: res.status, corpo, retryAfter: retryAfterS(res.headers.get("retry-after"), Date.now()), erro: res.status === 200 ? null : `HTTP ${res.status}` };
    } catch (err) {
      const nome = err instanceof Error ? err.name : "";
      return { status: null, corpo: null, retryAfter: null, erro: `${nome}: ${err instanceof Error ? err.message : String(err)}`.slice(0, 300) };
    }
  };
}

/** Classe da resposta: JSON pelo classificador do coletor; binário (BU) só pelo status. */
export function classeDe(r: RespostaHttp, json: boolean): ClasseFetch {
  if (r.status === null) return (r.erro ?? "").startsWith("TimeoutError") ? "timeout" : "erro_rede";
  const corpo = r.corpo ?? new Uint8Array();
  if (r.status === 200 && !json) {
    const c = classificar(200, corpo);
    return c === "negado" ? "negado" : "ok";
  }
  return classificar(r.status, corpo);
}

function linhaVazia(s: SecaoChave, origem: "amostra" | "paralela", em: string): LinhaSecao2t {
  return {
    uf: s.uf, mun: s.mun, zona: s.zona, secao: s.secao, origem, status_aux: "pendente", hash: null, bu_nome: null, dr_hr: null,
    encerramento_local: null, encerramento_iso: null, emissao_iso: null, recebido_iso: null, bu_sha256: null, aptos: null,
    comparecimento: null, votos_json: null, totalizado_mun_iso: null, lag_encerr_recebimento_min: null, lag_encerr_emissao_min: null,
    lag_recebimento_totalizacao_min: null, erro: null, tentativas: 0, atualizado_em: em,
  };
}

const porDue = (a: Alvo, b: Alvo): boolean => a.due < b.due || (a.due === b.due && a.id < b.id);

export class AmostraSecoes {
  private readonly urls: UrlsUrna;
  private readonly obter: Obter;
  private readonly lim: Limitador;
  private readonly dormir: (ms: number) => Promise<void>;
  private readonly porChave = new Map<string, Alvo>();
  private readonly filaAmostra = new HeapIndexado<Alvo>(porDue, (a) => a.id);
  private readonly filaParalela = new HeapIndexado<Alvo>(porDue, (a) => a.id);
  private readonly ufsSemQuadro = new Set<string>();
  private readonly marcas: number[] = [];
  private readonly classes: Partial<Record<ClasseFetch, number>> = {};
  private seq = 0;
  private emVoo = 0;
  private rodando = false;
  private ultimoPeriodico = 0;
  private ultimaPreparacao = 0;
  private parado = false;
  requisicoes = 0;

  constructor(private readonly o: OpcoesAmostra) {
    this.urls = o.urls ?? urlsUrna(o.pleito);
    this.obter = o.obter ?? obterPadrao(o.ua ?? UA_PADRAO, o.cfg.timeoutMs);
    this.dormir = o.dormir ?? ((ms) => Bun.sleep(ms));
    const rps = o.cfg.rps;
    this.lim = new Limitador(o.relogio, { global: { taxa: rps, rajada: Math.max(1, Math.ceil(rps)) }, sweep: { taxa: rps, rajada: Math.max(1, Math.ceil(rps)) } });
  }

  private log(x: Record<string, unknown>): void {
    this.o.log?.({ t: "secoes2t", ...x });
  }

  private agora(): number {
    return this.o.relogio.agora();
  }

  private fila(a: Alvo): HeapIndexado<Alvo> {
    return a.paralela ? this.filaParalela : this.filaAmostra;
  }

  private escalonar(a: Alvo, due: number): void {
    a.due = due;
    this.filaAmostra.remover(a.id);
    this.filaParalela.remover(a.id);
    this.fila(a).inserir(a);
  }

  private gravarLinha(a: Alvo, extra: ItemLote[] = []): void {
    a.linha.atualizado_em = isoDe(this.agora());
    this.o.gravar([{ k: "secao_2t", row: { ...a.linha } }, ...extra]);
  }

  /** Atraso inicial espalhado pelo intervalo, para a primeira rodada não sair em rajada. */
  private espalhado(chave: string, base: number, intervaloS: number): number {
    let h = 0;
    for (let i = 0; i < chave.length; i++) h = (h * 31 + chave.charCodeAt(i)) >>> 0;
    return base + (h % Math.max(1, Math.round(intervaloS))) * 1000;
  }

  private novoAlvo(s: SecaoChave, linha: LinhaSecao2t, paralela: boolean, due: number): Alvo {
    const votos = linha.votos_json === null ? null : (JSON.parse(linha.votos_json) as BuComparavel);
    const a: Alvo = { id: ++this.seq, s, chave: chaveSecao(s), linha, due, paralela, feito: linha.bu_sha256 !== null, votos, falhas: 0 };
    this.porChave.set(a.chave, a);
    if (!a.feito) this.fila(a).inserir(a);
    return a;
  }

  /** Estado do banco (retomada) e desenho das UFs ainda sem amostra. */
  async preparar(): Promise<void> {
    const agora = this.agora();
    this.ultimaPreparacao = agora;
    const inicio = Math.max(agora, this.o.cfg.inicioMs);
    if (this.porChave.size === 0) {
      for (const l of this.o.db.query<LinhaSecao2t, []>("SELECT * FROM secao_2t").all()) {
        const s = { uf: l.uf, mun: l.mun, zona: l.zona, secao: l.secao };
        const intervalo = l.origem === "paralela" ? this.o.cfg.intervaloParalelaS : this.o.cfg.intervaloS;
        this.novoAlvo(s, l, l.origem === "paralela", this.espalhado(chaveSecao(s), inicio, Math.min(intervalo, 120)));
      }
    }
    if (!this.o.cfg.amostra) return;
    const comAmostra = new Set(this.o.db.query<{ uf: string }, []>("SELECT DISTINCT uf FROM secao_2t WHERE origem = 'amostra'").all().map((r) => r.uf));
    const ufs = (this.o.ufs ?? UFS_AMOSTRA).filter((u) => !comAmostra.has(u));
    for (const uf of ufs) {
      const quadro = await this.quadro(uf);
      if (quadro === null) {
        this.ufsSemQuadro.add(uf);
        continue;
      }
      this.ufsSemQuadro.delete(uf);
      const em = isoDe(this.agora());
      const itens: ItemLote[] = [];
      for (const s of desenharUf(uf, quadro, this.o.cfg).values()) {
        const k = chaveSecao(s);
        const existente = this.porChave.get(k);
        if (existente) {
          existente.linha.origem = "amostra";
          continue;
        }
        const a = this.novoAlvo(s, linhaVazia(s, "amostra", em), false, this.espalhado(k, inicio, this.o.cfg.intervaloS));
        itens.push({ k: "secao_2t", row: { ...a.linha } });
      }
      if (itens.length > 0) this.o.gravar(itens);
      this.log({ ev: "amostra_uf", uf, secoes_quadro: quadro.length, alvo: itens.length });
    }
  }

  /** Quadro de seções da UF: cache local (até 6 h) ou TSE; null se nenhum dos dois. */
  private async quadro(uf: string): Promise<SecaoChave[] | null> {
    const arq = join(this.o.cfg.dirCs, `${uf}-p${String(this.o.pleito).padStart(6, "0")}-cs.json`);
    const fresco = existsSync(arq) && this.agora() - statSync(arq).mtimeMs < 6 * 3600_000;
    let bruto: Uint8Array | null = fresco ? new Uint8Array(readFileSync(arq)) : null;
    if (bruto === null) {
      const r = await this.pedir(this.urls.cs(uf));
      if (r.status === 200 && r.corpo !== null && classeDe(r, true) === "ok") {
        bruto = r.corpo;
        try {
          mkdirSync(this.o.cfg.dirCs, { recursive: true });
          writeFileSync(arq, r.corpo);
        } catch (err) {
          this.log({ ev: "cs_cache_falhou", uf, erro: err instanceof Error ? err.message : String(err) });
        }
      } else if (existsSync(arq)) {
        bruto = new Uint8Array(readFileSync(arq));
      } else {
        this.log({ ev: "cs_indisponivel", uf, status: r.status, erro: r.erro });
        return null;
      }
    }
    try {
      return quadroDoCs(lerCs(bruto)).secoes.filter((s) => s.uf === uf);
    } catch (err) {
      this.log({ ev: "cs_invalido", uf, erro: err instanceof Error ? err.message : String(err) });
      return null;
    }
  }

  /** Seção vinda da totalização paralela: entra (ou sobe) na fila prioritária. */
  adicionarParalela(s: SecaoChave): void {
    const k = chaveSecao(s);
    const a = this.porChave.get(k);
    const agora = this.agora();
    if (a) {
      if (!a.feito && !a.paralela) {
        a.paralela = true;
        this.escalonar(a, agora);
      }
      return;
    }
    const novo = this.novoAlvo(s, linhaVazia(s, "paralela", isoDe(agora)), true, agora);
    this.gravarLinha(novo);
  }

  estado(s: SecaoChave): EstadoSecao | null {
    const a = this.porChave.get(chaveSecao(s));
    return a ? { feito: a.feito, status: a.linha.status_aux, erro: a.linha.erro, linha: a.linha, votos: a.votos } : null;
  }

  /** Uma requisição com ficha do balde próprio, esperando a pausa global e a própria. */
  private async pedir(url: string): Promise<RespostaHttp> {
    for (;;) {
      if (this.parado) return { status: null, corpo: null, retryAfter: null, erro: "parado" };
      const principal = this.o.pausaPrincipal?.() ?? false;
      if (!principal && this.lim.tentar(false)) break;
      await this.dormir(principal ? 500 : Math.max(5, Math.min(1000, this.lim.esperaMs(false))));
    }
    const r = await this.obter(url);
    this.requisicoes += 1;
    this.marcas.push(this.agora());
    return r;
  }

  private registrarClasse(c: ClasseFetch): void {
    this.classes[c] = (this.classes[c] ?? 0) + 1;
  }

  private pausar(retryAfter: number | null, classe: ClasseFetch): number {
    const nova = !this.lim.pausado();
    const ate = this.lim.pausar(retryAfter);
    if (nova) {
      const em = isoDe(this.agora());
      const ev: EventoNovo = { em, tipo: "secoes2t_pausa", severidade: "warn", detalhe: { classe, ate: isoDe(ate), retry_after_s: retryAfter } };
      this.o.gravar([{ k: "evento", row: ev }]);
      this.log({ ev: "pausa", classe, ate: isoDe(ate) });
    }
    return ate;
  }

  /** Próxima consulta: intervalo normal, espera exponencial em erro, fim da pausa em 403/429. */
  private reagendar(a: Alvo, classe: ClasseFetch, retryAfter: number | null, emMs: number | null = null): void {
    const agora = this.agora();
    const intervalo = (a.paralela ? this.o.cfg.intervaloParalelaS : this.o.cfg.intervaloS) * 1000;
    let due = agora + intervalo;
    if (classe === "negado" || classe === "limite") due = this.pausar(retryAfter, classe);
    else if (emMs !== null) due = agora + Math.min(intervalo, emMs);
    else if (ERROS_TRANSITORIOS.has(classe)) due = agora + Math.min(intervalo, 5000 * 2 ** Math.min(6, a.falhas));
    this.escalonar(a, due);
  }

  /** aux.json → hash → BU. Nunca lança. */
  private async processar(a: Alvo): Promise<void> {
    a.linha.tentativas += 1;
    const aux = await this.pedir(this.urls.aux(a.s));
    if (this.parado) return; // desligando: a seção volta na próxima partida, sem erro gravado
    const ca = classeDe(aux, true);
    this.registrarClasse(ca);
    if (ca === "nao_existe") {
      a.falhas = 0;
      a.linha.status_aux = "aux_404";
      a.linha.erro = null;
      this.gravarLinha(a);
      this.reagendar(a, ca, null);
      return;
    }
    if (ca !== "ok" || aux.corpo === null) {
      a.falhas += 1;
      a.linha.status_aux = "aux_erro";
      a.linha.erro = `aux: ${aux.erro ?? ca}`;
      this.gravarLinha(a);
      this.reagendar(a, ca, aux.retryAfter);
      return;
    }
    let esc: ReturnType<typeof escolherHash>;
    try {
      const doc = AuxSchema.parse(JSON.parse(new TextDecoder().decode(aux.corpo)));
      a.linha.status_aux = doc.st ?? "sem_st";
      esc = escolherHash(doc);
    } catch (err) {
      a.falhas += 1;
      a.linha.status_aux = "aux_erro";
      a.linha.erro = `aux inválido: ${err instanceof Error ? err.message : String(err)}`.slice(0, 300);
      this.gravarLinha(a);
      this.reagendar(a, "corpo_invalido", null);
      return;
    }
    if (esc === null) {
      a.falhas = 0;
      a.linha.erro = null;
      this.gravarLinha(a);
      this.reagendar(a, "nao_existe", null);
      return;
    }
    a.linha.hash = esc.hash;
    a.linha.bu_nome = esc.bu;
    a.linha.dr_hr = esc.drHr;
    a.linha.recebido_iso = recebidoIso(esc.drHr);
    const bu = await this.pedir(this.urls.arquivo(a.s, esc.hash, esc.bu));
    if (this.parado) return;
    const cb = classeDe(bu, false);
    this.registrarClasse(cb);
    if (cb !== "ok" || bu.corpo === null) {
      a.falhas += 1;
      a.linha.erro = `bu: ${bu.erro ?? cb}`;
      this.gravarLinha(a);
      // hash listado e arquivo ainda ausente no CDN: tenta de novo em 1 min
      this.reagendar(a, cb, bu.retryAfter, cb === "nao_existe" ? 60_000 : null);
      return;
    }
    try {
      const r = resumoBu(decodificarBu(bu.corpo).bu, a.s.uf, this.o.eleFederal);
      const l = a.linha;
      l.bu_sha256 = new Bun.CryptoHasher("sha256").update(bu.corpo).digest("hex");
      l.encerramento_local = r.encerramentoLocal;
      l.encerramento_iso = r.encerramentoIso;
      l.emissao_iso = r.emissaoIso;
      l.aptos = r.aptos;
      l.comparecimento = r.comparecimento;
      l.votos_json = JSON.stringify(r.votos);
      l.lag_encerr_recebimento_min = minutosEntre(r.encerramentoIso, l.recebido_iso);
      l.lag_encerr_emissao_min = minutosEntre(r.encerramentoIso, r.emissaoIso);
      l.erro = null;
      a.votos = r.votos;
      a.feito = true;
      a.falhas = 0;
      this.preencherTotalizacao([a]);
      this.gravarLinha(a, this.tardia(a));
    } catch (err) {
      a.falhas += 1;
      a.linha.erro = `bu decodificação: ${err instanceof Error ? err.message : String(err)}`.slice(0, 300);
      this.gravarLinha(a);
      this.reagendar(a, "corpo_invalido", null);
    }
  }

  /** Evento info para seção encerrada depois das 18:00 de Brasília. */
  private tardia(a: Alvo): ItemLote[] {
    const l = a.linha;
    const enc = l.encerramento_iso;
    if (enc === null || Date.parse(enc) <= this.o.t0Ms + 60 * 60_000) return [];
    const minEnc = minutosDesde17h(enc, this.o.t0Ms);
    const minRec = l.recebido_iso === null ? null : minutosDesde17h(l.recebido_iso, this.o.t0Ms);
    const ev: EventoNovo = {
      em: isoDe(this.agora()), tipo: "secao_tardia", severidade: "info", eleicao_cd: this.o.eleFederal, nivel: "zona", uf: l.uf,
      municipio_cd: l.mun, zona_cd: String(l.zona).padStart(4, "0"),
      detalhe: {
        secao: l.secao, zona: l.zona, encerramento_iso: enc, encerramento_hhmm: minEnc === null ? null : hhmmDeMinutos(Math.floor(minEnc)),
        recebido_iso: l.recebido_iso, recebido_hhmm: minRec === null ? null : hhmmDeMinutos(Math.floor(minRec)), lag_min: l.lag_encerr_recebimento_min,
        origem: l.origem,
      },
    };
    return [{ k: "evento", row: ev }];
  }

  /**
   * Totalização do município depois do recebimento: primeira versão do arquivo -u (mu) de
   * presidente do município com totalizado_em, corrigido do fuso, igual ou posterior ao
   * recebimento da seção. Entra também o totalizado_em do município no -ab da UF, lido a cada
   * minuto, que pega versões do mu que a leitura mais espaçada do arquivo perdeu; vale a mais
   * cedo das duas. É a primeira versão em que a seção pode ter entrado: o TSE não publica a
   * inclusão seção a seção.
   */
  private preencherTotalizacao(alvos: readonly Alvo[]): Alvo[] {
    const ele = this.o.eleFederal;
    const qMu = this.o.db.query<{ t: string | null; g: string | null }, [string, string, number]>(
      `SELECT s.totalizado_em AS t, s.gerado_em AS g FROM arquivo a JOIN snapshot s ON s.arquivo_id = a.id AND s.regressivo = 0
       WHERE a.tipo = 'u' AND a.nivel = 'mu' AND a.cargo_cd = 1 AND a.municipio_cd = ? AND a.uf = ? AND a.eleicao_cd = ? AND s.totalizado_em IS NOT NULL`,
    );
    const qAb = this.o.db.query<{ t: string | null; g: string | null }, [string, string, number]>(
      `SELECT e.totalizado_em AS t, s.gerado_em AS g FROM ab_estado e
       JOIN snapshot s ON s.id = e.snapshot_id AND s.regressivo = 0 JOIN arquivo a ON a.id = s.arquivo_id
       WHERE e.cdabr = ? AND a.tipo = 'ab' AND a.nivel = 'uf' AND a.uf = ? AND a.eleicao_cd = ? AND e.totalizado_em IS NOT NULL`,
    );
    const cache = new Map<string, string[]>();
    const mudou: Alvo[] = [];
    for (const a of alvos) {
      const l = a.linha;
      if (l.recebido_iso === null || l.totalizado_mun_iso !== null || l.uf === "zz") continue;
      const k = `${l.uf}|${l.mun}`;
      let tempos = cache.get(k);
      if (!tempos) {
        tempos = [...qMu.all(l.mun, l.uf, ele), ...qAb.all(l.mun, l.uf, ele)]
          .map((r) => corrigirTotalizadoEm(l.uf, r.t, r.g))
          .filter((x): x is string => x !== null)
          .sort();
        cache.set(k, tempos);
      }
      const rec = l.recebido_iso;
      const t = tempos.find((x) => x >= rec);
      if (t === undefined) continue;
      l.totalizado_mun_iso = t;
      l.lag_recebimento_totalizacao_min = minutosEntre(rec, t);
      mudou.push(a);
    }
    return mudou;
  }

  private periodico(agora: number): void {
    if (agora - this.ultimoPeriodico < 60_000) return;
    this.ultimoPeriodico = agora;
    // teto por passada: o laço do coletor principal divide a mesma thread
    const pend = [...this.porChave.values()].filter((a) => a.feito && a.linha.recebido_iso !== null && a.linha.totalizado_mun_iso === null).slice(0, 1500);
    for (const a of this.preencherTotalizacao(pend)) this.gravarLinha(a);
    if (this.ufsSemQuadro.size > 0 && agora - this.ultimaPreparacao > 10 * 60_000) {
      void this.preparar().catch((err: unknown) => this.log({ ev: "preparar_falhou", erro: err instanceof Error ? err.message : String(err) }));
    }
  }

  private proximo(agora: number): Alvo | null {
    const p = this.filaParalela.topo();
    if (p && p.due <= agora) return this.filaParalela.extrair() ?? null;
    if (agora < this.o.cfg.inicioMs) return null;
    const a = this.filaAmostra.topo();
    if (a && a.due <= agora) return this.filaAmostra.extrair() ?? null;
    return null;
  }

  /** Laço até `parar()`. Não usa a fila nem o balde do coletor principal. */
  async rodar(): Promise<void> {
    this.rodando = true;
    while (this.rodando) {
      const agora = this.agora();
      try {
        this.periodico(agora);
      } catch (err) {
        this.log({ ev: "periodico_falhou", erro: err instanceof Error ? err.message : String(err) });
      }
      if (this.emVoo >= this.o.cfg.concorrencia) {
        await this.dormir(20);
        continue;
      }
      const a = this.proximo(agora);
      if (a === null) {
        await this.dormir(200);
        continue;
      }
      this.emVoo += 1;
      void this.processar(a)
        .catch((err: unknown) => {
          this.log({ ev: "erro_interno", chave: a.chave, erro: err instanceof Error ? err.message : String(err) });
          this.reagendar(a, "erro_rede", null);
        })
        .finally(() => {
          this.emVoo -= 1;
        });
    }
  }

  async parar(timeoutMs = 5000): Promise<void> {
    this.rodando = false;
    this.parado = true;
    const fim = Date.now() + timeoutMs;
    while (this.emVoo > 0 && Date.now() < fim) await Bun.sleep(20);
  }

  /** Para o estado do coletor (/api/estado). */
  metricas(agora: number): Record<string, unknown> {
    while (this.marcas.length > 0 && (this.marcas[0] ?? agora) < agora - 60_000) this.marcas.shift();
    let feitas = 0;
    let paralela = 0;
    for (const a of this.porChave.values()) {
      if (a.feito) feitas += 1;
      if (a.paralela || a.linha.origem === "paralela") paralela += 1;
    }
    return {
      alvo: this.porChave.size, feitas, pendentes: this.porChave.size - feitas, paralela, em_voo: this.emVoo,
      req_60s: this.marcas.length, rps_60s: Math.round((this.marcas.length / 60) * 10) / 10, requisicoes: this.requisicoes,
      classes: this.classes, pausado_ate: this.lim.pausado(agora) ? isoDe(this.lim.pausadoAte() ?? agora) : null,
      ufs_sem_quadro: [...this.ufsSemQuadro], inicio: isoDe(this.o.cfg.inicioMs),
    };
  }
}
