// Boot do telão: configuração e ativos, casca, telas, roteador, teclado, rotação,
// diretor por BroadcastChannel e dados por SSE (ou polling, mock e replay).

import "./styles/tokens.css";
import "./styles/base.css";
import "./styles/layout.css";
import "./styles/motion.css";
import "./styles/majoritarias.css";
import "./styles/mapa.css";
import "./styles/legislativas.css";

import { ativo, criarApi } from "./data/api.ts";
import type { Fonte } from "./data/api.ts";
import { campoDoPartido, CORES_PADRAO, normalizarCampos, normalizarCores } from "./data/cores.ts";
import { criarMock } from "./data/mock.ts";
import { conectarSse } from "./data/sse.ts";
import { preCarregar } from "./data/geo.ts";
import { abrirCanal, ehComando } from "./control/broadcast.ts";
import type { Comando, EspelhoTelao } from "./control/broadcast.ts";
import { ligarTeclado } from "./control/keyboard.ts";
import { destinoDaUf, subirNivel } from "./control/navegacao.ts";
import type { Destino } from "./control/navegacao.ts";
import { criarRotacao, normalizarPlaylist, PLAYLIST_PADRAO } from "./control/rotation.ts";
import type { Entrada } from "./control/rotation.ts";
import { lerHash, ligarRoteador } from "./control/router.ts";
import type { UiHash } from "./control/router.ts";
import { criarIndice } from "./control/search.ts";
import type { Achado } from "./control/search.ts";
import { criarCarregador, eventoAfeta } from "./dados.ts";
import { montarShell } from "./shell.ts";
import { criarStore } from "./state/store.ts";
import type { Config, EventoSse, Need, Resultado, State } from "./state/types.ts";
import { registrarTelas } from "./views/index.ts";
import { listar } from "./views/registry.ts";

const VIEW_POR_CARGO: Readonly<Record<number, string>> = { 1: "pres-uf", 3: "gov-uf", 5: "sen-uf", 6: "fed-uf", 7: "est-uf", 8: "dis-df" };

function estadoInicial(h: UiHash): State {
  return {
    config: null,
    estado: null,
    resultados: {},
    mapas: {},
    series: {},
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
  const [playlist, campos, cores] = await Promise.all([
    ativo<unknown>("/playlist.json"),
    ativo<unknown>("/campos.json"),
    ativo<unknown>("/cores.json"),
  ]);
  store.patch("playlist", normalizarPlaylist(playlist));
  store.patch("campos", normalizarCampos(campos));
  store.patch("cores", normalizarCores(cores));

  const api = criarApi("", hash.replay ? relogioReplay(hash.replay.inicio, hash.replay.speed) : () => null);
  let config: Config | null = null;
  try {
    config = await api.config();
  } catch {
    config = null; // sem servidor: o mock usa a amostra embutida
  }
  const fonte: Fonte = hash.mock
    ? criarMock({ speed: hash.speed, config, campoDe: sg => campoDoPartido(sg, store.get().campos) })
    : api;
  if (!config) config = await fonte.config().catch(() => null);
  if (config) store.patch("config", config);

  const indice = criarIndice();
  if (config) indice.adicionarConfig(config);
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
    if (a.tipo === "uf") irPara(destinoDaUf(store.get().ui.v, a.uf));
    else if (a.tipo === "mun") irPara({ v: "mun", uf: a.uf, mun: a.cd, zonas: false, zona: null });
    else {
      const uf = a.abr.length >= 2 && a.abr !== "br" ? a.abr.slice(0, 2).toUpperCase() : null;
      if (!uf && a.cargo === 1) irPara({ v: "pres", uf: null, mun: null, zonas: false, zona: null });
      else if (uf) irPara(destinoDaUf(VIEW_POR_CARGO[a.cargo] ?? "pres-uf", uf));
    }
  };

  const recarregar = (): void => carregador.carregarTodas(necessidades(store.get()));

  const tela_cheia = (): void => {
    if (document.fullscreenElement) void document.exitFullscreen();
    else void document.documentElement.requestFullscreen().catch(() => undefined);
  };

  ligarTeclado({
    ufAtual: () => store.get().ui.uf,
    telaAtual: () => store.get().ui.v,
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
      const d = subirNivel(store.get().ui);
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
  });

  // ---------- roteador ----------
  const roteador = ligarRoteador(
    () => store.get().ui,
    h => {
      const ui = store.get().ui;
      // mock, speed e replay só valem na carga da página.
      store.ui({ v: h.v, uf: h.uf, mun: h.mun, zonas: h.zonas, zona: h.zona, auto: h.auto, hud: h.hud, dwell: h.dwell, variante: h.variante, mock: ui.mock, speed: ui.speed, replay: ui.replay });
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
      case "pedir-estado":
        break;
    }
    canal.enviar(espelho());
  };

  // ---------- assinatura do store ----------
  let espelhoAgendado = false;
  let hashAgendado = false;
  store.subscribe((s, diff) => {
    montarSePreciso(s);
    shell.atualizar(s, diff, rotacao.entradas().length);
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
    conectarSse({
      aoEvento,
      aoPolling: recarregar,
      aoRede: r => store.patch("rede", { ...store.get().rede, ...r }),
    });
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
