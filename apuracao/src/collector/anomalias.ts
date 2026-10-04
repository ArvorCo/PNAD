// Anomalias calculadas na escrita, contra o estado anterior em memória.
import type { EventoNovo, IdRef } from "../db/escrita.ts";
import type { LinhaVotoCandidato } from "../db/linhas.ts";
import type { FileKey } from "../types.ts";
import type { CandResumo, TotaisResumo } from "./estado-arquivos.ts";

export const MAX_EVENTOS_CANDIDATO = 20;

const CAMPOS_CONTAGEM = ["st", "vvc", "vv", "vnom", "tv", "comparecimento", "est"] as const satisfies readonly (keyof TotaisResumo)[];

export interface CtxAnomalia {
  em: string;
  arquivoId: number;
  snapshot: IdRef;
  key: FileKey;
}

export interface ResultadoAnomalias {
  eventos: EventoNovo[];
  /** alguma anomalia de severidade warn: o snapshot força voto_candidato */
  alerta: boolean;
}

export function candidatosDe(rows: readonly LinhaVotoCandidato[]): Map<number, CandResumo> {
  const m = new Map<number, CandResumo>();
  for (const r of rows) m.set(r.sqcand, { vap: r.vap, eleito: r.eleito });
  return m;
}

export function compararU(
  antT: TotaisResumo | null,
  novoT: TotaisResumo,
  antC: ReadonlyMap<number, CandResumo> | null,
  novoC: ReadonlyMap<number, CandResumo> | null,
  ctx: CtxAnomalia,
): ResultadoAnomalias {
  const eventos: EventoNovo[] = [];
  const k = ctx.key;
  const base = (tipo: string, severidade: "info" | "warn", detalhe: unknown): EventoNovo => ({
    em: ctx.em, tipo, severidade, arquivo_id: ctx.arquivoId, snapshot_id: ctx.snapshot, eleicao_cd: k.ele,
    cargo_cd: k.cargo, nivel: k.nivel, uf: k.uf, municipio_cd: k.mun, zona_cd: k.zona, detalhe,
  });
  let alerta = false;

  if (antT !== null) {
    for (const campo of CAMPOS_CONTAGEM) {
      const de = antT[campo];
      const para = novoT[campo];
      if (de !== null && para !== null && para < de) {
        eventos.push(base("regressao_contagem", "warn", { campo, de, para }));
        alerta = true;
      }
    }
    if (antT.pst !== null && novoT.pst !== null && novoT.pst < antT.pst) {
      eventos.push(base("regressao_pst", "warn", { de: antT.pst, para: novoT.pst }));
      alerta = true;
    }
  }

  if (antC !== null && novoC !== null && antC.size > 0) {
    const regressoes: { sqcand: number; de: number; para: number }[] = [];
    const novos: number[] = [];
    const sumidos: number[] = [];
    const eleitos: { sqcand: number; de: number | null; para: number | null }[] = [];
    for (const [sq, c] of novoC) {
      const a = antC.get(sq);
      if (a === undefined) {
        novos.push(sq);
        continue;
      }
      if (a.vap !== null && c.vap !== null && c.vap < a.vap) regressoes.push({ sqcand: sq, de: a.vap, para: c.vap });
      if ((k.nivel === "br" || k.nivel === "uf") && a.eleito !== c.eleito && (a.eleito !== null || c.eleito !== null)) {
        eleitos.push({ sqcand: sq, de: a.eleito, para: c.eleito });
      }
    }
    for (const sq of antC.keys()) if (!novoC.has(sq)) sumidos.push(sq);

    for (const r of regressoes.slice(0, MAX_EVENTOS_CANDIDATO)) {
      eventos.push(base("regressao_contagem", "warn", { campo: "vap", ...r }));
    }
    if (regressoes.length > MAX_EVENTOS_CANDIDATO) {
      eventos.push(base("regressao_contagem", "warn", { campo: "vap", resumo: true, n_candidatos: regressoes.length }));
    }
    if (regressoes.length > 0) alerta = true;
    const lista = (tipo: string, sqs: number[]): void => {
      if (sqs.length === 0) return;
      eventos.push(base(tipo, "warn", { n: sqs.length, sqcand: sqs.slice(0, MAX_EVENTOS_CANDIDATO) }));
      alerta = true;
    };
    lista("candidato_novo", novos);
    lista("candidato_sumiu", sumidos);
    for (const e of eleitos.slice(0, MAX_EVENTOS_CANDIDATO)) eventos.push(base("eleito_mudou", "info", e));
  }
  return { eventos, alerta };
}
