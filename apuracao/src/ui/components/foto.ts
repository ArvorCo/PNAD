// Foto oficial do TSE pelo sqcand; sem arquivo, monograma com as iniciais.

import { mix, PAPEL } from "../data/cores.ts";

/** Caminho da foto local (public/fotos/, gerado por scripts/extrair-fotos.py). */
export const urlFoto = (sqcand: string): string => `/fotos/${sqcand}.jpg`;

export function iniciais(nome: string): string {
  const partes = nome
    .replace(/[^\p{L}\s]/gu, " ")
    .split(/\s+/)
    .filter(p => p.length > 2 || /^[A-ZÀ-Ú]/.test(p));
  const a = partes[0]?.charAt(0) ?? "";
  const b = partes.length > 1 ? (partes[partes.length - 1]?.charAt(0) ?? "") : "";
  return (a + b).toLocaleUpperCase("pt-BR");
}

export interface OpcoesFoto {
  sqcand: string;
  nome: string;
  tamanho: number; // px na referência 1920×1080; vira rem
  cor?: string; // anel e fundo do monograma
}

export function foto(o: OpcoesFoto): HTMLSpanElement {
  const caixa = document.createElement("span");
  caixa.className = "foto";
  const lado = `${o.tamanho / 16}rem`;
  caixa.style.width = lado;
  caixa.style.height = lado;
  if (o.cor) caixa.style.setProperty("--foto-anel", o.cor);
  const mono = (): void => {
    const m = document.createElement("span");
    m.className = "foto-mono";
    m.style.fontSize = `${(o.tamanho * 0.4) / 16}rem`;
    m.style.background = mix(PAPEL, o.cor ?? "#8a8f98", 0.28);
    m.textContent = iniciais(o.nome);
    caixa.replaceChildren(m);
  };
  const img = document.createElement("img");
  img.alt = "";
  img.decoding = "async";
  img.width = o.tamanho;
  img.height = o.tamanho;
  img.addEventListener("error", mono, { once: true });
  img.src = urlFoto(o.sqcand);
  caixa.append(img);
  return caixa;
}
