// SQL do servidor. Comandos curtos, sem transação longa: o coletor escreve em paralelo (WAL).
// `at` = ISO UTC; "até `at`" significa capturado_em <= at. Sem `at`, usa o sentinela FIM.
import type { Database } from "bun:sqlite";
import type { LinhaAbEstado, N, S } from "../db/linhas.ts";
import type { Nivel } from "../types.ts";

export const FIM = "9999-12-31T23:59:59.999Z";
const ate = (at: string | undefined): string => at ?? FIM;

export interface CandRow {
  sqcand: number;
  numero: N;
  nome: S;
  nome_urna: S;
  partido_n: N;
  sigla: S;
  fed_sigla: S;
  vices: S;
  vap: N;
  pvapn: N;
  eleito: N;
  st: S;
  dvt: S;
}

export function candidatosSql(db: Database, sid: number): CandRow[] {
  return db
    .query<CandRow, [number]>(
      `SELECT vc.sqcand, c.numero, c.nome, c.nome_urna, c.partido_n, p.sigla, f.sigla AS fed_sigla, c.vices,
              vc.vap, vc.pvapn, vc.eleito, vc.st, vc.dvt
       FROM voto_candidato vc
       LEFT JOIN candidato c ON c.sqcand = vc.sqcand
       LEFT JOIN partido p ON p.n = c.partido_n
       LEFT JOIN federacao f ON f.n = c.federacao_n
       WHERE vc.snapshot_id = ?`,
    )
    .all(sid);
}

export function votosDe(db: Database, sid: number): Map<number, number> {
  const rows = db.query<{ sqcand: number; vap: N }, [number]>("SELECT sqcand, vap FROM voto_candidato WHERE snapshot_id = ?").all(sid);
  return new Map(rows.map((r) => [r.sqcand, r.vap ?? 0]));
}

export interface PartidoRow {
  partido_n: number;
  sigla: S;
  fed_sigla: S;
  tvtn: N;
  tvtl: N;
  tvan: N;
}

export function partidosSql(db: Database, sid: number): PartidoRow[] {
  return db
    .query<PartidoRow, [number]>(
      `SELECT vp.partido_n, p.sigla, f.sigla AS fed_sigla, SUM(vp.tvtn) AS tvtn, SUM(vp.tvtl) AS tvtl, SUM(vp.tvan) AS tvan
       FROM voto_partido vp
       LEFT JOIN partido p ON p.n = vp.partido_n
       LEFT JOIN federacao f ON f.n = p.federacao_n
       WHERE vp.snapshot_id = ? GROUP BY vp.partido_n`,
    )
    .all(sid);
}

/** Versão não regressiva anterior do mesmo arquivo. */
export function anteriorId(db: Database, arquivoId: number, sid: number): number | null {
  return (
    db
      .query<{ id: number | null }, [number, number]>(
        "SELECT MAX(id) AS id FROM snapshot WHERE arquivo_id = ? AND regressivo = 0 AND id < ?",
      )
      .get(arquivoId, sid)?.id ?? null
  );
}

export function temCandidatos(db: Database, sid: number): boolean {
  return db.query<{ x: number }, [number]>("SELECT 1 AS x FROM voto_candidato WHERE snapshot_id = ? LIMIT 1").get(sid) !== null;
}

export interface AbRow extends LinhaAbEstado {
  snapshot_id: number;
  capturado_em: string;
  gerado_em: S;
}

/** Estado do -ab de um arquivo até `at`: última entrada de cada cdabr. */
export function abAsOf(db: Database, arquivoId: number, at?: string): AbRow[] {
  return db
    .query<AbRow, [number, string]>(
      `SELECT * FROM (
         SELECT e.*, s.capturado_em, s.gerado_em,
                ROW_NUMBER() OVER (PARTITION BY e.cdabr ORDER BY e.snapshot_id DESC) AS rn
         FROM snapshot s JOIN ab_estado e ON e.snapshot_id = s.id
         WHERE s.arquivo_id = ? AND s.regressivo = 0 AND s.capturado_em <= ?
       ) WHERE rn = 1 ORDER BY cdabr`,
    )
    .all(arquivoId, ate(at));
}

/** Primeira totalização com st = ts > 0 por cdabr no -ab (hora do TSE). */
export function fechamentosAb(db: Database, arquivoId: number, at?: string): Map<string, string> {
  const rows = db
    .query<{ cdabr: string; em: S }, [number, string]>(
      `SELECT e.cdabr, MIN(COALESCE(e.totalizado_em, s.capturado_em)) AS em
       FROM snapshot s JOIN ab_estado e ON e.snapshot_id = s.id
       WHERE s.arquivo_id = ? AND s.regressivo = 0 AND s.capturado_em <= ? AND e.ts > 0 AND e.st = e.ts
       GROUP BY e.cdabr`,
    )
    .all(arquivoId, ate(at));
  const m = new Map<string, string>();
  for (const r of rows) if (r.em) m.set(r.cdabr, r.em);
  return m;
}

/** Última requisição ao arquivo (mudada ou não) até `at`. */
export function ultimaLeitura(db: Database, arquivoId: number, at?: string): string | null {
  return (
    db
      .query<{ em: S }, [number, string]>("SELECT MAX(iniciado_em) AS em FROM fetch WHERE arquivo_id = ? AND iniciado_em <= ?")
      .get(arquivoId, ate(at))?.em ?? null
  );
}

export function ultimoSnapshot(db: Database, at?: string): { id: number; capturado_em: string } | null {
  if (at === undefined) {
    return db.query<{ id: number; capturado_em: string }, []>("SELECT id, capturado_em FROM snapshot ORDER BY id DESC LIMIT 1").get();
  }
  return db
    .query<{ id: number; capturado_em: string }, [string]>(
      "SELECT id, capturado_em FROM snapshot WHERE capturado_em <= ? ORDER BY capturado_em DESC, id DESC LIMIT 1",
    )
    .get(at);
}

export interface FiltroUnidades {
  ele: number;
  cargo: number;
  nivel: Nivel;
  uf?: string;
  mun?: string;
}

function whereUnidades(f: FiltroUnidades): { sql: string; params: (string | number)[] } {
  const partes = ["a.tipo = 'u'", "a.eleicao_cd = ?", "a.cargo_cd = ?", "a.nivel = ?"];
  const params: (string | number)[] = [f.ele, f.cargo, f.nivel];
  if (f.uf !== undefined) {
    partes.push("a.uf = ?");
    params.push(f.uf);
  }
  if (f.mun !== undefined) {
    partes.push("a.municipio_cd = ?");
    params.push(f.mun);
  }
  return { sql: partes.join(" AND "), params };
}

export interface UnidadeRow {
  arquivo_id: number;
  uf: S;
  municipio_cd: S;
  zona_cd: S;
  sid: N;
  tf: N;
  capturado_em: S;
  pst: N;
  te: N;
  vagas: N;
}

/** Arquivos -u de um nível com a última versão até `at` (sem versão: campos nulos). */
export function unidadesMapa(db: Database, f: FiltroUnidades, at?: string): UnidadeRow[] {
  const w = whereUnidades(f);
  return db
    .query<UnidadeRow, (string | number)[]>(
      `WITH u AS (
         SELECT a.id AS arquivo_id, a.uf, a.municipio_cd, a.zona_cd,
                (SELECT MAX(s2.id) FROM snapshot s2
                  WHERE s2.arquivo_id = a.id AND s2.regressivo = 0 AND s2.capturado_em <= ?) AS sid
         FROM arquivo a WHERE ${w.sql}
       )
       SELECT u.*, s.tf, s.capturado_em, t.pst, t.te, t.vagas
       FROM u LEFT JOIN snapshot s ON s.id = u.sid LEFT JOIN totais t ON t.snapshot_id = u.sid
       ORDER BY u.uf, u.municipio_cd, u.zona_cd`,
    )
    .all(ate(at), ...w.params);
}

export interface CandMapaRow {
  arquivo_id: number;
  sqcand: number;
  vap: N;
  pvapn: N;
  rk: number;
  numero: N;
  nome_urna: S;
  sigla: S;
  fed_sigla: S;
}

/**
 * Os `top` mais votados de cada unidade, na última versão com candidatos até `at`.
 * O corte vem antes da janela (subconsulta com LIMIT por snapshot): deputado estadual
 * em SP, 645 municípios com cerca de 1.800 candidaturas cada, cai de 380 ms para 40 ms.
 */
export function candidatosMapa(db: Database, f: FiltroUnidades, top: number, at?: string): CandMapaRow[] {
  const w = whereUnidades(f);
  return db
    .query<CandMapaRow, (string | number)[]>(
      `WITH u AS (
         SELECT a.id AS arquivo_id,
                (SELECT MAX(s2.id) FROM snapshot s2
                  WHERE s2.arquivo_id = a.id AND s2.regressivo = 0 AND s2.capturado_em <= ?
                    AND EXISTS (SELECT 1 FROM voto_candidato x WHERE x.snapshot_id = s2.id)) AS sid
         FROM arquivo a WHERE ${w.sql}
       ),
       r AS (
         SELECT u.arquivo_id, vc.sqcand, vc.vap, vc.pvapn,
                ROW_NUMBER() OVER (PARTITION BY u.arquivo_id ORDER BY vc.vap DESC, vc.sqcand) AS rk
         FROM u JOIN voto_candidato vc ON vc.snapshot_id = u.sid
          AND vc.sqcand IN (SELECT t.sqcand FROM voto_candidato t WHERE t.snapshot_id = u.sid
                            ORDER BY t.vap DESC, t.sqcand LIMIT ?)
       )
       SELECT r.*, c.numero, c.nome_urna, p.sigla, fd.sigla AS fed_sigla
       FROM r LEFT JOIN candidato c ON c.sqcand = r.sqcand
       LEFT JOIN partido p ON p.n = c.partido_n LEFT JOIN federacao fd ON fd.n = c.federacao_n
       ORDER BY r.arquivo_id, r.rk`,
    )
    .all(ate(at), ...w.params, top);
}

export interface PontoCandRow {
  snapshot_id: number;
  capturado_em: string;
  gerado_em: S;
  pst: N;
  sqcand: number;
  pvapn: N;
  vap: N;
}

/** Série por candidato de um arquivo (só versões com voto_candidato), limitada aos `sqcands`. */
export function serieCandidatos(db: Database, arquivoId: number, sqcands: readonly number[], at?: string): PontoCandRow[] {
  if (sqcands.length === 0) return [];
  return db
    .query<PontoCandRow, (string | number)[]>(
      `SELECT s.id AS snapshot_id, s.capturado_em, s.gerado_em, t.pst, vc.sqcand, vc.pvapn, vc.vap
       FROM snapshot s
       JOIN voto_candidato vc ON vc.snapshot_id = s.id
       LEFT JOIN totais t ON t.snapshot_id = s.id
       WHERE s.arquivo_id = ? AND s.regressivo = 0 AND s.capturado_em <= ?
         AND vc.sqcand IN (${sqcands.map(() => "?").join(", ")})
       ORDER BY s.id`,
    )
    .all(arquivoId, ate(at), ...sqcands);
}

export interface MunicipioInfo {
  cd: string;
  uf: string;
  ibge: S;
  nome: S;
  capital: N;
}

export function municipiosIndex(db: Database): Map<string, MunicipioInfo> {
  const rows = db.query<MunicipioInfo, []>("SELECT cd, uf, ibge, nome, capital FROM municipio").all();
  return new Map(rows.map((r) => [r.cd, r]));
}
