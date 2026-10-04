import { describe, expect, test } from "bun:test";
import { fingerprintAb, normalizarAb } from "../src/parse/normalizar.ts";
import type { AbFile } from "../src/parse/schemas.ts";
import { lerAb } from "./helpers.ts";

function clonar(p: AbFile): AbFile {
  return structuredClone(p);
}

describe("diff do -ab por município", () => {
  const base = lerAb("sp-e006257-ab.json");
  const inicial = normalizarAb(base, new Map());

  test("fingerprint = dt|ht|st|est|pst", () => {
    const a = base.abr.find((x) => x.cdabr === "71072");
    if (!a) throw new Error("sem 71072");
    expect(fingerprintAb(a)).toBe("||0|0|0,00");
  });

  test("sem mudança não gera entradas", () => {
    const n = normalizarAb(clonar(base), inicial.fingerprints);
    expect(n.primeiro).toBe(false);
    expect(n.entradas).toEqual([]);
    expect(n.mudancas).toEqual([]);
    expect(n.fingerprints).toEqual(inicial.fingerprints);
  });

  test("só o município alterado aparece; parcial não é final", () => {
    const p = clonar(base);
    const a = p.abr.find((x) => x.cdabr === "71072");
    if (!a?.s || !a.e) throw new Error("sem 71072");
    a.dt = "04/10/2026";
    a.ht = "17:20:00";
    a.s.st = "100";
    a.s.pst = "0,45";
    a.s.pstn = "0,453";
    const n = normalizarAb(p, inicial.fingerprints);
    expect(n.mudancas.length).toBe(1);
    expect(n.mudancas[0]).toMatchObject({ cdabr: "71072", tpabr: "mun", anterior: "||0|0|0,00", final: false });
    expect(n.entradas.length).toBe(1);
    expect(n.entradas[0]?.st).toBe(100);
    expect(n.entradas[0]?.pst).toBeCloseTo(0.453, 6);
    expect(n.entradas[0]?.totalizado_em).toBe("2026-10-04T20:20:00.000Z");
  });

  test("st == ts > 0 marca final", () => {
    const p = clonar(base);
    const a = p.abr.find((x) => x.cdabr === "61000");
    if (!a?.s) throw new Error("sem 61000");
    a.s.st = a.s.ts;
    a.s.pst = "100,00";
    a.ht = "19:00:00";
    const n = normalizarAb(p, inicial.fingerprints);
    expect(n.mudancas).toHaveLength(1);
    expect(n.mudancas[0]?.final).toBe(true);
  });

  test("cdabr novo entra com anterior null", () => {
    const p = clonar(base);
    const a = p.abr[0];
    if (!a) throw new Error("vazio");
    p.abr.push({ ...structuredClone(a), cdabr: "99999" });
    const n = normalizarAb(p, inicial.fingerprints);
    expect(n.mudancas.map((m) => [m.cdabr, m.anterior])).toEqual([["99999", null]]);
  });

  test("2024 contra o estado zerado: tudo muda e todos finalizados", () => {
    const n = normalizarAb(lerAb("2024/sp-e000619-ab.json"), inicial.fingerprints);
    expect(n.mudancas.length).toBe(646);
    expect(n.mudancas.filter((m) => m.tpabr === "mun").every((m) => m.final)).toBe(true);
  });
});
