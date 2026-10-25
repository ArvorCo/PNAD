// Vinheta de abertura do 2º turno: vídeo em tela cheia sobre o telão, às 17:00:00 em ponto.
// Disparo automático único (relógio do telão contra T0_2T_MS), só se o arquivo existir e sem
// `#vinheta=0`; `localStorage` guarda que já tocou. `#vinheta=1` força ao carregar (teste, cai no
// teste.mp4 se a abertura não existir); `#vinheta=teste` toca sempre o teste.mp4; `v` e o diretor alternam. Enquanto toca, a rotação e o
// boletim ficam suspensos; ao fim, o telão volta de onde estava.

import { T0_2T_MS } from "../../turno2/comum.ts";

export const ARQUIVO_VINHETA = "vinheta/abertura.mp4";
const ARQUIVO_TESTE = "vinheta/teste.mp4";
const CHAVE = "apuracao-vinheta-tocou";

export interface OpcoesVinheta {
  /** Hash da carga da página (`#vinheta=0|1`). */
  hash: string;
  /** Suspende (true) ou devolve (false) rotação e boletim. */
  suspender(sim: boolean): void;
  agora?: () => number;
}

export interface Vinheta {
  tocando(): boolean;
  alternar(valor?: boolean): void;
}

async function existe(url: string): Promise<boolean> {
  try {
    const r = await fetch(url, { method: "HEAD", cache: "no-store" });
    return r.ok;
  } catch {
    return false;
  }
}

function jaTocou(): boolean {
  try {
    return localStorage.getItem(CHAVE) === "1";
  } catch {
    return false;
  }
}

function marcarTocou(): void {
  try {
    localStorage.setItem(CHAVE, "1");
  } catch {
    // sem armazenamento: o disparo único vale só nesta carga
  }
}

export function criarVinheta(o: OpcoesVinheta): Vinheta {
  const agora = o.agora ?? Date.now;
  const param = new URLSearchParams(o.hash.replace(/^#/, "")).get("vinheta");
  const raiz = document.createElement("div");
  raiz.className = "vinheta";
  raiz.hidden = true;
  const video = document.createElement("video");
  video.className = "vinheta-video";
  video.playsInline = true;
  video.preload = "auto";
  const botao = document.createElement("button");
  botao.type = "button";
  botao.className = "vinheta-tocar";
  botao.textContent = "tocar vinheta";
  botao.hidden = true;
  raiz.append(video, botao);
  document.body.append(raiz);

  let ativa = false;
  let pronto: string | null = null;

  const fim = (): void => {
    if (!ativa) return;
    ativa = false;
    video.pause();
    raiz.hidden = true;
    botao.hidden = true;
    raiz.dataset.tocando = "0";
    o.suspender(false);
  };

  const iniciar = (url: string): void => {
    if (ativa) return;
    ativa = true;
    o.suspender(true);
    raiz.hidden = false;
    raiz.dataset.tocando = "1";
    if (!video.src.endsWith(url)) video.src = url;
    video.currentTime = 0;
    video.muted = false;
    video.play().then(
      () => {
        botao.hidden = true;
      },
      (e: unknown) => {
        if (e instanceof DOMException && e.name === "NotAllowedError") botao.hidden = false;
        else fim();
      },
    );
  };

  const resolver = async (comTeste: boolean): Promise<string | null> => {
    if (await existe(ARQUIVO_VINHETA)) return ARQUIVO_VINHETA;
    if (comTeste && (await existe(ARQUIVO_TESTE))) return ARQUIVO_TESTE;
    return null;
  };

  video.addEventListener("ended", fim);
  video.addEventListener("error", fim);
  botao.addEventListener("click", () => {
    botao.hidden = true;
    void video.play().catch(() => fim());
  });

  const alternar = (valor?: boolean): void => {
    const querTocar = valor ?? !ativa;
    if (!querTocar) {
      fim();
      return;
    }
    if (ativa) return;
    void resolver(false).then(url => {
      if (url) iniciar(url);
    });
  };

  // Disparo único às 17:00:00. Pré-carrega o vídeo antes para o primeiro quadro não atrasar.
  if (param !== "0" && !jaTocou()) {
    const falta = T0_2T_MS - agora();
    if (falta > 0 && falta < 36 * 3_600_000) {
      const pre = Math.max(0, falta - 60_000);
      setTimeout(() => {
        void resolver(false).then(url => {
          pronto = url;
          if (url) video.src = url;
        });
      }, pre);
      setTimeout(() => {
        if (jaTocou() || param === "0") return;
        const url = pronto ?? ARQUIVO_VINHETA;
        marcarTocou();
        void existe(url).then(ok => {
          if (ok) iniciar(url);
        });
      }, falta);
    }
  }
  if (param === "teste") iniciar(ARQUIVO_TESTE);
  else if (param === "1") {
    void resolver(true).then(url => {
      if (url) iniciar(url);
    });
  }

  (window as unknown as { vinhetaTelao: unknown }).vinhetaTelao = { tocando: () => ativa };
  return { tocando: () => ativa, alternar };
}
