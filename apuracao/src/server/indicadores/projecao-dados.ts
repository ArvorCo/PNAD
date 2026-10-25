// Leituras do banco para a projeção (/api/2t/projecao): estado de cada município do cargo até
// `at` (votos dos dois finalistas, seções) e a série da noite, guardada ao lado do banco.
import type { Database } from "bun:sqlite";
import { existsSync, readFileSync, renameSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import type { N, S } from "../../db/linhas.ts";
import { FIM } from "../consultas.ts";
import type { ObsMun } from "./projecao.ts";

export interface CandProjecao {
  sqcand: string;
  n: string;
  nome_urna: string;
}

/** Flávio (22) e Lula (13) na eleição e cargo; null se algum faltar. */
export function candidatosProjecao(db: Database, ele: number, cargo: number): { f: CandProjecao; l: CandProjecao } | null {
  const rows = db
    .query<{ sqcand: number; numero: N; nome_urna: S }, [number, number]>("SELECT sqcand, numero, nome_urna FROM candidato WHERE eleicao_cd = ? AND cargo_cd = ?")
    .all(ele, cargo);
  const de = (num: number): CandProjecao | null => {
    const r = rows.find((x) => x.numero === num);
    return r ? { sqcand: String(r.sqcand), n: String(num), nome_urna: r.nome_urna ?? "" } : null;
  };
  const f = de(22);
  const l = de(13);
  return f && l ? { f, l } : null;
}

interface Linha {
  uf: S;
  cd: S;
  ts: N;
  st: N;
  vv: N;
  f: N;
  l: N;
}

/** Última versão não regressiva de cada arquivo mu do cargo capturada até `at`. */
export function obsMunicipais(db: Database, ele: number, cargo: number, sqF: number, sqL: number, at?: string): ObsMun[] {
  const rows = db
    .query<Linha, [string, number, number, number, number]>(
      `WITH u AS (
         SELECT a.uf, a.municipio_cd AS cd,
                (SELECT MAX(s2.id) FROM snapshot s2 WHERE s2.arquivo_id = a.id AND s2.regressivo = 0 AND s2.capturado_em <= ?1) AS sid
         FROM arquivo a WHERE a.tipo = 'u' AND a.eleicao_cd = ?2 AND a.cargo_cd = ?3 AND a.nivel = 'mu'
       )
       SELECT u.uf, u.cd, t.ts, t.st, t.vv,
              (SELECT vap FROM voto_candidato v WHERE v.snapshot_id = u.sid AND v.sqcand = ?4) AS f,
              (SELECT vap FROM voto_candidato v WHERE v.snapshot_id = u.sid AND v.sqcand = ?5) AS l
       FROM u JOIN totais t ON t.snapshot_id = u.sid`,
    )
    .all(at ?? FIM, ele, cargo, sqF, sqL);
  const out: ObsMun[] = [];
  for (const r of rows) {
    if (!r.uf || !r.cd) continue;
    out.push({ uf: r.uf.toUpperCase(), cd: r.cd, st: r.st ?? 0, ts: r.ts ?? 0, f2: r.f ?? 0, l2: r.l ?? 0, vv2: r.vv ?? 0 });
  }
  return out;
}

/** [min após 17:00, p_f projetado, faixa_a, faixa_b, p_f observado, pst] */
export type PontoSerieProjecao = [number, number | null, number | null, number | null, number | null, number];

/** Passo mínimo entre pontos da série (s) e passo da grade de reconstrução (min). */
export const PASSO_SERIE_S = 60;
export const GRADE_MIN = 5;
/** Pontos da grade reconstruídos por chamada (cada um é uma leitura "até o instante"). */
export const RECONSTRUIR_POR_CHAMADA = 4;

/** Série da noite em memória, persistida em JSON ao lado do banco (reaberta na partida). */
export class SerieProjecao {
  private pontos: PontoSerieProjecao[] = [];
  private carregado = false;

  constructor(private readonly caminho: string | null) {}

  static paraBanco(db: Database, ele: number): SerieProjecao {
    const f = db.filename;
    const persistir = f && f !== ":memory:" ? join(dirname(f), ele === 6258 ? "projecao_2t_serie.json" : `projecao_serie_${ele}.json`) : null;
    return new SerieProjecao(persistir);
  }

  private abrir(): void {
    if (this.carregado) return;
    this.carregado = true;
    if (!this.caminho || !existsSync(this.caminho)) return;
    try {
      const j = JSON.parse(readFileSync(this.caminho, "utf8")) as { serie?: unknown };
      if (Array.isArray(j.serie)) this.pontos = j.serie.filter((p): p is PontoSerieProjecao => Array.isArray(p) && typeof p[0] === "number" && p.length === 6);
    } catch {
      this.pontos = [];
    }
  }

  lista(): PontoSerieProjecao[] {
    this.abrir();
    return [...this.pontos].sort((a, b) => a[0] - b[0]);
  }

  /** Minutos da grade (múltiplos de GRADE_MIN, de 0 até `minAgora` − 1) ainda sem ponto próximo. */
  faltantes(minAgora: number): number[] {
    this.abrir();
    const out: number[] = [];
    for (let m = 0; m <= minAgora - 1; m += GRADE_MIN) {
      if (!this.pontos.some((p) => Math.abs(p[0] - m) < GRADE_MIN / 2)) out.push(m);
    }
    return out;
  }

  /** Acrescenta (respeitando o passo mínimo) e grava. Devolve true se entrou. */
  acrescentar(p: PontoSerieProjecao, forcar = false): boolean {
    this.abrir();
    if (!forcar && this.pontos.some((q) => Math.abs(q[0] - p[0]) < PASSO_SERIE_S / 60)) return false;
    this.pontos.push(p);
    this.pontos.sort((a, b) => a[0] - b[0]);
    this.gravar();
    return true;
  }

  private gravar(): void {
    if (!this.caminho) return;
    try {
      const tmp = `${this.caminho}.tmp`;
      writeFileSync(tmp, `${JSON.stringify({ serie: this.pontos })}\n`);
      renameSync(tmp, this.caminho);
    } catch {
      // Sem disco gravável a série continua em memória.
    }
  }
}
