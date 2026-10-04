// Esquemas zod estritos das respostas da API: documentam o contrato do servidor para o telão.
import { z } from "zod";

export const Iso = z.string().regex(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/);
export const Campo = z.enum(["esquerda", "centro-esquerda", "centro", "centro-direita", "direita", "indefinido"]);

export const Fonte = z.enum(["tse", "soma_ufs"]);
const NacionalTse = z.object({ hg: Iso.nullable(), st: z.number(), pst: z.number() }).strict();

export const ConfigSchema = z
  .object({
    turno: z.number().int(),
    eleicoes: z.object({ federal: z.number().int(), estadual: z.number().int() }).strict(),
    ufs: z.array(z.object({ uf: z.string().regex(/^[a-z]{2}$/), nome: z.string(), cdi: z.string().optional(), te: z.number() }).strict()),
    municipios: z.record(
      z.string().regex(/^[A-Z]{2}$/),
      z.array(
        z.object({ cd: z.string().regex(/^\d{5}$/), cdi: z.string(), nm: z.string(), c: z.boolean(), z: z.array(z.string()), te: z.number().optional() }).strict(),
      ),
    ),
  })
  .strict();

const UfEstado = z
  .object({
    uf: z.string(), nome: z.string(), pst: z.number(), st: z.number(), ts: z.number(), te: z.number().optional(), munnr: z.number(), munpt: z.number(), munf: z.number(),
    dt_ht: Iso.nullable(), fechou_em: Iso.optional(),
  })
  .strict();

export const EstadoSchema = z
  .object({
    agora: Iso,
    pronto: z.boolean(),
    turno: z.number(),
    coletor: z.unknown(),
    db: z.object({ snapshots: z.number(), fetches: z.number(), eventos_warn: z.number(), tamanho_mb: z.number() }).strict().nullable(),
    ultimo_snapshot: z.object({ id: z.number(), capturado_em: Iso }).strict().nullable(),
    br: z
      .object({
        ts: z.number(), st: z.number(), pst: z.number(), dt_ht: Iso.nullable(), hg: Iso.nullable(), lido_em: Iso, atraso_s: z.number().nullable(),
        ultima_leitura_em: Iso.nullable(), idade_s: z.number().nullable(), fonte: Fonte.optional(), nacional_tse: NacionalTse.optional(),
      })
      .strict()
      .nullable(),
    ufs: z.array(UfEstado),
    historico: z.array(z.object({ at: Iso, st: z.number(), pst: z.number() }).strict()),
    latencias: z.object({ leitura_menos_hg: z.array(z.number()), hg_menos_ht: z.array(z.number()) }).strict(),
  })
  .strict();

const Cand = z
  .object({
    sqcand: z.string(), n: z.string(), nm: z.string(), nmu: z.string(), sg: z.string(), campo: Campo, fed_sg: z.string().optional(),
    e: z.boolean(), st: z.string(), dvt: z.string(), vap: z.number(), pvapn: z.number(), d_vap: z.number().optional(),
    vs: z.array(z.object({ tp: z.string(), nmu: z.string(), sgp: z.string() }).strict()),
  })
  .strict();

export const ResultadoSchema = z
  .object({
    ele: z.number(),
    cargo: z.object({ cd: z.number(), nome: z.string(), nome_f: z.string(), nv: z.number() }).strict(),
    tpabr: z.enum(["br", "uf", "mu", "zona"]),
    abr: z.string(),
    nome_escopo: z.string(),
    dg_hg: Iso.nullable(),
    dt_ht: Iso.nullable(),
    lido_em: Iso,
    tf: z.boolean(),
    idg: z.number().nullable(),
    snapshot_id: z.number(),
    anterior_id: z.number().nullable(),
    s: z.object({ ts: z.number(), st: z.number(), pst: z.number() }).strict(),
    e: z.object({ te: z.number(), c: z.number(), a: z.number(), pc: z.number(), pa: z.number() }).strict(),
    v: z
      .object({
        tv: z.number(), vv: z.number(), vvc: z.number(), vnom: z.number(), van: z.number(), vb: z.number(), vn: z.number(),
        pvb: z.number(), pvn: z.number(), pvan: z.number(),
      })
      .strict(),
    cand: z.array(Cand),
    partidos: z.array(
      z.object({ sg: z.string(), campo: Campo, fed_sg: z.string().optional(), tvtn: z.number(), tvtl: z.number(), tvan: z.number(), n_cand: z.number() }).strict(),
    ),
    candidatos_normalizados: z.boolean(),
    blob_url: z.string(),
    fonte: Fonte.optional(),
    nacional_tse: NacionalTse.optional(),
    ufs_usadas: z.number().int().optional(),
  })
  .strict();

const CandMapa = z.object({ sqcand: z.string(), n: z.string(), nmu: z.string(), sg: z.string(), campo: Campo, vap: z.number(), pvapn: z.number() }).strict();

export const MapaSchema = z
  .object({
    nivel: z.string(),
    pai: z.string(),
    gerado_em: Iso,
    unidades: z.array(
      z
        .object({
          cd: z.string(), cdi: z.string().optional(), nm: z.string(), te: z.number().optional(), pst: z.number(), tf: z.boolean(),
          snapshot_id: z.number().nullable(), lider: CandMapa.optional(), segundo: CandMapa.optional(), margem: z.number().optional(),
          top: z.array(CandMapa).optional(),
        })
        .strict(),
    ),
  })
  .strict();

export const SerieSchema = z
  .object({
    abr: z.string(),
    pontos: z.array(z.object({ at: Iso, snapshot_id: z.number(), pst: z.number(), cand: z.record(z.number()) }).strict()),
    viradas: z.array(z.object({ at: Iso, snapshot_id: z.number(), de: z.string(), para: z.string() }).strict()),
    candidatos: z.array(z.object({ sqcand: z.string(), n: z.string(), nmu: z.string(), sg: z.string(), campo: Campo }).strict()),
    fonte: Fonte.optional(),
  })
  .strict();

export const LotesSchema = z
  .object({
    abr: z.string(),
    candidatos: z.array(z.object({ sqcand: z.string(), n: z.string(), nmu: z.string(), sg: z.string() }).strict()),
    lotes: z.array(
      z
        .object({
          snapshot_id: z.number().int(), at: Iso, capturado_em: Iso, st: z.number(), d_st: z.number(), pst: z.number(),
          vv: z.number(), d_vv: z.number(), tv: z.number(), d_tv: z.number(),
          cand: z.record(z.object({ vap: z.number(), d_vap: z.number() }).strict()),
        })
        .strict(),
    ),
    fonte: Fonte.optional(),
  })
  .strict();

export const AnomaliasSchema = z.array(
  z
    .object({
      id: z.number(), at: Iso, tipo: z.string(), categoria: z.enum(["virada", "regressao", "fechou", "atraso", "outro"]),
      severidade: z.enum(["info", "warn", "error"]), nivel: z.string().nullable(), uf: z.string().nullable(), municipio_cd: z.string().nullable(),
      zona_cd: z.string().nullable(), cargo_cd: z.number().nullable(), cargo: z.number().nullable(), abr: z.string(),
      snapshot_id: z.number().nullable(), texto: z.string().min(1), detalhe: z.unknown(), derivado: z.boolean(),
    })
    .strict(),
);
