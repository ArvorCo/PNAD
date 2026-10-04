import { describe, expect, test } from "bun:test";
import { intBR, numBR, pctN, simNao, simNao01, texto } from "../src/parse/numeros.ts";

describe("intBR", () => {
  test("converte inteiros em string", () => {
    expect(intBR("6773587")).toBe(6773587);
    expect(intBR("0")).toBe(0);
    expect(intBR("0004")).toBe(4);
    expect(intBR("1.234.567")).toBe(1234567);
  });
  test("tolera vazio e ausente", () => {
    expect(intBR("")).toBeNull();
    expect(intBR(undefined)).toBeNull();
    expect(intBR(null)).toBeNull();
    expect(intBR("  ")).toBeNull();
  });
  test("rejeita lixo e decimais", () => {
    expect(intBR("abc")).toBeNull();
    expect(intBR("0,68")).toBeNull();
  });
  test("aceita número", () => {
    expect(intBR(12)).toBe(12);
    expect(intBR(1.5)).toBeNull();
  });
});

describe("numBR", () => {
  test("decimal com vírgula, nove casas", () => {
    expect(numBR("0,675628098")).toBeCloseTo(0.675628098, 12);
    expect(numBR("85,540556281")).toBeCloseTo(85.540556281, 12);
    expect(numBR("100,00")).toBe(100);
    expect(numBR("100")).toBe(100);
    expect(numBR("0,00")).toBe(0);
  });
  test("tolera vazio e lixo", () => {
    expect(numBR("")).toBeNull();
    expect(numBR(undefined)).toBeNull();
    expect(numBR("n/a")).toBeNull();
  });
});

describe("simNao e pctN", () => {
  test("simNao", () => {
    expect(simNao("s")).toBe(true);
    expect(simNao("n")).toBe(false);
    expect(simNao("S")).toBe(true);
    expect(simNao("")).toBeNull();
    expect(simNao(undefined)).toBeNull();
    expect(simNao01("s")).toBe(1);
    expect(simNao01("n")).toBe(0);
  });
  test("pctN prefere a versão precisa", () => {
    expect(pctN("19,230769231", "19,23")).toBeCloseTo(19.230769231, 12);
    expect(pctN("", "19,23")).toBe(19.23);
    expect(pctN(undefined, undefined)).toBeNull();
  });
  test("texto", () => {
    expect(texto("  a ")).toBe("a");
    expect(texto("")).toBeNull();
    expect(texto(undefined)).toBeNull();
  });
});
