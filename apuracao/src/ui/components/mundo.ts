// Mapa-múndi da tela `exterior`: terra em papel escuro, oceano em papel, uma bolha por
// cidade do exterior onde há votação (UF `zz` do TSE). Área da bolha proporcional ao
// eleitorado (raio pela raiz), cor do líder já com a banda de seções aplicada por quem
// chama. Coordenadas das cidades vêm de `public/exterior_cidades.json` (gazetteer
// GeoNames, gerado por scripts/gerar-mundo.ts), porque o TSE grava latitude −1 no exterior.
// Implementa o contrato `Mapa` de mapa.ts sem mexer em `NivelMapa`.

import { malhaMundo } from "../data/geo.ts";
import type { ColecaoFeicoes, Geometria } from "../data/geo.ts";
import { NAO_INICIADO } from "../data/cores.ts";
import { nomeProprio } from "../data/format.ts";
import { caminho, fitExtent } from "../geo/projecao.ts";
import type { Ajuste, Caixa } from "../geo/projecao.ts";
import type { UnidadeMapa } from "../state/types.ts";
import type { Mapa } from "./mapa.ts";
import { ALTURA_PADRAO, LARGURA_PADRAO, larguraTexto, SVG_NS } from "./mapa.ts";

// ---------- partes puras ----------

/** Lon −180..180, lat −60..85, cosseno de 20° N como compromisso entre hemisférios. */
export const CAIXA_MUNDO: Caixa = { lon0: -180, lon1: 180, lat0: -60, lat1: 85, latRef: 20 };

export const RAIO_MIN = 6;
export const RAIO_EXTRA = 22;
export const ROTULOS_MAX = 12;
export const FONTE_ROTULO = 22;

/** Projeção do mundo ajustada à caixa de desenho. */
export const ajusteMundo = (largura = LARGURA_PADRAO, altura = ALTURA_PADRAO, pad = 8): Ajuste =>
  fitExtent(CAIXA_MUNDO, largura, altura, pad);

/** Raio da bolha: 6 px mais 22 px pela raiz da fração do maior eleitorado. */
export function raioBolha(te: number | undefined, teMax: number): number {
  if (!(teMax > 0) || !(te !== undefined && te > 0)) return RAIO_MIN;
  return RAIO_MIN + RAIO_EXTRA * Math.sqrt(Math.min(1, te / teMax));
}

export interface PedidoRotulo {
  cd: string;
  /** Centro e raio da bolha. */
  x: number;
  y: number;
  r: number;
  /** Largura e altura da caixa do rótulo. */
  w: number;
  h: number;
}

export interface RotuloPosto {
  cd: string;
  x: number; // canto esquerdo da caixa
  y: number; // topo da caixa
  w: number;
  h: number;
}

const cruza = (a: RotuloPosto, b: RotuloPosto, folga: number): boolean =>
  a.x < b.x + b.w + folga && b.x < a.x + a.w + folga && a.y < b.y + b.h + folga && b.y < a.y + a.h + folga;

/**
 * Rótulos à direita da bolha, na ordem dada (a maior cidade primeiro). Se a caixa sair da
 * área ou cruzar a de uma cidade maior, tenta a esquerda; se ainda cruzar, o rótulo some.
 */
export function rotulosSemSobreposicao(pedidos: readonly PedidoRotulo[], largura: number, altura: number, folga = 2): RotuloPosto[] {
  const postos: RotuloPosto[] = [];
  for (const p of pedidos) {
    const y = Math.max(0, Math.min(altura - p.h, p.y - p.h / 2));
    const opcoes: RotuloPosto[] = [
      { cd: p.cd, x: p.x + p.r + 6, y, w: p.w, h: p.h },
      { cd: p.cd, x: p.x - p.r - 6 - p.w, y, w: p.w, h: p.h },
    ];
    const ok = opcoes.find(o => o.x >= 0 && o.x + o.w <= largura && !postos.some(q => cruza(o, q, folga)));
    if (ok) postos.push(ok);
  }
  return postos;
}

/** Ordem de desenho: maiores primeiro, para as bolhas pequenas ficarem por cima. */
export function ordemDeDesenho<T extends { cd: string; r: number }>(itens: readonly T[]): T[] {
  return [...itens].sort((a, b) => b.r - a.r || a.cd.localeCompare(b.cd));
}

// ---------- cidades ----------

export interface CidadeExterior {
  cd: string; // código TSE, 5 dígitos
  nm: string;
  lat: number;
  lon: number;
  pais: string; // ISO-2
}

let cacheCidades: Promise<CidadeExterior[]> | null = null;

/** Cidades do exterior com coordenada (arquivo versionado em public/). */
export function cidadesExterior(): Promise<CidadeExterior[]> {
  if (!cacheCidades) {
    const p = fetch("/exterior_cidades.json").then(async r => {
      if (!r.ok) throw new Error(`cidades do exterior ausentes (HTTP ${r.status})`);
      return (await r.json()) as CidadeExterior[];
    });
    p.catch(() => {
      cacheCidades = null;
    });
    cacheCidades = p;
  }
  return cacheCidades;
}

// ---------- componente ----------

export interface MundoOpcoes {
  /** Cor de preenchimento final (quem chama aplica `corPorBanda`). */
  cor: (u: UnidadeMapa) => string;
  /** Texto do rótulo das maiores cidades; padrão, o nome próprio. */
  rotulo?: (u: UnidadeMapa) => string;
  titulo?: (u: UnidadeMapa) => string;
  aoClicar?: (u: UnidadeMapa) => void;
  /** Clique fora das bolhas (oceano ou terra). */
  aoClicarFundo?: () => void;
  largura?: number;
  altura?: number;
}

interface NoCidade {
  cidade: CidadeExterior;
  circulo: SVGCircleElement;
  titulo: SVGTitleElement;
  x: number;
  y: number;
  r: number;
}

const criar = <K extends keyof SVGElementTagNameMap>(tag: K, attrs: Record<string, string | number> = {}): SVGElementTagNameMap[K] => {
  const el = document.createElementNS(SVG_NS, tag);
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, String(v));
  return el;
};

const r1 = (x: number): number => Math.round(x * 10) / 10;

let instancias = 0;

export function criarMundo(container: HTMLElement, opcoes: MundoOpcoes): Mapa {
  const largura = opcoes.largura ?? LARGURA_PADRAO;
  const altura = opcoes.altura ?? ALTURA_PADRAO;
  const clicavel = !!opcoes.aoClicar;
  const el = criar("svg", {
    viewBox: `0 0 ${largura} ${altura}`,
    preserveAspectRatio: "xMidYMid meet",
    width: "100%",
    height: "100%",
    role: "img",
    class: `mapa mapa--mundo${clicavel ? " mapa--clicavel" : ""}`,
  });
  el.setAttribute("aria-label", "Mapa-múndi com as cidades do exterior onde há votação");
  const gTerra = criar("g", { class: "mundo__terra", "aria-hidden": "true" });
  const gBolhas = criar("g", { class: "mundo__bolhas" });
  const gRealce = criar("g", { class: "mundo__realce", "aria-hidden": "true" });
  const gRotulos = criar("g", { class: "mundo__rotulos", "aria-hidden": "true" });
  el.append(gTerra, gBolhas, gRealce, gRotulos);
  container.appendChild(el);

  const ajuste = ajusteMundo(largura, altura);
  // Recorte da terra na caixa do mapa: as cópias dos países que cruzam o antimeridiano ficam de fora.
  const [cx0, cy0] = ajuste.projetar(CAIXA_MUNDO.lon0, CAIXA_MUNDO.lat1);
  const [cx1, cy1] = ajuste.projetar(CAIXA_MUNDO.lon1, CAIXA_MUNDO.lat0);
  const idRecorte = `mundo-recorte-${++instancias}`;
  const defs = criar("defs");
  const recorte = criar("clipPath", { id: idRecorte });
  recorte.appendChild(criar("rect", { x: r1(cx0), y: r1(cy0), width: r1(cx1 - cx0), height: r1(cy1 - cy0) }));
  defs.appendChild(recorte);
  el.insertBefore(defs, gTerra);
  gTerra.setAttribute("clip-path", `url(#${idRecorte})`);
  const nos = new Map<string, NoCidade>();
  const unidades = new Map<string, UnidadeMapa>();
  let pronto = false;
  let destruido = false;
  let pendentes: UnidadeMapa[] | null = null;
  let destaque: string | null = null;
  let ordemAtual = "";
  let assinaturaRotulos = "";

  const medir = (txt: string): number => {
    const t = criar("text", { class: "mundo__nome", x: -9999, y: -9999 });
    t.textContent = txt;
    gRotulos.appendChild(t);
    let w = 0;
    try {
      w = t.getComputedTextLength();
    } catch {
      w = 0;
    }
    t.remove();
    return w > 0 ? w : larguraTexto(txt, FONTE_ROTULO);
  };

  const desenharRotulos = (forcar = false): void => {
    const topo = [...nos.values()]
      .map(no => ({ no, u: unidades.get(no.cidade.cd) }))
      .filter((x): x is { no: NoCidade; u: UnidadeMapa } => !!x.u && (x.u.te ?? 0) > 0)
      .sort((a, b) => (b.u.te ?? 0) - (a.u.te ?? 0) || a.no.cidade.cd.localeCompare(b.no.cidade.cd))
      .slice(0, ROTULOS_MAX)
      .map(x => ({ ...x, txt: opcoes.rotulo?.(x.u) ?? nomeProprio(x.u.nm) }));
    const assin = topo.map(x => `${x.no.cidade.cd}:${x.txt}:${r1(x.no.r)}`).join("|");
    if (assin === assinaturaRotulos && !forcar) return;
    assinaturaRotulos = assin;
    const h = FONTE_ROTULO + 10;
    const textos = new Map(topo.map(x => [x.no.cidade.cd, x.txt]));
    const pedidos: PedidoRotulo[] = topo.map(x => ({ cd: x.no.cidade.cd, x: x.no.x, y: x.no.y, r: x.no.r, w: medir(x.txt) + 16, h }));
    const frag = document.createDocumentFragment();
    for (const p of rotulosSemSobreposicao(pedidos, largura, altura)) {
      const g = criar("g", { class: "mundo__rotulo", "data-rotulo": p.cd });
      g.append(criar("rect", { x: r1(p.x), y: r1(p.y), width: r1(p.w), height: p.h, rx: 5, class: "mundo__caixa" }));
      const t = criar("text", { x: r1(p.x + 8), y: r1(p.y + p.h / 2), "dominant-baseline": "central", class: "mundo__nome" });
      t.textContent = textos.get(p.cd) ?? "";
      g.appendChild(t);
      frag.appendChild(g);
    }
    gRotulos.replaceChildren(frag);
  };
  void document.fonts?.ready.then(() => {
    if (!destruido && pronto) desenharRotulos(true);
  });

  const aplicarDestaque = (): void => {
    gRealce.replaceChildren();
    if (!destaque) return;
    const no = nos.get(destaque);
    if (!no) return;
    const r = no.r + 4;
    gRealce.append(
      criar("circle", { cx: no.x, cy: no.y, r, class: "mundo__realce-lime" }),
      criar("circle", { cx: no.x, cy: no.y, r, class: "mundo__realce-tinta" }),
    );
  };

  const pintar = (lista: UnidadeMapa[]): void => {
    unidades.clear();
    for (const u of lista) unidades.set(u.cd, u);
    const teMax = lista.reduce((m, u) => Math.max(m, u.te ?? 0), 0);
    for (const no of nos.values()) {
      const u = unidades.get(no.cidade.cd);
      no.r = raioBolha(u?.te, teMax);
      no.circulo.setAttribute("r", String(r1(no.r)));
      no.circulo.style.fill = u ? opcoes.cor(u) : NAO_INICIADO;
      const t = u ? (opcoes.titulo?.(u) ?? nomeProprio(u.nm)) : `${nomeProprio(no.cidade.nm)}: sem dados`;
      if (no.titulo.textContent !== t) no.titulo.textContent = t;
    }
    const ordem = ordemDeDesenho([...nos.values()].map(no => ({ cd: no.cidade.cd, r: no.r })));
    const assin = ordem.map(o => o.cd).join(",");
    if (assin !== ordemAtual) {
      ordemAtual = assin;
      const frag = document.createDocumentFragment();
      for (const o of ordem) {
        const no = nos.get(o.cd);
        if (no) frag.appendChild(no.circulo);
      }
      gBolhas.appendChild(frag);
    }
    desenharRotulos();
    aplicarDestaque();
  };

  const montar = (malha: ColecaoFeicoes, cidades: CidadeExterior[]): void => {
    const t0 = performance.now();
    let d = "";
    for (const f of malha.features) if (f.geometry) d += caminho(f.geometry as Geometria, ajuste.projetar);
    gTerra.appendChild(criar("path", { d, class: "mundo__pais" }));
    for (const c of cidades) {
      const [x0, y0] = ajuste.projetar(c.lon, c.lat);
      const x = r1(x0);
      const y = r1(y0);
      const circulo = criar("circle", { cx: x, cy: y, r: RAIO_MIN, class: "mundo__bolha", "data-cd": c.cd });
      circulo.style.fill = NAO_INICIADO;
      const titulo = criar("title");
      titulo.textContent = nomeProprio(c.nm);
      circulo.appendChild(titulo);
      nos.set(c.cd, { cidade: c, circulo, titulo, x, y, r: RAIO_MIN });
    }
    pronto = true;
    pintar(pendentes ?? []);
    pendentes = null;
    el.setAttribute("data-render-ms", (performance.now() - t0).toFixed(1));
    el.setAttribute("data-pronto", "1");
  };

  Promise.all([malhaMundo(), cidadesExterior()]).then(
    ([malha, cidades]) => {
      if (!destruido) montar(malha, cidades);
    },
    (erro: unknown) => {
      if (destruido) return;
      const t = criar("text", { x: largura / 2, y: altura / 2, "text-anchor": "middle", class: "mapa__aviso" });
      t.textContent = "mapa-múndi indisponível";
      el.appendChild(t);
      el.setAttribute("data-erro", erro instanceof Error ? erro.message : String(erro));
    },
  );

  const aoClique = (ev: MouseEvent): void => {
    const cd = (ev.target as Element | null)?.closest(".mundo__bolha")?.getAttribute("data-cd");
    const u = cd ? unidades.get(cd) : undefined;
    if (u) opcoes.aoClicar?.(u);
    else opcoes.aoClicarFundo?.();
  };
  if (clicavel || opcoes.aoClicarFundo) el.addEventListener("click", aoClique);

  return {
    el,
    update(lista) {
      if (!pronto) {
        pendentes = lista;
        return;
      }
      pintar(lista);
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
