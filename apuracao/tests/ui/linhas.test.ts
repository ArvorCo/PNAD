import { describe, expect, test } from "bun:test";
import {
  ajusteLinear,
  caminho,
  caminhoArea,
  dominioAuto,
  escalaLinear,
  ritmoRecente,
  separarRotulos,
  ticksRedondos,
} from "../../src/ui/components/linhas.ts";

describe("escala e caminho", () => {
  test("escala linear inverte o eixo vertical e trata domínio degenerado", () => {
    const sy = escalaLinear(30, 60, 500, 0);
    expect(sy(30)).toBe(500);
    expect(sy(60)).toBe(0);
    expect(sy(45)).toBe(250);
    expect(escalaLinear(5, 5, 0, 100)(5)).toBe(50);
  });

  test("caminho com M e L e quebra em ponto inválido", () => {
    const sx = escalaLinear(0, 10, 0, 100);
    const sy = escalaLinear(0, 10, 100, 0);
    expect(caminho([{ x: 0, y: 0 }, { x: 5, y: 5 }, { x: 10, y: 10 }], sx, sy)).toBe("M0 100L50 50L100 0");
    expect(caminho([{ x: 0, y: 0 }, { x: 5, y: NaN }, { x: 10, y: 10 }], sx, sy)).toBe("M0 100M100 0");
    expect(caminho([], sx, sy)).toBe("");
    expect(caminho([{ x: 1 / 3, y: 0 }], sx, sy)).toBe("M3.3 100");
  });

  test("área fecha na base do domínio", () => {
    const sx = escalaLinear(0, 10, 0, 100);
    const sy = escalaLinear(0, 10, 100, 0);
    expect(caminhoArea([{ x: 0, y: 5 }, { x: 10, y: 10 }], sx, sy, 0)).toBe("M0 50L100 0L100 100L0 100Z");
    expect(caminhoArea([], sx, sy, 0)).toBe("");
  });
});

describe("domínio e ticks", () => {
  test("usa 30 a 60 quando os dados cabem e ajusta quando não cabem", () => {
    expect(dominioAuto([41.2, 44.8, 47.5], [30, 60])).toEqual([30, 60]);
    expect(dominioAuto([28.4, 52.1], [30, 60])).toEqual([25, 55]);
    expect(dominioAuto([62, 66], [30, 60], 5, 0, 100)).toEqual([55, 70]);
    expect(dominioAuto([], [30, 60])).toEqual([30, 60]);
    expect(dominioAuto([50], null, 5)).toEqual([45, 55]);
  });

  test("ticks redondos", () => {
    expect(ticksRedondos(30, 60, 6)).toEqual([30, 35, 40, 45, 50, 55, 60]);
    expect(ticksRedondos(0, 470_000, 4)).toEqual([0, 200_000, 400_000]);
    expect(ticksRedondos(5, 5)).toEqual([5]);
  });
});

describe("ajuste linear e rótulos", () => {
  test("mínimos quadrados", () => {
    const r = ajusteLinear([{ x: 0, y: 1 }, { x: 1, y: 3 }, { x: 2, y: 5 }]);
    expect(r?.a).toBeCloseTo(1, 10);
    expect(r?.b).toBeCloseTo(2, 10);
    expect(ajusteLinear([{ x: 1, y: 1 }])).toBeNull();
    expect(ajusteLinear([{ x: 1, y: 1 }, { x: 1, y: 2 }])).toBeNull();
  });

  test("separa rótulos sobrepostos preservando a ordem e os limites", () => {
    expect(separarRotulos([100, 105, 300], 30)).toEqual([100, 130, 300]);
    expect(separarRotulos([105, 100], 30)).toEqual([130, 100]);
    expect(separarRotulos([490, 495], 30, 0, 500)).toEqual([470, 500]);
    expect(separarRotulos([], 30)).toEqual([]);
  });
});

describe("ritmo recente", () => {
  const min = 60_000;
  test("taxa por minuto e previsão pela reta da janela", () => {
    const pts = [0, 5, 10, 15, 20].map(m => ({ x: m * min, y: m === 0 ? 0 : 100 * m }));
    const r = ritmoRecente(pts, 10 * min, 3000);
    expect(r?.porMinuto).toBeCloseTo(100, 6);
    expect(r?.previsao).toBeCloseTo(30 * min, 0);
  });

  test("usa o ponto anterior quando a janela tem um só", () => {
    const r = ritmoRecente([{ x: 0, y: 0 }, { x: 30 * min, y: 600 }], 10 * min, 1200);
    expect(r?.porMinuto).toBeCloseTo(20, 6);
    expect(r?.previsao).toBeCloseTo(60 * min, 0);
  });

  test("sem avanço não há previsão; alvo alcançado devolve o último instante", () => {
    expect(ritmoRecente([{ x: 0, y: 50 }, { x: min, y: 50 }], 10 * min, 100)?.previsao).toBeNull();
    expect(ritmoRecente([{ x: 0, y: 50 }, { x: min, y: 100 }], 10 * min, 100)?.previsao).toBe(min);
    expect(ritmoRecente([], 10 * min, 100)).toBeNull();
  });
});
