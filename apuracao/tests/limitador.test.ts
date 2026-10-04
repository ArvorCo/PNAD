import { describe, expect, test } from "bun:test";
import { Limitador, PAUSA_LIMPA_MS } from "../src/collector/limitador.ts";
import { RelogioFalso } from "../src/collector/relogio.ts";

describe("Limitador", () => {
  test("rajada global de 200 e reabastecimento a 100/s", () => {
    const r = new RelogioFalso(0);
    const l = new Limitador(r);
    let n = 0;
    while (l.tentar(false)) n++;
    expect(n).toBe(200);
    expect(l.esperaMs(false)).toBe(10);
    r.avancar(100);
    n = 0;
    while (l.tentar(false)) n++;
    expect(n).toBe(10);
  });

  test("varredura tira dos dois baldes e fica em 40/s", () => {
    const r = new RelogioFalso(0);
    const l = new Limitador(r);
    let n = 0;
    while (l.tentar(true)) n++;
    expect(n).toBe(40);
    expect(l.tentar(false)).toBe(true);
    r.avancar(1000);
    n = 0;
    while (l.tentar(true)) n++;
    expect(n).toBe(40);
  });

  test("pausa escalonada 30, 60, 120, 300 e zera após 10 min limpos", () => {
    const r = new RelogioFalso(0);
    const l = new Limitador(r);
    const duracoes: number[] = [];
    for (let i = 0; i < 5; i++) {
      const ate = l.pausar();
      duracoes.push((ate - r.agora()) / 1000);
      expect(l.tentar(false)).toBe(false);
      r.definir(ate);
    }
    expect(duracoes).toEqual([30, 60, 120, 300, 300]);
    r.avancar(PAUSA_LIMPA_MS);
    expect(l.atualizar()).toBe(true);
    expect((l.pausar() - r.agora()) / 1000).toBe(30);
  });

  test("pausa durante pausa não escala; Retry-After maior estende", () => {
    const r = new RelogioFalso(0);
    const l = new Limitador(r);
    l.pausar();
    expect(l.pausar()).toBe(30_000);
    expect(l.nivel).toBe(1);
    expect(l.pausar(90)).toBe(90_000);
    expect(l.pausadoAte()).toBe(90_000);
    r.definir(90_000);
    expect(l.pausado()).toBe(false);
    expect(l.pausar(5)).toBe(90_000 + 60_000);
  });
});
