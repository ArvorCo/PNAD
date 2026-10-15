// Leitor DER mínimo, suficiente para o certificado X.509 da urna. Só aceita a forma definida
// (sem comprimento indefinido) e recusa comprimento que ultrapasse o envelope; não reconstrói
// estruturas ASN.1 genéricas, apenas caminha pelos TLV que o certificado usa.

export class ErroDer extends Error {
  constructor(mensagem: string) {
    super(mensagem);
    this.name = "ErroDer";
  }
}

export const TAG = {
  BOOLEAN: 0x01,
  INTEGER: 0x02,
  BIT_STRING: 0x03,
  OCTET_STRING: 0x04,
  NULL: 0x05,
  OID: 0x06,
  UTF8_STRING: 0x0c,
  PRINTABLE_STRING: 0x13,
  T61_STRING: 0x14,
  IA5_STRING: 0x16,
  UTC_TIME: 0x17,
  GENERALIZED_TIME: 0x18,
  BMP_STRING: 0x1e,
  SEQUENCE: 0x30,
  SET: 0x31,
} as const;

/** Um elemento TLV dentro de um buffer: `bruto` inclui cabeçalho, `valor` só o conteúdo. */
export interface Tlv {
  tag: number;
  inicio: number;
  fim: number;
  valor: Uint8Array;
  bruto: Uint8Array;
}

/** Lê um TLV a partir de `pos`, limitado a `limite` (exclusivo). */
export function lerTlv(buf: Uint8Array, pos: number, limite = buf.length): Tlv {
  if (pos + 2 > limite) throw new ErroDer("TLV truncado");
  const tag = buf[pos] ?? 0;
  if ((tag & 0x1f) === 0x1f) throw new ErroDer("tag de vários bytes não suportada");
  let comprimento = buf[pos + 1] ?? 0;
  let cabecalho = 2;
  if (comprimento === 0x80) throw new ErroDer("comprimento indefinido não é DER");
  if (comprimento > 0x80) {
    const n = comprimento & 0x7f;
    if (n > 4) throw new ErroDer("comprimento grande demais");
    if (pos + 2 + n > limite) throw new ErroDer("TLV truncado");
    comprimento = 0;
    for (let i = 0; i < n; i++) comprimento = comprimento * 256 + (buf[pos + 2 + i] ?? 0);
    cabecalho += n;
  }
  const inicioValor = pos + cabecalho;
  const fim = inicioValor + comprimento;
  if (fim > limite) throw new ErroDer("comprimento ultrapassa o envelope");
  return { tag, inicio: pos, fim, valor: buf.subarray(inicioValor, fim), bruto: buf.subarray(pos, fim) };
}

/** Lê todos os filhos de um TLV construído (SEQUENCE, SET ou contexto explícito). */
export function filhos(tlv: Tlv): Tlv[] {
  const saida: Tlv[] = [];
  let pos = 0;
  while (pos < tlv.valor.length) {
    const filho = lerTlv(tlv.valor, pos);
    saida.push(filho);
    pos = filho.fim;
  }
  return saida;
}

export function esperarTag(tlv: Tlv | undefined, tag: number, rotulo: string): Tlv {
  if (!tlv) throw new ErroDer(`${rotulo}: elemento ausente`);
  if (tlv.tag !== tag) {
    throw new ErroDer(`${rotulo}: tag 0x${tlv.tag.toString(16)} onde se esperava 0x${tag.toString(16)}`);
  }
  return tlv;
}

/** Decodifica OBJECT IDENTIFIER em notação pontuada. */
export function lerOid(tlv: Tlv): string {
  esperarTag(tlv, TAG.OID, "OID");
  const v = tlv.valor;
  if (v.length === 0) throw new ErroDer("OID vazio");
  const arcos: bigint[] = [];
  let atual = 0n;
  for (let i = 0; i < v.length; i++) {
    const b = v[i] ?? 0;
    atual = (atual << 7n) | BigInt(b & 0x7f);
    if ((b & 0x80) === 0) {
      arcos.push(atual);
      atual = 0n;
    } else if (i === v.length - 1) {
      throw new ErroDer("OID truncado");
    }
  }
  const primeiro = arcos[0] ?? 0n;
  const x = primeiro < 40n ? 0n : primeiro < 80n ? 1n : 2n;
  return [x, primeiro - 40n * x, ...arcos.slice(1)].map(String).join(".");
}

/** INTEGER sem sinal (o certificado só usa positivos). */
export function lerInteiro(tlv: Tlv): bigint {
  esperarTag(tlv, TAG.INTEGER, "INTEGER");
  if (tlv.valor.length === 0) throw new ErroDer("INTEGER vazio");
  if (((tlv.valor[0] ?? 0) & 0x80) !== 0) throw new ErroDer("INTEGER negativo não esperado");
  let n = 0n;
  for (const b of tlv.valor) n = (n << 8n) | BigInt(b);
  return n;
}

/** BIT STRING com zero bits não usados; devolve os bytes do conteúdo. */
export function lerBitString(tlv: Tlv): Uint8Array {
  esperarTag(tlv, TAG.BIT_STRING, "BIT STRING");
  if (tlv.valor.length === 0) throw new ErroDer("BIT STRING vazio");
  if (tlv.valor[0] !== 0) throw new ErroDer("BIT STRING com bits não usados");
  return tlv.valor.subarray(1);
}

/** Cadeias de texto usadas em nomes X.509. */
export function lerTexto(tlv: Tlv): string {
  switch (tlv.tag) {
    case TAG.UTF8_STRING:
      return new TextDecoder("utf-8", { fatal: true }).decode(tlv.valor);
    case TAG.PRINTABLE_STRING:
    case TAG.IA5_STRING:
    case TAG.T61_STRING: {
      let s = "";
      for (const b of tlv.valor) s += String.fromCharCode(b);
      return s;
    }
    case TAG.BMP_STRING: {
      if (tlv.valor.length % 2 !== 0) throw new ErroDer("BMPString com comprimento ímpar");
      let s = "";
      for (let i = 0; i < tlv.valor.length; i += 2) s += String.fromCharCode(((tlv.valor[i] ?? 0) << 8) | (tlv.valor[i + 1] ?? 0));
      return s;
    }
    default:
      throw new ErroDer(`tipo de texto 0x${tlv.tag.toString(16)} não suportado`);
  }
}

/** UTCTime ou GeneralizedTime em UTC, devolvido como ISO 8601 ("2027-05-20T00:02:49Z"). */
export function lerTempo(tlv: Tlv): string {
  let s = "";
  for (const b of tlv.valor) s += String.fromCharCode(b);
  let m: RegExpMatchArray | null;
  if (tlv.tag === TAG.UTC_TIME) {
    m = /^(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})Z$/.exec(s);
    if (!m) throw new ErroDer(`UTCTime inválido: ${s}`);
    const aa = Number(m[1]);
    // RFC 5280, 4.1.2.5.1: anos 50 a 99 são 19xx, 00 a 49 são 20xx.
    const ano = aa >= 50 ? 1900 + aa : 2000 + aa;
    return `${ano}-${m[2]}-${m[3]}T${m[4]}:${m[5]}:${m[6]}Z`;
  }
  if (tlv.tag === TAG.GENERALIZED_TIME) {
    m = /^(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})Z$/.exec(s);
    if (!m) throw new ErroDer(`GeneralizedTime inválido: ${s}`);
    return `${m[1]}-${m[2]}-${m[3]}T${m[4]}:${m[5]}:${m[6]}Z`;
  }
  throw new ErroDer(`tag de tempo 0x${tlv.tag.toString(16)} inesperada`);
}
