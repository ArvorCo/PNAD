// Viradas de liderança e fechamento de UF gravados pelo coletor, na mesma passagem da versão
// nova do -u. O servidor só deriva das séries quando não há linha gravada para o snapshot.
import type { EventoNovo, IdRef } from "../db/escrita.ts";
import { titulo } from "../server/abr.ts";
import { corrigirTotalizadoEm } from "../turno2/comum.ts";
import type { FileKey } from "../types.ts";
import type { CandResumo, TotaisResumo } from "./estado-arquivos.ts";

const FEDERAIS: ReadonlySet<number> = new Set([6257, 6258]);
const ESTADUAIS: ReadonlySet<number> = new Set([6259, 6260]);

/** Líder por votos apurados: maior vap positivo e único (empate não tem líder). */
export function liderDe(c: ReadonlyMap<number, CandResumo>): { sq: number; vap: number } | null {
  let melhor: { sq: number; vap: number } | null = null;
  let empate = false;
  for (const [sq, x] of c) {
    const v = x.vap ?? 0;
    if (v <= 0) continue;
    if (melhor === null || v > melhor.vap) {
      melhor = { sq, vap: v };
      empate = false;
    } else if (v === melhor.vap) {
      empate = true;
    }
  }
  return empate ? null : melhor;
}

/** Arquivo que acompanha viradas: presidente br/UF e governador por UF. */
export function acompanhaVirada(k: FileKey): boolean {
  if (k.tipo !== "u" || k.ele === null) return false;
  if (FEDERAIS.has(k.ele) && k.cargo === 1) return k.nivel === "br" || k.nivel === "uf";
  return ESTADUAIS.has(k.ele) && k.cargo === 3 && k.nivel === "uf";
}

export interface CtxApuracao {
  em: string;
  arquivoId: number;
  snapshot: IdRef;
  key: FileKey;
  geradoEm: string | null;
  totalizadoEm: string | null;
  /** sqcand → nome de urna (da própria versão) */
  nomes: ReadonlyMap<number, string | null>;
}

export function eventosApuracao(
  antT: TotaisResumo | null,
  novoT: TotaisResumo,
  antC: ReadonlyMap<number, CandResumo> | null,
  novoC: ReadonlyMap<number, CandResumo> | null,
  c: CtxApuracao,
): EventoNovo[] {
  const k = c.key;
  const out: EventoNovo[] = [];
  const base = (tipo: string, severidade: "info" | "warn", detalhe: unknown): EventoNovo => ({
    em: c.em, tipo, severidade, arquivo_id: c.arquivoId, snapshot_id: c.snapshot, eleicao_cd: k.ele, cargo_cd: k.cargo, nivel: k.nivel,
    uf: k.uf, municipio_cd: null, zona_cd: null, detalhe,
  });
  if (acompanhaVirada(k) && antC !== null && novoC !== null) {
    const de = liderDe(antC);
    const para = liderDe(novoC);
    if (de !== null && para !== null && de.sq !== para.sq) {
      const nome = (sq: number): string => titulo(c.nomes.get(sq) ?? null) || String(sq);
      out.push(
        base("virada", "warn", {
          de: String(de.sq), para: String(para.sq), de_nome: nome(de.sq), para_nome: nome(para.sq),
          vap_de: novoC.get(de.sq)?.vap ?? null, vap_para: para.vap, pst: novoT.pst,
        }),
      );
    }
  }
  const fechadoNovo = novoT.ts !== null && novoT.ts > 0 && novoT.st === novoT.ts;
  const fechadoAnt = antT !== null && antT.ts !== null && antT.ts > 0 && antT.st === antT.ts;
  if (k.tipo === "u" && k.ele !== null && FEDERAIS.has(k.ele) && k.cargo === 1 && k.nivel === "uf" && k.uf !== null && fechadoNovo && !fechadoAnt) {
    out.push(
      base("uf_fechou", "info", {
        totalizado_em: corrigirTotalizadoEm(k.uf, c.totalizadoEm, c.geradoEm), gerado_em: c.geradoEm, st: novoT.st, ts: novoT.ts,
      }),
    );
  }
  return out;
}
