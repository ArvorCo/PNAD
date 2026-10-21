import { useFormato } from "../formato";
import { COR, FONTE, MONO } from "../tema";
import { Entrada } from "./Caixa";
import { IconeCheck, IconeLei } from "./Icones";
import { Surge } from "./Quadro";

export type ItemLei = {
  texto: string;
  /** Dispositivo citado (lei, artigo, parágrafo), como em roteiro/fontes.md. */
  referencia: string;
  /** Quadro em que o item entra. */
  q: number;
};

type Props = {
  titulo: string;
  itens: ItemLei[];
  inicio: number;
  rodape?: string;
  cor?: string;
  /** Corpo do texto dos itens, em px de referência. */
  tamanho?: number;
  /** Reserva o lugar de cada item desde o começo, para o cartão não crescer aos saltos. */
  reservar?: boolean;
};

/** Cartão de lei: título com a balança, itens que entram na palavra dita e a referência de cada um. */
export const Lei: React.FC<Props> = ({ titulo, itens, inicio, rodape, cor = COR.ouro, tamanho = 28, reservar = false }) => {
  const { t, vertical } = useFormato();
  const Aparece = reservar ? Surge : Entrada;
  return (
    <Surge inicio={inicio}>
      <div
        style={{
          background: "rgba(12,26,58,0.86)",
          border: `1px solid ${COR.linha}`,
          borderTop: `4px solid ${cor}`,
          borderRadius: 18,
          padding: `${t(22)}px ${t(28)}px`,
          boxShadow: "0 24px 70px rgba(0,0,0,0.45)",
          display: "flex",
          flexDirection: "column",
          gap: t(16),
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: t(14) }}>
          <IconeLei tamanho={t(34)} cor={cor} />
          <span style={{ fontFamily: MONO, fontSize: t(vertical ? 22 : 18), letterSpacing: 3, color: cor }}>{titulo}</span>
        </div>
        {itens.map((item) => (
          <Aparece key={item.texto} inicio={item.q} de="esquerda">
            <div style={{ display: "flex", gap: t(14), alignItems: "flex-start" }}>
              <IconeCheck tamanho={t(tamanho + 6)} cor={COR.outros} style={{ marginTop: t(2) }} />
              <div style={{ display: "flex", flexDirection: "column", gap: t(4), minWidth: 0 }}>
                <div style={{ fontFamily: FONTE, fontWeight: 700, fontSize: t(tamanho), lineHeight: 1.2, color: COR.tinta }}>{item.texto}</div>
                <div style={{ fontFamily: MONO, fontSize: t(vertical ? 20 : 16), lineHeight: 1.3, color: COR.suave, letterSpacing: 0.5 }}>{item.referencia}</div>
              </div>
            </div>
          </Aparece>
        ))}
        {rodape ? (
          <div style={{ fontFamily: MONO, fontSize: t(vertical ? 18 : 15), color: COR.suave, letterSpacing: 0.5, borderTop: `1px solid ${COR.linha}`, paddingTop: t(10) }}>{rodape}</div>
        ) : null}
      </div>
    </Surge>
  );
};
