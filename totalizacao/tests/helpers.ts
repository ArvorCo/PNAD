// Utilitários dos testes: fixtures oficiais, adulteração controlada e um codificador DER mínimo
// para montar certificados forjados.
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { p521 } from "@noble/curves/nist.js";
import { sha512 } from "@noble/hashes/sha2.js";
import { bytesParaHex, concatenar, hexParaBytes } from "../src/qrbu/bytes.ts";
import { sha512Hex } from "../src/qrbu/hash.ts";

export interface Exemplo {
  arquivo: string;
  qrbu: string[];
  qrce: string[];
  assinatura_valida: boolean;
}

const FIXTURES = join(import.meta.dir, "fixtures");

export function json<T>(nome: string): T {
  return JSON.parse(readFileSync(join(FIXTURES, nome), "utf8")) as T;
}

export const EXEMPLOS: Exemplo[] = json<{ exemplos: Exemplo[] }>("exemplos_tse_2026.json").exemplos;

/** Exemplo pelo trecho do nome do arquivo (ex.: "UE2013", "imgbusa", "PresGovPrefeito"). */
export function exemplo(trecho: string): Exemplo {
  const e = EXEMPLOS.find((x) => x.arquivo.includes(trecho));
  if (!e) throw new Error(`exemplo ${trecho} não encontrado`);
  return e;
}

/** Troca um dígito hexadecimal por outro (xor 1), na posição indicada. */
export function trocarHex(hex: string, posicao: number): string {
  const c = hex[posicao];
  if (c === undefined) throw new Error("posição fora do texto");
  const novo = (Number.parseInt(c, 16) ^ 1).toString(16).toUpperCase();
  return hex.slice(0, posicao) + novo + hex.slice(posicao + 1);
}

/** Substitui o valor de ASSI no último QR Code por outro hexadecimal. */
export function trocarAssi(qrbu: string[], transformar: (assi: string) => string): string[] {
  return qrbu.map((q) => q.replace(/ ASSI:([0-9A-F]+)$/, (_m, a: string) => ` ASSI:${transformar(a)}`));
}

/** Separa "QRBU:i:n VRQR:x <dados> HASH:h [ASSI:a]" para reconstrução nos testes. */
function partes(qrbu: string[]): { cab: string; dados: string; assi: string | null }[] {
  return [...qrbu]
    .sort((a, b) => Number(a.split(":")[1]) - Number(b.split(":")[1]))
    .map((q) => {
      const m = /^(QRBU:\d+:\d+ VRQR:\S+) (.+?) HASH:[0-9A-F]{128}(?: ASSI:([0-9A-F]+))?$/.exec(q);
      if (!m) throw new Error("QR inválido no teste");
      return { cab: m[1] ?? "", dados: m[2] ?? "", assi: m[3] ?? null };
    });
}

/** Refaz os HASH de um boletim depois de editar os dados, como faria um falsificador. */
export function refazerCadeia(qrbu: string[], editar: (dados: string, indice: number) => string, assi?: (ultimoHash: string) => string): string[] {
  const ps = partes(qrbu);
  let acumulado = "";
  return ps.map((p, i) => {
    const dados = editar(p.dados, i + 1);
    const entrada = acumulado === "" ? dados : `${acumulado} ${dados}`;
    const hash = sha512Hex(entrada);
    acumulado = `${entrada} HASH:${hash}`;
    const ultimo = i === ps.length - 1;
    const a = ultimo ? (assi ? assi(hash) : p.assi) : null;
    return `${p.cab} ${dados} HASH:${hash}${a ? ` ASSI:${a}` : ""}`;
  });
}

// Codificador DER mínimo (só o que os testes precisam).
function comprimento(n: number): Uint8Array {
  if (n < 0x80) return new Uint8Array([n]);
  const bytes: number[] = [];
  for (let v = n; v > 0; v = Math.floor(v / 256)) bytes.unshift(v % 256);
  return new Uint8Array([0x80 | bytes.length, ...bytes]);
}

export function tlv(tag: number, valor: Uint8Array): Uint8Array {
  return concatenar(new Uint8Array([tag]), comprimento(valor.length), valor);
}

/** Chave ECDSA P-521 de teste (escalar fixo, determinístico). */
export const CHAVE_FORJADA = new Uint8Array(66).fill(1);
export const PUBLICA_FORJADA = p521.getPublicKey(CHAVE_FORJADA, false);

/** Assina como uma urna 2013/2015: ECDSA P-521 sobre sha512(bytes do último HASH), DER. */
export function assinarComoUrna(ultimoHash: string, chave = CHAVE_FORJADA): string {
  const assinatura = p521.sign(sha512(hexParaBytes(ultimoHash)), chave, { prehash: false, lowS: false, format: "der" });
  return bytesParaHex(assinatura);
}

/** Divide um hexadecimal em dois QR Codes QRCE. */
export function qrceDe(certHex: string, idue: string, modelo: string): string[] {
  const meio = Math.ceil(certHex.length / 4) * 2;
  return [
    `QRCE:1:2 IDUE:${idue} MDUE:${modelo} CERT:${certHex.slice(0, meio)}`,
    `QRCE:2:2 IDUE:${idue} MDUE:${modelo} CERT:${certHex.slice(meio)}`,
  ];
}
