// Coletor da apuração: `bun run collect`. Único escritor do SQLite.
import { existsSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { lerConfig } from "../config.ts";
import { fecharEscrita } from "../db/abrir.ts";
import { Agendador } from "./agendador.ts";
import { inicializar } from "./bootstrap.ts";
import { instalarGanchos } from "./ganchos.ts";
import { fetchTse } from "./http.ts";
import { Limitador } from "./limitador.ts";
import { isoDe, relogioReal } from "./relogio.ts";

const log = (o: Record<string, unknown>): void => console.log(JSON.stringify({ em: new Date().toISOString(), ...o }));

function vivo(pid: number): boolean {
  try {
    process.kill(pid, 0);
    return true;
  } catch {
    return false;
  }
}

function tomarPidfile(path: string): void {
  if (existsSync(path)) {
    const pid = Number.parseInt(readFileSync(path, "utf8"), 10);
    if (Number.isFinite(pid) && pid !== process.pid && vivo(pid)) {
      throw new Error(`outro coletor rodando (pid ${pid}, ${path})`);
    }
    log({ t: "aviso", msg: `pidfile velho removido (pid ${pid})` });
  }
  writeFileSync(path, String(process.pid));
}

async function main(): Promise<void> {
  const env = process.env;
  const config = lerConfig(env);
  const pidfile = join(dirname(config.dbPath), "collect.pid");
  tomarPidfile(pidfile);
  const c = await inicializar(config, { log, eleicoesForcadas: env.APURACAO_ELEICOES !== undefined && env.APURACAO_ELEICOES !== "" });
  const http = { ...c.http, semCondicional: env.APURACAO_SEM_CONDICIONAL === "1" };
  const limitador = new Limitador(relogioReal, {
    global: { taxa: config.rateGlobal, rajada: config.rateGlobal * 2 },
    sweep: { taxa: config.rateSweep, rajada: config.rateSweep },
  });
  const ag = new Agendador({
    relogio: relogioReal,
    ctx: c.ctx,
    limitador,
    concurrencyMin: config.concurrencyMin,
    fetcher: (job, fs) => fetchTse(job, { etag: fs.etag, lastModified: fs.lastModified }, http),
    log,
  });
  instalarGanchos(c, ag, () => ({ ate: limitador.pausadoAte(), nivel: limitador.nivel }));
  ag.semear();
  const resumo = { ...config, userAgent: config.userAgent.slice(0, 40) };
  ag.registrarEvento({
    em: isoDe(Date.now()), tipo: "startup",
    detalhe: { bun: Bun.version, pid: process.pid, config: resumo, arquivos: c.estado.porId.size, fila: ag.fila.tamanho },
  });
  c.lote.gravar();
  log({ t: "startup", bun: Bun.version, arquivos: c.estado.porId.size, fila: ag.fila.tamanho, db: config.dbPath });

  let parando = false;
  const desligar = async (sinal: string): Promise<void> => {
    if (parando) {
      log({ t: "saida_forcada", sinal });
      process.exit(1);
    }
    parando = true;
    log({ t: "desligando", sinal, em_voo: ag.emVoo });
    await ag.parar(10_000);
    ag.registrarEvento({ em: isoDe(Date.now()), tipo: "shutdown", detalhe: { sinal, total_fetch: ag.metricas.total } });
    c.lote.gravar();
    fecharEscrita(c.db);
    rmSync(pidfile, { force: true });
    log({ t: "shutdown", sinal });
    process.exit(0);
  };
  process.on("SIGINT", () => void desligar("SIGINT"));
  process.on("SIGTERM", () => void desligar("SIGTERM"));
  await ag.rodar();
}

main().catch((err: unknown) => {
  log({ t: "fatal", erro: err instanceof Error ? `${err.message}\n${err.stack ?? ""}` : String(err) });
  process.exit(1);
});
