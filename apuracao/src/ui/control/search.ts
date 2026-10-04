// Índice em memória para a paleta de busca: municípios (sem acento), UFs e candidatos já carregados.

import type { Config, Resultado } from "../state/types.ts";
import { nomeProprio } from "../data/format.ts";

export type Achado =
  | { tipo: "uf"; uf: string; rotulo: string; detalhe: string }
  | { tipo: "mun"; uf: string; cd: string; rotulo: string; detalhe: string; capital: boolean }
  | { tipo: "cand"; sqcand: string; ele: number; cargo: number; abr: string; rotulo: string; detalhe: string };

interface Entrada {
  chave: string; // normalizada
  palavras: string[];
  peso: number;
  achado: Achado;
}

/** Minúsculas, sem acento, só letras, dígitos e espaço. */
export function normalizar(s: string): string {
  return s
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9 ]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

export interface Indice {
  adicionarConfig(c: Config): void;
  adicionarResultado(ele: number, r: Resultado): void;
  buscar(consulta: string, limite?: number): Achado[];
  tamanho(): number;
}

export function criarIndice(): Indice {
  const entradas: Entrada[] = [];
  const vistos = new Set<string>();

  const add = (id: string, texto: string, peso: number, achado: Achado): void => {
    if (vistos.has(id)) return;
    vistos.add(id);
    const chave = normalizar(texto);
    entradas.push({ chave, palavras: chave.split(" "), peso, achado });
  };

  return {
    adicionarConfig(c) {
      for (const u of c.ufs) {
        const uf = u.uf.toUpperCase();
        add(`uf:${uf}`, `${u.nome} ${uf}`, 3, { tipo: "uf", uf, rotulo: u.nome, detalhe: uf });
      }
      for (const [ufBruta, lista] of Object.entries(c.municipios)) {
        const uf = ufBruta.toUpperCase();
        for (const m of lista) {
          const nome = /[a-z]/.test(m.nm) ? m.nm : nomeProprio(m.nm);
          add(`mun:${uf}:${m.cd}`, nome, m.c ? 2 : 1, { tipo: "mun", uf, cd: m.cd, rotulo: nome, detalhe: uf, capital: m.c });
        }
      }
    },
    adicionarResultado(ele, r) {
      for (const c of r.cand) {
        const nome = nomeProprio(c.nmu);
        add(`cand:${c.sqcand}`, `${c.nmu} ${c.n}`, 2, {
          tipo: "cand",
          sqcand: c.sqcand,
          ele,
          cargo: r.cargo.cd,
          abr: r.abr,
          rotulo: nome,
          detalhe: `${c.n} · ${c.sg} · ${r.cargo.nome.toLowerCase()}`,
        });
      }
    },
    buscar(consulta, limite = 8) {
      const q = normalizar(consulta);
      if (!q) return [];
      const qp = q.split(" ");
      const pontuados: { e: Entrada; p: number }[] = [];
      for (const e of entradas) {
        let p = 0;
        if (e.chave === q) p = 100;
        else if (e.chave.startsWith(q)) p = 60;
        else if (qp.every(t => e.palavras.some(w => w.startsWith(t)))) p = 40;
        else if (e.chave.includes(q)) p = 20;
        if (p > 0) pontuados.push({ e, p: p + e.peso * 5 - e.chave.length / 100 });
      }
      pontuados.sort((a, b) => b.p - a.p || a.e.chave.localeCompare(b.e.chave));
      return pontuados.slice(0, limite).map(x => x.e.achado);
    },
    tamanho: () => entradas.length,
  };
}
