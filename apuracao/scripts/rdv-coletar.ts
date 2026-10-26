// Coleta retomável dos Registros Digitais do Voto (RDV, `-rdv.dat`) do 2º turno de 2026, seção a
// seção, num banco próprio (data/rdv_2t_2026.sqlite), com conferência contra o BU da mesma seção.
//
//   bun run scripts/rdv-coletar.ts --ufs ac             # só o Acre
//   bun run scripts/rdv-coletar.ts                      # todas as UFs, mesma ordem da coleta de BUs
//   bun run scripts/rdv-coletar.ts --so-conferir        # reconfere seções com BU que chegou depois
//   bun run scripts/rdv-coletar.ts --so-conferir --reconferir-divergentes   # e refaz as que divergiram
//   opções: --rps 60 (teto 70) --rps-com-bu 10 --concorrencia 24 --refazer-erros --limite N
//           --db data/rdv_2t_2026.sqlite --secoes data/secoes_2t_2026.sqlite
//
// O aux.json e o BU vêm de data/secoes_2t_2026.sqlite, aberto SÓ PARA LEITURA (a coleta de BUs
// escreve nele). Seção ainda sem aux lá: o aux é pedido ao TSE e guardado no banco do RDV.
// Taxa: enquanto o pid de data/secoes-p003221.pid estiver vivo, --rps-com-bu (10/s); depois,
// --rps (60/s). O teto somado com a coleta de BUs (78/s) fica perto do usado no 1º turno.
//
// O RDV guarda os votos por eleição e por cargo, cada lista ordenada por tipo e digitação
// (especificação do TSE, rdv.asn1 e README do pacote): não liga o voto de presidente ao de
// governador de um mesmo eleitor. O banco guarda as contagens por (tipo, digitação) de cada
// cargo; a matriz presidente × governador não é identificável e só sai como limites em
// scripts/apuracao-2t-2026-rdv.py.
import { Database } from "bun:sqlite";
import { appendFileSync, existsSync, mkdirSync, readFileSync, unlinkSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { parseArgs } from "node:util";
import { ClienteTse } from "./secoes/http.ts";
import { abrirRdv, dirSecao2t, escolherRdv, EscritorRdv, urlAux2t } from "./secoes/rdv-banco.ts";
import type { ResultadoRdv, SecaoAlvo } from "./secoes/rdv-banco.ts";
import { AuxSchema, sha256 } from "./secoes/secao.ts";
import { conferirComBu, decodificarRdv } from "../src/secoes2t/rdv-decode.ts";
import type { LinhaVotoBu } from "../src/secoes2t/rdv-decode.ts";
import { ORDEM_UF } from "./secoes/ordem.ts";

const RAIZ = join(import.meta.dir, "..");
const RPS_MAX = 70;

const { values: a } = parseArgs({
  options: {
    ufs: { type: "string" },
    rps: { type: "string", default: "60" },
    "rps-com-bu": { type: "string", default: "10" },
    concorrencia: { type: "string", default: "24" },
    "refazer-erros": { type: "boolean", default: false },
    "so-conferir": { type: "boolean", default: false },
    "reconferir-divergentes": { type: "boolean", default: false },
    limite: { type: "string" },
    db: { type: "string", default: join(RAIZ, "data", "rdv_2t_2026.sqlite") },
    secoes: { type: "string", default: join(RAIZ, "data", "secoes_2t_2026.sqlite") },
    "pid-bu": { type: "string", default: join(RAIZ, "data", "secoes-p003221.pid") },
  },
  strict: true,
});


const ufs = a.ufs === undefined ? [...ORDEM_UF] : ORDEM_UF.filter((u) => (a.ufs ?? "").toLowerCase().split(",").includes(u));
if (ufs.length === 0) throw new Error(`--ufs sem UF válida: ${a.ufs}`);
const rps = Math.min(RPS_MAX, Math.max(1, Number(a.rps)));
const rpsComBu = Math.min(rps, Math.max(1, Number(a["rps-com-bu"])));
const concorrencia = Math.max(1, Math.min(64, Number.parseInt(a.concorrencia ?? "24", 10)));
const limite = a.limite === undefined ? Number.POSITIVE_INFINITY : Number.parseInt(a.limite, 10);

const hoje = new Date();
const dia = `${hoje.getFullYear()}${String(hoje.getMonth() + 1).padStart(2, "0")}${String(hoje.getDate()).padStart(2, "0")}`;
const DIR_LOG = join(RAIZ, "data", "logs");
const ARQ_LOG = join(DIR_LOG, `rdv-p003221-${dia}.log`);
const PIDFILE = join(RAIZ, "data", "rdv-p003221.pid");
mkdirSync(DIR_LOG, { recursive: true });

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

function pidDe(arq: string): number | null {
  if (!existsSync(arq)) return null;
  const pid = Number.parseInt(readFileSync(arq, "utf8"), 10);
  return Number.isFinite(pid) ? pid : null;
}

const outro = pidDe(PIDFILE);
if (outro !== null && outro !== process.pid && vivo(outro)) {
  console.error(`outra coleta de RDV em andamento (pid ${outro}, ${PIDFILE})`);
  process.exit(1);
}
writeFileSync(PIDFILE, String(process.pid));
process.on("exit", () => {
  try {
    if (existsSync(PIDFILE) && readFileSync(PIDFILE, "utf8").trim() === String(process.pid)) unlinkSync(PIDFILE);
  } catch {
    // pidfile já removido
  }
});

let parar = false;
for (const sinal of ["SIGINT", "SIGTERM"] as const) {
  process.on(sinal, () => {
    if (parar) process.exit(130);
    parar = true;
    log({ t: "parando", sinal });
  });
}

// ---------------------------------------------------------------- taxa compartilhada
let buViva = false;
function checarBu(): boolean {
  const pid = pidDe(a["pid-bu"]);
  const agora = pid !== null && vivo(pid);
  if (agora !== buViva) log({ t: "taxa", coleta_bu_viva: agora, rps: agora ? rpsComBu : rps });
  buViva = agora;
  return agora;
}
checarBu();
const lento = new ClienteTse({ rps: rpsComBu, rajada: 2, log });
const rapido = new ClienteTse({ rps, log });
const cliente = (): ClienteTse => (buViva ? lento : rapido);

// ---------------------------------------------------------------- bancos
const db = abrirRdv(a.db);
const secoes = new Database(a.secoes, { readonly: true });
secoes.run("PRAGMA busy_timeout = 5000");
const escritor = new EscritorRdv(db);
db.query("INSERT OR REPLACE INTO meta (chave, valor) VALUES ('fonte', 'resultados.tse.jus.br/oficial/ele2026/arquivo-urna/3221')").run();
db.query("INSERT OR REPLACE INTO meta (chave, valor) VALUES ('pleito', '003221')").run();
db.query("INSERT OR REPLACE INTO meta (chave, valor) VALUES ('especificacao', 'scripts/secoes/rdv.asn1 sha256 282dcde0c7ba1f1bb128fe27443ad8d18f7490416c9546d033910a7ec557a465')").run();

const qSecoes = secoes.query<SecaoAlvo & { aux_json: string | null; bu_nome: string | null }, [string]>(
  "SELECT uf, mun, zona, secao, nsp, aux_json, bu_nome FROM secao WHERE uf = ? ORDER BY mun, zona, secao",
);
const qVotoBu = secoes.query<LinhaVotoBu, [string, string, number, number]>(
  "SELECT cargo, tipo, numero, votos FROM voto_secao WHERE uf = ? AND mun = ? AND zona = ? AND secao = ?",
);
const qAux = secoes.query<{ aux_json: string | null }, [string, string, number, number]>(
  "SELECT aux_json FROM secao WHERE uf = ? AND mun = ? AND zona = ? AND secao = ?",
);
const qTemBu = secoes.query<{ bu_nome: string | null }, [string, string, number, number]>(
  "SELECT bu_nome FROM secao WHERE uf = ? AND mun = ? AND zona = ? AND secao = ? AND bu_gz IS NOT NULL",
);

function feitas(uf: string): Set<string> {
  const cond = a["refazer-erros"] === true ? "status IN ('ok', 'sem_rdv', 'aux_404', 'agregada')" : "1";
  const s = new Set<string>();
  for (const r of db.query<{ k: string }, [string]>(`SELECT mun || '|' || zona || '|' || secao AS k FROM rdv WHERE uf = ? AND ${cond}`).all(uf)) s.add(r.k);
  return s;
}

/** Conferência contra o BU guardado; null quando o BU da seção ainda não está no banco. */
function conferir(r: ResultadoRdv): void {
  if (r.cargos === null) return;
  const tem = qTemBu.get(r.uf, r.mun, r.zona, r.secao);
  if (tem === null) {
    r.confere = null;
    r.divergencias = null;
    r.buNome = null;
    return;
  }
  const c = conferirComBu(r.cargos, qVotoBu.all(r.uf, r.mun, r.zona, r.secao));
  r.confere = c.confere;
  r.divergencias = c.divergencias;
  r.buNome = tem.bu_nome;
}

const msg = (e: unknown): string => (e instanceof Error ? `${e.name}: ${e.message}` : String(e)).slice(0, 300);

async function coletar(s: SecaoAlvo, auxGuardado: string | null): Promise<ResultadoRdv> {
  const r: ResultadoRdv = {
    ...s, status: "pendente", auxProprio: null, hash: null, rdvNome: null, bytes: null, sha256: null, gz: null, erro: null,
    requisicoes: 0, rdv: null, cargos: null, confere: null, divergencias: null, buNome: null, mesmoHashBu: null,
  };
  // a coleta de BUs pode ter guardado o aux depois que a fila foi montada
  let texto = auxGuardado ?? qAux.get(s.uf, s.mun, s.zona, s.secao)?.aux_json ?? null;
  if (texto === null) {
    const ar = await cliente().obter(urlAux2t(s));
    r.requisicoes += ar.requisicoes;
    if (ar.status === 404) {
      r.status = "aux_404";
      return r;
    }
    if (ar.corpo === null) {
      r.status = "erro";
      r.erro = `aux: ${ar.erro ?? "sem corpo"}`;
      return r;
    }
    texto = new TextDecoder().decode(ar.corpo);
    r.auxProprio = texto;
  }
  let esc;
  try {
    esc = escolherRdv(AuxSchema.parse(JSON.parse(texto)));
  } catch (e) {
    r.status = "erro";
    r.erro = `aux inválido: ${msg(e)}`;
    return r;
  }
  if (esc === null) {
    r.status = s.nsp !== null ? "agregada" : "sem_rdv";
    return r;
  }
  r.hash = esc.hash;
  r.rdvNome = esc.nome;
  r.mesmoHashBu = esc.temBu;
  const rr = await cliente().obter(`${dirSecao2t(s)}/${esc.hash}/${esc.nome}`);
  r.requisicoes += rr.requisicoes;
  if (rr.corpo === null) {
    r.status = rr.status === 404 ? "rdv_404" : "erro";
    r.erro = `rdv: ${rr.erro ?? "sem corpo"}`;
    return r;
  }
  r.bytes = rr.corpo.byteLength;
  r.sha256 = sha256(rr.corpo);
  r.gz = Bun.gzipSync(rr.corpo);
  try {
    r.rdv = decodificarRdv(rr.corpo);
    r.cargos = r.rdv.cargos;
    r.status = "ok";
  } catch (e) {
    r.status = "erro";
    r.erro = `rdv decodificação: ${msg(e)}`;
    return r;
  }
  conferir(r);
  return r;
}

// ---------------------------------------------------------------- progresso
let feitasRun = 0;
let restantes = 0;
const conta = { ok: 0, confere: 0, diverge: 0, sem_bu: 0, outros: 0 };
const t0 = Date.now();
const marcas: number[] = [];

function progresso(t: string): void {
  const agora = Date.now();
  while (marcas.length > 0 && (marcas[0] ?? agora) < agora - 60_000) marcas.shift();
  const sps = marcas.length / Math.min(60, Math.max(1, (agora - t0) / 1000));
  log({
    t, secoes_por_s: Math.round(sps * 10) / 10, feitas_run: feitasRun, restantes, eta_min: sps > 0 ? Math.round(restantes / sps / 60) : null,
    coleta_bu_viva: buViva, rps: buViva ? rpsComBu : rps, mb: Math.round((lento.bytes + rapido.bytes) / 1048576),
    http_lento: lento.contagem, http_rapido: rapido.contagem, conta,
  });
}

function reconferir(): void {
  const pend = db
    .query<{ uf: string; mun: string; zona: number; secao: number }, []>(
      `SELECT uf, mun, zona, secao FROM rdv WHERE status = 'ok' AND (confere IS NULL${a["reconferir-divergentes"] === true ? " OR confere = 0" : ""})`,
    )
    .all();
  let n = 0;
  for (const p of pend) {
    const tem = qTemBu.get(p.uf, p.mun, p.zona, p.secao);
    if (tem === null) continue;
    const cargos = escritor.cargosDe(p);
    const c = conferirComBu(cargos, qVotoBu.all(p.uf, p.mun, p.zona, p.secao));
    escritor.gravarConferencia(p, c.confere, c.divergencias, tem.bu_nome, new Date().toISOString());
    n += 1;
  }
  log({ t: "reconferencia", pendentes: pend.length, conferidas: n });
}

async function main(): Promise<void> {
  log({ t: "inicio", ufs, rps, rps_com_bu: rpsComBu, concorrencia, db: a.db, secoes: a.secoes, pid: process.pid });
  reconferir();
  if (a["so-conferir"] === true) return;
  const fila: Array<{ s: SecaoAlvo; aux: string | null }> = [];
  for (const uf of ufs) {
    const ja = feitas(uf);
    let n = 0;
    for (const x of qSecoes.all(uf)) {
      if (ja.has(`${x.mun}|${x.zona}|${x.secao}`)) continue;
      if (fila.length >= limite) break;
      fila.push({ s: { uf: x.uf, mun: x.mun, zona: x.zona, secao: x.secao, nsp: x.nsp }, aux: x.aux_json });
      n += 1;
    }
    log({ t: "fila_uf", uf, pendentes: n });
  }
  restantes = fila.length;
  log({ t: "fila", secoes: fila.length });

  const buffer: ResultadoRdv[] = [];
  const flush = (): void => {
    if (buffer.length > 0) escritor.gravar(buffer.splice(0), new Date().toISOString());
  };
  let idx = 0;
  const trabalhador = async (): Promise<void> => {
    while (!parar) {
      const item = fila[idx];
      idx += 1;
      if (item === undefined) return;
      const r = await coletar(item.s, item.aux);
      buffer.push(r);
      feitasRun += 1;
      restantes -= 1;
      marcas.push(Date.now());
      if (r.status === "ok") {
        conta.ok += 1;
        if (r.confere === true) conta.confere += 1;
        else if (r.confere === false) {
          conta.diverge += 1;
          log({ t: "diverge", uf: r.uf, mun: r.mun, zona: r.zona, secao: r.secao, divergencias: r.divergencias });
        } else conta.sem_bu += 1;
      } else conta.outros += 1;
      if (r.erro !== null) log({ t: "erro_secao", uf: r.uf, mun: r.mun, zona: r.zona, secao: r.secao, status: r.status, erro: r.erro });
    }
  };
  const tFlush = setInterval(flush, 500);
  const tProg = setInterval(() => progresso("progresso"), 15_000);
  const tBu = setInterval(checarBu, 20_000);
  await Promise.all(Array.from({ length: concorrencia }, () => trabalhador()));
  clearInterval(tFlush);
  clearInterval(tProg);
  clearInterval(tBu);
  flush();
  reconferir();
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
  secoes.close();
}

