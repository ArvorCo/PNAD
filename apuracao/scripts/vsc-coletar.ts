// Coleta retomável dos arquivos de assinatura da seção (`-vota.vsc` da urna, `-sa.vsc` do sistema
// de apuração) do 1º e do 2º turno de 2026, num banco próprio (data/vsc_2t_2026.sqlite).
//
//   bun run scripts/vsc-coletar.ts --ufs ac               # 2º turno, só o Acre
//   bun run scripts/vsc-coletar.ts                        # 2º turno, todas as UFs
//   bun run scripts/vsc-coletar.ts --turno 1              # 1º turno (aux de data/secoes_2026.sqlite)
//   opções: --rps 60 (teto 70) --rps-com-logs 20 --concorrencia 24 --refazer-erros --limite N
//           --guardar-vsc (guarda o arquivo inteiro, ~62 KB por seção) --sem-assinatura
//           --db data/vsc_2t_2026.sqlite --secoes <banco dos BUs do turno>
//
// O aux.json e o BU vêm do banco dos BUs do turno, aberto SÓ PARA LEITURA. Seção ainda sem aux
// lá: o aux é pedido ao TSE e guardado aqui. Taxa: enquanto a coleta dos logs
// (apuracao-2026-logs-coletar.py) estiver viva, --rps-com-logs (20/s); depois, --rps (60/s).
//
// De cada .vsc o banco guarda: SHA-256 do arquivo, o certificado de hardware da urna (DER,
// série, emissor, titular, validade, SHA-256, algoritmo), a cadeia até as ACs arquivadas em
// totalizacao/src/qrbu/ac (AC URNA, AC UE2020, AC UE2022), a autoassinatura de hardware e a do
// BU conferidas com a chave do certificado, e a lista de arquivos assinados com o SHA-512 de cada
// um. O BU guardado no banco dos BUs é conferido contra a sua entrada no .vsc.
import { Database } from "bun:sqlite";
import { appendFileSync, existsSync, mkdirSync, readFileSync, unlinkSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { parseArgs } from "node:util";
import { ClienteTse } from "./secoes/http.ts";
import { ORDEM_UF } from "./secoes/ordem.ts";
import { AuxSchema, sha256 } from "./secoes/secao.ts";
import { abrirVsc, dirSecaoTurno, escolherVsc, EscritorVsc, PLEITO_TURNO, urlAuxTurno } from "./secoes/vsc-banco.ts";
import type { ResultadoVsc, SecaoAlvoVsc } from "./secoes/vsc-banco.ts";
import { conferirArquivo, decodificarVsc, resumirVsc } from "../src/secoes2t/vsc-decode.ts";

const RAIZ = join(import.meta.dir, "..");
const RPS_MAX = 70;

const { values: a } = parseArgs({
  options: {
    turno: { type: "string", default: "2" },
    ufs: { type: "string" },
    rps: { type: "string", default: "60" },
    "rps-com-logs": { type: "string", default: "20" },
    concorrencia: { type: "string", default: "24" },
    "refazer-erros": { type: "boolean", default: false },
    "guardar-vsc": { type: "boolean", default: false },
    "sem-assinatura": { type: "boolean", default: false },
    limite: { type: "string" },
    db: { type: "string", default: join(RAIZ, "data", "vsc_2t_2026.sqlite") },
    secoes: { type: "string" },
    "padrao-logs": { type: "string", default: "apuracao-2026-logs-coletar" },
  },
  strict: true,
});

const turno = a.turno === "1" ? 1 : a.turno === "2" ? 2 : null;
if (turno === null) throw new Error(`--turno deve ser 1 ou 2: ${a.turno}`);
const secoesPath = a.secoes ?? join(RAIZ, "data", turno === 2 ? "secoes_2t_2026.sqlite" : "secoes_2026.sqlite");
const ufs = a.ufs === undefined ? [...ORDEM_UF] : ORDEM_UF.filter((u) => (a.ufs ?? "").toLowerCase().split(",").includes(u));
if (ufs.length === 0) throw new Error(`--ufs sem UF válida: ${a.ufs}`);
const rps = Math.min(RPS_MAX, Math.max(1, Number(a.rps)));
const rpsComLogs = Math.min(rps, Math.max(1, Number(a["rps-com-logs"])));
const concorrencia = Math.max(1, Math.min(64, Number.parseInt(a.concorrencia ?? "24", 10)));
const limite = a.limite === undefined ? Number.POSITIVE_INFINITY : Number.parseInt(a.limite, 10);
const pleito = PLEITO_TURNO[turno];

const hoje = new Date();
const dia = `${hoje.getFullYear()}${String(hoje.getMonth() + 1).padStart(2, "0")}${String(hoje.getDate()).padStart(2, "0")}`;
const DIR_LOG = join(RAIZ, "data", "logs");
const ARQ_LOG = join(DIR_LOG, `vsc-p00${pleito}-${dia}.log`);
const PIDFILE = join(RAIZ, "data", `vsc-p00${pleito}.pid`);
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

const outro = existsSync(PIDFILE) ? Number.parseInt(readFileSync(PIDFILE, "utf8"), 10) : null;
if (outro !== null && Number.isFinite(outro) && outro !== process.pid && vivo(outro)) {
  console.error(`outra coleta de .vsc do turno ${turno} em andamento (pid ${outro}, ${PIDFILE})`);
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

// ---------------------------------------------------------------- taxa compartilhada com a coleta dos logs
let logsVivos = false;
let pidsLogs: number[] = [];
function checarLogs(): boolean {
  const r = Bun.spawnSync(["pgrep", "-f", a["padrao-logs"]]);
  const pids = new TextDecoder().decode(r.stdout).split(/\s+/).map(Number).filter((n) => Number.isFinite(n) && n > 0 && n !== process.pid);
  const agora = pids.length > 0;
  if (agora !== logsVivos) log({ t: "taxa", coleta_logs_viva: agora, pids, rps: agora ? rpsComLogs : rps });
  logsVivos = agora;
  pidsLogs = pids;
  return agora;
}
checarLogs();
const lento = new ClienteTse({ rps: rpsComLogs, rajada: 2, log });
const rapido = new ClienteTse({ rps, log });
const cliente = (): ClienteTse => (logsVivos ? lento : rapido);

// ---------------------------------------------------------------- bancos
const db = abrirVsc(a.db);
const secoes = new Database(secoesPath, { readonly: true });
secoes.run("PRAGMA busy_timeout = 5000");
const escritor = new EscritorVsc(db);
const meta = db.query("INSERT OR REPLACE INTO meta (chave, valor) VALUES (?, ?)");
meta.run(`fonte_t${turno}`, `resultados.tse.jus.br/oficial/ele2026/arquivo-urna/${pleito}`);
meta.run("acs", "totalizacao/src/qrbu/ac (AC URNA, AC UE2020, AC UE2022); cópias em data/originals/tse_qrbu_2026/ac_certs");

interface LinhaSecao {
  uf: string;
  mun: string;
  zona: number;
  secao: number;
  nsp: number | null;
  aux_json: string | null;
  hash: string | null;
  status_aux: string | null;
}
const qSecoes = secoes.query<LinhaSecao, [string]>("SELECT uf, mun, zona, secao, nsp, aux_json, hash, status_aux FROM secao WHERE uf = ? ORDER BY mun, zona, secao");
const qAux = secoes.query<{ aux_json: string | null; hash: string | null }, [string, string, number, number]>(
  "SELECT aux_json, hash FROM secao WHERE uf = ? AND mun = ? AND zona = ? AND secao = ?",
);
const qBu = secoes.query<{ bu_nome: string | null; bu_gz: Uint8Array<ArrayBuffer> | null }, [string, string, number, number]>(
  "SELECT bu_nome, bu_gz FROM secao WHERE uf = ? AND mun = ? AND zona = ? AND secao = ? AND bu_gz IS NOT NULL",
);

function feitas(uf: string): Set<string> {
  const cond = a["refazer-erros"] === true ? "status IN ('ok', 'aux_404', 'agregada')" : "1";
  const s = new Set<string>();
  const q = db.query<{ k: string }, [number, string]>(`SELECT mun || '|' || zona || '|' || secao AS k FROM vsc WHERE turno = ? AND uf = ? AND ${cond}`);
  for (const r of q.all(turno ?? 2, uf)) s.add(r.k);
  return s;
}

const msg = (e: unknown): string => (e instanceof Error ? `${e.name}: ${e.message}` : String(e)).slice(0, 300);

async function coletar(s: SecaoAlvoVsc, auxGuardado: string | null, hashBu: string | null, statusAux: string | null): Promise<ResultadoVsc> {
  const r: ResultadoVsc = {
    ...s, status: "pendente", auxProprio: null, escolha: null, mesmoHashBu: null, bytes: null, sha256: null, gz: null, resumo: null,
    buNome: null, buConfere: null, erro: null, requisicoes: 0,
  };
  // seção agregada: a coleta dos BUs já recebeu 404 no aux dela; o .vsc fica na seção principal
  if (auxGuardado === null && statusAux === "aux_404" && s.nsp !== null) {
    r.status = "agregada";
    return r;
  }
  let texto = auxGuardado;
  let hash = hashBu;
  if (texto === null) {
    const g = qAux.get(s.uf, s.mun, s.zona, s.secao);
    texto = g?.aux_json ?? null;
    hash = g?.hash ?? hash;
  }
  if (texto === null) {
    const ar = await cliente().obter(urlAuxTurno(s));
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
  try {
    r.escolha = escolherVsc(AuxSchema.parse(JSON.parse(texto)), hash);
  } catch (e) {
    r.status = "erro";
    r.erro = `aux inválido: ${msg(e)}`;
    return r;
  }
  if (r.escolha === null && r.auxProprio === null) {
    // aux guardado pela coleta dos BUs antes de o .vsc ser publicado: pede o aux atual uma vez
    const ar = await cliente().obter(urlAuxTurno(s));
    r.requisicoes += ar.requisicoes;
    if (ar.corpo !== null) {
      r.auxProprio = new TextDecoder().decode(ar.corpo);
      try {
        r.escolha = escolherVsc(AuxSchema.parse(JSON.parse(r.auxProprio)), hash);
      } catch (e) {
        r.status = "erro";
        r.erro = `aux atual inválido: ${msg(e)}`;
        return r;
      }
    }
  }
  const esc = r.escolha;
  if (esc === null) {
    r.status = s.nsp !== null ? "agregada" : "sem_vsc";
    return r;
  }
  r.mesmoHashBu = hash === null ? null : esc.hash === hash;
  const rr = await cliente().obter(`${dirSecaoTurno(s)}/${esc.hash}/${esc.nome}`);
  r.requisicoes += rr.requisicoes;
  if (rr.corpo === null) {
    r.status = rr.status === 404 ? "vsc_404" : "erro";
    r.erro = `vsc: ${rr.erro ?? "sem corpo"}`;
    return r;
  }
  r.bytes = rr.corpo.byteLength;
  r.sha256 = sha256(rr.corpo);
  if (a["guardar-vsc"] === true) r.gz = Bun.gzipSync(rr.corpo);
  try {
    r.resumo = resumirVsc(decodificarVsc(rr.corpo), { verificarAssinatura: a["sem-assinatura"] !== true });
    r.status = "ok";
  } catch (e) {
    r.status = "erro";
    r.erro = `vsc decodificação: ${msg(e)}`;
    return r;
  }
  if (r.mesmoHashBu === true) {
    const bu = qBu.get(s.uf, s.mun, s.zona, s.secao);
    if (bu !== null && bu.bu_gz !== null && bu.bu_nome !== null) {
      r.buNome = bu.bu_nome;
      r.buConfere = conferirArquivo(r.resumo.arquivos, bu.bu_nome, Bun.gunzipSync(bu.bu_gz));
    }
  }
  return r;
}

// ---------------------------------------------------------------- progresso
let feitasRun = 0;
let restantes = 0;
const conta = { ok: 0, cadeia_ok: 0, assinatura_ok: 0, bu_confere: 0, bu_diverge: 0, alertas: 0, outros: 0 };
const t0 = Date.now();
const marcas: number[] = [];

function progresso(t: string): void {
  const agora = Date.now();
  while (marcas.length > 0 && (marcas[0] ?? agora) < agora - 60_000) marcas.shift();
  const sps = marcas.length / Math.min(60, Math.max(1, (agora - t0) / 1000));
  log({
    t, turno, secoes_por_s: Math.round(sps * 10) / 10, feitas_run: feitasRun, restantes, eta_min: sps > 0 ? Math.round(restantes / sps / 60) : null,
    coleta_logs_viva: logsVivos, pids_logs: pidsLogs, rps: logsVivos ? rpsComLogs : rps, mb: Math.round((lento.bytes + rapido.bytes) / 1048576),
    http_lento: lento.contagem, http_rapido: rapido.contagem, conta,
  });
}

/** Incoerências internas do .vsc que valem uma linha no log da coleta. */
function alertas(r: ResultadoVsc): string[] {
  const v = r.resumo;
  if (v === null) return [];
  const x: string[] = [];
  if (!v.swResumoConfere) x.push("resumo_sw");
  if (!v.hwResumoConfere) x.push("resumo_hw");
  if (!v.listasConferem) x.push("listas_sw_hw");
  if (v.certificado === null) x.push(`certificado: ${v.erroCertificado ?? "ausente"}`);
  else if (!v.certificado.cadeiaValida) x.push(`cadeia: ${v.certificado.motivoCadeia ?? ""}`);
  if (v.cnConfereUsuario === false) x.push("cn_diferente_do_usuario_hw");
  if (v.hwAssinaturaValida === false) x.push("assinatura_hw");
  if (v.hwAssinaturaBuValida === false) x.push("assinatura_bu");
  if (r.buConfere === false) x.push("bu_diferente_do_vsc");
  return x;
}

async function main(): Promise<void> {
  log({ t: "inicio", turno, ufs, rps, rps_com_logs: rpsComLogs, concorrencia, db: a.db, secoes: secoesPath, pid: process.pid });
  const fila: Array<{ s: SecaoAlvoVsc; aux: string | null; hash: string | null; statusAux: string | null }> = [];
  for (const uf of ufs) {
    const ja = feitas(uf);
    let n = 0;
    for (const x of qSecoes.all(uf)) {
      if (ja.has(`${x.mun}|${x.zona}|${x.secao}`)) continue;
      if (fila.length >= limite) break;
      fila.push({ s: { turno: turno ?? 2, uf: x.uf, mun: x.mun, zona: x.zona, secao: x.secao, nsp: x.nsp }, aux: x.aux_json, hash: x.hash, statusAux: x.status_aux });
      n += 1;
    }
    log({ t: "fila_uf", uf, pendentes: n });
  }
  restantes = fila.length;
  log({ t: "fila", secoes: fila.length });

  const buffer: ResultadoVsc[] = [];
  const flush = (): void => {
    if (buffer.length > 0) escritor.gravar(buffer.splice(0), new Date().toISOString());
  };
  let idx = 0;
  const trabalhador = async (): Promise<void> => {
    while (!parar) {
      const item = fila[idx];
      idx += 1;
      if (item === undefined) return;
      const r = await coletar(item.s, item.aux, item.hash, item.statusAux);
      buffer.push(r);
      feitasRun += 1;
      restantes -= 1;
      marcas.push(Date.now());
      if (r.status === "ok") {
        conta.ok += 1;
        if (r.resumo?.certificado?.cadeiaValida === true) conta.cadeia_ok += 1;
        if (r.resumo?.hwAssinaturaValida === true) conta.assinatura_ok += 1;
        if (r.buConfere === true) conta.bu_confere += 1;
        if (r.buConfere === false) conta.bu_diverge += 1;
        const al = alertas(r);
        if (al.length > 0) {
          conta.alertas += 1;
          log({ t: "alerta", uf: r.uf, mun: r.mun, zona: r.zona, secao: r.secao, alertas: al });
        }
      } else conta.outros += 1;
      if (r.erro !== null) log({ t: "erro_secao", uf: r.uf, mun: r.mun, zona: r.zona, secao: r.secao, status: r.status, erro: r.erro });
    }
  };
  const tFlush = setInterval(flush, 500);
  const tProg = setInterval(() => progresso("progresso"), 15_000);
  const tLogs = setInterval(checarLogs, 20_000);
  await Promise.all(Array.from({ length: concorrencia }, () => trabalhador()));
  clearInterval(tFlush);
  clearInterval(tProg);
  clearInterval(tLogs);
  flush();
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
