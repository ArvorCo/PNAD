// Mensagens rotativas da faixa inferior: anomalias do servidor ("virada no PR",
// "Sergipe fechou às 19:38") e, sem elas, o andamento.

import { horaCurta, pct } from "../data/format.ts";
import type { State } from "../state/types.ts";

const PASSO_MS = 7000;

export function mensagens(s: State): string[] {
  const saida: string[] = [];
  // Eventos operacionais (cópia velha do CDN, drift de esquema) ficam no banco e fora do ar.
  const noAr = s.anomalias.filter(a => a.tipo_bruto !== "idg_regressivo");
  for (const a of noAr.slice(0, 12)) if (a.texto) saida.push(a.texto);
  const nomes = new Map((s.config?.ufs ?? []).map(u => [u.uf.toUpperCase(), u.nome]));
  const fechadas = (s.estado?.ufs ?? [])
    .filter(u => u.fechou_em)
    .sort((a, b) => String(b.fechou_em).localeCompare(String(a.fechou_em)))
    .slice(0, 3);
  for (const u of fechadas) {
    const t = `${nomes.get(u.uf.toUpperCase()) ?? u.uf} fechou às ${horaCurta(u.fechou_em)}`;
    if (!saida.includes(t)) saida.push(t);
  }
  if (saida.length === 0) {
    const br = s.estado?.br;
    if (!br) saida.push("aguardando o primeiro arquivo do TSE");
    else if (br.st === 0) saida.push("nenhuma seção totalizada ainda; a divulgação começa às 17:00");
    else saida.push(`apuração em andamento: ${pct(br.pst, 2)} das seções totalizadas`);
  }
  return saida;
}

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
  let lista: string[] = [];
  let i = 0;

  const mostrar = (): void => {
    const m = lista[i % Math.max(1, lista.length)] ?? "";
    if (texto.textContent === m) return;
    texto.classList.add("saindo");
    setTimeout(() => {
      texto.textContent = m;
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
      const nova = mensagens(s);
      const mudou = nova.length !== lista.length || nova.some((m, k) => m !== lista[k]);
      if (!mudou) return;
      const atual = lista[i];
      lista = nova;
      const k = atual ? lista.indexOf(atual) : -1;
      i = k >= 0 ? k : 0;
      if (!texto.textContent) texto.textContent = lista[i] ?? "";
      else mostrar();
    },
    parar: () => clearInterval(timer),
  };
}
