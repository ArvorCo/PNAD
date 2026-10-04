// Contrato do componente de mapa (F2 substitui a implementação, mantendo as assinaturas).
// Um mapa desenha unidades (UFs, municípios ou tiles de zona) e pinta cada uma pela
// cor devolvida por `cor(unidade)`, já com a banda de parcialidade aplicada.

import type { NivelMapa, UnidadeMapa } from "../state/types.ts";

export interface MapaOpcoes {
  nivel: NivelMapa;
  /** "br" para UFs, "sp" para municípios de SP, "sp71072" para zonas de São Paulo. */
  pai: string;
  /** Cor de preenchimento final (F2 aplica `corPorBanda` por fora, se quiser). */
  cor: (u: UnidadeMapa) => string;
  /** Rótulo opcional sobre a unidade (sigla, nome curto ou porcentagem). */
  rotulo?: (u: UnidadeMapa) => string | null;
  /** Clique numa unidade (drill). */
  aoClicar?: (u: UnidadeMapa) => void;
  /** Texto do `<title>` para acessibilidade. */
  titulo?: (u: UnidadeMapa) => string;
}

export interface Mapa {
  readonly el: SVGSVGElement;
  /** Reaplica cores, rótulos e títulos sem recriar os nós (transição de `fill` por CSS). */
  update(unidades: UnidadeMapa[]): void;
  /** Contorno lime na unidade; `null` limpa. */
  destacar(cd: string | null): void;
  destroy(): void;
}

/**
 * Cria o mapa dentro de `container`, ocupando toda a área disponível.
 * Implementação de F2: UF e município usam a malha IBGE (`data/geo.ts`),
 * zona usa treemap squarified por eleitorado (`zonas.ts`).
 * Esta versão provisória só desenha um retângulo com o nome do nível.
 */
export function criarMapa(container: HTMLElement, opcoes: MapaOpcoes): Mapa {
  const ns = "http://www.w3.org/2000/svg";
  const el = document.createElementNS(ns, "svg");
  el.setAttribute("viewBox", "0 0 1152 800");
  el.setAttribute("class", "mapa mapa--provisorio");
  const texto = document.createElementNS(ns, "text");
  texto.setAttribute("x", "576");
  texto.setAttribute("y", "400");
  texto.setAttribute("text-anchor", "middle");
  texto.textContent = `mapa ${opcoes.nivel} de ${opcoes.pai} em construção`;
  el.appendChild(texto);
  container.appendChild(el);
  return {
    el,
    update(unidades) {
      texto.textContent = `mapa ${opcoes.nivel} de ${opcoes.pai}: ${unidades.length} unidades`;
    },
    destacar() {},
    destroy() {
      el.remove();
    },
  };
}
