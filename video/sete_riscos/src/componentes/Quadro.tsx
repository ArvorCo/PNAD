import type { CSSProperties, PropsWithChildren } from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { useFormato } from "../formato";
import { COR, FONTE } from "../tema";
import { mola, rampa } from "./util";

/** Topo da área útil das cenas com mídia: logo abaixo da barra de progresso do HUD. */
const TOPO = 150;

export type AreaUtil = { esquerda: number; topo: number; largura: number; altura: number };

/**
 * Retângulo útil das cenas dos capítulos 3 a 6, em px do formato atual: começa logo abaixo da
 * barra de progresso do HUD e termina onde o `Palco` termina (230 px acima do pé no 16:9, acima
 * dos 16% da legenda mais 120 px no 9:16). Nada de conteúdo desce além disso.
 */
export const useArea = (): AreaUtil => {
  const { vertical, largura, altura, margem } = useFormato();
  const base = vertical ? altura * 0.16 + 120 : 230;
  return { esquerda: margem, topo: TOPO, largura: largura - 2 * margem, altura: altura - TOPO - base };
};

/** Coluna absoluta sobre o retângulo de `useArea`. */
export const Area: React.FC<PropsWithChildren<{ style?: CSSProperties }>> = ({ children, style }) => {
  const a = useArea();
  return (
    <div
      style={{
        position: "absolute",
        left: a.esquerda,
        top: a.topo,
        width: a.largura,
        height: a.altura,
        display: "flex",
        flexDirection: "column",
        ...style,
      }}
    >
      {children}
    </div>
  );
};

/** Mostra os filhos de `de` até `ate` (quadros da cena), com esmaecimento na entrada e na saída. */
export const Fase: React.FC<PropsWithChildren<{ de: number; ate?: number; fade?: number; style?: CSSProperties }>> = ({
  de,
  ate,
  fade = 10,
  style,
  children,
}) => {
  const frame = useCurrentFrame();
  if (frame < de || (ate !== undefined && frame >= ate)) {
    return null;
  }
  const entra = rampa(frame, de, de + fade);
  const sai = ate === undefined ? 1 : 1 - rampa(frame, ate - fade, ate);
  return <div style={{ opacity: entra * sai, ...style }}>{children}</div>;
};

/**
 * Como `Entrada`, mas ocupa o lugar desde o primeiro quadro (invisível antes de `inicio`), para o
 * layout não pular quando o elemento aparece.
 */
export const Surge: React.FC<PropsWithChildren<{ inicio: number; de?: "baixo" | "esquerda" | "direita" | "zoom"; style?: CSSProperties }>> = ({
  inicio,
  de = "baixo",
  style,
  children,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = mola(frame, fps, inicio);
  const o = frame < inicio ? 0 : rampa(frame, inicio, inicio + 10);
  const d = 40 * (1 - p);
  const transform =
    de === "baixo" ? `translateY(${d}px)` : de === "esquerda" ? `translateX(${-d}px)` : de === "direita" ? `translateX(${d}px)` : `scale(${0.8 + 0.2 * p})`;
  return <div style={{ opacity: o, transform, ...style }}>{children}</div>;
};

/** Etiqueta que quebra linha (o `Chip` não quebra): para motivos e frases curtas. */
export const Etiqueta: React.FC<PropsWithChildren<{ cor?: string; solido?: boolean; tamanho?: number; style?: CSSProperties }>> = ({
  cor = COR.tealClaro,
  solido = false,
  tamanho = 22,
  style,
  children,
}) => {
  const { escala, vertical } = useFormato();
  // No 9:16 a tela é vista no celular: a etiqueta cresce 25% para continuar legível.
  const k = vertical ? 1.25 : 1;
  return (
    <div
      style={{
        display: "inline-block",
        fontFamily: FONTE,
        fontWeight: 700,
        fontSize: tamanho * escala * k,
        lineHeight: 1.2,
        padding: `${7 * escala}px ${14 * escala}px`,
        borderRadius: 10,
        color: solido ? COR.fundo0 : COR.tinta,
        background: solido ? cor : "rgba(6,11,26,0.72)",
        border: `2px solid ${cor}`,
        ...style,
      }}
    >
      {children}
    </div>
  );
};
