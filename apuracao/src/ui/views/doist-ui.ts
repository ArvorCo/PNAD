// Peças de DOM compartilhadas pelas telas do 2º turno: construtor de elementos, fábrica de
// tela, aviso de fonte indisponível e os dois candidatos do duelo com nome, cor e foto.

import { chipAndamento } from "../components/chip.ts";
import { foto } from "../components/foto.ts";
import { coresPresidente } from "../components/ranking.ts";
import { dadosDe, textoSemFonte } from "../data/doist.ts";
import type { Dados2T, Rota2T } from "../data/doist.ts";
import { nomeProprio } from "../data/format.ts";
import type { Candidato, Need, State } from "../state/types.ts";
import { chaveResultado } from "../state/types.ts";
import { definirChips, eleicaoDe } from "./executivo.ts";
import { parDoDuelo } from "./presidente.ts";
import type { Partes, View } from "./registry.ts";
import { partes } from "./registry.ts";
import { tituloDa2T } from "./meta-2t.ts";

/** Cria um elemento com classe e texto. */
export function h<K extends keyof HTMLElementTagNameMap>(tag: K, classe = "", texto = ""): HTMLElementTagNameMap[K] {
  const e = document.createElement(tag);
  if (classe) e.className = classe;
  if (texto) e.textContent = texto;
  return e;
}

/** Troca o texto só se mudou (evita reflow e mantém o foco da leitura). */
export function texto(e: HTMLElement | null, valor: string): void {
  if (e && e.textContent !== valor) e.textContent = valor;
}

export function esvaziar(e: HTMLElement): void {
  e.replaceChildren();
}

/** Bloco de aviso quando a fonte do 2º turno não responde: sempre diz o que falta, nunca fica em branco. */
export function avisoSemFonte(rotulo: string, mensagem: string): HTMLElement {
  const d = h("div", "d2-semfonte");
  d.append(h("p", "d2-semfonte-titulo", rotulo), h("p", "d2-semfonte-msg", mensagem));
  return d;
}

/**
 * Monta no corpo do palco o par aviso + conteúdo: o aviso ("fonte indisponível") fica escondido
 * enquanto há dados; o conteúdo, com a classe da tela, fica escondido quando não há.
 */
export function montarComAviso(corpo: HTMLElement, classe: string, html: string): HTMLElement {
  corpo.innerHTML = `<div class="d2-aviso" hidden></div><div class="d2-conteudo ${classe}">${html}</div>`;
  return corpo.querySelector<HTMLElement>(".d2-conteudo") as HTMLElement;
}

/**
 * Alterna aviso e conteúdo conforme a rota tenha dados. Devolve true quando há dados e a tela
 * pode desenhar; senão escreve o motivo ("pendente", "erro: ...") no aviso e devolve false.
 */
export function atualizarAviso(corpo: HTMLElement, s: State, rota: Rota2T, rotulo: string): boolean {
  const aviso = corpo.querySelector<HTMLElement>(".d2-aviso");
  const conteudo = corpo.querySelector<HTMLElement>(".d2-conteudo");
  const tem = !!dadosDe(s.doist, rota);
  if (aviso) {
    aviso.hidden = tem;
    if (!tem) aviso.replaceChildren(avisoSemFonte(rotulo, textoSemFonte(s.doist, rota)));
  }
  if (conteudo) conteudo.hidden = !tem;
  return tem;
}

export interface InfoCand {
  sqcand: string;
  n: string;
  nome: string;
  sg: string;
  cor: string;
}

export interface Duelo {
  a: InfoCand;
  b: InfoCand;
  /** Candidaturas completas do resultado nacional (para foto e situação). */
  cand: readonly Candidato[];
}

/**
 * Os dois candidatos do duelo nacional, na ordem do número de urna (13 à esquerda, 22 à direita,
 * como na tela do presidente), com nome e cor. Null enquanto o resultado nacional não chegou.
 */
export function dueloDe(s: State): Duelo | null {
  const r = s.resultados[chaveResultado(eleicaoDe(s, 1), 1, "br")];
  if (!r) return null;
  const par = parDoDuelo(r.cand);
  if (!par) return null;
  const cores = coresPresidente(r.cand, s.cores);
  const info = (c: Candidato): InfoCand => ({ sqcand: c.sqcand, n: c.n, nome: nomeProprio(c.nmu), sg: c.sg, cor: cores.get(c.sqcand) ?? "#5f6773" });
  return { a: info(par[0]), b: info(par[1]), cand: r.cand };
}

export function fotoDe(c: InfoCand, tamanho: number): HTMLElement {
  return foto({ sqcand: c.sqcand, nome: c.nome, tamanho, cor: c.cor });
}

export interface DefTela2T {
  id: string;
  dwell: number;
  /** Ocupa a largura toda (sem o painel lateral). */
  cheia?: boolean;
  needs(s: State): Need[];
  /** Monta o esqueleto dentro das partes; roda uma vez. */
  montar(p: Partes, raiz: HTMLElement): void;
  /**
   * Referências de que o desenho depende (resposta da rota, resultado nacional, cores...). A tela
   * só redesenha quando alguma delas troca de identidade: o store muda a cada batimento da rede e
   * redesenhar a cada um apagaria o texto que a câmera está lendo.
   */
  entradas(s: State): readonly unknown[];
  /** Redesenha com o estado. */
  atualizar(s: State, p: Partes, raiz: HTMLElement): void;
  /** Chips do título; padrão: andamento nacional. */
  chips?(s: State): (HTMLElement | null)[];
  desmontar?(): void;
  keys?(tecla: string, s: State): boolean;
}

/** Fábrica de tela do 2º turno: título do catálogo, chips de andamento e ciclo mount/update/unmount. */
export function criarTela2T(def: DefTela2T): View {
  let raiz: HTMLElement | null = null;
  let ultimas: readonly unknown[] | null = null;
  const view: View = {
    id: def.id,
    dwell: def.dwell,
    titulo: () => tituloDa2T(def.id) ?? def.id,
    needs: s => def.needs(s),
    mount(el) {
      raiz = el;
      if (def.cheia) el.classList.add("tela--cheia");
      el.classList.add("tela--2t");
      def.montar(partes(el), el);
    },
    update(s) {
      if (!raiz) return;
      const p = partes(raiz);
      definirChips(p.chips, (def.chips ? def.chips(s) : [chipAndamento(s.estado?.br.pst ?? 0, false)]).filter((c): c is HTMLElement => c !== null));
      const atuais = def.entradas(s);
      if (ultimas && atuais.length === ultimas.length && atuais.every((x, i) => x === ultimas?.[i])) return;
      ultimas = atuais;
      def.atualizar(s, p, raiz);
    },
    unmount() {
      def.desmontar?.();
      raiz = null;
      ultimas = null;
    },
  };
  if (def.keys) view.keys = def.keys;
  return view;
}

/** Dados da rota ou null; atalho tipado. */
export const dados = <K extends Rota2T>(s: State, rota: K): Dados2T[K] | null => dadosDe(s.doist, rota);

/** Barra de progresso 0 a 100 como `<span class="d2-barra"><i></i></span>`; a largura vai por estilo. */
export function barra(pst: number, classe = ""): HTMLElement {
  const b = h("span", `d2-barra ${classe}`.trim());
  const i = document.createElement("i");
  i.style.width = `${Math.max(0, Math.min(100, pst))}%`;
  b.append(i);
  return b;
}

/** Rodapé de rótulo obrigatório do contrato ("pede explicação, não indica irregularidade"). */
export function rodape(textoRodape: string): HTMLElement {
  return h("p", "d2-rodape", textoRodape);
}

export const ROTULO_ATRASO = "atraso pede explicação, não indica irregularidade";
export const ROTULO_ABSTENCAO = "abstenção atípica pede explicação, não indica irregularidade";
export const ROTULO_PAUSA = "pausa é intervalo sem versão nova publicada, não acusação";
export const ROTULO_PARALELA = "soma dos BUs recebidos, não projeção";
export const SEM_REGUA = "sem régua do 1º turno";
