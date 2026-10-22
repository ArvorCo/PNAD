// Utilidades dos indicadores do 2º turno: relógio da apuração, arredondamento e instantes.
import { ELEICAO_ESTADUAL_2T, ELEICAO_FEDERAL_2T, T0_1T_MS, T0_2T_MS, corrigirTotalizadoEm } from "../../turno2/comum.ts";

/** 17:00 de Brasília do dia da eleição a que `ele` pertence (6257/6259 = 1º turno; demais = 2º). */
export function t0De(ele: number): number {
  return ele === 6257 || ele === 6259 ? T0_1T_MS : T0_2T_MS;
}

/** Turno pelo código da eleição; null quando o código não é dos pleitos gerais. */
export function turnoDe(ele: number): 1 | 2 | null {
  if (ele === 6257 || ele === 6259) return 1;
  if (ele === ELEICAO_FEDERAL_2T || ele === ELEICAO_ESTADUAL_2T) return 2;
  return null;
}

export const r1 = (v: number): number => Math.round(v * 10) / 10;
export const r2 = (v: number): number => Math.round(v * 100) / 100;

/** Percentual de seções com 2 casas, truncado: 99,996% não vira 100% enquanto falta seção. */
export function pstDe(st: number, ts: number): number {
  if (ts <= 0) return 0;
  if (st >= ts) return 100;
  return Math.floor(((100 * st) / ts) * 100) / 100;
}

/** pa = abstencao / (comparecimento + abstencao) × 100, 2 casas; 0 sem eleitorado apurado. */
export function paDe(comparecimento: number, abstencao: number): number {
  const d = comparecimento + abstencao;
  return d > 0 ? r2((100 * abstencao) / d) : 0;
}

/** Igual a paDe, mas null sem eleitorado apurado (comparações). */
export function paOuNull(comparecimento: number, abstencao: number): number | null {
  return comparecimento + abstencao > 0 ? paDe(comparecimento, abstencao) : null;
}

/** Minutos após 17:00 de Brasília (1 casa). */
export function minutosDe(ms: number, t0Ms: number): number {
  return r1((ms - t0Ms) / 60000);
}

export const isoDe = (ms: number): string => new Date(ms).toISOString();

/**
 * Corretor do `totalizado_em` de um arquivo. A regra de `corrigirTotalizadoEm` compara o
 * carimbo com a geração do arquivo; quando o TSE regera o arquivo sem nova totalização, a diferença
 * passa do deslocamento e a correção deixaria de valer (no 1º turno, o AC voltaria duas horas).
 * Por isso cada valor de `totalizado_em` é decidido uma vez, com a geração da primeira versão
 * que o trouxe, e reaproveitado nas versões seguintes. O resultado nunca passa da geração
 * (o exterior chegou a trazer carimbo do dia seguinte).
 */
export class CorretorTotalizacao {
  private readonly decididos = new Map<string, string | null>();

  constructor(private readonly uf: string) {}

  /** Instante corrigido (ms) da versão; sem carimbo, a geração; sem geração, a leitura. */
  instante(totalizadoEm: string | null, geradoEm: string | null, capturadoEm: string): number {
    const ger = geradoEm ? Date.parse(geradoEm) : Number.NaN;
    let tot = Number.NaN;
    if (totalizadoEm) {
      let corr = this.decididos.get(totalizadoEm);
      if (corr === undefined) {
        corr = corrigirTotalizadoEm(this.uf, totalizadoEm, geradoEm);
        this.decididos.set(totalizadoEm, corr);
      }
      tot = corr ? Date.parse(corr) : Number.NaN;
    }
    if (Number.isFinite(tot) && Number.isFinite(ger)) return Math.min(tot, ger);
    if (Number.isFinite(tot)) return tot;
    if (Number.isFinite(ger)) return ger;
    return Date.parse(capturadoEm);
  }
}

/**
 * Relógio de um arquivo, versão a versão em ordem de leitura. O instante de uma versão é o da
 * totalização que trouxe as contagens dela:
 * - contagens iguais às da versão anterior (o TSE regerou o arquivo sem totalizar nada): mesmo
 *   instante da anterior, para que um arquivo parado envelheça;
 * - contagens novas: `totalizado_em` corrigido de fuso (decidido na primeira aparição do carimbo),
 *   limitado à geração do arquivo e nunca anterior ao instante da versão anterior.
 * No 1º turno isso resolve três defeitos de carimbo: AC/AM/RO/RR/MT/MS em hora local nas versões
 * regeradas, PE uma hora adiantado entre 18:09 e 20:15 e o exterior com a data do dia seguinte.
 */
export class RelogioArquivo {
  private readonly corretor: CorretorTotalizacao;
  private chaveAnt: string | null = null;
  private instAnt: number | null = null;

  constructor(uf: string) {
    this.corretor = new CorretorTotalizacao(uf);
  }

  /** `contagens` identifica o estado (ex.: st, tv e comparecimento juntos). */
  instante(contagens: string, totalizadoEm: string | null, geradoEm: string | null, capturadoEm: string): number {
    if (this.instAnt !== null && contagens === this.chaveAnt) return this.instAnt;
    let t = this.corretor.instante(totalizadoEm, geradoEm, capturadoEm);
    if (this.instAnt !== null && t < this.instAnt) t = this.instAnt;
    this.chaveAnt = contagens;
    this.instAnt = t;
    return t;
  }
}
