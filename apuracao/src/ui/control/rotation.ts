// Rotação da playlist: expansão de $destaque, dwell, pausa e modo manual.
// Enquanto nenhuma seção foi totalizada no país, o automático fica na tela de espera.

import { apuracaoComecou, ufsPorEleitorado } from "../state/selectors.ts";
import type { Config, Estado, ItemPlaylist, Playlist, State } from "../state/types.ts";
import type { Store } from "../state/store.ts";

export interface Entrada {
  v: string;
  uf: string | null;
  mun: string | null;
  dwellMs: number;
}

export const PLAYLIST_PADRAO: Playlist = {
  dwell: 20,
  itens: [
    { v: "pres", dwell: 25 },
    { v: "pres-uf", uf: "$destaque", max: 4 },
    { v: "gov" },
    { v: "sen" },
    { v: "ritmo" },
    { v: "mov" },
    { v: "fed-uf", uf: "SP" },
  ],
};

/** Aceita playlist como {dwell, itens, destaque} ou lista; cada item com `v` ou `view`. */
export function normalizarPlaylist(bruto: unknown): Playlist {
  const obj = !Array.isArray(bruto) && typeof bruto === "object" && bruto !== null ? (bruto as Record<string, unknown>) : null;
  const lista: unknown = Array.isArray(bruto) ? bruto : (obj?.itens ?? obj?.telas);
  if (!Array.isArray(lista)) return PLAYLIST_PADRAO;
  const itens: ItemPlaylist[] = [];
  for (const x of lista) {
    const r: Record<string, unknown> = typeof x === "string" ? { v: x } : typeof x === "object" && x !== null ? (x as Record<string, unknown>) : {};
    const v = r.v ?? r.view;
    if (typeof v !== "string") continue;
    itens.push({
      v,
      ...(typeof r.uf === "string" ? { uf: r.uf } : {}),
      ...(typeof r.mun === "string" ? { mun: r.mun } : {}),
      ...(typeof r.dwell === "number" && r.dwell > 0 ? { dwell: r.dwell } : {}),
      ...(typeof r.max === "number" && r.max > 0 ? { max: r.max } : {}),
    });
  }
  if (itens.length === 0) return PLAYLIST_PADRAO;
  const destaque = Array.isArray(obj?.destaque) ? obj.destaque.filter((u): u is string => typeof u === "string").map(u => u.toUpperCase()) : [];
  const dwell = typeof obj?.dwell === "number" && obj.dwell > 0 ? obj.dwell : PLAYLIST_PADRAO.dwell;
  return { dwell, itens, ...(destaque.length > 0 ? { destaque } : {}) };
}

/**
 * Expande a playlist no estado atual. $destaque vira as UFs com pst ≥ 5, na ordem da lista
 * `destaque` da playlist ou, sem ela, por eleitorado; `max` limita quantas entram.
 */
export function expandirPlaylist(pl: Playlist, estado: Estado | null, config: Config | null, dwellFixo: number | null): Entrada[] {
  const saida: Entrada[] = [];
  const pst = new Map((estado?.ufs ?? []).map(u => [u.uf.toUpperCase(), u.pst]));
  const ufs = pl.destaque ?? ufsPorEleitorado(config?.ufs ?? []).map(u => u.uf.toUpperCase());
  for (const it of pl.itens) {
    const dwellMs = 1000 * (dwellFixo ?? it.dwell ?? pl.dwell);
    if (it.v === "espera") continue;
    if (it.uf === "$destaque") {
      // Destaque com pelo menos 5% apurado; se sobrarem menos de 4 (começo da noite, quando
      // SP, RJ e o Nordeste ainda estão em zero), completa com as UFs mais adiantadas.
      const minimo = Math.min(4, it.max ?? 4);
      const escolhidas = ufs.filter(u => (pst.get(u) ?? 0) >= 5).slice(0, it.max ?? ufs.length);
      if (escolhidas.length < minimo) {
        const adiantadas = [...pst.entries()]
          .filter(([u, p]) => u !== "ZZ" && p >= 1 && !escolhidas.includes(u))
          .sort((a, b) => b[1] - a[1])
          .map(([u]) => u);
        for (const u of adiantadas) {
          if (escolhidas.length >= minimo) break;
          escolhidas.push(u);
        }
      }
      for (const uf of escolhidas) saida.push({ v: it.v, uf, mun: null, dwellMs });
      continue;
    }
    saida.push({ v: it.v, uf: it.uf ? it.uf.toUpperCase() : null, mun: it.mun ?? null, dwellMs });
  }
  return saida;
}

export const proximoIndice = (i: number, n: number, passo: 1 | -1): number => (n <= 0 ? 0 : (((i + passo) % n) + n) % n);

export interface Rotacao {
  entradas(): Entrada[];
  proxima(manual: boolean): void;
  anterior(): void;
  pausar(valor?: boolean): void;
  /** Reinicia o relógio da tela atual (troca manual ou dwell novo). */
  reiniciarDwell(): void;
  parar(): void;
}

export interface OpcoesRotacao {
  store: Store;
  aplicar(e: Entrada, indice: number): void;
  espera(): void;
}

export function criarRotacao(o: OpcoesRotacao): Rotacao {
  const { store } = o;
  let restanteMs: number | null = null; // tempo que faltava quando pausou
  let estavaEsperando = false;

  const entradas = (): Entrada[] => {
    const s: State = store.get();
    return expandirPlaylist(s.playlist, s.estado, s.config, s.ui.dwell);
  };

  const ir = (indice: number): void => {
    const lista = entradas();
    const e = lista[indice];
    if (!e) return;
    restanteMs = null;
    store.ui({ indice, dwellInicio: performance.now(), dwellMs: e.dwellMs, pausado: false });
    o.aplicar(e, indice);
  };

  const proxima = (manual: boolean): void => {
    const lista = entradas();
    if (lista.length === 0) return;
    if (manual) store.ui({ auto: false });
    ir(proximoIndice(store.get().ui.indice, lista.length, 1));
  };

  const tick = (): void => {
    const s = store.get();
    const comecou = apuracaoComecou(s.estado);
    if (s.ui.auto && !comecou) {
      // Sem seção totalizada no país: espera, com rotação parada.
      if (s.ui.v !== "espera") o.espera();
      estavaEsperando = true;
      return;
    }
    if (s.ui.auto && estavaEsperando && comecou) {
      estavaEsperando = false;
      ir(0);
      return;
    }
    if (!s.ui.auto || s.ui.pausado || s.ui.paleta) return;
    if (performance.now() - s.ui.dwellInicio >= s.ui.dwellMs) proxima(false);
  };

  const timer = setInterval(tick, 250);
  queueMicrotask(tick);

  return {
    entradas,
    proxima,
    anterior() {
      const lista = entradas();
      if (lista.length === 0) return;
      store.ui({ auto: false });
      ir(proximoIndice(store.get().ui.indice, lista.length, -1));
    },
    pausar(valor) {
      const ui = store.get().ui;
      const pausar = valor ?? !ui.pausado;
      if (pausar === ui.pausado) return;
      if (pausar) {
        restanteMs = Math.max(0, ui.dwellMs - (performance.now() - ui.dwellInicio));
        store.ui({ pausado: true });
      } else {
        const resto = restanteMs ?? ui.dwellMs;
        restanteMs = null;
        store.ui({ pausado: false, dwellInicio: performance.now() - (ui.dwellMs - resto) });
      }
    },
    reiniciarDwell() {
      const s = store.get();
      const e = entradas()[s.ui.indice];
      restanteMs = null;
      store.ui({ dwellInicio: performance.now(), dwellMs: e ? e.dwellMs : 1000 * (s.ui.dwell ?? s.playlist.dwell) });
    },
    parar: () => clearInterval(timer),
  };
}
