import { Composition } from "remotion";
import { DURACAO_E, Encerramento, FPS_E } from "./Encerramento";
import { DURACAO, FPS, Vinheta } from "./Vinheta";

export const RemotionRoot: React.FC = () => (
  <>
    <Composition id="Vinheta" component={Vinheta} durationInFrames={DURACAO} fps={FPS} width={1920} height={1080} />
    <Composition
      id="Encerramento"
      component={Encerramento}
      durationInFrames={DURACAO_E}
      fps={FPS_E}
      width={1920}
      height={1080}
    />
  </>
);
