// Conferência de um BU da totalização paralela (lido do QR impresso) contra o BU que o TSE
// publica para a mesma seção. Porte fiel de ../scripts/totalizacao-conferir-tse.py: mesmo
// esqueleto (eleição → cargo → contagens), mesmas situações e mesma regra de igualdade
// (ausente conta como zero). Igualdade comprova transmissão e soma da seção; não diz nada
// sobre o interior da urna.
import type { BuComparavel, CargoComparavel } from "../secoes2t/boletim.ts";

export type Situacao = "igual" | "divergente" | "tse_ainda_nao_publicou" | "erro" | "fora_do_oficial";
export const SITUACOES_FINAIS: ReadonlySet<Situacao> = new Set(["igual", "divergente", "fora_do_oficial"]);

/** Linha de v_bu_publico (só as colunas lidas). */
export interface BuPublico {
  id: number;
  recebido_em: string;
  uf: string;
  muni: number;
  zona: number;
  secao: number;
  fase: string | null;
  pleito: number | null;
  turno: number | null;
  orig: string | null;
  aptos: number | null;
  comparecimento: number | null;
  hash_final: string;
}

export interface CargoPublico {
  bu_id: number;
  idel: number;
  cargo: number;
  tipo: number | null;
  apta: number;
  nomi: number;
  legc: number;
  bran: number;
  nulo: number;
  totc: number;
}

export interface VotoPublico {
  bu_id: number;
  idel: number;
  cargo: number;
  partido: number | null;
  candidato: string;
  votos: number;
}

/** Cargo de um BU da paralela como guardado em paralela_bu.cargos_json. */
export interface CargoParalela {
  idel: number;
  cargo: number;
  apta: number;
  nomi: number;
  legc: number;
  bran: number;
  nulo: number;
  totc: number;
  /** candidato (número; "LEGP<partido>" para legenda) → votos */
  votos: Record<string, number>;
}

export function cargosDoBu(cargos: readonly CargoPublico[], votos: readonly VotoPublico[]): CargoParalela[] {
  const out = cargos.map((c) => ({ idel: c.idel, cargo: c.cargo, apta: c.apta, nomi: c.nomi, legc: c.legc, bran: c.bran, nulo: c.nulo, totc: c.totc, votos: {} as Record<string, number> }));
  for (const v of votos) {
    const c = out.find((x) => x.idel === v.idel && x.cargo === v.cargo);
    if (c) c.votos[v.candidato] = v.votos;
  }
  return out;
}

/** BU da paralela no mesmo esqueleto do BU oficial. */
export function qrComparavel(comparecimento: number | null, cargos: readonly CargoParalela[]): BuComparavel {
  const out: BuComparavel = { comparecimento, eleicoes: {} };
  for (const c of cargos) {
    const e = (out.eleicoes[String(c.idel)] ??= { aptos: null, cargos: {} });
    e.aptos ??= c.apta;
    const cargo: CargoComparavel = { nominais: {}, legenda: {}, branco: c.bran, nulo: c.nulo, comparecimento: c.totc };
    for (const [cand, n] of Object.entries(c.votos)) {
      if (cand.startsWith("LEGP")) cargo.legenda[cand.slice(4)] = n;
      else cargo.nominais[cand] = n;
    }
    e.cargos[String(c.cargo)] = cargo;
  }
  return out;
}

export interface Diferenca {
  campo: string;
  idel: number | null;
  cargo: number | null;
  chave: string | null;
  paralela: number | boolean | null;
  tse: number | boolean | null;
}

const chaves = (a: Record<string, unknown>, b: Record<string, unknown>): string[] =>
  [...new Set([...Object.keys(a), ...Object.keys(b)])].sort((x, y) => Number(x) - Number(y) || (x < y ? -1 : x > y ? 1 : 0));

/** Diferenças campo a campo; lista vazia = BU idêntico ao publicado. */
export function comparar(qr: BuComparavel, tse: BuComparavel): Diferenca[] {
  const dif: Diferenca[] = [];
  const reg = (campo: string, p: number | null | undefined, t: number | null | undefined, idel: number | null = null, cargo: number | null = null, chave: string | null = null): void => {
    if ((p ?? 0) !== (t ?? 0)) dif.push({ campo, idel, cargo, chave, paralela: p ?? null, tse: t ?? null });
  };
  reg("comparecimento", qr.comparecimento, tse.comparecimento);
  for (const k of chaves(qr.eleicoes, tse.eleicoes)) {
    const idel = Number(k);
    const eq = qr.eleicoes[k];
    const et = tse.eleicoes[k];
    if (eq === undefined || et === undefined) {
      dif.push({ campo: "eleicao_ausente", idel, cargo: null, chave: null, paralela: eq !== undefined, tse: et !== undefined });
      continue;
    }
    reg("aptos", eq.aptos, et.aptos, idel);
    for (const kc of chaves(eq.cargos, et.cargos)) {
      const cargo = Number(kc);
      const cq = eq.cargos[kc];
      const ct = et.cargos[kc];
      if (cq === undefined || ct === undefined) {
        dif.push({ campo: "cargo_ausente", idel, cargo, chave: null, paralela: cq !== undefined, tse: ct !== undefined });
        continue;
      }
      reg("branco", cq.branco, ct.branco, idel, cargo);
      reg("nulo", cq.nulo, ct.nulo, idel, cargo);
      reg("comparecimento_cargo", cq.comparecimento, ct.comparecimento, idel, cargo);
      for (const n of chaves(cq.nominais, ct.nominais)) reg("nominal", cq.nominais[n], ct.nominais[n], idel, cargo, n);
      for (const p of chaves(cq.legenda, ct.legenda)) reg("legenda", cq.legenda[p], ct.legenda[p], idel, cargo, p);
    }
  }
  return dif;
}

const NOME_CARGO: Readonly<Record<number, string>> = { 1: "presidente", 3: "governador", 5: "senador", 6: "deputado federal", 7: "deputado estadual", 8: "deputado distrital" };

/** Rótulo curto de uma diferença para o telão ("presidente: votos no 13"). */
export function rotuloDiferenca(d: Diferenca): string {
  const cargo = d.cargo === null ? null : (NOME_CARGO[d.cargo] ?? `cargo ${d.cargo}`);
  const pre = cargo === null ? "" : `${cargo}: `;
  switch (d.campo) {
    case "comparecimento":
      return "comparecimento";
    case "aptos":
      return `aptos (eleição ${d.idel ?? "?"})`;
    case "branco":
      return `${pre}brancos`;
    case "nulo":
      return `${pre}nulos`;
    case "comparecimento_cargo":
      return `${pre}comparecimento`;
    case "nominal":
      return `${pre}votos no ${d.chave ?? "?"}`;
    case "legenda":
      return `${pre}legenda ${d.chave ?? "?"}`;
    case "eleicao_ausente":
      return `eleição ${d.idel ?? "?"} ausente`;
    case "cargo_ausente":
      return `${pre}cargo ausente`;
    default:
      return d.campo;
  }
}
