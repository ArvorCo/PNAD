// Tipos de domínio compartilhados por coletor, servidor e testes.

/** Tipo de arquivo do TSE. */
export type Tipo = "ele-c" | "cm" | "ab" | "u" | "e";

/** Nível de abrangência de um arquivo. */
export type Nivel = "br" | "uf" | "mu" | "zona";

/** Camada de coleta: 0 núcleo, 1 ab por UF, 2 município, 3 zona, 4 sonda. */
export type Tier = 0 | 1 | 2 | 3 | 4;

/** Identidade de um arquivo do TSE; campos ausentes ficam null. */
export interface FileKey {
  tipo: Tipo;
  ele: number | null;
  cargo: number | null;
  nivel: Nivel | null;
  /** sigla minúscula (sp, zz); null no nível br */
  uf: string | null;
  /** código TSE de 5 dígitos, com zeros à esquerda */
  mun: string | null;
  /** zona com 4 dígitos */
  zona: string | null;
}

/** Linha do registro `arquivo` antes de ir para o banco. */
export interface ArquivoRegistro extends FileKey {
  chave: string;
  url: string;
  tier: Tier;
  sonda: boolean;
}

export type MotivoFetch = "periodico" | "gatilho_ab" | "final" | "sweep" | "probe" | "retry";

export type Prioridade = "final" | "t0" | "t1" | "gatilho" | "probe" | "sweep";

/** Um job por arquivo (coalescência). */
export interface Job {
  arquivoId: number;
  chave: string;
  url: string;
  prioridade: Prioridade;
  /** epoch ms */
  due: number;
  motivo: MotivoFetch;
}

export type ClasseFetch =
  | "ok"
  | "nao_modificado"
  | "igual"
  | "nao_existe"
  | "negado"
  | "limite"
  | "erro_servidor"
  | "timeout"
  | "erro_rede"
  | "corpo_invalido";

export interface FetchResult {
  classe: ClasseFetch;
  iniciadoEm: string;
  duracaoMs: number;
  condicional: boolean;
  httpStatus: number | null;
  etag: string | null;
  lastModified: string | null;
  servidorDate: string | null;
  cacheHdr: string | null;
  age: number | null;
  retryAfterS: number | null;
  bytes: number;
  body: Uint8Array<ArrayBuffer> | null;
  bodySha256: string | null;
  erro: string | null;
}

export type Severidade = "info" | "warn" | "error";

/** Arquivo do TSE já validado pelo esquema leniente. */
export type { ParsedFile } from "./parse/schemas.ts";
