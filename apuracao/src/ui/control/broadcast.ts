// Canal entre o telão e o diretor (segunda janela, mesma origem).

import type { ModoRede } from "../state/types.ts";

export const CANAL = "apuracao";

export type Comando =
  | { tipo: "nav"; v: string; uf?: string | null; mun?: string | null; zonas?: boolean; zona?: string | null }
  | { tipo: "uf"; uf: string }
  | { tipo: "proxima" }
  | { tipo: "anterior" }
  | { tipo: "pausa"; valor?: boolean }
  | { tipo: "auto" }
  | { tipo: "dwell"; segundos: number | null }
  | { tipo: "hud"; valor?: boolean }
  | { tipo: "refetch" }
  | { tipo: "pedir-estado" };

export interface EspelhoTelao {
  tipo: "estado";
  v: string;
  uf: string | null;
  mun: string | null;
  titulo: string;
  auto: boolean;
  pausado: boolean;
  hud: boolean;
  dwell: number | null;
  dwellPadrao: number;
  indice: number;
  playlist: { v: string; uf: string | null }[];
  telas: { id: string; titulo: string }[];
  pst: number | null;
  rede: ModoRede;
  hash: string;
}

export type Mensagem = Comando | EspelhoTelao;

const TIPOS_COMANDO = new Set(["nav", "uf", "proxima", "anterior", "pausa", "auto", "dwell", "hud", "refetch", "pedir-estado"]);

export function ehComando(x: unknown): x is Comando {
  return typeof x === "object" && x !== null && TIPOS_COMANDO.has(String((x as { tipo?: unknown }).tipo));
}

export function ehEspelho(x: unknown): x is EspelhoTelao {
  return typeof x === "object" && x !== null && (x as { tipo?: unknown }).tipo === "estado";
}

export interface Canal {
  enviar(m: Mensagem): void;
  fechar(): void;
}

export function abrirCanal(aoReceber: (m: Mensagem) => void): Canal {
  if (typeof BroadcastChannel === "undefined") return { enviar: () => undefined, fechar: () => undefined };
  const bc = new BroadcastChannel(CANAL);
  bc.onmessage = ev => {
    const d: unknown = ev.data;
    if (ehComando(d) || ehEspelho(d)) aoReceber(d);
  };
  return { enviar: m => bc.postMessage(m), fechar: () => bc.close() };
}
