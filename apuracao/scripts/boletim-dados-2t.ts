// Imprime o resumo do boletim do 2º turno (o mesmo JSON que o roteiro recebe), sem gravar nada.
// Uso: bun run scripts/boletim-dados-2t.ts [--at ISO] [--anterior data/boletins-2t/HHMM.dados.json]
import { readFileSync } from "node:fs";
import { coletarDados } from "../src/boletim/dados.ts";
import type { Base } from "../src/boletim/dados.ts";

const arg = (n: string): string | undefined => {
  const i = process.argv.indexOf(n);
  return i >= 0 ? process.argv[i + 1] : undefined;
};
const at = arg("--at");
const antPath = arg("--anterior");
const anterior = antPath ? ((JSON.parse(readFileSync(antPath, "utf8")) as { base: Base }).base ?? null) : null;
const saida = await coletarDados({ base: process.env.APURACAO_API ?? "http://127.0.0.1:4180", anterior, ...(at ? { at } : {}) });
console.log(JSON.stringify(saida, null, 1));
