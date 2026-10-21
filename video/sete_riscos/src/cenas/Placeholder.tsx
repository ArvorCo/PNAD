import { capituloDe } from "../capitulos";
import { Caixa, Chip, Entrada, Texto, Titulo } from "../componentes/Caixa";
import { Palco, Pilha } from "../componentes/Palco";
import { decimal } from "../componentes/util";
import { useFormato } from "../formato";
import { IDS } from "../ordem";
import { FPS } from "../plano";
import { COR, MONO } from "../tema";
import type { CenaProps } from "./registro";

const LIMITE = 120;

/** Cena ainda não desenhada: cor do capítulo, id, posição e o começo da narração. */
export const Placeholder: React.FC<CenaProps> = ({ cena }) => {
  const { vertical } = useFormato();
  const capitulo = capituloDe(cena.id);
  const posicao = IDS.indexOf(cena.id) + 1;
  const trecho = cena.texto.length > LIMITE ? `${cena.texto.slice(0, LIMITE).trimEnd()}...` : cena.texto;
  return (
    <Palco style={{ justifyContent: "center" }}>
      <Pilha gap={26} alinhar={vertical ? "stretch" : "flex-start"}>
        <Entrada inicio={0} de="esquerda">
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
            <Chip cor={capitulo.cor} solido tamanho={20}>
              {capitulo.numero} · {capitulo.titulo}
            </Chip>
            <Chip cor={COR.suave} tamanho={18}>
              cena {posicao} de {IDS.length}
            </Chip>
            <Chip cor={COR.ouro} tamanho={18}>
              {decimal(cena.frames / FPS, 1)} s
            </Chip>
          </div>
        </Entrada>
        <Entrada inicio={6} de="esquerda">
          <Titulo tamanho={vertical ? 76 : 96} cor={capitulo.cor} style={{ fontFamily: MONO, letterSpacing: -2 }}>
            {cena.id}
          </Titulo>
        </Entrada>
        <Entrada inicio={14} de="baixo" style={{ maxWidth: vertical ? "100%" : "72%" }}>
          <Caixa cor={capitulo.cor} titulo={cena.comVoz ? "NARRAÇÃO" : "SEM VOZ AINDA"}>
            <Texto tamanho={30} cor={cena.comVoz ? COR.tinta : COR.suave}>
              {cena.comVoz ? trecho : "Roteiro e voz desta cena ainda não foram gerados. Duração provisória."}
            </Texto>
          </Caixa>
        </Entrada>
      </Pilha>
    </Palco>
  );
};
