// Tela "comparecimento": vigilância de falso comparecimento. Mapa do Brasil com um ponto por
// seção recebida no 2º turno (cor pela diferença de comparecimento contra a mesma seção no 1º
// turno, anel vermelho com dois sinais ou mais, losango para urna de contingência ou recarregada)
// ou, com a tecla m, um ponto por município com 30% das seções apuradas. Painel com os
// contadores de sinais, a distribuição do delta e as seções (ou municípios) de maior alerta;
// faixa com os votos da prorrogação. Fonte: /api/2t/comparecimento.

import { chip, chipAndamento } from "../components/chip.ts";
import { criarMapa, IBGE_UF, SVG_NS } from "../components/mapa.ts";
import type { Mapa as MapaSvg } from "../components/mapa.ts";
import { NAO_INICIADO } from "../data/cores.ts";
import { decimal, inteiro, nomeProprio, pct } from "../data/format.ts";
import { CAIXA_BR, fitExtent } from "../geo/projecao.ts";
import type { ComparecimentoOut, MunicipioComparecimento, PontoSecao, SecaoComparecimento } from "../../secoes2t/comparecimento-tipos.ts";
import { ROTULO_COMPARECIMENTO } from "../../secoes2t/comparecimento-tipos.ts";
import type { UnidadeMapa } from "../state/types.ts";
import { atualizarAviso, criarTela2T, dados, esvaziar, h, montarComAviso } from "./doist-ui.ts";
import { COR_ABSTENCAO_CAIU, COR_ABSTENCAO_SUBIU, corDivergente, fundoDoDelta, rotuloPp } from "./doist-util.ts";

/** Saturação da cor dos pontos: ±10 pontos de comparecimento contra o 1º turno. */
export const SATURA_COMPARECIMENTO_PP = 10;
const COR_ANEL = "#c0261b";
const COR_CONTORNO = "#3c4250";
const LARGURA = 900;
const ALTURA = 760;
/** Mesma margem de rótulos que o mapa de UFs usa à direita (components/mapa.ts). */
const MARGEM_ROTULOS = 72;
const LISTA = 8;
/** As 27 UFs como unidades do mapa de fundo (cor clara única, para os pontos se destacarem). */
const UFS_FUNDO: UnidadeMapa[] = Object.values(IBGE_UF).map(uf => ({ cd: uf, nm: uf, pst: 100, tf: true }));
const FUNDO = "#ece6da";

export type Camada = "secoes" | "municipios";

/** A tecla m (variante da interface) alterna as duas camadas. */
export const camadaDe = (variante: number): Camada => (variante % 2 === 1 ? "municipios" : "secoes");

/** Raio do ponto da seção pela raiz dos aptos (400 aptos ≈ 5,6). */
export function raioSecao(aptos: number): number {
  return Math.max(2.2, Math.min(8.5, 2.2 + 3.4 * Math.sqrt(Math.max(0, aptos) / 400)));
}

/** Raio do ponto do município pela raiz do eleitorado (100 mil ≈ 3,8; 1 milhão ≈ 12). */
export function raioMunicipio(te: number): number {
  return Math.max(1.6, Math.min(20, 1.2 * Math.sqrt(Math.max(0, te) / 10_000)));
}

/** Ordem de desenho: sem alerta embaixo, maior escore e contingência por cima. */
export function ordemDesenho(pontos: readonly PontoSecao[]): PontoSecao[] {
  return [...pontos].sort((a, b) => a[3] - b[3] || a[5] - b[5] || Math.abs(a[2] ?? 0) - Math.abs(b[2] ?? 0));
}

/** Delta de fatia com o n ao lado; abaixo do mínimo do contrato, só o aviso de n pequeno. */
export function textoFatia(delta: number | null, n: number, nMin: number): string {
  if (n < nMin) return `n < ${nMin} (n = ${inteiro(n)})`;
  if (delta === null) return `sem dado (n = ${inteiro(n)})`;
  return `${rotuloPp(delta)} (n = ${inteiro(n)})`;
}

const cor = (d: number | null): string => corDivergente(d, SATURA_COMPARECIMENTO_PP);

function etiquetaDelta(delta: number | null): HTMLElement {
  const c = h("span", "ab-delta cp-delta num", delta === null ? "sem 1º turno" : rotuloPp(delta));
  c.style.background = delta === null ? NAO_INICIADO : fundoDoDelta(delta, SATURA_COMPARECIMENTO_PP);
  c.style.borderColor = delta === null ? "var(--line)" : cor(delta);
  return c;
}

function contador(n: number, rotulo: string, alerta = false): HTMLElement {
  const c = h("div", `cp-cont${alerta && n > 0 ? " cp-cont--alerta" : ""}`);
  c.append(h("b", "cp-cont-n num", inteiro(n)), h("span", "cp-cont-r", rotulo));
  return c;
}

function linhaSecao(s: SecaoComparecimento): HTMLElement {
  const li = h("li", "cp-item");
  const marcas: string[] = [`zona ${s.zona}, seção ${s.secao}`];
  if (s.encerramento_hhmm) marcas.push(s.enc1_hhmm ? `${s.encerramento_hhmm} (1T ${s.enc1_hhmm})` : s.encerramento_hhmm);
  if (s.sem_bio_pct !== null) marcas.push(`sem biometria ${pct(s.sem_bio_pct, 1)}`);
  if (s.papel) marcas.push("cédula");
  if (s.contingencia) marcas.push("contingência");
  li.append(
    h("span", "cp-item-nome corte", `${s.uf} · ${nomeProprio(s.nm)}`),
    etiquetaDelta(s.delta_pp),
    h("span", "cp-item-s corte", marcas.join(" · ")),
    h("span", `cp-item-e${s.escore >= 2 ? " cp-item-e--alto" : ""}`, s.escore === 1 ? "1 sinal" : `${s.escore} sinais`),
  );
  li.title = `${s.uf}, ${nomeProprio(s.nm)}, zona ${s.zona}, seção ${s.secao}: comparecimento ${s.taxa_comp === null ? "sem dado" : pct(s.taxa_comp, 1)} contra ${s.taxa_comp_1t === null ? "sem dado" : pct(s.taxa_comp_1t, 1)} no 1º turno`;
  return li;
}

function linhaMunicipio(m: MunicipioComparecimento): HTMLElement {
  const li = h("li", "cp-item");
  li.append(
    h("span", "cp-item-nome corte", `${m.uf} · ${nomeProprio(m.nm)}`),
    etiquetaDelta(m.delta_pp),
    h("span", "cp-item-s corte", `comparecimento ${pct(m.taxa_2t, 1)}, no 1º turno ${pct(m.taxa_1t, 1)}`),
    h("span", "cp-item-e", `${inteiro(m.pst)}% apurado`),
  );
  return li;
}

function celulaProrrogacao(rotulo: string, valor: string, nota: string): HTMLElement {
  const c = h("div", "cp-pr-cel");
  c.append(h("span", "cp-pr-r", rotulo), h("b", "cp-pr-v num", valor), h("span", "cp-pr-n", nota));
  return c;
}

function desenharPontos(g: SVGGElement, r: ComparecimentoOut, camada: Camada): void {
  const ajuste = fitExtent(CAIXA_BR, LARGURA - MARGEM_ROTULOS, ALTURA, 12);
  const frag = document.createDocumentFragment();
  const no = <K extends keyof SVGElementTagNameMap>(tag: K, attrs: Record<string, string | number>): SVGElementTagNameMap[K] => {
    const e = document.createElementNS(SVG_NS, tag);
    for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, String(v));
    return e;
  };
  if (camada === "secoes") {
    for (const p of ordemDesenho(r.pontos)) {
      const [x, y] = ajuste.projetar(p[0], p[1]);
      const raio = raioSecao(p[4]);
      const fill = cor(p[2]);
      if (p[5] === 1) {
        const d = raio + 1.6;
        frag.append(no("path", { d: `M${x} ${y - d}L${x + d} ${y}L${x} ${y + d}L${x - d} ${y}Z`, fill, stroke: COR_CONTORNO, "stroke-width": 1.4, class: "cp-ponto cp-ponto--cont" }));
      } else {
        frag.append(no("circle", { cx: x, cy: y, r: raio, fill, stroke: COR_CONTORNO, "stroke-width": 0.6, class: "cp-ponto" }));
      }
      if (p[3] >= 2) frag.append(no("circle", { cx: x, cy: y, r: raio + 3.2, fill: "none", stroke: COR_ANEL, "stroke-width": 2.4, class: "cp-anel" }));
    }
  } else {
    const ms = r.municipios.filter((m): m is MunicipioComparecimento & { lat: number; lon: number } => m.lat !== null && m.lon !== null);
    ms.sort((a, b) => b.te - a.te || Math.abs(a.delta_pp) - Math.abs(b.delta_pp));
    for (const m of ms) {
      const [x, y] = ajuste.projetar(m.lon, m.lat);
      const c = no("circle", { cx: x, cy: y, r: raioMunicipio(m.te), fill: cor(m.delta_pp), stroke: COR_CONTORNO, "stroke-width": 0.7, "fill-opacity": 0.92, class: "cp-ponto cp-ponto--mun" });
      const t = no("title", {});
      t.textContent = `${nomeProprio(m.nm)}, ${m.uf}: ${rotuloPp(m.delta_pp)} contra o 1º turno`;
      c.append(t);
      frag.append(c);
    }
  }
  g.replaceChildren(frag);
}

export function criarComparecimento() {
  let mapa: MapaSvg | null = null;
  let gPontos: SVGGElement | null = null;
  let vazio: HTMLElement | null = null;
  let legenda: HTMLElement | null = null;
  let faixa: HTMLElement | null = null;
  let lado: HTMLElement | null = null;

  return criarTela2T({
    id: "comparecimento",
    dwell: 24,
    needs: () => [{ tipo: "doist", rota: "comparecimento" }, { tipo: "estado" }],
    montar(p) {
      const c = montarComAviso(
        p.corpo,
        "cp",
        `<div class="cp-mapa"><p class="cp-vazio" hidden></p></div>
         <div class="cp-legenda"></div>
         <div class="cp-pr"></div>`,
      );
      const alvo = c.querySelector<HTMLElement>(".cp-mapa");
      vazio = c.querySelector<HTMLElement>(".cp-vazio");
      legenda = c.querySelector<HTMLElement>(".cp-legenda");
      faixa = c.querySelector<HTMLElement>(".cp-pr");
      c.append(h("p", "d2-rodape cp-rotulo", ROTULO_COMPARECIMENTO));
      if (alvo) {
        mapa = criarMapa(alvo, { nivel: "uf", pai: "br", largura: LARGURA, altura: ALTURA, cor: () => FUNDO, titulo: u => u.nm });
        mapa.update(UFS_FUNDO);
        gPontos = document.createElementNS(SVG_NS, "g") as SVGGElement;
        gPontos.setAttribute("class", "cp-pontos");
        gPontos.setAttribute("aria-hidden", "true");
        mapa.el.insertBefore(gPontos, mapa.el.querySelector(".mapa__rotulos"));
      }
      p.painel.classList.add("painel--2t");
      lado = h("div", "cp-painel");
      p.painel.append(lado);
    },
    chips(s) {
      const r = dados(s, "comparecimento");
      const camada = camadaDe(s.ui.variante);
      return [
        chipAndamento(s.estado?.br.pst ?? 0, false),
        r ? chip(camada === "secoes" ? `${inteiro(r.totais.recebidas)} seções recebidas` : `${inteiro(r.municipios.length)} municípios`, "neutro") : null,
      ];
    },
    entradas: s => [s.doist.comparecimento, camadaDe(s.ui.variante)],
    atualizar(s, p) {
      if (!lado || !legenda || !faixa) return;
      const r = dados(s, "comparecimento");
      if (!atualizarAviso(p.corpo, s, "comparecimento", "Comparecimento") || !r) {
        esvaziar(lado);
        return;
      }
      const camada = camadaDe(s.ui.variante);
      if (gPontos) desenharPontos(gPontos, r, camada);
      if (vazio) {
        const semSecao = camada === "secoes" && r.totais.recebidas === 0;
        const semMun = camada === "municipios" && r.municipios.length === 0;
        vazio.hidden = !semSecao && !semMun;
        vazio.textContent = semSecao ? "amostra ainda sem boletins" : semMun ? "nenhum município com 30% das seções apuradas" : "";
      }

      legenda.innerHTML = "";
      legenda.append(
        h("b", "cp-camada", camada === "secoes" ? "camada: seções" : "camada: municípios"),
        h("span", "cp-leg-t", "comparecimento caiu"),
        (() => {
          const barra = h("i", "ab-leg-barra cp-leg-barra");
          barra.style.background = `linear-gradient(90deg, ${COR_ABSTENCAO_CAIU}, #f4f0e6, ${COR_ABSTENCAO_SUBIU})`;
          return barra;
        })(),
        h("span", "cp-leg-t", "subiu"),
        h("span", "cp-leg-n", camada === "secoes" ? `±${SATURA_COMPARECIMENTO_PP} pp contra a mesma seção no 1º turno; anel vermelho: 2 sinais ou mais; losango: contingência; tecla m: municípios` : `±${SATURA_COMPARECIMENTO_PP} pp contra o município no 1º turno; tamanho pelo eleitorado; tecla m: seções`),
      );

      const pr = r.prorrogacao;
      const b = pr.brasil;
      faixa.replaceChildren(
        h("h2", "cp-h cp-pr-h", `votos da prorrogação: tardias (${r.regras.tardia_min_vs_1t} min depois do 1º turno ou após ${r.regras.apos_hhmm})`),
        celulaProrrogacao("seções tardias", inteiro(b.n_tardias), `${inteiro(b.n_apos_19h)} depois das 19:00; ${inteiro(b.n_pontuais)} no horário`),
        celulaProrrogacao(
          "comparecimento contra o 1º turno",
          b.delta_comp_tardias === null ? "sem dado" : rotuloPp(b.delta_comp_tardias),
          `tardias; pontuais ${b.delta_comp_pontuais === null ? "sem dado" : rotuloPp(b.delta_comp_pontuais)}`,
        ),
        celulaProrrogacao("fatia de Flávio contra a mesma seção no 1º turno", textoFatia(b.delta_fatia_vs_1t_pp, b.n_vs_1t, pr.n_min), "nas tardias, ponderada por votos"),
        celulaProrrogacao("fatia de Flávio contra as pontuais do município", textoFatia(b.delta_fatia_vs_pontuais_pp, b.n_vs_pontuais, pr.n_min), "tardias menos pontuais, mesmo município"),
      );

      const si = r.sinais;
      const grade = h("div", "cp-grade");
      grade.append(
        contador(si.delta, `subiu ${r.regras.delta_pp_min} pp ou mais`, true),
        contador(si.sem_bio, "sem biometria alta", true),
        contador(si.tardia, "encerramento tardio", true),
        contador(si.tarde, `depois das ${r.regras.tarde_hhmm}`),
        contador(si.papel, "cédula", true),
        contador(si.contingencia, "contingência ou recarga", true),
        contador(si.escore_2_mais, "2 sinais ou mais", true),
        contador(r.totais.com_ref_1t, "com régua do 1º turno"),
      );
      const dist = camada === "secoes" ? r.delta : r.municipios_delta;
      const itens = camada === "secoes" ? r.top.slice(0, LISTA).map(linhaSecao) : r.municipios_top.slice(0, LISTA).map(linhaMunicipio);
      const ol = h("ol", "cp-lista");
      ol.append(...itens);
      lado.replaceChildren(
        h("h2", "cp-h", `sinais em ${inteiro(r.totais.recebidas)} seções recebidas`),
        grade,
        h(
          "p",
          "cp-dist",
          dist.n === 0
            ? camada === "secoes"
              ? "diferença de comparecimento: sem seção com régua do 1º turno"
              : "diferença de comparecimento: sem município comparável"
            : `diferença de comparecimento: mediana ${rotuloPp(dist.p50)}, 90% até ${rotuloPp(dist.p90)} (n = ${inteiro(dist.n)})`,
        ),
        h("h2", "cp-h", camada === "secoes" ? "seções de maior escore" : "municípios onde o comparecimento mais subiu"),
        itens.length > 0 ? ol : h("p", "d2-vazio", camada === "secoes" ? "amostra ainda sem boletins" : "nenhum município com 30% das seções apuradas"),
        h("p", "d2-nota", camada === "secoes" ? `escore: soma de 4 sinais (comparecimento, biometria, encerramento tardio, cédula)` : `só municípios com ${decimal(r.regras.mun_pst_min, 0)}% das seções apuradas ou mais`),
      );
    },
    desmontar() {
      mapa?.destroy();
      mapa = null;
      gPontos = null;
      vazio = null;
      legenda = null;
      faixa = null;
      lado = null;
    },
  });
}
