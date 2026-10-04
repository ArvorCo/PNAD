// Projeção da casa, portada de scripts/voto_util_mapa.py: equirretangular com
// correção de cosseno na latitude média. Funções puras, sem DOM.

import type { Geometria, Posicao } from "../data/geo.ts";

export interface Caixa {
  lon0: number;
  lon1: number;
  lat0: number;
  lat1: number;
  /** Latitude de referência do cosseno; sem ela, o meio da caixa. */
  latRef?: number;
}

/** Caixa do Brasil usada pela casa, com cos(-14°). */
export const CAIXA_BR: Caixa = { lon0: -74.2, lon1: -34.6, lat0: -33.9, lat1: 5.4, latRef: -14 };

export interface Ajuste {
  projetar: (lon: number, lat: number) => [number, number];
  /** Pixels por grau de latitude. */
  escala: number;
  /** Fator de cosseno aplicado à longitude. */
  cos: number;
}

const rad = (g: number): number => (g * Math.PI) / 180;

/** Ajusta a caixa ao retângulo largura × altura com margem `pad`, centralizada. */
export function fitExtent(caixa: Caixa, largura: number, altura: number, pad = 10): Ajuste {
  const cos = Math.cos(rad(caixa.latRef ?? (caixa.lat0 + caixa.lat1) / 2));
  const spanY = Math.max(caixa.lat1 - caixa.lat0, 1e-9);
  const spanX = Math.max((caixa.lon1 - caixa.lon0) * cos, 1e-9);
  const w = Math.max(largura - 2 * pad, 1);
  const h = Math.max(altura - 2 * pad, 1);
  const escala = Math.min(w / spanX, h / spanY);
  const ox = pad + (w - spanX * escala) / 2;
  const oy = pad + (h - spanY * escala) / 2;
  return {
    escala,
    cos,
    projetar: (lon, lat) => [ox + (lon - caixa.lon0) * cos * escala, oy + (caixa.lat1 - lat) * escala],
  };
}

/** Anéis de uma geometria, achatando o MultiPolygon. */
export function aneis(g: Geometria): Posicao[][] {
  if (g.type === "Polygon") return g.coordinates as Posicao[][];
  return (g.coordinates as Posicao[][][]).flat();
}

/** Caixa que envolve todas as geometrias; latitude de referência no meio. */
export function caixaDe(geometrias: Iterable<Geometria>): Caixa {
  let lon0 = Infinity;
  let lon1 = -Infinity;
  let lat0 = Infinity;
  let lat1 = -Infinity;
  for (const g of geometrias) {
    for (const anel of aneis(g)) {
      for (const [lon, lat] of anel) {
        if (lon < lon0) lon0 = lon;
        if (lon > lon1) lon1 = lon;
        if (lat < lat0) lat0 = lat;
        if (lat > lat1) lat1 = lat;
      }
    }
  }
  if (!Number.isFinite(lon0)) return CAIXA_BR;
  return { lon0, lon1, lat0, lat1, latRef: (lat0 + lat1) / 2 };
}

const r1 = (x: number): number => Math.round(x * 10) / 10;

/**
 * Atributo `d` de um Polygon ou MultiPolygon, com coordenadas arredondadas a 0,1
 * e pontos repetidos depois do arredondamento descartados.
 */
export function caminho(g: Geometria, projetar: Ajuste["projetar"]): string {
  let d = "";
  for (const anel of aneis(g)) {
    let seg = "";
    let n = 0;
    let px = NaN;
    let py = NaN;
    let fx = NaN;
    let fy = NaN;
    for (const [lon, lat] of anel) {
      const [x0, y0] = projetar(lon, lat);
      const x = r1(x0);
      const y = r1(y0);
      if (x === px && y === py) continue;
      if (n === 0) {
        fx = x;
        fy = y;
      }
      seg += n === 0 ? `M${x},${y}` : ` ${x},${y}`;
      px = x;
      py = y;
      n++;
    }
    // O último ponto igual ao primeiro é redundante: o Z fecha o anel.
    if (n > 1 && px === fx && py === fy) {
      seg = seg.slice(0, seg.lastIndexOf(" "));
      n--;
    }
    if (n >= 3) d += `${seg}Z`;
  }
  return d;
}

/** Área com sinal (fórmula do laço) de um anel em coordenadas planas. */
export function areaAnel(anel: Posicao[]): number {
  let a = 0;
  for (let i = 0; i < anel.length; i++) {
    const p = anel[i];
    const q = anel[(i + 1) % anel.length];
    if (!p || !q) continue;
    a += p[0] * q[1] - q[0] * p[1];
  }
  return a / 2;
}

/** Centroide (lon, lat) do maior anel em área, para rótulos. */
export function centroide(g: Geometria): Posicao {
  let melhor: Posicao[] = [];
  let maior = -1;
  for (const anel of aneis(g)) {
    const a = Math.abs(areaAnel(anel));
    if (a > maior) {
      maior = a;
      melhor = anel;
    }
  }
  const a = areaAnel(melhor);
  if (melhor.length === 0) return [0, 0];
  if (Math.abs(a) < 1e-12) {
    const sx = melhor.reduce((s, p) => s + p[0], 0);
    const sy = melhor.reduce((s, p) => s + p[1], 0);
    return [sx / melhor.length, sy / melhor.length];
  }
  let cx = 0;
  let cy = 0;
  for (let i = 0; i < melhor.length; i++) {
    const p = melhor[i];
    const q = melhor[(i + 1) % melhor.length];
    if (!p || !q) continue;
    const c = p[0] * q[1] - q[0] * p[1];
    cx += (p[0] + q[0]) * c;
    cy += (p[1] + q[1]) * c;
  }
  return [cx / (6 * a), cy / (6 * a)];
}
