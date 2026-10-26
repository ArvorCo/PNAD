// Linha do tempo pura: transforma o manifesto da voz em cenas com início e duração em quadros.
// Sem importação de valores, para servir ao Remotion (via plano.ts) e ao `node src/verificar.ts`.
import type { CenaVoz, Voz } from "./tipos";

export const FPS = 30;
/** Silêncio depois de cada cena, em segundos, para a imagem respirar. */
export const RESPIRO = 0.9;
/** Cauda final, depois da última frase. */
export const CAUDA = 3.0;
/** Duração provisória de cada cena enquanto a voz não foi gerada. */
export const SEGUNDOS_SEM_VOZ = 6;

/** Portão de duração (CONTRATO.md): 9:30 a 11:00, de 570 a 660 s. */
export const PORTAO = { minimo: 570, maximo: 660 } as const;

type ItemOrdem = { readonly id: string; readonly capitulo: string };

export type CenaLinha = CenaVoz & {
  capitulo: string;
  inicio: number;
  frames: number;
  /** Falso quando a cena foi sintetizada sem voz (voz.json vazio): sem áudio, sem legenda. */
  comVoz: boolean;
};

export type TrechoCapitulo = { id: string; inicio: number; frames: number };

/** Diferenças entre os ids da voz e a ordem do contrato, em texto legível; vazio se iguais. */
export const diferencasDeOrdem = (ids: readonly string[], ordem: readonly ItemOrdem[]): string[] => {
  const esperado = ordem.map((c) => c.id);
  const faltam = esperado.filter((id) => !ids.includes(id));
  const sobram = ids.filter((id) => !esperado.includes(id));
  const erros: string[] = [];
  if (faltam.length) {
    erros.push(`faltam na voz: ${faltam.join(", ")}`);
  }
  if (sobram.length) {
    erros.push(`fora da ordem do contrato: ${sobram.join(", ")}`);
  }
  if (!erros.length) {
    const primeira = esperado.findIndex((id, i) => ids[i] !== id);
    if (primeira >= 0) {
      erros.push(`ordem trocada a partir da posição ${primeira + 1}: esperado ${esperado[primeira]}, veio ${ids[primeira]}`);
    }
  }
  return erros;
};

/**
 * Cenas na ordem do contrato. Com voz.json vazio, cada cena ganha `SEGUNDOS_SEM_VOZ` e nenhuma
 * palavra, para o estúdio abrir com placeholders; com voz, os ids precisam bater com a ordem.
 */
export const montarCenas = (voz: Voz, ordem: readonly ItemOrdem[]): CenaLinha[] => {
  const comVoz = voz.cenas.length > 0;
  if (comVoz) {
    const erros = diferencasDeOrdem(
      voz.cenas.map((c) => c.id),
      ordem,
    );
    if (erros.length) {
      throw new Error(
        `src/dados/voz.json não segue a ordem de src/ordem.ts (${erros.join("; ")}). ` +
          "Regere a voz com scripts/video-apuracao-2t-voz.py ou corrija o roteiro.",
      );
    }
  }
  const base: CenaVoz[] = comVoz
    ? voz.cenas
    : ordem.map((c) => ({ id: c.id, arquivo: "", segundos: SEGUNDOS_SEM_VOZ, texto: "", palavras: [] }));
  let cursor = 0;
  return base.map((c, i) => {
    const ultima = i === base.length - 1;
    const frames = Math.round((c.segundos + (ultima ? CAUDA : RESPIRO)) * FPS);
    const cena = { ...c, capitulo: ordem[i].capitulo, inicio: cursor, frames, comVoz };
    cursor += frames;
    return cena;
  });
};

/** Trecho contínuo de cada capítulo, na ordem em que aparece. */
export const trechosDosCapitulos = (cenas: readonly CenaLinha[]): TrechoCapitulo[] => {
  const saida: TrechoCapitulo[] = [];
  for (const c of cenas) {
    const ultimo = saida[saida.length - 1];
    if (ultimo && ultimo.id === c.capitulo) {
      ultimo.frames += c.frames;
    } else {
      saida.push({ id: c.capitulo, inicio: c.inicio, frames: c.frames });
    }
  }
  return saida;
};

/** 1 nos quadros em que alguma palavra está sendo dita (com folga), 0 no silêncio. */
export const quadrosNarrados = (cenas: readonly CenaLinha[], total: number, folgaSegundos = 0.25): Uint8Array => {
  const saida = new Uint8Array(total);
  for (const c of cenas) {
    const fimCena = Math.min(total, c.inicio + c.frames);
    for (const p of c.palavras) {
      const de = Math.max(c.inicio, c.inicio + Math.floor((p.t - folgaSegundos) * FPS));
      const ate = Math.min(fimCena, c.inicio + Math.ceil((p.f + folgaSegundos) * FPS));
      saida.fill(1, de, Math.max(de, ate));
    }
  }
  return saida;
};

/** Média móvel de ±raio quadros sobre o vetor de narração, para o ducking não bater em degrau. */
export const suavizar = (vetor: Uint8Array, raio: number): Float32Array => {
  const n = vetor.length;
  const acumulado = new Float64Array(n + 1);
  for (let i = 0; i < n; i++) {
    acumulado[i + 1] = acumulado[i] + vetor[i];
  }
  const saida = new Float32Array(n);
  for (let i = 0; i < n; i++) {
    const de = Math.max(0, i - raio);
    const ate = Math.min(n, i + raio + 1);
    saida[i] = (acumulado[ate] - acumulado[de]) / (ate - de);
  }
  return saida;
};

export const mmss = (segundos: number): string => {
  const s = Math.round(segundos);
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
};

export type Veredito = "OK" | "CURTO" | "LONGO";

export const veredito = (segundos: number): Veredito => {
  if (segundos > PORTAO.maximo) {
    return "LONGO";
  }
  return segundos >= PORTAO.minimo ? "OK" : "CURTO";
};
