import { AbsoluteFill, useCurrentFrame } from "remotion";
import { useFormato } from "../formato";
import { COR, FONTE, MONO } from "../tema";
import { Entrada } from "./Caixa";
import { Area, Surge } from "./Quadro";
import { rampa } from "./util";

type Props = {
  /** As três frases da casa, na ordem em que são ditas. */
  frases: readonly string[];
  /** Quadro em que cada frase entra. */
  q: readonly number[];
  /** Cor da barra lateral de cada frase. */
  cores?: readonly string[];
  /** Escurece o fundo (tela cheia tipográfica). */
  veu?: boolean;
};

/** As três frases da casa em tela tipográfica: uma por vez, a última dita em destaque. */
export const FrasesCasa: React.FC<Props> = ({ frases, q, cores = [COR.tealClaro, COR.ouro, COR.outros], veu = true }) => {
  const frame = useCurrentFrame();
  const { vertical, t } = useFormato();
  // No 9:16 cada frase tem o lugar reservado desde a primeira: as três ocupam a coluna sem pular.
  const Aparece = vertical ? Surge : Entrada;
  if (frame < q[0] - 10) {
    return null;
  }
  const atual = q.reduce((acc, qi, i) => (frame >= qi ? i : acc), 0);
  const escuro = rampa(frame, q[0] - 10, q[0] + 6);
  return (
    <AbsoluteFill style={{ background: veu ? `rgba(3,6,15,${0.96 * escuro})` : "transparent" }}>
      <Area style={{ justifyContent: "center", gap: t(vertical ? 64 : 40) }}>
        {frases.map((f, i) => (
          <Aparece key={f} inicio={q[i]} de="baixo">
            <div style={{ display: "flex", gap: t(26), alignItems: "stretch" }}>
              <div style={{ width: t(8), borderRadius: t(4), background: cores[i % cores.length], opacity: i === atual ? 1 : 0.45, flex: "none" }} />
              <div style={{ display: "flex", flexDirection: "column", gap: t(6) }}>
                <span style={{ fontFamily: MONO, fontSize: t(vertical ? 26 : 20), letterSpacing: 4, color: cores[i % cores.length] }}>{String(i + 1).padStart(2, "0")}</span>
                <div
                  style={{
                    fontFamily: FONTE,
                    fontWeight: 700,
                    fontSize: t(vertical ? 80 : 58),
                    lineHeight: 1.08,
                    letterSpacing: -1,
                    color: i === atual ? COR.tinta : COR.suave,
                    textWrap: "balance",
                  }}
                >
                  {f}
                </div>
              </div>
            </div>
          </Aparece>
        ))}
      </Area>
    </AbsoluteFill>
  );
};
