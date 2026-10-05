// Resumo em markdown (pt-BR) da avaliação final. Puro: recebe o objeto já montado.
import { CAMPOS, type Bloco, type Campo } from "./puro.ts";

const NF = new Intl.NumberFormat("pt-BR");
export const int = (x: number): string => NF.format(Math.round(x));
export const pct = (x: number, casas = 2): string => `${x.toLocaleString("pt-BR", { minimumFractionDigits: casas, maximumFractionDigits: casas })}%`;
export const pp = (x: number): string => `${x.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${Math.abs(x) === 1 ? "ponto" : "pontos"}`;
export const brt = (iso: string | null | undefined): string =>
  iso ? new Date(iso).toLocaleTimeString("pt-BR", { timeZone: "America/Sao_Paulo", hour: "2-digit", minute: "2-digit", second: "2-digit" }) : "sem registro";

export const ROTULO: Record<Campo, string> = {
  esquerda: "Esquerda", "centro-esquerda": "Centro-esquerda", centro: "Centro", "centro-direita": "Centro-direita", direita: "Direita", indefinido: "Indefinido",
};

const NUMERICO = /^-?[\d.,]+%?$|^$/;

/** Tabela markdown; coluna alinhada à direita quando todas as células são números. */
const tabela = (cab: readonly string[], linhas: readonly (readonly string[])[]): string => {
  const alinha = cab.map((_, i) => (i > 0 && linhas.every((l) => NUMERICO.test(l[i] ?? "")) ? "---:" : "---"));
  return [`| ${cab.join(" | ")} |`, `| ${alinha.join(" | ")} |`, ...linhas.map((l) => `| ${l.join(" | ")} |`)].join("\n");
};

/** Tabela campo × colunas; `cols` são contagens por campo, com % sobre o total da coluna quando `comPct`. */
export function tabelaCampos(cols: readonly { nome: string; dados: Record<Campo, number> }[], comPct: boolean): string {
  const totais = cols.map((c) => CAMPOS.reduce((s, k) => s + c.dados[k], 0));
  const cab = ["Campo", ...cols.flatMap((c) => (comPct ? [c.nome, "%"] : [c.nome]))];
  const linhas = CAMPOS.filter((k) => cols.some((c) => c.dados[k] > 0)).map((k) => [
    ROTULO[k],
    ...cols.flatMap((c, i) => (comPct ? [int(c.dados[k]), pct((100 * c.dados[k]) / ((totais[i] ?? 0) || 1), 1)] : [int(c.dados[k])])),
  ]);
  linhas.push(["Total", ...cols.flatMap((_, i) => (comPct ? [int(totais[i] ?? 0), ""] : [int(totais[i] ?? 0)]))]);
  return tabela(cab, linhas);
}

export const tabelaBlocos = (b: Record<Bloco, number>): string =>
  tabela(["Bloco", "Cadeiras"], (Object.entries(b) as [Bloco, number][]).filter(([, v]) => v > 0).map(([k, v]) => [k, int(v)]));

export { tabela };

export interface CandMd {
  nome: string;
  partido: string;
  campo: Campo;
  votos: number;
  pct: number;
}
export const cand = (c: CandMd): string => `${c.nome} (${c.partido}, ${ROTULO[c.campo].toLowerCase()}) ${pct(c.pct)}`;
