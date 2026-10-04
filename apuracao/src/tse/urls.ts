// Construção de URLs e chaves dos arquivos do TSE.
// chave = tipo:ele:cargo:nivel:uf:mun:zona (campos ausentes vazios)
import { BASE_URL, CICLO, cargosDe } from "../config.ts";
import type { ArquivoRegistro, FileKey, Nivel, Tier, Tipo } from "../types.ts";

export const pad4 = (n: number | string): string => String(n).padStart(4, "0");
export const segCargo = (cargo: number): string => `c${pad4(cargo)}`;
export const segEleicao = (ele: number): string => `e${String(ele).padStart(6, "0")}`;

const TIPOS: ReadonlySet<string> = new Set(["ele-c", "cm", "ab", "u", "e"]);
const NIVEIS: ReadonlySet<string> = new Set(["br", "uf", "mu", "zona"]);

export interface Urls {
  eleC(): string;
  cm(ele: number): string;
  ab(ele: number, abr: string): string;
  u(ele: number, cargo: number, nivel: Nivel, uf?: string | null, mun?: string | null, zona?: string | null): string;
  e(ele: number, cargo: number, uf: string): string;
  de(key: FileKey): string;
}

export function criarUrls(base: string = BASE_URL, ciclo: string = CICLO): Urls {
  const dados = (ele: number, dir: string): string => `${base}/${ciclo}/${ele}/dados/${dir}`;
  const urls: Urls = {
    eleC: () => `${base}/comum/config/ele-c.json`,
    cm: (ele) => `${base}/${ciclo}/${ele}/config/mun-${segEleicao(ele)}-cm.json`,
    ab: (ele, abr) => `${dados(ele, abr)}/${abr}-${segEleicao(ele)}-ab.json`,
    u: (ele, cargo, nivel, uf, mun, zona) => {
      const fim = `${segCargo(cargo)}-${segEleicao(ele)}-u.json`;
      if (nivel === "br") return `${dados(ele, "br")}/br-${fim}`;
      if (!uf) throw new Error(`uf obrigatória no nível ${nivel}`);
      if (nivel === "uf") return `${dados(ele, uf)}/${uf}-${fim}`;
      if (!mun) throw new Error(`município obrigatório no nível ${nivel}`);
      if (nivel === "mu") return `${dados(ele, uf)}/${uf}${mun}-${fim}`;
      if (!zona) throw new Error("zona obrigatória no nível zona");
      return `${dados(ele, uf)}/${uf}${mun}-z${pad4(zona)}-${fim}`;
    },
    e: (ele, cargo, uf) => `${dados(ele, uf)}/${uf}-${segCargo(cargo)}-${segEleicao(ele)}-e.json`,
    de: (k) => {
      switch (k.tipo) {
        case "ele-c":
          return urls.eleC();
        case "cm":
          return urls.cm(exigir(k.ele, "ele"));
        case "ab":
          return urls.ab(exigir(k.ele, "ele"), k.nivel === "br" ? "br" : exigir(k.uf, "uf"));
        case "u":
          return urls.u(exigir(k.ele, "ele"), exigir(k.cargo, "cargo"), exigir(k.nivel, "nivel"), k.uf, k.mun, k.zona);
        case "e":
          return urls.e(exigir(k.ele, "ele"), exigir(k.cargo, "cargo"), exigir(k.uf, "uf"));
      }
    },
  };
  return urls;
}

function exigir<T>(v: T | null, nome: string): T {
  if (v === null) throw new Error(`campo ${nome} ausente na chave`);
  return v;
}

const padrao = criarUrls();
export const eleC = padrao.eleC;
export const cm = padrao.cm;
export const ab = padrao.ab;
export const u = padrao.u;
export const e = padrao.e;
export const urlDe = padrao.de;

// ---- chaves ----

const vazio: Omit<FileKey, "tipo"> = { ele: null, cargo: null, nivel: null, uf: null, mun: null, zona: null };

export const keyEleC = (): FileKey => ({ tipo: "ele-c", ...vazio });
export const keyCm = (ele: number): FileKey => ({ tipo: "cm", ...vazio, ele });
export const keyAb = (ele: number, abr: string): FileKey =>
  abr === "br" ? { tipo: "ab", ...vazio, ele, nivel: "br" } : { tipo: "ab", ...vazio, ele, nivel: "uf", uf: abr };
export const keyU = (
  ele: number,
  cargo: number,
  nivel: Nivel,
  uf: string | null = null,
  mun: string | null = null,
  zona: string | null = null,
): FileKey => ({
  tipo: "u",
  ele,
  cargo,
  nivel,
  uf: nivel === "br" ? null : uf,
  mun: nivel === "mu" || nivel === "zona" ? mun : null,
  zona: nivel === "zona" && zona !== null ? pad4(zona) : null,
});
export const keyE = (ele: number, cargo: number, uf: string): FileKey => ({ tipo: "e", ...vazio, ele, cargo, nivel: "uf", uf });

export function chave(k: FileKey): string {
  const s = (v: string | number | null): string => (v === null ? "" : String(v));
  return [k.tipo, s(k.ele), s(k.cargo), s(k.nivel), s(k.uf), s(k.mun), s(k.zona)].join(":");
}

export function parseChave(texto: string): FileKey {
  const partes = texto.split(":");
  if (partes.length !== 7) throw new Error(`chave inválida: ${texto}`);
  const [tipo, ele, cargo, nivel, uf, mun, zona] = partes as [string, string, string, string, string, string, string];
  if (!TIPOS.has(tipo)) throw new Error(`tipo inválido na chave: ${texto}`);
  if (nivel !== "" && !NIVEIS.has(nivel)) throw new Error(`nível inválido na chave: ${texto}`);
  const num = (v: string): number | null => (v === "" ? null : Number.parseInt(v, 10));
  return {
    tipo: tipo as Tipo,
    ele: num(ele),
    cargo: num(cargo),
    nivel: nivel === "" ? null : (nivel as Nivel),
    uf: uf === "" ? null : uf,
    mun: mun === "" ? null : mun,
    zona: zona === "" ? null : zona,
  };
}

// ---- registro completo ----

/** Forma mínima do mun-e00XXXX-cm.json usada pelo registro. */
export interface CmMinimo {
  abr: ReadonlyArray<{ cd: string; mu: ReadonlyArray<{ cd: string; z: readonly string[] }> }>;
}

/**
 * Todas as linhas de `arquivo` (tiers 0 a 4) a partir dos cm de cada eleição,
 * mais o ele-c e os próprios cm.
 */
export function* registroDeArquivos(
  cmPorEleicao: ReadonlyMap<number, CmMinimo>,
  urls: Urls = padrao,
): Generator<ArquivoRegistro> {
  const linha = (k: FileKey, tier: Tier, sonda = false): ArquivoRegistro => ({
    ...k,
    chave: chave(k),
    url: urls.de(k),
    tier,
    sonda,
  });
  yield linha(keyEleC(), 0);
  for (const [ele, cmEle] of cmPorEleicao) {
    yield linha(keyCm(ele), 0);
    yield linha(keyAb(ele, "br"), 0);
    if (ele === 6257 || ele === 6258) {
      for (const cargo of cargosDe(ele, null)) yield linha(keyU(ele, cargo, "br"), 0);
    } else if (ele === 6259 || ele === 6260) {
      for (const cargo of cargosDe(ele, null)) yield linha(keyU(ele, cargo, "br"), 4, true);
    }
    for (const abr of cmEle.abr) {
      const uf = abr.cd.toLowerCase();
      const cargos = cargosDe(ele, uf);
      yield linha(keyAb(ele, uf), 1);
      for (const cargo of cargos) {
        yield linha(keyU(ele, cargo, "uf", uf), 0);
        yield linha(keyE(ele, cargo, uf), 4, true);
      }
      for (const mu of abr.mu) {
        for (const cargo of cargos) yield linha(keyU(ele, cargo, "mu", uf, mu.cd), 2);
        for (const z of mu.z) {
          for (const cargo of cargos) yield linha(keyU(ele, cargo, "zona", uf, mu.cd, z), 3);
        }
      }
    }
  }
}
