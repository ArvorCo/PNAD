// /api/2t/evolucao: % de seções e % válidos do duelo numa grade desde 17:00 de Brasília.
// Em cada instante da grade, cada UF entra com a última versão cujo instante de totalização
// corrigido não passa dele; região e Brasil são somas. A régua do 1º turno vem na mesma grade.
import { ORDEM_REGIOES, REGIOES } from "../../turno2/comum.ts";
import { isoDe, minutosDe, pstDe, r2 } from "./base.ts";
import type { CandInfo } from "./estaduais.ts";
import type { LinhaTempo, Versao } from "./linha-tempo.ts";
import { versaoLidaAte } from "./linha-tempo.ts";
import type { Regua } from "./regua.ts";
import { pstMesmoRelogio } from "./regua.ts";
import type { Relogio } from "./regioes.ts";
import { TODAS_UFS } from "./regioes.ts";

export const PASSO_MIN_S = 30;
export const PASSO_MAX_S = 3600;
export const PASSO_PADRAO_S = 60;
export const MAX_PONTOS = 1440;
/** Teto de pontos somando todas as séries: com 29 séries (nível uf) dá 413 pontos, cerca de 400 KB. */
export const MAX_CELULAS = 12_000;

export type NivelEvolucao = "regiao" | "uf";
/** [min, pst, pvapn_a, pvapn_b, st] */
export type PontoEvolucao = [number, number, number, number, number];

export interface RespostaEvolucao {
  at: string;
  ele: number;
  cargo: number;
  passo_s: number;
  candidatos: { sqcand: string; n: string; nome_urna: string }[];
  series: Record<string, PontoEvolucao[]>;
  referencia_1t: Record<string, [number, number][]> | null;
}

/** Os dois candidatos do duelo: os dois mais votados no último estado (ou os dois primeiros números), em ordem de número. */
export function duelo(lt: LinhaTempo, agoraMs: number, cands: readonly CandInfo[]): CandInfo[] {
  const soma = new Map<number, number>();
  for (const l of lt.ufs.values()) {
    const v = versaoLidaAte(l, agoraMs);
    if (v) for (const [sq, vap] of v.votos) soma.set(sq, (soma.get(sq) ?? 0) + vap);
  }
  const info = new Map(cands.map((c) => [c.sqcand, c]));
  const num = (sq: number): number => info.get(sq)?.numero ?? Number.POSITIVE_INFINITY;
  const conhecidos = [...new Set([...soma.keys(), ...cands.map((c) => c.sqcand)])];
  const escolhidos = conhecidos.sort((a, b) => (soma.get(b) ?? 0) - (soma.get(a) ?? 0) || num(a) - num(b) || a - b).slice(0, 2);
  return escolhidos
    .map((sq) => info.get(sq) ?? { sqcand: sq, uf: "", numero: null, nome_urna: "", sigla: "", fed_sigla: null })
    .sort((a, b) => (a.numero ?? Number.POSITIVE_INFINITY) - (b.numero ?? Number.POSITIVE_INFINITY) || a.sqcand - b.sqcand);
}

export function chavesDe(nivel: NivelEvolucao): { chave: string; ufs: readonly string[] }[] {
  const br = { chave: "BR", ufs: TODAS_UFS };
  if (nivel === "uf") return [br, ...TODAS_UFS.map((uf) => ({ chave: uf, ufs: [uf] }))];
  return [br, ...ORDEM_REGIOES.map((r) => ({ chave: r as string, ufs: REGIOES[r] }))];
}

/**
 * Instantes da grade (ms): de 17:00 até agora, mais o próprio agora; vazio antes das 17:00.
 * O passo pedido cresce (em múltiplos de 30 s) quando a noite não cabe no teto de pontos.
 */
export function grade(t0Ms: number, agoraMs: number, passoS: number, nSeries = 1): { instantes: number[]; passo_s: number } {
  if (agoraMs < t0Ms) return { instantes: [], passo_s: passoS };
  const span = (agoraMs - t0Ms) / 1000;
  const maxPontos = Math.max(1, Math.min(MAX_PONTOS, Math.floor(MAX_CELULAS / Math.max(1, nSeries))));
  const passo = Math.max(passoS, Math.ceil(span / maxPontos / PASSO_MIN_S) * PASSO_MIN_S);
  const instantes: number[] = [];
  for (let t = t0Ms; t <= agoraMs; t += passo * 1000) instantes.push(t);
  if (instantes[instantes.length - 1] !== agoraMs) instantes.push(agoraMs);
  return { instantes, passo_s: passo };
}

export interface EntradaEvolucao {
  lt: LinhaTempo;
  rel: Relogio;
  regua: Regua | null;
  cands: readonly CandInfo[];
  nivel: NivelEvolucao;
  passoS: number;
}

export function montarEvolucao(e: EntradaEvolucao): RespostaEvolucao {
  const { lt, rel, regua } = e;
  const [a, b] = duelo(lt, rel.agoraMs, e.cands);
  const chaves = chavesDe(e.nivel);
  const { instantes, passo_s } = grade(rel.t0Ms, rel.agoraMs, e.passoS, chaves.length);
  const series: Record<string, PontoEvolucao[]> = Object.fromEntries(chaves.map((c) => [c.chave, [] as PontoEvolucao[]]));
  // Varredura única: um ponteiro por UF sobre as versões (o instante corrigido cresce com o id).
  const linhas = TODAS_UFS.map((uf) => lt.ufs.get(uf)?.versoes.filter((v) => v.cap <= rel.agoraMs) ?? []);
  const pos = linhas.map(() => -1);
  const indice = new Map(TODAS_UFS.map((uf, i) => [uf, i]));
  for (const t of instantes) {
    const atual: (Versao | null)[] = linhas.map((l, i) => {
      let p = pos[i] ?? -1;
      while (p + 1 < l.length && (l[p + 1]?.inst ?? Infinity) <= t) p += 1;
      pos[i] = p;
      return p >= 0 ? (l[p] ?? null) : null;
    });
    const min = minutosDe(t, rel.t0Ms);
    for (const c of chaves) {
      let st = 0;
      let ts = 0;
      let vv = 0;
      let va = 0;
      let vb = 0;
      for (const uf of c.ufs) {
        const v = atual[indice.get(uf) ?? -1];
        if (!v) continue;
        st += v.st;
        ts += v.ts;
        vv += v.vv;
        if (a) va += v.votos.get(a.sqcand) ?? 0;
        if (b) vb += v.votos.get(b.sqcand) ?? 0;
      }
      series[c.chave]?.push([min, pstDe(st, ts), vv > 0 ? r2((100 * va) / vv) : 0, vv > 0 ? r2((100 * vb) / vv) : 0, st]);
    }
  }
  let referencia_1t: Record<string, [number, number][]> | null = null;
  if (regua) {
    referencia_1t = {};
    for (const c of chaves) {
      const curva = regua.agregada(c.ufs);
      referencia_1t[c.chave] = curva
        ? instantes.map((t): [number, number] => {
            const m = minutosDe(t, rel.t0Ms);
            return [m, pstMesmoRelogio(curva, m)];
          })
        : [];
    }
  }
  return {
    at: isoDe(rel.agoraMs),
    ele: lt.ele,
    cargo: lt.cargo,
    passo_s,
    candidatos: [a, b].flatMap((c) => (c ? [{ sqcand: String(c.sqcand), n: c.numero === null ? "" : String(c.numero), nome_urna: c.nome_urna }] : [])),
    series,
    referencia_1t,
  };
}
