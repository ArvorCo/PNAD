// Seletores puros sobre o estado. Nenhum toca o DOM.

import type { Campo, Candidato, ConfigUf, Estado, EstadoUf, Resultado } from "./types.ts";

/** Ordena por votos apurados (desc); empate pelo número de urna. */
export function ranking<T extends { vap: number; n: string }>(cand: readonly T[]): T[] {
  return [...cand].sort((a, b) => b.vap - a.vap || a.n.localeCompare(b.n, "pt-BR", { numeric: true }));
}

export interface Disputa<T> {
  lider: T | null;
  segundo: T | null;
  /** Diferença em pontos percentuais dos válidos entre 1º e 2º (0 sem segundo). */
  margem: number;
  /** Diferença em votos. */
  margemVotos: number;
  /** Empate exato em votos com votos apurados: o mapa não pinta líder. */
  empate: boolean;
}

export function disputa<T extends { vap: number; pvapn: number; n: string }>(cand: readonly T[]): Disputa<T> {
  const r = ranking(cand);
  const lider = r[0] ?? null;
  const segundo = r[1] ?? null;
  if (!lider) return { lider: null, segundo: null, margem: 0, margemVotos: 0, empate: false };
  const margemVotos = lider.vap - (segundo?.vap ?? 0);
  const margem = lider.pvapn - (segundo?.pvapn ?? 0);
  const empate = segundo !== null && lider.vap > 0 && margemVotos === 0;
  const semVoto = lider.vap === 0;
  return { lider: empate || semVoto ? null : lider, segundo, margem, margemVotos, empate };
}

export interface FatiaCampo {
  campo: Campo;
  votos: number;
  pct: number; // 0 a 100 sobre o total agregado
}

const ORDEM_CAMPOS: readonly Campo[] = ["esquerda", "centro-esquerda", "centro", "centro-direita", "direita", "indefinido"];

/** Soma qualquer lista por campo; ordem fixa da esquerda para a direita. */
export function agregarPorCampo<T>(itens: readonly T[], campoDe: (x: T) => Campo, valorDe: (x: T) => number): FatiaCampo[] {
  const soma = new Map<Campo, number>();
  let total = 0;
  for (const x of itens) {
    const v = valorDe(x);
    if (!Number.isFinite(v) || v <= 0) continue;
    const c = campoDe(x);
    soma.set(c, (soma.get(c) ?? 0) + v);
    total += v;
  }
  return ORDEM_CAMPOS.filter(c => soma.has(c)).map(c => {
    const votos = soma.get(c) ?? 0;
    return { campo: c, votos, pct: total > 0 ? (100 * votos) / total : 0 };
  });
}

export const camposDosCandidatos = (cand: readonly Candidato[]): FatiaCampo[] =>
  agregarPorCampo(cand, c => c.campo, c => c.vap);

export interface Composicao {
  validos: number; // 0 a 100 do total de votos
  brancos: number;
  nulos: number;
  total: number;
}

/** Parcelas de válidos, brancos e nulos sobre o total de votos (tv). */
export function composicaoVotos(v: Resultado["v"]): Composicao {
  const total = v.tv;
  if (!(total > 0)) return { validos: 0, brancos: 0, nulos: 0, total: 0 };
  return { validos: (100 * v.vv) / total, brancos: (100 * v.vb) / total, nulos: (100 * v.vn) / total, total };
}

export interface LinhaOutros {
  outros: true;
  quantidade: number;
  vap: number;
  pvapn: number;
}

/** Mantém os `n - 1` primeiros e junta o resto em "outros N" quando a lista passa de `n`. */
export function colapsarOutros<T extends { vap: number; pvapn: number; n: string }>(
  cand: readonly T[],
  n: number,
): (T | LinhaOutros)[] {
  const r = ranking(cand);
  if (r.length <= n) return r;
  const visiveis = r.slice(0, Math.max(0, n - 1));
  const resto = r.slice(Math.max(0, n - 1));
  const linha: LinhaOutros = {
    outros: true,
    quantidade: resto.length,
    vap: resto.reduce((s, c) => s + c.vap, 0),
    pvapn: resto.reduce((s, c) => s + c.pvapn, 0),
  };
  return [...visiveis, linha];
}

export const ehOutros = (x: object): x is LinhaOutros => "outros" in x;

export const rotuloOutros = (l: LinhaOutros): string => `outros ${l.quantidade}`;

/** UFs ordenadas por eleitorado (desc), empate pela sigla. */
export function ufsPorEleitorado<T extends Pick<ConfigUf, "uf" | "te">>(ufs: readonly T[]): T[] {
  return [...ufs].sort((a, b) => b.te - a.te || a.uf.localeCompare(b.uf));
}

/** Estado das UFs na ordem do eleitorado da configuração. */
export function estadoUfsOrdenado(estado: Estado | null, ufs: readonly ConfigUf[]): EstadoUf[] {
  if (!estado) return [];
  const porUf = new Map(estado.ufs.map(u => [u.uf.toUpperCase(), u]));
  const saida: EstadoUf[] = [];
  for (const u of ufsPorEleitorado(ufs)) {
    const e = porUf.get(u.uf.toUpperCase());
    if (e) saida.push(e);
  }
  return saida;
}

/** Percentual de seções totalizadas de uma UF (0 sem dado). */
export function pstUf(estado: Estado | null, uf: string): number {
  return estado?.ufs.find(u => u.uf.toUpperCase() === uf.toUpperCase())?.pst ?? 0;
}

/** Há alguma seção totalizada no país? Antes disso, o telão fica em espera. */
export const apuracaoComecou = (estado: Estado | null): boolean => (estado?.br.st ?? 0) > 0;
