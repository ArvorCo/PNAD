import { Audio, Sequence, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { CAPITULOS, capituloDe } from "../capitulos";
import type { CenaProps } from "../cenas/registro";
import { useFormato } from "../formato";
import { COR, MONO } from "../tema";
import { Chip, Entrada, Titulo } from "./Caixa";
import { Palco } from "./Palco";
import { existePublico } from "./publico";
import { mola, rampa, suave } from "./util";

const dois = (n: number): string => String(n).padStart(2, "0");

/**
 * Cartão de capítulo (cenas `cap-*`): número grande na cor do capítulo, título, barra que se
 * desenha e a trilha dos capítulos com o atual aceso. Gatilhos opcionais: `numero`, `titulo`.
 */
export const CartaoCapitulo: React.FC<CenaProps> = ({ cena, g }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { vertical, t } = useFormato();
  const capitulo = capituloDe(cena.id);
  const qNumero = g.numero ?? 0;
  const qTitulo = g.titulo ?? 10;
  const numero = mola(frame, fps, qNumero, { damping: 15 });
  const barra = suave(rampa(frame, qNumero + 4, qNumero + 34));
  const trilha = CAPITULOS.filter((c) => c.numero > 0);

  return (
    <Palco style={{ justifyContent: "center", alignItems: vertical ? "center" : "flex-start" }}>
      {existePublico("sfx/chime.mp3") ? (
        <Sequence from={qNumero} durationInFrames={60} layout="none">
          <Audio src={staticFile("sfx/chime.mp3")} volume={0.32} />
        </Sequence>
      ) : null}
      <div style={{ display: "flex", flexDirection: vertical ? "column" : "row", alignItems: vertical ? "center" : "flex-end", gap: t(48) }}>
        <div
          style={{
            fontFamily: MONO,
            fontWeight: 700,
            fontSize: t(vertical ? 260 : 300),
            lineHeight: 0.82,
            letterSpacing: -12,
            color: capitulo.cor,
            opacity: Math.min(1, numero * 1.3),
            transform: `translateY(${(1 - numero) * 60}px)`,
            textShadow: `0 0 60px ${capitulo.cor}55`,
          }}
        >
          {dois(capitulo.numero)}
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: t(18), alignItems: vertical ? "center" : "flex-start", textAlign: vertical ? "center" : "left" }}>
          <Entrada inicio={qNumero + 4} de="esquerda">
            <Chip cor={capitulo.cor} tamanho={22}>
              capítulo {capitulo.numero} de {trilha.length}
            </Chip>
          </Entrada>
          <Entrada inicio={qTitulo} de="baixo">
            <Titulo tamanho={vertical ? 76 : 92}>{capitulo.titulo}</Titulo>
          </Entrada>
        </div>
      </div>
      <div style={{ marginTop: t(44), width: vertical ? "100%" : "70%", height: 6, background: COR.linha, borderRadius: 3, overflow: "hidden" }}>
        <div style={{ width: `${barra * 100}%`, height: "100%", background: capitulo.cor, boxShadow: `0 0 24px ${capitulo.cor}` }} />
      </div>
      <div style={{ display: "flex", gap: t(14), marginTop: t(30), flexWrap: "wrap", justifyContent: vertical ? "center" : "flex-start" }}>
        {trilha.map((c, i) => {
          const aceso = c.id === capitulo.id;
          const passado = c.numero < capitulo.numero;
          return (
            <Entrada key={c.id} inicio={qTitulo + 6 + i * 3} de="baixo">
              <div
                style={{
                  fontFamily: MONO,
                  fontSize: t(16),
                  letterSpacing: 2,
                  padding: `${t(6)}px ${t(12)}px`,
                  borderRadius: 8,
                  border: `2px solid ${aceso || passado ? c.cor : COR.linha}`,
                  background: aceso ? c.cor : "transparent",
                  color: aceso ? COR.fundo0 : passado ? c.cor : COR.suave,
                  opacity: aceso ? 1 : passado ? 0.75 : 0.55,
                  whiteSpace: "nowrap",
                }}
              >
                {dois(c.numero)}
                {vertical ? "" : ` ${c.titulo.toUpperCase()}`}
              </div>
            </Entrada>
          );
        })}
      </div>
    </Palco>
  );
};
