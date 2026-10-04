// /api/mapa: uma consulta das unidades (última versão até `at`) e uma dos mais votados.
import type { Database } from "bun:sqlite";
import { maxSnapshotId } from "../db/leitura.ts";
import type { Nivel } from "../types.ts";
import { UFS, parseAbr, titulo } from "./abr.ts";
import { CacheCurto } from "./cache.ts";
import type { CandMapaRow, FiltroUnidades } from "./consultas.ts";
import { candidatosMapa, municipiosIndex, unidadesMapa } from "./consultas.ts";
import type { Campo, Contexto } from "./contexto.ts";
import { ErroHttp } from "./http.ts";
import type { Params } from "./http.ts";

export interface CandMapa {
  sqcand: string;
  n: string;
  nmu: string;
  sg: string;
  campo: Campo;
  vap: number;
  pvapn: number;
}

export interface UnidadeOut {
  cd: string;
  cdi?: string;
  nm: string;
  te?: number;
  pst: number;
  tf: boolean;
  snapshot_id: number | null;
  lider?: CandMapa;
  segundo?: CandMapa;
  margem?: number;
  top?: CandMapa[];
}

const cache = new CacheCurto<unknown>(5000, 128);

function filtro(ele: number, cargo: number, nivel: string, pai: string | undefined): FiltroUnidades {
  const tipos: Record<string, Nivel> = { uf: "uf", mun: "mu", zona: "zona" };
  const n = tipos[nivel];
  if (!n) throw new ErroHttp(400, "nivel precisa ser uf, mun ou zona");
  if (n === "uf") return { ele, cargo, nivel: n };
  if (pai === undefined) throw new ErroHttp(400, `parâmetro pai obrigatório no nível ${nivel}`);
  const a = parseAbr(pai);
  if (n === "mu") {
    if (a.nivel !== "uf" || a.uf === null) throw new ErroHttp(400, "pai do nível mun é uma UF (ex.: sp)");
    return { ele, cargo, nivel: n, uf: a.uf };
  }
  if (a.nivel !== "mu" || a.uf === null || a.mun === null) throw new ErroHttp(400, "pai do nível zona é um município (ex.: sp71072)");
  return { ele, cargo, nivel: n, uf: a.uf, mun: a.mun };
}

function candMapa(ctx: Contexto, r: CandMapaRow): CandMapa {
  return {
    sqcand: String(r.sqcand),
    n: r.numero === null ? "" : String(r.numero),
    nmu: r.nome_urna ?? "",
    sg: r.sigla ?? "",
    campo: ctx.campos.campo(r.sigla, r.fed_sigla),
    vap: r.vap ?? 0,
    pvapn: r.pvapn ?? 0,
  };
}

export function calcularMapa(ctx: Contexto, db: Database, f: FiltroUnidades, topMax: number, at?: string): UnidadeOut[] {
  const unidades = unidadesMapa(db, f, at);
  const vagas = Math.max(1, ...unidades.map((u) => u.vagas ?? 1));
  const top = Math.max(2, Math.min(vagas, topMax));
  const porArquivo = new Map<number, CandMapaRow[]>();
  for (const r of candidatosMapa(db, f, top, at)) {
    const l = porArquivo.get(r.arquivo_id);
    if (l) l.push(r);
    else porArquivo.set(r.arquivo_id, [r]);
  }
  const muns = f.nivel === "mu" ? municipiosIndex(db) : null;
  return unidades.map((u) => {
    let cd: string;
    let nm: string;
    let cdi: string | null = null;
    if (f.nivel === "uf") {
      cd = u.uf ?? "";
      nm = UFS[cd]?.nome ?? cd.toUpperCase();
      cdi = UFS[cd]?.cdi ?? null;
    } else if (f.nivel === "mu") {
      cd = u.municipio_cd ?? "";
      const m = muns?.get(cd);
      nm = titulo(m?.nome ?? cd);
      cdi = m?.ibge ?? null;
    } else {
      cd = u.zona_cd ?? "";
      nm = `Zona ${Number(cd)}`;
    }
    const out: UnidadeOut = { cd, nm, pst: u.pst ?? 0, tf: u.tf === 1, snapshot_id: u.sid };
    if (cdi) out.cdi = cdi;
    if (u.te !== null) out.te = u.te;
    const cands = (porArquivo.get(u.arquivo_id) ?? []).map((r) => candMapa(ctx, r));
    const [l1, l2] = cands;
    if (l1 && l1.vap > 0) {
      out.lider = l1;
      if (l2) {
        out.segundo = l2;
        out.margem = Math.round((l1.pvapn - l2.pvapn) * 1000) / 1000;
      }
      if (vagas > 1) out.top = cands.slice(0, Math.min(vagas, topMax));
    }
    return out;
  });
}

export function mapa(ctx: Contexto, db: Database, p: Params): unknown {
  const ele = p.exigirInt("ele");
  const cargo = p.exigirInt("cargo");
  const nivel = p.exigirTexto("nivel");
  const pai = p.texto("pai");
  const f = filtro(ele, cargo, nivel, pai);
  const at = p.at();
  const topMax = p.limite("top", 10, 100);
  const chave = [db.filename, ele, cargo, f.nivel, f.uf ?? "", f.mun ?? "", topMax, at ?? ""].join("|");
  const unidades = cache.obter(chave, maxSnapshotId(db), () => calcularMapa(ctx, db, f, topMax, at));
  return { nivel, pai: pai ?? "br", gerado_em: ctx.agora(), unidades };
}

export function limparCacheMapa(): void {
  cache.limpar();
}
