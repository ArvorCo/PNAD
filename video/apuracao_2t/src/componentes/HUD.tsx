import { AbsoluteFill, Img, staticFile } from "remotion";
import { capituloPorId, ULTIMO_CAPITULO } from "../capitulos";
import { useFormato } from "../formato";
import type { TrechoPlano } from "../plano";
import { COR, FONTE, MONO } from "../tema";
import { existePublico } from "./publico";

const Canto: React.FC<{ x: number; y: number; espelhoX: boolean; espelhoY: boolean }> = ({ x, y, espelhoX, espelhoY }) => (
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

const dois = (n: number): string => String(n).padStart(2, "0");

type Props = {
  /** Etiqueta do canto superior direito; sem ela, a do vídeo conforme o formato. */
  tag?: string;
  capitulos: TrechoPlano[];
  /** Quadro absoluto do vídeo. */
  frame: number;
};

/** Moldura fixa: cantos, marca Arvor, capítulo atual, progresso por capítulo e rodapé com a URL. */
export const HUD: React.FC<Props> = ({ tag, capitulos, frame }) => {
  const { largura, altura, vertical, margem } = useFormato();
  const m = margem * 0.45;
  const indice = Math.max(
    0,
    capitulos.findIndex((c) => frame >= c.inicio && frame < c.inicio + c.frames),
  );
  const trecho = capitulos[indice];
  const atual = trecho ? capituloPorId(trecho.id) : null;
  const total = capitulos.reduce((soma, c) => soma + c.frames, 0);
  const pisca = 0.6 + 0.4 * Math.abs(Math.sin(frame * 0.12));
  const etiqueta = tag ?? (vertical ? "2º TURNO · 25/10" : "A NOITE DO 2º TURNO · 25/10");
  const rotulo = !atual
    ? ""
    : atual.numero === 0
      ? atual.titulo.toUpperCase()
      : vertical
        ? `${dois(atual.numero)}/${dois(ULTIMO_CAPITULO)}`
        : `CAPÍTULO ${dois(atual.numero)} / ${dois(ULTIMO_CAPITULO)} · ${atual.titulo.toUpperCase()}`;

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <Canto x={m} y={m} espelhoX={false} espelhoY={false} />
      <Canto x={largura - m - 48} y={m} espelhoX espelhoY={false} />
      <Canto x={m} y={altura - m - 48} espelhoX={false} espelhoY />
      <Canto x={largura - m - 48} y={altura - m - 48} espelhoX espelhoY />

      <div style={{ position: "absolute", top: m + 10, left: m + 60, display: "flex", alignItems: "center", gap: 14 }}>
        {/* public/ fica fora do git: sem o logo, o HUD mostra só o nome, em vez de quebrar o render. */}
        {existePublico("arvor_logo.png") ? (
          <Img src={staticFile("arvor_logo.png")} style={{ width: 54, height: 54, filter: "brightness(0) invert(1)", opacity: 0.95 }} />
        ) : null}
        <div style={{ fontFamily: FONTE, color: COR.tinta, lineHeight: 1.05 }}>
          <div style={{ fontWeight: 700, fontSize: 24, letterSpacing: 2 }}>ARVOR</div>
          <div style={{ fontSize: 13, letterSpacing: 3.5, color: COR.tealClaro }}>INTELLIGENCE</div>
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
        <span style={{ color: COR.alta, opacity: pisca }}>●</span> {etiqueta}
        <div style={{ color: atual ? atual.cor : COR.tealClaro, marginTop: 2 }}>{rotulo}</div>
      </div>

      <div style={{ position: "absolute", left: m + 60, right: m + 60, top: m + 78, height: 4, display: "flex", gap: 4 }}>
        {capitulos.map((c, i) => {
          const dentro = Math.min(1, Math.max(0, (frame - c.inicio) / c.frames));
          const cor = capituloPorId(c.id).cor;
          return (
            <div key={c.id} style={{ flex: c.frames, background: COR.linha, borderRadius: 2, overflow: "hidden" }}>
              <div
                style={{
                  width: `${(i < indice ? 1 : i === indice ? dentro : 0) * 100}%`,
                  height: "100%",
                  background: cor,
                  opacity: i === indice ? 1 : 0.7,
                }}
              />
            </div>
          );
        })}
      </div>

      <div style={{ position: "absolute", bottom: m + 14, left: m + 60, fontFamily: MONO, fontSize: 17, color: COR.tealClaro, letterSpacing: 2 }}>
        brasil.arvor.co
      </div>
      <div style={{ position: "absolute", bottom: m + 14, right: m + 60, fontFamily: MONO, fontSize: 15, color: COR.suave, letterSpacing: 1.5 }}>
        {total > 0 ? Math.round((frame / total) * 100) : 0}%
      </div>
    </AbsoluteFill>
  );
};
