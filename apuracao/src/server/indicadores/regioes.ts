// /api/2t/regioes: soma dos arquivos de UF por região e Brasil, com ritmo e régua do 1º turno.
import type { Regiao } from "../../turno2/comum.ts";
import { NOME_REGIAO, ORDEM_REGIOES, REGIOES } from "../../turno2/comum.ts";
import type { Ritmo, TotaisOut, VotoOut } from "./agregados.ts";
import { estadoConjunto, liderMargem, ritmo, totaisOut, votosOut } from "./agregados.ts";
import { isoDe, minutosDe } from "./base.ts";
import type { LinhaTempo } from "./linha-tempo.ts";
import type { Regua } from "./regua.ts";
import { comparar } from "./regua.ts";

export const TODAS_UFS: readonly string[] = ORDEM_REGIOES.flatMap((r) => REGIOES[r]);

export interface Agregado extends TotaisOut, Ritmo {
  sigla: string;
  nome: string;
  ufs: string[];
  votos: Record<string, VotoOut>;
  vv: number;
  vb: number;
  vn: number;
  tv: number;
  lider: string | null;
  margem_pp: number;
  ref_1t: { pst_mesmo_relogio: number | null; atraso_min: number | null; pa_final_1t: number | null } | null;
  atualizado_em: string | null;
}

export interface Relogio {
  agoraMs: number;
  t0Ms: number;
}

export function agregado(lt: LinhaTempo, sigla: string, nome: string, ufs: readonly string[], rel: Relogio, regua: Regua | null): Agregado {
  const e = estadoConjunto(lt, ufs, rel.agoraMs, rel.t0Ms);
  const s = e.soma;
  const minAgora = minutosDe(rel.agoraMs, rel.t0Ms);
  const curva = regua?.agregada(ufs) ?? null;
  const lm = liderMargem(s.votos, s.vv);
  return {
    sigla,
    nome,
    ufs: [...ufs],
    ...totaisOut(s),
    votos: votosOut(s),
    vv: s.vv,
    vb: s.vb,
    vn: s.vn,
    tv: s.tv,
    lider: lm.lider,
    margem_pp: lm.margem_pp,
    ...ritmo(e.linhas, rel.agoraMs),
    ref_1t: regua && curva ? { ...comparar(curva, s.st, s.ts, minAgora, e.fechouMin), pa_final_1t: regua.paFinal(ufs) } : null,
    atualizado_em: e.atualizadoMs === null ? null : isoDe(e.atualizadoMs),
  };
}

export interface RespostaRegioes {
  at: string;
  min: number;
  ele: number;
  cargo: number;
  turno: number;
  referencia_1t: boolean;
  brasil: Agregado;
  regioes: Agregado[];
}

export function montarRegioes(lt: LinhaTempo, rel: Relogio, turno: number, regua: Regua | null): RespostaRegioes {
  return {
    at: isoDe(rel.agoraMs),
    min: minutosDe(rel.agoraMs, rel.t0Ms),
    ele: lt.ele,
    cargo: lt.cargo,
    turno,
    referencia_1t: regua !== null,
    brasil: agregado(lt, "BR", "Brasil", TODAS_UFS, rel, regua),
    regioes: ORDEM_REGIOES.map((r: Regiao) => agregado(lt, r, NOME_REGIAO[r], REGIOES[r], rel, regua)),
  };
}
