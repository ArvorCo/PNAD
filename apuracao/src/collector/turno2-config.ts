// Ajustes do motor do 2º turno (pausas, régua, amostra de seções, totalização paralela), todos por
// variável de ambiente. Turno pelo APURACAO_ELEICOES: 6258/6260 = 2º turno.
import { dirname, join } from "node:path";
import type { Config } from "../config.ts";
import { T0_1T_MS, T0_2T_MS, UFS_GOVERNADOR_2T } from "../turno2/comum.ts";
import { PAUSAS_PADRAO } from "./pausas.ts";
import type { OpcoesPausas } from "./pausas.ts";
import { REGUA_PADRAO } from "./regua.ts";
import type { OpcoesRegua } from "./regua.ts";

type Env = Readonly<Record<string, string | undefined>>;

export interface ConfigSecoes {
  /** amostra estratificada ligada (APURACAO_SECOES) */
  amostra: boolean;
  porUf: number;
  estadual: number;
  ufsEstaduais: readonly string[];
  intervaloS: number;
  intervaloParalelaS: number;
  rps: number;
  concorrencia: number;
  semente: string;
  /** antes disto (ms UTC) nenhuma seção é consultada */
  inicioMs: number;
  dirCs: string;
  timeoutMs: number;
}

export interface ConfigParalela {
  ativo: boolean;
  intervaloS: number;
  url: string | null;
  chave: string | null;
  /** ids reconsultados abaixo do maior já lido (commit fora de ordem no Supabase) */
  janela: number;
}

export interface ConfigTurno2 {
  turno: 1 | 2;
  eleFederal: number;
  eleEstadual: number;
  pleito: number;
  t0Ms: number;
  pausas: OpcoesPausas;
  regua: OpcoesRegua;
  secoes: ConfigSecoes;
  paralela: ConfigParalela;
}

function num(v: string | undefined, padrao: number, min = 0): number {
  if (v === undefined || v.trim() === "") return padrao;
  const n = Number(v);
  return Number.isFinite(n) && n >= min ? n : padrao;
}

/** "1" liga, "0" desliga, vazio segue o padrão. */
function chave(v: string | undefined, padrao: boolean): boolean {
  if (v === "1") return true;
  if (v === "0") return false;
  return padrao;
}

function instante(v: string | undefined, padrao: number): number {
  if (v === undefined || v.trim() === "") return padrao;
  const t = Date.parse(v);
  return Number.isFinite(t) ? t : padrao;
}

export function lerConfigTurno2(config: Pick<Config, "eleicoes" | "pleito" | "dbPath">, env: Env = process.env): ConfigTurno2 {
  const turno: 1 | 2 = config.eleicoes.includes(6258) || config.eleicoes.includes(6260) ? 2 : 1;
  const eleFederal = turno === 2 ? 6258 : 6257;
  const eleEstadual = turno === 2 ? 6260 : 6259;
  const t0Ms = turno === 2 ? T0_2T_MS : T0_1T_MS;
  const dados = dirname(config.dbPath);
  return {
    turno,
    eleFederal,
    eleEstadual,
    pleito: config.pleito,
    t0Ms,
    pausas: {
      ...PAUSAS_PADRAO,
      ele: eleFederal,
      limiarNacionalMin: num(env.APURACAO_PAUSA_MIN, PAUSAS_PADRAO.limiarNacionalMin, 1),
      limiarUfMin: num(env.APURACAO_PAUSA_UF_MIN, PAUSAS_PADRAO.limiarUfMin, 1),
    },
    regua: { ...REGUA_PADRAO, ele: eleFederal, t0Ms },
    secoes: {
      amostra: chave(env.APURACAO_SECOES, turno === 2),
      porUf: Math.round(num(env.APURACAO_SECOES_AMOSTRA_UF, 150)),
      estadual: Math.round(num(env.APURACAO_SECOES_AMOSTRA_ESTADUAL, 600)),
      ufsEstaduais: UFS_GOVERNADOR_2T.map((u) => u.toLowerCase()),
      intervaloS: num(env.APURACAO_SECOES_INTERVALO_S, 900, 10),
      intervaloParalelaS: num(env.APURACAO_SECOES_INTERVALO_PARALELA_S, 300, 10),
      rps: num(env.APURACAO_SECOES_RPS, 15, 0.1),
      concorrencia: Math.max(1, Math.round(num(env.APURACAO_SECOES_CONCORRENCIA, 12, 1))),
      semente: env.APURACAO_SECOES_SEMENTE ?? `amostra-${config.pleito}`,
      inicioMs: instante(env.APURACAO_SECOES_INICIO, t0Ms - 5 * 60_000),
      dirCs: env.APURACAO_SECOES_DIR_CS ?? join(dados, "secoes", "cs"),
      timeoutMs: num(env.APURACAO_SECOES_TIMEOUT_MS, 20_000, 1000),
    },
    paralela: {
      ativo: chave(env.APURACAO_PARALELA, turno === 2),
      intervaloS: num(env.APURACAO_PARALELA_INTERVALO_S, 60, 5),
      url: env.APURACAO_PARALELA_URL ?? null,
      chave: env.APURACAO_PARALELA_CHAVE ?? null,
      janela: Math.round(num(env.APURACAO_PARALELA_JANELA, 2000)),
    },
  };
}
