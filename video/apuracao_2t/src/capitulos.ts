import { CAPITULOS_BASE, capituloIdDe, type CapituloId } from "./ordem";
import { COR } from "./tema";

export type Capitulo = {
  id: CapituloId;
  numero: number;
  titulo: string;
  cor: string;
};

/** Cor de cada capítulo (CONTRATO.md, seção 1), sempre resolvida pela paleta da casa. */
const COR_CAPITULO: Record<CapituloId, keyof typeof COR> = {
  abertura: "tealClaro",
  noite: "flavio",
  projecao: "ouro",
  turnos: "lula",
  secoes: "media",
  pesquisas: "outros",
  urnas: "teal",
  fecho: "tealClaro",
};

export const CAPITULOS: Capitulo[] = CAPITULOS_BASE.map((c) => ({ ...c, cor: COR[COR_CAPITULO[c.id]] }));

/** Número do último capítulo, para o "03 / 07" do HUD. */
export const ULTIMO_CAPITULO = Math.max(...CAPITULOS.map((c) => c.numero));

export const capituloPorId = (id: CapituloId): Capitulo => {
  const capitulo = CAPITULOS.find((c) => c.id === id);
  if (!capitulo) {
    throw new Error(`capítulo desconhecido: ${id}`);
  }
  return capitulo;
};

/** Capítulo de uma cena, pela ordem do contrato. */
export const capituloDe = (cenaId: string): Capitulo => {
  const id = capituloIdDe(cenaId);
  if (!id) {
    throw new Error(`cena fora da ordem do contrato: ${cenaId}`);
  }
  return capituloPorId(id);
};
