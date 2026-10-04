// Assinatura do /events. O EventSource reconecta sozinho; se ficar 90 s sem nenhuma
// mensagem, o telão passa a sondar a cada 30 s até o fluxo voltar. Nunca tela branca:
// quem chama mantém o último snapshot e a rede vai para o HUD.

import type { EventoSse, ModoRede } from "../state/types.ts";

export interface OpcoesSse {
  url?: string;
  silencioMs?: number;
  intervaloPollingMs?: number;
  aoEvento: (e: EventoSse) => void;
  aoPolling: () => void;
  aoRede: (r: { modo: ModoRede; conectado: boolean; ultimo_evento_em: number | null }) => void;
}

type Kind = EventoSse["kind"];
const KINDS: ReadonlySet<string> = new Set<Kind>(["resultado", "ab", "config", "estado", "anomalia"]);

/** Nomes de evento do servidor (snapshot, evento, estado) e os antigos do contrato inicial. */
const TIPOS = ["snapshot", "evento", "estado", "resultado", "anomalia"] as const;
const KIND_PADRAO: Readonly<Record<string, Kind>> = { snapshot: "resultado", evento: "anomalia", estado: "estado", resultado: "resultado", anomalia: "anomalia" };

/**
 * Traduz o `data:` de um evento. `snapshot` traz kind resultado, ab ou config; `evento`,
 * kind anomalia; `estado` é o batimento com `max_snapshot_id`.
 */
export function lerEvento(dado: string, tipo?: string): EventoSse | null {
  try {
    const x = JSON.parse(dado) as Record<string, unknown>;
    const k = typeof x.kind === "string" ? x.kind : tipo ? KIND_PADRAO[tipo] : undefined;
    if (k === undefined || !KINDS.has(k)) return null;
    const n = (v: unknown): number => (typeof v === "number" && Number.isFinite(v) ? v : Number(v ?? 0) || 0);
    const e: EventoSse = {
      kind: k as Kind,
      ele: n(x.ele),
      cargo: n(x.cargo),
      abr: typeof x.abr === "string" ? x.abr : "",
      snapshot_id: n(x.snapshot_id ?? x.max_snapshot_id),
      at: typeof x.at === "string" ? x.at : typeof x.agora === "string" ? x.agora : "",
    };
    if (typeof x.nivel === "string" || x.nivel === null) e.nivel = x.nivel;
    if (typeof x.pst === "number" || x.pst === null) e.pst = x.pst;
    if (typeof x.tf === "boolean") e.tf = x.tf;
    return e;
  } catch {
    return null;
  }
}

export function conectarSse(o: OpcoesSse): () => void {
  const silencio = o.silencioMs ?? 90_000;
  const passo = o.intervaloPollingMs ?? 30_000;
  let ultimo: number | null = null;
  let modo: ModoRede = "sse";
  let conectado = false;
  let timerPolling: ReturnType<typeof setInterval> | null = null;
  const inicio = Date.now();

  const avisar = (): void => o.aoRede({ modo, conectado, ultimo_evento_em: ultimo });

  const pararPolling = (): void => {
    if (timerPolling !== null) clearInterval(timerPolling);
    timerPolling = null;
  };

  const tocar = (): void => {
    ultimo = Date.now();
    if (modo !== "sse" || !conectado) {
      modo = "sse";
      conectado = true;
      pararPolling();
      avisar();
    }
  };

  // tudo=1: o telão desce a município e zona, então precisa dos snapshots de todos os níveis.
  const es = new EventSource(o.url ?? "/events?tudo=1");
  // O batimento `estado` chega a cada 5 s; só vira evento quando o banco andou.
  let ultimoMax = -1;
  const entregar = (e: EventoSse | null): void => {
    if (!e) return;
    if (e.kind === "estado") {
      if (e.snapshot_id === ultimoMax) return;
      ultimoMax = e.snapshot_id;
    }
    o.aoEvento(e);
  };
  let aberturas = 0;
  es.onopen = () => {
    conectado = true;
    ultimo = Date.now();
    avisar();
    // Reconexão: o Last-Event-ID retoma os snapshots, mas as telas recarregam tudo por garantia.
    aberturas += 1;
    if (aberturas > 1) o.aoPolling();
  };
  es.onerror = () => {
    conectado = false;
    avisar();
  };
  es.onmessage = ev => {
    tocar();
    entregar(lerEvento(String(ev.data)));
  };
  for (const t of TIPOS) {
    es.addEventListener(t, ev => {
      tocar();
      entregar(lerEvento(String((ev as MessageEvent).data), t));
    });
  }
  es.addEventListener("ping", tocar);

  const vigia = setInterval(() => {
    const ref = ultimo ?? inicio;
    if (Date.now() - ref < silencio || timerPolling !== null) return;
    modo = "polling";
    avisar();
    o.aoPolling();
    timerPolling = setInterval(o.aoPolling, passo);
  }, 5_000);

  return () => {
    clearInterval(vigia);
    pararPolling();
    es.close();
  };
}
