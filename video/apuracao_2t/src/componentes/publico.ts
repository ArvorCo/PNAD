import { getStaticFiles, type StaticFile } from "remotion";

let memo: { lista: StaticFile[]; nomes: Set<string> } | null = null;

/**
 * Diz se um arquivo existe em `public/` (caminho relativo, como `midia/x_16x9.mp4`). Mídia, voz e
 * música ficam fora do git e podem faltar nesta máquina: o componente mostra um aviso no lugar
 * de quebrar o render. A lista vem do bundle (estúdio e render); fora dele volta vazia.
 */
export const existePublico = (nome: string): boolean => {
  const lista = getStaticFiles();
  if (!memo || memo.lista !== lista) {
    memo = { lista, nomes: new Set(lista.map((f) => f.name)) };
  }
  return memo.nomes.has(nome);
};
