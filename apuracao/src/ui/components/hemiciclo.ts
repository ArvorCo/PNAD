// Hemiciclo de 81 assentos do Senado, porta de scripts/senado_2026/pagina/hemiciclo.py:
// quatro arcos (raios 140, 185, 230 e 275 na referência 640 × 330), assentos distribuídos
// pelo comprimento de cada arco e ordenados da esquerda para a direita pelo ângulo.
// Aqui a referência é ampliada 1,8× para caber em 1152 × 594 no palco.
//
// Assento com contorno = mandato que continua até 2031 (eleitos em 2022). Assento cheio =
// vaga de 2026: líder na apuração (cor misturada ao papel pela banda de pst) ou eleito
// pelo TSE (cor cheia). Sem dado, cinza de não iniciado.

import { corCampo, corPorBanda, NAO_INICIADO } from "../data/cores.ts";
import type { Campo, Campos } from "../state/types.ts";

const NS = "http://www.w3.org/2000/svg";

export const ASSENTOS = 81;
export const ESCALA = 1.8;
const W0 = 640;
const H0 = 330;
const RAIOS0 = [140, 185, 230, 275] as const;
const RAIO_ASSENTO0 = 12.5;

export const LARGURA = W0 * ESCALA;
export const ALTURA = H0 * ESCALA;
export const RAIO_ASSENTO = RAIO_ASSENTO0 * ESCALA;

/** Ordem dos campos da esquerda para a direita. */
export const ORDEM_CAMPOS: readonly Campo[] = ["esquerda", "centro-esquerda", "centro", "centro-direita", "direita", "indefinido"];

/** Quantos assentos em cada arco, proporcional ao raio (sobra no arco externo). */
export function assentosPorArco(total = ASSENTOS, raios: readonly number[] = RAIOS0): number[] {
  const soma = raios.reduce((s, r) => s + r, 0);
  const qtd = raios.map(r => Math.round((total * r) / soma));
  const ultimo = qtd.length - 1;
  qtd[ultimo] = (qtd[ultimo] ?? 0) + total - qtd.reduce((s, x) => s + x, 0);
  return qtd;
}

/** Coordenadas dos assentos, da esquerda para a direita, na escala dada. */
export function posicoesHemiciclo(escala = ESCALA, total = ASSENTOS): { x: number; y: number }[] {
  const w = W0 * escala;
  const h = H0 * escala;
  const cx = w / 2;
  const cy = h - 14 * escala;
  const raios = RAIOS0.map(r => r * escala);
  const qtd = assentosPorArco(total, raios);
  const seats: { ang: number; r: number; x: number; y: number }[] = [];
  raios.forEach((r, i) => {
    const n = qtd[i] ?? 0;
    for (let k = 0; k < n; k++) {
      const ang = Math.PI * (1 - (n > 1 ? k / (n - 1) : 0.5));
      seats.push({ ang: -ang, r, x: cx + r * Math.cos(ang), y: cy - r * Math.sin(ang) });
    }
  });
  seats.sort((a, b) => a.ang - b.ang || a.r - b.r);
  return seats.map(s => ({ x: s.x, y: s.y }));
}

export type TipoAssento = "continua" | "eleito" | "lider" | "aguardando";

export interface Assento {
  tipo: TipoAssento;
  campo: Campo;
  uf: string;
  /** Seções totalizadas da UF (0 a 100), para a banda de cor do líder. */
  pst: number;
  nome: string;
}

const PESO_TIPO: Readonly<Record<TipoAssento, number>> = { continua: 0, eleito: 1, lider: 2, aguardando: 3 };

/**
 * Ordem de desenho: campo da esquerda para a direita; dentro do campo, primeiro os que
 * continuam, depois eleitos, depois líderes do mais apurado ao menos apurado. Vagas ainda
 * sem líder ficam no fim, depois de "indefinido", em cinza.
 */
export function ordenarAssentos(lista: readonly Assento[]): Assento[] {
  const ordem = (a: Assento): number => (a.tipo === "aguardando" ? ORDEM_CAMPOS.length : ORDEM_CAMPOS.indexOf(a.campo));
  return [...lista].sort(
    (a, b) => ordem(a) - ordem(b) || PESO_TIPO[a.tipo] - PESO_TIPO[b.tipo] || b.pst - a.pst || a.uf.localeCompare(b.uf),
  );
}

export interface FatiaComposicao {
  campo: Campo | "aguardando";
  n: number;
  continuam: number;
}

/** Composição por campo (continuam + vagas de 2026 com líder ou eleito) e vagas aguardando. */
export function composicao(lista: readonly Assento[]): FatiaComposicao[] {
  const saida: FatiaComposicao[] = ORDEM_CAMPOS.map(campo => ({ campo, n: 0, continuam: 0 }));
  const aguardando: FatiaComposicao = { campo: "aguardando", n: 0, continuam: 0 };
  for (const a of lista) {
    if (a.tipo === "aguardando") {
      aguardando.n += 1;
      continue;
    }
    const f = saida[ORDEM_CAMPOS.indexOf(a.campo)];
    if (!f) continue;
    f.n += 1;
    if (a.tipo === "continua") f.continuam += 1;
  }
  return [...saida.filter(f => f.n > 0), ...(aguardando.n > 0 ? [aguardando] : [])];
}

export interface Hemiciclo {
  readonly el: SVGSVGElement;
  update(assentos: readonly Assento[], campos: Campos): void;
  destroy(): void;
}

export function criarHemiciclo(container: HTMLElement, rotulo: string): Hemiciclo {
  const el = document.createElementNS(NS, "svg");
  el.setAttribute("viewBox", `0 0 ${LARGURA} ${ALTURA}`);
  el.setAttribute("class", "hemiciclo");
  el.setAttribute("role", "img");
  el.setAttribute("aria-label", rotulo);
  const pos = posicoesHemiciclo();
  const circulos = pos.map(p => {
    const c = document.createElementNS(NS, "circle");
    c.setAttribute("cx", p.x.toFixed(1));
    c.setAttribute("cy", p.y.toFixed(1));
    c.setAttribute("r", String(RAIO_ASSENTO - 2));
    c.setAttribute("class", "hc-assento");
    const t = document.createElementNS(NS, "title");
    c.append(t);
    el.append(c);
    return { c, t };
  });
  container.append(el);
  return {
    el,
    update(assentos, campos) {
      const ordem = ordenarAssentos(assentos);
      circulos.forEach(({ c, t }, i) => {
        const a = ordem[i];
        if (!a || a.tipo === "aguardando") {
          c.style.fill = NAO_INICIADO;
          c.style.stroke = NAO_INICIADO;
          c.dataset.tipo = "aguardando";
          t.textContent = a ? `vaga de ${a.uf} aguardando seções` : "";
          return;
        }
        const cor = corCampo(a.campo, campos);
        c.dataset.tipo = a.tipo;
        if (a.tipo === "continua") {
          c.style.fill = "#fffdf8";
          c.style.stroke = cor;
          t.textContent = `${a.nome}, ${a.uf}, mandato até 2031`;
        } else {
          const cheio = a.tipo === "eleito" ? cor : corPorBanda(cor, Math.min(a.pst, 99.99));
          c.style.fill = cheio;
          c.style.stroke = cheio;
          t.textContent = `${a.nome}, ${a.uf}, ${a.tipo === "eleito" ? "eleito pelo TSE" : "líder na apuração"}`;
        }
      });
    },
    destroy() {
      el.remove();
    },
  };
}
