// Verificação da assinatura ASSI do boletim (manual TSE 2026, seções 1.6.1 e 1.6.3).
//
// A urna assina o último HASH da cadeia. O código de referência do manual (ECPy) entrega ao
// verificador a mensagem sha512(bytes do último HASH), isto é, o SHA-512 dos 64 bytes obtidos
// do hexadecimal impresso, e não do texto hexadecimal.
//
// - Urnas 2013 e 2015: chave ecPublicKey (1.2.840.10045.2.1) na curva secp521r1. ECDSA P-521
//   com assinatura em DER (SEQUENCE de r e s), verificada sobre a mensagem já resumida, sem novo
//   hash, aceitando s alto e INTEGER não mínimo como o ECPy (ver ecdsa.ts).
// - Urnas 2020 e 2022: chave 1.3.6.1.4.1.44588.2.1, EdDSA na curva E-521 com SHAKE256 de 132
//   bytes e prefixo "SigEd521\0\0" (ver ed521.ts). Assinatura de 132 bytes: eR || S.
import { sha512 } from "@noble/hashes/sha2.js";
import { ErroBytes, hexParaBytes } from "./bytes.ts";
import { OID, type CertificadoUrna } from "./certificado.ts";
import { verificarEcdsaP521 } from "./ecdsa.ts";
import { verificarEd521 } from "./ed521.ts";

export type AlgoritmoAssinatura = "ECDSA P-521" | "EdDSA Ed521";

export interface ResultadoAssinatura {
  valido: boolean;
  algoritmo: AlgoritmoAssinatura | null;
  /** Explicação curta quando a assinatura não pôde ser verificada ou é inválida. */
  motivo: string | null;
}

/** Mensagem efetivamente assinada pela urna: SHA-512 dos bytes do último HASH. */
export function mensagemAssinada(ultimoHashHex: string): Uint8Array {
  return sha512(hexParaBytes(ultimoHashHex));
}

/** Identifica o algoritmo de assinatura pela chave pública do certificado. */
export function algoritmoDoCertificado(cert: Pick<CertificadoUrna, "chavePublica">): AlgoritmoAssinatura | null {
  const { algoritmo, parametro } = cert.chavePublica;
  if (algoritmo === OID.EC_PUBLIC_KEY && parametro === OID.SECP521R1) return "ECDSA P-521";
  if (algoritmo === OID.ED521) return "EdDSA Ed521";
  return null;
}

/**
 * Verifica ASSI contra o último HASH usando a chave pública do certificado da urna.
 * Nunca lança: entrada malformada resulta em `valido: false` com o motivo.
 */
export function verificarAssinatura(
  ultimoHashHex: string,
  assinaturaHex: string,
  cert: Pick<CertificadoUrna, "chavePublica">,
): ResultadoAssinatura {
  const algoritmo = algoritmoDoCertificado(cert);
  if (!algoritmo) {
    const { algoritmo: oid, parametro } = cert.chavePublica;
    return { valido: false, algoritmo: null, motivo: `algoritmo de chave não suportado: ${oid}${parametro ? ` (${parametro})` : ""}` };
  }
  let mensagem: Uint8Array;
  let assinatura: Uint8Array;
  try {
    mensagem = mensagemAssinada(ultimoHashHex);
    assinatura = hexParaBytes(assinaturaHex);
  } catch (e) {
    const detalhe = e instanceof ErroBytes ? e.message : String(e);
    return { valido: false, algoritmo, motivo: `HASH ou ASSI malformado: ${detalhe}` };
  }
  let valido: boolean;
  try {
    valido = algoritmo === "ECDSA P-521"
      ? verificarEcdsaP521(mensagem, assinatura, cert.chavePublica.bytes)
      : verificarEd521(mensagem, assinatura, cert.chavePublica.bytes);
  } catch (e) {
    return { valido: false, algoritmo, motivo: `assinatura ou chave malformada: ${(e as Error).message}` };
  }
  return { valido, algoritmo, motivo: valido ? null : "assinatura não confere com a chave pública do certificado" };
}
