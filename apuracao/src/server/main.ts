// Servidor do telão: estáticos de public/, API JSON de leitura e SSE. Só leitura do SQLite.
import { join, resolve } from "node:path";
import { responderApi } from "./api.ts";
import { Campos, FonteBanco } from "./contexto.ts";
import type { Contexto } from "./contexto.ts";
import { responderEstatico } from "./estatico.ts";
import { erro } from "./http.ts";
import type { OpcoesSse } from "./sse.ts";
import { responderSse } from "./sse.ts";

export interface OpcoesServidor {
  dbPath?: string;
  publicDir?: string;
  port?: number;
  hostname?: string;
  log?: boolean;
  sse?: OpcoesSse;
  agora?: () => string;
}

export interface Servidor {
  server: ReturnType<typeof Bun.serve>;
  ctx: Contexto;
  url: string;
  parar(): Promise<void>;
}

const RAIZ = resolve(import.meta.dir, "../..");

export function criarServidor(o: OpcoesServidor = {}): Servidor {
  const publicDir = o.publicDir ?? join(RAIZ, "public");
  const ctx: Contexto = {
    banco: new FonteBanco(o.dbPath ?? process.env.APURACAO_DB ?? join(RAIZ, "data/apuracao.sqlite")),
    campos: new Campos(join(publicDir, "campos.json")),
    publicDir,
    agora: o.agora ?? (() => new Date().toISOString()),
  };
  const log = o.log ?? true;
  const server = Bun.serve({
    hostname: o.hostname ?? "127.0.0.1",
    port: o.port ?? Number(process.env.APURACAO_PORT ?? 4180),
    idleTimeout: 120,
    fetch(req) {
      const inicio = performance.now();
      const url = new URL(req.url);
      let res: Response;
      if (url.pathname === "/events") res = responderSse(ctx, req, url, o.sse);
      else if (url.pathname.startsWith("/api/")) res = responderApi(ctx, req, url);
      else res = responderEstatico(publicDir, url.pathname) ?? erro(404, `não encontrado: ${url.pathname}`);
      if (log) {
        const linha = { t: new Date().toISOString(), m: req.method, p: url.pathname, q: url.search, s: res.status, ms: Math.round((performance.now() - inicio) * 10) / 10 };
        console.log(JSON.stringify(linha));
      }
      return res;
    },
  });
  return {
    server,
    ctx,
    url: server.url.toString().replace(/\/$/, ""),
    async parar() {
      await server.stop(true);
      ctx.banco.fechar();
    },
  };
}

if (import.meta.main) {
  const s = criarServidor();
  console.log(JSON.stringify({ t: new Date().toISOString(), evento: "servidor_no_ar", url: s.url, db: s.ctx.banco.path }));
  const sair = (): void => {
    void s.parar().then(() => process.exit(0));
  };
  process.on("SIGINT", sair);
  process.on("SIGTERM", sair);
}
