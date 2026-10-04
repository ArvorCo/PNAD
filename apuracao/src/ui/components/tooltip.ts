// Ficha de leitura (estilo da casa, docs/assets/reponderacao_tip.css): cartão escuro
// posicionado em absoluto dentro de #telao, nunca fora da caixa 1920×1080. Fica à direita
// da âncora e vira para a esquerda perto da borda direita. Todo texto entra por
// textContent. A conta de posição é pura e testada em tests/ui/acumulado.test.ts.

export interface Caixa {
  w: number;
  h: number;
}

export interface Posicao {
  x: number;
  y: number;
  lado: "dir" | "esq";
}

/**
 * Posição do canto superior esquerdo do cartão `card` ancorado em (ax, ay), dentro de
 * `caixa`. À direita da âncora com `folga`; vira à esquerda se passar da borda menos
 * `margem`. Na vertical, centrado na âncora e preso entre as margens.
 */
export function posicionarFicha(ax: number, ay: number, card: Caixa, caixa: Caixa, folga = 28, margem = 16): Posicao {
  let lado: Posicao["lado"] = "dir";
  let x = ax + folga;
  if (x + card.w > caixa.w - margem) {
    lado = "esq";
    x = ax - folga - card.w;
  }
  x = Math.max(margem, Math.min(x, caixa.w - margem - card.w));
  const y = Math.max(margem, Math.min(ay - card.h / 2, caixa.h - margem - card.h));
  return { x, y, lado };
}

export interface LinhaFicha {
  cor?: string;
  rotulo: string;
  valor: string;
  extra?: string;
}

export interface ConteudoFicha {
  titulo: string;
  sub?: string;
  /** Pares rótulo e valor antes da tabela (seções, válidos). */
  fatos?: readonly { rotulo: string; valor: string }[];
  linhas?: readonly LinhaFicha[];
  notas?: readonly string[];
}

export interface Ficha {
  readonly el: HTMLElement;
  /** Mostra o conteúdo ancorado no ponto (clientX, clientY) da janela. */
  mostrar(c: ConteudoFicha, clientX: number, clientY: number): void;
  esconder(): void;
  destroy(): void;
}

function el<K extends keyof HTMLElementTagNameMap>(tag: K, classe: string, texto?: string): HTMLElementTagNameMap[K] {
  const e = document.createElement(tag);
  e.className = classe;
  if (texto !== undefined) e.textContent = texto;
  return e;
}

/** Cria a ficha dentro de #telao (ou de `raiz`, quando não há #telao). */
export function criarFicha(raiz: HTMLElement): Ficha {
  const telao = document.getElementById("telao") ?? raiz;
  const card = el("div", "ficha");
  card.setAttribute("role", "tooltip");
  card.setAttribute("aria-hidden", "true");
  telao.append(card);

  const preencher = (c: ConteudoFicha): void => {
    const cab = el("p", "ficha-cab");
    cab.append(el("b", "", c.titulo));
    if (c.sub) cab.append(el("span", "", c.sub));
    const filhos: HTMLElement[] = [cab];
    if (c.fatos && c.fatos.length > 0) {
      const dl = el("dl", "ficha-fatos");
      for (const f of c.fatos) dl.append(el("dt", "", f.rotulo), el("dd", "", f.valor));
      filhos.push(dl);
    }
    if (c.linhas && c.linhas.length > 0) {
      const tab = el("table", "ficha-tab");
      const corpo = el("tbody", "");
      for (const l of c.linhas) {
        const tr = el("tr", "");
        const th = el("th", "");
        const sw = el("i", "ficha-cor");
        if (l.cor) sw.style.background = l.cor;
        th.append(sw, document.createTextNode(l.rotulo));
        tr.append(th, el("td", "", l.valor), el("td", "ficha-extra", l.extra ?? ""));
        corpo.append(tr);
      }
      tab.append(corpo);
      filhos.push(tab);
    }
    for (const n of c.notas ?? []) filhos.push(el("p", "ficha-nota", n));
    card.replaceChildren(...filhos);
  };

  return {
    el: card,
    mostrar(c, clientX, clientY) {
      preencher(c);
      const r = telao.getBoundingClientRect();
      // #telao é medido em rem; sem transformação, 1 px de CSS = 1 px na tela.
      const p = posicionarFicha(clientX - r.left, clientY - r.top, { w: card.offsetWidth, h: card.offsetHeight }, { w: r.width, h: r.height });
      card.style.transform = `translate(${Math.round(p.x)}px, ${Math.round(p.y)}px)`;
      card.dataset.lado = p.lado;
      card.classList.add("on");
      card.setAttribute("aria-hidden", "false");
    },
    esconder() {
      card.classList.remove("on");
      card.setAttribute("aria-hidden", "true");
    },
    destroy() {
      card.remove();
    },
  };
}
