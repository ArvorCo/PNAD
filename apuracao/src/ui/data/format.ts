// Formatação pt-BR com Intl em cache. Sinal de menos tipográfico.

const cache = new Map<string, Intl.NumberFormat>();

function nf(min: number, max: number): Intl.NumberFormat {
  const k = `${min}:${max}`;
  let f = cache.get(k);
  if (!f) {
    f = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: min, maximumFractionDigits: max });
    cache.set(k, f);
  }
  return f;
}

const menos = (s: string): string => s.replace("-", "−");

/** 1234567 → "1.234.567". */
export const inteiro = (x: number): string => menos(nf(0, 0).format(Math.round(x)));

/** Número com casas fixas: 62.4 → "62,4". */
export const decimal = (x: number, casas = 1): string => menos(nf(casas, casas).format(x));

/** Percentual a partir de valor já em pontos (0 a 100): 62.43 → "62,4%". */
export const pct = (x: number, casas: 1 | 2 = 1): string => `${decimal(x, casas)}%`;

/** Diferença com sinal: +3,2 ou −1,0. */
export function comSinal(x: number, casas = 1): string {
  const limiar = 0.5 * 10 ** -casas;
  const v = Math.abs(x) < limiar ? 0 : x;
  return (v > 0 ? "+" : "") + decimal(v, casas);
}

/** "660 mil" e "2,01 mi". Abaixo de mil devolve o inteiro. */
export function compacto(x: number): string {
  const a = Math.abs(x);
  if (a >= 1e6) return `${decimal(x / 1e6, 2)} mi`;
  if (a >= 1e3) return `${inteiro(x / 1e3)} mil`;
  return inteiro(x);
}

/** Regra da casa: "660 mil eleitores", "2,01 mi de eleitores" ("mil" não pede "de"). */
export function quantidade(x: number, unidade: string): string {
  const c = compacto(x);
  return c.endsWith(" mi") ? `${c} de ${unidade}` : `${c} ${unidade}`;
}

export const eleitores = (x: number): string => quantidade(x, "eleitores");

const FUSO = "America/Sao_Paulo";
let fmtHora: Intl.DateTimeFormat | null = null;
let fmtHoraCurta: Intl.DateTimeFormat | null = null;

function data(x: string | number | Date): Date | null {
  const d = x instanceof Date ? x : new Date(x);
  return Number.isNaN(d.getTime()) ? null : d;
}

/** "19:38:05" no horário de Brasília. Vazio para entrada inválida. */
export function hora(x: string | number | Date | null | undefined): string {
  if (x === null || x === undefined || x === "") return "";
  const d = data(x);
  if (!d) return "";
  fmtHora ??= new Intl.DateTimeFormat("pt-BR", {
    timeZone: FUSO,
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hourCycle: "h23",
  });
  return fmtHora.format(d);
}

/** "19:38" no horário de Brasília. */
export function horaCurta(x: string | number | Date | null | undefined): string {
  if (x === null || x === undefined || x === "") return "";
  const d = data(x);
  if (!d) return "";
  fmtHoraCurta ??= new Intl.DateTimeFormat("pt-BR", { timeZone: FUSO, hour: "2-digit", minute: "2-digit", hourCycle: "h23" });
  return fmtHoraCurta.format(d);
}

/** Duração em segundos para "42 s", "3 min 05 s", "1 h 02 min". */
export function duracao(segundos: number): string {
  const s = Math.max(0, Math.round(segundos));
  if (s < 60) return `${s} s`;
  if (s < 3600) return `${Math.floor(s / 60)} min ${String(s % 60).padStart(2, "0")} s`;
  return `${Math.floor(s / 3600)} h ${String(Math.floor((s % 3600) / 60)).padStart(2, "0")} min`;
}

/** Contagem regressiva "HH:MM:SS" (ou "MM:SS" abaixo de uma hora). */
export function regressiva(segundos: number): string {
  const s = Math.max(0, Math.floor(segundos));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const r = s % 60;
  const mm = String(m).padStart(2, "0");
  const ss = String(r).padStart(2, "0");
  return h > 0 ? `${String(h).padStart(2, "0")}:${mm}:${ss}` : `${mm}:${ss}`;
}

/** Instante das 17:00 de Brasília no dia (em Brasília) de `agora`. Brasil sem horário de verão: −03:00 fixo. */
export function dezessete(agora: Date): Date {
  const ymd = new Intl.DateTimeFormat("en-CA", { timeZone: FUSO, year: "numeric", month: "2-digit", day: "2-digit" }).format(agora);
  return new Date(`${ymd}T17:00:00-03:00`);
}

/** Nome próprio a partir de caixa alta do TSE: "SÃO JOSÉ DOS CAMPOS" → "São José dos Campos". */
export function nomeProprio(s: string): string {
  const pequenas = new Set(["de", "da", "do", "das", "dos", "e", "d'"]);
  return s
    .toLocaleLowerCase("pt-BR")
    .split(" ")
    .map((w, i) => (i > 0 && pequenas.has(w) ? w : w.charAt(0).toLocaleUpperCase("pt-BR") + w.slice(1)))
    .join(" ");
}
