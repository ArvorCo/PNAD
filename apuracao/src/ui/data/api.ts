// Cliente dos endpoints de "Contratos de API". O mock implementa a mesma interface.

import type { Anomalia, Config, ConfigUf, Estado, EstadoBr, EstadoUf, EventoSse, Mapa, NivelMapa, Resultado, Serie } from "../state/types.ts";

export interface ConsultaResultado {
  ele: number;
  cargo: number;
  abr: string;
}

export interface ConsultaMapa {
  ele: number;
  cargo: number;
  nivel: NivelMapa;
  pai: string;
}

/** Fonte de dados do telão: servidor real, replay (com `at`) ou mock. */
export interface Fonte {
  readonly tipo: "api" | "replay" | "mock";
  config(): Promise<Config>;
  estado(): Promise<Estado>;
  resultado(q: ConsultaResultado): Promise<Resultado>;
  mapa(q: ConsultaMapa): Promise<Mapa>;
  serie(q: ConsultaResultado): Promise<Serie>;
  anomalias(): Promise<Anomalia[]>;
  /** Endpoints de auditoria (JSON livre, lido direto das views do servidor). */
  auditoria(caminho: string, params?: Record<string, string | number>): Promise<unknown>;
  /** Eventos ao vivo. Só o mock implementa aqui; a API usa sse.ts. */
  eventos?(fn: (e: EventoSse) => void): () => void;
}

export class ErroApi extends Error {
  constructor(
    readonly status: number,
    readonly url: string,
  ) {
    super(`HTTP ${status} em ${url}`);
  }
}

export type Relogio = () => string | null;

/** Monta a URL com parâmetros e o `at` do replay quando houver. */
export function montarUrl(base: string, caminho: string, params: Record<string, string | number | undefined>, at: string | null): string {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) if (v !== undefined) q.set(k, String(v));
  if (at) q.set("at", at);
  const s = q.toString();
  return `${base}${caminho}${s ? `?${s}` : ""}`;
}

async function obter<T>(url: string, sinal?: AbortSignal): Promise<T> {
  const r = await fetch(url, { cache: "no-store", signal: sinal ?? null, headers: { accept: "application/json" } });
  if (!r.ok) throw new ErroApi(r.status, url);
  return (await r.json()) as T;
}

// ---------- ingresso: o servidor fala o dialeto do TSE, o telão usa caixa alta ----------

type Bruto = Record<string, unknown>;
const ehBruto = (x: unknown): x is Bruto => typeof x === "object" && x !== null && !Array.isArray(x);
const num = (x: unknown, padrao = 0): number => (typeof x === "number" && Number.isFinite(x) ? x : padrao);
const txt = (x: unknown): string => (typeof x === "string" ? x : x === null || x === undefined ? "" : String(x));
const txtOuNulo = (x: unknown): string | null => (typeof x === "string" ? x : null);

/**
 * Config do servidor: `ufs[].uf` vem em minúscula ("sp"); o telão indexa tudo em caixa alta.
 * O exterior ("zz") sai de `ufs`, que as telas leem como as 27 unidades da federação (governador,
 * senado, grade da espera); os municípios do exterior continuam em `municipios.ZZ` para a busca.
 */
export function normalizarConfig(bruto: unknown): Config {
  const b = ehBruto(bruto) ? bruto : {};
  const el = ehBruto(b.eleicoes) ? b.eleicoes : {};
  const ufs: ConfigUf[] = (Array.isArray(b.ufs) ? b.ufs : []).filter(ehBruto).map(u => ({
    uf: txt(u.uf).toUpperCase(),
    nome: txt(u.nome),
    cdi: txt(u.cdi),
    te: num(u.te),
  })).filter(u => u.uf !== "ZZ");
  const municipios: Config["municipios"] = {};
  if (ehBruto(b.municipios)) {
    for (const [k, v] of Object.entries(b.municipios)) {
      if (Array.isArray(v)) municipios[k.toUpperCase()] = v as Config["municipios"][string];
    }
  }
  return {
    turno: num(b.turno, 1),
    eleicoes: { federal: num(el.federal, 6257), estadual: num(el.estadual, 6259) },
    ufs,
    municipios,
  };
}

const BR_VAZIO: EstadoBr = { ts: 0, st: 0, pst: 0, dt_ht: null, hg: null, lido_em: null, atraso_s: null };

/** Estado do servidor: `br` é null antes do primeiro arquivo nacional e `ufs[].uf` vem em minúscula. */
export function normalizarEstado(bruto: unknown): Estado {
  const b = ehBruto(bruto) ? bruto : {};
  const br: EstadoBr = ehBruto(b.br) ? { ...BR_VAZIO, ...(b.br as Partial<EstadoBr>) } : BR_VAZIO;
  const ufs: EstadoUf[] = (Array.isArray(b.ufs) ? b.ufs : []).filter(ehBruto).map(u => ({
    ...(u as unknown as EstadoUf),
    uf: txt(u.uf).toUpperCase(),
  }));
  const lat = ehBruto(b.latencias) ? b.latencias : {};
  const lista = (x: unknown): number[] => (Array.isArray(x) ? x.filter((n): n is number => typeof n === "number") : []);
  const ult = ehBruto(b.ultimo_snapshot) ? { id: num(b.ultimo_snapshot.id), capturado_em: txt(b.ultimo_snapshot.capturado_em) } : null;
  return {
    agora: txt(b.agora) || new Date().toISOString(),
    pronto: b.pronto === true,
    turno: num(b.turno, 1),
    coletor: b.coletor ?? null,
    ultimo_snapshot: ult,
    br,
    ufs,
    historico: Array.isArray(b.historico) ? (b.historico as Estado["historico"]) : [],
    latencias: { leitura_menos_hg: lista(lat.leitura_menos_hg), hg_menos_ht: lista(lat.hg_menos_ht) },
  };
}

const CATEGORIAS = new Set<Anomalia["tipo"]>(["virada", "regressao", "fechou", "atraso"]);

/**
 * Anomalias do servidor: `tipo` é o tipo bruto do coletor e `categoria` a classe de exibição.
 * O telão usa a categoria e deixa de fora os eventos operacionais ("outro").
 */
export function normalizarAnomalias(bruto: unknown): Anomalia[] {
  if (!Array.isArray(bruto)) return [];
  const out: Anomalia[] = [];
  for (const a of bruto) {
    if (!ehBruto(a)) continue;
    const cat = txt(a.categoria || a.tipo) as Anomalia["tipo"];
    if (!CATEGORIAS.has(cat)) continue;
    const sev = a.severidade;
    const item: Anomalia = {
      at: txt(a.at),
      tipo: cat,
      abr: txt(a.abr),
      cargo: num(a.cargo ?? a.cargo_cd),
      texto: txt(a.texto),
      tipo_bruto: txt(a.tipo),
      uf: txtOuNulo(a.uf)?.toUpperCase() ?? null,
    };
    if (typeof a.id === "number") item.id = a.id;
    if (sev === "info" || sev === "warn" || sev === "error") item.severidade = sev;
    out.push(item);
  }
  return out;
}

/**
 * Cliente HTTP. `relogio` devolve o instante do replay (ISO) ou null no ao vivo;
 * ele é lido a cada chamada, então o replay avança sozinho.
 */
export function criarApi(base = "", relogio: Relogio = () => null): Fonte {
  const at = (): string | null => relogio();
  return {
    tipo: relogio() ? "replay" : "api",
    config: () => obter<unknown>(montarUrl(base, "/api/config", {}, null)).then(normalizarConfig),
    estado: () => obter<unknown>(montarUrl(base, "/api/estado", {}, at())).then(normalizarEstado),
    resultado: q => obter<Resultado>(montarUrl(base, "/api/resultado", { ele: q.ele, cargo: q.cargo, abr: q.abr }, at())),
    mapa: q => obter<Mapa>(montarUrl(base, "/api/mapa", { ele: q.ele, cargo: q.cargo, nivel: q.nivel, pai: q.pai }, at())),
    serie: q => obter<Serie>(montarUrl(base, "/api/serie", { ele: q.ele, cargo: q.cargo, abr: q.abr }, at())),
    anomalias: () => obter<unknown>(montarUrl(base, "/api/anomalias", {}, at())).then(normalizarAnomalias),
    auditoria: (caminho, params = {}) => obter<unknown>(montarUrl(base, caminho, params, at())),
  };
}

/** Ativos estáticos do telão (playlist, campos, cores, senadores de 2022). */
export async function ativo<T>(caminho: string): Promise<T | null> {
  try {
    return await obter<T>(caminho);
  } catch {
    return null;
  }
}
