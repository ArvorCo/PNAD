// /api/anomalias: eventos gravados pelo coletor + viradas e fechamentos derivados das séries
// só como reserva, quando o coletor não gravou a linha (sem duplicar).
import type { Database } from "bun:sqlite";
import { corrigirTotalizadoEm } from "../turno2/comum.ts";
import { chave, keyAb } from "../tse/urls.ts";
import { arquivoPorChave, maxSnapshotId } from "../db/leitura.ts";
import { abrTexto, titulo } from "./abr.ts";
import { eleicoes } from "./api-config.ts";
import { serieArquivo, viradasDe } from "./api-resultado.ts";
import { CacheCurto } from "./cache.ts";
import type { MunicipioInfo } from "./consultas.ts";
import { FIM, municipiosIndex } from "./consultas.ts";
import type { Contexto } from "./contexto.ts";
import type { Params } from "./http.ts";
import type { Categoria } from "./textos.ts";
import { categoria, textoEvento } from "./textos.ts";

export interface AnomaliaOut {
  id: number;
  at: string;
  tipo: string;
  categoria: Categoria;
  severidade: "info" | "warn" | "error";
  nivel: string | null;
  uf: string | null;
  municipio_cd: string | null;
  zona_cd: string | null;
  cargo_cd: number | null;
  cargo: number | null;
  abr: string;
  snapshot_id: number | null;
  texto: string;
  detalhe: unknown;
  derivado: boolean;
}

interface EventoRow {
  id: number;
  em: string;
  tipo: string;
  severidade: "info" | "warn" | "error";
  nivel: string | null;
  uf: string | null;
  municipio_cd: string | null;
  zona_cd: string | null;
  cargo_cd: number | null;
  snapshot_id: number | null;
  detalhe: string | null;
}

const GRAU: Readonly<Record<string, number>> = { info: 0, warn: 1, error: 2 };

function detalheDe(s: string | null): unknown {
  if (s === null) return null;
  try {
    return JSON.parse(s) as unknown;
  } catch {
    return s;
  }
}

function montar(r0: Omit<AnomaliaOut, "texto" | "categoria" | "abr" | "cargo">, muns: ReadonlyMap<string, MunicipioInfo>): AnomaliaOut {
  // O coletor grava o município de alguns eventos (municipio_finalizado) só no detalhe,
  // com nivel "uf"; sem este ajuste o texto diria que a UF inteira terminou.
  const det = r0.detalhe !== null && typeof r0.detalhe === "object" ? (r0.detalhe as { municipio?: unknown }) : {};
  const munDet = typeof det.municipio === "string" && det.municipio !== "" ? det.municipio : null;
  const r = r0.municipio_cd === null && munDet !== null ? { ...r0, municipio_cd: munDet, nivel: "mu" } : r0;
  const nivel = r.nivel === "mu" || r.nivel === "zona" || r.nivel === "uf" || r.nivel === "br" ? r.nivel : null;
  return {
    ...r,
    categoria: categoria(r.tipo),
    abr: abrTexto({ nivel, uf: r.uf, municipio_cd: r.municipio_cd, zona_cd: r.zona_cd }),
    cargo: r.cargo_cd,
    texto: textoEvento(r.tipo, r.at, r, r.detalhe, muns),
  };
}

const cacheDerivadas = new CacheCurto<AnomaliaOut[]>(5000, 16);

/** Fechamento de cada UF pelo -ab br até `at`, com o totalizado_em corrigido do fuso. */
function fechamentosUf(db: Database, arquivoId: number, at?: string): Map<string, string> {
  const rows = db
    .query<{ cdabr: string; em: string | null; gerado_em: string | null }, [number, string]>(
      `SELECT e.cdabr, MIN(COALESCE(e.totalizado_em, s.capturado_em)) AS em, s.gerado_em
       FROM snapshot s JOIN ab_estado e ON e.snapshot_id = s.id
       WHERE s.arquivo_id = ? AND s.regressivo = 0 AND s.capturado_em <= ? AND e.ts > 0 AND e.st = e.ts
       GROUP BY e.cdabr`,
    )
    .all(arquivoId, at ?? FIM);
  const m = new Map<string, string>();
  for (const r of rows) {
    const em = corrigirTotalizadoEm(r.cdabr, r.em, r.gerado_em);
    if (em) m.set(r.cdabr, em);
  }
  return m;
}

/**
 * Reserva para viradas (presidente br/uf, governador uf) e fechamentos de UF quando o coletor
 * não gravou a linha: virada derivada some se o mesmo snapshot já tem virada gravada; fechamento
 * derivado some se a UF já tem fechamento gravado.
 */
function derivadas(db: Database, muns: ReadonlyMap<string, MunicipioInfo>, at?: string): AnomaliaOut[] {
  const viradasGravadas = new Set(
    db
      .query<{ s: number }, []>("SELECT DISTINCT snapshot_id AS s FROM evento WHERE tipo = 'virada' AND snapshot_id IS NOT NULL")
      .all()
      .map((r) => r.s),
  );
  const ufsFechadas = new Set(
    db
      .query<{ uf: string }, []>("SELECT DISTINCT uf FROM evento WHERE tipo IN ('fechou', 'uf_fechou') AND uf IS NOT NULL")
      .all()
      .map((r) => r.uf),
  );
  const el = eleicoes(db);
  const out: AnomaliaOut[] = [];
  const arqs = db
    .query<{ id: number; cargo_cd: number; nivel: string; uf: string | null }, [number, number]>(
      `SELECT a.id, a.cargo_cd, a.nivel, a.uf FROM arquivo a
       WHERE a.tipo = 'u' AND ((a.eleicao_cd = ? AND a.cargo_cd = 1 AND a.nivel IN ('br', 'uf'))
                               OR (a.eleicao_cd = ? AND a.cargo_cd = 3 AND a.nivel = 'uf'))
         AND EXISTS (SELECT 1 FROM snapshot s WHERE s.arquivo_id = a.id)`,
    )
    .all(el.federal, el.estadual);
  for (const a of arqs) {
    const { pontos, ultimo } = serieArquivo(db, a.id, a.uf, 4, at);
    const nomes = new Map(ultimo.map((c) => [String(c.sqcand), titulo(c.nome_urna)]));
    for (const v of viradasDe(pontos)) {
      if (viradasGravadas.has(v.snapshot_id)) continue;
      out.push(
        montar(
          {
            id: -v.snapshot_id, at: v.at, tipo: "virada", severidade: "warn", nivel: a.nivel, uf: a.uf, municipio_cd: null, zona_cd: null,
            cargo_cd: a.cargo_cd, snapshot_id: v.snapshot_id, derivado: true,
            detalhe: { de: v.de, para: v.para, de_nome: nomes.get(v.de) ?? v.de, para_nome: nomes.get(v.para) ?? v.para },
          },
          muns,
        ),
      );
    }
  }
  const abBr = arquivoPorChave(db, chave(keyAb(el.federal, "br")));
  if (abBr) {
    let i = 0;
    for (const [uf, em] of fechamentosUf(db, abBr.id, at)) {
      if (uf === "br" || ufsFechadas.has(uf)) continue;
      i += 1;
      out.push(
        montar(
          {
            id: -(1_000_000_000 + abBr.id * 100 + i), at: em, tipo: "fechou", severidade: "info", nivel: "uf", uf, municipio_cd: null,
            zona_cd: null, cargo_cd: null, snapshot_id: null, derivado: true, detalhe: { totalizado_em: em },
          },
          muns,
        ),
      );
    }
  }
  return out;
}

export function anomalias(_ctx: Contexto, db: Database, p: Params): AnomaliaOut[] {
  const at = p.at();
  const desde = p.iso("desde");
  const tipo = p.texto("tipo");
  const sev = p.texto("severidade");
  const uf = p.texto("uf")?.toLowerCase();
  const limit = p.limite("limit", 200, 5000);
  const where: string[] = ["em <= ?"];
  const params: (string | number)[] = [at ?? "9999"];
  if (desde !== undefined) {
    where.push("em >= ?");
    params.push(desde);
  }
  if (tipo !== undefined) {
    where.push("tipo = ?");
    params.push(tipo);
  }
  if (sev !== undefined) {
    const g = GRAU[sev] ?? 0;
    where.push(`severidade IN (${Object.keys(GRAU).filter((k) => (GRAU[k] ?? 0) >= g).map((k) => `'${k}'`).join(", ")})`);
  }
  if (uf !== undefined) {
    where.push("uf = ?");
    params.push(uf);
  }
  const muns = municipiosIndex(db);
  const gravadas = db
    .query<EventoRow, (string | number)[]>(
      `SELECT id, em, tipo, severidade, nivel, uf, municipio_cd, zona_cd, cargo_cd, snapshot_id, detalhe FROM evento
       WHERE ${where.join(" AND ")} ORDER BY id DESC LIMIT ?`,
    )
    .all(...params, limit)
    .map(({ em, detalhe, ...r }) => montar({ ...r, at: em, detalhe: detalheDe(detalhe), derivado: false }, muns));
  const grauMin = sev === undefined ? 0 : (GRAU[sev] ?? 0);
  const extra = cacheDerivadas
    .obter(`${db.filename}|${at ?? ""}`, maxSnapshotId(db), () => derivadas(db, muns, at))
    .filter(
      (a) =>
        (tipo === undefined || a.tipo === tipo) &&
        (GRAU[a.severidade] ?? 0) >= grauMin &&
        (uf === undefined || a.uf === uf) &&
        (desde === undefined || a.at >= desde),
    );
  return [...gravadas, ...extra].sort((x, y) => (x.at < y.at ? 1 : x.at > y.at ? -1 : y.id - x.id)).slice(0, limit);
}
