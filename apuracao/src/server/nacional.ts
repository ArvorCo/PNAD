// Agregado nacional de presidente pela soma das 28 UFs (27 + exterior) quando o arquivo
// nacional do TSE (u:<ele>:1:br) para de andar enquanto o monitoramento (-ab br) e as UFs seguem.
// Regra: defasado se o -ab br tem mais de 2% das seções à frente do arquivo br, ou se o -ab br
// foi gerado mais de 180 s depois dele. A soma só substitui o arquivo quando as 28 UFs têm versão
// com candidatos e somam mais seções que ele. A totalização considerada em cada UF é a que não
// passa da geração do próprio arquivo (o exterior já trouxe ht do dia seguinte).
import type { Database } from "bun:sqlite";
import type { SnapshotLido } from "../db/leitura.ts";
import { arquivoPorChave, maxSnapshotId } from "../db/leitura.ts";
import type { N, S } from "../db/linhas.ts";
import { chave, keyAb } from "../tse/urls.ts";
import { CacheCurto } from "./cache.ts";
import type { CandRow, PartidoRow } from "./consultas.ts";
import { FIM } from "./consultas.ts";

export const UFS_ESPERADAS = 28;
const LIMIAR_SECOES = 0.02;
const LIMIAR_GERACAO_S = 180;

export interface NacionalTse {
  hg: string | null;
  st: number;
  pst: number;
}

export interface TotaisSoma {
  ts: number; st: number; pst: number; te: number; est: number; comparecimento: number; abstencao: number; pc: number; pa: number;
  tv: number; vv: number; vvc: number; vnom: number; van: number; vb: number; vn: number; tvn: number; pvb: number; pvn: number; pvan: number;
}

export interface SomaUfs {
  ufs_usadas: number;
  snapshot_id: number; // maior versão entre as UFs (muda quando qualquer UF muda)
  dt_ht: string | null;
  dg_hg: string | null;
  lido_em: string;
  tf: boolean;
  totais: TotaisSoma;
  cand: CandRow[];
  partidos: PartidoRow[];
  nacional_tse: NacionalTse;
}

const n0 = (v: number | null | undefined): number => v ?? 0;
const pct = (a: number, b: number): number => (b > 0 ? (100 * a) / b : 0);
const ate = (at: string | undefined): string => at ?? FIM;

interface AbBr {
  st: number;
  ts: number;
  gerado_em: string | null;
}

function abBrAsOf(db: Database, ele: number, at?: string): AbBr | null {
  const arq = arquivoPorChave(db, chave(keyAb(ele, "br")));
  if (!arq) return null;
  const linha = db
    .query<{ st: N; ts: N }, [number, string]>(
      `SELECT e.st, e.ts FROM snapshot s JOIN ab_estado e ON e.snapshot_id = s.id
       WHERE s.arquivo_id = ? AND s.regressivo = 0 AND s.capturado_em <= ? AND e.cdabr = 'br'
       ORDER BY s.id DESC LIMIT 1`,
    )
    .get(arq.id, ate(at));
  if (!linha) return null;
  const ger = db
    .query<{ gerado_em: S }, [number, string]>(
      "SELECT gerado_em FROM snapshot WHERE arquivo_id = ? AND regressivo = 0 AND capturado_em <= ? ORDER BY id DESC LIMIT 1",
    )
    .get(arq.id, ate(at));
  return { st: n0(linha.st), ts: n0(linha.ts), gerado_em: ger?.gerado_em ?? null };
}

/** O arquivo nacional está parado em relação ao monitoramento? */
export function nacionalDefasado(br: { st: number; gerado_em: string | null }, ab: AbBr | null): boolean {
  if (!ab) return false;
  if (ab.ts > 0 && ab.st - br.st > LIMIAR_SECOES * ab.ts) return true;
  if (ab.gerado_em && br.gerado_em) {
    const d = (Date.parse(ab.gerado_em) - Date.parse(br.gerado_em)) / 1000;
    if (Number.isFinite(d) && d > LIMIAR_GERACAO_S) return true;
  }
  return false;
}

interface UfSnap {
  sid: number;
}

interface TotaisRow {
  n: number;
  ts: N; st: N; te: N; est: N; comparecimento: N; abstencao: N; tv: N; vv: N; vvc: N; vnom: N; van: N; vb: N; vn: N; tvn: N;
  dt_ht: S; dg_hg: S; lido_em: S; tf_min: N;
}

function somar(db: Database, ele: number, cargo: number, br: SnapshotLido, at?: string): SomaUfs | null {
  const ufs = db
    .query<UfSnap, [string, number, number]>(
      `SELECT (SELECT MAX(s.id) FROM snapshot s
                WHERE s.arquivo_id = a.id AND s.regressivo = 0 AND s.capturado_em <= ?
                  AND EXISTS (SELECT 1 FROM voto_candidato x WHERE x.snapshot_id = s.id)) AS sid
       FROM arquivo a WHERE a.tipo = 'u' AND a.eleicao_cd = ? AND a.cargo_cd = ? AND a.nivel = 'uf'`,
    )
    .all(ate(at), ele, cargo);
  const ids = ufs.flatMap((u) => (u.sid === null ? [] : [u.sid]));
  if (ufs.length !== UFS_ESPERADAS || ids.length !== UFS_ESPERADAS) return null;
  const marcas = ids.map(() => "?").join(", ");
  const t = db
    .query<TotaisRow, number[]>(
      `SELECT COUNT(*) AS n, SUM(t.ts) AS ts, SUM(t.st) AS st, SUM(t.te) AS te, SUM(t.est) AS est,
              SUM(t.comparecimento) AS comparecimento, SUM(t.abstencao) AS abstencao, SUM(t.tv) AS tv, SUM(t.vv) AS vv,
              SUM(t.vvc) AS vvc, SUM(t.vnom) AS vnom, SUM(t.van) AS van, SUM(t.vb) AS vb, SUM(t.vn) AS vn, SUM(t.tvn) AS tvn,
              MAX(CASE WHEN s.gerado_em IS NULL OR s.totalizado_em <= s.gerado_em THEN s.totalizado_em END) AS dt_ht, MAX(s.gerado_em) AS dg_hg, MAX(s.capturado_em) AS lido_em, MIN(COALESCE(s.tf, 0)) AS tf_min
       FROM snapshot s LEFT JOIN totais t ON t.snapshot_id = s.id WHERE s.id IN (${marcas})`,
    )
    .get(...ids);
  if (!t || t.n !== UFS_ESPERADAS || t.lido_em === null) return null;
  const st = n0(t.st);
  if (st <= n0(br.st)) return null;
  const cand = db
    .query<CandRow, number[]>(
      `SELECT vc.sqcand, c.numero, c.nome, c.nome_urna, c.partido_n, p.sigla, f.sigla AS fed_sigla, c.vices,
              SUM(vc.vap) AS vap, 0 AS pvapn, MAX(vc.eleito) AS eleito, MAX(vc.st) AS st, MAX(vc.dvt) AS dvt
       FROM voto_candidato vc
       LEFT JOIN candidato c ON c.sqcand = vc.sqcand
       LEFT JOIN partido p ON p.n = c.partido_n
       LEFT JOIN federacao f ON f.n = c.federacao_n
       WHERE vc.snapshot_id IN (${marcas}) GROUP BY vc.sqcand`,
    )
    .all(...ids);
  const vv = n0(t.vv);
  for (const c of cand) c.pvapn = pct(n0(c.vap), vv);
  const partidos = db
    .query<PartidoRow, number[]>(
      `SELECT vp.partido_n, p.sigla, f.sigla AS fed_sigla, SUM(vp.tvtn) AS tvtn, SUM(vp.tvtl) AS tvtl, SUM(vp.tvan) AS tvan
       FROM voto_partido vp
       LEFT JOIN partido p ON p.n = vp.partido_n
       LEFT JOIN federacao f ON f.n = p.federacao_n
       WHERE vp.snapshot_id IN (${marcas}) GROUP BY vp.partido_n`,
    )
    .all(...ids);
  const ts = n0(t.ts);
  const te = n0(t.te);
  const comparecimento = n0(t.comparecimento);
  const abstencao = n0(t.abstencao);
  const tv = n0(t.tv);
  const vb = n0(t.vb);
  const vn = n0(t.vn);
  const van = n0(t.van);
  return {
    ufs_usadas: UFS_ESPERADAS,
    snapshot_id: Math.max(...ids),
    dt_ht: t.dt_ht,
    dg_hg: t.dg_hg,
    lido_em: t.lido_em,
    tf: t.tf_min === 1,
    totais: {
      ts, st, pst: pct(st, ts), te, est: n0(t.est), comparecimento, abstencao, pc: pct(comparecimento, te), pa: pct(abstencao, te),
      tv, vv, vvc: n0(t.vvc), vnom: n0(t.vnom), van, vb, vn, tvn: n0(t.tvn), pvb: pct(vb, tv), pvn: pct(vn, tv), pvan: pct(van, tv),
    },
    cand,
    partidos,
    nacional_tse: { hg: br.gerado_em, st: n0(br.st), pst: n0(br.pst) },
  };
}

const cache = new CacheCurto<SomaUfs | null>(5000, 16);

/**
 * Soma das UFs se o arquivo nacional `br` estiver defasado; null quando o arquivo do TSE serve.
 * Só presidente (cargo 1): os demais cargos não têm arquivo nacional.
 */
export function somaSeDefasado(db: Database, ele: number, cargo: number, br: SnapshotLido, at?: string): SomaUfs | null {
  if (cargo !== 1) return null;
  const k = [db.filename, ele, cargo, br.snapshot_id, at ?? ""].join("|");
  return cache.obter(k, maxSnapshotId(db), () => {
    if (!nacionalDefasado({ st: n0(br.st), gerado_em: br.gerado_em }, abBrAsOf(db, ele, at))) return null;
    return somar(db, ele, cargo, br, at);
  });
}

export function limparCacheNacional(): void {
  cache.limpar();
}
