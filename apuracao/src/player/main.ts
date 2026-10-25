// Player do boletim falado para a live: browser source do OBS em /boletim.html. Assina o SSE
// (/events?so=boletim), toca o mp3 quando o diretor manda pôr no ar, mostra uma tarja discreta com
// barra de progresso e avisa o servidor no fim. Desde 25/10 é a reserva: o telão toca o boletim no
// próprio widget e, aberto no mesmo navegador, este player cede a vez. Parâmetros: tarja=0 (só
// áudio), pos=bl|br|tl|tr, vol=0..1, forcar=1 (toca mesmo com o telão tocando). No OBS o autoplay não pede gesto; num Chrome comum aparece "clique para liberar o áudio".

import "./player.css";

interface EventoBoletim {
  kind: string;
  id: string;
  hora?: string;
  desde?: string;
  duracao_s?: number | null;
}

interface Lista {
  no_ar: { id: string; desde: string; duracao_s: number | null; hora: string | null; decorrido_s: number } | null;
}

const params = new URLSearchParams(location.search);
const comTarja = params.get("tarja") !== "0";
const pos = /^(bl|br|tl|tr)$/.test(params.get("pos") ?? "") ? (params.get("pos") as string) : "bl";
const vol = Math.min(1, Math.max(0, Number(params.get("vol") ?? "1") || 0));

const raiz = document.getElementById("player") ?? document.body;
raiz.dataset.pos = pos;
raiz.innerHTML = `
  <div class="tarja" hidden>
    <span class="tarja-ponto" aria-hidden="true"></span>
    <div class="tarja-texto"><strong class="tarja-titulo"></strong><span class="tarja-marca">Arvor Intelligence</span></div>
    <div class="tarja-barra"><i></i></div>
  </div>
  <button class="gesto" type="button" hidden>clique para liberar o áudio do boletim</button>`;
const tarja = raiz.querySelector(".tarja") as HTMLElement;
const titulo = raiz.querySelector(".tarja-titulo") as HTMLElement;
const barra = raiz.querySelector(".tarja-barra i") as HTMLElement;
const gesto = raiz.querySelector(".gesto") as HTMLButtonElement;

// Um player só: se o telão (mesmo navegador) estiver tocando o boletim, este cede, salvo ?forcar=1.
const forcar = params.get("forcar") === "1";
let telaoVistoEm = 0;
if (typeof BroadcastChannel !== "undefined") {
  const canal = new BroadcastChannel("apuracao");
  canal.onmessage = ev => {
    const d = ev.data as { tipo?: unknown; audio?: unknown } | null;
    if (d && d.tipo === "boletim-telao" && d.audio === true) telaoVistoEm = Date.now();
  };
}
const telaoTocando = (): boolean => !forcar && Date.now() - telaoVistoEm < 5000;

const audio = new Audio();
audio.preload = "auto";
audio.volume = vol;
let atual: { id: string; desde: string } | null = null;

const avisarFim = (id: string, motivo: string): void => {
  void fetch(`/api/boletins/${encodeURIComponent(id)}/fim`, { method: "POST", headers: { "x-apuracao": "boletim", "content-type": "application/json" }, body: JSON.stringify({ motivo }) }).catch(() => undefined);
};

const esconder = (): void => {
  tarja.hidden = true;
  barra.style.width = "0%";
  document.body.dataset.tocando = "0";
};

function parar(id?: string): void {
  if (!atual || (id !== undefined && atual.id !== id)) return;
  atual = null;
  audio.pause();
  esconder();
}

function tocar(id: string, hora: string | null | undefined, desde: string): void {
  if (atual && atual.id === id && atual.desde === desde) return;
  if (telaoTocando()) return;
  atual = { id, desde };
  const deslocamento = (Date.now() - Date.parse(desde)) / 1000;
  audio.src = `/boletins/${encodeURIComponent(id)}.mp3?v=${encodeURIComponent(desde)}`;
  // Recarga da fonte no meio do boletim: retoma do ponto em que o boletim está no ar.
  const retomar = deslocamento > 3 ? deslocamento - 0.5 : 0;
  audio.addEventListener(
    "loadedmetadata",
    () => {
      if (retomar > 0 && retomar < audio.duration - 1) audio.currentTime = retomar;
    },
    { once: true },
  );
  titulo.textContent = `Boletim das ${hora ?? `${id.slice(0, 2)}:${id.slice(2, 4)}`}`;
  tarja.hidden = !comTarja;
  document.body.dataset.tocando = "1";
  audio.play().then(
    () => {
      gesto.hidden = true;
    },
    (e: unknown) => {
      if (e instanceof DOMException && e.name === "NotAllowedError") gesto.hidden = false;
    },
  );
}

gesto.addEventListener("click", () => {
  gesto.hidden = true;
  if (atual) void audio.play().catch(() => undefined);
});

audio.addEventListener("timeupdate", () => {
  if (audio.duration > 0) barra.style.width = `${Math.min(100, (100 * audio.currentTime) / audio.duration).toFixed(2)}%`;
});
audio.addEventListener("ended", () => {
  const a = atual;
  atual = null;
  esconder();
  if (a) avisarFim(a.id, "terminou");
});
audio.addEventListener("error", () => {
  const a = atual;
  atual = null;
  esconder();
  if (a) avisarFim(a.id, "erro_no_player");
});

async function sincronizar(): Promise<void> {
  try {
    const r = await fetch("/api/boletins", { cache: "no-store" });
    if (!r.ok) return;
    const l = (await r.json()) as Lista;
    if (l.no_ar) {
      const dur = l.no_ar.duracao_s ?? 600;
      if (l.no_ar.decorrido_s < dur - 1) tocar(l.no_ar.id, l.no_ar.hora, l.no_ar.desde);
    } else if (atual) parar();
  } catch {
    // servidor fora: tenta na próxima reconexão
  }
}

const es = new EventSource("/events?so=boletim");
es.onopen = () => void sincronizar();
es.addEventListener("boletim", ev => {
  let d: EventoBoletim;
  try {
    d = JSON.parse(String((ev as MessageEvent).data)) as EventoBoletim;
  } catch {
    return;
  }
  if (d.kind === "no_ar" && d.desde) tocar(d.id, d.hora, d.desde);
  else if (d.kind === "fim" || d.kind === "descartado") parar(d.id);
});

// Para o QA (Playwright): estado do player.
(window as unknown as { boletimPlayer: unknown }).boletimPlayer = {
  estado: () => ({ id: atual?.id ?? null, tocando: !audio.paused, tempo: audio.currentTime, duracao: audio.duration, tarja: !tarja.hidden, gesto: !gesto.hidden, barra: barra.style.width }),
  irPara: (s: number) => {
    audio.currentTime = s;
  },
};
