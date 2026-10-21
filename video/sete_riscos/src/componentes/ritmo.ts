// Ajuste dos gatilhos quando a cena não tem voz (voz.json vazio): as reservas do registro são os
// tempos reais da narração e passariam do fim dos 6 s provisórios. Sem voz, comprime todos os
// gatilhos na mesma proporção para caberem na cena; com voz, devolve os gatilhos intactos.
import type { Cena, Gatilhos } from "../plano";

export const ritmo = (cena: Cena, g: Gatilhos, ocupacao = 0.8): Gatilhos => {
  if (cena.comVoz) {
    return g;
  }
  const maior = Math.max(1, ...Object.values(g));
  const limite = cena.frames * ocupacao;
  if (maior <= limite) {
    return g;
  }
  const k = limite / maior;
  return Object.fromEntries(Object.entries(g).map(([nome, q]) => [nome, Math.round(q * k)]));
};
