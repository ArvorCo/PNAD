// Tipos dos JSON gerados (CONTRATO.md, seções 3 a 6). Quem muda um esquema muda o contrato
// primeiro e depois este arquivo.

// ---------------------------------------------------------------- apuracao_2t.json (seção 3)

/** Contorno de uma UF no mapa projetado (mesma projeção do mapa de fiscais). */
export type MapaUf = { uf: string; d: string };

/** Blocos de `analysis/apuracao_2t_2026/dados/<bloco>.json` que o vídeo pode usar. */
export const BLOCOS = [
  "presidente",
  "linha_do_tempo",
  "projecao_noite",
  "comparacao_1t",
  "abstencao",
  "secoes_ranking",
  "pesquisas_vs_urna",
  "paralela",
  "secoes",
  "secoes_voto",
  "hipotese_autor",
  "logs",
  "rdv",
  "metadados",
  "transferencia",
] as const;

export type BlocoId = (typeof BLOCOS)[number];

/**
 * Blocos ainda sem esquema fixo: cada um é o JSON do dossiê inteiro (ou `{ grande: true, ... }`
 * se passou do limite de tamanho). As cenas leem por caminho (`ref.ts`), então um bloco ausente
 * ou com outra forma vira aviso na tela, nunca erro de render.
 */
export type Dados = {
  gerado_em: string;
  /** Caminho do arquivo lido → SHA-256. */
  fontes: Record<string, string>;
  /** Blocos esperados que ainda não existem em disco. */
  pendentes: BlocoId[];
  /** Blocos grandes demais para embutir: só caminho e hash. */
  avisos: string[];
  mapa: { view: number; ufs: MapaUf[] };
} & Partial<Record<BlocoId, unknown>>;

// ---------------------------------------------------------------- midia.json (seção 4)

export type FormatoMidia = "16x9" | "9x16";

export type ItemMidia = {
  tipo: "video" | "imagem";
  formatos: FormatoMidia[];
  segundos: number;
};

export type Midia = Record<string, ItemMidia | undefined>;

// ---------------------------------------------------------------- capturas.json (seção 5)

export type Captura = {
  formatos: FormatoMidia[];
  segundos: number;
  /** Nome do still → segundo da gravação em que foi tirado. */
  stills: Record<string, number>;
};

export type Capturas = Record<string, Captura | undefined>;

// ---------------------------------------------------------------- musica.json e voz.json (seção 6)

export type FaixaMusica = { arquivo: string; segundos: number; prompt: string };

/** Uma faixa por capítulo, chave = id do capítulo; capítulo sem faixa fica em silêncio. */
export type Musica = Record<string, FaixaMusica | undefined>;

export type Palavra = { w: string; t: number; f: number };

export type CenaVoz = {
  id: string;
  arquivo: string;
  segundos: number;
  texto: string;
  palavras: Palavra[];
};

export type Voz = { modelo: string; cenas: CenaVoz[] };
