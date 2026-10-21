import { loadFont as loadGrotesk } from "@remotion/google-fonts/SpaceGrotesk";
import { loadFont as loadMono } from "@remotion/google-fonts/JetBrainsMono";

const grotesk = loadGrotesk("normal", {
  weights: ["500", "700"],
  subsets: ["latin", "latin-ext"],
});
const mono = loadMono("normal", {
  weights: ["500", "700"],
  subsets: ["latin", "latin-ext"],
});

export const FONTE = grotesk.fontFamily;
export const MONO = mono.fontFamily;

/** Paleta: azul-noite da Arvor, verde-água da marca, e as cores da casa para os candidatos. */
export const COR = {
  fundo0: "#060b1a",
  fundo1: "#0c1a3a",
  papel: "#f4f0e6",
  tinta: "#eef2ff",
  suave: "#9aa6c4",
  linha: "rgba(154,166,196,0.22)",
  teal: "#2a9ab0",
  tealClaro: "#5fd3e6",
  indigo: "#3b3fa6",
  alta: "#ff5a4e",
  media: "#f5b942",
  baixa: "#6b7a99",
  lula: "#ea6a5c",
  flavio: "#4f8ff0",
  outros: "#2bb98a",
  ouro: "#f0c86b",
  vidro: "rgba(12,26,58,0.72)",
};

export const NIVEL_COR: Record<string, string> = {
  alta: COR.alta,
  media: COR.media,
  baixa: COR.baixa,
};

export const NIVEL_NOME: Record<string, string> = {
  alta: "ALTA",
  media: "MÉDIA",
  baixa: "BAIXA",
};
