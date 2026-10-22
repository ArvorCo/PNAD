// Banco de teste semeado a partir das fixtures reais, com várias versões do mesmo arquivo
// (vap/st/idg alterados) para formar séries com virada, regressão e município finalizado.
import type { Database } from "bun:sqlite";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { abrirEscrita, fecharEscrita } from "../src/db/abrir.ts";
import { Sequenciador } from "../src/replay/sequenciador.ts";
import { chave, keyAb, keyCm, keyEleC, keyU, registroDeArquivos } from "../src/tse/urls.ts";
import { json, lerCm } from "./helpers.ts";

/** 17:00 de Brasília em 04/10/2026. */
export const T0 = Date.parse("2026-10-04T20:00:00.000Z");
export const iso = (ms: number): string => new Date(ms).toISOString();
export const seg = (s: number): number => T0 + s * 1000;

const p2 = (n: number): string => String(n).padStart(2, "0");
const virgula = (n: number, casas = 2): string => n.toFixed(casas).replace(".", ",");

/** Data e hora do TSE (horário de Brasília) para um instante UTC. */
export function brt(ms: number): { d: string; h: string } {
  const x = new Date(ms - 3 * 3600_000);
  return {
    d: `${p2(x.getUTCDate())}/${p2(x.getUTCMonth() + 1)}/${x.getUTCFullYear()}`,
    h: `${p2(x.getUTCHours())}:${p2(x.getUTCMinutes())}:${p2(x.getUTCSeconds())}`,
  };
}

type Obj = Record<string, unknown>;
const obj = (v: unknown): Obj => v as Obj;
const arr = (v: unknown): Obj[] => (Array.isArray(v) ? (v as Obj[]) : []);

export interface VersaoU {
  /** seções totalizadas; "ts" usa o total do arquivo */
  st: number | "ts";
  /** votos por número de urna; os demais ficam zerados */
  votos: Record<string, number>;
  idg: number;
  /** geração do arquivo (ms UTC) */
  ger: number;
  /** totalização (ms UTC) */
  tot?: number;
  tf?: boolean;
  cdabr?: string;
}

/** Fixture -u com contagens e cabeçalho trocados. */
export function versaoU(nome: string, v: VersaoU): Uint8Array<ArrayBuffer> {
  const d = obj(structuredClone(json(nome)));
  const s = obj(d.s);
  const e = obj(d.e);
  const vt = obj(d.v);
  const ts = Number(s.ts);
  const st = v.st === "ts" ? ts : v.st;
  const vv = Object.values(v.votos).reduce((a, b) => a + b, 0);
  const brancos = Math.round(vv * 0.02);
  const nulos = Math.round(vv * 0.03);
  const tv = vv + brancos + nulos;
  const g = brt(v.ger);
  Object.assign(d, { dg: g.d, hg: g.h, idg: String(v.idg), tf: v.tf ? "s" : "n" });
  if (v.cdabr !== undefined) d.cdabr = v.cdabr;
  if (v.tot !== undefined) {
    const t = brt(v.tot);
    Object.assign(d, { dt: t.d, ht: t.h });
  }
  const pst = ts > 0 ? (st / ts) * 100 : 0;
  Object.assign(s, { st: String(st), pst: virgula(pst), pstn: virgula(pst, 4) });
  const te = Number(e.te);
  Object.assign(e, { c: String(tv), a: String(Math.max(0, te - tv)) });
  Object.assign(vt, { tv: String(tv), vv: String(vv), vvc: String(vv), vnom: String(vv), vb: String(brancos), vn: String(nulos) });
  for (const cargo of arr(d.carg)) {
    for (const agr of arr(cargo.agr)) {
      for (const par of arr(agr.par)) {
        let soma = 0;
        for (const c of arr(par.cand)) {
          const vap = v.votos[String(c.n)] ?? 0;
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

/** Fixture -ab com seções de algumas entradas trocadas. */
export function versaoAb(nome: string, idg: number, ger: number, entradas: Record<string, { st: number | "ts"; tot?: number }>): Uint8Array<ArrayBuffer> {
  const d = obj(structuredClone(json(nome)));
  const g = brt(ger);
  Object.assign(d, { dg: g.d, hg: g.h, idg: String(idg) });
  for (const a of arr(d.abr)) {
    const m = entradas[String(a.cdabr)];
    if (!m) continue;
    const s = obj(a.s);
    const ts = Number(s.ts);
    const st = m.st === "ts" ? ts : m.st;
    const pst = ts > 0 ? (st / ts) * 100 : 0;
    Object.assign(s, { st: String(st), pst: virgula(pst), pstn: virgula(pst, 4) });
    if (m.tot !== undefined) {
      const t = brt(m.tot);
      Object.assign(a, { dt: t.d, ht: t.h });
    }
  }
  return new TextEncoder().encode(JSON.stringify(d));
}

export const SQ = { lula: 280002542548, flavio: 280002551544 } as const;

export const CHAVES = {
  presBr: chave(keyU(6257, 1, "br")),
  presSp: chave(keyU(6257, 1, "uf", "sp")),
  presMun: chave(keyU(6257, 1, "mu", "sp", "71072")),
  presZona: chave(keyU(6257, 1, "zona", "sp", "71072", "0001")),
  govSp: chave(keyU(6259, 3, "uf", "sp")),
  estMun: chave(keyU(6259, 7, "mu", "sp", "71072")),
  abBr: chave(keyAb(6257, "br")),
  abSp: chave(keyAb(6257, "sp")),
} as const;

export interface Semeado {
  dir: string;
  path: string;
  db: Database;
  seq: Sequenciador;
  /** id do snapshot por rótulo */
  ids: Record<string, number>;
  /** id do snapshot por rótulo; rótulo desconhecido é erro */
  id(rotulo: string): number;
  fechar(): void;
  limpar(): void;
}

export interface OpcoesSemeio {
  /** clona o presidente de São Paulo para os 645 municípios de SP (teste de desempenho do mapa) */
  municipiosSp?: boolean;
}

export function semear(o: OpcoesSemeio = {}): Semeado {
  const dir = mkdtempSync(join(tmpdir(), "apuracao-teste-"));
  const path = join(dir, "teste.sqlite");
  const db = abrirEscrita(path);
  const seq = new Sequenciador(db);
  const cm57 = lerCm("mun-e006257-cm.json");
  seq.registrar(registroDeArquivos(new Map([[6257, cm57], [6259, lerCm("mun-e006259-cm.json")]])));
  const ids: Record<string, number> = {};
  const enc = (nome: string): Uint8Array<ArrayBuffer> => new TextEncoder().encode(JSON.stringify(json(nome)));
  const proc = (rotulo: string, ch: string, corpo: Uint8Array<ArrayBuffer>, s: number): void => {
    seq.processar(ch, corpo, iso(seg(s)));
    ids[rotulo] = db.query<{ m: number }, []>("SELECT MAX(id) AS m FROM snapshot").get()?.m ?? 0;
  };
  proc("eleC", chave(keyEleC()), enc("ele-c.json"), -600);
  proc("cm57", chave(keyCm(6257)), enc("mun-e006257-cm.json"), -600);
  proc("cm59", chave(keyCm(6259)), enc("mun-e006259-cm.json"), -600);
  proc("abBr0", CHAVES.abBr, enc("br-e006257-ab.json"), -300);
  proc("abSp0", CHAVES.abSp, enc("sp-e006257-ab.json"), -300);
  proc("presBr0", CHAVES.presBr, enc("br-c0001-e006257-u.json"), -300);
  proc("presSp0", CHAVES.presSp, enc("sp-c0001-e006257-u.json"), -300);
  proc("estMun0", CHAVES.estMun, enc("sp71072-c0007-e006259-u.json"), -300);
  const brVotos = [
    { 13: 6_000_000, 22: 5_000_000, 14: 500_000 },
    { 13: 9_000_000, 22: 8_900_000, 14: 700_000 },
    { 13: 11_000_000, 22: 11_500_000, 14: 900_000 },
    { 13: 13_000_000, 22: 14_000_000, 14: 1_000_000 },
  ];
  brVotos.forEach((votos, i) => {
    const k = i + 1;
    const cap = seg(k * 120);
    proc(`presBr${k}`, CHAVES.presBr, versaoU("br-c0001-e006257-u.json", { st: 50_000 * k, votos, idg: 1_100_000 + k * 10, ger: cap - 10_000, tot: cap - 30_000 }), k * 120);
  });
  // cópia velha do CDN: idg menor que o último
  seq.processar(CHAVES.presBr, versaoU("br-c0001-e006257-u.json", { st: 1, votos: { 13: 1 }, idg: 1_100_015, ger: seg(590), tot: seg(580) }), iso(seg(600)));
  ids.presBrRegressivo = db.query<{ m: number }, []>("SELECT MAX(id) AS m FROM snapshot").get()?.m ?? 0;
  proc("abBr1", CHAVES.abBr, versaoAb("br-e006257-ab.json", 1_100_001, seg(120), { se: { st: "ts", tot: seg(100) }, sp: { st: 100, tot: seg(100) } }), 125);
  proc("presSp1", CHAVES.presSp, versaoU("sp-c0001-e006257-u.json", { st: 30_000, votos: { 13: 2_000_000, 22: 1_900_000 }, idg: 1_100_002, ger: seg(125), tot: seg(110) }), 130);
  proc("abSp1", CHAVES.abSp, versaoAb("sp-e006257-ab.json", 1_100_003, seg(130), { 71072: { st: 10_000, tot: seg(120) } }), 135);
  proc("presMun1", CHAVES.presMun, versaoU("sp71072-c0001-e006257-u.json", { st: 10_000, votos: { 13: 800_000, 22: 600_000 }, idg: 1_100_004, ger: seg(135), tot: seg(120) }), 140);
  proc("presZona1", CHAVES.presZona, versaoU("sp71072-z0001-c0001-e006257-u.json", { st: 100, votos: { 13: 9_000, 22: 7_000 }, idg: 1_100_005, ger: seg(145), tot: seg(130) }), 150);
  proc("govSp1", CHAVES.govSp, versaoU("sp-c0003-e006259-u.json", { st: 30_000, votos: { 10: 3_000_000, 13: 2_000_000 }, idg: 1_100_006, ger: seg(155), tot: seg(140) }), 160);
  proc("estMun1", CHAVES.estMun, versaoU("sp71072-c0007-e006259-u.json", { st: 10_000, votos: { 12136: 50_000, 12190: 40_000, 12222: 10 }, idg: 1_100_007, ger: seg(165), tot: seg(150) }), 170);
  proc("abBr2", CHAVES.abBr, versaoAb("br-e006257-ab.json", 1_100_008, seg(240), { se: { st: "ts", tot: seg(100) }, sp: { st: 50_000, tot: seg(230) }, pr: { st: 900, tot: seg(230) } }), 245);
  proc("presSp2", CHAVES.presSp, versaoU("sp-c0001-e006257-u.json", { st: 60_000, votos: { 13: 2_500_000, 22: 3_000_000 }, idg: 1_100_009, ger: seg(245), tot: seg(230) }), 250);
  proc("presMun2", CHAVES.presMun, versaoU("sp71072-c0001-e006257-u.json", { st: "ts", votos: { 13: 1_600_000, 22: 1_700_000 }, idg: 1_100_010, ger: seg(255), tot: seg(240), tf: false }), 260);
  seq.gravar([
    { k: "evento", row: { em: iso(seg(155)), tipo: "regressao_contagem", severidade: "warn", eleicao_cd: 6257, cargo_cd: 1, nivel: "zona", uf: "sp", municipio_cd: "71072", zona_cd: "0001", snapshot_id: ids.presZona1 ?? null, detalhe: { campo: "st", de: 120, para: 100 } } },
    { k: "evento", row: { em: iso(seg(260)), tipo: "municipio_finalizado", severidade: "info", eleicao_cd: 6257, cargo_cd: 1, nivel: "mu", uf: "sp", municipio_cd: "71072", detalhe: { totalizado_em: iso(seg(240)) } } },
    { k: "meta", chave: "estado_coletor", valor: JSON.stringify({ em_voo: 3, fila: { t0: 1 } }) },
  ]);
  if (o.municipiosSp) {
    const sp = cm57.abr.find((a) => a.cd === "sp");
    let i = 0;
    for (const mu of sp?.mu ?? []) {
      if (mu.cd === "71072") continue;
      i += 1;
      const lulaNa = i % 3 !== 0;
      const votos = { 13: lulaNa ? 1000 + i : 900, 22: lulaNa ? 900 : 1000 + i, 30: 50 };
      seq.processar(chave(keyU(6257, 1, "mu", "sp", mu.cd)), versaoU("sp71072-c0001-e006257-u.json", { st: 10, votos, idg: 1_200_000 + i, ger: seg(300), tot: seg(290), cdabr: mu.cd }), iso(seg(300) + i));
    }
  }
  return {
    dir,
    path,
    db,
    seq,
    ids,
    id: (rotulo) => {
      const v = ids[rotulo];
      if (v === undefined) throw new Error(`rótulo sem snapshot: ${rotulo}`);
      return v;
    },
    fechar: () => fecharEscrita(db),
    limpar: () => rmSync(dir, { recursive: true, force: true }),
  };
}

// ------------------------------------------------------------------ 2º turno (25/10/2026)
// Fixtures em tests/fixtures/2t/: arquivos reais da varredura de 21/10 do pleito 3221, todos
// zerados (6258 presidente nas 28 UFs, 6260 governador nas 6 UFs, seis municípios). O cm do
// 6258 tem os mesmos municípios, nomes e zonas do 6257 (conferido na extração) e reaproveita a
// fixture existente. As versões parciais e finais são derivadas das zeradas.

/** 17:00 de Brasília em 25/10/2026. */
export const T0_2T = Date.parse("2026-10-25T20:00:00.000Z");
export const seg2t = (s: number): number => T0_2T + s * 1000;

export const SQ2T = {
  lula: 280002542548,
  flavio: 280002551544,
  alanRick: 10002532492,
  mailza: 10002544107,
  celina: 70002553055,
  leandro: 70002552496,
} as const;

export const UFS_2T = [
  "ac", "al", "am", "ap", "ba", "ce", "df", "es", "go", "ma", "mg", "ms", "mt", "pa",
  "pb", "pe", "pi", "pr", "rj", "rn", "ro", "rr", "rs", "sc", "se", "sp", "to", "zz",
] as const;

export interface VersaoU2t {
  st: number | "ts";
  votos: Record<string, number>;
  idg: number;
  ger: number;
  /** totalização (ms UTC); o carimbo sai em Brasília, salvo `fusoMin` */
  tot: number;
  /** deslocamento do relógio local (AC -120, AM -60): o carimbo sai na hora local */
  fusoMin?: number;
  /** abstenção entre as seções totalizadas, em % de comparecimento + abstenção (padrão 20) */
  pa?: number;
  /** total de seções e de eleitores do arquivo, quando o gerador clona um município (padrão: os da fixture) */
  ts?: number;
  te?: number;
  /** código do município clonado */
  cdabr?: string;
}

/** Fixture -u do 2º turno com contagens coerentes: tv = vv + 5%, abstenção pela taxa pedida. */
export function versaoU2t(nome: string, v: VersaoU2t): Uint8Array<ArrayBuffer> {
  const d = obj(structuredClone(json(nome)));
  const s = obj(d.s);
  const e = obj(d.e);
  const vt = obj(d.v);
  if (v.ts !== undefined) s.ts = String(v.ts);
  if (v.te !== undefined) e.te = String(v.te);
  if (v.cdabr !== undefined) d.cdabr = v.cdabr;
  const ts = Number(s.ts);
  const st = v.st === "ts" ? ts : v.st;
  const vv = Object.values(v.votos).reduce((a, b) => a + b, 0);
  const brancos = Math.round(vv * 0.02);
  const nulos = Math.round(vv * 0.03);
  const tv = vv + brancos + nulos;
  const pa = v.pa ?? 20;
  const abst = Math.round((tv * pa) / (100 - pa));
  const g = brt(v.ger);
  const t = brt(v.tot + (v.fusoMin ?? 0) * 60_000);
  Object.assign(d, { dg: g.d, hg: g.h, idg: String(v.idg), dt: t.d, ht: t.h, tf: st === ts ? "s" : "n" });
  const pst = ts > 0 ? (st / ts) * 100 : 0;
  Object.assign(s, { st: String(st), snt: String(ts - st), pst: virgula(pst), pstn: virgula(pst, 4) });
  const te = Number(e.te);
  Object.assign(e, {
    est: String(tv + abst), c: String(tv), a: String(abst),
    pc: virgula(te > 0 ? (100 * tv) / te : 0), pa: virgula(te > 0 ? (100 * abst) / te : 0),
  });
  Object.assign(vt, { tv: String(tv), vv: String(vv), vvc: String(vv), vnom: String(vv), vb: String(brancos), vn: String(nulos) });
  for (const cargo of arr(d.carg)) {
    for (const agr of arr(cargo.agr)) {
      for (const par of arr(agr.par)) {
        let soma = 0;
        for (const c of arr(par.cand)) {
          const vap = v.votos[String(c.n)] ?? 0;
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

export interface EntradaAb2t {
  st: number | "ts";
  munnr?: number;
  munpt?: number;
  munf?: number;
}

/** Fixture -ab do 2º turno com seções e contagem de municípios trocadas. */
export function versaoAb2t(nome: string, idg: number, ger: number, entradas: Record<string, EntradaAb2t>): Uint8Array<ArrayBuffer> {
  const d = obj(structuredClone(json(nome)));
  const g = brt(ger);
  Object.assign(d, { dg: g.d, hg: g.h, idg: String(idg) });
  for (const a of arr(d.abr)) {
    const m = entradas[String(a.cdabr)];
    if (!m) continue;
    const s = obj(a.s);
    const ts = Number(s.ts);
    const st = m.st === "ts" ? ts : m.st;
    const pst = ts > 0 ? (st / ts) * 100 : 0;
    Object.assign(s, { st: String(st), snt: String(ts - st), pst: virgula(pst), pstn: virgula(pst, 4) });
    if (m.munnr !== undefined) a.munnr = String(m.munnr);
    if (m.munpt !== undefined) a.munpt = String(m.munpt);
    if (m.munf !== undefined) a.munf = String(m.munf);
    const t = brt(ger - 20_000);
    Object.assign(a, { dt: t.d, ht: t.h });
  }
  return new TextEncoder().encode(JSON.stringify(d));
}

/** Votos finais de cada UF no cenário: cerca de 280 válidos por seção, Lula à frente no NE e no exterior. */
export function votosFinais2t(uf: string, ts: number): Record<string, number> {
  const vv = ts * 280;
  const ne = ["al", "ba", "ce", "ma", "pb", "pe", "pi", "rn", "se"].includes(uf);
  const lula = Math.round(vv * (ne ? 0.62 : uf === "zz" ? 0.55 : 0.45));
  return { 13: lula, 22: vv - lula };
}

/** Abstenção do 1º turno (régua sintética) dos municípios do cenário e o desvio no 2º turno. */
export const MUN_2T = {
  adamantina: { uf: "sp", cd: "61018", pa1: 22.42, delta: 1 },
  guarulhos: { uf: "sp", cd: "64777", pa1: 20, delta: 4 },
  campinas: { uf: "sp", cd: "62910", pa1: 22, delta: -3.5 },
  saoPaulo: { uf: "sp", cd: "71072", pa1: 21, delta: 0.5 },
  rioBranco: { uf: "ac", cd: "01392", pa1: 19, delta: 3.2 },
  rio: { uf: "rj", cd: "60011", pa1: 23, delta: 0 },
} as const;

/**
 * Banco do 2º turno: zerado às 16:00, parcial às 17:10 e 17:20 (com virada nacional, virada no AC
 * e no DF para governador, AC com carimbo em hora local e uma versão regerada sem mudança, RJ
 * parado depois das 17:10) e final às 19:00 (28 UFs e 6 estaduais fechados).
 */
export function semear2t(): Semeado {
  const dir = mkdtempSync(join(tmpdir(), "apuracao-2t-teste-"));
  const path = join(dir, "teste-2t.sqlite");
  const db = abrirEscrita(path);
  const seq = new Sequenciador(db);
  const cm58 = lerCm("mun-e006257-cm.json");
  const cm60 = lerCm("2t/mun-e006260-cm.json");
  seq.registrar(registroDeArquivos(new Map([[6258, cm58], [6260, cm60]])));
  const ids: Record<string, number> = {};
  const enc = (nome: string): Uint8Array<ArrayBuffer> => new TextEncoder().encode(JSON.stringify(json(nome)));
  const proc = (rotulo: string, ch: string, corpo: Uint8Array<ArrayBuffer>, s: number): void => {
    seq.processar(ch, corpo, iso(seg2t(s)));
    ids[rotulo] = db.query<{ m: number }, []>("SELECT MAX(id) AS m FROM snapshot").get()?.m ?? 0;
  };
  const uPres = (uf: string): string => chave(keyU(6258, 1, "uf", uf));
  const uGov = (uf: string): string => chave(keyU(6260, 3, "uf", uf));
  const uMun = (uf: string, cd: string): string => chave(keyU(6258, 1, "mu", uf, cd));
  const fPres = (uf: string): string => `2t/${uf}-c0001-e006258-u.json`;
  const fGov = (uf: string): string => `2t/${uf}-c0003-e006260-u.json`;
  const fMun = (uf: string, cd: string): string => `2t/${uf}${cd}-c0001-e006258-u.json`;
  const fuso = (uf: string): number => (uf === "ac" ? -120 : uf === "am" ? -60 : 0);
  // zerado (16:00)
  proc("cm58", chave(keyCm(6258)), enc("mun-e006257-cm.json"), -7200);
  proc("cm60", chave(keyCm(6260)), enc("2t/mun-e006260-cm.json"), -7200);
  proc("abBr0", chave(keyAb(6258, "br")), enc("2t/br-e006258-ab.json"), -3600);
  proc("abGov0", chave(keyAb(6260, "br")), enc("2t/br-e006260-ab.json"), -3600);
  proc("presBr0", chave(keyU(6258, 1, "br")), enc("2t/br-c0001-e006258-u.json"), -3600);
  for (const uf of UFS_2T) proc(`pres_${uf}_0`, uPres(uf), enc(fPres(uf)), -3600);
  for (const uf of ["ac", "am", "df", "es", "rn", "to"]) proc(`gov_${uf}_0`, uGov(uf), enc(fGov(uf)), -3600);
  for (const m of Object.values(MUN_2T)) proc(`mun_${m.cd}_0`, uMun(m.uf, m.cd), enc(fMun(m.uf, m.cd)), -3600);
  let idg = 4_000_000;
  const pres = (uf: string, s: number, st: number | "ts", votos: Record<string, number>, pa?: number): void => {
    idg += 1;
    proc(`pres_${uf}_${s}`, uPres(uf), versaoU2t(fPres(uf), { st, votos, idg, ger: seg2t(s) - 10_000, tot: seg2t(s) - 20_000, fusoMin: fuso(uf), ...(pa === undefined ? {} : { pa }) }), s);
  };
  const gov = (uf: string, s: number, st: number | "ts", votos: Record<string, number>): void => {
    idg += 1;
    proc(`gov_${uf}_${s}`, uGov(uf), versaoU2t(fGov(uf), { st, votos, idg, ger: seg2t(s) - 10_000, tot: seg2t(s) - 20_000, fusoMin: fuso(uf) }), s);
  };
  const mun = (m: { uf: string; cd: string; pa1: number; delta: number }, s: number, st: number | "ts", votos: Record<string, number>): void => {
    idg += 1;
    proc(`mun_${m.cd}_${s}`, uMun(m.uf, m.cd), versaoU2t(fMun(m.uf, m.cd), { st, votos, idg, ger: seg2t(s) - 10_000, tot: seg2t(s) - 20_000, fusoMin: fuso(m.uf), pa: m.pa1 + m.delta }), s);
  };
  // 17:10: Lula à frente
  pres("sp", 600, 20_000, { 13: 2_000_000, 22: 1_500_000 });
  pres("rj", 600, 5_000, { 13: 400_000, 22: 500_000 });
  pres("pe", 600, 3_000, { 13: 600_000, 22: 200_000 });
  pres("ac", 600, 500, { 13: 30_000, 22: 60_000 });
  pres("df", 600, 1_000, { 13: 150_000, 22: 200_000 });
  gov("ac", 600, 500, { 10: 30_000, 11: 25_000 });
  gov("df", 600, 1_000, { 11: 100_000, 13: 120_000 });
  mun(MUN_2T.rio, 600, 2_000, { 13: 200_000, 22: 250_000 });
  idg += 1;
  proc("abBr600", chave(keyAb(6258, "br")), versaoAb2t("2t/br-e006258-ab.json", idg, seg2t(600) - 5_000, {
    sp: { st: 20_000, munnr: 545, munpt: 100, munf: 0 }, rj: { st: 5_000, munnr: 80, munpt: 12, munf: 0 },
  }), 605);
  mun(MUN_2T.adamantina, 900, "ts", { 13: 8_000, 22: 10_000 });
  // 17:20: Flávio passa à frente; RJ não muda mais até o fim
  pres("sp", 1200, 60_000, { 13: 6_000_000, 22: 7_000_000 });
  pres("pe", 1200, 9_000, { 13: 1_800_000, 22: 600_000 });
  pres("ac", 1200, 1_000, { 13: 60_000, 22: 120_000 });
  pres("df", 1200, 3_000, { 13: 450_000, 22: 600_000 });
  gov("ac", 1200, 1_000, { 10: 40_000, 11: 50_000 });
  gov("df", 1200, 3_000, { 11: 300_000, 13: 250_000 });
  mun(MUN_2T.guarulhos, 1200, 1_000, { 13: 200_000, 22: 230_000 });
  mun(MUN_2T.saoPaulo, 1200, 15_000, { 13: 2_500_000, 22: 2_400_000 });
  idg += 1;
  proc("abBr1200", chave(keyAb(6258, "br")), versaoAb2t("2t/br-e006258-ab.json", idg, seg2t(1200) - 5_000, {
    sp: { st: 60_000, munnr: 400, munpt: 230, munf: 15 },
  }), 1205);
  idg += 1;
  proc("abGov1200", chave(keyAb(6260, "br")), versaoAb2t("2t/br-e006260-ab.json", idg, seg2t(1200) - 5_000, {
    ac: { st: 1_000, munnr: 10, munpt: 11, munf: 1 },
  }), 1205);
  mun(MUN_2T.guarulhos, 1800, "ts", { 13: 400_000, 22: 420_000 });
  mun(MUN_2T.campinas, 1800, "ts", { 13: 300_000, 22: 380_000 });
  // 17:35: o TSE regera o arquivo do AC sem nova totalização (mesmo carimbo em hora local, geração
  // 15 min depois): pela regra simples a correção de fuso deixaria de valer e o AC voltaria 2 h.
  idg += 1;
  proc("pres_ac_regerado", uPres("ac"), versaoU2t(fPres("ac"), { st: 1_000, votos: { 13: 60_000, 22: 120_000 }, idg, ger: seg2t(2100), tot: seg2t(1180), fusoMin: -120 }), 2110);
  mun(MUN_2T.rioBranco, 2400, "ts", { 13: 70_000, 22: 130_000 });
  // 19:00: tudo fechado (RJ continua parado até aqui)
  for (const uf of UFS_2T) {
    if (uf === "rj") continue;
    const ts = Number(obj(obj(json(fPres(uf))).s).ts);
    pres(uf, 7200, "ts", votosFinais2t(uf, ts));
  }
  pres("rj", 7260, "ts", votosFinais2t("rj", 37_675));
  for (const uf of ["ac", "am", "df", "es", "rn", "to"]) {
    const ts = Number(obj(obj(json(fGov(uf))).s).ts);
    const cands = arr(obj(json(fGov(uf))).carg).flatMap((c) => arr(c.agr).flatMap((a) => arr(a.par).flatMap((p) => arr(p.cand).map((x) => String(x.n)))));
    const [c1, c2] = cands.sort();
    gov(uf, 7200, "ts", { [c1 ?? "1"]: ts * 150, [c2 ?? "2"]: ts * 130 });
  }
  mun(MUN_2T.saoPaulo, 7200, "ts", { 13: 3_000_000, 22: 3_200_000 });
  idg += 1;
  proc("abBr7200", chave(keyAb(6258, "br")), versaoAb2t("2t/br-e006258-ab.json", idg, seg2t(7200) - 5_000, Object.fromEntries(UFS_2T.map((uf) => [uf, { st: "ts" as const, munnr: 0, munpt: 0 }]))), 7205);
  return {
    dir,
    path,
    db,
    seq,
    ids,
    id: (rotulo) => {
      const v = ids[rotulo];
      if (v === undefined) throw new Error(`rótulo sem snapshot: ${rotulo}`);
      return v;
    },
    fechar: () => fecharEscrita(db),
    limpar: () => rmSync(dir, { recursive: true, force: true }),
  };
}

type PontoRegua = [number, number, number, number, number, number, number];

/** Curva sintética: 10% aos 20 min, 50% aos 60, 90% aos 120 e 100% aos 180, abstenção `pa`. */
export function curvaSintetica(ts: number, te: number, pa = 20): PontoRegua[] {
  return [[20, 10], [60, 50], [120, 90], [180, 100]].map(([m, p]): PontoRegua => {
    const st = Math.round((ts * (p ?? 0)) / 100);
    const est = Math.round((te * st) / ts);
    const a = Math.round((est * pa) / 100);
    return [m ?? 0, Math.round(((100 * st) / ts) * 1000) / 1000, st, ts, est - a, a, pa];
  });
}

/**
 * Régua sintética do 1º turno para os testes (mesmo formato de data/referencia_1t.json):
 * curvas regulares em todas as UFs; no AC um ponto adiantado (versão regerada em hora local,
 * defeito real da régua de 22/10) que o saneamento descarta; no exterior a curva degenerada
 * num minuto só, também como na régua real; governador só no AC e no DF.
 */
export function escreverRegua2t(dir: string): string {
  const curvas: Record<string, PontoRegua[]> = {};
  const abst: Record<string, { te: number; comparecimento: number; abstencao: number; pa: number }> = {};
  for (const uf of UFS_2T) {
    const d = obj(json(`2t/${uf}-c0001-e006258-u.json`));
    const ts = Number(obj(d.s).ts);
    const te = Number(obj(d.e).te);
    const pa = uf === "zz" ? 60 : 20;
    const U = uf.toUpperCase();
    curvas[U] = curvaSintetica(ts, te, pa);
    const a = Math.round((te * pa) / 100);
    abst[U] = { te, comparecimento: te - a, abstencao: a, pa };
  }
  const ac = curvas.AC ?? [];
  curvas.AC = [[5, 95, Math.round(2270 * 0.95), 2270, 1000, 250, 20], ...ac];
  curvas.ZZ = (curvas.ZZ ?? []).map((p): PontoRegua => [979.8, p[1], p[2], p[3], p[4], p[5], p[6]]);
  const municipios: Record<string, Record<string, { nm: string; te: number; ts: number; st: number; comparecimento: number; abstencao: number; pa: number; fechou_min: number; apareceu_min: number }>> = {};
  for (const m of Object.values(MUN_2T)) {
    const d = obj(json(`2t/${m.uf}${m.cd}-c0001-e006258-u.json`));
    const te = Number(obj(d.e).te);
    const ts = Number(obj(d.s).ts);
    const a = Math.round((te * m.pa1) / 100);
    (municipios[m.uf.toUpperCase()] ??= {})[m.cd] = { nm: m.cd, te, ts, st: ts, comparecimento: te - a, abstencao: a, pa: m.pa1, fechou_min: 100, apareceu_min: 30 };
  }
  const governador_1t: Record<string, { curva: PontoRegua[]; marcos: Record<string, number>; final: { te: number; comparecimento: number; abstencao: number; pa: number } }> = {};
  for (const uf of ["ac", "df"]) {
    const d = obj(json(`2t/${uf}-c0003-e006260-u.json`));
    const ts = Number(obj(d.s).ts);
    const te = Number(obj(d.e).te);
    const pa = uf === "ac" ? 21 : 19;
    const a = Math.round((te * pa) / 100);
    governador_1t[uf.toUpperCase()] = { curva: curvaSintetica(ts, te, pa), marcos: { p50: 60, p90: 120, p99: 180, p100: 180 }, final: { te, comparecimento: te - a, abstencao: a, pa } };
  }
  const marcos: Record<string, Record<string, number>> = {};
  for (const uf of Object.keys(curvas)) marcos[uf] = { p50: 60, p90: 120, p99: 180, p100: 180 };
  const ref = {
    meta: { gerado_em: "2026-10-22T00:00:00.000Z", turno: 1, eleicoes: { presidente: 6257, governador: 6259 }, regioes: {}, sintetica: true },
    curvas: { br: curvaSintetica(499_248, 158_745_502), uf: curvas },
    marcos: { br: { p50: 60, p90: 120, p99: 180, p100: 180 }, uf: marcos },
    municipios,
    abstencao_uf: abst,
    secoes_lag: { uf: {}, municipio: {} },
    governador_1t,
  };
  const caminho = join(dir, "referencia_1t_sintetica.json");
  writeFileSync(caminho, JSON.stringify(ref));
  return caminho;
}
