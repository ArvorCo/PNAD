// Coleta de uma seção: aux.json -> hash -> -bu.dat e -log.jez; decodifica o BU e lê o modelo
// da urna no log. Nunca lança: falhas viram `erro` e `status_aux`.
import { createHash } from "node:crypto";
import { z } from "zod";
import { decodificarBu } from "../bu-decode.ts";
import type { ResultadoSecao, SecaoCs } from "./banco.ts";
import type { Resposta } from "./http.ts";
import { lerZip, modeloDaUrna, resumirLog } from "./log-urna.ts";

export const BASE_URNA = "https://resultados.tse.jus.br/oficial/ele2026/arquivo-urna/3220";
export const PLEITO = "003220";

export const ArqSchema = z.object({ nm: z.string(), tp: z.string().optional() }).passthrough();
export const HashSchema = z
  .object({ hash: z.string(), dr: z.string().optional(), hr: z.string().optional(), st: z.string().optional(), arq: z.array(ArqSchema).optional() })
  .passthrough();
export const AuxSchema = z
  .object({ dg: z.string().optional(), hg: z.string().optional(), st: z.string().optional(), hashes: z.array(HashSchema).optional() })
  .passthrough();
export type Aux = z.infer<typeof AuxSchema>;

const p4 = (n: number): string => String(n).padStart(4, "0");

export function dirSecao(s: { uf: string; mun: string; zona: number; secao: number }): string {
  return `${BASE_URNA}/dados/${s.uf}/${s.mun}/${p4(s.zona)}/${p4(s.secao)}`;
}

export function urlAux(s: { uf: string; mun: string; zona: number; secao: number }): string {
  return `${dirSecao(s)}/p${PLEITO}-${s.uf}-m${s.mun}-z${p4(s.zona)}-s${p4(s.secao)}-aux.json`;
}

export const urlCs = (uf: string): string => `${BASE_URNA}/config/${uf}/${uf}-p${PLEITO}-cs.json`;

/** 'dd/mm/aaaa' + 'hh:mm:ss' para 'aaaa-mm-dd hh:mm:ss' (hora como publicada pelo TSE). */
export function dataHoraTse(d: string | undefined, h: string | undefined): string | null {
  if (d === undefined) return null;
  const m = /^(\d{2})\/(\d{2})\/(\d{4})$/.exec(d);
  if (m === null) return `${d} ${h ?? ""}`.trim();
  return `${m[3]}-${m[2]}-${m[1]}${h === undefined ? "" : ` ${h}`}`;
}

export interface Escolha {
  hash: string;
  st: string | null;
  drHr: string | null;
  bu: string;
  log: string | null;
}

/**
 * Hash com boletim: o mais recente pela data de recebimento; empate fica com o último da lista.
 * O boletim é o `bu` da urna ou, quando a seção passou pelo Sistema de Apuração (cédula, urna
 * com defeito, apuração mista; comum no exterior), o `busa`, no mesmo formato ASN.1. Com os
 * dois no mesmo hash vale o `busa`, que é o resultado consolidado da seção.
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
    const log = arq.find((a) => a.tp === "log") ?? arq.find((a) => a.nm.endsWith("-log.jez"));
    const drHr = dataHoraTse(h.dr, h.hr);
    if (melhor === null || (drHr ?? "") >= (melhor.drHr ?? "")) {
      melhor = { hash: h.hash, st: h.st ?? null, drHr, bu: bu.nm, log: log?.nm ?? null };
    }
  }
  return melhor;
}

export const sha256 = (b: Uint8Array): string => createHash("sha256").update(b).digest("hex");

export interface OpcoesSecao {
  obter: (url: string) => Promise<Resposta>;
  guardarLog: boolean;
}

function vazio(s: SecaoCs): ResultadoSecao {
  return {
    uf: s.uf, mun: s.mun, zona: s.zona, secao: s.secao, statusAux: "pendente", auxDgHg: null, auxJson: null, nHashes: null,
    hash: null, hashSt: null, drHr: null, buNome: null, buBytes: null, buSha256: null, buGz: null, logNome: null, logBytes: null,
    logSha256: null, logZip: null, erro: null, requisicoes: 0, bu: null, modelo: null, resumoLog: null,
  };
}

const msg = (e: unknown): string => (e instanceof Error ? `${e.name}: ${e.message}` : String(e)).slice(0, 300);

export async function coletarSecao(s: SecaoCs, o: OpcoesSecao): Promise<ResultadoSecao> {
  const r = vazio(s);
  const auxR = await o.obter(urlAux(s));
  r.requisicoes += auxR.requisicoes;
  if (auxR.status === 404) {
    r.statusAux = "aux_404";
    return r;
  }
  if (auxR.corpo === null) {
    r.statusAux = "aux_erro";
    r.erro = `aux: ${auxR.erro ?? "sem corpo"}`;
    return r;
  }
  const texto = new TextDecoder().decode(auxR.corpo);
  r.auxJson = texto;
  let aux: Aux;
  try {
    aux = AuxSchema.parse(JSON.parse(texto));
  } catch (e) {
    r.statusAux = "aux_erro";
    r.erro = `aux inválido: ${msg(e)}`;
    return r;
  }
  r.statusAux = aux.st ?? "sem_st";
  r.auxDgHg = dataHoraTse(aux.dg, aux.hg);
  r.nHashes = aux.hashes?.length ?? 0;
  const e = escolherHash(aux);
  if (e === null) return r;
  r.hash = e.hash;
  r.hashSt = e.st;
  r.drHr = e.drHr;
  r.buNome = e.bu;
  const dir = `${dirSecao(s)}/${e.hash}`;
  const [buR, logR] = await Promise.all([o.obter(`${dir}/${e.bu}`), e.log === null ? Promise.resolve(null) : o.obter(`${dir}/${e.log}`)]);
  r.requisicoes += buR.requisicoes + (logR?.requisicoes ?? 0);
  const erros: string[] = [];
  if (buR.corpo === null) {
    erros.push(`bu: ${buR.erro ?? "sem corpo"}`);
  } else {
    r.buBytes = buR.corpo.byteLength;
    r.buSha256 = sha256(buR.corpo);
    r.buGz = Bun.gzipSync(buR.corpo);
    try {
      r.bu = decodificarBu(buR.corpo).bu;
    } catch (err) {
      erros.push(`bu decodificação: ${msg(err)}`);
    }
  }
  if (e.log === null || logR === null) {
    r.modelo = { modelo: null, fonte: "sem_log" };
  } else if (logR.corpo === null) {
    r.logNome = e.log;
    r.modelo = { modelo: null, fonte: "sem_log" };
    if (logR.status !== 404) erros.push(`log: ${logR.erro ?? "sem corpo"}`);
  } else {
    r.logNome = e.log;
    r.logBytes = logR.corpo.byteLength;
    r.logSha256 = sha256(logR.corpo);
    if (o.guardarLog) r.logZip = logR.corpo;
    try {
      r.resumoLog = resumirLog(lerZip(logR.corpo));
      r.modelo = r.bu === null ? null : modeloDaUrna(r.resumoLog, r.bu.urna.correspondenciaResultado.carga.numeroInternoUrna);
    } catch (err) {
      r.modelo = { modelo: null, fonte: "log_invalido" };
      erros.push(`log: ${msg(err)}`);
    }
  }
  if (erros.length > 0) r.erro = erros.join("; ");
  return r;
}
