// Tela "lotes": o que chegou em cada atualização do arquivo nacional de presidente desde
// as 17:00. Uma barra por lote, empilhada pelos votos que cada candidatura ganhou; altura
// = válidos acrescentados; escada de seções acrescentadas no eixo da direita. Ponteiro
// ou toque numa barra: contorno lime e ficha. Teclas "," e "." (e ↓/↑) andam a seleção.

import { lotesDesde } from "../components/acumulado.ts";
import { chip, chipAndamento, trocarChips } from "../components/chip.ts";
import { agrupar, liderDoBloco, OUTROS, participacao } from "../components/lotes.ts";
import type { Bloco, GraficoLotes } from "../components/lotes.ts";
import { criarGraficoLotes } from "../components/lotes.ts";
import { criarFicha } from "../components/tooltip.ts";
import type { ConteudoFicha, Ficha, LinhaFicha } from "../components/tooltip.ts";
import { compacto, duracao, hora, horaCurta, pct } from "../data/format.ts";
import type { Need, State } from "../state/types.ts";
import { chaveLotes } from "../state/types.ts";
import { COR_VALIDOS, comSinalInteiro, infoDosLotes, inicioDoEixo } from "./acumulado.ts";
import type { InfoCand } from "./acumulado.ts";
import type { View } from "./registry.ts";
import { partes } from "./registry.ts";

const ELE = 6257;
const CARGO = 1;
const LISTA = 8;

/** Teclas da tela: anterior e próxima barra. */
export const TECLAS_ANTERIOR: ReadonlySet<string> = new Set([",", "ArrowDown"]);
export const TECLAS_PROXIMA: ReadonlySet<string> = new Set([".", "ArrowUp"]);

/** Nova seleção depois de uma tecla: sem seleção, começa pela última barra. */
export function moverSelecao(atual: number | null, passo: -1 | 1, n: number): number | null {
  if (n <= 0) return null;
  if (atual === null) return n - 1;
  return Math.max(0, Math.min(n - 1, atual + passo));
}

const ganho = (v: number): string => (v > 0 ? `+${compacto(v)}` : compacto(v));

/** Texto de um bloco por candidatura: "Lula +120 mil, 48,2% do lote". */
export function linhaDoBloco(b: Bloco, c: InfoCand): LinhaFicha {
  return { cor: c.cor, rotulo: c.nome, valor: ganho(b.d_cand[c.sqcand] ?? 0), extra: `${pct(participacao(b, c.sqcand))} do lote` };
}

/** Latência do lote: segundos entre a geração do arquivo e a nossa leitura. */
export function latenciaS(b: Bloco): number | null {
  const g = Date.parse(b.ultimo.at);
  const l = Date.parse(b.ultimo.capturado_em);
  return Number.isFinite(g) && Number.isFinite(l) ? Math.max(0, (l - g) / 1000) : null;
}

/** `soma`: lotes da soma das 28 UFs (arquivo nacional do TSE parado); a hora é a da grade. */
export function fichaDoBloco(b: Bloco, info: readonly InfoCand[], soma = false): ConteudoFicha {
  const lat = latenciaS(b);
  const linhas = info.filter(c => (b.d_cand[c.sqcand] ?? 0) !== 0).slice(0, LISTA).map(c => linhaDoBloco(b, c));
  return {
    titulo: b.n > 1 ? `${horaCurta(b.ini)} a ${horaCurta(b.fim)}` : hora(b.ini),
    sub: b.n > 1 ? `${b.n} lotes somados` : `${pct(b.ultimo.pst, 2)} das seções`,
    fatos: [
      { rotulo: "seções", valor: comSinalInteiro(b.d_st) },
      { rotulo: "votos válidos", valor: comSinalInteiro(b.d_vv) },
    ],
    linhas,
    notas: soma
      ? [`soma das UFs às ${hora(b.ultimo.at)}`]
      : lat === null
        ? []
        : [`arquivo gerado às ${hora(b.ultimo.at)}, lido ${lat < 60 ? `${Math.round(lat)} s` : duracao(lat)} depois`],
  };
}

export function criarLotesView(): View {
  let raiz: HTMLElement | null = null;
  let grafico: GraficoLotes | null = null;
  let ficha: Ficha | null = null;
  let assinatura = "";
  let blocos: Bloco[] = [];
  let info: InfoCand[] = [];
  let selecao: number | null = null;
  let sobPonteiro = -1;
  let soma = false;

  const mostrar = (i: number, clientX?: number): void => {
    if (!grafico || !ficha) return;
    const b = blocos[i];
    const ancora = b ? grafico.marcar(i) : null;
    if (!b || !ancora) {
      grafico.marcar(-1);
      ficha.esconder();
      return;
    }
    ficha.mostrar(fichaDoBloco(b, info, soma), clientX ?? ancora.x, ancora.y);
  };

  const ler = (i: number, clientX: number): void => {
    sobPonteiro = i;
    if (i >= 0) mostrar(i, clientX);
    else if (selecao !== null) mostrar(selecao);
    else mostrar(-1);
  };

  return {
    id: "lotes",
    dwell: 30,
    titulo: () => "O que chegou em cada atualização",
    needs: (): Need[] => [
      { tipo: "estado" },
      { tipo: "lotes", ele: ELE, cargo: CARGO, abr: "br" },
    ],
    mount(el) {
      raiz = el;
      const p = partes(el);
      p.corpo.innerHTML = `
        <div class="lt">
          <p class="lt-sub">votos válidos e seções que cada atualização do arquivo nacional acrescentou desde as 17:00</p>
          <div class="lt-grafico"></div>
          <p class="lt-legenda"></p>
        </div>`;
      p.painel.innerHTML = `
        <div class="lt-painel">
          <section><h2>últimos lotes</h2><p class="lt-lista-cab"><span>hora</span><span>seções</span><span>válidos</span><span>quem levou</span></p><ol class="lt-lista"></ol></section>
          <section><h2>quem levou o último lote</h2><div class="lt-bloco"></div><ul class="lt-bloco-leg"></ul></section>
        </div>`;
      const g = el.querySelector<HTMLElement>(".lt-grafico");
      if (g) grafico = criarGraficoLotes(g, { largura: 1152, altura: 640, aoLer: ler });
      ficha = criarFicha(el);
    },
    update(s: State) {
      if (!raiz) return;
      const p = partes(raiz);
      const dados = s.lotes[chaveLotes(ELE, CARGO, "br")];
      soma = dados?.fonte === "soma_ufs";
      const sub = raiz.querySelector(".lt-sub");
      if (sub) sub.textContent = soma
        ? "votos válidos e seções que a soma das UFs acrescentou a cada minuto desde as 17:00"
        : "votos válidos e seções que cada atualização do arquivo nacional acrescentou desde as 17:00";
      trocarChips(p.chips, [chipAndamento(s.estado?.br.pst ?? 0, false), soma ? chip("soma das 27 UFs e exterior", "aviso") : null]);
      const desde = inicioDoEixo(s);
      const sig = [dados?.lotes.length, dados?.lotes[dados.lotes.length - 1]?.snapshot_id, dados?.fonte, s.cores, desde].join("|");
      if (sig === assinatura) return;
      assinatura = sig;
      info = infoDosLotes(dados, s.cores);
      const lotes = lotesDesde(dados?.lotes ?? [], desde).filter(l => l.st > 0 || l.d_vv !== 0 || l.d_st !== 0);
      const g = agrupar(lotes);
      blocos = g.blocos;
      const cores = new Map(info.map(c => [c.sqcand, c.cor]));
      grafico?.update({ blocos, ordem: info.map(c => c.sqcand), cor: id => (id === OUTROS ? COR_VALIDOS : (cores.get(id) ?? COR_VALIDOS)), hora: horaCurta });
      if (selecao !== null) selecao = Math.min(selecao, blocos.length - 1);
      if (selecao !== null && selecao < 0) selecao = null;
      if (sobPonteiro >= blocos.length) sobPonteiro = -1;
      const foco = sobPonteiro >= 0 ? sobPonteiro : selecao;
      if (foco !== null) mostrar(foco);
      desenharLegenda(raiz, lotes.length, g.agrupado);
      desenharPainel(raiz, blocos, info);
    },
    keys(tecla) {
      const passo = TECLAS_ANTERIOR.has(tecla) ? -1 : TECLAS_PROXIMA.has(tecla) ? 1 : 0;
      if (passo === 0) return false;
      selecao = moverSelecao(selecao, passo, blocos.length);
      sobPonteiro = -1;
      if (selecao !== null) mostrar(selecao);
      return true;
    },
    unmount() {
      grafico?.destroy();
      ficha?.destroy();
      grafico = null;
      ficha = null;
      raiz = null;
    },
  };
}

function desenharLegenda(raiz: HTMLElement, n: number, agrupado: boolean): void {
  const leg = raiz.querySelector<HTMLElement>(".lt-legenda");
  if (!leg) return;
  if (n === 0) {
    leg.textContent = "nenhuma atualização do TSE desde as 17h ainda";
    leg.classList.add("lt-legenda--vazio");
    return;
  }
  leg.classList.remove("lt-legenda--vazio");
  const base = `${n} ${n === 1 ? "atualização" : "atualizações"}; altura da barra: válidos acrescentados; linha escura: seções acrescentadas (eixo da direita); abaixo do zero, regressão`;
  leg.textContent = agrupado ? `${base}; com mais de 300 lotes, cada barra soma os lotes de 5 minutos` : base;
}

function desenharPainel(raiz: HTMLElement, blocos: readonly Bloco[], info: readonly InfoCand[]): void {
  const ol = raiz.querySelector<HTMLElement>(".lt-lista");
  const barra = raiz.querySelector<HTMLElement>(".lt-bloco");
  const leg = raiz.querySelector<HTMLElement>(".lt-bloco-leg");
  if (!ol || !barra || !leg) return;
  const ordem = info.map(c => c.sqcand);
  const porId = new Map(info.map(c => [c.sqcand, c]));
  const recentes = blocos.slice(-LISTA).reverse();
  if (recentes.length === 0) {
    ol.innerHTML = `<li class="lt-vazio">nenhuma atualização do TSE desde as 17h ainda</li>`;
    barra.replaceChildren();
    leg.replaceChildren();
    return;
  }
  ol.replaceChildren(
    ...recentes.map(b => {
      const li = document.createElement("li");
      const h = document.createElement("b");
      h.textContent = b.n > 1 ? horaCurta(b.ini) : hora(b.ini);
      const st = document.createElement("span");
      st.className = "lt-n";
      st.textContent = comSinalInteiro(b.d_st);
      const vv = document.createElement("span");
      vv.className = "lt-n";
      vv.textContent = ganho(b.d_vv);
      const lid = document.createElement("span");
      lid.className = "lt-lider";
      const id = liderDoBloco(b, ordem);
      const c = id ? porId.get(id) : undefined;
      if (c) {
        const sw = document.createElement("i");
        sw.style.background = c.cor;
        lid.append(sw, document.createTextNode(`${c.nome} ${pct(participacao(b, c.sqcand))}`));
      } else lid.textContent = "sem ganho";
      li.append(h, st, vv, lid);
      return li;
    }),
  );
  const ult = blocos[blocos.length - 1];
  if (!ult) return;
  const fatias = info
    .map(c => ({ c, v: Math.max(0, ult.d_cand[c.sqcand] ?? 0) }))
    .filter(x => x.v > 0);
  const total = Math.max(1, ult.d_vv, fatias.reduce((a, x) => a + x.v, 0));
  barra.replaceChildren(
    ...fatias.map(x => {
      const i = document.createElement("i");
      i.style.width = `${(100 * x.v) / total}%`;
      i.style.background = x.c.cor;
      i.title = x.c.nome;
      return i;
    }),
  );
  leg.replaceChildren(
    ...fatias.slice(0, 4).map(x => {
      const li = document.createElement("li");
      const sw = document.createElement("i");
      sw.style.background = x.c.cor;
      const nome = document.createElement("span");
      nome.textContent = x.c.nome;
      const v = document.createElement("b");
      v.textContent = `${pct(participacao(ult, x.c.sqcand))}, ${ganho(x.v)}`;
      li.append(sw, nome, v);
      return li;
    }),
  );
}

