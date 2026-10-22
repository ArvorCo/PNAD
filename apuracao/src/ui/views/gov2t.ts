// Tela "gov-2t": os seis duelos estaduais do 2º turno (AC, AM, DF, ES, RN, TO) em cartões, com
// foto, % dos válidos, seções, abstenção e a última virada. A tecla de uma UF leva ao mapa
// municipal (gov-uf).

import { chip, chipAndamento } from "../components/chip.ts";
import { corCampo, mix } from "../data/cores.ts";
import type { CandEstadual, Estadual } from "../data/doist.ts";
import { decimal, horaCurta, inteiro, nomeProprio, pct } from "../data/format.ts";
import type { Campos } from "../state/types.ts";
import { atualizarAviso, criarTela2T, dados, h, montarComAviso, SEM_REGUA } from "./doist-ui.ts";
import { rotuloAtraso, rotuloPp } from "./doist-util.ts";
import { navegar } from "./executivo.ts";
import { foto } from "../components/foto.ts";

/** Cores do par: campo político de cada um; se os dois caem no mesmo campo, o segundo escurece para a barra separar. */
export function coresDoPar(par: readonly CandEstadual[], campos: Campos): string[] {
  const cores = par.map(c => corCampo(c.campo, campos));
  if (cores.length === 2 && cores[0] === cores[1]) cores[1] = mix(cores[1] ?? "#8a8f98", "#192e2b", 0.45);
  return cores;
}

function cartaoCandidato(c: CandEstadual, cor: string, lider: boolean): HTMLElement {
  const l = h("div", `g2-cand${lider ? " g2-cand--lider" : ""}`);
  l.style.setProperty("--cor", cor);
  const f = h("span", "g2-foto");
  f.append(foto({ sqcand: c.sqcand, nome: nomeProprio(c.nome_urna), tamanho: 88, cor }));
  const nome = h("div", "g2-nome");
  nome.append(h("p", "g2-nome-t corte", nomeProprio(c.nome_urna)), h("p", "g2-nome-s", `${c.n} ${c.partido}`));
  const v = h("div", "g2-voto");
  v.append(h("p", "g2-pct num", c.vap > 0 ? decimal(c.pvapn, 1) : "–"), h("p", "g2-votos num", c.vap > 0 ? `${inteiro(c.vap)} votos` : "sem votos"));
  l.append(f, nome, v);
  return l;
}

function cartao(e: Estadual, campos: Campos, comRegua: boolean): HTMLElement {
  const c = h("article", "g2-cartao");
  c.dataset.uf = e.uf;
  const par = e.cand.slice(0, 2);
  const cores = coresDoPar(par, campos);
  const temVoto = par.some(x => x.vap > 0);
  const lider = temVoto ? (e.lider ?? "") : "";
  const cab = h("header", "g2-cab");
  cab.append(h("h2", "g2-uf", e.nome), h("span", "g2-pst num", `${pct(e.pst, 1)} das seções`));
  c.append(cab);
  par.forEach((x, i) => c.append(cartaoCandidato(x, cores[i] ?? "#5f6773", lider === x.sqcand)));
  const soma = par.reduce((s, x) => s + x.pvapn, 0);
  const barra = h("div", `g2-barra${temVoto ? "" : " vazia"}`);
  par.forEach((x, i) => {
    const seg = document.createElement("i");
    seg.style.width = `${soma > 0 ? (100 * x.pvapn) / soma : 50}%`;
    seg.style.background = cores[i] ?? "#5f6773";
    barra.append(seg);
  });
  c.append(barra);
  const rod = h("footer", "g2-rod");
  const nomeDe = (sq: string): string => nomeProprio(e.cand.find(x => x.sqcand === sq)?.nome_urna ?? "");
  const dif = temVoto ? `diferença ${rotuloPp(Math.abs(e.margem_pp)).replace("+", "")}` : "aguardando seções";
  rod.append(h("span", "g2-rod-a num", dif), h("span", "g2-rod-b num", e.comparecimento + e.abstencao > 0 ? `abstenção ${pct(e.pa, 1)}` : "abstenção sem dado"));
  const ultima = e.viradas[e.viradas.length - 1];
  const linha2 = h("p", "g2-virada num", ultima ? `virada às ${horaCurta(ultima.at)}: ${nomeDe(ultima.para)} passou à frente` : temVoto ? "sem virada até agora" : "");
  c.append(rod, linha2);
  const min = e.ref_1t?.atraso_min ?? null;
  if (comRegua && e.ref_1t && min !== null && Math.abs(min) >= 1) {
    const ch = chip(`${rotuloAtraso(min)} contra o 1º turno`, min >= 20 ? "atraso" : "neutro");
    ch.classList.add("g2-chip");
    c.append(ch);
  }
  c.addEventListener("click", () => navegar({ v: "gov-uf", uf: e.uf, mun: null, zonas: false, zona: null }));
  return c;
}

export function criarGov2T() {
  let grade: HTMLElement | null = null;
  return criarTela2T({
    id: "gov-2t",
    dwell: 24,
    cheia: true,
    needs: () => [{ tipo: "doist", rota: "estaduais" }, { tipo: "estado" }],
    montar(p) {
      const c = montarComAviso(p.corpo, "g2", `<div class="g2-grade"></div>`);
      grade = c.querySelector<HTMLElement>(".g2-grade");
    },
    chips(s) {
      const r = dados(s, "estaduais");
      const semRegua = !!r && r.ufs.length > 0 && r.ufs.every(u => !u.ref_1t);
      return [chipAndamento(s.estado?.br.pst ?? 0, false), semRegua ? chip(SEM_REGUA, "aviso") : null];
    },
    entradas: s => [s.doist.estaduais, s.campos],
    atualizar(s, p) {
      if (!grade) return;
      const r = dados(s, "estaduais");
      if (!atualizarAviso(p.corpo, s, "estaduais", "Governadores") || !r) return;
      const comRegua = r.ufs.some(u => u.ref_1t);
      grade.replaceChildren(...r.ufs.map(e => cartao(e, s.campos, comRegua)));
    },
    desmontar() {
      grade = null;
    },
  });
}
