// Tela "evolucao": % dos válidos dos dois candidatos ao longo da noite. O nacional fica grande
// à esquerda e as seis regiões em pequenos múltiplos à direita; a tecla m troca por 27 UFs mais o
// exterior numa grade 7×4. Em cada gráfico, a curva de seções totalizadas do 2º turno (cheia) e a
// do 1º turno no mesmo relógio (pontilhada).

import { chip, chipAndamento } from "../components/chip.ts";
import { NOME_REGIAO, ORDEM_REGIOES, REGIOES } from "../../turno2/comum.ts";
import { corCandidato } from "../data/cores.ts";
import type { Evolucao, PontoEvolucao } from "../data/doist.ts";
import { decimal, nomeProprio, pct } from "../data/format.ts";
import type { State } from "../state/types.ts";
import { atualizarAviso, criarTela2T, dados, dueloDe, h, montarComAviso, SEM_REGUA } from "./doist-ui.ts";
import { evolucaoSvg, fimDoEixo } from "./doist-util.ts";
import { eleicaoDe } from "./executivo.ts";
import { chaveResultado } from "../state/types.ts";

/** Chaves da grade de UFs: as regiões em ordem, cada uma com as suas UFs; o exterior por último (28 células). */
export const CHAVES_UFS: readonly string[] = ORDEM_REGIOES.flatMap(r => [...REGIOES[r]]);

export const variantePorUf = (s: State): boolean => s.ui.variante % 2 === 1;

/** Último ponto do duelo com os dois percentuais. */
export function ultimoDuelo(pontos: readonly PontoEvolucao[]): PontoEvolucao | null {
  for (let i = pontos.length - 1; i >= 0; i--) {
    const p = pontos[i];
    if (p && p.a !== null && p.b !== null && p.pst > 0) return p;
  }
  return null;
}

function celula(titulo: string, pontos: readonly PontoEvolucao[], ref: readonly (readonly [number, number])[] | null, cores: [string, string], fim: number, minAgora: number, dim: { w: number; h: number; mini: boolean }): HTMLElement {
  const c = h("div", `ev-cel${dim.mini ? " ev-cel--mini" : ""}`);
  const u = ultimoDuelo(pontos);
  const cab = h("div", "ev-cel-cab");
  const va = h("span", "ev-cel-v num", typeof u?.a === "number" ? decimal(u.a, 1) : "–");
  va.style.color = cores[0];
  const vb = h("span", "ev-cel-v num", typeof u?.b === "number" ? decimal(u.b, 1) : "–");
  vb.style.color = cores[1];
  cab.append(h("b", "ev-cel-t", titulo), va, vb);
  const svg = h("div", "ev-cel-svg");
  svg.innerHTML = evolucaoSvg({
    largura: dim.w,
    altura: dim.h,
    pontos,
    ref,
    corA: cores[0],
    corB: cores[1],
    minAgora,
    fim,
    fonte: 22,
    margem: dim.mini ? { t: 8, r: 8, b: 8, l: 46 } : { t: 12, r: 10, b: 8, l: 52 },
    ticksX: false,
  });
  c.append(cab, svg);
  return c;
}

export function criarEvolucaoTela() {
  let raiz: HTMLElement | null = null;
  return criarTela2T({
    id: "evolucao",
    dwell: 24,
    cheia: true,
    needs: (s: State) => [
      { tipo: "doist", rota: variantePorUf(s) ? "evolucao-uf" : "evolucao-regiao" },
      { tipo: "resultado", ele: eleicaoDe(s, 1), cargo: 1, abr: "br" },
      { tipo: "estado" },
    ],
    montar(p) {
      raiz = montarComAviso(p.corpo, "ev", `<div class="ev-nacional"></div><div class="ev-grade"></div><p class="d2-rodape">tecla m alterna entre regiões e UFs; linha cheia: seções do 2º turno; pontilhada: 1º turno no mesmo relógio</p>`);
    },
    chips(s) {
      const r = dados(s, variantePorUf(s) ? "evolucao-uf" : "evolucao-regiao");
      return [chipAndamento(s.estado?.br.pst ?? 0, false), chip(variantePorUf(s) ? "27 UFs e exterior" : "regiões", "neutro"), r && r.referencia_1t === null ? chip(SEM_REGUA, "aviso") : null];
    },
    entradas: s => [variantePorUf(s) ? s.doist["evolucao-uf"] : s.doist["evolucao-regiao"], s.resultados[chaveResultado(eleicaoDe(s, 1), 1, "br")], s.cores, s.ui.variante],
    atualizar(s, p) {
      if (!raiz) return;
      const porUf = variantePorUf(s);
      const rota = porUf ? "evolucao-uf" : "evolucao-regiao";
      const e: Evolucao | null = dados(s, rota);
      if (!atualizarAviso(p.corpo, s, rota, "Evolução") || !e) return;
      const nac = raiz.querySelector<HTMLElement>(".ev-nacional");
      const grade = raiz.querySelector<HTMLElement>(".ev-grade");
      if (!nac || !grade) return;
      const duelo = dueloDe(s);
      // Pelo número de urna: `a` é o menor (13), `b` o maior (22); a cor vem do duelo nacional.
      const [ca, cb] = e.candidatos;
      const cores: [string, string] = [
        duelo && ca && duelo.a.n === ca.n ? duelo.a.cor : corCandidato(ca?.n ?? "13", 0, s.cores),
        duelo && cb && duelo.b.n === cb.n ? duelo.b.cor : corCandidato(cb?.n ?? "22", 1, s.cores),
      ];
      const br = e.series.BR ?? [];
      const minAgora = br[br.length - 1]?.min ?? 0;
      const fim = fimDoEixo(minAgora);
      raiz.classList.toggle("ev--uf", porUf);
      const ref = (k: string): readonly (readonly [number, number])[] | null => e.referencia_1t?.[k] ?? null;

      // Painel nacional (some na grade de UFs, que usa a tela toda).
      nac.hidden = porUf;
      if (!porUf) {
        const u = ultimoDuelo(br);
        const cab = h("div", "ev-nac-cab");
        for (const [i, c] of [ca, cb].entries()) {
          const l = h("div", "ev-nac-lado");
          l.style.setProperty("--cor", cores[i] ?? "#5f6773");
          const v = i === 0 ? u?.a : u?.b;
          l.append(h("p", "ev-nac-nome corte", nomeProprio(c?.nome_urna ?? "")), h("p", "ev-nac-pct num", typeof v === "number" ? decimal(v, 2) : "–"));
          cab.append(l);
        }
        cab.append(h("p", "ev-nac-pst num", u ? `${pct(u.pst, 1)} das seções` : "sem votos ainda"));
        const g = h("div", "ev-nac-svg");
        g.innerHTML = evolucaoSvg({ largura: 1100, altura: 640, pontos: br, ref: ref("BR"), corA: cores[0], corB: cores[1], minAgora, fim, fonte: 22, margem: { t: 14, r: 40, b: 44, l: 64 } });
        nac.replaceChildren(cab, g);
      }

      // Pequenos múltiplos.
      const itens: { chave: string; titulo: string }[] = porUf
        ? CHAVES_UFS.map(k => ({ chave: k, titulo: k }))
        : ORDEM_REGIOES.map(k => ({ chave: k, titulo: NOME_REGIAO[k] }));
      grade.replaceChildren(
        ...itens.map(i => celula(i.titulo, e.series[i.chave] ?? [], ref(i.chave), cores, fim, minAgora, porUf ? { w: 252, h: 150, mini: true } : { w: 360, h: 200, mini: false })),
      );
    },
    desmontar() {
      raiz = null;
    },
  });
}
