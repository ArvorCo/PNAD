// Estado único do telão. `patch` troca um ramo por cópia estrutural (as referências
// dos ramos intocados ficam iguais) e devolve o diff das folhas numéricas alteradas,
// que as telas usam para count-up e para o sublinhado lime.

import type { Diff, DiffItem, State, UiState } from "./types.ts";

export type Ouvinte = (state: State, diff: Diff) => void;
export type Caminho = string | readonly string[];

const CHAVES_ID = ["sqcand", "uf", "cd", "sg"] as const;

type Registro = Record<string, unknown>;

const ehRegistro = (x: unknown): x is Registro => typeof x === "object" && x !== null && !Array.isArray(x);

function idDe(x: unknown): string | null {
  if (!ehRegistro(x)) return null;
  for (const k of CHAVES_ID) {
    const v = x[k];
    if (typeof v === "string" || typeof v === "number") return `${k}=${v}`;
  }
  return null;
}

/** Lista as folhas numéricas que mudaram entre `de` e `para`. Arrays de objetos com id são casados pelo id. */
export function diffNumerico(de: unknown, para: unknown, prefixo = "", saida: DiffItem[] = []): DiffItem[] {
  if (de === para) return saida;
  if (typeof para === "number") {
    if (typeof de === "number" && de !== para && Number.isFinite(de) && Number.isFinite(para)) {
      saida.push({ path: prefixo, de, para });
    }
    return saida;
  }
  if (Array.isArray(para)) {
    const antes = Array.isArray(de) ? de : [];
    const porId = new Map<string, unknown>();
    for (const item of antes) {
      const id = idDe(item);
      if (id !== null) porId.set(id, item);
    }
    para.forEach((item, i) => {
      const id = idDe(item);
      const anterior = id !== null ? porId.get(id) : antes[i];
      diffNumerico(anterior, item, `${prefixo}[${id ?? i}]`, saida);
    });
    return saida;
  }
  if (ehRegistro(para)) {
    const antes = ehRegistro(de) ? de : {};
    for (const k of Object.keys(para)) {
      diffNumerico(antes[k], para[k], prefixo ? `${prefixo}.${k}` : k, saida);
    }
  }
  return saida;
}

export function partesDoCaminho(caminho: Caminho): string[] {
  return typeof caminho === "string" ? caminho.split(".").filter(Boolean) : [...caminho];
}

/** Atribuição imutável: devolve uma raiz nova com o valor no caminho. */
export function atribuir<T>(raiz: T, partes: readonly string[], valor: unknown): T {
  if (partes.length === 0) return valor as T;
  const [cabeca, ...resto] = partes as [string, ...string[]];
  const base: Registro = ehRegistro(raiz) ? raiz : {};
  return { ...base, [cabeca]: atribuir(base[cabeca], resto, valor) } as T;
}

export function ler(raiz: unknown, partes: readonly string[]): unknown {
  let atual: unknown = raiz;
  for (const p of partes) {
    if (!ehRegistro(atual)) return undefined;
    atual = atual[p];
  }
  return atual;
}

export interface Store {
  get(): State;
  subscribe(fn: Ouvinte): () => void;
  /** Troca o valor no caminho ("resultados.6257:1:br" ou ["resultados", "6257:1:br"]). */
  patch(caminho: Caminho, valor: unknown): Diff;
  /** Mescla campos de `ui` (atalho para o roteador e o teclado). */
  ui(parcial: Partial<UiState>): void;
}

export function criarStore(inicial: State): Store {
  let state = inicial;
  const ouvintes = new Set<Ouvinte>();
  let pendente: DiffItem[] = [];
  let agendado = false;

  const emitir = (): void => {
    agendado = false;
    const diff = pendente;
    pendente = [];
    for (const fn of ouvintes) fn(state, diff);
  };

  const agendar = (diff: Diff): void => {
    pendente.push(...diff);
    if (agendado) return;
    agendado = true;
    queueMicrotask(emitir);
  };

  return {
    get: () => state,
    subscribe(fn) {
      ouvintes.add(fn);
      return () => {
        ouvintes.delete(fn);
      };
    },
    patch(caminho, valor) {
      const partes = partesDoCaminho(caminho);
      const antes = ler(state, partes);
      if (antes === valor) return [];
      const diff = diffNumerico(antes, valor, partes.join("."));
      state = atribuir(state, partes, valor);
      agendar(diff);
      return diff;
    },
    ui(parcial) {
      const atual = state.ui;
      let mudou = false;
      for (const k of Object.keys(parcial) as (keyof UiState)[]) {
        if (atual[k] !== parcial[k]) mudou = true;
      }
      if (!mudou) return;
      state = { ...state, ui: { ...atual, ...parcial } };
      agendar([]);
    },
  };
}
