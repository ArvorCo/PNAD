// Rotas /api/2t/* sintéticas do ensaio do 2º turno (#mock=1). Tudo é função do instante
// simulado `t`, determinístico, coerente com `speed` e com os números do mock principal
// (mock.ts): as seções, os votos e os municípios vêm dele pelo contexto `CtxMock2T`.
// A régua do 1º turno é inventada: a curva de cada UF no 1T é a curva do 2T deslocada de
// `shiftMin(uf)` minutos, então o atraso é exatamente esse deslocamento.
// Dados de ensaio: nomes de candidatura de governador são rotulados "ENSAIO".

import { minutosDesde17h, NOME_REGIAO, ORDEM_REGIOES, REGIOES } from "../../turno2/comum.ts";
import type { Anomalia, Config, Estado, Resultado } from "../state/types.ts";
import { erro, NORMALIZADORES, pendente } from "./doist.ts";
import type {
  Agregado,
  Dados2T,
  Estaduais,
  MunAbstencao,
  Paralela,
  Pausas,
  Regioes,
  Resposta,
  Rota2T,
  Secoes,
  UfLinha,
  UfsResp,
  VotoAgregado,
} from "./doist.ts";

const MIN = 60_000;

export const DUELO_2T_NUMEROS: readonly string[] = ["22", "13"];

interface CandMock {
  n: string;
  sqcand: string;
  nmu: string;
  sg: string;
}

const PARES_GOV: Readonly<Record<string, readonly [string, string]>> = {
  AC: ["PL", "PT"],
  AM: ["UNIÃO", "PSB"],
  DF: ["PSD", "PDT"],
  ES: ["NOVO", "PSOL"],
  RN: ["PP", "PT"],
  TO: ["REPUBLICANOS", "PSB"],
};
const NUMERO_PARTIDO: Readonly<Record<string, string>> = {
  PL: "22", PT: "13", "UNIÃO": "44", PSB: "40", PSD: "55", PDT: "12", NOVO: "30", PSOL: "50", PP: "11", REPUBLICANOS: "10",
};

/** Candidaturas fictícias ao governo nas seis UFs com 2º turno (nomes rotulados "ENSAIO"). */
export const GOVERNADORES_2T: Readonly<Record<string, CandMock[]>> = Object.fromEntries(
  Object.entries(PARES_GOV).map(([uf, par], i) => [
    uf,
    par.map((sg, k) => ({ n: NUMERO_PARTIDO[sg] ?? "99", sqcand: `92${i}000${k + 1}`, nmu: `ENSAIO ${uf} ${NUMERO_PARTIDO[sg] ?? "99"}`, sg })),
  ]),
);

// ---------- funções puras do cronograma de ensaio (testadas) ----------

/** Janelas de pausa do arquivo nacional, em minutos após 17:00. */
export const PAUSAS_NACIONAL: readonly (readonly [number, number])[] = [
  [38, 46.5],
  [118, 131],
  [205, 222],
];

/** Janelas de pausa de arquivos de UF, em minutos após 17:00. */
export const PAUSAS_UF: Readonly<Record<string, readonly [number, number]>> = { MA: [70, 92], PA: [150, 166] };

export const emPausaNacionalMin = (min: number): boolean => PAUSAS_NACIONAL.some(([d, a]) => min >= d && min < a);
export const emPausaUfMin = (uf: string, min: number): boolean => {
  const j = PAUSAS_UF[uf];
  return !!j && min >= j[0] && min < j[1];
};

/** Atraso fixo da UF contra o 1º turno, em minutos (positivo = 2T mais lento). */
export function shiftMin(uf: string): number {
  if (uf === "PA") return 32;
  if (uf === "MA") return 27;
  if (uf === "ZZ") return 6;
  return Math.round((aleatorio01(`sh${uf}`) * 32 - 8) * 10) / 10;
}

function aleatorio01(chave: string): number {
  let h = 0x811c9dc5;
  for (let i = 0; i < chave.length; i++) {
    h ^= chave.charCodeAt(i);
    h = Math.imul(h, 0x01000193);
  }
  let t = ((h >>> 0) + 0x6d2b79f5) >>> 0;
  t = Math.imul(t ^ (t >>> 15), t | 1);
  t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
}

/** Δ de abstenção do município no 2T contra o 1T, em pontos (viés regional mais ruído de ±4,5). */
export function deltaMunicipio(uf: string, cd: string): number {
  const regiao = Object.entries(REGIOES).find(([, ufs]) => ufs.includes(uf))?.[0] ?? "SE";
  const vies: Record<string, number> = { N: 1.5, NE: 2.2, CO: 0.8, SE: 1.0, S: -0.4, ZZ: 0 };
  return Math.round(((vies[regiao] ?? 0) + (aleatorio01(`dm${cd}`) - 0.5) * 9) * 10) / 10;
}

const hhmm = (minutos: number): string => {
  const total = Math.round(17 * 60 + minutos);
  return `${String(Math.floor(total / 60) % 24).padStart(2, "0")}:${String(total % 60).padStart(2, "0")}`;
};

// ---------- contexto ----------

export interface MunicipioMock {
  cd: string;
  nm: string;
  te: number;
  /** Progresso 0 a 1. */
  p: number;
  /** Instante (ms) em que o município fecha. */
  fecha: number;
  /** Comparecimento 0 a 1. */
  comp: number;
}

export interface CtxMock2T {
  config: Config;
  dezessete: number;
  estado(t: number): Estado;
  resultado(cargo: number, abr: string, t: number): Resultado;
  stUf(uf: string, t: number): { st: number; ts: number };
  municipios(uf: string, t: number): MunicipioMock[];
  falhas: Partial<Record<Rota2T, "erro" | "pendente" | "fonte">>;
  sem1t: boolean;
}

export interface Rotas2T {
  dados(rota: Rota2T, t: number): Resposta<Dados2T[Rota2T]>;
  anomalias(t: number): Anomalia[];
}

interface LinhaBase {
  uf: string;
  nome: string;
  regiao: string;
  ts: number;
  st: number;
  te: number;
  c: number;
  a: number;
  munnr: number;
  munpt: number;
  munf: number;
  votos: Record<string, number>;
  vb: number;
  vn: number;
}

const EXTERIOR = { te: 480_000, ts: 2100, abre: 4, dur: 170 };

export function criarRotas2T(ctx: CtxMock2T): Rotas2T {
  const iso = (ms: number): string => new Date(ms).toISOString();
  const minDe = (t: number): number => Math.round(((t - ctx.dezessete) / MIN) * 10) / 10;
  const duelo = (t: number): { sq: string; n: string; nome: string }[] => {
    const r = ctx.resultado(1, "br", t);
    return [...r.cand].sort((a, b) => b.n.localeCompare(a.n)).map(c => ({ sq: c.sqcand, n: c.n, nome: c.nmu }));
  };

  const cacheLinhas = new Map<number, LinhaBase[]>();
  const progressoZZ = (min: number): number => {
    if (min <= EXTERIOR.abre) return 0;
    const f = Math.min(1, (min - EXTERIOR.abre) / EXTERIOR.dur);
    return 1 - (1 - f) ** 1.7;
  };
  const stZZ = (t: number): number => Math.floor(EXTERIOR.ts * progressoZZ(minDe(t)));

  const stUf = (uf: string, t: number): { st: number; ts: number } => (uf === "ZZ" ? { st: stZZ(t), ts: EXTERIOR.ts } : ctx.stUf(uf, t));

  const linhas = (t: number): LinhaBase[] => {
    const k = Math.floor(t / 1000);
    const hit = cacheLinhas.get(k);
    if (hit) return hit;
    if (cacheLinhas.size > 40) cacheLinhas.clear();
    const e = ctx.estado(t);
    const regiaoDe = (uf: string): string => ORDEM_REGIOES.find(r => REGIOES[r].includes(uf)) ?? "SE";
    const saida: LinhaBase[] = [];
    for (const u of e.ufs) {
      const r = ctx.resultado(1, u.uf.toLowerCase(), t);
      const votos: Record<string, number> = {};
      for (const c of r.cand) votos[c.sqcand] = c.vap;
      saida.push({
        uf: u.uf,
        nome: ctx.config.ufs.find(x => x.uf.toUpperCase() === u.uf)?.nome ?? u.uf,
        regiao: regiaoDe(u.uf),
        ts: u.ts,
        st: u.st,
        te: r.e.te,
        c: r.e.c,
        a: Math.max(0, r.e.a),
        munnr: u.munnr,
        munpt: u.munpt,
        munf: u.munf,
        votos,
        vb: r.v.vb,
        vn: r.v.vn,
      });
    }
    // Exterior sintético: 56% de um lado e 44% do outro, comparecimento de 27%.
    const p = progressoZZ(minDe(t));
    const [d0, d1] = duelo(t);
    const eleitos = Math.round(EXTERIOR.te * p);
    const c = Math.round(eleitos * 0.27);
    const vv = Math.round(c * 0.97);
    const tem = !!d0 && !!d1;
    saida.push({
      uf: "ZZ",
      nome: "Exterior",
      regiao: "ZZ",
      ts: EXTERIOR.ts,
      st: stZZ(t),
      te: EXTERIOR.te,
      c,
      a: Math.max(0, eleitos - c),
      munnr: p <= 0 ? 186 : 0,
      munpt: p > 0 && p < 1 ? 186 : 0,
      munf: p >= 1 ? 186 : 0,
      votos: tem ? { [d0.sq]: Math.round(vv * 0.56), [d1.sq]: vv - Math.round(vv * 0.56) } : {},
      vb: Math.round(c * 0.01),
      vn: c - vv - Math.round(c * 0.01),
    });
    cacheLinhas.set(k, saida);
    return saida;
  };

  const pct = (a: number, b: number): number => (b > 0 ? (100 * a) / b : 0);

  const agregarVotos = (ls: LinhaBase[]): { votos: Record<string, VotoAgregado>; vv: number; lider: string | null; margem: number } => {
    const soma: Record<string, number> = {};
    for (const l of ls) for (const [sq, v] of Object.entries(l.votos)) soma[sq] = (soma[sq] ?? 0) + v;
    const vv = Object.values(soma).reduce((s, x) => s + x, 0);
    const votos: Record<string, VotoAgregado> = {};
    for (const [sq, v] of Object.entries(soma)) votos[sq] = { vap: v, pvapn: pct(v, vv) };
    const ord = Object.entries(votos).sort((a, b) => b[1].vap - a[1].vap);
    const [a, b] = ord;
    return { votos, vv, lider: a && a[1].vap > 0 ? a[0] : null, margem: a && b ? a[1].pvapn - b[1].pvapn : 0 };
  };

  const velocidade = (ufs: readonly string[], t: number): number => {
    const agora = ufs.reduce((s, u) => s + stUf(u, t).st, 0);
    const antes = ufs.reduce((s, u) => s + stUf(u, t - 10 * MIN).st, 0);
    return Math.round(((agora - antes) / 10) * 10) / 10;
  };

  const eta = (st: number, ts: number, vel: number, t: number): string | null => (st < ts && vel > 0.05 ? iso(t + ((ts - st) / vel) * MIN) : null);

  /** Referência do 1T: pst que a UF tinha no mesmo relógio (o 2T tem a mesma curva `shift` minutos adiante). */
  const pstRef = (ufs: readonly string[], t: number): { pst: number; atraso: number | null } => {
    let st = 0;
    let ts = 0;
    let atraso = 0;
    for (const u of ufs) {
      const sh = shiftMin(u);
      const s = stUf(u, t + sh * MIN);
      st += s.st;
      ts += s.ts;
      atraso += sh * s.ts;
    }
    // Antes de a primeira seção chegar não há atraso para medir.
    const comecou = ufs.some(u => stUf(u, t).st > 0);
    return { pst: pct(st, ts), atraso: ts > 0 && comecou ? Math.round((atraso / ts) * 10) / 10 : null };
  };

  const agregado = (sigla: string, nome: string, ls: LinhaBase[], t: number): Agregado => {
    const ts = ls.reduce((s, l) => s + l.ts, 0);
    const st = ls.reduce((s, l) => s + l.st, 0);
    const c = ls.reduce((s, l) => s + l.c, 0);
    const a = ls.reduce((s, l) => s + l.a, 0);
    const v = agregarVotos(ls);
    const ufs = ls.map(l => l.uf);
    const vel = velocidade(ufs, t);
    const ref = pstRef(ufs, t);
    const vb = ls.reduce((s, l) => s + l.vb, 0);
    const vn = ls.reduce((s, l) => s + l.vn, 0);
    return {
      sigla,
      nome,
      ufs,
      ts,
      st,
      snt: ts - st,
      pst: pct(st, ts),
      te: ls.reduce((s, l) => s + l.te, 0),
      est: ls.reduce((s, l) => s + l.te, 0),
      comparecimento: c,
      abstencao: a,
      pa: pct(a, c + a),
      votos: v.votos,
      vv: v.vv,
      vb,
      vn,
      tv: v.vv + vb + vn,
      lider: v.lider,
      margem_pp: Math.round(v.margem * 100) / 100,
      vel_10min_spm: vel,
      eta_100_iso: eta(st, ts, vel, t),
      ref_1t: ctx.sem1t ? null : { pst_mesmo_relogio: ref.pst, atraso_min: ref.atraso, pa_final_1t: 20.8 + aleatorio01(`paf${sigla}`) * 2.4 },
      atualizado_em: iso(t - 20_000),
    };
  };

  const regioes = (t: number): Regioes => {
    const ls = linhas(t);
    return {
      at: iso(t),
      min: minDe(t),
      turno: 2,
      referencia_1t: !ctx.sem1t,
      brasil: agregado("BR", "Brasil", ls, t),
      regioes: ORDEM_REGIOES.map(r => agregado(r, NOME_REGIAO[r], ls.filter(l => l.regiao === r), t)),
    };
  };

  const marcosRef = (uf: string): { p50: number; p90: number; p99: number; p100: number } => {
    const f = (alvo: number): number => {
      // Primeiro minuto em que o 2T chega ao alvo, menos o deslocamento: marco do 1T.
      for (let m = 1; m <= 900; m += 2) {
        const s = stUf(uf, ctx.dezessete + m * MIN);
        if (s.ts > 0 && (100 * s.st) / s.ts >= alvo) return m - shiftMin(uf);
      }
      return 900;
    };
    return { p50: f(50), p90: f(90), p99: f(99), p100: f(99.99) };
  };
  const cacheMarcos = new Map<string, ReturnType<typeof marcosRef>>();
  const marcos = (uf: string): ReturnType<typeof marcosRef> => {
    let m = cacheMarcos.get(uf);
    if (!m) {
      m = marcosRef(uf);
      cacheMarcos.set(uf, m);
    }
    return m;
  };

  const versaoUf = (uf: string, t: number): { em: number; parada: boolean } => {
    const min = minDe(t);
    const j = PAUSAS_UF[uf];
    if (j && min >= j[0] + 0.1 && min < j[1]) return { em: ctx.dezessete + j[0] * MIN, parada: min - j[0] > 10 };
    return { em: t - (12 + Math.floor(aleatorio01(`v${uf}${Math.floor(t / 20_000)}`) * 40)) * 1000, parada: false };
  };

  const ufs = (t: number): UfsResp => {
    const ls = linhas(t);
    const saida: UfLinha[] = ls.map(l => {
      const v = agregarVotos([l]);
      const vel = velocidade([l.uf], t);
      const ver = versaoUf(l.uf, t);
      const sh = shiftMin(l.uf);
      const s = stUf(l.uf, t + sh * MIN);
      const m = marcos(l.uf);
      const pend = ctx
        .municipios(l.uf, t)
        .filter(x => x.p < 1)
        .sort((a, b) => b.te - a.te)
        .slice(0, 3)
        .map(x => ({ cd: x.cd, nm: x.nm, te: x.te, pst: Math.round(x.p * 1000) / 10 }));
      return {
        uf: l.uf,
        nome: l.nome,
        regiao: l.regiao,
        ts: l.ts,
        st: l.st,
        snt: l.ts - l.st,
        pst: pct(l.st, l.ts),
        te: l.te,
        comparecimento: l.c,
        abstencao: l.a,
        pa: pct(l.a, l.c + l.a),
        munnr: l.munnr,
        munpt: l.munpt,
        munf: l.munf,
        votos: v.votos,
        lider: v.lider,
        margem_pp: Math.round(v.margem * 100) / 100,
        ultima_versao_em: iso(ver.em),
        idade_s: Math.round((t - ver.em) / 1000),
        vel_10min_spm: vel,
        eta_100_iso: eta(l.st, l.ts, vel, t),
        parada: ver.parada && l.st < l.ts,
        ref_1t: ctx.sem1t
          ? null
          : { pst_mesmo_relogio: pct(s.st, s.ts), atraso_min: l.st > 0 ? sh : null, p50_min: m.p50, p90_min: m.p90, p99_min: m.p99, p100_min: m.p100, pa_final: 20.6 + aleatorio01(`pf${l.uf}`) * 3 },
        pendentes_maiores: pend,
      };
    });
    saida.sort((a, b) => a.pst - b.pst || a.uf.localeCompare(b.uf));
    return { at: iso(t), min: minDe(t), limiar_parada_min: 10, ufs: saida };
  };

  const bloco = (chave: string, nome: string, muns: { uf: string; m: MunicipioMock; pa1: number }[], todos: number, campo: "sigla" | "uf"): Record<string, unknown> => {
    const fechados = muns.filter(x => x.m.p >= 1);
    const teF = fechados.reduce((s, x) => s + x.m.te, 0);
    const comp = fechados.reduce((s, x) => s + x.m.te * x.m.comp, 0);
    const abst = teF - comp;
    const pa2 = teF > 0 ? pct(abst, teF) : null;
    const pa1 = teF > 0 ? fechados.reduce((s, x) => s + x.m.te * x.pa1, 0) / teF : null;
    const teTotal = muns.reduce((s, x) => s + x.m.te, 0);
    const todosPa = muns.length > 0 ? muns.reduce((s, x) => s + x.m.te * (1 - x.m.comp) * 100, 0) / Math.max(1, teTotal) : null;
    return {
      [campo]: chave,
      nome,
      n_mun: todos,
      n_mun_fechados: fechados.length,
      te_fechado: teF,
      pct_te_fechado: pct(teF, teTotal),
      comparecimento: Math.round(comp),
      abstencao: Math.round(abst),
      pa_2t: pa2,
      pa_1t_mesmos: ctx.sem1t ? null : pa1,
      delta_pp: ctx.sem1t || pa2 === null || pa1 === null ? null : Math.round((pa2 - pa1) * 100) / 100,
      pa_corrente: todosPa,
      pa_final_1t: ctx.sem1t ? null : 21.4 + aleatorio01(`paf1${chave}`) * 2.2,
    };
  };

  const todasMunicipais = (t: number): { uf: string; m: MunicipioMock; pa1: number; nm: string }[] => {
    const saida: { uf: string; m: MunicipioMock; pa1: number; nm: string }[] = [];
    for (const cu of ctx.config.ufs) {
      const uf = cu.uf.toUpperCase();
      for (const m of ctx.municipios(uf, t)) saida.push({ uf, m, pa1: (1 - m.comp) * 100 - deltaMunicipio(uf, m.cd), nm: m.nm });
    }
    return saida;
  };

  const abstencao = (t: number): Record<string, unknown> => {
    const todas = todasMunicipais(t);
    const porUf = (uf: string): typeof todas => todas.filter(x => x.uf === uf);
    const ufsB = ctx.config.ufs.map(cu => bloco(cu.uf.toUpperCase(), cu.nome, porUf(cu.uf.toUpperCase()), porUf(cu.uf.toUpperCase()).length, "uf"));
    const regB = ORDEM_REGIOES.filter(r => r !== "ZZ").map(r =>
      bloco(r, NOME_REGIAO[r], todas.filter(x => REGIOES[r].includes(x.uf)), todas.filter(x => REGIOES[r].includes(x.uf)).length, "sigla"),
    );
    const destaques = (sinal: 1 | -1): MunAbstencao[] =>
      ctx.sem1t
        ? []
        : todas
            .filter(x => x.m.p >= 1 && x.m.te >= 20_000)
            .map(x => ({
              uf: x.uf,
              cd: x.m.cd,
              nm: x.nm,
              te: x.m.te,
              pa_2t: Math.round((1 - x.m.comp) * 1000) / 10,
              pa_1t: Math.round(x.pa1 * 10) / 10,
              delta_pp: deltaMunicipio(x.uf, x.m.cd),
              fechou_min: minutosDesde17h(iso(x.m.fecha), ctx.dezessete),
            }))
            .filter(x => sinal * x.delta_pp >= 3)
            .sort((a, b) => sinal * (b.delta_pp - a.delta_pp))
            .slice(0, 20);
    return {
      at: iso(t),
      min: minDe(t),
      base: "municipios_fechados",
      brasil: bloco("BR", "Brasil", todas, todas.length, "sigla"),
      regioes: regB,
      ufs: ufsB,
      destaques: { subiu: destaques(1), caiu: destaques(-1) },
    };
  };

  // ---------- estaduais ----------
  const viradasCache = new Map<string, { ate: number; ultimo: string | null; lista: { at: string; de: string; para: string }[] }>();
  const viradas = (uf: string, t: number): { at: string; de: string; para: string }[] => {
    const c = viradasCache.get(uf) ?? { ate: ctx.dezessete, ultimo: null, lista: [] };
    for (let s = c.ate + 3 * MIN; s <= t; s += 3 * MIN) {
      const r = ctx.resultado(3, uf.toLowerCase(), s);
      const top = [...r.cand].sort((a, b) => b.vap - a.vap)[0];
      if (top && top.vap > 0) {
        if (c.ultimo && c.ultimo !== top.sqcand) c.lista.push({ at: iso(s), de: c.ultimo, para: top.sqcand });
        c.ultimo = top.sqcand;
      }
      c.ate = s;
    }
    viradasCache.set(uf, c);
    return c.lista;
  };

  const estaduais = (t: number): Estaduais => ({
    at: iso(t),
    min: minDe(t),
    ufs: Object.keys(GOVERNADORES_2T).map(uf => {
      const r = ctx.resultado(3, uf.toLowerCase(), t);
      const ord = [...r.cand].sort((a, b) => b.vap - a.vap);
      const sh = shiftMin(uf);
      const s = stUf(uf, t + sh * MIN);
      const ver = versaoUf(uf, t);
      const l = linhas(t).find(x => x.uf === uf);
      return {
        uf,
        nome: ctx.config.ufs.find(x => x.uf.toUpperCase() === uf)?.nome ?? uf,
        ts: r.s.ts,
        st: r.s.st,
        pst: r.s.pst,
        te: r.e.te,
        comparecimento: r.e.c,
        abstencao: Math.max(0, r.e.a),
        pa: pct(Math.max(0, r.e.a), r.e.c + Math.max(0, r.e.a)),
        munnr: l?.munnr ?? 0,
        munpt: l?.munpt ?? 0,
        munf: l?.munf ?? 0,
        cand: [...r.cand]
          .sort((a, b) => a.n.localeCompare(b.n, "pt-BR", { numeric: true }))
          .map(c => ({ sqcand: c.sqcand, n: c.n, nome_urna: c.nmu, partido: c.sg, vap: c.vap, pvapn: c.pvapn, campo: c.campo })),
        lider: ord[0] && ord[0].vap > 0 ? ord[0].sqcand : null,
        margem_pp: ord[0] && ord[1] ? Math.round((ord[0].pvapn - ord[1].pvapn) * 100) / 100 : 0,
        viradas: viradas(uf, t),
        ultima_versao_em: iso(ver.em),
        idade_s: Math.round((t - ver.em) / 1000),
        ref_1t: ctx.sem1t ? null : { pst_mesmo_relogio: pct(s.st, s.ts), atraso_min: r.s.st > 0 ? sh : null },
        pa_final_1t: ctx.sem1t ? null : 20.9 + aleatorio01(`pg${uf}`) * 3,
      };
    }),
  });

  // ---------- evolução ----------
  const cacheEvolucao = new Map<string, { st: number; ts: number; votos: Record<string, number>; ref: { st: number; ts: number } }>();
  const pontoUf = (uf: string, g: number): { st: number; ts: number; votos: Record<string, number>; ref: { st: number; ts: number } } => {
    const k = `${uf}@${g}`;
    const hit = cacheEvolucao.get(k);
    if (hit) return hit;
    if (cacheEvolucao.size > 30_000) cacheEvolucao.clear();
    const s = stUf(uf, g);
    const votos: Record<string, number> = {};
    if (uf === "ZZ") {
      const [d0, d1] = duelo(g);
      const vv = Math.round(Math.round(EXTERIOR.te * progressoZZ(minDe(g))) * 0.27 * 0.97);
      if (d0 && d1) {
        votos[d0.sq] = Math.round(vv * 0.56);
        votos[d1.sq] = vv - Math.round(vv * 0.56);
      }
    } else {
      for (const c of ctx.resultado(1, uf.toLowerCase(), g).cand) votos[c.sqcand] = c.vap;
    }
    const ref = stUf(uf, g + shiftMin(uf) * MIN);
    const p = { st: s.st, ts: s.ts, votos, ref: { st: ref.st, ts: ref.ts } };
    cacheEvolucao.set(k, p);
    return p;
  };

  const evolucao = (nivel: "regiao" | "uf", t: number): Record<string, unknown> => {
    const passo = 300;
    const cand = duelo(t);
    const chaves: { chave: string; ufs: string[] }[] = [{ chave: "BR", ufs: [...ctx.config.ufs.map(u => u.uf.toUpperCase()), "ZZ"] }];
    if (nivel === "regiao") for (const r of ORDEM_REGIOES) chaves.push({ chave: r, ufs: [...REGIOES[r]].filter(u => u === "ZZ" || ctx.config.ufs.some(c => c.uf.toUpperCase() === u)) });
    else for (const u of [...ctx.config.ufs.map(x => x.uf.toUpperCase()), "ZZ"]) chaves.push({ chave: u, ufs: [u] });
    const series: Record<string, (number | null)[][]> = {};
    const referencia: Record<string, [number, number][]> = {};
    for (const { chave, ufs: lista } of chaves) {
      const pts: (number | null)[][] = [];
      const refs: [number, number][] = [];
      for (let m = 0; ctx.dezessete + m * MIN <= t; m += passo / 60) {
        const g = ctx.dezessete + m * MIN;
        let st = 0;
        let ts = 0;
        let rst = 0;
        let rts = 0;
        const v: Record<string, number> = {};
        for (const u of lista) {
          const p = pontoUf(u, g);
          st += p.st;
          ts += p.ts;
          rst += p.ref.st;
          rts += p.ref.ts;
          for (const [sq, n] of Object.entries(p.votos)) v[sq] = (v[sq] ?? 0) + n;
        }
        const vv = Object.values(v).reduce((s, x) => s + x, 0);
        const a = cand[0] ? (vv > 0 ? pct(v[cand[0].sq] ?? 0, vv) : null) : null;
        const b = cand[1] ? (vv > 0 ? pct(v[cand[1].sq] ?? 0, vv) : null) : null;
        pts.push([m, Math.round(pct(st, ts) * 100) / 100, a === null ? null : Math.round(a * 100) / 100, b === null ? null : Math.round(b * 100) / 100, st]);
        refs.push([m, Math.round(pct(rst, rts) * 100) / 100]);
      }
      series[chave] = pts;
      referencia[chave] = refs;
    }
    return {
      at: iso(t),
      passo_s: passo,
      candidatos: cand.map(c => ({ sqcand: c.sq, n: c.n, nome_urna: c.nome })),
      series,
      referencia_1t: ctx.sem1t ? null : referencia,
    };
  };

  // ---------- pausas ----------
  const pausas = (t: number): Pausas => {
    const min = minDe(t);
    const todas = [...ctx.config.ufs.map(u => u.uf.toUpperCase()), "ZZ"];
    const stSoma = (tt: number): number => todas.reduce((s, u) => s + stUf(u, tt).st, 0);
    const tsTotal = todas.reduce((s, u) => s + stUf(u, t).ts, 0);
    const janela = PAUSAS_NACIONAL.find(([d, a]) => min >= d && min < a);
    const efetivo = janela ? ctx.dezessete + janela[0] * MIN : t - 60_000;
    const stNac = stSoma(efetivo);
    const historico = PAUSAS_NACIONAL.filter(([, a]) => a <= min).map(([d, a]) => ({
      de: iso(ctx.dezessete + d * MIN),
      ate: iso(ctx.dezessete + a * MIN),
      minutos: Math.round((a - d) * 10) / 10,
      st_antes: stSoma(ctx.dezessete + d * MIN),
      st_depois: stSoma(ctx.dezessete + a * MIN),
    }));
    return {
      at: iso(t),
      min,
      limiar_min: 5,
      nacional: {
        ultima_versao_em: iso(efetivo),
        idade_s: Math.round((t - efetivo) / 1000),
        st: stNac,
        ts: tsTotal,
        em_pausa: !!janela && min - (janela[0]) > 5,
        pausa_atual: janela ? { desde: iso(ctx.dezessete + janela[0] * MIN), minutos: Math.round((min - janela[0]) * 10) / 10 } : null,
        historico,
      },
      soma_ufs: {
        st: stSoma(t),
        pst: pct(stSoma(t), tsTotal),
        defasagem_secoes: Math.max(0, stSoma(t) - stNac),
        defasagem_min: Math.round(((t - efetivo) / MIN) * 10) / 10,
      },
      ufs: todas.map(u => {
        const ver = versaoUf(u, t);
        const s = stUf(u, t);
        return {
          uf: u,
          ultima_versao_em: iso(ver.em),
          idade_s: Math.round((t - ver.em) / 1000),
          em_pausa: ver.parada && s.st < s.ts,
          st: s.st,
          ts: s.ts,
          historico_n: PAUSAS_UF[u] && min >= (PAUSAS_UF[u]?.[1] ?? Infinity) ? 1 : 0,
        };
      }),
      referencia_1t: ctx.sem1t
        ? { pausa_geral: null, travamento_nacional: null }
        : { pausa_geral: { de: "19:32", ate: "20:02", minutos: 29.6 }, travamento_nacional: { de: "18:00", ate: "18:10" } },
    };
  };

  // ---------- seções ----------
  const alvoUf = (uf: string): number => (uf === "ZZ" ? 12 : 24 + (uf in GOVERNADORES_2T ? 8 : 0));
  const tardiasTodas = (): { uf: string; cd: string; nm: string; zona: string; secao: string; enc: number; lag: number }[] => {
    const lista = ctx.config.ufs.map(u => u.uf.toUpperCase());
    return Array.from({ length: 16 }, (_, i) => {
      const uf = lista[Math.floor(aleatorio01(`ts${i}`) * lista.length)] ?? "SP";
      const ms = ctx.municipios(uf, ctx.dezessete);
      const m = ms[Math.floor(aleatorio01(`tm${i}`) * Math.max(1, ms.length))];
      return {
        uf,
        cd: m?.cd ?? "00000",
        nm: m?.nm ?? uf,
        zona: String(1 + Math.floor(aleatorio01(`tz${i}`) * 200)).padStart(4, "0"),
        secao: String(1 + Math.floor(aleatorio01(`tq${i}`) * 900)).padStart(4, "0"),
        enc: 61 + i * 5.5 + aleatorio01(`te${i}`) * 4,
        lag: Math.round((2 + aleatorio01(`tl${i}`) * 14) * 10) / 10,
      };
    });
  };
  const secoes = (t: number): Secoes => {
    const min = minDe(t);
    const todas = [...ctx.config.ufs.map(u => u.uf.toUpperCase()), "ZZ"];
    const linhaUf = (uf: string): Secoes["por_uf"][number] => {
      const s = stUf(uf, t - 3 * MIN);
      const alvo = alvoUf(uf);
      const recebidas = Math.floor((alvo * s.st) / Math.max(1, s.ts));
      const a = aleatorio01(`sl${uf}`);
      const p50 = Math.round((1.4 + a * 3.2) * 10) / 10;
      const e50 = 8 + Math.round(aleatorio01(`e5${uf}`) * 14);
      return {
        uf,
        alvo,
        recebidas,
        encerramento_p50_hhmm: hhmm(e50),
        encerramento_p90_hhmm: hhmm(e50 + 12 + Math.round(a * 10)),
        tarde_apos_1730_pct: Math.round((1 + a * 9) * 10) / 10,
        lag_encerr_recebimento_min: { p50, p90: Math.round(p50 * 3 * 10) / 10, p99: Math.round(p50 * 9 * 10) / 10 },
        lag_encerr_emissao_min: { p50: Math.round(p50 * 0.45 * 10) / 10, p90: Math.round(p50 * 1.3 * 10) / 10, p99: null },
        lag_recebimento_totalizacao_min: { p50: Math.round((3 + a * 4) * 10) / 10, p90: Math.round((9 + a * 8) * 10) / 10, p99: Math.round((25 + a * 20) * 10) / 10 },
        ref_1t: ctx.sem1t ? null : { lag_p50: Math.round(p50 * 0.9 * 10) / 10, lag_p90: Math.round(p50 * 3.3 * 10) / 10, enc_p90_hhmm: hhmm(e50 + 14 + Math.round(a * 8)) },
      };
    };
    const por = todas.map(linhaUf);
    const alvo = por.reduce((s, l) => s + l.alvo, 0);
    const recebidas = por.reduce((s, l) => s + l.recebidas, 0);
    const tard = tardiasTodas()
      .filter(x => x.enc + x.lag <= min)
      .map(x => ({
        uf: x.uf,
        mun: x.cd,
        nm: x.nm,
        zona: x.zona,
        secao: x.secao,
        encerramento_hhmm: hhmm(x.enc),
        recebido_hhmm: hhmm(x.enc + x.lag),
        lag_min: x.lag,
      }));
    const ultimas = Array.from({ length: recebidas > 0 ? Math.min(20, recebidas) : 0 }, (_, i) => {
      const uf = todas[Math.floor(aleatorio01(`ul${i}${Math.floor(t / 60_000)}`) * todas.length)] ?? "SP";
      const ms = ctx.municipios(uf, t);
      const m = ms[Math.floor(aleatorio01(`um${i}${uf}`) * Math.max(1, ms.length))];
      return {
        uf,
        mun: m?.cd ?? "00000",
        zona: String(1 + Math.floor(aleatorio01(`uz${i}${uf}`) * 200)).padStart(4, "0"),
        secao: String(1 + Math.floor(aleatorio01(`uq${i}${uf}`) * 900)).padStart(4, "0"),
        recebido_em: iso(t - i * 14_000),
        lag_min: Math.round((1 + aleatorio01(`ug${i}`) * 6) * 10) / 10,
      };
    });
    const bruto: Secoes["brasil"] = {
      uf: "BR",
      alvo,
      recebidas,
      encerramento_p50_hhmm: hhmm(16),
      encerramento_p90_hhmm: hhmm(31),
      tarde_apos_1730_pct: 4.1,
      lag_encerr_recebimento_min: { p50: 2.6, p90: 7.9, p99: 23.4 },
      lag_encerr_emissao_min: { p50: 1.2, p90: 3.4, p99: null },
      lag_recebimento_totalizacao_min: { p50: 4.8, p90: 13.1, p99: 38.2 },
      ref_1t: ctx.sem1t ? null : { lag_p50: 2.4, lag_p90: 8.6, enc_p90_hhmm: hhmm(33) },
    };
    return {
      at: iso(t),
      min,
      desenho: { nacional_por_uf: 24, estaduais_por_uf: 8, inclui_paralela: true, intervalo_s: 60 },
      totais: { alvo, recebidas, pendentes: Math.max(0, alvo - recebidas), tardias: tard.length },
      por_uf: por,
      brasil: bruto,
      tardias: tard,
      ultimas,
    };
  };

  // ---------- paralela ----------
  const paralela = (t: number, comErro: boolean): Paralela => {
    const min = minDe(t);
    const bus = Math.max(0, Math.floor((min - 60) * 24));
    const ufsCom = Math.min(27, Math.max(0, Math.floor((min - 60) / 4)));
    const todas = ctx.config.ufs.map(u => u.uf.toUpperCase());
    const peso = (uf: string): number => 0.4 + aleatorio01(`pp${uf}`);
    const somaPeso = todas.slice(0, ufsCom).reduce((s, u) => s + peso(u), 0) || 1;
    const cobertura = todas.slice(0, ufsCom).map(uf => {
      const total = ctx.estado(t).ufs.find(u => u.uf === uf)?.ts ?? 1000;
      const n = Math.floor((bus * peso(uf)) / somaPeso);
      return { uf, bus: n, secoes_total: total, pct: Math.round(pct(n, total) * 100) / 100 };
    });
    const d = duelo(t);
    const lula = d.find(x => x.n === "13");
    const flavio = d.find(x => x.n === "22");
    const comp = bus * 178;
    const placarGov: Paralela["placar_bus"]["governador"] = {};
    if (bus > 200) {
      for (const [uf, cs] of Object.entries(GOVERNADORES_2T)) {
        const n = Math.floor(bus / 40);
        placarGov[uf] = { votos: { [cs[0]?.n ?? "0"]: n * 61, [cs[1]?.n ?? "1"]: n * 54 }, secoes: n };
      }
    }
    const diverg = bus > 1200;
    return {
      at: iso(t),
      atualizado_em: iso(t - 40_000),
      erro: comErro ? "leitura do Supabase falhou (ensaio)" : null,
      recebidos: { bus, envios: Math.round(bus * 1.04), secoes: Math.round(bus * 0.98), ufs: ufsCom, conflitos: Math.floor(bus / 900) },
      conferencia: {
        iguais: Math.floor(bus * 0.9),
        divergentes: diverg ? 1 : 0,
        tse_ainda_nao_publicou: Math.floor(bus * 0.05),
        erro: 0,
        fora_do_oficial: Math.floor(bus / 700),
        pendentes: Math.max(0, bus - Math.floor(bus * 0.9) - Math.floor(bus * 0.05) - Math.floor(bus / 700) - (diverg ? 1 : 0)),
      },
      cobertura_uf: cobertura,
      placar_bus: {
        presidente: {
          votos: { [lula?.n ?? "13"]: Math.round(comp * 0.46), [flavio?.n ?? "22"]: Math.round(comp * 0.5) },
          comparecimento: comp,
          aptos: Math.round(comp / 0.79),
          brancos: Math.round(comp * 0.012),
          nulos: Math.round(comp * 0.028),
          secoes: bus,
        },
        governador: placarGov,
      },
      divergencias: diverg
        ? [
            {
              uf: "MG",
              mun: "41238",
              zona: "0038",
              secao: "0214",
              recebido_em: iso(ctx.dezessete + 95 * MIN),
              conferido_em: iso(ctx.dezessete + 97 * MIN),
              campos: [
                { campo: "nulos", paralela: "21", tse: "12" },
                { campo: "votos do 22", paralela: "188", tse: "197" },
              ],
            },
          ]
        : [],
      ultimos: Array.from({ length: Math.min(10, bus) }, (_, i) => {
        const uf = todas[Math.floor(aleatorio01(`pu${i}${Math.floor(t / 30_000)}`) * Math.max(1, ufsCom || 1))] ?? "SP";
        return {
          uf,
          mun: "00000",
          zona: String(1 + Math.floor(aleatorio01(`pz${i}`) * 200)).padStart(4, "0"),
          secao: String(1 + Math.floor(aleatorio01(`ps${i}`) * 900)).padStart(4, "0"),
          recebido_em: iso(t - i * 45_000),
          situacao: i % 7 === 3 ? "tse_ainda_nao_publicou" : "igual",
        };
      }),
    };
  };

  // ---------- despacho ----------
  const dados = (rota: Rota2T, t: number): Resposta<Dados2T[Rota2T]> => {
    const falha = ctx.falhas[rota];
    if (falha === "erro") return erro("falha simulada no ensaio");
    if (falha === "pendente") return pendente();
    const bruto = ((): unknown => {
      switch (rota) {
        case "regioes":
          return regioes(t);
        case "ufs":
          return ufs(t);
        case "abstencao":
          return abstencao(t);
        case "estaduais":
          return estaduais(t);
        case "evolucao-regiao":
          return evolucao("regiao", t);
        case "evolucao-uf":
          return evolucao("uf", t);
        case "pausas":
          return pausas(t);
        case "secoes":
          return secoes(t);
        case "paralela":
          return paralela(t, falha === "fonte");
      }
    })();
    // O mock passa pelo mesmo normalizador da API real.
    return NORMALIZADORES[rota](bruto) as Resposta<Dados2T[Rota2T]>;
  };

  // ---------- anomalias ----------
  const anomalias = (t: number): Anomalia[] => {
    const min = minDe(t);
    const saida: Anomalia[] = [];
    const add = (quando: number, tipo: Anomalia["tipo"], bruto: string, severidade: "info" | "warn" | "error", texto: string, uf: string | null, detalhe: Record<string, unknown>): void => {
      if (quando > t) return;
      saida.push({ at: iso(quando), tipo, abr: uf ? uf.toLowerCase() : "br", cargo: 1, texto, tipo_bruto: bruto, severidade, uf, detalhe });
    };
    for (const [d, a] of PAUSAS_NACIONAL) {
      add(ctx.dezessete + (d + 5) * MIN, "pausa", "pausa_nacional_inicio", a - d >= 15 ? "error" : "warn", `arquivo nacional sem versão nova há 5 min`, null, { minutos: 5 });
      add(ctx.dezessete + a * MIN, "pausa", "pausa_nacional_fim", "info", `arquivo nacional voltou depois de ${Math.round(a - d)} min`, null, { minutos: a - d });
    }
    for (const [uf, [d, a]] of Object.entries(PAUSAS_UF)) {
      const nome = ctx.config.ufs.find(u => u.uf.toUpperCase() === uf)?.nome ?? uf;
      add(ctx.dezessete + (d + 10) * MIN, "pausa", "pausa_uf_inicio", "warn", `${nome} sem versão nova há 10 min`, uf, { minutos: 10 });
      add(ctx.dezessete + a * MIN, "pausa", "pausa_uf_fim", "info", `${nome} voltou depois de ${Math.round(a - d)} min`, uf, { minutos: a - d });
    }
    for (const cu of ctx.config.ufs) {
      const uf = cu.uf.toUpperCase();
      const sh = shiftMin(uf);
      if (sh >= 20) add(ctx.dezessete + (55 + aleatorio01(`ua${uf}`) * 10) * MIN, "atraso", "uf_atrasada_1t", "warn", `${cu.nome} está ${Math.round(sh)} min atrás do 1º turno`, uf, { atraso_min: sh });
    }
    for (const x of todasMunicipais(t)) {
      const delta = deltaMunicipio(x.uf, x.m.cd);
      if (x.m.p >= 1 && x.m.te >= 20_000 && Math.abs(delta) >= 5 && !ctx.sem1t) {
        add(x.m.fecha, "abstencao", "abstencao_atipica_mun", "warn", `abstenção em ${x.nm}, ${x.uf}: ${(Math.round((1 - x.m.comp) * 1000) / 10).toString().replace(".", ",")}% contra ${(Math.round(x.pa1 * 10) / 10).toString().replace(".", ",")}% no 1º turno`, x.uf, { delta_pp: delta });
      }
    }
    for (const x of tardiasTodas().slice(0, 4)) {
      add(ctx.dezessete + (x.enc + x.lag) * MIN, "atraso", "secao_tardia", "info", `seção ${x.secao} da zona ${x.zona} de ${x.nm}, ${x.uf}, encerrada às ${hhmm(x.enc)}`, x.uf, { encerramento: hhmm(x.enc) });
    }
    if (min > 95) add(ctx.dezessete + 97 * MIN, "divergencia", "divergencia_paralela", "error", "seção 0214, zona 38, Belo Horizonte, MG: BU da paralela difere do oficial em nulos", "MG", { campos: ["nulos", "votos do 22"] });
    for (const m of [70, 130, 190, 250]) add(ctx.dezessete + m * MIN, "paralela", "paralela_conferida", "info", `lote de ${Math.floor((m - 60) * 24)} BUs da paralela conferido: 1 divergente`, null, { bus: Math.floor((m - 60) * 24) });
    return saida.sort((a, b) => b.at.localeCompare(a.at));
  };

  return { dados, anomalias };
}
