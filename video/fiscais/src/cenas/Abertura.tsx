import { AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Chip, Entrada, Texto, Titulo } from "../componentes/Caixa";
import { Contador } from "../componentes/Contador";
import { mola, rampa } from "../componentes/util";
import { useFormato } from "../formato";
import { quadro, type Cena } from "../plano";
import { COR, FONTE, MONO } from "../tema";
import type { Dados } from "../tipos";

const Icone: React.FC<{ nome: string; rotulo: string; inicio: number; tamanho: number }> = ({ nome, rotulo, inicio, tamanho }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = mola(frame, fps, inicio, { damping: 12 });
  if (frame < inicio) {
    return null;
  }
  const desenho =
    nome === "urna" ? (
      <g>
        <rect x={14} y={22} width={52} height={44} rx={6} fill="none" stroke={COR.tealClaro} strokeWidth={4} />
        <rect x={26} y={10} width={28} height={12} rx={3} fill={COR.tealClaro} />
        <rect x={22} y={34} width={36} height={20} rx={3} fill={COR.teal} opacity={0.6} />
      </g>
    ) : nome === "mesa" ? (
      <g>
        <rect x={8} y={38} width={64} height={8} rx={3} fill={COR.tealClaro} />
        <rect x={14} y={46} width={6} height={22} fill={COR.tealClaro} />
        <rect x={60} y={46} width={6} height={22} fill={COR.tealClaro} />
        <circle cx={40} cy={24} r={9} fill={COR.teal} />
      </g>
    ) : (
      <g>
        <rect x={20} y={8} width={40} height={62} rx={4} fill="none" stroke={COR.tealClaro} strokeWidth={4} />
        <line x1={28} x2={52} y1={24} y2={24} stroke={COR.teal} strokeWidth={4} />
        <line x1={28} x2={52} y1={36} y2={36} stroke={COR.teal} strokeWidth={4} />
        <line x1={28} x2={44} y1={48} y2={48} stroke={COR.teal} strokeWidth={4} />
      </g>
    );
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 10, transform: `scale(${p})`, opacity: p }}>
      <svg width={tamanho} height={tamanho} viewBox="0 0 80 80">{desenho}</svg>
      <span style={{ fontFamily: MONO, fontSize: 20, letterSpacing: 3, color: COR.suave }}>{rotulo.toUpperCase()}</span>
    </div>
  );
};

/** Cartão de abertura: marca Arvor, a data, o tamanho do país e a pergunta. */
export const Abertura: React.FC<{ cena: Cena; dados: Dados }> = ({ cena, dados }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { vertical, largura, altura, margem } = useFormato();
  const p = cena.palavras;
  const qDia = quadro(p, "vinte", 1.4);
  const qTurno = quadro(p, "Segundo", 3.1);
  const qSecoes = quadro(p, "Quase", 4.4);
  const qHora = quadro(p, "oito", 7);
  const qUrna = quadro(p, "urna", 10);
  const qMesa = quadro(p, "mesa", 11);
  const qBoletim = quadro(p, "boletim", 12);
  const qPergunta = quadro(p, "pergunta", 14);
  const qOnde = quadro(p, "onde", 19);

  const marca = mola(frame, fps, 0, { damping: 18 });
  const marcaSai = rampa(frame, qDia - 12, qDia);
  const primeiroBloco = 1 - rampa(frame, qPergunta - 10, qPergunta + 4);
  const escalaDia = interpolate(frame, [qDia, qDia + 20], [0.6, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const diaTamanho = vertical ? 300 : 340;

  return (
    <AbsoluteFill>
      {marcaSai < 1 ? (
        <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", opacity: 1 - marcaSai, transform: `scale(${1 + marcaSai * 0.25})` }}>
          <Img src={staticFile("arvor_logo.png")} style={{ width: 240, height: 240, filter: "brightness(0) invert(1)", transform: `scale(${marca})`, opacity: marca }} />
          <div style={{ fontFamily: FONTE, fontWeight: 700, fontSize: 56, color: COR.tinta, letterSpacing: 10, marginTop: 10, opacity: marca }}>ARVOR</div>
          <div style={{ fontFamily: MONO, fontSize: 22, color: COR.tealClaro, letterSpacing: 7, marginTop: 6, opacity: marca }}>INTELLIGENCE · APRESENTA</div>
        </AbsoluteFill>
      ) : null}

      <AbsoluteFill style={{ opacity: primeiroBloco, padding: `${vertical ? 190 : 170}px ${margem}px`, justifyContent: "center" }}>
        <div style={{ display: "flex", flexDirection: vertical ? "column" : "row", alignItems: vertical ? "center" : "center", gap: vertical ? 10 : 60 }}>
          {frame >= qDia ? (
            <div style={{ display: "flex", alignItems: "baseline", gap: 18, transform: `scale(${escalaDia})`, transformOrigin: "left center" }}>
              <span style={{ fontFamily: MONO, fontWeight: 700, fontSize: diaTamanho, color: COR.tinta, lineHeight: 0.9, letterSpacing: -12 }}>25</span>
              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                <span style={{ fontFamily: FONTE, fontWeight: 700, fontSize: 60, color: COR.tealClaro, letterSpacing: 4 }}>OUT</span>
                <span style={{ fontFamily: MONO, fontSize: 28, color: COR.suave, letterSpacing: 3 }}>2026</span>
              </div>
            </div>
          ) : null}
          <div style={{ display: "flex", flexDirection: "column", gap: 20, alignItems: vertical ? "center" : "flex-start" }}>
            <Entrada inicio={qTurno} de="esquerda">
              <Chip cor={COR.alta} solido tamanho={vertical ? 30 : 34}>2º turno</Chip>
            </Entrada>
            <Entrada inicio={qSecoes} de="baixo">
              <div style={{ display: "flex", flexDirection: "column", alignItems: vertical ? "center" : "flex-start" }}>
                <Contador valor={dados.resumo.secoes_universo} inicio={qSecoes} duracao={60} tamanho={vertical ? 96 : 120} cor={COR.tinta} />
                <Texto tamanho={vertical ? 30 : 34} cor={COR.tealClaro} style={{ letterSpacing: 2, textTransform: "uppercase", fontFamily: MONO }}>seções eleitorais</Texto>
              </div>
            </Entrada>
            <Entrada inicio={qHora} de="baixo">
              <div style={{ fontFamily: MONO, fontSize: vertical ? 34 : 40, color: COR.suave, letterSpacing: 3 }}>
                abrem às <span style={{ color: COR.tinta, fontWeight: 700 }}>08:00</span>
              </div>
            </Entrada>
          </div>
        </div>
        <div style={{ display: "flex", gap: vertical ? 60 : 90, justifyContent: "center", marginTop: vertical ? 70 : 60 }}>
          <Icone nome="urna" rotulo="uma urna" inicio={qUrna} tamanho={vertical ? 110 : 120} />
          <Icone nome="mesa" rotulo="uma mesa" inicio={qMesa} tamanho={vertical ? 110 : 120} />
          <Icone nome="boletim" rotulo="um boletim" inicio={qBoletim} tamanho={vertical ? 110 : 120} />
        </div>
      </AbsoluteFill>

      {frame >= qPergunta ? (
        <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", padding: `0 ${margem}px` }}>
          <Entrada inicio={qPergunta} de="zoom">
            <Chip cor={COR.tealClaro} tamanho={vertical ? 20 : 22}>a pergunta</Chip>
          </Entrada>
          <Entrada inicio={qOnde} de="baixo" style={{ marginTop: 30, maxWidth: vertical ? largura - 2 * margem : largura * 0.7, textAlign: "center" }}>
            <Titulo tamanho={vertical ? 72 : 88}>
              Onde um <span style={{ color: COR.tealClaro }}>fiscal</span> faz mais diferença?
            </Titulo>
          </Entrada>
          <div style={{ position: "absolute", bottom: altura * 0.3, fontFamily: MONO, fontSize: 18, color: COR.suave, letterSpacing: 4, opacity: 0.6 }}>
            13.045 RESPOSTAS, COM ENDEREÇO
          </div>
        </AbsoluteFill>
      ) : null}
    </AbsoluteFill>
  );
};
