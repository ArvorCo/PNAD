// Mapa de teclas do plano. Letras de comando que também iniciam sigla de UF
// (a de AC/AL/AM/AP, m de MA/MG/MS/MT, r de RJ/RN/RO/RR/RS) esperam a janela de
// 900 ms: se a segunda letra fechar uma UF, vale a UF; senão, roda o comando.

import { criarLeitorUf, destinoDoDigito, ehUf } from "./navegacao.ts";
import type { Destino } from "./navegacao.ts";

export interface AcoesTeclado {
  ufAtual(): string | null;
  telaAtual(): string;
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
}

const JANELA = 900;
const PREFIXOS = new Set(["a", "m", "r"]);

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
  };

  const aoTeclar = (ev: KeyboardEvent): void => {
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
    else if (/^[0-9]$/.test(k)) {
      const d = destinoDoDigito(k, a.ufAtual());
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
