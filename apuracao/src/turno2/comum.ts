// Constantes e relógio do 2º turno (25/10/2026), compartilhados por coletor, servidor e telão.
// Sem dependência de Node ou Bun: o telão também importa este módulo.

export const DIA_2T = "2026-10-25";
export const DIA_1T = "2026-10-04";
/** 17:00 de Brasília (UTC-3) do dia da eleição, em ms UTC. */
export const T0_2T_MS = Date.parse(`${DIA_2T}T20:00:00.000Z`);
export const T0_1T_MS = Date.parse(`${DIA_1T}T20:00:00.000Z`);

export const ELEICAO_FEDERAL_2T = 6258;
export const ELEICAO_ESTADUAL_2T = 6260;
export const PLEITO_2T = 3221;

/** UFs com 2º turno para governador (arquivo mun-e006260-cm.json do TSE, lido em 21/10/2026). */
export const UFS_GOVERNADOR_2T: readonly string[] = ["AC", "AM", "DF", "ES", "RN", "TO"];

export type Regiao = "N" | "NE" | "CO" | "SE" | "S" | "ZZ";

export const REGIOES: Readonly<Record<Regiao, readonly string[]>> = {
  N: ["AC", "AM", "AP", "PA", "RO", "RR", "TO"],
  NE: ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"],
  CO: ["DF", "GO", "MS", "MT"],
  SE: ["ES", "MG", "RJ", "SP"],
  S: ["PR", "RS", "SC"],
  ZZ: ["ZZ"],
};

export const NOME_REGIAO: Readonly<Record<Regiao, string>> = {
  N: "Norte",
  NE: "Nordeste",
  CO: "Centro-Oeste",
  SE: "Sudeste",
  S: "Sul",
  ZZ: "Exterior",
};

export const ORDEM_REGIOES: readonly Regiao[] = ["N", "NE", "CO", "SE", "S", "ZZ"];

const UF_REGIAO: Readonly<Record<string, Regiao>> = Object.fromEntries(
  (Object.keys(REGIOES) as Regiao[]).flatMap((r) => REGIOES[r].map((uf) => [uf, r] as const)),
) as Record<string, Regiao>;

export function regiaoDe(uf: string): Regiao | null {
  return UF_REGIAO[uf.toUpperCase()] ?? null;
}

/**
 * Deslocamento do relógio local da UF em relação a Brasília, em minutos (negativo = atrás).
 * Vale para a hora da urna (abertura, encerramento, emissão do BU) e para o `dt/ht`
 * (totalizado_em) dos arquivos do TSE, que nessas UFs vem em hora local rotulada como Brasília.
 */
export const FUSO_MIN: Readonly<Record<string, number>> = {
  AC: -120,
  AM: -60,
  RO: -60,
  RR: -60,
  MT: -60,
  MS: -60,
};

export function fusoMin(uf: string): number {
  return FUSO_MIN[uf.toUpperCase()] ?? 0;
}

/** Minutos após 17:00 de Brasília do dia da eleição (1 decimal). Negativo antes das 17:00. */
export function minutosDesde17h(iso: string, t0Ms: number = T0_2T_MS): number | null {
  const t = Date.parse(iso);
  if (!Number.isFinite(t)) return null;
  return Math.round(((t - t0Ms) / 60000) * 10) / 10;
}

/** O inverso: minutos após 17:00 → ISO UTC. */
export function isoDeMinutos(min: number, t0Ms: number = T0_2T_MS): string {
  return new Date(t0Ms + min * 60000).toISOString();
}

/** "hh:mm" de Brasília a partir de minutos após 17:00 (passa de 24h como "02:59 (+1)"). */
export function hhmmDeMinutos(min: number): string {
  const total = Math.round(17 * 60 + min);
  const dias = Math.floor(total / 1440);
  const resto = ((total % 1440) + 1440) % 1440;
  const hh = String(Math.floor(resto / 60)).padStart(2, "0");
  const mm = String(resto % 60).padStart(2, "0");
  return dias > 0 ? `${hh}:${mm} (+${dias})` : `${hh}:${mm}`;
}

/** Folga da regra do fuso: carimbo local pode ficar até 10 min além da geração (relógios). */
export const FOLGA_FUSO_MIN = 10;

/**
 * Corrige o `totalizado_em` de uma UF com fuso próprio quando ele veio em hora local.
 * O carimbo é local sempre que `gerado_em − totalizado_em` alcança o deslocamento da UF menos
 * 10 min; aí recebe o deslocamento, limitado à geração (a totalização não acontece depois da
 * publicação). Sem teto de diferença: a primeira versão depois de uma pausa geral traz uma
 * totalização feita durante ela (77 a 92 min antes da geração em AM, MS e MT às 20:02 do 1º
 * turno) e continua em hora local. Recomputações do dia seguinte vêm em Brasília com diferença
 * de segundos e ficam como estão.
 */
export function corrigirTotalizadoEm(uf: string, totalizadoIso: string | null, geradoIso: string | null): string | null {
  if (!totalizadoIso) return null;
  const desloc = fusoMin(uf);
  if (desloc === 0 || !geradoIso) return totalizadoIso;
  const t = Date.parse(totalizadoIso);
  const g = Date.parse(geradoIso);
  if (!Number.isFinite(t) || !Number.isFinite(g)) return totalizadoIso;
  const difMin = (g - t) / 60000;
  if (difMin >= -desloc - FOLGA_FUSO_MIN) return new Date(Math.min(t - desloc * 60000, g)).toISOString();
  return totalizadoIso;
}

/** Hora local da urna ("aaaa-mm-dd hh:mm:ss" ou "dd/mm/aaaa hh:mm:ss", sem fuso) → ISO UTC via fuso da UF. */
export function horaLocalUrnaParaIso(uf: string, texto: string | null | undefined): string | null {
  if (!texto) return null;
  const s = texto.trim();
  let m = /^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2}):(\d{2})/.exec(s);
  let ano: number, mes: number, dia: number;
  if (m) {
    ano = Number(m[1]);
    mes = Number(m[2]);
    dia = Number(m[3]);
  } else {
    m = /^(\d{2})\/(\d{2})\/(\d{4})[ T](\d{2}):(\d{2}):(\d{2})/.exec(s);
    if (!m) return null;
    dia = Number(m[1]);
    mes = Number(m[2]);
    ano = Number(m[3]);
  }
  const base = Date.UTC(ano, mes - 1, dia, Number(m[4]) + 3, Number(m[5]), Number(m[6]));
  if (!Number.isFinite(base)) return null;
  return new Date(base - fusoMin(uf) * 60000).toISOString();
}

/** Carimbo do TSE em Brasília ("aaaa-mm-dd hh:mm:ss", como no dr_hr do aux.json) → ISO UTC. */
export function horaBrasiliaParaIso(texto: string | null | undefined): string | null {
  return horaLocalUrnaParaIso("BR", texto);
}

export function percentil(ordenado: readonly number[], p: number): number | null {
  if (ordenado.length === 0) return null;
  const i = Math.min(ordenado.length - 1, Math.max(0, Math.ceil((p / 100) * ordenado.length) - 1));
  return ordenado[i] ?? null;
}
