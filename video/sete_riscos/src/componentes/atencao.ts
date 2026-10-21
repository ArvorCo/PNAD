import { COR } from "../tema";

/** Os quatro níveis de atenção dos logs (0 a 3), na ordem do mapa de fiscais. */
export const NIVEIS_ATENCAO = [0, 1, 2, 3] as const;
export type NivelAtencao = (typeof NIVEIS_ATENCAO)[number];

/**
 * Cor de cada nível, na mesma ordem da legenda do mapa de fiscais: rotina vazado, um sinal em
 * verde-água claro, sinais combinados em verde-água, conferir o arquivo em roxo.
 */
export const ATENCAO_COR: Record<NivelAtencao, string> = {
  0: COR.suave,
  1: COR.tealClaro,
  2: COR.teal,
  3: "#a77bff",
};

const NOME: Record<NivelAtencao, string> = {
  0: "Registro de rotina",
  1: "Um sinal",
  2: "Sinais combinados",
  3: "Conferir o arquivo",
};

/** Nome do nível como o mapa de fiscais publica na legenda. */
export const nomeAtencao = (nivel: NivelAtencao): string => NOME[nivel];

export const comoNivel = (n: number | null | undefined): NivelAtencao | null =>
  n === 0 || n === 1 || n === 2 || n === 3 ? n : null;
