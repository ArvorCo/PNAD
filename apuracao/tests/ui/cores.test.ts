import { describe, expect, test } from "bun:test";
import {
  banda,
  contraste,
  corCampo,
  corCandidato,
  corPorBanda,
  fromLab,
  mix,
  NAO_INICIADO,
  OUTROS_TEXTO,
  normalizarCampos,
  normalizarCores,
  PAPEL,
  ramp,
  textoSobre,
  toLab,
} from "../../src/ui/data/cores.ts";

describe("OKLab", () => {
  test("ida e volta preserva a cor", () => {
    for (const h of ["#b02f21", "#1457aa", "#0f7f5f", "#f4f0e6", "#000000", "#ffffff"]) expect(fromLab(toLab(h))).toBe(h);
  });

  test("mistura nas pontas e no meio", () => {
    expect(mix(PAPEL, "#1457aa", 0)).toBe(PAPEL);
    expect(mix(PAPEL, "#1457aa", 1)).toBe("#1457aa");
    const meio = toLab(mix("#000000", "#ffffff", 0.5));
    expect(meio[0]).toBeCloseTo(0.5, 2);
  });

  test("rampa", () => {
    expect(ramp(["#000000", "#ffffff"], 0)).toBe("#000000");
    expect(ramp(["#000000", "#808080", "#ffffff"], 1)).toBe("#ffffff");
  });
});

describe("bandas de parcialidade", () => {
  test("35 / 60 / 85 / 100% e cinza sem seção", () => {
    expect(banda(0)).toBe(0);
    expect(banda(10)).toBe(0.35);
    expect(banda(30)).toBe(0.6);
    expect(banda(99.9)).toBe(0.85);
    expect(banda(100)).toBe(1);
    expect(corPorBanda("#1457aa", 0)).toBe(NAO_INICIADO);
    expect(corPorBanda("#1457aa", 100)).toBe("#1457aa");
    expect(corPorBanda("#1457aa", 50)).not.toBe("#1457aa");
  });
});

describe("cores de candidato e campo", () => {
  test("fixa por número e sequência para os demais", () => {
    expect(corCandidato("13", 5)).toBe("#b02f21");
    expect(corCandidato("22", 0)).toBe("#1457aa");
    const cores = normalizarCores({ candidatos: { "55": "#123456" }, sequencia: ["#aaaaaa", "#bbbbbb"] });
    expect(corCandidato("55", 0, cores)).toBe("#123456");
    expect(corCandidato("70", 3, cores)).toBe("#bbbbbb");
    const f0 = normalizarCores({ candidatos: { "13": "#b02f21" }, terceiro: "#0f7f5f", outros: ["#8a8f98"] });
    expect(f0.sequencia).toEqual(["#0f7f5f", "#8a8f98"]);
  });

  test("campo com padrão e com campos.json", () => {
    expect(corCampo("direita")).toBe("#1457aa");
    expect(corCampo("qualquer")).toBe("#8a8f98");
    const campos = normalizarCampos({ partidos: { psdb: "centro-esquerda", X: "nada" }, campos: { centro: { cor: "#010203", rotulo: "centro" } } });
    expect(campos.partidos.PSDB).toBe("centro-esquerda");
    expect(campos.partidos.X).toBe("indefinido");
    expect(corCampo("centro", campos)).toBe("#010203");
  });

  test("contraste da paleta sobre papel", () => {
    expect(contraste("#b02f21", PAPEL)).toBeGreaterThan(4.5);
    expect(contraste("#1457aa", PAPEL)).toBeGreaterThan(4.5);
    // O teal da casa passa para texto grande e gráfico (3:1), não para texto pequeno sobre papel.
    expect(contraste("#0f7f5f", PAPEL)).toBeGreaterThan(3);
    expect(contraste(OUTROS_TEXTO, PAPEL)).toBeGreaterThan(4.5);
    expect(textoSobre("#142d2b")).toBe("#ffffff");
    expect(textoSobre(PAPEL)).toBe("#192e2b");
  });
});
