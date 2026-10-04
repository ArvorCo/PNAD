// Hash ⇄ UiState. O hash carrega tudo que o OBS precisa para uma browser source fixa:
// #v=mun&uf=SP&mun=71072&z=0248&auto=0&hud=0&mock=1&speed=60&replay=2026-10-04T17:30:00-03:00,60

import type { Replay, UiState } from "../state/types.ts";

export type UiHash = Pick<UiState, "v" | "uf" | "mun" | "zonas" | "zona" | "auto" | "hud" | "mock" | "speed" | "replay" | "dwell" | "variante">;

export const UI_PADRAO: UiHash = {
  v: "pres",
  uf: null,
  mun: null,
  zonas: false,
  zona: null,
  auto: true,
  hud: true,
  mock: false,
  speed: 1,
  replay: null,
  dwell: null,
  variante: 0,
};

const bool = (s: string | null, padrao: boolean): boolean => (s === null ? padrao : !(s === "0" || s === "false" || s === "nao"));

function num(s: string | null, padrao: number): number {
  if (s === null || s.trim() === "") return padrao;
  const x = Number(s.replace(",", "."));
  return Number.isFinite(x) ? x : padrao;
}

export function lerReplay(s: string | null): Replay | null {
  if (!s) return null;
  const i = s.lastIndexOf(",");
  const inicio = i > 0 ? s.slice(0, i) : s;
  const speed = i > 0 ? num(s.slice(i + 1), 1) : 1;
  if (Number.isNaN(Date.parse(inicio))) return null;
  return { inicio, speed: speed > 0 ? speed : 1 };
}

const ID_TELA = /^[a-z][a-z0-9-]{0,24}$/;

/** Lê o hash (com ou sem "#"). Valores inválidos caem no padrão. */
export function lerHash(hash: string): UiHash {
  const p = new URLSearchParams(hash.replace(/^#/, ""));
  const v = p.get("v");
  const uf = p.get("uf");
  const mun = p.get("mun");
  const z = p.get("z");
  const mock = bool(p.get("mock"), false);
  const dwell = p.get("dwell");
  return {
    v: v && ID_TELA.test(v) ? v : UI_PADRAO.v,
    uf: uf && /^[a-z]{2}$/i.test(uf) ? uf.toUpperCase() : null,
    mun: mun && /^\d{1,5}$/.test(mun) ? mun.padStart(5, "0") : null,
    zonas: z !== null,
    zona: z && /^\d{1,4}$/.test(z) && z !== "1" ? z.padStart(4, "0") : null,
    auto: bool(p.get("auto"), true),
    hud: bool(p.get("hud"), true),
    mock,
    speed: Math.max(0.1, num(p.get("speed"), mock ? 60 : 1)),
    replay: lerReplay(p.get("replay")),
    dwell: dwell === null ? null : Math.max(3, num(dwell, 20)),
    variante: Math.max(0, Math.floor(num(p.get("m"), 0))),
  };
}

/** Escreve o hash omitindo os valores padrão. Ordem estável. */
export function escreverHash(ui: UiHash): string {
  const p: [string, string][] = [["v", ui.v]];
  if (ui.uf) p.push(["uf", ui.uf]);
  if (ui.mun) p.push(["mun", ui.mun]);
  if (ui.zonas) p.push(["z", ui.zona ?? "1"]);
  if (!ui.auto) p.push(["auto", "0"]);
  if (!ui.hud) p.push(["hud", "0"]);
  if (ui.mock) p.push(["mock", "1"]);
  if (ui.speed !== (ui.mock ? 60 : 1)) p.push(["speed", String(ui.speed)]);
  if (ui.replay) p.push(["replay", `${ui.replay.inicio},${ui.replay.speed}`]);
  if (ui.dwell !== null) p.push(["dwell", String(ui.dwell)]);
  if (ui.variante > 0) p.push(["m", String(ui.variante)]);
  // Sem URLSearchParams.toString(): ele codificaria ":" e "," do replay e o hash ficaria ilegível no OBS.
  return "#" + p.map(([k, v]) => `${k}=${encodeURIComponent(v).replace(/%3A/gi, ":").replace(/%2C/gi, ",")}`).join("&");
}

/** Liga o hash ao store: lê na partida e no hashchange, escreve com replaceState. */
export function ligarRoteador(
  ler: () => UiHash,
  aplicar: (ui: UiHash) => void,
): { escrever: () => void; desligar: () => void } {
  const aoMudar = (): void => aplicar(lerHash(location.hash));
  window.addEventListener("hashchange", aoMudar);
  return {
    escrever() {
      const h = escreverHash(ler());
      if (h !== location.hash) history.replaceState(null, "", h);
    },
    desligar: () => window.removeEventListener("hashchange", aoMudar),
  };
}
