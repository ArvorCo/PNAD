// Configuração de seções por UF (`{uf}-p00{pleito}-cs.json`): abr[].mu[].zon[].sec[] com `ns`
// (seção), `nsp` (principal, quando a seção é agregada a outra) e `nsa` (agregadas a esta).
// A seção agregada não tem BU próprio: fica fora do quadro da amostra.
import { z } from "zod";
import type { SecaoChave } from "./urls.ts";

const SecSchema = z.object({ ns: z.string(), nsp: z.string().optional(), nsa: z.array(z.string()).optional() }).passthrough();
const ZonSchema = z.object({ cd: z.string(), sec: z.array(SecSchema) }).passthrough();
const MuSchema = z.object({ cd: z.string(), nm: z.string().optional(), zon: z.array(ZonSchema) }).passthrough();
export const CsSchema = z
  .object({
    dg: z.string().optional(),
    hg: z.string().optional(),
    idg: z.string().optional(),
    abr: z.array(z.object({ cd: z.string(), mu: z.array(MuSchema) }).passthrough()),
  })
  .passthrough();
export type Cs = z.infer<typeof CsSchema>;

export interface QuadroUf {
  secoes: SecaoChave[];
  /** código TSE → nome do município */
  nomes: Map<string, string>;
  agregadas: number;
}

/** Seções com BU próprio, em ordem de município, zona e seção. */
export function quadroDoCs(cs: Cs): QuadroUf {
  const secoes: SecaoChave[] = [];
  const nomes = new Map<string, string>();
  let agregadas = 0;
  for (const a of cs.abr) {
    const uf = a.cd.toLowerCase();
    for (const m of a.mu) {
      const mun = m.cd.padStart(5, "0");
      if (m.nm !== undefined) nomes.set(mun, m.nm);
      for (const zn of m.zon) {
        const zona = Number.parseInt(zn.cd, 10);
        for (const s of zn.sec) {
          if (s.nsp !== undefined && s.nsp !== s.ns) {
            agregadas += 1;
            continue;
          }
          secoes.push({ uf, mun, zona, secao: Number.parseInt(s.ns, 10) });
        }
      }
    }
  }
  secoes.sort((x, y) => (x.mun < y.mun ? -1 : x.mun > y.mun ? 1 : x.zona - y.zona || x.secao - y.secao));
  return { secoes, nomes, agregadas };
}

export function lerCs(bytes: Uint8Array): Cs {
  return CsSchema.parse(JSON.parse(new TextDecoder().decode(bytes)));
}
