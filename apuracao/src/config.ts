// Configuração do coletor. Tudo que o runbook ajusta por env entra em lerConfig().
import type { Prioridade } from "./types.ts";

export const BASE_URL = "https://resultados.tse.jus.br/oficial";
export const CICLO = "ele2026";
export const PLEITO = 3220;

export const ELEICOES_PADRAO: readonly number[] = [6257, 6259, 6261];

/** Cargos majoritários (voto_candidato sempre normalizado). */
export const CARGOS_MAJORITARIOS: ReadonlySet<number> = new Set([1, 3, 5, 25]);

/** Cargos proporcionais. */
export const CARGOS_PROPORCIONAIS: ReadonlySet<number> = new Set([6, 7, 8]);

/**
 * Cargos de uma eleição numa UF. Regra: 7 fora do DF, 8 só no DF.
 * Com uf null devolve os cargos de abrangência nacional (para sondas br).
 */
export function cargosDe(ele: number, uf: string | null): number[] {
  switch (ele) {
    case 6257:
    case 6258:
      return [1];
    case 6259:
      if (uf === null) return [3, 5, 6, 7];
      return uf === "df" ? [3, 5, 6, 8] : [3, 5, 6, 7];
    case 6260:
      return [3];
    case 6261:
      return [25];
    default:
      return [];
  }
}

/** Intervalos em segundos por camada (ver plano, tabela do agendador). */
export const INTERVALOS_S = {
  eleC: 60,
  abBr: 20,
  uBrUf: 30,
  abUf: 60,
  muMinCapital: 120,
  muMin: 300,
  zonaMin: 900,
  sonda: 600,
  sweepPularRecentes: 300,
  saude: 5,
  skew: 60,
  ajustes: 10,
} as const;

/** Eleitorado a partir do qual o município usa o intervalo de capital. */
export const ELEITORADO_GRANDE = 200_000;

/** Ordem do heap: menor número sai primeiro. */
export const PRIORIDADE: Readonly<Record<Prioridade, number>> = {
  final: 0,
  t0: 1,
  t1: 2,
  gatilho: 3,
  probe: 4,
  sweep: 5,
};

export const UA_PADRAO =
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36";

export type ModoZonas = "sempre" | "final";

export interface Config {
  baseUrl: string;
  ciclo: string;
  pleito: number;
  eleicoes: number[];
  dbPath: string;
  concurrency: number;
  concurrencyMin: number;
  rateGlobal: number;
  rateSweep: number;
  timeoutMs: number;
  userAgent: string;
  sweepMin: number;
  sweepLote: number;
  zonas: ModoZonas;
  minIntervaloMuS: number;
  loteMs: number;
  loteItens: number;
}

type Env = Readonly<Record<string, string | undefined>>;

function inteiro(v: string | undefined, padrao: number): number {
  if (v === undefined || v.trim() === "") return padrao;
  const n = Number.parseInt(v, 10);
  return Number.isFinite(n) && n >= 0 ? n : padrao;
}

function listaEleicoes(v: string | undefined): number[] {
  if (v === undefined || v.trim() === "") return [...ELEICOES_PADRAO];
  const out = v
    .split(",")
    .map((s) => Number.parseInt(s.trim(), 10))
    .filter((n) => Number.isFinite(n) && n > 0);
  return out.length > 0 ? out : [...ELEICOES_PADRAO];
}

export function lerConfig(env: Env = process.env): Config {
  return {
    baseUrl: env.APURACAO_BASE_URL ?? BASE_URL,
    ciclo: CICLO,
    pleito: inteiro(env.APURACAO_PLEITO, PLEITO),
    eleicoes: listaEleicoes(env.APURACAO_ELEICOES),
    dbPath: env.APURACAO_DB ?? "data/apuracao.sqlite",
    concurrency: inteiro(env.APURACAO_CONCURRENCY, 32),
    concurrencyMin: 8,
    rateGlobal: 100,
    rateSweep: 40,
    timeoutMs: 15_000,
    userAgent: env.APURACAO_UA ?? UA_PADRAO,
    sweepMin: inteiro(env.APURACAO_SWEEP_MIN, 30),
    sweepLote: 500,
    zonas: env.APURACAO_ZONAS === "final" ? "final" : "sempre",
    minIntervaloMuS: inteiro(env.APURACAO_MIN_INTERVALO_MU, INTERVALOS_S.muMin),
    loteMs: 200,
    loteItens: 50,
  };
}

export const CONFIG: Config = lerConfig();
