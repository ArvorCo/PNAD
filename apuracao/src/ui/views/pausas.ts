// Tela "pausas": a linha do tempo da noite. Em cima, as versões do arquivo nacional (um traço por
// versão) com as pausas detectadas como faixas; no meio, a soma dos arquivos de UF; embaixo, a
// referência cinza do 1º turno (pausa geral de 19:32 às 20:02). Pausa é um intervalo sem versão
// nova publicada, não acusação.

import { chip, chipAndamento } from "../components/chip.ts";
import { escalaLinear } from "../components/linhas.ts";
import type { Pausas } from "../data/doist.ts";
import { duracao, hora, horaCurta, inteiro } from "../data/format.ts";
import type { Lotes, State } from "../state/types.ts";
import { chaveLotes } from "../state/types.ts";
import { atualizarAviso, criarTela2T, dados, esvaziar, h, montarComAviso, ROTULO_PAUSA, rodape } from "./doist-ui.ts";
import { faixasDePausa, fimDoEixo, hhmmDeMin, idadeCurta, minDeHhmm, minutosDe, ticksDeHora } from "./doist-util.ts";
import type { FaixaTempo } from "./doist-util.ts";
import { eleicaoDe } from "./executivo.ts";

const L = 1152;
const A = 590;
const X0 = 44;
const X1 = L - 44;

export interface EspecLinhaDoTempo {
  fim: number;
  minAgora: number;
  versoes: readonly number[];
  pausas: readonly FaixaTempo[];
  refGeral: { de: number; ate: number } | null;
  refTrava: { de: number; ate: number } | null;
}

const f1 = (v: number): string => (Math.round(v * 10) / 10).toString();

/** Minutos (após 17:00) de cada versão do arquivo nacional, a partir dos lotes. */
export function minutosDasVersoes(lotes: Lotes | undefined, t0Ms: number): number[] {
  return (lotes?.lotes ?? [])
    .map(l => minutosDe(l.at, t0Ms))
    .filter((m): m is number => m !== null && m >= 0)
    .sort((a, b) => a - b);
}

/** Markup SVG da linha do tempo; as classes `pa-*` ficam no CSS. */
export function linhaDoTempoSvg(e: EspecLinhaDoTempo): string {
  const sx = escalaLinear(0, e.fim, X0, X1);
  const linhaNac = { y: 84, h: 150 };
  const linhaSoma = { y: 300, h: 70 };
  const linhaRef = { y: 436, h: 90 };
  const p: string[] = [`<svg class="pa-svg" viewBox="0 0 ${L} ${A}" role="img" aria-label="linha do tempo das pausas">`];
  for (const t of ticksDeHora(e.fim)) {
    const x = sx(t.v);
    p.push(`<line class="pa-grade" x1="${f1(x)}" x2="${f1(x)}" y1="48" y2="540"/><text class="pa-tick" x="${f1(x)}" y="574" text-anchor="middle">${t.texto}</text>`);
  }
  p.push(`<text class="pa-rot" x="${X0}" y="${linhaNac.y - 14}">arquivo nacional: uma marca por versão publicada</text>`);
  p.push(`<rect class="pa-trilho" x="${X0}" y="${linhaNac.y}" width="${X1 - X0}" height="${linhaNac.h}"/>`);
  for (const f of e.pausas) {
    const x = sx(Math.max(0, f.de));
    const w = Math.max(3, sx(Math.min(e.fim, f.ate)) - x);
    p.push(`<rect class="pa-pausa" x="${f1(x)}" y="${linhaNac.y}" width="${f1(w)}" height="${linhaNac.h}"><title>pausa de ${f1(f.minutos)} min</title></rect>`);
  }
  const tracos = e.versoes.map(m => `M${f1(sx(m))} ${linhaNac.y + 8}V${linhaNac.y + linhaNac.h - 8}`).join("");
  if (tracos) p.push(`<path class="pa-versao" d="${tracos}"/>`);
  p.push(`<text class="pa-rot" x="${X0}" y="${linhaSoma.y - 14}">soma dos arquivos de UF</text>`);
  p.push(`<rect class="pa-trilho" x="${X0}" y="${linhaSoma.y}" width="${X1 - X0}" height="${linhaSoma.h}"/>`);
  p.push(`<rect class="pa-soma" x="${X0}" y="${linhaSoma.y}" width="${f1(Math.max(0, sx(Math.min(e.minAgora, e.fim)) - X0))}" height="${linhaSoma.h}"/>`);
  p.push(`<text class="pa-rot" x="${X0}" y="${linhaRef.y - 14}">referência do 1º turno</text>`);
  p.push(`<rect class="pa-trilho" x="${X0}" y="${linhaRef.y}" width="${X1 - X0}" height="${linhaRef.h}"/>`);
  if (e.refTrava) {
    const x = sx(e.refTrava.de);
    p.push(`<rect class="pa-ref pa-ref--trava" x="${f1(x)}" y="${linhaRef.y}" width="${f1(Math.max(3, sx(e.refTrava.ate) - x))}" height="${linhaRef.h}"><title>travamento do arquivo nacional no 1º turno</title></rect>`);
  }
  if (e.refGeral) {
    const x = sx(e.refGeral.de);
    p.push(`<rect class="pa-ref pa-ref--geral" x="${f1(x)}" y="${linhaRef.y}" width="${f1(Math.max(3, sx(e.refGeral.ate) - x))}" height="${linhaRef.h}"><title>pausa geral do 1º turno</title></rect>`);
    p.push(`<text class="pa-ref-t" x="${f1(x + 8)}" y="${linhaRef.y + linhaRef.h / 2 + 8}">19:32 a 20:02</text>`);
  }
  const xa = sx(Math.min(e.minAgora, e.fim));
  p.push(`<line class="pa-agora" x1="${f1(xa)}" x2="${f1(xa)}" y1="48" y2="540"/><text class="pa-agora-t" x="${f1(Math.min(xa, X1 - 70))}" y="32">agora ${hhmmDeMin(e.minAgora)}</text>`);
  p.push("</svg>");
  return p.join("");
}

function resumoAtual(p: Pausas): { titulo: string; sub: string; tipo: "pausa" | "ok" | "sem" } {
  const n = p.nacional;
  if (n.pausa_atual && n.em_pausa) return { titulo: `em pausa há ${duracao(n.pausa_atual.minutos * 60)}`, sub: `última versão às ${hora(n.ultima_versao_em)}`, tipo: "pausa" };
  if (n.ultima_versao_em) return { titulo: `ativo, versão há ${idadeCurta(n.idade_s)}`, sub: `última versão às ${hora(n.ultima_versao_em)}`, tipo: "ok" };
  return { titulo: "nenhuma versão ainda", sub: "o arquivo nacional ainda não publicou", tipo: "sem" };
}

export function criarPausas() {
  let palco: HTMLElement | null = null;
  let lado: HTMLElement | null = null;
  return criarTela2T({
    id: "pausas",
    dwell: 20,
    needs: (s: State) => [{ tipo: "doist", rota: "pausas" }, { tipo: "lotes", ele: eleicaoDe(s, 1), cargo: 1, abr: "br" }, { tipo: "estado" }],
    montar(p) {
      palco = montarComAviso(p.corpo, "pa", `<div class="pa-linha"></div><div class="pa-resumo"></div>`);
      palco.append(rodape(ROTULO_PAUSA));
      p.painel.classList.add("painel--2t");
      lado = h("div", "pa-painel");
      p.painel.append(lado);
    },
    chips(s) {
      const r = dados(s, "pausas");
      return [chipAndamento(s.estado?.br.pst ?? 0, false), r?.nacional.em_pausa ? chip("arquivo nacional em pausa", "atraso") : null];
    },
    entradas: s => [s.doist.pausas, s.lotes[chaveLotes(eleicaoDe(s, 1), 1, "br")]],
    atualizar(s, p) {
      if (!palco || !lado) return;
      const r = dados(s, "pausas");
      if (!atualizarAviso(p.corpo, s, "pausas", "Pausas") || !r) {
        esvaziar(lado);
        return;
      }
      const t0 = Date.parse(r.at) - r.min * 60000;
      const lotes = s.lotes[chaveLotes(eleicaoDe(s, 1), 1, "br")];
      const geral = r.referencia_1t.pausa_geral;
      const trava = r.referencia_1t.travamento_nacional;
      const g = geral ? { de: minDeHhmm(geral.de), ate: minDeHhmm(geral.ate) } : null;
      const tr = trava ? { de: minDeHhmm(trava.de), ate: minDeHhmm(trava.ate) } : null;
      const pausas = faixasDePausa(r.nacional.historico, r.nacional.pausa_atual, t0);
      const fim = fimDoEixo(r.min, Math.max(180, g?.ate ? Math.ceil((g.ate + 10) / 60) * 60 : 180));
      const linha = palco.querySelector<HTMLElement>(".pa-linha");
      if (linha) {
        linha.innerHTML = linhaDoTempoSvg({
          fim,
          minAgora: r.min,
          versoes: minutosDasVersoes(lotes, t0),
          pausas,
          refGeral: g && g.de !== null && g.ate !== null ? { de: g.de, ate: g.ate } : null,
          refTrava: tr && tr.de !== null && tr.ate !== null ? { de: tr.de, ate: tr.ate } : null,
        });
      }
      const resumo = palco.querySelector<HTMLElement>(".pa-resumo");
      if (resumo) {
        const nota = lotes?.fonte === "soma_ufs" ? "As marcas vêm da soma das UFs, porque o arquivo nacional do TSE está parado." : r.referencia_1t.pausa_geral ? "Faixa cinza: a pausa geral do 1º turno, só como referência de relógio." : "Sem referência de pausa do 1º turno.";
        resumo.textContent = nota;
      }

      const res = resumoAtual(r);
      const soma = r.soma_ufs;
      const emPausa = r.ufs.filter(u => u.em_pausa);
      lado.replaceChildren(
        h("h2", "pa-h", "arquivo nacional"),
        (() => {
          const b = h("p", `pa-status pa-status--${res.tipo}`, res.titulo);
          return b;
        })(),
        h("p", "d2-nota", res.sub),
        h("p", "pa-linha-info", `${inteiro(r.nacional.st)} de ${inteiro(r.nacional.ts)} seções no arquivo nacional`),
        h(
          "p",
          "pa-linha-info",
          soma.defasagem_secoes > 0
            ? `soma das UFs à frente: ${inteiro(soma.defasagem_secoes)} seções${soma.defasagem_min !== null ? ` (${soma.defasagem_min.toString().replace(".", ",")} min)` : ""}`
            : "soma das UFs e arquivo nacional alinhados",
        ),
        h("h2", "pa-h", `pausas da noite (${r.nacional.historico.length})`),
        r.nacional.historico.length > 0
          ? (() => {
              const ol = h("ol", "pa-hist");
              for (const x of [...r.nacional.historico].reverse().slice(0, 5)) {
                const li = h("li", "pa-hist-item");
                li.append(
                  h("span", "pa-hist-hora", `${horaCurta(x.de)} a ${horaCurta(x.ate)}`),
                  h("span", "pa-hist-min", `${x.minutos.toString().replace(".", ",")} min`),
                  h("span", "pa-hist-sec", x.st_antes !== null && x.st_depois !== null ? `${inteiro(x.st_antes)} → ${inteiro(x.st_depois)} seções` : ""),
                );
                ol.append(li);
              }
              return ol;
            })()
          : h("p", "d2-vazio", `nenhuma pausa acima de ${r.limiar_min} min`),
        h("h2", "pa-h", "UFs em pausa agora"),
        emPausa.length > 0
          ? (() => {
              const d = h("div", "pa-ufs");
              for (const u of emPausa) d.append(h("span", "chip chip--atraso", `${u.uf} ${idadeCurta(u.idade_s)}`));
              return d;
            })()
          : h("p", "d2-vazio", "nenhuma UF em pausa"),
      );
    },
    desmontar() {
      palco = null;
      lado = null;
    },
  });
}
