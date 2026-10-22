// Uso: bun run scripts/referencia-1t.ts [--saida data/referencia_1t.json]
//
// Referência do 1º turno (04/10/2026) contra a qual o 2º turno (25/10/2026) é comparado ao vivo.
// Lê, somente leitura, data/apuracao.sqlite (arquivos `u` do TSE) e data/secoes_2026.sqlite
// (recebimento do hash do BU × último voto) e grava data/referencia_1t.json
// (ou .json.gz se passar de 15 MB). Idempotente: só `meta.gerado_em` muda entre execuções.
//
// Tempos: minutos após 17:00 de Brasília (UTC-3), com uma casa decimal; percentuais de 0 a 100.
// Curva: [min, pst, st, ts, comparecimento, abstencao, pa], ordenada pelo instante da totalização
// (RelogioArquivo, de src/server/indicadores/base.ts: o mesmo relógio do servidor do 2º turno),
// sem regressivos, sem pontos repetidos (mesmo pst, comparecimento e abstencao).
// `encerramento` do BU é hora local da urna: convertida a Brasília pelo fuso da UF.
import { Database } from "bun:sqlite";
import { existsSync, renameSync, statSync, unlinkSync, writeFileSync } from "node:fs";
import { gzipSync } from "node:zlib";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { RelogioArquivo } from "../src/server/indicadores/base.ts";

const RAIZ = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const DB_APURACAO = join(RAIZ, "data", "apuracao.sqlite");
const DB_SECOES = join(RAIZ, "data", "secoes_2026.sqlite");
const LIMITE_BYTES = 15 * 1024 * 1024;

const ELEICAO_PRES = 6257;
const ELEICAO_GOV = 6259;
const BASE_MS = Date.UTC(2026, 9, 4, 20, 0, 0); // 17:00 BRT de 04/10/2026
const BASE_BRT_NAIVE_MS = Date.UTC(2026, 9, 4, 17, 0, 0); // mesma hora lida como "relógio" sem fuso
const UFS_GOV_2T = ["AC", "AM", "DF", "ES", "RN", "TO"];
const REGIOES: Record<string, string[]> = {
  N: ["AC", "AM", "AP", "PA", "RO", "RR", "TO"],
  NE: ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"],
  CO: ["DF", "GO", "MS", "MT"],
  SE: ["ES", "MG", "RJ", "SP"],
  S: ["PR", "RS", "SC"],
};
// Deslocamento do relógio local da urna para Brasília, em minutos (AC UTC-5, AM/RO/RR/MT/MS UTC-4).
const LOCAL_PARA_BRT_MIN: Record<string, number> = {
  AC: 120,
  AM: 60,
  RO: 60,
  RR: 60,
  MT: 60,
  MS: 60,
};

type Ponto = [number, number, number, number, number, number, number];
interface Marcos {
  p50: number | null;
  p90: number | null;
  p99: number | null;
  p100: number | null;
  p50_hhmm: string | null;
  p90_hhmm: string | null;
  p99_hhmm: string | null;
  p100_hhmm: string | null;
  primeira_secao_min?: number | null;
  primeira_secao_hhmm?: string | null;
}
interface Final {
  te: number;
  comparecimento: number;
  abstencao: number;
  pa: number;
}
interface Contagens {
  [k: string]: number;
}

const ignorados: Contagens = {};
function ignora(motivo: string): void {
  ignorados[motivo] = (ignorados[motivo] ?? 0) + 1;
}

function r1(x: number): number {
  return Math.round(x * 10) / 10;
}
function r2(x: number): number {
  return Math.round(x * 100) / 100;
}
function r3(x: number): number {
  return Math.round(x * 1000) / 1000;
}
/** Minutos após 17:00 de Brasília de um instante em ms UTC. */
function minutosDe(ms: number): number {
  return r1((ms - BASE_MS) / 60000);
}
function hhmm(min: number | null): string | null {
  if (min === null) return null;
  const total = Math.round(17 * 60 + min);
  const dia = Math.floor(total / 1440);
  const resto = ((total % 1440) + 1440) % 1440;
  const h = String(Math.floor(resto / 60)).padStart(2, "0");
  const m = String(resto % 60).padStart(2, "0");
  return dia > 0 ? `${h}:${m}+${dia}d` : dia < 0 ? `${h}:${m}${dia}d` : `${h}:${m}`;
}
/**
 * Instante de cada versão pelo RelogioArquivo, versão a versão em ordem de id:
 * - contagens iguais às da versão anterior (arquivo regerado sem nova totalização) herdam o instante;
 * - cada carimbo `totalizado_em` é corrigido de fuso uma única vez, na primeira versão que o traz
 *   (AC +120 min, AM/RO/RR/MT/MS +60 min, pela regra de corrigirTotalizadoEm);
 * - o instante nunca passa da geração do arquivo nem volta antes do da versão anterior.
 * Corrige o AC regerado em hora local (p50 caía às 17:28), o PE uma hora adiantado entre 18:09 e
 * 20:15 e o exterior com carimbo do dia seguinte (curva inteira num só minuto).
 */
function instanteVersao(relogio: RelogioArquivo, r: SnapRow): number {
  return relogio.instante(`${r.st}|${r.tv}|${r.comparecimento}|${r.abstencao}`, r.totalizado_em, r.gerado_em, r.capturado_em);
}
function num(v: unknown): number | null {
  return typeof v === "number" && Number.isFinite(v) ? v : null;
}
/** Percentil por interpolação linear sobre vetor ordenado. */
function pct(ordenado: number[], p: number): number | null {
  const n = ordenado.length;
  if (n === 0) return null;
  const pos = (p / 100) * (n - 1);
  const lo = Math.floor(pos);
  const hi = Math.ceil(pos);
  const a = ordenado[lo] ?? 0;
  const b = ordenado[hi] ?? a;
  return r1(a + (b - a) * (pos - lo));
}
function ordenado(v: number[]): number[] {
  return Array.from(Float64Array.from(v).sort());
}

// ---------------------------------------------------------------------------------------------
// Parte A: apuracao.sqlite
// ---------------------------------------------------------------------------------------------

interface ArquivoRow {
  id: number;
  chave: string;
  nivel: string;
  uf: string | null;
  municipio_cd: string | null;
}
interface SnapRow {
  totalizado_em: string | null;
  gerado_em: string | null;
  capturado_em: string;
  tv: number | null;
  id: number;
  pst: number | null;
  st: number | null;
  ts: number | null;
  te: number | null;
  comparecimento: number | null;
  abstencao: number | null;
  pa: number | null;
}

const SQL_SNAPS = `
  SELECT s.totalizado_em AS totalizado_em, s.gerado_em AS gerado_em, s.capturado_em AS capturado_em, s.id AS id,
         t.pst AS pst, t.st AS st, t.ts AS ts, t.tv AS tv,
         t.te AS te, t.comparecimento AS comparecimento, t.abstencao AS abstencao, t.pa AS pa
  FROM snapshot s JOIN totais t ON t.snapshot_id = s.id
  WHERE s.arquivo_id = ? AND s.regressivo = 0
  ORDER BY s.id`;

interface Serie {
  curva: Ponto[];
  marcos: Marcos;
  final: Final | null;
}

function construirSerie(linhas: SnapRow[], comPrimeira: boolean, uf: string): Serie {
  const validas: { t: number; r: SnapRow }[] = [];
  const relogio = new RelogioArquivo(uf);
  for (const r of linhas) {
    if (!r.totalizado_em || num(r.pst) === null || num(r.st) === null || num(r.ts) === null) {
      ignora("snapshot_sem_totalizado_em_ou_totais");
      continue;
    }
    const t = minutosDe(instanteVersao(relogio, r));
    validas.push({ t, r });
  }
  validas.sort((a, b) => a.t - b.t || a.r.id - b.r.id);

  const curva: Ponto[] = [];
  let chaveAnt = "";
  for (const { t, r } of validas) {
    const ponto: Ponto = [
      t,
      r3(r.pst ?? 0),
      r.st ?? 0,
      r.ts ?? 0,
      r.comparecimento ?? 0,
      r.abstencao ?? 0,
      r2(r.pa ?? 0),
    ];
    const chave = `${ponto[1]}|${ponto[4]}|${ponto[5]}`;
    if (chave === chaveAnt) continue;
    chaveAnt = chave;
    curva.push(ponto);
  }

  const alcanca = (limite: number): number | null => {
    for (const p of curva) if (p[1] >= limite) return p[0];
    return null;
  };
  let p100: number | null = null;
  for (const p of curva) {
    if (p[3] > 0 && p[2] >= p[3]) {
      p100 = p[0];
      break;
    }
  }
  const p50 = alcanca(50);
  const p90 = alcanca(90);
  const p99 = alcanca(99);
  const marcos: Marcos = {
    p50,
    p90,
    p99,
    p100,
    p50_hhmm: hhmm(p50),
    p90_hhmm: hhmm(p90),
    p99_hhmm: hhmm(p99),
    p100_hhmm: hhmm(p100),
  };
  if (comPrimeira) {
    const prim = curva.find((p) => p[2] > 0);
    marcos.primeira_secao_min = prim ? prim[0] : null;
    marcos.primeira_secao_hhmm = prim ? hhmm(prim[0]) : null;
  }

  // Valor final: último snapshot (maior id) não regressivo com totais.
  let ultimo: SnapRow | null = null;
  for (const { r } of validas) if (ultimo === null || r.id > ultimo.id) ultimo = r;
  const final: Final | null = ultimo
    ? {
        te: ultimo.te ?? 0,
        comparecimento: ultimo.comparecimento ?? 0,
        abstencao: ultimo.abstencao ?? 0,
        pa: r2(ultimo.pa ?? 0),
      }
    : null;
  return { curva, marcos, final };
}

interface MunSaida {
  nm?: string;
  te: number;
  ts: number;
  st: number;
  comparecimento: number;
  abstencao: number;
  pa: number;
  fechou_min: number | null;
  apareceu_min: number | null;
}

function lerApuracao(db: Database) {
  const arquivos = db
    .query<ArquivoRow, [number, number]>(
      `SELECT id, chave, nivel, uf, municipio_cd FROM arquivo
       WHERE tipo = 'u' AND eleicao_cd = ? AND cargo_cd = ? AND nivel IN ('br','uf')`,
    )
    .all(ELEICAO_PRES, 1);
  const arquivosGov = db
    .query<ArquivoRow, [number, number]>(
      `SELECT id, chave, nivel, uf, municipio_cd FROM arquivo
       WHERE tipo = 'u' AND eleicao_cd = ? AND cargo_cd = ? AND nivel = 'uf'`,
    )
    .all(ELEICAO_GOV, 3);

  const stmtSnaps = db.query<SnapRow, [number]>(SQL_SNAPS);
  const br: { curva: Ponto[]; marcos: Marcos; final: Final | null }[] = [];
  const curvasUf: Record<string, Ponto[]> = {};
  const marcosUf: Record<string, Marcos> = {};
  const abstencaoUf: Record<string, Final> = {};
  const cobertura: Record<string, number> = {};

  for (const a of arquivos) {
    const serie = construirSerie(stmtSnaps.all(a.id), true, (a.uf ?? "").toUpperCase());
    if (a.nivel === "br") {
      br.push(serie);
    } else if (a.uf) {
      const uf = a.uf.toUpperCase();
      curvasUf[uf] = serie.curva;
      marcosUf[uf] = serie.marcos;
      if (serie.final) abstencaoUf[uf] = serie.final;
      cobertura[uf] = serie.curva.length;
    }
  }
  const serieBr = br[0];
  if (!serieBr) throw new Error("arquivo u:6257:1:br não encontrado");
  if (serieBr.final) abstencaoUf["BR"] = serieBr.final;

  const governador: Record<string, { curva: Ponto[]; marcos: Marcos; final: Final | null }> = {};
  for (const a of arquivosGov) {
    const uf = (a.uf ?? "").toUpperCase();
    if (!UFS_GOV_2T.includes(uf)) continue;
    governador[uf] = construirSerie(stmtSnaps.all(a.id), true, uf);
  }

  // Municípios (cargo 1): um passe ordenado por arquivo.
  const nomes = new Map<string, string>();
  for (const m of db.query<{ cd: string; nome: string | null }, []>("SELECT cd, nome FROM municipio").iterate()) {
    if (m.nome) nomes.set(m.cd, m.nome);
  }
  interface MunRow extends SnapRow {
    arquivo_id: number;
    uf: string | null;
    municipio_cd: string | null;
  }
  const iter = db
    .query<MunRow, [number, number]>(
      `SELECT a.id AS arquivo_id, a.uf AS uf, a.municipio_cd AS municipio_cd,
              s.totalizado_em AS totalizado_em, s.gerado_em AS gerado_em, s.capturado_em AS capturado_em, s.id AS id,
              t.pst AS pst, t.st AS st, t.ts AS ts, t.tv AS tv, t.te AS te,
              t.comparecimento AS comparecimento, t.abstencao AS abstencao, t.pa AS pa
       FROM arquivo a
       JOIN snapshot s ON s.arquivo_id = a.id AND s.regressivo = 0
       JOIN totais t ON t.snapshot_id = s.id
       WHERE a.tipo = 'u' AND a.nivel = 'mu' AND a.eleicao_cd = ? AND a.cargo_cd = ?
       ORDER BY a.id, s.id`,
    )
    .iterate(ELEICAO_PRES, 1);

  const municipios: Record<string, Record<string, MunSaida>> = {};
  let atual = -1;
  let acc: {
    uf: string;
    cd: string;
    final: MunRow | null;
    apareceu: number | null;
    fechou: number | null;
    relogio: RelogioArquivo;
  } | null = null;
  const fecha = (): void => {
    if (!acc || !acc.final) return;
    const f = acc.final;
    const uf = acc.uf.toUpperCase();
    const nm = nomes.get(acc.cd);
    const saida: MunSaida = {
      ...(nm ? { nm } : {}),
      te: f.te ?? 0,
      ts: f.ts ?? 0,
      st: f.st ?? 0,
      comparecimento: f.comparecimento ?? 0,
      abstencao: f.abstencao ?? 0,
      pa: r2(f.pa ?? 0),
      fechou_min: acc.fechou,
      apareceu_min: acc.apareceu,
    };
    (municipios[uf] ??= {})[acc.cd] = saida;
  };
  for (const r of iter) {
    if (r.arquivo_id !== atual) {
      fecha();
      atual = r.arquivo_id;
      acc = { uf: r.uf ?? "", cd: r.municipio_cd ?? "", final: null, apareceu: null, fechou: null, relogio: new RelogioArquivo((r.uf ?? "").toUpperCase()) };
    }
    if (!acc) continue;
    if (!acc.uf || !acc.cd) {
      ignora("municipio_sem_uf_ou_codigo");
      continue;
    }
    const st = num(r.st);
    const ts = num(r.ts);
    if (st === null || ts === null) {
      ignora("municipio_snapshot_sem_totais");
      continue;
    }
    if (acc.final === null || r.id > acc.final.id) acc.final = r;
    if (!r.totalizado_em) {
      ignora("municipio_snapshot_sem_totalizado_em");
      continue;
    }
    const t = minutosDe(instanteVersao(acc.relogio, r));
    if (st > 0 && (acc.apareceu === null || t < acc.apareceu)) acc.apareceu = t;
    if (ts > 0 && st === ts && (acc.fechou === null || t < acc.fechou)) acc.fechou = t;
  }
  fecha();

  return {
    br: serieBr,
    curvasUf,
    marcosUf,
    abstencaoUf,
    cobertura,
    governador,
    municipios,
  };
}

// ---------------------------------------------------------------------------------------------
// Parte B: secoes_2026.sqlite
// ---------------------------------------------------------------------------------------------

interface SecRow {
  uf: string;
  mun: string;
  dr_hr: string | null;
  encerramento: string | null;
  emissao: string | null;
}
interface Grupo {
  n: number;
  semRecebimento: number;
  encerr: number[];
  receb: number[];
  lagRec: number[];
  lagEmi: number[];
}
function novoGrupo(): Grupo {
  return { n: 0, semRecebimento: 0, encerr: [], receb: [], lagRec: [], lagEmi: [] };
}
const RE_DATA = /^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2}):(\d{2})/;
/** Lê 'aaaa-mm-dd hh:mm:ss' como relógio sem fuso (ms em escala UTC arbitrária). */
function relogio(s: string | null): number | null {
  if (!s) return null;
  const m = RE_DATA.exec(s);
  if (!m) return null;
  const ms = Date.UTC(Number(m[1]), Number(m[2]) - 1, Number(m[3]), Number(m[4]), Number(m[5]), Number(m[6]));
  return Number.isFinite(ms) ? ms : null;
}

function lerSecoes(db: Database) {
  const porUf = new Map<string, Grupo>();
  const porMun = new Map<string, Grupo>();
  const gBr = novoGrupo();
  const iter = db
    .query<SecRow, []>(
      `SELECT s.uf AS uf, s.mun AS mun, s.dr_hr AS dr_hr, b.encerramento AS encerramento, b.emissao AS emissao
       FROM secao s JOIN bu b ON b.uf = s.uf AND b.mun = s.mun AND b.zona = s.zona AND b.secao = s.secao`,
    )
    .iterate();
  let lagNegativo = 0;
  for (const r of iter) {
    const uf = r.uf.toUpperCase();
    const g = porUf.get(uf) ?? novoGrupo();
    porUf.set(uf, g);
    const chaveMun = `${uf}|${r.mun}`;
    const gm = porMun.get(chaveMun) ?? novoGrupo();
    porMun.set(chaveMun, gm);
    const noBr = uf !== "ZZ";
    g.n++;
    gm.n++;
    if (noBr) gBr.n++;

    const enc = relogio(r.encerramento);
    if (enc === null) {
      ignora(r.encerramento ? "encerramento_malformado" : "encerramento_nulo");
      continue;
    }
    const encBrt = enc + (LOCAL_PARA_BRT_MIN[uf] ?? 0) * 60000;
    const encMin = (encBrt - BASE_BRT_NAIVE_MS) / 60000;
    const emi = relogio(r.emissao);
    const rec = relogio(r.dr_hr);
    if (r.dr_hr === null) {
      g.semRecebimento++;
      gm.semRecebimento++;
      if (noBr) gBr.semRecebimento++;
      ignora("dr_hr_nulo");
    } else if (rec === null) {
      g.semRecebimento++;
      gm.semRecebimento++;
      if (noBr) gBr.semRecebimento++;
      ignora("dr_hr_malformado");
    }
    g.encerr.push(encMin);
    gm.encerr.push(encMin);
    if (noBr) gBr.encerr.push(encMin);
    if (rec !== null) {
      const recMin = (rec - BASE_BRT_NAIVE_MS) / 60000;
      const lag = recMin - encMin;
      if (lag < 0) lagNegativo++;
      g.receb.push(recMin);
      gm.receb.push(recMin);
      g.lagRec.push(lag);
      gm.lagRec.push(lag);
      if (noBr) {
        gBr.receb.push(recMin);
        gBr.lagRec.push(lag);
      }
    }
    if (emi !== null) {
      const lag = (emi - enc) / 60000;
      g.lagEmi.push(lag);
      gm.lagEmi.push(lag);
      if (noBr) gBr.lagEmi.push(lag);
    } else {
      ignora("emissao_nula_ou_malformada");
    }
  }
  if (lagNegativo > 0) ignorados["info_lag_encerr_recebimento_negativo"] = lagNegativo;

  const resumir = (g: Grupo) => {
    const lr = ordenado(g.lagRec);
    const le = ordenado(g.lagEmi);
    const rec = ordenado(g.receb);
    const enc = ordenado(g.encerr);
    return {
      lagP90: pct(lr, 90),
      resumo: {
        n: g.n,
        com_recebimento: g.receb.length,
        sem_recebimento: g.semRecebimento,
        encerramento_p50_hhmm: hhmm(pct(enc, 50)),
        encerramento_p90_hhmm: hhmm(pct(enc, 90)),
        lag_encerr_recebimento_min: { p50: pct(lr, 50), p90: pct(lr, 90), p99: pct(lr, 99) },
        lag_encerr_emissao_min: { p50: pct(le, 50), p90: pct(le, 90) },
        recebimento_p50_min: pct(rec, 50),
        recebimento_p90_min: pct(rec, 90),
        recebimento_p99_min: pct(rec, 99),
      },
    };
  };
  const uf: Record<string, unknown> = {};
  const lagP90Uf: [string, number][] = [];
  for (const [k, g] of [...porUf].sort(([a], [b]) => a.localeCompare(b))) {
    const { lagP90, resumo } = resumir(g);
    if (lagP90 !== null) lagP90Uf.push([k, lagP90]);
    uf[k] = resumo;
  }
  // Brasil = todas as seções exceto ZZ (exterior), mesmos campos de uma UF.
  const br = resumir(gBr).resumo;
  const municipio: Record<string, Record<string, unknown>> = {};
  for (const [k, g] of porMun) {
    if (g.receb.length < 20) continue;
    const [ufK, mun] = k.split("|") as [string, string];
    const lr = ordenado(g.lagRec);
    (municipio[ufK] ??= {})[mun] = {
      n: g.n,
      lag_encerr_recebimento_p50: pct(lr, 50),
      lag_p90: pct(lr, 90),
      recebimento_p90_min: pct(ordenado(g.receb), 90),
    };
  }
  return { uf, br, municipio, lagP90Uf };
}

// ---------------------------------------------------------------------------------------------
// Serialização legível: vetores e objetos-folha em uma linha
// ---------------------------------------------------------------------------------------------

function ehPrimitivo(v: unknown): boolean {
  return v === null || typeof v === "number" || typeof v === "string" || typeof v === "boolean";
}
function bonito(v: unknown, nivel: number): string {
  const pad = "  ".repeat(nivel);
  const pad1 = "  ".repeat(nivel + 1);
  if (ehPrimitivo(v)) return JSON.stringify(v);
  if (Array.isArray(v)) {
    if (v.every((x) => ehPrimitivo(x) || (Array.isArray(x) && x.every(ehPrimitivo)))) {
      if (v.every(ehPrimitivo)) return JSON.stringify(v);
      return `[\n${v.map((x) => pad1 + JSON.stringify(x)).join(",\n")}\n${pad}]`;
    }
    return `[\n${v.map((x) => pad1 + bonito(x, nivel + 1)).join(",\n")}\n${pad}]`;
  }
  const o = v as Record<string, unknown>;
  const ks = Object.keys(o);
  if (ks.length === 0) return "{}";
  if (ks.every((k) => ehPrimitivo(o[k]))) return JSON.stringify(o);
  return `{\n${ks.map((k) => `${pad1}${JSON.stringify(k)}: ${bonito(o[k], nivel + 1)}`).join(",\n")}\n${pad}}`;
}

// ---------------------------------------------------------------------------------------------

function main(): void {
  const argv = process.argv.slice(2);
  const i = argv.indexOf("--saida");
  const saidaArg = i >= 0 ? argv[i + 1] : undefined;
  const saida = saidaArg ? resolve(saidaArg) : join(RAIZ, "data", "referencia_1t.json");
  for (const p of [DB_APURACAO, DB_SECOES]) {
    if (!existsSync(p)) throw new Error(`fonte ausente: ${p}`);
  }
  const t0 = Date.now();
  const dbA = new Database(DB_APURACAO, { readonly: true });
  const dbS = new Database(DB_SECOES, { readonly: true });
  console.log("lendo apuracao.sqlite...");
  const a = lerApuracao(dbA);
  console.log(`  ok em ${((Date.now() - t0) / 1000).toFixed(1)} s`);
  console.log("lendo secoes_2026.sqlite...");
  const s = lerSecoes(dbS);
  console.log(`  ok em ${((Date.now() - t0) / 1000).toFixed(1)} s`);
  dbA.close();
  dbS.close();

  const marcosBr = a.br.marcos;
  const governador: Record<string, unknown> = {};
  for (const [uf, serie] of Object.entries(a.governador)) {
    governador[uf] = { curva: serie.curva, marcos: serie.marcos, final: serie.final };
  }
  const saidaObj = {
    meta: {
      gerado_em: new Date().toISOString(),
      fontes: {
        apuracao: { arquivo: "data/apuracao.sqlite", bytes: statSync(DB_APURACAO).size },
        secoes: { arquivo: "data/secoes_2026.sqlite", bytes: statSync(DB_SECOES).size },
      },
      turno: 1,
      eleicoes: { presidente: ELEICAO_PRES, governador: ELEICAO_GOV },
      regioes: REGIOES,
      convencoes: {
        fuso_totalizado_em:
          "totalizado_em de AC (+120 min), AM/RO/RR/MT/MS (+60 min) vem em hora local rotulada como Brasília; corrigido quando gerado_em - totalizado_em fica a até 10 min do deslocamento, decidido uma única vez por carimbo, na primeira versão que o traz",
        relogio:
          "instante de cada versão pelo RelogioArquivo (src/server/indicadores/base.ts), em ordem de id: versão regerada com as mesmas contagens (st, tv, comparecimento, abstencao) herda o instante da anterior; contagens novas usam totalizado_em com correção única por carimbo; o instante nunca passa de gerado_em nem fica antes do instante da versão anterior",
        tempo: "minutos após 17:00 de Brasília em 04/10/2026 (UTC-3); negativos = antes das 17:00",
        curva: "[min, pst, st, ts, comparecimento, abstencao, pa]; um ponto por estado distinto (pst, comparecimento, abstencao)",
        marcos: "primeiro ponto com pst >= 50/90/99; p100 = st >= ts; primeira_secao_min = primeiro st > 0",
        secoes_lag: "recebimento = secao.dr_hr (Brasília); encerramento do BU convertido de hora local da urna; lag = recebimento - encerramento",
        municipio_lag: "somente municípios com >= 20 seções com recebimento",
      },
      ignorados,
    },
    curvas: { br: a.br.curva, uf: a.curvasUf },
    marcos: { br: marcosBr, uf: a.marcosUf },
    municipios: a.municipios,
    abstencao_uf: a.abstencaoUf,
    secoes_lag: { uf: s.uf, br: s.br, municipio: s.municipio },
    governador_1t: governador,
  };

  const texto = bonito(saidaObj, 0) + "\n";
  const plano = saida;
  const gz = `${saida}.gz`;
  let final: string;
  if (Buffer.byteLength(texto) > LIMITE_BYTES) {
    const tmp = `${gz}.tmp`;
    writeFileSync(tmp, gzipSync(Buffer.from(texto), { level: 9 }));
    renameSync(tmp, gz);
    if (existsSync(plano)) unlinkSync(plano);
    final = gz;
  } else {
    const tmp = `${plano}.tmp`;
    writeFileSync(tmp, texto);
    renameSync(tmp, plano);
    if (existsSync(gz)) unlinkSync(gz);
    final = plano;
  }

  const tamanho = statSync(final).size;
  console.log(`\nsaída: ${final} (${(tamanho / 1048576).toFixed(2)} MB, ${final.endsWith(".gz") ? "gzip" : "json"})`);
  console.log(
    `BR: p50 ${marcosBr.p50} min (${marcosBr.p50_hhmm}), p90 ${marcosBr.p90} (${marcosBr.p90_hhmm}), p99 ${marcosBr.p99} (${marcosBr.p99_hhmm}), p100 ${marcosBr.p100} (${marcosBr.p100_hhmm})`,
  );
  const lentas = Object.entries(a.marcosUf)
    .filter(([, m]) => m.p99 !== null)
    .sort(([, x], [, y]) => (y.p99 ?? 0) - (x.p99 ?? 0))
    .slice(0, 5);
  console.log("5 UFs mais lentas (p99):", lentas.map(([k, m]) => `${k} ${m.p99} (${m.p99_hhmm})`).join(", "));
  const semP99 = Object.entries(a.marcosUf).filter(([, m]) => m.p99 === null).map(([k]) => k);
  if (semP99.length) console.log("UFs que nunca chegaram a 99%:", semP99.join(", "));
  const lag = [...s.lagP90Uf].sort((x, y) => y[1] - x[1]).slice(0, 5);
  console.log("5 UFs com maior lag p90 (encerramento→recebimento, min):", lag.map(([k, v]) => `${k} ${v}`).join(", "));
  const nMun = Object.values(a.municipios).reduce((acc, m) => acc + Object.keys(m).length, 0);
  const nMunLag = Object.values(s.municipio).reduce((acc, m) => acc + Object.keys(m).length, 0);
  console.log(`municípios: ${nMun}; com lag (n>=20): ${nMunLag}; governador: ${Object.keys(a.governador).join(",")}`);
  console.log("ignorados:", JSON.stringify(ignorados));
  console.log(`tempo total ${((Date.now() - t0) / 1000).toFixed(1)} s`);
}

main();
