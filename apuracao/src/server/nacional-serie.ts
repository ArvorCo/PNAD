// Série e lotes nacionais de presidente pela soma das 28 UFs (27 + exterior), numa grade de 60 s
// a partir das 17:00 de Brasília, usados quando o arquivo nacional do TSE está defasado
// (mesma regra de nacional.ts). Em cada instante t da grade, cada UF entra com a última versão
// não regressiva com candidatos e gerado_em <= t; pontos sem as 28 UFs ou sem mudança são omitidos.
import type { Database } from "bun:sqlite";
import { maxSnapshotId, ultimoSnapshotPorChave } from "../db/leitura.ts";
import type { N, S } from "../db/linhas.ts";
import { CacheCurto } from "./cache.ts";
import { FIM } from "./consultas.ts";
import type { SomaUfs } from "./nacional.ts";
import { UFS_ESPERADAS, somaSeDefasado } from "./nacional.ts";
import type { Abr } from "./abr.ts";
import { chaveU } from "./abr.ts";

/** 17:00 de Brasília no dia da eleição. */
export const INICIO_GRADE = Date.parse("2026-10-04T20:00:00.000Z");
export const PASSO_GRADE_MS = 60_000;

export interface PontoSoma {
  t: number; // instante da grade (ms UTC)
  snapshot_id: number; // maior versão entre as UFs em uso
  capturado_em: string; // leitura mais recente entre as versões em uso
  st: number;
  ts: number;
  vv: number;
  tv: number;
  vap: Map<number, number>;
}

interface SnapRow {
  id: number;
  arquivo_id: number;
  gerado_em: S;
  capturado_em: string;
  st: N;
  ts: N;
  vv: N;
  tv: N;
}

interface VotoRow {
  snapshot_id: number;
  sqcand: number;
  vap: N;
}

interface Versao {
  id: number;
  ger: number;
  capturado_em: string;
  st: number;
  ts: number;
  vv: number;
  tv: number;
  vap: Map<number, number>;
}

const n0 = (v: number | null | undefined): number => v ?? 0;

const FILTRO = `FROM snapshot s JOIN arquivo a ON a.id = s.arquivo_id
  WHERE a.tipo = 'u' AND a.eleicao_cd = ? AND a.cargo_cd = ? AND a.nivel = 'uf'
    AND s.regressivo = 0 AND s.capturado_em <= ?
    AND EXISTS (SELECT 1 FROM voto_candidato x WHERE x.snapshot_id = s.id)`;

function carregar(db: Database, ele: number, cargo: number, at: string): Map<number, Versao[]> {
  const snaps = db
    .query<SnapRow, [number, number, string]>(
      `SELECT s.id, s.arquivo_id, s.gerado_em, s.capturado_em, t.st, t.ts, t.vv, t.tv
       ${FILTRO.replace("FROM snapshot s", "FROM snapshot s LEFT JOIN totais t ON t.snapshot_id = s.id")} ORDER BY s.id`,
    )
    .all(ele, cargo, at);
  const votos = db
    .query<VotoRow, [number, number, string]>(`SELECT vc.snapshot_id, vc.sqcand, vc.vap ${FILTRO.replace("FROM snapshot s", "FROM snapshot s JOIN voto_candidato vc ON vc.snapshot_id = s.id")}`)
    .all(ele, cargo, at);
  const porSnap = new Map<number, Map<number, number>>();
  for (const v of votos) {
    let m = porSnap.get(v.snapshot_id);
    if (!m) {
      m = new Map();
      porSnap.set(v.snapshot_id, m);
    }
    m.set(v.sqcand, n0(v.vap));
  }
  const porUf = new Map<number, Versao[]>();
  for (const r of snaps) {
    const ger = Date.parse(r.gerado_em ?? r.capturado_em);
    if (!Number.isFinite(ger)) continue;
    let l = porUf.get(r.arquivo_id);
    if (!l) {
      l = [];
      porUf.set(r.arquivo_id, l);
    }
    l.push({ id: r.id, ger, capturado_em: r.capturado_em, st: n0(r.st), ts: n0(r.ts), vv: n0(r.vv), tv: n0(r.tv), vap: porSnap.get(r.id) ?? new Map() });
  }
  // Ordem de geração; empate pela versão mais nova (a última com gerado_em <= t vence).
  for (const l of porUf.values()) l.sort((x, y) => x.ger - y.ger || x.id - y.id);
  return porUf;
}

/** Pontos da grade com mudança, já com as 28 UFs. */
export function gradeSoma(db: Database, ele: number, cargo: number, at?: string): PontoSoma[] {
  const porUf = carregar(db, ele, cargo, at ?? FIM);
  if (porUf.size < UFS_ESPERADAS) return [];
  let fim = INICIO_GRADE;
  for (const l of porUf.values()) fim = Math.max(fim, l[l.length - 1]?.ger ?? fim);
  const instantes: number[] = [];
  for (let t = INICIO_GRADE; t < fim; t += PASSO_GRADE_MS) instantes.push(t);
  instantes.push(fim);

  const listas = [...porUf.values()];
  const pos = listas.map(() => -1);
  const pontos: PontoSoma[] = [];
  let assinaturaAnt = "";
  for (const t of instantes) {
    listas.forEach((l, i) => {
      let p = pos[i] ?? -1;
      while (p + 1 < l.length && (l[p + 1]?.ger ?? Infinity) <= t) p += 1;
      pos[i] = p;
    });
    if (pos.some((p) => p < 0)) continue;
    const ponto: PontoSoma = { t, snapshot_id: 0, capturado_em: "", st: 0, ts: 0, vv: 0, tv: 0, vap: new Map() };
    listas.forEach((l, i) => {
      const v = l[pos[i] ?? 0];
      if (!v) return;
      ponto.snapshot_id = Math.max(ponto.snapshot_id, v.id);
      if (v.capturado_em > ponto.capturado_em) ponto.capturado_em = v.capturado_em;
      ponto.st += v.st;
      ponto.ts += v.ts;
      ponto.vv += v.vv;
      ponto.tv += v.tv;
      for (const [sq, vap] of v.vap) ponto.vap.set(sq, (ponto.vap.get(sq) ?? 0) + vap);
    });
    const assinatura = [ponto.st, ponto.ts, ponto.vv, ponto.tv, ...[...ponto.vap].sort((x, y) => x[0] - y[0]).map(([sq, v]) => `${sq}:${v}`)].join("|");
    if (assinatura === assinaturaAnt) continue;
    assinaturaAnt = assinatura;
    pontos.push(ponto);
  }
  return pontos;
}

const cache = new CacheCurto<PontoSoma[]>(5000, 8);

export function gradeSomaCache(db: Database, ele: number, cargo: number, at?: string): PontoSoma[] {
  const k = [db.filename, ele, cargo, at ?? ""].join("|");
  return cache.obter(k, maxSnapshotId(db), () => gradeSoma(db, ele, cargo, at));
}

/** Soma das UFs quando a regra de defasagem de nacional.ts vale para o arquivo nacional `br`. */
export function somaNacionalAtiva(db: Database, ele: number, cargo: number, a: Abr, at?: string): SomaUfs | null {
  if (a.nivel !== "br" || cargo !== 1) return null;
  const br = ultimoSnapshotPorChave(db, chaveU(ele, cargo, a), at);
  return br ? somaSeDefasado(db, ele, cargo, br, at) : null;
}
