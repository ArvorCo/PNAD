// Widget "Boletim Arvor" do telão, operado com o mouse: lista dos últimos boletins falados com
// botão de tocar em cada item (inclusive os já tocados), pausar/retomar e parar no item no ar,
// barra de progresso clicável para avançar, próximo ciclo e alerta de boletim novo. O áudio toca
// aqui mesmo (o OBS precisa de "Control audio via OBS" na fonte do telão). Teclas b, Shift+B,
// [ e ] são atalho secundário.
// REGRA: nunca há play automático. Boletim pronto só acende o alerta; o áudio começa apenas com o
// evento `no_ar`, que o servidor só emite por ação humana (clique no widget, tecla, "tocar" no
// diretor). Sem fila e sem tocar o próximo ao terminar. Todo item com áudio toca de novo: "tocado"
// é rótulo, não bloqueio. A única retomada é a do mesmo boletim no ar quando o telão recarrega.
// Formato: cartão aberto nas telas com o canto livre, no alerta e quando aberto pelo mouse; nas
// demais, pílula na faixa inferior com os mesmos botões. #boletim=0 desliga o áudio do telão
// (usar só o boletim.html); #boletimw=aberto|compacto fixa o formato; #som=1 liga o toque do alerta.

import { EVENTO_BOLETIM } from "./ticker.ts";

interface Item {
  id: string;
  hora: string;
  estado: "gerando" | "pronto" | "no_ar" | "tocado" | "erro" | "descartado";
  duracao_s: number | null;
}

interface Lista {
  gerador: { vivo: boolean; proximo_ciclo_em?: string | null; relogio_ligado?: boolean };
  no_ar: { id: string; hora: string | null; desde: string; duracao_s: number | null } | null;
  itens: Item[];
}

interface Detalhe {
  kind: string;
  id: string;
  hora?: string;
  desde?: string;
  duracao_s?: number | null;
  motivo?: string;
}

export type AcaoBoletim = "alternar" | "parar" | "anterior" | "seguinte";

export interface BoletimWidget {
  el: HTMLElement;
  /** Tecla do telão; devolve true se tratou (Shift+B só para quando há boletim carregado). */
  tecla(acao: AcaoBoletim): boolean;
  /** Tela atual: decide compacto ou aberto. */
  tela(id: string): void;
}

export interface OpcoesBoletim {
  /** Toca o áudio no telão (padrão); false deixa o boletim.html tocar. */
  audio: boolean;
  /** Toque discreto no alerta de boletim novo. */
  som: boolean;
  formato: "auto" | "aberto" | "compacto";
  /** Linha no ticker quando um boletim fica pronto. */
  aoNovo: (texto: string) => void;
}

/** Telas cujo canto inferior direito fica livre: o cartão pode ficar aberto. */
const CANTO_LIVRE: ReadonlySet<string> = new Set(["regioes", "pausas", "paralela", "alertas", "espera"]);
const ALERTA_MS = 20_000;
const ESCOLHA_MS = 15_000;
const ROTULO: Readonly<Record<Item["estado"], string>> = { gerando: "gerando", pronto: "pronto", no_ar: "no ar", tocado: "tocado", erro: "erro", descartado: "descartado" };
const HEADERS = { "x-apuracao": "boletim", "content-type": "application/json" };
const PLAY = "▶";
const PAUSA = "❚❚";
const PARAR = "■";

function mmss(s: number | null | undefined): string {
  if (s === null || s === undefined || !Number.isFinite(s)) return "-";
  const t = Math.max(0, Math.round(s));
  return `${Math.floor(t / 60)}:${String(t % 60).padStart(2, "0")}`;
}

const horaBrt = (iso: string): string => new Date(iso).toLocaleTimeString("pt-BR", { timeZone: "America/Sao_Paulo", hour: "2-digit", minute: "2-digit" });

function bip(): void {
  try {
    const ctx = new AudioContext();
    const nota = (freq: number, t0: number): void => {
      const o = ctx.createOscillator();
      const g = ctx.createGain();
      o.frequency.value = freq;
      g.gain.setValueAtTime(0.0001, ctx.currentTime + t0);
      g.gain.exponentialRampToValueAtTime(0.06, ctx.currentTime + t0 + 0.02);
      g.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + t0 + 0.35);
      o.connect(g).connect(ctx.destination);
      o.start(ctx.currentTime + t0);
      o.stop(ctx.currentTime + t0 + 0.4);
    };
    nota(880, 0);
    nota(1320, 0.18);
    setTimeout(() => void ctx.close(), 1200);
  } catch {
    // sem áudio: o alerta visual basta
  }
}

function botao(classe: string, texto: string, rotulo: string): HTMLButtonElement {
  const b = document.createElement("button");
  b.type = "button";
  b.className = `bolw-b ${classe}`;
  b.textContent = texto;
  b.title = rotulo;
  b.setAttribute("aria-label", rotulo);
  return b;
}

export function criarBoletimWidget(o: OpcoesBoletim): BoletimWidget {
  const el = document.createElement("div");
  el.className = "bolw";
  el.dataset.modo = "compacto";

  // ---------- pílula (faixa inferior) ----------
  const pill = document.createElement("div");
  pill.className = "bolw-pill";
  const pillPlay = botao("bolw-pill-play", PLAY, "tocar ou pausar o boletim");
  const pillAbrir = document.createElement("button");
  pillAbrir.type = "button";
  pillAbrir.className = "bolw-pill-abrir";
  pillAbrir.title = "abrir a lista de boletins";
  pillAbrir.innerHTML = `<span class="bolw-ponto"></span><strong>Boletim Arvor</strong><span class="bolw-pill-txt"></span>`;
  const pillTxt = pillAbrir.querySelector(".bolw-pill-txt") as HTMLElement;
  const pillParar = botao("bolw-pill-parar", PARAR, "parar o boletim");
  const pillBarra = document.createElement("span");
  pillBarra.className = "bolw-pill-barra";
  pillBarra.innerHTML = "<i></i>";
  const pillBarraI = pillBarra.firstElementChild as HTMLElement;
  pill.append(pillPlay, pillAbrir, pillParar, pillBarra);

  // ---------- cartão ----------
  const card = document.createElement("div");
  card.className = "bolw-card";
  card.innerHTML = `
    <div class="bolw-topo"><strong>Boletim Arvor</strong></div>
    <div class="bolw-status"><span class="bolw-proximo"></span><span class="bolw-alerta" hidden></span></div>
    <ol class="bolw-lista"></ol>
    <div class="bolw-tocando" hidden><div class="bolw-barra" role="slider" aria-label="avançar no boletim" title="clique para avançar"><i></i></div><span class="bolw-tempo"></span></div>`;
  const topo = card.querySelector(".bolw-topo") as HTMLElement;
  const recolher = botao("bolw-recolher", "▾", "recolher a lista");
  topo.append(recolher);
  const status = card.querySelector(".bolw-status") as HTMLElement;
  const proximo = card.querySelector(".bolw-proximo") as HTMLElement;
  const alerta = card.querySelector(".bolw-alerta") as HTMLElement;
  const gesto = botao("bolw-gesto", "clique para liberar o áudio", "liberar o áudio do boletim");
  gesto.hidden = true;
  status.append(gesto);
  const lista = card.querySelector(".bolw-lista") as HTMLOListElement;
  const tocando = card.querySelector(".bolw-tocando") as HTMLElement;
  const barraEl = card.querySelector(".bolw-barra") as HTMLElement;
  const barra = barraEl.firstElementChild as HTMLElement;
  const tempo = card.querySelector(".bolw-tempo") as HTMLElement;
  el.append(pill, card);

  const audio = new Audio();
  audio.preload = "auto";
  let atual: { id: string; hora: string; desde: string } | null = null;
  // Instante de "no ar" que o telão já soltou (fim, parar): uma leitura atrasada da lista não o religa.
  let solto: string | null = null;
  let ultima: Lista | null = null;
  let telaAtual = "";
  let alertaAte = 0;
  let conhecidos: Set<string> | null = null;
  let timerAlerta: ReturnType<typeof setTimeout> | null = null;
  // Item escolhido com [ e ]; o cartão fica aberto enquanto a escolha vale.
  let escolhido: string | null = null;
  let escolhaAte = 0;
  // Aberto ou recolhido pelo mouse; null segue a regra da tela.
  let manual: "aberto" | "compacto" | null = null;
  let assinaturaLista = "";
  const tocavel = (i: Item): boolean => i.estado !== "gerando" && i.estado !== "erro";

  // Um player só: o telão avisa o boletim.html (mesmo navegador) de que está tocando.
  const canal = typeof BroadcastChannel !== "undefined" ? new BroadcastChannel("apuracao") : null;
  if (o.audio && canal) {
    const bater = (): void => canal.postMessage({ tipo: "boletim-telao", audio: true, em: Date.now() });
    bater();
    setInterval(bater, 2000);
  }

  const post = (caminho: string, corpo: unknown = {}): Promise<Response | null> =>
    fetch(caminho, { method: "POST", headers: HEADERS, body: JSON.stringify(corpo) }).catch(() => null);

  /** Posição e duração do que toca: o áudio local ou, sem áudio no telão, o relógio do servidor. */
  const progresso = (): { pos: number; dur: number | null } | null => {
    if (atual && Number.isFinite(audio.duration)) return { pos: audio.currentTime, dur: audio.duration };
    const n = ultima?.no_ar;
    if (!o.audio && n) return { pos: (Date.now() - Date.parse(n.desde)) / 1000, dur: n.duracao_s };
    return null;
  };

  const linha = (i: Item): HTMLLIElement => {
    const li = document.createElement("li");
    li.dataset.estado = i.estado;
    li.dataset.id = i.id;
    if (i.id === escolhido) li.dataset.escolhido = "1";
    const txt = document.createElement("span");
    txt.className = "bolw-li-txt";
    txt.innerHTML = `<span class="bolw-h"></span><span class="bolw-d"></span><span class="bolw-e"></span>`;
    (txt.children[0] as HTMLElement).textContent = i.hora;
    (txt.children[1] as HTMLElement).textContent = mmss(i.duracao_s);
    (txt.children[2] as HTMLElement).textContent = ROTULO[i.estado];
    const acoes = document.createElement("span");
    acoes.className = "bolw-li-acoes";
    if (atual?.id === i.id) {
      const pp = botao("bolw-li-pausa", audio.paused ? PLAY : PAUSA, audio.paused ? "retomar o boletim" : "pausar o boletim");
      pp.addEventListener("click", () => alternarLocal());
      const st = botao("bolw-li-parar", PARAR, "parar o boletim");
      st.addEventListener("click", () => parar());
      acoes.append(pp, st);
    } else if (tocavel(i)) {
      const tp = botao("bolw-li-tocar", PLAY, `tocar o boletim das ${i.hora}`);
      tp.addEventListener("click", () => pedirTocar(i.id));
      acoes.append(tp);
      if (!o.audio && ultima?.no_ar?.id === i.id) {
        const st = botao("bolw-li-parar", PARAR, "parar o boletim");
        st.addEventListener("click", () => parar());
        acoes.append(st);
      }
    }
    li.append(txt, acoes);
    return li;
  };

  const desenhar = (): void => {
    const l = ultima;
    const agora = Date.now();
    const temAlerta = agora < alertaAte;
    const carregado = atual !== null;
    const noArServidor = l?.no_ar ?? null;
    if (escolhido && agora > escolhaAte) escolhido = null;
    const automatico = o.formato === "aberto" || temAlerta || escolhido !== null || CANTO_LIVRE.has(telaAtual);
    const aberto = !gesto.hidden || (manual ?? (o.formato === "compacto" ? "compacto" : automatico ? "aberto" : "compacto")) === "aberto";
    el.dataset.modo = aberto ? "aberto" : "compacto";
    el.dataset.alerta = temAlerta ? "1" : "0";
    const tocandoAgora = carregado && !audio.paused;
    el.dataset.tocando = tocandoAgora || (!o.audio && noArServidor !== null) ? "1" : "0";
    pillPlay.textContent = tocandoAgora ? PAUSA : PLAY;
    pillPlay.title = tocandoAgora ? "pausar o boletim" : carregado ? "retomar o boletim" : "tocar o último boletim pronto";
    pillParar.hidden = !(carregado || noArServidor !== null);
    const prox = l?.gerador.proximo_ciclo_em ? `próximo às ${horaBrt(l.gerador.proximo_ciclo_em)}` : l?.gerador.vivo === false ? "gerador fora do ar" : "relógio desligado";
    proximo.textContent = prox;
    proximo.hidden = temAlerta;
    alerta.hidden = !temAlerta;

    const todos = l?.itens ?? [];
    const idxEscolhido = escolhido ? todos.findIndex(i => i.id === escolhido) : -1;
    const inicio = idxEscolhido >= 4 ? idxEscolhido - 3 : 0;
    const itens = todos.slice(inicio, inicio + 4);
    // Só reconstrói os botões quando algo muda (nunca a cada quadro: o clique precisa do mesmo botão).
    const assinatura = JSON.stringify([itens.map(i => [i.id, i.estado, i.duracao_s, i.hora]), escolhido, atual?.id ?? null, audio.paused, o.audio ? null : (noArServidor?.id ?? null)]);
    if (assinatura !== assinaturaLista) {
      assinaturaLista = assinatura;
      lista.replaceChildren(...itens.map(linha));
      if (itens.length === 0) {
        const li = document.createElement("li");
        li.className = "bolw-vazio";
        li.textContent = "nenhum boletim ainda";
        lista.append(li);
      }
    }

    const p = progresso();
    tocando.hidden = p === null;
    const largura = p && p.dur ? `${Math.min(100, (100 * p.pos) / p.dur).toFixed(1)}%` : "0%";
    barra.style.width = largura;
    pillBarraI.style.width = largura;
    if (p) tempo.textContent = `${mmss(p.pos)} / ${mmss(p.dur)}`;
    const ult = todos[0];
    const proxCurto = l?.gerador.proximo_ciclo_em ? `próximo ${horaBrt(l.gerador.proximo_ciclo_em)}` : prox;
    if (carregado && atual) pillTxt.textContent = `${atual.hora} ${audio.paused ? "pausado" : "no ar"} ${mmss(p?.pos)} / ${mmss(p?.dur)}`;
    else if (noArServidor) pillTxt.textContent = `${noArServidor.hora ?? noArServidor.id} no ar${p ? ` ${mmss(p.pos)} / ${mmss(p.dur)}` : ""}`;
    else if (temAlerta && ult) pillTxt.textContent = `novo boletim das ${ult.hora}`;
    else pillTxt.textContent = [ult ? `${ult.hora} ${ROTULO[ult.estado]}` : "", proxCurto].filter(Boolean).join(" · ");
  };

  const sincronizar = async (): Promise<void> => {
    try {
      const r = await fetch("/api/boletins", { cache: "no-store" });
      if (!r.ok) return;
      const l = (await r.json()) as Lista;
      ultima = l;
      // Boletim novo que o SSE não avisou (reconexão): alerta pelo diff da lista. Só alerta.
      const prontos = l.itens.filter(i => i.estado === "pronto").map(i => i.id);
      if (conhecidos) for (const id of prontos) if (!conhecidos.has(id)) novo(l.itens.find(i => i.id === id)?.hora ?? id);
      conhecidos = new Set(l.itens.map(i => i.id));
      // Retomada do mesmo boletim que um humano pôs no ar (telão recarregado no meio dele).
      if (l.no_ar && o.audio && (!atual || atual.id !== l.no_ar.id || atual.desde !== l.no_ar.desde)) {
        const dur = l.no_ar.duracao_s ?? 600;
        if ((Date.now() - Date.parse(l.no_ar.desde)) / 1000 < dur - 1) tocar(l.no_ar.id, l.no_ar.hora ?? l.no_ar.id, l.no_ar.desde);
      }
      desenhar();
    } catch {
      // servidor fora: mantém o último quadro
    }
  };

  /** Boletim novo pronto: só alerta, ticker e toque opcional. Nunca chama tocar(). */
  function novo(hora: string): void {
    alertaAte = Date.now() + ALERTA_MS;
    alerta.textContent = `novo boletim das ${hora}`;
    o.aoNovo(`novo boletim das ${hora} pronto para ir ao ar`);
    if (o.som) bip();
    if (timerAlerta !== null) clearTimeout(timerAlerta);
    timerAlerta = setTimeout(desenhar, ALERTA_MS + 50);
    desenhar();
  }

  /** Toca o que o servidor pôs no ar (evento no_ar). */
  function tocar(id: string, hora: string, desde: string): void {
    if (!o.audio || desde === solto) return;
    if (atual && atual.id === id && atual.desde === desde) return;
    atual = { id, hora, desde };
    const deslocamento = (Date.now() - Date.parse(desde)) / 1000;
    const retomar = deslocamento > 3 ? deslocamento - 0.5 : 0;
    audio.src = `/boletins/${encodeURIComponent(id)}.mp3?v=${encodeURIComponent(desde)}`;
    audio.addEventListener(
      "loadedmetadata",
      () => {
        if (retomar > 0 && retomar < audio.duration - 1) audio.currentTime = retomar;
      },
      { once: true },
    );
    audio.play().then(
      () => {
        gesto.hidden = true;
        desenhar();
      },
      (e: unknown) => {
        if (e instanceof DOMException && e.name === "NotAllowedError") gesto.hidden = false;
        desenhar();
      },
    );
    desenhar();
  }

  function soltar(): void {
    if (atual) solto = atual.desde;
    atual = null;
    audio.pause();
    audio.removeAttribute("src");
    audio.load();
    gesto.hidden = true;
    desenhar();
  }

  /** Pede ao servidor para pôr no ar (ação humana); o áudio começa no evento no_ar. */
  function pedirTocar(id: string): void {
    escolhido = null;
    void post(`/api/boletins/${encodeURIComponent(id)}/tocar`).then(() => sincronizar());
    desenhar();
  }

  function alternarLocal(): void {
    if (!atual) return;
    if (audio.paused) void audio.play().catch(() => undefined);
    else audio.pause();
    desenhar();
  }

  function parar(): boolean {
    if (!atual && !ultima?.no_ar) return false;
    if (ultima?.no_ar) solto = ultima.no_ar.desde;
    soltar();
    void post("/api/boletins/parar").then(() => sincronizar());
    return true;
  }

  /** Alvo padrão: último pronto ainda não tocado; sem ele, o mais recente com áudio. */
  function tocarPadrao(): void {
    const alvo = ultima?.itens.find(i => i.estado === "pronto") ?? ultima?.itens.find(tocavel);
    if (alvo) pedirTocar(alvo.id);
    else {
      alerta.textContent = "nenhum boletim com áudio";
      alertaAte = Date.now() + 4000;
      setTimeout(desenhar, 4100);
      desenhar();
    }
  }

  // ---------- mouse ----------
  pillPlay.addEventListener("click", () => {
    if (atual) alternarLocal();
    else tocarPadrao();
  });
  pillParar.addEventListener("click", () => void parar());
  pillAbrir.addEventListener("click", () => {
    manual = "aberto";
    desenhar();
  });
  recolher.addEventListener("click", () => {
    manual = "compacto";
    escolhido = null;
    desenhar();
  });
  gesto.addEventListener("click", () => {
    gesto.hidden = true;
    if (atual) void audio.play().catch(() => undefined);
    desenhar();
  });
  barraEl.addEventListener("click", ev => {
    if (!atual || !Number.isFinite(audio.duration)) return;
    const r = barraEl.getBoundingClientRect();
    const f = Math.min(1, Math.max(0, (ev.clientX - r.left) / Math.max(1, r.width)));
    audio.currentTime = f * audio.duration;
    desenhar();
  });

  audio.addEventListener("timeupdate", desenhar);
  audio.addEventListener("pause", desenhar);
  audio.addEventListener("play", desenhar);
  audio.addEventListener("ended", () => {
    const a = atual;
    soltar();
    if (a) void post(`/api/boletins/${encodeURIComponent(a.id)}/fim`, { motivo: "terminou" }).then(() => sincronizar());
  });
  audio.addEventListener("error", () => {
    const a = atual;
    if (!a) return;
    soltar();
    void post(`/api/boletins/${encodeURIComponent(a.id)}/fim`, { motivo: "erro_no_telao" });
  });

  document.addEventListener(EVENTO_BOLETIM, ev => {
    const d = (ev as CustomEvent<Detalhe>).detail;
    if (!d) return;
    if (d.kind === "pronto") novo(d.hora ?? d.id);
    else if (d.kind === "no_ar" && d.desde) tocar(d.id, d.hora ?? d.id, d.desde);
    else if ((d.kind === "fim" || d.kind === "descartado") && atual?.id === d.id) {
      // Encerramento pelo relógio do servidor durante uma pausa local: o telão segura o áudio.
      const resta = Number.isFinite(audio.duration) ? audio.duration - audio.currentTime : 0;
      if (!(d.motivo === "tempo" && resta > 2)) soltar();
    }
    void sincronizar();
  });

  // ---------- teclas (atalho secundário) ----------
  function tecla(acao: AcaoBoletim): boolean {
    if (acao === "anterior" || acao === "seguinte") {
      const lista2 = (ultima?.itens ?? []).filter(tocavel);
      if (lista2.length === 0) return true;
      const k = escolhido ? lista2.findIndex(i => i.id === escolhido) : -1;
      const prox2 = k < 0 ? 0 : acao === "seguinte" ? Math.min(lista2.length - 1, k + 1) : Math.max(0, k - 1);
      escolhido = lista2[prox2]?.id ?? null;
      escolhaAte = Date.now() + ESCOLHA_MS;
      setTimeout(desenhar, ESCOLHA_MS + 100);
      desenhar();
      return true;
    }
    if (acao === "parar") return parar();
    if (escolhido && Date.now() <= escolhaAte && escolhido !== atual?.id) {
      pedirTocar(escolhido);
      return true;
    }
    if (atual) alternarLocal();
    else tocarPadrao();
    return true;
  }

  void sincronizar();
  setInterval(() => void sincronizar(), 5000);
  setInterval(() => {
    if (!o.audio && ultima?.no_ar) desenhar();
  }, 1000);
  desenhar();

  // Para o QA (Playwright).
  (window as unknown as { boletimTelao: unknown }).boletimTelao = {
    estado: () => ({ id: atual?.id ?? null, tocando: atual !== null && !audio.paused, tempo: audio.currentTime, duracao: audio.duration, modo: el.dataset.modo, alerta: el.dataset.alerta, gesto: !gesto.hidden, escolhido }),
    irPara: (s: number) => {
      audio.currentTime = s;
    },
  };

  return {
    el,
    tecla,
    tela(id) {
      if (id === telaAtual) return;
      telaAtual = id;
      // Trocar de tela devolve o formato à regra da tela (o aberto pelo mouse vale até a próxima tela).
      manual = null;
      desenhar();
    },
  };
}
