// HUD 300 × 44 na faixa inferior: modo, posição na playlist, rede e hora da última leitura.

import { hora } from "../data/format.ts";
import type { State } from "../state/types.ts";

export interface Hud {
  el: HTMLElement;
  atualizar(s: State, total: number): void;
}

export function criarHud(): Hud {
  const el = document.createElement("div");
  el.className = "hud";
  el.setAttribute("aria-live", "off");
  el.innerHTML = `<span class="hud-ponto"></span><span class="hud-modo"></span><span class="hud-pos"></span><span class="hud-hora"></span>`;
  const modo = el.querySelector(".hud-modo") as HTMLElement;
  const pos = el.querySelector(".hud-pos") as HTMLElement;
  const h = el.querySelector(".hud-hora") as HTMLElement;
  return {
    el,
    atualizar(s, total) {
      el.hidden = !s.ui.hud;
      el.dataset.rede = s.rede.modo;
      // Divergência da paralela nas últimas 2 h do relógio da apuração acende o ponto do HUD.
      const agora = Date.parse(s.estado?.agora ?? "") || Date.now();
      const alerta = s.anomalias.some(a => a.tipo === "divergencia" && agora - Date.parse(a.at) < 2 * 3_600_000);
      if (alerta) el.dataset.alerta = "divergencia";
      else delete el.dataset.alerta;
      modo.textContent = s.ui.pausado ? "pausa" : s.ui.auto ? "auto" : "manual";
      pos.textContent = total > 0 && s.ui.auto ? `${s.ui.indice + 1}/${total}` : "";
      const ultimo = s.rede.ultimo_ok_em;
      h.textContent = ultimo ? hora(ultimo) : "sem dado";
      el.title = `rede: ${s.rede.modo}${s.rede.conectado ? "" : ", desconectado"}`;
    },
  };
}
