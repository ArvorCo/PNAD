import type { CSSProperties } from "react";
import { Easing, Freeze, interpolate, Loop, OffthreadVideo, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { useFormato } from "../formato";
import { ehPendente, resolverMidia } from "./fonteMidia";
import { MidiaAusente } from "./MidiaAusente";

/** Ponto de zoom: em `quadro`, a imagem está ampliada `escala` vezes em torno de (x, y), frações de 0 a 1. */
export type Foco = { quadro: number; x: number; y: number; escala: number };

type Props = {
  /** Id em `midia.json`, ou `cap_<id>` para uma captura de `capturas.json`. */
  id: string;
  /** Quando a cena dura mais que o clipe: congela no último quadro ou repete. */
  fim?: "congelar" | "repetir";
  /** Keyframes de zoom (transform-origin e escala interpolados). */
  foco?: Foco[];
  /** Véu escuro em gradiente para texto por cima: `true` ou intensidade de 0 a 1. */
  veu?: boolean | number;
  /** Segundos a pular no começo do clipe. */
  inicio?: number;
  style?: CSSProperties;
};

const ESTILO_VIDEO: CSSProperties = { width: "100%", height: "100%", objectFit: "cover" };

/** Transformação de zoom no quadro atual a partir dos keyframes. */
export const transformarFoco = (foco: Foco[], frame: number): CSSProperties => {
  if (!foco.length) {
    return {};
  }
  const ordenado = [...foco].sort((a, b) => a.quadro - b.quadro);
  const valor = (campo: "x" | "y" | "escala"): number =>
    ordenado.length === 1
      ? ordenado[0][campo]
      : interpolate(
          frame,
          ordenado.map((k) => k.quadro),
          ordenado.map((k) => k[campo]),
          { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) },
        );
  return { transform: `scale(${valor("escala")})`, transformOrigin: `${valor("x") * 100}% ${valor("y") * 100}%` };
};

export const Veu: React.FC<{ intensidade: number }> = ({ intensidade: a }) => (
  <div
    style={{
      position: "absolute",
      inset: 0,
      background: `linear-gradient(180deg, rgba(6,11,26,${0.6 * a}) 0%, rgba(6,11,26,${0.15 * a}) 38%, rgba(6,11,26,${0.25 * a}) 62%, rgba(6,11,26,${0.88 * a}) 100%)`,
    }}
  />
);

/**
 * Clipe de vídeo mudo em tela cheia do contêiner (`objectFit: cover`), no formato do vídeo ou
 * recortado ao centro do outro. Mídia ausente vira um painel com o id, nunca uma quebra.
 */
export const Clipe: React.FC<Props> = ({ id, fim = "congelar", foco = [], veu = false, inicio = 0, style }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { vertical } = useFormato();
  const fonte = resolverMidia(id, vertical ? "9x16" : "16x9", "mp4");
  const intensidade = veu === true ? 1 : veu === false ? 0 : veu;

  if (ehPendente(fonte)) {
    return (
      <div style={{ position: "relative", width: "100%", height: "100%", ...style }}>
        <MidiaAusente motivo={fonte.pendente} />
      </div>
    );
  }

  const pulo = Math.round(inicio * fps);
  const duracao = Math.max(2, Math.floor(fonte.segundos * fps) - pulo);
  const video = <OffthreadVideo src={staticFile(fonte.arquivo)} muted trimBefore={pulo || undefined} style={ESTILO_VIDEO} />;

  return (
    <div style={{ position: "relative", width: "100%", height: "100%", overflow: "hidden", ...style }}>
      <div style={{ position: "absolute", inset: 0, ...transformarFoco(foco, frame) }}>
        {fim === "repetir" ? (
          <Loop durationInFrames={duracao}>{video}</Loop>
        ) : (
          <Freeze frame={duracao - 2} active={(f) => f >= duracao - 2}>
            {video}
          </Freeze>
        )}
      </div>
      {intensidade > 0 ? <Veu intensidade={intensidade} /> : null}
    </div>
  );
};
