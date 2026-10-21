import { COR, MONO } from "../tema";

/** Painel visível no lugar de uma mídia que ainda não existe: o render segue, e o buraco aparece. */
export const MidiaAusente: React.FC<{ motivo: string }> = ({ motivo }) => (
  <div
    style={{
      position: "absolute",
      inset: 0,
      display: "flex",
      flexDirection: "column",
      justifyContent: "center",
      alignItems: "center",
      gap: 12,
      padding: 32,
      background: "repeating-linear-gradient(135deg, rgba(240,200,107,0.06) 0 18px, rgba(6,11,26,0.6) 18px 36px)",
      border: `2px dashed ${COR.ouro}`,
      borderRadius: 16,
      textAlign: "center",
    }}
  >
    <div style={{ fontFamily: MONO, fontSize: 18, letterSpacing: 3, color: COR.ouro }}>MÍDIA PENDENTE</div>
    <div style={{ fontFamily: MONO, fontSize: 20, color: COR.tinta, wordBreak: "break-word" }}>{motivo}</div>
  </div>
);
