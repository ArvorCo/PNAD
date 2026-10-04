import { describe, expect, test } from "bun:test";
import type { Geometria } from "../../src/ui/data/geo.ts";
import { areaAnel, CAIXA_BR, caixaDe, caminho, centroide, fitExtent } from "../../src/ui/geo/projecao.ts";

const quadrado: Geometria = {
  type: "Polygon",
  coordinates: [
    [
      [0, 0],
      [10, 0],
      [10, 10],
      [0, 10],
      [0, 0],
    ],
  ],
};

describe("fitExtent", () => {
  test("caixa quadrada no equador ocupa o lado menor e centraliza", () => {
    const a = fitExtent({ lon0: 0, lon1: 10, lat0: -5, lat1: 5, latRef: 0 }, 200, 100, 10);
    expect(a.escala).toBeCloseTo(8, 9); // (100 - 20) / 10
    expect(a.cos).toBeCloseTo(1, 12);
    expect(a.projetar(0, 5)).toEqual([60, 10]);
    expect(a.projetar(10, -5)).toEqual([140, 90]);
  });

  test("Brasil usa cos(-14°) da casa e cabe em 1152 × 800", () => {
    const a = fitExtent(CAIXA_BR, 1152, 800, 10);
    expect(a.cos).toBeCloseTo(Math.cos((-14 * Math.PI) / 180), 12);
    const [x0, y0] = a.projetar(CAIXA_BR.lon0, CAIXA_BR.lat1);
    const [x1, y1] = a.projetar(CAIXA_BR.lon1, CAIXA_BR.lat0);
    expect(y0).toBeCloseTo(10, 6);
    expect(y1).toBeCloseTo(790, 6);
    expect(x0).toBeGreaterThanOrEqual(10);
    expect(x1).toBeLessThanOrEqual(1142);
    expect((x0 + x1) / 2).toBeCloseTo(576, 6);
  });

  test("caixaDe usa a latitude média da malha", () => {
    const c = caixaDe([quadrado]);
    expect(c).toEqual({ lon0: 0, lon1: 10, lat0: 0, lat1: 10, latRef: 5 });
  });
});

describe("caminho", () => {
  test("quadrado vira M + pontos + Z, arredondado a 0,1 e sem ponto repetido", () => {
    const d = caminho(quadrado, (lon, lat) => [lon * 1.234, 100 - lat * 1.25]);
    expect(d).toBe("M0,100 12.3,100 12.3,87.5 0,87.5Z");
  });

  test("MultiPolygon concatena anéis e descarta anel degenerado", () => {
    const multi: Geometria = {
      type: "MultiPolygon",
      coordinates: [
        quadrado.coordinates as [number, number][][],
        [
          [
            [0, 0],
            [0.001, 0],
            [0, 0.001],
          ],
        ],
      ],
    };
    const d = caminho(multi, (lon, lat) => [lon, lat]);
    expect(d.match(/M/g)?.length).toBe(1);
  });
});

describe("centroide", () => {
  test("centro do quadrado", () => {
    const [x, y] = centroide(quadrado);
    expect(x).toBeCloseTo(5, 9);
    expect(y).toBeCloseTo(5, 9);
  });

  test("usa o maior anel em área, não em número de pontos", () => {
    const g: Geometria = {
      type: "MultiPolygon",
      coordinates: [
        [
          [
            [100, 100],
            [101, 100],
            [101, 100.5],
            [101, 101],
            [100.5, 101],
            [100, 101],
            [100, 100],
          ],
        ],
        quadrado.coordinates as [number, number][][],
      ],
    };
    expect(centroide(g)).toEqual([5, 5]);
    expect(Math.abs(areaAnel((quadrado.coordinates as [number, number][][])[0] ?? []))).toBe(100);
  });
});
