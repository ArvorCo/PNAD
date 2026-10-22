// Desenho da amostra de seções: por UF, alocação proporcional ao número de seções de cada
// município (parte inteira da cota mais restos sorteados) e sorteio sem reposição dentro do
// município, com semente fixa.
// Cada seção da UF tem a mesma chance de entrar (amostra autoponderada). As UFs com 2º turno
// para governador recebem um segundo sorteio, independente, de tamanho próprio.
import type { SecaoChave } from "./urls.ts";
import { chaveSecao } from "./urls.ts";

/** FNV-1a de 32 bits. */
export function hash32(s: string): number {
  let h = 0x811c9dc5;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 0x01000193) >>> 0;
  }
  return h >>> 0;
}

/** mulberry32: gerador determinístico em [0, 1). */
export function gerador(semente: string): () => number {
  let a = hash32(semente);
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const ordem = (x: SecaoChave, y: SecaoChave): number => (x.mun < y.mun ? -1 : x.mun > y.mun ? 1 : x.zona - y.zona || x.secao - y.secao);

/** `n` seções da UF: cota por município proporcional ao tamanho, sorteio dentro dele. */
export function amostrarUf(secoes: readonly SecaoChave[], n: number, semente: string): SecaoChave[] {
  if (n <= 0 || secoes.length === 0) return [];
  if (n >= secoes.length) return [...secoes].sort(ordem);
  const porMun = new Map<string, SecaoChave[]>();
  for (const s of secoes) {
    const l = porMun.get(s.mun);
    if (l) l.push(s);
    else porMun.set(s.mun, [s]);
  }
  const total = secoes.length;
  const cotas = [...porMun.entries()]
    .sort((a, b) => (a[0] < b[0] ? -1 : 1))
    .map(([mun, l]) => {
      const q = (n * l.length) / total;
      return { mun, l: [...l].sort(ordem), cota: Math.floor(q), resto: q - Math.floor(q) };
    });
  // Restos por amostragem sistemática (início aleatório, ordem dos códigos): cada município
  // ganha a unidade extra com probabilidade igual à fração da cota, então E[cota] = n·Nm/N e
  // toda seção tem a mesma chance n/N de entrar.
  const falta = n - cotas.reduce((s, c) => s + c.cota, 0);
  if (falta > 0) {
    let ponto = gerador(`${semente}|restos`)();
    let acumulado = 0;
    for (const c of cotas) {
      acumulado += c.resto;
      while (ponto < acumulado - 1e-12) {
        c.cota += 1;
        ponto += 1;
      }
    }
    // arredondamento de ponto flutuante na soma dos restos: completa pelo maior resto
    let soma = cotas.reduce((s, c) => s + c.cota, 0);
    for (const c of [...cotas].sort((a, b) => b.resto - a.resto)) {
      if (soma >= n) break;
      if (c.cota < c.l.length) {
        c.cota += 1;
        soma += 1;
      }
    }
  }
  const out: SecaoChave[] = [];
  for (const c of cotas) {
    if (c.cota <= 0) continue;
    const r = gerador(`${semente}|${c.mun}`);
    const v = [...c.l];
    for (let i = 0; i < c.cota; i++) {
      const j = i + Math.floor(r() * (v.length - i));
      const t = v[i] as SecaoChave;
      v[i] = v[j] as SecaoChave;
      v[j] = t;
    }
    out.push(...v.slice(0, c.cota));
  }
  return out.sort(ordem);
}

export interface DesenhoAmostra {
  porUf: number;
  estadual: number;
  ufsEstaduais: readonly string[];
  semente: string;
}

/** Amostra de uma UF (nacional mais, onde houver, a estadual). Chave → seção. */
export function desenharUf(uf: string, secoes: readonly SecaoChave[], d: DesenhoAmostra): Map<string, SecaoChave> {
  const m = new Map<string, SecaoChave>();
  for (const s of amostrarUf(secoes, d.porUf, `${d.semente}|${uf}|nacional`)) m.set(chaveSecao(s), s);
  if (d.ufsEstaduais.includes(uf)) {
    for (const s of amostrarUf(secoes, d.estadual, `${d.semente}|${uf}|estadual`)) m.set(chaveSecao(s), s);
  }
  return m;
}
