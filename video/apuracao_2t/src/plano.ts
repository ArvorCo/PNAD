import { VOZ } from "./dados";
import {
  FPS,
  montarCenas,
  quadrosNarrados,
  suavizar,
  trechosDosCapitulos,
  type CenaLinha,
  type TrechoCapitulo,
} from "./linha";
import { ORDEM, type CapituloId, type CenaId } from "./ordem";
import type { Palavra } from "./tipos";

export { FPS };

export type Cena = CenaLinha & { id: CenaId; capitulo: CapituloId };

/** Cenas com início e duração em quadros. Lança erro legível se voz.json fugir da ordem. */
export const CENAS = montarCenas(VOZ, ORDEM) as Cena[];

export const TOTAL_FRAMES = CENAS.reduce((soma, c) => soma + c.frames, 0);

export type TrechoPlano = TrechoCapitulo & { id: CapituloId };

/** Início e extensão de cada capítulo, para o HUD e a trilha. */
export const CAPITULOS_PLANO = trechosDosCapitulos(CENAS) as TrechoPlano[];

/** 1 em cada quadro com palavra sendo dita (folga de 0,25 s), para o ducking da trilha. */
export const NARRANDO = quadrosNarrados(CENAS, TOTAL_FRAMES);

/** `NARRANDO` em média móvel de ±8 quadros: 0 em silêncio, 1 em fala contínua. */
export const NARRANDO_SUAVE = suavizar(NARRANDO, 8);

export const duracaoSegundos = (): number => TOTAL_FRAMES / FPS;

export const cenaPorId = (id: CenaId): Cena => {
  const cena = CENAS.find((c) => c.id === id);
  if (!cena) {
    throw new Error(`cena sem plano: ${id}`);
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
 * Índice da primeira palavra, a partir de `aPartirDe`, que começa com `texto` (sem acento nem
 * pontuação). Devolve -1 se não achar.
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

/** Quadro (relativo à cena) em que a narração chega a uma palavra; `null` se não aparece. */
export const quadroDa = (palavras: Palavra[], texto: string, aPartirDe = 0): number | null => {
  const i = indiceDa(palavras, texto, aPartirDe);
  return i < 0 ? null : Math.round(palavras[i].t * FPS);
};

/** Mesmo que `quadroDa`, com reserva em segundos quando a palavra não aparece. */
export const quadro = (palavras: Palavra[], texto: string, reservaSegundos: number, aPartirDe = 0): number =>
  quadroDa(palavras, texto, aPartirDe) ?? Math.round(reservaSegundos * FPS);

export type Gatilhos = Record<string, number>;

/**
 * Resolve gatilhos `nome → [palavra, reserva em segundos]` em busca sequencial: cada palavra é
 * procurada depois da anterior encontrada, como nos critérios do vídeo dos fiscais. Palavra
 * ausente usa a reserva e não move o cursor.
 */
export const resolverGatilhos = (
  palavras: Palavra[],
  definicao: Record<string, readonly [palavra: string, reservaSegundos: number]> = {},
): Gatilhos => {
  const saida: Gatilhos = {};
  let cursor = 0;
  for (const [nome, [palavra, reserva]] of Object.entries(definicao)) {
    const i = indiceDa(palavras, palavra, cursor);
    if (i >= 0) {
      saida[nome] = Math.round(palavras[i].t * FPS);
      cursor = i + 1;
    } else {
      saida[nome] = Math.round(reserva * FPS);
    }
  }
  return saida;
};
