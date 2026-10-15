// ECDSA P-521 (secp521r1) como verificado pelo ECPy 8143d9ac, referência do manual do QR Code.
//
// A aritmética é a do @noble/curves (p521). O que se porta do ECPy é a leitura da assinatura e a
// forma da mensagem:
// - a mensagem já chega resumida (SHA-512, 64 bytes) e não passa por novo hash; como 512 bits é
//   menos que os 521 bits da ordem, nenhum bit é truncado;
// - a assinatura é um SEQUENCE DER com dois INTEGER, r e s, lidos como inteiros sem sinal em
//   big-endian. O ECPy aceita zero à esquerda não mínimo nos INTEGER; o parser DER do noble
//   recusaria. Se um codificador escrevesse r e s com largura fixa de 66 bytes, a forma não
//   mínima apareceria sempre que r ou s ficasse abaixo de 2^519, cerca de 44% das assinaturas;
//   aceitá-la, como a referência, evita reprovar boletim verdadeiro. A matemática não muda:
//   valem os mesmos r e s, ambos em [1, n). Bytes depois do SEQUENCE são recusados, como no ECPy;
// - s alto é aceito (o ECPy não impõe s baixo).
import { p521 } from "@noble/curves/nist.js";
import { bytesParaBigIntBE } from "./bytes.ts";
import { esperarTag, filhos, lerTlv, TAG } from "./der.ts";

export const ORDEM_P521: bigint = p521.Point.Fn.ORDER;

/** Lê r e s de uma assinatura ECDSA em DER, com a tolerância do ECPy. Devolve null se malformada. */
export function lerAssinaturaEcdsa(der: Uint8Array): { r: bigint; s: bigint } | null {
  try {
    const seq = esperarTag(lerTlv(der, 0), TAG.SEQUENCE, "assinatura ECDSA");
    if (seq.fim !== der.length) return null;
    const partes = filhos(seq);
    if (partes.length !== 2) return null;
    const [r, s] = partes.map((p) => esperarTag(p, TAG.INTEGER, "r ou s"));
    if (!r || !s || r.valor.length === 0 || s.valor.length === 0) return null;
    return { r: bytesParaBigIntBE(r.valor), s: bytesParaBigIntBE(s.valor) };
  } catch {
    return null;
  }
}

/**
 * Verifica ECDSA P-521 sobre uma mensagem já resumida.
 * @param resumo SHA-512 do conteúdo assinado (64 bytes)
 * @param assinaturaDer SEQUENCE { r INTEGER, s INTEGER }
 * @param chavePublica ponto SEC1 (04||X||Y, 133 bytes; comprimido também é aceito)
 */
export function verificarEcdsaP521(resumo: Uint8Array, assinaturaDer: Uint8Array, chavePublica: Uint8Array): boolean {
  const rs = lerAssinaturaEcdsa(assinaturaDer);
  if (!rs || rs.r <= 0n || rs.r >= ORDEM_P521 || rs.s <= 0n || rs.s >= ORDEM_P521) return false;
  try {
    const compacta = new p521.Signature(rs.r, rs.s).toBytes("compact");
    return p521.verify(compacta, resumo, chavePublica, { prehash: false, lowS: false, format: "compact" });
  } catch {
    return false;
  }
}
