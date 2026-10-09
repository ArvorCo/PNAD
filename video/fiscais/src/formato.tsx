import { createContext, useContext } from "react";

export type Formato = {
  largura: number;
  altura: number;
  vertical: boolean;
  /** Margem segura horizontal, em px. */
  margem: number;
};

const Contexto = createContext<Formato>({
  largura: 1920,
  altura: 1080,
  vertical: false,
  margem: 96,
});

export const FormatoProvider = Contexto.Provider;

export const useFormato = (): Formato => useContext(Contexto);

export const formatoDe = (largura: number, altura: number): Formato => ({
  largura,
  altura,
  vertical: altura > largura,
  margem: altura > largura ? 56 : 96,
});
