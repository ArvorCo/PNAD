// Formas das linhas gravadas no SQLite (snake_case = nome da coluna).
// Geradas por parse/normalizar.ts e consumidas por db/escrita.ts.

export type N = number | null;
export type S = string | null;

/** Metadados de versão comuns a todo arquivo do TSE. */
export interface LinhaSnapshotMeta {
  dg: S;
  hg: S;
  idg: N;
  gerado_em: S;
  dt: S;
  ht: S;
  totalizado_em: S;
  tf: 0 | 1 | null;
  andamento: S;
  divulgacao: S;
  turno: N;
}

export interface LinhaTotais {
  vagas: N;
  ts: N; st: N; snt: N; si: N; sni: N; sa: N; sna: N; pst: N;
  te: N; est: N; esnt: N; esi: N; esni: N; esa: N; esna: N;
  comparecimento: N; abstencao: N; pc: N; pa: N;
  tv: N; vvc: N; vv: N; vnom: N; vl: N; van: N; vansj: N; vb: N; tvn: N; vn: N; vnt: N; vsan: N; vscv: N;
  pvvc: N; pvb: N; ptvn: N; pvan: N; pvn: N;
}

export interface LinhaVotoCandidato {
  sqcand: number;
  vap: N;
  pvapn: N;
  eleito: 0 | 1 | null;
  st: S;
  dvt: S;
}

export interface LinhaVotoPartido {
  partido_n: number;
  agremiacao_n: number;
  tvtn: N;
  tvtl: N;
  tval: N;
  tvan: N;
  dvt: S;
}

export interface LinhaVotoAgremiacao {
  agremiacao_n: number;
  tp: S;
  nome: S;
  composicao: S;
  tvtn: N;
  tvtl: N;
  tval: N;
  tvan: N;
  vagas: N;
}

export interface LinhaCandidato {
  sqcand: number;
  eleicao_cd: number;
  cargo_cd: number;
  uf: S;
  numero: N;
  nome: S;
  nome_urna: S;
  nascimento: S;
  partido_n: N;
  federacao_n: N;
  agremiacao_n: N;
  /** JSON de [{tp,sqcand,nm,nmu,sgp}] ou null */
  vices: S;
}

export interface LinhaPartido {
  n: number;
  sigla: S;
  nome: S;
  federacao_n: N;
}

export interface LinhaFederacao {
  n: number;
  sigla: S;
  nome: S;
  composicao: S;
  /** JSON de números de partido */
  partidos: S;
}

export interface LinhaAbEstado {
  tpabr: string;
  cdabr: string;
  andamento: S;
  dt: S;
  ht: S;
  totalizado_em: S;
  ts: N; st: N; pst: N; snt: N; si: N; sni: N; sa: N; sna: N;
  te: N; est: N; esnt: N; esi: N; esni: N; esa: N; esna: N;
  comparecimento: N; abstencao: N;
  munnr: N; munpt: N; munf: N;
  ufsnr: N; ufspt: N; ufsf: N;
}

export interface LinhaEEntrada {
  tpabr: S;
  cdabr: string;
  nome: S;
  dt: S;
  ht: S;
  totalizado_em: S;
  tvap: N;
  /** JSON de [{sqcand,n,vap}] */
  cand: string;
}

export interface LinhaEleicao {
  cd: number;
  cdt2: N;
  nome: S;
  turno: N;
  tipo: S;
  pleito: N;
  ciclo: S;
  data: S;
}

export interface LinhaCargo {
  eleicao_cd: number;
  cd: number;
  nome: S;
  tp: S;
  proporcional: 0 | 1;
}

export interface LinhaUf {
  sigla: string;
  nome: S;
}

export interface LinhaMunicipio {
  cd: string;
  uf: string;
  ibge: S;
  nome: S;
  capital: 0 | 1 | null;
  eleitores: N;
  origem: "cm" | "ab";
}

export interface LinhaZona {
  municipio_cd: string;
  cd: string;
  uf: string;
}
