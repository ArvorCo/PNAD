// Tela `pres`: mapa do Brasil por UF na cor do líder (bandas de seções totalizadas) e
// painel executivo. No 2º turno vira duelo: dois blocos de 348 px, barra bipartida e
// mapa divergente pela margem (vermelho, papel, azul).

import { chip, chipSituacao } from "../components/chip.ts";
import { criarBarraValidos } from "../components/barraValidos.ts";
import { criarContador } from "../components/contador.ts";
import type { Contador } from "../components/contador.ts";
import { foto } from "../components/foto.ts";
import { coresPresidente } from "../components/ranking.ts";
import { mix, NAO_INICIADO, PAPEL } from "../data/cores.ts";
import { duracao, hora, inteiro, nomeProprio, pct } from "../data/format.ts";
import type { Candidato, Diff, Resultado, State, UnidadeMapa } from "../state/types.ts";
import { chaveMapa, chaveResultado } from "../state/types.ts";
import type { View } from "./registry.ts";
import { partes } from "./registry.ts";
import {
  assinaturaDeCores,
  chipDeAndamento,
  corDaUnidade,
  criarMapaVivo,
  criarPainelExecutivo,
  criarPalco,
  definirChips,
  desenharLegenda,
  eleicaoDe,
  LEGENDA_FIXA,
  legendaDosLideres,
  lembrarCargo,
  navegar,
  sufixoNacionalParado,
  textoDiferenca,
} from "./executivo.ts";
import type { ItemLegenda, Palco, PainelExecutivo } from "./executivo.ts";

/** Margem (pontos dos válidos) que satura a cor no mapa do duelo. */
export const MARGEM_SATURA = 20;
/** Fração mínima de cor para uma unidade com vencedor não parecer papel. */
const PISO_DUELO = 0.14;

/** Os dois candidatos do duelo em ordem fixa pelo número de urna (a posição não troca na virada). */
export function parDoDuelo(cand: readonly Candidato[]): [Candidato, Candidato] | null {
  const top = [...cand].sort((a, b) => b.vap - a.vap || a.n.localeCompare(b.n, "pt-BR", { numeric: true })).slice(0, 2);
  if (top.length < 2) return null;
  top.sort((a, b) => a.n.localeCompare(b.n, "pt-BR", { numeric: true }));
  return [top[0] as Candidato, top[1] as Candidato];
}

/** Cor divergente pela margem do líder da unidade: papel no empate, cor cheia a partir de 20 pontos. */
export function corDuelo(u: UnidadeMapa, cores: ReadonlyMap<string, string>): string {
  if (!u.lider || !(u.lider.vap > 0) || !(u.pst > 0)) return NAO_INICIADO;
  const margem = u.margem ?? 0;
  if (u.segundo && u.lider.vap === u.segundo.vap) return PAPEL;
  const cor = cores.get(u.lider.sqcand) ?? "#8a8f98";
  const t = Math.min(1, Math.max(PISO_DUELO, margem / MARGEM_SATURA));
  return mix(PAPEL, cor, t);
}

// ---------- painel do duelo ----------

interface BlocoDuelo {
  el: HTMLElement;
  fotoCaixa: HTMLElement;
  nome: HTMLElement;
  sub: HTMLElement;
  chips: HTMLElement;
  pct: Contador;
  votos: Contador;
  chave: string;
}

interface PainelDuelo {
  readonly el: HTMLElement;
  update(s: State, r: Resultado | null, cores: ReadonlyMap<string, string>): void;
  destroy(): void;
}

function criarPainelDuelo(): PainelDuelo {
  const el = document.createElement("div");
  el.className = "duelo";
  const blocos = document.createElement("div");
  blocos.className = "duelo-blocos";
  const bipartida = document.createElement("div");
  bipartida.className = "duelo-barra";
  bipartida.innerHTML = '<i class="duelo-a"></i><i class="duelo-b"></i><span class="duelo-meio"></span>';
  const barraA = bipartida.querySelector<HTMLElement>(".duelo-a") as HTMLElement;
  const barraB = bipartida.querySelector<HTMLElement>(".duelo-b") as HTMLElement;
  const vazio = document.createElement("p");
  vazio.className = "pex-vazio";
  const dif = document.createElement("p");
  dif.className = "pex-dif";
  const bv = criarBarraValidos();
  const tot = document.createElement("p");
  tot.className = "pex-tot num";
  el.append(vazio, blocos, bipartida, dif, bv.el, tot);

  const lados: BlocoDuelo[] = [0, 1].map(i => {
    const b = document.createElement("div");
    b.className = `duelo-bloco duelo-bloco--${i === 0 ? "a" : "b"}`;
    const fotoCaixa = document.createElement("div");
    fotoCaixa.className = "duelo-foto";
    const nome = document.createElement("p");
    nome.className = "duelo-nome corte";
    const sub = document.createElement("p");
    sub.className = "duelo-sub";
    const chips = document.createElement("p");
    chips.className = "duelo-chips";
    const pctC = criarContador({ formato: x => pct(Math.max(0, x), 2).replace("%", ""), classe: "duelo-pct", tag: "p" });
    const votos = criarContador({ formato: x => `${inteiro(Math.max(0, x))} votos`, classe: "duelo-votos", tag: "p" });
    b.append(fotoCaixa, nome, sub, pctC.el, votos.el, chips);
    blocos.append(b);
    return { el: b, fotoCaixa, nome, sub, chips, pct: pctC, votos, chave: "" };
  });

  return {
    el,
    update(s, r, cores) {
      const par = r ? parDoDuelo(r.cand) : null;
      const comecou = !!r && r.s.st > 0;
      vazio.hidden = !!par && comecou;
      vazio.textContent = !r
        ? "aguardando o primeiro arquivo nacional do 2º turno no servidor"
        : !par
          ? "o arquivo do 2º turno ainda não traz as duas candidaturas"
          : comecou
            ? ""
            : "a totalização do 2º turno ainda não começou";
      blocos.hidden = !par;
      bipartida.hidden = !par;
      if (par) {
        par.forEach((c, i) => {
          const b = lados[i];
          if (!b) return;
          const cor = cores.get(c.sqcand) ?? "#8a8f98";
          b.el.style.setProperty("--cor", cor);
          if (b.chave !== c.sqcand) {
            b.chave = c.sqcand;
            b.fotoCaixa.replaceChildren(foto({ sqcand: c.sqcand, nome: c.nmu, tamanho: 120, cor }));
          }
          b.nome.textContent = nomeProprio(c.nmu);
          b.nome.classList.toggle("longo", c.nmu.length > 12);
          b.sub.textContent = `${c.n} ${c.sg}`;
          b.pct.definir(c.pvapn, c.vap > 0);
          b.votos.definir(c.vap, c.vap > 0);
          const sit = chipSituacao(c.st, c.e, c.dvt);
          definirChips(b.chips, sit ? [sit] : []);
          b.el.classList.toggle("lider", c.vap > 0 && c.vap > (par[1 - i]?.vap ?? 0));
        });
        const [a, b] = par;
        const total = a.pvapn + b.pvapn;
        barraA.style.width = `${total > 0 ? (100 * a.pvapn) / total : 50}%`;
        barraB.style.width = `${total > 0 ? (100 * b.pvapn) / total : 50}%`;
        barraA.style.background = cores.get(a.sqcand) ?? "#8a8f98";
        barraB.style.background = cores.get(b.sqcand) ?? "#8a8f98";
        bipartida.classList.toggle("vazia", !(total > 0));
      }
      dif.textContent = r && comecou ? textoDiferenca(r.cand) : "";
      dif.hidden = !comecou;
      bv.update(r);
      bv.el.hidden = !r;
      const quando = hora(r?.dt_ht ?? null);
      const atraso = s.estado?.br.atraso_s;
      tot.textContent = quando
        ? `totalização TSE ${quando}${atraso === null || atraso === undefined ? "" : ` (atraso ${duracao(atraso)})`}${sufixoNacionalParado(r)}`
        : "o TSE ainda não totalizou seções do 2º turno";
      tot.classList.toggle("atrasado", (atraso ?? 0) > 180);
    },
    destroy() {
      for (const b of lados) {
        b.pct.destroy();
        b.votos.destroy();
      }
    },
  };
}

// ---------- tela ----------

export function criarPresidente(): View {
  let raiz: HTMLElement | null = null;
  let palco: Palco | null = null;
  let painel: PainelExecutivo | null = null;
  let duelo: PainelDuelo | null = null;
  let modoDuelo: boolean | null = null;
  // Com a soma das UFs a linha da totalização ganha uma segunda linha: o ranking cede uma posição.
  let modoSoma: boolean | null = null;
  const mapa = criarMapaVivo();
  let cores: Map<string, string> = new Map();
  let ultimoR: Resultado | null | undefined;
  let ultimoState: State | null = null;

  const ehDuelo = (s: State): boolean => (s.config?.turno ?? s.estado?.turno ?? 1) === 2;

  return {
    id: "pres",
    dwell: 25,
    titulo: s => (ehDuelo(s) ? "Presidente, Brasil, 2º turno" : "Presidente, Brasil"),
    needs(s) {
      const ele = eleicaoDe(s, 1);
      return [
        { tipo: "resultado", ele, cargo: 1, abr: "br" },
        { tipo: "mapa", ele, cargo: 1, nivel: "uf", pai: "br" },
        { tipo: "estado" },
      ];
    },
    mount(el) {
      raiz = el;
      lembrarCargo(1);
      el.classList.add("tela--executivo");
      palco = criarPalco(partes(el).corpo);
    },
    update(s: State, _diff: Diff) {
      if (!raiz || !palco) return;
      ultimoState = s;
      const p = partes(raiz);
      const duel = ehDuelo(s);
      const ele = eleicaoDe(s, 1);
      const r = s.resultados[chaveResultado(ele, 1, "br")] ?? null;
      const soma = r?.fonte === "soma_ufs";
      if (duel !== modoDuelo || (!duel && soma !== modoSoma)) {
        modoDuelo = duel;
        modoSoma = soma;
        painel?.destroy();
        duelo?.destroy();
        painel = null;
        duelo = null;
        p.painel.classList.toggle("painel--duelo", duel);
        if (duel) {
          duelo = criarPainelDuelo();
          p.painel.replaceChildren(duelo.el);
        } else {
          painel = criarPainelExecutivo({ max: soma ? 6 : 7, casas: 1 });
          p.painel.replaceChildren(painel.el);
        }
        ultimoR = undefined;
        mapa.destroy();
      }

      if (r !== ultimoR) {
        cores = r ? coresPresidente(r.cand, s.cores) : new Map();
        ultimoR = r;
      }
      const chipsTopo = r ? [chipDeAndamento(r.s, r.tf)] : [];
      if (r?.fonte === "soma_ufs") chipsTopo.push(chip("soma das 27 UFs e exterior", "aviso"));
      definirChips(p.chips, chipsTopo);

      if (duelo) duelo.update(s, r, cores);
      else painel?.update(s, r, cores, r ? "a totalização nacional ainda não começou" : "aguardando o primeiro arquivo nacional no servidor");

      mapa.definir(palco.mapaEl, "uf", "br", {
        cor: u => (modoDuelo ? corDuelo(u, cores) : corDaUnidade(u, cores, 1, ultimoState ?? s)),
        rotulo: u => u.cd.toUpperCase(),
        titulo: u =>
          `${u.nm}: ${u.lider && u.lider.vap > 0 ? `${nomeProprio(u.lider.nmu)} ${pct(u.lider.pvapn)}` : "sem votos totalizados"}`,
        aoClicar: u => navegar({ v: "pres-uf", uf: u.cd.toUpperCase(), mun: null, zonas: false, zona: null }),
      });
      const dados = s.mapas[chaveMapa(ele, 1, "uf", "br")];
      mapa.pintar(dados, `${duel}|${assinaturaDeCores(cores)}`);

      let legenda: ItemLegenda[];
      const par = r ? parDoDuelo(r.cand) : null;
      if (duel && par) {
        const [a, b] = par;
        const ca = cores.get(a.sqcand) ?? "#8a8f98";
        const cb = cores.get(b.sqcand) ?? "#8a8f98";
        legenda = [
          { cor: ca, texto: `${nomeProprio(a.nmu)} +${MARGEM_SATURA} pontos` },
          { cor: `linear-gradient(90deg, ${ca}, ${PAPEL}, ${cb})`, texto: "empate no centro", classe: "fixa gradiente" },
          { cor: cb, texto: `${nomeProprio(b.nmu)} +${MARGEM_SATURA} pontos` },
          { cor: NAO_INICIADO, texto: "cinza = não iniciado", classe: "fixa" },
        ];
      } else {
        legenda = [...(dados ? legendaDosLideres(dados.unidades, cores) : []), ...LEGENDA_FIXA];
      }
      desenharLegenda(palco.legenda, legenda);

      const ufs = s.estado?.ufs ?? [];
      if (ufs.length === 0) palco.rodape.textContent = "o andamento por UF ainda não chegou";
      else {
        const fechadas = ufs.filter(u => u.pst >= 100).length;
        const paradas = ufs.filter(u => !(u.pst > 0)).length;
        const parciais = ufs.length - fechadas - paradas;
        palco.rodape.textContent = `UFs: ${inteiro(fechadas)} encerradas, ${inteiro(parciais)} parciais, ${inteiro(paradas)} não iniciadas`;
      }
    },
    unmount() {
      painel?.destroy();
      duelo?.destroy();
      mapa.destroy();
      raiz = null;
      palco = null;
      painel = null;
      duelo = null;
      ultimoState = null;
    },
  };
}
