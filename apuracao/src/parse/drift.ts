// Gêmeos estritos dos esquemas: servem só para listar caminhos desconhecidos ou
// com tipo inesperado. A coleta usa sempre o esquema leniente.
import { z } from "zod";
import type { Tipo } from "../types.ts";
import { SCHEMAS } from "./schemas.ts";

/** Converte recursivamente objetos passthrough em strict. */
export function estrito(schema: z.ZodTypeAny): z.ZodTypeAny {
  if (schema instanceof z.ZodObject) {
    const shape = schema.shape as Record<string, z.ZodTypeAny>;
    const novo: Record<string, z.ZodTypeAny> = {};
    for (const [k, v] of Object.entries(shape)) novo[k] = estrito(v);
    return z.object(novo).strict();
  }
  if (schema instanceof z.ZodArray) return z.array(estrito(schema.element as z.ZodTypeAny));
  if (schema instanceof z.ZodOptional) return estrito(schema.unwrap() as z.ZodTypeAny).optional();
  if (schema instanceof z.ZodNullable) return estrito(schema.unwrap() as z.ZodTypeAny).nullable();
  // ZodEffects (preprocess) e primitivos: no modo estrito exige o tipo de dentro sem coerção
  if (schema instanceof z.ZodEffects) return estrito(schema.innerType() as z.ZodTypeAny);
  return schema;
}

const cache = new Map<Tipo, z.ZodTypeAny>();

export function esquemaEstrito(tipo: Tipo): z.ZodTypeAny {
  let s = cache.get(tipo);
  if (!s) {
    s = estrito(SCHEMAS[tipo]);
    cache.set(tipo, s);
  }
  return s;
}

export interface Drift {
  /** caminhos com chave não prevista, índices de array normalizados para [] */
  desconhecidos: string[];
  /** caminhos obrigatórios ausentes ou com tipo diferente do previsto */
  divergentes: string[];
}

function caminho(path: ReadonlyArray<string | number>): string {
  let out = "$";
  for (const p of path) out += typeof p === "number" ? "[]" : `.${p}`;
  return out;
}

/** Lista o drift de um JSON contra o gêmeo estrito do tipo. Vazio = formato conhecido. */
export function detectarDrift(tipo: Tipo, json: unknown): Drift {
  const r = esquemaEstrito(tipo).safeParse(json);
  const desconhecidos = new Set<string>();
  const divergentes = new Set<string>();
  if (!r.success) {
    for (const issue of r.error.issues) {
      if (issue.code === "unrecognized_keys") {
        for (const k of issue.keys) desconhecidos.add(`${caminho(issue.path)}.${k}`);
      } else {
        divergentes.add(caminho(issue.path));
      }
    }
  }
  return { desconhecidos: [...desconhecidos].sort(), divergentes: [...divergentes].sort() };
}
