import { describe, expect, test } from "bun:test";
import {
  comSinal,
  compacto,
  decimal,
  dezessete,
  duracao,
  eleitores,
  hora,
  horaCurta,
  inteiro,
  nomeProprio,
  pct,
  quantidade,
  regressiva,
} from "../../src/ui/data/format.ts";

describe("números pt-BR", () => {
  test("inteiro e decimal", () => {
    expect(inteiro(1234567)).toBe("1.234.567");
    expect(decimal(62.43)).toBe("62,4");
    expect(decimal(-1.5, 1)).toBe("−1,5");
  });

  test("percentual com 1 ou 2 casas", () => {
    expect(pct(62.43)).toBe("62,4%");
    expect(pct(62.436, 2)).toBe("62,44%");
  });

  test("sinal", () => {
    expect(comSinal(3.24)).toBe("+3,2");
    expect(comSinal(-1)).toBe("−1,0");
    expect(comSinal(0.01)).toBe("0,0");
  });

  test("regra da casa: mil sem de, mi com de", () => {
    expect(eleitores(660_000)).toBe("660 mil eleitores");
    expect(eleitores(2_010_000)).toBe("2,01 mi de eleitores");
    expect(quantidade(158_745_502, "eleitores")).toBe("158,75 mi de eleitores");
    expect(compacto(950)).toBe("950");
  });
});

describe("horas em Brasília", () => {
  test("HH:MM:SS e HH:MM", () => {
    expect(hora("2026-10-04T22:38:05Z")).toBe("19:38:05");
    expect(horaCurta("2026-10-04T22:38:05Z")).toBe("19:38");
    expect(hora(null)).toBe("");
    expect(hora("lixo")).toBe("");
  });

  test("17:00 do dia em Brasília, mesmo depois da meia-noite UTC", () => {
    expect(dezessete(new Date("2026-10-05T01:30:00Z")).toISOString()).toBe("2026-10-04T20:00:00.000Z");
    expect(dezessete(new Date("2026-10-04T12:00:00Z")).toISOString()).toBe("2026-10-04T20:00:00.000Z");
  });

  test("duração e contagem regressiva", () => {
    expect(duracao(42)).toBe("42 s");
    expect(duracao(185)).toBe("3 min 05 s");
    expect(duracao(3720)).toBe("1 h 02 min");
    expect(regressiva(65)).toBe("01:05");
    expect(regressiva(3725)).toBe("01:02:05");
  });

  test("nome próprio", () => {
    expect(nomeProprio("SÃO JOSÉ DOS CAMPOS")).toBe("São José dos Campos");
  });
});
