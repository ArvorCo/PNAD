// Banco de teste semeado a partir das fixtures reais, com várias versões do mesmo arquivo
// (vap/st/idg alterados) para formar séries com virada, regressão e município finalizado.
import type { Database } from "bun:sqlite";
import { mkdtempSync, rmSync } from "node:fs";
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
