// Rotas do boletim falado no servidor: lista, POST restrito, no ar, fim, descartar, parar, mp3 com Range e eventos.
import { afterAll, beforeAll, describe, expect, test } from "bun:test";
import { existsSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { gravarJson, lerControle } from "../src/boletim/estado.ts";
import type { ItemIndice } from "../src/boletim/estado.ts";
import { Boletins } from "../src/server/boletins.ts";
import type { EventoBoletim } from "../src/server/boletins.ts";
import { criarServidor } from "../src/server/main.ts";
import type { Servidor } from "../src/server/main.ts";

const item = (id: string, estado: ItemIndice["estado"], criado: string, duracao = 30): ItemIndice => ({
  id, hora: `${id.slice(0, 2)}:${id.slice(2, 4)}`, estado, etapa: null, origem: "relogio", criado_em: criado, atualizado_em: criado,
  modo: "muita", palavras: 520, duracao_s: duracao, resumo: `${id} resumo`, erro: null,
});

const H = { "x-apuracao": "boletim" };
let dir: string;
let srv: Servidor;
const eventos: EventoBoletim[] = [];

beforeAll(() => {
  dir = mkdtempSync(join(tmpdir(), "bol-srv-"));
  gravarJson(join(dir, "indice.json"), { atualizado_em: "", itens: [item("1710", "pronto", "2026-10-25T20:10:00Z"), item("1720", "pronto", "2026-10-25T20:20:00Z"), item("1730", "gerando", "2026-10-25T20:30:00Z")] });
  const bytes = new Uint8Array(5000).map((_, i) => i % 251);
  writeFileSync(join(dir, "1710.mp3"), bytes);
  writeFileSync(join(dir, "1720.mp3"), bytes);
  writeFileSync(join(dir, "1720.txt"), "[calm] Dezessete e vinte.\n");
  gravarJson(join(dir, "1720.meta.json"), { id: "1720", tempos: { total_ms: 1 } });
  srv = criarServidor({ dbPath: join(dir, "nao-existe.sqlite"), port: 0, log: false, boletimDir: dir });
  srv.ctx.boletins?.assinar(e => eventos.push(e));
});

afterAll(async () => {
  await srv.parar();
});

const post = (p: string, headers: Record<string, string> = H): Promise<Response> => fetch(srv.url + p, { method: "POST", headers });

describe("rotas do boletim", () => {
  test("lista sem o gerador no ar e detalhe com texto, meta e mp3", async () => {
    const l = (await (await fetch(`${srv.url}/api/boletins`)).json()) as { gerador: { vivo: boolean }; itens: { id: string; estado: string }[]; no_ar: unknown };
    expect(l.gerador.vivo).toBe(false);
    expect(l.no_ar).toBeNull();
    expect(l.itens.map(i => i.id)).toEqual(["1730", "1720", "1710"]);
    const d = (await (await fetch(`${srv.url}/api/boletins/1720`)).json()) as { texto: string; meta: { id: string }; mp3: string };
    expect(d.texto).toContain("Dezessete e vinte");
    expect(d.meta.id).toBe("1720");
    expect(d.mp3).toBe("/boletins/1720.mp3");
    expect((await fetch(`${srv.url}/api/boletins/9999`)).status).toBe(404);
  });

  test("POST exige o cabeçalho da casa e origem local; GET e HEAD continuam no resto da API", async () => {
    expect((await post("/api/boletins/1720/tocar", {})).status).toBe(403);
    expect((await post("/api/boletins/1720/tocar", { ...H, origin: "https://exemplo.com" })).status).toBe(403);
    expect((await fetch(`${srv.url}/api/estado`, { method: "POST" })).status).toBe(405);
    const b = new Boletins(dir);
    const r = b.responder(new Request("http://x/api/boletins/parar", { method: "POST", headers: H }), new URL("http://x/api/boletins/parar"), "192.168.0.9");
    expect(r?.status).toBe(403);
  });

  test("gerar: 503 sem gerador, 409 gerando, 202 grava o pedido", async () => {
    expect((await post("/api/boletins/gerar")).status).toBe(503);
    const g = { pid: 1, iniciado_em: "", batimento_em: new Date().toISOString(), relogio_ligado: true, intervalo_s: 600, inicio_em: "", proximo_ciclo_em: null, gerando: "1730", etapa: "roteiro", ultimo_erro: null };
    gravarJson(join(dir, "gerador.json"), g);
    expect((await post("/api/boletins/gerar")).status).toBe(409);
    gravarJson(join(dir, "gerador.json"), { ...g, gerando: null });
    expect((await post("/api/boletins/gerar")).status).toBe(202);
    expect(existsSync(join(dir, "pedido.json"))).toBe(true);
  });

  test("tocar, trocar, fim do player, parar e descartar", async () => {
    eventos.length = 0;
    expect((await post("/api/boletins/1730/tocar")).status).toBe(409);
    expect((await post("/api/boletins/1710/tocar")).status).toBe(200);
    expect(lerControle(dir).no_ar?.id).toBe("1710");
    expect((await post("/api/boletins/1720/tocar")).status).toBe(200);
    expect(eventos.map(e => [e.kind, e.id])).toEqual([["no_ar", "1710"], ["fim", "1710"], ["no_ar", "1720"]]);
    const fimErrado = (await (await post("/api/boletins/1710/fim")).json()) as { efeito: boolean };
    expect(fimErrado.efeito).toBe(false);
    const fim = (await (await post("/api/boletins/1720/fim")).json()) as { efeito: boolean };
    expect(fim.efeito).toBe(true);
    let l = (await (await fetch(`${srv.url}/api/boletins`)).json()) as { itens: { id: string; estado: string }[]; no_ar: unknown };
    expect(l.no_ar).toBeNull();
    expect(l.itens.find(i => i.id === "1720")?.estado).toBe("tocado");
    expect((await post("/api/boletins/1720/tocar")).status).toBe(200);
    expect((await (await post("/api/boletins/parar")).json()) as { parado: string }).toEqual({ ok: true, parado: "1720" } as never);
    expect((await post("/api/boletins/1710/descartar")).status).toBe(200);
    l = (await (await fetch(`${srv.url}/api/boletins`)).json()) as { itens: { id: string; estado: string }[]; no_ar: unknown };
    expect(l.itens.some(i => i.id === "1710")).toBe(false);
  });

  test("mp3 inteiro e por faixa", async () => {
    const r = await fetch(`${srv.url}/boletins/1720.mp3`);
    expect(r.status).toBe(200);
    expect(r.headers.get("accept-ranges")).toBe("bytes");
    expect(r.headers.get("content-type")).toBe("audio/mpeg");
    expect((await r.arrayBuffer()).byteLength).toBe(5000);
    const p = await fetch(`${srv.url}/boletins/1720.mp3`, { headers: { range: "bytes=100-199" } });
    expect(p.status).toBe(206);
    expect(p.headers.get("content-range")).toBe("bytes 100-199/5000");
    const corpo = new Uint8Array(await p.arrayBuffer());
    expect(corpo.length).toBe(100);
    expect(corpo[0]).toBe(100 % 251);
    const sufixo = await fetch(`${srv.url}/boletins/1720.mp3`, { headers: { range: "bytes=-10" } });
    expect(sufixo.headers.get("content-range")).toBe("bytes 4990-4999/5000");
    expect((await fetch(`${srv.url}/boletins/1720.mp3`, { headers: { range: "bytes=9000-" } })).status).toBe(416);
    expect((await fetch(`${srv.url}/boletins/..%2Findice.mp3`)).status).toBe(404);
  });

  test("observador: pronto vira evento e boletim esquecido no ar encerra pelo tempo", () => {
    const d2 = mkdtempSync(join(tmpdir(), "bol-obs-"));
    let agora = Date.parse("2026-10-25T20:40:00Z");
    const b = new Boletins(d2, () => agora);
    const evs: EventoBoletim[] = [];
    b.assinar(e => evs.push(e));
    gravarJson(join(d2, "indice.json"), { atualizado_em: "", itens: [item("1740", "gerando", "2026-10-25T20:40:00Z")] });
    b.observar();
    expect(evs).toEqual([]);
    Bun.sleepSync(5);
    gravarJson(join(d2, "indice.json"), { atualizado_em: "x", itens: [item("1740", "pronto", "2026-10-25T20:40:00Z")] });
    b.observar();
    expect(evs.map(e => e.kind)).toEqual(["pronto"]);
    gravarJson(join(d2, "controle.json"), { atualizado_em: "", no_ar: { id: "1740", desde: "2026-10-25T20:41:00Z", duracao_s: 30 }, tocados: {}, descartados: {} });
    agora = Date.parse("2026-10-25T20:41:59Z");
    b.observar();
    expect(lerControle(d2).no_ar?.id).toBe("1740");
    agora = Date.parse("2026-10-25T20:42:01Z");
    b.observar();
    expect(lerControle(d2).no_ar).toBeNull();
    expect(evs.at(-1)).toEqual({ kind: "fim", id: "1740", motivo: "tempo" });
  });
});

describe("SSE", () => {
  test("so=boletim entrega o evento boletim", async () => {
    const ctrl = new AbortController();
    const r = await fetch(`${srv.url}/events?so=boletim`, { signal: ctrl.signal });
    const leitor = r.body?.getReader();
    expect(leitor).toBeDefined();
    await post("/api/boletins/1720/tocar");
    let texto = "";
    const dec = new TextDecoder();
    const limite = Date.now() + 3000;
    while (!texto.includes("event: boletim") && Date.now() < limite) {
      const { value, done } = (await leitor?.read()) ?? { value: undefined, done: true };
      if (done) break;
      texto += dec.decode(value);
    }
    ctrl.abort();
    expect(texto).toContain("event: boletim");
    expect(texto).toContain('"kind":"no_ar"');
    expect(texto).not.toContain("event: snapshot");
    await post("/api/boletins/parar");
  });
});
