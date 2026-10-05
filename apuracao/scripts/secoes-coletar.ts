// Coleta retomável dos boletins de urna (BU) do 1º turno de 2026, seção a seção, com o
// modelo da urna lido no log da própria urna, e conferência automática por zona.
//
//   bun run scripts/secoes-coletar.ts                       # todas as UFs, ordem das pequenas para SP, depois zz
//   bun run scripts/secoes-coletar.ts --ufs ac              # só o Acre
//   bun run scripts/secoes-coletar.ts --refazer-erros       # repete seções com erro
//   bun run scripts/secoes-coletar.ts --revisitar           # repete seções sem BU (aux sem boletim, 404)
//   bun run scripts/secoes-coletar.ts --so-conferir --ufs ac
//   opções: --rps 74 (teto 80) --concorrencia 32 --guardar-log --refresh-cs --limite N
//           --db data/secoes_2026.sqlite --apuracao data/apuracao.sqlite
//
// Por seção: aux.json -> hash -> -bu.dat (gzip no banco, decodificado em bu, bu_cargo e
// voto_secao) e -log.jez (só o modelo e as urnas; o ZIP só fica com --guardar-log).
// Zona concluída: soma das seções contra o arquivo de zona do coletor (conferencia_zona).
// Log em JSON por linha: data/logs/secoes-AAAAMMDD.log. Pidfile: data/secoes.pid.
import { Database } from "bun:sqlite";
import { appendFileSync, existsSync, mkdirSync, readFileSync, unlinkSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { parseArgs } from "node:util";
import { abrirSecoes, EscritorSecoes } from "./secoes/banco.ts";
import type { ResultadoSecao, SecaoCs } from "./secoes/banco.ts";
import { conferirZona } from "./secoes/conferencia.ts";
import { CsSchema, secoesDoCs } from "./secoes/cs.ts";
import { ClienteTse } from "./secoes/http.ts";
import { coletarSecao, sha256, urlCs } from "./secoes/secao.ts";

/** Pequenas primeiro, SP por último entre as UFs, exterior no fim. */
export const ORDEM_UF = [
  "ac", "ap", "rr", "ro", "to", "se", "df", "al", "ms", "mt", "es", "rn", "pb", "pi", "am",
  "pa", "go", "sc", "ce", "ma", "pe", "rs", "pr", "ba", "rj", "mg", "sp", "zz",
] as const;

const RAIZ = join(import.meta.dir, "..");
const RPS_MAX = 80;

const { values: a } = parseArgs({
  options: {
    ufs: { type: "string" },
    rps: { type: "string", default: "74" },
    concorrencia: { type: "string", default: "32" },
    "refazer-erros": { type: "boolean", default: false },
    revisitar: { type: "boolean", default: false },
    "refresh-cs": { type: "boolean", default: false },
    "guardar-log": { type: "boolean", default: false },
    "so-conferir": { type: "boolean", default: false },
    limite: { type: "string" },
    db: { type: "string", default: join(RAIZ, "data", "secoes_2026.sqlite") },
    apuracao: { type: "string", default: join(RAIZ, "data", "apuracao.sqlite") },
  },
  strict: true,
});

const ufs = a.ufs === undefined ? [...ORDEM_UF] : ORDEM_UF.filter((u) => (a.ufs ?? "").toLowerCase().split(",").includes(u));
if (ufs.length === 0) throw new Error(`--ufs sem UF válida: ${a.ufs}`);
const rps = Math.min(RPS_MAX, Math.max(1, Number(a.rps)));
const concorrencia = Math.max(1, Math.min(64, Number.parseInt(a.concorrencia ?? "32", 10)));
const limite = a.limite === undefined ? Number.POSITIVE_INFINITY : Number.parseInt(a.limite, 10);

const hoje = new Date();
const dia = `${hoje.getFullYear()}${String(hoje.getMonth() + 1).padStart(2, "0")}${String(hoje.getDate()).padStart(2, "0")}`;
const DIR_LOG = join(RAIZ, "data", "logs");
const DIR_CS = join(RAIZ, "data", "secoes", "cs");
const ARQ_LOG = join(DIR_LOG, `secoes-${dia}.log`);
const PIDFILE = join(RAIZ, "data", "secoes.pid");
mkdirSync(DIR_LOG, { recursive: true });
mkdirSync(DIR_CS, { recursive: true });

function log(o: Record<string, unknown>): void {
  const linha = JSON.stringify({ em: new Date().toISOString(), ...o });
  appendFileSync(ARQ_LOG, `${linha}\n`);
  if (process.stdout.isTTY) console.log(linha);
}

function vivo(pid: number): boolean {
  try {
    process.kill(pid, 0);
    return true;
  } catch {
    return false;
  }
}

if (existsSync(PIDFILE)) {
  const pid = Number.parseInt(readFileSync(PIDFILE, "utf8"), 10);
  if (Number.isFinite(pid) && pid !== process.pid && vivo(pid)) {
    console.error(`outra coleta em andamento (pid ${pid}, ${PIDFILE})`);
    process.exit(1);
  }
}
writeFileSync(PIDFILE, String(process.pid));
const limparPid = (): void => {
  try {
    if (existsSync(PIDFILE) && readFileSync(PIDFILE, "utf8").trim() === String(process.pid)) unlinkSync(PIDFILE);
  } catch {
    // pidfile já removido
  }
};
process.on("exit", limparPid);

let parar = false;
for (const sinal of ["SIGINT", "SIGTERM"] as const) {
  process.on(sinal, () => {
    if (parar) process.exit(130);
    parar = true;
    log({ t: "parando", sinal });
  });
}

const db = abrirSecoes(a.db);
const apuracao = new Database(a.apuracao, { readonly: true });
const escritor = new EscritorSecoes(db);
const cliente = new ClienteTse({ rps, log });
db.query("INSERT OR REPLACE INTO meta (chave, valor) VALUES ('fonte', ?)").run("resultados.tse.jus.br/oficial/ele2026/arquivo-urna/3220");

// ---------------------------------------------------------------- configuração de seções
async function prepararUf(uf: string): Promise<number> {
  const arq = join(DIR_CS, `${uf}-p003220-cs.json`);
  let bruto: Uint8Array;
  if (existsSync(arq) && a["refresh-cs"] !== true) {
    bruto = new Uint8Array(readFileSync(arq));
  } else {
    const r = await cliente.obter(urlCs(uf));
    if (r.corpo === null) throw new Error(`${uf}: cs indisponível (${r.erro ?? "sem corpo"})`);
    bruto = r.corpo;
    writeFileSync(arq, bruto);
  }
  const cs = CsSchema.parse(JSON.parse(new TextDecoder().decode(bruto)));
  const secoes = secoesDoCs(cs);
  db.query("INSERT OR REPLACE INTO cs (uf, dg, hg, idg, secoes, bytes, sha256, baixado_em) VALUES (?, ?, ?, ?, ?, ?, ?, ?)").run(
    uf, cs.dg ?? null, cs.hg ?? null, cs.idg ?? null, secoes.length, bruto.byteLength, sha256(bruto), new Date().toISOString(),
  );
  escritor.semear(secoes);
  return secoes.length;
}

function pendentes(uf: string): SecaoCs[] {
  const cond = ["baixado_em IS NULL"];
  if (a["refazer-erros"] === true) cond.push("erro IS NOT NULL", "status_aux = 'aux_erro'");
  if (a.revisitar === true) cond.push("bu_gz IS NULL");
  return db
    .query<SecaoCs, [string]>(`SELECT uf, mun, zona, secao, nsp, nsa FROM secao WHERE uf = ? AND (${cond.join(" OR ")}) ORDER BY mun, zona, secao`)
    .all(uf);
}

// ---------------------------------------------------------------- conferência
const chaveZ = (uf: string, mun: string, zona: number): string => `${uf}|${mun}|${zona}`;
const resumoConf = { zonas: 0, ok: 0, diverge: 0, sem_arquivo: 0 };

function conferir(uf: string, mun: string, zona: number): void {
  const agora = new Date().toISOString();
  try {
    const linhas = conferirZona(db, apuracao, uf, mun, zona, agora);
    resumoConf.zonas += 1;
    for (const l of linhas) {
      if (l.ok === true) resumoConf.ok += 1;
      else if (l.ok === false) {
        resumoConf.diverge += 1;
        log({ t: "conferencia_divergente", uf, mun, zona, cargo: l.cargo, chave: l.chave, divergencias: l.divergencias.slice(0, 20) });
      } else resumoConf.sem_arquivo += 1;
    }
  } catch (e) {
    log({ t: "conferencia_erro", uf, mun, zona, erro: e instanceof Error ? e.message : String(e) });
  }
}

const qIncompleta = db.query<{ x: number }, [string, string, number]>("SELECT 1 AS x FROM secao WHERE uf = ? AND mun = ? AND zona = ? AND baixado_em IS NULL LIMIT 1");
/** Zona sem seção por baixar (com --limite a fila pode cobrir só parte dela). */
const zonaCompleta = (uf: string, mun: string, zona: number): boolean => qIncompleta.get(uf, mun, zona) === null;

/** Zonas com BU e sem conferência (retomada, --so-conferir). */
function zonasSemConferencia(uf: string, todas: boolean): Array<{ mun: string; zona: number }> {
  const sql = todas
    ? "SELECT DISTINCT mun, zona FROM bu WHERE uf = ? ORDER BY mun, zona"
    : `SELECT DISTINCT b.mun, b.zona FROM bu b WHERE b.uf = ?1
       AND NOT EXISTS (SELECT 1 FROM conferencia_zona c WHERE c.uf = b.uf AND c.mun = b.mun AND c.zona = b.zona)
       AND NOT EXISTS (SELECT 1 FROM secao s WHERE s.uf = b.uf AND s.mun = b.mun AND s.zona = b.zona AND s.baixado_em IS NULL)
       ORDER BY b.mun, b.zona`;
  return db.query<{ mun: string; zona: number }, [string]>(sql).all(uf);
}

// ---------------------------------------------------------------- progresso
interface PorUf {
  total: number;
  feitas: number;
  comBu: number;
  erros: number;
  inicio: number | null;
  fim: number | null;
}
const porUf = new Map<string, PorUf>();
const marcas: Array<[number, number]> = [];
let feitasRun = 0;
let requisicoesRun = 0;
let restantes = 0;
const t0 = Date.now();

function taxa60(): number {
  const agora = Date.now();
  while (marcas.length > 0 && (marcas[0]?.[0] ?? agora) < agora - 60_000) marcas.shift();
  const n = marcas.reduce((s, m) => s + m[1], 0);
  const janela = Math.min(60, (agora - t0) / 1000);
  return janela > 0 ? n / janela : 0;
}

function progresso(t: string): void {
  const sps = taxa60();
  const ufsResumo = Object.fromEntries(
    [...porUf.entries()].filter(([, p]) => p.inicio !== null && (p.fim === null || Date.now() - p.fim < 20_000)).map(([uf, p]) => [uf, `${p.feitas}/${p.total} bu=${p.comBu} err=${p.erros}`]),
  );
  log({
    t, secoes_por_s: Math.round(sps * 10) / 10, req_por_s: Math.round((requisicoesRun / Math.max(1, (Date.now() - t0) / 1000)) * 10) / 10,
    feitas_run: feitasRun, restantes, eta_min: sps > 0 ? Math.round(restantes / sps / 60) : null, mb: Math.round(cliente.bytes / 1048576),
    http: cliente.contagem, conferencia: resumoConf, ufs: ufsResumo,
  });
}

// ---------------------------------------------------------------- execução
async function main(): Promise<void> {
  log({ t: "inicio", ufs, rps, concorrencia, db: a.db, guardar_log: a["guardar-log"], pid: process.pid });
  const fila: SecaoCs[] = [];
  for (const uf of ufs) {
    const total = await prepararUf(uf);
    const feitas = db.query<{ b: number | null; e: number | null }, [string]>(
      "SELECT SUM(bu_gz IS NOT NULL) AS b, SUM(erro IS NOT NULL) AS e FROM secao WHERE uf = ? AND baixado_em IS NOT NULL",
    ).get(uf);
    const pend = a["so-conferir"] === true ? [] : pendentes(uf);
    porUf.set(uf, { total, feitas: total - pend.length, comBu: feitas?.b ?? 0, erros: feitas?.e ?? 0, inicio: null, fim: null });
    for (const s of pend) {
      if (fila.length >= limite) break;
      fila.push(s);
    }
    log({ t: "cs", uf, secoes: total, pendentes: pend.length });
  }
  if (a["so-conferir"] === true) {
    for (const uf of ufs) for (const z of zonasSemConferencia(uf, true)) if (zonaCompleta(uf, z.mun, z.zona)) conferir(uf, z.mun, z.zona);
    progresso("fim_conferencia");
    return;
  }
  // retomada: zonas já completas sem conferência
  for (const uf of ufs) for (const z of zonasSemConferencia(uf, false)) conferir(uf, z.mun, z.zona);

  const pendZona = new Map<string, number>();
  for (const s of fila) pendZona.set(chaveZ(s.uf, s.mun, s.zona), (pendZona.get(chaveZ(s.uf, s.mun, s.zona)) ?? 0) + 1);
  restantes = fila.length;
  log({ t: "fila", secoes: fila.length, zonas: pendZona.size });

  const buffer: ResultadoSecao[] = [];
  const flush = (): void => {
    if (buffer.length === 0) return;
    const lote = buffer.splice(0);
    escritor.gravar(lote, new Date().toISOString());
    for (const r of lote) {
      const k = chaveZ(r.uf, r.mun, r.zona);
      const n = (pendZona.get(k) ?? 1) - 1;
      pendZona.set(k, n);
      if (n === 0) {
        pendZona.delete(k);
        if (zonaCompleta(r.uf, r.mun, r.zona)) conferir(r.uf, r.mun, r.zona);
      }
    }
  };

  let idx = 0;
  const trabalhador = async (): Promise<void> => {
    while (!parar) {
      const s = fila[idx];
      idx += 1;
      if (s === undefined) return;
      const p = porUf.get(s.uf);
      if (p !== undefined && p.inicio === null) {
        p.inicio = Date.now();
        log({ t: "uf_inicio", uf: s.uf });
      }
      const r = await coletarSecao(s, { obter: (u) => cliente.obter(u), guardarLog: a["guardar-log"] === true });
      buffer.push(r);
      feitasRun += 1;
      restantes -= 1;
      requisicoesRun += r.requisicoes;
      marcas.push([Date.now(), 1]);
      if (p !== undefined) {
        p.feitas += 1;
        if (r.buGz !== null) p.comBu += 1;
        if (r.erro !== null) p.erros += 1;
        if (p.feitas >= p.total && p.fim === null) {
          p.fim = Date.now();
          log({ t: "uf_fim", uf: s.uf, secoes: p.total, com_bu: p.comBu, erros: p.erros, min: Math.round((p.fim - (p.inicio ?? p.fim)) / 600) / 100 });
        }
      }
      if (r.erro !== null) log({ t: "erro_secao", uf: r.uf, mun: r.mun, zona: r.zona, secao: r.secao, status_aux: r.statusAux, erro: r.erro });
    }
  };

  const tFlush = setInterval(flush, 500);
  const tProg = setInterval(() => progresso("progresso"), 15_000);
  await Promise.all(Array.from({ length: concorrencia }, () => trabalhador()));
  clearInterval(tFlush);
  clearInterval(tProg);
  flush();
  // zonas que ficaram completas por retomada parcial
  for (const uf of ufs) for (const z of zonasSemConferencia(uf, false)) conferir(uf, z.mun, z.zona);
  db.run("PRAGMA wal_checkpoint(TRUNCATE)");
  progresso(parar ? "interrompido" : "fim");
}

try {
  await main();
} catch (e) {
  log({ t: "falha", erro: e instanceof Error ? `${e.message}\n${e.stack ?? ""}` : String(e) });
  process.exitCode = 1;
} finally {
  db.close();
  apuracao.close();
  limparPid();
}
