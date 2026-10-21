import { AbsoluteFill } from "remotion";
import type { CenaProps } from "../cenas/registro";
import { useFormato } from "../formato";
import { CartaoCapitulo } from "./CartaoCapitulo";
import { ClipeSeHouver, temClipe } from "./ClipeSeHouver";
import { ehPendente, resolverMidia } from "./fonteMidia";
import { Still } from "./Still";

type Fundo = {
  /** Clipe preferido (`midia.json`), usado só quando o arquivo existe. */
  clipe?: string;
  /** Still de reserva (`midia.json`), com Ken Burns lento. */
  still?: string;
  opacidade?: number;
};

/**
 * Cartão de capítulo dos capítulos 3 a 5 com uma imagem atenuada atrás: o clipe quando existe,
 * senão o still; sem nenhum dos dois, fica só o fundo da casa (o cartão se basta).
 */
export const capituloComFundo = ({ clipe, still, opacidade = 0.34 }: Fundo): React.FC<CenaProps> => {
  const CapituloComFundo: React.FC<CenaProps> = (props) => {
    const { vertical } = useFormato();
    const usaClipe = clipe !== undefined && temClipe(clipe, vertical);
    const usaStill = !usaClipe && still !== undefined && !ehPendente(resolverMidia(still, vertical ? "9x16" : "16x9", "png"));
    return (
      <>
        {usaClipe ? <ClipeSeHouver id={clipe} opacidade={opacidade} veu={0.9} /> : null}
        {usaStill ? (
          <AbsoluteFill style={{ opacity: opacidade }}>
            <Still id={still} de={1.02} ate={1.1} veu={0.9} />
          </AbsoluteFill>
        ) : null}
        <CartaoCapitulo {...props} />
      </>
    );
  };
  return CapituloComFundo;
};
