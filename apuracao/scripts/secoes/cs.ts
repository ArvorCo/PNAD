// Configuração de seções por UF (`{uf}-p003220-cs.json`): abr[].mu[].zon[].sec[] com
// `ns` (seção), `nsp` (principal, quando a seção é agregada) e `nsa` (agregadas a esta).
import { z } from "zod";
import type { SecaoCs } from "./banco.ts";

const SecSchema = z
  .object({ ns: z.string(), nsp: z.string().optional(), nsa: z.array(z.string()).optional() })
  .passthrough();
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

/** Seções do arquivo, em ordem de município, zona e seção. */
export function secoesDoCs(cs: Cs): SecaoCs[] {
  const out: SecaoCs[] = [];
  for (const a of cs.abr) {
    const uf = a.cd.toLowerCase();
    for (const m of a.mu) {
      for (const z of m.zon) {
        for (const s of z.sec) {
          out.push({
            uf,
            mun: m.cd.padStart(5, "0"),
            zona: Number.parseInt(z.cd, 10),
            secao: Number.parseInt(s.ns, 10),
            nsp: s.nsp === undefined ? null : Number.parseInt(s.nsp, 10),
            nsa: s.nsa === undefined ? null : JSON.stringify(s.nsa.map((x) => Number.parseInt(x, 10))),
          });
        }
      }
    }
  }
  out.sort((x, y) => (x.mun < y.mun ? -1 : x.mun > y.mun ? 1 : x.zona - y.zona || x.secao - y.secao));
  return out;
}
