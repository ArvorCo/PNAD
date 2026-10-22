// Ponte com a totalização paralela: a cada APURACAO_PARALELA_INTERVALO_S lê as views públicas do
// Supabase, guarda os BUs aceitos em paralela_bu e confere cada BU oficial (fase O) contra o BU
// que o TSE publica para a mesma seção, buscado pela amostra de seções com prioridade.
// Falha de rede no Supabase não derruba o coletor: o estado fica em meta.paralela_estado com
// `erro` preenchido e os últimos dados lidos.
import type { Database } from "bun:sqlite";
import type { Relogio } from "../collector/relogio.ts";
import { isoDe } from "../collector/relogio.ts";
import type { ConfigParalela } from "../collector/turno2-config.ts";
import type { EventoNovo, ItemLote, LinhaParalelaBu, LinhaParalelaConferencia } from "../db/escrita.ts";
import type { AmostraSecoes } from "../secoes2t/coletor.ts";
import type { BuPublico, CargoParalela, CargoPublico, Diferenca, Situacao, VotoPublico } from "./conferir.ts";
import { cargosDoBu, comparar, qrComparavel, rotuloDiferenca, SITUACOES_FINAIS } from "./conferir.ts";
import type { ClienteSupabase } from "./supabase.ts";

export const ROTULO_PARALELA = "soma dos BUs recebidos, não projeção";
export const META_ESTADO = "paralela_estado";

const COLS_BU = "id,recebido_em,uf,muni,zona,secao,fase,pleito,turno,orig,aptos,comparecimento,hash_final";

export interface CoberturaUf {
  uf: string;
  secoes_total: number;
  secoes_com_bu: number;
  secoes_em_conflito: number;
}

export interface EstatisticasParalela {
  envios: number;
  envios_aceitos: number;
  envios_rejeitados: number;
  bus_oficiais: number;
  secoes_em_conflito: number;
  ultimo_envio: string | null;
  consultado_em: string | null;
}

/** meta.paralela_estado: último retrato dos agregados do Supabase. */
export interface EstadoParalela {
  atualizado_em: string | null;
  consultado_em: string;
  erro: string | null;
  estatisticas: EstatisticasParalela | null;
  cobertura_uf: CoberturaUf[];
  conflitos: number | null;
  totais_br: unknown[];
  totais_uf: unknown[];
  requisicoes: number;
}

export interface OpcoesPonte {
  cfg: ConfigParalela;
  pleito: number;
  eleFederal: number;
  db: Database;
  gravar: (itens: ItemLote[]) => void;
  relogio: Relogio;
  cliente: ClienteSupabase;
  amostra: AmostraSecoes | null;
  dormir?: (ms: number) => Promise<void>;
  log?: (o: Record<string, unknown>) => void;
}

interface BuLocal {
  linha: LinhaParalelaBu;
  cargos: CargoParalela[];
  conf: LinhaParalelaConferencia | null;
}

interface Resultado {
  situacao: Situacao;
  diferencas: Diferenca[];
  erro: string | null;
  tse: { hash: string | null; arquivo: string | null; sha256: string | null; recebido: string | null };
}

const SEM_TSE = { hash: null, arquivo: null, sha256: null, recebido: null };

function agrupar<T extends { bu_id: number }>(l: readonly T[]): Map<number, T[]> {
  const m = new Map<number, T[]>();
  for (const x of l) {
    const g = m.get(x.bu_id);
    if (g) g.push(x);
    else m.set(x.bu_id, [x]);
  }
  return m;
}

export class PonteParalela {
  private readonly bus = new Map<number, BuLocal>();
  private maxId = 0;
  private rodando = false;
  private estado: EstadoParalela | null = null;
  private readonly dormir: (ms: number) => Promise<void>;

  constructor(private readonly o: OpcoesPonte) {
    this.dormir = o.dormir ?? ((ms) => Bun.sleep(ms));
  }

  private log(x: Record<string, unknown>): void {
    this.o.log?.({ t: "paralela", ...x });
  }

  /** Retomada: BUs e conferências já gravados. */
  carregar(): void {
    const confs = new Map(
      this.o.db.query<LinhaParalelaConferencia, []>("SELECT * FROM paralela_conferencia").all().map((c) => [c.bu_id, c] as const),
    );
    for (const l of this.o.db.query<LinhaParalelaBu, []>("SELECT * FROM paralela_bu ORDER BY id").all()) {
      this.bus.set(l.id, { linha: l, cargos: JSON.parse(l.cargos_json) as CargoParalela[], conf: confs.get(l.id) ?? null });
      this.maxId = Math.max(this.maxId, l.id);
    }
    const txt = this.o.db.query<{ valor: string | null }, []>(`SELECT valor FROM meta WHERE chave = '${META_ESTADO}'`).get()?.valor ?? null;
    if (txt !== null) {
      try {
        this.estado = JSON.parse(txt) as EstadoParalela;
      } catch {
        this.estado = null;
      }
    }
  }

  get total(): number {
    return this.bus.size;
  }

  /** Lê os BUs novos (janela de ids abaixo do maior, para commits fora de ordem) e os cargos/votos deles. */
  private async lerNovos(em: string): Promise<number> {
    const c = this.o.cliente;
    const desde = Math.max(0, this.maxId - this.o.cfg.janela);
    const novos = (await c.depoisDe<BuPublico>("v_bu_publico", desde, [["select", COLS_BU]])).filter((b) => !this.bus.has(b.id));
    if (novos.length === 0) return 0;
    const ids = novos.map((b) => b.id);
    const filtro: [string, string][] = [["bu_id", `gte.${Math.min(...ids)}`], ["bu_id", `lte.${Math.max(...ids)}`]];
    const cargos = await c.tudo<CargoPublico>("v_bu_cargo_publico", [...filtro, ["order", "bu_id,idel,cargo"]]);
    const votos = await c.tudo<VotoPublico>("v_bu_voto_publico", [...filtro, ["order", "bu_id,idel,cargo,candidato"]]);
    const cPor = agrupar(cargos);
    const vPor = agrupar(votos);
    const linhas: LinhaParalelaBu[] = [];
    for (const b of novos) {
      const cs = cPor.get(b.id);
      if (!cs || cs.length === 0) continue; // cargos ainda não visíveis: volta na próxima leitura
      const cargosBu = cargosDoBu(cs, vPor.get(b.id) ?? []);
      const linha: LinhaParalelaBu = {
        id: b.id, recebido_em: new Date(b.recebido_em).toISOString(), uf: b.uf.toLowerCase(), mun: String(b.muni).padStart(5, "0"), zona: b.zona,
        secao: b.secao, fase: b.fase, pleito: b.pleito, turno: b.turno, orig: b.orig, aptos: b.aptos, comparecimento: b.comparecimento,
        hash_final: b.hash_final, cargos_json: JSON.stringify(cargosBu), lido_em: em,
      };
      linhas.push(linha);
      this.bus.set(b.id, { linha, cargos: cargosBu, conf: null });
      this.maxId = Math.max(this.maxId, b.id);
    }
    if (linhas.length > 0) this.o.gravar([{ k: "paralela_bu", rows: linhas }]);
    return linhas.length;
  }

  private async lerAgregados(): Promise<Pick<EstadoParalela, "estatisticas" | "cobertura_uf" | "conflitos" | "totais_br" | "totais_uf">> {
    const c = this.o.cliente;
    const est = await c.tudo<EstatisticasParalela>("v_estatisticas", []);
    const cobertura = await c.tudo<CoberturaUf>("v_cobertura_uf", [["select", "uf,secoes_total,secoes_com_bu,secoes_em_conflito"], ["order", "uf"]]);
    const conflitos = await c.tudo<{ uf: string }>("v_conflito", [["select", "uf,muni,zona,secao"], ["order", "uf,muni,zona,secao"]]);
    const totaisBr = await c.tudo<unknown>("v_totais_br", [["order", "cargo,candidato"]]);
    const totaisUf = await c.tudo<unknown>("v_totais_uf", [["order", "uf,cargo,candidato"]]);
    return { estatisticas: est[0] ?? null, cobertura_uf: cobertura, conflitos: conflitos.length, totais_br: totaisBr, totais_uf: totaisUf };
  }

  private situacao(b: BuLocal): Resultado {
    const l = b.linha;
    if (l.fase !== "O") return { situacao: "fora_do_oficial", diferencas: [], erro: null, tse: SEM_TSE };
    if (l.pleito !== null && l.pleito !== this.o.pleito) {
      return { situacao: "erro", diferencas: [], erro: `pleito ${l.pleito} fora deste painel (${this.o.pleito})`, tse: SEM_TSE };
    }
    const am = this.o.amostra;
    if (am === null) return { situacao: "erro", diferencas: [], erro: "busca de seções desligada", tse: SEM_TSE };
    const s = { uf: l.uf, mun: l.mun, zona: l.zona, secao: l.secao };
    am.adicionarParalela(s);
    const st = am.estado(s);
    if (st === null) return { situacao: "tse_ainda_nao_publicou", diferencas: [], erro: null, tse: SEM_TSE };
    const tse = { hash: st.linha.hash, arquivo: st.linha.bu_nome, sha256: st.linha.bu_sha256, recebido: st.linha.recebido_iso };
    if (st.feito && st.votos !== null) {
      const dif = comparar(qrComparavel(l.comparecimento, b.cargos), st.votos);
      return { situacao: dif.length === 0 ? "igual" : "divergente", diferencas: dif, erro: null, tse };
    }
    if (st.status === "aux_erro" || st.erro !== null) return { situacao: "erro", diferencas: [], erro: st.erro, tse };
    return { situacao: "tse_ainda_nao_publicou", diferencas: [], erro: null, tse };
  }

  /** Confere os BUs sem situação final; grava o que mudou e os eventos. */
  conferir(em: string): { novos: Record<Situacao, number> } {
    const novos: Record<Situacao, number> = { igual: 0, divergente: 0, tse_ainda_nao_publicou: 0, erro: 0, fora_do_oficial: 0 };
    const itens: ItemLote[] = [];
    for (const b of this.bus.values()) {
      if (b.conf !== null && SITUACOES_FINAIS.has(b.conf.situacao)) continue;
      const r = this.situacao(b);
      const difJson = r.diferencas.length > 0 ? JSON.stringify(r.diferencas) : null;
      if (b.conf !== null && b.conf.situacao === r.situacao && b.conf.erro === r.erro && b.conf.diferencas_json === difJson) continue;
      const l = b.linha;
      const conf: LinhaParalelaConferencia = {
        bu_id: l.id, uf: l.uf, mun: l.mun, zona: l.zona, secao: l.secao, hash_final: l.hash_final, situacao: r.situacao, diferencas_json: difJson,
        erro: r.erro, tse_hash: r.tse.hash, tse_arquivo: r.tse.arquivo, tse_sha256: r.tse.sha256, tse_recebido_iso: r.tse.recebido,
        primeira_em: b.conf?.primeira_em ?? em, conferido_em: em,
      };
      b.conf = conf;
      itens.push({ k: "paralela_conferencia", row: conf });
      novos[r.situacao] += 1;
      if (r.situacao === "divergente") {
        const ev: EventoNovo = {
          em, tipo: "divergencia_paralela", severidade: "error", eleicao_cd: this.o.eleFederal, nivel: "zona", uf: l.uf, municipio_cd: l.mun,
          zona_cd: String(l.zona).padStart(4, "0"),
          detalhe: {
            secao: l.secao, zona: l.zona, bu_id: l.id, hash_final: l.hash_final, recebido_em: l.recebido_em, tse_sha256: r.tse.sha256,
            campos: r.diferencas.slice(0, 30).map((d) => ({ campo: rotuloDiferenca(d), paralela: d.paralela, tse: d.tse })),
            n_diferencas: r.diferencas.length,
          },
        };
        itens.push({ k: "evento", row: ev });
      }
    }
    if (novos.igual + novos.divergente > 0) {
      const ev: EventoNovo = {
        em, tipo: "paralela_conferida", severidade: "info", eleicao_cd: this.o.eleFederal,
        detalhe: { conferidos: novos.igual + novos.divergente, iguais: novos.igual, divergentes: novos.divergente, fora_do_oficial: novos.fora_do_oficial, rotulo: ROTULO_PARALELA },
      };
      itens.push({ k: "evento", row: ev });
    }
    if (itens.length > 0) this.o.gravar(itens);
    return { novos };
  }

  /** Um ciclo: leitura do Supabase (se falhar, segue com o que tem) e conferência. */
  async ciclo(): Promise<EstadoParalela> {
    const em = isoDe(this.o.relogio.agora());
    const anterior = this.estado;
    let erro: string | null = null;
    let novos = 0;
    let agregados: Pick<EstadoParalela, "estatisticas" | "cobertura_uf" | "conflitos" | "totais_br" | "totais_uf"> = {
      estatisticas: anterior?.estatisticas ?? null, cobertura_uf: anterior?.cobertura_uf ?? [], conflitos: anterior?.conflitos ?? null,
      totais_br: anterior?.totais_br ?? [], totais_uf: anterior?.totais_uf ?? [],
    };
    try {
      novos = await this.lerNovos(em);
      agregados = await this.lerAgregados();
    } catch (err) {
      erro = err instanceof Error ? err.message : String(err);
      this.log({ ev: "erro", erro });
    }
    const { novos: conf } = this.conferir(em);
    const estado: EstadoParalela = {
      atualizado_em: erro === null ? em : (anterior?.atualizado_em ?? null), consultado_em: em, erro, ...agregados, requisicoes: this.o.cliente.requisicoes,
    };
    this.estado = estado;
    this.o.gravar([{ k: "meta", chave: META_ESTADO, valor: JSON.stringify(estado) }]);
    if (novos > 0 || conf.igual + conf.divergente > 0) this.log({ ev: "ciclo", novos, conferencia: conf, total: this.bus.size });
    return estado;
  }

  async rodar(): Promise<void> {
    this.rodando = true;
    while (this.rodando) {
      try {
        await this.ciclo();
      } catch (err) {
        this.log({ ev: "ciclo_falhou", erro: err instanceof Error ? err.message : String(err) });
      }
      const fim = this.o.relogio.agora() + this.o.cfg.intervaloS * 1000;
      while (this.rodando && this.o.relogio.agora() < fim) await this.dormir(Math.min(500, fim - this.o.relogio.agora()));
    }
  }

  parar(): void {
    this.rodando = false;
  }

  metricas(): Record<string, unknown> {
    return { bus: this.bus.size, max_id: this.maxId, erro: this.estado?.erro ?? null, atualizado_em: this.estado?.atualizado_em ?? null };
  }
}
