// Mensagens rotativas da faixa inferior: anomalias do servidor ("virada no PR",
// "Sergipe fechou às 19:38") e, sem elas, o andamento.

import { NOVAS_CATEGORIAS } from "../data/categorias.ts";
import type { Categoria } from "../data/categorias.ts";
import { horaCurta, pct } from "../data/format.ts";
import type { State } from "../state/types.ts";

const PASSO_MS = 7000;

/** Evento de documento com o boletim falado (disparado pelo main a partir do SSE). */
export const EVENTO_BOLETIM = "apuracao:boletim";

interface DetalheBoletim {
  kind: string;
  id: string;
  hora?: string;
  desde?: string;
  duracao_s?: number | null;
}

/** Chip "boletim das HH:MM no ar" na faixa inferior enquanto o boletim toca; some no fim. */
function criarChipBoletim(): HTMLElement {
  const chip = document.createElement("span");
  chip.className = "ticker-boletim";
  chip.hidden = true;
  let atual: string | null = null;
  let timer: ReturnType<typeof setTimeout> | null = null;
  const apagar = (): void => {
    chip.hidden = true;
    atual = null;
    if (timer !== null) clearTimeout(timer);
    timer = null;
  };
  document.addEventListener(EVENTO_BOLETIM, ev => {
    const d = (ev as CustomEvent<DetalheBoletim>).detail;
    if (!d) return;
    if (d.kind === "no_ar") {
      atual = d.id;
      chip.textContent = `boletim das ${d.hora ?? `${d.id.slice(0, 2)}:${d.id.slice(2, 4)}`} no ar`;
      chip.hidden = false;
      if (timer !== null) clearTimeout(timer);
      // Rede de segurança: sem o evento de fim, o chip some ao fim previsto do áudio.
      const resta = (d.duracao_s ?? 600) * 1000 - (Date.now() - Date.parse(d.desde ?? new Date().toISOString())) + 5000;
      timer = setTimeout(apagar, Math.max(1000, resta));
    } else if ((d.kind === "fim" || d.kind === "descartado") && d.id === atual) apagar();
  });
  return chip;
}

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
  el.prepend(criarChipBoletim());
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
