// Tela "paralela": a totalização paralela por QR do BU. Mostra quantos BUs chegaram, a
// cobertura por UF, o resultado da conferência contra o boletim oficial do TSE, o placar da
// soma dos BUs recebidos (rótulo fixo: não é projeção) e as últimas divergências. Com a fonte
// (Supabase) em erro, diz "fonte indisponível" e nunca fica em branco.

import { chip, chipAndamento } from "../components/chip.ts";
import { corCampo } from "../data/cores.ts";
import type { Paralela } from "../data/doist.ts";
import { decimal, hora, inteiro, nomeProprio } from "../data/format.ts";
import type { State } from "../state/types.ts";
import { atualizarAviso, criarTela2T, dados, dueloDe, esvaziar, h, montarComAviso, ROTULO_PARALELA } from "./doist-ui.ts";
import type { Duelo } from "./doist-ui.ts";
import { fatiasConferencia } from "./doist-util.ts";
import { eleicaoDe } from "./executivo.ts";
import { coresDoPar } from "./gov2t.ts";
import { chaveResultado } from "../state/types.ts";

const COR_FATIA: Readonly<Record<string, string>> = {
  iguais: "#0f7f5f",
  divergentes: "#a8281c",
  tse_ainda_nao_publicou: "#4f7fc2",
  fora_do_oficial: "#8a7a3a",
  erro: "#6b4a92",
  pendentes: "#c7c9bb",
};

function kpi(rotulo: string, valor: string, nota = ""): HTMLElement {
  const k = h("div", "pl-kpi");
  k.append(h("p", "pl-kpi-v num", valor), h("p", "pl-kpi-r", rotulo));
  if (nota) k.append(h("p", "pl-kpi-n", nota));
  return k;
}

/** Aptos, comparecimento e abstenção somados dos BUs recebidos. */
function presencaBus(r: Paralela): HTMLElement {
  const p = r.placar_bus.presidente;
  const aptos = p.aptos ?? 0;
  const comp = p.comparecimento ?? 0;
  const abst = Math.max(0, aptos - comp);
  const pc = aptos > 0 ? (100 * comp) / aptos : null;
  const pa = aptos > 0 ? (100 * abst) / aptos : null;
  const el = h("div", "pl-presenca");
  const cel = (rot: string, valor: string, pct: string | null): HTMLElement => {
    const c = h("div", "pl-presenca-c");
    c.append(h("span", "pl-presenca-rot", rot), h("b", "num", valor), h("span", "pl-presenca-pct num", pct ?? ""));
    return c;
  };
  el.append(
    cel("aptos", inteiro(aptos), null),
    cel("compareceram", inteiro(comp), pc === null ? null : `${pc.toFixed(1).replace(".", ",")}%`),
    cel("abstenção", inteiro(abst), pa === null ? null : `${pa.toFixed(1).replace(".", ",")}%`),
  );
  return el;
}

/** Chamada com o QR da totalização: a tela é o lugar onde o espectador decide enviar. */
function chamadaQr(): HTMLElement {
  const el = h("div", "espera-chamada pl-chamada");
  const img = document.createElement("img");
  img.className = "espera-qr";
  img.src = "img/qr_totalizacao.svg";
  img.alt = "QR code de brasil.arvor.co/totalizacao";
  img.width = 112;
  img.height = 112;
  const txt = h("div");
  txt.append(h("p", "espera-chamada-titulo", "TEM UM BU? LEIA-O AGORA!"), h("p", "espera-chamada-link", "brasil.arvor.co/totalizacao"));
  el.append(img, txt);
  return el;
}

/** % dos válidos (soma dos dois do duelo) de cada lado a partir dos votos por número de urna. */
export function pctPlacar(votos: Record<string, number>, a: string, b: string): { a: number; b: number; total: number } | null {
  const va = votos[a] ?? 0;
  const vb = votos[b] ?? 0;
  const total = va + vb;
  return total > 0 ? { a: (100 * va) / total, b: (100 * vb) / total, total } : null;
}

function placarPresidente(p: Paralela, d: Duelo | null): HTMLElement {
  const bloco = h("div", "pl-placar");
  const pc = d ? pctPlacar(p.placar_bus.presidente.votos, d.a.n, d.b.n) : null;
  for (const c of d ? [d.a, d.b] : []) {
    const l = h("div", "pl-placar-lado");
    l.style.setProperty("--cor", c.cor);
    const votos = p.placar_bus.presidente.votos[c.n] ?? 0;
    l.append(h("p", "pl-placar-nome corte", c.nome), h("p", "pl-placar-pct num", pc ? decimal(c === d?.a ? pc.a : pc.b, 1) : "–"), h("p", "pl-placar-v num", `${inteiro(votos)} votos`));
    bloco.append(l);
  }
  if (!d) bloco.append(h("p", "d2-vazio", "aguardando o resultado nacional para nomear os lados"));
  return bloco;
}

export function criarParalela() {
  let palco: HTMLElement | null = null;
  let lado: HTMLElement | null = null;
  return criarTela2T({
    id: "paralela",
    dwell: 20,
    needs: (s: State) => [
      { tipo: "doist", rota: "paralela" },
      { tipo: "doist", rota: "estaduais" },
      { tipo: "resultado", ele: eleicaoDe(s, 1), cargo: 1, abr: "br" },
      { tipo: "estado" },
    ],
    montar(p) {
      palco = montarComAviso(
        p.corpo,
        "pl",
        `<p class="pl-erro" hidden></p>
         <div class="pl-kpis"></div>
         <h2 class="pl-h">conferência contra o boletim oficial do TSE</h2>
         <div class="pl-conf"></div>
         <h2 class="pl-h">cobertura por UF (BUs recebidos sobre as seções)</h2>
         <div class="pl-cob"></div>`,
      );
      p.painel.classList.add("painel--2t");
      lado = h("div", "pl-painel");
      p.painel.append(lado);
    },
    chips(s) {
      const r = dados(s, "paralela");
      return [chipAndamento(s.estado?.br.pst ?? 0, false), r?.erro ? chip("fonte com erro", "atraso") : null];
    },
    entradas: s => [s.doist.paralela, s.doist.estaduais, s.resultados[chaveResultado(eleicaoDe(s, 1), 1, "br")], s.cores, s.campos],
    atualizar(s, p) {
      if (!palco || !lado) return;
      const r = dados(s, "paralela");
      if (!atualizarAviso(p.corpo, s, "paralela", "Totalização paralela") || !r) {
        esvaziar(lado);
        // Rótulo fixo também sem fonte: a tela nunca sugere que há placar.
        lado.append(h("p", "pl-rotulo", ROTULO_PARALELA));
        return;
      }
      const q = <T extends HTMLElement>(c: string): T => palco?.querySelector<T>(c) as T;
      const err = q<HTMLElement>(".pl-erro");
      err.hidden = !r.erro;
      err.textContent = r.erro ? `Fonte indisponível agora (${r.erro}). Números da última leitura${r.atualizado_em ? `, às ${hora(r.atualizado_em)}` : ""}.` : "";
      q(".pl-kpis").replaceChildren(
        kpi("BUs recebidos", inteiro(r.recebidos.bus)),
        kpi("seções", inteiro(r.recebidos.secoes)),
        kpi("UFs com BU", `${inteiro(r.recebidos.ufs)} de 27`),
        kpi("conflitos", inteiro(r.recebidos.conflitos), "segundo BU na mesma seção"),
      );
      const fatias = fatiasConferencia(r.conferencia);
      const barra = h("div", "pl-conf-barra");
      for (const f of fatias.filter(x => x.n > 0)) {
        const i = document.createElement("i");
        i.style.width = `${f.pct}%`;
        i.style.background = COR_FATIA[f.chave] ?? "#8a8f98";
        i.title = `${f.rotulo}: ${inteiro(f.n)}`;
        barra.append(i);
      }
      const leg = h("ul", "pl-conf-leg");
      for (const f of fatias) {
        const li = h("li", f.n === 0 ? "pl-leg--zero" : "");
        const sw = document.createElement("i");
        sw.style.background = COR_FATIA[f.chave] ?? "#8a8f98";
        li.append(sw, h("span", "", f.rotulo), h("b", "num", inteiro(f.n)));
        leg.append(li);
      }
      q(".pl-conf").replaceChildren(r.recebidos.bus > 0 ? barra : h("p", "d2-vazio", "nenhum BU recebido ainda"), leg);
      const cob = [...r.cobertura_uf].sort((a, b) => b.pct - a.pct || a.uf.localeCompare(b.uf));
      const maiorCob = Math.max(1, ...cob.map(u => u.pct));
      q(".pl-cob").replaceChildren(
        ...(cob.length > 0
          ? cob.map(u => {
              const c = h("div", "pl-cob-item");
              const b = h("span", "d2-barra");
              const i = document.createElement("i");
              i.style.width = `${Math.min(100, (100 * u.pct) / maiorCob)}%`;
              b.append(i);
              c.append(h("b", "", u.uf), b, h("span", "num", `${decimal(u.pct, 1)}%`));
              c.title = `${u.uf}: ${inteiro(u.bus)} BUs de ${inteiro(u.secoes_total)} seções`;
              return c;
            })
          : [h("p", "d2-vazio", "nenhuma UF com BU recebido")]),
      );

      const d = dueloDe(s);
      const gov = dados(s, "estaduais");
      const govLinhas = Object.entries(r.placar_bus.governador).map(([uf, g]) => {
        const e = gov?.ufs.find(x => x.uf === uf);
        const ns = e ? e.cand.slice(0, 2).map(c => c.n) : Object.keys(g.votos).sort((a, b) => a.localeCompare(b, "pt-BR", { numeric: true })).slice(0, 2);
        const pc = ns.length === 2 ? pctPlacar(g.votos, ns[0] ?? "", ns[1] ?? "") : null;
        const cores = e ? coresDoPar(e.cand.slice(0, 2), s.campos) : [corCampo("indefinido", s.campos), "#5f6773"];
        const l = h("div", "pl-gov");
        const b = h("span", "pl-gov-barra");
        const a = document.createElement("i");
        const z = document.createElement("i");
        a.style.width = `${pc ? pc.a : 50}%`;
        z.style.width = `${pc ? pc.b : 50}%`;
        a.style.background = cores[0] ?? "#5f6773";
        z.style.background = cores[1] ?? "#8a8f98";
        b.append(a, z);
        l.append(h("b", "", uf), h("span", "num", pc ? decimal(pc.a, 1) : "–"), b, h("span", "num", pc ? decimal(pc.b, 1) : "–"));
        l.title = e ? e.cand.slice(0, 2).map(c => nomeProprio(c.nome_urna)).join(" × ") : "";
        return l;
      });
      const div = r.divergencias.slice(0, 2);
      lado.replaceChildren(
        h("h2", "pl-h2", "placar dos BUs recebidos"),
        placarPresidente(r, d),
        h("p", "pl-placar-info num", `${inteiro(r.placar_bus.presidente.secoes)} seções; brancos ${inteiro(r.placar_bus.presidente.brancos)}, nulos ${inteiro(r.placar_bus.presidente.nulos)}`),
        presencaBus(r),
        h("p", "pl-rotulo", ROTULO_PARALELA),
        chamadaQr(),
        h("h2", "pl-h2", "governadores nos BUs"),
        ...(govLinhas.length > 0 ? govLinhas : [h("p", "d2-vazio", "nenhum BU de governador ainda")]),
        h("h2", "pl-h2", `últimas divergências (${inteiro(r.conferencia.divergentes)})`),
        ...(div.length > 0
          ? div.map(x => {
              const li = h("p", "pl-div");
              const campos = x.campos.map(c => `${c.campo}: ${c.paralela} contra ${c.tse} no oficial`).join("; ");
              li.textContent = `${x.uf}, zona ${Number(x.zona) || x.zona}, seção ${Number(x.secao) || x.secao}: ${campos}`;
              return li;
            })
          : [h("p", "d2-vazio", "nenhuma divergência até agora")]),
        h("p", "d2-nota", "divergência pede conferência da ata; não prova erro do BU nem da urna"),
      );
    },
    desmontar() {
      palco = null;
      lado = null;
    },
  });
}
