// Tela "abstencao": mapa das UFs colorido pela diferença de abstenção contra o 1º turno
// (escala divergente que satura em ±5 pontos), tabela por região e os seis municípios que mais
// subiram e que mais caíram. Base de comparação: só os municípios já fechados.

import { chip, chipAndamento } from "../components/chip.ts";
import { criarMapa } from "../components/mapa.ts";
import type { Mapa as MapaSvg } from "../components/mapa.ts";
import { NAO_INICIADO } from "../data/cores.ts";
import type { BlocoAbstencao, MunAbstencao } from "../data/doist.ts";
import { inteiro, nomeProprio, pct } from "../data/format.ts";
import type { UnidadeMapa } from "../state/types.ts";
import { atualizarAviso, criarTela2T, dados, esvaziar, h, montarComAviso, ROTULO_ABSTENCAO, rodape, SEM_REGUA } from "./doist-ui.ts";
import { COR_ABSTENCAO_CAIU, COR_ABSTENCAO_SUBIU, corDivergente, fundoDoDelta, rotuloPp, SATURA_ABSTENCAO_PP } from "./doist-util.ts";

/** Unidades do mapa a partir dos blocos por UF: a "seção fechada" vira o % do eleitorado fechado. */
export function unidadesDeAbstencao(ufs: readonly BlocoAbstencao[]): UnidadeMapa[] {
  return ufs.map(u => ({ cd: u.chave, nm: u.nome, pst: u.pct_te_fechado, tf: false }));
}

/** Etiqueta do Δ: fundo claro, borda na cor da escala do mapa e texto escuro (nenhuma cor da escala dá 4,5:1 com texto nos dois lados). */
function celulaDelta(delta: number | null): HTMLElement {
  const c = h("span", "ab-delta num", rotuloPp(delta));
  c.style.background = fundoDoDelta(delta);
  c.style.borderColor = corDivergente(delta);
  return c;
}

function linhaRegiao(b: BlocoAbstencao, comRegua: boolean): HTMLElement {
  const l = h("div", "ab-reg");
  l.append(
    h("b", "ab-reg-nome", b.nome),
    comRegua ? celulaDelta(b.delta_pp) : h("span", "ab-delta ab-delta--sem", "–"),
    h("span", "ab-reg-pa", b.pa_2t === null ? "nenhum fechado" : `${pct(b.pa_2t, 1)}${comRegua && b.pa_1t_mesmos !== null ? ` · ${pct(b.pa_1t_mesmos, 1)}` : ""}`),
    h("span", "ab-reg-f", `${inteiro(b.pct_te_fechado)}%`),
  );
  l.title = `${b.n_mun_fechados} de ${b.n_mun} municípios fechados`;
  return l;
}

function linhaMun(m: MunAbstencao): HTMLElement {
  const l = h("div", "ab-mun");
  l.append(h("span", "ab-mun-nome corte", `${nomeProprio(m.nm)}, ${m.uf}`), celulaDelta(m.delta_pp), h("span", "ab-mun-pa num", pct(m.pa_2t, 1)));
  l.title = `${nomeProprio(m.nm)}, ${m.uf}: ${pct(m.pa_2t, 1)} agora, ${pct(m.pa_1t, 1)} no 1º turno`;
  return l;
}

export function criarAbstencao() {
  let mapa: MapaSvg | null = null;
  let lado: HTMLElement | null = null;
  let legenda: HTMLElement | null = null;
  let deltas = new Map<string, number | null>();
  let ultimoDados: unknown = null;

  return criarTela2T({
    id: "abstencao",
    dwell: 22,
    needs: () => [{ tipo: "doist", rota: "abstencao" }, { tipo: "estado" }],
    montar(p) {
      const c = montarComAviso(
        p.corpo,
        "ab",
        `<div class="ab-mapa"></div>
         <div class="ab-legenda"></div>`,
      );
      const alvo = c.querySelector<HTMLElement>(".ab-mapa");
      legenda = c.querySelector<HTMLElement>(".ab-legenda");
      c.append(rodape(`base: municípios fechados; ${ROTULO_ABSTENCAO}`));
      if (alvo) {
        mapa = criarMapa(alvo, {
          nivel: "uf",
          pai: "br",
          largura: 1152,
          altura: 700,
          cor: u => (deltas.has(u.cd) ? corDivergente(deltas.get(u.cd) ?? null) : NAO_INICIADO),
          titulo: u => {
            const d = deltas.get(u.cd);
            return d === null || d === undefined ? `${u.nm}: sem município fechado ou sem régua` : `${u.nm}: ${rotuloPp(d)} contra o 1º turno`;
          },
        });
      }
      if (legenda) {
        legenda.innerHTML = `
          <span class="ab-leg-t">abstenção caiu</span>
          <i class="ab-leg-barra" style="background:linear-gradient(90deg, ${COR_ABSTENCAO_CAIU}, #f4f0e6, ${COR_ABSTENCAO_SUBIU})"></i>
          <span class="ab-leg-t">abstenção subiu</span>
          <span class="ab-leg-n num">cor cheia em ±${SATURA_ABSTENCAO_PP} pp; cinza: nenhum município fechado</span>`;
      }
      p.painel.classList.add("painel--2t");
      lado = h("div", "ab-painel");
      p.painel.append(lado);
    },
    chips(s) {
      // O título é longo: só dois chips. A falta da régua do 1º turno aparece no painel e no mapa.
      return [chipAndamento(s.estado?.br.pst ?? 0, false), chip("base: municípios fechados", "neutro")];
    },
    entradas: s => [s.doist.abstencao],
    atualizar(s, p) {
      if (!lado) return;
      const r = dados(s, "abstencao");
      if (!atualizarAviso(p.corpo, s, "abstencao", "Abstenção") || !r) {
        esvaziar(lado);
        return;
      }
      if (r !== ultimoDados) {
        ultimoDados = r;
        deltas = new Map(r.ufs.map(u => [u.chave, u.delta_pp]));
        mapa?.update(unidadesDeAbstencao(r.ufs));
      }
      const comRegua = r.ufs.some(u => u.delta_pp !== null) || r.brasil.delta_pp !== null;
      const subiu = r.destaques.subiu.slice(0, 6);
      const caiu = r.destaques.caiu.slice(0, 6);
      const secao = (titulo: string, itens: HTMLElement[], vazio: string): HTMLElement[] => [
        h("h2", "ab-h", titulo),
        ...(itens.length > 0 ? itens : [h("p", "d2-vazio", vazio)]),
      ];
      const cabRegiao = h("div", "ab-reg ab-reg--cab");
      for (const t of ["região", "diferença", comRegua ? "abstenção 2T · 1T" : "abstenção 2T", "fechado"]) cabRegiao.append(h("span", "", t));
      lado.replaceChildren(
        h("h2", "ab-h", `Brasil: ${r.brasil.pa_2t === null ? "sem município fechado" : pct(r.brasil.pa_2t, 1)}${comRegua && r.brasil.delta_pp !== null ? ` (${rotuloPp(r.brasil.delta_pp)})` : ""}`),
        cabRegiao,
        ...r.regioes.map(b => linhaRegiao(b, comRegua)),
        ...secao("municípios que mais subiram", subiu.map(linhaMun), comRegua ? "nenhum município com alta de 3 pontos ou mais" : SEM_REGUA),
        ...secao("municípios que mais caíram", caiu.map(linhaMun), comRegua ? "nenhum município com queda de 3 pontos ou mais" : SEM_REGUA),
      );
    },
    desmontar() {
      mapa?.destroy();
      mapa = null;
      lado = null;
      legenda = null;
      deltas = new Map();
      ultimoDados = null;
    },
  });
}
