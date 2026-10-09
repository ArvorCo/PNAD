import voz from "./dados/voz.json";
import type { CenaVoz, Palavra, Voz } from "./tipos";

export const FPS = 30;
/** Silêncio depois de cada cena, em segundos, para a imagem respirar. */
const RESPIRO = 0.9;
/** Cauda final, depois da última frase. */
const CAUDA = 3.0;

export type Cena = CenaVoz & {
  inicio: number;
  frames: number;
};

const VOZ = voz as Voz;

export const CENAS: Cena[] = (() => {
  let cursor = 0;
  return VOZ.cenas.map((c, i) => {
    const ultima = i === VOZ.cenas.length - 1;
    const frames = Math.round((c.segundos + (ultima ? CAUDA : RESPIRO)) * FPS);
    const cena = { ...c, inicio: cursor, frames };
    cursor += frames;
    return cena;
  });
})();

export const TOTAL_FRAMES = CENAS.reduce((soma, c) => soma + c.frames, 0);

export const cenaPorId = (id: string): Cena => {
  const cena = CENAS.find((c) => c.id === id);
  if (!cena) {
    throw new Error(`cena sem narração: ${id}`);
  }
  return cena;
};

const normalizar = (s: string): string =>
  s
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/[^a-z0-9]/g, "");

/**
 * Quadro (relativo à cena) em que a narração chega a uma palavra. Procura, a partir de
 * `aPartirDe` (índice de palavra), a primeira palavra que começa com `texto`, sem acento
 * nem pontuação. Devolve `null` se não achar: a cena então usa a hipótese de tempo.
 */
export const indiceDa = (palavras: Palavra[], texto: string, aPartirDe = 0): number => {
  const alvo = normalizar(texto);
  for (let i = Math.max(0, aPartirDe); i < palavras.length; i++) {
    if (normalizar(palavras[i].w).startsWith(alvo)) {
      return i;
    }
  }
  return -1;
};

export const quadroDa = (
  palavras: Palavra[],
  texto: string,
  aPartirDe = 0,
): number | null => {
  const i = indiceDa(palavras, texto, aPartirDe);
  return i < 0 ? null : Math.round(palavras[i].t * FPS);
};

/** Mesmo que `quadroDa`, com reserva quando a palavra não aparece. */
export const quadro = (
  palavras: Palavra[],
  texto: string,
  reservaSegundos: number,
  aPartirDe = 0,
): number => quadroDa(palavras, texto, aPartirDe) ?? Math.round(reservaSegundos * FPS);
