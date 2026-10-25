// Tela "projecao": projeção estatística do resultado final a partir do que já foi totalizado
// (oscilação proporcional por município contra o 1º turno, com pooling parcial na UF). À
// esquerda, os dois percentuais projetados em % dos válidos com a faixa de 90%, o totalizado
// até agora e o gráfico da noite; à direita, a cobertura por região e as UFs que mais oscilaram.
// Sem base mínima (menos de 1% das seções), mostra o motivo e não inventa número.

import { chip, chipAndamento } from "../components/chip.ts";
import { caminho, escalaLinear } from "../components/linhas.ts";
import type { Ponto } from "../components/linhas.ts";
import { corCandidato } from "../data/cores.ts";
import type { BlocoProjecao, PontoProjecao, Projecao } from "../data/doist.ts";
import { ROTULO_PROJECAO } from "../data/doist.ts";
import { comSinal, decimal, inteiro, nomeProprio, pct } from "../data/format.ts";
import type { State } from "../state/types.ts";
import { chaveResultado } from "../state/types.ts";
import { atualizarAviso, criarTela2T, dados, dueloDe, h, montarComAviso } from "./doist-ui.ts";
import { fimDoEixo, ticksDeHora } from "./doist-util.ts";
import { eleicaoDe } from "./executivo.ts";

/** Lado do duelo na projeção: nome, cor e percentuais (Flávio = p_f; Lula = 100 − p_f). */
interface Lado {
  chave: "f" | "l";
  nome: string;
  cor: string;
}

/** Os dois lados na ordem das outras telas (13 à esquerda, 22 à direita). */
export function ladosDaProjecao(s: State, p: Projecao): [Lado, Lado] {
  const d = dueloDe(s);
  const nomeDe = (n: string, padrao: string): string => {
    const c = d && (d.a.n === n ? d.a : d.b.n === n ? d.b : null);
    return c?.nome ?? (padrao ? nomeProprio(padrao) : n);
  };
  const corDe = (n: string, i: number): string => {
    const c = d && (d.a.n === n ? d.a : d.b.n === n ? d.b : null);
    return c?.cor ?? corCandidato(n, i, s.cores);
  };
  const nl = p.candidatos.l.n || "13";
  const nf = p.candidatos.f.n || "22";
  return [
    { chave: "l", nome: nomeDe(nl, p.candidatos.l.nome_urna || "Lula"), cor: corDe(nl, 0) },
    { chave: "f", nome: nomeDe(nf, p.candidatos.f.nome_urna || "Flávio Bolsonaro"), cor: corDe(nf, 1) },
  ];
}

/** Percentual de um lado a partir de p_f (Flávio entre os dois). */
const doLado = (chave: "f" | "l", pf: number): number => (chave === "f" ? pf : 100 - pf);

/** As `n` UFs com maior oscilação em módulo (só as que têm oscilação medida). */
export function ufsQueMaisOscilaram(ufs: readonly BlocoProjecao[], n = 6): (BlocoProjecao & { swing_pp: number })[] {
  return ufs
    .filter((u): u is BlocoProjecao & { swing_pp: number } => u.swing_pp !== null && Number.isFinite(u.swing_pp))
    .sort((a, b) => Math.abs(b.swing_pp) - Math.abs(a.swing_pp) || a.sigla.localeCompare(b.sigla))
    .slice(0, n);
}

/** Domínio vertical do gráfico: 40 a 60 quando tudo cabe; senão alarga de 5 em 5 pontos. */
export function dominioProjecao(serie: readonly PontoProjecao[]): [number, number] {
  const v: number[] = [];
  for (const p of serie) {
    for (const x of [p.proj, p.a, p.b, p.obs]) {
      if (x === null || !Number.isFinite(x)) continue;
      v.push(x, 100 - x);
    }
  }
  if (v.length === 0) return [40, 60];
  const min = Math.min(...v);
  const max = Math.max(...v);
  if (min >= 40 && max <= 60) return [40, 60];
  const meia = Math.max(50 - Math.floor(min / 5) * 5, Math.ceil(max / 5) * 5 - 50);
  return [Math.max(0, 50 - meia), Math.min(100, 50 + meia)];
}

const f1 = (v: number): string => (Math.round(v * 10) / 10).toString();

/** SVG do gráfico da noite: projeção (linha cheia com banda de 90%) e totalizado (tracejado), os dois lados. */
export function graficoProjecaoSvg(serie: readonly PontoProjecao[], lados: readonly [Lado, Lado], larg: number, alt: number): string {
  const m = { t: 16, r: 24, b: 44, l: 64 };
  const pts = serie.filter(p => p.pst > 0 || p.proj !== null);
  const minAgora = serie[serie.length - 1]?.min ?? 0;
  const fim = fimDoEixo(minAgora);
  const [d0, d1] = dominioProjecao(pts);
  const sx = escalaLinear(0, fim, m.l, larg - m.r);
  const sy = escalaLinear(d0, d1, alt - m.b, m.t);
  const out: string[] = [`<svg class="pj-svg" viewBox="0 0 ${larg} ${alt}" role="img" aria-label="projeção e totalizado ao longo da noite">`];
  for (const t of ticksDeHora(fim)) {
    const x = sx(t.v);
    out.push(`<line class="pj-gl" x1="${f1(x)}" x2="${f1(x)}" y1="${m.t}" y2="${alt - m.b}"/>`);
    // O último rótulo encosta na borda direita: ancorado no fim para não ser cortado.
    const ancora = x > larg - m.r - 40 ? "end" : "middle";
    out.push(`<text class="pj-tick" x="${f1(x)}" y="${alt - m.b + 32}" text-anchor="${ancora}">${t.texto}</text>`);
  }
  const passoY = d1 - d0 > 20 ? 10 : 5;
  for (let v = d0; v <= d1 + 1e-9; v += passoY) {
    const y = sy(v);
    out.push(`<line class="${v === 50 ? "pj-meio" : "pj-gl"}" x1="${m.l}" x2="${larg - m.r}" y1="${f1(y)}" y2="${f1(y)}"/>`);
    out.push(`<text class="pj-tick" x="${m.l - 10}" y="${f1(y + 8)}" text-anchor="end">${v}</text>`);
  }
  out.push(`<line class="pj-base" x1="${m.l}" x2="${larg - m.r}" y1="${alt - m.b}" y2="${alt - m.b}"/>`);
  const comFaixa = pts.filter(p => p.proj !== null && p.a !== null && p.b !== null);
  for (const lado of lados) {
    // Banda de 90%: para Lula, o espelho da faixa de Flávio.
    if (comFaixa.length > 0) {
      const sup = comFaixa.map(p => ({ x: sx(p.min), y: sy(doLado(lado.chave, lado.chave === "f" ? (p.b as number) : (p.a as number))) }));
      const inf = comFaixa.map(p => ({ x: sx(p.min), y: sy(doLado(lado.chave, lado.chave === "f" ? (p.a as number) : (p.b as number))) })).reverse();
      const d = [...sup, ...inf].map((q, i) => `${i === 0 ? "M" : "L"}${f1(q.x)} ${f1(q.y)}`).join("");
      out.push(`<path class="pj-banda" d="${d}Z" fill="${lado.cor}"/>`);
    }
  }
  for (const lado of lados) {
    const obs: Ponto[] = pts.map(p => ({ x: p.min, y: p.obs === null ? Number.NaN : doLado(lado.chave, p.obs) }));
    const dObs = caminho(obs, sx, sy);
    if (dObs) out.push(`<path class="pj-obs" d="${dObs}" stroke="${lado.cor}"/>`);
    const proj: Ponto[] = pts.map(p => ({ x: p.min, y: p.proj === null ? Number.NaN : doLado(lado.chave, p.proj) }));
    const dProj = caminho(proj, sx, sy);
    if (dProj) out.push(`<path class="pj-proj" d="${dProj}" stroke="${lado.cor}"/>`);
  }
  const xa = sx(Math.min(minAgora, fim));
  out.push(`<line class="pj-agora" x1="${f1(xa)}" x2="${f1(xa)}" y1="${m.t}" y2="${alt - m.b}"/>`);
  out.push("</svg>");
  return out.join("");
}

function cartaoLado(lado: Lado, b: BlocoProjecao): HTMLElement {
  const c = h("div", "pj-lado");
  c.style.setProperty("--cor", lado.cor);
  const pj = b.projetado;
  const v = pj ? doLado(lado.chave, pj.p_f) : null;
  c.append(h("p", "pj-lado-nome corte", lado.nome), h("p", "pj-lado-pct num", v === null ? "–" : decimal(v, 1)));
  if (pj) {
    const [a, z] = lado.chave === "f" ? pj.faixa90 : [100 - pj.faixa90[1], 100 - pj.faixa90[0]];
    c.append(h("p", "pj-lado-faixa num", `faixa de 90%: ${decimal(a, 1)} a ${decimal(z, 1)}`));
  }
  return c;
}

/** Barra de 0 a 100% dos válidos: Lula a partir da esquerda, Flávio da direita, faixa de 90% em hachura. */
function barraFaixa(lados: readonly [Lado, Lado], b: BlocoProjecao): HTMLElement {
  const barra = h("div", "pj-barra");
  const pj = b.projetado;
  if (!pj) {
    barra.classList.add("pj-barra--vazia");
    return barra;
  }
  const esq = h("i", "pj-barra-esq");
  esq.style.width = `${100 - pj.p_f}%`;
  esq.style.background = lados[0].cor;
  const dir = h("i", "pj-barra-dir");
  dir.style.width = `${pj.p_f}%`;
  dir.style.background = lados[1].cor;
  const faixa = h("span", "pj-barra-faixa");
  const ini = Math.max(0, 100 - pj.faixa90[1]);
  const fimF = Math.min(100, 100 - pj.faixa90[0]);
  faixa.style.left = `${ini}%`;
  faixa.style.width = `${Math.max(0.4, fimF - ini)}%`;
  barra.append(esq, dir, faixa, h("span", "pj-barra-meio"));
  return barra;
}

function totalizado(lados: readonly [Lado, Lado], p: Projecao): HTMLElement {
  const b = p.brasil;
  const e = h("p", "pj-total");
  const pf = b.observado.p_f;
  if (pf === null) {
    e.textContent = `Totalizado até agora: sem votos dos dois ainda (${pct(p.cobertura.pst, 2)} das seções).`;
    return e;
  }
  e.append(h("span", "pj-total-rot", "Totalizado até agora: "));
  for (const [i, lado] of lados.entries()) {
    const s = h("b", "num", `${lado.nome} ${pct(doLado(lado.chave, pf), 2)}`);
    s.style.color = lado.cor;
    e.append(s);
    if (i === 0) e.append(h("span", "", " × "));
  }
  e.append(h("span", "pj-total-rot", ` com ${pct(p.cobertura.pst, 2)} das seções`));
  return e;
}

function cobertura(p: Projecao): HTMLElement {
  const c = h("section", "pj-cob");
  c.append(h("h2", "pj-h", "Quanto já foi observado"));
  const nums = h("div", "pj-cob-nums");
  const item = (v: string, rot: string): HTMLElement => {
    const d = h("div", "pj-cob-item");
    d.append(h("p", "pj-cob-v num", v), h("p", "pj-cob-rot", rot));
    return d;
  };
  nums.append(item(pct(p.cobertura.pst, 1), "das seções totalizadas"), item(pct(p.cobertura.pct_vv_observado, 1), "dos votos esperados já vistos"));
  const mun = `${inteiro(p.cobertura.municipios_observados)} de ${inteiro(p.cobertura.municipios_total)} municípios com voto, ${inteiro(p.cobertura.municipios_fechados)} fechados`;
  c.append(nums, h("p", "pj-cob-mun", mun));
  const lista = h("div", "pj-reg");
  for (const r of p.regioes) {
    const l = h("div", "pj-reg-linha");
    const barra = h("span", "d2-barra");
    const i = h("i");
    i.style.width = `${Math.max(0, Math.min(100, r.pct_vv_observado))}%`;
    barra.append(i);
    l.append(h("span", "pj-reg-nome corte", r.nome), barra, h("span", "pj-reg-v num", pct(r.pct_vv_observado, 1)));
    lista.append(l);
  }
  c.append(lista);
  return c;
}

function tabelaUfs(p: Projecao): HTMLElement {
  const c = h("section", "pj-ufs");
  c.append(h("h2", "pj-h", "Onde mais oscilou contra o 1º turno"), h("p", "pj-ufs-sub", "Flávio entre os dois, em %; oscilação no mesmo estágio"));
  const top = ufsQueMaisOscilaram(p.ufs);
  if (top.length === 0) {
    c.append(h("p", "d2-vazio", "nenhuma UF com votos observados ainda"));
    return c;
  }
  const t = h("table", "pj-tab");
  t.innerHTML = `<thead><tr><th>UF</th><th>1º turno</th><th>agora</th><th>projeção</th><th>oscilação</th></tr></thead>`;
  const corpo = h("tbody");
  for (const u of top) {
    const tr = h("tr");
    const td = (v: string, classe = "num"): HTMLElement => h("td", classe, v);
    tr.append(
      td(u.sigla, "pj-tab-uf"),
      td(u.p1_f === null ? "–" : decimal(u.p1_f, 1)),
      td(u.observado.p_f === null ? "–" : decimal(u.observado.p_f, 1)),
      td(u.projetado ? decimal(u.projetado.p_f, 1) : "–"),
      td(comSinal(u.swing_pp, 1)),
    );
    corpo.append(tr);
  }
  t.append(corpo);
  c.append(t);
  return c;
}

function rodapeProjecao(p: Projecao): HTMLElement {
  const r = h("div", "pj-rodape");
  const par = p.parametros;
  r.append(
    h("p", "pj-rotulo", `${(p.rotulo || ROTULO_PROJECAO).replace(/^./, x => x.toUpperCase())}.`),
    h(
      "p",
      "pj-param",
      `Oscilação de cada município contra o 1º turno no mesmo estágio da contagem, puxada para a média da UF quando há poucos votos (K = ${inteiro(par.K)} votos); faixa de ${inteiro(par.nivel_faixa)}% por ${inteiro(par.reps)} reamostragens de municípios mais ${decimal(par.erro_comum_pp, 1)} ponto de erro comum; projeção a partir de ${decimal(par.minimo_pst, 0)}% das seções.`,
    ),
  );
  return r;
}

export function criarProjecao() {
  let raiz: HTMLElement | null = null;
  return criarTela2T({
    id: "projecao",
    dwell: 24,
    cheia: true,
    needs: s => [{ tipo: "doist", rota: "projecao" }, { tipo: "resultado", ele: eleicaoDe(s, 1), cargo: 1, abr: "br" }, { tipo: "estado" }],
    montar(p) {
      raiz = montarComAviso(p.corpo, "pj", `<div class="pj-esq"></div><div class="pj-dir"></div><div class="pj-pe"></div>`);
    },
    chips(s) {
      const r = dados(s, "projecao");
      return [chipAndamento(r?.cobertura.pst ?? s.estado?.br.pst ?? 0, false), chip("projeção, não é resultado", "aviso")];
    },
    entradas: s => [s.doist.projecao, s.resultados[chaveResultado(eleicaoDe(s, 1), 1, "br")], s.cores],
    atualizar(s, p) {
      if (!raiz) return;
      const pr = dados(s, "projecao");
      if (!atualizarAviso(p.corpo, s, "projecao", "Projeção") || !pr) return;
      const esq = raiz.querySelector<HTMLElement>(".pj-esq");
      const dir = raiz.querySelector<HTMLElement>(".pj-dir");
      const pe = raiz.querySelector<HTMLElement>(".pj-pe");
      if (!esq || !dir || !pe) return;
      const lados = ladosDaProjecao(s, pr);
      const b = pr.brasil;
      const cab = h("div", "pj-cab");
      cab.append(h("p", "pj-cab-t", "Como termina se o resto seguir o que já foi totalizado, em % dos válidos"));
      const topo = h("div", "pj-topo");
      if (b.projetado) {
        topo.append(cartaoLado(lados[0], b), h("p", "pj-x", "×"), cartaoLado(lados[1], b));
      } else {
        const v = h("div", "pj-semproj");
        v.append(h("p", "pj-semproj-t", "Ainda sem base para projetar"), h("p", "pj-semproj-m", pr.motivo_sem_projecao ?? "aguardando as primeiras seções"));
        topo.append(v);
      }
      const graf = h("div", "pj-graf");
      graf.innerHTML = graficoProjecaoSvg(pr.serie, lados, 1160, 420);
      const leg = h("p", "pj-leg", "linha cheia: projeção do final, com a faixa de 90% sombreada; tracejada: totalizado até a hora");
      esq.replaceChildren(cab, topo, barraFaixa(lados, b), totalizado(lados, pr), graf, leg);
      dir.replaceChildren(cobertura(pr), tabelaUfs(pr));
      pe.replaceChildren(rodapeProjecao(pr));
    },
    desmontar() {
      raiz = null;
    },
  });
}
