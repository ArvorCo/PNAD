// Quadros de conferência: empacota uma vez e grava PNGs de vários quadros das duas composições.
// Uso: node stills.mjs FiscaisWide 250 620 1300 ...   (saída em out/stills/<comp>_<quadro>.png)
import { bundle } from "@remotion/bundler";
import { renderStill, selectComposition } from "@remotion/renderer";
import { mkdirSync } from "node:fs";
import path from "node:path";
import { navegador } from "./navegador.mjs";

const [comp, ...quadros] = process.argv.slice(2);
const serveUrl = await bundle({ entryPoint: path.resolve("src/index.ts"), publicDir: path.resolve("public") });
const browserExecutable = navegador();
const composition = await selectComposition({ serveUrl, id: comp, browserExecutable });
mkdirSync("out/stills", { recursive: true });
for (const q of quadros) {
  const output = `out/stills/${comp}_${q}.png`;
  await renderStill({ composition, serveUrl, output, frame: Number(q), imageFormat: "png", browserExecutable });
  console.log(output);
}
