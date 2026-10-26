import { useCurrentFrame } from "remotion";
import { COR, MONO } from "../tema";
import { decimal, inteiro, rampa, suave } from "./util";

type Props = {
  valor: number;
  inicio: number;
  duracao?: number;
  casas?: number;
  prefixo?: string;
  sufixo?: string;
  tamanho?: number;
  cor?: string;
  peso?: number;
};

/** Número que sobe do zero até o valor, com formatação pt-BR e dígitos tabulares. */
export const Contador: React.FC<Props> = ({
  valor,
  inicio,
  duracao = 40,
  casas = 0,
  prefixo = "",
  sufixo = "",
  tamanho = 96,
  cor = COR.tinta,
  peso = 700,
}) => {
  const frame = useCurrentFrame();
  const p = suave(rampa(frame, inicio, inicio + duracao));
  const atual = valor * p;
  const texto = casas > 0 ? decimal(atual, casas) : inteiro(atual);
  const entrada = rampa(frame, inicio, inicio + 10);
  return (
    <span
      style={{
        fontFamily: MONO,
        fontWeight: peso,
        fontSize: tamanho,
        color: cor,
        fontVariantNumeric: "tabular-nums",
        letterSpacing: -1,
        opacity: entrada,
        transform: `translateY(${(1 - entrada) * 18}px)`,
        display: "inline-block",
        lineHeight: 1,
      }}
    >
      {prefixo}
      {texto}
      {sufixo}
    </span>
  );
};
