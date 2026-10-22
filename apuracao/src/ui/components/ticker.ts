// Mensagens rotativas da faixa inferior: anomalias do servidor ("virada no PR",
// "Sergipe fechou às 19:38") e, sem elas, o andamento.

import { NOVAS_CATEGORIAS } from "../data/categorias.ts";
import type { Categoria } from "../data/categorias.ts";
import { horaCurta, pct } from "../data/format.ts";
import type { State } from "../state/types.ts";

const PASSO_MS = 7000;

export interface ItemTicker {
  texto: string;
  /** Categoria das anomalias novas do 2º turno (pausa, divergência, abstenção, paralela): ganham cor própria. */
  categoria: Categoria | null;
}

export function itensTicker(s: State): ItemTicker[] {
  const saida: ItemTicker[] = [];
  // Eventos operacionais (cópia velha do CDN, drift de esquema) ficam no banco e fora do ar.
  const noAr = s.anomalias.filter(a => a.tipo_bruto !== "idg_regressivo");
  for (const a of noAr.slice(0, 12)) if (a.texto) saida.push({ texto: a.texto, categoria: NOVAS_CATEGORIAS.has(a.tipo) ? a.tipo : null });
  const nomes = new Map((s.config?.ufs ?? []).map(u => [u.uf.toUpperCase(), u.nome]));
  const fechadas = (s.estado?.ufs ?? [])
    .filter(u => u.fechou_em)
    .sort((a, b) => String(b.fechou_em).localeCompare(String(a.fechou_em)))
    .slice(0, 3);
  for (const u of fechadas) {
    const t = `${nomes.get(u.uf.toUpperCase()) ?? u.uf} fechou às ${horaCurta(u.fechou_em)}`;
    if (!saida.some(i => i.texto === t)) saida.push({ texto: t, categoria: null });
  }
  if (saida.length === 0) {
    const br = s.estado?.br;
    if (!br) saida.push({ texto: "aguardando o primeiro arquivo do TSE", categoria: null });
    else if (br.st === 0) saida.push({ texto: "nenhuma seção totalizada ainda; a divulgação começa às 17:00", categoria: null });
    else saida.push({ texto: `apuração em andamento: ${pct(br.pst, 2)} das seções totalizadas`, categoria: null });
  }
  return saida;
}

export const mensagens = (s: State): string[] => itensTicker(s).map(i => i.texto);

export interface Ticker {
  el: HTMLElement;
  atualizar(s: State): void;
  parar(): void;
}

export function criarTicker(): Ticker {
  const el = document.createElement("div");
  el.className = "ticker";
  el.innerHTML = `<span class="ticker-marca">agora</span><span class="ticker-texto"></span>`;
  const texto = el.querySelector(".ticker-texto") as HTMLElement;
  const marca = el.querySelector(".ticker-marca") as HTMLElement;
  let lista: ItemTicker[] = [];
  let i = 0;

  const pintar = (item: ItemTicker | undefined): void => {
    texto.textContent = item?.texto ?? "";
    for (const alvo of [texto, marca]) {
      if (item?.categoria) alvo.dataset.cat = item.categoria;
      else delete alvo.dataset.cat;
    }
  };

  const mostrar = (): void => {
    const m = lista[i % Math.max(1, lista.length)];
    if (texto.textContent === (m?.texto ?? "")) return;
    texto.classList.add("saindo");
    setTimeout(() => {
      pintar(m);
      texto.classList.remove("saindo");
    }, 300);
  };

  const timer = setInterval(() => {
    if (lista.length > 1) {
      i = (i + 1) % lista.length;
      mostrar();
    }
  }, PASSO_MS);

  return {
    el,
    atualizar(s) {
      const nova = itensTicker(s);
      const mudou = nova.length !== lista.length || nova.some((m, k) => m.texto !== lista[k]?.texto);
      if (!mudou) return;
      const atual = lista[i]?.texto;
      lista = nova;
      const k = atual ? lista.findIndex(m => m.texto === atual) : -1;
      i = k >= 0 ? k : 0;
      if (!texto.textContent) pintar(lista[i]);
      else mostrar();
    },
    parar: () => clearInterval(timer),
  };
}
