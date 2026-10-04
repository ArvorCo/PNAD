/**
 * Copia as fontes do telão de node_modules para public/fonts/ e escreve
 * public/fonts/fonts.css. Só o subconjunto latino, estilo normal:
 * Archivo variável (eixo wght), Fraunces variável (eixos wght e opsz) e
 * IBM Plex Mono 400 e 500. `font-display: block` evita troca visível de fonte
 * no telão durante o carregamento.
 */
import { copyFile, mkdir, stat, writeFile } from "node:fs/promises";
import { join, resolve } from "node:path";

const RAIZ = resolve(import.meta.dir, "..");
const NM = join(RAIZ, "node_modules");
const DESTINO = join(RAIZ, "public/fonts");

/** Faixa unicode do subconjunto "latin" do Fontsource. */
const LATIN =
  "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD";

interface Fonte {
  familia: string;
  origem: string;
  arquivo: string;
  peso: string;
  variavel: boolean;
}

const FONTES: Fonte[] = [
  {
    familia: "Archivo",
    origem: "@fontsource-variable/archivo/files/archivo-latin-wght-normal.woff2",
    arquivo: "archivo-latin-wght-normal.woff2",
    peso: "100 900",
    variavel: true,
  },
  {
    familia: "Fraunces",
    origem: "@fontsource-variable/fraunces/files/fraunces-latin-opsz-normal.woff2",
    arquivo: "fraunces-latin-opsz-normal.woff2",
    peso: "100 900",
    variavel: true,
  },
  {
    familia: "IBM Plex Mono",
    origem: "@fontsource/ibm-plex-mono/files/ibm-plex-mono-latin-400-normal.woff2",
    arquivo: "ibm-plex-mono-latin-400-normal.woff2",
    peso: "400",
    variavel: false,
  },
  {
    familia: "IBM Plex Mono",
    origem: "@fontsource/ibm-plex-mono/files/ibm-plex-mono-latin-500-normal.woff2",
    arquivo: "ibm-plex-mono-latin-500-normal.woff2",
    peso: "500",
    variavel: false,
  },
];

function regra(f: Fonte): string {
  const url = `url("./${f.arquivo}")`;
  const src = f.variavel ? `${url} format("woff2-variations"), ${url} format("woff2")` : `${url} format("woff2")`;
  return [
    "@font-face {",
    `  font-family: "${f.familia}";`,
    "  font-style: normal;",
    "  font-display: block;",
    `  font-weight: ${f.peso};`,
    `  src: ${src};`,
    `  unicode-range: ${LATIN};`,
    "}",
  ].join("\n");
}

async function main(): Promise<void> {
  await mkdir(DESTINO, { recursive: true });
  let total = 0;
  for (const f of FONTES) {
    const alvo = join(DESTINO, f.arquivo);
    await copyFile(join(NM, f.origem), alvo);
    const bytes = (await stat(alvo)).size;
    total += bytes;
    console.log(`${f.arquivo.padEnd(40)} ${(bytes / 1024).toFixed(1).padStart(7)} kB`);
  }
  const css = `/* Gerado por scripts/copiar-fontes.ts. Não editar à mão. */\n${FONTES.map(regra).join("\n\n")}\n`;
  await writeFile(join(DESTINO, "fonts.css"), css);
  console.log(`total ${(total / 1024).toFixed(1)} kB em ${FONTES.length} arquivos`);
}

await main();
