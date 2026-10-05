// Partes puras da avaliação final da noite: campo, eleitos (TSE ou provisórios), contagens e lacunas.
// Nenhum acesso a banco ou disco; testado em tests/final.test.ts.
import { alocarCadeiras } from "../../src/ui/components/cadeiras.ts";

export type Campo = "esquerda" | "centro-esquerda" | "centro" | "centro-direita" | "direita" | "indefinido";
export const CAMPOS: readonly Campo[] = ["esquerda", "centro-esquerda", "centro", "centro-direita", "direita", "indefinido"];
export type Bloco = "direita + centro-direita" | "esquerda + centro-esquerda" | "centro" | "indefinido";
export type Fonte = "tse" | "provisorio";

export interface Classificador {
  partidos: ReadonlyMap<string, Campo>;
  excecoes: ReadonlyMap<string, Campo>;
}

const VALIDOS: ReadonlySet<string> = new Set(CAMPOS);

/** Lê o conteúdo de public/campos.json; siglas em caixa alta, valores fora da lista são ignorados. */
export function classificador(bruto: { partidos?: Record<string, unknown>; excecoes?: Record<string, unknown> }): Classificador {
  const partidos = new Map<string, Campo>();
  for (const [sg, c] of Object.entries(bruto.partidos ?? {})) if (typeof c === "string" && VALIDOS.has(c)) partidos.set(sg.toUpperCase(), c as Campo);
  const excecoes = new Map<string, Campo>();
  for (const [sq, c] of Object.entries(bruto.excecoes ?? {})) if (typeof c === "string" && VALIDOS.has(c)) excecoes.set(sq, c as Campo);
  return { partidos, excecoes };
}

/** Exceção por candidatura vence; depois o partido; depois a federação. */
export function campoDe(cl: Classificador, sq: string | null, ...siglas: (string | null | undefined)[]): Campo {
  const e = sq ? cl.excecoes.get(sq) : undefined;
  if (e) return e;
  for (const s of siglas) {
    const c = s ? cl.partidos.get(s.toUpperCase()) : undefined;
    if (c) return c;
  }
  return "indefinido";
}

export function blocoDe(c: Campo): Bloco {
  if (c === "direita" || c === "centro-direita") return "direita + centro-direita";
  if (c === "esquerda" || c === "centro-esquerda") return "esquerda + centro-esquerda";
  return c === "centro" ? "centro" : "indefinido";
}

export interface Cand {
  sq: string;
  nome: string;
  partido: string;
  federacao: string | null;
  agremiacao: string;
  vap: number;
  pct: number;
  eleito: boolean;
  st: string | null;
  valido: boolean;
  campo: Campo;
}

export interface PartidoVoto {
  agremiacao: string;
  sigla: string;
  tvtn: number;
  tvtl: number;
}

export interface Disputa {
  uf: string;
  cargo: number;
  tf: boolean;
  pst: number;
  vagas: number;
  vv: number;
  cands: Cand[]; // do mais votado ao menos votado
  partidos: PartidoVoto[];
}

export interface Eleitos {
  fonte: Fonte;
  eleitos: Cand[];
  qe: number | null;
  alertas: string[];
}

/** O TSE marca eleito = 1 também para quem vai ao 2º turno; a situação textual decide. */
export const eleitoTse = (c: Cand): boolean => (c.st ? c.st.startsWith("Eleito") : c.eleito);

const porVotos = (a: Cand, b: Cand): number => b.vap - a.vap || a.sq.localeCompare(b.sq);

/** Eleitos de cargo proporcional: marca do TSE com tf = 1, senão a alocação provisória de cadeiras.ts. */
export function eleitosProporcional(d: Disputa): Eleitos {
  const alertas: string[] = [];
  if (d.tf) {
    const eleitos = d.cands.filter(eleitoTse).sort(porVotos);
    if (eleitos.length > 0) {
      if (eleitos.length !== d.vagas) alertas.push(`${d.uf.toUpperCase()} cargo ${d.cargo}: TSE marca ${eleitos.length} eleitos para ${d.vagas} vagas`);
      return { fonte: "tse", eleitos, qe: null, alertas };
    }
    alertas.push(`${d.uf.toUpperCase()} cargo ${d.cargo}: arquivo final sem eleito marcado; usada a alocação provisória`);
  }
  const votos = new Map<string, number>();
  for (const p of d.partidos) votos.set(p.agremiacao, (votos.get(p.agremiacao) ?? 0) + p.tvtn + p.tvtl);
  const cands = new Map<string, Cand[]>();
  for (const c of d.cands) {
    if (!c.valido) continue;
    const l = cands.get(c.agremiacao) ?? [];
    l.push(c);
    cands.set(c.agremiacao, l);
    if (!votos.has(c.agremiacao)) votos.set(c.agremiacao, 0);
  }
  const entrada = [...votos.entries()].map(([id, v]) => ({ id, votos: v, candidatos: (cands.get(id) ?? []).map((c) => c.vap) }));
  const res = alocarCadeiras(d.vagas, entrada, d.vv > 0 ? d.vv : undefined);
  const eleitos: Cand[] = [];
  for (const [id, r] of Object.entries(res.porAgremiacao)) eleitos.push(...(cands.get(id) ?? []).sort(porVotos).slice(0, r.total));
  if (eleitos.length !== d.vagas) alertas.push(`${d.uf.toUpperCase()} cargo ${d.cargo}: alocação provisória preencheu ${eleitos.length} de ${d.vagas} vagas`);
  return { fonte: "provisorio", eleitos: eleitos.sort(porVotos), qe: res.qe, alertas };
}

/** Eleitos de cargo majoritário: marca do TSE com tf = 1, senão os n mais votados entre os válidos. */
export function eleitosMajoritario(d: Disputa, n: number): Eleitos {
  if (d.tf) {
    const eleitos = d.cands.filter(eleitoTse).sort(porVotos);
    if (eleitos.length > 0) return { fonte: "tse", eleitos, qe: null, alertas: [] };
  }
  const alertas: string[] = [];
  const validos = d.cands.filter((c) => c.valido).sort(porVotos);
  const corte = validos[n - 1]?.vap ?? 0;
  for (const c of d.cands) if (!c.valido && c.vap > corte) alertas.push(`${d.uf.toUpperCase()} cargo ${d.cargo}: ${c.nome} (${c.partido}) teria vaga, mas os votos estão sub judice`);
  return { fonte: "provisorio", eleitos: validos.slice(0, n), qe: null, alertas };
}

export interface Governo {
  uf: string;
  fonte: Fonte;
  pst: number;
  decisao: "eleito" | "segundo_turno";
  candidatos: Cand[]; // eleito, ou o par do 2º turno
  terceiro: Cand | null;
}

export function governador(d: Disputa): Governo {
  const validos = d.cands.filter((c) => c.valido).sort(porVotos);
  const base = { uf: d.uf, pst: d.pst };
  if (d.tf) {
    const eleito = d.cands.filter(eleitoTse);
    if (eleito.length > 0) return { ...base, fonte: "tse", decisao: "eleito", candidatos: eleito, terceiro: null };
    const par = d.cands.filter((c) => c.st === "2º turno").sort(porVotos);
    if (par.length === 2) return { ...base, fonte: "tse", decisao: "segundo_turno", candidatos: par, terceiro: validos.find((c) => !par.includes(c)) ?? null };
  }
  const lider = validos[0];
  if (lider && lider.pct > 50) return { ...base, fonte: "provisorio", decisao: "eleito", candidatos: [lider], terceiro: null };
  return { ...base, fonte: "provisorio", decisao: "segundo_turno", candidatos: validos.slice(0, 2), terceiro: validos[2] ?? null };
}

export function zeroPorCampo(): Record<Campo, number> {
  return { esquerda: 0, "centro-esquerda": 0, centro: 0, "centro-direita": 0, direita: 0, indefinido: 0 };
}

export function contarPorCampo(itens: readonly { campo: Campo }[], peso: (i: { campo: Campo }) => number = () => 1): Record<Campo, number> {
  const r = zeroPorCampo();
  for (const i of itens) r[i.campo] += peso(i);
  return r;
}

export function blocos(porCampo: Record<Campo, number>): Record<Bloco, number> {
  const r: Record<Bloco, number> = { "direita + centro-direita": 0, "esquerda + centro-esquerda": 0, centro: 0, indefinido: 0 };
  for (const c of CAMPOS) r[blocoDe(c)] += porCampo[c];
  return r;
}

export function contarPor<T>(itens: readonly T[], chave: (i: T) => string): Record<string, number> {
  const m = new Map<string, number>();
  for (const i of itens) m.set(chave(i), (m.get(chave(i)) ?? 0) + 1);
  return Object.fromEntries([...m.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0])));
}

export interface Lacuna {
  de: string;
  ate: string;
  minutos: number;
}

/** Intervalos sem geração nova acima de `minMin` minutos, dos maiores aos menores. */
export function lacunas(tempos: readonly string[], minMin: number): Lacuna[] {
  const t = [...new Set(tempos)].sort();
  const out: Lacuna[] = [];
  for (let i = 1; i < t.length; i++) {
    const de = t[i - 1] as string;
    const ate = t[i] as string;
    const minutos = (Date.parse(ate) - Date.parse(de)) / 60_000;
    if (minutos >= minMin) out.push({ de, ate, minutos: Math.round(minutos * 10) / 10 });
  }
  return out.sort((a, b) => b.minutos - a.minutos);
}

export interface Vao {
  uf: string;
  governador: string;
  partido: string;
  campo: Campo;
  pct_governador: number;
  presidenciavel: string;
  pct_presidenciavel: number;
  vao_pp: number;
}

/** Governador (até dois por UF) menos o presidenciável finalista do mesmo bloco, na mesma UF. */
export function vaoEstadual(govs: readonly Governo[], finalistas: readonly Cand[], presUf: ReadonlyMap<string, readonly Cand[]>): Vao[] {
  const out: Vao[] = [];
  for (const g of govs) {
    const pres = presUf.get(g.uf) ?? [];
    for (const c of g.candidatos) {
      const fin = finalistas.find((f) => blocoDe(f.campo) === blocoDe(c.campo) && blocoDe(c.campo) !== "centro" && blocoDe(c.campo) !== "indefinido");
      const p = fin ? pres.find((x) => x.sq === fin.sq) : undefined;
      if (!fin || !p) continue;
      out.push({ uf: g.uf, governador: c.nome, partido: c.partido, campo: c.campo, pct_governador: r2(c.pct), presidenciavel: fin.nome, pct_presidenciavel: r2(p.pct), vao_pp: r2(c.pct - p.pct) });
    }
  }
  return out.sort((a, b) => b.vao_pp - a.vao_pp);
}

export const r2 = (x: number): number => Math.round(x * 100) / 100;
