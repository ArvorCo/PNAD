// Endpoints de auditoria: versões de um arquivo, latências, municípios fechados, velocidade,
// andamento do -ab, log de requisições e corpo original.
import type { Database } from "bun:sqlite";
import { chave, keyAb, parseChave } from "../tse/urls.ts";
import { gunzipTexto } from "../db/itens.ts";
import { arquivoPorChave, blobDoSnapshot, serieDoArquivo, ultimoSnapshotPorChave } from "../db/leitura.ts";
import type { Nivel } from "../types.ts";
import { abrTexto, chaveU, nomeUf, parseAbr, titulo } from "./abr.ts";
import { FIM, abAsOf, municipiosIndex } from "./consultas.ts";
import type { Contexto } from "./contexto.ts";
import { ErroHttp } from "./http.ts";
import type { Params } from "./http.ts";
import { nomeEscopoEvento } from "./textos.ts";

const r2 = (v: number | null): number | null => (v === null ? null : Math.round(v * 100) / 100);

function arquivoU(db: Database, p: Params): { id: number; uf: string | null; abr: string } {
  const a = parseAbr(p.exigirTexto("abr"));
  const arq = arquivoPorChave(db, chaveU(p.exigirInt("ele"), p.exigirInt("cargo"), a));
  if (!arq) throw new ErroHttp(404, `arquivo desconhecido: ${abrTexto(a)}`);
  return { id: arq.id, uf: a.uf, abr: abrTexto(a) };
}

/** Versões de um arquivo com latências e deltas (mesmas fórmulas de v_snapshot_delta, filtradas pelo arquivo). */
export function snapshots(_ctx: Contexto, db: Database, p: Params): unknown {
  const arq = arquivoU(db, p);
  const limit = p.limite("limit", 200, 5000);
  const antes = p.int("antes") ?? Number.MAX_SAFE_INTEGER;
  const rows = db
    .query<Record<string, string | number | null>, [number, string, number, number]>(
      `SELECT * FROM (
         SELECT s.id AS snapshot_id, s.capturado_em, s.gerado_em, s.totalizado_em, s.idg, s.regressivo, s.tf, s.sha256,
                (julianday(s.capturado_em) - julianday(s.gerado_em)) * 86400.0 AS latencia_captura_s,
                (julianday(s.gerado_em) - julianday(s.totalizado_em)) * 86400.0 AS latencia_geracao_s,
                (julianday(s.gerado_em) - julianday(LAG(s.gerado_em) OVER w)) * 86400.0 AS intervalo_geracao_s,
                t.st, t.ts, t.pst, t.vvc, t.tv, t.comparecimento,
                t.st - LAG(t.st) OVER w AS d_st, t.vvc - LAG(t.vvc) OVER w AS d_vvc, t.tv - LAG(t.tv) OVER w AS d_tv,
                t.pst - LAG(t.pst) OVER w AS d_pst, t.comparecimento - LAG(t.comparecimento) OVER w AS d_comparecimento
         FROM snapshot s LEFT JOIN totais t ON t.snapshot_id = s.id
         WHERE s.arquivo_id = ?
         WINDOW w AS (ORDER BY s.id)
       ) WHERE capturado_em <= ? AND snapshot_id < ? ORDER BY snapshot_id DESC LIMIT ?`,
    )
    .all(arq.id, p.at() ?? FIM, antes, limit);
  for (const r of rows) {
    for (const k of ["latencia_captura_s", "latencia_geracao_s", "intervalo_geracao_s", "d_pst"]) {
      const v = r[k];
      if (typeof v === "number") r[k] = r2(v);
    }
  }
  return { abr: arq.abr, snapshots: rows };
}

function percentil(ordenado: readonly number[], q: number): number | null {
  if (ordenado.length === 0) return null;
  const i = Math.min(ordenado.length - 1, Math.max(0, Math.ceil(q * ordenado.length) - 1));
  return r2(ordenado[i] ?? null);
}

interface Resumo {
  n: number;
  p50: number | null;
  p95: number | null;
  max: number | null;
}

function resumo(v: number[]): Resumo {
  const o = [...v].sort((a, b) => a - b);
  return { n: o.length, p50: percentil(o, 0.5), p95: percentil(o, 0.95), max: r2(o.at(-1) ?? null) };
}

const NIVEIS: Readonly<Record<string, Nivel>> = { br: "br", uf: "uf", mu: "mu", mun: "mu", zona: "zona" };

export function latencia(_ctx: Contexto, db: Database, p: Params): unknown {
  const nivel = NIVEIS[p.exigirTexto("nivel")];
  if (!nivel) throw new ErroHttp(400, "nivel precisa ser br, uf, mun ou zona");
  const uf = p.texto("uf")?.toLowerCase();
  const params: (string | number)[] = [p.exigirInt("ele"), p.exigirInt("cargo"), nivel, p.at() ?? FIM];
  if (uf !== undefined) params.push(uf);
  const rows = db
    .query<{ uf: string | null; municipio_cd: string | null; zona_cd: string | null; lc: number | null; lg: number | null }, (string | number)[]>(
      `SELECT a.uf, a.municipio_cd, a.zona_cd,
              (julianday(s.capturado_em) - julianday(s.gerado_em)) * 86400.0 AS lc,
              (julianday(s.gerado_em) - julianday(s.totalizado_em)) * 86400.0 AS lg
       FROM arquivo a JOIN snapshot s ON s.arquivo_id = a.id
       WHERE a.tipo = 'u' AND a.eleicao_cd = ? AND a.cargo_cd = ? AND a.nivel = ? AND s.regressivo = 0
         AND s.gerado_em IS NOT NULL AND s.capturado_em <= ? ${uf !== undefined ? "AND a.uf = ?" : ""}`,
    )
    .all(...params);
  const muns = municipiosIndex(db);
  const grupos = new Map<string, { nome: string; lc: number[]; lg: number[] }>();
  const todos = { lc: [] as number[], lg: [] as number[] };
  for (const r of rows) {
    const abr = abrTexto({ nivel, uf: r.uf, municipio_cd: r.municipio_cd, zona_cd: r.zona_cd });
    let g = grupos.get(abr);
    if (!g) {
      g = { nome: nomeEscopoEvento({ nivel, uf: r.uf, municipio_cd: r.municipio_cd, zona_cd: r.zona_cd, cargo_cd: null }, muns), lc: [], lg: [] };
      grupos.set(abr, g);
    }
    if (r.lc !== null) {
      g.lc.push(r.lc);
      todos.lc.push(r.lc);
    }
    if (r.lg !== null) {
      g.lg.push(r.lg);
      todos.lg.push(r.lg);
    }
  }
  const escopos = [...grupos.entries()].map(([abr, g]) => ({ abr, nome: g.nome, captura: resumo(g.lc), geracao: resumo(g.lg) }));
  return { nivel, escopos, geral: { captura: resumo(todos.lc), geracao: resumo(todos.lg) } };
}

export function fim(_ctx: Contexto, db: Database, p: Params): unknown {
  const ele = p.exigirInt("ele");
  const cargo = p.exigirInt("cargo");
  const uf = p.texto("uf")?.toLowerCase();
  const at = p.at() ?? FIM;
  const filtroUf = uf !== undefined ? "AND f.uf = ?" : "";
  const base: (string | number)[] = uf !== undefined ? [ele, cargo, at, uf] : [ele, cargo, at];
  const fechados = db
    .query<{ uf: string; cd: string; cdi: string | null; nome: string | null; snapshot_id: number; capturado_em: string; gerado_em: string | null; totalizado_em: string | null }, (string | number)[]>(
      `SELECT f.uf, f.municipio_cd AS cd, m.ibge AS cdi, m.nome, f.snapshot_id, f.capturado_em, f.gerado_em, f.totalizado_em
       FROM v_municipio_fim f LEFT JOIN municipio m ON m.cd = f.municipio_cd
       WHERE f.eleicao_cd = ? AND f.cargo_cd = ? AND f.capturado_em <= ? ${filtroUf}
       ORDER BY COALESCE(f.totalizado_em, f.capturado_em) DESC, f.snapshot_id DESC`,
    )
    .all(...base);
  const totalArqs = db
    .query<{ n: number }, (string | number)[]>(
      `SELECT COUNT(*) AS n FROM arquivo WHERE tipo = 'u' AND nivel = 'mu' AND eleicao_cd = ? AND cargo_cd = ? ${uf !== undefined ? "AND uf = ?" : ""}`,
    )
    .get(...(uf !== undefined ? [ele, cargo, uf] : [ele, cargo]))?.n ?? 0;
  const limit = p.limite("limit", 100, 10000);
  return {
    total_fechados: fechados.length,
    pendentes: Math.max(0, totalArqs - fechados.length),
    fechados: fechados.slice(0, limit).map(({ nome, ...f }) => ({ ...f, nm: titulo(nome ?? f.cd) })),
  };
}

export function velocidade(_ctx: Contexto, db: Database, p: Params): unknown {
  const arq = arquivoU(db, p);
  const janela = p.limite("janela_s", 600, 86_400, 10);
  const at = p.at();
  const pts = serieDoArquivo(db, arq.id)
    .filter((x) => at === undefined || x.capturado_em <= at)
    .map((x) => ({ t: Date.parse(x.gerado_em ?? x.capturado_em), st: x.st ?? 0, ts: x.ts ?? 0, pst: x.pst ?? 0, tv: x.tv ?? 0 }))
    .filter((x) => Number.isFinite(x.t));
  const vazio = { abr: arq.abr, janela_s: janela, de: null, ate: null, n_pontos: pts.length, secoes_por_min: null, votos_por_min: null, pst_por_min: null, eta_100: null };
  const ult = pts.at(-1);
  if (!ult) return vazio;
  const corte = ult.t - janela * 1000;
  const naJanela = pts.findIndex((x) => x.t >= corte);
  const base = naJanela >= 0 && naJanela < pts.length - 1 ? pts[naJanela] : pts.at(-2);
  if (!base || base.t >= ult.t) return { ...vazio, ate: new Date(ult.t).toISOString() };
  const min = (ult.t - base.t) / 60_000;
  const spm = (ult.st - base.st) / min;
  const eta = spm > 0 && ult.ts > ult.st ? new Date(ult.t + ((ult.ts - ult.st) / spm) * 60_000).toISOString() : null;
  return {
    abr: arq.abr, janela_s: janela, de: new Date(base.t).toISOString(), ate: new Date(ult.t).toISOString(), n_pontos: pts.length,
    secoes_por_min: r2(spm), votos_por_min: r2((ult.tv - base.tv) / min), pst_por_min: r2((ult.pst - base.pst) / min), eta_100: eta,
  };
}

export function andamento(_ctx: Contexto, db: Database, p: Params): unknown {
  const ele = p.exigirInt("ele");
  const uf = p.texto("uf")?.toLowerCase();
  const abr = uf ?? "br";
  const k = chave(keyAb(ele, abr));
  const arq = arquivoPorChave(db, k);
  if (!arq) throw new ErroHttp(404, `andamento desconhecido: ${abr}`);
  const at = p.at();
  const s = ultimoSnapshotPorChave(db, k, at);
  const muns = uf !== undefined ? municipiosIndex(db) : null;
  const entradas = abAsOf(db, arq.id, at).map((r) => ({
    tpabr: r.tpabr, cdabr: r.cdabr,
    nome: r.cdabr === "br" ? "Brasil" : muns ? titulo(muns.get(r.cdabr)?.nome ?? r.cdabr) : nomeUf(r.cdabr),
    andamento: r.andamento, dt_ht: r.totalizado_em, ts: r.ts ?? 0, st: r.st ?? 0, pst: r.pst ?? 0, te: r.te ?? 0, est: r.est ?? 0,
    comparecimento: r.comparecimento ?? 0, abstencao: r.abstencao ?? 0, munnr: r.munnr, munpt: r.munpt, munf: r.munf,
    snapshot_id: r.snapshot_id,
  }));
  return { ele, abr, snapshot_id: s?.snapshot_id ?? null, gerado_em: s?.gerado_em ?? null, lido_em: s?.capturado_em ?? null, entradas };
}

export function fetches(_ctx: Contexto, db: Database, p: Params): unknown {
  const ch = p.texto("chave");
  const limit = p.limite("limit", 100, 5000);
  const classe = p.texto("classe");
  const where: string[] = ["f.iniciado_em <= ?"];
  const params: (string | number)[] = [p.at() ?? FIM];
  if (ch !== undefined) {
    try {
      parseChave(ch);
    } catch {
      throw new ErroHttp(400, `chave inválida: ${ch}`);
    }
    const arq = arquivoPorChave(db, ch);
    if (!arq) throw new ErroHttp(404, `arquivo desconhecido: ${ch}`);
    where.push("f.arquivo_id = ?");
    params.push(arq.id);
  }
  if (classe !== undefined) {
    where.push("f.classe = ?");
    params.push(classe);
  }
  return db
    .query<Record<string, string | number | null>, (string | number)[]>(
      `SELECT f.*, a.chave FROM fetch f JOIN arquivo a ON a.id = f.arquivo_id WHERE ${where.join(" AND ")} ORDER BY f.id DESC LIMIT ?`,
    )
    .all(...params, limit);
}

export function blob(db: Database, id: number): Response {
  const gz = blobDoSnapshot(db, id);
  if (!gz) throw new ErroHttp(404, `snapshot ${id} sem corpo`);
  return new Response(gunzipTexto(gz), {
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });
}
