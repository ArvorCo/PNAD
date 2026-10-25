// Mini widget de status do coletor na faixa inferior: chips curtos (valor + rótulo) atualizados a
// cada batimento do `estado` (SSE, 5 s). Paralela e amostra vêm de /api/2t/* a cada 60 s.
// Sem estado do servidor, nada de número vazio: o chip some ou mostra "aguardando".

import { hora, horaCurta } from "../data/format.ts";
import type { Estado } from "../state/types.ts";

export type Saude = "ok" | "aviso" | "falha";

export interface Extras {
  paralela: { bus: number; lido_em: string | null } | null;
  amostra: { recebidas: number; alvo: number } | null;
}

export interface Chip {
  id: string;
  valor: string;
  rotulo: string;
  aviso?: boolean;
  /** Rótulo antes do valor ("TSE 17:04"). */
  antes?: boolean;
}

export interface Resumo {
  saude: Saude;
  linha1: Chip[];
  linha2: Chip[];
}

/** Ordem em que os chips somem quando falta largura (o ticker tem prioridade). */
const CORTE = ["voo", "fil", "304", "lat", "amo"] as const;
const ERROS = ["negado", "limite", "erro_servidor", "timeout", "erro_rede"] as const;
const num = (x: unknown): number => (typeof x === "number" && Number.isFinite(x) ? x : 0);
const reg = (x: unknown): Record<string, unknown> => (typeof x === "object" && x !== null ? (x as Record<string, unknown>) : {});
const soma = (o: Record<string, unknown>): number => Object.values(o).reduce<number>((a, v) => a + num(v), 0);
const int = (n: number): string => Math.round(n).toLocaleString("pt-BR");

export function idade(s: number): string {
  const t = Math.max(0, Math.round(s));
  if (t < 90) return `há ${t} s`;
  if (t < 5400) return `há ${Math.round(t / 60)} min`;
  return `há ${Math.floor(t / 3600)} h ${Math.round((t % 3600) / 60)} min`;
}

function mediana(v: number[]): number | null {
  if (v.length === 0) return null;
  const o = [...v].sort((a, b) => a - b);
  const m = Math.floor(o.length / 2);
  return o.length % 2 ? (o[m] ?? null) : (((o[m - 1] ?? 0) + (o[m] ?? 0)) / 2);
}

export function resumir(e: Estado | null, x: Extras): Resumo {
  if (!e) return { saude: "falha", linha1: [{ id: "c", valor: "sem dado", rotulo: "coletor" }], linha2: [] };
  const agora = Date.parse(e.agora) || Date.now();
  const c = reg(e.coletor);
  const taxas = reg(c.taxas_60s);
  const leituras = soma(taxas);
  const nm = num(taxas.nao_modificado);
  const erros = ERROS.reduce((a, k) => a + num(taxas[k]), 0);
  const fila = soma(reg(c.fila));
  const emVoo = num(c.em_voo);
  const pausaAte = typeof c.pausa_global_ate === "string" ? Date.parse(c.pausa_global_ate) : NaN;
  const pausa = Number.isFinite(pausaAte) && pausaAte > agora;
  const emC = typeof c.em === "string" ? Date.parse(c.em) : NaN;
  const semBatida = !Number.isFinite(emC) || agora - emC > 90_000;

  const { st, ts, dt_ht: dtHt, hg } = e.br;
  const versao = dtHt ?? hg;
  const idadeVersao = st > 0 && versao ? (agora - Date.parse(versao)) / 1000 : null;
  const velha = st > 0 && st < ts && idadeVersao !== null && idadeVersao > 420;

  let saude: Saude = "ok";
  if (pausa || semBatida || leituras === 0) saude = "falha";
  else if (erros > 0 || velha) saude = "aviso";

  const linha1: Chip[] = [
    { id: "lei", valor: int(leituras), rotulo: "leit/min" },
    { id: "304", valor: leituras > 0 ? `${Math.round((nm / leituras) * 100)}%` : "-", rotulo: "sem mudança" },
    { id: "nov", valor: int(num(taxas.ok)), rotulo: "vers/min" },
    { id: "err", valor: int(erros), rotulo: "err/min", aviso: erros > 0 },
    { id: "fil", valor: int(fila), rotulo: "fila" },
    { id: "voo", valor: int(emVoo), rotulo: "em voo" },
  ];
  if (pausa) linha1.push({ id: "pau", valor: "pausa", rotulo: "global", aviso: true });

  const linha2: Chip[] = [];
  if (st === 0) linha2.push({ id: "tse", valor: "aguardando a primeira versão", rotulo: "TSE", antes: true });
  else {
    const h = versao ? `${horaCurta(versao)} ${idade((agora - Date.parse(versao)) / 1000).replace("há ", "")}` : "-";
    linha2.push({ id: "tse", valor: `${h} ${int(st)}/${int(ts)}`, rotulo: "TSE", aviso: velha, antes: true });
    linha2.push({ id: "ufs", valor: `${e.ufs.filter(u => u.st > 0).length}/${e.ufs.length || 27}`, rotulo: "UFs" });
    const p50 = mediana(e.latencias.leitura_menos_hg);
    if (p50 !== null) linha2.push({ id: "lat", valor: `${int(p50)} s`, rotulo: "latência p50" });
  }
  if (x.paralela) linha2.push({ id: "par", valor: `${int(x.paralela.bus)} BUs${x.paralela.lido_em ? ` às ${hora(x.paralela.lido_em)}` : ""}`, rotulo: "paralela", antes: true });
  if (x.amostra) linha2.push({ id: "amo", valor: `${int(x.amostra.recebidas)}/${int(x.amostra.alvo)}`, rotulo: "amostra", antes: true });
  return { saude, linha1, linha2 };
}

export interface Status {
  el: HTMLElement;
  atualizar(e: Estado | null): void;
}

async function obter(url: string): Promise<Record<string, unknown> | null> {
  try {
    const r = await fetch(url, { cache: "no-store" });
    return r.ok ? reg(await r.json()) : null;
  } catch {
    return null;
  }
}

export function criarStatus(buscar: boolean): Status {
  const el = document.createElement("div");
  el.className = "stt";
  el.setAttribute("aria-live", "off");
  el.dataset.saude = "ok";
  const extras: Extras = { paralela: null, amostra: null };
  let ultimo: Estado | null = null;

  // Poda por prioridade: chips inteiros somem (ordem CORTE, depois o último de cada linha)
  // até as duas linhas caberem na largura real; nunca corta texto no meio.
  const podar = (): void => {
    const linhas = [...el.querySelectorAll<HTMLElement>(".stt-l")];
    const chips = [...el.querySelectorAll<HTMLElement>(".stt-c")];
    for (const c of chips) c.hidden = false;
    const cabe = (): boolean => linhas.every(l => l.scrollWidth <= l.clientWidth + 1);
    for (const id of CORTE) {
      if (cabe()) return;
      for (const c of el.querySelectorAll<HTMLElement>(`[data-chip="${id}"]`)) c.hidden = true;
    }
    for (const l of linhas) {
      const vis = [...l.querySelectorAll<HTMLElement>(".stt-c")].filter(c => !c.hidden);
      while (l.scrollWidth > l.clientWidth + 1 && vis.length > 1) (vis.pop() as HTMLElement).hidden = true;
    }
  };

  const desenhar = (): void => {
    const r = resumir(ultimo, extras);
    el.dataset.saude = r.saude;
    const linha = (cs: Chip[]): string =>
      `<div class="stt-l">${cs.map(c => `<span class="stt-c${c.aviso ? " aviso" : ""}" data-chip="${c.id}">${c.antes ? `${c.rotulo} <b>${c.valor}</b>` : `<b>${c.valor}</b> ${c.rotulo}`}</span>`).join("")}</div>`;
    el.innerHTML = `<span class="stt-ponto"></span><div class="stt-t">${linha(r.linha1)}${linha(r.linha2)}</div>`;
    podar();
  };

  const puxar = async (): Promise<void> => {
    const [p, s] = await Promise.all([obter("/api/2t/paralela"), obter("/api/2t/secoes")]);
    const rec = reg(p?.recebidos);
    extras.paralela = p ? { bus: num(rec.bus), lido_em: typeof p.atualizado_em === "string" ? p.atualizado_em : null } : null;
    const t = reg(s?.totais);
    extras.amostra = s && num(t.alvo) > 0 ? { recebidas: num(t.recebidas), alvo: num(t.alvo) } : null;
    desenhar();
  };
  if (buscar) {
    void puxar();
    setInterval(() => void puxar(), 60_000);
  }
  desenhar();
  let larg = 0;
  if (typeof ResizeObserver !== "undefined") {
    new ResizeObserver(() => {
      if (Math.abs(el.clientWidth - larg) < 1) return;
      larg = el.clientWidth;
      podar();
    }).observe(el);
  }
  return {
    el,
    atualizar(e) {
      ultimo = e;
      desenhar();
    },
  };
}
