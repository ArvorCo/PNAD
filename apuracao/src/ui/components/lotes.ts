// Barras empilhadas por lote: uma barra por versão do arquivo (ou por janela de 5 minutos
// quando há mais de MAX_BARRAS), larguras iguais com 2 px de intervalo, altura = votos
// válidos acrescentados, segmentos nas cores das candidaturas na ordem do ranking
// nacional a partir da base. Regressões (deltas negativos) descem abaixo do zero em
// --warn. Por cima, a escada de seções acrescentadas num eixo secundário à direita.
// As contas (pilhas, agrupamento, ticks) são puras e testadas em tests/ui/lotes.test.ts.

import type { Lote } from "../state/types.ts";
import { tetoRedondo, ticksVotos, votosEixo } from "./acumulado.ts";
import { escalaLinear, ticksRedondos } from "./linhas.ts";
import type { Margem } from "./linhas.ts";

const NS = "http://www.w3.org/2000/svg";
export const MAX_BARRAS = 300;
export const JANELA_BIN_MS = 5 * 60_000;
export const OUTROS = "outros";

// ---------- contas puras ----------

/** Um bloco: um lote ou vários lotes vizinhos somados. */
export interface Bloco {
  /** Geração do primeiro e do último lote (ms). */
  ini: number;
  fim: number;
  n: number;
  /** Lote final do bloco (valores acumulados e latência). */
  ultimo: Lote;
  d_st: number;
  d_vv: number;
  d_tv: number;
  d_cand: Record<string, number>;
}

export function blocoDe(l: Lote): Bloco {
  const t = Date.parse(l.at);
  const d_cand: Record<string, number> = {};
  for (const [k, v] of Object.entries(l.cand)) d_cand[k] = v.d_vap;
  return { ini: t, fim: t, n: 1, ultimo: l, d_st: l.d_st, d_vv: l.d_vv, d_tv: l.d_tv, d_cand };
}

/**
 * Um bloco por lote até `max`; acima disso, soma lotes vizinhos em janelas de `janela` ms
 * (alinhadas ao relógio). Devolve os blocos e se houve agrupamento.
 */
export function agrupar(lotes: readonly Lote[], max = MAX_BARRAS, janela = JANELA_BIN_MS): { blocos: Bloco[]; agrupado: boolean } {
  if (lotes.length <= max) return { blocos: lotes.map(blocoDe), agrupado: false };
  const blocos: Bloco[] = [];
  let chave = NaN;
  for (const l of lotes) {
    const t = Date.parse(l.at);
    const k = Math.floor(t / janela);
    const atual = blocos[blocos.length - 1];
    if (atual && k === chave) {
      atual.fim = t;
      atual.n += 1;
      atual.ultimo = l;
      atual.d_st += l.d_st;
      atual.d_vv += l.d_vv;
      atual.d_tv += l.d_tv;
      for (const [sq, v] of Object.entries(l.cand)) atual.d_cand[sq] = (atual.d_cand[sq] ?? 0) + v.d_vap;
    } else {
      blocos.push(blocoDe(l));
      chave = k;
    }
  }
  return { blocos, agrupado: true };
}

export interface Segmento {
  id: string; // sqcand ou OUTROS
  y0: number; // votos, base do segmento
  y1: number; // votos, topo do segmento
  negativo: boolean;
}

/**
 * Pilha de um bloco: positivos de baixo para cima na ordem `ordem`, depois o resto dos
 * válidos que nenhuma candidatura listada explica (OUTROS); negativos descem do zero na
 * mesma ordem. A soma dos positivos menos a dos negativos é d_vv quando o resto é ≥ 0.
 */
export function pilha(b: Bloco, ordem: readonly string[]): Segmento[] {
  const out: Segmento[] = [];
  let cima = 0;
  let baixo = 0;
  let soma = 0;
  for (const id of ordem) {
    const v = b.d_cand[id] ?? 0;
    soma += v;
    if (v > 0) {
      out.push({ id, y0: cima, y1: cima + v, negativo: false });
      cima += v;
    } else if (v < 0) {
      out.push({ id, y0: baixo + v, y1: baixo, negativo: true });
      baixo += v;
    }
  }
  const resto = b.d_vv - soma;
  if (resto > 0) out.push({ id: OUTROS, y0: cima, y1: cima + resto, negativo: false });
  else if (resto < 0) out.push({ id: OUTROS, y0: baixo + resto, y1: baixo, negativo: true });
  return out;
}

/** Extremos verticais de um conjunto de pilhas (sempre incluem o zero). */
export function extremos(pilhas: readonly Segmento[][]): { min: number; max: number } {
  let min = 0;
  let max = 0;
  for (const p of pilhas) for (const s of p) {
    min = Math.min(min, s.y0);
    max = Math.max(max, s.y1);
  }
  return { min, max };
}

/** Geometria das barras: largura igual, `gap` entre elas, dentro de [x0, x1]. */
export function barras(n: number, x0: number, x1: number, gap = 2, maxLargura = 48): { x: number[]; w: number } {
  if (n <= 0) return { x: [], w: 0 };
  const w = Math.max(1, Math.min(maxLargura, (x1 - x0 - gap * (n - 1)) / n));
  return { x: Array.from({ length: n }, (_, i) => x0 + i * (w + gap)), w };
}

/** Participação de cada candidatura no bloco (só ganhos positivos), em pontos. */
export function participacao(b: Bloco, id: string): number {
  return b.d_vv > 0 ? (100 * (b.d_cand[id] ?? 0)) / b.d_vv : 0;
}

/** Candidatura com mais votos no bloco (null sem ganho positivo). */
export function liderDoBloco(b: Bloco, ordem: readonly string[]): string | null {
  let melhor: string | null = null;
  let v = 0;
  for (const id of ordem) {
    const x = b.d_cand[id] ?? 0;
    if (x > v) {
      v = x;
      melhor = id;
    }
  }
  return melhor;
}

/** Índices das barras que recebem rótulo de hora, sem colidir (`minPx` entre rótulos). */
/** Índices das barras que recebem rótulo de hora: a primeira, uma a cada `minPx`, e sempre a última
 *  (o rótulo anterior sai se ficar colado nela), para o eixo terminar no último lote. */
export function indicesDeHora(n: number, passoPx: number, minPx = 110): number[] {
  if (n <= 0) return [];
  const cada = Math.max(1, Math.ceil(minPx / Math.max(1, passoPx)));
  const out: number[] = [];
  for (let i = 0; i < n; i += cada) out.push(i);
  const ultimo = n - 1;
  if (out[out.length - 1] !== ultimo) {
    const anterior = out[out.length - 1] ?? 0;
    if (out.length > 1 && (ultimo - anterior) * passoPx < minPx * 0.7) out.pop();
    out.push(ultimo);
  }
  return out;
}

// ---------- componente ----------

export interface OpcoesBarras {
  largura: number;
  altura: number;
  margem?: Partial<Margem>;
  /** Índice do bloco sob o ponteiro (-1 ao sair) e a posição na janela. */
  aoLer(i: number, clientX: number, clientY: number): void;
}

export interface DesenhoBarras {
  blocos: readonly Bloco[];
  ordem: readonly string[];
  cor: (id: string) => string;
  hora: (ms: number) => string;
}

export interface GraficoLotes {
  update(d: DesenhoBarras): void;
  /** Contorno lime no bloco `i`; devolve a âncora (topo da barra) na janela, ou null. */
  marcar(i: number): { x: number; y: number } | null;
  destroy(): void;
}

function no<K extends keyof SVGElementTagNameMap>(tag: K, attrs: Record<string, string | number> = {}): SVGElementTagNameMap[K] {
  const e = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, String(v));
  return e;
}

const r1 = (v: number): number => Math.round(v * 10) / 10;

export function criarGraficoLotes(container: HTMLElement, o: OpcoesBarras): GraficoLotes {
  const m: Margem = { t: 56, r: 120, b: 52, l: 110, ...o.margem };
  let altura = o.altura;
  const svg = no("svg", { viewBox: `0 0 ${o.largura} ${altura}`, class: "lt-svg" });
  const gEixos = no("g", { class: "lt-eixos" });
  const gBarras = no("g", { class: "lt-barras" });
  const gSecoes = no("g", { class: "lt-secoes" });
  const gMarca = no("g", { class: "lt-marca" });
  svg.append(gEixos, gBarras, gSecoes, gMarca);
  container.append(svg);

  let xs: number[] = [];
  let w = 0;
  let topos: number[] = [];
  let bases: number[] = [];

  const indiceEm = (clientX: number, clientY: number): number => {
    const r = svg.getBoundingClientRect();
    const x = ((clientX - r.left) * o.largura) / Math.max(1, r.width);
    const y = ((clientY - r.top) * altura) / Math.max(1, r.height);
    if (xs.length === 0 || y < m.t - 40 || y > altura - m.b + 8) return -1;
    const passo = w + 2;
    const i = Math.floor((x - (xs[0] ?? 0) + 1) / passo);
    return i >= 0 && i < xs.length ? i : -1;
  };
  const mover = (ev: PointerEvent): void => o.aoLer(indiceEm(ev.clientX, ev.clientY), ev.clientX, ev.clientY);
  // No toque o pointerleave vem logo depois do pointerup: a leitura fica até o próximo toque
  // fora das barras ou dos pontos.
  const sair = (ev: PointerEvent): void => {
    if (ev.pointerType !== "touch") o.aoLer(-1, 0, 0);
  };
  svg.addEventListener("pointermove", mover);
  svg.addEventListener("pointerdown", mover);
  svg.addEventListener("pointerleave", sair);

  const paraJanela = (x: number, y: number): { x: number; y: number } => {
    const r = svg.getBoundingClientRect();
    return { x: r.left + (x * r.width) / o.largura, y: r.top + (y * r.height) / Math.max(1, altura) };
  };

  return {
    update(d) {
      const caixa = container.getBoundingClientRect();
      if (caixa.width > 0 && caixa.height > 0) {
        const nova = Math.round((o.largura * caixa.height) / caixa.width);
        if (nova !== altura) {
          altura = nova;
          svg.setAttribute("viewBox", `0 0 ${o.largura} ${altura}`);
        }
      }
      const x0 = m.l;
      const x1 = o.largura - m.r;
      const y0 = altura - m.b;
      const y1 = m.t;
      const pilhas = d.blocos.map(b => pilha(b, d.ordem));
      const ext = extremos(pilhas);
      const teto = tetoRedondo(ext.max, 5);
      const piso = ext.min < 0 ? -tetoRedondo(-ext.min, 2) : 0;
      const sy = escalaLinear(piso, teto, y0, y1);
      const maxSt = Math.max(1, ...d.blocos.map(b => b.d_st));
      const tetoSt = tetoRedondo(maxSt, 4);
      const ss = escalaLinear(0, tetoSt, sy(0), y1);
      const g = barras(d.blocos.length, x0, x1);
      xs = g.x;
      w = g.w;

      // Eixos: votos à esquerda, seções à direita, horas embaixo.
      const eixos: SVGElement[] = [];
      for (const t of ticksVotos(piso, teto, 5)) {
        const y = r1(sy(t.v));
        eixos.push(no("line", { x1: x0, x2: x1, y1: y, y2: y, class: t.v === 0 ? "lt-zero" : "lt-grade" }));
        const tx = no("text", { x: x0 - 12, y, class: "lt-tick lt-tick--y" });
        tx.textContent = t.texto;
        eixos.push(tx);
      }
      for (const v of ticksRedondos(0, tetoSt, 4)) {
        if (v === 0) continue;
        const tx = no("text", { x: x1 + 12, y: r1(ss(v)), class: "lt-tick lt-tick--st" });
        tx.textContent = votosEixo(v);
        eixos.push(tx);
      }
      const tituloSt = no("text", { x: o.largura - 4, y: 20, class: "lt-eixo-st" });
      tituloSt.textContent = "seções no lote";
      const tituloV = no("text", { x: 4, y: 20, class: "lt-eixo-v" });
      tituloV.textContent = "válidos no lote";
      eixos.push(tituloSt, tituloV);
      for (const i of indicesDeHora(d.blocos.length, g.w + 2)) {
        const b = d.blocos[i];
        const x = xs[i];
        if (!b || x === undefined) continue;
        const cx = r1(x + g.w / 2);
        eixos.push(no("line", { x1: cx, x2: cx, y1: y0, y2: y0 + 8, class: "lt-marca-x" }));
        const tx = no("text", { x: cx, y: y0 + 34, class: "lt-tick lt-tick--x" });
        tx.textContent = d.hora(b.ini);
        eixos.push(tx);
      }
      eixos.push(no("line", { x1: x0, x2: x1, y1: y0, y2: y0, class: "lt-base" }));
      gEixos.replaceChildren(...eixos);

      // Barras.
      const rects: SVGElement[] = [];
      topos = [];
      bases = [];
      pilhas.forEach((p, i) => {
        const x = xs[i] ?? 0;
        let topo = sy(0);
        let base = sy(0);
        for (const s of p) {
          const ya = sy(s.y1);
          const yb = sy(s.y0);
          topo = Math.min(topo, ya);
          base = Math.max(base, yb);
          const h = Math.max(0, yb - ya);
          if (h <= 0) continue;
          const r = no("rect", { x: r1(x), y: r1(ya), width: r1(g.w), height: r1(Math.max(h, 0.5)), class: s.negativo ? "lt-seg lt-seg--neg" : "lt-seg" });
          if (!s.negativo) r.setAttribute("fill", d.cor(s.id));
          rects.push(r);
        }
        topos.push(topo);
        bases.push(base);
      });
      gBarras.replaceChildren(...rects);

      // Escada de seções acrescentadas.
      let caminho = "";
      d.blocos.forEach((b, i) => {
        const x = xs[i] ?? 0;
        const y = r1(ss(Math.max(0, b.d_st)));
        caminho += `${i === 0 ? "M" : "L"}${r1(x)} ${y}L${r1(x + g.w + (i < d.blocos.length - 1 ? 2 : 0))} ${y}`;
      });
      gSecoes.replaceChildren(...(caminho ? [no("path", { d: caminho, class: "lt-escada" })] : []));
    },
    marcar(i) {
      const x = xs[i];
      const topo = topos[i];
      const base = bases[i];
      if (x === undefined || topo === undefined || base === undefined) {
        gMarca.replaceChildren();
        return null;
      }
      const h = Math.max(4, base - topo);
      gMarca.replaceChildren(no("rect", { x: r1(x - 3), y: r1(topo - 3), width: r1(w + 6), height: r1(h + 6), class: "lt-contorno" }));
      return paraJanela(x + w / 2, topo);
    },
    destroy() {
      svg.removeEventListener("pointermove", mover);
      svg.removeEventListener("pointerdown", mover);
      svg.removeEventListener("pointerleave", sair);
      svg.remove();
    },
  };
}
