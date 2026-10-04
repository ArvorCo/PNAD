// Conversão dos números do TSE: strings, decimais com vírgula, "" para ausente.

type Entrada = string | number | null | undefined;

const RE_INT = /^-?\d+$/;
const RE_NUM = /^-?\d+(\.\d+)?$/;

/** "6773587" → 6773587; "" / undefined / lixo → null. Aceita ponto de milhar. */
export function intBR(v: Entrada): number | null {
  if (v === null || v === undefined) return null;
  if (typeof v === "number") return Number.isInteger(v) ? v : null;
  const s = v.trim().replaceAll(".", "");
  return RE_INT.test(s) ? Number.parseInt(s, 10) : null;
}

/** "0,675628098" → 0.675628098; "100" → 100; "" → null. */
export function numBR(v: Entrada): number | null {
  if (v === null || v === undefined) return null;
  if (typeof v === "number") return Number.isFinite(v) ? v : null;
  const s = v.trim();
  if (s === "") return null;
  const normal = s.includes(",") ? s.replaceAll(".", "").replace(",", ".") : s;
  return RE_NUM.test(normal) ? Number.parseFloat(normal) : null;
}

/** "s" → true, "n" → false, resto → null. */
export function simNao(v: Entrada): boolean | null {
  if (typeof v !== "string") return null;
  const s = v.trim().toLowerCase();
  if (s === "s") return true;
  if (s === "n") return false;
  return null;
}

/** simNao como 0/1 para SQLite. */
export function simNao01(v: Entrada): 0 | 1 | null {
  const b = simNao(v);
  return b === null ? null : b ? 1 : 0;
}

/** Percentual: prefere a versão precisa (`...n`), cai na arredondada. */
export function pctN(precisa: Entrada, arredondada?: Entrada): number | null {
  return numBR(precisa) ?? numBR(arredondada);
}

/** "" / undefined → null; senão a string aparada. */
export function texto(v: Entrada): string | null {
  if (v === null || v === undefined) return null;
  const s = String(v).trim();
  return s === "" ? null : s;
}
