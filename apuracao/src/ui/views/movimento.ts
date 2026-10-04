// Tela "mov": frações dos válidos de cada candidatura presidencial a cada snapshot desde
// as 17:00 (série 6257/1/br), linhas de 4 px nas cores dos candidatos e viradas marcadas
// com círculo e hora. Painel: sparklines de SP, MG, RJ, BA, RS e PR e as maiores viradas
// registradas em /api/anomalias.

import { chipAndamento, trocarChips } from "../components/chip.ts";
import { criarLinhas, dominioAuto, ticksRedondos } from "../components/linhas.ts";
import type { Linhas, Marcador, SerieLinha, Tick } from "../components/linhas.ts";
import { corCandidato } from "../data/cores.ts";
import { comSinal, decimal, dezessete, horaCurta, nomeProprio, pct } from "../data/format.ts";
import { ranking } from "../state/selectors.ts";
import type { Cores, Need, Resultado, Serie, State } from "../state/types.ts";
import { chaveResultado, chaveSerie } from "../state/types.ts";
import type { View } from "./registry.ts";
import { nomeUf, partes } from "./registry.ts";

const ELE = 6257;
const CARGO = 1;
const MIN = 60_000;
export const UFS_SPARK = ["SP", "MG", "RJ", "BA", "RS", "PR"] as const;
/** Só entram no gráfico principal as candidaturas que passaram de 10% dos válidos. */
const PISO_LINHA = 10;

interface InfoCand {
  nome: string;
  cor: string;
}

export function infoCandidatos(r: Resultado | undefined, cores: Cores): Map<string, InfoCand> {
  const m = new Map<string, InfoCand>();
  if (!r) return m;
  ranking(r.cand).forEach((c, i) => m.set(c.sqcand, { nome: nomeProprio(c.nmu), cor: corCandidato(c.n, i, cores) }));
  return m;
}

/** Candidaturas a desenhar: máximo da série acima do piso, ordenadas pelo último valor. */
export function candidatosDaSerie(serie: Serie, piso: number): string[] {
  const max = new Map<string, number>();
  for (const p of serie.pontos) for (const [k, v] of Object.entries(p.cand)) max.set(k, Math.max(max.get(k) ?? 0, v));
  const ultimo = serie.pontos[serie.pontos.length - 1]?.cand ?? {};
  return [...max.entries()]
    .filter(([, v]) => v >= piso)
    .map(([k]) => k)
    .sort((a, b) => (ultimo[b] ?? 0) - (ultimo[a] ?? 0));
}

export function criarMovimento(): View {
  let raiz: HTMLElement | null = null;
  let grafico: Linhas | null = null;
  const sparks = new Map<string, Linhas>();
  let assinatura = "";

  return {
    id: "mov",
    dwell: 25,
    titulo: () => "Movimento da apuração",
    needs: (): Need[] => [
      { tipo: "estado" },
      { tipo: "anomalias" },
      { tipo: "resultado", ele: ELE, cargo: CARGO, abr: "br" },
      { tipo: "serie", ele: ELE, cargo: CARGO, abr: "br" },
      ...UFS_SPARK.map((uf): Need => ({ tipo: "serie", ele: ELE, cargo: CARGO, abr: uf.toLowerCase() })),
    ],
    mount(el) {
      raiz = el;
      const p = partes(el);
      p.corpo.innerHTML = `
        <div class="mv">
          <p class="mv-sub">percentual dos válidos para presidente a cada leitura desde as 17:00</p>
          <div class="mv-grafico"></div>
          <p class="mv-nota"></p>
        </div>`;
      p.painel.innerHTML = `
        <div class="mv-painel">
          <section><h2>seis maiores eleitorados</h2><div class="mv-sparks"></div></section>
          <section><h2>maiores viradas</h2><ol class="mv-viradas"></ol></section>
        </div>`;
      const g = el.querySelector<HTMLElement>(".mv-grafico");
      if (g) grafico = criarLinhas(g, { largura: 1152, altura: 640, margem: { r: 300, l: 84 } });
      const box = el.querySelector<HTMLElement>(".mv-sparks");
      if (box) {
        for (const uf of UFS_SPARK) {
          const card = document.createElement("div");
          card.className = "mv-spark";
          card.dataset.uf = uf;
          card.innerHTML = `<p class="mv-spark-cab"><b>${uf}</b><span class="mv-spark-margem"></span></p><div class="mv-spark-g"></div>`;
          box.append(card);
          const alvo = card.querySelector<HTMLElement>(".mv-spark-g");
          if (alvo) sparks.set(uf, criarLinhas(alvo, { largura: 300, altura: 96, mini: true }));
        }
      }
    },
    update(s: State) {
      if (!raiz) return;
      const p = partes(raiz);
      trocarChips(p.chips, [chipAndamento(s.estado?.br.pst ?? 0, false)]);
      const r = s.resultados[chaveResultado(ELE, CARGO, "br")];
      const serie = s.series[chaveSerie(ELE, CARGO, "br")];
      const sig = [r?.lido_em, serie?.pontos.length, serie?.pontos[serie.pontos.length - 1]?.at, s.anomalias.length, s.cores, ...UFS_SPARK.map(uf => s.series[chaveSerie(ELE, CARGO, uf.toLowerCase())]?.pontos.length)].join("|");
      if (sig === assinatura) return;
      assinatura = sig;
      const info = infoCandidatos(r, s.cores);
      desenharPrincipal(raiz, grafico, serie, info);
      for (const uf of UFS_SPARK) desenharSpark(raiz, s, uf, sparks.get(uf), info);
      desenharViradas(raiz, s);
    },
    unmount() {
      grafico?.destroy();
      for (const g of sparks.values()) g.destroy();
      sparks.clear();
      grafico = null;
      raiz = null;
    },
  };
}

const corDe = (info: Map<string, InfoCand>, sq: string): string => info.get(sq)?.cor ?? "#5f6773";

function desenharPrincipal(raiz: HTMLElement, grafico: Linhas | null, serie: Serie | undefined, info: Map<string, InfoCand>): void {
  const nota = raiz.querySelector<HTMLElement>(".mv-nota");
  if (!grafico || !nota) return;
  // Só leituras com seção totalizada: o snapshot zerado da véspera abriria o eixo em 17:00 de ontem.
  const pontos = (serie?.pontos ?? []).filter(q => q.pst > 0);
  if (!serie || pontos.length === 0) {
    grafico.update([], { dominioX: [0, 1], dominioY: [30, 60] });
    nota.textContent = "nenhuma leitura com seções totalizadas ainda; a linha começa na primeira";
    return;
  }
  const ids = candidatosDaSerie(serie, PISO_LINHA);
  const xs = pontos.map(q => Date.parse(q.at));
  const x0 = dezessete(new Date(xs[0] ?? Date.now())).getTime();
  const x1 = Math.max(x0 + 60 * MIN, (xs[xs.length - 1] ?? x0) + 10 * MIN);
  const series: SerieLinha[] = ids.map(sq => {
    const ult = pontos[pontos.length - 1]?.cand[sq] ?? 0;
    return {
      id: sq,
      cor: corDe(info, sq),
      rotulo: `${info.get(sq)?.nome ?? sq} ${pct(ult)}`,
      pontos: pontos.map((q, i) => ({ x: xs[i] ?? NaN, y: q.cand[sq] ?? NaN })),
    };
  });
  const valores = series.flatMap(sr => sr.pontos.map(q => q.y));
  const dy = dominioAuto(valores, [30, 60], 5, 0, 100);
  const ticksY: Tick[] = ticksRedondos(dy[0], dy[1], 6).map(v => ({ v, texto: `${decimal(v, 0)}%` }));
  const passoX = x1 - x0 > 4 * 60 * MIN ? 60 * MIN : 30 * MIN;
  const ticksX: Tick[] = [];
  for (let t = x0; t <= x1; t += passoX) ticksX.push({ v: t, texto: horaCurta(t) });
  const marcadores: Marcador[] = serie.viradas.flatMap(v => {
    const t = Date.parse(v.at);
    const ponto = pontos.find(q => q.at === v.at);
    const y = ponto?.cand[v.para];
    return Number.isFinite(t) && y !== undefined ? [{ x: t, y, cor: corDe(info, v.para), texto: horaCurta(t) }] : [];
  });
  grafico.update(series, { dominioX: [x0, x1], dominioY: dy, ticksX, ticksY, marcadores });
  const ultimo = pontos[pontos.length - 1]?.cand ?? {};
  const resto = Object.entries(ultimo)
    .filter(([k]) => !ids.includes(k))
    .reduce((acc, [, v]) => acc + v, 0);
  const viradas = serie.viradas.length;
  nota.textContent =
    `demais candidaturas somam ${pct(resto)} dos válidos` +
    (viradas > 0 ? `; ${viradas} ${viradas === 1 ? "troca" : "trocas"} de liderança no país, marcadas com círculo` : "; nenhuma troca de liderança no país até agora");
}

function desenharSpark(raiz: HTMLElement, s: State, uf: string, g: Linhas | undefined, info: Map<string, InfoCand>): void {
  const card = raiz.querySelector<HTMLElement>(`.mv-spark[data-uf="${uf}"]`);
  const margem = card?.querySelector<HTMLElement>(".mv-spark-margem");
  const cab = card?.querySelector<HTMLElement>(".mv-spark-cab b");
  if (!card || !margem || !g) return;
  if (cab) {
    cab.textContent = uf;
    cab.title = nomeUf(s, uf);
  }
  const serie = s.series[chaveSerie(ELE, CARGO, uf.toLowerCase())];
  const pontos = (serie?.pontos ?? []).filter(q => q.pst > 0);
  if (!serie || pontos.length === 0) {
    margem.textContent = "aguardando seções";
    margem.style.color = "";
    g.update([], { dominioX: [0, 1], dominioY: [0, 1] });
    return;
  }
  const ids = candidatosDaSerie(serie, 0).slice(0, 2);
  const xs = pontos.map(q => Date.parse(q.at));
  const series: SerieLinha[] = ids.map(sq => ({ id: sq, cor: corDe(info, sq), pontos: pontos.map((q, i) => ({ x: xs[i] ?? NaN, y: q.cand[sq] ?? NaN })) }));
  const dy = dominioAuto(
    series.flatMap(sr => sr.pontos.map(q => q.y)),
    null,
    5,
    0,
    100,
  );
  const marcadores: Marcador[] = serie.viradas.flatMap(v => {
    const ponto = pontos.find(q => q.at === v.at);
    const y = ponto?.cand[v.para];
    return y !== undefined ? [{ x: Date.parse(v.at), y, cor: corDe(info, v.para) }] : [];
  });
  g.update(series, { dominioX: [xs[0] ?? 0, Math.max((xs[0] ?? 0) + MIN, xs[xs.length - 1] ?? 0)], dominioY: dy, marcadores });
  const [a, b] = ids;
  const ult = pontos[pontos.length - 1]?.cand ?? {};
  if (a) {
    const dif = (ult[a] ?? 0) - (b ? (ult[b] ?? 0) : 0);
    margem.textContent = `${info.get(a)?.nome ?? a} ${comSinal(dif)}`;
    margem.style.color = corDe(info, a);
  }
}

function desenharViradas(raiz: HTMLElement, s: State): void {
  const ol = raiz.querySelector<HTMLElement>(".mv-viradas");
  if (!ol) return;
  const vs = s.anomalias
    .filter(a => a.tipo === "virada")
    .sort((a, b) => b.at.localeCompare(a.at))
    .slice(0, 6);
  if (vs.length === 0) {
    ol.innerHTML = `<li class="mv-vazio">nenhuma virada registrada até agora</li>`;
    return;
  }
  ol.replaceChildren(
    ...vs.map(v => {
      const li = document.createElement("li");
      const h = document.createElement("b");
      h.textContent = horaCurta(v.at);
      const t = document.createElement("span");
      t.textContent = v.texto;
      li.append(h, t);
      return li;
    }),
  );
}
