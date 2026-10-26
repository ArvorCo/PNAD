import { useMemo } from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { useFormato } from "../formato";
import { COR, FONTE } from "../tema";
import type { Palavra } from "../tipos";

type Trecho = { palavras: Palavra[]; t: number; f: number };

const MAX_PALAVRAS = 9;

/** Agrupa as palavras em frases curtas, quebrando em pontuação forte. */
const trechos = (palavras: Palavra[]): Trecho[] => {
  const saida: Trecho[] = [];
  let atual: Palavra[] = [];
  for (const p of palavras) {
    atual.push(p);
    const fim = /[.?!:]$|\.\.\.$/.test(p.w);
    if (fim || atual.length >= MAX_PALAVRAS) {
      saida.push({ palavras: atual, t: atual[0].t, f: atual[atual.length - 1].f });
      atual = [];
    }
  }
  if (atual.length) {
    saida.push({ palavras: atual, t: atual[0].t, f: atual[atual.length - 1].f });
  }
  // Fragmento de uma ou duas palavras volta para a frase anterior, se ela ainda couber.
  const unidos: Trecho[] = [];
  for (const trecho of saida) {
    const anterior = unidos[unidos.length - 1];
    if (anterior && trecho.palavras.length <= 2 && anterior.palavras.length + trecho.palavras.length <= MAX_PALAVRAS + 3) {
      anterior.palavras = [...anterior.palavras, ...trecho.palavras];
      anterior.f = trecho.f;
    } else {
      unidos.push({ ...trecho, palavras: [...trecho.palavras] });
    }
  }
  return unidos;
};

/** Legenda sincronizada com a narração, palavra ativa em destaque. */
export const Legenda: React.FC<{ palavras: Palavra[] }> = ({ palavras }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { vertical, largura, altura, margem } = useFormato();
  const lista = useMemo(() => trechos(palavras), [palavras]);
  const t = frame / fps;
  const trecho = lista.find((x) => t >= x.t - 0.15 && t <= x.f + 0.35);
  if (!trecho) {
    return null;
  }
  return (
    <div
      style={{
        position: "absolute",
        left: margem,
        right: margem,
        bottom: vertical ? altura * 0.16 : margem * 0.9,
        display: "flex",
        justifyContent: "center",
      }}
    >
      <div
        style={{
          maxWidth: vertical ? largura - 2 * margem : largura * 0.62,
          background: "rgba(3,8,20,0.78)",
          border: `1px solid ${COR.linha}`,
          borderRadius: 14,
          padding: vertical ? "14px 22px" : "12px 24px",
          fontFamily: FONTE,
          fontSize: vertical ? 34 : 30,
          fontWeight: 500,
          lineHeight: 1.3,
          color: COR.tinta,
          textAlign: "center",
          textWrap: "balance",
        }}
      >
        {trecho.palavras.map((p, i) => {
          const ativa = t >= p.t - 0.05;
          return (
            <span
              key={i}
              style={{
                color: ativa ? COR.tealClaro : COR.tinta,
                opacity: ativa ? 1 : 0.55,
              }}
            >
              {p.w}
              {i < trecho.palavras.length - 1 ? " " : ""}
            </span>
          );
        })}
      </div>
    </div>
  );
};
