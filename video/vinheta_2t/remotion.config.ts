import { Config } from "@remotion/cli/config";
import { existsSync } from "node:fs";

Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
Config.setPublicDir("./public");

const shell =
  "/Users/leonardodias/arvor/PNAD/video/fiscais/node_modules/.remotion/chrome-headless-shell/mac-arm64/chrome-headless-shell-mac-arm64/chrome-headless-shell";
const chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
Config.setBrowserExecutable(existsSync(shell) ? shell : existsSync(chrome) ? chrome : null);
