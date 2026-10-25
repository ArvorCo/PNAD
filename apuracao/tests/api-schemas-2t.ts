// Esquemas zod estritos das rotas de indicadores do 2º turno (/api/2t/regioes, ufs, abstencao,
// estaduais, evolucao) e dos acréscimos do /api/config no 2º turno. Documentam o contrato de
// analysis/apuracao_2t_2026/CONTRATO.md para o telão e para a página pública.
import { z } from "zod";
import { Campo, ConfigSchema, Iso } from "./api-schemas.ts";

const Sq = z.string().regex(/^\d+$/);
const Pct = z.number().min(0).max(100);
const Uf = z.string().regex(/^[A-Z]{2}$/);
const Regiao = z.enum(["N", "NE", "CO", "SE", "S", "ZZ"]);
const Votos = z.record(Sq, z.object({ vap: z.number().int().nonnegative(), pvapn: Pct }).strict());

const Totais = {
  ts: z.number().int().nonnegative(),
  st: z.number().int().nonnegative(),
  snt: z.number().int().nonnegative(),
  pst: Pct,
  te: z.number().int().nonnegative(),
  est: z.number().int().nonnegative(),
  comparecimento: z.number().int().nonnegative(),
  abstencao: z.number().int().nonnegative(),
  pa: Pct,
};

const Ritmo = { vel_10min_spm: z.number().nonnegative(), eta_100_iso: Iso.nullable() };

export const AgregadoSchema = z
  .object({
    sigla: z.union([Regiao, z.literal("BR")]),
    nome: z.string(),
    ufs: z.array(Uf),
    ...Totais,
    votos: Votos,
    vv: z.number().int().nonnegative(),
    vb: z.number().int().nonnegative(),
    vn: z.number().int().nonnegative(),
    tv: z.number().int().nonnegative(),
    lider: Sq.nullable(),
    margem_pp: z.number().nonnegative(),
    ...Ritmo,
    ref_1t: z.object({ pst_mesmo_relogio: Pct.nullable(), atraso_min: z.number().nullable(), pa_final_1t: Pct.nullable() }).strict().nullable(),
    atualizado_em: Iso.nullable(),
  })
  .strict();

export const RegioesSchema = z
  .object({
    at: Iso,
    min: z.number(),
    ele: z.number().int(),
    cargo: z.number().int(),
    turno: z.number().int(),
    referencia_1t: z.boolean(),
    brasil: AgregadoSchema,
    regioes: z.array(AgregadoSchema).length(6),
  })
  .strict();

export const UfLinhaSchema = z
  .object({
    uf: Uf,
    nome: z.string(),
    regiao: Regiao,
    ...Totais,
    munnr: z.number().int().nonnegative(),
    munpt: z.number().int().nonnegative(),
    munf: z.number().int().nonnegative(),
    votos: Votos,
    lider: Sq.nullable(),
    margem_pp: z.number().nonnegative(),
    ultima_versao_em: Iso.nullable(),
    idade_s: z.number().nullable(),
    ...Ritmo,
    parada: z.boolean(),
    ref_1t: z
      .object({
        pst_mesmo_relogio: Pct.nullable(),
        atraso_min: z.number().nullable(),
        p50_min: z.number().nullable(),
        p90_min: z.number().nullable(),
        p99_min: z.number().nullable(),
        p100_min: z.number().nullable(),
        pa_final: Pct.nullable(),
      })
      .strict()
      .nullable(),
    pendentes_maiores: z.array(z.object({ cd: z.string().regex(/^\d{5}$/), nm: z.string(), te: z.number().int().nonnegative(), pst: Pct }).strict()).max(3),
  })
  .strict();

export const UfsSchema = z
  .object({
    at: Iso,
    min: z.number(),
    ele: z.number().int(),
    cargo: z.number().int(),
    limiar_parada_min: z.number().int().positive(),
    ufs: z.array(UfLinhaSchema).length(28),
  })
  .strict();

const BlocoBase = {
  nome: z.string(),
  n_mun: z.number().int().nonnegative(),
  n_mun_fechados: z.number().int().nonnegative(),
  te_fechado: z.number().int().nonnegative(),
  pct_te_fechado: Pct,
  comparecimento: z.number().int().nonnegative(),
  abstencao: z.number().int().nonnegative(),
  pa_2t: Pct.nullable(),
  pa_1t_mesmos: Pct.nullable(),
  delta_pp: z.number().nullable(),
};

const Mun = z
  .object({
    uf: Uf,
    cd: z.string().regex(/^\d{5}$/),
    nm: z.string(),
    te: z.number().int().nonnegative(),
    pa_2t: Pct,
    pa_1t: Pct,
    delta_pp: z.number(),
    fechou_min: z.number().nullable(),
  })
  .strict();

export const AbstencaoSchema = z
  .object({
    at: Iso,
    min: z.number(),
    ele: z.number().int(),
    cargo: z.number().int(),
    base: z.literal("municipios_fechados"),
    brasil: z.object({ sigla: z.literal("BR"), ...BlocoBase }).strict(),
    regioes: z.array(z.object({ sigla: Regiao, ...BlocoBase }).strict()).length(6),
    ufs: z.array(z.object({ uf: Uf, ...BlocoBase, pa_corrente: Pct.nullable(), pa_final_1t: Pct.nullable() }).strict()).length(28),
    destaques: z.object({ subiu: z.array(Mun).max(20), caiu: z.array(Mun).max(20) }).strict(),
  })
  .strict();

export const EstadualSchema = z
  .object({
    uf: z.enum(["AC", "AM", "DF", "ES", "RN", "TO"]),
    nome: z.string(),
    ts: z.number().int().nonnegative(),
    st: z.number().int().nonnegative(),
    pst: Pct,
    te: z.number().int().nonnegative(),
    comparecimento: z.number().int().nonnegative(),
    abstencao: z.number().int().nonnegative(),
    pa: Pct,
    munnr: z.number().int().nonnegative(),
    munpt: z.number().int().nonnegative(),
    munf: z.number().int().nonnegative(),
    cand: z.array(
      z.object({ sqcand: Sq, n: z.string(), nome_urna: z.string(), partido: z.string(), vap: z.number().int().nonnegative(), pvapn: Pct, campo: Campo }).strict(),
    ),
    lider: Sq.nullable(),
    margem_pp: z.number().nonnegative(),
    viradas: z.array(z.object({ at: Iso, de: Sq, para: Sq }).strict()),
    ultima_versao_em: Iso.nullable(),
    idade_s: z.number().nullable(),
    ref_1t: z.object({ pst_mesmo_relogio: Pct.nullable(), atraso_min: z.number().nullable() }).strict().nullable(),
    pa_final_1t: Pct.nullable(),
  })
  .strict();

export const EstaduaisSchema = z
  .object({ at: Iso, min: z.number(), ele: z.number().int(), cargo: z.number().int(), ufs: z.array(EstadualSchema).length(6) })
  .strict();

const PontoEvolucao = z.tuple([z.number(), Pct, Pct, Pct, z.number().int().nonnegative()]);

export const EvolucaoSchema = z
  .object({
    at: Iso,
    ele: z.number().int(),
    cargo: z.number().int(),
    passo_s: z.number().int().min(30),
    candidatos: z.array(z.object({ sqcand: Sq, n: z.string(), nome_urna: z.string() }).strict()).max(2),
    series: z.record(z.string(), z.array(PontoEvolucao)),
    referencia_1t: z.record(z.string(), z.array(z.tuple([z.number(), Pct]))).nullable(),
  })
  .strict();

/** /api/config no 2º turno: o contrato do 1º turno mais as UFs com governador e o mapa de regiões. */
export const Config2tSchema = ConfigSchema.extend({
  ufs_governador_2t: z.array(Uf),
  regioes: z.record(Regiao, z.array(Uf)),
}).strict();

// ---------------------------------------------------------------- /api/2t/projecao

const PctOuNulo = Pct.nullable();

const ProjetadoSchema = z
  .object({
    f: z.number().int().nonnegative(),
    l: z.number().int().nonnegative(),
    p_f: Pct,
    p_l: Pct,
    p_f_validos: Pct,
    p_l_validos: Pct,
    faixa90: z.tuple([Pct, Pct]),
  })
  .strict()
  .refine((p) => p.faixa90[0] <= p.p_f && p.p_f <= p.faixa90[1], { message: "faixa de 90% não contém a projeção" });

export const BlocoProjecaoSchema = z
  .object({
    sigla: z.union([Regiao, Uf, z.literal("BR")]),
    nome: z.string(),
    pst: Pct,
    pct_vv_observado: Pct,
    p1_f: PctOuNulo,
    observado: z.object({ f: z.number().int().nonnegative(), l: z.number().int().nonnegative(), p_f: PctOuNulo }).strict(),
    projetado: ProjetadoSchema.nullable(),
    swing_pp: z.number().min(-100).max(100).nullable(),
  })
  .strict();

const CandProjecao = z.object({ sqcand: Sq, n: z.string(), nome_urna: z.string() }).strict();

export const ProjecaoSchema = z
  .object({
    at: Iso,
    min: z.number(),
    ele: z.number().int(),
    cargo: z.number().int(),
    rotulo: z.literal("projeção estatística a partir do que já foi totalizado; não é resultado nem previsão de vitória"),
    candidatos: z.object({ f: CandProjecao, l: CandProjecao }).strict().nullable(),
    cobertura: z
      .object({
        pst: Pct,
        st: z.number().int().nonnegative(),
        ts: z.number().int().nonnegative(),
        pct_vv_observado: Pct,
        municipios_observados: z.number().int().nonnegative(),
        municipios_fechados: z.number().int().nonnegative(),
        municipios_total: z.number().int().nonnegative(),
      })
      .strict(),
    brasil: BlocoProjecaoSchema,
    regioes: z.array(BlocoProjecaoSchema).length(6),
    ufs: z.array(BlocoProjecaoSchema).length(28),
    parametros: z
      .object({
        K: z.number().positive(),
        K_uf: z.number().positive(),
        mesmo_estagio: z.boolean(),
        erro_comum_pp: z.number().nonnegative(),
        reps: z.number().int().nonnegative(),
        nivel_faixa: z.literal(90),
        minimo_pst: z.number().nonnegative(),
        metodo: z.string().min(20),
      })
      .strict(),
    motivo_sem_projecao: z.string().nullable(),
    serie: z.array(z.tuple([z.number(), PctOuNulo, PctOuNulo, PctOuNulo, PctOuNulo, Pct])),
  })
  .strict();
