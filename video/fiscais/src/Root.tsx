import { Composition } from "remotion";
import { FPS, TOTAL_FRAMES } from "./plano";
import { Video } from "./Video";

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="FiscaisWide"
      component={Video}
      durationInFrames={TOTAL_FRAMES}
      fps={FPS}
      width={1920}
      height={1080}
      defaultProps={{ largura: 1920, altura: 1080 }}
    />
    <Composition
      id="FiscaisVertical"
      component={Video}
      durationInFrames={TOTAL_FRAMES}
      fps={FPS}
      width={1080}
      height={1920}
      defaultProps={{ largura: 1080, altura: 1920 }}
    />
  </>
);
