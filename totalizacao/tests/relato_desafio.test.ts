import { describe, expect, test } from "bun:test";
import { createHash } from "node:crypto";
import { BITS_PROVA, conferirDesafio, emitirDesafio, hashDesafio, TEMPO_MINIMO_MS, VALIDADE_MS, zerosIniciais } from "../src/relato/desafio.ts";
import { armadilha } from "../src/relato/validar.ts";

const SAL = "sal-de-teste";
const T0 = 1_793_000_000_000;

function minerar(desafio: string, bits: number): string {
  for (let n = 0; ; n++) {
    const h = createHash("sha256").update(desafio + String(n)).digest();
    if (zerosIniciais(new Uint8Array(h), bits)) return String(n);
  }
}

describe("zerosIniciais", () => {
  test("conta bits, não bytes", () => {
    expect(zerosIniciais(new Uint8Array([0, 0, 0x3f, 9]), 18)).toBe(true);
    expect(zerosIniciais(new Uint8Array([0, 0, 0x40, 9]), 18)).toBe(false);
    expect(zerosIniciais(new Uint8Array([0, 1, 0, 0]), 16)).toBe(false);
    expect(zerosIniciais(new Uint8Array([0, 0]), 16)).toBe(true);
    expect(BITS_PROVA).toBe(18);
  });
});

describe("desafio e prova de trabalho", () => {
  test("ciclo completo com tempo mínimo e validade", async () => {
    const d = await emitirDesafio(SAL, T0, "0".repeat(32));
    expect(d).toMatch(/^\d{13}\.[0-9a-f]{32}\.[0-9a-f]{64}$/);
    const nonce = minerar(d, 10);
    expect(await conferirDesafio(SAL, d, nonce, T0 + TEMPO_MINIMO_MS, 10)).toEqual({ ok: true, emitidoMs: T0 });
    expect(await conferirDesafio(SAL, d, nonce, T0 + TEMPO_MINIMO_MS - 1, 10)).toEqual({ ok: false, motivo: "envio rapido demais" });
    expect(await conferirDesafio(SAL, d, nonce, T0 + VALIDADE_MS + 1, 10)).toEqual({ ok: false, motivo: "desafio expirado" });
  });

  test("recusa desafio forjado, nonce errado e prova ausente", async () => {
    const d = await emitirDesafio(SAL, T0);
    const nonce = minerar(d, 8);
    const agora = T0 + 9_000;
    expect((await conferirDesafio("outro-sal", d, nonce, agora, 8)).ok).toBe(false);
    const forjado = `${String(T0 - 60_000)}${d.slice(13)}`; // carimbo trocado para burlar o tempo
    expect(await conferirDesafio(SAL, forjado, nonce, agora, 8)).toEqual({ ok: false, motivo: "desafio nao emitido por este servico" });
    let errado = Number(nonce) + 1;
    while (zerosIniciais(new Uint8Array(createHash("sha256").update(d + String(errado)).digest()), 8)) errado++;
    expect(await conferirDesafio(SAL, d, String(errado), agora, 8)).toEqual({ ok: false, motivo: "prova de trabalho invalida" });
    expect(await conferirDesafio(SAL, undefined, nonce, agora, 8)).toEqual({ ok: false, motivo: "prova ausente" });
    expect(await conferirDesafio(SAL, d, "abc", agora, 8)).toEqual({ ok: false, motivo: "prova malformada" });
  });

  test("hash de uso único é estável", async () => {
    const d = await emitirDesafio(SAL, T0, "a".repeat(32));
    expect(await hashDesafio(d)).toMatch(/^[0-9a-f]{64}$/);
    expect(await hashDesafio(d)).toBe(await hashDesafio(d));
  });
});

test("campo-armadilha", () => {
  expect(armadilha({ website: "" })).toBe("vazia");
  expect(armadilha({ website: "http://x" })).toBe("preenchida");
  expect(armadilha({})).toBe("ausente");
  expect(armadilha(null)).toBe("ausente");
});
