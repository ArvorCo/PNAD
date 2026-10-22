// Tela "regioes": as cinco regiões e o exterior em seis faixas. Cada faixa mostra o duelo
// em % dos válidos, as seções totalizadas, a abstenção, o ritmo e o atraso contra o 1º turno;
// a região mais lenta ganha destaque. O painel soma o Brasil.

import { chip, chipAndamento } from "../components/chip.ts";
import { decimal, horaCurta, inteiro, pct } from "../data/format.ts";
import type { Agregado } from "../data/doist.ts";
import { atualizarAviso, barra, criarTela2T, dados, dueloDe, esvaziar, h, montarComAviso, ROTULO_ATRASO, rodape, SEM_REGUA, texto } from "./doist-ui.ts";
import type { Duelo } from "./doist-ui.ts";
import { atrasoDaCelula, regiaoMaisLenta, rotuloAtraso, rotuloPp } from "./doist-util.ts";
import { eleicaoDe } from "./executivo.ts";
import { chaveResultado } from "../state/types.ts";

/** % dos válidos de cada lado do duelo numa unidade agregada (null sem votos). */
export function pctDuelo(a: Agregado, d: Duelo): { a: number; b: number } | null {
  const va = a.votos[d.a.sqcand]?.pvapn;
  const vb = a.votos[d.b.sqcand]?.pvapn;
  if (va === undefined || vb === undefined || a.vv <= 0) return null;
  return { a: va, b: vb };
}

function textoDuelo(a: Agregado, d: Duelo | null): string {
  if (!d) return "";
  const p = pctDuelo(a, d);
  if (!p) return "sem votos totalizados";
  const dif = p.a - p.b;
  if (Math.abs(dif) < 0.05) return "empate técnico";
  return `${dif > 0 ? d.a.nome : d.b.nome} ${rotuloPp(Math.abs(dif))} na frente`;
}

export function criarRegioes() {
  let linhas: HTMLElement | null = null;
  let painel: HTMLElement | null = null;
  const nos = new Map<string, HTMLElement>();

  return criarTela2T({
    id: "regioes",
    dwell: 22,
    needs: s => [
      { tipo: "doist", rota: "regioes" },
      { tipo: "resultado", ele: eleicaoDe(s, 1), cargo: 1, abr: "br" },
      { tipo: "estado" },
    ],
    montar(p) {
      montarComAviso(p.corpo, "rg", `<div class="rg-linhas"></div>`);
      linhas = p.corpo.querySelector<HTMLElement>(".rg-linhas");
      p.painel.classList.add("painel--2t");
      painel = h("div", "rg-painel");
      p.painel.append(painel);
    },
    chips(s) {
      const r = dados(s, "regioes");
      return [chipAndamento(r?.brasil.pst ?? s.estado?.br.pst ?? 0, false), r && !r.referencia_1t ? chip(SEM_REGUA, "aviso") : null];
    },
    entradas: s => [s.doist.regioes, s.resultados[chaveResultado(eleicaoDe(s, 1), 1, "br")], s.cores],
    atualizar(s, p) {
      if (!linhas || !painel) return;
      const r = dados(s, "regioes");
      if (!atualizarAviso(p.corpo, s, "regioes", "Regiões") || !r) {
        esvaziar(painel);
        return;
      }
      const duelo = dueloDe(s);
      const lenta = regiaoMaisLenta(r.regioes);
      for (const reg of r.regioes) {
        let no = nos.get(reg.sigla);
        if (!no) {
          no = criarLinha(reg.sigla);
          nos.set(reg.sigla, no);
          linhas.append(no);
        }
        preencherLinha(no, reg, duelo, lenta?.sigla === reg.sigla, r.referencia_1t);
      }
      desenharPainel(painel, r.brasil, duelo, lenta, r.referencia_1t);
    },
    desmontar() {
      nos.clear();
      linhas = null;
      painel = null;
    },
  });
}

function criarLinha(sigla: string): HTMLElement {
  const l = h("div", "rg-linha");
  l.dataset.r = sigla;
  l.innerHTML = `
    <div class="rg-nome"><b></b><span class="rg-pst num"></span><span class="d2-barra"><i></i></span></div>
    <div class="rg-duelo">
      <div class="rg-barra"><i class="rg-a"></i><i class="rg-b"></i><span class="rg-va num"></span><span class="rg-vb num"></span></div>
      <span class="rg-margem"></span>
    </div>
    <div class="rg-meta">
      <span class="rg-abst num"></span>
      <span class="rg-vel num"></span>
      <span class="rg-atraso chip"></span>
    </div>`;
  return l;
}

function preencherLinha(l: HTMLElement, r: Agregado, d: Duelo | null, lenta: boolean, comRegua: boolean): void {
  const q = <T extends HTMLElement>(c: string): T => l.querySelector<T>(c) as T;
  l.classList.toggle("rg-linha--lenta", lenta);
  texto(q("b"), r.nome);
  texto(q(".rg-pst"), r.ts > 0 ? `${pct(r.pst, 1)} das seções` : "sem seções");
  q<HTMLElement>(".d2-barra > i").style.width = `${Math.max(0, Math.min(100, r.pst))}%`;
  const p = d ? pctDuelo(r, d) : null;
  const a = q<HTMLElement>(".rg-a");
  const b = q<HTMLElement>(".rg-b");
  const soma = p ? p.a + p.b : 0;
  a.style.width = p && soma > 0 ? `${(100 * p.a) / soma}%` : "50%";
  b.style.width = p && soma > 0 ? `${(100 * p.b) / soma}%` : "50%";
  a.style.background = d?.a.cor ?? "#8a8f98";
  b.style.background = d?.b.cor ?? "#8a8f98";
  q(".rg-barra").classList.toggle("vazia", !p);
  texto(q(".rg-va"), p ? decimal(p.a, 1) : "");
  texto(q(".rg-vb"), p ? decimal(p.b, 1) : "");
  texto(q(".rg-margem"), textoDuelo(r, d));
  texto(q(".rg-abst"), r.comparecimento + r.abstencao > 0 ? `abstenção ${pct(r.pa, 1)}` : "abstenção sem dado");
  texto(q(".rg-vel"), r.st >= r.ts && r.ts > 0 ? "encerrada" : `${inteiro(r.vel_10min_spm)} seções/min`);
  const at = q(".rg-atraso");
  const min = r.ref_1t?.atraso_min ?? null;
  texto(at, atrasoDaCelula(comRegua && !!r.ref_1t, min));
  at.classList.toggle("chip--atraso", min !== null && min >= 20);
  at.classList.toggle("chip--neutro", !(min !== null && min >= 20));
}

function desenharPainel(alvo: HTMLElement, br: Agregado, d: Duelo | null, lenta: Agregado | null, comRegua: boolean): void {
  const p = d ? pctDuelo(br, d) : null;
  const eta = br.eta_100_iso ? `100% previsto às ${horaCurta(br.eta_100_iso)}` : br.st >= br.ts && br.ts > 0 ? "todas as seções totalizadas" : "sem previsão de 100%";
  const refTxt =
    comRegua && br.ref_1t
      ? `No 1º turno, a esta hora: ${pct(br.ref_1t.pst_mesmo_relogio, 1)} das seções (${rotuloAtraso(br.ref_1t.atraso_min)}).`
      : `${SEM_REGUA}: a comparação fica de fora.`;
  alvo.replaceChildren(
    h("h2", "rg-h", "Brasil"),
    (() => {
      const duo = h("div", "rg-brasil");
      for (const c of d ? [d.a, d.b] : []) {
        const lado = h("div", "rg-brasil-lado");
        lado.style.setProperty("--cor", c.cor);
        const v = c === d?.a ? p?.a : p?.b;
        lado.append(h("p", "rg-brasil-nome corte", c.nome), h("p", "rg-brasil-pct num", v === undefined ? "–" : decimal(v, 2)));
        duo.append(lado);
      }
      if (!d) duo.append(h("p", "rg-brasil-nome", "aguardando o resultado nacional"));
      return duo;
    })(),
    h("p", "rg-linha-info", `${pct(br.pst, 2)} das seções totalizadas (${inteiro(br.st)} de ${inteiro(br.ts)})`),
    barra(br.pst, "d2-barra--grande"),
    h("p", "rg-linha-info", `${inteiro(br.vel_10min_spm)} seções por minuto nos últimos 10 minutos`),
    h("p", "rg-linha-info", eta),
    h("p", "rg-linha-info", br.pa > 0 ? `abstenção até agora ${pct(br.pa, 1)}` : "abstenção ainda sem dado"),
    h("p", "rg-ref", refTxt),
    lenta
      ? (() => {
          const e = h("div", "rg-lenta");
          e.append(
            h("p", "rg-lenta-rot", "região mais lenta"),
            h("p", "rg-lenta-nome", `${lenta.nome}, ${pct(lenta.pst, 1)}`),
            h("p", "rg-lenta-nota", lenta.ref_1t && comRegua ? `${rotuloAtraso(lenta.ref_1t.atraso_min)} contra o 1º turno` : SEM_REGUA),
          );
          return e;
        })()
      : h("p", "rg-ref", ""),
    rodape(ROTULO_ATRASO),
  );
}
