// /api/2t/ufs: as 27 UFs e o exterior, mais lentas primeiro, com régua do 1º turno, sinal de
// arquivo parado e os maiores municípios ainda abertos.
import { regiaoDe } from "../../turno2/comum.ts";
import type { AbRow } from "../consultas.ts";
import { nomeUf } from "../abr.ts";
import type { Ritmo, TotaisOut, VotoOut } from "./agregados.ts";
import { acumular, liderMargem, ritmo, somaVazia, totaisOut, votosOut } from "./agregados.ts";
import { isoDe, minutosDe, pstDe, r1 } from "./base.ts";
import type { LinhaTempo } from "./linha-tempo.ts";
import { versaoFechamento, versaoLidaAte, versaoNoInstante } from "./linha-tempo.ts";
import type { Municipio } from "./municipios.ts";
import type { Regua } from "./regua.ts";
import { comparar } from "./regua.ts";
import type { Relogio } from "./regioes.ts";
import { TODAS_UFS } from "./regioes.ts";

export const LIMIAR_PARADA_PADRAO_MIN = 10;

export interface Pendente {
  cd: string;
  nm: string;
  te: number;
  pst: number;
}

export interface UfLinha extends TotaisOut, Ritmo {
  uf: string;
  nome: string;
  regiao: string;
  munnr: number;
  munpt: number;
  munf: number;
  votos: Record<string, VotoOut>;
  lider: string | null;
  margem_pp: number;
  ultima_versao_em: string | null;
  idade_s: number | null;
  parada: boolean;
  ref_1t: {
    pst_mesmo_relogio: number | null;
    atraso_min: number | null;
    p50_min: number | null;
    p90_min: number | null;
    p99_min: number | null;
    p100_min: number | null;
    pa_final: number | null;
  } | null;
  pendentes_maiores: Pendente[];
}

export interface RespostaUfs {
  at: string;
  min: number;
  ele: number;
  cargo: number;
  limiar_parada_min: number;
  ufs: UfLinha[];
}

/** Os `n` maiores municípios abertos de cada UF, pelo eleitorado. */
export function pendentesPorUf(muns: readonly Municipio[], regua: Regua | null, n = 3): Map<string, Pendente[]> {
  const porUf = new Map<string, Pendente[]>();
  for (const m of muns) {
    if (m.ts > 0 && m.st >= m.ts) continue;
    const te = m.te > 0 ? m.te : (regua?.ref.municipios?.[m.uf]?.[m.cd]?.te ?? 0);
    const l = porUf.get(m.uf) ?? [];
    l.push({ cd: m.cd, nm: m.nm, te, pst: pstDe(m.st, m.ts) });
    porUf.set(m.uf, l);
  }
  for (const [uf, l] of porUf) porUf.set(uf, l.sort((a, b) => b.te - a.te || a.cd.localeCompare(b.cd)).slice(0, n));
  return porUf;
}

/** Instante (relógio do TSE) da primeira seção totalizada no país; null se ainda não começou. */
function inicioDoPais(lt: LinhaTempo, agoraMs: number): number | null {
  let ini: number | null = null;
  for (const l of lt.ufs.values()) {
    const v = l.versoes.find((x) => x.st > 0 && x.cap <= agoraMs);
    if (v && (ini === null || v.inst < ini)) ini = v.inst;
  }
  return ini;
}

/**
 * O resto do país totalizou seção nova entre `desdeMs` e `agoraMs`? Medido no relógio do TSE
 * (instante corrigido), para que versões anteriores a uma pausa geral, lidas com atraso, não contem.
 */
function paisAvancou(lt: LinhaTempo, exceto: string, desdeMs: number, agoraMs: number): boolean {
  let antes = 0;
  let agora = 0;
  for (const [uf, l] of lt.ufs) {
    if (uf === exceto) continue;
    antes += versaoNoInstante(l, desdeMs, agoraMs)?.st ?? 0;
    agora += versaoLidaAte(l, agoraMs)?.st ?? 0;
  }
  return agora > antes;
}

export interface EntradaUfs {
  lt: LinhaTempo;
  rel: Relogio;
  regua: Regua | null;
  /** -ab nacional (munnr/munpt/munf por UF, cdabr minúsculo) */
  ab: readonly AbRow[];
  muns: readonly Municipio[];
  limiarMin: number;
}

export function montarUfs(e: EntradaUfs): RespostaUfs {
  const { lt, rel, regua } = e;
  const minAgora = minutosDe(rel.agoraMs, rel.t0Ms);
  const ab = new Map(e.ab.map((r) => [r.cdabr.toUpperCase(), r]));
  const pend = pendentesPorUf(e.muns, regua);
  const inicio = inicioDoPais(lt, rel.agoraMs);
  const linhas: { linha: UfLinha; atraso: number | null }[] = [];
  for (const uf of TODAS_UFS) {
    const l = lt.ufs.get(uf);
    const v = l ? versaoLidaAte(l, rel.agoraMs) : null;
    const s = somaVazia();
    acumular(s, v);
    const lm = liderMargem(s.votos, s.vv);
    const ultimaMs = v?.inst ?? null;
    const idade = ultimaMs === null ? null : r1((rel.agoraMs - ultimaMs) / 1000);
    const aberta = s.ts > 0 && s.st < s.ts;
    // Parada conta desde a última versão, mas nunca antes de o país começar a totalizar.
    const desde = Math.max(ultimaMs ?? rel.t0Ms, rel.t0Ms, inicio ?? Number.POSITIVE_INFINITY);
    // O país precisa ter andado dentro da própria janela do limiar: numa pausa geral (19:32 a 20:02
    // no 1º turno) ninguém anda e nenhuma UF é marcada.
    const limiarMs = e.limiarMin * 60_000;
    const parada = aberta && inicio !== null && rel.agoraMs - desde > limiarMs && paisAvancou(lt, uf, rel.agoraMs - limiarMs, rel.agoraMs);
    const curva = regua?.uf(uf) ?? null;
    const marcos = regua?.marcosUf(uf) ?? null;
    const fech = l && v && !aberta && s.ts > 0 ? versaoFechamento(l) : null;
    const abUf = ab.get(uf);
    const reg = regiaoDe(uf);
    const linha: UfLinha = {
      uf,
      nome: nomeUf(uf),
      regiao: reg ?? "",
      ...totaisOut(s),
      munnr: abUf?.munnr ?? 0,
      munpt: abUf?.munpt ?? 0,
      munf: abUf?.munf ?? 0,
      votos: votosOut(s),
      lider: lm.lider,
      margem_pp: lm.margem_pp,
      ultima_versao_em: ultimaMs === null ? null : isoDe(ultimaMs),
      idade_s: idade,
      ...ritmo(l ? [l] : [], rel.agoraMs),
      parada,
      ref_1t: regua && curva
        ? {
            ...comparar(curva, s.st, s.ts, minAgora, fech ? minutosDe(fech.inst, rel.t0Ms) : null),
            p50_min: marcos?.p50 ?? null,
            p90_min: marcos?.p90 ?? null,
            p99_min: marcos?.p99 ?? null,
            p100_min: marcos?.p100 ?? null,
            pa_final: regua.paFinal([uf]),
          }
        : null,
      pendentes_maiores: pend.get(uf) ?? [],
    };
    linhas.push({ linha, atraso: linha.ref_1t?.atraso_min ?? null });
  }
  linhas.sort((a, b) => a.linha.pst - b.linha.pst || maiorAtrasoPrimeiro(a.atraso, b.atraso) || a.linha.uf.localeCompare(b.linha.uf));
  return { at: isoDe(rel.agoraMs), min: minAgora, ele: lt.ele, cargo: lt.cargo, limiar_parada_min: e.limiarMin, ufs: linhas.map((x) => x.linha) };
}

/** Desempate: maior atraso primeiro; sem régua por último. */
function maiorAtrasoPrimeiro(x: number | null, y: number | null): number {
  if (x === y) return 0;
  if (x === null) return 1;
  if (y === null) return -1;
  return y - x;
}
