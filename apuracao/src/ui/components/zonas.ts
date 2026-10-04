// Cartograma de zonas eleitorais: treemap squarified (d3-hierarchy) com área
// proporcional ao eleitorado da zona, um tile por unidade, ordenados por código.

import { hierarchy, treemap, treemapSquarify } from "d3-hierarchy";
import { NAO_INICIADO, textoSobre } from "../data/cores.ts";
import { pct } from "../data/format.ts";
import type { UnidadeMapa } from "../state/types.ts";
import type { Mapa, MapaOpcoes } from "./mapa.ts";

const SVG_NS = "http://www.w3.org/2000/svg";
const LARGURA = 1152;
const ALTURA = 800;

export const NOTA_ZONA_UNICA = "este município tem uma única zona";
export const FONTE_ZONA = 24;
export const FONTE_PCT = 22;

export interface Tile {
  cd: string;
  x0: number;
  y0: number;
  x1: number;
  y1: number;
}

/** Pesos dos tiles: eleitorado; sem nenhum `te`, áreas iguais; `te` ausente vira a mediana dos presentes. */
export function pesosZonas(unidades: UnidadeMapa[]): number[] {
  const presentes = unidades.map(u => u.te ?? 0).filter(t => t > 0).sort((a, b) => a - b);
  if (presentes.length === 0) return unidades.map(() => 1);
  const meio = Math.floor(presentes.length / 2);
  const mediana = presentes.length % 2 ? (presentes[meio] ?? 1) : ((presentes[meio - 1] ?? 1) + (presentes[meio] ?? 1)) / 2;
  return unidades.map(u => (u.te && u.te > 0 ? u.te : mediana));
}

export const ordenarPorCd = (unidades: UnidadeMapa[]): UnidadeMapa[] =>
  [...unidades].sort((a, b) => a.cd.localeCompare(b.cd, "pt-BR", { numeric: true }));

/** Layout squarified no retângulo `largura × altura`, espaçamento interno `padding`. */
export function layoutZonas(unidades: UnidadeMapa[], largura = LARGURA, altura = ALTURA, padding = 4): Tile[] {
  const ordenadas = ordenarPorCd(unidades);
  if (ordenadas.length === 0) return [];
  const pesos = pesosZonas(ordenadas);
  interface Folha {
    cd: string;
    peso: number;
  }
  interface Raiz {
    children: Folha[];
  }
  const raiz = hierarchy<Raiz | Folha>({ children: ordenadas.map((u, i) => ({ cd: u.cd, peso: pesos[i] ?? 1 })) }, d =>
    "children" in d ? d.children : undefined,
  ).sum(d => ("peso" in d ? d.peso : 0));
  const arranjo = treemap<Raiz | Folha>().tile(treemapSquarify).size([largura, altura]).paddingInner(padding).round(false);
  return arranjo(raiz)
    .leaves()
    .map(n => ({ cd: "cd" in n.data ? n.data.cd : "", x0: n.x0, y0: n.y0, x1: n.x1, y1: n.y1 }));
}

export type NivelRotulo = "completo" | "numero" | "nada";

/** Largura estimada do número da zona (4 dígitos, Archivo 600 a 22 px). */
export const LARGURA_NUMERO = 4 * FONTE_PCT * 0.6;

/**
 * Rótulo completo (nome + %) a partir de 140 × 70; só o número a partir de 40 × 24
 * e desde que o número caiba com 4 px de cada lado; nada abaixo.
 */
export function nivelRotulo(w: number, h: number, larguraNumero = 0): NivelRotulo {
  if (w >= 140 && h >= 70) return "completo";
  if (w >= Math.max(40, larguraNumero + 8) && h >= 24) return "numero";
  return "nada";
}

/** "0248" a partir de "0248", "248", "z0248" ou "sp71072-z0248". */
export function numeroZona(cd: string): string {
  const m = /(\d+)\D*$/.exec(cd);
  return (m?.[1] ?? cd).padStart(4, "0");
}

/** Assinatura do conjunto de zonas e eleitorados: muda só quando o layout precisa mudar. */
export const assinatura = (unidades: UnidadeMapa[]): string =>
  ordenarPorCd(unidades)
    .map(u => `${u.cd}:${u.te ?? 0}`)
    .join("|");

const criar = <K extends keyof SVGElementTagNameMap>(tag: K, attrs: Record<string, string | number> = {}): SVGElementTagNameMap[K] => {
  const el = document.createElementNS(SVG_NS, tag);
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, String(v));
  return el;
};

interface NoZona {
  g: SVGGElement;
  rect: SVGRectElement;
  titulo: SVGTitleElement;
  nome: SVGTextElement | null;
  linha: SVGTextElement | null;
  tile: Tile;
  nivel: NivelRotulo;
}

export function criarZonas(container: HTMLElement, opcoes: MapaOpcoes): Mapa {
  const largura = opcoes.largura ?? LARGURA;
  const altura = opcoes.altura ?? ALTURA;
  const el = criar("svg", {
    viewBox: `0 0 ${largura} ${altura}`,
    preserveAspectRatio: "xMidYMid meet",
    width: "100%",
    height: "100%",
    role: "img",
    class: `mapa mapa--zona${opcoes.aoClicar ? " mapa--clicavel" : ""}`,
  });
  el.setAttribute("aria-label", "Cartograma das zonas eleitorais, área proporcional ao eleitorado");
  const gTiles = criar("g", { class: "mapa__tiles" });
  const gRealce = criar("g", { class: "mapa__realce", "aria-hidden": "true" });
  el.append(gTiles, gRealce);
  container.appendChild(el);

  const nos = new Map<string, NoZona>();
  const unidades = new Map<string, UnidadeMapa>();
  let assin = "";
  let destaque: string | null = null;
  let nota: SVGTextElement | null = null;

  const segundaLinha = (u: UnidadeMapa, espaco: number): string => {
    const r = opcoes.rotulo?.(u);
    if (r) return r;
    if (!u.lider) return u.pst > 0 ? "" : "sem seções";
    const longo = `${u.lider.nmu} ${pct(u.lider.pvapn)}`;
    return longo.length * FONTE_PCT * 0.6 <= espaco ? longo : pct(u.lider.pvapn);
  };

  const montar = (lista: UnidadeMapa[]): void => {
    gTiles.replaceChildren();
    nos.clear();
    nota?.remove();
    nota = null;
    const tiles = layoutZonas(lista, largura, altura);
    const frag = document.createDocumentFragment();
    for (const tile of tiles) {
      const w = tile.x1 - tile.x0;
      const h = tile.y1 - tile.y0;
      const nivel = nivelRotulo(w, h, LARGURA_NUMERO);
      const g = criar("g", { class: "mapa__tile", "data-cd": tile.cd });
      const rect = criar("rect", { x: tile.x0, y: tile.y0, width: w, height: h, class: "mapa__tile-rect" });
      rect.style.fill = NAO_INICIADO;
      const titulo = criar("title");
      rect.appendChild(titulo);
      g.appendChild(rect);
      let nome: SVGTextElement | null = null;
      let linha: SVGTextElement | null = null;
      if (tiles.length === 1) {
        nome = criar("text", { x: tile.x0 + w / 2, y: tile.y0 + h / 2 - 20, "text-anchor": "middle", class: "mapa__zona-nome" });
        linha = criar("text", { x: tile.x0 + w / 2, y: tile.y0 + h / 2 + 16, "text-anchor": "middle", class: "mapa__zona-pct" });
        nota = criar("text", { x: tile.x0 + w / 2, y: tile.y0 + h / 2 + 56, "text-anchor": "middle", class: "mapa__zona-nota" });
        nota.textContent = NOTA_ZONA_UNICA;
      } else if (nivel === "completo") {
        nome = criar("text", { x: tile.x0 + 10, y: tile.y0 + 10 + FONTE_ZONA * 0.8, class: "mapa__zona-nome" });
        linha = criar("text", { x: tile.x0 + 10, y: tile.y0 + 18 + FONTE_ZONA * 0.8 + FONTE_PCT, class: "mapa__zona-pct" });
      } else if (nivel === "numero") {
        nome = criar("text", {
          x: tile.x0 + w / 2,
          y: tile.y0 + h / 2,
          "text-anchor": "middle",
          "dominant-baseline": "central",
          class: "mapa__zona-num",
        });
      }
      for (const t of [nome, linha, nota]) if (t) g.appendChild(t);
      nos.set(tile.cd, { g, rect, titulo, nome, linha, tile, nivel });
      frag.appendChild(g);
    }
    gTiles.appendChild(frag);
  };

  const pintar = (): void => {
    for (const [cd, no] of nos) {
      const u = unidades.get(cd);
      if (!u) continue;
      const fill = opcoes.cor(u);
      no.rect.style.fill = fill;
      const cor = textoSobre(fill);
      const num = numeroZona(cd);
      const t = opcoes.titulo?.(u) ?? `Zona ${num}`;
      if (no.titulo.textContent !== t) no.titulo.textContent = t;
      const unica = nos.size === 1;
      if (no.nome) {
        const txt = no.nivel === "numero" && !unica ? num : `Zona ${num}`;
        if (no.nome.textContent !== txt) no.nome.textContent = txt;
        no.nome.style.fill = cor;
      }
      if (no.linha) {
        const txt = segundaLinha(u, unica ? largura - 40 : no.tile.x1 - no.tile.x0 - 20);
        if (no.linha.textContent !== txt) no.linha.textContent = txt;
        no.linha.style.fill = cor;
      }
      if (unica && nota) nota.style.fill = cor;
    }
    aplicarDestaque();
  };

  const aplicarDestaque = (): void => {
    for (const no of nos.values()) no.g.classList.toggle("mapa__unidade--destaque", no.tile.cd === destaque);
    gRealce.replaceChildren();
    const no = destaque ? nos.get(destaque) : undefined;
    if (!no) return;
    gTiles.appendChild(no.g);
    const { x0, y0, x1, y1 } = no.tile;
    const caixa = { x: x0, y: y0, width: x1 - x0, height: y1 - y0 };
    gRealce.append(criar("rect", { ...caixa, class: "mapa__realce-lime" }), criar("rect", { ...caixa, class: "mapa__realce-tinta" }));
  };

  const aoClique = (ev: MouseEvent): void => {
    const cd = (ev.target as Element | null)?.closest("[data-cd]")?.getAttribute("data-cd");
    const u = cd ? unidades.get(cd) : undefined;
    if (u) opcoes.aoClicar?.(u);
  };
  if (opcoes.aoClicar) el.addEventListener("click", aoClique);

  return {
    el,
    update(lista) {
      unidades.clear();
      for (const u of lista) unidades.set(u.cd, u);
      const nova = assinatura(lista);
      if (nova !== assin) {
        assin = nova;
        montar(lista);
      }
      pintar();
    },
    destacar(cd) {
      destaque = cd;
      aplicarDestaque();
    },
    destroy() {
      el.removeEventListener("click", aoClique);
      el.remove();
    },
  };
}
