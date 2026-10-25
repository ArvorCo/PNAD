// Projeção estatística do resultado final do 2º turno a partir do que já foi totalizado
// (/api/2t/projecao). Função pura: recebe a régua de votos do 1º turno por município e o estado
// observado de cada município no 2º turno; devolve Brasil, regiões e UFs.
//
// Método (oscilação proporcional por município com pooling parcial; contrato em
// ../../../../analysis/apuracao_2t_2026/CONTRATO.md):
// 1. p2 = f2/(f2+l2) observado; p1 = parte de Flávio no 1º turno no mesmo estágio da contagem do
//    município (mesma fração de seções, pela trajetória da noite de 04/10); oscilação d = p2 − p1.
//    Comparar com o final do 1º turno herdaria o viés de ordem (as primeiras seções de cada
//    município são mais favoráveis a Flávio) e projetava +1,5 ponto às 18:00 na validação.
// 2. Oscilação da UF = média de d ponderada pelos votos dos dois (n), encolhida para a nacional
//    com peso N_uf/(N_uf + K_uf); UF sem observação usa a nacional.
// 3. Oscilação do município = λ d + (1 − λ) d_uf, λ = n/(n + K): município com poucos votos
//    contados fica perto da UF.
// 4. Parte não observada = votos dos dois que faltavam no 1º turno nesse estágio × r_uf, com a
//    parte de Flávio desses votos mais a oscilação; r_uf é a razão entre
//    os votos dos dois no 2º turno e no 1º nos municípios observados (fechados, quando somam ao
//    menos R_MIN_FECHADOS votos do 1º turno; senão todos, no mesmo estágio).
// 5. Faixa de 90%: bootstrap dos municípios observados dentro de cada UF, resíduo municipal
//    sorteado entre os observados e um erro comum normal de ERRO_COMUM_PP pontos, aplicados só ao
//    que falta totalizar (a faixa fecha quando tudo foi totalizado).
// Não é resultado nem previsão de vitória: projeção condicionada ao que já foi contado.
import type { Regiao } from "../../turno2/comum.ts";
import { NOME_REGIAO, ORDEM_REGIOES, REGIOES } from "../../turno2/comum.ts";
import type { MunVotos1T } from "../../turno2/referencia.ts";
import { pstDe, r2 } from "./base.ts";

export const ROTULO_PROJECAO = "projeção estatística a partir do que já foi totalizado; não é resultado nem previsão de vitória";
export const K_PADRAO = 2000;
export const K_UF_PADRAO = 20_000;
export const ERRO_COMUM_PP = 1.0;
export const REPS_PADRAO = 200;
export const MINIMO_PST = 1;
export const NIVEL_FAIXA = 90;
export const SEMENTE = 20_261_025;
/** Votos dos dois no 1º turno, nos municípios fechados da UF, para usar só eles na razão r_uf. */
export const R_MIN_FECHADOS = 20_000;

export const METODO =
  "oscilação proporcional por município contra o 1º turno no mesmo estágio da contagem (mesma fração de seções), com pooling parcial: município pesa n/(n+K) e o resto vem da UF; " +
  "UF pesa N/(N+K_uf) e o resto vem do Brasil; parte não totalizada = votos dos dois que faltavam no 1º turno nesse estágio × razão de comparecimento dos dois observada; " +
  "faixa de 90% por bootstrap dos municípios observados dentro da UF, resíduo municipal e erro comum, só sobre o que falta totalizar";

/** Estado observado de um município no 2º turno (arquivo mu da eleição federal, cargo 1). */
export interface ObsMun {
  uf: string;
  cd: string;
  st: number;
  ts: number;
  /** votos de Flávio (22) */
  f2: number;
  /** votos de Lula (13) */
  l2: number;
  /** votos válidos (no 2º turno, f2 + l2) */
  vv2: number;
}

export interface EntradaProjecao {
  /** UF em caixa alta → código de 5 dígitos → votos do 1º turno */
  ref: Readonly<Record<string, Readonly<Record<string, MunVotos1T>>>>;
  obs: readonly ObsMun[];
  K?: number;
  K_uf?: number;
  /** Compara com o 1º turno no mesmo estágio da contagem do município (padrão true). */
  mesmoEstagio?: boolean;
  erroComumPp?: number;
  reps?: number;
  semente?: number;
  minimoPst?: number;
}

export interface Projetado {
  f: number;
  l: number;
  p_f: number;
  p_l: number;
  p_f_validos: number;
  p_l_validos: number;
  faixa90: [number, number];
}

export interface BlocoProjecao {
  sigla: string;
  nome: string;
  pst: number;
  pct_vv_observado: number;
  p1_f: number | null;
  observado: { f: number; l: number; p_f: number | null };
  projetado: Projetado | null;
  swing_pp: number | null;
}

export interface ResultadoProjecao {
  cobertura: {
    pst: number;
    st: number;
    ts: number;
    pct_vv_observado: number;
    municipios_observados: number;
    municipios_fechados: number;
    municipios_total: number;
  };
  brasil: BlocoProjecao;
  regioes: BlocoProjecao[];
  ufs: BlocoProjecao[];
  parametros: { K: number; K_uf: number; mesmo_estagio: boolean; erro_comum_pp: number; reps: number; nivel_faixa: number; minimo_pst: number; metodo: string };
  motivo_sem_projecao: string | null;
}

interface Unidade {
  uf: string;
  ref: MunVotos1T | null;
  /** f1 + l1 */
  v1: number;
  p1: number | null;
  /** votos dos dois no 1º turno no mesmo estágio da contagem (fração de seções) */
  v1w: number;
  /** votos dos dois que faltavam no 1º turno nesse estágio, e a parte de Flávio neles */
  rv: number;
  p1rest: number;
  st: number;
  ts: number;
  w: number;
  f2: number;
  l2: number;
  vv2: number;
  n: number;
  d: number;
  observada: boolean;
  fechada: boolean;
}

/** Gerador determinístico (mulberry32): a faixa não treme entre chamadas com os mesmos dados. */
function rng(semente: number): () => number {
  let a = semente >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function normal(u: () => number): number {
  const a = Math.max(u(), 1e-12);
  return Math.sqrt(-2 * Math.log(a)) * Math.cos(2 * Math.PI * u());
}

function quantil(ordenado: readonly number[], q: number): number {
  if (ordenado.length === 0) return Number.NaN;
  const pos = q * (ordenado.length - 1);
  const i = Math.floor(pos);
  const f = pos - i;
  const a = ordenado[i] ?? 0;
  const b = ordenado[Math.min(i + 1, ordenado.length - 1)] ?? a;
  return a + f * (b - a);
}

const clamp01 = (x: number): number => (x < 0 ? 0 : x > 1 ? 1 : x);

/** Votos [Flávio, Lula] do 1º turno do município quando ele tinha a fração `w` das seções (interpolação linear). */
export function estagio1T(ref: MunVotos1T, w: number): [number, number] {
  if (w >= 1 || !ref.c || !ref.ts1 || ref.ts1 <= 0) return w >= 1 ? [ref.f1, ref.l1] : [ref.f1 * w, ref.l1 * w];
  let ant: [number, number, number] = [0, 0, 0];
  for (const p of ref.c) {
    const wp = p[0] / ref.ts1;
    if (wp >= w) {
      const wa = ant[0] / ref.ts1;
      const f = wp > wa ? (w - wa) / (wp - wa) : 1;
      return [ant[1] + f * (p[1] - ant[1]), ant[2] + f * (p[2] - ant[2])];
    }
    ant = p;
  }
  const wa = ant[0] / ref.ts1;
  const f = wa < 1 ? (w - wa) / (1 - wa) : 1;
  return [ant[1] + f * (ref.f1 - ant[1]), ant[2] + f * (ref.l1 - ant[2])];
}

function unidades(e: EntradaProjecao): Unidade[] {
  const obsPor = new Map<string, ObsMun>();
  for (const o of e.obs) obsPor.set(`${o.uf.toUpperCase()}|${o.cd.padStart(5, "0")}`, o);
  const vistos = new Set<string>();
  const out: Unidade[] = [];
  const estagio = e.mesmoEstagio ?? true;
  const montar = (uf: string, ref: MunVotos1T | null, o: ObsMun | undefined): Unidade => {
    const v1 = ref ? ref.f1 + ref.l1 : 0;
    const p1 = ref && v1 > 0 ? ref.f1 / v1 : null;
    const st = o?.st ?? 0;
    const ts = o?.ts ?? 0;
    const w = ts > 0 ? clamp01(st / ts) : 0;
    const f2 = o?.f2 ?? 0;
    const l2 = o?.l2 ?? 0;
    const n = f2 + l2;
    const observada = st > 0 && n > 0;
    // 1º turno no mesmo estágio: sem trajetória (ou com o ajuste desligado), a fração das seções.
    const [fw, lw] = ref && p1 !== null ? (estagio ? estagio1T(ref, w) : [ref.f1 * w, ref.l1 * w]) : [0, 0];
    const v1w = fw + lw;
    const p1w = v1w > 0 ? fw / v1w : p1;
    const rv = Math.max(0, v1 - v1w);
    const p1rest = rv > 0 ? clamp01((ref?.f1 ?? 0) - fw > 0 ? ((ref?.f1 ?? 0) - fw) / rv : 0) : (p1 ?? 0);
    return {
      uf, ref, v1, p1, v1w, rv, p1rest, st, ts, w, f2, l2, vv2: o?.vv2 ?? 0, n,
      d: observada && p1w !== null ? f2 / n - p1w : 0,
      observada,
      fechada: ts > 0 && st >= ts,
    };
  };
  for (const [ufRaw, muns] of Object.entries(e.ref)) {
    const uf = ufRaw.toUpperCase();
    for (const [cd, ref] of Object.entries(muns)) {
      const k = `${uf}|${cd.padStart(5, "0")}`;
      vistos.add(k);
      out.push(montar(uf, ref, obsPor.get(k)));
    }
  }
  for (const [k, o] of obsPor) if (!vistos.has(k)) out.push(montar(o.uf.toUpperCase(), null, o));
  return out;
}

interface Swing {
  /** oscilação média ponderada e votos observados por UF */
  uf: Map<string, { d: number; n: number }>;
  br: { d: number; n: number };
}

function swingDe(obs: readonly Unidade[]): Swing {
  const uf = new Map<string, { d: number; n: number }>();
  let sd = 0;
  let sn = 0;
  for (const u of obs) {
    if (u.p1 === null) continue;
    const a = uf.get(u.uf) ?? { d: 0, n: 0 };
    a.d += u.n * u.d;
    a.n += u.n;
    uf.set(u.uf, a);
    sd += u.n * u.d;
    sn += u.n;
  }
  for (const a of uf.values()) a.d = a.n > 0 ? a.d / a.n : 0;
  return { uf, br: { d: sn > 0 ? sd / sn : 0, n: sn } };
}

/** Oscilação da UF encolhida para a nacional. */
function dUf(s: Swing, uf: string, kUf: number): number {
  const a = s.uf.get(uf);
  if (!a || a.n <= 0) return s.br.d;
  const lam = a.n / (a.n + kUf);
  return lam * a.d + (1 - lam) * s.br.d;
}

/** Razão de votos dos dois (2º turno sobre 1º) por UF e nacional. */
function razoes(us: readonly Unidade[]): { uf: Map<string, number>; br: number } {
  const acc = new Map<string, { fn: number; fd: number; on: number; od: number }>();
  const tot = { fn: 0, fd: 0, on: 0, od: 0 };
  for (const u of us) {
    if (!u.observada || u.v1 <= 0) continue;
    const a = acc.get(u.uf) ?? { fn: 0, fd: 0, on: 0, od: 0 };
    for (const x of [a, tot]) {
      if (u.fechada) {
        x.fn += u.n;
        x.fd += u.v1;
      }
      x.on += u.n;
      x.od += u.v1w;
    }
    acc.set(u.uf, a);
  }
  const r = (x: { fn: number; fd: number; on: number; od: number }): number | null =>
    x.fd >= R_MIN_FECHADOS ? x.fn / x.fd : x.od > 0 ? x.on / x.od : null;
  const br = r(tot) ?? 1;
  const uf = new Map<string, number>();
  for (const [k, x] of acc) uf.set(k, r(x) ?? br);
  return { uf, br };
}

interface Soma {
  F: number;
  L: number;
}

/**
 * Projeta todas as unidades e soma por UF. `ruido(u)` devolve o deslocamento extra (resíduo e
 * erro comum) da parte não observada; `dUfDe(uf)` a oscilação da UF.
 */
function projetarUfs(us: readonly Unidade[], k: number, dUfDe: (uf: string) => number, r: { uf: Map<string, number>; br: number }, ruido: (u: Unidade) => number): Map<string, Soma> {
  const out = new Map<string, Soma>();
  for (const u of us) {
    let F: number;
    let L: number;
    if (u.fechada && u.observada) {
      F = u.f2;
      L = u.l2;
    } else if (u.p1 === null) {
      // Município sem 1º turno: só o observado, expandido pela fração de seções.
      if (u.w <= 0) continue;
      F = u.f2 / u.w;
      L = u.l2 / u.w;
    } else {
      const lam = u.observada ? u.n / (u.n + k) : 0;
      const ds = lam * u.d + (1 - lam) * dUfDe(u.uf) + ruido(u);
      const q = clamp01(u.p1rest + ds);
      const resto = u.rv * (r.uf.get(u.uf) ?? r.br);
      F = u.f2 + resto * q;
      L = u.l2 + resto * (1 - q);
    }
    const a = out.get(u.uf) ?? { F: 0, L: 0 };
    a.F += F;
    a.L += L;
    out.set(u.uf, a);
  }
  return out;
}

interface Conjunto {
  /** chave única (a sigla SE é ao mesmo tempo Sudeste e Sergipe) */
  chave: string;
  sigla: string;
  nome: string;
  ufs: readonly string[];
}

function conjuntos(): { brasil: Conjunto; regioes: Conjunto[]; ufs: Conjunto[] } {
  const todas = ORDEM_REGIOES.flatMap((r: Regiao) => REGIOES[r]);
  return {
    brasil: { chave: "br", sigla: "BR", nome: "Brasil", ufs: todas },
    regioes: ORDEM_REGIOES.map((r: Regiao) => ({ chave: `r:${r}`, sigla: r, nome: NOME_REGIAO[r], ufs: REGIOES[r] })),
    ufs: todas.map((uf) => ({ chave: `u:${uf}`, sigla: uf, nome: uf, ufs: [uf] })),
  };
}

function somaEm(m: ReadonlyMap<string, Soma>, ufs: readonly string[]): Soma {
  const s = { F: 0, L: 0 };
  for (const uf of ufs) {
    const a = m.get(uf);
    if (a) {
      s.F += a.F;
      s.L += a.L;
    }
  }
  return s;
}

export function projetar(e: EntradaProjecao): ResultadoProjecao {
  const K = e.K ?? K_PADRAO;
  const kUf = e.K_uf ?? K_UF_PADRAO;
  const erro = e.erroComumPp ?? ERRO_COMUM_PP;
  const reps = e.reps ?? REPS_PADRAO;
  const minimo = e.minimoPst ?? MINIMO_PST;
  const us = unidades(e);
  const obs = us.filter((u) => u.observada);
  const sw = swingDe(obs);
  const r = razoes(us);
  const cj = conjuntos();

  let stBr = 0;
  let tsBr = 0;
  for (const u of us) {
    stBr += u.st;
    tsBr += u.ts;
  }
  const pstBr = pstDe(stBr, tsBr);
  const motivo =
    obs.length === 0
      ? "nenhum município com votos totalizados no 2º turno ainda"
      : pstBr < minimo
        ? `menos de ${String(minimo).replace(".", ",")}% das seções do país totalizadas (${String(pstBr).replace(".", ",")}%): base pequena e concentrada demais para projetar`
        : null;

  const central = projetarUfs(us, K, (uf) => dUf(sw, uf, kUf), r, () => 0);

  // Bootstrap: só quando há projeção.
  const amostras = new Map<string, number[]>();
  if (motivo === null && reps > 0) {
    const u01 = rng(e.semente ?? SEMENTE);
    const obsPorUf = new Map<string, Unidade[]>();
    for (const u of obs) {
      if (u.p1 === null) continue;
      const lista = obsPorUf.get(u.uf);
      if (lista) lista.push(u);
      else obsPorUf.set(u.uf, [u]);
    }
    // Resíduos (d − d_uf) com peso n, para sortear o desvio próprio de cada município não observado.
    const residuos = new Map<string, { cum: number[]; res: number[] }>();
    const todosRes: { cum: number[]; res: number[] } = { cum: [], res: [] };
    for (const [uf, lista] of obsPorUf) {
      const media = sw.uf.get(uf)?.d ?? 0;
      const x = { cum: [] as number[], res: [] as number[] };
      let c = 0;
      for (const u of lista) {
        c += u.n;
        x.cum.push(c);
        x.res.push(u.d - media);
        todosRes.cum.push((todosRes.cum[todosRes.cum.length - 1] ?? 0) + u.n);
        todosRes.res.push(u.d - media);
      }
      residuos.set(uf, x);
    }
    const sortear = (x: { cum: number[]; res: number[] }): number => {
      const tot = x.cum[x.cum.length - 1] ?? 0;
      if (tot <= 0) return 0;
      const alvo = u01() * tot;
      let lo = 0;
      let hi = x.cum.length - 1;
      while (lo < hi) {
        const mid = (lo + hi) >> 1;
        if ((x.cum[mid] ?? 0) < alvo) lo = mid + 1;
        else hi = mid;
      }
      return x.res[lo] ?? 0;
    };
    const todos = [cj.brasil, ...cj.regioes, ...cj.ufs];
    for (const c of todos) amostras.set(c.chave, []);
    for (let i = 0; i < reps; i++) {
      const reamostra: Unidade[] = [];
      for (const lista of obsPorUf.values()) for (let j = 0; j < lista.length; j++) reamostra.push(lista[Math.floor(u01() * lista.length)] as Unidade);
      const swB = swingDe(reamostra);
      const eps = (erro / 100) * normal(u01);
      const proj = projetarUfs(us, K, (uf) => dUf(swB, uf, kUf), r, (u) => {
        const lam = u.observada ? u.n / (u.n + K) : 0;
        return (1 - lam) * sortear(residuos.get(u.uf) ?? todosRes) + eps;
      });
      for (const c of todos) {
        const s = somaEm(proj, c.ufs);
        if (s.F + s.L > 0) amostras.get(c.chave)?.push((100 * s.F) / (s.F + s.L));
      }
    }
    for (const v of amostras.values()) v.sort((a, b) => a - b);
  }

  // Participação dos dois entre os válidos observados (1 no 2º turno; serve à validação no 1º).
  const partBr = ((): number => {
    let n = 0;
    let vv = 0;
    for (const u of obs) {
      n += u.n;
      vv += u.vv2;
    }
    return vv > 0 ? Math.min(1, n / vv) : 1;
  })();

  const bloco = (c: Conjunto): BlocoProjecao => {
    const set = new Set(c.ufs);
    let st = 0;
    let ts = 0;
    let fo = 0;
    let lo = 0;
    let vvo = 0;
    let f1 = 0;
    let l1 = 0;
    let sd = 0;
    let sn = 0;
    for (const u of us) {
      if (!set.has(u.uf)) continue;
      st += u.st;
      ts += u.ts;
      if (u.ref) {
        f1 += u.ref.f1;
        l1 += u.ref.l1;
      }
      if (u.observada) {
        fo += u.f2;
        lo += u.l2;
        vvo += u.vv2;
        if (u.p1 !== null) {
          sd += u.n * u.d;
          sn += u.n;
        }
      }
    }
    const s = somaEm(central, c.ufs);
    const tot = s.F + s.L;
    let projetado: Projetado | null = null;
    if (motivo === null && tot > 0) {
      const pf = (100 * s.F) / tot;
      const amo = amostras.get(c.chave) ?? [];
      const a = amo.length > 0 ? Math.min(quantil(amo, (1 - NIVEL_FAIXA / 100) / 2), pf) : pf;
      const b = amo.length > 0 ? Math.max(quantil(amo, 1 - (1 - NIVEL_FAIXA / 100) / 2), pf) : pf;
      const part = vvo > 0 ? Math.min(1, (fo + lo) / vvo) : partBr;
      projetado = {
        f: Math.round(s.F),
        l: Math.round(s.L),
        p_f: r2(pf),
        p_l: r2(100 - pf),
        p_f_validos: r2(pf * part),
        p_l_validos: r2((100 - pf) * part),
        faixa90: [r2(a), r2(b)],
      };
    }
    return {
      sigla: c.sigla,
      nome: c.nome,
      pst: pstDe(st, ts),
      pct_vv_observado: tot > 0 ? r2((100 * (fo + lo)) / tot) : 0,
      p1_f: f1 + l1 > 0 ? r2((100 * f1) / (f1 + l1)) : null,
      observado: { f: fo, l: lo, p_f: fo + lo > 0 ? r2((100 * fo) / (fo + lo)) : null },
      projetado,
      swing_pp: sn > 0 ? r2((100 * sd) / sn) : null,
    };
  };

  const brasil = bloco(cj.brasil);
  return {
    cobertura: {
      pst: pstBr,
      st: stBr,
      ts: tsBr,
      pct_vv_observado: brasil.pct_vv_observado,
      municipios_observados: obs.length,
      municipios_fechados: us.filter((u) => u.fechada && u.observada).length,
      municipios_total: us.length,
    },
    brasil,
    regioes: cj.regioes.map(bloco),
    ufs: cj.ufs.map(bloco),
    parametros: { K, K_uf: kUf, mesmo_estagio: e.mesmoEstagio ?? true, erro_comum_pp: erro, reps, nivel_faixa: NIVEL_FAIXA, minimo_pst: minimo, metodo: METODO },
    motivo_sem_projecao: motivo,
  };
}
