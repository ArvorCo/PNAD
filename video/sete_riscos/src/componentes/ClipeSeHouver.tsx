import { AbsoluteFill } from "remotion";
import { useFormato } from "../formato";
import { Clipe, type Foco } from "./Clipe";
import { ehPendente, resolverMidia } from "./fonteMidia";

type Props = {
  /** Id em `midia.json` (ou `cap_<id>`). */
  id: string;
  /** Opacidade do clipe inteiro, para o texto por cima continuar legível. */
  opacidade?: number;
  veu?: number;
  foco?: Foco[];
};

/** Diz se o clipe existe em `public/midia` no formato atual ou no outro. */
export const temClipe = (id: string, vertical: boolean): boolean =>
  !ehPendente(resolverMidia(id, vertical ? "9x16" : "16x9", "mp4"));

/**
 * Clipe de fundo em tela cheia só quando o arquivo existe. Diferente de `Clipe`, não desenha o
 * painel de mídia pendente: o fundo da casa continua e a cena se basta sem o vídeo.
 */
export const ClipeSeHouver: React.FC<Props> = ({ id, opacidade = 0.55, veu = 0.85, foco }) => {
  const { vertical } = useFormato();
  if (!temClipe(id, vertical)) {
    return null;
  }
  return (
    <AbsoluteFill style={{ opacity: opacidade }}>
      <Clipe id={id} veu={veu} foco={foco} />
    </AbsoluteFill>
  );
};
