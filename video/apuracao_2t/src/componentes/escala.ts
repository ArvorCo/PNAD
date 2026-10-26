import { interpolateColors } from "remotion";
import { COR } from "../tema";

const NEUTRO = "#1b2a4d";

export const NEUTRO_ESCALA = NEUTRO;

/**
 * Cor de um valor entre `-dominio` (cor `baixa`, Lula por padrão) e `+dominio` (cor `alta`,
 * Flávio por padrão); fora do domínio satura.
 */
export const corDivergente = (valor: number, dominio: number, baixa: string = COR.lula, alta: string = COR.flavio): string => {
  const v = Math.max(-dominio, Math.min(dominio, valor));
  return interpolateColors(v, [-dominio, 0, dominio], [baixa, NEUTRO, alta]);
};

/** Cor de um valor de `minimo` a `maximo`, do fundo da marca ao verde-água claro. */
export const corSequencial = (valor: number, minimo: number, maximo: number): string => {
  const v = Math.max(minimo, Math.min(maximo, valor));
  return interpolateColors(v, [minimo, maximo], [NEUTRO, COR.tealClaro]);
};
