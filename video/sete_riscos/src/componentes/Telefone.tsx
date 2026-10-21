import type { CSSProperties, PropsWithChildren } from "react";
import { useFormato } from "../formato";
import { COR } from "../tema";

/** Espessura da borda do aparelho e das faixas de cima e de baixo, em px de referência. */
const BORDA = 12;
const FAIXA = 16;

/** Largura da tela que cabe numa altura total de aparelho, para a proporção dada. */
export const larguraDaTela = (alturaTotal: number, proporcao: number, t: (px: number) => number): number =>
  Math.max(1, (alturaTotal - 2 * t(BORDA) - 2 * t(FAIXA)) * proporcao);

/** Largura total do aparelho para uma largura de tela. */
export const larguraDoTelefone = (larguraTela: number, t: (px: number) => number): number => larguraTela + 2 * t(BORDA);

/** Aparelho celular desenhado em CSS em volta de uma tela com a proporção dada. */
export const Telefone: React.FC<PropsWithChildren<{ largura: number; proporcao: number; cor?: string; style?: CSSProperties }>> = ({
  largura,
  proporcao,
  cor = COR.tealClaro,
  style,
  children,
}) => {
  const { t } = useFormato();
  const borda = t(BORDA);
  const faixa = t(FAIXA);
  return (
    <div
      style={{
        position: "relative",
        flex: "none",
        padding: `${borda + faixa}px ${borda}px`,
        borderRadius: t(48),
        background: "linear-gradient(160deg, #22325a 0%, #0b1328 55%, #050914 100%)",
        border: "2px solid rgba(154,166,196,0.38)",
        boxShadow: `0 40px 90px rgba(0,0,0,0.6), 0 0 50px ${cor}26`,
        ...style,
      }}
    >
      <div
        style={{
          position: "absolute",
          top: borda + faixa / 2 - t(3),
          left: "50%",
          width: t(64),
          height: t(6),
          marginLeft: -t(32),
          borderRadius: t(3),
          background: "rgba(154,166,196,0.45)",
        }}
      />
      <div style={{ position: "relative", width: largura, height: largura / proporcao, borderRadius: t(26), overflow: "hidden", background: "#000" }}>
        {children}
      </div>
    </div>
  );
};
