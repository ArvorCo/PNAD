// Uma varredura completa de todos os arquivos do registro, na taxa do balde de varredura,
// e uma segunda passada de T0 para medir o 304. Imprime relatório e sai.
// Uso: bun run sweep   (APURACAO_SWEEP_RPS=80 para acelerar; teto 100)
import type { Database } from "bun:sqlite";
import { lerConfig } from "../src/config.ts";
import { fecharEscrita } from "../src/db/abrir.ts";
import { Agendador } from "../src/collector/agendador.ts";
import { inicializar } from "../src/collector/bootstrap.ts";
import { fetchTse } from "../src/collector/http.ts";
import { Limitador } from "../src/collector/limitador.ts";
import { isoDe, relogioReal } from "../src/collector/relogio.ts";
import type { Tier } from "../src/types.ts";

const log = (o: Record<string, unknown>): void => console.log(JSON.stringify({ em: new Date().toISOString(), ...o }));

function percentil(ordenado: readonly number[], p: number): number | null {
  if (ordenado.length === 0) return null;
  return ordenado[Math.min(ordenado.length - 1, Math.floor((p / 100) * ordenado.length))] ?? null;
}

function relatorio(db: Database, de: number, ate: number): Record<string, unknown> {
  const classes = db
    .query<{ classe: string; n: number }, [number, number]>("SELECT classe, COUNT(*) AS n FROM fetch WHERE id > ? AND id <= ? GROUP BY 1 ORDER BY 2 DESC")
    .all(de, ate);
  const inexistentes = db
    .query<{ tipo: string; nivel: string | null; uf: string | null; n: number }, [number, number]>(
      `SELECT a.tipo, a.nivel, a.uf, COUNT(*) AS n FROM fetch f JOIN arquivo a ON a.id = f.arquivo_id
       WHERE f.id > ? AND f.id <= ? AND f.classe = 'nao_existe' GROUP BY 1, 2, 3 ORDER BY 4 DESC`,
    )
    .all(de, ate);
  const dur = db
    .query<{ d: number }, [number, number]>("SELECT duracao_ms AS d FROM fetch WHERE id > ? AND id <= ? AND duracao_ms IS NOT NULL ORDER BY 1")
    .all(de, ate)
    .map((r) => r.d);
  const tot = db
    .query<{ n: number; bytes: number | null; ini: string | null; fim: string | null }, [number, number]>(
      "SELECT COUNT(*) AS n, SUM(bytes) AS bytes, MIN(iniciado_em) AS ini, MAX(iniciado_em) AS fim FROM fetch WHERE id > ? AND id <= ?",
    )
    .get(de, ate);
  return {
    requisicoes: tot?.n ?? 0, bytes: tot?.bytes ?? 0, mb: Math.round(((tot?.bytes ?? 0) / 1048576) * 10) / 10,
    inicio: tot?.ini, fim: tot?.fim, classes: Object.fromEntries(classes.map((c) => [c.classe, c.n])),
    nao_existe: inexistentes, p50_ms: percentil(dur, 50), p95_ms: percentil(dur, 95), max_ms: dur.at(-1) ?? null,
  };
}

const maxFetch = (db: Database): number => db.query<{ m: number | null }, []>("SELECT MAX(id) AS m FROM fetch").get()?.m ?? 0;

async function passada(ag: Agendador, tiers: readonly Tier[]): Promise<void> {
  ag.varredura.iniciar(relogioReal.agora(), { tiers, pularRecentesS: 0, incluirInativos: true });
  await ag.rodar(true);
  ag.passo();
}

async function main(): Promise<void> {
  const env = process.env;
  const config = lerConfig(env);
  const rps = Math.min(100, Math.max(1, Number.parseInt(env.APURACAO_SWEEP_RPS ?? String(config.rateSweep), 10) || config.rateSweep));
  const c = await inicializar(config, { log, eleicoesForcadas: env.APURACAO_ELEICOES !== undefined && env.APURACAO_ELEICOES !== "" });
  const limitador = new Limitador(relogioReal, { global: { taxa: config.rateGlobal, rajada: config.rateGlobal * 2 }, sweep: { taxa: rps, rajada: rps } });
  const http = { ...c.http, semCondicional: env.APURACAO_SEM_CONDICIONAL === "1" };
  const ag = new Agendador({
    relogio: relogioReal, ctx: c.ctx, limitador, modo: "unico", concurrencyMin: config.concurrencyMin, log,
    fetcher: (job, fs) => fetchTse(job, { etag: fs.etag, lastModified: fs.lastModified }, http),
  });
  ag.varredura.automatica = false;
  ag.aCada(15_000, (agora) => {
    const j = ag.metricas.janela(agora);
    log({ t: "progresso", total: ag.metricas.total, fila: ag.fila.tamanho, em_voo: ag.emVoo, sweep: ag.resumoSweep(), taxas_60s: j.taxas });
  });
  log({ t: "sweep_once_inicio", arquivos: c.estado.porId.size, rps });
  const ini = maxFetch(c.db);
  const t0 = Date.now();
  await passada(ag, [0, 1, 2, 3, 4]);
  c.lote.gravar();
  const fim1 = maxFetch(c.db);
  const r1 = relatorio(c.db, ini, fim1);
  await passada(ag, [0]);
  c.lote.gravar();
  const fim2 = maxFetch(c.db);
  const r2 = relatorio(c.db, fim1, fim2);
  const resumo = { passada_completa: r1, segunda_passada_t0: r2, duracao_s: Math.round((Date.now() - t0) / 1000), rps };
  ag.registrarEvento({ em: isoDe(Date.now()), tipo: "sweep_relatorio", detalhe: resumo });
  c.lote.gravar();
  fecharEscrita(c.db);
  console.log(JSON.stringify(resumo, null, 2));
}

main().catch((err: unknown) => {
  log({ t: "fatal", erro: err instanceof Error ? `${err.message}\n${err.stack ?? ""}` : String(err) });
  process.exit(1);
});
