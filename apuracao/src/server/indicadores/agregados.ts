// Soma de estados de UF (regiões, Brasil) e as medidas derivadas: votos em % válidos, líder,
// margem, velocidade em seções por minuto nos últimos 10 min e previsão de 100%.
import type { LinhaTempo, LinhaUf, Versao } from "./linha-tempo.ts";
import { versaoFechamento, versaoLidaAte, versaoPublicadaAte } from "./linha-tempo.ts";
import { isoDe, minutosDe, paDe, pstDe, r2 } from "./base.ts";

export const JANELA_VEL_MS = 10 * 60_000;
/** Previsão de 100% além deste horizonte vira null (velocidade de retomada ou de fim de noite). */
export const ETA_MAX_MS = 8 * 3_600_000;
/** Abaixo desta velocidade (3 seções em 10 min) não há previsão: uma ou duas seções são ruído. */
export const VEL_MIN_ETA_SPM = 0.3;

export interface Soma {
  ts: number;
  st: number;
  snt: number;
  te: number;
  est: number;
  comparecimento: number;
  abstencao: number;
  tv: number;
  vv: number;
  vb: number;
  vn: number;
  votos: Map<number, number>;
}

export function somaVazia(): Soma {
  return { ts: 0, st: 0, snt: 0, te: 0, est: 0, comparecimento: 0, abstencao: 0, tv: 0, vv: 0, vb: 0, vn: 0, votos: new Map() };
}

export function acumular(s: Soma, v: Versao | null): void {
  if (!v) return;
  s.ts += v.ts;
  s.st += v.st;
  s.snt += v.snt;
  s.te += v.te;
  s.est += v.est;
  s.comparecimento += v.comparecimento;
  s.abstencao += v.abstencao;
  s.tv += v.tv;
  s.vv += v.vv;
  s.vb += v.vb;
  s.vn += v.vn;
  for (const [sq, vap] of v.votos) s.votos.set(sq, (s.votos.get(sq) ?? 0) + vap);
}

export interface VotoOut {
  vap: number;
  pvapn: number;
}

export function votosOut(s: Soma): Record<string, VotoOut> {
  const out: Record<string, VotoOut> = {};
  for (const [sq, vap] of [...s.votos].sort((x, y) => x[0] - y[0])) out[String(sq)] = { vap, pvapn: s.vv > 0 ? r2((100 * vap) / s.vv) : 0 };
  return out;
}

/** Líder e margem em pontos de % válidos; sem voto ou com empate no topo, líder null e margem 0. */
export function liderMargem(votos: ReadonlyMap<number, number>, vv: number): { lider: string | null; margem_pp: number } {
  const ord = [...votos].sort((x, y) => y[1] - x[1] || x[0] - y[0]);
  const [a, b] = ord;
  if (!a || a[1] <= 0 || vv <= 0) return { lider: null, margem_pp: 0 };
  if (b && b[1] === a[1]) return { lider: null, margem_pp: 0 };
  return { lider: String(a[0]), margem_pp: r2((100 * (a[1] - (b?.[1] ?? 0))) / vv) };
}

export interface Ritmo {
  vel_10min_spm: number;
  eta_100_iso: string | null;
}

/**
 * Seções por minuto publicadas nos últimos 10 min, no relógio de publicação do TSE (gerado_em):
 * pelo carimbo de totalização, a volta de uma pausa geral (totalizações de durante a pausa,
 * publicadas depois dela) zerava a velocidade e jogava a previsão de 100% para semanas adiante.
 * Previsão null abaixo de VEL_MIN_ETA_SPM ou além de ETA_MAX_MS.
 */
export function ritmo(linhas: readonly LinhaUf[], agoraMs: number): Ritmo {
  let st = 0;
  let ts = 0;
  let stAntes = 0;
  for (const l of linhas) {
    const v = versaoLidaAte(l, agoraMs);
    st += v?.st ?? 0;
    ts += v?.ts ?? 0;
    stAntes += versaoPublicadaAte(l, agoraMs - JANELA_VEL_MS, agoraMs)?.st ?? 0;
  }
  const vel = Math.max(0, (st - stAntes) / (JANELA_VEL_MS / 60_000));
  const faltaMs = vel >= VEL_MIN_ETA_SPM && ts > st ? ((ts - st) / vel) * 60_000 : Number.POSITIVE_INFINITY;
  const eta = faltaMs <= ETA_MAX_MS ? isoDe(agoraMs + faltaMs) : null;
  return { vel_10min_spm: r2(vel), eta_100_iso: eta };
}

export interface EstadoConjunto {
  soma: Soma;
  linhas: LinhaUf[];
  /** maior instante corrigido entre as versões vigentes (ms) */
  atualizadoMs: number | null;
  /** minuto (após 17:00) em que o conjunto inteiro fechou; null se não fechou */
  fechouMin: number | null;
}

/** Estado somado de um conjunto de UFs no instante `agoraMs` (o que estava lido). */
export function estadoConjunto(lt: LinhaTempo, ufs: readonly string[], agoraMs: number, t0Ms: number): EstadoConjunto {
  const soma = somaVazia();
  const linhas: LinhaUf[] = [];
  let atualizadoMs: number | null = null;
  let fechouMs: number | null = null;
  let todasFecharam = true;
  for (const uf of ufs) {
    const l = lt.ufs.get(uf.toUpperCase());
    if (!l) {
      todasFecharam = false;
      continue;
    }
    linhas.push(l);
    const v = versaoLidaAte(l, agoraMs);
    acumular(soma, v);
    if (v) atualizadoMs = atualizadoMs === null ? v.inst : Math.max(atualizadoMs, v.inst);
    const f = v && v.ts > 0 && v.st >= v.ts ? versaoFechamento(l) : null;
    if (f) fechouMs = fechouMs === null ? f.inst : Math.max(fechouMs, f.inst);
    else todasFecharam = false;
  }
  return { soma, linhas, atualizadoMs, fechouMin: todasFecharam && fechouMs !== null ? minutosDe(fechouMs, t0Ms) : null };
}

export interface TotaisOut {
  ts: number;
  st: number;
  snt: number;
  pst: number;
  te: number;
  est: number;
  comparecimento: number;
  abstencao: number;
  pa: number;
}

export function totaisOut(s: Soma): TotaisOut {
  return {
    ts: s.ts, st: s.st, snt: s.snt, pst: pstDe(s.st, s.ts), te: s.te, est: s.est,
    comparecimento: s.comparecimento, abstencao: s.abstencao, pa: paDe(s.comparecimento, s.abstencao),
  };
}
