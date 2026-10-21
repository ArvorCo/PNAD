// Garante o binário do Chrome Headless Shell que o Remotion baixa mas não consegue extrair aqui.
// Uso: node navegador.mjs  (exporta o caminho; stills.mjs e remotion.config.ts o procuram no mesmo lugar)
import { execFileSync } from "node:child_process";
import { existsSync, mkdirSync, rmSync } from "node:fs";
import path from "node:path";

const base = path.resolve("node_modules/.remotion/chrome-headless-shell");
const zip = path.join(base, "chrome-headless-shell-mac-arm64.zip");
const pasta = path.join(base, "mac-arm64");
export const BINARIO = path.join(pasta, "chrome-headless-shell-mac-arm64", "chrome-headless-shell");
export const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";

export const navegador = () => {
  if (existsSync(BINARIO)) {
    return BINARIO;
  }
  if (existsSync(zip)) {
    rmSync(pasta, { recursive: true, force: true });
    mkdirSync(pasta, { recursive: true });
    execFileSync("unzip", ["-q", zip], { cwd: pasta, stdio: "inherit" });
    if (existsSync(BINARIO)) {
      return BINARIO;
    }
  }
  if (existsSync(CHROME)) {
    return CHROME;
  }
  return null;
};

if (process.argv[1] && path.resolve(process.argv[1]) === new URL(import.meta.url).pathname) {
  console.log(navegador() ?? "nenhum navegador encontrado; rode `npx remotion browser ensure` e `unzip` o zip");
}
