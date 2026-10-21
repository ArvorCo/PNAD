import { createContext, useContext } from "react";

export type Formato = {
  largura: number;
  altura: number;
  vertical: boolean;
  /** Margem segura horizontal, em px. */
  margem: number;
  /** Fator de tipografia e espaçamento: 1 no 16:9, 0,92 no 9:16. */
  escala: number;
  /** Converte px de referência (16:9) para o formato atual, arredondado. */
  t: (px: number) => number;
};

export const formatoDe = (largura: number, altura: number): Formato => {
  const vertical = altura > largura;
  const escala = vertical ? 0.92 : 1;
  return {
    largura,
    altura,
    vertical,
    margem: vertical ? 56 : 96,
    escala,
    t: (px: number) => Math.round(px * escala),
  };
};

const Contexto = createContext<Formato>(formatoDe(1920, 1080));

export const FormatoProvider = Contexto.Provider;

export const useFormato = (): Formato => useContext(Contexto);
