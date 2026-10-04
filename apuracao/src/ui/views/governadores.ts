// Tela "gov": mapa do Brasil por UF na cor do campo do líder para governador, legenda de
// campos e painel com as 27 UFs (listaUf). Cor cheia só com 100% das seções e líder acima
// de 50% dos válidos ("decidido no 1º turno"); antes disso, banda de mistura com o papel.
// "1º turno" na lista só quando o TSE marcar eleito. Tecla m troca o palco pela lista de
// quem já decidiu (UFs com totalização encerrada).

import { chip, chipAndamento, trocarChips } from "../components/chip.ts";
import { criarListaUf } from "../components/listaUf.ts";
import type { LinhaUf, ListaUf } from "../components/listaUf.ts";
import { criarMapa } from "../components/mapa.ts";
import type { Mapa as MapaSvg } from "../components/mapa.ts";
import { banda, corCampo, mix, NAO_INICIADO, PAPEL } from "../data/cores.ts";
import { nomeProprio, pct } from "../data/format.ts";
import { ufsPorEleitorado } from "../state/selectors.ts";
import type { Campo, Campos, Candidato, Mapa, Need, Resultado, State, UnidadeMapa } from "../state/types.ts";
import { chaveMapa, chaveResultado } from "../state/types.ts";
import type { View } from "./registry.ts";
import { nomeUf, partes } from "./registry.ts";

const ELE = 6259;
const CARGO = 3;
const CAMPOS_LEGENDA: readonly Campo[] = ["esquerda", "centro-esquerda", "centro", "centro-direita", "direita", "indefinido"];
const ROTULO_PADRAO: Readonly<Record<Campo, string>> = {
  esquerda: "esquerda",
  "centro-esquerda": "centro-esquerda",
  centro: "centro",
  "centro-direita": "centro-direita",
  direita: "direita",
  indefinido: "indefinido",
};
/** Cinza de empate: há votos, mas nenhum líder para pintar. */
const EMPATE = "#c9c5b8";

export const rotuloCampo = (c: Campo, campos: Campos): string => (campos.rotulos[c] ?? ROTULO_PADRAO[c]).toLocaleLowerCase("pt-BR");

/** Siglas das UFs na ordem do eleitorado (config) ou, sem config, na ordem do mapa. */
export function ordemUfs(s: State, unidades: readonly UnidadeMapa[]): string[] {
  if (s.config && s.config.ufs.length > 0) return ufsPorEleitorado(s.config.ufs).map(u => u.uf.toUpperCase());
  return [...unidades].sort((a, b) => (b.te ?? 0) - (a.te ?? 0) || a.cd.localeCompare(b.cd)).map(u => u.cd.toUpperCase());
}

export const empatado = (u: UnidadeMapa): boolean =>
  u.lider !== undefined && u.segundo !== undefined && u.lider.vap > 0 && u.lider.vap === u.segundo.vap;

/** Cor da UF: campo do líder, banda por pst, cor cheia só quando decidido no 1º turno. */
export function corGovernador(u: UnidadeMapa, campos: Campos): string {
  if (!u.lider || !(u.pst > 0)) return NAO_INICIADO;
  if (empatado(u)) return EMPATE;
  let f = banda(u.pst);
  if (f === 1 && !(u.lider.pvapn > 50)) f = 0.85;
  const cor = corCampo(u.lider.campo, campos);
  return f === 1 ? cor : mix(PAPEL, cor, f);
}

export const eleitoPeloTse = (c: Pick<Candidato, "e" | "st">): boolean => c.e || /^eleit/i.test(c.st);
export const segundoTurnoTse = (c: Pick<Candidato, "st">): boolean => /2.?\s*turno/i.test(c.st);

const unidadesDe = (s: State): UnidadeMapa[] => (s.mapas[chaveMapa(ELE, CARGO, "uf", "br")] as Mapa | undefined)?.unidades ?? [];
const resultadoUf = (s: State, uf: string): Resultado | undefined => s.resultados[chaveResultado(ELE, CARGO, uf.toLowerCase())];

interface Decidido {
  uf: string;
  nome: string;
  lider: string;
  pct: number;
  situacao: string;
}

function decididos(s: State, unidades: readonly UnidadeMapa[], ordem: readonly string[]): Decidido[] {
  const porUf = new Map(unidades.map(u => [u.cd.toUpperCase(), u]));
  const saida: Decidido[] = [];
  for (const uf of ordem) {
    const u = porUf.get(uf);
    if (!u || !u.lider || !(u.tf || u.pst >= 100)) continue;
    const r = resultadoUf(s, uf);
    const eleito = r?.cand.find(eleitoPeloTse);
    const segundos = r?.cand.filter(segundoTurnoTse) ?? [];
    let situacao = "totalização encerrada, sem situação do TSE";
    if (eleito) situacao = "eleito no 1º turno pelo TSE";
    else if (segundos.length >= 2) situacao = `2º turno: ${segundos.map(c => nomeProprio(c.nmu)).join(" e ")}`;
    saida.push({ uf, nome: nomeUf(s, uf), lider: nomeProprio(eleito?.nmu ?? u.lider.nmu), pct: eleito?.pvapn ?? u.lider.pvapn, situacao });
  }
  return saida;
}

export function criarGovernadores(): View {
  let raiz: HTMLElement | null = null;
  let mapa: MapaSvg | null = null;
  let lista: ListaUf | null = null;
  let campos: Campos | null = null;
  let ultimoMapa: Mapa | undefined;
  let ultimosCampos: Campos | null = null;
  let palcoMapa: HTMLElement | null = null;
  let palcoDecididos: HTMLElement | null = null;
  let legenda: HTMLElement | null = null;

  return {
    id: "gov",
    dwell: 30,
    titulo: () => "Governadores",
    needs(s: State): Need[] {
      const ufs = s.config?.ufs.map(u => u.uf.toLowerCase()) ?? [];
      return [
        { tipo: "estado" },
        { tipo: "mapa", ele: ELE, cargo: CARGO, nivel: "uf", pai: "br" },
        ...ufs.map((abr): Need => ({ tipo: "resultado", ele: ELE, cargo: CARGO, abr })),
      ];
    },
    mount(el) {
      raiz = el;
      const p = partes(el);
      p.corpo.innerHTML = `
        <div class="gv">
          <div class="gv-mapa"></div>
          <div class="gv-decididos" hidden></div>
          <ul class="gv-legenda" aria-label="campo do líder"></ul>
        </div>`;
      palcoMapa = el.querySelector(".gv-mapa");
      palcoDecididos = el.querySelector(".gv-decididos");
      legenda = el.querySelector(".gv-legenda");
      if (palcoMapa) {
        mapa = criarMapa(palcoMapa, {
          nivel: "uf",
          pai: "br",
          largura: 1152,
          altura: 752,
          cor: u => (campos ? corGovernador(u, campos) : NAO_INICIADO),
          titulo: u =>
            u.lider ? `${u.nm}: ${nomeProprio(u.lider.nmu)} (${u.lider.sg}), ${pct(u.lider.pvapn)} dos válidos` : `${u.nm}: aguardando seções`,
        });
      }
      p.painel.classList.add("painel--lista");
      lista = criarListaUf(p.painel, "gov");
    },
    update(s: State) {
      if (!raiz) return;
      campos = s.campos;
      const p = partes(raiz);
      const unidades = unidadesDe(s);
      const ordem = ordemUfs(s, unidades);
      const porUf = new Map(unidades.map(u => [u.cd.toUpperCase(), u]));

      // Chips: andamento nacional e UFs encerradas.
      const encerradas = unidades.filter(u => u.tf || u.pst >= 100).length;
      trocarChips(p.chips, [
        chipAndamento(s.estado?.br.pst ?? 0, false),
        unidades.length > 0 ? chip(`${encerradas} de ${unidades.length} UFs encerradas`, "neutro") : null,
      ]);

      // Mapa: só reaplica quando o dado ou as cores mudam.
      const mapaAtual = s.mapas[chaveMapa(ELE, CARGO, "uf", "br")] as Mapa | undefined;
      if (mapa && (mapaAtual !== ultimoMapa || s.campos !== ultimosCampos)) {
        mapa.update(unidades);
        ultimoMapa = mapaAtual;
      }

      // Legenda de campos (6 cores) e nota de cor cheia.
      if (legenda && s.campos !== ultimosCampos) {
        legenda.replaceChildren(
          ...CAMPOS_LEGENDA.map(c => {
            const li = document.createElement("li");
            const sw = document.createElement("i");
            sw.style.background = corCampo(c, s.campos);
            li.append(sw, document.createTextNode(rotuloCampo(c, s.campos)));
            return li;
          }),
        );
        const nota = document.createElement("li");
        nota.className = "gv-nota";
        nota.textContent = "cor cheia: decidido no 1º turno";
        legenda.append(nota);
      }
      ultimosCampos = s.campos;

      // Variante (tecla m): quem já decidiu.
      const variante = s.ui.variante % 2 === 1;
      if (palcoMapa) palcoMapa.hidden = variante;
      if (palcoDecididos) {
        palcoDecididos.hidden = !variante;
        if (variante) desenharDecididos(palcoDecididos, decididos(s, unidades, ordem));
      }

      // Painel: 27 linhas.
      const linhas: LinhaUf[] = ordem.map(uf => {
        const u = porUf.get(uf);
        const r = resultadoUf(s, uf);
        const eleito = r?.cand.some(eleitoPeloTse) ?? false;
        const l = u?.lider;
        return {
          uf,
          nomeUf: nomeUf(s, uf),
          pst: u?.pst ?? 0,
          itens: l && !(u && empatado(u)) ? [{ nome: l.nmu, campo: l.campo, pct: l.pvapn, marca: eleito ? "1º turno" : null }] : [],
        };
      });
      lista?.update(linhas, s.campos);
    },
    unmount() {
      mapa?.destroy();
      lista?.destroy();
      mapa = null;
      lista = null;
      raiz = null;
    },
  };
}

function desenharDecididos(alvo: HTMLElement, itens: readonly Decidido[]): void {
  if (itens.length === 0) {
    alvo.innerHTML = `<p class="gv-vazio">nenhuma UF com totalização encerrada para governador ainda</p>`;
    return;
  }
  const h = document.createElement("h2");
  h.className = "gv-dec-titulo";
  h.textContent = `quem já decidiu: ${itens.length} ${itens.length === 1 ? "UF" : "UFs"}`;
  const ol = document.createElement("ol");
  ol.className = `gv-dec-lista${itens.length > 8 ? " gv-dec-lista--duas" : ""}`;
  for (const d of itens) {
    const li = document.createElement("li");
    const uf = document.createElement("b");
    uf.textContent = d.nome;
    const nome = document.createElement("span");
    nome.className = "gv-dec-nome";
    nome.textContent = `${d.lider}, ${pct(d.pct)}; ${d.situacao}`;
    li.append(uf, nome);
    ol.append(li);
  }
  alvo.replaceChildren(h, ol);
}
