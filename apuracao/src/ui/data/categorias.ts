// Categorias de anomalia do telão: rótulo, cor e prioridade. Cores testadas sobre papel
// (#f4f0e6) e sobre branco com contraste mínimo de 4,5:1 para texto pequeno.

import type { Anomalia } from "../state/types.ts";

export type Categoria = Anomalia["tipo"];

/** Ordem de exibição dos contadores: do que mais pede atenção para o que só informa. */
export const CATEGORIAS: readonly Categoria[] = ["divergencia", "pausa", "atraso", "abstencao", "paralela", "virada", "regressao", "fechou"];

export const ROTULO_CATEGORIA: Readonly<Record<Categoria, string>> = {
  divergencia: "divergência",
  pausa: "pausa",
  atraso: "atraso",
  abstencao: "abstenção",
  paralela: "paralela",
  virada: "virada",
  regressao: "regressão",
  fechou: "encerrou",
};

/** Cor de texto e de marca de cada categoria (todas com 4,5:1 ou mais sobre o papel e o branco). */
export const COR_CATEGORIA: Readonly<Record<Categoria, string>> = {
  divergencia: "#a8281c",
  pausa: "#24627f",
  atraso: "#8f4a14",
  abstencao: "#6b4a92",
  paralela: "#0b6e55",
  virada: "#192e2b",
  regressao: "#9a3f6b",
  fechou: "#535b54",
};

export const NOVAS_CATEGORIAS: ReadonlySet<Categoria> = new Set<Categoria>(["pausa", "divergencia", "abstencao", "paralela"]);

export const ehCategoria = (x: unknown): x is Categoria => typeof x === "string" && (CATEGORIAS as readonly string[]).includes(x);

const PESO_SEVERIDADE: Readonly<Record<string, number>> = { error: 3, warn: 2, info: 1 };

/** Contagem por categoria sobre uma lista de anomalias. Todas as categorias aparecem, mesmo com zero. */
export function contarPorCategoria(lista: readonly Pick<Anomalia, "tipo">[]): Record<Categoria, number> {
  const c = Object.fromEntries(CATEGORIAS.map(k => [k, 0])) as Record<Categoria, number>;
  for (const a of lista) c[a.tipo] += 1;
  return c;
}

/** As `n` anomalias mais recentes (instante decrescente; empate pela maior severidade). */
export function maisRecentes<T extends Pick<Anomalia, "at" | "severidade">>(lista: readonly T[], n: number): T[] {
  return [...lista]
    .sort((a, b) => b.at.localeCompare(a.at) || (PESO_SEVERIDADE[b.severidade ?? "info"] ?? 1) - (PESO_SEVERIDADE[a.severidade ?? "info"] ?? 1))
    .slice(0, n);
}
