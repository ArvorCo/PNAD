import { Img, staticFile, useCurrentFrame } from "remotion";
import { useFormato } from "../formato";
import { COR, MONO } from "../tema";
import { Clipe, transformarFoco, type Foco } from "./Clipe";
import { ehPendente, resolverMidia } from "./fonteMidia";
import { MidiaAusente } from "./MidiaAusente";
import { rampa } from "./util";

type Props = {
  /** Id `cap_<id>` de uma captura (tela do telão ou página) em `capturas.json`. */
  id: string;
  /** Nome do still dentro da captura, quando houver. */
  nome?: string;
  /** Keyframes de zoom em quadros da cena. */
  foco?: Foco[];
  /** Gravação em vídeo (`cap_<id>` com mp4) no lugar de um quadro parado. */
  video?: boolean;
  /** Endereço mostrado na barra da moldura; sem ele, só a moldura. */
  endereco?: string;
};

/**
 * Captura de tela em moldura 16:9 com zoom por keyframes. A moldura mantém a proporção original
 * nos dois formatos (no 9:16 ocupa a largura e deixa o resto livre para o texto), então o
 * telão nunca é recortado ao centro.
 */
export const Zoom: React.FC<Props> = ({ id, nome, foco = [], video = false, endereco }) => {
  const frame = useCurrentFrame();
  const { vertical, t } = useFormato();
  const fonte = resolverMidia(id, "16x9", video ? "mp4" : "png", nome);
  const entra = rampa(frame, 0, 14);
  return (
    <div
      style={{
        width: "100%",
        aspectRatio: "16 / 9",
        maxHeight: "100%",
        position: "relative",
        overflow: "hidden",
        borderRadius: t(16),
        border: `2px solid ${COR.tealClaro}`,
        background: COR.fundo1,
        opacity: entra,
        boxShadow: "0 24px 70px rgba(0,0,0,0.45)",
        alignSelf: vertical ? "stretch" : "center",
      }}
    >
      {ehPendente(fonte) ? (
        <MidiaAusente motivo={fonte.pendente} />
      ) : video ? (
        <Clipe id={id} foco={foco} />
      ) : (
        <div style={{ position: "absolute", inset: 0, ...transformarFoco(foco, frame) }}>
          <Img src={staticFile(fonte.arquivo)} style={{ width: "100%", height: "100%", objectFit: "contain" }} />
        </div>
      )}
      {endereco ? (
        <div style={{ position: "absolute", left: t(14), top: t(10), fontFamily: MONO, fontSize: t(15), color: COR.tealClaro, background: "rgba(6,11,26,0.78)", padding: `${t(3)}px ${t(10)}px`, borderRadius: 6 }}>
          {endereco}
        </div>
      ) : null}
    </div>
  );
};
