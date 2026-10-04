// /api/config e /api/estado.
import type { Database } from "bun:sqlite";
import { chave, keyAb, keyU } from "../tse/urls.ts";
import { arquivoPorChave, lerMeta, maxSnapshotId, ultimoSnapshotPorChave } from "../db/leitura.ts";
import { UFS, nomeUf, titulo } from "./abr.ts";
import { CacheCurto } from "./cache.ts";
import { FIM, abAsOf, fechamentosAb, ultimaLeitura, ultimoSnapshot } from "./consultas.ts";
import type { Contexto } from "./contexto.ts";
import type { Params } from "./http.ts";
import { somaSeDefasado } from "./nacional.ts";

const n0 = (v: number | null | undefined): number => v ?? 0;
const segundos = (a: string | null, b: string | null): number | null => {
  if (!a || !b) return null;
  const d = (Date.parse(a) - Date.parse(b)) / 1000;
  return Number.isFinite(d) ? Math.round(d * 10) / 10 : null;
};

export interface Eleicoes {
  turno: number;
  federal: number;
  estadual: number;
}

/** Turno pelo registro: arquivos de 6258/6260 indicam 2º turno. APURACAO_TURNO força. */
export function eleicoes(db: Database | null): Eleicoes {
  const forca = process.env.APURACAO_TURNO;
  let turno = forca === "2" ? 2 : 1;
  if (forca === undefined && db) {
    const r = db.query<{ x: number }, []>("SELECT 1 AS x FROM arquivo WHERE eleicao_cd IN (6258, 6260) LIMIT 1").get();
    if (r) turno = 2;
  }
  return turno === 2 ? { turno, federal: 6258, estadual: 6260 } : { turno, federal: 6257, estadual: 6259 };
}

const cacheConfig = new CacheCurto<unknown>(30_000, 4);

export function config(_ctx: Contexto, db: Database | null): unknown {
  const el = eleicoes(db);
  const base = { turno: el.turno, eleicoes: { federal: el.federal, estadual: el.estadual } };
  if (!db) return { ...base, ufs: [], municipios: {} };
  return cacheConfig.obter(db.filename, maxSnapshotId(db), () => {
    const teAb = new Map<string, number>();
    const abBr = arquivoPorChave(db, chave(keyAb(el.federal, "br")));
    if (abBr) for (const r of abAsOf(db, abBr.id)) if (r.te !== null) teAb.set(r.cdabr, r.te);
    const teMun = new Map<string, number>();
    const rowsTe = db
      .query<{ cdabr: string; te: number | null }, [number]>(
        "SELECT cdabr, te FROM v_ab_atual WHERE eleicao_cd = ? AND nivel = 'uf' AND tpabr <> 'uf'",
      )
      .all(el.federal);
    for (const r of rowsTe) if (r.te !== null) teMun.set(r.cdabr, r.te);
    const ufsDb = db.query<{ sigla: string; nome: string | null }, []>("SELECT sigla, nome FROM uf ORDER BY sigla").all();
    const ufs = ufsDb.map((u) => {
      const o: { uf: string; nome: string; cdi?: string; te: number } = { uf: u.sigla, nome: nomeUf(u.sigla), te: teAb.get(u.sigla) ?? 0 };
      const cdi = UFS[u.sigla]?.cdi;
      if (cdi) o.cdi = cdi;
      return o;
    });
    const zonas = new Map<string, string[]>();
    for (const z of db.query<{ municipio_cd: string; cd: string }, []>("SELECT municipio_cd, cd FROM zona ORDER BY municipio_cd, cd").all()) {
      const l = zonas.get(z.municipio_cd);
      if (l) l.push(z.cd);
      else zonas.set(z.municipio_cd, [z.cd]);
    }
    const municipios: Record<string, { cd: string; cdi: string; nm: string; c: boolean; z: string[]; te?: number }[]> = {};
    const muns = db
      .query<{ cd: string; uf: string; ibge: string | null; nome: string | null; capital: number | null }, []>(
        "SELECT cd, uf, ibge, nome, capital FROM municipio ORDER BY uf, nome",
      )
      .all();
    for (const m of muns) {
      const k = m.uf.toUpperCase();
      const o: { cd: string; cdi: string; nm: string; c: boolean; z: string[]; te?: number } = {
        cd: m.cd, cdi: m.ibge ?? "", nm: titulo(m.nome ?? m.cd), c: m.capital === 1, z: zonas.get(m.cd) ?? [],
      };
      const te = teMun.get(m.cd);
      if (te !== undefined) o.te = te;
      (municipios[k] ??= []).push(o);
    }
    return { ...base, ufs, municipios };
  });
}

interface UfEstado {
  uf: string;
  nome: string;
  pst: number;
  st: number;
  ts: number;
  te: number; // eleitorado da UF, inclusive "zz" (exterior)
  munnr: number;
  munpt: number;
  munf: number;
  dt_ht: string | null;
  fechou_em?: string;
}

interface PartePesada {
  ufs: UfEstado[];
  historico: { at: string; st: number; pst: number }[];
  latencias: { leitura_menos_hg: number[]; hg_menos_ht: number[] };
}

const cacheEstado = new CacheCurto<PartePesada>(1000, 16);

function coletor(db: Database): unknown {
  const bruto = lerMeta(db, "estado_coletor");
  if (bruto === null) return null;
  try {
    return JSON.parse(bruto) as unknown;
  } catch {
    return null;
  }
}

export function estado(ctx: Contexto, db: Database | null, p: Params): unknown {
  const at = p.at();
  const agora = at ?? ctx.agora();
  const el = eleicoes(db);
  const vazio = { leitura_menos_hg: [], hg_menos_ht: [] };
  if (!db) return { agora, pronto: false, turno: el.turno, coletor: null, db: null, ultimo_snapshot: null, br: null, ufs: [], historico: [], latencias: vazio };
  const ult = ultimoSnapshot(db, at);
  const maxFetch = db.query<{ m: number | null }, []>("SELECT MAX(id) AS m FROM fetch").get()?.m ?? 0;
  const warns = db.query<{ n: number }, []>("SELECT COUNT(*) AS n FROM evento WHERE severidade IN ('warn', 'error')").get()?.n ?? 0;
  const chavePres = chave(keyU(el.federal, 1, "br"));
  const pres = ultimoSnapshotPorChave(db, chavePres, at);
  const arqPres = arquivoPorChave(db, chavePres);
  const soma = pres ? somaSeDefasado(db, el.federal, 1, pres, at) : null;
  const br = pres
    ? soma
      ? {
          ts: soma.totais.ts, st: soma.totais.st, pst: soma.totais.pst, dt_ht: soma.dt_ht, hg: soma.dg_hg, lido_em: soma.lido_em,
          atraso_s: segundos(soma.lido_em, soma.dg_hg),
          ultima_leitura_em: arqPres ? ultimaLeitura(db, arqPres.id, at) : null,
          idade_s: segundos(agora, soma.dg_hg),
          fonte: "soma_ufs" as const,
          nacional_tse: soma.nacional_tse,
        }
      : {
          ts: n0(pres.ts), st: n0(pres.st), pst: n0(pres.pst), dt_ht: pres.totalizado_em, hg: pres.gerado_em, lido_em: pres.capturado_em,
          atraso_s: segundos(pres.capturado_em, pres.gerado_em),
          ultima_leitura_em: arqPres ? ultimaLeitura(db, arqPres.id, at) : null,
          idade_s: segundos(agora, pres.gerado_em),
          fonte: "tse" as const,
        }
    : null;
  const pesada = cacheEstado.obter(`${db.filename}|${at ?? ""}`, maxSnapshotId(db), () => partePesada(db, el, arqPres?.id ?? null, at));
  return {
    agora,
    pronto: ult !== null,
    turno: el.turno,
    coletor: coletor(db),
    db: { snapshots: maxSnapshotId(db), fetches: maxFetch, eventos_warn: warns, tamanho_mb: ctx.banco.tamanhoMb() },
    ultimo_snapshot: ult,
    br,
    ...pesada,
  };
}

function partePesada(db: Database, el: Eleicoes, arqPres: number | null, at?: string): PartePesada {
  const abBr = arquivoPorChave(db, chave(keyAb(el.federal, "br")));
  const ufs: UfEstado[] = [];
  if (abBr) {
    const fechou = fechamentosAb(db, abBr.id, at);
    for (const r of abAsOf(db, abBr.id, at)) {
      if (r.tpabr === "br" || r.cdabr === "br") continue;
      const o: UfEstado = {
        uf: r.cdabr, nome: nomeUf(r.cdabr), pst: n0(r.pst), st: n0(r.st), ts: n0(r.ts), te: n0(r.te), munnr: n0(r.munnr), munpt: n0(r.munpt), munf: n0(r.munf),
        dt_ht: r.totalizado_em,
      };
      const f = fechou.get(r.cdabr);
      if (f) o.fechou_em = f;
      ufs.push(o);
    }
  }
  const historico = arqPres !== null
    ? db
        .query<{ at: string; st: number | null; pst: number | null }, [number, string]>(
          `SELECT COALESCE(s.gerado_em, s.capturado_em) AS at, t.st, t.pst FROM snapshot s LEFT JOIN totais t ON t.snapshot_id = s.id
           WHERE s.arquivo_id = ? AND s.regressivo = 0 AND s.capturado_em <= ? ORDER BY s.id`,
        )
        .all(arqPres, at ?? FIM)
        .map((h) => ({ at: h.at, st: n0(h.st), pst: n0(h.pst) }))
    : [];
  const lat = db
    .query<{ lh: number | null; hh: number | null }, [string]>(
      `SELECT (julianday(capturado_em) - julianday(gerado_em)) * 86400.0 AS lh,
              (julianday(gerado_em) - julianday(totalizado_em)) * 86400.0 AS hh
       FROM snapshot WHERE capturado_em <= ? AND gerado_em IS NOT NULL AND regressivo = 0
       ORDER BY capturado_em DESC, id DESC LIMIT 500`,
    )
    .all(at ?? FIM);
  const r1 = (v: number): number => Math.round(v * 10) / 10;
  return {
    ufs,
    historico,
    latencias: {
      leitura_menos_hg: lat.flatMap((l) => (l.lh === null ? [] : [r1(l.lh)])),
      hg_menos_ht: lat.flatMap((l) => (l.hh === null ? [] : [r1(l.hh)])),
    },
  };
}
