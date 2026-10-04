// Regras puras de navegação entre telas: cargo por tecla, variante por UF e subida de nível.

import type { UiState } from "../state/types.ts";

export type Destino = Pick<UiState, "v" | "uf" | "mun" | "zonas" | "zona">;

const LIMPO = { mun: null, zonas: false, zona: null } as const;

/** Telas nacionais e suas variantes por UF. */
const POR_UF: Readonly<Record<string, string>> = {
  pres: "pres-uf",
  gov: "gov-uf",
  sen: "sen-uf",
  "pres-uf": "pres-uf",
  "gov-uf": "gov-uf",
  "sen-uf": "sen-uf",
  "fed-uf": "fed-uf",
  "est-uf": "est-uf",
  mun: "pres-uf",
  ritmo: "pres-uf",
  mov: "pres-uf",
  espera: "pres-uf",
};

const ACIMA: Readonly<Record<string, string>> = {
  "pres-uf": "pres",
  "gov-uf": "gov",
  "sen-uf": "sen",
  "fed-uf": "gov",
  "est-uf": "gov",
  "dis-df": "gov",
};

/** Tecla de cargo (códigos do TSE) mais 9 ritmo e 0 movimento. */
export function destinoDoDigito(d: string, ufAtual: string | null): Destino | null {
  switch (d) {
    case "1":
      return { v: "pres", uf: null, ...LIMPO };
    case "3":
      return { v: "gov", uf: null, ...LIMPO };
    case "5":
      return { v: "sen", uf: null, ...LIMPO };
    case "6":
      return { v: "fed-uf", uf: ufAtual && ufAtual !== "DF" ? ufAtual : "SP", ...LIMPO };
    case "7":
      return { v: ufAtual === "DF" ? "dis-df" : "est-uf", uf: ufAtual ?? "SP", ...LIMPO };
    case "8":
      return { v: "dis-df", uf: "DF", ...LIMPO };
    case "9":
      return { v: "ritmo", uf: null, ...LIMPO };
    case "0":
      return { v: "mov", uf: null, ...LIMPO };
    default:
      return null;
  }
}

/** Mesma família de tela, recortada para a UF. Deputado estadual no DF vira distrital. */
export function destinoDaUf(v: string, uf: string): Destino {
  const u = uf.toUpperCase();
  if (v === "est-uf" && u === "DF") return { v: "dis-df", uf: u, ...LIMPO };
  if (v === "dis-df") return { v: u === "DF" ? "dis-df" : "est-uf", uf: u, ...LIMPO };
  if (v === "fed-uf" || v === "est-uf") return { v, uf: u, ...LIMPO };
  return { v: POR_UF[v] ?? "pres-uf", uf: u, ...LIMPO };
}

/** Backspace: zona → zonas → município → UF → país. Devolve null quando já está no topo. */
export function subirNivel(ui: Destino): Destino | null {
  if (ui.v === "mun") {
    if (ui.zona) return { ...ui, zona: null };
    if (ui.zonas) return { ...ui, zonas: false };
    return { v: "pres-uf", uf: ui.uf, ...LIMPO };
  }
  const acima = ACIMA[ui.v];
  return acima ? { v: acima, uf: null, ...LIMPO } : null;
}

const SIGLAS = new Set([
  "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ",
  "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO",
]);

export const ehUf = (s: string): boolean => SIGLAS.has(s.toUpperCase());

/** Acumulador de duas letras em 900 ms. Devolve a UF quando completa, senão null. */
export function criarLeitorUf(janelaMs = 900): (letra: string, agora: number) => string | null {
  let buffer = "";
  let ultimo = 0;
  return (letra, agora) => {
    if (agora - ultimo > janelaMs) buffer = "";
    ultimo = agora;
    buffer = (buffer + letra.toUpperCase()).slice(-2);
    if (buffer.length === 2 && ehUf(buffer)) {
      const uf = buffer;
      buffer = "";
      return uf;
    }
    return null;
  };
}
