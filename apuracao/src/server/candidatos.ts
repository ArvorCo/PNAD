// Candidatos de um snapshot: das tabelas normalizadas ou, quando o coletor não normalizou
// (proporcional em município/zona fora do primeiro e do final), do blob original descomprimido.
import type { Database } from "bun:sqlite";
import { gunzipTexto } from "../db/itens.ts";
import { blobDoSnapshot } from "../db/leitura.ts";
import { normalizarU } from "../parse/normalizar.ts";
import { parseCorpo } from "../parse/schemas.ts";
import type { CandRow } from "./consultas.ts";
import { candidatosSql, temCandidatos } from "./consultas.ts";

const LRU_MAX = 32;
const lru = new Map<string, CandRow[] | null>();

function lembrar(sid: string, v: CandRow[] | null): CandRow[] | null {
  lru.set(sid, v);
  if (lru.size > LRU_MAX) {
    const k = lru.keys().next().value;
    if (k !== undefined) lru.delete(k);
  }
  return v;
}

/** Decodifica o blob do snapshot e devolve os candidatos no mesmo formato do SQL. */
export function candidatosDoBlob(db: Database, sid: number, uf: string | null): CandRow[] | null {
  const k = `${db.filename}:${sid}`;
  if (lru.has(k)) return lru.get(k) ?? null;
  const gz = blobDoSnapshot(db, sid);
  if (!gz) return lembrar(k, null);
  const r = parseCorpo("u", gunzipTexto(gz));
  if (!r.ok || r.parsed.tipo !== "u") return lembrar(k, null);
  const n = normalizarU(r.parsed.data, { uf, politicaCandidatos: "sempre", primeiro: true });
  const siglas = new Map(n.partidos.map((p) => [p.n, p.sigla]));
  const feds = new Map(n.federacoes.map((f) => [f.n, f.sigla]));
  const info = new Map(n.candidatos.map((c) => [c.sqcand, c]));
  const out: CandRow[] = n.votoCandidato.map((v) => {
    const c = info.get(v.sqcand);
    return {
      sqcand: v.sqcand,
      numero: c?.numero ?? null,
      nome: c?.nome ?? null,
      nome_urna: c?.nome_urna ?? null,
      partido_n: c?.partido_n ?? null,
      sigla: c?.partido_n !== null && c?.partido_n !== undefined ? (siglas.get(c.partido_n) ?? null) : null,
      fed_sigla: c?.federacao_n !== null && c?.federacao_n !== undefined ? (feds.get(c.federacao_n) ?? null) : null,
      vices: c?.vices ?? null,
      vap: v.vap,
      pvapn: v.pvapn,
      eleito: v.eleito,
      st: v.st,
      dvt: v.dvt,
    };
  });
  return lembrar(k, out);
}

export interface CandidatosLidos {
  rows: CandRow[];
  normalizados: boolean;
}

/** SQL quando há voto_candidato para o snapshot; senão o blob. */
export function candidatosDe(db: Database, sid: number, uf: string | null): CandidatosLidos {
  if (temCandidatos(db, sid)) return { rows: candidatosSql(db, sid), normalizados: true };
  return { rows: candidatosDoBlob(db, sid, uf) ?? [], normalizados: false };
}

/** vap por sqcand de um snapshot, pela mesma regra. */
export function votosDoSnapshot(db: Database, sid: number, uf: string | null): Map<number, number> {
  const { rows } = candidatosDe(db, sid, uf);
  return new Map(rows.map((r) => [r.sqcand, r.vap ?? 0]));
}
