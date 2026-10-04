// Banco de ensaio do telão: apuração sintética e determinística sobre as fixtures reais do TSE.
// Presidente em br e nas 27 UFs, governador e senado de SP, os 645 municípios de SP e as
// 57 zonas da capital, em passos de 6 minutos a partir das 17h de 04/10/2026.
//
//   bun run scripts/semear-ensaio.ts                  # recria data/ensaio.sqlite com 10 passos
//   bun run scripts/semear-ensaio.ts --passos 6       # outro número de passos
//   bun run scripts/semear-ensaio.ts --mais 1         # acrescenta 1 passo ao banco existente (teste do SSE)
//   bun run scripts/semear-ensaio.ts --db outro.sqlite
//
// Os números são inventados (lean fixo por UF, deriva para forçar viradas em MG e PR);
// nomes de senado são de ensaio. Nunca usar este banco como dado.
import { existsSync, mkdirSync, rmSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { abrirEscrita, fecharEscrita } from "../src/db/abrir.ts";
import { lerMeta } from "../src/db/leitura.ts";
import { Sequenciador } from "../src/replay/sequenciador.ts";
import { chave, keyAb, keyCm, keyEleC, keyU, registroDeArquivos } from "../src/tse/urls.ts";
import { json, lerCm } from "../tests/helpers.ts";
import { brt } from "../tests/server-helpers.ts";

type Obj = Record<string, unknown>;
const obj = (v: unknown): Obj => v as Obj;
const arr = (v: unknown): Obj[] => (Array.isArray(v) ? (v as Obj[]) : []);
const virgula = (n: number, casas = 2): string => n.toFixed(casas).replace(".", ",");

function arg(nome: string): string | undefined {
  const i = process.argv.indexOf(`--${nome}`);
  return i >= 0 ? process.argv[i + 1] : undefined;
}

const RAIZ = resolve(import.meta.dir, "..");
const DB = resolve(RAIZ, arg("db") ?? "data/ensaio.sqlite");
const MAIS = arg("mais");
const PASSOS = Number(arg("passos") ?? 10);
const T0 = Date.parse("2026-10-04T20:00:00.000Z");
const PASSO_MS = 6 * 60_000;
const iso = (ms: number): string => new Date(ms).toISOString();

/** Pseudoaleatório determinístico em [0, 1) a partir de um texto. */
function hash01(s: string): number {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 16777619);
  return ((h >>> 0) % 100_000) / 100_000;
}

/** Fração de seções totalizadas no passo `k` (velocidade própria por unidade). */
function fracao(id: string, k: number, total: number): number {
  const vel = 0.6 + hash01(`vel:${id}`) * 0.8;
  const atraso = hash01(`atr:${id}`) * 1.5;
  return Math.max(0, Math.min(1, ((k - atraso) / total) * vel));
}

// Lean do presidente por UF: fração de Lula entre Lula e Flávio no fim; deriva negativa = Lula
// começa à frente e perde (virada). Terceiras vias somam ~12%.
const LEAN: Readonly<Record<string, number>> = {
  ac: 0.32, al: 0.62, am: 0.5, ap: 0.48, ba: 0.7, ce: 0.68, df: 0.4, es: 0.42, go: 0.36, ma: 0.7, mg: 0.48, ms: 0.38,
  mt: 0.33, pa: 0.56, pb: 0.66, pe: 0.68, pi: 0.74, pr: 0.4, rj: 0.44, rn: 0.64, ro: 0.3, rr: 0.28, rs: 0.42, sc: 0.32,
  se: 0.66, sp: 0.46, to: 0.52, zz: 0.45,
};
const DERIVA: Readonly<Record<string, number>> = { mg: 0.12, pr: -0.25, sp: 0.06 };

function votosPres(id: string, lean: number, deriva: number, vv: number, f: number): Record<string, number> {
  const p = Math.max(0.05, Math.min(0.95, lean + deriva * (0.5 - f)));
  const terceira = 0.12;
  const resto = vv * (1 - terceira);
  const r = hash01(`t:${id}`);
  return {
    13: Math.round(resto * p),
    22: Math.round(resto * (1 - p)),
    55: Math.round(vv * terceira * (0.3 + r * 0.1)),
    30: Math.round(vv * terceira * 0.25),
    14: Math.round(vv * terceira * 0.2),
    70: Math.round(vv * terceira * 0.1),
    80: Math.round(vv * terceira * 0.03),
  };
}

interface GerarU {
  ts?: number;
  te?: number;
  st: number;
  votos: Record<string, number>;
  idg: number;
  ger: number;
  tot: number;
  tf: boolean;
  cdabr?: string;
  mexer?: (d: Obj) => void;
}

/** Fixture -u com cabeçalho, seções, eleitorado e votos trocados (mesma lógica de tests/server-helpers.ts). */
function gerarU(nome: string, g: GerarU): Uint8Array<ArrayBuffer> {
  const d = obj(structuredClone(json(nome)));
  g.mexer?.(d);
  const s = obj(d.s);
  const e = obj(d.e);
  const vt = obj(d.v);
  if (g.ts !== undefined) Object.assign(s, { ts: String(g.ts) });
  if (g.te !== undefined) Object.assign(e, { te: String(g.te) });
  const ts = Number(s.ts);
  const st = Math.min(ts, g.st);
  const vv = Object.values(g.votos).reduce((a, b) => a + b, 0);
  const brancos = Math.round(vv * 0.025);
  const nulos = Math.round(vv * 0.035);
  const tv = vv + brancos + nulos;
  const gr = brt(g.ger);
  const tt = brt(g.tot);
  Object.assign(d, { dg: gr.d, hg: gr.h, idg: String(g.idg), tf: g.tf ? "s" : "n", dt: tt.d, ht: tt.h });
  if (g.cdabr !== undefined) d.cdabr = g.cdabr;
  const pst = ts > 0 ? (st / ts) * 100 : 0;
  Object.assign(s, { st: String(st), snt: String(ts - st), pst: virgula(pst), pstn: virgula(pst, 4) });
  const te = Number(e.te);
  const pc = te > 0 ? (tv / te) * 100 : 0;
  Object.assign(e, { c: String(tv), pc: virgula(pc), a: String(Math.max(0, Math.round(te * (st / Math.max(1, ts))) - tv)) });
  Object.assign(vt, {
    tv: String(tv), vv: String(vv), vvc: String(vv), vnom: String(vv), vb: String(brancos), vn: String(nulos), tvn: String(nulos),
    pvb: virgula(tv > 0 ? (brancos / tv) * 100 : 0), pvn: virgula(tv > 0 ? (nulos / tv) * 100 : 0),
  });
  for (const cargo of arr(d.carg)) {
    for (const agr of arr(cargo.agr)) {
      for (const par of arr(agr.par)) {
        let soma = 0;
        for (const c of arr(par.cand)) {
          const vap = g.votos[String(c.n)] ?? 0;
          soma += vap;
          const pct = vv > 0 ? (vap / vv) * 100 : 0;
          Object.assign(c, { vap: String(vap), pvap: virgula(pct), pvapn: virgula(pct, 4) });
        }
        par.tvtn = String(soma);
      }
    }
  }
  return new TextEncoder().encode(JSON.stringify(d));
}

interface EntradaAb {
  st: number;
  tot: number;
  munf?: number;
  munpt?: number;
}

function gerarAb(nome: string, idg: number, ger: number, entradas: ReadonlyMap<string, EntradaAb>): Uint8Array<ArrayBuffer> {
  const d = obj(structuredClone(json(nome)));
  const g = brt(ger);
  Object.assign(d, { dg: g.d, hg: g.h, idg: String(idg) });
  for (const a of arr(d.abr)) {
    const m = entradas.get(String(a.cdabr));
    if (!m) continue;
    const s = obj(a.s);
    const ts = Number(s.ts);
    const st = Math.min(ts, m.st);
    const pst = ts > 0 ? (st / ts) * 100 : 0;
    Object.assign(s, { st: String(st), snt: String(ts - st), pst: virgula(pst), pstn: virgula(pst, 4) });
    if (st > 0) {
      const t = brt(m.tot);
      Object.assign(a, { dt: t.d, ht: t.h, and: st === ts ? "f" : "p" });
    }
    if (m.munf !== undefined && m.munpt !== undefined) {
      const total = Number(a.munnr ?? 0) + Number(a.munpt ?? 0) + Number(a.munf ?? 0);
      Object.assign(a, { munf: String(m.munf), munpt: String(m.munpt), munnr: String(Math.max(0, total - m.munf - m.munpt)) });
    }
  }
  return new TextEncoder().encode(JSON.stringify(d));
}

// ---------- universo ----------
const cm57 = lerCm("mun-e006257-cm.json");
const abBrFix = arr(obj(json("br-e006257-ab.json")).abr);
const abSpFix = arr(obj(json("sp-e006257-ab.json")).abr);
const UFS = abBrFix.map(a => String(a.cdabr)).filter(u => u !== "br" && u !== "zz");
const tsUf = new Map(abBrFix.map(a => [String(a.cdabr), Number(obj(a.s).ts)]));
const teUf = new Map(abBrFix.map(a => [String(a.cdabr), Number(obj(a.e).te)]));
const munSp = abSpFix.filter(a => a.tpabr === "mun").map(a => ({ cd: String(a.cdabr), ts: Number(obj(a.s).ts), te: Number(obj(a.e).te) }));
const capital = cm57.abr.find(a => a.cd === "sp")?.mu.find(m => m.cd === "71072");
const zonasCap = capital?.z ?? [];
const tsCap = munSp.find(m => m.cd === "71072")?.ts ?? 0;
const teCap = munSp.find(m => m.cd === "71072")?.te ?? 0;

/** Senado de SP de ensaio: o arquivo do governador com cargo 5, duas vagas e nomes fictícios. */
function senadoEnsaio(d: Obj): void {
  const nomes = ["ENSAIO SENADO A", "ENSAIO SENADO B", "ENSAIO SENADO C", "ENSAIO SENADO D", "ENSAIO SENADO E"];
  let i = 0;
  for (const cargo of arr(d.carg)) {
    Object.assign(cargo, { cd: "5", nmn: "Senador", nv: "2" });
    for (const agr of arr(cargo.agr)) {
      for (const par of arr(agr.par)) {
        for (const c of arr(par.cand)) {
          const nome = nomes[i % nomes.length] ?? "ENSAIO";
          Object.assign(c, { n: String(Number(c.n) * 10 + 1), sqcand: String(Number(c.sqcand) + 9_000_000), nm: nome, nmu: nome });
          i += 1;
        }
      }
    }
  }
}
const SEN_N = ["101", "131", "801", "161", "211"];

function semearPasso(seq: Sequenciador, k: number, total: number, idg: () => number): void {
  const ger = T0 + k * PASSO_MS;
  const cap = ger + 8_000;
  const tot = ger - 20_000;
  const em = (desloc = 0): string => iso(cap + desloc);
  let off = 0;
  const proc = (ch: string, corpo: Uint8Array<ArrayBuffer>): void => {
    seq.processar(ch, corpo, em(off));
    off += 5;
  };

  // Monitoramento nacional
  const entradasBr = new Map<string, EntradaAb>();
  const brTotal = { st: 0, votos: {} as Record<string, number> };
  for (const uf of UFS) {
    const f = fracao(uf, k, total);
    const ts = tsUf.get(uf) ?? 0;
    const st = Math.round(ts * f);
    entradasBr.set(uf, { st, tot });
    brTotal.st += st;
    const vv = Math.round((teUf.get(uf) ?? 0) * 0.78 * 0.93 * f);
    const votos = votosPres(uf, LEAN[uf] ?? 0.5, DERIVA[uf] ?? 0, vv, f);
    for (const [n, v] of Object.entries(votos)) brTotal.votos[n] = (brTotal.votos[n] ?? 0) + v;
    proc(chave(keyU(6257, 1, "uf", uf)), gerarU("sp-c0001-e006257-u.json", { ts, te: teUf.get(uf) ?? 0, st, votos, idg: idg(), ger, tot, tf: st === ts, cdabr: uf }));
  }

  // São Paulo: municípios, capital e zonas
  const entradasSp = new Map<string, EntradaAb>();
  let munf = 0;
  let munpt = 0;
  for (const m of munSp) {
    const f = fracao(`sp${m.cd}`, k, total);
    const st = Math.round(m.ts * f);
    if (st === 0) continue;
    if (st === m.ts) munf += 1;
    else munpt += 1;
    entradasSp.set(m.cd, { st, tot });
    const lean = (LEAN.sp ?? 0.5) + (hash01(`lean:${m.cd}`) - 0.5) * 0.4;
    const vv = Math.round(m.te * 0.78 * 0.93 * f);
    const votos = votosPres(`sp${m.cd}`, lean, 0.04, vv, f);
    proc(chave(keyU(6257, 1, "mu", "sp", m.cd)), gerarU("sp71072-c0001-e006257-u.json", { ts: m.ts, te: m.te, st, votos, idg: idg(), ger, tot, tf: st === m.ts, cdabr: m.cd }));
  }
  const spEntrada = entradasBr.get("sp");
  if (spEntrada) entradasBr.set("sp", { ...spEntrada, munf, munpt });
  entradasSp.set("sp", { st: spEntrada?.st ?? 0, tot });
  proc(chave(keyAb(6257, "sp")), gerarAb("sp-e006257-ab.json", idg(), ger, entradasSp));
  const tsBr = tsUf.get("br") ?? 0;
  entradasBr.set("br", { st: brTotal.st, tot });
  proc(chave(keyAb(6257, "br")), gerarAb("br-e006257-ab.json", idg(), ger, entradasBr));
  proc(chave(keyU(6257, 1, "br")), gerarU("br-c0001-e006257-u.json", { st: brTotal.st, votos: brTotal.votos, idg: idg(), ger, tot, tf: brTotal.st === tsBr }));

  const fCap = fracao("sp71072", k, total);
  zonasCap.forEach((z, i) => {
    const fz = Math.min(1, fCap * (0.8 + hash01(`z:${z}`) * 0.4));
    const tsz = Math.max(1, Math.round(tsCap / zonasCap.length));
    const tez = Math.max(1, Math.round(teCap / zonasCap.length * (0.7 + hash01(`te:${z}`) * 0.6)));
    const st = Math.round(tsz * fz);
    if (st === 0) return;
    const vv = Math.round(tez * 0.78 * 0.93 * fz);
    const votos = votosPres(`z${z}`, 0.3 + (i / zonasCap.length) * 0.4, 0, vv, fz);
    proc(chave(keyU(6257, 1, "zona", "sp", "71072", z)), gerarU("sp71072-z0001-c0001-e006257-u.json", { ts: tsz, te: tez, st, votos, idg: idg(), ger, tot, tf: st === tsz, cdabr: z }));
  });

  // Governador e senado de SP (eleição estadual)
  const fSp = fracao("sp", k, total);
  const tsSp = tsUf.get("sp") ?? 0;
  const vvSp = Math.round((teUf.get("sp") ?? 0) * 0.78 * 0.9 * fSp);
  const govVotos = { 10: Math.round(vvSp * (0.5 + 0.06 * (1 - fSp))), 13: Math.round(vvSp * 0.38), 80: Math.round(vvSp * 0.04), 16: Math.round(vvSp * 0.02), 21: Math.round(vvSp * 0.01) };
  proc(chave(keyU(6259, 3, "uf", "sp")), gerarU("sp-c0003-e006259-u.json", { st: Math.round(tsSp * fSp), votos: govVotos, idg: idg(), ger, tot, tf: false }));
  const pesos = [0.31, 0.27 + 0.03 * (0.5 - fSp), 0.22 - 0.03 * (0.5 - fSp), 0.12, 0.08];
  const senVotos = Object.fromEntries(SEN_N.map((n, i) => [n, Math.round(vvSp * 2 * (pesos[i] ?? 0))]));
  proc(chave(keyU(6259, 5, "uf", "sp")), gerarU("sp-c0003-e006259-u.json", { st: Math.round(tsSp * fSp), votos: senVotos, idg: idg(), ger, tot, tf: false, mexer: senadoEnsaio }));
}

// ---------- execução ----------
mkdirSync(dirname(DB), { recursive: true });
if (MAIS === undefined) for (const suf of ["", "-wal", "-shm"]) if (existsSync(DB + suf)) rmSync(DB + suf);
const db = abrirEscrita(DB);
const seq = new Sequenciador(db);
const enc = (nome: string): Uint8Array<ArrayBuffer> => new TextEncoder().encode(JSON.stringify(json(nome)));

let passoInicial = 1;
let idgAtual = 1_100_000;
if (MAIS === undefined) {
  seq.registrar(registroDeArquivos(new Map([[6257, cm57], [6259, lerCm("mun-e006259-cm.json")]])));
  seq.processar(chave(keyEleC()), enc("ele-c.json"), iso(T0 - 600_000));
  seq.processar(chave(keyCm(6257)), enc("mun-e006257-cm.json"), iso(T0 - 600_000));
  seq.processar(chave(keyCm(6259)), enc("mun-e006259-cm.json"), iso(T0 - 600_000));
} else {
  passoInicial = Number(lerMeta(db, "ensaio_passo") ?? "0") + 1;
  idgAtual = Number(lerMeta(db, "ensaio_idg") ?? String(idgAtual));
}
const total = Math.max(PASSOS, 12);
const nPassos = MAIS === undefined ? PASSOS : Number(MAIS);
const inicio = performance.now();
for (let k = passoInicial; k < passoInicial + nPassos; k++) {
  semearPasso(seq, k, total, () => (idgAtual += 1));
  seq.gravar([
    { k: "meta", chave: "ensaio_passo", valor: String(k) },
    { k: "meta", chave: "ensaio_idg", valor: String(idgAtual) },
  ]);
}
if (MAIS === undefined) {
  // Um evento de regressão para o ticker e o movimento.
  seq.gravar([
    {
      k: "evento",
      row: {
        em: iso(T0 + 3 * PASSO_MS + 30_000), tipo: "regressao_contagem", severidade: "warn", eleicao_cd: 6257, cargo_cd: 1, nivel: "mu",
        uf: "sp", municipio_cd: "71072", detalhe: { campo: "st", de: 1200, para: 1180 },
      },
    },
  ]);
}
fecharEscrita(db);
console.log(JSON.stringify({ db: DB, passos: [passoInicial, passoInicial + nPassos - 1], ...seq.contagem, ms: Math.round(performance.now() - inicio) }));
