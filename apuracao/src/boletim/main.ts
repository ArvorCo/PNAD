// Processo do boletim falado do 2º turno (`bun run boletim`, use scripts/start-boletim.sh no dia).
// Fica fora do servidor de propósito: uma correção no roteiro ou nos dados reinicia só este
// processo, nunca o servidor do telão. Escritor único de indice.json e gerador.json.
import { existsSync, mkdirSync, readFileSync, unlinkSync, writeFileSync } from "node:fs";
import { caminho, dirBoletins } from "./estado.ts";
import { GeradorBoletim } from "./gerador.ts";
import { inicioDoRelogio } from "./relogio.ts";

const dir = dirBoletins();
mkdirSync(dir, { recursive: true });
const pidPath = caminho(dir, "gerador.pid");
if (existsSync(pidPath)) {
  const pid = Number(readFileSync(pidPath, "utf8").trim());
  let vivo = false;
  try {
    vivo = pid > 0 && pid !== process.pid && process.kill(pid, 0);
  } catch {
    vivo = false;
  }
  if (vivo) {
    console.error(`boletim: outro gerador já está rodando (pid ${pid}, ${pidPath})`);
    process.exit(3);
  }
}
writeFileSync(pidPath, String(process.pid));

const intervaloS = Number(process.env.APURACAO_BOLETIM_INTERVALO_S ?? 600);
const g = new GeradorBoletim({
  dir,
  api: process.env.APURACAO_API ?? `http://127.0.0.1:${process.env.APURACAO_PORT ?? 4180}`,
  relogioLigado: process.env.APURACAO_BOLETIM === "1",
  intervaloS: Number.isFinite(intervaloS) && intervaloS >= 60 ? intervaloS : 600,
  inicioMs: inicioDoRelogio(process.env.APURACAO_BOLETIM_INICIO, new Date()),
  ...(process.env.APURACAO_BOLETIM_AT ? { at: process.env.APURACAO_BOLETIM_AT } : {}),
});
g.iniciar();

// SIGTERM sai com 143 para o laço do start-boletim.sh religar (recarregar código: pkill -f src/boletim/main.ts);
// para desligar de vez, mate antes o laço (data/boletins-2t/laco.pid).
const sair = (codigo: number): void => {
  g.parar();
  try {
    if (readFileSync(pidPath, "utf8").trim() === String(process.pid)) unlinkSync(pidPath);
  } catch {
    // pidfile já removido
  }
  process.exit(codigo);
};
process.on("SIGINT", () => sair(0));
process.on("SIGTERM", () => sair(143));
