import { Config } from "@remotion/cli/config";
import { existsSync } from "node:fs";
import path from "node:path";

Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
Config.setPublicDir("./public");
Config.setConcurrency(6);

// A extração automática do Chrome Headless Shell pelo Remotion falha nesta máquina (só ABOUT e
// LICENSE saem do zip). `node navegador.mjs` extrai o zip à mão; na falta dele, usa o Chrome instalado.
const shell = path.resolve(
  "node_modules/.remotion/chrome-headless-shell/mac-arm64/chrome-headless-shell-mac-arm64/chrome-headless-shell",
);
const chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
Config.setBrowserExecutable(existsSync(shell) ? shell : existsSync(chrome) ? chrome : null);
