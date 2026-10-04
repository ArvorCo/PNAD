// Tela `exterior`: voto para presidente nas 186 cidades do exterior (UF `zz` do TSE).
// Palco com o mapa-múndi de bolhas (área pelo eleitorado, cor do líder em bandas de
// seções totalizadas); painel com o ranking executivo do agregado do exterior e a lista
// das cidades com mais eleitores. Clicar numa bolha (ou numa linha da lista) troca o
// ranking para a cidade sem sair da tela; Backspace ou clique fora das bolhas volta.

import { chip } from "../components/chip.ts";
import { criarMundo } from "../components/mundo.ts";
import type { Mapa as MapaComp } from "../components/mapa.ts";
import { NAO_INICIADO } from "../data/cores.ts";
import { inteiro, nomeProprio, pct } from "../data/format.ts";
import type { Diff, Need, Resultado, State, UnidadeMapa } from "../state/types.ts";
import { chaveMapa, chaveResultado } from "../state/types.ts";
import type { View } from "./registry.ts";
import { partes, pedirDados } from "./registry.ts";
import {
  assinaturaDeCores,
  chipDeAndamento,
  coresDoRecorte,
  corDaUnidade,
  criarPainelExecutivo,
  criarPalco,
  definirChips,
  desenharLegenda,
  eleicaoDe,
  lembrarCargo,
  legendaDosLideres,
  unidadeEmpatada,
} from "./executivo.ts";
import type { ItemLegenda, PainelExecutivo, Palco } from "./executivo.ts";

/** Sigla do exterior no TSE (minúscula na abrangência, maiúscula nas chaves do cliente). */
export const ABR_EXTERIOR = "zz";
const UF_EXTERIOR = "ZZ";
const CARGO = 1;
/** Linhas do ranking, contando "outros". */
const MAX_RANKING = 6;
/** Cidades na lista do painel. */
export const TOP_CIDADES = 8;

/** Unidades do exterior: cadastro do config como base (eleitorado, cinza) e o mapa do TSE por cima. */
export function unidadesDoExterior(s: State, mapa: readonly UnidadeMapa[] | undefined): UnidadeMapa[] {
  const porCd = new Map<string, UnidadeMapa>();
  for (const m of s.config?.municipios[UF_EXTERIOR] ?? []) {
    porCd.set(m.cd, { cd: m.cd, nm: m.nm, pst: 0, tf: false, ...(m.te !== undefined ? { te: m.te } : {}) });
  }
  for (const u of mapa ?? []) {
    const base = porCd.get(u.cd);
    porCd.set(u.cd, { ...u, te: u.te ?? base?.te });
  }
  return [...porCd.values()];
}

/** As `n` cidades de maior eleitorado, desempate pelo código. */
export function maioresCidades(unidades: readonly UnidadeMapa[], n = TOP_CIDADES): UnidadeMapa[] {
  return [...unidades].sort((a, b) => (b.te ?? 0) - (a.te ?? 0) || a.cd.localeCompare(b.cd)).slice(0, n);
}

const LEGENDA_EXTERIOR: readonly ItemLegenda[] = [
  { cor: "linear-gradient(90deg, #f4f0e6, #8a8f98)", texto: "claro = poucas seções totalizadas", classe: "fixa" },
  { cor: "transparent", texto: "tamanho = eleitorado", classe: "fixa bolha" },
  { cor: NAO_INICIADO, texto: "cinza = não iniciado", classe: "fixa" },
];

const VAZIO_EXTERIOR = "nenhuma seção do exterior totalizada ainda";

interface LinhaTop {
  li: HTMLLIElement;
  nome: HTMLElement;
  marca: HTMLElement;
  lider: HTMLElement;
  pct: HTMLElement;
  pst: HTMLElement;
}

export function criarExterior(): View {
  let raiz: HTMLElement | null = null;
  let palco: Palco | null = null;
  let painel: PainelExecutivo | null = null;
  let mapa: MapaComp | null = null;
  let cabCidade: HTMLElement | null = null;
  let chipCidade: HTMLElement | null = null;
  let chipsCidade: HTMLElement | null = null;
  let caixaPainel: HTMLElement | null = null;
  let listaTop: HTMLOListElement | null = null;
  const linhasTop: LinhaTop[] = [];
  let cidade: string | null = null;
  let ultimoState: State | null = null;
  let cores: Map<string, string> = new Map();
  let ultimoR: Resultado | null | undefined;
  let ultimaRef: Resultado | null | undefined;
  let ultimasUnidades: UnidadeMapa[] = [];
  let assinaturaMapa = "";

  const nomeDaCidade = (cd: string): string => {
    const u = ultimasUnidades.find(x => x.cd === cd);
    return u ? nomeProprio(u.nm) : cd;
  };

  const escolher = (cd: string | null): void => {
    if (cd === cidade) return;
    cidade = cd;
    mapa?.destacar(cd);
    if (ultimoState) render(ultimoState);
    pedirDados();
  };

  const criarLinhaTop = (): LinhaTop => {
    const li = document.createElement("li");
    li.className = "ext-top-linha";
    const nome = document.createElement("span");
    nome.className = "ext-top-nome corte";
    const quem = document.createElement("span");
    quem.className = "ext-top-quem";
    const marca = document.createElement("i");
    const lider = document.createElement("span");
    lider.className = "corte";
    quem.append(marca, lider);
    const p = document.createElement("span");
    p.className = "ext-top-pct num";
    const pst = document.createElement("span");
    pst.className = "ext-top-pst num";
    li.append(nome, quem, p, pst);
    li.addEventListener("click", () => {
      const cd = li.dataset.cd;
      if (cd) escolher(cd === cidade ? null : cd);
    });
    return { li, nome, marca, lider, pct: p, pst };
  };

  const render = (s: State): void => {
    if (!raiz || !palco || !painel || !mapa) return;
    const ele = eleicaoDe(s, CARGO);
    const rZz = s.resultados[chaveResultado(ele, CARGO, ABR_EXTERIOR)] ?? null;
    const ref = s.resultados[chaveResultado(ele, CARGO, "br")] ?? null;
    if (rZz !== ultimoR || ref !== ultimaRef) {
      cores = coresDoRecorte(s, rZz, ref);
      ultimoR = rZz;
      ultimaRef = ref;
    }

    // título
    const p = partes(raiz);
    definirChips(p.chips, rZz ? [chipDeAndamento(rZz.s, rZz.tf)] : []);

    // mapa
    const dados = s.mapas[chaveMapa(ele, CARGO, "mun", ABR_EXTERIOR)];
    const unidades = unidadesDoExterior(s, dados?.unidades);
    ultimasUnidades = unidades;
    const assin = `${assinaturaDeCores(cores)}#${unidades.map(u => `${u.cd}:${u.te ?? 0}:${u.pst}:${u.lider?.sqcand ?? ""}:${u.lider?.vap ?? 0}`).join(",")}`;
    if (assin !== assinaturaMapa) {
      assinaturaMapa = assin;
      mapa.update(unidades);
    }
    mapa.destacar(cidade);
    desenharLegenda(palco.legenda, [...legendaDosLideres(unidades, cores), ...LEGENDA_EXTERIOR]);
    const fechadas = unidades.filter(u => u.tf || u.pst >= 100).length;
    const paradas = unidades.filter(u => !(u.pst > 0)).length;
    const parciais = unidades.length - fechadas - paradas;
    palco.rodape.textContent =
      unidades.length === 0
        ? "o cadastro das cidades do exterior ainda não chegou"
        : paradas === unidades.length
          ? VAZIO_EXTERIOR
          : `cidades: ${inteiro(fechadas)} encerradas, ${inteiro(parciais)} parciais, ${inteiro(paradas)} não iniciadas`;

    // painel: agregado do exterior ou a cidade escolhida
    if (cidade) {
      const nome = nomeDaCidade(cidade);
      const rCid = s.resultados[chaveResultado(ele, CARGO, `${ABR_EXTERIOR}${cidade}`)] ?? null;
      const coresCid = coresDoRecorte(s, rCid, ref);
      if (chipCidade) chipCidade.textContent = `cidade: ${nome}`;
      if (cabCidade) cabCidade.hidden = false;
      caixaPainel?.classList.add("com-cidade");
      if (chipsCidade) definirChips(chipsCidade, rCid ? [chipDeAndamento(rCid.s, rCid.tf)] : []);
      const vazio = rCid ? `nenhuma seção de ${nome} totalizada ainda` : `aguardando o arquivo de ${nome} no servidor`;
      painel.update(s, rCid, coresCid, vazio);
    } else {
      if (cabCidade) cabCidade.hidden = true;
      caixaPainel?.classList.remove("com-cidade");
      painel.update(s, rZz, cores, VAZIO_EXTERIOR);
    }

    // cidades com mais eleitores
    const top = maioresCidades(unidades);
    if (listaTop) {
      while (linhasTop.length < top.length) {
        const l = criarLinhaTop();
        linhasTop.push(l);
        listaTop.appendChild(l.li);
      }
      linhasTop.forEach((l, i) => {
        const u = top[i];
        l.li.hidden = !u;
        if (!u) return;
        l.li.dataset.cd = u.cd;
        l.li.classList.toggle("escolhida", u.cd === cidade);
        l.nome.textContent = nomeProprio(u.nm);
        const temLider = !!u.lider && u.lider.vap > 0 && u.pst > 0;
        const empate = temLider && unidadeEmpatada(u);
        l.marca.style.background = temLider ? corDaUnidade(u, cores, CARGO, s) : NAO_INICIADO;
        l.lider.textContent = !temLider ? "aguardando" : empate ? "empate" : nomeProprio(u.lider?.nmu ?? "");
        l.pct.textContent = temLider && !empate ? pct(u.lider?.pvapn ?? 0) : "";
        l.pst.textContent = `seções ${inteiro(Math.floor(u.pst))}%`;
        l.li.title = `${nomeProprio(u.nm)}: ${inteiro(u.te ?? 0)} eleitores`;
      });
    }
  };

  return {
    id: "exterior",
    dwell: 25,
    titulo: () => "Voto no exterior",
    needs(s) {
      const ele = eleicaoDe(s, CARGO);
      const ns: Need[] = [
        { tipo: "estado" },
        { tipo: "resultado", ele, cargo: CARGO, abr: ABR_EXTERIOR },
        { tipo: "mapa", ele, cargo: CARGO, nivel: "mun", pai: ABR_EXTERIOR },
        { tipo: "resultado", ele, cargo: CARGO, abr: "br" },
      ];
      if (cidade) ns.push({ tipo: "resultado", ele, cargo: CARGO, abr: `${ABR_EXTERIOR}${cidade}` });
      return ns;
    },
    mount(el) {
      raiz = el;
      lembrarCargo(CARGO);
      el.classList.add("tela--executivo", "tela--exterior");
      const p = partes(el);
      palco = criarPalco(p.corpo);
      mapa = criarMundo(palco.mapaEl, {
        cor: u => (ultimoState ? corDaUnidade(u, cores, CARGO, ultimoState) : NAO_INICIADO),
        titulo: u =>
          `${nomeProprio(u.nm)}: ${u.lider && u.lider.vap > 0 ? `${nomeProprio(u.lider.nmu)} ${pct(u.lider.pvapn)}` : "sem votos totalizados"}`,
        aoClicar: u => escolher(u.cd === cidade ? null : u.cd),
        aoClicarFundo: () => escolher(null),
      });

      const caixa = document.createElement("div");
      caixa.className = "ext-painel";
      cabCidade = document.createElement("div");
      cabCidade.className = "ext-cab";
      cabCidade.hidden = true;
      chipCidade = chip("cidade", "primeiro");
      chipsCidade = document.createElement("span");
      chipsCidade.className = "ext-cab-chips";
      const voltar = document.createElement("button");
      voltar.type = "button";
      voltar.className = "ext-voltar";
      voltar.textContent = "voltar ao exterior";
      voltar.addEventListener("click", () => escolher(null));
      const esquerda = document.createElement("span");
      esquerda.className = "ext-cab-esq";
      esquerda.append(chipCidade, chipsCidade);
      cabCidade.append(esquerda, voltar);
      caixaPainel = caixa;
      painel = criarPainelExecutivo({ max: MAX_RANKING, nvLidera: 0, casas: 1, fotoPx: 48 });
      const secao = document.createElement("section");
      secao.className = "ext-top";
      const h = document.createElement("h2");
      h.className = "ext-top-titulo";
      h.textContent = "cidades com mais eleitores";
      listaTop = document.createElement("ol");
      listaTop.className = "ext-top-lista";
      secao.append(h, listaTop);
      caixa.append(cabCidade, painel.el, secao);
      p.painel.replaceChildren(caixa);
    },
    update(s: State, _diff: Diff) {
      ultimoState = s;
      render(s);
    },
    keys(tecla) {
      if (tecla !== "Backspace" || !cidade) return false;
      escolher(null);
      return true;
    },
    unmount() {
      painel?.destroy();
      mapa?.destroy();
      painel = null;
      mapa = null;
      palco = null;
      raiz = null;
      cabCidade = null;
      chipCidade = null;
      chipsCidade = null;
      caixaPainel = null;
      listaTop = null;
      linhasTop.length = 0;
      ultimoState = null;
    },
  };
}
