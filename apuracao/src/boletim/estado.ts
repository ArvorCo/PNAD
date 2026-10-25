// Estado do boletim falado em arquivos (data/boletins-2t/). Dois escritores, um arquivo cada:
// o gerador (processo `bun run boletim`) escreve indice.json, gerador.json e os HHMM.*; o servidor
// escreve controle.json (no ar, tocados, descartados) e pedido.json (geração manual). Ninguém
// escreve no SQLite. Toda gravação é atômica (arquivo temporário + rename).
import { existsSync, mkdirSync, readFileSync, renameSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";

export const RAIZ_APURACAO = resolve(import.meta.dir, "../..");

export function dirBoletins(): string {
  return process.env.APURACAO_BOLETIM_DIR ?? join(RAIZ_APURACAO, "data/boletins-2t");
}

export type EstadoGeracao = "gerando" | "pronto" | "erro";
export type EstadoBoletim = EstadoGeracao | "no_ar" | "tocado" | "descartado";
export type Etapa = "dados" | "roteiro" | "enxugar" | "audio";
export type Modo = "abertura" | "pouca" | "muita";

/** Linha do indice.json (escrito só pelo gerador). */
export interface ItemIndice {
  id: string;
  hora: string;
  estado: EstadoGeracao;
  etapa: Etapa | null;
  origem: "relogio" | "manual";
  criado_em: string;
  atualizado_em: string;
  modo: Modo | null;
  palavras: number | null;
  duracao_s: number | null;
  resumo: string | null;
  erro: string | null;
}

export interface Indice {
  atualizado_em: string;
  itens: ItemIndice[];
}

/** controle.json (escrito só pelo servidor). */
export interface Controle {
  atualizado_em: string;
  no_ar: { id: string; desde: string; duracao_s: number | null } | null;
  tocados: Record<string, string>;
  descartados: Record<string, string>;
}

/** gerador.json: batimento do processo gerador (a cada 2 s). */
export interface Gerador {
  pid: number;
  iniciado_em: string;
  batimento_em: string;
  relogio_ligado: boolean;
  intervalo_s: number;
  inicio_em: string;
  proximo_ciclo_em: string | null;
  gerando: string | null;
  etapa: Etapa | null;
  ultimo_erro: string | null;
}

/** pedido.json: geração manual pedida pelo diretor (o gerador apaga ao atender). */
export interface Pedido {
  em: string;
}

/** Item como a API entrega: geração + controle. */
export interface ItemBoletim extends Omit<ItemIndice, "estado"> {
  estado: EstadoBoletim;
  tocado_em: string | null;
}

export const RE_ID = /^\d{4}(-\d{1,2})?$/;

export const caminho = (dir: string, nome: string): string => join(dir, nome);

export function gravarJson(path: string, dado: unknown): void {
  const dir = resolve(path, "..");
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
  const tmp = `${path}.tmp-${process.pid}`;
  writeFileSync(tmp, `${JSON.stringify(dado, null, 1)}\n`);
  renameSync(tmp, path);
}

export function lerJson<T>(path: string): T | null {
  try {
    return JSON.parse(readFileSync(path, "utf8")) as T;
  } catch {
    return null;
  }
}

export const lerIndice = (dir: string): Indice => lerJson<Indice>(caminho(dir, "indice.json")) ?? { atualizado_em: "", itens: [] };

export const lerControle = (dir: string): Controle =>
  lerJson<Controle>(caminho(dir, "controle.json")) ?? { atualizado_em: "", no_ar: null, tocados: {}, descartados: {} };

export const lerGerador = (dir: string): Gerador | null => lerJson<Gerador>(caminho(dir, "gerador.json"));

/** Estado combinado de um item: descartado > no ar > gerando/erro > tocado > pronto. */
export function estadoDe(item: ItemIndice, c: Controle): EstadoBoletim {
  if (c.descartados[item.id]) return "descartado";
  if (c.no_ar?.id === item.id) return "no_ar";
  if (item.estado !== "pronto") return item.estado;
  if (c.tocados[item.id]) return "tocado";
  return "pronto";
}

/** Lista para a API, mais recente primeiro; descartados só com `todos`. */
export function listar(ind: Indice, c: Controle, todos = false): ItemBoletim[] {
  return [...ind.itens]
    .sort((a, b) => b.criado_em.localeCompare(a.criado_em))
    .map(i => ({ ...i, estado: estadoDe(i, c), tocado_em: c.tocados[i.id] ?? null }))
    .filter(i => todos || i.estado !== "descartado");
}

/** HH:MM de Brasília de um instante. */
export function horaBrt(iso: string | number | Date): string {
  return new Date(iso).toLocaleTimeString("pt-BR", { timeZone: "America/Sao_Paulo", hour: "2-digit", minute: "2-digit", hour12: false });
}

/** HHMM de Brasília (id do boletim). */
export const hhmmBrt = (iso: string | number | Date): string => horaBrt(iso).replace(":", "");
