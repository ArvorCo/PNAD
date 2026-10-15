// Certificado da urna nos dois QR Codes QRCE (manual TSE 2026, seção 1.6.2).
//
// Cada QR traz "QRCE:i:n IDUE:<série> MDUE:<modelo> CERT:<hex>". Concatenando os CERT em ordem
// e convertendo de hexadecimal, obtém-se o certificado: em DER nas urnas 2013 e 2015 e em PEM
// (texto ASCII com Base64) nas urnas 2020 e 2022. Nos exemplos oficiais o DER vem seguido de um
// byte 0x00 de preenchimento; bytes zero depois do certificado são aceitos e contados, qualquer
// outro byte excedente é recusado.
import { sha256 } from "@noble/hashes/sha2.js";
import { base64ParaBytes, bytesParaAscii, bytesParaHex, hexParaBytes } from "./bytes.ts";
import {
  ErroDer, esperarTag, filhos, lerBitString, lerInteiro, lerOid, lerTempo, lerTexto, lerTlv, TAG, type Tlv,
} from "./der.ts";

export class ErroCertificado extends Error {
  readonly codigo: string;
  constructor(codigo: string, mensagem: string) {
    super(mensagem);
    this.name = "ErroCertificado";
    this.codigo = codigo;
  }
}

export const OID = {
  EC_PUBLIC_KEY: "1.2.840.10045.2.1",
  SECP521R1: "1.3.132.0.35",
  ED521: "1.3.6.1.4.1.44588.2.1",
  ECDSA_SHA512: "1.2.840.10045.4.3.4",
  AUTHORITY_KEY_IDENTIFIER: "2.5.29.35",
  SUBJECT_KEY_IDENTIFIER: "2.5.29.14",
} as const;

/** Rótulos curtos dos atributos de nome X.509 mais comuns. */
const ROTULOS_NOME: Record<string, string> = {
  "2.5.4.3": "CN",
  "2.5.4.6": "C",
  "2.5.4.7": "L",
  "2.5.4.8": "ST",
  "2.5.4.10": "O",
  "2.5.4.11": "OU",
  "2.5.4.5": "serialNumber",
  "1.2.840.113549.1.9.1": "emailAddress",
};

export type FormatoCertificado = "DER" | "PEM";

export interface QrCertificado {
  indice: number;
  total: number;
  idue: string;
  modelo: string;
  certHex: string;
}

export interface AtributoNome {
  oid: string;
  rotulo: string | null;
  valor: string;
}

export interface NomeX509 {
  /** Atributos na ordem do certificado. */
  atributos: AtributoNome[];
  /** Primeiro valor de cada rótulo conhecido (CN, O, OU, C, ST, L, emailAddress). */
  campos: Record<string, string>;
}

export interface ChavePublica {
  /** OID do algoritmo em SubjectPublicKeyInfo. */
  algoritmo: string;
  /** OID do parâmetro (curva nomeada) quando houver. */
  parametro: string | null;
  /** Conteúdo do BIT STRING: ponto não comprimido 04||X||Y (P-521) ou ponto de 66 bytes (Ed521). */
  bytes: Uint8Array;
}

/** Certificado X.509 decodificado pelo leitor mínimo. */
export interface CertificadoX509 {
  formato: FormatoCertificado;
  /** Certificado em DER, sem bytes de preenchimento. */
  der: Uint8Array;
  bytesExcedentes: number;
  versao: number;
  serial: bigint;
  algoritmoAssinatura: string;
  emissor: NomeX509;
  /** Name do emissor em DER, para comparação byte a byte com o titular da AC. */
  emissorDer: Uint8Array;
  titular: NomeX509;
  titularDer: Uint8Array;
  validadeInicio: string;
  validadeFim: string;
  chavePublica: ChavePublica;
  identificadorChaveAutoridade: string | null;
  identificadorChaveTitular: string | null;
  /** tbsCertificate em DER: é o que a AC assina. */
  tbs: Uint8Array;
  /** Conteúdo do BIT STRING signatureValue (DER para ECDSA, 132 bytes para Ed521). */
  assinaturaEmissor: Uint8Array;
}

/** Certificado da urna, com a série e o modelo declarados nos QR Codes QRCE. */
export interface CertificadoUrna extends CertificadoX509 {
  idue: string;
  modelo: string;
}

/** Resumo serializável em JSON (sem Uint8Array nem bigint). */
export interface ResumoCertificado {
  idue: string;
  modelo: string;
  formato: FormatoCertificado;
  bytesExcedentes: number;
  sha256: string;
  versao: number;
  serial: string;
  serialHex: string;
  algoritmoAssinatura: string;
  emissorCN: string | null;
  titularCN: string | null;
  emissor: Record<string, string>;
  titular: Record<string, string>;
  validadeInicio: string;
  validadeFim: string;
  algoritmoChave: string;
  parametroChave: string | null;
  chavePublicaHex: string;
  identificadorChaveAutoridade: string | null;
  identificadorChaveTitular: string | null;
}

const PADRAO_QRCE = /^QRCE:(\d+):(\d+) IDUE:(\d+) MDUE:(\d+) CERT:([0-9A-F]+)$/;

/** Interpreta o texto de um QR Code de certificado. */
export function lerQrCertificado(texto: string): QrCertificado {
  const m = PADRAO_QRCE.exec(texto.trim());
  if (!m) throw new ErroCertificado("QRCE_INVALIDO", "QR Code de certificado fora do formato QRCE:i:n IDUE MDUE CERT");
  const indice = Number(m[1]);
  const total = Number(m[2]);
  if (indice < 1 || total < 1 || indice > total) {
    throw new ErroCertificado("QRCE_INVALIDO", `índice ${indice} de ${total} inválido no QR do certificado`);
  }
  return { indice, total, idue: m[3] ?? "", modelo: m[4] ?? "", certHex: m[5] ?? "" };
}

/** Junta os QR Codes QRCE (em qualquer ordem) e decodifica o certificado. */
export function montarCertificado(textos: string[]): CertificadoUrna {
  if (textos.length === 0) throw new ErroCertificado("CERTIFICADO_AUSENTE", "nenhum QR Code de certificado (QRCE)");
  const unicos = [...new Set(textos.map((t) => t.trim()))];
  const partes = unicos.map(lerQrCertificado).sort((a, b) => a.indice - b.indice);
  const primeiro = partes[0];
  if (!primeiro) throw new ErroCertificado("CERTIFICADO_AUSENTE", "nenhum QR Code de certificado (QRCE)");
  const total = primeiro.total;
  for (const p of partes) {
    if (p.total !== total) throw new ErroCertificado("QRCE_INCONSISTENTE", "QR Codes de certificado com totais diferentes");
    if (p.idue !== primeiro.idue || p.modelo !== primeiro.modelo) {
      throw new ErroCertificado("QRCE_INCONSISTENTE", "QR Codes de certificado de urnas ou modelos diferentes");
    }
  }
  const indices = partes.map((p) => p.indice);
  if (new Set(indices).size !== indices.length) {
    throw new ErroCertificado("QRCE_DUPLICADO", "dois QR Codes de certificado com o mesmo índice e conteúdo diferente");
  }
  for (let i = 1; i <= total; i++) {
    if (!indices.includes(i)) throw new ErroCertificado("QRCE_FALTANDO", `falta o QR Code ${i} de ${total} do certificado`);
  }
  let bytes: Uint8Array;
  try {
    bytes = hexParaBytes(partes.map((p) => p.certHex).join(""));
  } catch (e) {
    throw new ErroCertificado("CERTIFICADO_INVALIDO", `campo CERT não é hexadecimal válido: ${(e as Error).message}`);
  }
  return { idue: primeiro.idue, modelo: primeiro.modelo, ...decodificarCertificado(bytes) };
}

const PEM = /^\s*-----BEGIN CERTIFICATE-----([A-Za-z0-9+/=\s]+)-----END CERTIFICATE-----\s*$/;

/** Detecta DER ou PEM e devolve o certificado em DER e quantos bytes zero sobraram depois dele. */
export function extrairDer(bytes: Uint8Array): { formato: FormatoCertificado; der: Uint8Array; bytesExcedentes: number } {
  if (bytes[0] === TAG.SEQUENCE) return { formato: "DER", ...cortarPreenchimento(bytes) };
  let texto: string;
  try {
    texto = bytesParaAscii(bytes).replace(/\0+$/, "");
  } catch {
    throw new ErroCertificado("CERTIFICADO_INVALIDO", "certificado não é DER nem texto PEM");
  }
  const m = PEM.exec(texto);
  if (!m) throw new ErroCertificado("CERTIFICADO_INVALIDO", "certificado não é DER nem texto PEM");
  let der: Uint8Array;
  try {
    der = base64ParaBytes(m[1] ?? "");
  } catch {
    throw new ErroCertificado("CERTIFICADO_INVALIDO", "Base64 inválido dentro do PEM");
  }
  return { formato: "PEM", ...cortarPreenchimento(der) };
}

function cortarPreenchimento(bytes: Uint8Array): { der: Uint8Array; bytesExcedentes: number } {
  let externo: Tlv;
  try {
    externo = lerTlv(bytes, 0);
  } catch (e) {
    throw new ErroCertificado("CERTIFICADO_INVALIDO", `DER inválido: ${(e as Error).message}`);
  }
  const resto = bytes.subarray(externo.fim);
  if (resto.some((b) => b !== 0)) {
    throw new ErroCertificado("CERTIFICADO_INVALIDO", "bytes não nulos depois do certificado");
  }
  return { der: bytes.subarray(0, externo.fim), bytesExcedentes: resto.length };
}

function lerNome(tlv: Tlv): NomeX509 {
  esperarTag(tlv, TAG.SEQUENCE, "Name");
  const atributos: AtributoNome[] = [];
  const campos: Record<string, string> = {};
  for (const rdn of filhos(tlv)) {
    esperarTag(rdn, TAG.SET, "RelativeDistinguishedName");
    for (const atv of filhos(rdn)) {
      const [tipo, valor] = filhos(esperarTag(atv, TAG.SEQUENCE, "AttributeTypeAndValue"));
      const oid = lerOid(esperarTag(tipo, TAG.OID, "tipo do atributo"));
      if (!valor) throw new ErroDer("atributo de nome sem valor");
      const texto = lerTexto(valor);
      const rotulo = ROTULOS_NOME[oid] ?? null;
      atributos.push({ oid, rotulo, valor: texto });
      if (rotulo && !(rotulo in campos)) campos[rotulo] = texto;
    }
  }
  return { atributos, campos };
}

function lerExtensoes(tlv: Tlv): { aki: string | null; ski: string | null } {
  let aki: string | null = null;
  let ski: string | null = null;
  const lista = esperarTag(filhos(tlv)[0], TAG.SEQUENCE, "Extensions");
  for (const ext of filhos(lista)) {
    const partes = filhos(esperarTag(ext, TAG.SEQUENCE, "Extension"));
    const oid = lerOid(esperarTag(partes[0], TAG.OID, "extnID"));
    const valor = esperarTag(partes[partes.length - 1], TAG.OCTET_STRING, "extnValue");
    if (oid === OID.AUTHORITY_KEY_IDENTIFIER) {
      const interno = esperarTag(lerTlv(valor.valor, 0), TAG.SEQUENCE, "AuthorityKeyIdentifier");
      // keyIdentifier é [0] IMPLICIT OCTET STRING (tag 0x80).
      const id = filhos(interno).find((f) => f.tag === 0x80);
      aki = id ? bytesParaHex(id.valor) : null;
    } else if (oid === OID.SUBJECT_KEY_IDENTIFIER) {
      ski = bytesParaHex(esperarTag(lerTlv(valor.valor, 0), TAG.OCTET_STRING, "SubjectKeyIdentifier").valor);
    }
  }
  return { aki, ski };
}

/** Decodifica um certificado X.509 (DER ou PEM) com o leitor DER mínimo. */
export function decodificarCertificado(bytes: Uint8Array): CertificadoX509 {
  const { formato, der, bytesExcedentes } = extrairDer(bytes);
  try {
    const cert = esperarTag(lerTlv(der, 0), TAG.SEQUENCE, "Certificate");
    const externos = filhos(cert);
    if (externos.length !== 3) throw new ErroDer("Certificate deveria ter tbsCertificate, signatureAlgorithm e signatureValue");
    const [tbsTlv, algExterno, assinaturaTlv] = externos;
    const tbs = esperarTag(tbsTlv, TAG.SEQUENCE, "tbsCertificate");
    const campos = filhos(tbs);
    let i = 0;
    let versao = 1;
    if (campos[0]?.tag === 0xa0) {
      versao = Number(lerInteiro(esperarTag(filhos(campos[0])[0], TAG.INTEGER, "version"))) + 1;
      i = 1;
    }
    const serial = lerInteiro(esperarTag(campos[i], TAG.INTEGER, "serialNumber"));
    const algInterno = lerOid(esperarTag(filhos(esperarTag(campos[i + 1], TAG.SEQUENCE, "signature"))[0], TAG.OID, "signature"));
    const emissorTlv = esperarTag(campos[i + 2], TAG.SEQUENCE, "issuer");
    const emissor = lerNome(emissorTlv);
    const [inicio, fim] = filhos(esperarTag(campos[i + 3], TAG.SEQUENCE, "validity"));
    if (!inicio || !fim) throw new ErroDer("validade incompleta");
    const titularTlv = esperarTag(campos[i + 4], TAG.SEQUENCE, "subject");
    const titular = lerNome(titularTlv);
    const [algSpki, chaveTlv] = filhos(esperarTag(campos[i + 5], TAG.SEQUENCE, "subjectPublicKeyInfo"));
    const algPartes = filhos(esperarTag(algSpki, TAG.SEQUENCE, "AlgorithmIdentifier"));
    const algoritmoChave = lerOid(esperarTag(algPartes[0], TAG.OID, "algoritmo da chave"));
    const parametro = algPartes[1]?.tag === TAG.OID ? lerOid(algPartes[1]) : null;
    const chave = lerBitString(esperarTag(chaveTlv, TAG.BIT_STRING, "subjectPublicKey"));
    let aki: string | null = null;
    let ski: string | null = null;
    const ext = campos.slice(i + 6).find((c) => c.tag === 0xa3);
    if (ext) ({ aki, ski } = lerExtensoes(ext));
    const algoritmoAssinatura = lerOid(esperarTag(filhos(esperarTag(algExterno, TAG.SEQUENCE, "signatureAlgorithm"))[0], TAG.OID, "signatureAlgorithm"));
    if (algoritmoAssinatura !== algInterno) throw new ErroDer("algoritmo de assinatura difere entre tbsCertificate e Certificate");
    return {
      formato,
      der,
      bytesExcedentes,
      versao,
      serial,
      algoritmoAssinatura,
      emissor,
      emissorDer: emissorTlv.bruto,
      titular,
      titularDer: titularTlv.bruto,
      validadeInicio: lerTempo(inicio),
      validadeFim: lerTempo(fim),
      chavePublica: { algoritmo: algoritmoChave, parametro, bytes: chave },
      identificadorChaveAutoridade: aki,
      identificadorChaveTitular: ski,
      tbs: tbs.bruto,
      assinaturaEmissor: lerBitString(esperarTag(assinaturaTlv, TAG.BIT_STRING, "signatureValue")),
    };
  } catch (e) {
    if (e instanceof ErroCertificado) throw e;
    throw new ErroCertificado("CERTIFICADO_INVALIDO", `certificado X.509 malformado: ${(e as Error).message}`);
  }
}

/** Resumo do certificado para relatório e armazenamento. */
export function resumirCertificado(c: CertificadoUrna): ResumoCertificado {
  return {
    idue: c.idue,
    modelo: c.modelo,
    formato: c.formato,
    bytesExcedentes: c.bytesExcedentes,
    sha256: bytesParaHex(sha256(c.der)),
    versao: c.versao,
    serial: c.serial.toString(10),
    serialHex: c.serial.toString(16).toUpperCase(),
    algoritmoAssinatura: c.algoritmoAssinatura,
    emissorCN: c.emissor.campos.CN ?? null,
    titularCN: c.titular.campos.CN ?? null,
    emissor: { ...c.emissor.campos },
    titular: { ...c.titular.campos },
    validadeInicio: c.validadeInicio,
    validadeFim: c.validadeFim,
    algoritmoChave: c.chavePublica.algoritmo,
    parametroChave: c.chavePublica.parametro,
    chavePublicaHex: bytesParaHex(c.chavePublica.bytes),
    identificadorChaveAutoridade: c.identificadorChaveAutoridade,
    identificadorChaveTitular: c.identificadorChaveTitular,
  };
}
