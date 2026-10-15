// EdDSA sobre a curva E-521 (Ed521), como implementada no ECPy (commit 8143d9ac), a biblioteca
// de referência citada no manual do QR Code do BU de 2026 (seção 1.6.3). A aritmética de pontos
// vem do construtor genérico de curvas de Edwards do @noble/curves; a regra de verificação é
// portada do ECPy linha a linha:
//
//   h = SHAKE256("SigEd521" || 0x00 || 0x00 || eR || eA || mensagem, 132 bytes)
//   h é lido em little-endian e reduzido módulo n
//   válida se R + h·A == S·B (equação sem multiplicação pelo cofator, como no ECPy)
//
// Codificação de ponto (66 bytes): coordenada y em little-endian; o bit mais alto do último byte
// guarda a paridade de x. Assinatura (132 bytes): eR (66 bytes) seguido de S (66 bytes, little-endian).
//
// Rigor acima do ECPy, sem efeito sobre assinaturas honestas: y precisa ser menor que p, x = 0 com
// bit de sinal ligado é recusado, S precisa ser menor que n e a chave pública não pode ter ordem
// pequena. O ECPy aceitaria S + n no lugar de S (maleabilidade); aqui não.
import { edwards, type EdwardsPoint } from "@noble/curves/abstract/edwards.js";
import { shake256 } from "@noble/hashes/sha3.js";
import { asciiParaBytes, bytesParaBigIntLE, concatenar } from "./bytes.ts";

/** Parâmetros da curva "Ed521" em ecpy/curve_defs.py (E-521: x² + y² = 1 + d·x²·y², d = −376014). */
export const ED521 = {
  p: (1n << 521n) - 1n,
  n: 0x7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffd15b6c64746fc85f736b8af5e7ec53f04fbd8c4569a8f1f4540ea2435f5180d6bn,
  h: 4n,
  a: 1n,
  d: (1n << 521n) - 1n - 376014n,
  Gx: 0x752cb45c48648b189df90cb2296b2878a3bfd9f42fc6c818ec8bf3c9c0c6203913f6ecc5ccc72434b1ae949d568fc99c6059d0fb13364838aa302a940a2f19ba6cn,
  Gy: 0x0cn,
} as const;

/** Tamanho em bytes de um ponto codificado e de cada metade da assinatura. */
export const ED521_BYTES = 66;
/** Tamanho da saída do SHAKE256 usada pelo ECPy (hash_len=132). */
export const ED521_HASH_BYTES = 132;

const DOMINIO = concatenar(asciiParaBytes("SigEd521"), new Uint8Array([0, 0]));

/** Construtor de pontos da E-521 (campo little-endian de 66 bytes, como no ECPy). */
export const Ed521Ponto = edwards(ED521);

/** Decodifica um ponto de 66 bytes; lança erro se a codificação for inválida. */
export function decodificarPontoEd521(bytes: Uint8Array): EdwardsPoint {
  if (bytes.length !== ED521_BYTES) throw new Error(`ponto Ed521 precisa de ${ED521_BYTES} bytes, recebeu ${bytes.length}`);
  return Ed521Ponto.fromBytes(bytes, false);
}

/** Hash de desafio do ECPy: SHAKE256 com prefixo de domínio, lido em little-endian módulo n. */
export function desafioEd521(eR: Uint8Array, eA: Uint8Array, mensagem: Uint8Array): bigint {
  const h = shake256(concatenar(DOMINIO, eR, eA, mensagem), { dkLen: ED521_HASH_BYTES });
  return bytesParaBigIntLE(h) % ED521.n;
}

/**
 * Verifica uma assinatura EdDSA Ed521.
 * @param mensagem bytes assinados (no BU, o SHA-512 dos bytes do último HASH)
 * @param assinatura 132 bytes: eR || S
 * @param chavePublica ponto codificado de 66 bytes (conteúdo do BIT STRING do certificado)
 */
export function verificarEd521(mensagem: Uint8Array, assinatura: Uint8Array, chavePublica: Uint8Array): boolean {
  if (assinatura.length !== 2 * ED521_BYTES || chavePublica.length !== ED521_BYTES) return false;
  const eR = assinatura.subarray(0, ED521_BYTES);
  const S = bytesParaBigIntLE(assinatura.subarray(ED521_BYTES));
  if (S >= ED521.n) return false;
  let R: EdwardsPoint;
  let A: EdwardsPoint;
  try {
    R = decodificarPontoEd521(eR);
    A = decodificarPontoEd521(chavePublica);
  } catch {
    return false;
  }
  if (A.isSmallOrder()) return false;
  // O ECPy recodifica a chave pública antes do hash; com decodificação estrita o resultado é idêntico.
  const h = desafioEd521(eR, A.toBytes(), mensagem);
  const esquerda = h === 0n ? R : R.add(A.multiplyUnsafe(h));
  const direita = S === 0n ? Ed521Ponto.ZERO : Ed521Ponto.BASE.multiplyUnsafe(S);
  return esquerda.equals(direita);
}
