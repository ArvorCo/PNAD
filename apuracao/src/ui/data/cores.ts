// Cores em OKLab, portadas de docs/assets/predicao_2026_mapa.js (mesma conta de
// scripts/predicao_2026/mapa.py). Parcialidade vira mistura com o papel por banda de pst.

import type { Campo, Campos, Cores } from "../state/types.ts";

export const PAPEL = "#f4f0e6";
export const NAO_INICIADO = "#d9d6cc";
export const TINTA = "#192e2b";
/** Teal para texto pequeno sobre papel: #0f7f5f dá 4,37:1 no papel, abaixo de AA. */
export const OUTROS_TEXTO = "#0b6e55";

export const CORES_CAMPO_PADRAO: Readonly<Record<Campo, string>> = {
  esquerda: "#b02f21",
  "centro-esquerda": "#d9775f",
  centro: "#8a7a3a",
  "centro-direita": "#4f7fc2",
  direita: "#1457aa",
  indefinido: "#8a8f98",
};

export const CORES_PADRAO: Cores = {
  candidatos: { "13": "#b02f21", "22": "#1457aa" },
  sequencia: ["#0f7f5f", "#8a7a3a", "#6b4a92", "#a3541b", "#4f7fc2", "#5f6773", "#9a3f6b", "#2f6f8f"],
};

type Lab = readonly [number, number, number];

const lin = (c: number): number => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4);
const gam = (c: number): number => {
  const x = Math.min(1, Math.max(0, c));
  return x <= 0.0031308 ? 12.92 * x : 1.055 * x ** (1 / 2.4) - 0.055;
};

const labCache = new Map<string, Lab>();

export function rgb(hex: string): [number, number, number] {
  const h = hex.replace("#", "");
  const full = h.length === 3 ? h.split("").map(c => c + c).join("") : h;
  return [0, 2, 4].map(i => parseInt(full.slice(i, i + 2), 16)) as [number, number, number];
}

export function toLab(hex: string): Lab {
  const hit = labCache.get(hex);
  if (hit) return hit;
  const [r, g, b] = rgb(hex).map(c => lin(c / 255)) as [number, number, number];
  const l = Math.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b);
  const m = Math.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b);
  const s = Math.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b);
  const out: Lab = [
    0.2104542553 * l + 0.793617785 * m - 0.0040720468 * s,
    1.9779984951 * l - 2.428592205 * m + 0.4505937099 * s,
    0.0259040371 * l + 0.7827717662 * m - 0.808675766 * s,
  ];
  labCache.set(hex, out);
  return out;
}

export function fromLab([L, a, b]: Lab): string {
  const l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3;
  const m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3;
  const s = (L - 0.0894841775 * a - 1.291485548 * b) ** 3;
  const out = [
    4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
    -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
    -0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s,
  ];
  return "#" + out.map(c => Math.round(255 * gam(c)).toString(16).padStart(2, "0")).join("");
}

export function mix(c0: string, c1: string, t: number): string {
  const a = toLab(c0);
  const b = toLab(c1);
  return fromLab([a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t]);
}

export function ramp(stops: readonly string[], t: number): string {
  if (stops.length === 0) return PAPEL;
  if (stops.length === 1) return stops[0] ?? PAPEL;
  const x = Math.min(1, Math.max(0, t)) * (stops.length - 1);
  const i = Math.min(stops.length - 2, Math.floor(x));
  return mix(stops[i] ?? PAPEL, stops[i + 1] ?? PAPEL, x - i);
}

/** Fração da cor cheia por banda de seções totalizadas: 35% / 60% / 85% / 100%. 0 = não iniciado. */
export function banda(pst: number): number {
  if (!(pst > 0)) return 0;
  if (pst < 25) return 0.35;
  if (pst < 50) return 0.6;
  if (pst < 100) return 0.85;
  return 1;
}

/** Cor de unidade no mapa: mistura com o papel pela banda; cinza quando não iniciada. */
export function corPorBanda(cor: string, pst: number): string {
  const f = banda(pst);
  return f === 0 ? NAO_INICIADO : f === 1 ? cor : mix(PAPEL, cor, f);
}

/** Cor do candidato: fixa por número (cores.json) ou pela posição na sequência. */
export function corCandidato(numero: string, posicao: number, cores: Cores = CORES_PADRAO): string {
  const fixa = cores.candidatos[numero];
  if (fixa) return fixa;
  const seq = cores.sequencia.length > 0 ? cores.sequencia : CORES_PADRAO.sequencia;
  return seq[((posicao % seq.length) + seq.length) % seq.length] ?? TINTA;
}

export function corCampo(campo: Campo | string, campos?: Campos): string {
  return campos?.cores[campo] ?? CORES_CAMPO_PADRAO[campo as Campo] ?? CORES_CAMPO_PADRAO.indefinido;
}

/** Luminância relativa WCAG. */
export function luminancia(hex: string): number {
  const [r, g, b] = rgb(hex).map(c => lin(c / 255)) as [number, number, number];
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

export function contraste(a: string, b: string): number {
  const la = luminancia(a);
  const lb = luminancia(b);
  return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05);
}

/** Texto legível sobre um fundo: tinta ou branco, o de maior contraste. */
export const textoSobre = (fundo: string): string => (contraste(fundo, TINTA) >= contraste(fundo, "#ffffff") ? TINTA : "#ffffff");

// ---------- normalização dos ativos ----------
const CAMPOS_VALIDOS = new Set<string>(Object.keys(CORES_CAMPO_PADRAO));

export function campoValido(x: unknown): Campo {
  return typeof x === "string" && CAMPOS_VALIDOS.has(x) ? (x as Campo) : "indefinido";
}

const ehObj = (x: unknown): x is Record<string, unknown> => typeof x === "object" && x !== null && !Array.isArray(x);

/**
 * Aceita campos.json em formatos próximos: {partidos:{PL:"direita"}, cores:{direita:"#..."}, rotulos:{}},
 * {PARTIDO_CAMPO, CORES_CAMPO} ou {campos:{direita:{cor, rotulo}}}.
 */
export function normalizarCampos(bruto: unknown): Campos {
  const saida: Campos = { partidos: {}, cores: { ...CORES_CAMPO_PADRAO }, rotulos: {} };
  if (!ehObj(bruto)) return saida;
  const partidos = bruto.partidos ?? bruto.PARTIDO_CAMPO ?? bruto.partido_campo;
  if (ehObj(partidos)) {
    for (const [sg, c] of Object.entries(partidos)) saida.partidos[sg.toUpperCase()] = campoValido(c);
  }
  const cores = bruto.cores ?? bruto.CORES_CAMPO ?? bruto.cores_campo;
  if (ehObj(cores)) {
    for (const [c, v] of Object.entries(cores)) if (typeof v === "string") saida.cores[c] = v;
  }
  const campos = bruto.campos;
  if (ehObj(campos)) {
    for (const [c, v] of Object.entries(campos)) {
      if (typeof v === "string") saida.cores[c] = v;
      else if (ehObj(v)) {
        if (typeof v.cor === "string") saida.cores[c] = v.cor;
        if (typeof v.rotulo === "string") saida.rotulos[c] = v.rotulo;
      }
    }
  }
  const rotulos = bruto.rotulos;
  if (ehObj(rotulos)) {
    for (const [c, v] of Object.entries(rotulos)) if (typeof v === "string") saida.rotulos[c] = v;
  }
  return saida;
}

/**
 * Aceita cores.json como {candidatos:{"13":"#..."}, sequencia:[...]} ou no formato de
 * scripts (F0): {candidatos, terceiro, outros:[...]}, em que a sequência é terceiro + outros.
 */
export function normalizarCores(bruto: unknown): Cores {
  if (!ehObj(bruto)) return CORES_PADRAO;
  const cand = bruto.candidatos ?? bruto.numeros;
  const candidatos: Record<string, string> = { ...CORES_PADRAO.candidatos };
  if (ehObj(cand)) for (const [n, v] of Object.entries(cand)) if (typeof v === "string") candidatos[n] = v;
  const strings = (x: unknown): string[] => (Array.isArray(x) ? x.filter((y): y is string => typeof y === "string") : []);
  let sequencia = strings(bruto.sequencia ?? bruto.paleta);
  if (sequencia.length === 0) {
    const terceiro = typeof bruto.terceiro === "string" ? [bruto.terceiro] : [];
    sequencia = [...terceiro, ...strings(bruto.outros)];
  }
  return { candidatos, sequencia: sequencia.length > 0 ? sequencia : CORES_PADRAO.sequencia };
}

export function campoDoPartido(sg: string, campos: Campos): Campo {
  return campos.partidos[sg.toUpperCase()] ?? "indefinido";
}
