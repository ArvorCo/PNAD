// Métricas do coletor e linha de saúde (meta.estado_coletor + JSON lines no stdout).
import { statSync } from "node:fs";
import type { ClasseFetch } from "../types.ts";

const CLASSES: readonly ClasseFetch[] = [
  "ok", "nao_modificado", "igual", "nao_existe", "negado", "limite", "erro_servidor", "timeout", "erro_rede", "corpo_invalido",
];

type Contagem = Record<ClasseFetch, number>;
const zerada = (): Contagem => Object.fromEntries(CLASSES.map((c) => [c, 0])) as Contagem;

export interface UltimoErro {
  em: string;
  classe: ClasseFetch | "interno";
  chave: string;
  erro: string | null;
}

/** Janela deslizante de 60 s em baldes de 1 s. */
export class Metricas {
  private readonly baldes = new Map<number, { c: Contagem; mudancas: number; bytes: number }>();
  private readonly skews: number[] = [];
  ultimoErro: UltimoErro | null = null;
  total = 0;

  registrar(classe: ClasseFetch, agora: number, mudou: boolean, bytes: number): void {
    const s = Math.floor(agora / 1000);
    let b = this.baldes.get(s);
    if (!b) {
      b = { c: zerada(), mudancas: 0, bytes: 0 };
      this.baldes.set(s, b);
      for (const k of this.baldes.keys()) if (k < s - 61) this.baldes.delete(k);
    }
    b.c[classe]++;
    if (mudou) b.mudancas++;
    b.bytes += bytes;
    this.total++;
  }

  /** Desvio do relógio local contra o cabeçalho Date (resolução de 1 s; média das últimas 50). */
  registrarSkew(servidorDate: string | null, iniciadoEm: string, duracaoMs: number): void {
    if (servidorDate === null) return;
    const srv = Date.parse(servidorDate);
    const loc = Date.parse(iniciadoEm) + duracaoMs / 2;
    if (!Number.isFinite(srv) || !Number.isFinite(loc)) return;
    this.skews.push(srv - loc);
    if (this.skews.length > 50) this.skews.shift();
  }

  skewMs(): number | null {
    if (this.skews.length === 0) return null;
    return Math.round(this.skews.reduce((a, b) => a + b, 0) / this.skews.length);
  }

  janela(agora: number): { taxas: Contagem; mudancas: number; bytes: number } {
    const s = Math.floor(agora / 1000);
    const taxas = zerada();
    let mudancas = 0;
    let bytes = 0;
    for (const [k, b] of this.baldes) {
      if (k <= s - 60 || k > s) continue;
      for (const c of CLASSES) taxas[c] += b.c[c];
      mudancas += b.mudancas;
      bytes += b.bytes;
    }
    return { taxas, mudancas, bytes };
  }
}

export function tamanhoMb(path: string): number | null {
  try {
    return Math.round((statSync(path).size / 1048576) * 10) / 10;
  } catch {
    return null;
  }
}

export interface EstadoColetor {
  em: string;
  em_voo: number;
  concorrencia: number;
  fila: Record<string, number>;
  taxas_60s: Record<string, number>;
  mudancas_60s: number;
  bytes_60s: number;
  pausa_global_ate: string | null;
  nivel_pausa: number;
  sweep: unknown;
  skew_ms: number | null;
  /** RSS: inclui páginas do mmap do SQLite e o cache de páginas */
  memoria_mb: number;
  heap_mb: number;
  wal_mb: number | null;
  db_mb: number | null;
  total_fetch: number;
  ultimo_erro: UltimoErro | null;
}

/** Linha JSON única para o log. */
export function linhaLog(e: EstadoColetor): string {
  return JSON.stringify({ t: "saude", ...e });
}
