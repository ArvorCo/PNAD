// Apuração sintética determinística para ensaio (#mock=1&speed=60). Implementa a
// mesma interface de api.ts. Relógio simulado: começa às 16:59:30 de 04/10/2026
// (Brasília) e anda `speed` vezes mais rápido. Municípios abrem depois das 17:00,
// o pst avança por município, há viradas forçadas em MG e AM e uma regressão de
// seções na BA entre 18:40 e 18:46. Os candidatos a presidente são os 12 reais
// do arquivo do TSE (tests/fixtures/br-c0001-e006257-u.json); os demais cargos
// usam candidaturas sintéticas, rotuladas como tal.

import type { Fonte, ConsultaMapa, ConsultaResultado } from "./api.ts";
import { ErroApi } from "./api.ts";
import { AMOSTRA_CONFIG } from "./amostra.ts";
import type {
  Anomalia,
  Campo,
  Candidato,
  Config,
  ConfigMunicipio,
  Estado,
  EventoSse,
  LiderUnidade,
  Mapa,
  PartidoResultado,
  Resultado,
  Serie,
  UnidadeMapa,
} from "../state/types.ts";

// ---------- aleatoriedade determinística ----------
function fnv(s: string): number {
  let h = 0x811c9dc5;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 0x01000193);
  }
  return h >>> 0;
}

/** Número em [0, 1) fixo para cada chave (mulberry32 de um passo). */
export function aleatorio(chave: string): number {
  let t = (fnv(chave) + 0x6d2b79f5) >>> 0;
  t = Math.imul(t ^ (t >>> 15), t | 1);
  t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
}

// ---------- candidatos ----------
interface CandBase {
  n: string;
  sqcand: string;
  nmu: string;
  sg: string;
  fed_sg?: string;
}

export const PRESIDENTE_2026: readonly CandBase[] = [
  { n: "22", sqcand: "280002551544", nmu: "FLAVIO BOLSONARO", sg: "PL" },
  { n: "55", sqcand: "280002551932", nmu: "RONALDO CAIADO", sg: "PSD" },
  { n: "13", sqcand: "280002542548", nmu: "LULA", sg: "PT", fed_sg: "PT/PC do B/PV" },
  { n: "27", sqcand: "280002552484", nmu: "CLARIANA BARAO", sg: "DC" },
  { n: "21", sqcand: "280002551975", nmu: "EDMILSON COSTA", sg: "PCB" },
  { n: "16", sqcand: "280002541457", nmu: "HERTZ DIAS", sg: "PSTU" },
  { n: "70", sqcand: "280002551547", nmu: "ESCRITOR AUGUSTO CURY", sg: "AVANTE" },
  { n: "30", sqcand: "280002539826", nmu: "ZEMA", sg: "NOVO" },
  { n: "80", sqcand: "280002538811", nmu: "SAMARA", sg: "UP" },
  { n: "35", sqcand: "280002548139", nmu: "VETERINÁRIO WILSON GRASSI", sg: "DEMOCRATA" },
  { n: "14", sqcand: "280002540694", nmu: "RENAN SANTOS", sg: "MISSÃO" },
  { n: "29", sqcand: "280002552487", nmu: "RUI COSTA PIMENTA", sg: "PCO" },
];

/** Cópia de PARTIDO_CAMPO (scripts/voto_util_base.py) para o mock rodar sem campos.json. */
const PARTIDO_CAMPO: Readonly<Record<string, Campo>> = {
  PL: "direita", NOVO: "direita", REPUBLICANOS: "direita", PRTB: "direita", DC: "direita", "MISSÃO": "direita",
  DEMOCRATA: "direita", PP: "centro-direita", "UNIÃO": "centro-direita", PODEMOS: "centro-direita",
  PRD: "centro-direita", AGIR: "centro-direita", MOBILIZA: "centro-direita", PSD: "centro", MDB: "centro",
  AVANTE: "centro", PSDB: "centro-esquerda", CIDADANIA: "centro-esquerda", SOLIDARIEDADE: "centro-esquerda",
  PDT: "esquerda", PT: "esquerda", PSB: "esquerda", PCDOB: "esquerda", PV: "esquerda", PSOL: "esquerda",
  REDE: "esquerda", UP: "esquerda", PCB: "esquerda", PSTU: "esquerda", PCO: "esquerda",
};

const PARTIDOS_SINTETICOS = ["PL", "PT", "PSD", "UNIÃO", "PSOL", "MDB", "NOVO", "PSB", "REPUBLICANOS", "PP", "PDT", "PODEMOS"];

const VAGAS_FED: Readonly<Record<string, number>> = {
  SP: 70, MG: 53, RJ: 46, BA: 39, RS: 31, PR: 30, PE: 25, CE: 22, MA: 18, GO: 17, PA: 17, SC: 16, PB: 12, ES: 10,
  PI: 10, AL: 9,
};

const NORDESTE = new Set(["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"]);
const SUL = new Set(["PR", "RS", "SC"]);
const CENTRO_OESTE = new Set(["GO", "MS", "MT"]);
const NORTE_DIREITA = new Set(["AC", "RO", "RR"]);
const VIRADAS = new Set(["MG", "AM"]);

/** Parcelas de Lula e Flávio no início (0) e no fim (1) da contagem. */
function duelo(uf: string): { l0: number; f0: number; l1: number; f1: number } {
  if (uf === "MG") return { l0: 0.52, f0: 0.37, l1: 0.28, f1: 0.62 }; // virada para Flávio
  if (uf === "AM") return { l0: 0.37, f0: 0.52, l1: 0.62, f1: 0.28 }; // virada para Lula
  let l = 0.42;
  let f = 0.46;
  if (NORDESTE.has(uf)) [l, f] = [0.62, 0.28];
  else if (SUL.has(uf)) [l, f] = [0.35, 0.53];
  else if (CENTRO_OESTE.has(uf)) [l, f] = [0.33, 0.55];
  else if (NORTE_DIREITA.has(uf)) [l, f] = [0.3, 0.58];
  else if (uf === "SP") [l, f] = [0.38, 0.48];
  else if (uf === "RJ") [l, f] = [0.4, 0.49];
  else if (uf === "ES") [l, f] = [0.38, 0.5];
  else if (uf === "DF") [l, f] = [0.4, 0.47];
  else if (["AP", "PA", "TO"].includes(uf)) [l, f] = [0.48, 0.42];
  return { l0: l, f0: f, l1: l, f1: f };
}

function menoresPres(uf: string): Record<string, number> {
  return {
    "55": uf === "GO" ? 0.17 : CENTRO_OESTE.has(uf) ? 0.06 : 0.03,
    "30": uf === "MG" ? 0.07 : 0.018,
    "70": 0.015,
    "14": 0.02,
    "80": 0.006,
    "27": 0.003,
    "21": 0.002,
    "16": 0.002,
    "35": 0.002,
    "29": 0.001,
  };
}

// ---------- modelo ----------
interface Unidade {
  uf: string;
  cd: string;
  cdi: string;
  nm: string;
  capital: boolean;
  te: number;
  ts: number;
  abre: number; // ms simulado
  fecha: number;
  desvio: number; // deslocamento Lula − Flávio
  semente: string;
}

interface Bruto {
  ts: number;
  st: number;
  te: number;
  c: number;
  vb: number;
  vn: number;
  vv: number;
  vap: number[];
}

interface Cargo {
  cd: number;
  ele: number;
  nome: string;
  nome_f: string;
}

const CARGOS: Readonly<Record<number, Cargo>> = {
  1: { cd: 1, ele: 6257, nome: "Presidente", nome_f: "Presidente" },
  3: { cd: 3, ele: 6259, nome: "Governador", nome_f: "Governadora" },
  5: { cd: 5, ele: 6259, nome: "Senador", nome_f: "Senadora" },
  6: { cd: 6, ele: 6259, nome: "Deputado Federal", nome_f: "Deputada Federal" },
  7: { cd: 7, ele: 6259, nome: "Deputado Estadual", nome_f: "Deputada Estadual" },
  8: { cd: 8, ele: 6259, nome: "Deputado Distrital", nome_f: "Deputada Distrital" },
};

const MIN = 60_000;
export const INICIO_MOCK = Date.parse("2026-10-04T16:59:30-03:00");
const DEZESSETE = Date.parse("2026-10-04T17:00:00-03:00");
const REGRESSAO = { uf: "BA", de: Date.parse("2026-10-04T18:40:00-03:00"), ate: Date.parse("2026-10-04T18:46:00-03:00"), fator: 0.96 };

function progresso(u: Pick<Unidade, "abre" | "fecha" | "uf">, t: number): number {
  if (t <= u.abre) return 0;
  const f = Math.min(1, (t - u.abre) / (u.fecha - u.abre));
  let p = 1 - (1 - f) ** 1.7;
  if (u.uf === REGRESSAO.uf && t >= REGRESSAO.de && t < REGRESSAO.ate && p < 1) p *= REGRESSAO.fator;
  return p;
}

/** Parcela acumulada quando a marginal anda linearmente de s0 a s1: s0·p + (s1 − s0)·p²/2, sobre p. */
const acumulada = (s0: number, s1: number, p: number): number => s0 * p + ((s1 - s0) * p * p) / 2;

export interface OpcoesMock {
  speed: number;
  config?: Config | null;
  campoDe?: (sg: string) => Campo;
  inicio?: number; // ms simulado inicial
  agoraReal?: () => number;
}

export function criarMock(o: OpcoesMock): Fonte & { agoraSimulado(): number } {
  const config = o.config && o.config.ufs.length > 0 ? o.config : AMOSTRA_CONFIG;
  const campoDe = o.campoDe ?? ((sg: string) => PARTIDO_CAMPO[sg.toUpperCase()] ?? "indefinido");
  const agoraReal = o.agoraReal ?? (() => Date.now());
  const real0 = agoraReal();
  const inicio = o.inicio ?? INICIO_MOCK;
  const speed = Math.max(0.1, o.speed);
  const agora = (): number => inicio + (agoraReal() - real0) * speed;

  // Unidades municipais com eleitorado e seções distribuídos pelo peso das zonas.
  const munPorUf = new Map<string, Unidade[]>();
  const munPorChave = new Map<string, Unidade>();
  for (const cu of config.ufs) {
    const uf = cu.uf.toUpperCase();
    const lista: ConfigMunicipio[] = config.municipios[uf] ?? config.municipios[uf.toLowerCase()] ?? [];
    const pesos = lista.map(m => m.te ?? Math.max(1, m.z.length) * (m.c ? 2.5 : 1) * (0.6 + aleatorio(`p${m.cd}`)));
    const soma = pesos.reduce((s, x) => s + x, 0) || 1;
    const durUf = (110 + 120 * aleatorio(`dur${uf}`)) * MIN;
    const unidades = lista.map((m, i) => {
      const te = m.te ?? Math.round((cu.te * (pesos[i] ?? 1)) / soma);
      const abre = DEZESSETE + aleatorio(`a${m.cd}`) * 12 * MIN;
      const fecha = abre + durUf * (0.55 + 0.5 * aleatorio(`f${m.cd}`)) + (m.c ? 45 * MIN : 0);
      const u: Unidade = {
        uf,
        cd: m.cd,
        cdi: m.cdi,
        nm: m.nm,
        capital: m.c,
        te,
        ts: Math.max(1, Math.round(te / 320)),
        abre,
        fecha,
        desvio: (aleatorio(`d${m.cd}`) - 0.5) * 0.16,
        semente: m.cd,
      };
      munPorChave.set(`${uf}:${m.cd}`, u);
      return u;
    });
    munPorUf.set(uf, unidades);
  }

  const zonasDe = (u: Unidade): Unidade[] => {
    const cm = (config.municipios[u.uf] ?? []).find(m => m.cd === u.cd);
    const zs = cm?.z.length ? cm.z : ["0001"];
    const pesos = zs.map(z => 0.5 + aleatorio(`z${u.cd}${z}`));
    const soma = pesos.reduce((s, x) => s + x, 0);
    return zs.map((z, i) => {
      const te = Math.round((u.te * (pesos[i] ?? 1)) / soma);
      return {
        ...u,
        cd: z,
        cdi: "",
        nm: `Zona ${Number(z)}`,
        te,
        ts: Math.max(1, Math.round(te / 320)),
        abre: u.abre + aleatorio(`za${u.cd}${z}`) * 5 * MIN,
        fecha: u.abre + (u.fecha - u.abre) * (0.8 + 0.4 * aleatorio(`zf${u.cd}${z}`)),
        desvio: u.desvio + (aleatorio(`zd${u.cd}${z}`) - 0.5) * 0.12,
        semente: `${u.cd}${z}`,
      };
    });
  };

  // Candidaturas por cargo e UF.
  const candCache = new Map<string, CandBase[]>();
  const vagas = (cargo: number, uf: string): number => {
    if (cargo === 1 || cargo === 3) return 1;
    if (cargo === 5) return 2;
    if (cargo === 8) return 24;
    const fed = VAGAS_FED[uf] ?? 8;
    return cargo === 6 ? fed : fed <= 12 ? 3 * fed : fed + 24;
  };
  const candidatos = (cargo: number, uf: string): CandBase[] => {
    if (cargo === 1) return [...PRESIDENTE_2026];
    const k = `${cargo}:${uf}`;
    const hit = candCache.get(k);
    if (hit) return hit;
    const qtd = cargo === 3 ? 5 : cargo === 5 ? 8 : 60;
    const ufIdx = String(config.ufs.findIndex(x => x.uf.toUpperCase() === uf) + 10);
    const lista: CandBase[] = [];
    for (let i = 0; i < qtd; i++) {
      const sg = PARTIDOS_SINTETICOS[Math.floor(aleatorio(`sg${k}${i}`) * PARTIDOS_SINTETICOS.length)] ?? "PSD";
      const base = cargo === 3 || cargo === 5 ? 10 + i * 11 : 1000 + i * 37;
      const n = String(cargo === 5 ? base * 10 + 1 : base);
      lista.push({ n, sqcand: `9${cargo}${ufIdx}${String(i).padStart(4, "0")}`, nmu: `CANDIDATURA ${n} ${uf}`, sg });
    }
    candCache.set(k, lista);
    return lista;
  };

  /** Parcelas (início e fim) dos candidatos numa unidade. */
  const parcelas = (cargo: number, u: Unidade): { s0: number[]; s1: number[] } => {
    const cands = candidatos(cargo, u.uf);
    if (cargo === 1) {
      const d = duelo(u.uf);
      const menores = menoresPres(u.uf);
      const somaMen = Object.values(menores).reduce((s, x) => s + x, 0);
      // Nas UFs de virada forçada o desvio municipal é amortecido para a virada acontecer em todo município grande.
      const desvio = VIRADAS.has(u.uf) ? u.desvio * 0.3 : u.desvio;
      const fase = (l: number, f: number): number[] => {
        const ll = Math.max(0.02, l + desvio);
        const ff = Math.max(0.02, f - desvio);
        const escala = (1 - somaMen) / (ll + ff);
        return cands.map(c => (c.n === "13" ? ll * escala : c.n === "22" ? ff * escala : (menores[c.n] ?? 0.001) * (0.7 + 0.6 * aleatorio(`m${c.n}${u.semente}`))));
      };
      return norm2(fase(d.l0, d.f0), fase(d.l1, d.f1));
    }
    const forca = cands.map((c, i) => {
      const w = cargo === 3 || cargo === 5 ? 1.5 / (i + 1) ** 1.1 : 1 / (i + 1) ** 0.9;
      return w * (0.6 + 0.8 * aleatorio(`w${c.sqcand}`)) * (0.85 + 0.3 * aleatorio(`w${c.sqcand}${u.semente}`));
    });
    const fim = forca.map((w, i) => w * (0.8 + 0.4 * aleatorio(`v${i}${cargo}${u.uf}`)));
    return norm2(forca, fim);
  };

  const bruto = (cargo: number, u: Unidade, t: number): Bruto => {
    const p = progresso(u, t);
    const comparecimento = 0.79 + 0.04 * (aleatorio(`c${u.semente}`) - 0.5);
    const comparecem = u.te * comparecimento * p;
    const vb = Math.round(comparecem * (cargo === 1 ? 0.022 : 0.045));
    const vn = Math.round(comparecem * (cargo === 1 ? 0.038 : 0.06));
    const vvFinal = u.te * comparecimento * (1 - (cargo === 1 ? 0.06 : 0.105));
    const { s0, s1 } = parcelas(cargo, u);
    const vap = s0.map((a, i) => Math.round(vvFinal * acumulada(a, s1[i] ?? a, p)));
    const vv = vap.reduce((s, x) => s + x, 0);
    return { ts: u.ts, st: Math.floor(u.ts * p), te: u.te, c: vv + vb + vn, vb, vn, vv, vap };
  };

  const somar = (lista: Bruto[], n: number): Bruto => {
    const acc: Bruto = { ts: 0, st: 0, te: 0, c: 0, vb: 0, vn: 0, vv: 0, vap: new Array<number>(n).fill(0) };
    for (const b of lista) {
      acc.ts += b.ts;
      acc.st += b.st;
      acc.te += b.te;
      acc.c += b.c;
      acc.vb += b.vb;
      acc.vn += b.vn;
      acc.vv += b.vv;
      b.vap.forEach((v, i) => (acc.vap[i] = (acc.vap[i] ?? 0) + v));
    }
    return acc;
  };

  // Cache por segundo simulado, com teto de entradas (séries pedem instantes antigos).
  const cache = new Map<string, Bruto>();
  const memo = (k: string, t: number, f: () => Bruto): Bruto => {
    const kk = `${k}@${Math.floor(t / 1000)}`;
    let b = cache.get(kk);
    if (!b) {
      if (cache.size > 6000) cache.clear();
      b = f();
      cache.set(kk, b);
    }
    return b;
  };

  const brutoUf = (cargo: number, uf: string, t: number): Bruto =>
    memo(`${cargo}:${uf}`, t, () => somar((munPorUf.get(uf) ?? []).map(u => bruto(cargo, u, t)), candidatos(cargo, uf).length));

  const brutoBr = (t: number): Bruto =>
    memo(`1:br`, t, () => somar([...munPorUf.keys()].map(uf => brutoUf(1, uf, t)), PRESIDENTE_2026.length));

  interface Escopo {
    tpabr: Resultado["tpabr"];
    uf: string | null;
    mun: Unidade | null;
    zona: Unidade | null;
    nome: string;
  }

  const lerAbr = (abr: string): Escopo => {
    const m = /^([a-z]{2})(\d{5})?(?:-z(\d{1,4}))?$/i.exec(abr);
    if (abr === "br" || !m) return { tpabr: "br", uf: null, mun: null, zona: null, nome: "Brasil" };
    const uf = (m[1] ?? "").toUpperCase();
    const nomeUf = config.ufs.find(x => x.uf.toUpperCase() === uf)?.nome ?? uf;
    if (!m[2]) return { tpabr: "uf", uf, mun: null, zona: null, nome: nomeUf };
    const mun = munPorChave.get(`${uf}:${m[2]}`);
    if (!mun) throw new ErroApi(404, abr);
    if (!m[3]) return { tpabr: "mu", uf, mun, zona: null, nome: mun.nm };
    const zona = zonasDe(mun).find(z => Number(z.cd) === Number(m[3]));
    if (!zona) throw new ErroApi(404, abr);
    return { tpabr: "zona", uf, mun, zona, nome: `${mun.nm}, ${zona.nm.toLowerCase()}` };
  };

  const brutoEscopo = (cargo: number, e: Escopo, t: number): Bruto => {
    if (e.zona) return bruto(cargo, e.zona, t);
    if (e.mun) return bruto(cargo, e.mun, t);
    if (e.uf) return brutoUf(cargo, e.uf, t);
    if (cargo !== 1) throw new ErroApi(404, `br cargo ${cargo}`);
    return brutoBr(t);
  };

  const montarResultado = (cargo: number, e: Escopo, t: number): Resultado => {
    const b = brutoEscopo(cargo, e, t);
    const cands = candidatos(cargo, e.uf ?? "BR");
    const cg = CARGOS[cargo] ?? CARGOS[1];
    const nv = vagas(cargo, e.uf ?? "BR");
    const pst = b.ts > 0 ? (100 * b.st) / b.ts : 0;
    const tf = b.st >= b.ts && b.ts > 0;
    const lista: Candidato[] = cands.map((c, i) => ({
      sqcand: c.sqcand,
      n: c.n,
      nm: c.nmu,
      nmu: c.nmu,
      sg: c.sg,
      campo: campoDe(c.sg),
      ...(c.fed_sg ? { fed_sg: c.fed_sg } : {}),
      e: false,
      st: "",
      dvt: cargo === 6 && i === 7 ? "Anulado sub judice" : "Válido",
      vap: b.vap[i] ?? 0,
      pvapn: b.vv > 0 ? (100 * (b.vap[i] ?? 0)) / b.vv : 0,
      vs: [],
    }));
    if (tf && e.tpabr !== "mu" && e.tpabr !== "zona") situacoes(cargo, nv, lista);
    const partidos = new Map<string, PartidoResultado>();
    for (const c of lista) {
      const p = partidos.get(c.sg) ?? { sg: c.sg, campo: c.campo, tvtn: 0, tvan: 0, n_cand: 0 };
      p.tvtn += c.vap;
      p.n_cand += 1;
      partidos.set(c.sg, p);
    }
    const iso = new Date(t).toISOString();
    return {
      cargo: { cd: cg?.cd ?? cargo, nome: cg?.nome ?? "", nome_f: cg?.nome_f ?? "", nv },
      tpabr: e.tpabr,
      abr: e.tpabr === "br" ? "br" : (e.uf ?? "").toLowerCase() + (e.mun ? e.mun.cd : "") + (e.zona ? `-z${e.zona.cd}` : ""),
      nome_escopo: e.nome,
      dg_hg: new Date(t - 9_000).toISOString(),
      dt_ht: b.st > 0 ? new Date(t - 21_000).toISOString() : null,
      lido_em: iso,
      tf,
      s: { ts: b.ts, st: b.st, pst },
      e: { te: b.te, c: b.c, a: Math.round(b.te * (pst / 100)) - b.c, pc: pst > 0 ? (100 * b.c) / ((b.te * pst) / 100) : 0, pa: 0 },
      v: {
        tv: b.c,
        vv: b.vv,
        vvc: b.vv,
        vnom: b.vv,
        van: 0,
        vb: b.vb,
        vn: b.vn,
        pvb: b.c > 0 ? (100 * b.vb) / b.c : 0,
        pvn: b.c > 0 ? (100 * b.vn) / b.c : 0,
        pvan: 0,
      },
      cand: lista,
      partidos: [...partidos.values()].sort((a, z) => z.tvtn - a.tvtn),
    };
  };

  const lider = (c: Candidato): LiderUnidade => ({ sqcand: c.sqcand, n: c.n, nmu: c.nmu, sg: c.sg, campo: c.campo, vap: c.vap, pvapn: c.pvapn });

  const unidadeMapa = (cargo: number, e: Escopo, cd: string, cdi: string, nm: string, t: number): UnidadeMapa => {
    const r = montarResultado(cargo, e, t);
    const ord = [...r.cand].sort((a, b) => b.vap - a.vap);
    const [a, b] = ord;
    const temVoto = (a?.vap ?? 0) > 0;
    return {
      cd,
      ...(cdi ? { cdi } : {}),
      nm,
      te: r.e.te,
      pst: r.s.pst,
      tf: r.tf,
      ...(temVoto && a ? { lider: lider(a) } : {}),
      ...(temVoto && b ? { segundo: lider(b) } : {}),
      ...(temVoto && a && b ? { margem: a.pvapn - b.pvapn } : {}),
      ...(temVoto ? { top: ord.slice(0, r.cargo.nv).map(lider) } : {}),
    };
  };

  const resultado = (q: ConsultaResultado, t = agora()): Resultado => montarResultado(q.cargo, lerAbr(q.abr), t);

  const mapa = (q: ConsultaMapa, t = agora()): Mapa => {
    if (q.nivel === "uf") {
      if (q.cargo !== 1 && q.cargo !== 3 && q.cargo !== 5) return { unidades: [] };
      return {
        unidades: config.ufs.map(u =>
          unidadeMapa(q.cargo, { tpabr: "uf", uf: u.uf.toUpperCase(), mun: null, zona: null, nome: u.nome }, u.uf.toUpperCase(), u.cdi, u.nome, t),
        ),
      };
    }
    if (q.nivel === "mun") {
      const uf = q.pai.toUpperCase();
      return {
        unidades: (munPorUf.get(uf) ?? []).map(m => unidadeMapa(q.cargo, { tpabr: "mu", uf, mun: m, zona: null, nome: m.nm }, m.cd, m.cdi, m.nm, t)),
      };
    }
    const e = lerAbr(q.pai);
    if (!e.mun) return { unidades: [] };
    const mun = e.mun;
    return {
      unidades: zonasDe(mun).map(z => unidadeMapa(q.cargo, { tpabr: "zona", uf: e.uf, mun, zona: z, nome: z.nm }, z.cd, "", z.nm, t)),
    };
  };

  const serie = (q: ConsultaResultado, t = agora()): Serie => {
    const pontos: Serie["pontos"] = [];
    const viradas: Serie["viradas"] = [];
    let anterior: string | null = null;
    for (let s = DEZESSETE + 5 * MIN; s <= t; s += 5 * MIN) {
      const r = resultado(q, s);
      if (r.s.st === 0) continue;
      const cand: Record<string, number> = {};
      let melhor: Candidato | null = null;
      for (const c of r.cand) {
        cand[c.sqcand] = c.pvapn;
        if (!melhor || c.vap > melhor.vap) melhor = c;
      }
      const at = new Date(s).toISOString();
      pontos.push({ at, pst: r.s.pst, cand });
      if (melhor && anterior && melhor.sqcand !== anterior) viradas.push({ at, de: anterior, para: melhor.sqcand });
      if (melhor) anterior = melhor.sqcand;
    }
    return { pontos, viradas };
  };

  // Anomalias: viradas de MG e AM, regressão da BA, fechamento de cada UF.
  const fechamentoUf = (uf: string): number => Math.max(...(munPorUf.get(uf) ?? []).map(u => u.fecha), DEZESSETE);
  const viradasCache = new Map<string, number | null>();
  const instanteVirada = (uf: string): number | null => {
    if (viradasCache.has(uf)) return viradasCache.get(uf) ?? null;
    let anterior: string | null = null;
    let achou: number | null = null;
    for (let s = DEZESSETE + 2 * MIN; s <= fechamentoUf(uf) + MIN; s += 2 * MIN) {
      const r = resultado({ ele: 6257, cargo: 1, abr: uf.toLowerCase() }, s);
      const m = [...r.cand].sort((a, b) => b.vap - a.vap)[0];
      if (!m || m.vap === 0) continue;
      if (anterior && m.sqcand !== anterior) {
        achou = s;
        break;
      }
      anterior = m.sqcand;
    }
    viradasCache.set(uf, achou);
    return achou;
  };

  const nomeUf = (uf: string): string => config.ufs.find(x => x.uf.toUpperCase() === uf)?.nome ?? uf;
  const horaBr = (ms: number): string =>
    new Intl.DateTimeFormat("pt-BR", { timeZone: "America/Sao_Paulo", hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).format(ms);

  const anomalias = (t = agora()): Anomalia[] => {
    const saida: Anomalia[] = [];
    for (const uf of VIRADAS) {
      const v = instanteVirada(uf);
      if (v !== null && v <= t && munPorUf.has(uf)) {
        const r = resultado({ ele: 6257, cargo: 1, abr: uf.toLowerCase() }, v);
        const m = [...r.cand].sort((a, b) => b.vap - a.vap)[0];
        saida.push({ at: new Date(v).toISOString(), tipo: "virada", abr: uf.toLowerCase(), cargo: 1, texto: `virada em ${nomeUf(uf)}: ${m ? nomeCurto(m.nmu) : ""} passa à frente às ${horaBr(v)}` });
      }
    }
    if (REGRESSAO.de <= t && munPorUf.has(REGRESSAO.uf)) {
      saida.push({ at: new Date(REGRESSAO.de).toISOString(), tipo: "regressao", abr: "ba", cargo: 1, texto: `seções totalizadas recuaram na ${nomeUf(REGRESSAO.uf)} às ${horaBr(REGRESSAO.de)}` });
    }
    for (const uf of munPorUf.keys()) {
      const f = fechamentoUf(uf);
      if (f <= t) saida.push({ at: new Date(f).toISOString(), tipo: "fechou", abr: uf.toLowerCase(), cargo: 1, texto: `${nomeUf(uf)} fechou às ${horaBr(f)}` });
    }
    return saida.sort((a, b) => b.at.localeCompare(a.at));
  };

  const estado = (t = agora()): Estado => {
    const br = brutoBr(t);
    const ufs = config.ufs.map(cu => {
      const uf = cu.uf.toUpperCase();
      const lista = munPorUf.get(uf) ?? [];
      const b = brutoUf(1, uf, t);
      let munnr = 0;
      let munpt = 0;
      let munf = 0;
      for (const u of lista) {
        const p = progresso(u, t);
        if (p <= 0) munnr++;
        else if (p >= 1) munf++;
        else munpt++;
      }
      const f = fechamentoUf(uf);
      return {
        uf,
        pst: b.ts > 0 ? (100 * b.st) / b.ts : 0,
        st: b.st,
        ts: b.ts,
        munnr,
        munpt,
        munf,
        dt_ht: b.st > 0 ? new Date(t - 21_000).toISOString() : null,
        fechou_em: f <= t ? new Date(f).toISOString() : null,
      };
    });
    const historico: Estado["historico"] = [];
    for (let s = DEZESSETE; s <= t; s += 5 * MIN) {
      const h = brutoBr(s);
      historico.push({ at: new Date(s).toISOString(), st: h.st, pst: h.ts > 0 ? (100 * h.st) / h.ts : 0 });
    }
    const lat = (k: string, base: number, amp: number): number[] =>
      Array.from({ length: 60 }, (_, i) => Math.round(base + amp * aleatorio(`${k}${i}${Math.floor(t / 60_000)}`)));
    const atraso = br.st > 0 ? 20 + Math.round(30 * aleatorio(`at${Math.floor(t / 30_000)}`)) : null;
    return {
      agora: new Date(t).toISOString(),
      turno: config.turno,
      br: {
        ts: br.ts,
        st: br.st,
        pst: br.ts > 0 ? (100 * br.st) / br.ts : 0,
        dt_ht: br.st > 0 ? new Date(t - 21_000).toISOString() : null,
        hg: new Date(t - 9_000).toISOString(),
        lido_em: new Date(t).toISOString(),
        atraso_s: atraso,
      },
      ufs,
      historico,
      latencias: { leitura_menos_hg: lat("l", 4, 40), hg_menos_ht: lat("g", 8, 30) },
    };
  };

  const eventos = (fn: (e: EventoSse) => void): (() => void) => {
    let ultimoSt = new Map<string, number>();
    let ultimasAnomalias = anomalias().length;
    let id = 0;
    const tick = (): void => {
      const t = agora();
      const at = new Date(t).toISOString();
      fn({ kind: "estado", ele: 6257, cargo: 0, abr: "br", snapshot_id: ++id, at });
      const atual = new Map<string, number>();
      for (const uf of munPorUf.keys()) {
        const st = brutoUf(1, uf, t).st;
        atual.set(uf, st);
        if (ultimoSt.get(uf) !== st) {
          for (const cargo of [1, 3, 5, 6, uf === "DF" ? 8 : 7]) {
            fn({ kind: "resultado", ele: CARGOS[cargo]?.ele ?? 6259, cargo, abr: uf.toLowerCase(), snapshot_id: ++id, at });
          }
        }
      }
      if ([...atual.entries()].some(([uf, st]) => ultimoSt.get(uf) !== st)) {
        fn({ kind: "resultado", ele: 6257, cargo: 1, abr: "br", snapshot_id: ++id, at });
      }
      ultimoSt = atual;
      const n = anomalias(t).length;
      if (n !== ultimasAnomalias) fn({ kind: "anomalia", ele: 6257, cargo: 1, abr: "br", snapshot_id: ++id, at });
      ultimasAnomalias = n;
    };
    const timer = setInterval(tick, 1000);
    return () => clearInterval(timer);
  };

  const atrasar = <T>(f: () => T): Promise<T> =>
    new Promise((ok, falha) => {
      try {
        ok(f());
      } catch (e) {
        falha(e);
      }
    });

  return {
    tipo: "mock",
    agoraSimulado: agora,
    config: () => Promise.resolve(config),
    estado: () => atrasar(() => estado()),
    resultado: q => atrasar(() => resultado(q)),
    mapa: q => atrasar(() => mapa(q)),
    serie: q => atrasar(() => serie(q)),
    anomalias: () => atrasar(() => anomalias()),
    auditoria: caminho => Promise.resolve({ mock: true, caminho }),
    eventos,
  };
}

function norm2(a: number[], b: number[]): { s0: number[]; s1: number[] } {
  const n = (v: number[]): number[] => {
    const s = v.reduce((x, y) => x + y, 0) || 1;
    return v.map(x => x / s);
  };
  return { s0: n(a), s1: n(b) };
}

/** Situação de fim de totalização (só o mock decide; o telão real lê o st do TSE). */
function situacoes(cargo: number, nv: number, lista: Candidato[]): void {
  const ord = [...lista].sort((a, b) => b.vap - a.vap);
  if (cargo === 1 || cargo === 3) {
    const [a, b] = ord;
    if (a && a.pvapn > 50) {
      a.e = true;
      a.st = "Eleito";
    } else {
      if (a) a.st = "2º turno";
      if (b) b.st = "2º turno";
    }
    return;
  }
  ord.forEach((c, i) => {
    c.e = i < nv;
    c.st = i < nv ? "Eleito" : "Não eleito";
  });
}

function nomeCurto(nmu: string): string {
  return nmu
    .toLocaleLowerCase("pt-BR")
    .split(" ")
    .map(w => (w === "de" || w === "da" || w === "do" ? w : w.charAt(0).toLocaleUpperCase("pt-BR") + w.slice(1)))
    .join(" ");
}
