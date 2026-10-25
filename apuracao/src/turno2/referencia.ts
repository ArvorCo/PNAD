// Régua do 1º turno (data/referencia_1t.json, gerada por scripts/referencia-1t.ts).
// Carregada uma vez pelo coletor e pelo servidor; o telão recebe só recortes pela API.
import { existsSync, readFileSync, statSync } from "node:fs";
import { resolve } from "node:path";

/** [min após 17:00 BRT, pst, st, ts, comparecimento, abstencao, pa] */
export type PontoCurva = readonly [number, number, number, number, number, number, number];

export interface Marcos {
  p50: number | null;
  p90: number | null;
  p99: number | null;
  p100: number | null;
  p50_hhmm?: string | null;
  p90_hhmm?: string | null;
  p99_hhmm?: string | null;
  p100_hhmm?: string | null;
  primeira_secao_min?: number | null;
  primeira_secao_hhmm?: string | null;
}

export interface MunicipioRef {
  nm?: string;
  te: number;
  ts?: number;
  st: number;
  comparecimento: number;
  abstencao: number;
  pa: number;
  fechou_min: number | null;
  apareceu_min: number | null;
}

export interface AbstencaoRef {
  te: number;
  comparecimento: number;
  abstencao: number;
  pa: number;
}

export interface Percentis {
  p50: number | null;
  p90: number | null;
  p99?: number | null;
}

export interface SecoesLagUf {
  n: number;
  com_recebimento?: number;
  sem_recebimento?: number;
  encerramento_p50_hhmm: string | null;
  encerramento_p90_hhmm: string | null;
  lag_encerr_recebimento_min: Percentis;
  lag_encerr_emissao_min: Percentis;
  recebimento_p50_min: number | null;
  recebimento_p90_min: number | null;
  recebimento_p99_min: number | null;
}

export interface SecoesLagMunicipio {
  n: number;
  lag_encerr_recebimento_p50: number | null;
  lag_p90: number | null;
  recebimento_p90_min: number | null;
}

export interface GovernadorRef {
  curva: PontoCurva[];
  marcos: Marcos;
  final?: unknown;
}

export interface Referencia1T {
  meta: {
    gerado_em: string;
    turno: 1;
    eleicoes: { presidente: number; governador: number };
    regioes: Record<string, string[]>;
    convencoes?: Record<string, string>;
    ignorados?: Record<string, number>;
    [k: string]: unknown;
  };
  curvas: { br: PontoCurva[]; uf: Record<string, PontoCurva[]> };
  marcos: { br: Marcos; uf: Record<string, Marcos> };
  municipios: Record<string, Record<string, MunicipioRef>>;
  abstencao_uf: Record<string, AbstencaoRef>;
  secoes_lag: { uf: Record<string, SecoesLagUf>; br?: SecoesLagUf; municipio: Record<string, Record<string, SecoesLagMunicipio>> };
  governador_1t: Record<string, GovernadorRef>;
}

export const CAMINHO_PADRAO = "data/referencia_1t.json";

let cache: { path: string; mtimeMs: number; ref: Referencia1T } | null = null;

/** Lê a régua (com cache por mtime). Devolve null se o arquivo não existir: o sistema roda sem ela. */
export function carregarReferencia(path: string = process.env.APURACAO_REFERENCIA_1T ?? CAMINHO_PADRAO): Referencia1T | null {
  const abs = resolve(path);
  if (!existsSync(abs)) return null;
  const mtimeMs = statSync(abs).mtimeMs;
  if (cache && cache.path === abs && cache.mtimeMs === mtimeMs) return cache.ref;
  const ref = JSON.parse(readFileSync(abs, "utf8")) as Referencia1T;
  cache = { path: abs, mtimeMs, ref };
  return ref;
}

/** pst que a curva do 1º turno tinha em `min` minutos após 17:00 (último ponto até `min`; 0 antes do primeiro). */
export function pstNoMinuto(curva: readonly PontoCurva[], min: number): number {
  let v = 0;
  for (const p of curva) {
    if (p[0] > min) break;
    v = p[1];
  }
  return v;
}

/** Minutos que o 1º turno levou para alcançar `pst` (interpolação linear entre pontos); null se nunca alcançou. */
export function minutoDoPst(curva: readonly PontoCurva[], pst: number): number | null {
  if (curva.length === 0) return null;
  if (pst <= 0) return curva[0]?.[0] ?? null;
  let ant: PontoCurva | null = null;
  for (const p of curva) {
    if (p[1] >= pst) {
      if (!ant || p[1] === ant[1]) return p[0];
      const f = (pst - ant[1]) / (p[1] - ant[1]);
      return Math.round((ant[0] + f * (p[0] - ant[0])) * 10) / 10;
    }
    ant = p;
  }
  return null;
}

/**
 * Atraso em minutos do 2º turno em relação ao 1º: quanto tempo o 1º turno levou para chegar ao
 * pst atual, menos o tempo decorrido agora. Positivo = 2º turno mais lento.
 */
export function atrasoVsReferencia(curva: readonly PontoCurva[], pstAtual: number, minAgora: number): number | null {
  const m = minutoDoPst(curva, pstAtual);
  if (m === null) return null;
  return Math.round((minAgora - m) * 10) / 10;
}

// ---------------------------------------------------------------- votos do 1º turno por município
// data/referencia_1t_votos.json, gerado por scripts/referencia-1t-votos.ts: base da projeção ao vivo.

/** Votos finais do 1º turno de um município: Flávio (22), Lula (13), válidos, comparecimento, eleitorado. */
export interface MunVotos1T {
  f1: number;
  l1: number;
  vv1: number;
  comp1: number;
  te1: number;
  /** seções do município no 1º turno */
  ts1?: number;
  /** trajetória da noite: [st, votos de Flávio, votos de Lula], st crescente */
  c?: [number, number, number][];
}

export interface ReferenciaVotos1T {
  meta: { gerado_em: string; eleicao: number; cargo: number; [k: string]: unknown };
  brasil: MunVotos1T & { municipios: number };
  ufs: Record<string, MunVotos1T & { municipios: number }>;
  /** UF em caixa alta → código TSE de 5 dígitos → votos */
  municipios: Record<string, Record<string, MunVotos1T>>;
}

export const CAMINHO_VOTOS_PADRAO = "data/referencia_1t_votos.json";

let cacheVotos: { path: string; mtimeMs: number; ref: ReferenciaVotos1T } | null = null;

/** Lê a régua de votos (cache por mtime); null se o arquivo não existir. */
export function carregarReferenciaVotos(path: string = process.env.APURACAO_REFERENCIA_1T_VOTOS ?? CAMINHO_VOTOS_PADRAO): ReferenciaVotos1T | null {
  const abs = resolve(path);
  if (!existsSync(abs)) return null;
  const mtimeMs = statSync(abs).mtimeMs;
  if (cacheVotos && cacheVotos.path === abs && cacheVotos.mtimeMs === mtimeMs) return cacheVotos.ref;
  const ref = JSON.parse(readFileSync(abs, "utf8")) as ReferenciaVotos1T;
  cacheVotos = { path: abs, mtimeMs, ref };
  return ref;
}

// ---------------------------------------------------------------- régua por seção (comparecimento)
// data/referencia_1t_secoes.json, gerada por scripts/referencia-1t-secoes.ts.

export interface MunicipioSecoesRef {
  n: number;
  comp_p50: number | null;
  comp_p90: number | null;
  sem_bio_p50: number | null;
  sem_bio_p90: number | null;
  lon: number | null;
  lat: number | null;
}

export interface RefSecoes1T {
  meta: {
    gerado_em: string;
    campos_secao: string[];
    n_secoes: number;
    enc_1t_pct?: { apos_1700: number | null; apos_1800: number | null; apos_1900: number | null };
    [k: string]: unknown;
  };
  /** [lon, lat] por índice */
  locais: [number, number][];
  /** uf → mun → zona → [secao, aptos1, comp1, sem_bio1, ano_nasc1, enc1_min, local, fl1, lu1][] */
  secoes: Record<string, Record<string, Record<string, (number | null)[][]>>>;
  municipios: Record<string, Record<string, MunicipioSecoesRef>>;
}

export interface SecaoRef1T {
  aptos1: number | null;
  comp1: number | null;
  sem_bio1: number | null;
  ano_nasc1: number | null;
  enc1_min: number | null;
  lon: number | null;
  lat: number | null;
  fl1: number | null;
  lu1: number | null;
}

export const CAMINHO_SECOES_PADRAO = "data/referencia_1t_secoes.json";

let cacheSecoes: { path: string; mtimeMs: number; ref: RefSecoes1T; zonas: Map<string, Map<number, (number | null)[]>> } | null = null;

/** Lê a régua por seção (cache por mtime); null se o arquivo não existir. */
export function carregarReferenciaSecoes(path: string = process.env.APURACAO_REFERENCIA_1T_SECOES ?? CAMINHO_SECOES_PADRAO): RefSecoes1T | null {
  const abs = resolve(path);
  if (!existsSync(abs)) return null;
  const mtimeMs = statSync(abs).mtimeMs;
  if (cacheSecoes && cacheSecoes.path === abs && cacheSecoes.mtimeMs === mtimeMs) return cacheSecoes.ref;
  const ref = JSON.parse(readFileSync(abs, "utf8")) as RefSecoes1T;
  cacheSecoes = { path: abs, mtimeMs, ref, zonas: new Map() };
  return ref;
}

/** Linha da seção no 1T (uf em caixa baixa, mun com 5 dígitos); null se não houver. */
export function secaoRef1T(ref: RefSecoes1T, uf: string, mun: string, zona: number, secao: number): SecaoRef1T | null {
  const u = uf.toLowerCase();
  const kz = `${u}:${mun}:${zona}`;
  let z = cacheSecoes?.ref === ref ? cacheSecoes.zonas.get(kz) : undefined;
  if (z === undefined) {
    const l = ref.secoes[u]?.[mun]?.[String(zona)] ?? [];
    z = new Map(l.map((x) => [x[0] ?? -1, x]));
    if (cacheSecoes?.ref === ref) cacheSecoes.zonas.set(kz, z);
  }
  const x = z.get(secao);
  if (!x) return null;
  const li = x[6] ?? -1;
  const c = li >= 0 ? ref.locais[li] : undefined;
  return {
    aptos1: x[1] ?? null, comp1: x[2] ?? null, sem_bio1: x[3] ?? null, ano_nasc1: x[4] ?? null, enc1_min: x[5] ?? null,
    lon: c?.[0] ?? null, lat: c?.[1] ?? null, fl1: x[7] ?? null, lu1: x[8] ?? null,
  };
}
