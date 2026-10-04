// Cliente HTTP do TSE: GET condicional, gzip e classificação pelo corpo, não só pelo status.
import { BASE_URL, UA_PADRAO } from "../config.ts";
import { sha256Hex } from "../db/itens.ts";
import type { ClasseFetch, FetchResult, MotivoFetch } from "../types.ts";

export interface OpcoesHttp {
  ua?: string;
  timeoutMs?: number;
  /** APURACAO_SEM_CONDICIONAL=1 desliga If-None-Match/If-Modified-Since */
  semCondicional?: boolean;
  /** troca o prefixo BASE_URL das URLs do registro (APURACAO_BASE_URL nos testes) */
  baseUrl?: string;
  fetchImpl?: (url: string, init: RequestInit) => Promise<Response>;
  agora?: () => number;
}

export interface Validadores {
  etag: string | null;
  lastModified: string | null;
}

export function resolverUrl(url: string, base: string | undefined): string {
  if (base === undefined || base === BASE_URL || !url.startsWith(BASE_URL)) return url;
  return base + url.slice(BASE_URL.length);
}

/** Retry-After em segundos ou data HTTP. */
export function retryAfterS(v: string | null, agora: number): number | null {
  if (v === null || v.trim() === "") return null;
  const n = Number(v.trim());
  if (Number.isFinite(n)) return Math.max(0, Math.round(n));
  const t = Date.parse(v);
  return Number.isFinite(t) ? Math.max(0, Math.round((t - agora) / 1000)) : null;
}

const decod = new TextDecoder();

/** Classificação por corpo e status, na ordem do plano. */
export function classificar(status: number, corpo: Uint8Array): ClasseFetch {
  if (status === 304) return "nao_modificado";
  const ini = decod.decode(corpo.subarray(0, 2048));
  const lead = ini.trimStart();
  if (status === 200 && lead.startsWith("{")) return "ok";
  if (ini.includes("<Code>NoSuchKey</Code>") || status === 404) return "nao_existe";
  if (status === 403 || ini.includes("Access Denied")) return "negado";
  if (status === 429) return "limite";
  if (status >= 500) return "erro_servidor";
  if (status === 200) return "corpo_invalido";
  return "erro_rede";
}

function inteiroOuNull(v: string | null): number | null {
  if (v === null) return null;
  const n = Number.parseInt(v, 10);
  return Number.isFinite(n) ? n : null;
}

function resumoCache(h: Headers): string | null {
  const partes: string[] = [];
  const add = (nome: string, rotulo: string = nome): void => {
    const v = h.get(nome);
    if (v !== null) partes.push(`${rotulo}=${v}`);
  };
  add("cache-control", "cc");
  add("x-cache");
  add("cdn-cache-status", "cdn");
  add("x-ratelimit-limit", "rl");
  add("x-ratelimit-remaining", "rlr");
  add("x-ratelimit-reset", "rlz");
  return partes.length > 0 ? partes.join("; ") : null;
}

/** Uma requisição. Nunca lança: falhas viram classe. */
export async function fetchTse(
  job: { url: string; motivo: MotivoFetch },
  estado: Validadores | null,
  opts: OpcoesHttp = {},
): Promise<FetchResult> {
  const agora = opts.agora ?? Date.now;
  const t0 = agora();
  const iniciadoEm = new Date(t0).toISOString();
  const headers: Record<string, string> = {
    "User-Agent": opts.ua ?? UA_PADRAO,
    "Accept-Encoding": "gzip",
    Accept: "application/json, text/plain, */*",
  };
  const usarCondicional = job.motivo !== "final" && opts.semCondicional !== true && estado !== null;
  let condicional = false;
  if (usarCondicional && estado.etag !== null) {
    headers["If-None-Match"] = estado.etag;
    condicional = true;
  }
  if (usarCondicional && estado.lastModified !== null) {
    headers["If-Modified-Since"] = estado.lastModified;
    condicional = true;
  }
  const base: FetchResult = {
    classe: "erro_rede", iniciadoEm, duracaoMs: 0, condicional, httpStatus: null, etag: null, lastModified: null,
    servidorDate: null, cacheHdr: null, age: null, retryAfterS: null, bytes: 0, body: null, bodySha256: null, erro: null,
  };
  const f = opts.fetchImpl ?? ((u: string, i: RequestInit) => fetch(u, i));
  try {
    const res = await f(resolverUrl(job.url, opts.baseUrl), {
      headers,
      signal: AbortSignal.timeout(opts.timeoutMs ?? 15_000),
      redirect: "follow",
    });
    const corpo = new Uint8Array(await res.arrayBuffer());
    const classe = classificar(res.status, corpo);
    const h = res.headers;
    return {
      ...base,
      classe,
      duracaoMs: Math.round(agora() - t0),
      httpStatus: res.status,
      etag: h.get("etag"),
      lastModified: h.get("last-modified"),
      servidorDate: h.get("date"),
      cacheHdr: resumoCache(h),
      age: inteiroOuNull(h.get("age")),
      retryAfterS: classe === "limite" ? retryAfterS(h.get("retry-after"), agora()) : null,
      bytes: corpo.byteLength,
      body: corpo.byteLength > 0 ? corpo : null,
      bodySha256: classe === "ok" ? sha256Hex(corpo) : null,
      erro: classe === "ok" || classe === "nao_modificado" ? null : `HTTP ${res.status}`,
    };
  } catch (err) {
    const nome = err instanceof Error ? err.name : "";
    const msg = err instanceof Error ? err.message : String(err);
    const timeout = nome === "TimeoutError" || nome === "AbortError";
    return { ...base, classe: timeout ? "timeout" : "erro_rede", duracaoMs: Math.round(agora() - t0), erro: `${nome}: ${msg}`.slice(0, 500) };
  }
}
