// Tela "ritmo": seções totalizadas no país desde as 17:00, seções por minuto nos últimos
// 10 minutos (herói), previsão ingênua de 100% pela reta desses 10 minutos, histogramas
// de latência (leitura menos geração do arquivo e geração menos totalização) e as 27 UFs
// por seções totalizadas, as mais lentas no topo.

import { chipAndamento, trocarChips } from "../components/chip.ts";
import { criarLinhas, ritmoRecente, ticksRedondos } from "../components/linhas.ts";
import type { Linhas, Ponto, SerieLinha, Tick } from "../components/linhas.ts";
import { compacto, decimal, dezessete, duracao, horaCurta, inteiro, pct } from "../data/format.ts";
import type { Estado, Need, State } from "../state/types.ts";
import type { View } from "./registry.ts";
import { nomeUf, partes } from "./registry.ts";

const MIN = 60_000;
const JANELA = 10 * MIN;
const COR_LINHA = "#0f7f5f";
const LARGURA = 1152;
const ALTURA = 600;

/** Faixas do histograma de latência, em segundos. */
export const FAIXAS: readonly { ate: number; rotulo: string }[] = [
  { ate: 15, rotulo: "até 15 s" },
  { ate: 30, rotulo: "15 a 30 s" },
  { ate: 60, rotulo: "30 a 60 s" },
  { ate: 120, rotulo: "1 a 2 min" },
  { ate: 180, rotulo: "2 a 3 min" },
  { ate: 300, rotulo: "3 a 5 min" },
  { ate: Infinity, rotulo: "≥ 5 min" },
];

export function histograma(valores: readonly number[]): number[] {
  const c = FAIXAS.map(() => 0);
  for (const v of valores) {
    if (!Number.isFinite(v) || v < 0) continue;
    const i = FAIXAS.findIndex(f => v < f.ate);
    const k = i < 0 ? FAIXAS.length - 1 : i;
    c[k] = (c[k] ?? 0) + 1;
  }
  return c;
}

export function mediana(valores: readonly number[]): number | null {
  const v = valores.filter(Number.isFinite).sort((a, b) => a - b);
  if (v.length === 0) return null;
  const m = Math.floor(v.length / 2);
  return v.length % 2 ? (v[m] ?? null) : ((v[m - 1] ?? 0) + (v[m] ?? 0)) / 2;
}

/** Histórico com o ponto atual do país no fim (x em ms, y em seções). */
export function pontosDoHistorico(e: Estado): Ponto[] {
  const pts = e.historico.map(h => ({ x: Date.parse(h.at), y: h.st })).filter(p => Number.isFinite(p.x));
  const agora = Date.parse(e.agora);
  const ult = pts[pts.length - 1];
  if (Number.isFinite(agora) && (!ult || agora > ult.x)) pts.push({ x: agora, y: e.br.st });
  return pts;
}

export function criarRitmo(): View {
  let raiz: HTMLElement | null = null;
  let grafico: Linhas | null = null;
  let ultimoEstado: Estado | null = null;

  return {
    id: "ritmo",
    dwell: 20,
    titulo: () => "Ritmo da apuração",
    needs: (): Need[] => [{ tipo: "estado" }],
    mount(el) {
      raiz = el;
      const p = partes(el);
      p.corpo.innerHTML = `
        <div class="rt">
          <div class="rt-heroi">
            <div><b class="rt-taxa">0</b><span class="rt-taxa-rot">seções por minuto nos últimos 10 minutos</span></div>
            <div class="rt-prev"><b class="rt-prev-hora"></b><span class="rt-prev-nota"></span><span class="rt-total"></span></div>
          </div>
          <div class="rt-grafico"></div>
        </div>`;
      p.painel.innerHTML = `
        <div class="rt-painel">
          <section><h2 class="rt-h-leitura">leitura menos geração do arquivo</h2><div class="rt-hist rt-hist-leitura"></div></section>
          <section><h2 class="rt-h-geracao">geração do arquivo menos totalização</h2><div class="rt-hist rt-hist-geracao"></div></section>
          <section><h2>seções totalizadas por UF, as mais lentas no topo</h2><ol class="rt-ufs"></ol></section>
        </div>`;
      const g = el.querySelector<HTMLElement>(".rt-grafico");
      if (g) grafico = criarLinhas(g, { largura: LARGURA, altura: ALTURA, margem: { r: 40, l: 112 } });
    },
    update(s: State) {
      if (!raiz) return;
      const p = partes(raiz);
      const e = s.estado;
      trocarChips(p.chips, [chipAndamento(e?.br.pst ?? 0, (e?.br.pst ?? 0) >= 100)]);
      if (!e) {
        const t = raiz.querySelector(".rt-taxa-rot");
        if (t) t.textContent = "aguardando o primeiro estado da apuração";
        return;
      }
      if (e === ultimoEstado) return;
      ultimoEstado = e;
      desenharPalco(raiz, e, grafico);
      desenharPainel(raiz, s, e);
    },
    unmount() {
      grafico?.destroy();
      grafico = null;
      raiz = null;
      ultimoEstado = null;
    },
  };
}

function desenharPalco(raiz: HTMLElement, e: Estado, grafico: Linhas | null): void {
  const q = (c: string): HTMLElement | null => raiz.querySelector<HTMLElement>(c);
  const pts = pontosDoHistorico(e);
  const ts = e.br.ts;
  const r = ritmoRecente(pts, JANELA, ts);
  const taxa = q(".rt-taxa");
  const taxaRot = q(".rt-taxa-rot");
  const prevHora = q(".rt-prev-hora");
  const prevNota = q(".rt-prev-nota");
  const total = q(".rt-total");
  if (taxa) taxa.textContent = r && e.br.st > 0 ? inteiro(Math.max(0, r.porMinuto)) : "0";
  if (taxaRot) taxaRot.textContent = e.br.st > 0 ? "seções por minuto nos últimos 10 minutos" : "nenhuma seção totalizada ainda";
  if (total) total.textContent = `${inteiro(e.br.st)} de ${inteiro(ts)} seções totalizadas`;
  if (prevHora && prevNota) {
    if (e.br.st >= ts && ts > 0) {
      const fim = pts.find(q => q.y >= ts)?.x ?? Date.parse(e.br.dt_ht ?? e.agora);
      prevHora.textContent = `100% às ${horaCurta(fim)}`;
      prevNota.textContent = "todas as seções do país totalizadas";
    } else if (r && r.previsao !== null && e.br.st > 0) {
      prevHora.textContent = `previsão de 100%: ${horaCurta(r.previsao)}`;
      prevNota.textContent = "projeção ingênua, pela reta dos últimos 10 minutos";
    } else {
      prevHora.textContent = "previsão de 100%: sem ritmo";
      prevNota.textContent = "precisa de seções totalizadas em pelo menos dois instantes";
    }
  }
  if (!grafico) return;
  const agora = Date.parse(e.agora);
  const x0 = dezessete(new Date(Number.isFinite(agora) ? agora : Date.now())).getTime();
  const prev = r?.previsao ?? null;
  const fimDados = pts[pts.length - 1]?.x ?? x0 + 60 * MIN;
  const x1 = Math.max(x0 + 60 * MIN, fimDados, prev !== null && prev - fimDados < 6 * 60 * MIN ? prev : fimDados) + 10 * MIN;
  const passoX = x1 - x0 > 4 * 60 * MIN ? 60 * MIN : 30 * MIN;
  const ticksX: Tick[] = [];
  for (let t = x0; t <= x1; t += passoX) ticksX.push({ v: t, texto: horaCurta(t) });
  const y1 = Math.max(ts, 1);
  const ticksY: Tick[] = ticksRedondos(0, y1, 4).map(v => ({ v, texto: compacto(v) }));
  const series: SerieLinha[] = [{ id: "st", cor: COR_LINHA, pontos: pts.filter(p => p.x >= x0) }];
  const ult = pts[pts.length - 1];
  if (prev !== null && ult && ult.y < ts && prev <= x1) {
    series.push({ id: "proj", cor: "#5f6773", pontos: [ult, { x: prev, y: ts }], tracejado: true });
  }
  grafico.update(series, {
    dominioX: [x0, x1],
    dominioY: [0, y1 * 1.04],
    ticksX,
    ticksY,
    area: true,
    referenciaY: ts > 0 ? { v: ts, texto: "100% das seções" } : undefined,
  });
}

function desenharPainel(raiz: HTMLElement, s: State, e: Estado): void {
  const hist = (sel: string, titulo: string, tituloSel: string, valores: readonly number[]): void => {
    const alvo = raiz.querySelector<HTMLElement>(sel);
    const h = raiz.querySelector<HTMLElement>(tituloSel);
    if (!alvo || !h) return;
    const med = mediana(valores);
    h.textContent = med === null ? titulo : `${titulo}: mediana ${duracao(med)}`;
    if (valores.length === 0) {
      alvo.innerHTML = `<p class="rt-vazio">nenhuma leitura medida ainda</p>`;
      return;
    }
    const c = histograma(valores);
    const maior = Math.max(1, ...c);
    alvo.replaceChildren(
      ...FAIXAS.map((f, i) => {
        const col = document.createElement("div");
        col.className = "rt-col";
        const n = c[i] ?? 0;
        const v = document.createElement("span");
        v.className = "rt-col-n";
        v.textContent = n > 0 ? `${decimal((100 * n) / valores.length, 0)}%` : "";
        const barra = document.createElement("i");
        barra.style.height = `${(100 * n) / maior}%`;
        const rot = document.createElement("span");
        rot.className = "rt-col-rot";
        rot.textContent = f.rotulo;
        col.append(v, barra, rot);
        return col;
      }),
    );
  };
  hist(".rt-hist-leitura", "leitura menos geração", ".rt-h-leitura", e.latencias.leitura_menos_hg);
  hist(".rt-hist-geracao", "geração menos totalização", ".rt-h-geracao", e.latencias.hg_menos_ht);

  const ol = raiz.querySelector<HTMLElement>(".rt-ufs");
  if (!ol) return;
  const ufs = [...e.ufs].sort((a, b) => a.pst - b.pst || a.uf.localeCompare(b.uf));
  if (ufs.length === 0 || ufs.every(u => !(u.pst > 0))) {
    ol.innerHTML = `<li class="rt-vazio">nenhuma UF com seções totalizadas ainda</li>`;
    return;
  }
  ol.replaceChildren(
    ...ufs.map(u => {
      const li = document.createElement("li");
      li.title = nomeUf(s, u.uf);
      const sg = document.createElement("b");
      sg.textContent = u.uf.toUpperCase();
      const barra = document.createElement("span");
      barra.className = "rt-uf-barra";
      const i = document.createElement("i");
      i.style.width = `${Math.max(0, Math.min(100, u.pst))}%`;
      if (u.pst >= 100) i.classList.add("rt-uf-fim");
      barra.append(i);
      const v = document.createElement("span");
      v.className = "rt-uf-pct";
      v.textContent = pct(u.pst);
      li.append(sg, barra, v);
      return li;
    }),
  );
}
