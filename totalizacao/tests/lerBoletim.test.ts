// lerBoletim de ponta a ponta: exemplos oficiais, adulterações e um boletim forjado completo.
import { describe, expect, test } from "bun:test";
import { p521 } from "@noble/curves/nist.js";
import { sha512 } from "@noble/hashes/sha2.js";
import { lerBoletim } from "../src/index.ts";
import { bytesParaHex, concatenar } from "../src/qrbu/bytes.ts";
import { montarCertificado } from "../src/qrbu/certificado.ts";
import { lerTlv } from "../src/qrbu/der.ts";
import { CHAVE_FORJADA, EXEMPLOS, PUBLICA_FORJADA, assinarComoUrna, exemplo, qrceDe, refazerCadeia, tlv, trocarAssi, trocarHex } from "./helpers.ts";

const SIMULADO = { faseEsperada: "S" } as const;

function codigos(r: ReturnType<typeof lerBoletim>): string[] {
  return r.problemas.map((p) => p.codigo);
}

/** Certificado de urna 2013 com a chave do falsificador, reassinado por ele, nos QR Codes QRCE. */
function qrceForjado(): string[] {
  const cert = montarCertificado(exemplo("UE2013").qrce);
  const inicioTbs = cert.tbs.byteOffset - cert.der.byteOffset;
  const tbs = Uint8Array.from(cert.tbs);
  tbs.set(PUBLICA_FORJADA, cert.chavePublica.bytes.byteOffset - cert.der.byteOffset - inicioTbs);
  const algId = lerTlv(cert.der, inicioTbs + cert.tbs.length).bruto;
  const assinatura = p521.sign(sha512(tbs), CHAVE_FORJADA, { prehash: false, lowS: false, format: "der" });
  const der = tlv(0x30, concatenar(tbs, algId, tlv(0x03, concatenar(new Uint8Array([0]), assinatura))));
  return qrceDe(bytesParaHex(der), cert.idue, cert.modelo);
}

describe("lerBoletim", () => {
  for (const e of EXEMPLOS) {
    test(`autêntico e válido: ${e.arquivo.split("/").pop()}`, () => {
      const r = lerBoletim([...e.qrce, ...e.qrbu], SIMULADO);
      expect(r.problemas).toEqual([]);
      expect(r.autentico).toBe(true);
      expect(r.valido).toBe(true);
      expect(r.cadeia?.ok).toBe(true);
      expect(r.assinatura?.valido).toBe(true);
      expect(r.certificado?.cadeia.valida).toBe(true);
      expect(r.certificado?.idue).toBe(String(r.boletim?.cabecalho.IDUE));
      expect(r.quantidadeQr).toBe(e.qrbu.length);
      expect(r.versao).toBe("6.0");
      expect(r.ultimoHash).toBe(r.cadeia?.ultimoHash ?? "");
      expect(r.conteudo?.startsWith("ORIG:")).toBe(true);
    });
  }

  test("resultado esperado para a urna 2013 e para a urna 2022", () => {
    const a = lerBoletim(exemplo("UE2013").qrbu.concat(exemplo("UE2013").qrce), SIMULADO);
    expect(a.assinatura?.algoritmo).toBe("ECDSA P-521");
    expect(a.certificado).toMatchObject({ formato: "DER", modelo: "2013", titularCN: "uead01671722", emissorCN: "AC URNA", cadeia: { valida: true, ac: "AC URNA" } });
    const b = lerBoletim(exemplo("UE2022").qrbu.concat(exemplo("UE2022").qrce), SIMULADO);
    expect(b.assinatura?.algoritmo).toBe("EdDSA Ed521");
    expect(b.certificado).toMatchObject({ formato: "PEM", modelo: "2022", titularCN: "UEAD02250280", emissorCN: "AC UE2022", cadeia: { valida: true, ac: "AC UE2022" } });
  });

  test("ordem embaralhada, leituras repetidas e espaços nas bordas", () => {
    const e = exemplo("UE2015");
    const textos = [` ${e.qrce[1]}\n`, e.qrbu[1] ?? "", e.qrbu[1] ?? "", e.qrce[0] ?? "", `${e.qrbu[0]} `, e.qrce[1] ?? ""];
    const r = lerBoletim(textos, SIMULADO);
    expect(r.valido).toBe(true);
    expect(r.duplicadosDescartados).toBe(1);
  });

  test("fase oficial por padrão: exemplo simulado é autêntico, mas não válido", () => {
    const e = exemplo("UE2020");
    const r = lerBoletim([...e.qrbu, ...e.qrce]);
    expect(r.autentico).toBe(true);
    expect(r.valido).toBe(false);
    expect(codigos(r)).toEqual(["FASE_INESPERADA"]);
  });

  test("QR Code faltando: rejeitado, sem boletim", () => {
    const e = exemplo("UE2013");
    const r = lerBoletim([e.qrbu[1] ?? "", ...e.qrce], SIMULADO);
    expect(codigos(r)).toEqual(["QR_FALTANDO"]);
    expect(r.boletim).toBeNull();
    expect(r.autentico).toBe(false);
  });

  test("voto alterado: cadeia de hashes quebrada, boletim não autêntico", () => {
    const e = exemplo("UE2013");
    const qrbu = e.qrbu.map((q) => q.replace(" 93:2 95:1 ", " 93:1 95:2 "));
    expect(qrbu).not.toEqual(e.qrbu);
    const r = lerBoletim([...qrbu, ...e.qrce], SIMULADO);
    expect(codigos(r)).toEqual(["CADEIA_HASH_INVALIDA"]);
    expect(r.assinatura?.valido).toBe(true);
    expect(r.autentico).toBe(false);
    expect(r.boletim?.eleicoes[1]?.cargos[0]?.votos).toEqual([{ numero: 93, votos: 1 }, { numero: 95, votos: 2 }]);
  });

  test("voto alterado e cadeia refeita: a assinatura original deixa de conferir", () => {
    const e = exemplo("UE2022");
    const qrbu = refazerCadeia(e.qrbu, (d) => d.replace(" 93:2 95:2 ", " 93:1 95:3 "));
    expect(qrbu[1]).not.toBe(e.qrbu[1]);
    const r = lerBoletim([...qrbu, ...e.qrce], SIMULADO);
    expect(r.cadeia?.ok).toBe(true);
    expect(codigos(r)).toEqual(["ASSINATURA_INVALIDA"]);
    expect(r.autentico).toBe(false);
  });

  for (const trecho of ["UE2013", "UE2022"]) {
    test(`${trecho}: um dígito de ASSI alterado reprova`, () => {
      const e = exemplo(trecho);
      const r = lerBoletim([...trocarAssi(e.qrbu, (a) => trocarHex(a, 40)), ...e.qrce], SIMULADO);
      expect(codigos(r)).toEqual(["ASSINATURA_INVALIDA"]);
      expect(r.autentico).toBe(false);
    });
  }

  test("certificado de outra urna (outra chave): assinatura inválida e urna divergente", () => {
    const r = lerBoletim([...exemplo("UE2013").qrbu, ...exemplo("UE2015").qrce], SIMULADO);
    expect(codigos(r)).toEqual(["ASSINATURA_INVALIDA", "CERTIFICADO_DE_OUTRA_URNA"]);
    expect(r.certificado?.cadeia.valida).toBe(true);
    expect(r.autentico).toBe(false);
  });

  test("sem QR Codes do certificado", () => {
    const r = lerBoletim(exemplo("UE2020").qrbu, SIMULADO);
    expect(codigos(r)).toEqual(["CERTIFICADO_AUSENTE"]);
    expect(r.boletim).not.toBeNull();
    expect(r.cadeia?.ok).toBe(true);
    expect(r.autentico).toBe(false);
  });

  test("sem ASSI no último QR Code", () => {
    const e = exemplo("UE2020");
    const r = lerBoletim([...e.qrbu.map((q) => q.replace(/ ASSI:[0-9A-F]+$/, "")), ...e.qrce], SIMULADO);
    expect(codigos(r)).toEqual(["ASSINATURA_AUSENTE"]);
    expect(r.autentico).toBe(false);
  });

  test("QR Code estranho e versão de formato diferente viram problema", () => {
    const e = exemplo("UE2020");
    const r = lerBoletim([...e.qrbu, ...e.qrce, "https://exemplo.invalido"], SIMULADO);
    expect(codigos(r)).toEqual(["QR_DESCONHECIDO"]);
    expect(r.autentico).toBe(true);
    expect(r.valido).toBe(false);
    const v = lerBoletim([...e.qrbu, ...e.qrce], { ...SIMULADO, versaoEsperada: "6.1" });
    expect(codigos(v)).toEqual(["VERSAO_NAO_SUPORTADA"]);
  });

  test("boletim forjado de ponta a ponta: cadeia e assinatura conferem, a AC não", () => {
    const e = exemplo("UE2013");
    const qrbu = refazerCadeia(e.qrbu, (d) => d.replace(" 93:2 95:1 ", " 93:1 95:2 "), (h) => assinarComoUrna(h));
    expect(qrbu[1]?.split(" HASH:")[0]).not.toBe(e.qrbu[1]?.split(" HASH:")[0]);
    const r = lerBoletim([...qrbu, ...qrceForjado()], SIMULADO);
    expect(r.cadeia?.ok).toBe(true);
    expect(r.assinatura).toEqual({ valido: true, algoritmo: "ECDSA P-521", motivo: null });
    expect(r.certificado?.cadeia).toMatchObject({ valida: false, ac: "AC URNA" });
    expect(codigos(r)).toEqual(["CADEIA_CERTIFICADO_INVALIDA"]);
    expect(r.autentico).toBe(false);
    expect(r.valido).toBe(false);
  });

  test("boletim forjado com o certificado verdadeiro da urna: assinatura não confere", () => {
    const e = exemplo("UE2013");
    const qrbu = refazerCadeia(e.qrbu, (d) => d.replace(" 93:2 95:1 ", " 93:1 95:2 "), (h) => assinarComoUrna(h));
    const r = lerBoletim([...qrbu, ...e.qrce], SIMULADO);
    expect(codigos(r)).toEqual(["ASSINATURA_INVALIDA"]);
    expect(r.autentico).toBe(false);
  });

  test("conteúdo malformado com cadeia íntegra: problema de conteúdo, sem boletim", () => {
    const e = exemplo("UE2022");
    const qrbu = refazerCadeia(e.qrbu, (d, i) => (i === 2 ? d.replace(/ TOTC:\d+$/, "") : d));
    const r = lerBoletim([...qrbu, ...e.qrce], SIMULADO);
    expect(r.cadeia?.ok).toBe(true);
    expect(r.boletim).toBeNull();
    expect(codigos(r)).toEqual(["CONTEUDO_INVALIDO", "ASSINATURA_INVALIDA"]);
  });
});
