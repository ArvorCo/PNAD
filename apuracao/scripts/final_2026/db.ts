// Leitura do banco de auditoria para a avaliação final: disputas por UF e linha do tempo da noite.
import type { Database } from "bun:sqlite";
import { candidatosDoSnapshot, partidosDoSnapshot, snapshotPorId, ultimoSnapshotComCandidatos, type SnapshotLido } from "../../src/db/leitura.ts";
import { campoDe, lacunas, type Classificador, type Disputa, type Lacuna } from "./puro.ts";

export const ELE_FED = 6257;
export const ELE_EST = 6259;

export interface DisputaLida extends Disputa {
  snap: SnapshotLido;
}

interface ArqRow {
  id: number;
  eleicao_cd: number;
  cargo_cd: number;
  nivel: string;
  uf: string | null;
}

/** Todas as disputas de nível UF/BR das duas eleições, chave `${eleicao}:${cargo}:${uf|br}`. */
export function lerDisputas(db: Database, cl: Classificador): Map<string, DisputaLida> {
  const feds = new Map(db.query<{ n: number; sigla: string }, []>("SELECT n, sigla FROM federacao").all().map((f) => [f.n, f.sigla]));
  const arqs = db
    .query<ArqRow, [number, number]>("SELECT id, eleicao_cd, cargo_cd, nivel, uf FROM arquivo WHERE tipo = 'u' AND nivel IN ('uf', 'br') AND eleicao_cd IN (?, ?)")
    .all(ELE_FED, ELE_EST);
  const out = new Map<string, DisputaLida>();
  for (const a of arqs) {
    const sid = ultimoSnapshotComCandidatos(db, a.id);
    if (sid === null) continue;
    const snap = snapshotPorId(db, sid);
    if (!snap) continue;
    const uf = a.nivel === "br" ? "br" : (a.uf ?? "?");
    const cands = candidatosDoSnapshot(db, sid).map((c) => {
      const federacao = c.federacao_n !== null ? (feds.get(c.federacao_n) ?? null) : null;
      const sq = String(c.sqcand);
      return {
        sq,
        nome: c.nome_urna ?? c.nome ?? sq,
        partido: c.sigla ?? "?",
        federacao,
        agremiacao: String(c.agremiacao_n ?? c.partido_n ?? sq),
        vap: c.vap ?? 0,
        pct: c.pvapn ?? 0,
        eleito: c.eleito === 1,
        st: c.st,
        valido: c.dvt === null || c.dvt.startsWith("Válido"),
        campo: campoDe(cl, sq, c.sigla, federacao),
      };
    });
    const partidos = partidosDoSnapshot(db, sid).map((p) => ({ agremiacao: String(p.agremiacao_n), sigla: p.sigla ?? String(p.partido_n), tvtn: p.tvtn ?? 0, tvtl: p.tvtl ?? 0 }));
    out.set(`${a.eleicao_cd}:${a.cargo_cd}:${uf}`, {
      uf,
      cargo: a.cargo_cd,
      tf: snap.tf === 1,
      pst: snap.pst ?? 0,
      vagas: snap.vagas ?? 0,
      vv: snap.vv ?? 0,
      cands,
      partidos,
      snap,
    });
  }
  return out;
}

export interface Linha {
  primeira_totalizacao: string | null;
  primeiro_arquivo_com_secoes: string | null;
  travamentos_nacional: Lacuna[];
  travamentos_ufs: Lacuna[];
  uf_100: { uf: string; gerado_em: string | null; capturado_em: string }[];
  snapshots: number;
  fetches: number;
  bytes_banco: number;
}

/** Linha do tempo da noite a partir dos arquivos de presidente (nacional e por UF). */
export function lerLinha(db: Database, bytesBanco: number): Linha {
  const br = db
    .query<{ t: string | null; g: string | null }, [number]>(
      `SELECT MIN(s.totalizado_em) AS t, MIN(s.gerado_em) AS g FROM snapshot s JOIN arquivo a ON a.id = s.arquivo_id JOIN totais t ON t.snapshot_id = s.id
       WHERE a.tipo = 'u' AND a.eleicao_cd = ? AND a.nivel = 'br' AND s.regressivo = 0 AND t.st > 0`,
    )
    .get(ELE_FED);
  const inicio = br?.g ?? "0000";
  const gerados = (nivel: string): string[] =>
    db
      .query<{ g: string }, [number, string, string]>(
        `SELECT DISTINCT s.gerado_em AS g FROM snapshot s JOIN arquivo a ON a.id = s.arquivo_id
         WHERE a.tipo = 'u' AND a.eleicao_cd = ? AND a.cargo_cd = 1 AND a.nivel = ? AND s.regressivo = 0 AND s.gerado_em >= ?`,
      )
      .all(ELE_FED, nivel, inicio)
      .map((r) => r.g);
  const uf100 = db
    .query<{ uf: string; g: string | null; c: string }, [number]>(
      `SELECT a.uf AS uf, MIN(s.gerado_em) AS g, MIN(s.capturado_em) AS c FROM snapshot s JOIN arquivo a ON a.id = s.arquivo_id JOIN totais t ON t.snapshot_id = s.id
       WHERE a.tipo = 'u' AND a.eleicao_cd = ? AND a.cargo_cd = 1 AND a.nivel = 'uf' AND s.regressivo = 0 AND t.pst >= 100
       GROUP BY a.uf ORDER BY MIN(s.gerado_em)`,
    )
    .all(ELE_FED)
    .map((r) => ({ uf: r.uf, gerado_em: r.g, capturado_em: r.c }));
  const n = (sql: string): number => db.query<{ n: number }, []>(sql).get()?.n ?? 0;
  return {
    primeira_totalizacao: br?.t ?? null,
    primeiro_arquivo_com_secoes: br?.g ?? null,
    travamentos_nacional: lacunas(gerados("br"), 10),
    travamentos_ufs: lacunas(gerados("uf"), 10),
    uf_100: uf100,
    snapshots: n("SELECT COUNT(*) AS n FROM snapshot"),
    fetches: n("SELECT COUNT(*) AS n FROM fetch"),
    bytes_banco: bytesBanco,
  };
}
