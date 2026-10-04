// Roteador da API JSON. Toda resposta com Cache-Control: no-store; erros como {erro}.
import type { Database } from "bun:sqlite";
import { andamento, blob, fetches, fim, latencia, snapshots, velocidade } from "./api-auditoria.ts";
import { anomalias } from "./api-anomalias.ts";
import { config, estado } from "./api-config.ts";
import { lotes } from "./api-lotes.ts";
import { mapa } from "./api-mapa.ts";
import { resultado, serie } from "./api-resultado.ts";
import type { Contexto } from "./contexto.ts";
import { ErroHttp, Params, erro, json } from "./http.ts";

type Rota = (ctx: Contexto, db: Database, p: Params) => unknown;

const COM_BANCO: Readonly<Record<string, Rota>> = {
  "/api/resultado": resultado,
  "/api/mapa": mapa,
  "/api/serie": serie,
  "/api/lotes": lotes,
  "/api/anomalias": anomalias,
  "/api/snapshots": snapshots,
  "/api/latencia": latencia,
  "/api/fim": fim,
  "/api/velocidade": velocidade,
  "/api/andamento": andamento,
  "/api/fetches": fetches,
};

const RE_BLOB = /^\/api\/blob\/(\d+)$/;

export function responderApi(ctx: Contexto, req: Request, url: URL): Response {
  if (req.method !== "GET" && req.method !== "HEAD") return erro(405, "método não permitido");
  const p = new Params(url.searchParams);
  try {
    const db = ctx.banco.obter();
    if (url.pathname === "/api/config") return json(config(ctx, db));
    if (url.pathname === "/api/estado") return json(estado(ctx, db, p));
    const rota = COM_BANCO[url.pathname];
    const mBlob = RE_BLOB.exec(url.pathname);
    if (!rota && !mBlob) return erro(404, `rota desconhecida: ${url.pathname}`);
    if (!db) return erro(503, "banco ainda não existe: o coletor não começou");
    if (mBlob) return blob(db, Number(mBlob[1]));
    if (rota) return json(rota(ctx, db, p));
    return erro(404, `rota desconhecida: ${url.pathname}`);
  } catch (e) {
    if (e instanceof ErroHttp) return erro(e.status, e.message);
    const msg = e instanceof Error ? e.message : String(e);
    if (/database is locked|SQLITE_BUSY/i.test(msg)) return erro(503, "banco ocupado, tente de novo");
    return erro(500, msg);
  }
}
