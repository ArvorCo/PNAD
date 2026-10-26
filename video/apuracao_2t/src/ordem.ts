// Ordem das cenas e dos capítulos (CONTRATO.md, seção 1). Fonte única: o roteiro, o plano, o
// registro de componentes e o teste conferem contra esta lista. Arquivo puro, sem importações,
// para rodar também em `node src/verificar.ts`. Ordem final do roteiro de 25/10/2026.

/** Capítulos na ordem do vídeo: id, número mostrado no HUD e título. */
export const CAPITULOS_BASE = [
  { id: "abertura", numero: 0, titulo: "Abertura" },
  { id: "noite", numero: 1, titulo: "A noite minuto a minuto" },
  { id: "projecao", numero: 2, titulo: "A projeção" },
  { id: "turnos", numero: 3, titulo: "Entre os dois turnos" },
  { id: "secoes", numero: 4, titulo: "Seção por seção" },
  { id: "pesquisas", numero: 5, titulo: "Pesquisas contra a urna" },
  { id: "urnas", numero: 6, titulo: "As urnas por dentro" },
  { id: "fecho", numero: 7, titulo: "Fecho" },
] as const;

export type CapituloId = (typeof CAPITULOS_BASE)[number]["id"];

/** As 32 cenas, na ordem exata dos blocos `## id` do roteiro. */
export const ORDEM = [
  { id: "abertura", capitulo: "abertura" },
  { id: "tese", capitulo: "abertura" },
  { id: "cap-noite", capitulo: "noite" },
  { id: "noite-stf", capitulo: "noite" },
  { id: "noite-parada", capitulo: "noite" },
  { id: "noite-virada", capitulo: "noite" },
  { id: "noite-fim", capitulo: "noite" },
  { id: "cap-projecao", capitulo: "projecao" },
  { id: "proj-primeiro-ponto", capitulo: "projecao" },
  { id: "proj-serie", capitulo: "projecao" },
  { id: "proj-sem-virada", capitulo: "projecao" },
  { id: "cap-turnos", capitulo: "turnos" },
  { id: "turnos-swing-uf", capitulo: "turnos" },
  { id: "turnos-transferencia", capitulo: "turnos" },
  { id: "turnos-abstencao", capitulo: "turnos" },
  { id: "cap-secoes", capitulo: "secoes" },
  { id: "secoes-encerramento", capitulo: "secoes" },
  { id: "secoes-biometria", capitulo: "secoes" },
  { id: "secoes-comparecimento", capitulo: "secoes" },
  { id: "secoes-ranking", capitulo: "secoes" },
  { id: "cap-pesquisas", capitulo: "pesquisas" },
  { id: "pesq-erro", capitulo: "pesquisas" },
  { id: "pesq-reponderacao", capitulo: "pesquisas" },
  { id: "pesq-hipotese", capitulo: "pesquisas" },
  { id: "cap-urnas", capitulo: "urnas" },
  { id: "urnas-cadencia", capitulo: "urnas" },
  { id: "urnas-integridade", capitulo: "urnas" },
  { id: "urnas-assinatura", capitulo: "urnas" },
  { id: "paralela-177", capitulo: "urnas" },
  { id: "cap-fecho", capitulo: "fecho" },
  { id: "fecho-arvor", capitulo: "fecho" },
  { id: "fecho-chamada", capitulo: "fecho" },
] as const satisfies readonly { id: string; capitulo: CapituloId }[];

export type CenaId = (typeof ORDEM)[number]["id"];

export const IDS: readonly CenaId[] = ORDEM.map((c) => c.id);

/** Capítulo de uma cena; `undefined` se o id não está na ordem. */
export const capituloIdDe = (id: string): CapituloId | undefined => ORDEM.find((c) => c.id === id)?.capitulo;
