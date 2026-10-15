// Cadeia do certificado da urna até a AC do TSE.
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, test } from "bun:test";
import { p521 } from "@noble/curves/nist.js";
import { sha512 } from "@noble/hashes/sha2.js";
import { PEM_AC_UE2020, PEM_AC_UE2022, PEM_AC_URNA } from "../src/qrbu/ac/certificados.ts";
import { asciiParaBytes, bytesParaHex, concatenar } from "../src/qrbu/bytes.ts";
import { AUTORIDADES, verificarCadeiaCertificado, type AutoridadeCertificadora, type NomeAc } from "../src/qrbu/cadeia.ts";
import { decodificarCertificado, montarCertificado, OID, type CertificadoX509 } from "../src/qrbu/certificado.ts";
import { lerTlv } from "../src/qrbu/der.ts";
import { CHAVE_FORJADA, PUBLICA_FORJADA, exemplo, tlv } from "./helpers.ts";

const PASTA_AC = join(import.meta.dir, "..", "src", "qrbu", "ac");

// SHA-256 registrados em data/originals/tse_qrbu_2026/ac_certs/fonte.json.
const SHA256_AC: [string, string][] = [
  ["ac_urna.pem", "5ccf7c696458bd643d773e9b5b0385ad209bac2b5b5ee657a5f00c5a1e15e271"],
  ["ac_ue2020.pem", "90fa46d45d93015290631416ce8cfacf78b3d69d37bb3d493c9c537a9b901454"],
  ["ac_ue2022.pem", "ff1d8f27a3d3a3cc24b5dd42515e4975f69628660d814b18091e62a9a1394e29"],
];

/** Reconstrói o certificado com outro tbsCertificate e outra assinatura (mesmo AlgorithmIdentifier). */
function remontar(cert: CertificadoX509, tbs: Uint8Array, assinatura: Uint8Array): Uint8Array {
  const fimTbs = cert.tbs.byteOffset - cert.der.byteOffset + cert.tbs.length;
  const algId = lerTlv(cert.der, fimTbs).bruto;
  return tlv(0x30, concatenar(tbs, algId, tlv(0x03, concatenar(new Uint8Array([0]), assinatura))));
}

/** Troca, dentro do tbs, um trecho por outro do mesmo tamanho. */
function trocarNoTbs(cert: CertificadoX509, trecho: Uint8Array, novo: Uint8Array): Uint8Array {
  const pos = cert.tbs.byteOffset - cert.der.byteOffset;
  const inicio = trecho.byteOffset - cert.der.byteOffset - pos;
  const tbs = Uint8Array.from(cert.tbs);
  tbs.set(novo, inicio);
  return tbs;
}

describe("autoridades certificadoras embutidas", () => {
  test("cópia literal dos .pem com o SHA-256 registrado na procedência", () => {
    const embutidos: Record<string, string> = { "ac_urna.pem": PEM_AC_URNA, "ac_ue2020.pem": PEM_AC_UE2020, "ac_ue2022.pem": PEM_AC_UE2022 };
    for (const [arquivo, sha] of SHA256_AC) {
      const texto = readFileSync(join(PASTA_AC, arquivo), "utf8");
      expect(embutidos[arquivo]).toBe(texto);
      expect(createHash("sha256").update(texto).digest("hex")).toBe(sha);
    }
  });

  test("titulares, algoritmos e validade das ACs", () => {
    const resumo = AUTORIDADES.map((a) => [a.nome, a.algoritmo, a.certificado.emissor.campos.CN, a.certificado.validadeFim]);
    expect(resumo).toEqual([
      ["AC URNA", "ECDSA P-521", "AC RAIZ UE", "2026-07-18T21:59:57Z"],
      ["AC UE2020", "EdDSA Ed521", "AC URNA v2", "2037-07-01T21:31:56Z"],
      ["AC UE2022", "EdDSA Ed521", "AC URNA v2", "2039-02-24T13:46:49Z"],
    ]);
  });
});

describe("cadeia do certificado da urna", () => {
  const CASOS: [string, NomeAc][] = [["UE2013", "AC URNA"], ["UE2015", "AC URNA"], ["UE2020", "AC UE2020"], ["UE2022", "AC UE2022"]];
  for (const [trecho, ac] of CASOS) {
    test(`${trecho} emitido e assinado pela ${ac}`, () => {
      const r = verificarCadeiaCertificado(montarCertificado(exemplo(trecho).qrce));
      expect(r.valida).toBe(true);
      expect(r.ac).toBe(ac);
      expect(r.motivo).toBeNull();
    });
  }

  test("AC URNA expirada em 18/07/2026 não reprova: validade da AC é só informação", () => {
    const r = verificarCadeiaCertificado(montarCertificado(exemplo("UE2013").qrce));
    expect(r.valida).toBe(true);
    expect(r.acValidadeFim).toBe("2026-07-18T21:59:57Z");
  });

  for (const trecho of ["UE2013", "UE2022"]) {
    test(`${trecho}: um byte alterado na assinatura do certificado reprova`, () => {
      const cert = montarCertificado(exemplo(trecho).qrce);
      for (const pos of [5, 30, cert.assinaturaEmissor.length - 2]) {
        const sig = Uint8Array.from(cert.assinaturaEmissor);
        sig[pos] = (sig[pos] ?? 0) ^ 0x01;
        const r = verificarCadeiaCertificado(decodificarCertificado(remontar(cert, cert.tbs, sig)));
        expect(r.valida).toBe(false);
        expect(r.ac).toBe(trecho === "UE2013" ? "AC URNA" : "AC UE2022");
      }
    });

    test(`${trecho}: um byte alterado no tbsCertificate (titular) reprova`, () => {
      const cert = montarCertificado(exemplo(trecho).qrce);
      const cn = asciiParaBytes(cert.titular.campos.CN ?? "");
      const pos = bytesParaHex(cert.titularDer).indexOf(bytesParaHex(cn)) / 2;
      const trecho2 = cert.titularDer.subarray(pos, pos + cn.length);
      const novo = Uint8Array.from(cn);
      novo[novo.length - 1] = (novo[novo.length - 1] ?? 0x30) === 0x39 ? 0x38 : (novo[novo.length - 1] ?? 0x30) + 1;
      const tbs = trocarNoTbs(cert, trecho2, novo);
      const forjado = decodificarCertificado(remontar(cert, tbs, cert.assinaturaEmissor));
      expect(forjado.titular.campos.CN).not.toBe(cert.titular.campos.CN);
      expect(verificarCadeiaCertificado(forjado).valida).toBe(false);
    });
  }

  test("certificado com emissor desconhecido reprova sem AC", () => {
    const cert = montarCertificado(exemplo("UE2015").qrce);
    const nome = asciiParaBytes("AC URNA");
    const pos = bytesParaHex(cert.emissorDer).indexOf(bytesParaHex(nome)) / 2;
    const tbs = trocarNoTbs(cert, cert.emissorDer.subarray(pos, pos + nome.length), asciiParaBytes("AC XXXX"));
    const r = verificarCadeiaCertificado(decodificarCertificado(remontar(cert, tbs, cert.assinaturaEmissor)));
    expect(r).toMatchObject({ valida: false, ac: null });
  });

  test("certificado forjado com chave própria, reassinado pelo falsificador, reprova", () => {
    const cert = montarCertificado(exemplo("UE2013").qrce);
    expect(cert.chavePublica.bytes.length).toBe(PUBLICA_FORJADA.length);
    const tbs = trocarNoTbs(cert, cert.chavePublica.bytes, PUBLICA_FORJADA);
    const assinatura = p521.sign(sha512(tbs), CHAVE_FORJADA, { prehash: false, lowS: false, format: "der" });
    const forjado = decodificarCertificado(remontar(cert, tbs, assinatura));
    expect(bytesParaHex(forjado.chavePublica.bytes)).toBe(bytesParaHex(PUBLICA_FORJADA));
    expect(forjado.emissor.campos.CN).toBe("AC URNA");
    const r = verificarCadeiaCertificado(forjado);
    expect(r).toMatchObject({ valida: false, ac: "AC URNA" });
    // Contraprova: a mesma conta aceitaria o forjado se a AC fosse a chave do falsificador.
    const acFalsa: AutoridadeCertificadora[] = [{
      nome: "AC URNA",
      algoritmo: "ECDSA P-521",
      certificado: { ...forjado, titular: forjado.emissor, titularDer: forjado.emissorDer, identificadorChaveTitular: forjado.identificadorChaveAutoridade },
    }];
    expect(verificarCadeiaCertificado(forjado, acFalsa).valida).toBe(true);
  });

  test("certificado autoassinado (emissor = titular) reprova", () => {
    const cert = montarCertificado(exemplo("UE2022").qrce);
    const auto = { ...cert, emissor: cert.titular, emissorDer: cert.titularDer };
    expect(verificarCadeiaCertificado(auto)).toMatchObject({ valida: false, ac: null });
  });

  test("algoritmo de assinatura incompatível com a AC reprova", () => {
    const cert = montarCertificado(exemplo("UE2022").qrce);
    const r = verificarCadeiaCertificado({ ...cert, algoritmoAssinatura: OID.ECDSA_SHA512 });
    expect(r.valida).toBe(false);
    expect(r.motivo).toContain("incompatível");
  });

  test("identificador de chave da autoridade divergente reprova", () => {
    const cert = montarCertificado(exemplo("UE2020").qrce);
    const r = verificarCadeiaCertificado({ ...cert, identificadorChaveAutoridade: "00".repeat(20) });
    expect(r.valida).toBe(false);
  });
});
