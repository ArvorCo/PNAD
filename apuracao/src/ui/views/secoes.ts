// Tela "secoes": a cadeia de tempos de uma seção (encerramento, emissão do BU, recebimento no
// TSE, totalização do município), o atraso entre encerramento e recebimento por UF (p50 e p90
// com a marca do 1º turno), as seções fechadas tarde e a cobertura da amostra. Fonte: amostra
// de seções do arquivo-urna; não cobre todas as seções do país.

import { chip, chipAndamento } from "../components/chip.ts";
import type { LagPct, LinhaSecoes } from "../data/doist.ts";
import { decimal, inteiro, nomeProprio, pct } from "../data/format.ts";
import { atualizarAviso, barra, criarTela2T, dados, esvaziar, h, montarComAviso, rodape, SEM_REGUA } from "./doist-ui.ts";

const MOSTRAR = 12;

const min1 = (x: number | null): string => (x === null ? "sem medida" : `${decimal(x, 1)} min`);
const mais1 = (x: number | null): string => (x === null ? "sem medida" : `+${decimal(x, 1)} min`);

function passo(rotulo: string, grande: string, pequeno: string, ref: string | null): HTMLElement {
  const p = h("div", "sc-passo");
  p.append(h("p", "sc-passo-rot", rotulo), h("p", "sc-passo-v num", grande), h("p", "sc-passo-p", pequeno), h("p", "sc-passo-ref", ref ?? ""));
  return p;
}

function lagTexto(l: LagPct): string {
  return l.p90 === null ? "" : `90% em até ${min1(l.p90)}`;
}

/** Maior valor entre p90 e a marca do 1T, para a escala das barras. */
export function escalaLag(linhas: readonly LinhaSecoes[]): number {
  const v = linhas.flatMap(l => [l.lag_encerr_recebimento_min.p90, l.ref_1t?.lag_p90 ?? null]).filter((x): x is number => x !== null);
  return Math.max(5, ...v) * 1.05;
}

/** As UFs com maior p90 de atraso entre encerramento e recebimento (as de maior espera aparecem primeiro). */
export function ufsDeMaiorLag(linhas: readonly LinhaSecoes[], n: number): LinhaSecoes[] {
  return [...linhas]
    .filter(l => l.recebidas > 0 && l.lag_encerr_recebimento_min.p90 !== null)
    .sort((a, b) => (b.lag_encerr_recebimento_min.p90 ?? 0) - (a.lag_encerr_recebimento_min.p90 ?? 0) || a.uf.localeCompare(b.uf))
    .slice(0, n);
}

function linhaLag(l: LinhaSecoes, max: number, comRegua: boolean): HTMLElement {
  const r = h("div", "sc-lag");
  const p50 = l.lag_encerr_recebimento_min.p50 ?? 0;
  const p90 = l.lag_encerr_recebimento_min.p90 ?? 0;
  const area = h("div", "sc-lag-area");
  const b90 = h("i", "sc-b90");
  b90.style.width = `${(100 * p90) / max}%`;
  const b50 = h("i", "sc-b50");
  b50.style.width = `${(100 * p50) / max}%`;
  area.append(b90, b50);
  if (comRegua && l.ref_1t) {
    for (const [v, c, t] of [
      [l.ref_1t.lag_p50, "sc-ref sc-ref--50", "mediana no 1º turno"],
      [l.ref_1t.lag_p90, "sc-ref sc-ref--90", "90% no 1º turno"],
    ] as const) {
      if (v === null) continue;
      const m = h("i", c);
      m.style.left = `${(100 * v) / max}%`;
      m.title = `${t}: ${min1(v)}`;
      area.append(m);
    }
  }
  r.append(h("b", "sc-lag-uf", l.uf), area, h("span", "sc-lag-v num", `${decimal(p50, 1)} · ${decimal(p90, 1)} min`));
  return r;
}

export function criarSecoes() {
  let palco: HTMLElement | null = null;
  let lado: HTMLElement | null = null;
  return criarTela2T({
    id: "secoes",
    dwell: 22,
    needs: () => [{ tipo: "doist", rota: "secoes" }, { tipo: "estado" }],
    montar(p) {
      palco = montarComAviso(p.corpo, "sc", `<div class="sc-cadeia"></div><h2 class="sc-h">atraso entre o encerramento e o recebimento no TSE, por UF</h2><div class="sc-lags"></div>`);
      palco.append(rodape("amostra de seções do arquivo-urna, não todas as seções; mediana e 90% em minutos"));
      p.painel.classList.add("painel--2t");
      lado = h("div", "sc-painel");
      p.painel.append(lado);
    },
    chips(s) {
      const r = dados(s, "secoes");
      return [chipAndamento(s.estado?.br.pst ?? 0, false), r ? chip(`amostra de ${inteiro(r.totais.alvo)} seções`, "neutro") : null];
    },
    entradas: s => [s.doist.secoes],
    atualizar(s, p) {
      if (!palco || !lado) return;
      const r = dados(s, "secoes");
      if (!atualizarAviso(p.corpo, s, "secoes", "Seções") || !r) {
        esvaziar(lado);
        return;
      }
      const br = r.brasil;
      const comRegua = br.ref_1t !== null;
      const cadeia = palco.querySelector<HTMLElement>(".sc-cadeia");
      const lags = palco.querySelector<HTMLElement>(".sc-lags");
      if (!cadeia || !lags) return;
      const seta = (): HTMLElement => h("span", "sc-seta", "→");
      cadeia.replaceChildren(
        passo("votação encerrada", br.encerramento_p50_hhmm ?? "sem dado", br.encerramento_p90_hhmm ? `90% até ${br.encerramento_p90_hhmm}` : "", comRegua && br.ref_1t?.enc_p90_hhmm ? `1º turno: 90% até ${br.ref_1t.enc_p90_hhmm}` : null),
        seta(),
        passo("BU emitido", mais1(br.lag_encerr_emissao_min.p50), br.lag_encerr_emissao_min.p90 !== null ? `90% em até ${min1(br.lag_encerr_emissao_min.p90)}` : "", null),
        seta(),
        passo("recebido no TSE", mais1(br.lag_encerr_recebimento_min.p50), lagTexto(br.lag_encerr_recebimento_min), comRegua && br.ref_1t?.lag_p50 !== null && br.ref_1t?.lag_p50 !== undefined ? `1º turno: ${min1(br.ref_1t.lag_p50)}` : null),
        seta(),
        passo(
          "município totalizado",
          br.lag_recebimento_totalizacao_min ? mais1(br.lag_recebimento_totalizacao_min.p50) : "sem medida",
          br.lag_recebimento_totalizacao_min ? lagTexto(br.lag_recebimento_totalizacao_min) : "a rota ainda não informa este passo",
          null,
        ),
      );
      const top = ufsDeMaiorLag(r.por_uf, MOSTRAR);
      const max = escalaLag(top);
      lags.replaceChildren(
        ...(top.length > 0
          ? [
              h("p", "sc-leg", "barra escura: mediana; barra clara: 90%; traço: 1º turno"),
              ...top.map(l => linhaLag(l, max, comRegua)),
            ]
          : [h("p", "d2-vazio", "nenhuma seção da amostra recebida ainda")]),
      );
      if (!comRegua) lags.append(h("p", "d2-nota", SEM_REGUA));

      const tard = r.tardias.slice(0, 6);
      lado.replaceChildren(
        h("h2", "sc-h", `seções fechadas tarde (${inteiro(r.totais.tardias)})`),
        tard.length > 0
          ? (() => {
              const ol = h("ol", "sc-tard");
              for (const t of tard) {
                const li = h("li", "sc-tard-item");
                li.append(
                  h("span", "sc-tard-nome corte", `${nomeProprio(t.nm)}, ${t.uf}`),
                  h("span", "sc-tard-v num", `${t.encerramento_hhmm} → ${t.recebido_hhmm}`),
                  h("span", "sc-tard-s num", `zona ${Number(t.zona) || t.zona}, seção ${Number(t.secao) || t.secao}`),
                );
                ol.append(li);
              }
              return ol;
            })()
          : h("p", "d2-vazio", "nenhuma seção da amostra fechou depois das 18:00"),
        h("p", "d2-nota", "tarde: votação encerrada depois das 18:00 de Brasília; não indica irregularidade"),
        h("h2", "sc-h", "cobertura da amostra"),
        barra(r.totais.alvo > 0 ? (100 * r.totais.recebidas) / r.totais.alvo : 0, "d2-barra--grande"),
        h("p", "sc-cob num", `${inteiro(r.totais.recebidas)} de ${inteiro(r.totais.alvo)} seções recebidas (${pct(r.totais.alvo > 0 ? (100 * r.totais.recebidas) / r.totais.alvo : 0, 1)})`),
        h(
          "p",
          "d2-nota",
          `${r.desenho.nacional_por_uf} seções por UF para o nacional${r.desenho.estaduais_por_uf > 0 ? `, mais ${r.desenho.estaduais_por_uf} nas UFs com governador` : ""}${r.desenho.inclui_paralela ? ", incluindo as da paralela" : ""}`,
        ),
      );
    },
    desmontar() {
      palco = null;
      lado = null;
    },
  });
}
