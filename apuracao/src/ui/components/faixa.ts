// Faixa superior: ao vivo, tela atual, % de seções, horas do TSE e da leitura, atraso.

import { hora, pct, duracao } from "../data/format.ts";
import type { State } from "../state/types.ts";

const LIMITE_ATRASO_S = 180;

export interface Faixa {
  el: HTMLElement;
  atualizar(s: State, titulo: string): void;
}

export function criarFaixa(): Faixa {
  const el = document.createElement("header");
  el.className = "faixa";
  el.innerHTML = `
    <div class="faixa-vivo"><span class="faixa-pulso"></span><span class="faixa-modo">ao vivo</span></div>
    <div class="faixa-tela corte"></div>
    <div class="faixa-secoes"><span>seções</span><span class="faixa-barra"><i></i></span><span class="faixa-pct num"></span></div>
    <div class="faixa-horas num">
      <span class="h-tse">totalização <b></b></span>
      <span class="h-arq">arquivo <b></b></span>
      <span class="h-lido">leitura <b></b></span>
      <span class="h-atraso">atraso <b></b></span>
    </div>`;
  const q = <T extends HTMLElement>(s: string): T => el.querySelector<T>(s) as T;
  const modo = q(".faixa-modo");
  const tela = q(".faixa-tela");
  const barra = q<HTMLElement>(".faixa-barra > i");
  const pctEl = q(".faixa-pct");
  const tse = q(".h-tse b");
  const arq = q(".h-arq b");
  const lido = q(".h-lido b");
  const atrasoBox = q(".h-atraso");
  const atraso = q(".h-atraso b");

  return {
    el,
    atualizar(s, titulo) {
      const r = s.rede.modo;
      el.dataset.rede = r;
      modo.textContent = r === "mock" ? "ensaio" : r === "replay" ? "replay" : r === "polling" ? "ao vivo, sondando" : "ao vivo";
      tela.textContent = titulo;
      const br = s.estado?.br;
      const p = br?.pst ?? 0;
      barra.style.width = `${Math.min(100, Math.max(0, p))}%`;
      pctEl.textContent = br ? pct(p, 2) : "sem dado";
      tse.textContent = hora(br?.dt_ht) || "aguardando";
      arq.textContent = hora(br?.hg) || "aguardando";
      // Leitura = última requisição ao arquivo nacional, mudado ou não: prova que o coletor está vivo.
      lido.textContent = hora(br?.ultima_leitura_em ?? br?.lido_em) || "aguardando";
      // Atraso = leitura menos geração da última versão gravada. Antes da primeira seção
      // totalizada a última versão é a da véspera e o número não significa nada.
      const comecou = (br?.st ?? 0) > 0;
      const a = br?.atraso_s;
      atraso.textContent = !comecou ? "aguardando" : a === null || a === undefined ? "sem dado" : duracao(a);
      atrasoBox.classList.toggle("atrasado", comecou && (a ?? 0) > LIMITE_ATRASO_S);
    },
  };
}
