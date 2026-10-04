// Casca do telão: faixa superior, miolo com crossfade entre telas, faixa inferior
// (ticker + HUD), barra de dwell e paleta. Nunca tela branca: a tela atual só sai
// depois que a próxima montou.

import { criarFaixa } from "./components/faixa.ts";
import { criarHud } from "./components/hud.ts";
import { criarTicker } from "./components/ticker.ts";
import { criarPaleta } from "./components/paleta.ts";
import type { Paleta } from "./components/paleta.ts";
import type { Achado, Indice } from "./control/search.ts";
import type { Diff, State } from "./state/types.ts";
import type { View } from "./views/registry.ts";
import { esqueleto, get, partes, placeholder } from "./views/registry.ts";

const DURACAO_TELA_MS = 350;

export interface Shell {
  /** Monta a tela `id` (instância nova) e faz o crossfade. */
  trocar(id: string, s: State): View;
  atual(): View | null;
  atualizar(s: State, diff: Diff, totalPlaylist: number): void;
  paleta: Paleta;
}

export function montarShell(raiz: HTMLElement, indice: Indice, escolher: (a: Achado) => void, aoFecharPaleta: () => void): Shell {
  const faixa = criarFaixa();
  const miolo = document.createElement("main");
  miolo.className = "miolo";
  const base = document.createElement("footer");
  base.className = "base";
  const ticker = criarTicker();
  const hud = criarHud();
  base.append(ticker.el, hud.el);
  const dwell = document.createElement("div");
  dwell.className = "dwell";
  dwell.innerHTML = "<i></i>";
  const barra = dwell.firstElementChild as HTMLElement;
  const paleta = criarPaleta(indice, escolher, aoFecharPaleta);
  raiz.replaceChildren(faixa.el, miolo, base, dwell, paleta.el);

  let atual: { view: View; el: HTMLElement } | null = null;
  let chaveDwell = "";

  const desenharDwell = (s: State): void => {
    const visivel = s.ui.auto && s.ui.v !== "espera";
    dwell.hidden = !visivel;
    const chave = `${s.ui.dwellInicio}|${s.ui.dwellMs}|${s.ui.pausado}|${visivel}`;
    if (!visivel || chave === chaveDwell) return;
    chaveDwell = chave;
    const passado = performance.now() - s.ui.dwellInicio;
    const f = Math.min(1, Math.max(0, passado / Math.max(1, s.ui.dwellMs)));
    barra.style.transition = "none";
    barra.style.width = `${f * 100}%`;
    if (s.ui.pausado) return;
    void barra.offsetWidth; // aplica a largura antes da transição
    barra.style.transition = `width ${Math.max(0, s.ui.dwellMs - passado)}ms linear`;
    barra.style.width = "100%";
  };

  return {
    paleta,
    atual: () => atual?.view ?? null,
    trocar(id, s) {
      const view = get(id) ?? placeholder(id, id)();
      const el = esqueleto();
      el.dataset.tela = id;
      miolo.append(el);
      view.mount(el);
      partes(el).titulo.textContent = view.titulo(s);
      view.update(s, []);
      const anterior = atual;
      atual = { view, el };
      requestAnimationFrame(() => el.classList.add("ativa"));
      if (anterior) {
        anterior.el.classList.remove("ativa");
        setTimeout(() => {
          anterior.view.unmount();
          anterior.el.remove();
        }, DURACAO_TELA_MS);
      }
      return view;
    },
    atualizar(s, diff, totalPlaylist) {
      const titulo = atual ? atual.view.titulo(s) : "";
      if (atual) {
        const t = partes(atual.el).titulo;
        if (t.textContent !== titulo) t.textContent = titulo;
        atual.view.update(s, diff);
      }
      faixa.atualizar(s, titulo);
      ticker.atualizar(s);
      hud.atualizar(s, totalPlaylist);
      desenharDwell(s);
    },
  };
}
