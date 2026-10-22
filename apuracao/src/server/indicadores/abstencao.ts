// /api/2t/abstencao: abstenção dos municípios já fechados no 2º turno contra os mesmos municípios
// no 1º (régua). Diferença de abstenção pede explicação, não indica irregularidade.
import type { Regiao } from "../../turno2/comum.ts";
import { NOME_REGIAO, ORDEM_REGIOES, REGIOES } from "../../turno2/comum.ts";
import { nomeUf } from "../abr.ts";
import { isoDe, minutosDe, paOuNull, r2 } from "./base.ts";
import type { LinhaTempo } from "./linha-tempo.ts";
import { versaoLidaAte } from "./linha-tempo.ts";
import type { Municipio } from "./municipios.ts";
import type { Regua } from "./regua.ts";
import type { Relogio } from "./regioes.ts";
import { TODAS_UFS } from "./regioes.ts";

export const DESTAQUE_DELTA_PP = 3;
export const DESTAQUE_TE_MIN = 20_000;
export const DESTAQUE_MAX = 20;

export interface BlocoBase {
  nome: string;
  n_mun: number;
  n_mun_fechados: number;
  te_fechado: number;
  pct_te_fechado: number;
  comparecimento: number;
  abstencao: number;
  pa_2t: number | null;
  pa_1t_mesmos: number | null;
  delta_pp: number | null;
}

export type BlocoSigla = BlocoBase & { sigla: string };
export type BlocoUf = BlocoBase & { uf: string; pa_corrente: number | null; pa_final_1t: number | null };

export interface MunDestaque {
  uf: string;
  cd: string;
  nm: string;
  te: number;
  pa_2t: number;
  pa_1t: number;
  delta_pp: number;
  fechou_min: number | null;
}

export interface RespostaAbstencao {
  at: string;
  min: number;
  ele: number;
  cargo: number;
  base: "municipios_fechados";
  brasil: BlocoSigla;
  regioes: BlocoSigla[];
  ufs: BlocoUf[];
  destaques: { subiu: MunDestaque[]; caiu: MunDestaque[] };
}

interface Acc {
  n_mun: number;
  n_fech: number;
  te_total: number;
  te_fech: number;
  c2: number;
  a2: number;
  c1: number;
  a1: number;
}

const accVazio = (): Acc => ({ n_mun: 0, n_fech: 0, te_total: 0, te_fech: 0, c2: 0, a2: 0, c1: 0, a1: 0 });

function somarAcc(alvo: Acc, x: Acc): void {
  alvo.n_mun += x.n_mun;
  alvo.n_fech += x.n_fech;
  alvo.te_total += x.te_total;
  alvo.te_fech += x.te_fech;
  alvo.c2 += x.c2;
  alvo.a2 += x.a2;
  alvo.c1 += x.c1;
  alvo.a1 += x.a1;
}

/** Percentual sem arredondar (para diferenças). */
const paBruto = (c: number, a: number): number | null => (c + a > 0 ? (100 * a) / (c + a) : null);

function bloco(nome: string, x: Acc, comRegua: boolean): BlocoBase {
  const p2 = paBruto(x.c2, x.a2);
  const p1 = comRegua ? paBruto(x.c1, x.a1) : null;
  return {
    nome,
    n_mun: x.n_mun,
    n_mun_fechados: x.n_fech,
    te_fechado: x.te_fech,
    pct_te_fechado: x.te_total > 0 ? r2((100 * x.te_fech) / x.te_total) : 0,
    comparecimento: x.c2,
    abstencao: x.a2,
    pa_2t: p2 === null ? null : r2(p2),
    pa_1t_mesmos: p1 === null ? null : r2(p1),
    delta_pp: p2 !== null && p1 !== null ? r2(p2 - p1) : null,
  };
}

export interface EntradaAbstencao {
  lt: LinhaTempo;
  rel: Relogio;
  regua: Regua | null;
  muns: readonly Municipio[];
}

export function montarAbstencao(e: EntradaAbstencao): RespostaAbstencao {
  const { regua, rel } = e;
  const refMun = regua?.ref.municipios ?? null;
  const porUf = new Map<string, Acc>();
  const candidatos: MunDestaque[] = [];
  for (const m of e.muns) {
    const acc = porUf.get(m.uf) ?? accVazio();
    porUf.set(m.uf, acc);
    const r = refMun?.[m.uf]?.[m.cd];
    const te = m.te > 0 ? m.te : (r?.te ?? 0);
    acc.n_mun += 1;
    acc.te_total += te;
    if (!(m.ts > 0 && m.st >= m.ts)) continue;
    // Com a régua, a comparação usa só os municípios que também estão nela (mesmos municípios).
    if (refMun && !r) continue;
    acc.n_fech += 1;
    acc.te_fech += te;
    acc.c2 += m.comparecimento;
    acc.a2 += m.abstencao;
    if (!r) continue;
    acc.c1 += r.comparecimento;
    acc.a1 += r.abstencao;
    const p2 = paBruto(m.comparecimento, m.abstencao);
    const p1 = paBruto(r.comparecimento, r.abstencao);
    if (p2 === null || p1 === null || te < DESTAQUE_TE_MIN) continue;
    const d = p2 - p1;
    if (Math.abs(d) < DESTAQUE_DELTA_PP) continue;
    candidatos.push({
      uf: m.uf, cd: m.cd, nm: m.nm, te, pa_2t: r2(p2), pa_1t: r2(p1), delta_pp: r2(d),
      fechou_min: m.fechouMs === null ? null : minutosDe(m.fechouMs, rel.t0Ms),
    });
  }
  const comRegua = refMun !== null;
  const somaDe = (ufs: readonly string[]): Acc => {
    const t = accVazio();
    for (const uf of ufs) {
      const x = porUf.get(uf);
      if (x) somarAcc(t, x);
    }
    return t;
  };
  const ufs: BlocoUf[] = TODAS_UFS.map((uf) => {
    const l = e.lt.ufs.get(uf);
    const v = l ? versaoLidaAte(l, rel.agoraMs) : null;
    return {
      uf,
      ...bloco(nomeUf(uf), porUf.get(uf) ?? accVazio(), comRegua),
      pa_corrente: v ? paOuNull(v.comparecimento, v.abstencao) : null,
      pa_final_1t: regua?.paFinal([uf]) ?? null,
    };
  });
  const ordem = (a: MunDestaque, b: MunDestaque): number => Math.abs(b.delta_pp) - Math.abs(a.delta_pp) || b.te - a.te || a.cd.localeCompare(b.cd);
  return {
    at: isoDe(rel.agoraMs),
    min: minutosDe(rel.agoraMs, rel.t0Ms),
    ele: e.lt.ele,
    cargo: e.lt.cargo,
    base: "municipios_fechados",
    brasil: { sigla: "BR", ...bloco("Brasil", somaDe(TODAS_UFS), comRegua) },
    regioes: ORDEM_REGIOES.map((r: Regiao) => ({ sigla: r, ...bloco(NOME_REGIAO[r], somaDe(REGIOES[r]), comRegua) })),
    ufs,
    destaques: {
      subiu: candidatos.filter((c) => c.delta_pp > 0).sort(ordem).slice(0, DESTAQUE_MAX),
      caiu: candidatos.filter((c) => c.delta_pp < 0).sort(ordem).slice(0, DESTAQUE_MAX),
    },
  };
}
