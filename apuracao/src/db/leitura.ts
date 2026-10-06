// Consultas tipadas de leitura, compartilhadas por servidor, replay e testes.
import type { Database } from "bun:sqlite";
import type { Nivel, Tipo } from "../types.ts";
import type { LinhaAbEstado, LinhaTotais, N, S } from "./linhas.ts";

export interface ArquivoLido {
  id: number;
  chave: string;
  url: string;
  tipo: Tipo;
  eleicao_cd: N;
  cargo_cd: N;
  nivel: Nivel | null;
  uf: S;
  municipio_cd: S;
  zona_cd: S;
  tier: number;
  sonda: number;
  ativo: number;
  etag: S;
  last_modified: S;
  sha256: S;
  idg: N;
  gerado_em: S;
  ultimo_snapshot_id: N;
  ultimo_fetch_em: S;
  ultimo_status: S;
  n_fetch: number;
  n_mudancas: number;
  erros_seguidos: number;
  backoff_ate: S;
  final_agendado: number;
}

export interface SnapshotLido extends Partial<LinhaTotais> {
  snapshot_id: number;
  arquivo_id: number;
  chave: string;
  sha256: string;
  capturado_em: string;
  dg: S;
  hg: S;
  idg: N;
  gerado_em: S;
  dt: S;
  ht: S;
  totalizado_em: S;
  tf: N;
  andamento: S;
  divulgacao: S;
  turno: N;
  regressivo: number;
}

export interface CandidatoLido {
  sqcand: number;
  numero: N;
  nome: S;
  nome_urna: S;
  partido_n: N;
  sigla: S;
  federacao_n: N;
  agremiacao_n: N;
  vices: S;
  vap: N;
  pvapn: N;
  eleito: N;
  st: S;
  dvt: S;
}

export interface PartidoLido {
  partido_n: number;
  agremiacao_n: number;
  sigla: S;
  tvtn: N;
  tvtl: N;
  tval: N;
  tvan: N;
  dvt: S;
}

export interface PontoSerie {
  snapshot_id: number;
  capturado_em: string;
  gerado_em: S;
  totalizado_em: S;
  idg: N;
  st: N;
  ts: N;
  pst: N;
  vv: N;
  tv: N;
  comparecimento: N;
}

export interface FiltroAtual {
  eleicao?: number;
  cargo?: number;
  nivel?: Nivel;
  uf?: string;
  municipio?: string;
  tipo?: Tipo;
}

export interface AtualLido {
  arquivo_id: number;
  chave: string;
  tipo: Tipo;
  eleicao_cd: N;
  cargo_cd: N;
  nivel: Nivel | null;
  uf: S;
  municipio_cd: S;
  zona_cd: S;
  snapshot_id: number;
  capturado_em: string;
  gerado_em: S;
  totalizado_em: S;
  idg: N;
  tf: N;
  andamento: S;
  vagas: N;
  ts: N;
  st: N;
  pst: N;
  te: N;
  est: N;
  comparecimento: N;
  abstencao: N;
  tv: N;
  vv: N;
  vvc: N;
  vb: N;
  tvn: N;
  van: N;
}

export interface AbAtualLido extends LinhaAbEstado {
  arquivo_id: number;
  eleicao_cd: N;
  nivel: Nivel | null;
  uf_arquivo: S;
  snapshot_id: number;
  capturado_em: string;
  gerado_em: S;
}

const COLS_TOTAIS = [
  "vagas", "ts", "st", "snt", "si", "sni", "sa", "sna", "pst", "te", "est", "esnt", "esi", "esni", "esa", "esna", "comparecimento", "abstencao", "pc", "pa", "tv", "vvc", "vv", "vnom", "vl", "van", "vansj", "vb", "tvn", "vn", "vnt", "vsan", "vscv", "pvvc", "pvb", "ptvn", "pvan", "pvn",
].map((c) => `t.${c}`).join(", ");

const SEL_SNAPSHOT = `
  SELECT s.id AS snapshot_id, s.arquivo_id, a.chave, s.sha256, s.capturado_em, s.dg, s.hg, s.idg, s.gerado_em, s.dt, s.ht,
         s.totalizado_em, s.tf, s.andamento, s.divulgacao, s.turno, s.regressivo,
         ${COLS_TOTAIS}
  FROM snapshot s JOIN arquivo a ON a.id = s.arquivo_id LEFT JOIN totais t ON t.snapshot_id = s.id`;

export function arquivoPorChave(db: Database, chave: string): ArquivoLido | null {
  return db.query<ArquivoLido, [string]>("SELECT * FROM arquivo WHERE chave = ?").get(chave);
}

export function arquivoPorId(db: Database, id: number): ArquivoLido | null {
  return db.query<ArquivoLido, [number]>("SELECT * FROM arquivo WHERE id = ?").get(id);
}

/** Todos os arquivos (reconstrução de estado do coletor na partida). */
export function todosArquivos(db: Database): ArquivoLido[] {
  return db.query<ArquivoLido, []>("SELECT * FROM arquivo ORDER BY id").all();
}

/** Última versão não regressiva de um arquivo, opcionalmente até `at` (ISO, replay). */
export function ultimoSnapshotPorChave(db: Database, chave: string, at?: string): SnapshotLido | null {
  if (at === undefined) {
    return db
      .query<SnapshotLido, [string]>(`${SEL_SNAPSHOT} WHERE a.chave = ? AND s.regressivo = 0 ORDER BY s.id DESC LIMIT 1`)
      .get(chave);
  }
  return db
    .query<SnapshotLido, [string, string]>(
      `${SEL_SNAPSHOT} WHERE a.chave = ? AND s.regressivo = 0 AND s.capturado_em <= ? ORDER BY s.id DESC LIMIT 1`,
    )
    .get(chave, at);
}

export function snapshotPorId(db: Database, id: number): SnapshotLido | null {
  return db.query<SnapshotLido, [number]>(`${SEL_SNAPSHOT} WHERE s.id = ?`).get(id);
}

/** Candidatos com votos de um snapshot, do mais votado ao menos votado. */
export function candidatosDoSnapshot(db: Database, snapshotId: number): CandidatoLido[] {
  return db
    .query<CandidatoLido, [number]>(
      `SELECT vc.sqcand, c.numero, c.nome, c.nome_urna, c.partido_n, p.sigla, c.federacao_n, c.agremiacao_n, c.vices,
              vc.vap, vc.pvapn, vc.eleito, vc.st, vc.dvt
       FROM voto_candidato vc
       LEFT JOIN candidato c ON c.sqcand = vc.sqcand
       LEFT JOIN partido p ON p.n = c.partido_n
       WHERE vc.snapshot_id = ?
       ORDER BY vc.vap DESC, c.numero`,
    )
    .all(snapshotId);
}

/** Último snapshot do arquivo que tenha voto_candidato (proporcionais nem sempre têm). */
export function ultimoSnapshotComCandidatos(db: Database, arquivoId: number, at?: string): number | null {
  const row = db
    .query<{ id: number }, [number, string]>(
      // Versão vigente = a mais nova pela hora de geração do TSE, não a última não marcada como
      // regressiva: a marca comparou contadores entre níveis e sinalizou versões legítimas
      // (a final do AM para deputados, por exemplo). Cópia velha do CDN tem gerado_em menor.
      `SELECT s.id FROM snapshot s WHERE s.arquivo_id = ? AND s.capturado_em <= ?
         AND EXISTS (SELECT 1 FROM voto_candidato vc WHERE vc.snapshot_id = s.id)
       ORDER BY s.gerado_em DESC, s.id DESC LIMIT 1`,
    )
    .get(arquivoId, at ?? "9999");
  return row ? row.id : null;
}

export function partidosDoSnapshot(db: Database, snapshotId: number): PartidoLido[] {
  return db
    .query<PartidoLido, [number]>(
      `SELECT vp.partido_n, vp.agremiacao_n, p.sigla, vp.tvtn, vp.tvtl, vp.tval, vp.tvan, vp.dvt
       FROM voto_partido vp LEFT JOIN partido p ON p.n = vp.partido_n
       WHERE vp.snapshot_id = ? ORDER BY vp.tvtn DESC`,
    )
    .all(snapshotId);
}

/** Série temporal de um arquivo (todas as versões não regressivas). */
export function serieDoArquivo(db: Database, arquivoId: number): PontoSerie[] {
  return db
    .query<PontoSerie, [number]>(
      `SELECT s.id AS snapshot_id, s.capturado_em, s.gerado_em, s.totalizado_em, s.idg,
              t.st, t.ts, t.pst, t.vv, t.tv, t.comparecimento
       FROM snapshot s LEFT JOIN totais t ON t.snapshot_id = s.id
       WHERE s.arquivo_id = ? AND s.regressivo = 0 ORDER BY s.id`,
    )
    .all(arquivoId);
}

/** v_atual com filtros opcionais. */
export function atual(db: Database, f: FiltroAtual = {}): AtualLido[] {
  const where: string[] = [];
  const params: (string | number)[] = [];
  const add = (col: string, v: string | number | undefined): void => {
    if (v === undefined) return;
    where.push(`${col} = ?`);
    params.push(v);
  };
  add("eleicao_cd", f.eleicao);
  add("cargo_cd", f.cargo);
  add("nivel", f.nivel);
  add("uf", f.uf);
  add("municipio_cd", f.municipio);
  add("tipo", f.tipo);
  const sql = `SELECT * FROM v_atual${where.length > 0 ? ` WHERE ${where.join(" AND ")}` : ""} ORDER BY arquivo_id`;
  return db.query<AtualLido, (string | number)[]>(sql).all(...params);
}

/** Estado atual do -ab (última entrada por arquivo × cdabr). */
export function abAtual(db: Database, eleicao: number, ufArquivo?: string): AbAtualLido[] {
  if (ufArquivo === undefined) {
    return db
      .query<AbAtualLido, [number]>("SELECT * FROM v_ab_atual WHERE eleicao_cd = ? AND nivel = 'br' ORDER BY cdabr")
      .all(eleicao);
  }
  return db
    .query<AbAtualLido, [number, string]>("SELECT * FROM v_ab_atual WHERE eleicao_cd = ? AND uf_arquivo = ? ORDER BY cdabr")
    .all(eleicao, ufArquivo);
}

/** Corpo gzip original de um snapshot. */
export function blobDoSnapshot(db: Database, snapshotId: number): Uint8Array<ArrayBuffer> | null {
  const row = db
    .query<{ gz: Uint8Array }, [number]>("SELECT b.gz FROM snapshot s JOIN blob b ON b.sha256 = s.sha256 WHERE s.id = ?")
    .get(snapshotId);
  return row ? new Uint8Array(row.gz) : null;
}

export function maxSnapshotId(db: Database): number {
  return db.query<{ m: number | null }, []>("SELECT MAX(id) AS m FROM snapshot").get()?.m ?? 0;
}

export function lerMeta(db: Database, chave: string): string | null {
  return db.query<{ valor: string | null }, [string]>("SELECT valor FROM meta WHERE chave = ?").get(chave)?.valor ?? null;
}
