// Chips de estado junto do título e nas linhas: rótulos em caixa normal, sem travessão.

import { pct } from "../data/format.ts";

export type TipoChip = "parcial" | "encerrada" | "subjudice" | "eleito" | "segundo" | "primeiro" | "atraso" | "aviso" | "neutro";

export function chip(texto: string, tipo: TipoChip = "neutro"): HTMLSpanElement {
  const s = document.createElement("span");
  s.className = `chip chip--${tipo}`;
  s.textContent = texto;
  return s;
}

/** "parcial 62,4%" enquanto não fecha; "totalização encerrada" com tf. */
export function chipAndamento(pst: number, tf: boolean): HTMLSpanElement {
  if (tf) return chip("totalização encerrada", "encerrada");
  if (!(pst > 0)) return chip("aguardando seções", "neutro");
  return chip(`parcial ${pct(pst, 1)}`, "parcial");
}

/** Chip pela situação do TSE (nunca projetada). Devolve null quando não há situação. */
export function chipSituacao(st: string, e: boolean, dvt: string): HTMLSpanElement | null {
  if (dvt && !/^v[aá]lido/i.test(dvt)) return chip("sub judice", "subjudice");
  // Nos arquivos finais o TSE marca e="s" também em quem vai ao 2º turno (visto em 04/10/2026,
  // Douglas Ruas e Celina Leão); por isso o texto st decide, e a flag só vale sem texto.
  if (/2.?\s*turno/i.test(st)) return chip("2º turno", "segundo");
  if (/^eleit/i.test(st) || (e && st.trim() === "")) return chip("eleito", "eleito");
  return null;
}

/** Troca o conteúdo de um contêiner de chips. */
export function trocarChips(alvo: HTMLElement, chips: (HTMLElement | null)[]): void {
  alvo.replaceChildren(...chips.filter((c): c is HTMLElement => c !== null));
}
