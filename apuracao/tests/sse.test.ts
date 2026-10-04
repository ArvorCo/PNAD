// /events: novo snapshot chega em menos de 1 s; Last-Event-ID retoma; filtros de nível; eventos warn.
import { afterAll, beforeAll, describe, expect, test } from "bun:test";
import { criarServidor } from "../src/server/main.ts";
import type { Servidor } from "../src/server/main.ts";
import { conexoesSse } from "../src/server/sse.ts";
import type { Semeado } from "./server-helpers.ts";
import { CHAVES, iso, seg, semear, versaoU } from "./server-helpers.ts";

interface Ev {
  id: string | null;
  event: string;
  data: Record<string, unknown>;
}

interface Conexao {
  eventos(): Ev[];
  esperar(pred: (e: Ev) => boolean, ms?: number): Promise<Ev>;
  fechar(): void;
}

async function conectar(url: string, headers: Record<string, string> = {}): Promise<Conexao> {
  const ac = new AbortController();
  const res = await fetch(url, { headers, signal: ac.signal });
  expect(res.headers.get("content-type")).toContain("text/event-stream");
  const body = res.body;
  if (!body) throw new Error("sem corpo");
  const reader = body.getReader();
  const dec = new TextDecoder();
  let buf = "";
  void (async () => {
    try {
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += dec.decode(value, { stream: true });
      }
    } catch {
      // abortado
    }
  })();
  const eventos = (): Ev[] =>
    buf
      .split("\n\n")
      .filter((b) => b.includes("data: "))
      .map((b) => {
        const linhas = b.split("\n");
        const campo = (k: string): string | null => linhas.find((l) => l.startsWith(`${k}: `))?.slice(k.length + 2) ?? null;
        return { id: campo("id"), event: campo("event") ?? "message", data: JSON.parse(campo("data") ?? "{}") as Record<string, unknown> };
      });
  return {
    eventos,
    async esperar(pred, ms = 1000) {
      const fim = Date.now() + ms;
      while (Date.now() < fim) {
        const e = eventos().find(pred);
        if (e) return e;
        await Bun.sleep(20);
      }
      throw new Error(`evento não chegou em ${ms} ms; recebidos: ${eventos().map((e) => `${e.event}:${e.id ?? ""}`).join(",")}`);
    },
    fechar: () => ac.abort(),
  };
}

let s: Semeado;
let srv: Servidor;

beforeAll(() => {
  s = semear();
  srv = criarServidor({ dbPath: s.path, port: 0, log: false, sse: { pollMs: 100, heartbeatMs: 300 } });
});

afterAll(async () => {
  s.fechar();
  await srv.parar();
  s.limpar();
});

describe("SSE", () => {
  test("snapshot novo chega em menos de 1 s; estado periódico", async () => {
    const c = await conectar(`${srv.url}/events`);
    try {
      await c.esperar((e) => e.event === "estado");
      const antes = c.eventos().filter((e) => e.event === "snapshot").length;
      expect(antes).toBe(0);
      const t = performance.now();
      s.seq.processar(CHAVES.presBr, versaoU("br-c0001-e006257-u.json", { st: 250_000, votos: { 13: 1, 22: 2 }, idg: 1_200_000, ger: seg(700), tot: seg(690) }), iso(seg(710)));
      const ev = await c.esperar((e) => e.event === "snapshot");
      expect(performance.now() - t).toBeLessThan(1000);
      expect(ev.data).toMatchObject({ kind: "resultado", ele: 6257, cargo: 1, abr: "br", nivel: "br", at: iso(seg(710)), tf: false });
      expect(ev.id).toBe(String(ev.data.snapshot_id));
      expect(ev.data.pst).toBeCloseTo((250_000 / 499_248) * 100, 2);
      const estados = c.eventos().filter((e) => e.event === "estado");
      await c.esperar((e) => e.event === "estado" && c.eventos().filter((x) => x.event === "estado").length > estados.length, 1000);
    } finally {
      c.fechar();
    }
  });

  test("Last-Event-ID retoma; município e zona só com tudo=1", async () => {
    const desde = String(s.id("presBr2"));
    const c = await conectar(`${srv.url}/events`, { "Last-Event-ID": desde });
    const t = await conectar(`${srv.url}/events?tudo=1`, { "Last-Event-ID": desde });
    try {
      await c.esperar((e) => e.id === String(s.id("presSp2")));
      const ids = c.eventos().filter((e) => e.event === "snapshot").map((e) => Number(e.id));
      expect(ids).toContain(s.id("presBr3"));
      expect(ids).toContain(s.id("abBr1"));
      expect(ids).not.toContain(s.id("presBrRegressivo"));
      expect(ids).not.toContain(s.id("presMun1"));
      expect(ids.every((id) => id > Number(desde))).toBe(true);
      expect(c.eventos().find((e) => e.id === String(s.id("abBr1")))?.data.kind).toBe("ab");
      await t.esperar((e) => e.id === String(s.id("presMun1")));
      await t.esperar((e) => e.id === String(s.id("presZona1")));
    } finally {
      c.fechar();
      t.fechar();
    }
  });

  test("evento warn vira event: evento; info não", async () => {
    const c = await conectar(`${srv.url}/events?nivel=br`);
    try {
      await c.esperar((e) => e.event === "estado");
      s.seq.gravar([
        { k: "evento", row: { em: iso(seg(720)), tipo: "municipio_finalizado", severidade: "info", uf: "sp", municipio_cd: "71072", nivel: "mu" } },
        { k: "evento", row: { em: iso(seg(721)), tipo: "regressao_pst", severidade: "warn", uf: "pr", nivel: "uf", cargo_cd: 1, eleicao_cd: 6257 } },
      ]);
      const ev = await c.esperar((e) => e.event === "evento");
      expect(ev.data).toMatchObject({ kind: "anomalia", tipo: "regressao_pst", abr: "pr", texto: "Regressão do percentual de seções em Paraná (presidente)" });
      expect(c.eventos().filter((e) => e.event === "evento").length).toBe(1);
    } finally {
      c.fechar();
    }
  });

  test("conexões fechadas liberam recursos", async () => {
    const c = await conectar(`${srv.url}/events`);
    await c.esperar((e) => e.event === "estado");
    const abertas = conexoesSse();
    c.fechar();
    const fim = Date.now() + 1000;
    while (conexoesSse() >= abertas && Date.now() < fim) await Bun.sleep(20);
    expect(conexoesSse()).toBeLessThan(abertas);
  });
});
