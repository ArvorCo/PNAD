// Esquemas zod lenientes dos arquivos do TSE: todo campo folha é string opcional,
// campos desconhecidos passam (passthrough). O gêmeo estrito fica em drift.ts.
import { z } from "zod";
import type { Tipo } from "../types.ts";

/** String opcional; número vira string para tolerar mudança de formato. */
export const str = z.preprocess((v) => (typeof v === "number" ? String(v) : v), z.string()).optional();

type Campos<K extends string> = { [P in K]: typeof str };

function campos<const K extends string>(nomes: readonly K[]): Campos<K> {
  const shape = {} as Campos<K>;
  for (const n of nomes) shape[n] = str;
  return shape;
}

export const SecoesSchema = z
  .object(
    campos([
      "ts", "st", "pst", "pstn", "snt", "psnt", "psntn", "si", "psi", "psin",
      "sni", "psni", "psnin", "sa", "psa", "psan", "sna", "psna", "psnan",
    ]),
  )
  .passthrough();

export const EleitoradoSchema = z
  .object(
    campos([
      "te", "est", "pest", "pestn", "esnt", "pesnt", "pesntn", "esi", "pesi", "pesin",
      "esni", "pesni", "pesnin", "esa", "pesa", "pesan", "esna", "pesna", "pesnan",
      "c", "pc", "pcn", "a", "pa", "pan",
    ]),
  )
  .passthrough();

export const VotosSchema = z
  .object(
    campos([
      "tv", "vvc", "pvvc", "pvvcn", "vv", "pvv", "pvvn", "vnom", "pvnom", "pvnomn",
      "vl", "pvl", "pvln", "van", "pvan", "pvann", "vansj", "pvansj", "pvansjn",
      "vb", "pvb", "pvbn", "tvn", "ptvn", "ptvnn", "vn", "pvn", "pvnn", "vnt", "pvnt", "pvntn",
      "vsan", "vscv",
    ]),
  )
  .passthrough();

const cabecalho = campos(["dg", "hg", "idg", "f"]);

// ---- ele-c.json ----
export const EleCSchema = z
  .object({
    ...cabecalho,
    arq: z.array(z.object(campos(["tp", "dir"])).passthrough()).optional(),
    pl: z.array(
      z
        .object({
          ...campos(["cd", "cdpr", "c", "dt", "dtlim"]),
          e: z
            .array(
              z
                .object({
                  ...campos(["cd", "cdt2", "sqele", "nm", "t", "tp"]),
                  abr: z
                    .array(
                      z
                        .object({
                          ...campos(["cd"]),
                          cp: z.array(z.object(campos(["cd", "ds", "tp"])).passthrough()).optional(),
                          mu: z.array(z.object(campos(["cd", "cdi"])).passthrough()).optional(),
                        })
                        .passthrough(),
                    )
                    .optional(),
                })
                .passthrough(),
            )
            .optional(),
        })
        .passthrough(),
    ),
  })
  .passthrough();

// ---- mun-e00XXXX-cm.json ----
export const MunCmSchema = z
  .object({
    ...cabecalho,
    abr: z.array(
      z
        .object({
          cd: z.string(),
          ds: str,
          mu: z.array(
            z
              .object({ cd: z.string(), ...campos(["cdi", "nm", "c"]), z: z.array(z.string()) })
              .passthrough(),
          ),
        })
        .passthrough(),
    ),
  })
  .passthrough();

// ---- -ab.json ----
export const AbEntradaSchema = z
  .object({
    ...campos([
      "and", "tpabr", "cdabr", "dt", "ht",
      "munnr", "pmunnr", "pmunnrn", "munpt", "pmunpt", "pmunptn", "munf", "pmunf", "pmunfn",
      "ufsnr", "pufsnr", "pufsnrn", "ufspt", "pufspt", "pufsptn", "ufsf", "pufsf", "pufsfn",
    ]),
    s: SecoesSchema.optional(),
    e: EleitoradoSchema.optional(),
  })
  .passthrough();

export const AbFileSchema = z
  .object({ ...campos(["ele", "t"]), ...cabecalho, abr: z.array(AbEntradaSchema) })
  .passthrough();

// ---- -u.json ----
export const ViceSchema = z.object(campos(["tp", "sqcand", "nm", "nmu", "sgp"])).passthrough();

export const CandidatoSchema = z
  .object({
    ...campos(["n", "sqcand", "nm", "nmu", "dt", "dvt", "seq", "e", "st", "vap", "pvap", "pvapn"]),
    vs: z.array(ViceSchema).optional(),
  })
  .passthrough();

export const PartidoSchema = z
  .object({
    ...campos(["n", "sg", "nm", "nfed", "dvt", "tvtn", "tvtl", "tval", "tvan"]),
    cand: z.array(CandidatoSchema).optional(),
  })
  .passthrough();

export const AgremiacaoSchema = z
  .object({
    ...campos(["n", "nm", "tp", "com", "vag", "tvtn", "tvtl", "tval", "tvan"]),
    par: z.array(PartidoSchema).optional(),
  })
  .passthrough();

export const FederacaoSchema = z
  .object({ ...campos(["n", "sg", "nm", "com"]), npar: z.array(z.string()).optional() })
  .passthrough();

export const CargoSchema = z
  .object({
    ...campos(["cd", "nmn", "nmm", "nmf", "nv", "qe"]),
    fed: z.array(FederacaoSchema).optional(),
    agr: z.array(AgremiacaoSchema).optional(),
  })
  .passthrough();

export const ResultadoUSchema = z
  .object({
    ...campos(["ele", "t", "sup", "tpabr", "cdabr", "dt", "ht", "dv", "tf", "and", "esae"]),
    ...cabecalho,
    mnae: z.array(z.unknown()).optional(),
    carg: z.array(CargoSchema),
    s: SecoesSchema.optional(),
    e: EleitoradoSchema.optional(),
    v: VotosSchema.optional(),
  })
  .passthrough();

// ---- -e.json (formato de 2024) ----
export const ECandidatoSchema = z
  .object({
    ...campos(["n", "sqcand", "nm", "nmu", "sgp", "com", "vap", "seq"]),
    vs: z.array(ViceSchema).optional(),
  })
  .passthrough();

export const EEntradaSchema = z
  .object({
    ...campos(["dt", "ht", "tpabr", "cdabr", "nmabr", "tvap", "scv", "esae"]),
    mnae: z.array(z.unknown()).optional(),
    cand: z.array(ECandidatoSchema).optional(),
  })
  .passthrough();

export const EFileSchema = z
  .object({
    ...campos(["ele", "cdabr", "nmabr", "t", "cdcar", "nmcar"]),
    ...cabecalho,
    abr: z.array(EEntradaSchema),
  })
  .passthrough();

export type EleC = z.infer<typeof EleCSchema>;
export type MunCm = z.infer<typeof MunCmSchema>;
export type AbFile = z.infer<typeof AbFileSchema>;
export type AbEntrada = z.infer<typeof AbEntradaSchema>;
export type ResultadoU = z.infer<typeof ResultadoUSchema>;
export type EFile = z.infer<typeof EFileSchema>;

export type ParsedFile =
  | { tipo: "ele-c"; data: EleC }
  | { tipo: "cm"; data: MunCm }
  | { tipo: "ab"; data: AbFile }
  | { tipo: "u"; data: ResultadoU }
  | { tipo: "e"; data: EFile };

export const SCHEMAS = {
  "ele-c": EleCSchema,
  cm: MunCmSchema,
  ab: AbFileSchema,
  u: ResultadoUSchema,
  e: EFileSchema,
} as const satisfies Record<Tipo, z.ZodTypeAny>;

export type ResultadoParse = { ok: true; parsed: ParsedFile; json: unknown } | { ok: false; erro: string; json?: unknown };

/** true se o corpo começa (após espaços) com { ou [. XML/HTML de erro do CDN dá false. */
export function pareceJson(corpo: Uint8Array | string): boolean {
  const s = typeof corpo === "string" ? corpo : new TextDecoder().decode(corpo.subarray(0, 64));
  const c = s.trimStart()[0];
  return c === "{" || c === "[";
}

/** Valida um JSON já decodificado contra o esquema do tipo. */
export function parseJson(tipo: Tipo, json: unknown): ResultadoParse {
  const r = SCHEMAS[tipo].safeParse(json);
  if (!r.success) return { ok: false, erro: r.error.issues.slice(0, 5).map((i) => `${i.path.join(".")}: ${i.message}`).join("; "), json };
  return { ok: true, parsed: { tipo, data: r.data } as ParsedFile, json };
}

/** Decodifica e valida o corpo bruto. */
export function parseCorpo(tipo: Tipo, corpo: Uint8Array | string): ResultadoParse {
  if (!pareceJson(corpo)) return { ok: false, erro: "corpo não é JSON" };
  let json: unknown;
  try {
    json = JSON.parse(typeof corpo === "string" ? corpo : new TextDecoder().decode(corpo));
  } catch (err) {
    return { ok: false, erro: `JSON inválido: ${err instanceof Error ? err.message : String(err)}` };
  }
  return parseJson(tipo, json);
}
