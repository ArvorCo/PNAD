// Cadeia de hashes conferida contra os exemplos oficiais e contra o SHA-512 do node:crypto.
import { createHash } from "node:crypto";
import { describe, expect, test } from "bun:test";
import { sha512Hex, verificarCadeia } from "../src/qrbu/hash.ts";
import { montarQrBu } from "../src/qrbu/parse.ts";
import { EXEMPLOS, exemplo } from "./helpers.ts";

function sha512Node(texto: string): string {
  return createHash("sha512").update(texto, "ascii").digest("hex").toUpperCase();
}

describe("cadeia de hashes", () => {
  test("SHA-512 do @noble/hashes coincide com o node:crypto", () => {
    for (const t of ["", "ORIG:VOTA", "QRBU:1:1 VRQR:6.0 ".repeat(50)]) expect(sha512Hex(t)).toBe(sha512Node(t));
  });

  for (const e of EXEMPLOS) {
    test(`confere em ${e.arquivo.split("/").pop()}`, () => {
      const r = verificarCadeia(montarQrBu(e.qrbu).partes);
      expect(r.ok).toBe(true);
      expect(r.elos.length).toBe(e.qrbu.length);
      for (const elo of r.elos) expect(elo.hashCalculado).toBe(elo.hashDeclarado);
    });
  }

  test("fórmula do manual refeita à mão no exemplo de dois QR Codes, com o espaço da quebra", () => {
    const { partes } = montarQrBu(exemplo("UE2013").qrbu);
    const [p1, p2] = partes;
    if (!p1 || !p2) throw new Error("exemplo deveria ter dois QR Codes");
    expect(sha512Node(p1.dados)).toBe(p1.hash);
    expect(sha512Node(`${p1.dados} HASH:${p1.hash} ${p2.dados}`)).toBe(p2.hash);
    // Sem o espaço devolvido na junção o hash não fecha: a regra do manual é necessária.
    expect(sha512Node(`${p1.dados} HASH:${p1.hash}${p2.dados}`)).not.toBe(p2.hash);
    const r = verificarCadeia(partes);
    expect(r.ultimoHash).toBe(p2.hash);
    expect(r.conteudoEncadeado).toBe(`${p1.dados} HASH:${p1.hash} ${p2.dados} HASH:${p2.hash}`);
  });

  test("alterar um voto quebra o elo do QR Code alterado e só ele", () => {
    const e = exemplo("UE2013");
    const adulterado = e.qrbu.map((q) => (q.startsWith("QRBU:2:2") ? q.replace(" 93:2 95:1 ", " 93:3 95:1 ") : q));
    expect(adulterado).not.toEqual(e.qrbu);
    const r = verificarCadeia(montarQrBu(adulterado).partes);
    expect(r.ok).toBe(false);
    expect(r.elos.map((x) => x.confere)).toEqual([true, false]);
  });

  test("alterar o primeiro QR Code quebra também os elos seguintes, porque o hash é cumulativo", () => {
    const e = exemplo("UE2020");
    const adulterado = e.qrbu.map((q) => (q.startsWith("QRBU:1:2") ? q.replace("COMP:4 ", "COMP:5 ") : q));
    expect(adulterado).not.toEqual(e.qrbu);
    const r = verificarCadeia(montarQrBu(adulterado).partes);
    expect(r.elos.map((x) => x.confere)).toEqual([false, false]);
  });

  test("trocar o HASH declarado do primeiro QR Code quebra o primeiro e o segundo elos", () => {
    const e = exemplo("UE2022");
    const adulterado = e.qrbu.map((q) => (q.startsWith("QRBU:1:2") ? q.replace(/HASH:([0-9A-F])/, (_m, c: string) => `HASH:${c === "0" ? "1" : "0"}`) : q));
    const r = verificarCadeia(montarQrBu(adulterado).partes);
    expect(r.elos.map((x) => x.confere)).toEqual([false, false]);
  });

  test("cadeia vazia não é ok", () => {
    expect(verificarCadeia([]).ok).toBe(false);
  });
});
