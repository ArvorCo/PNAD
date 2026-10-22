// Funções puras das telas do 2º turno: escalas, seleção de destaques, ordenações e textos
// curtos. Nenhuma toca o DOM, para os testes de tests/ui/doist.test.ts.

import { mix, NAO_INICIADO, PAPEL } from "../data/cores.ts";
import type { Agregado, Estadual, MunicipioPendente, PausaHistorico, PontoEvolucao, UfLinha } from "../data/doist.ts";
import { decimal, duracao, inteiro } from "../data/format.ts";
import { escalaLinear, caminho } from "../components/linhas.ts";
import type { Ponto } from "../components/linhas.ts";

// ---------- cor divergente da abstenção ----------

/** Saturação do mapa de abstenção: ±5 pontos contra o 1º turno. */
export const SATURA_ABSTENCAO_PP = 5;
/** Abstenção subiu (mais gente faltou): laranja queimado. */
export const COR_ABSTENCAO_SUBIU = "#a3541b";
/** Abstenção caiu (mais gente votou): teal. */
export const COR_ABSTENCAO_CAIU = "#0f7f5f";

/**
 * Cor divergente pelo Δ de abstenção: papel no zero, cor cheia a partir de ±5 pontos.
 * Sem Δ (município nenhum fechado ou sem régua do 1º turno) vale o cinza de não iniciado.
 */
export function corDivergente(delta: number | null | undefined, satura = SATURA_ABSTENCAO_PP): string {
  if (delta === null || delta === undefined || !Number.isFinite(delta)) return NAO_INICIADO;
  const t = Math.min(1, Math.abs(delta) / satura);
  return mix(PAPEL, delta >= 0 ? COR_ABSTENCAO_SUBIU : COR_ABSTENCAO_CAIU, t);
}

/** Fundo claro da etiqueta do Δ: a cor da escala diluída a 28% no branco, para o texto escuro ter folga. */
export function fundoDoDelta(delta: number | null | undefined, satura = SATURA_ABSTENCAO_PP): string {
  if (delta === null || delta === undefined || !Number.isFinite(delta)) return NAO_INICIADO;
  const t = Math.min(1, Math.abs(delta) / satura);
  return mix("#fffdf8", delta >= 0 ? COR_ABSTENCAO_SUBIU : COR_ABSTENCAO_CAIU, 0.28 * t);
}

// ---------- seleções ----------

/** Região nacional mais lenta (menor % de seções totalizadas). O exterior fica de fora quando há outra região. */
export function regiaoMaisLenta(regioes: readonly Agregado[]): Agregado | null {
  // Antes da primeira seção totalizada no país não há "mais lenta".
  if (!regioes.some(r => r.st > 0)) return null;
  const comSecoes = regioes.filter(r => r.ts > 0);
  const nacionais = comSecoes.filter(r => r.sigla !== "ZZ");
  const base = nacionais.length > 0 ? nacionais : comSecoes;
  let pior: Agregado | null = null;
  for (const r of base) if (!pior || r.pst < pior.pst) pior = r;
  return pior;
}

/** UFs das mais lentas para as mais rápidas (menor pst primeiro; empate pelo maior número de seções). */
export function ufsMaisLentas<T extends Pick<UfLinha, "uf" | "pst" | "ts">>(ufs: readonly T[]): T[] {
  return [...ufs].sort((a, b) => a.pst - b.pst || b.ts - a.ts || a.uf.localeCompare(b.uf));
}

/** As `n` UFs com maior atraso contra o 1º turno; só entram as que têm régua e já começaram. */
export function topAtraso(ufs: readonly UfLinha[], n: number): UfLinha[] {
  return ufs
    .filter(u => u.ref_1t && u.ref_1t.atraso_min !== null && u.ts > 0 && u.st > 0)
    .sort((a, b) => (b.ref_1t?.atraso_min ?? 0) - (a.ref_1t?.atraso_min ?? 0) || a.pst - b.pst)
    .slice(0, n);
}

/** Minutos após 17:00 em que a UF deve fechar: ETA do servidor ou p100 do 1º turno mais o atraso de agora. */
export function fechamentoPrevisto(u: UfLinha, t0Ms: number): number | null {
  if (u.pst >= 100) return null;
  if (u.eta_100_iso) {
    const m = (Date.parse(u.eta_100_iso) - t0Ms) / 60000;
    if (Number.isFinite(m)) return Math.round(m * 10) / 10;
  }
  const r = u.ref_1t;
  if (r && r.p100_min !== null && r.atraso_min !== null) return Math.round((r.p100_min + r.atraso_min) * 10) / 10;
  return null;
}

/** As `n` UFs que devem fechar por último, da mais tardia para a mais cedo. */
export function fechamPorUltimo(ufs: readonly UfLinha[], t0Ms: number, n: number): { u: UfLinha; min: number }[] {
  return ufs
    .map(u => ({ u, min: fechamentoPrevisto(u, t0Ms) }))
    .filter((x): x is { u: UfLinha; min: number } => x.min !== null)
    .sort((a, b) => b.min - a.min)
    .slice(0, n);
}

/** Maiores municípios ainda abertos no país: junta os até três de cada UF e ordena pelo eleitorado. */
export function municipiosAbertos(ufs: readonly UfLinha[], n: number): (MunicipioPendente & { uf: string })[] {
  return ufs
    .flatMap(u => u.pendentes_maiores.map(m => ({ ...m, uf: u.uf })))
    .sort((a, b) => b.te - a.te || a.nm.localeCompare(b.nm))
    .slice(0, n);
}

/** Estadual mais disputado: menor margem entre os dois, entre os que têm votos. */
export function estadualMaisApertado(es: readonly Estadual[]): Estadual | null {
  let melhor: Estadual | null = null;
  for (const e of es) {
    if (!e.cand.some(c => c.vap > 0)) continue;
    if (!melhor || Math.abs(e.margem_pp) < Math.abs(melhor.margem_pp)) melhor = e;
  }
  return melhor;
}

// ---------- textos curtos ----------

/** "+12 min" contra o 1º turno, "−4 min" quando adiantado, "no ritmo" perto de zero, "sem régua" sem dado. */
export function rotuloAtraso(min: number | null | undefined): string {
  if (min === null || min === undefined || !Number.isFinite(min)) return "sem régua";
  if (Math.abs(min) < 1) return "no ritmo";
  return `${min > 0 ? "+" : "−"}${inteiro(Math.abs(min))} min`;
}

/**
 * Atraso para uma célula com régua do 1º turno opcional: sem régua, "sem régua do 1º turno";
 * com régua mas sem atraso medido (nada totalizado ainda), "aguardando".
 */
export function atrasoDaCelula(temRegua: boolean, min: number | null | undefined): string {
  if (!temRegua) return "sem régua do 1º turno";
  return min === null || min === undefined ? "aguardando" : rotuloAtraso(min);
}

/** Pontos percentuais com sinal e vírgula: "+1,3 pp", "−0,4 pp". */
export function rotuloPp(pp: number | null | undefined, casas = 1): string {
  if (pp === null || pp === undefined || !Number.isFinite(pp)) return "sem dado";
  const v = Math.abs(pp) < 0.5 * 10 ** -casas ? 0 : pp;
  return `${v > 0 ? "+" : v < 0 ? "−" : ""}${decimal(Math.abs(v), casas)} pp`;
}

/** Idade da última versão: "24 s", "3 min", "1 h 05". */
export function idadeCurta(segundos: number | null | undefined): string {
  if (segundos === null || segundos === undefined || !Number.isFinite(segundos)) return "sem dado";
  const s = Math.max(0, Math.round(segundos));
  if (s < 90) return `${s} s`;
  if (s < 3600) return `${Math.round(s / 60)} min`;
  return duracao(s);
}

/** Minutos após 17:00 em "hh:mm" de Brasília (passa da meia-noite como "00:12"). */
export function hhmmDeMin(min: number): string {
  const total = Math.round(17 * 60 + min);
  const resto = ((total % 1440) + 1440) % 1440;
  return `${String(Math.floor(resto / 60)).padStart(2, "0")}:${String(resto % 60).padStart(2, "0")}`;
}

/** "hh:mm" em minutos após 17:00 de um texto "hh:mm" de Brasília (para a faixa de referência do 1T). */
export function minDeHhmm(texto: string | null | undefined): number | null {
  const m = /^(\d{1,2}):(\d{2})/.exec(texto ?? "");
  if (!m) return null;
  let total = Number(m[1]) * 60 + Number(m[2]);
  if (total < 17 * 60) total += 1440;
  return total - 17 * 60;
}

/** Minutos após 17:00 (relógio da apuração) de um instante ISO, dado o instante do zero. */
export const minutosDe = (iso: string | null | undefined, t0Ms: number): number | null => {
  const t = Date.parse(iso ?? "");
  return Number.isFinite(t) ? Math.round(((t - t0Ms) / 60000) * 10) / 10 : null;
};

// ---------- linha do tempo das pausas ----------

export interface FaixaTempo {
  de: number;
  ate: number;
  /** Minutos após 17:00. */
  minutos: number;
}

/** Faixas de pausa do histórico mais a pausa em curso (até agora). */
export function faixasDePausa(historico: readonly PausaHistorico[], atual: { desde: string; minutos: number } | null, t0Ms: number): FaixaTempo[] {
  const lista: FaixaTempo[] = [];
  for (const h of historico) {
    const de = minutosDe(h.de, t0Ms);
    const ate = minutosDe(h.ate, t0Ms);
    if (de !== null && ate !== null && ate > de) lista.push({ de, ate, minutos: h.minutos > 0 ? h.minutos : ate - de });
  }
  if (atual) {
    const de = minutosDe(atual.desde, t0Ms);
    if (de !== null) lista.push({ de, ate: de + atual.minutos, minutos: atual.minutos });
  }
  return lista.sort((a, b) => a.de - b.de);
}

/** Fim do eixo do tempo: múltiplo de 60 min que cobre o agora com folga, de 3 a 24 horas (relógio fora disso é erro de dado). */
export function fimDoEixo(minAgora: number, minimo = 180): number {
  return Math.min(1440, Math.max(minimo, Math.ceil((Math.max(0, minAgora) + 10) / 60) * 60));
}

/** Passo de hora cheia que mantém o eixo com no máximo nove marcas: 1 h até 8 h, depois 2 h, 4 h, 6 h... */
export function passoDoEixo(fim: number): number {
  const horas = Math.max(1, Math.ceil(fim / 60 / 8));
  return 60 * horas;
}

/** Ticks de hora cheia do eixo do tempo: minutos 0, 60, 120... com o rótulo "17:00", "18:00"... */
export function ticksDeHora(fim: number, passo = passoDoEixo(fim)): { v: number; texto: string }[] {
  const saida: { v: number; texto: string }[] = [];
  for (let m = 0; m <= fim + 1e-9; m += passo) saida.push({ v: m, texto: hhmmDeMin(m) });
  return saida;
}

// ---------- gráfico da evolução (SVG em texto) ----------

export interface EspecEvolucao {
  largura: number;
  altura: number;
  /** Fração da altura para o painel de cima (duelo); o resto é o painel do pst. */
  fracaoDuelo?: number;
  pontos: readonly PontoEvolucao[];
  ref: readonly (readonly [number, number])[] | null;
  corA: string;
  corB: string;
  minAgora: number;
  fim: number;
  /** Fonte dos ticks, em px da referência. */
  fonte: number;
  margem: { t: number; r: number; b: number; l: number };
  ticksX?: boolean;
  /** Valores fixos do eixo y do duelo; padrão 30 a 70. */
  dominioDuelo?: readonly [number, number];
}

/** Pontos válidos do duelo: ignora as primeiras leituras, em que poucas seções dão percentuais instáveis. */
export function pontosDoDuelo(pontos: readonly PontoEvolucao[], pstMinimo = 2): PontoEvolucao[] {
  return pontos.filter(p => p.pst >= pstMinimo && p.a !== null && p.b !== null);
}

/** Domínio vertical do duelo: o preferido se todos cabem; senão ajustado de 5 em 5 pontos. */
export function dominioDuelo(pontos: readonly PontoEvolucao[], preferido: readonly [number, number] = [30, 70]): [number, number] {
  const v = pontos.flatMap(p => [p.a, p.b]).filter((x): x is number => x !== null && Number.isFinite(x));
  if (v.length === 0) return [preferido[0], preferido[1]];
  const min = Math.min(...v);
  const max = Math.max(...v);
  if (min >= preferido[0] && max <= preferido[1]) return [preferido[0], preferido[1]];
  return [Math.max(0, Math.floor(min / 5) * 5), Math.min(100, Math.ceil(max / 5) * 5)];
}

const f1 = (v: number): string => (Math.round(v * 10) / 10).toString();

/**
 * Markup SVG do gráfico da noite: em cima as duas linhas de % dos válidos (com a linha de 50%),
 * embaixo a curva de seções totalizadas do 2º turno (cheia) e a do 1º turno no mesmo relógio
 * (pontilhada). Texto em classes `ev-*` para o CSS.
 */
export function evolucaoSvg(e: EspecEvolucao): string {
  const { largura, altura, margem } = e;
  const frac = e.fracaoDuelo ?? 0.66;
  const x0 = margem.l;
  const x1 = largura - margem.r;
  const topoDuelo = margem.t;
  const baseDuelo = margem.t + (altura - margem.t - margem.b) * frac - 14;
  const topoPst = baseDuelo + 14 + 8;
  const basePst = altura - margem.b;
  const sx = escalaLinear(0, e.fim, x0, x1);
  const duelo = pontosDoDuelo(e.pontos);
  const [d0, d1] = dominioDuelo(duelo, e.dominioDuelo ?? [30, 70]);
  const sy = escalaLinear(d0, d1, baseDuelo, topoDuelo);
  const sp = escalaLinear(0, 100, basePst, topoPst);
  const linhaA: Ponto[] = duelo.map(p => ({ x: p.min, y: p.a ?? NaN }));
  const linhaB: Ponto[] = duelo.map(p => ({ x: p.min, y: p.b ?? NaN }));
  const pst2: Ponto[] = e.pontos.map(p => ({ x: p.min, y: p.pst }));
  const pst1: Ponto[] = (e.ref ?? []).map(p => ({ x: p[0], y: p[1] }));
  const ticks = ticksDeHora(e.fim);
  const partes: string[] = [];
  partes.push(`<svg class="ev-svg" viewBox="0 0 ${largura} ${altura}" role="img" aria-label="evolução dos válidos e das seções totalizadas">`);
  // grade e eixos
  for (const t of ticks) {
    const x = sx(t.v);
    partes.push(`<line class="ev-gl" x1="${f1(x)}" x2="${f1(x)}" y1="${f1(topoDuelo)}" y2="${f1(basePst)}"/>`);
    if (e.ticksX !== false) partes.push(`<text class="ev-tick ev-tick--x" x="${f1(x)}" y="${f1(basePst + e.fonte + 8)}" text-anchor="middle">${t.texto}</text>`);
  }
  const meio = d0 < 50 && d1 > 50 ? sy(50) : null;
  if (meio !== null) partes.push(`<line class="ev-meio" x1="${f1(x0)}" x2="${f1(x1)}" y1="${f1(meio)}" y2="${f1(meio)}"/><text class="ev-tick" x="${f1(x0 - 8)}" y="${f1(meio + e.fonte * 0.35)}" text-anchor="end">50</text>`);
  partes.push(`<text class="ev-tick" x="${f1(x0 - 8)}" y="${f1(topoDuelo + e.fonte * 0.8)}" text-anchor="end">${d1}</text>`);
  partes.push(`<text class="ev-tick" x="${f1(x0 - 8)}" y="${f1(baseDuelo)}" text-anchor="end">${d0}</text>`);
  partes.push(`<line class="ev-base" x1="${f1(x0)}" x2="${f1(x1)}" y1="${f1(baseDuelo)}" y2="${f1(baseDuelo)}"/>`);
  partes.push(`<line class="ev-base" x1="${f1(x0)}" x2="${f1(x1)}" y1="${f1(basePst)}" y2="${f1(basePst)}"/>`);
  partes.push(`<text class="ev-tick" x="${f1(x0 - 8)}" y="${f1(topoPst + e.fonte * 0.8)}" text-anchor="end">100</text>`);
  // pst
  const dPst1 = caminho(pst1, sx, sp);
  if (dPst1) partes.push(`<path class="ev-pst1" d="${dPst1}"/>`);
  const dPst2 = caminho(pst2, sx, sp);
  if (dPst2) partes.push(`<path class="ev-pst2" d="${dPst2}"/>`);
  // duelo
  const dA = caminho(linhaA, sx, sy);
  const dB = caminho(linhaB, sx, sy);
  if (dA) partes.push(`<path class="ev-linha" d="${dA}" stroke="${e.corA}"/>`);
  if (dB) partes.push(`<path class="ev-linha" d="${dB}" stroke="${e.corB}"/>`);
  // agora
  const xa = sx(Math.min(e.minAgora, e.fim));
  partes.push(`<line class="ev-agora" x1="${f1(xa)}" x2="${f1(xa)}" y1="${f1(topoDuelo)}" y2="${f1(basePst)}"/>`);
  partes.push("</svg>");
  return partes.join("");
}

// ---------- paralela ----------

export interface FatiaConferencia {
  chave: "iguais" | "divergentes" | "tse_ainda_nao_publicou" | "fora_do_oficial" | "erro" | "pendentes";
  rotulo: string;
  n: number;
  pct: number;
}

const ROTULO_CONF: Readonly<Record<FatiaConferencia["chave"], string>> = {
  iguais: "iguais ao oficial",
  divergentes: "divergentes",
  tse_ainda_nao_publicou: "TSE ainda não publicou",
  fora_do_oficial: "fora do oficial",
  erro: "erro de leitura",
  pendentes: "pendentes",
};

/** Fatias da conferência em % do total de BUs recebidos, na ordem de leitura. */
export function fatiasConferencia(c: Record<FatiaConferencia["chave"], number>): FatiaConferencia[] {
  const chaves: FatiaConferencia["chave"][] = ["iguais", "divergentes", "tse_ainda_nao_publicou", "fora_do_oficial", "erro", "pendentes"];
  const total = chaves.reduce((s, k) => s + (c[k] ?? 0), 0);
  return chaves.map(k => ({ chave: k, rotulo: ROTULO_CONF[k], n: c[k] ?? 0, pct: total > 0 ? (100 * (c[k] ?? 0)) / total : 0 }));
}
