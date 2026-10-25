// Espera com alvo configurável e modo vigília: o telão fica na espera até chegar uma versão
// nova do TSE (mais seções nacionais ou em qualquer UF, ou nova hora de totalização).

import { dezessete, horaCurta } from "../data/format.ts";
import type { Estado } from "../state/types.ts";

export const CHAVE_RETOMADA = "apuracao.vigilia.retomada";
export const ALVO_VIGILIA_PADRAO = "19:00";

/** Alvo do hash (`19:00` de hoje em Brasília, ou ISO) em ms epoch; null sem alvo ou inválido. */
export function resolverAlvo(alvo: string | null, agora: Date): number | null {
  if (!alvo) return null;
  const txt = alvo.trim().replace(/ /g, "+");
  const hm = /^(\d{1,2}):(\d{2})$/.exec(txt);
  if (hm) {
    const h = Number(hm[1]);
    const m = Number(hm[2]);
    if (h > 23 || m > 59) return null;
    const base = dezessete(agora).getTime() - 17 * 3_600_000;
    return base + (h * 60 + m) * 60_000;
  }
  const t = Date.parse(txt);
  return Number.isNaN(t) ? null : t;
}

/** Hora de Brasília do alvo, "19:00". */
export const horaDoAlvo = (alvo: number): string => horaCurta(alvo);

export interface Base {
  st: number;
  dtHt: string | null;
  ufs: Record<string, number>;
}

export function baseDe(e: Estado): Base {
  return { st: e.br.st, dtHt: e.br.dt_ht, ufs: Object.fromEntries(e.ufs.map(u => [u.uf.toUpperCase(), u.st])) };
}

/** Seções novas desde a base se houve versão nova do TSE; null se nada mudou. */
export function versaoNova(base: Base, e: Estado): number | null {
  const ufsMaiores = e.ufs.filter(u => u.st > (base.ufs[u.uf.toUpperCase()] ?? 0));
  const mudouHora = e.br.dt_ht !== base.dtHt && e.br.dt_ht !== null;
  if (e.br.st <= base.st && ufsMaiores.length === 0 && !mudouHora) return null;
  const porUf = e.ufs.reduce((a, u) => a + Math.max(0, u.st - (base.ufs[u.uf.toUpperCase()] ?? 0)), 0);
  return Math.max(0, e.br.st - base.st, porUf);
}

export interface Retomada {
  em: string;
  hora: string;
  novas: number;
}

export function registrarRetomada(r: Retomada): void {
  try {
    localStorage.setItem(CHAVE_RETOMADA, JSON.stringify(r));
  } catch {
    // armazenamento indisponível: o ticker já avisou
  }
}

export function lerRetomada(): Retomada | null {
  try {
    const x: unknown = JSON.parse(localStorage.getItem(CHAVE_RETOMADA) ?? "null");
    if (typeof x === "object" && x !== null) {
      const r = x as Record<string, unknown>;
      if (typeof r.em === "string" && typeof r.hora === "string" && typeof r.novas === "number") return { em: r.em, hora: r.hora, novas: r.novas };
    }
  } catch {
    return null;
  }
  return null;
}

export const textoRetomada = (hora: string, novas: number): string =>
  `divulgação retomada às ${hora}: ${novas} ${novas === 1 ? "seção nova" : "seções novas"}`;
