// Conversões de bytes usadas em todo o leitor. São estritas de propósito: o QR Code do boletim
// usa o modo alfanumérico, que só tem dígitos e letras maiúsculas, então hexadecimal minúsculo,
// comprimento ímpar ou caractere estranho indicam leitura corrompida e não devem ser tolerados.

export class ErroBytes extends Error {
  constructor(mensagem: string) {
    super(mensagem);
    this.name = "ErroBytes";
  }
}

const HEX_MAIUSCULO = /^[0-9A-F]*$/;

/** Converte hexadecimal em bytes. Exige maiúsculas, como no QR alfanumérico. */
export function hexParaBytes(hex: string): Uint8Array {
  if (!HEX_MAIUSCULO.test(hex)) throw new ErroBytes("hexadecimal com caractere inválido");
  if (hex.length % 2 !== 0) throw new ErroBytes("hexadecimal com número ímpar de dígitos");
  const saida = new Uint8Array(hex.length / 2);
  for (let i = 0; i < saida.length; i++) saida[i] = Number.parseInt(hex.slice(2 * i, 2 * i + 2), 16);
  return saida;
}

/** Converte bytes em hexadecimal maiúsculo, o formato impresso pela urna. */
export function bytesParaHex(bytes: Uint8Array): string {
  let saida = "";
  for (const b of bytes) saida += b.toString(16).padStart(2, "0");
  return saida.toUpperCase();
}

/** Codifica texto ASCII em bytes, recusando qualquer caractere fora de 0x00..0x7F. */
export function asciiParaBytes(texto: string): Uint8Array {
  const saida = new Uint8Array(texto.length);
  for (let i = 0; i < texto.length; i++) {
    const c = texto.charCodeAt(i);
    if (c > 0x7f) throw new ErroBytes(`caractere não ASCII na posição ${i}`);
    saida[i] = c;
  }
  return saida;
}

/** Decodifica bytes como ASCII estrito. */
export function bytesParaAscii(bytes: Uint8Array): string {
  let saida = "";
  for (const b of bytes) {
    if (b > 0x7f) throw new ErroBytes("byte não ASCII");
    saida += String.fromCharCode(b);
  }
  return saida;
}

export function concatenar(...partes: Uint8Array[]): Uint8Array {
  const total = partes.reduce((s, p) => s + p.length, 0);
  const saida = new Uint8Array(total);
  let pos = 0;
  for (const p of partes) {
    saida.set(p, pos);
    pos += p.length;
  }
  return saida;
}

export function bytesIguais(a: Uint8Array, b: Uint8Array): boolean {
  if (a.length !== b.length) return false;
  for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) return false;
  return true;
}

/** Inteiro sem sinal em ordem big-endian. */
export function bytesParaBigIntBE(bytes: Uint8Array): bigint {
  let n = 0n;
  for (const b of bytes) n = (n << 8n) | BigInt(b);
  return n;
}

/** Inteiro sem sinal em ordem little-endian (convenção do EdDSA). */
export function bytesParaBigIntLE(bytes: Uint8Array): bigint {
  let n = 0n;
  for (let i = bytes.length - 1; i >= 0; i--) n = (n << 8n) | BigInt(bytes[i] ?? 0);
  return n;
}

/** Decodifica Base64 padrão (RFC 4648), recusando caracteres fora do alfabeto. */
export function base64ParaBytes(texto: string): Uint8Array {
  const limpo = texto.replace(/\s+/g, "");
  if (!/^[A-Za-z0-9+/]*={0,2}$/.test(limpo) || limpo.length % 4 !== 0) {
    throw new ErroBytes("Base64 inválido");
  }
  const binario = atob(limpo);
  const saida = new Uint8Array(binario.length);
  for (let i = 0; i < binario.length; i++) saida[i] = binario.charCodeAt(i);
  return saida;
}
