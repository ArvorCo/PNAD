// Gramática de abrangência do TSE (br | uf | uf+mun5 | uf+mun5-z+zona4), nomes de UF e de cargo.
import { chave, keyU } from "../tse/urls.ts";
import type { FileKey, Nivel } from "../types.ts";
import { ErroHttp } from "./http.ts";

export interface Abr {
  nivel: Nivel;
  uf: string | null;
  mun: string | null;
  zona: string | null;
}

const RE_UF = /^[a-z]{2}$/;
const RE_MU = /^([a-z]{2})(\d{5})$/;
const RE_ZONA = /^([a-z]{2})(\d{5})-z(\d{4})$/;

/** "br", "sp", "sp71072", "sp71072-z0001" → partes; inválido → 400. */
export function parseAbr(texto: string): Abr {
  const s = texto.trim().toLowerCase();
  if (s === "br") return { nivel: "br", uf: null, mun: null, zona: null };
  if (RE_UF.test(s)) return { nivel: "uf", uf: s, mun: null, zona: null };
  const mu = RE_MU.exec(s);
  if (mu) return { nivel: "mu", uf: mu[1] ?? null, mun: mu[2] ?? null, zona: null };
  const z = RE_ZONA.exec(s);
  if (z) return { nivel: "zona", uf: z[1] ?? null, mun: z[2] ?? null, zona: z[3] ?? null };
  throw new ErroHttp(400, `abrangência inválida: ${texto}`);
}

export function abrTexto(a: { nivel: Nivel | null; uf: string | null; mun?: string | null; municipio_cd?: string | null; zona?: string | null; zona_cd?: string | null }): string {
  const mun = a.mun ?? a.municipio_cd ?? null;
  const zona = a.zona ?? a.zona_cd ?? null;
  if (a.nivel === "br" || a.uf === null) return "br";
  if (a.nivel === "uf" || mun === null) return a.uf;
  if (a.nivel === "mu" || zona === null) return `${a.uf}${mun}`;
  return `${a.uf}${mun}-z${zona}`;
}

export function chaveU(ele: number, cargo: number, a: Abr): string {
  return chave(keyDeAbr(ele, cargo, a));
}

export function keyDeAbr(ele: number, cargo: number, a: Abr): FileKey {
  return keyU(ele, cargo, a.nivel, a.uf, a.mun, a.zona);
}

/** sigla minúscula → nome e código IBGE da UF. */
export const UFS: Readonly<Record<string, { nome: string; cdi: string | null }>> = {
  ac: { nome: "Acre", cdi: "12" }, al: { nome: "Alagoas", cdi: "27" }, ap: { nome: "Amapá", cdi: "16" },
  am: { nome: "Amazonas", cdi: "13" }, ba: { nome: "Bahia", cdi: "29" }, ce: { nome: "Ceará", cdi: "23" },
  df: { nome: "Distrito Federal", cdi: "53" }, es: { nome: "Espírito Santo", cdi: "32" }, go: { nome: "Goiás", cdi: "52" },
  ma: { nome: "Maranhão", cdi: "21" }, mt: { nome: "Mato Grosso", cdi: "51" }, ms: { nome: "Mato Grosso do Sul", cdi: "50" },
  mg: { nome: "Minas Gerais", cdi: "31" }, pa: { nome: "Pará", cdi: "15" }, pb: { nome: "Paraíba", cdi: "25" },
  pr: { nome: "Paraná", cdi: "41" }, pe: { nome: "Pernambuco", cdi: "26" }, pi: { nome: "Piauí", cdi: "22" },
  rj: { nome: "Rio de Janeiro", cdi: "33" }, rn: { nome: "Rio Grande do Norte", cdi: "24" },
  rs: { nome: "Rio Grande do Sul", cdi: "43" }, ro: { nome: "Rondônia", cdi: "11" }, rr: { nome: "Roraima", cdi: "14" },
  sc: { nome: "Santa Catarina", cdi: "42" }, sp: { nome: "São Paulo", cdi: "35" }, se: { nome: "Sergipe", cdi: "28" },
  to: { nome: "Tocantins", cdi: "17" }, zz: { nome: "Exterior", cdi: null },
};

export const nomeUf = (uf: string): string => UFS[uf.toLowerCase()]?.nome ?? uf.toUpperCase();

const CARGOS: Readonly<Record<number, { nome: string; nome_f: string }>> = {
  1: { nome: "Presidente", nome_f: "Presidente" },
  3: { nome: "Governador", nome_f: "Governadora" },
  5: { nome: "Senador", nome_f: "Senadora" },
  6: { nome: "Deputado Federal", nome_f: "Deputada Federal" },
  7: { nome: "Deputado Estadual", nome_f: "Deputada Estadual" },
  8: { nome: "Deputado Distrital", nome_f: "Deputada Distrital" },
  25: { nome: "Conselheiro Distrital", nome_f: "Conselheira Distrital" },
};

export function nomeCargo(cd: number): { nome: string; nome_f: string } {
  return CARGOS[cd] ?? { nome: `Cargo ${cd}`, nome_f: `Cargo ${cd}` };
}

const MINUSCULAS: ReadonlySet<string> = new Set(["de", "da", "do", "das", "dos", "e", "d'"]);

/** "SANTA BÁRBARA D'OESTE" → "Santa Bárbara d'Oeste". */
export function titulo(nome: string | null): string {
  if (nome === null) return "";
  return nome
    .toLocaleLowerCase("pt-BR")
    .split(" ")
    .map((p, i) => {
      if (i > 0 && MINUSCULAS.has(p)) return p;
      if (p.startsWith("d'") && p.length > 2) return `d'${p.charAt(2).toLocaleUpperCase("pt-BR")}${p.slice(3)}`;
      return p.charAt(0).toLocaleUpperCase("pt-BR") + p.slice(1);
    })
    .join(" ");
}
