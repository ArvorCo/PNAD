// Limitador de taxa: baldes de fichas global (100/s, rajada 200) e de varredura
// (40/s, rajada 40; job de varredura tira dos dois) e pausa global escalonada
// 30 → 60 → 120 → 300 s, zerada depois de 10 min sem incidente.
import type { Relogio } from "./relogio.ts";

class Balde {
  private fichas: number;
  private ultimo: number;

  constructor(
    public taxa: number,
    public capacidade: number,
    agora: number,
  ) {
    this.fichas = capacidade;
    this.ultimo = agora;
  }

  reabastecer(agora: number): void {
    const dt = Math.max(0, agora - this.ultimo) / 1000;
    this.fichas = Math.min(this.capacidade, this.fichas + dt * this.taxa);
    this.ultimo = agora;
  }

  tem(agora: number): boolean {
    this.reabastecer(agora);
    return this.fichas >= 1;
  }

  tirar(): void {
    this.fichas -= 1;
  }

  /** ms até haver uma ficha. */
  esperaMs(agora: number): number {
    this.reabastecer(agora);
    if (this.fichas >= 1 || this.taxa <= 0) return 0;
    return Math.ceil(((1 - this.fichas) / this.taxa) * 1000);
  }
}

export const ESCALA_PAUSA_S: readonly number[] = [30, 60, 120, 300];
export const PAUSA_LIMPA_MS = 10 * 60_000;

export interface OpcoesLimitador {
  global: { taxa: number; rajada: number };
  sweep: { taxa: number; rajada: number };
}

export const LIMITES_PADRAO: OpcoesLimitador = {
  global: { taxa: 100, rajada: 200 },
  sweep: { taxa: 40, rajada: 40 },
};

export class Limitador {
  private readonly global: Balde;
  private readonly sweep: Balde;
  private pausaAte: number | null = null;
  private ultimoIncidente: number | null = null;
  /** índice em ESCALA_PAUSA_S da próxima pausa */
  nivel = 0;

  constructor(
    private readonly relogio: Relogio,
    opts: OpcoesLimitador = LIMITES_PADRAO,
  ) {
    const t = relogio.agora();
    this.global = new Balde(opts.global.taxa, opts.global.rajada, t);
    this.sweep = new Balde(opts.sweep.taxa, opts.sweep.rajada, t);
  }

  /** Tira uma ficha (das duas, se varredura). false = sem ficha agora. */
  tentar(varredura: boolean): boolean {
    const t = this.relogio.agora();
    if (this.pausado(t)) return false;
    if (!this.global.tem(t)) return false;
    if (varredura && !this.sweep.tem(t)) return false;
    this.global.tirar();
    if (varredura) this.sweep.tirar();
    return true;
  }

  esperaMs(varredura: boolean): number {
    const t = this.relogio.agora();
    const p = this.pausaAte !== null ? Math.max(0, this.pausaAte - t) : 0;
    const g = this.global.esperaMs(t);
    return Math.max(p, g, varredura ? this.sweep.esperaMs(t) : 0);
  }

  pausado(agora: number = this.relogio.agora()): boolean {
    return this.pausaAte !== null && agora < this.pausaAte;
  }

  pausadoAte(): number | null {
    return this.pausado() ? this.pausaAte : null;
  }

  /** Zera a escalada depois de 10 min sem incidente. Devolve true se zerou agora. */
  atualizar(agora: number = this.relogio.agora()): boolean {
    if (this.nivel > 0 && this.ultimoIncidente !== null && agora - this.ultimoIncidente >= PAUSA_LIMPA_MS && !this.pausado(agora)) {
      this.nivel = 0;
      return true;
    }
    return false;
  }

  /**
   * Pausa global (403/429). Se já pausado, não escala de novo: os jobs em voo da mesma
   * rajada não multiplicam a pausa. Devolve o instante final da pausa.
   */
  pausar(retryAfterS: number | null = null): number {
    const t = this.relogio.agora();
    this.atualizar(t);
    if (this.pausado(t) && this.pausaAte !== null) {
      if (retryAfterS !== null) this.pausaAte = Math.max(this.pausaAte, t + retryAfterS * 1000);
      return this.pausaAte;
    }
    const base = ESCALA_PAUSA_S[Math.min(this.nivel, ESCALA_PAUSA_S.length - 1)] ?? 300;
    const s = Math.max(base, retryAfterS ?? 0);
    this.pausaAte = t + s * 1000;
    this.ultimoIncidente = t;
    this.nivel = Math.min(this.nivel + 1, ESCALA_PAUSA_S.length - 1);
    return this.pausaAte;
  }

  definirTaxaSweep(taxa: number, rajada: number = Math.max(1, Math.round(taxa))): void {
    this.sweep.taxa = taxa;
    this.sweep.capacidade = rajada;
  }
}
