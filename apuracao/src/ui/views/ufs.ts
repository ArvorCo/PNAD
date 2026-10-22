// Tela "ufs": as 27 UFs e o exterior, das mais lentas para as mais rápidas. As 14 mais lentas
// ficam no palco com seções faltantes, municípios faltantes, idade da última versão e ETA;
// as 14 restantes, no painel. Chip "parada" quando o arquivo da UF não anda.

import { chip, chipAndamento } from "../components/chip.ts";
import { horaCurta, inteiro, pct } from "../data/format.ts";
import type { UfLinha } from "../data/doist.ts";
import { atualizarAviso, barra, criarTela2T, dados, esvaziar, h, montarComAviso, ROTULO_ATRASO, rodape, SEM_REGUA } from "./doist-ui.ts";
import { atrasoDaCelula, idadeCurta, ufsMaisLentas } from "./doist-util.ts";

const NO_PALCO = 14;

function celulaAtraso(u: UfLinha): HTMLElement {
  const min = u.ref_1t?.atraso_min ?? null;
  const c = h("span", `chip ${min !== null && min >= 20 ? "chip--atraso" : "chip--neutro"}`, atrasoDaCelula(!!u.ref_1t, min));
  c.title = u.ref_1t ? `No 1º turno, a esta hora: ${pct(u.ref_1t.pst_mesmo_relogio, 1)} das seções` : SEM_REGUA;
  return c;
}

function celulaFecha(u: UfLinha): string {
  if (u.st >= u.ts && u.ts > 0) return "fechou";
  return u.eta_100_iso ? horaCurta(u.eta_100_iso) : "sem ETA";
}

function linhaPalco(u: UfLinha): HTMLElement {
  const l = h("div", `uf-linha${u.parada ? " uf-linha--parada" : ""}`);
  const sg = h("b", "uf-sg", u.uf);
  sg.title = u.nome;
  const pst = h("div", "uf-pst");
  pst.append(barra(u.pst), h("span", "uf-pct num", pct(u.pst, 1)));
  const idade = h("span", "uf-idade num");
  if (u.parada) idade.append(h("span", "chip chip--atraso", `parada ${idadeCurta(u.idade_s)}`));
  else idade.textContent = idadeCurta(u.idade_s);
  const mun = u.munnr + u.munpt;
  l.append(
    sg,
    pst,
    celulaAtraso(u),
    h("span", "uf-n num", u.ts > 0 ? inteiro(u.snt) : "–"),
    h("span", "uf-n num", u.ts > 0 ? inteiro(mun) : "–"),
    idade,
    h("span", "uf-eta num", celulaFecha(u)),
  );
  l.title = `${u.nome}: não iniciados ${u.munnr}, parciais ${u.munpt}, fechados ${u.munf}`;
  return l;
}

function linhaPainel(u: UfLinha): HTMLElement {
  const l = h("div", `uf-linha uf-linha--compacta${u.parada ? " uf-linha--parada" : ""}`);
  const sg = h("b", "uf-sg", u.uf);
  sg.title = u.nome;
  const pst = h("div", "uf-pst");
  pst.append(barra(u.pst), h("span", "uf-pct num", pct(u.pst, 1)));
  l.append(sg, pst, celulaAtraso(u), h("span", "uf-eta num", celulaFecha(u)));
  return l;
}

function cabecalho(colunas: readonly string[], classe: string): HTMLElement {
  const c = h("div", `uf-cab ${classe}`);
  for (const t of colunas) c.append(h("span", "", t));
  return c;
}

export function criarUfs() {
  let esq: HTMLElement | null = null;
  let dir: HTMLElement | null = null;
  return criarTela2T({
    id: "ufs",
    dwell: 22,
    needs: () => [{ tipo: "doist", rota: "ufs" }, { tipo: "estado" }],
    montar(p) {
      montarComAviso(p.corpo, "uf", `<div class="uf-lista"></div>`);
      esq = p.corpo.querySelector<HTMLElement>(".uf-lista");
      p.painel.classList.add("painel--2t");
      dir = h("div", "uf-painel");
      p.painel.append(dir);
    },
    chips(s) {
      const r = dados(s, "ufs");
      const paradas = r ? r.ufs.filter(u => u.parada).length : 0;
      return [chipAndamento(s.estado?.br.pst ?? 0, false), paradas > 0 ? chip(`${paradas} ${paradas === 1 ? "UF parada" : "UFs paradas"}`, "atraso") : null];
    },
    entradas: s => [s.doist.ufs],
    atualizar(s, p) {
      if (!esq || !dir) return;
      const r = dados(s, "ufs");
      if (!atualizarAviso(p.corpo, s, "ufs", "UFs") || !r) {
        esvaziar(dir);
        return;
      }
      const ordem = ufsMaisLentas(r.ufs);
      const nota = rodape(`${ROTULO_ATRASO}; parada: sem versão nova há mais de ${r.limiar_parada_min} min enquanto o país avança`);
      esq.replaceChildren(
        cabecalho(["UF", "seções totalizadas", "atraso", "faltam", "municípios", "versão", "fecha"], "uf-cab--palco"),
        ...ordem.slice(0, NO_PALCO).map(linhaPalco),
        nota,
      );
      dir.replaceChildren(
        h("h2", "uf-h", "as outras UFs"),
        cabecalho(["UF", "seções", "atraso", "fecha"], "uf-cab--painel"),
        ...ordem.slice(NO_PALCO).map(linhaPainel),
      );
    },
    desmontar() {
      esq = null;
      dir = null;
    },
  });
}
