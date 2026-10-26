// Textos fixos da casa e utilitários de grafia usados por mais de uma cena.

/** Rótulos obrigatórios (CONTRATO.md, seção 2). O roteiro os diz; a tela os repete onde cabem. */
export const ROTULO = {
  projecao: "Projeção estatística a partir do que já foi totalizado; não é resultado nem previsão de vitória.",
  paralela: "Soma dos BUs recebidos, não projeção.",
  atraso: "Atraso e abstenção atípica pedem explicação, não indicam irregularidade.",
  pausa: "Pausa é intervalo sem versão nova publicada, não acusação.",
  atipicidade: "Atipicidade estatística não é irregularidade.",
  hipotese: "Juízo editorial do autor, não fato verificado.",
} as const;

/** Tese do vídeo (analysis/apuracao_2t_2026/TESE.md, juízo editorial do autor). */
export const TESE = "A projeção da noite acertou. Entre sábado e domingo, algo mudou.";

/** "17:07" a partir de minutos depois das 17:00 de Brasília (float aceito). */
export const hhmmDe = (minutos: number): string => {
  const total = 17 * 60 + Math.round(minutos);
  const h = Math.floor(total / 60) % 24;
  const m = total % 60;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
};
