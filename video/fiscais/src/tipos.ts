export type Nivel = "alta" | "media" | "baixa";

export type Exemplo = {
  uf: string;
  municipio: string;
  zona: number;
  secao: number;
  local: string;
  bairro: string | null;
  aptos: number;
  votantes: number;
  validos: number;
  brancos: number;
  nulos: number;
  lula: number;
  flavio: number;
  lula_pct: number;
  flavio_pct: number;
  zona_lula_pct: number;
  zona_flavio_pct: number;
  uf_lula_pct: number;
  uf_flavio_pct: number;
  encerramento_brasilia: string;
  recebido_tse: string;
  n_cargas: number;
  lula_2022_pct: number | null;
  flavio_2022_pct: number | null;
  criterios: string[];
  nivel: Nivel;
  pontuacao: number;
  explicacao_provavel: string;
  o_que_conferir: string;
  lat: number;
  lon: number;
  local_id: string;
  detalhe: Record<string, unknown> | null;
  detalhes: Record<string, Record<string, unknown>>;
  local_secoes_sinalizadas: number | null;
  local_secoes_total: number | null;
  xy: [number, number];
};

export type Criterio = {
  id: string;
  nome: string;
  mede: string;
  limiar: string;
  peso: number | Record<string, number>;
  secoes: number;
  por_nivel: Record<Nivel, number>;
  explicacao_comum: string;
  o_que_conferir: string;
  exemplo: Exemplo;
};

export type Dados = {
  gerado_em: string;
  fonte: string;
  rotulos: { atipico: string; prioridade: string; resolve: string };
  resumo: {
    secoes_universo: number;
    secoes_sinalizadas: number;
    por_nivel: Record<Nivel, { secoes: number; locais: number; municipios: number }>;
    aptos_sinalizadas: number;
    pct_sinalizadas: number;
    fiscais_um_por_local: { alta: number; alta_media: number; todos: number };
    fiscais_dois_por_secao: { alta: number; alta_media: number; todos: number };
    explicacao_por_codigo: Record<string, number>;
    sem_arquivo: number;
  };
  sem_arquivo_por_zona: { uf: string; municipio: string; zona: number; secoes: number }[];
  zonas_congeladas: { zonas: number; secoes: number; horas_min: number; horas_max: number };
  criterios: Criterio[];
  por_uf: {
    uf: string;
    regiao: string;
    secoes: number;
    alta: number;
    media: number;
    baixa: number;
    locais_alta: number;
    taxa_pct: number;
  }[];
  municipios: {
    uf: string;
    municipio: string;
    secoes: number;
    alta: number;
    media: number;
    pontuacao_soma: number;
  }[];
  contrario: string[];
  mapa: {
    view: number;
    ufs: { uf: string; d: string }[];
    pontos: [number, number, Nivel][];
    pontos_baixa: [number, number][];
  };
};

export type Palavra = { w: string; t: number; f: number };

export type CenaVoz = {
  id: string;
  arquivo: string;
  segundos: number;
  texto: string;
  palavras: Palavra[];
};

export type Voz = { modelo: string; cenas: CenaVoz[] };
