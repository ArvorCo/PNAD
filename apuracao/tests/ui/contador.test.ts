import { describe, expect, test } from "bun:test";
import { criarAnimador, DURACAO_CONTAGEM_MS, easeOutCubic, quadro } from "../../src/ui/components/contador.ts";
import type { Relogio } from "../../src/ui/components/contador.ts";
import { inteiro, pct } from "../../src/ui/data/format.ts";

/** rAF falso: os quadros só rodam quando o teste avança o relógio. */
function relogioFalso(): Relogio & { avancar(ms: number): void; pendentes(): number } {
  let t = 0;
  let id = 0;
  const fila = new Map<number, (t: number) => void>();
  return {
    raf(cb) {
      fila.set(++id, cb);
      return id;
    },
    caf(i) {
      fila.delete(i);
    },
    agora: () => t,
    avancar(ms) {
      t += ms;
      const atuais = [...fila.entries()];
      fila.clear();
      for (const [, cb] of atuais) cb(t);
    },
    pendentes: () => fila.size,
  };
}

describe("easing", () => {
  test("ease-out cúbico nos extremos e no meio", () => {
    expect(easeOutCubic(0)).toBe(0);
    expect(easeOutCubic(1)).toBe(1);
    expect(easeOutCubic(0.5)).toBeCloseTo(0.875, 10);
    expect(easeOutCubic(-1)).toBe(0);
    expect(easeOutCubic(2)).toBe(1);
  });

  test("quadro interpola e assenta no alvo", () => {
    expect(quadro(0, 100, 0)).toBe(0);
    expect(quadro(0, 100, DURACAO_CONTAGEM_MS / 2)).toBeCloseTo(87.5, 10);
    expect(quadro(0, 100, DURACAO_CONTAGEM_MS)).toBe(100);
    expect(quadro(10, 20, 50, 0)).toBe(20);
  });
});

describe("animador com rAF falso", () => {
  test("sequência de quadros formatada em pt-BR, monotônica, termina exata e para", () => {
    const r = relogioFalso();
    const textos: string[] = [];
    const a = criarAnimador(v => textos.push(inteiro(v)), { relogio: r, reduzido: () => false });
    a.ir(1_000_000);
    for (let i = 0; i < 6; i++) r.avancar(150);
    expect(textos).toEqual(["421.296", "703.704", "875.000", "962.963", "995.370", "1.000.000"]);
    expect(r.pendentes()).toBe(0);
    expect(a.atual()).toBe(1_000_000);
  });

  test("percentual com uma casa por quadro", () => {
    const r = relogioFalso();
    const textos: string[] = [];
    const a = criarAnimador(v => textos.push(pct(v)), { inicial: 40, relogio: r, reduzido: () => false });
    a.ir(50);
    r.avancar(450);
    r.avancar(450);
    expect(textos).toEqual(["48,8%", "50,0%"]);
  });

  test("novo alvo no meio parte do valor exibido, sem salto", () => {
    const r = relogioFalso();
    const vistos: number[] = [];
    const a = criarAnimador(v => vistos.push(v), { relogio: r, reduzido: () => false });
    a.ir(100);
    r.avancar(450);
    const meio = a.atual();
    expect(meio).toBeCloseTo(87.5, 6);
    a.ir(0);
    r.avancar(1);
    expect(a.atual()).toBeLessThan(meio);
    expect(a.atual()).toBeGreaterThan(80);
    r.avancar(900);
    expect(a.atual()).toBe(0);
  });

  test("movimento reduzido salta direto ao valor", () => {
    const r = relogioFalso();
    const vistos: number[] = [];
    const a = criarAnimador(v => vistos.push(v), { relogio: r, reduzido: () => true });
    expect(a.ir(42)).toBe(true);
    expect(vistos).toEqual([42]);
    expect(r.pendentes()).toBe(0);
  });

  test("mesmo alvo não reanima e informa que nada mudou", () => {
    const r = relogioFalso();
    const a = criarAnimador(() => undefined, { relogio: r, reduzido: () => false });
    a.ir(5, false);
    expect(a.ir(5)).toBe(false);
    expect(r.pendentes()).toBe(0);
  });
});
