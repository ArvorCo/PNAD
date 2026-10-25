// /api/2t/comparecimento: vigilância de falso comparecimento nas seções recebidas no 2º turno
// (amostra e totalização paralela) contra a própria seção no 1º turno, mais a camada municipal
// (arquivos mu com ao menos 30% das seções apuradas). Só leitura de secao_2t e dos totais.
// Sinal pede explicação, não prova irregularidade: a extensão até 19h eleva o comparecimento
// legitimamente. Contrato em ./comparecimento-tipos.ts.
import type { Database } from "bun:sqlite";
import type { Municipio } from "../server/indicadores/municipios.ts";
import { hhmmDeMinutos, minutosDesde17h, percentil } from "../turno2/comum.ts";
import type { Referencia1T, RefSecoes1T } from "../turno2/referencia.ts";
import { secaoRef1T } from "../turno2/referencia.ts";
import type { BuComparavel } from "./boletim.ts";
import type {
  BlocoProrrogacao,
  ComparecimentoOut,
  ContagemSinais,
  Distribuicao,
  MunicipioComparecimento,
  PontoSecao,
  SecaoComparecimento,
} from "./comparecimento-tipos.ts";
import { REGRAS_COMPARECIMENTO as R, ROTULO_COMPARECIMENTO } from "./comparecimento-tipos.ts";
import { tabelaExiste } from "./resumo.ts";

/** números de urna de Flávio (PL) e Lula (PT) no 2º turno presidencial */
const FLAVIO = "22";
const LULA = "13";
const N_MIN_PRORROGACAO = 20;

interface Linha {
  uf: string;
  mun: string;
  zona: number;
  secao: number;
  origem: "amostra" | "paralela";
  encerramento_iso: string | null;
  recebido_iso: string | null;
  bu_sha256: string | null;
  aptos: number | null;
  comparecimento: number | null;
  votos_json: string | null;
  comp_sem_biometria: number | null;
  hab_ano_nascimento: number | null;
  tipo_arquivo: number | null;
  tipo_urna: number | null;
  n_cargas: number | null;
}

export interface OpcoesComparecimento {
  at: string | undefined;
  agora: string;
  t0Ms: number;
  eleFederal: number;
  refSecoes: RefSecoes1T | null;
  ref1t: Referencia1T | null;
  /** estado dos municípios (arquivos mu de presidente) até `at` */
  municipios: readonly Municipio[];
  nome: (cd: string) => string | null;
}

const r2 = (x: number): number => Math.round(x * 100) / 100;
const pct = (num: number | null, den: number | null): number | null => (num === null || den === null || den <= 0 ? null : r2((100 * num) / den));

function distribuicao(v: readonly (number | null)[]): Distribuicao {
  const o = v.filter((x): x is number => x !== null && Number.isFinite(x)).sort((a, b) => a - b);
  const p = (q: number): number | null => {
    const x = percentil(o, q);
    return x === null ? null : r2(x);
  };
  return { n: o.length, p50: p(50), p90: p(90) };
}

/** [Flávio, Lula] do presidente no BU do 2T. */
function votosFL(json: string | null, ele: number): [number, number] | null {
  if (json === null) return null;
  try {
    const b = JSON.parse(json) as BuComparavel;
    const c = b.eleicoes[String(ele)]?.cargos["1"];
    if (!c) return null;
    return [c.nominais[FLAVIO] ?? 0, c.nominais[LULA] ?? 0];
  } catch {
    return null;
  }
}

const COLS_NOVAS = ["comp_sem_biometria", "hab_ano_nascimento", "tipo_arquivo", "tipo_urna", "n_cargas"] as const;

function lerLinhas(db: Database): Linha[] {
  if (!tabelaExiste(db, "secao_2t")) return [];
  const tem = new Set(db.query<{ name: string }, []>("PRAGMA table_info(secao_2t)").all().map((c) => c.name));
  // banco anterior à migração das colunas do detalhamento: lê NULL no lugar
  const extra = COLS_NOVAS.map((c) => (tem.has(c) ? c : `NULL AS ${c}`)).join(", ");
  return db
    .query<Linha, []>(
      `SELECT uf, mun, zona, secao, origem, encerramento_iso, recebido_iso, bu_sha256, aptos, comparecimento, votos_json, ${extra}
       FROM secao_2t WHERE bu_sha256 IS NOT NULL`,
    )
    .all();
}

interface Avaliada {
  s: SecaoComparecimento;
  fl: [number, number] | null;
  fl1: [number, number] | null;
  encMin: number | null;
}

function avaliar(l: Linha, o: OpcoesComparecimento): Avaliada {
  const ref = o.refSecoes === null ? null : secaoRef1T(o.refSecoes, l.uf, l.mun, l.zona, l.secao);
  const refMun = o.refSecoes?.municipios[l.uf.toLowerCase()]?.[l.mun] ?? null;
  const taxa = pct(l.comparecimento, l.aptos);
  const taxa1 = ref === null ? null : pct(ref.comp1, ref.aptos1);
  const delta = taxa !== null && taxa1 !== null ? r2(taxa - taxa1) : null;
  const semBio = pct(l.comp_sem_biometria, l.comparecimento);
  const semBio1 = ref === null ? null : pct(ref.sem_bio1, ref.comp1);
  const semBioMun = refMun?.sem_bio_p50 ?? null;
  const encMin = l.uf === "zz" || l.encerramento_iso === null ? null : minutosDesde17h(l.encerramento_iso, o.t0Ms);
  const recMin = l.recebido_iso === null ? null : minutosDesde17h(l.recebido_iso, o.t0Ms);
  // hora no minuto, como exibida (17:00:40 é 17:00, não conta como depois de 17:00)
  const encHm = encMin === null ? null : Math.floor(encMin);
  const tarde = encHm !== null && encHm >= 1;
  const apos19 = encHm !== null && encHm >= 121;
  const enc1 = ref?.enc1_min ?? null;
  const tardia = encMin !== null && (apos19 || (enc1 !== null && encMin - enc1 >= R.tardia_min_vs_1t));
  const papel = l.tipo_arquivo !== null && l.tipo_arquivo >= R.papel_tipo_min;
  const contingencia = (l.tipo_urna !== null && [3, 4, 6].includes(l.tipo_urna)) || (l.n_cargas !== null && l.n_cargas > 1);
  const fl = votosFL(l.votos_json, o.eleFederal);
  const fl1: [number, number] | null = ref !== null && ref.fl1 !== null && ref.lu1 !== null ? [ref.fl1, ref.lu1] : null;
  const fatia = fl === null ? null : pct(fl[0], fl[0] + fl[1]);
  const fatia1 = fl1 === null ? null : pct(fl1[0], fl1[0] + fl1[1]);
  const sinais = {
    delta: delta !== null && delta >= R.delta_pp_min,
    sem_bio: semBio !== null && semBio >= R.sem_bio_min_pct && semBioMun !== null && semBio >= R.sem_bio_fator * semBioMun,
    tardia,
    papel,
  };
  return {
    s: {
      uf: l.uf.toUpperCase(), mun: l.mun, nm: o.nome(l.mun) ?? l.mun, zona: l.zona, secao: l.secao, lat: ref?.lat ?? null, lon: ref?.lon ?? null,
      aptos: l.aptos, comp: l.comparecimento, taxa_comp: taxa, taxa_comp_1t: taxa1, delta_pp: delta, sem_bio_pct: semBio, sem_bio_pct_1t: semBio1,
      sem_bio_mun_p50_1t: semBioMun, ano_nasc_pct: pct(l.hab_ano_nascimento, l.comparecimento),
      encerramento_hhmm: encMin === null ? null : hhmmDeMinutos(Math.floor(encMin)), enc1_hhmm: enc1 === null ? null : hhmmDeMinutos(Math.floor(enc1)),
      tardia, encerrou_apos_17h: tarde, apos_19h: apos19, papel,
      tipo_arquivo: l.tipo_arquivo, tipo_urna: l.tipo_urna, n_cargas: l.n_cargas, contingencia, fatia_flavio: fatia, fatia_flavio_1t: fatia1,
      recebido_hhmm: recMin === null ? null : hhmmDeMinutos(Math.floor(recMin)), origem: l.origem, sinais,
      escore: Number(sinais.delta) + Number(sinais.sem_bio) + Number(sinais.tardia) + Number(sinais.papel),
    },
    fl,
    fl1,
    encMin,
  };
}

function contar(l: readonly SecaoComparecimento[]): ContagemSinais {
  return {
    delta: l.filter((s) => s.sinais.delta).length,
    sem_bio: l.filter((s) => s.sinais.sem_bio).length,
    tarde: l.filter((s) => s.encerrou_apos_17h).length,
    tardia: l.filter((s) => s.tardia).length,
    apos_19h: l.filter((s) => s.apos_19h).length,
    papel: l.filter((s) => s.sinais.papel).length,
    contingencia: l.filter((s) => s.contingencia).length,
    escore_2_mais: l.filter((s) => s.escore >= 2).length,
  };
}

const media = (v: readonly (number | null)[]): number | null => {
  const o = v.filter((x): x is number => x !== null);
  return o.length === 0 ? null : r2(o.reduce((a, b) => a + b, 0) / o.length);
};

/** Tardias (≥ 30 min depois do encerramento da própria seção no 1T, ou depois das 19:00) contra o 1T e contra as pontuais do município. */
export function blocoProrrogacao(uf: string, av: readonly Avaliada[], nMin = N_MIN_PRORROGACAO): BlocoProrrogacao {
  const comHora = av.filter((a) => a.encMin !== null);
  const tardias = comHora.filter((a) => a.s.tardia);
  const pontuais = comHora.filter((a) => !a.s.tardia);
  // 2T − 1T na própria seção, ponderado pelos votos dos dois no 2T
  let w1 = 0;
  let d1 = 0;
  let n1 = 0;
  for (const a of tardias) {
    if (a.fl === null || a.fl1 === null) continue;
    const v2 = a.fl[0] + a.fl[1];
    const v1 = a.fl1[0] + a.fl1[1];
    if (v2 <= 0 || v1 <= 0) continue;
    n1 += 1;
    w1 += v2;
    d1 += v2 * (a.fl[0] / v2 - a.fl1[0] / v1);
  }
  // tardias × pontuais do mesmo município, média dos municípios ponderada pelos votos das tardias
  const porMun = new Map<string, { t: [number, number]; p: [number, number]; nt: number }>();
  for (const a of comHora) {
    if (a.fl === null) continue;
    const k = `${a.s.uf}:${a.s.mun}`;
    let g = porMun.get(k);
    if (!g) {
      g = { t: [0, 0], p: [0, 0], nt: 0 };
      porMun.set(k, g);
    }
    const alvo = a.s.tardia ? g.t : g.p;
    alvo[0] += a.fl[0];
    alvo[1] += a.fl[1];
    if (a.s.tardia) g.nt += 1;
  }
  let w2 = 0;
  let d2 = 0;
  let n2 = 0;
  for (const g of porMun.values()) {
    const vt = g.t[0] + g.t[1];
    const vp = g.p[0] + g.p[1];
    if (g.nt === 0 || vt <= 0 || vp <= 0) continue;
    n2 += g.nt;
    w2 += vt;
    d2 += vt * (g.t[0] / vt - g.p[0] / vp);
  }
  return {
    uf,
    n_tardias: tardias.length,
    n_apos_19h: tardias.filter((a) => a.s.apos_19h).length,
    n_pontuais: pontuais.length,
    delta_comp_tardias: media(tardias.map((a) => a.s.delta_pp)),
    delta_comp_pontuais: media(pontuais.map((a) => a.s.delta_pp)),
    n_vs_1t: n1,
    delta_fatia_vs_1t_pp: n1 >= nMin && w1 > 0 ? r2((100 * d1) / w1) : null,
    n_vs_pontuais: n2,
    delta_fatia_vs_pontuais_pp: n2 >= nMin && w2 > 0 ? r2((100 * d2) / w2) : null,
  };
}

const porEscore = (a: SecaoComparecimento, b: SecaoComparecimento): number =>
  b.escore - a.escore || (b.delta_pp ?? -Infinity) - (a.delta_pp ?? -Infinity) || (a.uf < b.uf ? -1 : a.uf > b.uf ? 1 : a.secao - b.secao);

function camadaMunicipal(o: OpcoesComparecimento): MunicipioComparecimento[] {
  const out: MunicipioComparecimento[] = [];
  for (const m of o.municipios) {
    if (m.ts <= 0 || m.uf === "ZZ") continue;
    const pst = (100 * m.st) / m.ts;
    const den = m.comparecimento + m.abstencao;
    if (pst < R.mun_pst_min || den <= 0) continue;
    const r1 = o.ref1t?.municipios[m.uf]?.[m.cd];
    if (!r1) continue;
    const ref = o.refSecoes?.municipios[m.uf.toLowerCase()]?.[m.cd];
    const taxa2 = (100 * m.comparecimento) / den;
    const taxa1 = 100 - r1.pa;
    out.push({
      uf: m.uf, cd: m.cd, nm: m.nm, lat: ref?.lat ?? null, lon: ref?.lon ?? null, te: m.te, pst: r2(pst), taxa_2t: r2(taxa2), taxa_1t: r2(taxa1),
      delta_pp: r2(taxa2 - taxa1),
    });
  }
  return out.sort((a, b) => (a.uf < b.uf ? -1 : a.uf > b.uf ? 1 : a.cd < b.cd ? -1 : 1));
}

export function resumoComparecimento(db: Database, o: OpcoesComparecimento): ComparecimentoOut {
  const at = o.at ?? o.agora;
  const av = lerLinhas(db)
    .filter((l) => l.recebido_iso !== null && l.recebido_iso <= at)
    .map((l) => avaliar(l, o));
  const secoes = av.map((a) => a.s);
  const porUf = new Map<string, Avaliada[]>();
  for (const a of av) {
    const g = porUf.get(a.s.uf);
    if (g) g.push(a);
    else porUf.set(a.s.uf, [a]);
  }
  const ufsOrd = [...porUf.keys()].sort();
  const pontos: PontoSecao[] = secoes
    .filter((s): s is SecaoComparecimento & { lon: number; lat: number } => s.lon !== null && s.lat !== null)
    .map((s) => [s.lon, s.lat, s.delta_pp, s.escore, s.aptos ?? 0, s.contingencia ? 1 : 0]);
  const muns = camadaMunicipal(o);
  const munsPorUf = new Map<string, MunicipioComparecimento[]>();
  for (const m of muns) {
    const g = munsPorUf.get(m.uf);
    if (g) g.push(m);
    else munsPorUf.set(m.uf, [m]);
  }
  return {
    at,
    min: minutosDesde17h(at, o.t0Ms),
    rotulo: ROTULO_COMPARECIMENTO,
    regras: R,
    referencia: {
      secoes: o.refSecoes !== null,
      gerado_em: o.refSecoes?.meta.gerado_em ?? null,
      municipios: o.ref1t !== null,
      enc_1t_pct: {
        apos_1700: o.refSecoes?.meta.enc_1t_pct?.apos_1700 ?? null,
        apos_1800: o.refSecoes?.meta.enc_1t_pct?.apos_1800 ?? null,
        apos_1900: o.refSecoes?.meta.enc_1t_pct?.apos_1900 ?? null,
      },
    },
    totais: {
      recebidas: secoes.length,
      com_ref_1t: secoes.filter((s) => s.taxa_comp_1t !== null).length,
      com_coord: pontos.length,
      amostra: secoes.filter((s) => s.origem === "amostra").length,
      paralela: secoes.filter((s) => s.origem === "paralela").length,
    },
    sinais: contar(secoes),
    delta: distribuicao(secoes.map((s) => s.delta_pp)),
    por_uf: ufsOrd.map((uf) => {
      const l = (porUf.get(uf) ?? []).map((a) => a.s);
      return { uf, recebidas: l.length, ...contar(l), delta_dist: distribuicao(l.map((s) => s.delta_pp)) };
    }),
    pontos,
    top: [...secoes].sort(porEscore).slice(0, 30),
    contingencia: secoes
      .filter((s) => s.contingencia)
      .sort((a, b) => ((a.recebido_hhmm ?? "") < (b.recebido_hhmm ?? "") ? 1 : -1))
      .slice(0, 50),
    prorrogacao: {
      n_min: N_MIN_PRORROGACAO,
      brasil: blocoProrrogacao("BR", av),
      por_uf: ufsOrd.map((uf) => blocoProrrogacao(uf, porUf.get(uf) ?? [])),
    },
    municipios: muns,
    municipios_uf: [...munsPorUf.entries()].sort((a, b) => (a[0] < b[0] ? -1 : 1)).map(([uf, l]) => ({ uf, n: l.length, delta: distribuicao(l.map((m) => m.delta_pp)) })),
    municipios_delta: distribuicao(muns.map((m) => m.delta_pp)),
    municipios_top: muns
      .filter((m) => m.delta_pp > 0)
      .sort((a, b) => b.delta_pp - a.delta_pp)
      .slice(0, 30),
  };
}
