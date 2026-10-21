// Cena 0.2: a tese em três verbos (vê, anota, pede cópia), o que o fiscal não faz, do que ele
// precisa e o fecho "Sete riscos. Um fiscal. A lei.", com o fiscal na cadeira ao fundo.
import type { ReactNode } from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { IconeCheck, IconeLei, IconeX } from "../componentes/Icones";
import { Area, Fase, Surge } from "../componentes/Quadro";
import { RiscoFundo } from "../componentes/Risco";
import { ritmo } from "../componentes/ritmo";
import { mola, rampa } from "../componentes/util";
import { useFormato } from "../formato";
import { COR, FONTE, MONO } from "../tema";
import type { CenaProps } from "./registro";

const Svg: React.FC<{ tamanho: number; children: ReactNode }> = ({ tamanho, children }) => (
  <svg width={tamanho} height={tamanho} viewBox="0 0 64 64" fill="none" stroke={COR.tealClaro} strokeWidth={3.5} strokeLinecap="round" strokeLinejoin="round" style={{ flex: "none" }}>
    {children}
  </svg>
);

const Olho: React.FC<{ tamanho: number }> = ({ tamanho }) => (
  <Svg tamanho={tamanho}>
    <path d="M4 32 C16 14 48 14 60 32 C48 50 16 50 4 32 Z" />
    <circle cx="32" cy="32" r="9" />
  </Svg>
);

const Caneta: React.FC<{ tamanho: number }> = ({ tamanho }) => (
  <Svg tamanho={tamanho}>
    <path d="M44 8 L56 20 L24 52 L10 56 L14 42 Z" />
    <path d="M38 14 L50 26" />
  </Svg>
);

const Copia: React.FC<{ tamanho: number }> = ({ tamanho }) => (
  <Svg tamanho={tamanho}>
    <rect x="18" y="6" width="34" height="42" rx="3" />
    <path d="M12 16 L12 58 L44 58" />
    <path d="M26 18 L44 18 M26 28 L44 28 M26 38 L38 38" />
  </Svg>
);

const Verbo: React.FC<{ q: number; icone: ReactNode; texto: string }> = ({ q, icone, texto }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { t, vertical } = useFormato();
  const p = frame < q ? 0 : mola(frame, fps, q, { damping: 11 });
  return (
    <div style={{ display: "flex", alignItems: "center", gap: t(20), opacity: Math.min(1, p * 1.3), transform: `scale(${0.6 + 0.4 * p})`, transformOrigin: vertical ? "left center" : "center" }}>
      {icone}
      <span style={{ fontFamily: FONTE, fontWeight: 700, fontSize: t(vertical ? 104 : 96), letterSpacing: -3, color: COR.tinta, lineHeight: 1, whiteSpace: "nowrap" }}>{texto}</span>
    </div>
  );
};

const Item: React.FC<{ q: number; sim: boolean; texto: string }> = ({ q, sim, texto }) => {
  const { t, vertical } = useFormato();
  const cor = sim ? COR.outros : COR.alta;
  return (
    <Surge inicio={q} de="esquerda">
      <div style={{ display: "flex", alignItems: "center", gap: t(16) }}>
        {sim ? <IconeCheck tamanho={t(vertical ? 54 : 50)} cor={cor} /> : <IconeX tamanho={t(vertical ? 54 : 50)} cor={cor} />}
        <span style={{ fontFamily: FONTE, fontWeight: 700, fontSize: t(vertical ? 54 : 50), color: COR.tinta, lineHeight: 1.05 }}>{texto}</span>
      </div>
    </Surge>
  );
};

const Coluna: React.FC<{ titulo: string; cor: string; children: ReactNode }> = ({ titulo, cor, children }) => {
  const { t, vertical } = useFormato();
  return (
    <div style={{ flex: vertical ? "none" : 1, display: "flex", flexDirection: "column", gap: t(vertical ? 22 : 24), padding: `${t(26)}px ${t(32)}px`, background: "rgba(6,11,26,0.62)", borderTop: `5px solid ${cor}`, borderRadius: 18 }}>
      <span style={{ fontFamily: MONO, fontWeight: 700, fontSize: t(vertical ? 30 : 26), letterSpacing: 4, color: cor }}>{titulo}</span>
      {children}
    </div>
  );
};

export const Tese: React.FC<CenaProps> = ({ cena, g: gBruto }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { vertical, t } = useFormato();
  const g = ritmo(cena, gBruto);
  const nega = (q: number, texto: string) => (
    <Surge inicio={q}>
      <span style={{ fontFamily: FONTE, fontWeight: 700, fontSize: t(vertical ? 40 : 36), color: COR.suave, padding: `${t(6)}px ${t(16)}px`, border: `2px solid ${COR.linha}`, borderRadius: 12, whiteSpace: "nowrap" }}>
        {texto}
      </span>
    </Surge>
  );
  const linhaFecho = (q: number, texto: string, cor: string) => {
    const p = frame < q ? 0 : mola(frame, fps, q, { damping: 13 });
    return (
      <div style={{ fontFamily: FONTE, fontWeight: 700, fontSize: t(vertical ? 132 : 120), letterSpacing: -4, lineHeight: 1.02, color: cor, opacity: Math.min(1, p * 1.3), transform: `translateY(${(1 - p) * 40}px)` }}>{texto}</div>
    );
  };
  const fundoForte = rampa(frame, g.sete - 10, g.sete + 20);

  return (
    <>
      <AbsoluteFill style={{ opacity: 1 }}>
        <RiscoFundo ids={["fiscal_cadeira", "secao_vazia"]} opacidade={0.35 + 0.3 * fundoForte} veu={0.9 - 0.25 * fundoForte} />
      </AbsoluteFill>
      <Area>
        <Fase de={0} ate={g.precisa} style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", justifyContent: "center", gap: t(vertical ? 48 : 40) }}>
          <Surge inicio={g.fiscal} de="esquerda">
            <span style={{ fontFamily: MONO, fontWeight: 700, fontSize: t(vertical ? 34 : 30), letterSpacing: 6, color: COR.tealClaro }}>O FISCAL</span>
          </Surge>
          <div style={{ display: "flex", flexDirection: vertical ? "column" : "row", justifyContent: "space-between", gap: t(vertical ? 30 : 30) }}>
            <Verbo q={g.ve} icone={<Olho tamanho={t(96)} />} texto="vê" />
            <Verbo q={g.anota} icone={<Caneta tamanho={t(96)} />} texto="anota" />
            <Verbo q={g.pede} icone={<Copia tamanho={t(96)} />} texto="pede cópia" />
          </div>
          <div style={{ display: "flex", gap: t(16), flexWrap: "wrap", alignItems: "center" }}>
            {nega(g.discute, "não discute")}
            {nega(g.grita, "não grita")}
            {nega(g.muda, "não muda resultado")}
          </div>
          <Surge inicio={g.protege}>
            <div style={{ fontFamily: FONTE, fontWeight: 700, fontSize: t(vertical ? 76 : 72), letterSpacing: -2, lineHeight: 1.05, color: COR.tealClaro, textWrap: "balance" }}>Protege o voto de todo mundo.</div>
          </Surge>
        </Fase>
        <Fase de={g.precisa} ate={g.sete} style={{ position: "absolute", inset: 0, display: "flex", flexDirection: vertical ? "column" : "row", justifyContent: "center", alignItems: vertical ? "stretch" : "center", gap: t(vertical ? 30 : 40) }}>
          <Coluna titulo="NÃO PRECISA DE" cor={COR.alta}>
            <Item q={g.arma} sim={false} texto="arma" />
            <Item q={g.gritaria} sim={false} texto="gritaria" />
            <Item q={g.teatral} sim={false} texto="coragem teatral" />
          </Coluna>
          <Coluna titulo="PRECISA DE" cor={COR.outros}>
            <Item q={g.atencao} sim texto="atenção" />
            <Item q={g.papel} sim texto="papel" />
            <Item q={g.lei} sim texto="a lei na mão" />
          </Coluna>
        </Fase>
        <Fase de={g.sete} style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", justifyContent: "center", gap: t(vertical ? 18 : 10) }}>
          {linhaFecho(g.sete, "Sete riscos.", COR.alta)}
          {linhaFecho(g.um, "Um fiscal.", COR.tealClaro)}
          <div style={{ display: "flex", alignItems: "center", gap: t(28) }}>
            {frame >= g.leiFim ? <IconeLei tamanho={t(vertical ? 120 : 110)} cor={COR.ouro} /> : null}
            {linhaFecho(g.leiFim, "A lei.", COR.ouro)}
          </div>
        </Fase>
      </Area>
    </>
  );
};
