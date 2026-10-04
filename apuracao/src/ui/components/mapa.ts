// Componente de mapa do telão. Um mapa desenha unidades (UFs, municípios ou tiles de
// zona) e pinta cada uma pela cor devolvida por `cor(unidade)`, já com a banda de
// parcialidade aplicada. UF e município usam a malha IBGE (`data/geo.ts`) com a
// projeção da casa (`geo/projecao.ts`); zona usa o treemap de `zonas.ts`.

import { malhaMunicipios, malhaUfs, codigoIbge } from "../data/geo.ts";
import type { ColecaoFeicoes, Geometria } from "../data/geo.ts";
import { NAO_INICIADO, textoSobre } from "../data/cores.ts";
import { CAIXA_BR, caixaDe, caminho, centroide, fitExtent } from "../geo/projecao.ts";
import type { Ajuste } from "../geo/projecao.ts";
import type { NivelMapa, UnidadeMapa } from "../state/types.ts";
import { criarZonas } from "./zonas.ts";

export interface MapaOpcoes {
  nivel: NivelMapa;
  /** "br" para UFs, "sp" para municípios de SP, "sp71072" para zonas de São Paulo. */
  pai: string;
  /** Cor de preenchimento final (quem chama aplica `corPorBanda`). */
  cor: (u: UnidadeMapa) => string;
  /**
   * Rótulo sobre a unidade. Nível `uf`: substitui a sigla quando devolve texto.
   * Nível `mun`: só as unidades com texto ganham rótulo (capitais, por exemplo).
   * Nível `zona`: segunda linha do tile (sem ela, o % do líder).
   */
  rotulo?: (u: UnidadeMapa) => string | null;
  /** Clique numa unidade (drill). */
  aoClicar?: (u: UnidadeMapa) => void;
  /** Texto do `<title>` para acessibilidade. */
  titulo?: (u: UnidadeMapa) => string;
  /** Unidades com dado do TSE e sem polígono na malha IBGE (ex.: MT 5101837). */
  aoSemGeometria?: (unidades: UnidadeMapa[]) => void;
  /** Caixa de desenho em unidades de usuário; padrão 1152 × 800. */
  largura?: number;
  altura?: number;
}

export interface Mapa {
  readonly el: SVGSVGElement;
  /** Reaplica cores, rótulos e títulos sem recriar os nós (transição de `fill` por CSS). */
  update(unidades: UnidadeMapa[]): void;
  /** Contorno lime na unidade; `null` limpa. */
  destacar(cd: string | null): void;
  destroy(): void;
}

export const SVG_NS = "http://www.w3.org/2000/svg";
export const LARGURA_PADRAO = 1152;
export const ALTURA_PADRAO = 800;

/** Código IBGE da UF (`codarea` de br_uf) → sigla. Mesma tabela de scripts/voto_util_mapa.py. */
export const IBGE_UF: Readonly<Record<string, string>> = {
  "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO",
  "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL",
  "28": "SE", "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP", "41": "PR",
  "42": "SC", "43": "RS", "50": "MS", "51": "MT", "52": "GO", "53": "DF",
};

/** Estados pequenos: rótulo fora do contorno com guia, deslocamento em graus (lon, lat para baixo). */
export const FORA: Readonly<Record<string, readonly [number, number]>> = {
  RN: [1.9, -0.2],
  PB: [2.3, 0.3],
  PE: [2.6, 1.1],
  AL: [2.3, 1.4],
  SE: [2.0, 1.8],
  ES: [2.4, 0.4],
  RJ: [2.2, 1.6],
  DF: [2.6, -0.6],
};

/** Ajuste fino do rótulo dentro do contorno, em graus. */
export const LABEL_NUDGE: Readonly<Record<string, readonly [number, number]>> = {
  GO: [0.2, 0.6],
  MG: [0.3, 0.2],
  PA: [0.0, 0.8],
  MT: [0.0, 0.3],
  BA: [0.4, 0.2],
};

export const FONTE_SIGLA = 24;
export const FONTE_ROTULO_MUN = 22;
/** Reserva à direita do Brasil para os rótulos deslocados do litoral. */
const MARGEM_ROTULOS_BR = 72;

/** Chave de uma feição da malha: sigla minúscula para UF, código IBGE para município. */
export function chaveFeicao(nivel: NivelMapa, codarea: string): string {
  if (nivel === "uf") return (IBGE_UF[codarea] ?? codarea).toLowerCase();
  return codarea;
}

/** Chave de uma unidade do TSE no mesmo espaço da malha. */
export function chaveUnidade(nivel: NivelMapa, u: UnidadeMapa): string {
  return nivel === "uf" ? u.cd.toLowerCase() : (u.cdi ?? "");
}

/** Unidades sem polígono correspondente na malha. */
export function semGeometria(nivel: NivelMapa, unidades: UnidadeMapa[], chaves: ReadonlySet<string>): UnidadeMapa[] {
  return unidades.filter(u => !chaves.has(chaveUnidade(nivel, u)));
}

export interface CaixaRotulo {
  id: string;
  x: number;
  y: number; // linha de base
  w: number;
  h: number;
}

/**
 * Afasta verticalmente rótulos que se sobrepõem na horizontal, de cima para baixo,
 * mantendo pelo menos `folga` entre caixas. Devolve novas posições (não altera a entrada).
 */
export function afastarRotulos(rotulos: CaixaRotulo[], folga = 4): CaixaRotulo[] {
  const ordem = rotulos.map(r => ({ ...r })).sort((a, b) => a.y - b.y);
  for (let i = 1; i < ordem.length; i++) {
    const r = ordem[i];
    if (!r) continue;
    for (let j = 0; j < i; j++) {
      const s = ordem[j];
      if (!s) continue;
      const cruzaX = r.x < s.x + s.w && s.x < r.x + r.w;
      if (cruzaX && r.y - r.h < s.y + folga) r.y = s.y + folga + r.h;
    }
  }
  return ordem;
}

/** Largura estimada de texto (sem medir no DOM), para caixas de rótulo. */
export const larguraTexto = (texto: string, fonte: number, fator = 0.62): number => texto.length * fonte * fator;

interface No {
  path: SVGPathElement;
  titulo: SVGTitleElement | null;
  chave: string;
  ancora: [number, number]; // centroide projetado
  rotuloPos: [number, number]; // posição do rótulo (UF)
  fora: boolean;
}

interface RotuloUf {
  g: SVGGElement;
  texto: SVGTextElement;
  caixa: SVGRectElement | null;
}

const criar = <K extends keyof SVGElementTagNameMap>(tag: K, attrs: Record<string, string | number> = {}): SVGElementTagNameMap[K] => {
  const el = document.createElementNS(SVG_NS, tag);
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, String(v));
  return el;
};

/**
 * Cria o mapa dentro de `container`, ocupando toda a área disponível.
 * A malha chega por promessa: o `<svg>` nasce vazio e `update` antes dela fica guardado.
 */
export function criarMapa(container: HTMLElement, opcoes: MapaOpcoes): Mapa {
  if (opcoes.nivel === "zona") return criarZonas(container, opcoes);

  const nivel = opcoes.nivel;
  const largura = opcoes.largura ?? LARGURA_PADRAO;
  const altura = opcoes.altura ?? ALTURA_PADRAO;
  const el = criar("svg", {
    viewBox: `0 0 ${largura} ${altura}`,
    preserveAspectRatio: "xMidYMid meet",
    width: "100%",
    height: "100%",
    role: "img",
    class: `mapa mapa--${nivel}${opcoes.aoClicar ? " mapa--clicavel" : ""}`,
  });
  el.setAttribute("aria-label", nivel === "uf" ? "Mapa do Brasil por estado" : `Mapa dos municípios de ${opcoes.pai.toUpperCase()}`);
  const gUnidades = criar("g", { class: "mapa__unidades" });
  const gRealce = criar("g", { class: "mapa__realce", "aria-hidden": "true" });
  const gRotulos = criar("g", { class: "mapa__rotulos", "aria-hidden": "true" });
  el.append(gUnidades, gRealce, gRotulos);
  container.appendChild(el);

  const nos = new Map<string, No>(); // chave da malha → nó
  const porCd = new Map<string, No>(); // cd do TSE → nó
  const unidadePorChave = new Map<string, UnidadeMapa>();
  const rotulosUf = new Map<string, RotuloUf>();
  let pronto = false;
  let destruido = false;
  let pendentes: UnidadeMapa[] | null = null;
  let destaque: string | null = null;
  let ultimaListaSem = "";

  const pintar = (unidades: UnidadeMapa[]): void => {
    unidadePorChave.clear();
    porCd.clear();
    for (const u of unidades) {
      const k = chaveUnidade(nivel, u);
      unidadePorChave.set(k, u);
      const no = nos.get(k);
      if (no) porCd.set(u.cd, no);
    }
    for (const no of nos.values()) {
      const u = unidadePorChave.get(no.chave);
      const fill = u ? opcoes.cor(u) : NAO_INICIADO;
      no.path.style.fill = fill;
      const t = u ? (opcoes.titulo?.(u) ?? u.nm) : nivel === "uf" ? no.chave.toUpperCase() : `${no.chave}: sem dados`;
      if (!no.titulo) {
        no.titulo = criar("title");
        no.path.appendChild(no.titulo);
      }
      if (no.titulo.textContent !== t) no.titulo.textContent = t;
      if (nivel === "uf") atualizarRotuloUf(no, u, fill);
    }
    if (nivel === "mun") desenharRotulosMun(unidades);

    const sem = semGeometria(nivel, unidades, new Set(nos.keys()));
    const lista = sem.map(u => u.cd).join(" ");
    if (lista) el.setAttribute("data-sem-geometria", lista);
    else el.removeAttribute("data-sem-geometria");
    if (lista !== ultimaListaSem) {
      ultimaListaSem = lista;
      if (sem.length > 0) opcoes.aoSemGeometria?.(sem);
    }
    aplicarDestaque();
  };

  const atualizarRotuloUf = (no: No, u: UnidadeMapa | undefined, fill: string): void => {
    const r = rotulosUf.get(no.chave);
    if (!r) return;
    const txt = (u && opcoes.rotulo?.(u)) || no.chave.toUpperCase();
    if (r.texto.textContent !== txt) r.texto.textContent = txt;
    if (r.caixa) {
      r.caixa.setAttribute("width", String(larguraTexto(txt, FONTE_SIGLA) + 12));
      return;
    }
    const claro = textoSobre(fill) === "#ffffff";
    r.texto.classList.toggle("mapa__sigla--claro", claro);
  };

  /** Largura renderizada do texto; estimativa quando não há layout (aba oculta, fonte ausente). */
  const medir = (txt: string, classe: string, fonte: number): number => {
    const t = criar("text", { class: classe, x: -9999, y: -9999 });
    t.textContent = txt;
    gRotulos.appendChild(t);
    let w = 0;
    try {
      w = t.getComputedTextLength();
    } catch {
      w = 0;
    }
    t.remove();
    return w > 0 ? w : larguraTexto(txt, fonte);
  };

  let assinaturaRotulos = "";
  let ultimasUnidades: UnidadeMapa[] = [];
  const desenharRotulosMun = (unidades: UnidadeMapa[], forcar = false): void => {
    ultimasUnidades = unidades;
    if (!opcoes.rotulo) return;
    const pedidos: { u: UnidadeMapa; txt: string; no: No }[] = [];
    for (const u of unidades) {
      const txt = opcoes.rotulo(u);
      const no = nos.get(chaveUnidade(nivel, u));
      if (txt && no) pedidos.push({ u, txt, no });
    }
    const assin = pedidos.map(p => `${p.u.cd}:${p.txt}`).join("|");
    if (assin === assinaturaRotulos && !forcar) return;
    assinaturaRotulos = assin;
    gRotulos.replaceChildren();
    const caixas: CaixaRotulo[] = [];
    const ancoras = new Map<string, [number, number]>();
    for (const { u, txt, no } of pedidos) {
      const [ax, ay] = no.ancora;
      const w = medir(txt, "mapa__nome", FONTE_ROTULO_MUN) + 16;
      const h = FONTE_ROTULO_MUN + 10;
      // À direita do ponto; vira para a esquerda se encostar na borda.
      const x = ax + 10 + w > largura - 4 ? ax - 10 - w : ax + 10;
      const id = `${u.cd}\u0000${txt}`;
      caixas.push({ id, x, y: Math.max(h + 4, Math.min(altura - 4, ay + h / 2)), w, h });
      ancoras.set(id, no.ancora);
    }
    const frag = document.createDocumentFragment();
    for (const c of afastarRotulos(caixas)) {
      const [cd, txt] = c.id.split("\u0000");
      const ancora = ancoras.get(c.id);
      if (!ancora || txt === undefined) continue;
      const g = criar("g", { class: "mapa__rotulo-mun", "data-cd": cd ?? "" });
      g.append(
        criar("circle", { cx: ancora[0], cy: ancora[1], r: 4.5, class: "mapa__ponto" }),
        criar("rect", { x: c.x, y: c.y - c.h, width: c.w, height: c.h, rx: 5, class: "mapa__caixa" }),
      );
      const t = criar("text", { x: c.x + 8, y: c.y - c.h / 2, "dominant-baseline": "central", class: "mapa__nome" });
      t.textContent = txt;
      g.appendChild(t);
      frag.appendChild(g);
    }
    gRotulos.appendChild(frag);
  };
  // Remede quando as fontes chegarem: a largura da caixa depende da Archivo.
  if (nivel === "mun") {
    void document.fonts?.ready.then(() => {
      if (!destruido && pronto) desenharRotulosMun(ultimasUnidades, true);
    });
  }

  const aplicarDestaque = (): void => {
    for (const p of gUnidades.querySelectorAll(".mapa__unidade--destaque")) p.classList.remove("mapa__unidade--destaque");
    gRealce.replaceChildren();
    if (!destaque) return;
    const no = porCd.get(destaque) ?? (nivel === "uf" ? nos.get(destaque.toLowerCase()) : undefined);
    if (!no) return;
    no.path.classList.add("mapa__unidade--destaque");
    gUnidades.appendChild(no.path);
    const d = no.path.getAttribute("d") ?? "";
    gRealce.append(criar("path", { d, class: "mapa__realce-lime" }), criar("path", { d, class: "mapa__realce-tinta" }));
  };

  const montar = (malha: ColecaoFeicoes): void => {
    const t0 = performance.now();
    const feicoes = malha.features.filter((f): f is typeof f & { geometry: Geometria } => f.geometry !== null);
    let ajuste: Ajuste;
    if (nivel === "uf") ajuste = fitExtent(CAIXA_BR, largura - MARGEM_ROTULOS_BR, altura, 12);
    else ajuste = fitExtent(caixaDe(feicoes.map(f => f.geometry)), largura, altura, 16);

    const frag = document.createDocumentFragment();
    const rotulos: CaixaRotulo[] = [];
    for (const f of feicoes) {
      const chave = chaveFeicao(nivel, codigoIbge(f));
      const path = criar("path", { d: caminho(f.geometry, ajuste.projetar), class: "mapa__unidade", "data-cd": chave });
      path.style.fill = NAO_INICIADO;
      const [lon, lat] = centroide(f.geometry);
      const ancora = ajuste.projetar(lon, lat);
      const sigla = chave.toUpperCase();
      let rotuloPos = ancora;
      let fora = false;
      if (nivel === "uf") {
        const desloc = FORA[sigla];
        if (desloc) {
          fora = true;
          rotuloPos = [ancora[0] + desloc[0] * ajuste.escala * ajuste.cos, ancora[1] + desloc[1] * ajuste.escala];
          const w = larguraTexto(sigla, FONTE_SIGLA) + 12;
          const h = FONTE_SIGLA + 8;
          rotulos.push({ id: sigla, x: rotuloPos[0] - 6, y: rotuloPos[1] + h / 2, w, h });
        } else {
          const n = LABEL_NUDGE[sigla] ?? [0, 0];
          rotuloPos = ajuste.projetar(lon + n[0], lat - n[1]);
        }
      }
      const no: No = { path, titulo: null, chave, ancora, rotuloPos, fora };
      nos.set(chave, no);
      frag.appendChild(path);
    }
    gUnidades.appendChild(frag);

    if (nivel === "uf") {
      const rf = document.createDocumentFragment();
      const posFora = new Map(afastarRotulos(rotulos).map(r => [r.id, r]));
      for (const no of nos.values()) {
        const sigla = no.chave.toUpperCase();
        const g = criar("g", { class: `mapa__rotulo-uf${no.fora ? " mapa__rotulo-uf--fora" : ""}` });
        let caixa: SVGRectElement | null = null;
        let texto: SVGTextElement;
        const c = posFora.get(sigla);
        if (no.fora && c) {
          const [ax, ay] = no.ancora;
          const tx = c.x + 6;
          const ty = c.y - c.h / 2;
          g.appendChild(criar("line", { x1: ax, y1: ay, x2: c.x, y2: ty, class: "mapa__guia" }));
          caixa = criar("rect", { x: c.x, y: c.y - c.h, width: c.w, height: c.h, rx: 4, class: "mapa__caixa" });
          g.appendChild(caixa);
          texto = criar("text", { x: tx, y: ty, "dominant-baseline": "central", class: "mapa__sigla mapa__sigla--fora" });
        } else {
          const [x, y] = no.rotuloPos;
          texto = criar("text", { x, y, "text-anchor": "middle", "dominant-baseline": "central", class: "mapa__sigla" });
        }
        texto.textContent = sigla;
        g.appendChild(texto);
        rotulosUf.set(no.chave, { g, texto, caixa });
        rf.appendChild(g);
      }
      gRotulos.appendChild(rf);
    }

    pronto = true;
    pintar(pendentes ?? []);
    pendentes = null;
    el.setAttribute("data-render-ms", (performance.now() - t0).toFixed(1));
    el.setAttribute("data-pronto", "1");
  };

  const carregar = nivel === "uf" ? malhaUfs() : malhaMunicipios(opcoes.pai.slice(0, 2));
  carregar.then(
    malha => {
      if (!destruido) montar(malha);
    },
    (erro: unknown) => {
      if (destruido) return;
      const t = criar("text", { x: largura / 2, y: altura / 2, "text-anchor": "middle", class: "mapa__aviso" });
      t.textContent = "malha indisponível";
      el.appendChild(t);
      el.setAttribute("data-erro", erro instanceof Error ? erro.message : String(erro));
    },
  );

  const aoClique = (ev: MouseEvent): void => {
    const alvo = (ev.target as Element | null)?.closest("[data-cd]");
    const k = alvo?.getAttribute("data-cd");
    if (!k) return;
    const u = unidadePorChave.get(k) ?? [...unidadePorChave.values()].find(x => x.cd === k);
    if (u) opcoes.aoClicar?.(u);
  };
  if (opcoes.aoClicar) el.addEventListener("click", aoClique);

  return {
    el,
    update(unidades) {
      if (!pronto) {
        pendentes = unidades;
        return;
      }
      pintar(unidades);
    },
    destacar(cd) {
      destaque = cd;
      if (pronto) aplicarDestaque();
    },
    destroy() {
      destruido = true;
      el.removeEventListener("click", aoClique);
      el.remove();
    },
  };
}
