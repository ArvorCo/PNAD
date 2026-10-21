// Textos fixos da casa e utilitários de grafia usados por mais de uma cena.

/** As três frases da casa (CONTRATO.md, seção 2), na ordem em que são ditas. */
export const FRASES_CASA = [
  "Atipicidade estatística não é irregularidade.",
  "A lista é de prioridade de fiscalização, não de acusação.",
  "O que resolve cada item é a ata da mesa, o log da urna e a presença do fiscal.",
] as const;

/** "ESCOLA MUNICIPAL GETÚLIO VARGAS" → "Escola Municipal Getúlio Vargas" (preposições em minúscula). */
export const nomeProprio = (s: string): string =>
  s
    .toLowerCase()
    .split(/\s+/)
    .map((p, i) => (i > 0 && ["de", "da", "do", "das", "dos", "e"].includes(p) ? p : p.charAt(0).toUpperCase() + p.slice(1)))
    .join(" ");
