import { AbsoluteFill, Img, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Entrada, Titulo } from "../componentes/Caixa";
import { ClipeSeHouver } from "../componentes/ClipeSeHouver";
import { FrasesCasa } from "../componentes/FrasesCasa";
import { Area, Fase, Surge } from "../componentes/Quadro";
import { FRASES_CASA } from "../componentes/textos";
import { mola, rampa } from "../componentes/util";
import { useFormato } from "../formato";
import { COR, FONTE, MONO } from "../tema";
import type { CenaProps } from "./registro";

/** Os três endereços do vídeo, na ordem em que aparecem nos capítulos. */
const URLS = [
  { url: "fiscaisdopl.com.br", cor: COR.ouro },
  { url: "brasil.arvor.co/totalizacao", cor: COR.outros },
  { url: "brasil.arvor.co/fiscais_mapa.html", cor: COR.teal },
];

const Enderecos: React.FC<{ q: number }> = ({ q }) => {
  const { vertical, t } = useFormato();
  return (
    <div style={{ display: "flex", flexDirection: vertical ? "column" : "row", gap: t(vertical ? 12 : 18), justifyContent: "center", alignItems: "center" }}>
      {URLS.map((u, i) => (
        <Surge key={u.url} inicio={q + i * 6} de="baixo">
          <div
            style={{
              fontFamily: MONO,
              fontWeight: 700,
              fontSize: t(vertical ? 32 : 24),
              color: COR.tinta,
              padding: `${t(8)}px ${t(16)}px`,
              borderRadius: 10,
              border: `2px solid ${u.cor}`,
              background: "rgba(3,8,20,0.82)",
              whiteSpace: "nowrap",
            }}
          >
            {u.url}
          </div>
        </Surge>
      ))}
    </div>
  );
};

/**
 * O convite: as três frases da casa, uma a uma; "Sete riscos. Um fiscal. Nenhuma arma além da
 * lei."; a seção sem testemunha; e "Alguém precisa estar olhando. Pode ser VOCÊ.", com os três
 * endereços no pé da cena.
 */
export const FechoChamada: React.FC<CenaProps> = ({ g }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { vertical, t, altura } = useFormato();
  const fimFrases = g.sete - 8;
  const fimSete = g.alguem - 8;
  const voce = mola(frame, fps, g.voce, { damping: 10, stiffness: 150 });
  const marca = mola(frame, fps, g.alguem, { damping: 16 });
  const pulso = 0.5 + 0.5 * Math.sin(frame * 0.2);

  return (
    <>
      <ClipeSeHouver id="fiscal_cadeira" opacidade={0.38 + 0.12 * rampa(frame, fimFrases, fimFrases + 20)} veu={0.9} />
      <Fase de={0} ate={g.atipicidade}>
        <Area style={{ justifyContent: "center" }}>
          <Entrada inicio={0} de="baixo">
            <Titulo tamanho={vertical ? 84 : 76}>
              Três frases <span style={{ color: COR.tealClaro }}>para levar</span>
            </Titulo>
          </Entrada>
        </Area>
      </Fase>
      <Fase de={g.atipicidade - 10} ate={fimFrases}>
        <AbsoluteFill>
          <FrasesCasa frases={FRASES_CASA} q={[g.atipicidade, g.lista, g.resolve]} veu={false} />
        </AbsoluteFill>
      </Fase>
      <Fase de={fimFrases} ate={fimSete}>
        <Area style={{ justifyContent: "center", gap: t(vertical ? 40 : 26) }}>
          <Surge inicio={g.sete} de="esquerda">
            <Titulo tamanho={vertical ? 110 : 96}>Sete riscos.</Titulo>
          </Surge>
          <Surge inicio={g.fiscal} de="esquerda">
            <Titulo tamanho={vertical ? 110 : 96} cor={COR.tealClaro}>
              Um fiscal.
            </Titulo>
          </Surge>
          <Surge inicio={g.nenhuma} de="esquerda">
            <Titulo tamanho={vertical ? 78 : 66} cor={COR.ouro}>
              Nenhuma arma além da lei.
            </Titulo>
          </Surge>
          <Surge inicio={g.daqui} de="baixo">
            <div style={{ fontFamily: FONTE, fontWeight: 500, fontSize: t(vertical ? 40 : 34), color: COR.suave, lineHeight: 1.25, maxWidth: t(1300), textWrap: "balance" }}>
              Até o fim do segundo turno, cada seção sem olhar atento é uma seção sem testemunha.
            </div>
          </Surge>
        </Area>
      </Fase>
      <Fase de={fimSete}>
        <Area style={{ justifyContent: "center", alignItems: "center", gap: t(vertical ? 54 : 36), textAlign: "center" }}>
          <div style={{ display: "flex", alignItems: "center", gap: t(22), opacity: marca, transform: `translateY(${(1 - marca) * 24}px)` }}>
            <Img src={staticFile("arvor_logo.png")} style={{ width: t(vertical ? 110 : 84), height: t(vertical ? 110 : 84), filter: "brightness(0) invert(1)" }} />
            <div style={{ fontFamily: FONTE, lineHeight: 1, textAlign: "left" }}>
              <div style={{ fontWeight: 700, fontSize: t(vertical ? 60 : 46), color: COR.tinta, letterSpacing: 8 }}>ARVOR</div>
              <div style={{ fontFamily: MONO, fontSize: t(vertical ? 28 : 22), color: COR.tealClaro, letterSpacing: 8, marginTop: t(6) }}>INTELLIGENCE</div>
            </div>
          </div>
          <Surge inicio={g.alguem} de="baixo">
            <Titulo tamanho={vertical ? 92 : 80}>Alguém precisa estar olhando.</Titulo>
          </Surge>
          <div style={{ display: "flex", alignItems: "baseline", gap: t(28), justifyContent: "center", flexWrap: "wrap" }}>
            <Surge inicio={g.pode} de="baixo">
              <Titulo tamanho={vertical ? 92 : 80}>Pode ser</Titulo>
            </Surge>
            <div
              style={{
                fontFamily: FONTE,
                fontWeight: 700,
                fontSize: t(vertical ? 190 : 170),
                lineHeight: 0.9,
                letterSpacing: -4,
                color: COR.ouro,
                opacity: frame < g.voce ? 0 : 1,
                transform: `scale(${frame < g.voce ? 0.5 : 0.5 + 0.5 * voce})`,
                textShadow: `0 0 ${30 + 30 * pulso}px ${COR.ouro}66`,
              }}
            >
              VOCÊ.
            </div>
          </div>
        </Area>
      </Fase>
      <Fase de={fimFrases}>
        <div style={{ position: "absolute", left: 0, right: 0, bottom: vertical ? altura * 0.16 + 130 : 238, display: "flex", justifyContent: "center" }}>
          <Enderecos q={g.sete} />
        </div>
      </Fase>
    </>
  );
};
