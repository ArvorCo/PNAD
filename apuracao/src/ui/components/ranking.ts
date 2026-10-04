// Ranking do template executivo: foto, nome de urna, número e sigla, percentual dos
// válidos com count-up, barra na cor do candidato e votos. Nós estáveis por sqcand,
// reordenação FLIP de 500 ms. Chips só pela situação do TSE (nunca projetada).

import { chip, chipSituacao } from "./chip.ts";
import { criarContador, movimentoReduzido } from "./contador.ts";
import type { Contador } from "./contador.ts";
import { foto } from "./foto.ts";
import { corCampo, corCandidato, mix, PAPEL } from "../data/cores.ts";
import { inteiro, nomeProprio, pct } from "../data/format.ts";
import { colapsarOutros, ehOutros, ranking, rotuloOutros } from "../state/selectors.ts";
import type { Campos, Candidato, Cores } from "../state/types.ts";

export const COR_OUTROS = "#8a8f98";
/** Cor neutra de empate: o mapa e o ranking não pintam líder. */
export const COR_EMPATE = mix(PAPEL, "#192e2b", 0.3);

// ---------- partes puras ----------

export interface ItemRanking {
  chave: string; // sqcand ou "outros"
  outros: boolean;
  nome: string;
  numero: string;
  sigla: string;
  vap: number;
  pvapn: number;
  cor: string;
  semVoto: boolean;
  valido: boolean;
  cand: Candidato | null;
}

/** Destinação do voto válida? (o resto vira "sub judice", em muted). */
export const votoValido = (dvt: string): boolean => !dvt || /^v[aá]lido/i.test(dvt);

/**
 * Linhas do ranking: ordem por votos (zero votos ficam pela ordem do número) e, quando
 * a lista passa de `max`, os `max - 1` primeiros mais "outros N".
 */
export function linhasRanking(cand: readonly Candidato[], max: number, cores: ReadonlyMap<string, string>): ItemRanking[] {
  return colapsarOutros(cand, max).map(x => {
    if (ehOutros(x)) {
      return {
        chave: "outros",
        outros: true,
        nome: rotuloOutros(x),
        numero: "",
        sigla: "",
        vap: x.vap,
        pvapn: x.pvapn,
        cor: COR_OUTROS,
        semVoto: x.vap === 0,
        valido: true,
        cand: null,
      };
    }
    return {
      chave: x.sqcand,
      outros: false,
      nome: nomeProprio(x.nmu),
      numero: x.n,
      sigla: x.sg,
      vap: x.vap,
      pvapn: x.pvapn,
      cor: cores.get(x.sqcand) ?? COR_OUTROS,
      semVoto: x.vap === 0,
      valido: votoValido(x.dvt),
      cand: x,
    };
  });
}

/** Empate no topo: os dois primeiros com o mesmo total de votos (e algum voto). */
export function empateNoTopo(cand: readonly Candidato[]): boolean {
  const [a, b] = ranking(cand);
  return !!a && !!b && a.vap > 0 && a.vap === b.vap;
}

/**
 * Cores dos candidatos a presidente: fixas por número (cores.json) e, para os demais,
 * a sequência pela ordem de `referencia` (o ranking nacional, para a cor não mudar entre telas).
 */
export function coresPresidente(cand: readonly Candidato[], cores: Cores, referencia: readonly Candidato[] = cand): Map<string, string> {
  const ordem = ranking(referencia).filter(c => !cores.candidatos[c.n]);
  const pos = new Map(ordem.map((c, i) => [c.n, i]));
  const extra = ordem.length;
  const saida = new Map<string, string>();
  let novos = 0;
  for (const c of ranking(cand)) {
    const p = pos.get(c.n) ?? extra + novos++;
    saida.set(c.sqcand, corCandidato(c.n, p, cores));
  }
  return saida;
}

/** Fração de papel na cor de quem divide o campo com o líder. */
export const MISTURA_MESMO_CAMPO = 0.35;

/**
 * Cores das disputas estaduais pelo campo. Quem divide o campo com o líder recebe a cor
 * misturada com 35% de papel, para o 1º e o 2º não ficarem iguais.
 */
export function coresEstaduais(cand: readonly Candidato[], campos?: Campos): Map<string, string> {
  const r = ranking(cand);
  const lider = r[0];
  const saida = new Map<string, string>();
  r.forEach((c, i) => {
    const base = corCampo(c.campo, campos);
    const mesmo = i > 0 && lider !== undefined && lider.vap > 0 && c.campo === lider.campo;
    saida.set(c.sqcand, mesmo ? mix(base, PAPEL, MISTURA_MESMO_CAMPO) : base);
  });
  return saida;
}

/**
 * Quem recebe o chip "lidera": os `nv` primeiros com votos, desde que a última vaga não
 * esteja empatada com o seguinte. Sem `nv`, ninguém.
 */
export function lideres(cand: readonly Candidato[], nv: number): Set<string> {
  if (nv <= 0) return new Set();
  const r = ranking(cand).filter(c => c.vap > 0);
  const corte = r[nv - 1];
  const seguinte = r[nv];
  const topo = r.slice(0, nv);
  if (corte && seguinte && corte.vap === seguinte.vap) return new Set(topo.filter(c => c.vap > corte.vap).map(c => c.sqcand));
  return new Set(topo.map(c => c.sqcand));
}

// ---------- componente ----------

export interface OpcoesRanking {
  /** Linhas visíveis, contando "outros". */
  max: number;
  fotoPx?: number;
  casas?: 1 | 2;
  /** Vagas que recebem o chip "lidera" (0 = sem chip). */
  nvLidera?: number;
}

export interface Ranking {
  readonly el: HTMLElement;
  update(cand: readonly Candidato[], cores: ReadonlyMap<string, string>): void;
  destroy(): void;
}

interface NoLinha {
  el: HTMLElement;
  nome: HTMLElement;
  sub: HTMLElement;
  chips: HTMLElement;
  barra: HTMLElement;
  fotoCaixa: HTMLElement;
  pct: Contador;
  votos: Contador;
  cor: string;
}

const votosTexto = (x: number): string => `${inteiro(x)} ${Math.round(x) === 1 ? "voto" : "votos"}`;

export function criarRanking(o: OpcoesRanking): Ranking {
  const el = document.createElement("ol");
  el.className = "rk";
  const casas = o.casas ?? 1;
  const fotoPx = o.fotoPx ?? 72;
  const nos = new Map<string, NoLinha>();

  const criarNo = (it: ItemRanking): NoLinha => {
    const li = document.createElement("li");
    li.className = "rk-linha";
    li.dataset.chave = it.chave;
    const fotoCaixa = document.createElement("span");
    fotoCaixa.className = "rk-foto";
    if (it.cand) fotoCaixa.append(foto({ sqcand: it.cand.sqcand, nome: it.cand.nmu, tamanho: fotoPx, cor: it.cor }));
    else {
      const d = document.createElement("span");
      d.className = "rk-outros-marca";
      fotoCaixa.append(d);
    }
    const nome = document.createElement("span");
    nome.className = "rk-nome corte";
    const linhaSub = document.createElement("span");
    linhaSub.className = "rk-linhasub";
    const sub = document.createElement("span");
    sub.className = "rk-sub";
    const chips = document.createElement("span");
    chips.className = "rk-chips";
    linhaSub.append(sub, chips);
    const pctC = criarContador({ formato: x => pct(Math.max(0, x), casas), classe: "rk-pct" });
    const trilho = document.createElement("span");
    trilho.className = "rk-trilho";
    const barra = document.createElement("i");
    trilho.append(barra);
    const votos = criarContador({ formato: x => votosTexto(Math.max(0, x)), classe: "rk-votos" });
    li.append(fotoCaixa, nome, pctC.el, linhaSub, trilho, votos.el);
    return { el: li, nome, sub, chips, barra, fotoCaixa, pct: pctC, votos, cor: it.cor };
  };

  return {
    el,
    update(cand, cores) {
      const itens = linhasRanking(cand, o.max, cores);
      const empate = empateNoTopo(cand);
      const lid = lideres(cand, o.nvLidera ?? 0);
      const primeiro = ranking(cand)[0];

      // FLIP, passo 1: posições antes.
      const animar = !movimentoReduzido() && el.isConnected;
      const antes = new Map<string, number>();
      if (animar) for (const [k, n] of nos) antes.set(k, n.el.getBoundingClientRect().top);

      const vistos = new Set<string>();
      itens.forEach((it, i) => {
        vistos.add(it.chave);
        let no = nos.get(it.chave);
        if (!no) {
          no = criarNo(it);
          nos.set(it.chave, no);
        }
        if (el.children[i] !== no.el) el.insertBefore(no.el, el.children[i] ?? null);
        const ehLider = !empate && !it.outros && primeiro !== undefined && it.chave === primeiro.sqcand && it.vap > 0;
        no.el.classList.toggle("lider", ehLider);
        no.el.classList.toggle("outros", it.outros);
        no.el.classList.toggle("sem-voto", it.semVoto);
        no.el.classList.toggle("subjudice", !it.valido);
        const cor = it.valido ? it.cor : COR_OUTROS;
        no.el.style.setProperty("--cor", cor);
        if (cor !== no.cor) {
          no.cor = cor;
          no.fotoCaixa.querySelector<HTMLElement>(".foto")?.style.setProperty("--foto-anel", cor);
        }
        if (no.nome.textContent !== it.nome) no.nome.textContent = it.nome;
        const sub = it.outros ? "somados" : `${it.numero} ${it.sigla}`;
        if (no.sub.textContent !== sub) no.sub.textContent = sub;
        const c = it.cand;
        const chips: (HTMLElement | null)[] = [];
        if (c) {
          const situacao = chipSituacao(c.st, c.e, c.dvt);
          if (situacao) chips.push(situacao);
          else if (empate && c.vap > 0 && c.vap === primeiro?.vap) chips.push(chip("empate"));
          else if (lid.has(c.sqcand)) chips.push(chip("lidera", "primeiro"));
        }
        const assinatura = chips.map(x => x?.textContent ?? "").join("|");
        if (no.chips.dataset.assinatura !== assinatura) {
          no.chips.dataset.assinatura = assinatura;
          no.chips.replaceChildren(...chips.filter((x): x is HTMLElement => x !== null));
        }
        no.barra.style.width = `${Math.min(100, Math.max(0, it.pvapn))}%`;
        no.pct.definir(it.pvapn, !it.semVoto);
        no.votos.definir(it.vap, !it.semVoto);
      });
      for (const [k, n] of nos) {
        if (vistos.has(k)) continue;
        n.pct.destroy();
        n.votos.destroy();
        n.el.remove();
        nos.delete(k);
      }

      // FLIP, passos 2 a 4: inverte e solta.
      if (!animar || antes.size === 0) return;
      const mover: HTMLElement[] = [];
      for (const [k, n] of nos) {
        const t0 = antes.get(k);
        if (t0 === undefined) continue;
        const dy = t0 - n.el.getBoundingClientRect().top;
        if (Math.abs(dy) < 0.5) continue;
        n.el.style.transition = "none";
        n.el.style.transform = `translateY(${dy}px)`;
        mover.push(n.el);
      }
      if (mover.length === 0) return;
      void el.offsetHeight;
      for (const m of mover) {
        m.style.transition = "transform var(--d-flip) var(--ease)";
        m.style.transform = "";
      }
    },
    destroy() {
      for (const n of nos.values()) {
        n.pct.destroy();
        n.votos.destroy();
      }
      nos.clear();
      el.remove();
    },
  };
}
