// Template "proporcional" para fed-uf (6259/6), est-uf (6259/7) e dis-df (6259/8, DF fixo).
// Palco: 18 mais votados com acumulado (SP tem 1.346 candidaturas: ordena uma vez por
// snapshot e desenha só 18) e a linha dos demais. Painel: votos por campo (nominais e
// legenda), 10 maiores partidos e, quando o TSE marcar eleitos, eleitos por campo; sem
// eleitos e com pst ≥ 70, a distribuição provisória por quociente eleitoral e sobras.

import { alocarCadeiras } from "../components/cadeiras.ts";
import type { AgremiacaoEntrada } from "../components/cadeiras.ts";
import { chip, chipAndamento, chipSituacao, trocarChips } from "../components/chip.ts";
import { foto } from "../components/foto.ts";
import { corCampo, mix, PAPEL } from "../data/cores.ts";
import { compacto, inteiro, nomeProprio, pct } from "../data/format.ts";
import { agregarPorCampo, ranking } from "../state/selectors.ts";
import type { Campo, Campos, Candidato, PartidoResultado, Resultado, State } from "../state/types.ts";
import { chaveResultado } from "../state/types.ts";
import { rotuloCampo } from "./governadores.ts";
import { tituloDaTela } from "./index.ts";
import type { View } from "./registry.ts";
import { nomeUf, partes } from "./registry.ts";

const ELE = 6259;
const LINHAS = 18;
const PARTIDOS = 10;
export const PST_PROJECAO = 70;

export interface OpcoesProporcional {
  id: "fed-uf" | "est-uf" | "dis-df";
  cargo: 6 | 7 | 8;
}

const NOME_CARGO: Readonly<Record<number, string>> = { 6: "deputado federal", 7: "deputado estadual", 8: "deputado distrital" };

const valido = (c: Candidato): boolean => !c.dvt || /^v[aá]lido/i.test(c.dvt);
const eleito = (c: Candidato): boolean => c.e || /^eleit/i.test(c.st);

export interface Preparado {
  ordem: Candidato[];
  totalNominal: number;
}

/** Ordena uma vez por snapshot. */
export function preparar(r: Resultado): Preparado {
  const ordem = ranking(r.cand);
  const soma = ordem.reduce((s, c) => s + (valido(c) ? c.vap : 0), 0);
  return { ordem, totalNominal: r.v.vnom > 0 ? r.v.vnom : soma };
}

/** Agremiação (federação ou partido) de cada sigla, pelos candidatos. */
export function agremiacoes(r: Resultado): AgremiacaoEntrada[] {
  const deSigla = new Map<string, string>();
  for (const c of r.cand) deSigla.set(c.sg, c.fed_sg || c.sg);
  const votos = new Map<string, number>();
  for (const p of r.partidos) {
    const id = deSigla.get(p.sg) ?? p.sg;
    // Nominais mais legenda; tvan inclui nominais e sub judice, somar com ele contaria duas vezes.
    votos.set(id, (votos.get(id) ?? 0) + p.tvtn + (p.tvtl ?? 0));
  }
  const cands = new Map<string, number[]>();
  for (const c of r.cand) {
    if (!valido(c)) continue;
    const id = c.fed_sg || c.sg;
    const l = cands.get(id) ?? [];
    l.push(c.vap);
    cands.set(id, l);
    if (!votos.has(id)) votos.set(id, 0);
  }
  return [...votos.entries()].map(([id, v]) => ({ id, votos: v, candidatos: cands.get(id) ?? [] }));
}

/** Campo da agremiação: o do partido mais votado dentro dela. */
function campoDaAgremiacao(r: Resultado): Map<string, Campo> {
  const deSigla = new Map<string, string>();
  for (const c of r.cand) deSigla.set(c.sg, c.fed_sg || c.sg);
  const melhor = new Map<string, PartidoResultado>();
  for (const p of r.partidos) {
    const id = deSigla.get(p.sg) ?? p.sg;
    const atual = melhor.get(id);
    if (!atual || p.tvtn + p.tvan > atual.tvtn + atual.tvan) melhor.set(id, p);
  }
  const saida = new Map<string, Campo>();
  for (const [id, p] of melhor) saida.set(id, p.campo);
  for (const c of r.cand) if (!saida.has(c.fed_sg || c.sg)) saida.set(c.fed_sg || c.sg, c.campo);
  return saida;
}

const ORDEM: readonly Campo[] = ["esquerda", "centro-esquerda", "centro", "centro-direita", "direita", "indefinido"];

/** Quadrados por campo, da esquerda para a direita. */
function quadrados(porCampo: Map<Campo, number>): Campo[] {
  return ORDEM.flatMap(c => new Array<Campo>(porCampo.get(c) ?? 0).fill(c));
}

export function criarProporcional(o: OpcoesProporcional): View {
  let raiz: HTMLElement | null = null;
  let ultimoResultado: Resultado | undefined;
  let preparado: Preparado | null = null;
  let ultimosCampos: Campos | null = null;

  const ufDe = (s: State): string => (o.id === "dis-df" ? "DF" : (s.ui.uf ?? "SP").toUpperCase());
  const chave = (s: State): string => chaveResultado(ELE, o.cargo, ufDe(s).toLowerCase());

  return {
    id: o.id,
    dwell: 25,
    titulo: s => tituloDaTela(o.id, s, ufDe(s)),
    needs: s => [{ tipo: "resultado", ele: ELE, cargo: o.cargo, abr: ufDe(s).toLowerCase() }, { tipo: "estado" }],
    mount(el) {
      raiz = el;
      const p = partes(el);
      p.corpo.innerHTML = `
        <div class="pr">
          <div class="pr-cab"><span>#</span><span></span><span>candidatura</span><span>partido</span><span class="pr-num">votos</span><span class="pr-num">válidos</span><span>acumulado</span></div>
          <ol class="pr-lista"></ol>
          <p class="pr-rodape"></p>
        </div>`;
      p.painel.innerHTML = `
        <div class="pr-painel">
          <section><h2>votos por campo</h2><div class="pr-campos-barra"></div><ul class="pr-campos-leg"></ul></section>
          <section><h2>partidos mais votados</h2><ol class="pr-partidos"></ol></section>
          <section class="pr-cadeiras"><h2></h2><div class="pr-quadros"></div><p class="pr-cad-nota"></p></section>
        </div>`;
    },
    update(s: State) {
      if (!raiz) return;
      const p = partes(raiz);
      const r = s.resultados[chave(s)];
      const uf = ufDe(s);
      if (!r) {
        trocarChips(p.chips, [chipAndamento(0, false)]);
        const lista = raiz.querySelector(".pr-lista");
        if (lista) lista.innerHTML = `<li class="pr-vazio">aguardando o resultado de ${NOME_CARGO[o.cargo]} em ${nomeUf(s, uf)}</li>`;
        const rod = raiz.querySelector(".pr-rodape");
        if (rod) rod.textContent = "";
        return;
      }
      if (r !== ultimoResultado || !preparado) {
        preparado = preparar(r);
      }
      const mudouCampos = s.campos !== ultimosCampos;
      ultimosCampos = s.campos;
      if (r === ultimoResultado && !mudouCampos) return;
      ultimoResultado = r;

      const eleitos = r.cand.filter(eleito);
      const projetar = eleitos.length === 0 && r.s.pst >= PST_PROJECAO;
      trocarChips(p.chips, [
        chipAndamento(r.s.pst, r.tf),
        chip(`${r.cargo.nv} vagas`, "neutro"),
        projetar ? chip("projeção provisória", "primeiro") : null,
      ]);
      desenharLista(raiz, preparado, s.campos);
      desenharPainel(raiz, r, s.campos, eleitos, projetar);
    },
    unmount() {
      raiz = null;
      preparado = null;
    },
  };
}

function desenharLista(raiz: HTMLElement, pr: Preparado, campos: Campos): void {
  const lista = raiz.querySelector<HTMLElement>(".pr-lista");
  const rodape = raiz.querySelector<HTMLElement>(".pr-rodape");
  if (!lista || !rodape) return;
  const comVoto = pr.ordem.filter(c => c.vap > 0);
  if (comVoto.length === 0) {
    lista.innerHTML = `<li class="pr-vazio">nenhum voto nominal apurado ainda</li>`;
    rodape.textContent = `${inteiro(pr.ordem.length)} candidaturas aguardando seções`;
    return;
  }
  const top = comVoto.slice(0, LINHAS);
  const total = pr.totalNominal || 1;
  let acum = 0;
  const acumulados = top.map(c => (acum += c.vap));
  const escala = acum || 1;
  const itens = top.map((c, i) => {
    const li = document.createElement("li");
    li.className = "pr-linha";
    if (!valido(c)) li.classList.add("pr-linha--subjudice");
    const cor = corCampo(c.campo, campos);
    const pos = document.createElement("span");
    pos.className = "pr-pos";
    pos.textContent = String(i + 1);
    const nome = document.createElement("span");
    nome.className = "pr-nome";
    const nm = document.createElement("span");
    nm.className = "pr-nm";
    nm.textContent = nomeProprio(c.nmu);
    nome.append(nm);
    const sit = chipSituacao(c.st, c.e, c.dvt);
    if (sit) nome.append(sit);
    const partido = document.createElement("span");
    partido.className = "pr-partido";
    partido.textContent = c.sg;
    const votos = document.createElement("span");
    votos.className = "pr-num";
    votos.textContent = inteiro(c.vap);
    const pc = document.createElement("span");
    pc.className = "pr-num";
    pc.textContent = pct(c.pvapn, 2);
    const barra = document.createElement("span");
    barra.className = "pr-acum";
    const antes = document.createElement("i");
    const proprio = document.createElement("i");
    const anterior = acumulados[i - 1] ?? 0;
    antes.style.width = `${(100 * anterior) / escala}%`;
    antes.style.background = mix(PAPEL, "#5f6773", 0.35);
    proprio.style.width = `${(100 * c.vap) / escala}%`;
    proprio.style.background = cor;
    barra.append(antes, proprio);
    li.append(pos, foto({ sqcand: c.sqcand, nome: c.nmu, tamanho: 40, cor }), nome, partido, votos, pc, barra);
    return li;
  });
  lista.replaceChildren(...itens);
  const resto = comVoto.length - top.length + (pr.ordem.length - comVoto.length);
  const votosResto = total - (acumulados[acumulados.length - 1] ?? 0);
  rodape.textContent =
    resto > 0
      ? `outros ${inteiro(resto)} candidatos: ${pct((100 * Math.max(0, votosResto)) / total)} dos nominais`
      : "todas as candidaturas estão na lista";
}

function desenharPainel(raiz: HTMLElement, r: Resultado, campos: Campos, eleitos: readonly Candidato[], projetar: boolean): void {
  // Votos por campo: nominais em cor cheia, legenda em tom claro ao lado.
  const barra = raiz.querySelector<HTMLElement>(".pr-campos-barra");
  const leg = raiz.querySelector<HTMLElement>(".pr-campos-leg");
  const nominais = agregarPorCampo(r.partidos, x => x.campo, x => x.tvtn);
  const legenda = new Map(agregarPorCampo(r.partidos, x => x.campo, x => x.tvan).map(f => [f.campo, f.votos]));
  const total = nominais.reduce((s, f) => s + f.votos, 0) + [...legenda.values()].reduce((s, v) => s + v, 0);
  const camposVistos = ORDEM.filter(c => nominais.some(f => f.campo === c) || legenda.has(c));
  if (barra && leg) {
    if (!(total > 0)) {
      barra.replaceChildren();
      leg.innerHTML = `<li class="pr-vazio-painel">nenhum voto apurado por partido ainda</li>`;
    } else {
      const segs: HTMLElement[] = [];
      const itens: HTMLElement[] = [];
      for (const c of camposVistos) {
        const vn = nominais.find(f => f.campo === c)?.votos ?? 0;
        const vl = legenda.get(c) ?? 0;
        const cor = corCampo(c, campos);
        const a = document.createElement("i");
        a.style.width = `${(100 * vn) / total}%`;
        a.style.background = cor;
        const b = document.createElement("i");
        b.style.width = `${(100 * vl) / total}%`;
        b.style.background = mix(PAPEL, cor, 0.45);
        segs.push(a, b);
        const li = document.createElement("li");
        const sw = document.createElement("i");
        sw.style.background = cor;
        const v = document.createElement("b");
        v.textContent = pct((100 * (vn + vl)) / total);
        li.append(sw, document.createTextNode(`${rotuloCampo(c, campos)} `), v);
        itens.push(li);
      }
      barra.replaceChildren(...segs);
      leg.replaceChildren(...itens);
    }
  }

  // Partidos mais votados.
  const ol = raiz.querySelector<HTMLElement>(".pr-partidos");
  if (ol) {
    const ps = [...r.partidos].filter(x => x.tvtn + x.tvan > 0).sort((a, b) => b.tvtn + b.tvan - (a.tvtn + a.tvan)).slice(0, PARTIDOS);
    const maior = ps[0] ? ps[0].tvtn + ps[0].tvan : 1;
    if (ps.length === 0) ol.innerHTML = `<li class="pr-vazio-painel">nenhum partido com votos apurados ainda</li>`;
    else
      ol.replaceChildren(
        ...ps.map(x => {
          const li = document.createElement("li");
          const cor = corCampo(x.campo, campos);
          const sg = document.createElement("span");
          sg.className = "pr-p-sg";
          const dot = document.createElement("i");
          dot.style.background = cor;
          sg.append(dot, document.createTextNode(x.sg));
          const v = document.createElement("span");
          v.className = "pr-num";
          v.textContent = compacto(x.tvtn + x.tvan);
          const pc = document.createElement("span");
          pc.className = "pr-num";
          pc.textContent = total > 0 ? pct((100 * (x.tvtn + x.tvan)) / total) : "";
          const bar = document.createElement("span");
          bar.className = "pr-p-barra";
          const n = document.createElement("i");
          n.style.width = `${(100 * x.tvtn) / maior}%`;
          n.style.background = cor;
          const l = document.createElement("i");
          l.style.width = `${(100 * x.tvan) / maior}%`;
          l.style.background = mix(PAPEL, cor, 0.45);
          l.title = "votos de legenda";
          bar.append(n, l);
          li.append(sg, v, pc, bar);
          return li;
        }),
      );
  }

  // Cadeiras: eleitos pelo TSE ou projeção provisória.
  const sec = raiz.querySelector<HTMLElement>(".pr-cadeiras");
  if (!sec) return;
  const h = sec.querySelector("h2");
  const quadros = sec.querySelector<HTMLElement>(".pr-quadros");
  const nota = sec.querySelector<HTMLElement>(".pr-cad-nota");
  if (!h || !quadros || !nota) return;
  let porCampo: Map<Campo, number> | null = null;
  if (eleitos.length > 0) {
    h.textContent = "eleitos por campo, segundo o TSE";
    porCampo = new Map();
    for (const c of eleitos) porCampo.set(c.campo, (porCampo.get(c.campo) ?? 0) + 1);
    nota.textContent = `${eleitos.length} de ${r.cargo.nv} vagas com eleito marcado pelo TSE`;
  } else if (projetar) {
    h.textContent = "cadeiras por campo, projeção provisória";
    const res = alocarCadeiras(r.cargo.nv, agremiacoes(r), r.v.vv > 0 ? r.v.vv : undefined);
    const campoDe = campoDaAgremiacao(r);
    porCampo = new Map();
    for (const [id, c] of Object.entries(res.porAgremiacao)) {
      if (c.total <= 0) continue;
      const campo = campoDe.get(id) ?? "indefinido";
      porCampo.set(campo, (porCampo.get(campo) ?? 0) + c.total);
    }
    nota.textContent = `quociente eleitoral de ${inteiro(res.qe)} votos com ${pct(r.s.pst)} das seções; muda até o fim da apuração`;
  } else {
    h.textContent = "cadeiras por campo";
    nota.textContent = `a distribuição provisória de cadeiras aparece a partir de ${PST_PROJECAO}% das seções apuradas`;
  }
  if (!porCampo) {
    quadros.replaceChildren();
    return;
  }
  const lista = quadrados(porCampo);
  const vagos = Math.max(0, r.cargo.nv - lista.length);
  quadros.replaceChildren(
    ...lista.map(c => {
      const i = document.createElement("i");
      i.style.background = corCampo(c, campos);
      i.title = rotuloCampo(c, campos);
      return i;
    }),
    ...Array.from({ length: vagos }, () => {
      const i = document.createElement("i");
      i.className = "pr-quadro-vago";
      return i;
    }),
  );
}
