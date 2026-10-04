// Diretor: segunda janela que comanda o telão por BroadcastChannel('apuracao')
// e espelha o estado que o telão publica.

import "./director.css";

import { abrirCanal, ehEspelho } from "../ui/control/broadcast.ts";
import type { Comando, EspelhoTelao } from "../ui/control/broadcast.ts";
import { criarIndice } from "../ui/control/search.ts";
import { AMOSTRA_CONFIG } from "../ui/data/amostra.ts";
import { ufsPorEleitorado } from "../ui/state/selectors.ts";
import type { Config } from "../ui/state/types.ts";
import { pct } from "../ui/data/format.ts";

const TELAS_PADRAO = [
  { id: "pres", titulo: "Presidente" },
  { id: "gov", titulo: "Governadores" },
  { id: "sen", titulo: "Senado" },
  { id: "ritmo", titulo: "Ritmo da apuração" },
  { id: "mov", titulo: "Movimento da apuração" },
  { id: "espera", titulo: "Espera" },
];

function el<K extends keyof HTMLElementTagNameMap>(tag: K, attrs: Record<string, string> = {}, texto = ""): HTMLElementTagNameMap[K] {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  if (texto) e.textContent = texto;
  return e;
}

async function carregarConfig(): Promise<Config> {
  try {
    const r = await fetch("/api/config", { cache: "no-store" });
    if (r.ok) return (await r.json()) as Config;
  } catch {
    // sem servidor: amostra embutida
  }
  return AMOSTRA_CONFIG;
}

async function iniciar(): Promise<void> {
  const raiz = document.getElementById("diretor");
  if (!raiz) return;
  let espelho: EspelhoTelao | null = null;
  const canal = abrirCanal(m => {
    if (!ehEspelho(m)) return;
    espelho = m;
    desenharEspelho();
  });
  const enviar = (c: Comando): void => canal.enviar(c);

  const config = await carregarConfig();
  const indice = criarIndice();
  indice.adicionarConfig(config);

  // ---------- topo ----------
  const topo = el("header", { class: "dir-topo" });
  const titulo = el("span", { class: "dir-titulo" }, "aguardando o telão");
  const meta = el("span", { class: "dir-meta" });
  topo.append(el("h1", {}, "diretor"), titulo, meta);

  // ---------- controles ----------
  const controles = el("section");
  controles.append(el("h2", {}, "controle"));
  const linha = el("div", { class: "controles" });
  const botao = (texto: string, c: () => Comando): HTMLButtonElement => {
    const b = el("button", { type: "button" }, texto);
    b.addEventListener("click", () => enviar(c()));
    return b;
  };
  const bPausa = botao("pausar", () => ({ tipo: "pausa" }));
  const bAuto = botao("automático", () => ({ tipo: "auto" }));
  const bHud = botao("hud", () => ({ tipo: "hud" }));
  const dwell = el("input", { type: "range", min: "5", max: "60", step: "1", value: "20" });
  const dwellRot = el("span", { class: "dir-valor" }, "20 s");
  dwell.addEventListener("input", () => {
    dwellRot.textContent = `${dwell.value} s`;
    enviar({ tipo: "dwell", segundos: Number(dwell.value) });
  });
  const rotDwell = el("label");
  rotDwell.append("tempo por tela", dwell, dwellRot);
  linha.append(
    botao("anterior", () => ({ tipo: "anterior" })),
    botao("próxima", () => ({ tipo: "proxima" })),
    bPausa,
    bAuto,
    bHud,
    botao("recarregar dados", () => ({ tipo: "refetch" })),
    rotDwell,
    botao("tempo padrão", () => ({ tipo: "dwell", segundos: null })),
  );
  controles.append(linha);

  // ---------- telas ----------
  const telasSec = el("section");
  telasSec.append(el("h2", {}, "telas"));
  const telasGrade = el("div", { class: "grade" });
  telasSec.append(telasGrade);
  let telasDesenhadas = "";
  const desenharTelas = (lista: { id: string; titulo: string }[]): void => {
    const chave = lista.map(t => t.id).join(",");
    if (chave === telasDesenhadas) return;
    telasDesenhadas = chave;
    telasGrade.replaceChildren(
      ...lista.map(t => {
        const b = el("button", { type: "button", "data-v": t.id }, t.titulo);
        b.addEventListener("click", () => {
          const uf = espelho?.uf ?? null;
          const precisaUf = t.id.endsWith("-uf") || t.id === "mun";
          if (t.id === "dis-df") enviar({ tipo: "nav", v: t.id, uf: "DF" });
          else enviar({ tipo: "nav", v: t.id, uf: precisaUf ? (uf ?? "SP") : null });
        });
        return b;
      }),
    );
  };
  desenharTelas(TELAS_PADRAO);

  // ---------- UFs ----------
  const ufsSec = el("section");
  ufsSec.append(el("h2", {}, "estados (mesma tela, recortada para a UF)"));
  const ufsGrade = el("div", { class: "grade ufs" });
  for (const u of ufsPorEleitorado(config.ufs)) {
    const b = el("button", { type: "button", title: u.nome, "data-uf": u.uf.toUpperCase() }, u.uf.toUpperCase());
    b.addEventListener("click", () => enviar({ tipo: "uf", uf: u.uf.toUpperCase() }));
    ufsGrade.append(b);
  }
  ufsSec.append(ufsGrade);

  // ---------- busca ----------
  const buscaSec = el("section");
  buscaSec.append(el("h2", {}, "busca"));
  const campo = el("input", { type: "search", placeholder: "município, estado ou candidatura", autocomplete: "off" });
  const achados = el("ul", { class: "achados" });
  campo.addEventListener("input", () => {
    achados.replaceChildren(
      ...indice.buscar(campo.value, 8).map(a => {
        const li = el("li");
        const b = el("button", { type: "button" }, a.rotulo);
        b.append(el("small", {}, a.detalhe));
        b.addEventListener("click", () => {
          if (a.tipo === "uf") enviar({ tipo: "uf", uf: a.uf });
          else if (a.tipo === "mun") enviar({ tipo: "nav", v: "mun", uf: a.uf, mun: a.cd });
        });
        li.append(b);
        return li;
      }),
    );
  });
  buscaSec.append(campo, achados);

  // ---------- playlist ----------
  const plSec = el("section");
  plSec.append(el("h2", {}, "playlist"));
  const pl = el("ol", { class: "playlist" });
  plSec.append(pl);

  raiz.replaceChildren(topo, controles, telasSec, ufsSec, buscaSec, plSec);

  function desenharEspelho(): void {
    const e = espelho;
    if (!e) return;
    titulo.textContent = e.titulo || e.v;
    meta.dataset.rede = e.rede;
    meta.textContent = `${e.auto ? (e.pausado ? "pausa" : "auto") : "manual"} · ${e.rede} · seções ${e.pst === null ? "sem dado" : pct(e.pst, 2)} · ${e.hash}`;
    bPausa.setAttribute("aria-pressed", String(e.pausado));
    bPausa.textContent = e.pausado ? "continuar" : "pausar";
    bAuto.setAttribute("aria-pressed", String(e.auto));
    bHud.setAttribute("aria-pressed", String(e.hud));
    const seg = e.dwell ?? e.dwellPadrao;
    if (document.activeElement !== dwell) {
      dwell.value = String(seg);
      dwellRot.textContent = `${seg} s`;
    }
    if (e.telas.length > 0) desenharTelas(e.telas);
    for (const b of telasGrade.querySelectorAll<HTMLButtonElement>("button")) b.setAttribute("aria-pressed", String(b.dataset.v === e.v));
    for (const b of ufsGrade.querySelectorAll<HTMLButtonElement>("button")) b.setAttribute("aria-pressed", String(b.dataset.uf === e.uf));
    pl.replaceChildren(
      ...e.playlist.map((p, i) => {
        const li = el("li", {}, p.uf ? `${p.v} ${p.uf}` : p.v);
        if (i === e.indice && e.auto) li.className = "atual";
        return li;
      }),
    );
  }

  enviar({ tipo: "pedir-estado" });
}

void iniciar();
