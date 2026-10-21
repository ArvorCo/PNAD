import { Children, type CSSProperties, type PropsWithChildren } from "react";
import { useFormato } from "../formato";

type Alinhamento = CSSProperties["alignItems"];

/**
 * Área útil de cada cena: entre o HUD (topo) e a legenda (base), dentro das margens seguras.
 * Toda cena nova monta o conteúdo aqui dentro para nunca colidir com HUD e legenda.
 */
export const Palco: React.FC<PropsWithChildren<{ style?: CSSProperties }>> = ({ children, style }) => {
  const { vertical, altura, margem } = useFormato();
  return (
    <div
      style={{
        position: "absolute",
        left: margem,
        right: margem,
        top: margem + 110,
        bottom: vertical ? altura * 0.16 + 120 : 230,
        display: "flex",
        flexDirection: "column",
        ...style,
      }}
    >
      {children}
    </div>
  );
};

type LadoProps = PropsWithChildren<{
  /** Peso de cada filho no eixo principal (flex-grow); falta = 1. */
  proporcoes?: number[];
  /** Pesos só para o 9:16, quando diferem dos do 16:9. */
  proporcoesVertical?: number[];
  /** Espaço entre filhos em px de referência (escalado). */
  gap?: number;
  alinhar?: Alinhamento;
  style?: CSSProperties;
}>;

/** Lado a lado no 16:9, empilhado no 9:16, com a proporção de cada filho. */
export const Lado: React.FC<LadoProps> = ({ children, proporcoes = [], proporcoesVertical, gap = 36, alinhar = "stretch", style }) => {
  const { vertical, t } = useFormato();
  const pesos = vertical && proporcoesVertical ? proporcoesVertical : proporcoes;
  return (
    <div
      style={{
        display: "flex",
        flexDirection: vertical ? "column" : "row",
        gap: t(gap),
        alignItems: alinhar,
        flex: 1,
        minWidth: 0,
        minHeight: 0,
        ...style,
      }}
    >
      {Children.toArray(children).map((filho, i) => (
        <div key={i} style={{ flex: `${pesos[i] ?? 1} 1 0`, minWidth: 0, minHeight: 0, display: "flex", flexDirection: "column" }}>
          {filho}
        </div>
      ))}
    </div>
  );
};

type PilhaProps = PropsWithChildren<{
  gap?: number;
  alinhar?: Alinhamento;
  /** Distribuição vertical dos filhos. */
  justificar?: CSSProperties["justifyContent"];
  style?: CSSProperties;
}>;

/** Coluna com espaçamento escalado. */
export const Pilha: React.FC<PilhaProps> = ({ children, gap = 22, alinhar = "stretch", justificar = "flex-start", style }) => {
  const { t } = useFormato();
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: t(gap), alignItems: alinhar, justifyContent: justificar, minWidth: 0, minHeight: 0, ...style }}>
      {children}
    </div>
  );
};
