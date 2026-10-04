// Normalização pura: esquema leniente do TSE → linhas do SQLite. Sem I/O.
import { CARGOS_MAJORITARIOS, PLEITO } from "../config.ts";
import type {
  LinhaAbEstado, LinhaCandidato, LinhaCargo, LinhaEEntrada, LinhaEleicao, LinhaFederacao,
  LinhaMunicipio, LinhaPartido, LinhaSnapshotMeta, LinhaTotais, LinhaUf, LinhaVotoAgremiacao,
  LinhaVotoCandidato, LinhaVotoPartido, LinhaZona,
} from "../db/linhas.ts";
import { dgHgToUtcIso } from "../tse/time.ts";
import type { Nivel } from "../types.ts";
import { intBR, pctN, simNao01, texto } from "./numeros.ts";
import type { AbEntrada, AbFile, EFile, EleC, MunCm, ResultadoU } from "./schemas.ts";

type Txt = string | undefined;

/** Metadados de cabeçalho (dg/hg/idg + dt/ht quando houver). */
export function metaDe(o: { dg?: Txt; hg?: Txt; idg?: Txt; dt?: Txt; ht?: Txt; tf?: Txt; and?: Txt; dv?: Txt; t?: Txt }): LinhaSnapshotMeta {
  return {
    dg: texto(o.dg),
    hg: texto(o.hg),
    idg: intBR(o.idg),
    gerado_em: dgHgToUtcIso(o.dg, o.hg),
    dt: texto(o.dt),
    ht: texto(o.ht),
    totalizado_em: dgHgToUtcIso(o.dt, o.ht),
    tf: simNao01(o.tf),
    andamento: texto(o.and),
    divulgacao: texto(o.dv),
    turno: intBR(o.t),
  };
}

// ---------------------------------------------------------------- resultado -u

export type PoliticaCandidatos = "sempre" | "primeiro_e_final";

/** voto_candidato sempre em br/uf e nos majoritários; proporcionais em mu/zona só no primeiro e no final. */
export function politicaPara(cargo: number, nivel: Nivel): PoliticaCandidatos {
  if (nivel === "br" || nivel === "uf" || CARGOS_MAJORITARIOS.has(cargo)) return "sempre";
  return "primeiro_e_final";
}

export interface CtxU {
  uf: string | null;
  politicaCandidatos: PoliticaCandidatos;
  /** primeiro snapshot deste arquivo */
  primeiro: boolean;
  /** força candidatos (snapshot marcado com anomalia) */
  forcarCandidatos?: boolean;
}

export interface NormalizadoU {
  snapshotMeta: LinhaSnapshotMeta;
  ele: number | null;
  cargo: number | null;
  tpabr: string | null;
  cdabr: string | null;
  /** tf = s ou pst = 100 */
  final: boolean;
  incluiuCandidatos: boolean;
  totais: LinhaTotais;
  votoCandidato: LinhaVotoCandidato[];
  votoPartido: LinhaVotoPartido[];
  votoAgremiacao: LinhaVotoAgremiacao[];
  candidatos: LinhaCandidato[];
  partidos: LinhaPartido[];
  federacoes: LinhaFederacao[];
}

export function normalizarU(p: ResultadoU, ctx: CtxU): NormalizadoU {
  const s = p.s ?? {};
  const e = p.e ?? {};
  const v = p.v ?? {};
  const cargo0 = p.carg[0];
  const totais: LinhaTotais = {
    vagas: intBR(cargo0?.nv),
    ts: intBR(s.ts), st: intBR(s.st), snt: intBR(s.snt), si: intBR(s.si), sni: intBR(s.sni),
    sa: intBR(s.sa), sna: intBR(s.sna), pst: pctN(s.pstn, s.pst),
    te: intBR(e.te), est: intBR(e.est), esnt: intBR(e.esnt), esi: intBR(e.esi), esni: intBR(e.esni),
    esa: intBR(e.esa), esna: intBR(e.esna),
    comparecimento: intBR(e.c), abstencao: intBR(e.a), pc: pctN(e.pcn, e.pc), pa: pctN(e.pan, e.pa),
    tv: intBR(v.tv), vvc: intBR(v.vvc), vv: intBR(v.vv), vnom: intBR(v.vnom), vl: intBR(v.vl),
    van: intBR(v.van), vansj: intBR(v.vansj), vb: intBR(v.vb), tvn: intBR(v.tvn), vn: intBR(v.vn),
    vnt: intBR(v.vnt), vsan: intBR(v.vsan), vscv: intBR(v.vscv),
    pvvc: pctN(v.pvvcn, v.pvvc), pvb: pctN(v.pvbn, v.pvb), ptvn: pctN(v.ptvnn, v.ptvn),
    pvan: pctN(v.pvann, v.pvan), pvn: pctN(v.pvnn, v.pvn),
  };
  const meta = metaDe(p);
  const final = meta.tf === 1 || totais.pst === 100;
  const incluir =
    ctx.politicaCandidatos === "sempre" || ctx.primeiro || final || ctx.forcarCandidatos === true;
  const ele = intBR(p.ele);

  const out: NormalizadoU = {
    snapshotMeta: meta,
    ele,
    cargo: intBR(cargo0?.cd),
    tpabr: texto(p.tpabr),
    cdabr: texto(p.cdabr),
    final,
    incluiuCandidatos: incluir,
    totais,
    votoCandidato: [],
    votoPartido: [],
    votoAgremiacao: [],
    candidatos: [],
    partidos: [],
    federacoes: [],
  };
  const partidosVistos = new Set<number>();

  for (const carg of p.carg) {
    const cargoCd = intBR(carg.cd);
    for (const f of carg.fed ?? []) {
      const n = intBR(f.n);
      if (n === null) continue;
      const npar = (f.npar ?? []).map((x) => intBR(x)).filter((x): x is number => x !== null);
      out.federacoes.push({ n, sigla: texto(f.sg), nome: texto(f.nm), composicao: texto(f.com), partidos: JSON.stringify(npar) });
    }
    for (const agr of carg.agr ?? []) {
      const agrN = intBR(agr.n);
      if (agrN === null) continue;
      out.votoAgremiacao.push({
        agremiacao_n: agrN, tp: texto(agr.tp), nome: texto(agr.nm), composicao: texto(agr.com),
        tvtn: intBR(agr.tvtn), tvtl: intBR(agr.tvtl), tval: intBR(agr.tval), tvan: intBR(agr.tvan), vagas: intBR(agr.vag),
      });
      for (const par of agr.par ?? []) {
        const parN = intBR(par.n);
        if (parN === null) continue;
        const fedN = intBR(par.nfed);
        out.votoPartido.push({
          partido_n: parN, agremiacao_n: agrN,
          tvtn: intBR(par.tvtn), tvtl: intBR(par.tvtl), tval: intBR(par.tval), tvan: intBR(par.tvan), dvt: texto(par.dvt),
        });
        if (!partidosVistos.has(parN)) {
          partidosVistos.add(parN);
          out.partidos.push({ n: parN, sigla: texto(par.sg), nome: texto(par.nm), federacao_n: fedN });
        }
        if (!incluir) continue;
        for (const c of par.cand ?? []) {
          const sq = intBR(c.sqcand);
          if (sq === null) continue;
          out.votoCandidato.push({
            sqcand: sq, vap: intBR(c.vap), pvapn: pctN(c.pvapn, c.pvap), eleito: simNao01(c.e), st: texto(c.st), dvt: texto(c.dvt),
          });
          if (ele !== null && cargoCd !== null) {
            out.candidatos.push({
              sqcand: sq, eleicao_cd: ele, cargo_cd: cargoCd, uf: ctx.uf, numero: intBR(c.n), nome: texto(c.nm),
              nome_urna: texto(c.nmu), nascimento: texto(c.dt), partido_n: parN, federacao_n: fedN, agremiacao_n: agrN,
              vices: c.vs && c.vs.length > 0
                ? JSON.stringify(c.vs.map((x) => ({ tp: x.tp ?? null, sqcand: x.sqcand ?? null, nm: x.nm ?? null, nmu: x.nmu ?? null, sgp: x.sgp ?? null })))
                : null,
            });
          }
        }
      }
    }
  }
  return out;
}

// ---------------------------------------------------------------- monitoramento -ab

export const fingerprintAb = (a: AbEntrada): string =>
  [a.dt ?? "", a.ht ?? "", a.s?.st ?? "", a.e?.est ?? "", a.s?.pst ?? ""].join("|");

export interface MudancaAb {
  tpabr: string;
  cdabr: string;
  anterior: string | null;
  atual: string;
  /** st == ts && ts > 0 */
  final: boolean;
}

export interface NormalizadoAb {
  snapshotMeta: LinhaSnapshotMeta;
  ele: number | null;
  /** nenhum fingerprint anterior: todas as entradas entram */
  primeiro: boolean;
  entradas: LinhaAbEstado[];
  mudancas: MudancaAb[];
  fingerprints: Map<string, string>;
}

export function linhaAb(a: AbEntrada): LinhaAbEstado {
  const s = a.s ?? {};
  const e = a.e ?? {};
  return {
    tpabr: a.tpabr ?? "", cdabr: a.cdabr ?? "", andamento: texto(a.and), dt: texto(a.dt), ht: texto(a.ht),
    totalizado_em: dgHgToUtcIso(a.dt, a.ht),
    ts: intBR(s.ts), st: intBR(s.st), pst: pctN(s.pstn, s.pst), snt: intBR(s.snt), si: intBR(s.si),
    sni: intBR(s.sni), sa: intBR(s.sa), sna: intBR(s.sna),
    te: intBR(e.te), est: intBR(e.est), esnt: intBR(e.esnt), esi: intBR(e.esi), esni: intBR(e.esni),
    esa: intBR(e.esa), esna: intBR(e.esna), comparecimento: intBR(e.c), abstencao: intBR(e.a),
    munnr: intBR(a.munnr), munpt: intBR(a.munpt), munf: intBR(a.munf),
    ufsnr: intBR(a.ufsnr), ufspt: intBR(a.ufspt), ufsf: intBR(a.ufsf),
  };
}

/** Diff do -ab contra os fingerprints anteriores (chave = cdabr). */
export function normalizarAb(p: AbFile, fingerprintsAnteriores: ReadonlyMap<string, string>): NormalizadoAb {
  const primeiro = fingerprintsAnteriores.size === 0;
  const entradas: LinhaAbEstado[] = [];
  const mudancas: MudancaAb[] = [];
  const fingerprints = new Map<string, string>();
  for (const a of p.abr) {
    const cd = a.cdabr;
    if (!cd) continue;
    const fp = fingerprintAb(a);
    fingerprints.set(cd, fp);
    const anterior = fingerprintsAnteriores.get(cd) ?? null;
    if (!primeiro && anterior === fp) continue;
    const linha = linhaAb(a);
    entradas.push(linha);
    const ts = linha.ts ?? 0;
    mudancas.push({ tpabr: linha.tpabr, cdabr: cd, anterior, atual: fp, final: ts > 0 && linha.st === ts });
  }
  return { snapshotMeta: metaDe(p), ele: intBR(p.ele), primeiro, entradas, mudancas, fingerprints };
}

// ---------------------------------------------------------------- configuração

export interface NormalizadoEleC {
  snapshotMeta: LinhaSnapshotMeta;
  eleicoes: LinhaEleicao[];
  cargos: LinhaCargo[];
}

export function normalizarEleC(p: EleC, pleito: number = PLEITO): NormalizadoEleC {
  const eleicoes: LinhaEleicao[] = [];
  const cargos: LinhaCargo[] = [];
  for (const pl of p.pl) {
    if (intBR(pl.cd) !== pleito) continue;
    for (const el of pl.e ?? []) {
      const cd = intBR(el.cd);
      if (cd === null) continue;
      eleicoes.push({
        cd, cdt2: intBR(el.cdt2), nome: texto(el.nm), turno: intBR(el.t), tipo: texto(el.tp),
        pleito, ciclo: texto(pl.c), data: texto(pl.dt),
      });
      const vistos = new Set<number>();
      for (const abr of el.abr ?? []) {
        for (const cp of abr.cp ?? []) {
          const ccd = intBR(cp.cd);
          if (ccd === null || vistos.has(ccd)) continue;
          vistos.add(ccd);
          cargos.push({ eleicao_cd: cd, cd: ccd, nome: texto(cp.ds), tp: texto(cp.tp), proporcional: cp.tp === "2" ? 1 : 0 });
        }
      }
    }
  }
  return { snapshotMeta: metaDe(p), eleicoes, cargos };
}

export interface NormalizadoCm {
  snapshotMeta: LinhaSnapshotMeta;
  ufs: LinhaUf[];
  municipios: LinhaMunicipio[];
  zonas: LinhaZona[];
}

export function normalizarCm(p: MunCm): NormalizadoCm {
  const ufs: LinhaUf[] = [];
  const municipios: LinhaMunicipio[] = [];
  const zonas: LinhaZona[] = [];
  for (const abr of p.abr) {
    const uf = abr.cd.toLowerCase();
    ufs.push({ sigla: uf, nome: texto(abr.ds) });
    for (const mu of abr.mu) {
      municipios.push({ cd: mu.cd, uf, ibge: texto(mu.cdi), nome: texto(mu.nm), capital: simNao01(mu.c), eleitores: null, origem: "cm" });
      for (const z of mu.z) zonas.push({ municipio_cd: mu.cd, cd: z, uf });
    }
  }
  return { snapshotMeta: metaDe(p), ufs, municipios, zonas };
}

export interface NormalizadoE {
  snapshotMeta: LinhaSnapshotMeta;
  ele: number | null;
  cargo: number | null;
  uf: string | null;
  entradas: LinhaEEntrada[];
}

export function normalizarE(p: EFile): NormalizadoE {
  const entradas: LinhaEEntrada[] = [];
  for (const a of p.abr) {
    if (!a.cdabr) continue;
    const cand = (a.cand ?? []).map((c) => ({ sqcand: intBR(c.sqcand), n: intBR(c.n), vap: intBR(c.vap) }));
    entradas.push({
      tpabr: texto(a.tpabr), cdabr: a.cdabr, nome: texto(a.nmabr), dt: texto(a.dt), ht: texto(a.ht),
      totalizado_em: dgHgToUtcIso(a.dt, a.ht), tvap: intBR(a.tvap), cand: JSON.stringify(cand),
    });
  }
  return { snapshotMeta: metaDe(p), ele: intBR(p.ele), cargo: intBR(p.cdcar), uf: texto(p.cdabr), entradas };
}
