import { useFormato } from "../formato";
import { COR, FONTE, MONO } from "../tema";
import { Entrada } from "./Caixa";
import { lerEm } from "../ref";
import { decimal, inteiro } from "./util";

export type FormatoColuna = "texto" | "inteiro" | "decimal" | "pct";

export type Coluna = {
  titulo: string;
  campo: string;
  formato?: FormatoColuna;
  /** Rótulo legível para valores de texto do JSON (chave crua como "nao_informado" não vai à tela). */
  rotulos?: Readonly<Record<string, string>>;
  casas?: number;
  /** Peso de largura relativa; falta = 1. */
  largura?: number;
};

type Props = {
  colunas: Coluna[];
  linhas: unknown[];
  /** Quadro em que a primeira linha entra; as demais vêm a cada `passo` quadros. */
  inicio: number;
  passo?: number;
  cor?: string;
  /** Linhas com este campo verdadeiro ganham realce. */
  destaque?: string;
};

const celula = (item: unknown, c: Coluna): string => {
  const v = lerEm(item, c.campo);
  if (v === undefined || v === null) {
    return "n/d";
  }
  if (typeof v !== "number") {
    return c.rotulos?.[String(v)] ?? String(v);
  }
  switch (c.formato) {
    case "inteiro":
      return inteiro(v);
    case "decimal":
      return decimal(v, c.casas ?? 1);
    case "pct":
      return `${decimal(v, c.casas ?? 1)}%`;
    default:
      return String(v);
  }
};

/** Tabela de ranking: cabeçalho fixo e linhas que entram em sequência. */
export const Tabela: React.FC<Props> = ({ colunas, linhas, inicio, passo = 4, cor = COR.tealClaro, destaque }) => {
  const { t, vertical } = useFormato();
  const grade = colunas.map((c) => `${c.largura ?? 1}fr`).join(" ");
  // Acima de dez linhas a letra encolhe na mesma proporção, para a tabela caber na área da cena.
  const tamanho = t((vertical ? 28 : 26) * Math.min(1, 10 / Math.max(linhas.length, 1)));
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: t(8), width: "100%" }}>
      <div style={{ display: "grid", gridTemplateColumns: grade, gap: t(14), fontFamily: MONO, fontWeight: 700, fontSize: t(16), letterSpacing: 2, color: cor, paddingBottom: t(8), borderBottom: `2px solid ${cor}` }}>
        {colunas.map((c) => (
          <div key={c.campo} style={{ textAlign: c.formato && c.formato !== "texto" ? "right" : "left" }}>
            {c.titulo.toUpperCase()}
          </div>
        ))}
      </div>
      {linhas.map((item, i) => {
        const marcada = destaque !== undefined && (item as Record<string, unknown>)[destaque] === true;
        return (
          <Entrada key={i} inicio={inicio + i * passo} de="esquerda">
            <div
              style={{
                display: "grid",
                gridTemplateColumns: grade,
                gap: t(14),
                fontFamily: FONTE,
                fontWeight: marcada ? 700 : 500,
                fontSize: tamanho,
                color: marcada ? COR.ouro : COR.tinta,
                padding: `${t(5)}px 0`,
                borderBottom: `1px solid ${COR.linha}`,
              }}
            >
              {colunas.map((c) => (
                <div key={c.campo} style={{ textAlign: c.formato && c.formato !== "texto" ? "right" : "left", fontVariantNumeric: "tabular-nums", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {celula(item, c)}
                </div>
              ))}
            </div>
          </Entrada>
        );
      })}
    </div>
  );
};
