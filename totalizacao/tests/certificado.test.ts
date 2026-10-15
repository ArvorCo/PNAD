// Certificado da urna nos QR Codes QRCE: DER (2013/2015) e PEM (2020/2022).
import { createHash, X509Certificate } from "node:crypto";
import { describe, expect, test } from "bun:test";
import { bytesParaHex } from "../src/qrbu/bytes.ts";
import {
  decodificarCertificado, ErroCertificado, extrairDer, lerQrCertificado, montarCertificado, OID, resumirCertificado,
} from "../src/qrbu/certificado.ts";
import { lerOid, lerTlv } from "../src/qrbu/der.ts";
import { exemplo } from "./helpers.ts";

function codigoDe(f: () => unknown): string | null {
  try {
    f();
    return null;
  } catch (e) {
    if (e instanceof ErroCertificado) return e.codigo;
    throw e;
  }
}

// Valores conferidos com asn1crypto sobre os mesmos certificados (scratch certinfo.py).
const ESPERADO = [
  {
    trecho: "UE2013", formato: "DER", excedentes: 1, titular: "uead01671722", emissor: "AC URNA", serial: "2688559",
    inicio: "2013-09-10T00:02:49Z", fim: "2027-05-20T00:02:49Z", chave: OID.EC_PUBLIC_KEY, parametro: OID.SECP521R1, tamanho: 133,
    aki: "CDAAF4B29701B3F0DEB2B54258594A6D34ADA48A", algoritmo: OID.ECDSA_SHA512,
  },
  {
    trecho: "UE2015", formato: "DER", excedentes: 1, titular: "uead01786888", emissor: "AC URNA", serial: "3113453",
    inicio: "2016-07-26T08:31:53Z", fim: "2030-04-04T08:31:53Z", chave: OID.EC_PUBLIC_KEY, parametro: OID.SECP521R1, tamanho: 133,
    aki: "CDAAF4B29701B3F0DEB2B54258594A6D34ADA48A", algoritmo: OID.ECDSA_SHA512,
  },
  {
    trecho: "UE2020", formato: "PEM", excedentes: 0, titular: "UEAD02031032", emissor: "AC UE2020", serial: "62",
    inicio: "2022-04-01T22:11:04Z", fim: "2035-12-09T22:11:04Z", chave: OID.ED521, parametro: null, tamanho: 66,
    aki: "BCB3545DEEEA432E1E832E81283CB8AE948E400B", algoritmo: OID.ED521,
  },
  {
    trecho: "UE2022", formato: "PEM", excedentes: 0, titular: "UEAD02250280", emissor: "AC UE2022", serial: "1447",
    inicio: "2023-05-19T13:56:47Z", fim: "2037-01-25T13:56:47Z", chave: OID.ED521, parametro: null, tamanho: 66,
    aki: "BB7C517F294A5B96F9BF6A964C4F255A755F698A", algoritmo: OID.ED521,
  },
] as const;

describe("certificado da urna", () => {
  for (const esp of ESPERADO) {
    test(`${esp.trecho}: ${esp.formato}, titular, emissor, série, validade e chave`, () => {
      const e = exemplo(esp.trecho);
      const c = montarCertificado([...e.qrce].reverse());
      expect(c.formato).toBe(esp.formato);
      expect(c.bytesExcedentes).toBe(esp.excedentes);
      expect(c.modelo).toBe(esp.trecho.slice(2));
      expect(c.titular.campos.CN).toBe(esp.titular);
      expect(c.emissor.campos.CN).toBe(esp.emissor);
      expect(c.emissor.campos.O).toBe("TSE");
      expect(c.serial.toString()).toBe(esp.serial);
      expect(c.validadeInicio).toBe(esp.inicio);
      expect(c.validadeFim).toBe(esp.fim);
      expect(c.versao).toBe(3);
      expect(c.algoritmoAssinatura).toBe(esp.algoritmo);
      expect(c.chavePublica.algoritmo).toBe(esp.chave);
      expect(c.chavePublica.parametro).toBe(esp.parametro);
      expect(c.chavePublica.bytes.length).toBe(esp.tamanho);
      expect(c.identificadorChaveAutoridade).toBe(esp.aki);
      expect(c.identificadorChaveTitular).toMatch(/^[0-9A-F]{40}$/);
      const r = resumirCertificado(c);
      expect(r.sha256).toBe(createHash("sha256").update(c.der).digest("hex").toUpperCase());
      expect(r.titularCN).toBe(esp.titular);
      expect(r.emissorCN).toBe(esp.emissor);
      expect(r.serialHex).toBe(BigInt(esp.serial).toString(16).toUpperCase());
      expect(JSON.parse(JSON.stringify(r))).toEqual(r);
    });
  }

  test("o DER extraído é o mesmo que o node:crypto reconhece (série e validade)", () => {
    for (const trecho of ["UE2013", "UE2022"]) {
      const c = montarCertificado(exemplo(trecho).qrce);
      const x = new X509Certificate(c.der);
      expect(BigInt(`0x${x.serialNumber}`)).toBe(c.serial);
      expect(new Date(x.validTo).toISOString().replace(".000", "")).toBe(c.validadeFim);
    }
  });

  test("tbsCertificate e Names são fatias do próprio DER", () => {
    const c = montarCertificado(exemplo("UE2015").qrce);
    const tbs = lerTlv(lerTlv(c.der, 0).valor, 0);
    expect(bytesParaHex(tbs.bruto)).toBe(bytesParaHex(c.tbs));
    expect(bytesParaHex(c.der)).toContain(bytesParaHex(c.emissorDer));
    expect(bytesParaHex(c.der)).toContain(bytesParaHex(c.titularDer));
  });

  test("PEM decodificado e DER cru dão o mesmo certificado", () => {
    const c = montarCertificado(exemplo("UE2022").qrce);
    const pem = `-----BEGIN CERTIFICATE-----\n${Buffer.from(c.der).toString("base64")}\n-----END CERTIFICATE-----\n`;
    const viaPem = decodificarCertificado(new TextEncoder().encode(pem));
    expect(viaPem.formato).toBe("PEM");
    expect(bytesParaHex(viaPem.der)).toBe(bytesParaHex(c.der));
    expect(decodificarCertificado(c.der).formato).toBe("DER");
  });

  test("bytes excedentes não nulos depois do DER são recusados", () => {
    const c = montarCertificado(exemplo("UE2013").qrce);
    const lixo = new Uint8Array([...c.der, 0x00, 0x01]);
    expect(codigoDe(() => extrairDer(lixo))).toBe("CERTIFICADO_INVALIDO");
  });

  test("QRCE faltando, inconsistente ou corrompido é rejeitado", () => {
    const [c1, c2] = exemplo("UE2013").qrce as [string, string];
    expect(codigoDe(() => montarCertificado([]))).toBe("CERTIFICADO_AUSENTE");
    expect(codigoDe(() => montarCertificado([c1]))).toBe("QRCE_FALTANDO");
    expect(codigoDe(() => montarCertificado([c1, c2.replace("IDUE:1671722", "IDUE:1671723")]))).toBe("QRCE_INCONSISTENTE");
    expect(codigoDe(() => montarCertificado([c1, c2.replace("MDUE:2013", "MDUE:2015")]))).toBe("QRCE_INCONSISTENTE");
    expect(codigoDe(() => montarCertificado([c1, c2, c2.replace("CERT:30", "CERT:31")]))).toBe("QRCE_DUPLICADO");
    expect(codigoDe(() => montarCertificado([c1, `${c2}0`]))).toBe("CERTIFICADO_INVALIDO");
    expect(codigoDe(() => montarCertificado([c1.replace("CERT:308203AD", "CERT:308203AE"), c2]))).toBe("CERTIFICADO_INVALIDO");
    expect(codigoDe(() => lerQrCertificado("QRCE:1:2 IDUE:1 CERT:00"))).toBe("QRCE_INVALIDO");
    expect(codigoDe(() => decodificarCertificado(new TextEncoder().encode("isto não é certificado")))).toBe("CERTIFICADO_INVALIDO");
  });

  test("leitor de OID", () => {
    const oid = (hex: string): string => lerOid(lerTlv(Uint8Array.from(Buffer.from(hex, "hex")), 0));
    expect(oid("06072A8648CE3D0201")).toBe(OID.EC_PUBLIC_KEY);
    expect(oid("06052B81040023")).toBe(OID.SECP521R1);
    expect(oid("060A2B0601040182DC2C0201")).toBe(OID.ED521);
  });
});
