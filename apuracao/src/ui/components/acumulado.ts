// Gráfico de votos acumulados: as linhas vêm de criarLinhas (mesma conta de caminho e o
// mesmo estilo de "mov"), e por cima ficam o ponto final pulsante de cada candidatura e
// a linha vertical de leitura do lote mais próximo do ponteiro. As contas de eixo
// compacto, ganho na janela e lote mais próximo são puras e testadas em
// tests/ui/acumulado.test.ts.

import { decimal, inteiro } from "../data/format.ts";
import type { Lote } from "../state/types.ts";
import { criarLinhas, escalaLinear, ticksRedondos } from "./linhas.ts";
import type { Linhas, Margem, OpcoesDesenho, SerieLinha, Tick } from "./linhas.ts";

const NS = "http://www.w3.org/2000/svg";

// ---------- contas puras ----------

const casas = (x: number): number => (Math.abs(x - Math.round(x)) < 1e-9 ? 0 : Math.abs(x * 10 - Math.round(x * 10)) < 1e-9 ? 1 : 2);

/** Rótulo de eixo em votos: "0", "500 mil", "2,5 mi", "10 mi". */
export function votosEixo(v: number): string {
  const a = Math.abs(v);
  if (a >= 1e6) return `${decimal(v / 1e6, casas(v / 1e6))} mi`;
  if (a >= 1e3) return `${decimal(v / 1e3, casas(v / 1e3))} mil`;
  return inteiro(v);
}

/** Ticks de votos de 0 até cobrir `max`, com rótulo compacto. */
export function ticksVotos(min: number, max: number, n = 5): Tick[] {
  const topo = max > min ? max : min + 1;
  return ticksRedondos(min, topo, n).map(v => ({ v, texto: votosEixo(v) }));
}

/** Teto do domínio: o primeiro tick redondo que cobre `max` (nunca menos que 1). */
export function tetoRedondo(max: number, n = 5): number {
  if (!(max > 0)) return 1;
  const ts = ticksRedondos(0, max, n);
  const ult = ts[ts.length - 1] ?? max;
  if (ult >= max) return ult;
  const passo = ts.length > 1 ? (ts[1] ?? 0) - (ts[0] ?? 0) : max;
  return ult + passo;
}

/** Índice do valor de `xs` (ordenado) mais próximo de `x`; -1 se vazio. */
export function maisProximo(xs: readonly number[], x: number): number {
  if (xs.length === 0) return -1;
  let lo = 0;
  let hi = xs.length - 1;
  while (hi - lo > 1) {
    const mid = (lo + hi) >> 1;
    if ((xs[mid] ?? 0) <= x) lo = mid;
    else hi = mid;
  }
  const a = xs[lo] ?? 0;
  const b = xs[hi] ?? 0;
  return Math.abs(x - a) <= Math.abs(b - x) ? lo : hi;
}

/**
 * Votos que `sq` ganhou desde `desde` (ms): último valor menos o do último lote com
 * geração em `desde` ou antes; sem lote anterior à janela, a base é zero.
 */
export function ganhoDesde(lotes: readonly Lote[], sq: string, desde: number): number {
  const ult = lotes[lotes.length - 1];
  if (!ult) return 0;
  let base = 0;
  for (const l of lotes) {
    if (Date.parse(l.at) <= desde) base = l.cand[sq]?.vap ?? 0;
    else break;
  }
  return (ult.cand[sq]?.vap ?? 0) - base;
}

/** Lotes gerados a partir de `desde` (ms). */
export function lotesDesde(lotes: readonly Lote[], desde: number): Lote[] {
  return lotes.filter(l => Date.parse(l.at) >= desde);
}

// ---------- componente ----------

export interface SerieVotos {
  id: string;
  cor: string;
  rotulo: string;
  nome: string;
  espessura?: number;
  /** Linha de referência (válidos): sem ponto pulsante. */
  referencia?: boolean;
}

export interface OpcoesAcumulado {
  largura: number;
  altura: number;
  margem: Partial<Margem>;
  /** Chamado com o índice do lote sob o ponteiro (-1 ao sair) e a posição na janela. */
  aoLer(i: number, clientX: number, clientY: number): void;
}

export interface GraficoAcumulado {
  update(lotes: readonly Lote[], series: readonly SerieVotos[], valor: (l: Lote, id: string) => number, op: Omit<OpcoesDesenho, "marcadores">): void;
  /** Linha de leitura no lote `i`; devolve a posição da âncora na janela (ou null). */
  ler(i: number): { x: number; y: number } | null;
  limparLeitura(): void;
  destroy(): void;
}

function no<K extends keyof SVGElementTagNameMap>(tag: K, attrs: Record<string, string | number> = {}): SVGElementTagNameMap[K] {
  const e = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, String(v));
  return e;
}

export function criarAcumulado(container: HTMLElement, o: OpcoesAcumulado): GraficoAcumulado {
  const m: Margem = { t: 16, r: 220, b: 44, l: 96, ...o.margem };
  const linhas: Linhas = criarLinhas(container, { largura: o.largura, altura: o.altura, margem: m, classe: "ac-linhas" });
  const svg = linhas.el;
  const gPulso = no("g", { class: "ac-pulsos" });
  const gLeitura = no("g", { class: "ac-leitura" });
  const alvo = no("rect", { class: "ac-alvo", x: 0, y: 0, width: o.largura, height: o.altura });
  svg.append(gPulso, gLeitura, alvo);

  let xs: number[] = [];
  let ys: { id: string; cor: string; v: number[]; referencia: boolean }[] = [];
  let sx = (v: number): number => v;
  let sy = (v: number): number => v;
  let altura = o.altura;

  const paraSvg = (clientX: number, clientY: number): { x: number; y: number } => {
    const r = svg.getBoundingClientRect();
    return { x: ((clientX - r.left) * o.largura) / Math.max(1, r.width), y: ((clientY - r.top) * altura) / Math.max(1, r.height) };
  };
  const paraJanela = (x: number, y: number): { x: number; y: number } => {
    const r = svg.getBoundingClientRect();
    return { x: r.left + (x * r.width) / o.largura, y: r.top + (y * r.height) / Math.max(1, altura) };
  };

  const indiceEm = (clientX: number, clientY: number): number => {
    const p = paraSvg(clientX, clientY);
    if (p.x < m.l - 24 || p.x > o.largura - m.r + 24 || p.y < 0 || p.y > altura) return -1;
    return maisProximo(xs.map(sx), p.x);
  };

  const mover = (ev: PointerEvent): void => {
    o.aoLer(indiceEm(ev.clientX, ev.clientY), ev.clientX, ev.clientY);
  };
  // No toque o pointerleave vem logo depois do pointerup: a leitura fica até o próximo toque
  // fora das barras ou dos pontos.
  const sair = (ev: PointerEvent): void => {
    if (ev.pointerType !== "touch") o.aoLer(-1, 0, 0);
  };
  alvo.addEventListener("pointermove", mover);
  alvo.addEventListener("pointerdown", mover);
  alvo.addEventListener("pointerleave", sair);

  const ler = (i: number): { x: number; y: number } | null => {
    const x = xs[i];
    if (x === undefined) return null;
    const px = sx(x);
    const y0 = altura - m.b;
    const y1 = m.t;
    const filhos: SVGElement[] = [no("line", { x1: px, x2: px, y1, y2: y0, class: "ac-leitura-linha" })];
    let topo = y0;
    for (const s of ys) {
      const v = s.v[i];
      if (v === undefined || !Number.isFinite(v)) continue;
      const py = sy(v);
      topo = Math.min(topo, py);
      filhos.push(no("circle", { cx: px, cy: py, r: s.referencia ? 6 : 9, class: "ac-leitura-ponto", stroke: s.cor }));
    }
    gLeitura.replaceChildren(...filhos);
    return paraJanela(px, topo);
  };

  return {
    update(lotes, series, valor, op) {
      linhas.update(
        series.map((s): SerieLinha => ({
          id: s.id,
          cor: s.cor,
          rotulo: s.rotulo,
          espessura: s.espessura ?? 4,
          pontos: lotes.map(l => ({ x: Date.parse(l.at), y: valor(l, s.id) })),
        })),
        op,
      );
      const vb = svg.viewBox.baseVal;
      altura = vb && vb.height > 0 ? vb.height : o.altura;
      alvo.setAttribute("height", String(altura));
      sx = escalaLinear(op.dominioX[0], op.dominioX[1], m.l, o.largura - m.r);
      sy = escalaLinear(op.dominioY[0], op.dominioY[1], altura - m.b, m.t);
      xs = lotes.map(l => Date.parse(l.at));
      ys = series.map(s => ({ id: s.id, cor: s.cor, v: lotes.map(l => valor(l, s.id)), referencia: s.referencia ?? false }));
      const ultimo = lotes.length - 1;
      gPulso.replaceChildren(
        ...(ultimo < 0
          ? []
          : ys
              .filter(s => !s.referencia)
              .flatMap(s => {
                const v = s.v[ultimo];
                const x = xs[ultimo];
                if (v === undefined || x === undefined) return [];
                const cx = sx(x);
                const cy = sy(v);
                return [no("circle", { cx, cy, r: 7, fill: s.cor, class: "ac-ponto" }), no("circle", { cx, cy, r: 7, stroke: s.cor, class: "ac-pulso" })];
              })),
      );
    },
    ler,
    limparLeitura() {
      gLeitura.replaceChildren();
    },
    destroy() {
      alvo.removeEventListener("pointermove", mover);
      alvo.removeEventListener("pointerdown", mover);
      alvo.removeEventListener("pointerleave", sair);
      linhas.destroy();
    },
  };
}
