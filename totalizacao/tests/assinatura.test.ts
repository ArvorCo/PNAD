// Assinatura ASSI: ECDSA P-521 (urnas 2013/2015) e EdDSA Ed521 (urnas 2020/2022).
import { describe, expect, test } from "bun:test";
import { p521 } from "@noble/curves/nist.js";
import { sha512 } from "@noble/hashes/sha2.js";
import { mensagemAssinada, verificarAssinatura } from "../src/qrbu/assinatura.ts";
import { asciiParaBytes, bytesParaHex, hexParaBytes } from "../src/qrbu/bytes.ts";
import { montarCertificado, OID } from "../src/qrbu/certificado.ts";
import { lerAssinaturaEcdsa, ORDEM_P521 } from "../src/qrbu/ecdsa.ts";
import { montarQrBu } from "../src/qrbu/parse.ts";
import { EXEMPLOS, exemplo, json, trocarHex } from "./helpers.ts";

function hashEAssi(trecho: string): { hash: string; assi: string } {
  const m = montarQrBu(exemplo(trecho).qrbu);
  return { hash: m.ultimoHash, assi: m.assinatura ?? "" };
}

interface Intermediario {
  arquivo: string;
  algoritmo: string;
  mensagem: string;
  chave_x: string;
  chave_y: string;
  r?: string;
  s?: string;
}

describe("assinatura do boletim", () => {
  for (const e of EXEMPLOS) {
    test(`válida em ${e.arquivo.split("/").pop()}`, () => {
      const m = montarQrBu(e.qrbu);
      const cert = montarCertificado(e.qrce);
      const r = verificarAssinatura(m.ultimoHash, m.assinatura ?? "", cert);
      expect(r).toEqual({ valido: true, algoritmo: ["2013", "2015"].includes(cert.modelo) ? "ECDSA P-521" : "EdDSA Ed521", motivo: null });
    });
  }

  test("a mensagem é o SHA-512 dos bytes do HASH, não do texto hexadecimal", () => {
    const { hash, assi } = hashEAssi("UE2013");
    const cert = montarCertificado(exemplo("UE2013").qrce);
    expect(bytesParaHex(mensagemAssinada(hash))).toBe(bytesParaHex(sha512(hexParaBytes(hash))));
    const opcoes = { prehash: false, lowS: false, format: "der" } as const;
    expect(p521.verify(hexParaBytes(assi), sha512(hexParaBytes(hash)), cert.chavePublica.bytes, opcoes)).toBe(true);
    expect(p521.verify(hexParaBytes(assi), sha512(asciiParaBytes(hash)), cert.chavePublica.bytes, opcoes)).toBe(false);
    expect(p521.verify(hexParaBytes(assi), hexParaBytes(hash), cert.chavePublica.bytes, opcoes)).toBe(false);
  });

  test("ECDSA: r, s e chave pública iguais aos do ECPy", () => {
    const itens = json<{ exemplos: Intermediario[] }>("intermediarios_ecpy.json").exemplos.filter((x) => x.algoritmo === "ECDSA P-521");
    expect(itens.length).toBe(2);
    for (const it of itens) {
      const nome = it.arquivo.split("/").pop() ?? "";
      const { hash, assi } = hashEAssi(nome);
      const sig = p521.Signature.fromBytes(hexParaBytes(assi), "der");
      expect(sig.r).toBe(BigInt(it.r ?? ""));
      expect(sig.s).toBe(BigInt(it.s ?? ""));
      const ponto = p521.Point.fromBytes(montarCertificado(exemplo(nome).qrce).chavePublica.bytes);
      expect(ponto.x).toBe(BigInt(it.chave_x));
      expect(ponto.y).toBe(BigInt(it.chave_y));
      expect(bytesParaHex(mensagemAssinada(hash))).toBe(it.mensagem);
    }
  });

  test("ECDSA com s alto (n − s) continua válida, como no ECPy", () => {
    const { hash, assi } = hashEAssi("UE2015");
    const cert = montarCertificado(exemplo("UE2015").qrce);
    const sig = p521.Signature.fromBytes(hexParaBytes(assi), "der");
    const alto = new p521.Signature(sig.r, ORDEM_P521 - sig.s).toBytes("der");
    expect(verificarAssinatura(hash, bytesParaHex(alto), cert).valido).toBe(true);
  });

  test("DER com zero à esquerda não mínimo é aceito, como no ECPy; bytes excedentes e r fora de [1, n) não", () => {
    const { hash, assi } = hashEAssi("UE2013");
    const cert = montarCertificado(exemplo("UE2013").qrce);
    // r passa de "02 42 01EF..." para "02 43 00 01EF..."; o ECPy 8143d9ac aceita esta forma (conferido no scratch).
    const naoMinimo = `308189024300${assi.slice(10)}`;
    expect(assi.startsWith("308188024201")).toBe(true);
    expect(lerAssinaturaEcdsa(hexParaBytes(naoMinimo))).toEqual(lerAssinaturaEcdsa(hexParaBytes(assi)));
    expect(verificarAssinatura(hash, naoMinimo, cert).valido).toBe(true);
    expect(verificarAssinatura(hash, `${assi}00`, cert).valido).toBe(false);
    const rs = lerAssinaturaEcdsa(hexParaBytes(assi));
    if (!rs) throw new Error("assinatura do exemplo deveria ser legível");
    const der = (r: bigint, s: bigint): string => {
      const inteiro = (n: bigint): string => {
        const h = n.toString(16).padStart(2, "0");
        const corpo = (h.length % 2 ? "0" : "") + h;
        return `02${(corpo.length / 2).toString(16).padStart(2, "0")}${corpo}`;
      };
      const corpo = inteiro(r) + inteiro(s);
      return `30${corpo.length / 2 >= 0x80 ? "81" : ""}${(corpo.length / 2).toString(16).padStart(2, "0")}${corpo}`.toUpperCase();
    };
    expect(verificarAssinatura(hash, der(rs.r, rs.s), cert).valido).toBe(true);
    expect(verificarAssinatura(hash, der(0n, rs.s), cert).valido).toBe(false);
    expect(verificarAssinatura(hash, der(rs.r + ORDEM_P521, rs.s), cert).valido).toBe(false);
    expect(verificarAssinatura(hash, der(rs.r, rs.s + ORDEM_P521), cert).valido).toBe(false);
  });

  for (const trecho of ["UE2013", "UE2020", "UE2022"]) {
    test(`${trecho}: trocar um dígito de ASSI reprova a assinatura`, () => {
      const { hash, assi } = hashEAssi(trecho);
      const cert = montarCertificado(exemplo(trecho).qrce);
      const posicoes = [0, 7, 20, Math.floor(assi.length / 2), Math.floor(assi.length / 2) + 9, assi.length - 3, assi.length - 1];
      for (const pos of posicoes) {
        const r = verificarAssinatura(hash, trocarHex(assi, pos), cert);
        expect(r.valido).toBe(false);
        expect(r.motivo).not.toBeNull();
      }
    });

    test(`${trecho}: trocar um dígito do último HASH reprova a assinatura`, () => {
      const { hash, assi } = hashEAssi(trecho);
      const cert = montarCertificado(exemplo(trecho).qrce);
      expect(verificarAssinatura(trocarHex(hash, 50), assi, cert).valido).toBe(false);
    });
  }

  test("certificado de outra urna, com outra chave, reprova", () => {
    const pares: [string, string][] = [["UE2013", "UE2015"], ["UE2015", "UE2013"], ["UE2020", "UE2022"], ["UE2022", "UE2020"], ["UE2013", "UE2022"], ["UE2022", "UE2013"]];
    for (const [bu, cert] of pares) {
      const { hash, assi } = hashEAssi(bu);
      const r = verificarAssinatura(hash, assi, montarCertificado(exemplo(cert).qrce));
      expect(r.valido).toBe(false);
    }
  });

  test("algoritmo de chave desconhecido e hexadecimal malformado não lançam", () => {
    const { hash, assi } = hashEAssi("UE2022");
    const cert = montarCertificado(exemplo("UE2022").qrce);
    const estranho = { chavePublica: { ...cert.chavePublica, algoritmo: "1.2.3.4" } };
    expect(verificarAssinatura(hash, assi, estranho)).toEqual({ valido: false, algoritmo: null, motivo: "algoritmo de chave não suportado: 1.2.3.4" });
    const curvaErrada = { chavePublica: { ...cert.chavePublica, algoritmo: OID.EC_PUBLIC_KEY, parametro: "1.2.840.10045.3.1.7" } };
    expect(verificarAssinatura(hash, assi, curvaErrada).algoritmo).toBeNull();
    expect(verificarAssinatura(hash, `${assi}0`, cert).valido).toBe(false);
    expect(verificarAssinatura("XYZ", assi, cert).valido).toBe(false);
    const chaveCurta = { chavePublica: { ...cert.chavePublica, bytes: cert.chavePublica.bytes.subarray(1) } };
    expect(verificarAssinatura(hash, assi, chaveCurta).valido).toBe(false);
  });
});
