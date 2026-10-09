import type { CSSProperties, PropsWithChildren } from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { COR, FONTE, MONO } from "../tema";
import { mola, rampa } from "./util";

type EntradaProps = PropsWithChildren<{
  inicio: number;
  de?: "baixo" | "cima" | "esquerda" | "direita" | "zoom";
  style?: CSSProperties;
}>;

/** Entrada com mola: deslize e opacidade a partir de um quadro. */
export const Entrada: React.FC<EntradaProps> = ({ inicio, de = "baixo", children, style }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = mola(frame, fps, inicio);
  const o = rampa(frame, inicio, inicio + 10);
  const d = 48 * (1 - p);
  const transform =
    de === "baixo"
      ? `translateY(${d}px)`
      : de === "cima"
        ? `translateY(${-d}px)`
        : de === "esquerda"
          ? `translateX(${-d}px)`
          : de === "direita"
            ? `translateX(${d}px)`
            : `scale(${0.7 + 0.3 * p})`;
  if (frame < inicio) {
    return null;
  }
  return <div style={{ opacity: o, transform, ...style }}>{children}</div>;
};

type CaixaProps = PropsWithChildren<{
  style?: CSSProperties;
  cor?: string;
  titulo?: string;
}>;

/** Painel de vidro com borda fina e, opcionalmente, um título em mono. */
export const Caixa: React.FC<CaixaProps> = ({ children, style, cor = COR.teal, titulo }) => (
  <div
    style={{
      background: COR.vidro,
      border: `1px solid ${COR.linha}`,
      borderLeft: `4px solid ${cor}`,
      borderRadius: 16,
      padding: "22px 28px",
      boxShadow: "0 20px 60px rgba(0,0,0,0.35)",
      backdropFilter: "blur(6px)",
      ...style,
    }}
  >
    {titulo ? (
      <div
        style={{
          fontFamily: MONO,
          fontSize: 16,
          letterSpacing: 3,
          color: cor,
          marginBottom: 10,
        }}
      >
        {titulo}
      </div>
    ) : null}
    {children}
  </div>
);

/** Etiqueta pequena, estilo badge de jogo. */
export const Chip: React.FC<PropsWithChildren<{ cor?: string; solido?: boolean; tamanho?: number }>> = ({
  children,
  cor = COR.tealClaro,
  solido = false,
  tamanho = 18,
}) => (
  <span
    style={{
      display: "inline-block",
      fontFamily: MONO,
      fontSize: tamanho,
      fontWeight: 700,
      letterSpacing: 2.5,
      padding: "6px 14px",
      borderRadius: 8,
      color: solido ? COR.fundo0 : cor,
      background: solido ? cor : "transparent",
      border: `2px solid ${cor}`,
      textTransform: "uppercase",
      whiteSpace: "nowrap",
    }}
  >
    {children}
  </span>
);

/** Título grande com a fonte da casa. */
export const Titulo: React.FC<PropsWithChildren<{ tamanho?: number; cor?: string; style?: CSSProperties }>> = ({
  children,
  tamanho = 64,
  cor = COR.tinta,
  style,
}) => (
  <div
    style={{
      fontFamily: FONTE,
      fontWeight: 700,
      fontSize: tamanho,
      lineHeight: 1.05,
      color: cor,
      letterSpacing: -1,
      textWrap: "balance",
      ...style,
    }}
  >
    {children}
  </div>
);

export const Texto: React.FC<PropsWithChildren<{ tamanho?: number; cor?: string; style?: CSSProperties }>> = ({
  children,
  tamanho = 28,
  cor = COR.tinta,
  style,
}) => (
  <div
    style={{
      fontFamily: FONTE,
      fontWeight: 500,
      fontSize: tamanho,
      lineHeight: 1.3,
      color: cor,
      textWrap: "pretty",
      ...style,
    }}
  >
    {children}
  </div>
);
