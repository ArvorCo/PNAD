// Tipos compartilhados pelo processamento e pelo agendador.
import type { Database } from "bun:sqlite";
import type { ModoZonas } from "../config.ts";
import type { EventoNovo, ItemLote, LinhaFetch } from "../db/escrita.ts";
import type { ClasseFetch, FetchResult, Job, MotivoFetch, Prioridade } from "../types.ts";
import type { EstadoArquivos, FileState } from "./estado-arquivos.ts";
import type { Lote } from "./lote.ts";
import type { Relogio } from "./relogio.ts";

/** Ajustes que mudam a quente (env na partida, meta.ajustes a cada 10 s). */
export interface Knobs {
  zonas: ModoZonas;
  minIntervaloMuS: number;
  sweepMin: number;
  concurrency: number;
}

export interface CtxProc {
  db: Database;
  estado: EstadoArquivos;
  lote: Lote;
  relogio: Relogio;
  knobs: Knobs;
  pleito: number;
  /** contagem de detecções de drift por tipo:nivel:cargo nesta execução */
  driftContagem: Map<string, number>;
  /** caminhos de drift já reportados (tipo + caminho) */
  driftVisto: Set<string>;
  aleatorio?: () => number;
}

export interface JobNovo {
  arquivoId: number;
  prioridade: Prioridade;
  due: number;
  motivo: MotivoFetch;
}

export interface SaidaProc {
  classe: ClasseFetch;
  mudou: boolean;
  jobs: JobNovo[];
  pausar: { retryAfterS: number | null } | null;
  retryEm: number | null;
}

/** Tudo que o processamento de um corpo novo precisa. */
export interface CtxCorpo {
  ctx: CtxProc;
  job: Job;
  fs: FileState;
  r: FetchResult;
  fetchRef: string;
  em: string;
  agora: number;
  grupo: ItemLote[];
  saida: SaidaProc;
}

export function evento(fs: FileState, em: string, tipo: string, severidade: "info" | "warn" | "error", detalhe: unknown, snapshot: string | null = null): ItemLote {
  const k = fs.key;
  const row: EventoNovo = {
    em, tipo, severidade, arquivo_id: fs.id, snapshot_id: snapshot === null ? null : { ref: snapshot },
    eleicao_cd: k.ele, cargo_cd: k.cargo, nivel: k.nivel, uf: k.uf, municipio_cd: k.mun, zona_cd: k.zona, detalhe,
  };
  return { k: "evento", row };
}

export function linhaFetch(job: Job, fs: FileState, r: FetchResult, classe: ClasseFetch): LinhaFetch {
  return {
    arquivo_id: fs.id, iniciado_em: r.iniciadoEm, duracao_ms: r.duracaoMs, motivo: job.motivo, condicional: r.condicional ? 1 : 0,
    http_status: r.httpStatus, classe, etag: r.etag, last_modified: r.lastModified, servidor_date: r.servidorDate,
    cache_hdr: r.cacheHdr, age: r.age, bytes: r.bytes, body_sha256: r.bodySha256, mudou: 0, erro: r.erro,
  };
}
