// Tela "sen": hemiciclo de 81 assentos. Os 27 eleitos em 2022 (public/senadores_2022.json)
// são contorno; as 54 vagas de 2026 (2 por UF, nv = 2 no arquivo do TSE) se enchem com a
// cor do campo dos dois líderes de cada UF, em banda de pst. Tudo é "líder" até o TSE
// marcar eleito. Abaixo, barra da composição projetada de 2027 por campo com as marcas de
// 41 (maioria), 49 (três quintos) e 54 (dois terços). Painel: 27 UFs × 2 vagas.

import { chipAndamento, trocarChips, chip } from "../components/chip.ts";
import { ASSENTOS, composicao, criarHemiciclo } from "../components/hemiciclo.ts";
import type { Assento, FatiaComposicao, Hemiciclo } from "../components/hemiciclo.ts";
import { criarListaUf } from "../components/listaUf.ts";
import type { LinhaUf, ListaUf } from "../components/listaUf.ts";
import { campoValido, corCampo, NAO_INICIADO } from "../data/cores.ts";
import type { Campo, Campos, Mapa, Need, Resultado, State, UnidadeMapa } from "../state/types.ts";
import { chaveMapa, chaveResultado } from "../state/types.ts";
import { eleitoPeloTse, ordemUfs, rotuloCampo } from "./governadores.ts";
import type { View } from "./registry.ts";
import { nomeUf, partes } from "./registry.ts";

const ELE = 6259;
const CARGO = 5;
const VAGAS_POR_UF = 2;
const MARCAS = [41, 49, 54] as const;

export interface Senador2022 {
  uf: string;
  nome: string;
  partido: string;
  campo: Campo;
}

/** Valida o JSON de public/senadores_2022.json; descarta entradas sem UF ou nome. */
export function lerSenadores(bruto: unknown): Senador2022[] {
  if (!Array.isArray(bruto)) return [];
  const saida: Senador2022[] = [];
  for (const x of bruto) {
    if (typeof x !== "object" || x === null) continue;
    const r = x as Record<string, unknown>;
    if (typeof r.uf !== "string" || typeof r.nome !== "string") continue;
    saida.push({
      uf: r.uf.toUpperCase(),
      nome: r.nome,
      partido: typeof r.partido === "string" ? r.partido : "",
      campo: campoValido(r.campo),
    });
  }
  return saida;
}

// Cache do módulo: uma busca por carga de página. Falha zera a promessa para tentar de novo na próxima montagem.
let senadores: Promise<Senador2022[]> | null = null;

export function carregarSenadores(f: typeof fetch = fetch): Promise<Senador2022[]> {
  senadores ??= f("/senadores_2022.json", { cache: "no-store" })
    .then(r => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
    .then(lerSenadores)
    .catch(() => {
      senadores = null;
      return [];
    });
  return senadores;
}

const resultadoUf = (s: State, uf: string): Resultado | undefined => s.resultados[chaveResultado(ELE, CARGO, uf.toLowerCase())];

/** Os 81 assentos: 27 que continuam e 2 vagas de 2026 por UF (líder, eleito ou aguardando). */
export function montarAssentos(s: State, unidades: readonly UnidadeMapa[], continuam: readonly Senador2022[], ordem: readonly string[]): Assento[] {
  const saida: Assento[] = continuam.map(c => ({ tipo: "continua", campo: c.campo, uf: c.uf, pst: 100, nome: c.nome }));
  const porUf = new Map(unidades.map(u => [u.cd.toUpperCase(), u]));
  for (const uf of ordem) {
    const u = porUf.get(uf);
    const r = resultadoUf(s, uf);
    const top = (u?.top ?? []).filter(t => t.vap > 0);
    for (let k = 0; k < VAGAS_POR_UF; k++) {
      const t = top[k];
      if (!t || !u) {
        saida.push({ tipo: "aguardando", campo: "indefinido", uf, pst: 0, nome: uf });
        continue;
      }
      const c = r?.cand.find(x => x.sqcand === t.sqcand);
      saida.push({ tipo: c && eleitoPeloTse(c) ? "eleito" : "lider", campo: t.campo, uf, pst: u.pst, nome: t.nmu });
    }
  }
  return saida.slice(0, ASSENTOS);
}

export function criarSenado(): View {
  let raiz: HTMLElement | null = null;
  let hemi: Hemiciclo | null = null;
  let lista: ListaUf | null = null;
  let continuam: Senador2022[] = [];
  let ultimo: State | null = null;
  let vivo = true;

  const desenhar = (s: State): void => {
    if (!raiz) return;
    const p = partes(raiz);
    const unidades = (s.mapas[chaveMapa(ELE, CARGO, "uf", "br")] as Mapa | undefined)?.unidades ?? [];
    const ordem = ordemUfs(s, unidades);
    const assentos = montarAssentos(s, unidades, continuam, ordem);
    hemi?.update(assentos, s.campos);

    const lideres = assentos.filter(a => a.tipo === "lider").length;
    const eleitos = assentos.filter(a => a.tipo === "eleito").length;
    const emDisputa = ordem.length * VAGAS_POR_UF;
    trocarChips(p.chips, [
      chipAndamento(s.estado?.br.pst ?? 0, false),
      eleitos > 0 ? chip(`${eleitos} de ${emDisputa} vagas com eleito pelo TSE`, "eleito") : null,
    ]);

    const centro = raiz.querySelector(".sn-centro");
    if (centro) {
      const b = centro.querySelector("b");
      const sp = centro.querySelector("span");
      if (b) b.textContent = `${emDisputa || 54} vagas em disputa`;
      if (sp) {
        sp.textContent =
          lideres + eleitos === 0
            ? "nenhuma vaga com voto apurado ainda"
            : eleitos > 0
              ? `${lideres} com líder, ${eleitos} com eleito pelo TSE`
              : `${lideres} com líder na apuração`;
      }
    }
    desenharComposicao(raiz, composicao(assentos), s.campos, continuam.length === 0);

    const porUf = new Map(unidades.map(u => [u.cd.toUpperCase(), u]));
    const linhas: LinhaUf[] = ordem.map(uf => {
      const u = porUf.get(uf);
      const r = resultadoUf(s, uf);
      const top = (u?.top ?? []).filter(t => t.vap > 0).slice(0, VAGAS_POR_UF);
      return {
        uf,
        nomeUf: nomeUf(s, uf),
        pst: u?.pst ?? 0,
        itens: top.map(t => {
          const c = r?.cand.find(x => x.sqcand === t.sqcand);
          return { nome: t.nmu, campo: t.campo, pct: t.pvapn, marca: c && eleitoPeloTse(c) ? "eleito" : null };
        }),
      };
    });
    lista?.update(linhas, s.campos);
  };

  return {
    id: "sen",
    dwell: 30,
    titulo: () => "Senado",
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
      vivo = true;
      const p = partes(el);
      p.corpo.innerHTML = `
        <div class="sn">
          <div class="sn-hemi"><p class="sn-centro"><b></b><span></span></p></div>
          <div class="sn-comp">
            <p class="sn-comp-titulo">composição projetada para 2027 por campo, com os líderes de agora</p>
            <div class="sn-barra"></div>
            <div class="sn-marcas"></div>
            <ul class="sn-legenda"></ul>
          </div>
        </div>`;
      const caixa = el.querySelector<HTMLElement>(".sn-hemi");
      if (caixa) hemi = criarHemiciclo(caixa, "Senado de 2027: 27 mandatos que continuam e 54 vagas de 2026");
      const marcas = el.querySelector<HTMLElement>(".sn-marcas");
      if (marcas) {
        for (const n of MARCAS) {
          const i = document.createElement("span");
          i.style.left = `${(100 * n) / ASSENTOS}%`;
          i.textContent = String(n);
          marcas.append(i);
        }
      }
      p.painel.classList.add("painel--lista");
      lista = criarListaUf(p.painel, "sen");
      void carregarSenadores().then(l => {
        if (!vivo) return;
        continuam = l;
        if (ultimo) desenhar(ultimo);
      });
    },
    update(s: State) {
      ultimo = s;
      desenhar(s);
    },
    unmount() {
      vivo = false;
      hemi?.destroy();
      lista?.destroy();
      hemi = null;
      lista = null;
      raiz = null;
      ultimo = null;
    },
  };
}

function desenharComposicao(raiz: HTMLElement, fatias: readonly FatiaComposicao[], campos: Campos, semContinuam: boolean): void {
  const barra = raiz.querySelector<HTMLElement>(".sn-barra");
  const legenda = raiz.querySelector<HTMLElement>(".sn-legenda");
  if (!barra || !legenda) return;
  const cor = (f: FatiaComposicao): string => (f.campo === "aguardando" ? NAO_INICIADO : corCampo(f.campo, campos));
  const chave = fatias.map(f => `${f.campo}:${f.n}`).join("|") + campos.cores.esquerda;
  if (barra.dataset.chave === chave) return;
  barra.dataset.chave = chave;
  barra.replaceChildren(
    ...fatias.map(f => {
      const i = document.createElement("i");
      i.style.width = `${(100 * f.n) / ASSENTOS}%`;
      i.style.background = cor(f);
      i.title = `${f.campo === "aguardando" ? "aguardando" : rotuloCampo(f.campo, campos)}: ${f.n}`;
      return i;
    }),
  );
  legenda.replaceChildren(
    ...fatias.map(f => {
      const li = document.createElement("li");
      const sw = document.createElement("i");
      sw.style.background = cor(f);
      const nome = f.campo === "aguardando" ? "vagas aguardando seções" : rotuloCampo(f.campo, campos);
      const b = document.createElement("b");
      b.textContent = String(f.n);
      li.append(sw, document.createTextNode(`${nome} `), b);
      if (f.continuam > 0) {
        const sm = document.createElement("small");
        sm.textContent = ` (${f.continuam} até 2031)`;
        li.append(sm);
      }
      return li;
    }),
  );
  const marcas = document.createElement("li");
  marcas.className = "sn-marcas-nota";
  marcas.textContent = "41 é maioria, 49 são três quintos, 54 são dois terços";
  legenda.append(marcas);
  if (semContinuam) {
    const li = document.createElement("li");
    li.className = "sn-aviso";
    li.textContent = "lista dos 27 mandatos que continuam ainda não carregou";
    legenda.append(li);
  }
}
