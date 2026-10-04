// Paleta de busca (tecla /): município sem acento, UF ou candidato; até 8 achados.

import type { Achado, Indice } from "../control/search.ts";

export interface Paleta {
  el: HTMLElement;
  abrir(): void;
  fechar(): void;
  aberta(): boolean;
}

const ROTULO_TIPO: Readonly<Record<Achado["tipo"], string>> = { uf: "estado", mun: "município", cand: "candidatura" };

export function criarPaleta(indice: Indice, escolher: (a: Achado) => void, aoFechar: () => void): Paleta {
  const el = document.createElement("div");
  el.className = "paleta";
  el.hidden = true;
  el.innerHTML = `<div class="paleta-caixa" role="dialog" aria-label="busca">
      <input class="paleta-campo" type="text" autocomplete="off" spellcheck="false" placeholder="município, estado ou candidatura" />
      <ul class="paleta-lista" role="listbox"></ul>
    </div>`;
  const campo = el.querySelector("input") as HTMLInputElement;
  const lista = el.querySelector("ul") as HTMLUListElement;
  let achados: Achado[] = [];
  let sel = 0;

  const desenhar = (): void => {
    if (achados.length === 0) {
      lista.innerHTML = campo.value.trim() ? `<li class="paleta-vazia">nada encontrado para essa busca</li>` : "";
      return;
    }
    lista.replaceChildren(
      ...achados.map((a, i) => {
        const li = document.createElement("li");
        li.setAttribute("role", "option");
        li.setAttribute("aria-selected", String(i === sel));
        const tipo = document.createElement("span");
        tipo.className = "tipo";
        tipo.textContent = ROTULO_TIPO[a.tipo];
        const nome = document.createElement("span");
        nome.className = "corte";
        nome.textContent = a.rotulo;
        const det = document.createElement("span");
        det.className = "detalhe";
        det.textContent = a.detalhe;
        li.append(tipo, nome, det);
        li.addEventListener("mousedown", ev => {
          ev.preventDefault();
          confirmar(i);
        });
        return li;
      }),
    );
  };

  const confirmar = (i: number): void => {
    const a = achados[i];
    if (!a) return;
    fechar();
    escolher(a);
  };

  const fechar = (): void => {
    if (el.hidden) return;
    el.hidden = true;
    campo.blur();
    aoFechar();
  };

  campo.addEventListener("input", () => {
    achados = indice.buscar(campo.value, 8);
    sel = 0;
    desenhar();
  });
  campo.addEventListener("keydown", ev => {
    if (ev.key === "ArrowDown") sel = Math.min(achados.length - 1, sel + 1);
    else if (ev.key === "ArrowUp") sel = Math.max(0, sel - 1);
    else if (ev.key === "Enter") confirmar(sel);
    else if (ev.key === "Escape") fechar();
    else return;
    ev.preventDefault();
    ev.stopPropagation();
    desenhar();
  });
  el.addEventListener("mousedown", ev => {
    if (ev.target === el) fechar();
  });

  return {
    el,
    abrir() {
      el.hidden = false;
      campo.value = "";
      achados = [];
      sel = 0;
      desenhar();
      requestAnimationFrame(() => campo.focus());
    },
    fechar,
    aberta: () => !el.hidden,
  };
}
