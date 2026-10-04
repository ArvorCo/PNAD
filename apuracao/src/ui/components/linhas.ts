// Gráfico de linhas e sparklines em SVG com nós estáveis: cada série guarda o seu <path>
// entre atualizações (Map<id, Element>). As contas de escala, domínio, caminho, ajuste
// linear e separação de rótulos são puras e testadas em tests/ui/linhas.test.ts.

const NS = "http://www.w3.org/2000/svg";

export interface Ponto {
  x: number;
  y: number;
}

export interface SerieLinha {
  id: string;
  cor: string;
  pontos: readonly Ponto[];
  /** Rótulo no fim da linha (nome e valor); omitido nas sparklines. */
  rotulo?: string;
  espessura?: number; // px, padrão 4
  tracejado?: boolean;
}

export interface Marcador {
  x: number;
  y: number;
  cor: string;
  texto?: string;
}

export interface Tick {
  v: number;
  texto: string;
}

export interface Margem {
  t: number;
  r: number;
  b: number;
  l: number;
}

export interface OpcoesDesenho {
  dominioX: readonly [number, number];
  dominioY: readonly [number, number];
  ticksX?: readonly Tick[];
  ticksY?: readonly Tick[];
  marcadores?: readonly Marcador[];
  /** Preenche a área sob a primeira série (ritmo da apuração). */
  area?: boolean;
  /** Linha horizontal de referência (100% de seções, por exemplo). */
  referenciaY?: { v: number; texto: string };
}

// ---------- contas puras ----------

export type Escala = (v: number) => number;

/** Escala linear de [d0, d1] para [r0, r1]; domínio degenerado vai para o meio. */
export function escalaLinear(d0: number, d1: number, r0: number, r1: number): Escala {
  const span = d1 - d0;
  if (!(Math.abs(span) > 0)) return () => (r0 + r1) / 2;
  return v => {
    const t = (v - d0) / span;
    return r0 * (1 - t) + r1 * t;
  };
}

const fmt = (v: number): string => (Math.round(v * 10) / 10).toString();

/** Atributo `d` de um path. Pontos não finitos quebram a linha (novo M). */
export function caminho(pontos: readonly Ponto[], sx: Escala, sy: Escala): string {
  let d = "";
  let aberto = false;
  for (const p of pontos) {
    if (!Number.isFinite(p.x) || !Number.isFinite(p.y)) {
      aberto = false;
      continue;
    }
    d += `${aberto ? "L" : "M"}${fmt(sx(p.x))} ${fmt(sy(p.y))}`;
    aberto = true;
  }
  return d;
}

/** Path da área entre a linha e a base `y0` do domínio. */
export function caminhoArea(pontos: readonly Ponto[], sx: Escala, sy: Escala, y0: number): string {
  const ok = pontos.filter(p => Number.isFinite(p.x) && Number.isFinite(p.y));
  const primeiro = ok[0];
  const ultimo = ok[ok.length - 1];
  if (!primeiro || !ultimo) return "";
  return `${caminho(ok, sx, sy)}L${fmt(sx(ultimo.x))} ${fmt(sy(y0))}L${fmt(sx(primeiro.x))} ${fmt(sy(y0))}Z`;
}

/**
 * Domínio vertical: o preferido quando todos os valores cabem nele; senão o ajuste aos
 * dados com folga, arredondado ao `passo` e sem passar dos limites [piso, teto].
 */
export function dominioAuto(
  valores: readonly number[],
  preferido: readonly [number, number] | null,
  passo = 5,
  piso = -Infinity,
  teto = Infinity,
): [number, number] {
  const v = valores.filter(Number.isFinite);
  if (v.length === 0) return preferido ? [preferido[0], preferido[1]] : [0, 1];
  const min = Math.min(...v);
  const max = Math.max(...v);
  if (preferido && min >= preferido[0] && max <= preferido[1]) return [preferido[0], preferido[1]];
  const folga = Math.max((max - min) * 0.08, passo / 2);
  let a = Math.max(piso, Math.floor((min - folga) / passo) * passo);
  let b = Math.min(teto, Math.ceil((max + folga) / passo) * passo);
  if (b <= a) {
    a = Math.max(piso, a - passo);
    b = Math.min(teto, b + passo);
  }
  return [a, b];
}

/** Ticks "redondos" (1, 2, 2,5 ou 5 × 10^k) cobrindo [a, b], no máximo ~n. */
export function ticksRedondos(a: number, b: number, n = 5): number[] {
  if (!(b > a)) return [a];
  const bruto = (b - a) / Math.max(1, n);
  const pot = 10 ** Math.floor(Math.log10(bruto));
  const passo = [1, 2, 2.5, 5, 10].map(m => m * pot).find(p => p >= bruto) ?? 10 * pot;
  const saida: number[] = [];
  for (let v = Math.ceil(a / passo) * passo; v <= b + passo * 1e-9; v += passo) saida.push(Math.round(v / passo) * passo);
  return saida;
}

/** Mínimos quadrados y = a + b·x. Null com menos de 2 pontos ou x constante. */
export function ajusteLinear(pontos: readonly Ponto[]): { a: number; b: number } | null {
  const ok = pontos.filter(p => Number.isFinite(p.x) && Number.isFinite(p.y));
  const n = ok.length;
  if (n < 2) return null;
  const mx = ok.reduce((s, p) => s + p.x, 0) / n;
  const my = ok.reduce((s, p) => s + p.y, 0) / n;
  let sxx = 0;
  let sxy = 0;
  for (const p of ok) {
    sxx += (p.x - mx) ** 2;
    sxy += (p.x - mx) * (p.y - my);
  }
  if (!(sxx > 0)) return null;
  const b = sxy / sxx;
  return { a: my - b * mx, b };
}

/**
 * Afasta rótulos verticais para que fiquem a pelo menos `gap` uns dos outros, dentro de
 * [min, max], preservando a ordem. Devolve as novas posições na ordem de entrada.
 */
export function separarRotulos(ys: readonly number[], gap: number, min = -Infinity, max = Infinity): number[] {
  const idx = ys.map((y, i) => ({ y, i })).sort((a, b) => a.y - b.y);
  const pos = idx.map(o => o.y);
  for (let k = 0; k < pos.length; k++) {
    const anterior = k > 0 ? (pos[k - 1] ?? min) + gap : min;
    pos[k] = Math.max(pos[k] ?? 0, anterior);
  }
  // Se estourou embaixo, empurra de volta para cima.
  for (let k = pos.length - 1; k >= 0; k--) {
    const limite = k < pos.length - 1 ? (pos[k + 1] ?? max) - gap : max;
    pos[k] = Math.min(pos[k] ?? 0, limite);
  }
  const saida = new Array<number>(ys.length);
  idx.forEach((o, k) => (saida[o.i] = pos[k] ?? o.y));
  return saida;
}

// ---------- componente ----------

export interface OpcoesLinhas {
  largura: number;
  altura: number;
  margem?: Partial<Margem>;
  classe?: string;
  /** Sparkline: sem eixos, sem rótulos, traço mais fino. */
  mini?: boolean;
}

export interface Linhas {
  readonly el: SVGSVGElement;
  update(series: readonly SerieLinha[], opcoes: OpcoesDesenho): void;
  destroy(): void;
}

function no<K extends keyof SVGElementTagNameMap>(tag: K, attrs: Record<string, string | number> = {}): SVGElementTagNameMap[K] {
  const e = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, String(v));
  return e;
}

export function criarLinhas(container: HTMLElement, o: OpcoesLinhas): Linhas {
  const mini = o.mini ?? false;
  const m: Margem = { t: mini ? 4 : 16, r: mini ? 4 : 220, b: mini ? 4 : 44, l: mini ? 4 : 96, ...o.margem };
  let altura = o.altura;
  const el = no("svg", { viewBox: `0 0 ${o.largura} ${altura}`, class: `linhas${mini ? " linhas--mini" : ""} ${o.classe ?? ""}`.trim() });
  const gEixos = no("g", { class: "linhas-eixos" });
  const gArea = no("g", { class: "linhas-area" });
  const gSeries = no("g", { class: "linhas-series" });
  const gMarcas = no("g", { class: "linhas-marcas" });
  const gRotulos = no("g", { class: "linhas-rotulos" });
  el.append(gEixos, gArea, gSeries, gMarcas, gRotulos);
  container.append(el);

  const paths = new Map<string, SVGPathElement>();
  const rotulos = new Map<string, SVGTextElement>();
  let area: SVGPathElement | null = null;

  return {
    el,
    update(series, op) {
      // A altura acompanha a proporção do contêiner (largura fixa na referência), para o
      // texto do SVG não encolher quando o contêiner é mais baixo que o previsto.
      const caixa = container.getBoundingClientRect();
      if (caixa.width > 0 && caixa.height > 0) {
        const nova = Math.round((o.largura * caixa.height) / caixa.width);
        if (nova !== altura) {
          altura = nova;
          el.setAttribute("viewBox", `0 0 ${o.largura} ${altura}`);
        }
      }
      const x0 = m.l;
      const x1 = o.largura - m.r;
      const y0 = altura - m.b;
      const y1 = m.t;
      const sx = escalaLinear(op.dominioX[0], op.dominioX[1], x0, x1);
      const sy = escalaLinear(op.dominioY[0], op.dominioY[1], y0, y1);

      // Eixos e grade: poucos nós, recriados a cada atualização.
      gEixos.replaceChildren();
      if (!mini) {
        for (const t of op.ticksY ?? []) {
          const y = sy(t.v);
          gEixos.append(no("line", { x1: x0, x2: x1, y1: fmt(y), y2: fmt(y), class: "linhas-grade" }));
          const tx = no("text", { x: x0 - 12, y: fmt(y), class: "linhas-tick linhas-tick--y" });
          tx.textContent = t.texto;
          gEixos.append(tx);
        }
        for (const t of op.ticksX ?? []) {
          const x = sx(t.v);
          gEixos.append(no("line", { x1: fmt(x), x2: fmt(x), y1: y0, y2: y0 + 8, class: "linhas-marca-x" }));
          const tx = no("text", { x: fmt(x), y: y0 + 34, class: "linhas-tick linhas-tick--x" });
          tx.textContent = t.texto;
          gEixos.append(tx);
        }
        gEixos.append(no("line", { x1: x0, x2: x1, y1: y0, y2: y0, class: "linhas-base" }));
        if (op.referenciaY) {
          const y = sy(op.referenciaY.v);
          gEixos.append(no("line", { x1: x0, x2: x1, y1: fmt(y), y2: fmt(y), class: "linhas-ref" }));
          const tx = no("text", { x: x1, y: fmt(y - 10), class: "linhas-ref-texto" });
          tx.textContent = op.referenciaY.texto;
          gEixos.append(tx);
        }
      }

      // Área sob a primeira série.
      const primeira = series[0];
      if (op.area && primeira) {
        area ??= gArea.appendChild(no("path", { class: "linhas-preenchimento" }));
        area.setAttribute("d", caminhoArea(primeira.pontos, sx, sy, op.dominioY[0]));
        area.setAttribute("fill", primeira.cor);
      } else if (area) {
        area.remove();
        area = null;
      }

      // Séries com nós estáveis.
      const vivos = new Set<string>();
      const fins: { id: string; y: number; s: SerieLinha }[] = [];
      for (const s of series) {
        vivos.add(s.id);
        let p = paths.get(s.id);
        if (!p) {
          p = no("path", { class: "linhas-serie", fill: "none", "stroke-linejoin": "round", "stroke-linecap": "round" });
          paths.set(s.id, p);
          gSeries.append(p);
        }
        p.setAttribute("d", caminho(s.pontos, sx, sy));
        p.setAttribute("stroke", s.cor);
        p.setAttribute("stroke-width", String(s.espessura ?? (mini ? 3 : 4)));
        if (s.tracejado) p.setAttribute("stroke-dasharray", "8 8");
        else p.removeAttribute("stroke-dasharray");
        const ult = [...s.pontos].reverse().find(q => Number.isFinite(q.x) && Number.isFinite(q.y));
        if (ult && s.rotulo && !mini) fins.push({ id: s.id, y: sy(ult.y), s });
      }
      for (const [id, p] of paths) {
        if (!vivos.has(id)) {
          p.remove();
          paths.delete(id);
        }
      }

      // Rótulos no fim das linhas, separados para não colidir.
      const ys = separarRotulos(
        fins.map(f => f.y),
        30,
        y1 + 12,
        y0 - 6,
      );
      const comRotulo = new Set<string>();
      fins.forEach((f, i) => {
        comRotulo.add(f.id);
        let t = rotulos.get(f.id);
        if (!t) {
          t = no("text", { class: "linhas-rotulo" });
          rotulos.set(f.id, t);
          gRotulos.append(t);
        }
        t.setAttribute("x", String(x1 + 14));
        t.setAttribute("y", fmt(ys[i] ?? f.y));
        t.setAttribute("fill", f.s.cor);
        t.textContent = f.s.rotulo ?? "";
      });
      for (const [id, t] of rotulos) {
        if (!comRotulo.has(id)) {
          t.remove();
          rotulos.delete(id);
        }
      }

      // Marcadores (viradas): poucos, recriados.
      gMarcas.replaceChildren();
      for (const mk of op.marcadores ?? []) {
        const cx = sx(mk.x);
        const cy = sy(mk.y);
        gMarcas.append(no("circle", { cx: fmt(cx), cy: fmt(cy), r: mini ? 4 : 9, class: "linhas-virada", stroke: mk.cor }));
        if (mk.texto && !mini) {
          const tx = no("text", { x: fmt(cx), y: fmt(cy - 18), class: "linhas-virada-texto" });
          tx.textContent = mk.texto;
          gMarcas.append(tx);
        }
      }
    },
    destroy() {
      el.remove();
      paths.clear();
      rotulos.clear();
    },
  };
}

/**
 * Ritmo recente de uma série acumulada (x em ms, y em contagem): reta dos pontos dentro
 * da janela final, com o ponto imediatamente anterior para haver pelo menos dois.
 * Devolve a taxa por minuto e o instante em que a reta alcança `alvo` (null sem ritmo).
 */
export function ritmoRecente(
  pontos: readonly Ponto[],
  janelaMs: number,
  alvo: number,
): { porMinuto: number; previsao: number | null } | null {
  const ok = pontos.filter(p => Number.isFinite(p.x) && Number.isFinite(p.y)).sort((a, b) => a.x - b.x);
  const ultimo = ok[ok.length - 1];
  if (!ultimo) return null;
  const inicio = ultimo.x - janelaMs;
  let k = ok.findIndex(p => p.x >= inicio);
  if (k > 0 && ok.length - k < 2) k -= 1;
  const janela = ok.slice(Math.max(0, k));
  const ajuste = ajusteLinear(janela);
  if (!ajuste) return null;
  const porMinuto = ajuste.b * 60_000;
  if (ultimo.y >= alvo) return { porMinuto, previsao: ultimo.x };
  const previsao = ajuste.b > 0 ? Math.max(ultimo.x, (alvo - ajuste.a) / ajuste.b) : null;
  return { porMinuto, previsao };
}
