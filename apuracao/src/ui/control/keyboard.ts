// Mapa de teclas do plano. Letras de comando que também iniciam sigla de UF
// (a de AC/AL/AM/AP, m de MA/MG/MS/MT, r de RJ/RN/RO/RR/RS) esperam a janela de
// 900 ms: se a segunda letra fechar uma UF, vale a UF; senão, roda o comando.

import { criarLeitorUf, destinoDaTecla2T, destinoDoDigito, ehUf } from "./navegacao.ts";
import type { Destino } from "./navegacao.ts";

export interface AcoesTeclado {
  ufAtual(): string | null;
  telaAtual(): string;
  /** Turno da eleição (config.turno); o 2º turno troca a tecla 3 para o quadro dos 6 governadores. */
  turno(): number;
  irPara(d: Destino): void; // sempre passa para o modo manual
  irParaUf(uf: string): void;
  proxima(): void;
  anterior(): void;
  pausar(): void; // alterna
  auto(): void;
  subir(): void;
  paleta(abrir: boolean): void;
  paletaAberta(): boolean;
  zonas(): void;
  tela_cheia(): void;
  hud(): void;
  variante(): void;
  refetch(): void;
  /** Teclas próprias da tela (↑/↓ entre zonas). Devolve true se tratou. */
  teclaDaTela(tecla: string): boolean;
  /**
   * Boletim falado: `b` alterna (toca o escolhido ou o último pronto, pausa, retoma); `[` e `]`
   * escolhem o item na lista do widget; Shift+B e Ctrl+B param.
   * Shift+B só para quando há boletim carregado; sem boletim, continua abrindo a abstenção.
   * Devolve true se tratou.
   */
  /** Tecla `v`: toca a vinheta de abertura ou interrompe a que está no ar. */
  vinheta?(): void;
  boletim?(acao: "alternar" | "parar" | "anterior" | "seguinte"): boolean;
}

const JANELA = 900;
// b também espera a janela: b + a é a Bahia.
const PREFIXOS = new Set(["a", "b", "m", "r"]);

export function ligarTeclado(a: AcoesTeclado, alvo: Window = window): () => void {
  const lerUf = criarLeitorUf(JANELA);
  let adiado: ReturnType<typeof setTimeout> | null = null;

  const cancelarAdiado = (): void => {
    if (adiado !== null) clearTimeout(adiado);
    adiado = null;
  };

  const comando = (k: string): void => {
    if (k === "a") a.auto();
    else if (k === "m") a.variante();
    else if (k === "r") a.refetch();
    else if (k === "z") a.zonas();
    else if (k === "f") a.tela_cheia();
    else if (k === "h") a.hud();
    else if (k === "x") a.irPara({ v: "exterior", uf: null, mun: null, zonas: false, zona: null });
    else if (k === "v") a.vinheta?.();
    else if (k === "b") a.boletim?.("alternar");
  };

  const aoTeclar = (ev: KeyboardEvent): void => {
    if (ev.ctrlKey && !ev.metaKey && !ev.altKey && ev.code === "KeyB") {
      if (a.boletim?.("parar")) ev.preventDefault();
      return;
    }
    if (ev.ctrlKey || ev.metaKey || ev.altKey) return;
    if (a.paletaAberta()) {
      if (ev.key === "Escape") {
        a.paleta(false);
        ev.preventDefault();
      }
      return; // a paleta trata as próprias teclas
    }
    const alvoEv = ev.target as HTMLElement | null;
    if (alvoEv && (alvoEv.tagName === "INPUT" || alvoEv.tagName === "TEXTAREA")) return;

    const k = ev.key;
    let tratou = true;
    if (k === "ArrowRight") a.proxima();
    else if (k === "ArrowLeft") a.anterior();
    else if (k === " ") a.pausar();
    else if (k === "Backspace") {
      // A tela pode tratar a subida dentro dela (exterior: da cidade para o agregado).
      if (!a.teclaDaTela(k)) a.subir();
    }
    else if (k === "/") a.paleta(true);
    else if (k === "Escape") a.paleta(false);
    else if (k === "ArrowUp" || k === "ArrowDown") tratou = a.teclaDaTela(k);
    else if (k === "," || k === ".") tratou = a.teclaDaTela(k);
    else if (k === "[") tratou = a.boletim?.("anterior") ?? false;
    else if (k === "]") tratou = a.boletim?.("seguinte") ?? false;
    else if (/^[0-9]$/.test(k)) {
      const d = destinoDoDigito(k, a.ufAtual(), a.turno());
      if (d) a.irPara(d);
    } else if (ev.shiftKey && (k === "B" || k === "b") && a.boletim?.("parar")) {
      cancelarAdiado();
    } else if (ev.shiftKey && destinoDaTecla2T(k)) {
      // Shift + letra abre as telas do 2º turno sem disputar a letra com as siglas de UF.
      cancelarAdiado();
      const d = destinoDaTecla2T(k);
      if (d) a.irPara(d);
    } else if (/^[a-z]$/i.test(k)) {
      const letra = k.toLowerCase();
      const uf = lerUf(letra, performance.now());
      if (uf && ehUf(uf)) {
        cancelarAdiado();
        a.irParaUf(uf);
      } else if (PREFIXOS.has(letra)) {
        cancelarAdiado();
        adiado = setTimeout(() => {
          adiado = null;
          comando(letra);
        }, JANELA);
      } else {
        cancelarAdiado();
        comando(letra);
      }
    } else tratou = false;
    if (tratou) ev.preventDefault();
  };

  alvo.addEventListener("keydown", aoTeclar);
  return () => {
    cancelarAdiado();
    alvo.removeEventListener("keydown", aoTeclar);
  };
}
