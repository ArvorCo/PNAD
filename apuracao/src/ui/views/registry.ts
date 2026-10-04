// Registro de telas. Cada tela é criada de novo a cada montagem (o crossfade
// mantém duas instâncias vivas por 350 ms) e escreve só dentro do seu <section>.
//
// A casca monta em `el`:
//   <section class="tela">
//     <div class="palco"><header class="palco-cab"><h1 class="palco-titulo"></h1><div class="palco-chips"></div></header>
//       <div class="palco-corpo"></div></div>
//     <aside class="painel"></aside>
//   </section>
// O título (h1) é escrito pela casca a partir de `titulo(state)`; a tela preenche
// `.palco-corpo`, `.palco-chips` e `.painel` (use `partes(el)`). Uma tela que queira
// ocupar a largura toda adiciona a classe `tela--cheia` ao `el`.

import type { Diff, Need, State } from "../state/types.ts";

export interface View {
  readonly id: string;
  /** Título do palco e da faixa superior (frase em caixa normal, sem travessão). */
  titulo(state: State): string;
  /** Dwell padrão em segundos (a playlist pode sobrescrever). */
  readonly dwell: number;
  /** Dados de que a tela precisa no estado atual; a casca busca e reassina pelo SSE. */
  needs(state: State): Need[];
  mount(el: HTMLElement): void;
  /** Chamado após mount e a cada mudança de estado. `diff` traz as folhas numéricas alteradas. */
  update(state: State, diff: Diff): void;
  unmount(): void;
  /** Teclas próprias (↑/↓ entre zonas). Devolve true se tratou. */
  keys?(tecla: string, state: State): boolean;
}

export type FabricaView = () => View;

const telas = new Map<string, FabricaView>();
const titulos = new Map<string, string>();

export function register(id: string, fabrica: FabricaView, tituloCurto?: string): void {
  telas.set(id, fabrica);
  if (tituloCurto) titulos.set(id, tituloCurto);
}

/** Nova instância da tela, ou undefined se o id não existe. */
export function get(id: string): View | undefined {
  const f = telas.get(id);
  return f ? f() : undefined;
}

export const has = (id: string): boolean => telas.has(id);

let pedidoDeDados: (() => void) | null = null;

/** A casca liga aqui a busca das necessidades da tela atual. */
export function ligarPedidoDeDados(f: (() => void) | null): void {
  pedidoDeDados = f;
}

/** Tela que trocou o próprio recorte sem mudar o hash pede as necessidades de novo. */
export function pedirDados(): void {
  pedidoDeDados?.();
}

/** Telas registradas com rótulo curto (para o diretor e o HUD). */
export function listar(): { id: string; titulo: string }[] {
  return [...telas.keys()].map(id => ({ id, titulo: titulos.get(id) ?? id }));
}

export interface Partes {
  titulo: HTMLElement;
  chips: HTMLElement;
  corpo: HTMLElement;
  painel: HTMLElement;
}

function exigir(el: HTMLElement, seletor: string): HTMLElement {
  const x = el.querySelector<HTMLElement>(seletor);
  if (!x) throw new Error(`tela sem ${seletor}`);
  return x;
}

export function partes(el: HTMLElement): Partes {
  return {
    titulo: exigir(el, ".palco-titulo"),
    chips: exigir(el, ".palco-chips"),
    corpo: exigir(el, ".palco-corpo"),
    painel: exigir(el, ".painel"),
  };
}

/** Esqueleto que a casca coloca em cada tela antes do mount. */
export function esqueleto(): HTMLElement {
  const s = document.createElement("section");
  s.className = "tela";
  s.innerHTML =
    '<div class="palco"><header class="palco-cab"><h1 class="palco-titulo"></h1><div class="palco-chips"></div></header>' +
    '<div class="palco-corpo"></div></div><aside class="painel"></aside>';
  return s;
}

/** Tela provisória para ids ainda não implementados: a playlist roda de ponta a ponta. */
export function placeholder(id: string, titulo: string | ((s: State) => string), dwell = 20): FabricaView {
  const tituloDe = (s: State): string =>
    typeof titulo === "function" ? titulo(s) : s.ui.uf && id.endsWith("-uf") ? `${titulo}, ${nomeUf(s, s.ui.uf)}` : titulo;
  return () => {
    let raiz: HTMLElement | null = null;
    return {
      id,
      dwell,
      titulo: tituloDe,
      needs: () => [],
      mount(el) {
        raiz = el;
        const p = partes(el);
        p.corpo.innerHTML = `<div class="vazio"><p class="vazio-titulo"></p><p class="vazio-nota">tela em construção</p></div>`;
        p.painel.innerHTML = `<div class="vazio vazio--painel"><p class="vazio-nota">o painel desta tela entra no próximo pacote</p></div>`;
      },
      update(s) {
        const t = raiz?.querySelector(".vazio-titulo");
        if (t) t.textContent = tituloDe(s);
      },
      unmount() {
        raiz = null;
      },
    };
  };
}

export function nomeUf(s: State, uf: string): string {
  return s.config?.ufs.find(u => u.uf.toUpperCase() === uf.toUpperCase())?.nome ?? uf;
}
