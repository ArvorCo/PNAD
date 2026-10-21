import type { CSSProperties } from "react";
import { Img, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { useFormato } from "../formato";
import { Veu } from "./Clipe";
import { ehPendente, resolverMidia } from "./fonteMidia";
import { MidiaAusente } from "./MidiaAusente";

type Props = {
  /** Id de imagem em `midia.json`, ou `cap_<id>` com `nome` para um still de captura. */
  id: string;
  nome?: string;
  /** Escala no início e no fim do movimento. */
  de?: number;
  ate?: number;
  /** Deslocamento total em px de referência ao longo do movimento. */
  pan?: [number, number];
  /** Duração do movimento em quadros; falta = duração da cena (Sequence) em curso. */
  duracao?: number;
  veu?: boolean | number;
  style?: CSSProperties;
};

/** Imagem com Ken Burns lento (escala 1 a 1,08 e deslocamento), recorte central se o formato faltar. */
export const Still: React.FC<Props> = ({ id, nome, de = 1, ate = 1.08, pan = [0, 0], duracao, veu = false, style }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const { vertical, escala: k } = useFormato();
  const fonte = resolverMidia(id, vertical ? "9x16" : "16x9", "png", nome);
  const intensidade = veu === true ? 1 : veu === false ? 0 : veu;

  if (ehPendente(fonte)) {
    return (
      <div style={{ position: "relative", width: "100%", height: "100%", ...style }}>
        <MidiaAusente motivo={fonte.pendente} />
      </div>
    );
  }

  const p = interpolate(frame, [0, Math.max(1, duracao ?? durationInFrames)], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const escalaAtual = de + (ate - de) * p;
  return (
    <div style={{ position: "relative", width: "100%", height: "100%", overflow: "hidden", ...style }}>
      <Img
        src={staticFile(fonte.arquivo)}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transform: `translate(${pan[0] * k * p}px, ${pan[1] * k * p}px) scale(${escalaAtual})`,
        }}
      />
      {intensidade > 0 ? <Veu intensidade={intensidade} /> : null}
    </div>
  );
};
