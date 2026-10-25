// Servidor do telão: estáticos de public/, API JSON de leitura e SSE. Só leitura do SQLite.
import { join, resolve } from "node:path";
import { dirBoletins } from "../boletim/estado.ts";
import { responderApi } from "./api.ts";
import { Boletins } from "./boletins.ts";
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
  /** Pasta do boletim falado (padrão data/boletins-2t ou APURACAO_BOLETIM_DIR). */
  boletimDir?: string;
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
    boletins: new Boletins(o.boletimDir ?? dirBoletins()),
  };
  const boletins = ctx.boletins;
  boletins?.iniciar();
  const log = o.log ?? true;
  const server = Bun.serve({
    hostname: o.hostname ?? "127.0.0.1",
    port: o.port ?? Number(process.env.APURACAO_PORT ?? 4180),
    idleTimeout: 120,
    fetch(req, srv) {
      const inicio = performance.now();
      const url = new URL(req.url);
      let res: Response;
      const doBoletim = boletins?.responder(req, url, srv.requestIP(req)?.address ?? null) ?? null;
      if (doBoletim) res = doBoletim;
      else if (url.pathname === "/events") res = responderSse(ctx, req, url, o.sse);
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
      boletins?.parar();
      await server.stop(true);
      ctx.banco.fechar();
    },
  };
}

if (import.meta.main) {
  const s = criarServidor();
  console.log(JSON.stringify({ t: new Date().toISOString(), evento: "servidor_no_ar", url: s.url, db: s.ctx.banco.path }));
  // SIGTERM sai com 143: o laço do start-serve.sh (`until bun run serve`) só religa com código diferente
  // de zero, então `pkill -f src/server/main.ts` reinicia o servidor. SIGINT (Ctrl+C) sai com 0 e encerra.
  const sair = (codigo: number): void => {
    void s.parar().then(() => process.exit(codigo));
  };
  process.on("SIGINT", () => sair(0));
  process.on("SIGTERM", () => sair(143));
}
