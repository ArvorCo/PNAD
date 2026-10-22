// URLs do arquivo-urna do TSE por pleito: configuração de seções (-cs.json), aux.json da seção e
// arquivos do hash escolhido (-bu.dat ou -busa.dat).
import { BASE_URL, CICLO } from "../config.ts";

export interface SecaoChave {
  /** sigla minúscula ("zz" no exterior) */
  uf: string;
  /** código TSE com 5 dígitos */
  mun: string;
  zona: number;
  secao: number;
}

export const chaveSecao = (s: SecaoChave): string => `${s.uf}|${s.mun}|${s.zona}|${s.secao}`;

const p4 = (n: number): string => String(n).padStart(4, "0");

export interface UrlsUrna {
  cs(uf: string): string;
  aux(s: SecaoChave): string;
  arquivo(s: SecaoChave, hash: string, nome: string): string;
}

export function urlsUrna(pleito: number, base: string = BASE_URL, ciclo: string = CICLO): UrlsUrna {
  const raiz = `${base}/${ciclo}/arquivo-urna/${pleito}`;
  const p6 = String(pleito).padStart(6, "0");
  const dir = (s: SecaoChave): string => `${raiz}/dados/${s.uf}/${s.mun}/${p4(s.zona)}/${p4(s.secao)}`;
  return {
    cs: (uf) => `${raiz}/config/${uf}/${uf}-p${p6}-cs.json`,
    aux: (s) => `${dir(s)}/p${p6}-${s.uf}-m${s.mun}-z${p4(s.zona)}-s${p4(s.secao)}-aux.json`,
    arquivo: (s, hash, nome) => `${dir(s)}/${hash}/${nome}`,
  };
}
