import { Easing, interpolate, useCurrentFrame } from "remotion";
import { useFormato } from "../formato";
import { COR } from "../tema";

/** Posição do cursor em frações (0 a 1) do contêiner; `clique` dispara um anel no quadro. */
export type PassoCursor = { quadro: number; x: number; y: number; clique?: boolean };

const DURACAO_CLIQUE = 18;

/** Seta de mouse em SVG que percorre os keyframes, com anel no clique. Fica acima da mídia. */
export const Cursor: React.FC<{ passos: PassoCursor[]; tamanho?: number }> = ({ passos, tamanho = 44 }) => {
  const frame = useCurrentFrame();
  const { t } = useFormato();
  if (!passos.length) {
    return null;
  }
  const ordenado = [...passos].sort((a, b) => a.quadro - b.quadro);
  const opcoes = { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.quad) } as const;
  const valor = (campo: "x" | "y"): number =>
    ordenado.length === 1
      ? ordenado[0][campo]
      : interpolate(
          frame,
          ordenado.map((p) => p.quadro),
          ordenado.map((p) => p[campo]),
          opcoes,
        );
  const clique = ordenado.find((p) => p.clique && frame >= p.quadro && frame < p.quadro + DURACAO_CLIQUE);
  const fase = clique ? (frame - clique.quadro) / DURACAO_CLIQUE : 0;
  const lado = t(tamanho);
  return (
    <div style={{ position: "absolute", inset: 0, pointerEvents: "none" }}>
      <div style={{ position: "absolute", left: `${valor("x") * 100}%`, top: `${valor("y") * 100}%` }}>
        {clique ? (
          <div
            style={{
              position: "absolute",
              left: -lado * fase,
              top: -lado * fase,
              width: 2 * lado * fase,
              height: 2 * lado * fase,
              borderRadius: "50%",
              border: `3px solid ${COR.tealClaro}`,
              opacity: 1 - fase,
            }}
          />
        ) : null}
        <svg width={lado} height={lado} viewBox="0 0 24 24" style={{ position: "absolute", left: 0, top: 0, transform: `scale(${clique ? 1 - 0.12 * Math.sin(Math.PI * fase) : 1})`, transformOrigin: "0 0", filter: "drop-shadow(0 4px 8px rgba(0,0,0,0.55))" }}>
          <path d="M2 1 L2 19 L7 14.5 L10.5 22 L13.5 20.6 L10 13.3 L16.5 13.3 Z" fill="#ffffff" stroke={COR.fundo0} strokeWidth={1.4} strokeLinejoin="round" />
        </svg>
      </div>
    </div>
  );
};
