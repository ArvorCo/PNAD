import { describe, expect, test } from "bun:test";
import { alocarCadeiras, quocienteEleitoral } from "../../src/ui/components/cadeiras.ts";

const muitos = (votos: number, n = 20): number[] => Array.from({ length: n }, () => votos / n);
const totais = (r: ReturnType<typeof alocarCadeiras>): Record<string, number> =>
  Object.fromEntries(Object.entries(r.porAgremiacao).map(([k, v]) => [k, v.total]));

describe("quociente eleitoral", () => {
  test("despreza fração igual ou inferior a meio e arredonda a superior", () => {
    expect(quocienteEleitoral(1000, 3)).toBe(333);
    expect(quocienteEleitoral(1000, 6)).toBe(167);
    expect(quocienteEleitoral(1500, 4)).toBe(375);
    expect(quocienteEleitoral(1001, 2)).toBe(500);
    expect(quocienteEleitoral(0, 10)).toBe(0);
  });
});

describe("alocação de cadeiras", () => {
  test("quociente partidário exato", () => {
    const r = alocarCadeiras(10, [
      { id: "A", votos: 5000, candidatos: muitos(5000) },
      { id: "B", votos: 3000, candidatos: muitos(3000) },
      { id: "C", votos: 2000, candidatos: muitos(2000) },
    ]);
    expect(r.qe).toBe(1000);
    expect(totais(r)).toEqual({ A: 5, B: 3, C: 2 });
  });

  test("sobra pela maior média", () => {
    const r = alocarCadeiras(5, [
      { id: "A", votos: 4400, candidatos: [2000, 1500, 900] },
      { id: "B", votos: 3100, candidatos: [1500, 1000, 600] },
      { id: "C", votos: 2500, candidatos: [1500, 1000] },
    ]);
    expect(r.qe).toBe(2000);
    expect(totais(r)).toEqual({ A: 2, B: 2, C: 1 });
    expect(r.porAgremiacao.B).toEqual({ qp: 1, sobras: 1, total: 2 });
  });

  test("cláusula de 80% do QE para disputar sobras", () => {
    const com80 = alocarCadeiras(5, [
      { id: "A", votos: 4200, candidatos: [2000, 1200, 1000] },
      { id: "B", votos: 4200, candidatos: [2000, 1200, 1000] },
      { id: "C", votos: 1600, candidatos: [1000, 600] },
    ]);
    expect(totais(com80)).toEqual({ A: 2, B: 2, C: 1 });
    const abaixo = alocarCadeiras(5, [
      { id: "A", votos: 4210, candidatos: [2000, 1210, 1000] },
      { id: "B", votos: 4200, candidatos: [2000, 1200, 1000] },
      { id: "C", votos: 1590, candidatos: [1000, 590] },
    ]);
    expect(totais(abaixo)).toEqual({ A: 3, B: 2, C: 0 });
  });

  test("limite dos 10% no QP, 20% nas sobras e terceira fase aberta a todos", () => {
    const r = alocarCadeiras(4, [
      { id: "A", votos: 8000, candidatos: [7900, 50, 50] },
      { id: "B", votos: 2000, candidatos: [1500, 500] },
    ]);
    expect(r.qe).toBe(2500);
    expect(r.porAgremiacao.A).toEqual({ qp: 1, sobras: 1, total: 2 });
    expect(r.porAgremiacao.B).toEqual({ qp: 0, sobras: 2, total: 2 });
  });

  test("ninguém alcança o QE: elegem-se os mais votados", () => {
    const r = alocarCadeiras(3, [
      { id: "A", votos: 900, candidatos: [500, 400] },
      { id: "B", votos: 800, candidatos: [800] },
      { id: "C", votos: 700, candidatos: [600, 100] },
      { id: "D", votos: 600, candidatos: [600] },
    ]);
    expect(r.semQuociente).toBe(true);
    expect(totais(r)).toEqual({ A: 0, B: 1, C: 1, D: 1 });
  });

  test("sem votos não aloca e o total nunca passa das vagas", () => {
    expect(totais(alocarCadeiras(5, [{ id: "A", votos: 0, candidatos: [] }]))).toEqual({ A: 0 });
    const r = alocarCadeiras(70, [
      { id: "A", votos: 900_000, candidatos: muitos(900_000, 90) },
      { id: "B", votos: 600_000, candidatos: muitos(600_000, 90) },
      { id: "C", votos: 120_000, candidatos: muitos(120_000, 10) },
    ]);
    expect(Object.values(totais(r)).reduce((s, x) => s + x, 0)).toBe(70);
  });
});
