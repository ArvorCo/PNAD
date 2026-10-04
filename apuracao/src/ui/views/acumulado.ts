// Tela "acumulado": votos absolutos de cada candidatura presidencial a cada versão do
// arquivo nacional desde as 17:00 (lotes 6257/1/br), com a linha fina dos válidos no
// mesmo eixo e o ponto final pulsante. Passar o ponteiro (ou tocar) mostra a linha de
// leitura no lote mais próximo e a ficha; o painel não muda com a leitura.

import { criarAcumulado, ganhoDesde, lotesDesde, tetoRedondo, ticksVotos } from "../components/acumulado.ts";
import type { GraficoAcumulado, SerieVotos } from "../components/acumulado.ts";
import { chip, chipAndamento, trocarChips } from "../components/chip.ts";
import { criarContador } from "../components/contador.ts";
import type { Contador } from "../components/contador.ts";
import type { Tick } from "../components/linhas.ts";
import { criarFicha } from "../components/tooltip.ts";
import type { Ficha, LinhaFicha } from "../components/tooltip.ts";
import { corCandidato } from "../data/cores.ts";
import { compacto, dezessete, hora, horaCurta, inteiro, nomeProprio, pct } from "../data/format.ts";
import type { Cores, Lote, Lotes, Need, State } from "../state/types.ts";
import { chaveLotes } from "../state/types.ts";
import type { View } from "./registry.ts";
import { partes } from "./registry.ts";

const ELE = 6257;
const CARGO = 1;
const MIN = 60_000;
const JANELA = 10 * MIN;
/** Linhas no gráfico: as candidaturas que passaram desta fração dos válidos (em pontos). */
const PISO_LINHA = 5;
const LINHAS_PAINEL = 8;
/** Cinza dos válidos: 4,6:1 sobre o papel, legível também no rótulo do fim da linha. */
export const COR_VALIDOS = "#666c75";

export interface InfoCand {
  sqcand: string;
  nome: string;
  cor: string;
}

/** Candidaturas na ordem do ranking nacional (votos na última versão), com cor e nome. */
export function infoDosLotes(l: Lotes | undefined, cores: Cores): InfoCand[] {
  return (l?.candidatos ?? []).map((c, i) => ({ sqcand: c.sqcand, nome: nomeProprio(c.nmu), cor: corCandidato(c.n, i, cores) }));
}

/** Início do eixo: 17:00 do dia de `agora` (Brasília). */
export function inicioDoEixo(s: State): number {
  const agora = Date.parse(s.estado?.agora ?? "");
  return dezessete(new Date(Number.isFinite(agora) ? agora : Date.now())).getTime();
}

const pctDe = (v: number, vv: number): number => (vv > 0 ? (100 * v) / vv : 0);
const ganho = (v: number): string => (v > 0 ? `+${compacto(v)}` : v < 0 ? compacto(v) : "0");
/** Inteiro com sinal explícito: "+1.234", "−56", "0". */
export const comSinalInteiro = (v: number): string => (v > 0 ? `+${inteiro(v)}` : inteiro(v));

interface Linha {
  tr: HTMLTableRowElement;
  votos: Contador;
  pct: Contador;
  lote: Contador;
  dez: Contador;
}

export function criarAcumuladoView(): View {
  let raiz: HTMLElement | null = null;
  let grafico: GraficoAcumulado | null = null;
  let ficha: Ficha | null = null;
  const linhas = new Map<string, Linha>();
  let assinatura = "";
  let visiveis: Lote[] = [];
  let info: InfoCand[] = [];

  const lerLote = (i: number, clientX: number, clientY: number): void => {
    const l = visiveis[i];
    if (!grafico || !ficha) return;
    if (i < 0 || !l) {
      grafico.limparLeitura();
      ficha.esconder();
      return;
    }
    const ancora = grafico.ler(i);
    const linhasFicha: LinhaFicha[] = info
      .filter(c => (l.cand[c.sqcand]?.vap ?? 0) > 0)
      .slice(0, LINHAS_PAINEL)
      .map(c => {
        const v = l.cand[c.sqcand]?.vap ?? 0;
        return { cor: c.cor, rotulo: c.nome, valor: inteiro(v), extra: pct(pctDe(v, l.vv)) };
      });
    ficha.mostrar(
      {
        titulo: hora(l.at),
        sub: `${pct(l.pst, 2)} das seções`,
        fatos: [
          { rotulo: "seções totalizadas", valor: inteiro(l.st) },
          { rotulo: "votos válidos", valor: inteiro(l.vv) },
        ],
        linhas: linhasFicha,
      },
      ancora?.x ?? clientX,
      ancora?.y ?? clientY,
    );
  };

  return {
    id: "acumulado",
    dwell: 30,
    titulo: () => "Votos acumulados",
    needs: (): Need[] => [
      { tipo: "estado" },
      { tipo: "lotes", ele: ELE, cargo: CARGO, abr: "br" },
    ],
    mount(el) {
      raiz = el;
      const p = partes(el);
      p.corpo.innerHTML = `
        <div class="ac">
          <p class="ac-sub">votos de cada candidatura a presidente a cada atualização do TSE desde as 17:00</p>
          <div class="ac-grafico"></div>
          <p class="ac-nota"></p>
        </div>`;
      p.painel.innerHTML = `
        <div class="ac-painel">
          <table class="ac-tab">
            <thead><tr><th>candidatura</th><th>votos</th><th>válidos</th><th>lote</th><th>10 min</th></tr></thead>
            <tbody></tbody>
          </table>
          <p class="ac-ultimo"></p>
        </div>`;
      const g = el.querySelector<HTMLElement>(".ac-grafico");
      if (g) grafico = criarAcumulado(g, { largura: 1152, altura: 640, margem: { l: 104, r: 360 }, aoLer: lerLote });
      ficha = criarFicha(el);
    },
    update(s: State) {
      if (!raiz) return;
      const p = partes(raiz);
      const dados = s.lotes[chaveLotes(ELE, CARGO, "br")];
      trocarChips(p.chips, [chipAndamento(s.estado?.br.pst ?? 0, false), dados?.fonte === "soma_ufs" ? chip("soma das 27 UFs e exterior", "aviso") : null]);
      const desde = inicioDoEixo(s);
      const sig = [dados?.lotes.length, dados?.lotes[dados.lotes.length - 1]?.snapshot_id, dados?.fonte, s.cores, desde, s.estado?.agora.slice(0, 15)].join("|");
      if (sig === assinatura) return;
      assinatura = sig;
      info = infoDosLotes(dados, s.cores);
      visiveis = lotesDesde(dados?.lotes ?? [], desde).filter(l => l.st > 0 || l.vv > 0);
      desenharGrafico(raiz, grafico, visiveis, info, desde, dados?.fonte === "soma_ufs");
      const agora = Date.parse(s.estado?.agora ?? "");
      desenharPainel(raiz, linhas, visiveis, info, Number.isFinite(agora) ? agora : Date.now());
    },
    unmount() {
      grafico?.destroy();
      ficha?.destroy();
      for (const l of linhas.values()) for (const c of [l.votos, l.pct, l.lote, l.dez]) c.destroy();
      linhas.clear();
      grafico = null;
      ficha = null;
      raiz = null;
    },
  };
}

function desenharGrafico(raiz: HTMLElement, g: GraficoAcumulado | null, lotes: Lote[], info: InfoCand[], desde: number, soma: boolean): void {
  const nota = raiz.querySelector<HTMLElement>(".ac-nota");
  if (!g || !nota) return;
  const ult = lotes[lotes.length - 1];
  const fimX = Math.max(desde + 60 * MIN, (ult ? Date.parse(ult.at) : desde) + 10 * MIN);
  const passoX = fimX - desde > 4 * 60 * MIN ? 60 * MIN : 30 * MIN;
  const ticksX: Tick[] = [];
  for (let t = desde; t <= fimX; t += passoX) ticksX.push({ v: t, texto: horaCurta(t) });
  if (!ult) {
    g.update([], [], () => NaN, { dominioX: [desde, fimX], dominioY: [0, 10_000_000], ticksX, ticksY: ticksVotos(0, 10_000_000) });
    nota.textContent = "nenhuma atualização do TSE desde as 17h ainda";
    nota.classList.add("ac-nota--vazio");
    return;
  }
  nota.classList.remove("ac-nota--vazio");
  const nasLinhas = info.filter(c => pctDe(ult.cand[c.sqcand]?.vap ?? 0, ult.vv) >= PISO_LINHA);
  const series: SerieVotos[] = [
    { id: "vv", cor: COR_VALIDOS, rotulo: `válidos ${compacto(ult.vv)}`, nome: "válidos", espessura: 2, referencia: true },
    ...nasLinhas.map(c => ({ id: c.sqcand, cor: c.cor, nome: c.nome, rotulo: `${c.nome} ${compacto(ult.cand[c.sqcand]?.vap ?? 0)}` })),
  ];
  const teto = tetoRedondo(Math.max(...lotes.map(l => l.vv)), 5);
  g.update(lotes, series, (l, id) => (id === "vv" ? l.vv : (l.cand[id]?.vap ?? NaN)), {
    dominioX: [desde, fimX],
    dominioY: [0, teto],
    ticksX,
    ticksY: ticksVotos(0, teto),
  });
  const fora = info.length - nasLinhas.length;
  nota.textContent =
    `${lotes.length} ${lotes.length === 1 ? "atualização" : "atualizações"} ${soma ? "da soma das UFs, minuto a minuto" : "do arquivo nacional"}; linha cinza: votos válidos` +
    (fora > 0 ? `; candidaturas abaixo de ${PISO_LINHA}% dos válidos ficam fora do gráfico` : "");
}

function desenharPainel(raiz: HTMLElement, linhas: Map<string, Linha>, lotes: Lote[], info: InfoCand[], agora: number): void {
  const corpo = raiz.querySelector<HTMLElement>(".ac-tab tbody");
  const rodape = raiz.querySelector<HTMLElement>(".ac-ultimo");
  if (!corpo || !rodape) return;
  const ult = lotes[lotes.length - 1];
  const lista = info.slice(0, LINHAS_PAINEL);
  const vivos = new Set(lista.map(c => c.sqcand));
  for (const [k, l] of linhas) {
    if (!vivos.has(k)) {
      l.tr.remove();
      for (const c of [l.votos, l.pct, l.lote, l.dez]) c.destroy();
      linhas.delete(k);
    }
  }
  const ordem: HTMLTableRowElement[] = [];
  for (const c of lista) {
    let l = linhas.get(c.sqcand);
    if (!l) {
      const tr = document.createElement("tr");
      const nome = document.createElement("th");
      const sw = document.createElement("i");
      sw.className = "ac-cor";
      nome.append(sw, document.createElement("span"));
      l = {
        tr,
        votos: criarContador({ formato: inteiro, contarDoZero: false }),
        pct: criarContador({ formato: x => pct(x), contarDoZero: false }),
        lote: criarContador({ formato: ganho, contarDoZero: false }),
        dez: criarContador({ formato: ganho, contarDoZero: false }),
      };
      const tds = [l.votos, l.pct, l.lote, l.dez].map(x => {
        const td = document.createElement("td");
        td.append(x.el);
        return td;
      });
      tr.append(nome, ...tds);
      linhas.set(c.sqcand, l);
    }
    const sw = l.tr.querySelector<HTMLElement>(".ac-cor");
    const nm = l.tr.querySelector<HTMLElement>("th span");
    if (sw) sw.style.background = c.cor;
    if (nm) nm.textContent = c.nome;
    const v = ult?.cand[c.sqcand]?.vap ?? 0;
    l.votos.definir(v);
    l.pct.definir(pctDe(v, ult?.vv ?? 0));
    l.lote.definir(ult?.cand[c.sqcand]?.d_vap ?? 0);
    l.dez.definir(ganhoDesde(lotes, c.sqcand, agora - JANELA));
    ordem.push(l.tr);
  }
  corpo.replaceChildren(...ordem);
  if (!ult) {
    rodape.textContent = "último lote: nenhum desde as 17h";
    return;
  }
  rodape.textContent = `último lote: ${hora(ult.at)}, ${comSinalInteiro(ult.d_st)} seções, ${comSinalInteiro(ult.d_vv)} votos`;
}
