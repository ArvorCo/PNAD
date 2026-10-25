// Boot do telão: configuração e ativos, casca, telas, roteador, teclado, rotação,
// diretor por BroadcastChannel e dados por SSE (ou polling, mock e replay).

import "./styles/tokens.css";
import "./styles/base.css";
import "./styles/layout.css";
import "./styles/motion.css";
import "./styles/majoritarias.css";
import "./styles/mapa.css";
import "./styles/legislativas.css";
import "./styles/exterior.css";
import "./styles/evolucao.css";
import "./styles/doist.css";

import { ativo, criarApi } from "./data/api.ts";
import type { Fonte } from "./data/api.ts";
import { campoDoPartido, CORES_PADRAO, normalizarCampos, normalizarCores } from "./data/cores.ts";
import { criarMock } from "./data/mock.ts";
import { lerParamsMock } from "./data/mock-hash.ts";
import { conectarSse } from "./data/sse.ts";
import type { EventoBoletimTelao } from "./data/sse.ts";
import { EVENTO_BOLETIM, EVENTO_TICKER_EXTRA } from "./components/ticker.ts";
import { criarBoletimWidget } from "./components/boletim.ts";
import type { BoletimWidget } from "./components/boletim.ts";
import { criarVinheta } from "./components/vinheta.ts";
import { preCarregar } from "./data/geo.ts";
import { abrirCanal, ehComando } from "./control/broadcast.ts";
import type { Comando, EspelhoTelao } from "./control/broadcast.ts";
import { ligarTeclado } from "./control/keyboard.ts";
import { baseDe, registrarRetomada, textoRetomada, versaoNova } from "./control/vigilia.ts";
import type { Base } from "./control/vigilia.ts";
import { horaCurta } from "./data/format.ts";
import { vigiarBundle } from "./control/recarga.ts";
import { destinoDaUf, subirNivel } from "./control/navegacao.ts";
import type { Destino } from "./control/navegacao.ts";
import { criarRotacao, PLAYLIST_PADRAO, playlistDoTurno } from "./control/rotation.ts";
import type { Entrada } from "./control/rotation.ts";
import { lerHash, ligarRoteador } from "./control/router.ts";
import type { UiHash } from "./control/router.ts";
import { criarIndice } from "./control/search.ts";
import type { Achado } from "./control/search.ts";
import { criarCarregador, eventoAfeta } from "./dados.ts";
import { montarShell } from "./shell.ts";
import { criarStore } from "./state/store.ts";
import type { Config, EventoSse, Need, Resultado, State } from "./state/types.ts";
import { aplicarTurno, registrarTelas } from "./views/index.ts";
import { TELAS_2T } from "./views/meta-2t.ts";
import { ligarPedidoDeDados, listar } from "./views/registry.ts";

const VIEW_POR_CARGO: Readonly<Record<number, string>> = { 1: "pres-uf", 3: "gov-uf", 5: "sen-uf", 6: "fed-uf", 7: "est-uf", 8: "dis-df" };

function estadoInicial(h: UiHash): State {
  return {
    config: null,
    doist: {},
    estado: null,
    resultados: {},
    mapas: {},
    series: {},
    lotes: {},
    anomalias: [],
    campos: normalizarCampos(null),
    cores: CORES_PADRAO,
    playlist: PLAYLIST_PADRAO,
    rede: { modo: h.mock ? "mock" : h.replay ? "replay" : "sse", conectado: false, ultimo_evento_em: null, ultimo_ok_em: null },
    ui: { ...h, pausado: false, paleta: false, indice: 0, dwellInicio: performance.now(), dwellMs: 20_000 },
  };
}

async function iniciar(): Promise<void> {
  const raiz = document.getElementById("telao");
  if (!raiz) return;
  const hash = lerHash(location.hash);
  const store = criarStore(estadoInicial(hash));
  registrarTelas();

  // Ativos estáticos e configuração em paralelo; nada disso bloqueia a casca.
  const [playlist, playlist2t, campos, cores] = await Promise.all([
    ativo<unknown>("/playlist.json"),
    ativo<unknown>("/playlist-2t.json"),
    ativo<unknown>("/campos.json"),
    ativo<unknown>("/cores.json"),
  ]);
  store.patch("campos", normalizarCampos(campos));
  store.patch("cores", normalizarCores(cores));

  const api = criarApi("", hash.replay ? relogioReplay(hash.replay.inicio, hash.replay.speed) : () => null);
  let config: Config | null = null;
  try {
    config = await api.config();
  } catch {
    config = null; // sem servidor: o mock usa a amostra embutida
  }
  // Ensaio: o 2º turno é o padrão (o 1º já passou); `turno=1`, `t0`, `falha` e `sem1t` ajustam o mock.
  const mockParams = lerParamsMock(location.hash);
  const fonte: Fonte = hash.mock
    ? criarMock({
        speed: hash.speed,
        config,
        turno: mockParams.turno,
        falhas: mockParams.falhas,
        sem1t: mockParams.sem1t,
        congelar: mockParams.congelar,
        ...(mockParams.inicioMin !== null ? { inicioMin: mockParams.inicioMin } : {}),
        campoDe: sg => campoDoPartido(sg, store.get().campos),
      })
    : api;
  if (!config || hash.mock) config = await fonte.config().catch(() => config);
  if (config) store.patch("config", config);
  // O turno decide a playlist (a do 2º turno vem de playlist-2t.json ou do contrato) e o rótulo do duelo.
  const turno = config?.turno ?? 1;
  store.patch("playlist", playlistDoTurno(turno, playlist, playlist2t));
  aplicarTurno(turno);

  const indice = criarIndice();
  if (config) indice.adicionarConfig(config);
  indice.adicionarTelas(TELAS_2T.map(t => ({ id: t.id, rotulo: t.titulo, atalho: t.atalho, busca: t.busca })));
  const indexados = new Set<string>();

  const carregador = criarCarregador(store, fonte, () => {
    // Mantém o último snapshot; a falha aparece no HUD pela hora da última leitura.
  });

  // ---------- telas ----------
  const shell = montarShell(raiz, indice, a => escolher(a), () => store.ui({ paleta: false }));
  let telaMontada = "";
  let assinaturaTela = "";

  const necessidades = (s: State): Need[] => {
    const v = shell.atual();
    const ns: Need[] = [{ tipo: "estado" }, { tipo: "anomalias" }];
    if (v) ns.push(...v.needs(s));
    return ns;
  };

  const montarSePreciso = (s: State): void => {
    const assinatura = `${s.ui.v}|${s.ui.uf ?? ""}|${s.ui.mun ?? ""}|${s.ui.zonas}|${s.ui.zona ?? ""}`;
    if (assinatura === assinaturaTela && telaMontada) return;
    assinaturaTela = assinatura;
    // Troca de UF, município ou zona dentro da mesma tela também remonta (crossfade).
    shell.trocar(s.ui.v, s);
    telaMontada = s.ui.v;
    carregador.carregarTodas(necessidades(s));
    preCarregar(s.ui.uf);
  };

  // ---------- navegação ----------
  const irPara = (d: Destino, manual = true): void => {
    store.ui({ ...d, ...(manual ? { auto: false } : {}) });
    rotacao.reiniciarDwell();
  };

  const aplicarEntrada = (e: Entrada): void => {
    store.ui({ v: e.v, uf: e.uf, mun: e.mun, zonas: false, zona: null });
  };

  const rotacao = criarRotacao({
    store,
    aplicar: aplicarEntrada,
    espera: () => store.ui({ v: "espera", uf: null, mun: null, zonas: false, zona: null }),
  });

  const escolher = (a: Achado): void => {
    if (a.tipo === "tela") irPara({ v: a.v, uf: null, mun: null, zonas: false, zona: null });
    else if (a.tipo === "uf") irPara(destinoDaUf(store.get().ui.v, a.uf));
    else if (a.tipo === "mun") irPara({ v: "mun", uf: a.uf, mun: a.cd, zonas: false, zona: null });
    else {
      const uf = a.abr.length >= 2 && a.abr !== "br" ? a.abr.slice(0, 2).toUpperCase() : null;
      if (!uf && a.cargo === 1) irPara({ v: "pres", uf: null, mun: null, zonas: false, zona: null });
      else if (uf) irPara(destinoDaUf(VIEW_POR_CARGO[a.cargo] ?? "pres-uf", uf));
    }
  };

  const recarregar = (): void => carregador.carregarTodas(necessidades(store.get()));
  ligarPedidoDeDados(recarregar);

  const tela_cheia = (): void => {
    if (document.fullscreenElement) void document.exitFullscreen();
    else void document.documentElement.requestFullscreen().catch(() => undefined);
  };

  // Widget do boletim falado (montado só com servidor ao vivo, mais abaixo).
  let boletimW: BoletimWidget | null = null;
  // Vinheta de abertura: pausa a rotação e o boletim enquanto toca e devolve o telão como estava.
  let pausadoAntes = false;
  const vinheta = criarVinheta({
    hash: location.hash,
    suspender: sim => {
      if (sim) {
        pausadoAntes = store.get().ui.pausado;
        rotacao.pausar(true);
      } else if (!pausadoAntes) rotacao.pausar(false);
      boletimW?.suspender(sim);
    },
  });
  ligarTeclado({
    vinheta: () => vinheta.alternar(),
    ufAtual: () => store.get().ui.uf,
    telaAtual: () => store.get().ui.v,
    turno: () => store.get().config?.turno ?? 1,
    irPara: d => irPara(d),
    irParaUf: uf => irPara(destinoDaUf(store.get().ui.v, uf)),
    proxima: () => rotacao.proxima(true),
    anterior: () => rotacao.anterior(),
    pausar: () => rotacao.pausar(),
    auto: () => {
      store.ui({ auto: true });
      rotacao.reiniciarDwell();
    },
    subir: () => {
      const d = subirNivel(store.get().ui, store.get().config?.turno ?? 1);
      if (d) irPara(d);
    },
    paleta: abrir => {
      store.ui({ paleta: abrir });
      if (abrir) shell.paleta.abrir();
      else shell.paleta.fechar();
    },
    paletaAberta: () => shell.paleta.aberta(),
    zonas: () => {
      const ui = store.get().ui;
      if (ui.v === "mun") irPara({ v: ui.v, uf: ui.uf, mun: ui.mun, zonas: !ui.zonas, zona: null });
    },
    tela_cheia,
    hud: () => store.ui({ hud: !store.get().ui.hud }),
    variante: () => store.ui({ variante: (store.get().ui.variante + 1) % 4 }),
    refetch: recarregar,
    teclaDaTela: tecla => shell.atual()?.keys?.(tecla, store.get()) ?? false,
    boletim: acao => boletimW?.tecla(acao) ?? false,
  });

  // ---------- roteador ----------
  const roteador = ligarRoteador(
    () => store.get().ui,
    h => {
      const ui = store.get().ui;
      // mock, speed e replay só valem na carga da página.
      store.ui({ v: h.v, uf: h.uf, mun: h.mun, zonas: h.zonas, zona: h.zona, auto: h.auto, hud: h.hud, dwell: h.dwell, variante: h.variante, alvo: h.alvo, vigilia: h.vigilia, mock: ui.mock, speed: ui.speed, replay: ui.replay });
      rotacao.reiniciarDwell();
    },
  );

  // ---------- diretor ----------
  const espelho = (): EspelhoTelao => {
    const s = store.get();
    return {
      tipo: "estado",
      v: s.ui.v,
      uf: s.ui.uf,
      mun: s.ui.mun,
      titulo: shell.atual()?.titulo(s) ?? "",
      auto: s.ui.auto,
      pausado: s.ui.pausado,
      hud: s.ui.hud,
      dwell: s.ui.dwell,
      dwellPadrao: s.playlist.dwell,
      indice: s.ui.indice,
      playlist: rotacao.entradas().map(e => ({ v: e.v, uf: e.uf })),
      telas: listar(),
      pst: s.estado?.br.pst ?? null,
      vigilia: s.ui.vigilia,
      rede: s.rede.modo,
      hash: location.hash,
    };
  };
  const canal = abrirCanal(m => {
    if (!ehComando(m)) return;
    executarComando(m);
  });
  const executarComando = (c: Comando): void => {
    switch (c.tipo) {
      case "nav":
        irPara({ v: c.v, uf: c.uf ?? null, mun: c.mun ?? null, zonas: c.zonas ?? false, zona: c.zona ?? null });
        break;
      case "uf":
        irPara(destinoDaUf(store.get().ui.v, c.uf));
        break;
      case "proxima":
        rotacao.proxima(true);
        break;
      case "anterior":
        rotacao.anterior();
        break;
      case "pausa":
        rotacao.pausar(c.valor);
        break;
      case "auto":
        store.ui({ auto: true });
        rotacao.reiniciarDwell();
        break;
      case "dwell":
        store.ui({ dwell: c.segundos });
        rotacao.reiniciarDwell();
        break;
      case "hud":
        store.ui({ hud: c.valor ?? !store.get().ui.hud });
        break;
      case "refetch":
        recarregar();
        break;
      case "vinheta":
        vinheta.alternar(c.valor);
        break;
      case "vigilia":
        if (c.alvo) {
          base = null;
          store.ui({ v: "espera", uf: null, mun: null, zonas: false, zona: null, auto: false, alvo: c.alvo, vigilia: true });
        } else {
          store.ui({ alvo: null, vigilia: false });
          rotacao.iniciar();
        }
        break;
      case "pedir-estado":
        break;
    }
    canal.enviar(espelho());
  };

  // ---------- vigília ----------
  let base: Base | null = null;
  const vigiar = (s: State): void => {
    if (!s.ui.vigilia) {
      base = null;
      return;
    }
    if (!s.estado || s.estado.pronto === false) return;
    if (!base) {
      base = baseDe(s.estado);
      return;
    }
    const novas = versaoNova(base, s.estado);
    if (novas === null) return;
    base = null;
    const hora = horaCurta(s.estado.agora);
    registrarRetomada({ em: new Date().toISOString(), hora, novas });
    store.ui({ vigilia: false, alvo: null });
    rotacao.iniciar();
    document.dispatchEvent(new CustomEvent(EVENTO_TICKER_EXTRA, { detail: { texto: textoRetomada(hora, novas), ms: 600_000 } }));
  };

  // ---------- assinatura do store ----------
  let espelhoAgendado = false;
  let hashAgendado = false;
  store.subscribe((s, diff) => {
    vigiar(s);
    montarSePreciso(s);
    shell.atualizar(s, diff, rotacao.entradas().length);
    boletimW?.tela(s.ui.v);
    for (const [k, r] of Object.entries(s.resultados)) {
      if (indexados.has(k)) continue;
      indexados.add(k);
      indice.adicionarResultado(Number(k.split(":")[0]), r as Resultado);
    }
    if (!hashAgendado) {
      hashAgendado = true;
      setTimeout(() => {
        hashAgendado = false;
        roteador.escrever();
      }, 150);
    }
    if (!espelhoAgendado) {
      espelhoAgendado = true;
      setTimeout(() => {
        espelhoAgendado = false;
        canal.enviar(espelho());
      }, 250);
    }
  });

  // ---------- dados ao vivo ----------
  const aoEvento = (e: EventoSse): void => {
    const r = store.get().rede;
    store.patch("rede", { ...r, ultimo_evento_em: Date.now() });
    for (const n of necessidades(store.get())) if (eventoAfeta(e, n)) carregador.carregar(n);
  };

  if (fonte.eventos) {
    store.patch("rede", { modo: "mock", conectado: true, ultimo_evento_em: null, ultimo_ok_em: null });
    fonte.eventos(aoEvento);
  } else if (hash.replay) {
    store.patch("rede", { modo: "replay", conectado: true, ultimo_evento_em: null, ultimo_ok_em: null });
    setInterval(recarregar, 2000);
  } else {
    const avisarBoletim = (d: EventoBoletimTelao): void => {
      document.dispatchEvent(new CustomEvent<EventoBoletimTelao>(EVENTO_BOLETIM, { detail: d }));
    };
    conectarSse({
      aoEvento,
      aoPolling: recarregar,
      aoRede: r => store.patch("rede", { ...store.get().rede, ...r }),
      aoBoletim: avisarBoletim,
    });
    // Widget "Boletim Arvor" na faixa inferior; #boletim=0 deixa o áudio para o boletim.html.
    const hp = new URLSearchParams(location.hash.replace(/^#/, ""));
    const formato = hp.get("boletimw");
    boletimW = criarBoletimWidget({
      audio: hp.get("boletim") !== "0",
      som: hp.get("som") === "1",
      formato: formato === "aberto" || formato === "compacto" ? formato : "auto",
      aoNovo: texto => document.dispatchEvent(new CustomEvent(EVENTO_TICKER_EXTRA, { detail: { texto, ms: 180_000 } })),
    });
    const baseEl = raiz.querySelector(".base");
    baseEl?.insertBefore(boletimW.el, baseEl.querySelector(".hud"));
    boletimW.tela(store.get().ui.v);
    // Boletim já no ar quando o telão carrega: acende o chip sem esperar o próximo evento.
    void fetch("/api/boletins", { cache: "no-store" })
      .then(r => (r.ok ? (r.json() as Promise<{ no_ar: { id: string; hora: string | null; desde: string; duracao_s: number | null } | null }>) : null))
      .then(l => {
        if (l?.no_ar) avisarBoletim({ kind: "no_ar", id: l.no_ar.id, hora: l.no_ar.hora ?? undefined, desde: l.no_ar.desde, duracao_s: l.no_ar.duracao_s });
      })
      .catch(() => undefined);
  }
  // Rede de segurança: estado a cada 15 s mesmo sem evento.
  setInterval(() => carregador.carregar({ tipo: "estado" }), 15_000);

  // Primeira tela e primeira carga.
  montarSePreciso(store.get());
  shell.atualizar(store.get(), [], rotacao.entradas().length);
  carregador.carregarTodas(necessidades(store.get()));
  canal.enviar(espelho());
}

/** Relógio do replay: instante ISO que anda `speed` vezes mais rápido desde a carga. */
function relogioReplay(inicio: string, speed: number): () => string {
  const t0 = Date.parse(inicio);
  const real0 = Date.now();
  return () => new Date(t0 + (Date.now() - real0) * speed).toISOString();
}

void iniciar();
vigiarBundle(!location.hash.includes("mock=1"));
