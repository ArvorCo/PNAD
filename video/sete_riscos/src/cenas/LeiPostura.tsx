// Cena 1.2: a postura do fiscal em seis gestos, cada um na palavra dita, sobre a ata em branco,
// e o fecho "Coragem é ficar. Sabedoria é não dar MOTIVO."
import { useCurrentFrame, useVideoConfig } from "remotion";
import { Area, Fase, Surge } from "../componentes/Quadro";
import { RiscoFundo } from "../componentes/Risco";
import { ritmo } from "../componentes/ritmo";
import { mola } from "../componentes/util";
import { useFormato } from "../formato";
import { COR, FONTE, MONO } from "../tema";
import type { CenaProps } from "./registro";

/** Os seis gestos, com o gatilho em que cada um entra. */
const GESTOS: readonly { texto: string; gatilho: string }[] = [
  { texto: "Crachá só com nome e partido", gatilho: "cracha" },
  { texto: "Não discute, não encosta em ninguém", gatilho: "discute" },
  { texto: "Anota hora e nome", gatilho: "anota" },
  { texto: "Pede registro na ata: campo 4.2, protesto e impugnação", gatilho: "ata" },
  { texto: "Mandado sair? Sai, registra e comunica ao juiz", gatilho: "sai" },
  { texto: "Crime fora da seção: Ministério Público Eleitoral", gatilho: "ministerio" },
];

const Gesto: React.FC<{ n: number; texto: string; q: number }> = ({ n, texto, q }) => {
  const { t, vertical } = useFormato();
  return (
    <Surge inicio={q} de="esquerda" style={{ display: "flex" }}>
      <div style={{ flex: 1, display: "flex", alignItems: "center", gap: t(18), padding: `${t(14)}px ${t(22)}px`, background: "rgba(12,26,58,0.86)", border: `1px solid ${COR.linha}`, borderLeft: `5px solid ${COR.ouro}`, borderRadius: 14 }}>
        <span style={{ fontFamily: MONO, fontWeight: 700, fontSize: t(vertical ? 32 : 28), color: COR.ouro, flex: "none" }}>{String(n).padStart(2, "0")}</span>
        <span style={{ fontFamily: FONTE, fontWeight: 700, fontSize: t(vertical ? 36 : 31), lineHeight: 1.15, color: COR.tinta }}>{texto}</span>
      </div>
    </Surge>
  );
};

export const LeiPostura: React.FC<CenaProps> = ({ cena, g: gBruto }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { vertical, t } = useFormato();
  const g = ritmo(cena, gBruto);
  const palavra = (q: number, texto: string, cor: string) => {
    const p = frame < q ? 0 : mola(frame, fps, q, { damping: 12 });
    return <span style={{ fontFamily: MONO, fontWeight: 700, fontSize: t(vertical ? 36 : 34), letterSpacing: 4, color: cor, opacity: Math.min(1, p * 1.3), transform: `scale(${0.7 + 0.3 * p})`, display: "inline-block" }}>{texto}</span>;
  };
  const motivo = frame < g.motivo ? 0 : mola(frame, fps, g.motivo, { damping: 10 });

  return (
    <>
      <RiscoFundo ids={["ata_mesa_still", "atas_mesa_lampada"]} opacidade={0.45} veu={0.9} />
      <Area style={{ gap: t(vertical ? 26 : 22) }}>
        <div style={{ display: "flex", gap: t(vertical ? 22 : 30), flexWrap: "wrap", alignItems: "center" }}>
          {palavra(g.sabedoria, "SABEDORIA", COR.tealClaro)}
          {palavra(g.coragem, "CORAGEM", COR.alta)}
          {palavra(g.lei, "SÓ A LEI", COR.ouro)}
        </div>
        <div style={{ display: "grid", gridTemplateColumns: vertical ? "1fr" : "1fr 1fr", gap: t(vertical ? 16 : 16) }}>
          {GESTOS.map((gesto, i) => (
            <Gesto key={gesto.gatilho} n={i + 1} texto={gesto.texto} q={g[gesto.gatilho] ?? g.cracha} />
          ))}
        </div>
        <div style={{ position: "relative", flex: 1, minHeight: t(vertical ? 300 : 150) }}>
          <Fase de={g.decide} ate={g.coragemFim} style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", justifyContent: "center", gap: t(10) }}>
            <div style={{ fontFamily: FONTE, fontWeight: 700, fontSize: t(vertical ? 40 : 36), lineHeight: 1.15, color: COR.tinta }}>
              Na seção, decide o presidente. Fora dela, a polícia e o Ministério Público.
            </div>
            <Surge inicio={g.calma}>
              <div style={{ fontFamily: FONTE, fontWeight: 500, fontSize: t(vertical ? 36 : 32), color: COR.suave }}>Quem perde a calma perde a razão.</div>
            </Surge>
          </Fase>
          <Fase de={g.coragemFim} style={{ position: "absolute", inset: 0, display: "flex", flexDirection: vertical ? "column" : "row", justifyContent: vertical ? "center" : "flex-start", alignItems: vertical ? "flex-start" : "center", gap: t(vertical ? 8 : 34) }}>
            <Surge inicio={g.coragemFim}>
              <span style={{ fontFamily: FONTE, fontWeight: 700, fontSize: t(vertical ? 80 : 72), letterSpacing: -2, color: COR.tinta }}>Coragem é ficar.</span>
            </Surge>
            <Surge inicio={g.sabedoriaFim}>
              <span style={{ fontFamily: FONTE, fontWeight: 700, fontSize: t(vertical ? 80 : 72), letterSpacing: -2, color: COR.tinta }}>
                Sabedoria é não dar{" "}
                <span style={{ whiteSpace: "nowrap" }}>
                  <span style={{ color: COR.ouro, display: "inline-block", transform: `scale(${0.8 + 0.2 * motivo})`, textShadow: `0 0 ${24 * motivo}px ${COR.ouro}88` }}>MOTIVO</span>.
                </span>
              </span>
            </Surge>
          </Fase>
        </div>
      </Area>
    </>
  );
};
