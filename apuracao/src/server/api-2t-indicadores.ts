// Indicadores do 2º turno (regiões, UFs, abstenção, estaduais, evolução). Contrato em
// ../../../analysis/apuracao_2t_2026/CONTRATO.md. As leituras do banco têm cache curto
// (indicadores/*); a montagem usa o relógio do pedido, então idade e ritmo nunca envelhecem no cache.
import type { Database } from "bun:sqlite";
import { arquivoPorChave, maxSnapshotId } from "../db/leitura.ts";
import { chave, keyAb } from "../tse/urls.ts";
import { eleicoes } from "./api-config.ts";
import { CacheCurto } from "./cache.ts";
import type { AbRow } from "./consultas.ts";
import { abAsOf } from "./consultas.ts";
import type { Contexto } from "./contexto.ts";
import { ErroHttp } from "./http.ts";
import type { Params } from "./http.ts";
import { montarAbstencao } from "./indicadores/abstencao.ts";
import type { RespostaAbstencao } from "./indicadores/abstencao.ts";
import { isoDe, minutosDe, t0De, turnoDe } from "./indicadores/base.ts";
import { candidatosCargo, montarEstaduais } from "./indicadores/estaduais.ts";
import type { CandInfo, RespostaEstaduais } from "./indicadores/estaduais.ts";
import { PASSO_MAX_S, PASSO_MIN_S, PASSO_PADRAO_S, montarEvolucao } from "./indicadores/evolucao.ts";
import type { NivelEvolucao, RespostaEvolucao } from "./indicadores/evolucao.ts";
import { linhaTempo } from "./indicadores/linha-tempo.ts";
import { ROTULO_PROJECAO, projetar } from "./indicadores/projecao.ts";
import type { ResultadoProjecao } from "./indicadores/projecao.ts";
import { RECONSTRUIR_POR_CHAMADA, SerieProjecao, candidatosProjecao, obsMunicipais } from "./indicadores/projecao-dados.ts";
import type { CandProjecao, PontoSerieProjecao } from "./indicadores/projecao-dados.ts";
import { carregarReferenciaVotos } from "../turno2/referencia.ts";
import { municipios } from "./indicadores/municipios.ts";
import type { Relogio, RespostaRegioes } from "./indicadores/regioes.ts";
import { montarRegioes } from "./indicadores/regioes.ts";
import { regua } from "./indicadores/regua.ts";
import { LIMIAR_PARADA_PADRAO_MIN, montarUfs } from "./indicadores/ufs.ts";
import type { RespostaUfs } from "./indicadores/ufs.ts";

interface Alvo {
  ele: number;
  cargo: number;
  at: string | undefined;
  rel: Relogio;
}

function alvo(ctx: Contexto, db: Database, p: Params, padrao: "federal" | "estadual"): Alvo {
  const el = eleicoes(db);
  const ele = p.int("ele") ?? (padrao === "federal" ? el.federal : el.estadual);
  const cargo = p.int("cargo") ?? (padrao === "federal" ? 1 : 3);
  const at = p.at();
  const agoraMs = Date.parse(at ?? ctx.agora());
  if (!Number.isFinite(agoraMs)) throw new ErroHttp(400, "relógio do servidor inválido");
  return { ele, cargo, at, rel: { agoraMs, t0Ms: t0De(ele) } };
}

const cacheAb = new CacheCurto<AbRow[]>(3000, 16);

/** -ab nacional da eleição até `at` (munnr, munpt e munf por UF). */
function abNacional(db: Database, ele: number, at: string | undefined): AbRow[] {
  return cacheAb.obter([db.filename, ele, at ?? ""].join("|"), maxSnapshotId(db), () => {
    const arq = arquivoPorChave(db, chave(keyAb(ele, "br")));
    return arq ? abAsOf(db, arq.id, at).filter((r) => r.cdabr !== "br") : [];
  });
}

const cacheCands = new CacheCurto<CandInfo[]>(30_000, 8);

function cands(db: Database, ele: number, cargo: number): CandInfo[] {
  return cacheCands.obter([db.filename, ele, cargo].join("|"), maxSnapshotId(db), () => candidatosCargo(db, ele, cargo));
}

export function regioes(ctx: Contexto, db: Database, p: Params): RespostaRegioes {
  const a = alvo(ctx, db, p, "federal");
  return montarRegioes(linhaTempo(db, a.ele, a.cargo, a.at), a.rel, turnoDe(a.ele) ?? eleicoes(db).turno, regua());
}

export function ufs(ctx: Contexto, db: Database, p: Params): RespostaUfs {
  const a = alvo(ctx, db, p, "federal");
  return montarUfs({
    lt: linhaTempo(db, a.ele, a.cargo, a.at),
    rel: a.rel,
    regua: regua(),
    ab: abNacional(db, a.ele, a.at),
    muns: municipios(db, a.ele, a.cargo, a.at),
    limiarMin: p.limite("limiar_parada_min", LIMIAR_PARADA_PADRAO_MIN, 120),
  });
}

export function abstencao(ctx: Contexto, db: Database, p: Params): RespostaAbstencao {
  const a = alvo(ctx, db, p, "federal");
  return montarAbstencao({ lt: linhaTempo(db, a.ele, a.cargo, a.at), rel: a.rel, regua: regua(), muns: municipios(db, a.ele, a.cargo, a.at) });
}

export function estaduais(ctx: Contexto, db: Database, p: Params): RespostaEstaduais {
  const a = alvo(ctx, db, p, "estadual");
  return montarEstaduais({
    lt: linhaTempo(db, a.ele, a.cargo, a.at),
    rel: a.rel,
    regua: regua(),
    ab: abNacional(db, a.ele, a.at),
    cands: cands(db, a.ele, a.cargo),
    campo: (sq, sigla, fed) => ctx.campos.campoCandidato(sq, sigla, fed),
  });
}

export function evolucao(ctx: Contexto, db: Database, p: Params): RespostaEvolucao {
  const a = alvo(ctx, db, p, "federal");
  const nivel = p.texto("nivel") ?? "regiao";
  if (nivel !== "regiao" && nivel !== "uf") throw new ErroHttp(400, "nivel precisa ser regiao ou uf");
  return montarEvolucao({
    lt: linhaTempo(db, a.ele, a.cargo, a.at),
    rel: a.rel,
    regua: regua(),
    cands: cands(db, a.ele, a.cargo),
    nivel: nivel as NivelEvolucao,
    passoS: p.limite("passo", PASSO_PADRAO_S, PASSO_MAX_S, PASSO_MIN_S),
  });
}

// ---------------------------------------------------------------- /api/2t/projecao

export interface RespostaProjecao extends ResultadoProjecao {
  at: string;
  min: number;
  ele: number;
  cargo: number;
  rotulo: string;
  candidatos: { f: CandProjecao; l: CandProjecao } | null;
  serie: PontoSerieProjecao[];
}

const cacheProj = new CacheCurto<ResultadoProjecao>(10_000, 64);
const cacheCandsProj = new CacheCurto<{ f: CandProjecao; l: CandProjecao } | null>(60_000, 8);
const series = new Map<string, SerieProjecao>();

function serieDe(db: Database, ele: number, cargo: number): SerieProjecao {
  const k = [db.filename, ele, cargo].join("|");
  let s = series.get(k);
  if (!s) {
    s = cargo === 1 ? SerieProjecao.paraBanco(db, ele) : new SerieProjecao(null);
    series.set(k, s);
  }
  return s;
}

function pontoDe(min: number, r: ResultadoProjecao): PontoSerieProjecao {
  const pj = r.brasil.projetado;
  return [min, pj?.p_f ?? null, pj?.faixa90[0] ?? null, pj?.faixa90[1] ?? null, r.brasil.observado.p_f, r.cobertura.pst];
}

export function projecao(ctx: Contexto, db: Database, p: Params): RespostaProjecao {
  const a = alvo(ctx, db, p, "federal");
  const ref = carregarReferenciaVotos();
  const cands = cacheCandsProj.obter([db.filename, a.ele, a.cargo].join("|"), maxSnapshotId(db), () => candidatosProjecao(db, a.ele, a.cargo));
  // estagio=0 desliga a comparação no mesmo estágio da contagem (diagnóstico: compara com o final do 1º turno).
  const mesmoEstagio = p.texto("estagio") !== "0";
  const calcular = (at: string | undefined): ResultadoProjecao => {
    const k = [db.filename, a.ele, a.cargo, at ?? "", mesmoEstagio ? 1 : 0].join("|");
    return cacheProj.obter(k, maxSnapshotId(db), () => {
      if (!ref || !cands) {
        const vazio = projetar({ ref: {}, obs: [] });
        return { ...vazio, motivo_sem_projecao: !ref ? "régua de votos do 1º turno ausente (data/referencia_1t_votos.json)" : "candidatos 13 e 22 ausentes no banco" };
      }
      return projetar({ ref: ref.municipios, obs: obsMunicipais(db, a.ele, a.cargo, Number(cands.f.sqcand), Number(cands.l.sqcand), at), mesmoEstagio });
    });
  };
  const res = calcular(a.at);
  const serie = serieDe(db, a.ele, a.cargo);
  const minAgora = minutosDe(a.rel.agoraMs, a.rel.t0Ms);
  let pontos: PontoSerieProjecao[];
  if (a.at === undefined && ref && cands && mesmoEstagio) {
    // Ao vivo: reconstrói a grade de 5 em 5 min que faltar (leituras "até o instante") e acrescenta o ponto de agora.
    for (const m of serie.faltantes(minAgora).slice(0, RECONSTRUIR_POR_CHAMADA)) {
      serie.acrescentar(pontoDe(m, calcular(isoDe(a.rel.t0Ms + m * 60_000))), true);
    }
    if (minAgora >= 0) serie.acrescentar(pontoDe(minAgora, res));
    pontos = serie.lista().filter((q) => q[0] <= minAgora);
  } else {
    pontos = serie.lista().filter((q) => q[0] <= minAgora);
  }
  return {
    at: isoDe(a.rel.agoraMs),
    min: minAgora,
    ele: a.ele,
    cargo: a.cargo,
    rotulo: ROTULO_PROJECAO,
    candidatos: cands,
    ...res,
    serie: pontos,
  };
}
