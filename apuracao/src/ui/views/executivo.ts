// Template executivo: palco com mapa (municípios da UF ou zonas do município) e painel
// com ranking, diferença entre 1º e 2º, válidos/brancos/nulos e hora da totalização.
// Usado por pres-uf, gov-uf, sen-uf e mun; presidente.ts reaproveita o painel e os
// auxiliares de cor, chips e navegação.

import { chip, trocarChips } from "../components/chip.ts";
import type { TipoChip } from "../components/chip.ts";
import { criarBarraValidos } from "../components/barraValidos.ts";
import { criarMapa } from "../components/mapa.ts";
import type { Mapa as MapaComp, MapaOpcoes } from "../components/mapa.ts";
import { COR_EMPATE, coresEstaduais, coresPresidente, criarRanking, empateNoTopo } from "../components/ranking.ts";
import { escreverHash, lerHash } from "../control/router.ts";
import type { UiHash } from "../control/router.ts";
import { corCampo, corCandidato, corPorBanda, NAO_INICIADO } from "../data/cores.ts";
import { decimal, duracao, hora, inteiro, nomeProprio, pct } from "../data/format.ts";
import { ranking } from "../state/selectors.ts";
import type { Candidato, Diff, Mapa, Need, NivelMapa, Resultado, State, UnidadeMapa } from "../state/types.ts";
import { abrDe, chaveMapa, chaveResultado } from "../state/types.ts";
import type { View } from "./registry.ts";
import { nomeUf, partes } from "./registry.ts";

// ---------- eleição, cargo e navegação ----------

export const ELEICAO_FEDERAL_PADRAO = 6257;
export const ELEICAO_ESTADUAL_PADRAO = 6259;

export const NOME_CARGO: Readonly<Record<number, string>> = { 1: "presidente", 3: "governador", 5: "senado" };

/** Presidente é eleição federal; governador e senado, estadual. */
export function eleicaoDe(s: State, cargo: number): number {
  return cargo === 1
    ? (s.config?.eleicoes.federal ?? ELEICAO_FEDERAL_PADRAO)
    : (s.config?.eleicoes.estadual ?? ELEICAO_ESTADUAL_PADRAO);
}

// Último cargo majoritário visto: a tela de município herda o recorte de quem a abriu.
let ultimoCargo = 1;
export const lembrarCargo = (cargo: number): void => {
  ultimoCargo = cargo;
};
export const cargoDoMunicipio = (): number => ultimoCargo;

/** Navega pelo hash (o roteador aplica ao store); toda navegação da tela é manual. */
export function navegar(d: Partial<UiHash>): void {
  const atual = lerHash(location.hash);
  const h = escreverHash({ ...atual, auto: false, ...d });
  if (h !== location.hash) location.hash = h;
}

// ---------- cores ----------

/** Cor por candidato no recorte: presidente pela tabela fixa e sequência; estaduais pelo campo. */
export function coresDoRecorte(s: State, r: Resultado | null, referencia: Resultado | null): Map<string, string> {
  if (!r) return new Map();
  if (r.cargo.cd === 1) return coresPresidente(r.cand, s.cores, referencia?.cand ?? r.cand);
  return coresEstaduais(r.cand, s.campos);
}

/** Empate exato entre 1º e 2º numa unidade do mapa. */
export const unidadeEmpatada = (u: UnidadeMapa): boolean =>
  !!u.lider && !!u.segundo && u.lider.vap > 0 && u.lider.vap === u.segundo.vap;

/** Cor da unidade pelo líder, em bandas de seções totalizadas; cinza sem voto; neutra no empate. */
export function corDaUnidade(u: UnidadeMapa, cores: ReadonlyMap<string, string>, cargo: number, s: State): string {
  if (!u.lider || !(u.lider.vap > 0) || !(u.pst > 0)) return NAO_INICIADO;
  if (unidadeEmpatada(u)) return COR_EMPATE;
  const cor =
    cores.get(u.lider.sqcand) ?? (cargo === 1 ? corCandidato(u.lider.n, 99, s.cores) : corCampo(u.lider.campo, s.campos));
  return corPorBanda(cor, u.pst);
}

// ---------- textos e chips ----------

const plural = (x: number, um: string, varios: string): string => (Math.round(x) === 1 ? um : varios);

/** "4,9 milhões de votos", "320 mil votos", "1 voto". */
export function votosPorExtenso(x: number): string {
  const a = Math.abs(x);
  if (a >= 1e6) {
    const m = decimal(a / 1e6, 1);
    return `${m} ${a < 2e6 ? "milhão" : "milhões"} de votos`;
  }
  if (a >= 1e4) return `${inteiro(a / 1e3)} mil votos`;
  return `${inteiro(a)} ${plural(a, "voto", "votos")}`;
}

/** Linha da diferença entre 1º e 2º. */
export function textoDiferenca(cand: readonly Candidato[]): string {
  const [a, b] = ranking(cand);
  if (!a || !(a.vap > 0)) return "nenhum voto totalizado ainda";
  if (!b) return `${nomeProprio(a.nmu)} é a única candidatura com votos`;
  if (empateNoTopo(cand)) return `empate entre ${nomeProprio(a.nmu)} e ${nomeProprio(b.nmu)}`;
  const pontos = a.pvapn - b.pvapn;
  const p = decimal(pontos, 1);
  return `diferença ${p} ${p === "1,0" ? "ponto" : "pontos"}, ${votosPorExtenso(a.vap - b.vap)}`;
}

/** Chip de andamento: parcial, encerrada, encerrada com seções faltando, aguardando. */
export function chipDeAndamento(s: { ts: number; st: number; pst: number }, tf: boolean): HTMLSpanElement {
  if (tf) {
    const faltam = Math.max(0, s.ts - s.st);
    if (faltam > 0) {
      return chip(`encerrada com ${inteiro(faltam)} ${plural(faltam, "seção não totalizada", "seções não totalizadas")}`, "encerrada");
    }
    return chip("totalização encerrada", "encerrada");
  }
  if (!(s.pst > 0)) return chip("aguardando seções", "neutro");
  return chip(`parcial ${pct(s.pst, 1)}`, "parcial");
}

/** Assinatura para só trocar os chips quando o texto muda. */
export function definirChips(alvo: HTMLElement, itens: { texto: string; tipo: TipoChip }[] | HTMLElement[]): void {
  const els = itens.map(i => (i instanceof HTMLElement ? i : chip(i.texto, i.tipo)));
  const assinatura = els.map(e => `${e.className}:${e.textContent}`).join("|");
  if (alvo.dataset.assinatura === assinatura) return;
  alvo.dataset.assinatura = assinatura;
  trocarChips(alvo, els);
}

const LIMITE_ATRASO_S = 180;

// ---------- painel executivo ----------

export interface PainelExecutivo {
  readonly el: HTMLElement;
  /** `vazio`: frase quando não há resultado ou a totalização ainda não começou. */
  update(s: State, r: Resultado | null, cores: ReadonlyMap<string, string>, vazio: string, cabecalho?: HTMLElement[]): void;
  destroy(): void;
}

export function criarPainelExecutivo(o: { max: number; nvLidera?: number; casas?: 1 | 2; fotoPx?: number }): PainelExecutivo {
  const el = document.createElement("div");
  el.className = "pex";
  const cab = document.createElement("div");
  cab.className = "pex-cab";
  const rk = criarRanking({ max: o.max, nvLidera: o.nvLidera ?? 0, casas: o.casas ?? 1, ...(o.fotoPx ? { fotoPx: o.fotoPx } : {}) });
  const vazioEl = document.createElement("p");
  vazioEl.className = "pex-vazio";
  const dif = document.createElement("p");
  dif.className = "pex-dif";
  const barra = criarBarraValidos();
  const tot = document.createElement("p");
  tot.className = "pex-tot num";
  el.append(cab, vazioEl, rk.el, dif, barra.el, tot);

  return {
    el,
    update(s, r, cores, vazio, cabecalho = []) {
      definirChips(cab, cabecalho);
      cab.hidden = cabecalho.length === 0;
      const semDado = !r || r.cand.length === 0;
      vazioEl.hidden = !semDado && r.s.st > 0;
      vazioEl.textContent = semDado || r.s.st === 0 ? vazio : "";
      const parado = semDado || r.s.st === 0;
      rk.el.hidden = parado;
      if (r) rk.update(r.cand, cores);
      dif.textContent = r && r.s.st > 0 ? textoDiferenca(r.cand) : "";
      dif.hidden = !r || r.s.st === 0;
      barra.update(r);
      barra.el.hidden = parado;
      const quando = hora(r?.dt_ht ?? null);
      // Atraso só faz sentido depois da primeira seção totalizada no país; antes, a última
      // versão gravada é a da véspera e a conta devolve horas.
      const comecou = (s.estado?.br.st ?? 0) > 0;
      const atraso = comecou ? s.estado?.br.atraso_s : null;
      const atrasoTxt = atraso === null || atraso === undefined ? "" : ` (atraso ${duracao(atraso)})`;
      tot.textContent = quando ? `totalização TSE ${quando}${atrasoTxt}` : "o TSE ainda não totalizou seções deste recorte";
      tot.classList.toggle("atrasado", (atraso ?? 0) > LIMITE_ATRASO_S);
    },
    destroy() {
      rk.destroy();
    },
  };
}

// ---------- palco: mapa, legenda e contagem ----------

export interface Palco {
  readonly el: HTMLElement;
  readonly mapaEl: HTMLElement;
  readonly legenda: HTMLElement;
  readonly rodape: HTMLElement;
}

export function criarPalco(corpo: HTMLElement): Palco {
  corpo.innerHTML = `
    <div class="ex-palco">
      <div class="ex-mapa"></div>
      <div class="ex-base"><ul class="ex-legenda"></ul><p class="ex-rodape num"></p></div>
    </div>`;
  const q = (c: string): HTMLElement => corpo.querySelector<HTMLElement>(c) as HTMLElement;
  return { el: q(".ex-palco"), mapaEl: q(".ex-mapa"), legenda: q(".ex-legenda"), rodape: q(".ex-rodape") };
}

export interface ItemLegenda {
  cor: string;
  texto: string;
  classe?: string;
}

export function desenharLegenda(ul: HTMLElement, itens: ItemLegenda[]): void {
  const assinatura = itens.map(i => `${i.cor}:${i.texto}`).join("|");
  if (ul.dataset.assinatura === assinatura) return;
  ul.dataset.assinatura = assinatura;
  ul.replaceChildren(
    ...itens.map(i => {
      const li = document.createElement("li");
      if (i.classe) li.className = i.classe;
      const sw = document.createElement("i");
      sw.style.background = i.cor;
      const t = document.createElement("span");
      t.textContent = i.texto;
      li.append(sw, t);
      return li;
    }),
  );
}

/** Líderes de pelo menos uma unidade, pelo número de unidades lideradas. */
export function legendaDosLideres(unidades: readonly UnidadeMapa[], cores: ReadonlyMap<string, string>, max = 5): ItemLegenda[] {
  const conta = new Map<string, { n: number; nome: string }>();
  for (const u of unidades) {
    if (!u.lider || !(u.lider.vap > 0) || unidadeEmpatada(u)) continue;
    const k = u.lider.sqcand;
    const x = conta.get(k) ?? { n: 0, nome: nomeProprio(u.lider.nmu) };
    x.n += 1;
    conta.set(k, x);
  }
  return [...conta.entries()]
    .sort((a, b) => b[1].n - a[1].n)
    .slice(0, max)
    .map(([k, x]) => ({ cor: cores.get(k) ?? "#8a8f98", texto: x.nome }));
}

export const LEGENDA_FIXA: readonly ItemLegenda[] = [
  { cor: "linear-gradient(90deg, #f4f0e6, #8a8f98)", texto: "claro = poucas seções totalizadas", classe: "fixa" },
  { cor: NAO_INICIADO, texto: "cinza = não iniciado", classe: "fixa" },
];

/** Mapa que só recria quando nível ou pai mudam e só repinta quando os dados mudam. */
export interface MapaVivo {
  definir(container: HTMLElement, nivel: NivelMapa, pai: string, o: Omit<MapaOpcoes, "nivel" | "pai">): void;
  pintar(m: Mapa | undefined, assinaturaCores: string): void;
  destacar(cd: string | null): void;
  destroy(): void;
}

export function criarMapaVivo(): MapaVivo {
  let comp: MapaComp | null = null;
  let chave = "";
  let ultimo: Mapa | undefined;
  let ultimaCor = "";
  let destaque: string | null = null;
  return {
    definir(container, nivel, pai, o) {
      const k = `${nivel}:${pai}`;
      if (k === chave && comp) return;
      comp?.destroy();
      chave = k;
      ultimo = undefined;
      ultimaCor = "";
      comp = criarMapa(container, { nivel, pai, ...o });
      if (destaque) comp.destacar(destaque);
    },
    pintar(m, assinaturaCores) {
      if (!comp || !m) return;
      if (m === ultimo && assinaturaCores === ultimaCor) return;
      ultimo = m;
      ultimaCor = assinaturaCores;
      comp.update(m.unidades);
      if (destaque) comp.destacar(destaque);
    },
    destacar(cd) {
      destaque = cd;
      comp?.destacar(cd);
    },
    destroy() {
      comp?.destroy();
      comp = null;
      chave = "";
    },
  };
}

export const assinaturaDeCores = (cores: ReadonlyMap<string, string>): string =>
  [...cores.entries()].map(([k, v]) => `${k}=${v}`).join(",");

// ---------- fábrica ----------

export interface DefExecutivo {
  id: string;
  /** Cargo fixo, ou null para o município (herda o último cargo majoritário). */
  cargo: 1 | 3 | 5 | null;
  /** Linhas visíveis no ranking, contando "outros". */
  max: number;
  nvLidera: number;
  dwell?: number;
}

const TITULO_CARGO: Readonly<Record<number, string>> = { 1: "Presidente", 3: "Governador", 5: "Senado" };

function municipioDe(s: State, uf: string | null, mun: string | null): { nm: string; c: boolean; z: string[] } | null {
  if (!uf || !mun) return null;
  const m = s.config?.municipios[uf.toUpperCase()]?.find(x => x.cd === mun);
  return m ? { nm: nomeProprio(m.nm), c: m.c, z: m.z } : null;
}

const capitais = (s: State, uf: string): Set<string> =>
  new Set((s.config?.municipios[uf.toUpperCase()] ?? []).filter(m => m.c).map(m => m.cd));

/** Nome curto da zona: "0248" → "zona 0248". */
export const rotuloZona = (z: string): string => `zona ${z.padStart(4, "0")}`;

export function criarExecutivo(def: DefExecutivo): View {
  let raiz: HTMLElement | null = null;
  let painel: PainelExecutivo | null = null;
  let palco: Palco | null = null;
  const mapa = criarMapaVivo();
  let cores: Map<string, string> = new Map();
  let ultimoState: State | null = null;
  let ultimoR: Resultado | null | undefined;
  let ultimaRef: Resultado | null | undefined;

  const cargoDe = (): number => def.cargo ?? cargoDoMunicipio();
  const ehMun = def.cargo === null;

  const abrDoRecorte = (s: State): string | null => {
    if (!s.ui.uf) return null;
    if (!ehMun) return abrDe(s.ui.uf);
    if (!s.ui.mun) return null;
    return abrDe(s.ui.uf, s.ui.mun, s.ui.zonas ? s.ui.zona : null);
  };

  const mapaDoRecorte = (s: State): { nivel: NivelMapa; pai: string } | null => {
    const uf = s.ui.uf?.toLowerCase();
    if (!uf) return null;
    if (ehMun && s.ui.zonas && s.ui.mun) return { nivel: "zona", pai: `${uf}${s.ui.mun}` };
    return { nivel: "mun", pai: uf };
  };

  const titulo = (s: State): string => {
    const cargo = cargoDe();
    if (ehMun) {
      const m = municipioDe(s, s.ui.uf, s.ui.mun);
      return m && s.ui.uf ? `${m.nm}, ${s.ui.uf}` : "Município";
    }
    return s.ui.uf ? `${TITULO_CARGO[cargo] ?? ""}, ${nomeUf(s, s.ui.uf)}` : (TITULO_CARGO[cargo] ?? "");
  };

  const vazioDe = (s: State, r: Resultado | null): string => {
    if (!s.ui.uf) return "nenhuma UF escolhida: digite a sigla de duas letras para abrir o recorte";
    if (ehMun && !s.ui.mun) return "nenhum município escolhido: abra a busca para escolher um";
    if (!r) return "aguardando o primeiro arquivo deste recorte no servidor";
    if (ehMun) {
      return s.ui.zonas && s.ui.zona
        ? "a totalização desta zona ainda não começou"
        : "a totalização deste município ainda não começou";
    }
    return "a totalização deste estado ainda não começou";
  };

  return {
    id: def.id,
    dwell: def.dwell ?? 20,
    titulo,
    needs(s) {
      const cargo = cargoDe();
      const ele = eleicaoDe(s, cargo);
      const ns: Need[] = [{ tipo: "estado" }];
      const abr = abrDoRecorte(s);
      if (abr) ns.push({ tipo: "resultado", ele, cargo, abr });
      const m = mapaDoRecorte(s);
      if (m && (!ehMun || s.ui.mun)) ns.push({ tipo: "mapa", ele, cargo, nivel: m.nivel, pai: m.pai });
      if (cargo === 1) ns.push({ tipo: "resultado", ele, cargo, abr: "br" });
      return ns;
    },
    mount(el) {
      raiz = el;
      if (def.cargo !== null) lembrarCargo(def.cargo);
      el.classList.add("tela--executivo");
      const p = partes(el);
      palco = criarPalco(p.corpo);
      painel = criarPainelExecutivo({ max: def.max, nvLidera: def.nvLidera, casas: 1 });
      p.painel.replaceChildren(painel.el);
    },
    update(s: State, _diff: Diff) {
      if (!raiz || !palco || !painel) return;
      ultimoState = s;
      const cargo = cargoDe();
      const ele = eleicaoDe(s, cargo);
      const abr = abrDoRecorte(s);
      const r = abr ? (s.resultados[chaveResultado(ele, cargo, abr)] ?? null) : null;
      const ref = cargo === 1 ? (s.resultados[chaveResultado(ele, 1, "br")] ?? null) : null;
      if (r !== ultimoR || ref !== ultimaRef) {
        cores = coresDoRecorte(s, r, ref);
        ultimoR = r;
        ultimaRef = ref;
      }

      // chips do título
      const p = partes(raiz);
      const chipsTitulo: HTMLElement[] = [];
      if (ehMun) chipsTitulo.push(chip(NOME_CARGO[cargo] ?? "cargo", "neutro"));
      if (r) chipsTitulo.push(chipDeAndamento(r.s, r.tf));
      definirChips(p.chips, chipsTitulo);

      // painel
      const cab: HTMLElement[] = [];
      if (ehMun && s.ui.zonas && s.ui.zona) {
        const m = municipioDe(s, s.ui.uf, s.ui.mun);
        cab.push(chip(`${rotuloZona(s.ui.zona)} de ${m?.nm ?? "município"}`, "primeiro"));
      } else if (ehMun && s.ui.zonas) {
        cab.push(chip("total do município, zonas no mapa", "neutro"));
      }
      painel.update(s, r, cores, vazioDe(s, r), cab);

      // palco
      const m = mapaDoRecorte(s);
      if (!m || (ehMun && !s.ui.mun)) {
        palco.rodape.textContent = vazioDe(s, null);
        return;
      }
      const uf = s.ui.uf ?? "";
      const caps = capitais(s, uf);
      mapa.definir(palco.mapaEl, m.nivel, m.pai, {
        cor: u => corDaUnidade(u, cores, cargo, ultimoState ?? s),
        // Município: só capitais ganham rótulo. Zona: o padrão do mapa (líder e %) fica.
        ...(m.nivel === "mun" ? { rotulo: (u: UnidadeMapa) => (caps.has(u.cd) ? nomeProprio(u.nm) : null) } : {}),
        titulo: u => `${nomeProprio(u.nm)}: ${u.lider ? `${nomeProprio(u.lider.nmu)} ${pct(u.lider.pvapn)}` : "sem votos totalizados"}`,
        aoClicar: u => {
          if (m.nivel === "zona") navegar({ v: "mun", uf, mun: s.ui.mun, zonas: true, zona: u.cd.padStart(4, "0") });
          else navegar({ v: "mun", uf, mun: u.cd, zonas: false, zona: null });
        },
      });
      // `cor` lê `cores` e o último estado pelo fechamento; repinta quando dados ou cores mudam.
      const dados = s.mapas[chaveMapa(ele, cargo, m.nivel, m.pai)];
      mapa.pintar(dados, assinaturaDeCores(cores));
      if (ehMun) mapa.destacar(s.ui.zonas ? (s.ui.zona ?? null) : s.ui.mun);

      const legenda = dados ? legendaDosLideres(dados.unidades, cores) : [];
      desenharLegenda(palco.legenda, [...legenda, ...LEGENDA_FIXA]);

      if (ehMun) {
        const mu = municipioDe(s, s.ui.uf, s.ui.mun);
        const nz = mu?.z.length ?? 0;
        palco.rodape.textContent = s.ui.zonas
          ? `${inteiro(nz)} ${plural(nz, "zona eleitoral", "zonas eleitorais")}, área proporcional ao eleitorado`
          : `${mu?.nm ?? "município"} em destaque no mapa de ${nomeUf(s, uf)}`;
      } else {
        const e = s.estado?.ufs.find(x => x.uf.toUpperCase() === uf.toUpperCase());
        palco.rodape.textContent = e
          ? `municípios: ${inteiro(e.munf)} finalizados, ${inteiro(e.munpt)} parciais, ${inteiro(e.munnr)} não iniciados`
          : "a contagem de municípios desta UF ainda não chegou";
      }
    },
    keys(tecla, s) {
      if (!ehMun || !s.ui.zonas || !s.ui.uf || !s.ui.mun) return false;
      if (tecla !== "ArrowUp" && tecla !== "ArrowDown") return false;
      const zonas = municipioDe(s, s.ui.uf, s.ui.mun)?.z ?? [];
      if (zonas.length === 0) return false;
      const lista = zonas.map(z => z.padStart(4, "0"));
      const i = s.ui.zona ? lista.indexOf(s.ui.zona) : -1;
      const j = tecla === "ArrowDown" ? Math.min(lista.length - 1, i + 1) : i - 1;
      navegar({ v: "mun", uf: s.ui.uf, mun: s.ui.mun, zonas: true, zona: j < 0 ? null : (lista[j] ?? null) });
      return true;
    },
    unmount() {
      painel?.destroy();
      mapa.destroy();
      painel = null;
      palco = null;
      raiz = null;
      ultimoState = null;
    },
  };
}
