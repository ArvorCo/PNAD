// Arquivos estáticos de public/, sem escapar do diretório.
import { existsSync, statSync } from "node:fs";
import { extname, join, normalize, resolve, sep } from "node:path";

const TIPOS: Readonly<Record<string, string>> = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".geojson": "application/geo+json; charset=utf-8",
  ".map": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".webp": "image/webp",
  ".ico": "image/x-icon",
  ".woff2": "font/woff2",
  ".woff": "font/woff",
  ".txt": "text/plain; charset=utf-8",
};

export function tipoDe(caminho: string): string {
  return TIPOS[extname(caminho).toLowerCase()] ?? "application/octet-stream";
}

/**
 * HTML, bundle (dist/) e JSON de configuração revalidam sempre: um `bun run build:ui` durante a
 * live chega ao OBS no próximo recarregamento. Malhas, fontes e fotos não mudam no dia.
 */
export function cacheDe(raiz: string, arquivo: string): string {
  const rel = arquivo.slice(raiz.length + 1).split(sep).join("/");
  if (/^(geo|fonts|fotos)\//.test(rel)) return "public, max-age=3600";
  return "no-cache";
}

export function responderEstatico(publicDir: string, pathname: string): Response | null {
  const raiz = resolve(publicDir);
  let rel: string;
  try {
    rel = decodeURIComponent(pathname);
  } catch {
    return null;
  }
  if (rel.includes("\0")) return null;
  if (rel === "/" || rel === "") rel = "/index.html";
  const alvo = resolve(join(raiz, normalize(rel)));
  if (alvo !== raiz && !alvo.startsWith(raiz + sep)) return null;
  if (!existsSync(alvo)) return null;
  let final = alvo;
  if (statSync(alvo).isDirectory()) {
    final = join(alvo, "index.html");
    if (!existsSync(final)) return null;
  }
  const st = statSync(final);
  // Last-Modified e ETag permitem ao telão perceber um bundle novo e recarregar sozinho.
  return new Response(Bun.file(final), {
    headers: {
      "content-type": tipoDe(final),
      "cache-control": cacheDe(raiz, final),
      "last-modified": st.mtime.toUTCString(),
      etag: `"${st.size.toString(16)}-${Math.floor(st.mtimeMs).toString(16)}"`,
    },
  });
}
