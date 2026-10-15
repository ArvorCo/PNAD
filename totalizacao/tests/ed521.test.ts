// Curva E-521 e EdDSA Ed521 contra os parâmetros e vetores do ECPy 8143d9ac.
import { describe, expect, test } from "bun:test";
import { asciiParaBytes, bytesParaBigIntLE, hexParaBytes } from "../src/qrbu/bytes.ts";
import { decodificarPontoEd521, desafioEd521, ED521, Ed521Ponto, verificarEd521 } from "../src/qrbu/ed521.ts";
import { mensagemAssinada } from "../src/qrbu/assinatura.ts";
import { json, exemplo, trocarHex } from "./helpers.ts";

interface Vetor {
  nome: string;
  mensagem_ascii?: string;
  mensagem_hex?: string;
  chave_publica: string;
  assinatura: string;
  x?: string;
  y?: string;
}
const VETORES = json<{ vetores: Vetor[] }>("vetores_ecpy_ed521.json").vetores;

interface Intermediario {
  arquivo: string;
  algoritmo: string;
  mensagem: string;
  chave_x: string;
  chave_y: string;
  R_x?: string;
  desafio?: string;
  S?: string;
}
const INTERMEDIARIOS = json<{ exemplos: Intermediario[] }>("intermediarios_ecpy.json").exemplos;

function mensagemDe(v: Vetor): Uint8Array {
  return v.mensagem_ascii !== undefined ? asciiParaBytes(v.mensagem_ascii) : hexParaBytes(v.mensagem_hex ?? "");
}

describe("parâmetros da curva E-521", () => {
  test("p = 2^521 − 1, d = −376014, a = 1, cofator 4", () => {
    expect(ED521.p).toBe(2n ** 521n - 1n);
    expect((ED521.d + 376014n) % ED521.p).toBe(0n);
    expect(ED521.a).toBe(1n);
    expect(ED521.h).toBe(4n);
    expect(ED521.Gy).toBe(12n);
  });

  test("gerador está na curva e tem ordem n", () => {
    const { p, d, Gx, Gy } = ED521;
    const x2 = (Gx * Gx) % p;
    const y2 = (Gy * Gy) % p;
    expect((x2 + y2 - 1n - ((d * x2) % p) * y2) % p).toBe(0n);
    const G = Ed521Ponto.BASE;
    expect(G.multiplyUnsafe(ED521.n - 1n).add(G).is0()).toBe(true);
    expect(G.multiplyUnsafe(ED521.n - 1n).is0()).toBe(false);
  });

  test("codificação de 66 bytes: y little-endian e paridade de x no bit 0x80 do último byte", () => {
    const v = VETORES[0];
    if (!v?.x || !v.y) throw new Error("vetor sem coordenadas");
    const bytes = hexParaBytes(v.chave_publica);
    expect(bytes.length).toBe(66);
    const P = decodificarPontoEd521(bytes);
    expect(P.x).toBe(BigInt(v.x));
    expect(P.y).toBe(BigInt(v.y));
    const semSinal = Uint8Array.from(bytes);
    semSinal[65] = (semSinal[65] ?? 0) & 0x7f;
    expect(bytesParaBigIntLE(semSinal)).toBe(BigInt(v.y));
    expect(((bytes[65] ?? 0) & 0x80) !== 0).toBe((BigInt(v.x) & 1n) === 1n);
    expect(Array.from(P.toBytes())).toEqual(Array.from(bytes));
  });

  test("decodificação recusa y ≥ p, comprimento errado e x = 0 com sinal", () => {
    const yGrande = new Uint8Array(66).fill(0xff);
    yGrande[65] = 0x7f;
    expect(() => decodificarPontoEd521(yGrande)).toThrow();
    expect(() => decodificarPontoEd521(new Uint8Array(65))).toThrow();
    // y = 1 é o ponto neutro (x = 0); com o bit de sinal ligado a codificação não é canônica.
    const neutroComSinal = new Uint8Array(66);
    neutroComSinal[0] = 1;
    neutroComSinal[65] = 0x80;
    expect(() => decodificarPontoEd521(neutroComSinal)).toThrow();
  });
});

describe("vetores do ECPy", () => {
  for (const v of VETORES) {
    test(`${v.nome}: válida`, () => {
      expect(verificarEd521(mensagemDe(v), hexParaBytes(v.assinatura), hexParaBytes(v.chave_publica))).toBe(true);
    });

    test(`${v.nome}: mensagem, R, S ou chave alterados reprovam`, () => {
      const msg = mensagemDe(v);
      const sig = hexParaBytes(v.assinatura);
      const chave = hexParaBytes(v.chave_publica);
      const outra = Uint8Array.from(msg);
      outra[0] = (outra[0] ?? 0) ^ 1;
      expect(verificarEd521(outra, sig, chave)).toBe(false);
      for (const pos of [0, 64, 131, 200, 262]) {
        expect(verificarEd521(msg, hexParaBytes(trocarHex(v.assinatura, pos)), chave)).toBe(false);
      }
      const outroVetor = VETORES.find((x) => x !== v);
      if (outroVetor) expect(verificarEd521(msg, sig, hexParaBytes(outroVetor.chave_publica))).toBe(false);
      expect(verificarEd521(msg, sig.subarray(0, 131), chave)).toBe(false);
    });

    test(`${v.nome}: S + n (maleabilidade aceita pelo ECPy) é recusado`, () => {
      const sig = hexParaBytes(v.assinatura);
      let s = bytesParaBigIntLE(sig.subarray(66)) + ED521.n;
      const malea = Uint8Array.from(sig);
      for (let i = 66; i < 132; i++) {
        malea[i] = Number(s & 0xffn);
        s >>= 8n;
      }
      expect(verificarEd521(mensagemDe(v), malea, hexParaBytes(v.chave_publica))).toBe(false);
    });
  }
});

describe("valores intermediários iguais aos do ECPy nos exemplos oficiais", () => {
  for (const it of INTERMEDIARIOS.filter((x) => x.algoritmo === "EdDSA Ed521")) {
    test(it.arquivo.split("/").pop() ?? it.arquivo, () => {
      const e = exemplo(it.arquivo.split("/").pop() ?? "");
      const ultimo = [...e.qrbu].sort().at(-1) ?? "";
      const hash = /HASH:([0-9A-F]{128})/.exec(ultimo)?.[1] ?? "";
      const assi = /ASSI:([0-9A-F]+)$/.exec(ultimo)?.[1] ?? "";
      const msg = mensagemAssinada(hash);
      expect(Array.from(msg)).toEqual(Array.from(hexParaBytes(it.mensagem)));
      const sig = hexParaBytes(assi);
      const R = decodificarPontoEd521(sig.subarray(0, 66));
      expect(R.x).toBe(BigInt(it.R_x ?? ""));
      expect(bytesParaBigIntLE(sig.subarray(66))).toBe(BigInt(it.S ?? ""));
      const A = Ed521Ponto.fromAffine({ x: BigInt(it.chave_x), y: BigInt(it.chave_y) });
      expect(desafioEd521(sig.subarray(0, 66), A.toBytes(), msg)).toBe(BigInt(it.desafio ?? ""));
      expect(verificarEd521(msg, sig, A.toBytes())).toBe(true);
    });
  }
});
