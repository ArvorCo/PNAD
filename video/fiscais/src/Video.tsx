import { AbsoluteFill, Audio, Sequence, interpolate, staticFile, useCurrentFrame } from "remotion";
import { Abertura } from "./cenas/Abertura";
import { Acao1, Acao2 } from "./cenas/Acoes";
import { CriterioCena } from "./cenas/Criterio";
import { Fecho } from "./cenas/Fecho";
import { MapaCena } from "./cenas/MapaCena";
import { Niveis } from "./cenas/Niveis";
import { Pergunta } from "./cenas/Pergunta";
import { Quantos } from "./cenas/Quantos";
import { Fundo } from "./componentes/Fundo";
import { HUD } from "./componentes/HUD";
import { Legenda } from "./componentes/Legenda";
import { rampa } from "./componentes/util";
import dadosJson from "./dados/dados.json";
import { FormatoProvider, formatoDe } from "./formato";
import { CENAS, TOTAL_FRAMES, type Cena } from "./plano";
import type { Dados } from "./tipos";

const DADOS = dadosJson as unknown as Dados;
const VOLUME_TRILHA = 0.22;

const Conteudo: React.FC<{ cena: Cena }> = ({ cena }) => {
  if (cena.id.startsWith("c-")) {
    const letra = cena.id.slice(2);
    const indice = DADOS.criterios.findIndex((c) => c.id === letra);
    return <CriterioCena criterio={DADOS.criterios[indice]} indice={indice + 1} cena={cena} dados={DADOS} />;
  }
  switch (cena.id) {
    case "abertura":
      return <Abertura cena={cena} dados={DADOS} />;
    case "pergunta":
      return <Pergunta cena={cena} dados={DADOS} />;
    case "niveis":
      return <Niveis cena={cena} dados={DADOS} />;
    case "mapa":
      return <MapaCena cena={cena} dados={DADOS} />;
    case "quantos":
      return <Quantos cena={cena} dados={DADOS} />;
    case "acao1":
      return <Acao1 cena={cena} />;
    case "acao2":
      return <Acao2 cena={cena} />;
    default:
      return <Fecho cena={cena} />;
  }
};

/** Entrada e saída de cada cena: fade curto, com leve zoom na entrada. */
const Transicao: React.FC<{ frames: number; children: React.ReactNode }> = ({ frames, children }) => {
  const frame = useCurrentFrame();
  const entra = rampa(frame, 0, 12);
  const sai = 1 - rampa(frame, frames - 12, frames);
  return (
    <AbsoluteFill style={{ opacity: entra * sai, transform: `scale(${1.02 - 0.02 * entra})` }}>{children}</AbsoluteFill>
  );
};

export const Video: React.FC<{ largura: number; altura: number }> = ({ largura, altura }) => {
  return (
    <FormatoProvider value={formatoDe(largura, altura)}>
      <AbsoluteFill style={{ background: "#060b1a" }}>
        <Fundo />
        <Audio
          src={staticFile("sfx/trilha_loop.mp3")}
          loop
          volume={(f) =>
            interpolate(f, [0, 60, TOTAL_FRAMES - 120, TOTAL_FRAMES], [0, VOLUME_TRILHA, VOLUME_TRILHA, 0], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            })
          }
        />
        {CENAS.map((cena) => (
          <Sequence key={cena.id} from={cena.inicio} durationInFrames={cena.frames} name={cena.id}>
            <Audio src={staticFile(cena.arquivo)} />
            <Audio src={staticFile("sfx/whoosh.mp3")} volume={0.28} />
            <Transicao frames={cena.frames}>
              <Conteudo cena={cena} />
            </Transicao>
            <Legenda palavras={cena.palavras} />
          </Sequence>
        ))}
        <HUD />
      </AbsoluteFill>
    </FormatoProvider>
  );
};
