// Tela de espera: antes das 17:00 de Brasília ou enquanto nenhuma seção foi totalizada.
// Contagem regressiva em Plex Mono, eleitorado e seções, próximas telas da playlist.
// A rotação fica parada até o primeiro st > 0 (control/rotation.ts).

import { compacto, dezessete, inteiro, regressiva } from "../data/format.ts";
import { expandirPlaylist } from "../control/rotation.ts";
import type { Diff, State } from "../state/types.ts";
import type { View } from "./registry.ts";
import { partes, nomeUf } from "./registry.ts";
import { corPorBanda, textoSobre } from "../data/cores.ts";

/**
 * Instante atual (ms epoch) na referência do servidor ou do relógio simulado, extrapolado
 * desde o último estado. `recebidoEm` e `agoraMonotonico` vêm de performance.now().
 * Sem estado, usa o relógio da máquina.
 */
export function relogioDaTela(s: State, recebidoEm: number, agoraMonotonico: number, epoch = Date.now()): number {
  if (!s.estado) return epoch;
  const ritmo = s.ui.mock ? s.ui.speed : s.ui.replay ? s.ui.replay.speed : 1;
  return Date.parse(s.estado.agora) + (agoraMonotonico - recebidoEm) * ritmo;
}

export function criarEspera(titulos: (id: string, s: State, uf: string | null) => string): View {
  let raiz: HTMLElement | null = null;
  let timer: ReturnType<typeof setInterval> | null = null;
  let ultimo: State | null = null;
  let ultimoAgora = "";
  let recebidoEm = performance.now();
  let contagem: HTMLElement | null = null;
  let rotulo: HTMLElement | null = null;

  const tique = (): void => {
    const s = ultimo;
    if (!s || !contagem || !rotulo) return;
    const agora = relogioDaTela(s, recebidoEm, performance.now());
    const alvo = dezessete(new Date(agora)).getTime();
    const falta = (alvo - agora) / 1000;
    if (falta > 0) {
      rotulo.textContent = "a divulgação dos resultados começa às 17:00 de Brasília";
      contagem.textContent = regressiva(falta);
    } else {
      rotulo.textContent = "aguardando as primeiras seções totalizadas pelo TSE";
      contagem.textContent = "17:00";
    }
  };

  return {
    id: "espera",
    dwell: 30,
    titulo: () => "Apuração 2026, primeiro turno",
    needs: () => [{ tipo: "estado" }],
    mount(el) {
      raiz = el;
      el.classList.add("tela--cheia");
      const p = partes(el);
      p.corpo.innerHTML = `
        <div class="espera">
          <div class="espera-relogio">
            <p class="espera-rotulo"></p>
            <p class="espera-contagem" aria-live="off">00:00</p>
            <div class="espera-numeros">
              <p>eleitorado<b class="e-te">aguardando</b></p>
              <p>seções<b class="e-ts">aguardando</b></p>
              <p>municípios<b class="e-mun">aguardando</b></p>
            </div>
            <div class="espera-grade" aria-label="estados"></div>
          </div>
          <aside class="espera-lado">
            <h2>a seguir no telão</h2>
            <ol class="espera-lista"></ol>
          </aside>
        </div>`;
      contagem = el.querySelector(".espera-contagem");
      rotulo = el.querySelector(".espera-rotulo");
      timer = setInterval(tique, 250);
    },
    update(s: State, _diff: Diff) {
      if (!raiz) return;
      ultimo = s;
      if (s.estado && s.estado.agora !== ultimoAgora) {
        ultimoAgora = s.estado.agora;
        recebidoEm = performance.now();
      }
      const q = (c: string): HTMLElement | null => raiz?.querySelector<HTMLElement>(c) ?? null;
      const te = (s.config?.ufs ?? []).reduce((a, u) => a + u.te, 0);
      const teEl = q(".e-te");
      if (teEl) {
        teEl.textContent = te > 0 ? compacto(te) : "aguardando";
        teEl.classList.toggle("vazio-num", !(te > 0));
      }
      const tsEl = q(".e-ts");
      if (tsEl) {
        // Mesmo universo do eleitorado: soma das 27 UFs, sem o exterior (ZZ).
        const ts = s.estado ? s.estado.ufs.filter(u => u.uf !== "ZZ").reduce((a, u) => a + u.ts, 0) : 0;
        tsEl.textContent = ts > 0 ? inteiro(ts) : "aguardando";
        tsEl.classList.toggle("vazio-num", !(ts > 0));
      }
      const munEl = q(".e-mun");
      // Mesmo universo do eleitorado (27 UFs): as cidades do exterior (ZZ) ficam fora.
      const nMun = Object.entries(s.config?.municipios ?? {}).reduce((a, [uf, l]) => (uf === "ZZ" ? a : a + l.length), 0);
      if (munEl) {
        munEl.textContent = nMun > 0 ? inteiro(nMun) : "aguardando";
        munEl.classList.toggle("vazio-num", !(nMun > 0));
      }

      const grade = q(".espera-grade");
      if (grade) {
        const pst = new Map((s.estado?.ufs ?? []).map(u => [u.uf.toUpperCase(), u.pst]));
        const ufs = [...(s.config?.ufs ?? [])].map(u => u.uf.toUpperCase()).sort();
        if (grade.childElementCount !== ufs.length) {
          grade.replaceChildren(
            ...ufs.map(uf => {
              const sp = document.createElement("span");
              sp.dataset.uf = uf;
              sp.textContent = uf;
              sp.title = nomeUf(s, uf);
              return sp;
            }),
          );
        }
        for (const sp of grade.querySelectorAll<HTMLElement>("span")) {
          const fundo = corPorBanda("#0f7f5f", pst.get(sp.dataset.uf ?? "") ?? 0);
          sp.style.backgroundColor = fundo;
          sp.style.color = textoSobre(fundo);
        }
      }

      const lista = q(".espera-lista");
      if (lista) {
        const entradas = expandirPlaylist(s.playlist, s.estado, s.config, s.ui.dwell).slice(0, 9);
        const itens = entradas.length > 0 ? entradas : [];
        lista.replaceChildren(
          ...itens.map((e, i) => {
            const li = document.createElement("li");
            const o = document.createElement("span");
            o.className = "ordem";
            o.textContent = String(i + 1);
            const t = document.createElement("span");
            t.className = "corte";
            t.textContent = titulos(e.v, s, e.uf);
            li.append(o, t);
            return li;
          }),
        );
        if (itens.length === 0) lista.innerHTML = `<li>a playlist ainda não foi carregada</li>`;
      }
      tique();
    },
    unmount() {
      if (timer !== null) clearInterval(timer);
      timer = null;
      raiz = null;
      contagem = null;
      rotulo = null;
    },
  };
}
