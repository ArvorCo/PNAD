import { describe, expect, test } from "bun:test";
import { readdirSync } from "node:fs";
import { join } from "node:path";
import { detectarDrift } from "../src/parse/drift.ts";
import { pareceJson, parseCorpo, parseJson } from "../src/parse/schemas.ts";
import type { Tipo } from "../src/types.ts";
import { FIXTURES, bytes, json } from "./helpers.ts";

function tipoDe(nome: string): Tipo | null {
  if (nome === "ele-c.json") return "ele-c";
  if (nome.endsWith("-cm.json")) return "cm";
  if (nome.endsWith("-ab.json")) return "ab";
  if (nome.endsWith("-u.json")) return "u";
  if (nome.endsWith("-e.json")) return "e";
  return null;
}

const arquivos = [
  ...readdirSync(FIXTURES).filter((f) => f.endsWith(".json")),
  ...readdirSync(join(FIXTURES, "2024")).map((f) => `2024/${f}`),
]
  .map((f) => ({ f, tipo: tipoDe(f.split("/").pop() ?? "") }))
  .filter((x): x is { f: string; tipo: Tipo } => x.tipo !== null);

describe("todas as fixtures reais", () => {
  test("cobre os cinco tipos", () => {
    expect(new Set(arquivos.map((a) => a.tipo))).toEqual(new Set<Tipo>(["ele-c", "cm", "ab", "u", "e"]));
    expect(arquivos.length).toBe(20);
  });
  for (const { f, tipo } of arquivos) {
    test(`${f} passa no esquema e não tem drift`, () => {
      const r = parseCorpo(tipo, bytes(f));
      expect(r.ok).toBe(true);
      expect(detectarDrift(tipo, json(f))).toEqual({ desconhecidos: [], divergentes: [] });
    });
  }
});

describe("drift", () => {
  test("chave desconhecida é preservada pelo passthrough e reportada", () => {
    const j = json("2024/sp71072-c0013-e000619-u.json") as Record<string, unknown> & {
      carg: Array<Record<string, unknown> & { agr: Array<{ par: Array<{ cand: Array<Record<string, unknown>> }> }> }>;
    };
    j.novidade = "x";
    const c0 = j.carg[0];
    if (!c0) throw new Error("sem cargo");
    const cand = c0.agr[0]?.par[0]?.cand[0];
    if (!cand) throw new Error("sem candidato");
    cand.campoNovo = "1";
    const r = parseJson("u", j);
    expect(r.ok).toBe(true);
    if (!r.ok || r.parsed.tipo !== "u") throw new Error("tipo");
    expect((r.parsed.data as Record<string, unknown>).novidade).toBe("x");
    const d = detectarDrift("u", j);
    expect(d.desconhecidos).toEqual(["$.carg[].agr[].par[].cand[].campoNovo", "$.novidade"]);
  });
  test("tipo divergente e obrigatório ausente", () => {
    const j = json("br-c0001-e006257-u.json") as Record<string, unknown>;
    j.dg = 3;
    delete j.carg;
    expect(parseJson("u", j).ok).toBe(false);
    const d = detectarDrift("u", j);
    expect(d.divergentes).toContain("$.dg");
    expect(d.divergentes).toContain("$.carg");
  });
  test("número no lugar de string é tolerado pelo leniente", () => {
    const j = json("br-c0001-e006257-u.json") as Record<string, unknown>;
    j.idg = 1079360;
    const r = parseJson("u", j);
    expect(r.ok).toBe(true);
    if (r.ok && r.parsed.tipo === "u") expect(r.parsed.data.idg).toBe("1079360");
  });
});

describe("corpos de erro", () => {
  test("XML do bucket e HTML do Akamai não são JSON", () => {
    for (const f of ["erros/nosuchkey.xml", "erros/access-denied.html"]) {
      expect(pareceJson(bytes(f))).toBe(false);
      const r = parseCorpo("u", bytes(f));
      expect(r.ok).toBe(false);
      if (!r.ok) expect(r.erro).toBe("corpo não é JSON");
    }
  });
  test("JSON truncado vira erro, não exceção", () => {
    const r = parseCorpo("ab", '{"ele":"6257","abr":[');
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.erro).toStartWith("JSON inválido");
  });
});
