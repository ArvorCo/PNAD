// Relógio injetável: o coletor nunca chama Date.now() direto, para os testes controlarem o tempo.

export interface Relogio {
  /** epoch ms */
  agora(): number;
}

export const relogioReal: Relogio = { agora: () => Date.now() };

/** Relógio manual para testes. */
export class RelogioFalso implements Relogio {
  constructor(private t: number = Date.parse("2026-10-04T20:00:00.000Z")) {}
  agora(): number {
    return this.t;
  }
  avancar(ms: number): void {
    this.t += ms;
  }
  definir(ms: number): void {
    this.t = ms;
  }
}

export const isoDe = (ms: number): string => new Date(ms).toISOString();

export function msDe(iso: string | null): number | null {
  if (iso === null) return null;
  const t = Date.parse(iso);
  return Number.isFinite(t) ? t : null;
}

/**
 * Intervalo de re-sondagem de arquivo inativo: 10 min na primeira hora depois das 17h
 * de Brasília (20h UTC), 30 min fora dela.
 */
export function intervaloResondagemS(agoraMs: number): number {
  const h = new Date(agoraMs).getUTCHours();
  return h === 20 ? 600 : 1800;
}
