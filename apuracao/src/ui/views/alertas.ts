// Tela "alertas": as 12 anomalias mais recentes do servidor (pausa, atraso, abstenção atípica,
// divergência da paralela, virada, regressão, encerramento) com categoria em cor própria, hora,
// UF e texto, e o contador por categoria no painel.

import { chipAndamento } from "../components/chip.ts";
import { COR_CATEGORIA, contarPorCategoria, CATEGORIAS, maisRecentes, ROTULO_CATEGORIA } from "../data/categorias.ts";
import { horaCurta, inteiro } from "../data/format.ts";
import type { Anomalia } from "../state/types.ts";
import { criarTela2T, h, ROTULO_ABSTENCAO, ROTULO_ATRASO, ROTULO_PAUSA } from "./doist-ui.ts";

const VISIVEIS = 12;

function linha(a: Anomalia): HTMLElement {
  const l = h("li", `al-item al-item--${a.severidade ?? "info"}`);
  l.style.setProperty("--cor", COR_CATEGORIA[a.tipo]);
  const tag = h("span", "al-tag", ROTULO_CATEGORIA[a.tipo]);
  l.append(h("span", "al-hora num", horaCurta(a.at)), h("b", "al-uf", a.uf ?? "BR"), tag, h("span", "al-texto", a.texto));
  return l;
}

export function criarAlertas() {
  let lista: HTMLElement | null = null;
  let contagem: HTMLElement | null = null;
  return criarTela2T({
    id: "alertas",
    dwell: 16,
    needs: () => [{ tipo: "anomalias" }, { tipo: "estado" }],
    montar(p) {
      p.corpo.innerHTML = `<div class="al"><ol class="al-lista"></ol></div>`;
      lista = p.corpo.querySelector<HTMLElement>(".al-lista");
      p.painel.classList.add("painel--2t");
      contagem = h("div", "al-painel");
      p.painel.append(contagem);
    },
    chips: s => [chipAndamento(s.estado?.br.pst ?? 0, false)],
    entradas: s => [s.anomalias],
    atualizar(s) {
      if (!lista || !contagem) return;
      const todas = s.anomalias;
      const recentes = maisRecentes(todas, VISIVEIS);
      lista.replaceChildren(...(recentes.length > 0 ? recentes.map(linha) : [h("li", "d2-vazio", "nenhum alerta até agora")]));
      const c = contarPorCategoria(todas);
      const ul = h("ul", "al-cont");
      for (const k of CATEGORIAS) {
        const li = h("li", c[k] === 0 ? "al-cont--zero" : "");
        li.style.setProperty("--cor", COR_CATEGORIA[k]);
        li.append(h("i", "al-cont-ponto"), h("span", "al-cont-rot", ROTULO_CATEGORIA[k]), h("b", "al-cont-n num", inteiro(c[k])));
        ul.append(li);
      }
      contagem.replaceChildren(
        h("h2", "al-h", `${inteiro(todas.length)} ${todas.length === 1 ? "alerta" : "alertas"} na noite`),
        ul,
        h("p", "d2-nota", `${ROTULO_ATRASO}; ${ROTULO_ABSTENCAO}; ${ROTULO_PAUSA}`),
      );
    },
    desmontar() {
      lista = null;
      contagem = null;
    },
  });
}
