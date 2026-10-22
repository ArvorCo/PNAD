// aux.json da seção (hashes e recebimento) e o BU decodificado reduzido ao que a amostra e a
// conferência da totalização paralela usam: horas convertidas para UTC e o esqueleto
// eleição → cargo → contagens, o mesmo de ../scripts/totalizacao-conferir-tse.py.
import { z } from "zod";
import { horaBrasiliaParaIso, horaLocalUrnaParaIso } from "../turno2/comum.ts";
import type { BoletimUrna } from "./bu-decode.ts";
import { dataHoraJe } from "./bu-decode.ts";

const ArqSchema = z.object({ nm: z.string(), tp: z.string().optional() }).passthrough();
const HashSchema = z
  .object({ hash: z.string(), dr: z.string().optional(), hr: z.string().optional(), st: z.string().optional(), arq: z.array(ArqSchema).optional() })
  .passthrough();
export const AuxSchema = z
  .object({ dg: z.string().optional(), hg: z.string().optional(), st: z.string().optional(), hashes: z.array(HashSchema).optional() })
  .passthrough();
export type Aux = z.infer<typeof AuxSchema>;

/** 'dd/mm/aaaa' + 'hh:mm:ss' → 'aaaa-mm-dd hh:mm:ss' (hora como publicada). */
export function dataHoraTse(d: string | undefined, h: string | undefined): string | null {
  if (d === undefined) return null;
  const m = /^(\d{2})\/(\d{2})\/(\d{4})$/.exec(d);
  if (m === null) return `${d} ${h ?? ""}`.trim();
  return `${m[3]}-${m[2]}-${m[1]}${h === undefined ? "" : ` ${h}`}`;
}

export interface Escolha {
  hash: string;
  st: string | null;
  /** recebimento no TSE, 'aaaa-mm-dd hh:mm:ss' de Brasília */
  drHr: string | null;
  bu: string;
}

/**
 * Hash com boletim, o mais recente pelo recebimento (empate: o último da lista). Com `busa`
 * (Sistema de Apuração) e `bu` no mesmo hash vale o `busa`, resultado consolidado da seção.
 */
export function escolherHash(aux: Aux): Escolha | null {
  let melhor: Escolha | null = null;
  for (const h of aux.hashes ?? []) {
    const arq = h.arq ?? [];
    const bu =
      arq.find((a) => a.tp === "busa") ??
      arq.find((a) => a.nm.endsWith("-busa.dat")) ??
      arq.find((a) => a.tp === "bu") ??
      arq.find((a) => a.nm.endsWith("-bu.dat"));
    if (bu === undefined) continue;
    const drHr = dataHoraTse(h.dr, h.hr);
    if (melhor === null || (drHr ?? "") >= (melhor.drHr ?? "")) melhor = { hash: h.hash, st: h.st ?? null, drHr, bu: bu.nm };
  }
  return melhor;
}

export interface CargoComparavel {
  nominais: Record<string, number>;
  legenda: Record<string, number>;
  branco: number;
  nulo: number;
  comparecimento: number | null;
}

export interface EleicaoComparavel {
  aptos: number | null;
  cargos: Record<string, CargoComparavel>;
}

/** Esqueleto comum ao BU oficial e ao BU lido do QR. */
export interface BuComparavel {
  comparecimento: number | null;
  eleicoes: Record<string, EleicaoComparavel>;
}

const TIPO = { nominal: 1, branco: 2, nulo: 3, legenda: 4 } as const;

/** BU oficial no esqueleto da conferência (tipo 5, cargo sem candidato, fica de fora). */
export function buComparavel(bu: BoletimUrna): BuComparavel {
  const out: BuComparavel = { comparecimento: bu.qtdEleitoresCompareceram, eleicoes: {} };
  for (const e of bu.resultadosVotacaoPorEleicao) {
    const ele: EleicaoComparavel = { aptos: e.qtdEleitoresAptos, cargos: {} };
    for (const rv of e.resultadosVotacao) {
      for (const tc of rv.totaisVotosCargo) {
        const c: CargoComparavel = { nominais: {}, legenda: {}, branco: 0, nulo: 0, comparecimento: rv.qtdComparecimento };
        for (const v of tc.votosVotaveis) {
          const q = v.quantidadeVotos;
          if (v.tipoVoto === TIPO.nominal) {
            const k = String(v.codigo);
            c.nominais[k] = (c.nominais[k] ?? 0) + q;
          } else if (v.tipoVoto === TIPO.legenda) {
            const k = String(v.partido);
            c.legenda[k] = (c.legenda[k] ?? 0) + q;
          } else if (v.tipoVoto === TIPO.branco) {
            c.branco += q;
          } else if (v.tipoVoto === TIPO.nulo) {
            c.nulo += q;
          }
        }
        ele.cargos[String(tc.codigoCargo.valor)] = c;
      }
    }
    out.eleicoes[String(e.idEleicao)] = ele;
  }
  return out;
}

export interface ResumoBu {
  encerramentoLocal: string | null;
  encerramentoIso: string | null;
  emissaoIso: string | null;
  aptos: number | null;
  comparecimento: number;
  votos: BuComparavel;
}

/**
 * Horas do BU são locais da urna: convertidas pelo fuso da UF. No exterior (zz) o fuso é o do
 * país e não está no BU: a hora local fica, a conversão não.
 */
export function resumoBu(bu: BoletimUrna, uf: string, eleFederal: number): ResumoBu {
  const local = dataHoraJe(bu.dadosSecao?.dataHoraEncerramento ?? null);
  const emissao = dataHoraJe(bu.dataHoraEmissao);
  const exterior = uf.toLowerCase() === "zz";
  const fed = bu.resultadosVotacaoPorEleicao.find((e) => e.idEleicao === eleFederal) ?? bu.resultadosVotacaoPorEleicao[0];
  return {
    encerramentoLocal: local,
    encerramentoIso: exterior ? null : horaLocalUrnaParaIso(uf, local),
    emissaoIso: exterior ? null : horaLocalUrnaParaIso(uf, emissao),
    aptos: fed?.qtdEleitoresAptos ?? null,
    comparecimento: bu.qtdEleitoresCompareceram,
    votos: buComparavel(bu),
  };
}

export const recebidoIso = (drHr: string | null): string | null => horaBrasiliaParaIso(drHr);

/** Minutos entre dois ISO (b − a), uma casa; null se faltar um. */
export function minutosEntre(a: string | null, b: string | null): number | null {
  if (a === null || b === null) return null;
  const d = (Date.parse(b) - Date.parse(a)) / 60000;
  return Number.isFinite(d) ? Math.round(d * 10) / 10 : null;
}
