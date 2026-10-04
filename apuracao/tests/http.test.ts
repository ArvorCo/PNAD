import { afterAll, describe, expect, test } from "bun:test";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { BASE_URL } from "../src/config.ts";
import { classificar, fetchTse, resolverUrl, retryAfterS } from "../src/collector/http.ts";
import { FIXTURES } from "./helpers.ts";

const corpo = readFileSync(join(FIXTURES, "br-c0001-e006257-u.json"));
const xml404 = readFileSync(join(FIXTURES, "erros/nosuchkey.xml"));
const negado = readFileSync(join(FIXTURES, "erros/access-denied.html"));
const vistos: Record<string, string | null>[] = [];

const tse = Bun.serve({
  port: 0,
  async fetch(req) {
    const p = new URL(req.url).pathname;
    vistos.push({ path: p, inm: req.headers.get("if-none-match"), ims: req.headers.get("if-modified-since"), ua: req.headers.get("user-agent") });
    switch (p) {
      case "/oficial/ok.json":
        if (req.headers.get("if-none-match") === '"abc"') return new Response(null, { status: 304, headers: { etag: '"abc"' } });
        return new Response(Bun.gzipSync(corpo), {
          headers: {
            "content-type": "application/json", "content-encoding": "gzip", etag: '"abc"', "last-modified": "Sat, 03 Oct 2026 17:48:37 GMT",
            "cache-control": "max-age=57", age: "12", "x-cache": "TCP_HIT", "x-ratelimit-limit": "2000;w=1", "x-ratelimit-remaining": "1999",
          },
        });
      case "/oficial/negado":
        return new Response(negado, { status: 403, headers: { "content-type": "text/html" } });
      case "/oficial/limite":
        return new Response("slow down", { status: 429, headers: { "retry-after": "7" } });
      case "/oficial/lento":
        await Bun.sleep(400);
        return new Response("{}");
      case "/oficial/html":
        return new Response("<html>manutenção</html>", { headers: { "content-type": "text/html" } });
      case "/oficial/quebrado":
        return new Response("erro", { status: 503 });
      default:
        return new Response(xml404, { status: 404, headers: { "content-type": "application/xml" } });
    }
  },
});
const base = `http://localhost:${tse.port}/oficial`;
const opts = { baseUrl: base, timeoutMs: 2000, ua: "Teste/1.0" };
const job = (path: string, motivo: "periodico" | "final" = "periodico"): { url: string; motivo: "periodico" | "final" } => ({ url: `${BASE_URL}${path}`, motivo });

afterAll(() => void tse.stop(true));

describe("fetchTse contra TSE falso", () => {
  test("200 gzip: corpo decodificado, sha, cabeçalhos", async () => {
    const r = await fetchTse(job("/ok.json"), null, opts);
    expect(r.classe).toBe("ok");
    expect(r.bytes).toBe(corpo.byteLength);
    expect(r.bodySha256).toHaveLength(64);
    expect(r.etag).toBe('"abc"');
    expect(r.lastModified).toBe("Sat, 03 Oct 2026 17:48:37 GMT");
    expect(r.age).toBe(12);
    expect(r.cacheHdr).toContain("cc=max-age=57");
    expect(r.cacheHdr).toContain("x-cache=TCP_HIT");
    expect(r.cacheHdr).toContain("rlr=1999");
    expect(r.condicional).toBe(false);
    expect(vistos.at(-1)?.ua).toBe("Teste/1.0");
  });

  test("If-None-Match conhecido vira 304", async () => {
    const r = await fetchTse(job("/ok.json"), { etag: '"abc"', lastModified: "Sat, 03 Oct 2026 17:48:37 GMT" }, opts);
    expect(r.classe).toBe("nao_modificado");
    expect(r.condicional).toBe(true);
    expect(r.body).toBeNull();
    expect(vistos.at(-1)?.ims).toBe("Sat, 03 Oct 2026 17:48:37 GMT");
  });

  test("motivo final e APURACAO_SEM_CONDICIONAL ignoram validadores", async () => {
    const v = { etag: '"abc"', lastModified: null };
    expect((await fetchTse(job("/ok.json", "final"), v, opts)).classe).toBe("ok");
    expect(vistos.at(-1)?.inm).toBeNull();
    expect((await fetchTse(job("/ok.json"), v, { ...opts, semCondicional: true })).classe).toBe("ok");
    expect(vistos.at(-1)?.inm).toBeNull();
  });

  test("XML NoSuchKey é nao_existe", async () => {
    const r = await fetchTse(job("/sumiu.json"), null, opts);
    expect(r.classe).toBe("nao_existe");
    expect(r.httpStatus).toBe(404);
    expect(r.bodySha256).toBeNull();
  });

  test("403 HTML é negado; 429 traz Retry-After", async () => {
    expect((await fetchTse(job("/negado"), null, opts)).classe).toBe("negado");
    const r = await fetchTse(job("/limite"), null, opts);
    expect(r.classe).toBe("limite");
    expect(r.retryAfterS).toBe(7);
  });

  test("timeout, 5xx e 200 não JSON", async () => {
    expect((await fetchTse(job("/lento"), null, { ...opts, timeoutMs: 100 })).classe).toBe("timeout");
    expect((await fetchTse(job("/quebrado"), null, opts)).classe).toBe("erro_servidor");
    expect((await fetchTse(job("/html"), null, opts)).classe).toBe("corpo_invalido");
  });

  test("falha de conexão é erro_rede", async () => {
    const r = await fetchTse(job("/ok.json"), null, { ...opts, baseUrl: "http://127.0.0.1:1/oficial" });
    expect(r.classe).toBe("erro_rede");
    expect(r.erro).not.toBeNull();
  });
});

describe("auxiliares HTTP", () => {
  test("classificar pelo corpo", () => {
    const t = (s: string): Uint8Array => new TextEncoder().encode(s);
    expect(classificar(200, t("\n{ \"a\": 1 }"))).toBe("ok");
    expect(classificar(403, xml404)).toBe("nao_existe");
    expect(classificar(200, negado)).toBe("negado");
    expect(classificar(418, t(""))).toBe("erro_rede");
  });

  test("resolverUrl e Retry-After em data", () => {
    expect(resolverUrl(`${BASE_URL}/x.json`, "http://h/o")).toBe("http://h/o/x.json");
    expect(resolverUrl(`${BASE_URL}/x.json`, undefined)).toBe(`${BASE_URL}/x.json`);
    expect(retryAfterS("Sun, 04 Oct 2026 20:00:30 GMT", Date.parse("2026-10-04T20:00:00Z"))).toBe(30);
    expect(retryAfterS("", 0)).toBeNull();
  });
});
