// Datas do TSE (dd/mm/aaaa + hh:mm:ss, horário de Brasília sem verão) em ISO UTC.

const RE_DATA = /^(\d{2})\/(\d{2})\/(\d{4})$/;
const RE_HORA = /^(\d{2}):(\d{2}):(\d{2})$/;
const OFFSET_H = 3; // -03:00 fixo

export function dgHgToUtcIso(dg: string | null | undefined, hg: string | null | undefined): string | null {
  if (!dg || !hg) return null;
  const d = RE_DATA.exec(dg.trim());
  const h = RE_HORA.exec(hg.trim());
  if (!d || !h) return null;
  const ms = Date.UTC(Number(d[3]), Number(d[2]) - 1, Number(d[1]), Number(h[1]) + OFFSET_H, Number(h[2]), Number(h[3]));
  return Number.isFinite(ms) ? new Date(ms).toISOString() : null;
}

export function nowIso(): string {
  return new Date().toISOString();
}

/** a − b em milissegundos; null se qualquer lado faltar ou for inválido. */
export function isoDiffMs(a: string | null | undefined, b: string | null | undefined): number | null {
  if (!a || !b) return null;
  const ta = Date.parse(a);
  const tb = Date.parse(b);
  return Number.isFinite(ta) && Number.isFinite(tb) ? ta - tb : null;
}
