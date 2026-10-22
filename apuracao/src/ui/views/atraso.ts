// Tela "atraso": quem está lerdo. As oito UFs mais atrasadas contra o 1º turno, com as barras
// de seções totalizadas do 1T e do 2T no mesmo relógio; no painel, os maiores municípios ainda
// abertos no país e as UFs que devem fechar por último (p100 do 1º turno mais o atraso de agora).
// Sem régua do 1º turno: mostra as oito mais lentas só pelo avanço, e diz isso.

import { chip, chipAndamento } from "../components/chip.ts";
import { compacto, inteiro, pct } from "../data/format.ts";
import type { UfLinha } from "../data/doist.ts";
import { atualizarAviso, criarTela2T, dados, esvaziar, h, montarComAviso, ROTULO_ATRASO, rodape, SEM_REGUA } from "./doist-ui.ts";
import { fechamPorUltimo, hhmmDeMin, municipiosAbertos, rotuloAtraso, topAtraso, ufsMaisLentas } from "./doist-util.ts";

const TOP = 8;

function trilho(rotulo: string, valor: number, classe: string): HTMLElement {
  const t = h("div", `at-trilho ${classe}`);
  const b = h("span", "at-b");
  const i = document.createElement("i");
  i.style.width = `${Math.max(0, Math.min(100, valor))}%`;
  b.append(i);
  t.append(h("span", "at-rot", rotulo), b, h("span", "at-val num", pct(valor, 1)));
  return t;
}

function linha(u: UfLinha, comRegua: boolean): HTMLElement {
  const l = h("div", "at-linha");
  const sg = h("b", "at-sg", u.uf);
  sg.title = u.nome;
  const barras = h("div", "at-barras");
  if (comRegua && u.ref_1t) barras.append(trilho("1T", u.ref_1t.pst_mesmo_relogio, "at-trilho--1t"));
  barras.append(trilho("2T", u.pst, "at-trilho--2t"));
  const min = u.ref_1t?.atraso_min ?? null;
  const at = h("span", `at-atraso num${min !== null && min >= 20 ? " at-atraso--alto" : ""}`, comRegua && u.ref_1t ? rotuloAtraso(min) : "");
  l.append(sg, barras, at);
  return l;
}

export function criarAtraso() {
  let palco: HTMLElement | null = null;
  let lado: HTMLElement | null = null;
  return criarTela2T({
    id: "atraso",
    dwell: 20,
    needs: () => [{ tipo: "doist", rota: "ufs" }, { tipo: "estado" }],
    montar(p) {
      palco = montarComAviso(p.corpo, "at", `<p class="at-sub"></p><div class="at-linhas"></div><p class="d2-rodape"></p>`);
      palco.querySelector(".d2-rodape")?.replaceWith(rodape(ROTULO_ATRASO));
      p.painel.classList.add("painel--2t");
      lado = h("div", "at-painel");
      p.painel.append(lado);
    },
    chips(s) {
      const r = dados(s, "ufs");
      const semRegua = !!r && !r.ufs.some(u => u.ref_1t);
      return [chipAndamento(s.estado?.br.pst ?? 0, false), semRegua ? chip(SEM_REGUA, "aviso") : null];
    },
    entradas: s => [s.doist.ufs],
    atualizar(s, p) {
      if (!palco || !lado) return;
      const r = dados(s, "ufs");
      if (!atualizarAviso(p.corpo, s, "ufs", "Atraso") || !r) {
        esvaziar(lado);
        return;
      }
      const comRegua = r.ufs.some(u => u.ref_1t);
      const sub = palco.querySelector<HTMLElement>(".at-sub");
      const lista = palco.querySelector<HTMLElement>(".at-linhas");
      if (!sub || !lista) return;
      const t0 = Date.parse(r.at) - r.min * 60000;
      const escolhidas = comRegua ? topAtraso(r.ufs, TOP) : ufsMaisLentas(r.ufs.filter(u => u.ts > 0 && u.st < u.ts)).slice(0, TOP);
      sub.textContent = comRegua
        ? "as oito UFs mais atrasadas contra o 1º turno, no mesmo relógio"
        : `${SEM_REGUA}: as oito UFs mais lentas pelo avanço das seções`;
      lista.replaceChildren(
        ...(escolhidas.length > 0 ? escolhidas.map(u => linha(u, comRegua)) : [h("p", "d2-vazio", "nenhuma UF com seções totalizadas ainda")]),
      );

      const munis = municipiosAbertos(r.ufs, 6);
      const ultimos = comRegua ? fechamPorUltimo(r.ufs, t0, 5) : [];
      lado.replaceChildren(
        h("h2", "at-h", "maiores municípios ainda abertos"),
        munis.length > 0
          ? (() => {
              const ol = h("ol", "at-lista");
              for (const m of munis) {
                const li = h("li", "at-item");
                li.append(h("span", "at-item-nome corte", `${m.nm}, ${m.uf}`), h("span", "at-item-v num", `${inteiro(m.pst)}% · ${compacto(m.te)}`));
                ol.append(li);
              }
              return ol;
            })()
          : h("p", "d2-vazio", "nenhum município aberto"),
        h("h2", "at-h", "devem fechar por último"),
        ultimos.length > 0
          ? (() => {
              const ol = h("ol", "at-lista");
              for (const x of ultimos) {
                const li = h("li", "at-item");
                li.append(h("span", "at-item-nome corte", x.u.nome), h("span", "at-item-v num", hhmmDeMin(x.min)));
                ol.append(li);
              }
              return ol;
            })()
          : h("p", "d2-vazio", comRegua ? "nenhuma UF com previsão ainda" : SEM_REGUA),
        h("p", "d2-nota", "previsão pelo ritmo do 1º turno mais o atraso de agora; muda a cada leitura"),
      );
    },
    desmontar() {
      palco = null;
      lado = null;
    },
  });
}
