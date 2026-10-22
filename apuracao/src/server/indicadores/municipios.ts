// Estado dos municípios (arquivos de nível mu) até `at`: última versão de cada um e, para os que
// fecharam (st = ts > 0), a primeira versão fechada. Eleitorado sem versão vem de
// municipio.eleitores e, na falta, da régua do 1º turno.
import type { Database } from "bun:sqlite";
import { maxSnapshotId } from "../../db/leitura.ts";
import type { N, S } from "../../db/linhas.ts";
import { titulo } from "../abr.ts";
import { CacheCurto } from "../cache.ts";
import { FIM } from "../consultas.ts";
import { CorretorTotalizacao } from "./base.ts";

export interface Municipio {
  /** sigla em caixa alta */
  uf: string;
  /** código TSE com 5 dígitos */
  cd: string;
  nm: string;
  /** há versão com totais até `at` */
  com_versao: boolean;
  te: number;
  ts: number;
  st: number;
  comparecimento: number;
  abstencao: number;
  /** instante corrigido da primeira versão fechada (ms); null se ainda aberto */
  fechouMs: number | null;
}

interface UltRow {
  uf: S;
  cd: S;
  nome: S;
  eleitores: N;
  sid: N;
  ts: N;
  st: N;
  te: N;
  comparecimento: N;
  abstencao: N;
}

interface FechRow {
  cd: S;
  totalizado_em: S;
  gerado_em: S;
  capturado_em: string;
}

export function carregarMunicipios(db: Database, ele: number, cargo: number, at?: string): Municipio[] {
  const ate = at ?? FIM;
  const ult = db
    .query<UltRow, [string, number, number]>(
      `WITH u AS (
         SELECT a.id, a.uf, a.municipio_cd,
                (SELECT MAX(s2.id) FROM snapshot s2 WHERE s2.arquivo_id = a.id AND s2.regressivo = 0 AND s2.capturado_em <= ?) AS sid
         FROM arquivo a WHERE a.tipo = 'u' AND a.eleicao_cd = ? AND a.cargo_cd = ? AND a.nivel = 'mu'
       )
       SELECT u.uf, u.municipio_cd AS cd, m.nome, m.eleitores, u.sid, t.ts, t.st, t.te, t.comparecimento, t.abstencao
       FROM u LEFT JOIN totais t ON t.snapshot_id = u.sid LEFT JOIN municipio m ON m.cd = u.municipio_cd`,
    )
    .all(ate, ele, cargo);
  const fech = db
    .query<FechRow, [string, number, number]>(
      `WITH f AS (
         SELECT a.municipio_cd AS cd, MIN(s.id) AS sid
         FROM arquivo a
         JOIN snapshot s ON s.arquivo_id = a.id AND s.regressivo = 0 AND s.capturado_em <= ?
         JOIN totais t ON t.snapshot_id = s.id
         WHERE a.tipo = 'u' AND a.eleicao_cd = ? AND a.cargo_cd = ? AND a.nivel = 'mu' AND t.ts > 0 AND t.st >= t.ts
         GROUP BY a.id
       )
       SELECT f.cd, s.totalizado_em, s.gerado_em, s.capturado_em FROM f JOIN snapshot s ON s.id = f.sid`,
    )
    .all(ate, ele, cargo);
  const ufDe = new Map<string, string>();
  for (const r of ult) if (r.cd && r.uf) ufDe.set(r.cd, r.uf.toUpperCase());
  const fechou = new Map<string, number>();
  for (const r of fech) {
    if (!r.cd) continue;
    const ms = new CorretorTotalizacao(ufDe.get(r.cd) ?? "").instante(r.totalizado_em, r.gerado_em, r.capturado_em);
    if (Number.isFinite(ms)) fechou.set(r.cd, ms);
  }
  const out: Municipio[] = [];
  for (const r of ult) {
    if (!r.cd || !r.uf) continue;
    const com = r.sid !== null && r.ts !== null;
    const ts = r.ts ?? 0;
    const st = r.st ?? 0;
    out.push({
      uf: r.uf.toUpperCase(),
      cd: r.cd,
      nm: titulo(r.nome ?? r.cd),
      com_versao: com,
      te: r.te ?? r.eleitores ?? 0,
      ts,
      st,
      comparecimento: r.comparecimento ?? 0,
      abstencao: r.abstencao ?? 0,
      fechouMs: ts > 0 && st >= ts ? (fechou.get(r.cd) ?? null) : null,
    });
  }
  return out;
}

const cache = new CacheCurto<Municipio[]>(4000, 8);

export function municipios(db: Database, ele: number, cargo: number, at?: string): Municipio[] {
  const k = [db.filename, ele, cargo, at ?? ""].join("|");
  return cache.obter(k, maxSnapshotId(db), () => carregarMunicipios(db, ele, cargo, at));
}

export function limparCacheMunicipios(): void {
  cache.limpar();
}
