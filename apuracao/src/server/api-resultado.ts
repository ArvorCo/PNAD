// /api/resultado e /api/serie.
import type { Database } from "bun:sqlite";
import { arquivoPorChave, snapshotPorId, ultimoSnapshotComCandidatos, ultimoSnapshotPorChave } from "../db/leitura.ts";
import type { SnapshotLido } from "../db/leitura.ts";
import type { Abr } from "./abr.ts";
import { abrTexto, chaveU, nomeCargo, nomeUf, parseAbr, titulo } from "./abr.ts";
import { candidatosDe, votosDoSnapshot } from "./candidatos.ts";
import type { CandRow, PartidoRow } from "./consultas.ts";
import { anteriorId, partidosSql, serieCandidatos } from "./consultas.ts";
import type { Campo, Contexto } from "./contexto.ts";
import { ErroHttp } from "./http.ts";
import type { SomaUfs } from "./nacional.ts";
import { somaSeDefasado } from "./nacional.ts";
import { gradeSomaCache, somaNacionalAtiva } from "./nacional-serie.ts";
import type { Params } from "./http.ts";

const n0 = (v: number | null | undefined): number => v ?? 0;

export interface ViceOut {
  tp: string;
  nmu: string;
  sgp: string;
}

export interface CandOut {
  sqcand: string;
  n: string;
  nm: string;
  nmu: string;
  sg: string;
  campo: Campo;
  fed_sg?: string;
  e: boolean;
  st: string;
  dvt: string;
  vap: number;
  pvapn: number;
  d_vap?: number;
  vs: ViceOut[];
}

function vices(json: string | null): ViceOut[] {
  if (!json) return [];
  try {
    const arr = JSON.parse(json) as { tp?: string | null; nmu?: string | null; sgp?: string | null }[];
    return arr.map((v) => ({ tp: v.tp ?? "", nmu: v.nmu ?? "", sgp: v.sgp ?? "" }));
  } catch {
    return [];
  }
}

export function ordenarCand(rows: CandRow[]): CandRow[] {
  return [...rows].sort((a, b) => n0(b.vap) - n0(a.vap) || n0(a.numero) - n0(b.numero));
}

export function candOut(ctx: Contexto, c: CandRow, anterior?: Map<number, number>): CandOut {
  const out: CandOut = {
    sqcand: String(c.sqcand),
    n: c.numero === null ? "" : String(c.numero),
    nm: c.nome ?? "",
    nmu: c.nome_urna ?? "",
    sg: c.sigla ?? "",
    campo: ctx.campos.campo(c.sigla, c.fed_sigla),
    e: c.eleito === 1,
    st: c.st ?? "",
    dvt: c.dvt ?? "",
    vap: n0(c.vap),
    pvapn: n0(c.pvapn),
    vs: vices(c.vices),
  };
  if (c.fed_sigla) out.fed_sg = c.fed_sigla;
  const ant = anterior?.get(c.sqcand);
  if (ant !== undefined) out.d_vap = out.vap - ant;
  return out;
}

/** Nome legível de uma abrangência. */
export function nomeEscopo(db: Database, a: Abr): string {
  if (a.nivel === "br") return "Brasil";
  if (a.uf === null) return "";
  if (a.nivel === "uf") return nomeUf(a.uf);
  const m = db.query<{ nome: string | null }, [string]>("SELECT nome FROM municipio WHERE cd = ?").get(a.mun ?? "");
  const nome = m?.nome ? titulo(m.nome) : `${a.uf.toUpperCase()} ${a.mun ?? ""}`;
  return a.nivel === "mu" ? nome : `${nome}, zona ${Number(a.zona)}`;
}

function snapshotPedido(db: Database, chave: string, p: Params): SnapshotLido {
  const sid = p.int("snapshot_id");
  if (sid !== undefined) {
    const s = snapshotPorId(db, sid);
    if (!s || s.chave !== chave) throw new ErroHttp(404, `snapshot ${sid} não pertence a ${chave}`);
    return s;
  }
  const s = ultimoSnapshotPorChave(db, chave, p.at());
  if (!s) {
    const existe = arquivoPorChave(db, chave);
    throw new ErroHttp(404, existe ? `arquivo ainda sem versão: ${chave}` : `arquivo desconhecido: ${chave}`);
  }
  return s;
}

function partidosOut(ctx: Contexto, rows: PartidoRow[], cand: CandOut[]): unknown[] {
  const nCand = new Map<string, number>();
  for (const c of cand) nCand.set(c.sg, (nCand.get(c.sg) ?? 0) + 1);
  return rows
    .map((pr) => {
      const sg = pr.sigla ?? "";
      const o: { sg: string; campo: Campo; fed_sg?: string; tvtn: number; tvtl: number; tvan: number; n_cand: number } = {
        sg, campo: ctx.campos.campo(sg, pr.fed_sigla), tvtn: n0(pr.tvtn), tvtl: n0(pr.tvtl), tvan: n0(pr.tvan), n_cand: nCand.get(sg) ?? 0,
      };
      if (pr.fed_sigla) o.fed_sg = pr.fed_sigla;
      return o;
    })
    .sort((x, y) => y.tvtn + y.tvtl - (x.tvtn + x.tvtl));
}

/** Resposta montada da soma das UFs (arquivo nacional do TSE defasado). */
function resultadoSoma(ctx: Contexto, db: Database, ele: number, cargo: number, a: Abr, s: SnapshotLido, soma: SomaUfs): unknown {
  const cand = ordenarCand(soma.cand).map((c) => candOut(ctx, c));
  const t = soma.totais;
  const nomes = nomeCargo(cargo);
  return {
    ele,
    cargo: { cd: cargo, nome: nomes.nome, nome_f: nomes.nome_f, nv: n0(s.vagas) },
    tpabr: a.nivel,
    abr: abrTexto(a),
    nome_escopo: nomeEscopo(db, a),
    dg_hg: soma.dg_hg,
    dt_ht: soma.dt_ht,
    lido_em: soma.lido_em,
    tf: soma.tf,
    idg: null,
    snapshot_id: soma.snapshot_id,
    anterior_id: null,
    s: { ts: t.ts, st: t.st, pst: t.pst },
    e: { te: t.te, c: t.comparecimento, a: t.abstencao, pc: t.pc, pa: t.pa },
    v: { tv: t.tv, vv: t.vv, vvc: t.vvc, vnom: t.vnom, van: t.van, vb: t.vb, vn: t.vn, pvb: t.pvb, pvn: t.pvn, pvan: t.pvan },
    cand,
    partidos: partidosOut(ctx, soma.partidos, cand),
    candidatos_normalizados: true,
    blob_url: `/api/blob/${s.snapshot_id}`,
    fonte: "soma_ufs",
    nacional_tse: soma.nacional_tse,
    ufs_usadas: soma.ufs_usadas,
  };
}

export function resultado(ctx: Contexto, db: Database, p: Params): unknown {
  const ele = p.exigirInt("ele");
  const cargo = p.exigirInt("cargo");
  const a = parseAbr(p.exigirTexto("abr"));
  const chave = chaveU(ele, cargo, a);
  const s = snapshotPedido(db, chave, p);
  if (a.nivel === "br" && p.int("snapshot_id") === undefined) {
    const soma = somaSeDefasado(db, ele, cargo, s, p.at());
    if (soma) return resultadoSoma(ctx, db, ele, cargo, a, s, soma);
  }
  const sid = s.snapshot_id;
  const ant = anteriorId(db, s.arquivo_id, sid);
  const { rows, normalizados } = candidatosDe(db, sid, a.uf);
  const votosAnt = ant === null ? undefined : votosDoSnapshot(db, ant, a.uf);
  const cand = ordenarCand(rows).map((c) => candOut(ctx, c, votosAnt));
  const partidos = partidosOut(ctx, partidosSql(db, sid), cand);
  const nomes = nomeCargo(cargo);
  return {
    ele,
    cargo: { cd: cargo, nome: nomes.nome, nome_f: nomes.nome_f, nv: n0(s.vagas) },
    tpabr: a.nivel,
    abr: abrTexto(a),
    nome_escopo: nomeEscopo(db, a),
    dg_hg: s.gerado_em,
    dt_ht: s.totalizado_em,
    lido_em: s.capturado_em,
    tf: s.tf === 1,
    idg: s.idg,
    snapshot_id: sid,
    anterior_id: ant,
    s: { ts: n0(s.ts), st: n0(s.st), pst: n0(s.pst) },
    e: { te: n0(s.te), c: n0(s.comparecimento), a: n0(s.abstencao), pc: n0(s.pc), pa: n0(s.pa) },
    v: {
      tv: n0(s.tv), vv: n0(s.vv), vvc: n0(s.vvc), vnom: n0(s.vnom), van: n0(s.van), vb: n0(s.vb), vn: n0(s.vn),
      pvb: n0(s.pvb), pvn: n0(s.pvn), pvan: n0(s.pvan),
    },
    cand,
    partidos,
    candidatos_normalizados: normalizados,
    blob_url: `/api/blob/${sid}`,
    fonte: "tse",
  };
}

export interface PontoSerieOut {
  at: string;
  snapshot_id: number;
  pst: number;
  cand: Record<string, number>;
  vap: Record<string, number>;
}

export interface Virada {
  at: string;
  snapshot_id: number;
  de: string;
  para: string;
}

/** Troca de líder entre pontos consecutivos com votos; empate não troca. */
export function viradasDe(pontos: readonly PontoSerieOut[]): Virada[] {
  const out: Virada[] = [];
  let lider: string | null = null;
  for (const pt of pontos) {
    const ordem = Object.entries(pt.vap).sort((x, y) => y[1] - x[1]);
    const [primeiro, segundo] = ordem;
    if (!primeiro || primeiro[1] <= 0) continue;
    if (segundo && segundo[1] === primeiro[1]) continue;
    if (lider !== null && primeiro[0] !== lider) out.push({ at: pt.at, snapshot_id: pt.snapshot_id, de: lider, para: primeiro[0] });
    lider = primeiro[0];
  }
  return out;
}

/** Série de um arquivo: os `top` candidatos da última versão, pontos por versão não regressiva. */
export function serieArquivo(db: Database, arquivoId: number, uf: string | null, top: number, at?: string): { pontos: PontoSerieOut[]; ultimo: CandRow[] } {
  const ult = ultimoSnapshotComCandidatos(db, arquivoId, at);
  if (ult === null) return { pontos: [], ultimo: [] };
  const ultimo = ordenarCand(candidatosDe(db, ult, uf).rows).slice(0, top);
  const rows = serieCandidatos(db, arquivoId, ultimo.map((c) => c.sqcand), at);
  const pontos: PontoSerieOut[] = [];
  let atual = null as PontoSerieOut | null;
  for (const r of rows) {
    if (atual?.snapshot_id !== r.snapshot_id) {
      atual = { at: r.gerado_em ?? r.capturado_em, snapshot_id: r.snapshot_id, pst: n0(r.pst), cand: {}, vap: {} };
      pontos.push(atual);
    }
    atual.cand[String(r.sqcand)] = n0(r.pvapn);
    atual.vap[String(r.sqcand)] = n0(r.vap);
  }
  return { pontos, ultimo };
}

export function serie(ctx: Contexto, db: Database, p: Params): unknown {
  const ele = p.exigirInt("ele");
  const cargo = p.exigirInt("cargo");
  const a = parseAbr(p.exigirTexto("abr"));
  const arq = arquivoPorChave(db, chaveU(ele, cargo, a));
  if (!arq) throw new ErroHttp(404, `arquivo desconhecido: ${abrTexto(a)}`);
  const top = p.limite("top", 12, 100);
  const soma = somaNacionalAtiva(db, ele, cargo, a, p.at());
  if (soma) return serieSoma(ctx, db, ele, cargo, top, soma, p.at());
  const { pontos, ultimo } = serieArquivo(db, arq.id, a.uf, top, p.at());
  return {
    abr: abrTexto(a),
    pontos: pontos.map(({ at, snapshot_id, pst, cand }) => ({ at, snapshot_id, pst, cand })),
    viradas: viradasDe(pontos),
    fonte: "tse",
    candidatos: ultimo.map((c) => {
      const o = candOut(ctx, c);
      return { sqcand: o.sqcand, n: o.n, nmu: o.nmu, sg: o.sg, campo: o.campo };
    }),
  };
}

/** Série nacional pela soma das 28 UFs numa grade de 60 s (arquivo nacional do TSE defasado). */
function serieSoma(ctx: Contexto, db: Database, ele: number, cargo: number, top: number, soma: SomaUfs, at?: string): unknown {
  const ultimo = ordenarCand(soma.cand).slice(0, top);
  const pontos: PontoSerieOut[] = gradeSomaCache(db, ele, cargo, at).map((g) => {
    const pt: PontoSerieOut = { at: new Date(g.t).toISOString(), snapshot_id: g.snapshot_id, pst: g.ts > 0 ? (100 * g.st) / g.ts : 0, cand: {}, vap: {} };
    for (const c of ultimo) {
      const vap = g.vap.get(c.sqcand) ?? 0;
      pt.cand[String(c.sqcand)] = g.vv > 0 ? (100 * vap) / g.vv : 0;
      pt.vap[String(c.sqcand)] = vap;
    }
    return pt;
  });
  return {
    abr: "br",
    pontos: pontos.map(({ at: em, snapshot_id, pst, cand }) => ({ at: em, snapshot_id, pst, cand })),
    viradas: viradasDe(pontos),
    fonte: "soma_ufs",
    candidatos: ultimo.map((c) => {
      const o = candOut(ctx, c);
      return { sqcand: o.sqcand, n: o.n, nmu: o.nmu, sg: o.sg, campo: o.campo };
    }),
  };
}
