import { useMemo } from "react";
import { AbsoluteFill, Audio, Sequence, staticFile, useCurrentFrame } from "remotion";
import { definicaoDe } from "./cenas/registro";
import { Fundo } from "./componentes/Fundo";
import { HUD } from "./componentes/HUD";
import { Legenda } from "./componentes/Legenda";
import { existePublico } from "./componentes/publico";
import { Trilha } from "./componentes/Trilha";
import { rampa } from "./componentes/util";
import { DADOS } from "./dados";
import { FormatoProvider, formatoDe } from "./formato";
import { CAPITULOS_PLANO, CENAS, resolverGatilhos, type Cena } from "./plano";
import { COR, MONO } from "./tema";

const arquivoSfx = (nome: string): string => `sfx/${nome.endsWith(".mp3") ? nome : `${nome}.mp3`}`;

/** Componente registrado da cena, com gatilhos resolvidos e os efeitos que ela declara. */
const Conteudo: React.FC<{ cena: Cena }> = ({ cena }) => {
  const def = definicaoDe(cena.id);
  const g = useMemo(() => resolverGatilhos(cena.palavras, def.gatilhos), [cena.palavras, def.gatilhos]);
  const Componente = def.componente;
  return (
    <>
      {(def.sfx ?? []).map((s) => {
        if (s.gatilho !== undefined && !(s.gatilho in g)) {
          throw new Error(`cena ${cena.id}: efeito ${s.arquivo} aponta para o gatilho inexistente "${s.gatilho}"`);
        }
        const arquivo = arquivoSfx(s.arquivo);
        const volume = s.volume ?? 0.35;
        return existePublico(arquivo) ? (
          <Sequence key={`${s.arquivo}-${s.gatilho ?? "inicio"}`} from={s.gatilho ? g[s.gatilho] : 0} durationInFrames={90} layout="none">
            <Audio src={staticFile(arquivo)} volume={() => volume} />
          </Sequence>
        ) : null;
      })}
      <Componente cena={cena} dados={DADOS} g={g} />
    </>
  );
};

/** Entrada e saída de cada cena: fade curto, com leve zoom na entrada. */
const Transicao: React.FC<{ frames: number; children: React.ReactNode }> = ({ frames, children }) => {
  const frame = useCurrentFrame();
  const entra = rampa(frame, 0, 12);
  const sai = 1 - rampa(frame, frames - 12, frames);
  return <AbsoluteFill style={{ opacity: entra * sai, transform: `scale(${1.02 - 0.02 * entra})` }}>{children}</AbsoluteFill>;
};

/** Aviso visível quando o manifesto tem a voz da cena e o arquivo não está em public/voz. */
const VozAusente: React.FC<{ arquivo: string }> = ({ arquivo }) => (
  <div
    style={{
      position: "absolute",
      left: "50%",
      top: 150,
      transform: "translateX(-50%)",
      padding: "8px 18px",
      borderRadius: 10,
      background: COR.alta,
      color: COR.fundo0,
      fontFamily: MONO,
      fontWeight: 700,
      fontSize: 18,
      letterSpacing: 2,
    }}
  >
    VOZ AUSENTE: {arquivo}
  </div>
);

export const Video: React.FC<{ largura: number; altura: number }> = ({ largura, altura }) => {
  const frame = useCurrentFrame();
  const formato = useMemo(() => formatoDe(largura, altura), [largura, altura]);
  const whoosh = existePublico("sfx/whoosh.mp3");
  return (
    <FormatoProvider value={formato}>
      <AbsoluteFill style={{ background: COR.fundo0 }}>
        <Fundo />
        <Trilha />
        {CENAS.map((cena) => {
          const vozPresente = cena.comVoz && existePublico(cena.arquivo);
          return (
            <Sequence key={cena.id} from={cena.inicio} durationInFrames={cena.frames} name={cena.id}>
              {vozPresente ? <Audio src={staticFile(cena.arquivo)} /> : null}
              {whoosh ? <Audio src={staticFile("sfx/whoosh.mp3")} volume={() => (cena.id.startsWith("cap-") ? 0.34 : 0.22)} /> : null}
              <Transicao frames={cena.frames}>
                <Conteudo cena={cena} />
              </Transicao>
              <Legenda palavras={cena.palavras} />
              {cena.comVoz && !vozPresente ? <VozAusente arquivo={cena.arquivo} /> : null}
            </Sequence>
          );
        })}
        <HUD capitulos={CAPITULOS_PLANO} frame={frame} />
      </AbsoluteFill>
    </FormatoProvider>
  );
};
