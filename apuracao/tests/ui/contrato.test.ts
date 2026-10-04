// Contrato telão ↔ servidor: as respostas reais passam pelo ingresso do cliente (api.ts)
// e os eventos do /events pela tradução do sse.ts, sem depender do mock.
import { afterAll, beforeAll, describe, expect, test } from "bun:test";
import { criarServidor } from "../../src/server/main.ts";
import type { Servidor } from "../../src/server/main.ts";
import { criarApi, normalizarAnomalias, normalizarConfig, normalizarEstado } from "../../src/ui/data/api.ts";
import { lerEvento } from "../../src/ui/data/sse.ts";
import { eventoAfeta } from "../../src/ui/dados.ts";
import type { EventoSse } from "../../src/ui/state/types.ts";
import type { Semeado } from "../server-helpers.ts";
import { semear } from "../server-helpers.ts";

let sem: Semeado;
let srv: Servidor;

beforeAll(() => {
  sem = semear();
  srv = criarServidor({ dbPath: sem.path, port: 0, log: false });
});

afterAll(async () => {
  await srv.parar();
  sem.fechar();
  sem.limpar();
});

describe("ingresso do cliente contra o servidor real", () => {
  test("config: UFs em caixa alta, chaves de municípios casam com ui.uf", async () => {
    const api = criarApi(srv.url);
    const c = await api.config();
    expect(c.eleicoes).toEqual({ federal: 6257, estadual: 6259 });
    const sp = c.ufs.find(u => u.uf === "SP");
    expect(sp?.nome).toBe("São Paulo");
    expect(c.ufs.every(u => u.uf === u.uf.toUpperCase())).toBe(true);
    expect(c.ufs.length).toBe(27);
    expect(c.ufs.some(u => u.uf === "ZZ")).toBe(false);
    expect(c.municipios.SP?.some(m => m.cd === "71072" && m.c)).toBe(true);
  });

  test("estado: br preenchido e UFs em caixa alta", async () => {
    const e = await criarApi(srv.url).estado();
    expect(e.br.st).toBeGreaterThan(0);
    expect(e.ufs.find(u => u.uf === "SP")?.st).toBe(50_000);
    expect(e.ufs.find(u => u.uf === "SE")?.fechou_em).toBeTruthy();
  });

  test("anomalias: categoria vira tipo e operacionais ficam fora", async () => {
    const a = await criarApi(srv.url).anomalias();
    expect(a.length).toBeGreaterThan(0);
    expect(a.every(x => ["virada", "regressao", "fechou", "atraso"].includes(x.tipo))).toBe(true);
    expect(a.some(x => x.tipo === "regressao" && x.tipo_bruto === "regressao_contagem")).toBe(true);
  });

  test("resultado, mapa e série chegam no formato que as telas leem", async () => {
    const api = criarApi(srv.url);
    const r = await api.resultado({ ele: 6257, cargo: 1, abr: "br" });
    expect(r.cand[0]?.nmu).toBeTruthy();
    const m = await api.mapa({ ele: 6257, cargo: 1, nivel: "zona", pai: "sp71072" });
    expect(m.unidades.some(u => u.cd === "0001" && u.lider)).toBe(true);
    const s = await api.serie({ ele: 6257, cargo: 1, abr: "br" });
    expect(s.candidatos?.length).toBeGreaterThan(0);
  });
});

describe("normalizadores sem servidor", () => {
  test("estado antes do primeiro arquivo nacional", () => {
    const e = normalizarEstado({ agora: "2026-10-04T19:00:00.000Z", pronto: false, turno: 1, br: null, ufs: [{ uf: "ac", pst: 0 }] });
    expect(e.br.st).toBe(0);
    expect(e.ufs[0]?.uf).toBe("AC");
  });

  test("config vazia não quebra", () => {
    expect(normalizarConfig({ turno: 1, eleicoes: { federal: 6257, estadual: 6259 }, ufs: [], municipios: {} }).ufs).toEqual([]);
  });

  test("anomalia sem categoria conhecida some", () => {
    expect(normalizarAnomalias([{ tipo: "parse_error", categoria: "outro", texto: "x", at: "" }])).toEqual([]);
  });
});

describe("eventos do /events", () => {
  test("snapshot de resultado, de -ab e evento de anomalia", () => {
    const r = lerEvento(JSON.stringify({ kind: "resultado", ele: 6257, cargo: 1, abr: "sp", nivel: "uf", snapshot_id: 9, at: "x", pst: 12.5, tf: false }), "snapshot");
    expect(r).toMatchObject({ kind: "resultado", ele: 6257, cargo: 1, abr: "sp", pst: 12.5 });
    const ab = lerEvento(JSON.stringify({ kind: "ab", ele: 6257, cargo: null, abr: "br", snapshot_id: 10, at: "x" }), "snapshot");
    expect(ab?.cargo).toBe(0);
    const an = lerEvento(JSON.stringify({ kind: "anomalia", id: 3, at: "x", ele: 6257, cargo: 1, abr: "pr", snapshot_id: null }), "evento");
    expect(an?.kind).toBe("anomalia");
    const est = lerEvento(JSON.stringify({ kind: "estado", agora: "x", pronto: true, max_snapshot_id: 42 }), "estado");
    expect(est?.snapshot_id).toBe(42);
  });

  test("quem cada evento invalida", () => {
    const ev = (e: Partial<EventoSse>): EventoSse => ({ kind: "resultado", ele: 6257, cargo: 1, abr: "br", snapshot_id: 1, at: "", ...e });
    expect(eventoAfeta(ev({ kind: "ab", cargo: 0 }), { tipo: "estado" })).toBe(true);
    expect(eventoAfeta(ev({ kind: "ab", cargo: 0, abr: "sp" }), { tipo: "mapa", ele: 6257, cargo: 1, nivel: "mun", pai: "sp" })).toBe(true);
    expect(eventoAfeta(ev({ kind: "ab", cargo: 0, abr: "sp" }), { tipo: "mapa", ele: 6257, cargo: 1, nivel: "uf", pai: "br" })).toBe(false);
    expect(eventoAfeta(ev({}), { tipo: "estado" })).toBe(true);
    expect(eventoAfeta(ev({ abr: "sp71072-z0001" }), { tipo: "mapa", ele: 6257, cargo: 1, nivel: "zona", pai: "sp71072" })).toBe(true);
    expect(eventoAfeta(ev({ abr: "sp" }), { tipo: "mapa", ele: 6257, cargo: 1, nivel: "uf", pai: "br" })).toBe(true);
  });
});
