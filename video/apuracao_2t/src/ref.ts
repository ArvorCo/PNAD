// Leitura de valores dos blocos de dados por caminho (`presidente.nacional.pct.flavio`,
// `linha_do_tempo.marcos[0].hhmm`). As cenas declaram o caminho; o dado só é lido na hora de
// desenhar, e caminho que não existe devolve `null` para a cena mostrar o aviso de dado pendente.
import type { Dados } from "./tipos";

/** Número literal ou caminho em `Dados`. */
export type RefNumero = number | { dado: string };
export type RefTexto = string | { dado: string };

const PASSO = /[^.[\]]+|\[(\d+)\]/g;

const passos = (caminho: string): (string | number)[] =>
  [...caminho.matchAll(PASSO)].map((m) => (m[1] !== undefined ? Number(m[1]) : m[0]));

/** Valor no caminho a partir de um objeto qualquer, ou `undefined` se algum passo não existe. */
export const lerEm = (origem: unknown, caminho: string): unknown => {
  let atual: unknown = origem;
  for (const passo of passos(caminho)) {
    if (atual === null || typeof atual !== "object") {
      return undefined;
    }
    atual = (atual as Record<string | number, unknown>)[passo];
  }
  return atual;
};

/** Valor no caminho em `Dados`, ou `undefined` se qualquer passo não existe. */
export const lerDado = (dados: Dados, caminho: string): unknown => lerEm(dados, caminho);

export const numeroDe = (dados: Dados, ref: RefNumero): number | null => {
  const v = typeof ref === "number" ? ref : lerDado(dados, ref.dado);
  return typeof v === "number" && Number.isFinite(v) ? v : null;
};

export const textoDe = (dados: Dados, ref: RefTexto): string | null => {
  const v = typeof ref === "string" ? ref : lerDado(dados, ref.dado);
  return typeof v === "string" || typeof v === "number" ? String(v) : null;
};

export const listaDe = (dados: Dados, caminho: string): unknown[] | null => {
  const v = lerDado(dados, caminho);
  return Array.isArray(v) ? v : null;
};

/** Campo numérico de um objeto qualquer (caminho com pontos aceito), ou `null`. */
export const campoNumero = (item: unknown, campo: string): number | null => {
  const v = lerEm(item, campo);
  return typeof v === "number" && Number.isFinite(v) ? v : null;
};

export const campoTexto = (item: unknown, campo: string): string | null => {
  const v = lerEm(item, campo);
  return typeof v === "string" || typeof v === "number" ? String(v) : null;
};

/** Tabela no formato `{ colunas: [...], linhas: [[...]] }`, como a série da linha do tempo. */
export type Tabela = { colunas: string[]; linhas: unknown[][] };

export const tabelaDe = (dados: Dados, caminho: string): Tabela | null => {
  const v = lerDado(dados, caminho);
  if (v === null || typeof v !== "object") {
    return null;
  }
  const { colunas, linhas } = v as Record<string, unknown>;
  return Array.isArray(colunas) && Array.isArray(linhas) ? { colunas: colunas.map(String), linhas: linhas as unknown[][] } : null;
};
