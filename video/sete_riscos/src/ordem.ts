// Ordem das cenas e dos capítulos (CONTRATO.md, seção 1). Fonte única: o roteiro, o plano, o
// registro de componentes e o teste conferem contra esta lista. Arquivo puro, sem importações,
// para rodar também em `node src/verificar.ts`.

/** Capítulos na ordem do vídeo: id, número mostrado no HUD e título. */
export const CAPITULOS_BASE = [
  { id: "abertura", numero: 0, titulo: "Abertura" },
  { id: "lei", numero: 1, titulo: "O fiscal e a lei" },
  { id: "riscos", numero: 2, titulo: "Sete riscos" },
  { id: "fechamento", numero: 3, titulo: "A hora de fechar" },
  { id: "mapa", numero: 4, titulo: "Onde você faz diferença" },
  { id: "fecho", numero: 5, titulo: "Convite" },
] as const;

export type CapituloId = (typeof CAPITULOS_BASE)[number]["id"];

/** As 20 cenas, na ordem exata dos blocos `## id` do roteiro. */
export const ORDEM = [
  { id: "abertura", capitulo: "abertura" },
  { id: "tese", capitulo: "abertura" },
  { id: "cap-lei", capitulo: "lei" },
  { id: "lei-poderes", capitulo: "lei" },
  { id: "lei-postura", capitulo: "lei" },
  { id: "cap-riscos", capitulo: "riscos" },
  { id: "risco-boca-de-urna", capitulo: "riscos" },
  { id: "risco-compra", capitulo: "riscos" },
  { id: "risco-transporte", capitulo: "riscos" },
  { id: "risco-medo", capitulo: "riscos" },
  { id: "risco-mesario", capitulo: "riscos" },
  { id: "risco-pianista", capitulo: "riscos" },
  { id: "risco-totalizacao", capitulo: "riscos" },
  { id: "cap-fechamento", capitulo: "fechamento" },
  { id: "fecha-ultimos", capitulo: "fechamento" },
  { id: "fecha-totalizacao", capitulo: "fechamento" },
  { id: "cap-mapa", capitulo: "mapa" },
  { id: "mapa-fiscais", capitulo: "mapa" },
  { id: "mapa-cadastro", capitulo: "mapa" },
  { id: "fecho-chamada", capitulo: "fecho" },
] as const satisfies readonly { id: string; capitulo: CapituloId }[];

export type CenaId = (typeof ORDEM)[number]["id"];

export const IDS: readonly CenaId[] = ORDEM.map((c) => c.id);

/** Capítulo de uma cena; `undefined` se o id não está na ordem. */
export const capituloIdDe = (id: string): CapituloId | undefined => ORDEM.find((c) => c.id === id)?.capitulo;
