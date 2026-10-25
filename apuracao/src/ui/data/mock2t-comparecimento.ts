// /api/2t/comparecimento sintética do ensaio (#mock=1): seções da amostra espalhadas pelas UFs
// (coordenadas em torno do centro de cada UF), sinais de falso comparecimento raros e
// determinísticos, municípios do mock principal com 30% das seções apuradas e os votos da
// prorrogação por UF. Tudo é função do minuto simulado.

import { REGRAS_COMPARECIMENTO, ROTULO_COMPARECIMENTO } from "../../secoes2t/comparecimento-tipos.ts";
import type { BlocoProrrogacao, Distribuicao, MunicipioComparecimento, SecaoComparecimento } from "../../secoes2t/comparecimento-tipos.ts";
import type { MunicipioMock } from "./mock2t.ts";

/** FNV-1a seguido de um passo do mulberry32: número determinístico em [0, 1) por chave. */
function a01(chave: string): number {
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

/** Centro aproximado (lon, lat) e espalhamento em graus de cada UF, só para o ensaio. */
const CENTRO_UF: Readonly<Record<string, readonly [number, number, number]>> = {
  AC: [-70.5, -9.3, 1.2], AL: [-36.6, -9.6, 0.4], AP: [-51.8, 1.4, 0.8], AM: [-64.6, -4.2, 4], BA: [-41.7, -12.5, 2.5],
  CE: [-39.6, -5.1, 1.2], DF: [-47.8, -15.8, 0.2], ES: [-40.6, -19.6, 0.6], GO: [-49.6, -16.0, 2], MA: [-45.3, -5.1, 2],
  MT: [-55.9, -12.9, 3], MS: [-54.8, -20.5, 2], MG: [-44.6, -18.5, 2.5], PA: [-52.5, -4.0, 3.5], PB: [-36.8, -7.1, 0.6],
  PR: [-51.6, -24.6, 1.5], PE: [-37.9, -8.4, 0.8], PI: [-42.9, -7.5, 1.8], RJ: [-42.7, -22.3, 0.6], RN: [-36.6, -5.8, 0.5],
  RS: [-53.3, -29.7, 1.8], RO: [-62.8, -10.9, 1.8], RR: [-61.4, 2.1, 1.2], SC: [-50.5, -27.3, 0.9], SP: [-48.6, -22.3, 1.5],
  SE: [-37.4, -10.6, 0.4], TO: [-48.3, -10.2, 1.8],
};

/** Peso de sorteio da UF na amostra do ensaio (aproxima o eleitorado). */
const PESO_UF: Readonly<Record<string, number>> = { SP: 22, MG: 11, RJ: 8, BA: 7, RS: 5, PR: 5, PE: 5, CE: 4, PA: 4, SC: 3, GO: 3, MA: 3 };

const UFS = Object.keys(CENTRO_UF).sort();
const SORTEIO = UFS.flatMap(uf => Array.from({ length: PESO_UF[uf] ?? 1 }, () => uf));

const r1 = (x: number): number => Math.round(x * 10) / 10;
const r2 = (x: number): number => Math.round(x * 100) / 100;

function posicao(uf: string, chave: string): [number, number] {
  const [lon, lat, s] = CENTRO_UF[uf] ?? [-47.8, -15.8, 0.2];
  return [r2(lon + (a01(`${chave}x`) - 0.5) * 2 * s), r2(lat + (a01(`${chave}y`) - 0.5) * 2 * s * 0.8)];
}

const hhmm = (min: number): string => {
  const total = Math.round(17 * 60 + min);
  return `${String(Math.floor(total / 60)).padStart(2, "0")}:${String(((total % 60) + 60) % 60).padStart(2, "0")}`;
};

function percentil(v: readonly number[], p: number): number | null {
  if (v.length === 0) return null;
  const s = [...v].sort((a, b) => a - b);
  const k = (s.length - 1) * (p / 100);
  const i = Math.floor(k);
  const lo = s[i] ?? 0;
  const hi = s[Math.min(s.length - 1, i + 1)] ?? lo;
  return r2(lo + (hi - lo) * (k - i));
}

const dist = (v: readonly number[]): Distribuicao => ({ n: v.length, p50: percentil(v, 50), p90: percentil(v, 90) });

interface SecaoMock extends SecaoComparecimento {
  /** minuto do encerramento após 17:00 de Brasília */
  enc: number;
  votos: number;
}

function secao(i: number): SecaoMock {
  const uf = SORTEIO[Math.floor(a01(`cu${i}`) * SORTEIO.length)] ?? "SP";
  const [lon, lat] = posicao(uf, `cs${i}`);
  const aptos = 150 + Math.floor(a01(`ca${i}`) * 300);
  const t1 = 72 + a01(`c1${i}`) * 16;
  const raro = a01(`cr${i}`);
  const delta = raro > 0.93 ? 5 + a01(`cd${i}`) * 8 : (a01(`cn${i}`) + a01(`cm${i}`) - 1) * 6;
  const t2 = Math.min(99, t1 + delta);
  const comp = Math.round((aptos * t2) / 100);
  const semMun = 2.5 + a01(`cb${uf}`) * 2.5;
  const semBio = raro > 0.955 || a01(`cz${i}`) > 0.96 ? 12 + a01(`ce${i}`) * 14 : semMun * (0.4 + a01(`cg${i}`) * 1.2);
  const enc = a01(`ct${i}`) < 0.45 ? -50 + a01(`ch${i}`) * 50 : a01(`ck${i}`) < 0.7 ? 1 + a01(`cj${i}`) * 100 : 121 + a01(`cl${i}`) * 25;
  // encerramento da mesma seção no 1T: perto das 17:00, cauda até 18:30
  const enc1 = Math.round(a01(`cu1${i}`) < 0.8 ? a01(`cu2${i}`) * 20 : 20 + a01(`cu3${i}`) * 70);
  const tardia = enc > 120 || enc - enc1 >= REGRAS_COMPARECIMENTO.tardia_min_vs_1t;
  const tipoArq = a01(`cp${i}`) > 0.985 ? 4 : 1;
  const tipoUrna = a01(`cq${i}`) > 0.975 ? 4 : 1;
  const cargas = a01(`cw${i}`) > 0.99 ? 2 : 1;
  const f1 = 48 + (a01(`cf${uf}`) - 0.5) * 30 + (a01(`cv${i}`) - 0.5) * 20;
  const f2 = Math.max(5, Math.min(95, f1 + (a01(`co${i}`) - 0.45) * 6));
  const sinais = {
    delta: delta >= REGRAS_COMPARECIMENTO.delta_pp_min,
    sem_bio: semBio >= Math.max(REGRAS_COMPARECIMENTO.sem_bio_min_pct, REGRAS_COMPARECIMENTO.sem_bio_fator * semMun),
    tardia,
    papel: tipoArq >= REGRAS_COMPARECIMENTO.papel_tipo_min,
  };
  return {
    uf,
    mun: String(10000 + Math.floor(a01(`cc${i}`) * 89999)).padStart(5, "0"),
    nm: `ENSAIO ${uf} ${1 + Math.floor(a01(`cx${i}`) * 40)}`,
    zona: 1 + Math.floor(a01(`cy${i}`) * 300),
    secao: 1 + Math.floor(a01(`ci${i}`) * 600),
    lat,
    lon,
    aptos,
    comp,
    taxa_comp: r2((100 * comp) / aptos),
    taxa_comp_1t: r2(t1),
    delta_pp: r2((100 * comp) / aptos - t1),
    sem_bio_pct: r2(semBio),
    sem_bio_pct_1t: r2(semMun * (0.5 + a01(`cs1${i}`))),
    sem_bio_mun_p50_1t: r2(semMun),
    ano_nasc_pct: r2(semBio * 0.8),
    encerramento_hhmm: hhmm(enc),
    enc1_hhmm: hhmm(enc1),
    tardia,
    encerrou_apos_17h: enc > 0,
    apos_19h: enc > 120,
    papel: sinais.papel,
    tipo_arquivo: tipoArq,
    tipo_urna: tipoUrna,
    n_cargas: cargas,
    contingencia: tipoUrna !== 1 || cargas > 1,
    fatia_flavio: r2(f2),
    fatia_flavio_1t: r2(f1),
    recebido_hhmm: hhmm(Math.max(enc, 0) + 4),
    origem: a01(`cpa${i}`) > 0.95 ? "paralela" : "amostra",
    sinais,
    escore: Number(sinais.delta) + Number(sinais.sem_bio) + Number(sinais.tardia) + Number(sinais.papel),
    enc,
    votos: Math.round(comp * 0.94),
  };
}

const media = (v: readonly number[]): number | null => (v.length === 0 ? null : r2(v.reduce((s, x) => s + x, 0) / v.length));

/** Fatia ponderada pelos votos dos dois. */
const fatia = (l: readonly SecaoMock[], campo: "fatia_flavio" | "fatia_flavio_1t"): number => {
  const w = l.reduce((s, x) => s + x.votos, 0);
  return w > 0 ? l.reduce((s, x) => s + (x[campo] ?? 0) * x.votos, 0) / w : 0;
};

function prorrogacao(uf: string, l: readonly SecaoMock[], nMin: number): BlocoProrrogacao {
  const tard = l.filter(x => x.tardia);
  const pont = l.filter(x => !x.tardia);
  const vs1 = tard.length >= nMin ? r2(fatia(tard, "fatia_flavio") - fatia(tard, "fatia_flavio_1t")) : null;
  const vsP = tard.length >= nMin && pont.length > 0 ? r2(fatia(tard, "fatia_flavio") - fatia(pont, "fatia_flavio")) : null;
  return {
    uf,
    n_tardias: tard.length,
    n_apos_19h: tard.filter(x => x.enc > 120).length,
    n_pontuais: pont.length,
    delta_comp_tardias: media(tard.map(x => x.delta_pp ?? 0)),
    delta_comp_pontuais: media(pont.map(x => x.delta_pp ?? 0)),
    n_vs_1t: tard.length,
    delta_fatia_vs_1t_pp: vs1,
    n_vs_pontuais: pont.length > 0 ? tard.length : 0,
    delta_fatia_vs_pontuais_pp: vsP,
  };
}

const semCampos = ({ enc: _e, votos: _v, ...s }: SecaoMock): SecaoComparecimento => s;

/**
 * Corpo bruto da rota no minuto `min` após 17:00. `municipios(uf)` vem do mock principal (nome,
 * eleitorado, progresso e comparecimento simulados); `delta(uf, cd)` é o Δ de abstenção do ensaio.
 */
export function comparecimentoMock(min: number, at: string, municipios: (uf: string) => MunicipioMock[], deltaAbst: (uf: string, cd: string) => number): Record<string, unknown> {
  const n = min < 3 ? 0 : Math.round(300 * Math.min(1, (min - 3) / 150));
  const secoes = Array.from({ length: n }, (_, i) => secao(i));
  const nMin = 20;
  const com = secoes.filter(s => s.delta_pp !== null);
  const conta = (l: readonly SecaoMock[]): Record<string, number> => ({
    delta: l.filter(s => s.sinais.delta).length,
    sem_bio: l.filter(s => s.sinais.sem_bio).length,
    tarde: l.filter(s => s.encerrou_apos_17h).length,
    tardia: l.filter(s => s.tardia).length,
    apos_19h: l.filter(s => s.apos_19h).length,
    papel: l.filter(s => s.papel).length,
    contingencia: l.filter(s => s.contingencia).length,
    escore_2_mais: l.filter(s => s.escore >= 2).length,
  });
  const porUf = new Map<string, SecaoMock[]>();
  for (const s of secoes) porUf.set(s.uf, [...(porUf.get(s.uf) ?? []), s]);
  const ufs = [...porUf.keys()].sort();
  const top = [...secoes].sort((a, b) => b.escore - a.escore || (b.delta_pp ?? -99) - (a.delta_pp ?? -99)).slice(0, 30);

  const muns: MunicipioComparecimento[] = [];
  for (const uf of UFS) {
    const l = municipios(uf)
      .slice()
      .sort((a, b) => b.te - a.te)
      .slice(0, 8);
    for (const m of l) {
      if (m.p < REGRAS_COMPARECIMENTO.mun_pst_min / 100) continue;
      const [lon, lat] = posicao(uf, `m${m.cd}`);
      const taxa2 = r2(100 * m.comp);
      const taxa1 = r2(taxa2 + deltaAbst(uf, m.cd));
      muns.push({ uf, cd: m.cd, nm: m.nm, lat, lon, te: m.te, pst: r2(100 * m.p), taxa_2t: taxa2, taxa_1t: taxa1, delta_pp: r2(taxa2 - taxa1) });
    }
  }
  const munsPorUf = new Map<string, number[]>();
  for (const m of muns) munsPorUf.set(m.uf, [...(munsPorUf.get(m.uf) ?? []), m.delta_pp]);

  return {
    at,
    min: r1(min),
    rotulo: ROTULO_COMPARECIMENTO,
    regras: REGRAS_COMPARECIMENTO,
    referencia: {
      secoes: true,
      gerado_em: "2026-10-25T20:00:00.000Z",
      municipios: true,
      enc_1t_pct: { apos_1700: 92.38, apos_1800: 8.42, apos_1900: 1.63 },
    },
    totais: { recebidas: n, com_ref_1t: com.length, com_coord: n, amostra: secoes.filter(s => s.origem === "amostra").length, paralela: secoes.filter(s => s.origem === "paralela").length },
    sinais: conta(secoes),
    delta: dist(com.map(s => s.delta_pp ?? 0)),
    por_uf: ufs.map(uf => {
      const l = porUf.get(uf) ?? [];
      return { uf, recebidas: l.length, ...conta(l), delta: dist(l.map(s => s.delta_pp ?? 0)) };
    }),
    pontos: secoes.map(s => [s.lon, s.lat, s.delta_pp, s.escore, s.aptos, s.contingencia ? 1 : 0]),
    top: top.map(semCampos),
    contingencia: secoes.filter(s => s.contingencia).slice(0, 50).map(semCampos),
    prorrogacao: { n_min: nMin, brasil: prorrogacao("BR", secoes, nMin), por_uf: ufs.map(uf => prorrogacao(uf, porUf.get(uf) ?? [], nMin)) },
    municipios: muns,
    municipios_uf: [...munsPorUf.entries()].sort((a, b) => (a[0] < b[0] ? -1 : 1)).map(([uf, v]) => ({ uf, n: v.length, delta: dist(v) })),
    municipios_delta: dist(muns.map(m => m.delta_pp)),
    municipios_top: muns
      .filter(m => m.delta_pp > 0)
      .sort((a, b) => b.delta_pp - a.delta_pp)
      .slice(0, 30),
  };
}
