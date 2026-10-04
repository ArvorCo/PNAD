// Tipos do telão. Espelham os "Contratos de API" do plano: números já convertidos,
// nunca string com vírgula. Datas em texto ISO-8601 (UTC ou com deslocamento).

/** Campo político editorial (tucano é centro-esquerda). */
export type Campo = "esquerda" | "centro-esquerda" | "centro" | "centro-direita" | "direita" | "indefinido";

// ---------- /api/config ----------
export interface ConfigUf {
  uf: string; // sigla em caixa alta, "SP"
  nome: string;
  cdi: string; // código IBGE da UF
  te: number; // eleitorado
}

export interface ConfigMunicipio {
  cd: string; // código TSE, 5 dígitos
  cdi: string; // código IBGE, 7 dígitos ("" no exterior)
  nm: string;
  c: boolean; // capital
  z: string[]; // zonas
  te?: number;
}

export interface Config {
  turno: number;
  eleicoes: { federal: number; estadual: number };
  ufs: ConfigUf[];
  municipios: Record<string, ConfigMunicipio[]>; // chave: UF em caixa alta
}

// ---------- /api/estado ----------
export interface EstadoBr {
  ts: number;
  st: number;
  pst: number; // 0 a 100
  dt_ht: string | null; // última totalização
  hg: string | null; // geração do arquivo
  lido_em: string | null; // nossa leitura
  atraso_s: number | null;
}

export interface EstadoUf {
  uf: string;
  pst: number;
  st: number;
  ts: number;
  munnr: number;
  munpt: number;
  munf: number;
  dt_ht: string | null;
  fechou_em?: string | null;
}

export interface Estado {
  agora: string;
  turno: number;
  br: EstadoBr;
  ufs: EstadoUf[];
  historico: { at: string; st: number; pst: number }[];
  latencias: { leitura_menos_hg: number[]; hg_menos_ht: number[] };
}

// ---------- /api/resultado ----------
export interface Vice {
  tp: string;
  nmu: string;
  sgp: string;
}

export interface Candidato {
  sqcand: string;
  n: string; // número de urna
  nm: string;
  nmu: string;
  sg: string; // partido
  campo: Campo;
  fed_sg?: string;
  e: boolean; // eleito pelo TSE
  st: string; // situação do TSE ("Eleito", "2º turno", "Não eleito", "")
  dvt: string; // destinação do voto ("Válido", "Anulado sub judice", ...)
  vap: number;
  pvapn: number; // % dos válidos, 0 a 100
  vs: Vice[];
}

export interface PartidoResultado {
  sg: string;
  campo: Campo;
  tvtn: number;
  tvan: number;
  n_cand: number;
}

export interface Resultado {
  cargo: { cd: number; nome: string; nome_f: string; nv: number };
  tpabr: "br" | "uf" | "mu" | "zona";
  abr: string;
  nome_escopo: string;
  dg_hg: string | null;
  dt_ht: string | null;
  lido_em: string | null;
  tf: boolean; // totalização final
  s: { ts: number; st: number; pst: number };
  e: { te: number; c: number; a: number; pc: number; pa: number };
  v: { tv: number; vv: number; vvc: number; vnom: number; van: number; vb: number; vn: number; pvb: number; pvn: number; pvan: number };
  cand: Candidato[];
  partidos: PartidoResultado[];
}

// ---------- /api/mapa ----------
export interface LiderUnidade {
  sqcand: string;
  n: string;
  nmu: string;
  sg: string;
  campo: Campo;
  vap: number;
  pvapn: number;
}

export interface UnidadeMapa {
  cd: string;
  cdi?: string;
  nm: string;
  te?: number;
  pst: number;
  tf: boolean;
  lider?: LiderUnidade;
  segundo?: LiderUnidade;
  margem?: number; // pontos percentuais dos válidos entre 1º e 2º
  top?: LiderUnidade[]; // nv primeiros
}

export interface Mapa {
  unidades: UnidadeMapa[];
}

export type NivelMapa = "uf" | "mun" | "zona";

// ---------- /api/serie ----------
export interface Serie {
  pontos: { at: string; pst: number; cand: Record<string, number> }[];
  viradas: { at: string; de: string; para: string }[];
}

// ---------- /api/anomalias ----------
export interface Anomalia {
  at: string;
  tipo: "virada" | "regressao" | "fechou" | "atraso";
  abr: string;
  cargo: number;
  texto: string;
}

// ---------- /events ----------
export interface EventoSse {
  kind: "resultado" | "estado" | "anomalia";
  ele: number;
  cargo: number;
  abr: string;
  snapshot_id: number;
  at: string;
}

// ---------- ativos estáticos ----------
/** campos.json normalizado: partido → campo e campo → cor e rótulo. */
export interface Campos {
  partidos: Record<string, Campo>;
  cores: Record<string, string>;
  rotulos: Record<string, string>;
}

/** cores.json normalizado: cor fixa por número de urna e sequência para os demais. */
export interface Cores {
  candidatos: Record<string, string>;
  sequencia: string[];
}

export interface ItemPlaylist {
  v: string;
  uf?: string; // sigla ou "$destaque"
  mun?: string;
  dwell?: number; // segundos
  max?: number; // limite de UFs na expansão de $destaque
}

export interface Playlist {
  dwell: number;
  itens: ItemPlaylist[];
  /** Ordem de prioridade das UFs para $destaque (sem ela, eleitorado). */
  destaque?: string[];
}

// ---------- estado da interface ----------
export interface Replay {
  inicio: string; // ISO
  speed: number;
}

export interface UiState {
  v: string;
  uf: string | null;
  mun: string | null;
  zonas: boolean; // hash z presente
  zona: string | null; // hash z=0248
  auto: boolean;
  hud: boolean;
  mock: boolean;
  speed: number;
  replay: Replay | null;
  dwell: number | null; // sobrescreve o dwell da playlist, segundos
  variante: number; // tecla m
  pausado: boolean;
  paleta: boolean;
  indice: number; // posição na playlist expandida
  dwellInicio: number; // performance.now() do início da tela
  dwellMs: number; // duração da tela atual
}

export type ModoRede = "sse" | "polling" | "mock" | "replay" | "offline";

export interface Rede {
  modo: ModoRede;
  conectado: boolean;
  ultimo_evento_em: number | null; // Date.now()
  ultimo_ok_em: number | null;
}

export interface State {
  config: Config | null;
  estado: Estado | null;
  resultados: Record<string, Resultado>; // chave chaveResultado()
  mapas: Record<string, Mapa>; // chave chaveMapa()
  series: Record<string, Serie>; // chave chaveSerie()
  anomalias: Anomalia[];
  campos: Campos;
  cores: Cores;
  playlist: Playlist;
  rede: Rede;
  ui: UiState;
}

/** Folha numérica que mudou num patch, para count-up e sublinhado. */
export interface DiffItem {
  path: string; // caminho com pontos, "resultados.6257:1:br.v.tv"
  de: number;
  para: number;
}

export type Diff = DiffItem[];

// ---------- chaves ----------
export const chaveResultado = (ele: number, cargo: number, abr: string): string => `${ele}:${cargo}:${abr}`;
export const chaveMapa = (ele: number, cargo: number, nivel: NivelMapa, pai: string): string =>
  `${ele}:${cargo}:${nivel}:${pai}`;
export const chaveSerie = (ele: number, cargo: number, abr: string): string => `${ele}:${cargo}:${abr}`;

/** Abrangência no formato do TSE: "br", "sp", "sp71072", "sp71072-z0248". */
export function abrDe(uf?: string | null, mun?: string | null, zona?: string | null): string {
  if (!uf) return "br";
  const u = uf.toLowerCase();
  if (!mun) return u;
  if (!zona) return `${u}${mun}`;
  return `${u}${mun}-z${zona.padStart(4, "0")}`;
}

/** Necessidade de dados declarada por uma tela. */
export type Need =
  | { tipo: "resultado"; ele: number; cargo: number; abr: string }
  | { tipo: "mapa"; ele: number; cargo: number; nivel: NivelMapa; pai: string }
  | { tipo: "serie"; ele: number; cargo: number; abr: string }
  | { tipo: "estado" }
  | { tipo: "anomalias" };
