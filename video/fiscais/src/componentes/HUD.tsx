import { AbsoluteFill, Img, staticFile, useCurrentFrame } from "remotion";
import { useFormato } from "../formato";
import { CENAS, TOTAL_FRAMES } from "../plano";
import { COR, FONTE, MONO } from "../tema";

const Canto: React.FC<{ x: number; y: number; espelhoX: boolean; espelhoY: boolean }> = ({
  x,
  y,
  espelhoX,
  espelhoY,
}) => (
  <svg
    width={48}
    height={48}
    style={{
      position: "absolute",
      left: x,
      top: y,
      transform: `scale(${espelhoX ? -1 : 1}, ${espelhoY ? -1 : 1})`,
      opacity: 0.8,
    }}
  >
    <path d="M 2 30 L 2 2 L 30 2" fill="none" stroke={COR.tealClaro} strokeWidth={3} />
  </svg>
);

/** Moldura fixa: cantos, marca Arvor, progresso por cena e rodapé com a URL. */
export const HUD: React.FC = () => {
  const frame = useCurrentFrame();
  const { largura, altura, vertical, margem } = useFormato();
  const m = margem * 0.45;
  const atual = CENAS.findIndex((c) => frame >= c.inicio && frame < c.inicio + c.frames);
  const progresso = frame / TOTAL_FRAMES;
  const pisca = 0.6 + 0.4 * Math.abs(Math.sin(frame * 0.12));

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <Canto x={m} y={m} espelhoX={false} espelhoY={false} />
      <Canto x={largura - m - 48} y={m} espelhoX espelhoY={false} />
      <Canto x={m} y={altura - m - 48} espelhoX={false} espelhoY />
      <Canto x={largura - m - 48} y={altura - m - 48} espelhoX espelhoY />

      <div
        style={{
          position: "absolute",
          top: m + 10,
          left: m + 60,
          display: "flex",
          alignItems: "center",
          gap: 14,
        }}
      >
        <Img
          src={staticFile("arvor_logo.png")}
          style={{
            width: 54,
            height: 54,
            filter: "brightness(0) invert(1)",
            opacity: 0.95,
          }}
        />
        <div style={{ fontFamily: FONTE, color: COR.tinta, lineHeight: 1.05 }}>
          <div style={{ fontWeight: 700, fontSize: 24, letterSpacing: 2 }}>ARVOR</div>
          <div style={{ fontSize: 13, letterSpacing: 3.5, color: COR.tealClaro }}>
            INTELLIGENCE
          </div>
        </div>
      </div>

      <div
        style={{
          position: "absolute",
          top: m + 24,
          right: m + 60,
          fontFamily: MONO,
          fontSize: 16,
          color: COR.suave,
          letterSpacing: 2,
          textAlign: "right",
        }}
      >
        <span style={{ color: COR.alta, opacity: pisca }}>●</span>{" "}
        {vertical ? "2º TURNO · 25/10" : "FISCALIZAÇÃO DO 2º TURNO · 25/10/2026"}
        <div style={{ color: COR.tealClaro, marginTop: 2 }}>
          FASE {String(atual + 1).padStart(2, "0")} / {String(CENAS.length).padStart(2, "0")}
        </div>
      </div>

      <div
        style={{
          position: "absolute",
          left: m + 60,
          right: m + 60,
          top: m + 78,
          height: 4,
          display: "flex",
          gap: 3,
        }}
      >
        {CENAS.map((c, i) => {
          const dentro = Math.min(
            1,
            Math.max(0, (frame - c.inicio) / c.frames),
          );
          return (
            <div
              key={c.id}
              style={{
                flex: c.frames,
                background: COR.linha,
                borderRadius: 2,
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  width: `${(i < atual ? 1 : i === atual ? dentro : 0) * 100}%`,
                  height: "100%",
                  background: i === atual ? COR.tealClaro : COR.teal,
                }}
              />
            </div>
          );
        })}
      </div>

      <div
        style={{
          position: "absolute",
          bottom: m + 14,
          left: m + 60,
          fontFamily: MONO,
          fontSize: 17,
          color: COR.tealClaro,
          letterSpacing: 2,
        }}
      >
        brasil.arvor.co
      </div>
      <div
        style={{
          position: "absolute",
          bottom: m + 14,
          right: m + 60,
          fontFamily: MONO,
          fontSize: 15,
          color: COR.suave,
          letterSpacing: 1.5,
        }}
      >
        {Math.round(progresso * 100)}%
      </div>
    </AbsoluteFill>
  );
};
