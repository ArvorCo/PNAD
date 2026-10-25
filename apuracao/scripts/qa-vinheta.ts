// QA da vinheta de abertura: telão real na 4180, `#vinheta=teste` toca o mp4 de teste, o overlay cobre
// a tela e some ao fim. Grava qa/2t-vinheta.png no meio da reprodução.
import { chromium } from "@playwright/test";

const base = process.env.QA_URL ?? "http://localhost:4180";
const navegador = await chromium.launch({ channel: process.env.QA_CANAL ?? "chrome", args: ["--autoplay-policy=no-user-gesture-required"] });
const pagina = await navegador.newPage({ viewport: { width: 1920, height: 1080 } });
await pagina.goto(`${base}/#mock=1&vinheta=teste`);
await pagina.waitForSelector(".vinheta[data-tocando='1']", { timeout: 15_000 });
await pagina.waitForTimeout(1500);
const meio = await pagina.evaluate(() => {
  const r = document.querySelector(".vinheta")?.getBoundingClientRect();
  const v = document.querySelector<HTMLVideoElement>(".vinheta-video");
  return { w: r?.width, h: r?.height, t: v?.currentTime ?? 0, parado: v?.paused ?? true };
});
await pagina.screenshot({ path: "qa/2t-vinheta.png" });
await pagina.waitForSelector(".vinheta[hidden]", { state: "attached", timeout: 15_000 });
const fim = await pagina.evaluate(() => ({ oculta: document.querySelector<HTMLElement>(".vinheta")?.hidden, auto: location.hash }));
await navegador.close();
const ok = meio.w === 1920 && meio.h === 1080 && meio.t > 0 && !meio.parado && fim.oculta === true;
console.log(JSON.stringify({ meio, fim, ok }));
if (!ok) process.exit(1);
