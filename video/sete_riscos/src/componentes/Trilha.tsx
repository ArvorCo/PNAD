import { Audio, interpolate, Sequence, staticFile } from "remotion";
import { MUSICA } from "../dados";
import { CAPITULOS_PLANO, FPS, NARRANDO_SUAVE, TOTAL_FRAMES } from "../plano";
import { existePublico } from "./publico";

/** Volume da trilha no silêncio e sob a narração (ducking). */
const VOLUME_SILENCIO = 0.22;
const VOLUME_NARRACAO = 0.1;
/** Pré-rolagem e cross-fade entre capítulos, em quadros. */
const CRUZAMENTO = 2 * FPS;
const SAIDA_FINAL = 3 * FPS;

const opcoes = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

/**
 * Uma faixa por capítulo (`musica.json`): entra 2 s antes do capítulo em fade-in, sai em fade-out
 * nos 2 s finais (cruzando com a seguinte) e abaixa sob a fala pelo vetor `NARRANDO` suavizado.
 * Capítulo sem faixa, ou com arquivo ausente, fica sem música.
 */
export const Trilha: React.FC = () => (
  <>
    {CAPITULOS_PLANO.map((cap, i) => {
      const faixa = MUSICA[cap.id];
      const arquivo = faixa
        ? [faixa.arquivo.replace(/^(\.\/)?public\//, ""), `musica/${cap.id}.mp3`].find(existePublico)
        : undefined;
      if (!faixa || !arquivo) {
        return null;
      }
      const ultimo = i === CAPITULOS_PLANO.length - 1;
      const de = Math.max(0, cap.inicio - CRUZAMENTO);
      const ate = Math.min(TOTAL_FRAMES, cap.inicio + cap.frames);
      const frames = Math.min(ate - de, Math.floor(faixa.segundos * FPS));
      if (frames <= 0) {
        return null;
      }
      const entrada = Math.min(CRUZAMENTO, frames / 2);
      const saida = Math.min(ultimo ? SAIDA_FINAL : CRUZAMENTO, frames / 2);
      const volume = (f: number): number => {
        const fadeIn = interpolate(f, [0, entrada], [0, 1], opcoes);
        const fadeOut = interpolate(f, [frames - saida, frames], [1, 0], opcoes);
        const fala = NARRANDO_SUAVE[Math.min(TOTAL_FRAMES - 1, de + f)] ?? 0;
        return fadeIn * fadeOut * (VOLUME_SILENCIO + (VOLUME_NARRACAO - VOLUME_SILENCIO) * fala);
      };
      return (
        <Sequence key={cap.id} from={de} durationInFrames={frames} name={`trilha ${cap.id}`} layout="none">
          <Audio src={staticFile(arquivo)} volume={volume} />
        </Sequence>
      );
    })}
  </>
);
