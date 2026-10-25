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

// ---------------------------------------------------------------- /api/2t/comparecimento
const NumN = z.number().nullable();
const Dist = z.object({ n: z.number().int().nonnegative(), p50: NumN, p90: NumN }).strict();
const Contagem = {
  delta: z.number().int().nonnegative(),
  sem_bio: z.number().int().nonnegative(),
  tarde: z.number().int().nonnegative(),
  apos_19h: z.number().int().nonnegative(),
  papel: z.number().int().nonnegative(),
  contingencia: z.number().int().nonnegative(),
  escore_2_mais: z.number().int().nonnegative(),
};
const Hhmm = z.string().regex(/^\d{2}:\d{2}$/);
export const SecaoComparecimentoSchema = z
  .object({
    uf: Uf, mun: z.string().regex(/^\d{5}$/), nm: z.string(), zona: z.number().int(), secao: z.number().int(), lat: NumN, lon: NumN,
    aptos: z.number().int().nullable(), comp: z.number().int().nullable(), taxa_comp: NumN, taxa_comp_1t: NumN, delta_pp: NumN,
    sem_bio_pct: NumN, sem_bio_pct_1t: NumN, sem_bio_mun_p50_1t: NumN, ano_nasc_pct: NumN, encerramento_hhmm: Hhmm.nullable(),
    encerrou_apos_17h: z.boolean(), apos_19h: z.boolean(), papel: z.boolean(), tipo_arquivo: z.number().int().nullable(),
    tipo_urna: z.number().int().nullable(), n_cargas: z.number().int().nullable(), contingencia: z.boolean(), fatia_flavio: Pct.nullable(),
    fatia_flavio_1t: Pct.nullable(), recebido_hhmm: Hhmm.nullable(), origem: z.enum(["amostra", "paralela"]),
    sinais: z.object({ delta: z.boolean(), sem_bio: z.boolean(), tarde: z.boolean(), papel: z.boolean() }).strict(),
    escore: z.number().int().min(0).max(4),
  })
  .strict();
const MunicipioComparecimentoSchema = z
  .object({
    uf: Uf, cd: z.string().regex(/^\d{5}$/), nm: z.string(), lat: NumN, lon: NumN, te: z.number().int().nonnegative(), pst: Pct, taxa_2t: Pct,
    taxa_1t: Pct, delta_pp: z.number(),
  })
  .strict();
const BlocoProrrogacaoSchema = z
  .object({
    uf: z.string(), n_tardias: z.number().int().nonnegative(), n_apos_19h: z.number().int().nonnegative(), n_pontuais: z.number().int().nonnegative(),
    delta_comp_tardias: NumN, delta_comp_pontuais: NumN, n_vs_1t: z.number().int().nonnegative(), delta_fatia_vs_1t_pp: NumN,
    n_vs_pontuais: z.number().int().nonnegative(), delta_fatia_vs_pontuais_pp: NumN,
  })
  .strict();
export const ComparecimentoSchema = z
  .object({
    at: Iso,
    min: NumN,
    rotulo: z.string().min(20),
    regras: z
      .object({
        delta_pp_min: z.number(), sem_bio_fator: z.number(), sem_bio_min_pct: z.number(), tarde_hhmm: Hhmm, apos_hhmm: Hhmm, papel_tipo_min: z.number(),
        mun_pst_min: z.number(),
      })
      .strict(),
    referencia: z
      .object({
        secoes: z.boolean(), gerado_em: z.string().nullable(), municipios: z.boolean(),
        enc_1t_pct: z.object({ apos_1700: Pct.nullable(), apos_1800: Pct.nullable(), apos_1900: Pct.nullable() }).strict(),
      })
      .strict(),
    totais: z
      .object({
        recebidas: z.number().int().nonnegative(), com_ref_1t: z.number().int().nonnegative(), com_coord: z.number().int().nonnegative(),
        amostra: z.number().int().nonnegative(), paralela: z.number().int().nonnegative(),
      })
      .strict(),
    sinais: z.object(Contagem).strict(),
    delta: Dist,
    por_uf: z.array(z.object({ uf: Uf, recebidas: z.number().int().nonnegative(), ...Contagem, delta_dist: Dist }).strict()),
    pontos: z.array(z.tuple([z.number(), z.number(), NumN, z.number().int(), z.number().int(), z.union([z.literal(0), z.literal(1)])])),
    top: z.array(SecaoComparecimentoSchema).max(30),
    contingencia: z.array(SecaoComparecimentoSchema).max(50),
    prorrogacao: z.object({ n_min: z.number().int().positive(), brasil: BlocoProrrogacaoSchema, por_uf: z.array(BlocoProrrogacaoSchema) }).strict(),
    municipios: z.array(MunicipioComparecimentoSchema),
    municipios_uf: z.array(z.object({ uf: Uf, n: z.number().int().nonnegative(), delta: Dist }).strict()),
    municipios_delta: Dist,
    municipios_top: z.array(MunicipioComparecimentoSchema).max(30),
  })
  .strict();
