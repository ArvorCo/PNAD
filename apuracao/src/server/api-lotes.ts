// /api/lotes: o que cada versão não regressiva de um arquivo acrescentou à anterior
// (seções, votos válidos, votos totais e votos por candidatura). Só versões com
// voto_candidato, como /api/serie; o primeiro lote tem d = valor.
import type { Database } from "bun:sqlite";
import { arquivoPorChave, ultimoSnapshotComCandidatos } from "../db/leitura.ts";
import { abrTexto, chaveU, parseAbr } from "./abr.ts";
import { candidatosDe } from "./candidatos.ts";
import { FIM } from "./consultas.ts";
import type { Contexto } from "./contexto.ts";
import { ErroHttp } from "./http.ts";
import type { Params } from "./http.ts";
import { ordenarCand } from "./api-resultado.ts";

export interface CandLoteOut {
  sqcand: string;
  n: string;
  nmu: string;
  sg: string;
}

export interface LoteOut {
  snapshot_id: number;
  at: string;
  capturado_em: string;
  st: number;
  d_st: number;
  pst: number;
  vv: number;
  d_vv: number;
  tv: number;
  d_tv: number;
  cand: Record<string, { vap: number; d_vap: number }>;
}

interface TotalRow {
  snapshot_id: number;
  capturado_em: string;
  gerado_em: string | null;
  st: number | null;
  pst: number | null;
  vv: number | null;
  tv: number | null;
}

interface VotoRow {
  snapshot_id: number;
  sqcand: number;
  vap: number | null;
}

const n0 = (v: number | null | undefined): number => v ?? 0;

/** Lotes de um arquivo até `at`, limitados às candidaturas `sqcands`. */
export function lotesArquivo(db: Database, arquivoId: number, sqcands: readonly number[], at?: string): LoteOut[] {
  const totais = db
    .query<TotalRow, [number, string]>(
      `SELECT s.id AS snapshot_id, s.capturado_em, s.gerado_em, t.st, t.pst, t.vv, t.tv
       FROM snapshot s LEFT JOIN totais t ON t.snapshot_id = s.id
       WHERE s.arquivo_id = ? AND s.regressivo = 0 AND s.capturado_em <= ?
         AND EXISTS (SELECT 1 FROM voto_candidato x WHERE x.snapshot_id = s.id)
       ORDER BY s.id`,
    )
    .all(arquivoId, at ?? FIM);
  if (totais.length === 0) return [];
  const votos = new Map<number, Map<number, number>>();
  if (sqcands.length > 0) {
    const rows = db
      .query<VotoRow, (string | number)[]>(
        `SELECT vc.snapshot_id, vc.sqcand, vc.vap
         FROM snapshot s JOIN voto_candidato vc ON vc.snapshot_id = s.id
         WHERE s.arquivo_id = ? AND s.regressivo = 0 AND s.capturado_em <= ?
           AND vc.sqcand IN (${sqcands.map(() => "?").join(", ")})`,
      )
      .all(arquivoId, at ?? FIM, ...sqcands);
    for (const r of rows) {
      let m = votos.get(r.snapshot_id);
      if (!m) {
        m = new Map();
        votos.set(r.snapshot_id, m);
      }
      m.set(r.sqcand, n0(r.vap));
    }
  }
  const out: LoteOut[] = [];
  let ant: LoteOut | null = null;
  for (const t of totais) {
    const st = n0(t.st);
    const vv = n0(t.vv);
    const tv = n0(t.tv);
    const vs = votos.get(t.snapshot_id);
    const cand: LoteOut["cand"] = {};
    for (const sq of sqcands) {
      const k = String(sq);
      const vap = vs?.get(sq) ?? 0;
      cand[k] = { vap, d_vap: vap - (ant?.cand[k]?.vap ?? 0) };
    }
    const lote: LoteOut = {
      snapshot_id: t.snapshot_id,
      at: t.gerado_em ?? t.capturado_em,
      capturado_em: t.capturado_em,
      st,
      d_st: st - (ant?.st ?? 0),
      pst: n0(t.pst),
      vv,
      d_vv: vv - (ant?.vv ?? 0),
      tv,
      d_tv: tv - (ant?.tv ?? 0),
      cand,
    };
    out.push(lote);
    ant = lote;
  }
  return out;
}

export function lotes(_ctx: Contexto, db: Database, p: Params): unknown {
  const ele = p.exigirInt("ele");
  const cargo = p.exigirInt("cargo");
  const a = parseAbr(p.exigirTexto("abr"));
  const arq = arquivoPorChave(db, chaveU(ele, cargo, a));
  if (!arq) throw new ErroHttp(404, `arquivo desconhecido: ${abrTexto(a)}`);
  const at = p.at();
  const top = p.limite("top", 12, 100);
  const ult = ultimoSnapshotComCandidatos(db, arq.id, at);
  const ordem = ult === null ? [] : ordenarCand(candidatosDe(db, ult, a.uf).rows);
  const escolhidos = ordem.filter((c, i) => i < top || (c.vap ?? 0) > 0);
  const candidatos: CandLoteOut[] = escolhidos.map((c) => ({
    sqcand: String(c.sqcand),
    n: c.numero === null ? "" : String(c.numero),
    nmu: c.nome_urna ?? "",
    sg: c.sigla ?? "",
  }));
  return {
    abr: abrTexto(a),
    candidatos,
    lotes: lotesArquivo(db, arq.id, escolhidos.map((c) => c.sqcand), at),
    fonte: "tse",
  };
}
