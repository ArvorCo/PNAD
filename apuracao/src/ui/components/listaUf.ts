// Lista das 27 UFs em 3 colunas × 9 linhas (cada célula ≈ 232 × 98 no painel de 696).
// Modo "gov": barra de campo de 6 px, sigla, nome do líder, percentual, mini barra de pst
// e marca lime "1º turno" só quando o TSE marcar eleito. Modo "sen": duas vagas por UF,
// cada uma com ponto de campo de 14 px e nome; pst em Plex Mono à direita da sigla.
// Nós estáveis por UF; a ordem é a da lista recebida (eleitorado, por padrão).

import { corCampo } from "../data/cores.ts";
import { decimal, nomeProprio, pct } from "../data/format.ts";
import type { Campo, Campos } from "../state/types.ts";

export interface ItemUf {
  nome: string;
  campo: Campo;
  /** % dos válidos (0 a 100) ou null sem voto. */
  pct: number | null;
  /** Marca do TSE ("1º turno", "eleito"); nunca projetada. */
  marca?: string | null;
}

export interface LinhaUf {
  uf: string;
  nomeUf: string;
  pst: number;
  itens: ItemUf[];
}

export type ModoLista = "gov" | "sen";

export interface ListaUf {
  readonly el: HTMLElement;
  update(linhas: readonly LinhaUf[], campos: Campos): void;
  destroy(): void;
}

interface NosLinha {
  raiz: HTMLElement;
  barra: HTMLElement | null;
  pctOuPst: HTMLElement;
  pst: HTMLElement;
  itens: { ponto: HTMLElement | null; nome: HTMLElement; marca: HTMLElement }[];
}

function span(classe: string, texto = ""): HTMLSpanElement {
  const s = document.createElement("span");
  s.className = classe;
  s.textContent = texto;
  return s;
}

function criarLinha(uf: string, modo: ModoLista): NosLinha {
  const raiz = document.createElement("div");
  raiz.className = `lu-linha lu-linha--${modo}`;
  raiz.dataset.uf = uf;
  const topo = document.createElement("div");
  topo.className = "lu-topo";
  const sigla = span("lu-sigla", uf);
  const pctOuPst = span(modo === "gov" ? "lu-pct" : "lu-pstn");
  topo.append(sigla, pctOuPst);
  let barra: HTMLElement | null = null;
  if (modo === "gov") {
    barra = document.createElement("i");
    barra.className = "lu-campo";
    raiz.append(barra);
  }
  raiz.append(topo);
  const itens: NosLinha["itens"] = [];
  const vagas = modo === "gov" ? 1 : 2;
  for (let i = 0; i < vagas; i++) {
    const linha = document.createElement("div");
    linha.className = "lu-item";
    let ponto: HTMLElement | null = null;
    if (modo === "sen") {
      ponto = document.createElement("i");
      ponto.className = "lu-ponto";
      linha.append(ponto);
    }
    const nome = span("lu-nome");
    const marca = span("lu-marca");
    marca.hidden = true;
    linha.append(nome, marca);
    raiz.append(linha);
    itens.push({ ponto, nome, marca });
  }
  const pstBarra = document.createElement("div");
  pstBarra.className = "lu-pst";
  const pst = document.createElement("i");
  pstBarra.append(pst);
  raiz.append(pstBarra);
  return { raiz, barra, pctOuPst, pst, itens };
}

export function criarListaUf(container: HTMLElement, modo: ModoLista): ListaUf {
  const el = document.createElement("div");
  el.className = `lista-uf lista-uf--${modo}`;
  container.append(el);
  const nos = new Map<string, NosLinha>();
  let ordemAtual = "";

  return {
    el,
    update(linhas, campos) {
      const ordem = linhas.map(l => l.uf).join(",");
      for (const l of linhas) {
        let n = nos.get(l.uf);
        if (!n) {
          n = criarLinha(l.uf, modo);
          nos.set(l.uf, n);
        }
        n.raiz.title = l.nomeUf;
        n.pst.style.width = `${Math.max(0, Math.min(100, l.pst))}%`;
        const primeiro = l.itens[0];
        if (modo === "gov") {
          n.pctOuPst.textContent = primeiro && primeiro.pct !== null ? pct(primeiro.pct) : "";
          if (n.barra) n.barra.style.background = primeiro && primeiro.pct !== null ? corCampo(primeiro.campo, campos) : "var(--nao-iniciado)";
        } else {
          n.pctOuPst.textContent = l.pst > 0 ? `${decimal(l.pst, 0)}%` : "0%";
        }
        n.itens.forEach((it, i) => {
          const dado = l.itens[i];
          const temVoto = dado !== undefined && dado.pct !== null;
          it.nome.textContent = temVoto ? nomeProprio(dado.nome) : "aguardando seções";
          it.nome.classList.toggle("lu-nome--vazio", !temVoto);
          if (it.ponto) it.ponto.style.background = temVoto ? corCampo(dado.campo, campos) : "var(--nao-iniciado)";
          const marca = temVoto ? (dado.marca ?? null) : null;
          it.marca.hidden = marca === null;
          it.marca.textContent = marca ?? "";
        });
      }
      for (const [uf, n] of nos) {
        if (!linhas.some(l => l.uf === uf)) {
          n.raiz.remove();
          nos.delete(uf);
        }
      }
      if (ordem !== ordemAtual) {
        ordemAtual = ordem;
        el.replaceChildren(...linhas.map(l => nos.get(l.uf)?.raiz).filter((x): x is HTMLElement => x !== undefined));
      }
    },
    destroy() {
      el.remove();
      nos.clear();
    },
  };
}
