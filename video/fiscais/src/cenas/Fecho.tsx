import { AbsoluteFill, Img, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Caixa, Chip, Entrada, Texto, Titulo } from "../componentes/Caixa";
import { mola, rampa } from "../componentes/util";
import { useFormato } from "../formato";
import { quadro, type Cena } from "../plano";
import { COR, FONTE, MONO } from "../tema";

/** Fecho: as duas ações, os dois links, a marca e a última frase. */
export const Fecho: React.FC<{ cena: Cena }> = ({ cena }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { vertical, margem } = useFormato();
  const p = cena.palavras;
  const q1 = quadro(p, "Fiscal", 0.5);
  const q2 = quadro(p, "Conversa", 2);
  const qDados = quadro(p, "dados", 9);
  const qArvor = quadro(p, "Arvor", 15);
  const qDia = quadro(p, "Dia", 18);
  const marca = mola(frame, fps, qArvor, { damping: 16 });
  const escurece = rampa(frame, qDia - 6, qDia + 10);

  return (
    <AbsoluteFill style={{ padding: `${vertical ? 180 : 160}px ${margem}px`, justifyContent: "center", gap: 26 }}>
      <div style={{ display: "flex", flexDirection: vertical ? "column" : "row", gap: 24, opacity: 1 - escurece * 0.85 }}>
        <Entrada inicio={q1} de="esquerda" style={{ flex: 1 }}>
          <Caixa cor={COR.alta} style={{ height: "100%" }}>
            <Chip cor={COR.alta} solido tamanho={18}>ação 1</Chip>
            <Titulo tamanho={vertical ? 44 : 52} style={{ marginTop: 14 }}>Fiscal na sala</Titulo>
            <Entrada inicio={qDados} de="baixo">
              <div style={{ fontFamily: MONO, fontWeight: 700, fontSize: vertical ? 30 : 34, color: COR.tinta, marginTop: 16 }}>fiscaisdopl.com.br</div>
            </Entrada>
          </Caixa>
        </Entrada>
        <Entrada inicio={q2} de="direita" style={{ flex: 1 }}>
          <Caixa cor={COR.outros} style={{ height: "100%" }}>
            <Chip cor={COR.outros} solido tamanho={18}>ação 2</Chip>
            <Titulo tamanho={vertical ? 44 : 52} style={{ marginTop: 14 }}>Conversa na vizinhança</Titulo>
            <Entrada inicio={qDados} de="baixo">
              <div style={{ fontFamily: MONO, fontWeight: 700, fontSize: vertical ? 30 : 34, color: COR.tinta, marginTop: 16 }}>brasil.arvor.co/politize</div>
            </Entrada>
          </Caixa>
        </Entrada>
      </div>
      <Entrada inicio={qDados + 20} de="baixo" style={{ opacity: 1 - escurece * 0.85 }}>
        <Texto tamanho={vertical ? 22 : 26} cor={COR.suave}>
          Dados, critérios e a lista completa, com o endereço de cada local: <span style={{ color: COR.tealClaro, fontFamily: MONO }}>brasil.arvor.co</span>
        </Texto>
      </Entrada>
      {frame >= qArvor ? (
        <div style={{ display: "flex", alignItems: "center", gap: 22, opacity: marca, transform: `translateY(${(1 - marca) * 30}px)` }}>
          <Img src={staticFile("arvor_logo.png")} style={{ width: 96, height: 96, filter: "brightness(0) invert(1)" }} />
          <div style={{ fontFamily: FONTE, lineHeight: 1 }}>
            <div style={{ fontWeight: 700, fontSize: 48, color: COR.tinta, letterSpacing: 6 }}>ARVOR</div>
            <div style={{ fontFamily: MONO, fontSize: 20, color: COR.tealClaro, letterSpacing: 6 }}>INTELLIGENCE</div>
          </div>
        </div>
      ) : null}
      {frame >= qDia ? (
        <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", background: `rgba(3,6,15,${escurece * 0.85})`, padding: `0 ${margem}px` }}>
          <Entrada inicio={qDia} de="zoom" style={{ textAlign: "center" }}>
            <div style={{ fontFamily: MONO, fontWeight: 700, fontSize: vertical ? 200 : 260, color: COR.tinta, lineHeight: 0.9, letterSpacing: -10 }}>25</div>
            <div style={{ fontFamily: MONO, fontSize: vertical ? 30 : 36, color: COR.tealClaro, letterSpacing: 8, marginTop: 10 }}>DE OUTUBRO</div>
          </Entrada>
          <Entrada inicio={qDia + 40} de="baixo" style={{ marginTop: 40, textAlign: "center" }}>
            <Titulo tamanho={vertical ? 56 : 72}>Alguém precisa estar olhando.</Titulo>
          </Entrada>
        </AbsoluteFill>
      ) : null}
    </AbsoluteFill>
  );
};
