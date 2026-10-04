// Servidor estático mínimo para ensaiar o telão sem o servidor da apuração:
// serve public/ e responde 404 em /api/* e /events, então o telão cai no mock (#mock=1).
// Uso: bun run scripts/dev-static.ts [porta]

import { join, normalize } from "node:path";

const raiz = join(import.meta.dir, "..", "public");
const porta = Number(process.argv[2] ?? 4181);

const servidor = Bun.serve({
  port: porta,
  hostname: "127.0.0.1",
  async fetch(req) {
    const url = new URL(req.url);
    if (url.pathname.startsWith("/api/") || url.pathname === "/events") return new Response("sem servidor", { status: 404 });
    const caminho = normalize(decodeURIComponent(url.pathname === "/" ? "/index.html" : url.pathname));
    if (caminho.includes("..")) return new Response("proibido", { status: 403 });
    const arquivo = Bun.file(join(raiz, caminho));
    if (!(await arquivo.exists())) return new Response("não encontrado", { status: 404 });
    return new Response(arquivo, { headers: { "cache-control": "no-store" } });
  },
});

console.log(`telão estático em http://127.0.0.1:${servidor.port}/#mock=1&speed=60`);
