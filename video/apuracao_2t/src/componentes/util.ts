import { interpolate, spring } from "remotion";

/** Formata inteiro em pt-BR: 13045 → "13.045". */
export const inteiro = (n: number): string => {
  const s = Math.round(Math.abs(n)).toString();
  const partes: string[] = [];
  for (let i = s.length; i > 0; i -= 3) {
    partes.unshift(s.slice(Math.max(0, i - 3), i));
  }
  return (n < 0 ? "-" : "") + partes.join(".");
};

/** Formata decimal em pt-BR com `casas` casas: 24.69 → "24,7". */
export const decimal = (n: number, casas = 1): string => {
  const [a, b] = Math.abs(n).toFixed(casas).split(".");
  return (n < 0 ? "-" : "") + inteiro(Number(a)) + (b ? "," + b : "");
};

/** Hora "HH:MM" de um carimbo "AAAA-MM-DD HH:MM:SS". */
export const hora = (carimbo: string): string => carimbo.slice(11, 16);

/** Progresso 0..1 com mola, a partir de um quadro de início. */
export const mola = (
  frame: number,
  fps: number,
  inicio: number,
  config: { damping?: number; stiffness?: number; mass?: number } = {},
): number =>
  spring({
    frame: frame - inicio,
    fps,
    config: { damping: 14, stiffness: 120, mass: 0.8, ...config },
  });

/** Progresso linear 0..1 entre dois quadros, com clamp. */
export const rampa = (frame: number, de: number, ate: number): number =>
  interpolate(frame, [de, ate], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

/** Ease out cúbico. */
export const suave = (t: number): number => 1 - Math.pow(1 - t, 3);

/** Pseudoaleatório determinístico em [0, 1) a partir de um inteiro. */
export const ruido = (semente: number): number => {
  const x = Math.sin(semente * 127.1 + 311.7) * 43758.5453;
  return x - Math.floor(x);
};
