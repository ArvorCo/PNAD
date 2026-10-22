// /api/2t/estaduais: os seis segundos turnos de governador (AC, AM, DF, ES, RN, TO).
import type { Database } from "bun:sqlite";
import { UFS_GOVERNADOR_2T } from "../../turno2/comum.ts";
import type { N, S } from "../../db/linhas.ts";
import { nomeUf } from "../abr.ts";
import type { PontoSerieOut } from "../api-resultado.ts";
import { viradasDe } from "../api-resultado.ts";
import type { AbRow } from "../consultas.ts";
import type { Campo } from "../contexto.ts";
import { acumular, liderMargem, somaVazia } from "./agregados.ts";
import { isoDe, minutosDe, paDe, pstDe, r1, r2 } from "./base.ts";
import type { LinhaTempo } from "./linha-tempo.ts";
import { versaoFechamento, versaoLidaAte } from "./linha-tempo.ts";
import type { Regua } from "./regua.ts";
import { comparar } from "./regua.ts";
import type { Relogio } from "./regioes.ts";

export const MAX_VIRADAS = 20;

export interface CandInfo {
  sqcand: number;
  uf: string;
  numero: number | null;
  nome_urna: string;
  sigla: string;
  fed_sigla: string | null;
}

export function candidatosCargo(db: Database, ele: number, cargo: number): CandInfo[] {
  return db
    .query<{ sqcand: number; uf: S; numero: N; nome_urna: S; sigla: S; fed_sigla: S }, [number, number]>(
      `SELECT c.sqcand, c.uf, c.numero, c.nome_urna, p.sigla, f.sigla AS fed_sigla
       FROM candidato c LEFT JOIN partido p ON p.n = c.partido_n LEFT JOIN federacao f ON f.n = c.federacao_n
       WHERE c.eleicao_cd = ? AND c.cargo_cd = ?`,
    )
    .all(ele, cargo)
    .map((r) => ({ sqcand: r.sqcand, uf: (r.uf ?? "").toUpperCase(), numero: r.numero, nome_urna: r.nome_urna ?? "", sigla: r.sigla ?? "", fed_sigla: r.fed_sigla }));
}

export interface CandEstadual {
  sqcand: string;
  n: string;
  nome_urna: string;
  partido: string;
  vap: number;
  pvapn: number;
  campo: Campo;
}

export interface Estadual {
  uf: string;
  nome: string;
  ts: number;
  st: number;
  pst: number;
  te: number;
  comparecimento: number;
  abstencao: number;
  pa: number;
  munnr: number;
  munpt: number;
  munf: number;
  cand: CandEstadual[];
  lider: string | null;
  margem_pp: number;
  viradas: { at: string; de: string; para: string }[];
  ultima_versao_em: string | null;
  idade_s: number | null;
  ref_1t: { pst_mesmo_relogio: number | null; atraso_min: number | null } | null;
  pa_final_1t: number | null;
}

export interface RespostaEstaduais {
  at: string;
  min: number;
  ele: number;
  cargo: number;
  ufs: Estadual[];
}

export interface EntradaEstaduais {
  lt: LinhaTempo;
  rel: Relogio;
  regua: Regua | null;
  ab: readonly AbRow[];
  cands: readonly CandInfo[];
  campo(sqcand: number, sigla: string, fed: string | null): Campo;
}

/** Ordem por número de urna; sem número por último. */
export function porNumero(a: { n: string; sqcand: string }, b: { n: string; sqcand: string }): number {
  const x = a.n === "" ? Number.POSITIVE_INFINITY : Number(a.n);
  const y = b.n === "" ? Number.POSITIVE_INFINITY : Number(b.n);
  if (x !== y) return x < y ? -1 : 1;
  return a.sqcand.localeCompare(b.sqcand);
}

export function montarEstaduais(e: EntradaEstaduais): RespostaEstaduais {
  const { lt, rel, regua } = e;
  const minAgora = minutosDe(rel.agoraMs, rel.t0Ms);
  const ab = new Map(e.ab.map((r) => [r.cdabr.toUpperCase(), r]));
  const info = new Map(e.cands.map((c) => [c.sqcand, c]));
  const ufs = UFS_GOVERNADOR_2T.map((uf): Estadual => {
    const l = lt.ufs.get(uf);
    const v = l ? versaoLidaAte(l, rel.agoraMs) : null;
    const s = somaVazia();
    acumular(s, v);
    const sqcands = new Set<number>(s.votos.keys());
    for (const c of e.cands) if (c.uf === uf) sqcands.add(c.sqcand);
    const cand = [...sqcands]
      .map((sq): CandEstadual => {
        const c = info.get(sq);
        const vap = s.votos.get(sq) ?? 0;
        return {
          sqcand: String(sq),
          n: c?.numero === null || c?.numero === undefined ? "" : String(c.numero),
          nome_urna: c?.nome_urna ?? "",
          partido: c?.sigla ?? "",
          vap,
          pvapn: s.vv > 0 ? r2((100 * vap) / s.vv) : 0,
          campo: e.campo(sq, c?.sigla ?? "", c?.fed_sigla ?? null),
        };
      })
      .sort(porNumero);
    const lm = liderMargem(s.votos, s.vv);
    const pontos: PontoSerieOut[] = (l?.versoes ?? []).map((x) => ({
      at: isoDe(x.inst), snapshot_id: x.id, pst: pstDe(x.st, x.ts), cand: {}, vap: Object.fromEntries([...x.votos].map(([sq, vap]) => [String(sq), vap])),
    }));
    const viradas = viradasDe(pontos).slice(-MAX_VIRADAS).map(({ at, de, para }) => ({ at, de, para }));
    const curva = regua?.gov(uf) ?? null;
    const fech = l && s.ts > 0 && s.st >= s.ts ? versaoFechamento(l) : null;
    const abUf = ab.get(uf);
    return {
      uf,
      nome: nomeUf(uf),
      ts: s.ts,
      st: s.st,
      pst: pstDe(s.st, s.ts),
      te: s.te,
      comparecimento: s.comparecimento,
      abstencao: s.abstencao,
      pa: paDe(s.comparecimento, s.abstencao),
      munnr: abUf?.munnr ?? 0,
      munpt: abUf?.munpt ?? 0,
      munf: abUf?.munf ?? 0,
      cand,
      lider: lm.lider,
      margem_pp: lm.margem_pp,
      viradas,
      ultima_versao_em: v ? isoDe(v.inst) : null,
      idade_s: v ? r1((rel.agoraMs - v.inst) / 1000) : null,
      ref_1t: regua && curva ? comparar(curva, s.st, s.ts, minAgora, fech ? minutosDe(fech.inst, rel.t0Ms) : null) : null,
      pa_final_1t: regua?.paFinalGov(uf) ?? null,
    };
  });
  return { at: isoDe(rel.agoraMs), min: minAgora, ele: lt.ele, cargo: lt.cargo, ufs };
}
