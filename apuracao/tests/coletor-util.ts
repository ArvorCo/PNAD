// Montagem do coletor em banco de memória com relógio e respostas falsas.
import { abrirEscrita } from "../src/db/abrir.ts";
import { Escritor } from "../src/db/escrita.ts";
import type { ItemLote } from "../src/db/escrita.ts";
import { sha256Hex } from "../src/db/itens.ts";
import { registroDeArquivos } from "../src/tse/urls.ts";
import type { ClasseFetch, FetchResult, Job } from "../src/types.ts";
import type { CtxProc, Knobs } from "../src/collector/contexto.ts";
import { EstadoArquivos } from "../src/collector/estado-arquivos.ts";
import type { FileState } from "../src/collector/estado-arquivos.ts";
import { Lote } from "../src/collector/lote.ts";
import { RelogioFalso } from "../src/collector/relogio.ts";
import { lerCm } from "./helpers.ts";

export const KNOBS_TESTE: Knobs = { zonas: "sempre", minIntervaloMuS: 300, sweepMin: 0, concurrency: 32 };

export interface Montagem {
  ctx: CtxProc;
  relogio: RelogioFalso;
  estado: EstadoArquivos;
  lote: Lote;
}

/** Registro da eleição 6257 (presidente) a partir do cm real; path ":memory:" por padrão. */
export function montar(path = ":memory:", knobs: Partial<Knobs> = {}): Montagem {
  const db = abrirEscrita(path);
  const escritor = new Escritor(db);
  const itens: ItemLote[] = [...registroDeArquivos(new Map([[6257, lerCm("mun-e006257-cm.json")]]))].map((row) => ({ k: "arquivo", row }));
  escritor.gravarLote(itens);
  const relogio = new RelogioFalso();
  const estado = EstadoArquivos.carregarDoBanco(db);
  const lote = new Lote(escritor, relogio);
  const ctx: CtxProc = {
    db, estado, lote, relogio, knobs: { ...KNOBS_TESTE, ...knobs }, pleito: 3220, driftContagem: new Map(), driftVisto: new Set(),
    aleatorio: () => 0.5,
  };
  return { ctx, relogio, estado, lote };
}

export function resultado(classe: ClasseFetch, extra: Partial<FetchResult> = {}): FetchResult {
  return {
    classe, iniciadoEm: "2026-10-04T20:00:00.000Z", duracaoMs: 10, condicional: false,
    httpStatus: classe === "nao_modificado" ? 304 : classe === "nao_existe" ? 404 : classe === "negado" ? 403 : classe === "limite" ? 429 : classe === "erro_servidor" ? 503 : 200,
    etag: null, lastModified: null, servidorDate: null, cacheHdr: null, age: null, retryAfterS: null, bytes: 0, body: null,
    bodySha256: null, erro: null, ...extra,
  };
}

export function ok(body: Uint8Array<ArrayBuffer> | string, etag: string | null = null): FetchResult {
  const b = typeof body === "string" ? new TextEncoder().encode(body) : body;
  return resultado("ok", { body: b, bytes: b.byteLength, bodySha256: sha256Hex(b), etag });
}

export function jobDe(fs: FileState, motivo: Job["motivo"] = "periodico"): Job {
  return { arquivoId: fs.id, chave: fs.chave, url: fs.url, prioridade: "t0", due: 0, motivo };
}

export function arquivo(m: Montagem, chave: string): FileState {
  const fs = m.estado.porChave.get(chave);
  if (!fs) throw new Error(`sem arquivo ${chave}`);
  return fs;
}

export function contar(m: Montagem, sql: string): number {
  return m.ctx.db.query<{ n: number }, []>(sql).get()?.n ?? 0;
}
