// Utilitários de teste: leitura das fixtures reais do TSE.
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { parseJson } from "../src/parse/schemas.ts";
import type { AbFile, EFile, EleC, MunCm, ResultadoU } from "../src/parse/schemas.ts";
import type { Tipo } from "../src/types.ts";

export const FIXTURES = join(import.meta.dir, "fixtures");

export function bytes(nome: string): Uint8Array<ArrayBuffer> {
  return new Uint8Array(readFileSync(join(FIXTURES, nome)));
}

export function json(nome: string): unknown {
  return JSON.parse(readFileSync(join(FIXTURES, nome), "utf8"));
}

function parse(tipo: Tipo, nome: string): unknown {
  const r = parseJson(tipo, json(nome));
  if (!r.ok) throw new Error(`${nome}: ${r.erro}`);
  return r.parsed.data;
}

export const lerU = (nome: string): ResultadoU => parse("u", nome) as ResultadoU;
export const lerAb = (nome: string): AbFile => parse("ab", nome) as AbFile;
export const lerCm = (nome: string): MunCm => parse("cm", nome) as MunCm;
export const lerEleC = (nome: string): EleC => parse("ele-c", nome) as EleC;
export const lerE = (nome: string): EFile => parse("e", nome) as EFile;
