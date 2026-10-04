// Barra empilhada de válidos, brancos e nulos (parcelas do total de votos) e a linha
// de comparecimento e abstenção do recorte.

import { compacto, pct } from "../data/format.ts";
import { composicaoVotos } from "../state/selectors.ts";
import type { Resultado } from "../state/types.ts";

export interface Participacao {
  comparecimento: number; // 0 a 100
  abstencao: number;
  comparecem: number;
}

/** Comparecimento e abstenção sobre o eleitorado das seções totalizadas. */
export function participacao(e: Resultado["e"]): Participacao | null {
  const base = e.c + e.a;
  if (base > 0) return { comparecimento: (100 * e.c) / base, abstencao: (100 * e.a) / base, comparecem: e.c };
  if (e.pc > 0) return { comparecimento: e.pc, abstencao: e.pa, comparecem: e.c };
  return null;
}

export interface BarraValidos {
  readonly el: HTMLElement;
  update(r: Resultado | null): void;
}

export function criarBarraValidos(): BarraValidos {
  const el = document.createElement("div");
  el.className = "bvalidos";
  el.innerHTML = `
    <div class="bvalidos-barra" aria-hidden="true"><i class="bv-v"></i><i class="bv-b"></i><i class="bv-n"></i></div>
    <p class="bvalidos-rotulos"><span class="bv-rv"></span><span class="bv-rb"></span><span class="bv-rn"></span></p>
    <p class="bvalidos-part"></p>`;
  const q = (s: string): HTMLElement => el.querySelector<HTMLElement>(s) as HTMLElement;
  const v = q(".bv-v");
  const b = q(".bv-b");
  const n = q(".bv-n");
  const rv = q(".bv-rv");
  const rb = q(".bv-rb");
  const rn = q(".bv-rn");
  const part = q(".bvalidos-part");

  return {
    el,
    update(r) {
      const c = r ? composicaoVotos(r.v) : null;
      const vazio = !c || !(c.total > 0);
      el.classList.toggle("bvalidos--vazio", vazio);
      v.style.width = `${vazio ? 0 : c.validos}%`;
      b.style.width = `${vazio ? 0 : c.brancos}%`;
      n.style.width = `${vazio ? 0 : c.nulos}%`;
      if (vazio) {
        rv.textContent = "nenhum voto totalizado ainda neste recorte";
        rb.textContent = "";
        rn.textContent = "";
      } else {
        rv.textContent = `válidos ${pct(c.validos)}`;
        rb.textContent = `brancos ${pct(c.brancos)}`;
        rn.textContent = `nulos ${pct(c.nulos)}`;
      }
      const p = r ? participacao(r.e) : null;
      part.textContent = p
        ? `comparecimento ${pct(p.comparecimento)} (${compacto(p.comparecem)}), abstenção ${pct(p.abstencao)}`
        : "comparecimento ainda sem seções totalizadas";
    },
  };
}
