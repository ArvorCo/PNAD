import { describe, expect, test } from "bun:test";
import type { ArquivoRegistro } from "../src/types.ts";
import {
  ab, chave, cm, criarUrls, e, eleC, keyAb, keyU, pad4, parseChave, registroDeArquivos, segCargo, segEleicao, u, urlDe,
} from "../src/tse/urls.ts";
import { lerCm } from "./helpers.ts";

const B = "https://resultados.tse.jus.br/oficial";

describe("segmentos", () => {
  test("pad4, cargo e eleição", () => {
    expect(pad4(1)).toBe("0001");
    expect(segCargo(1)).toBe("c0001");
    expect(segCargo(25)).toBe("c0025");
    expect(segEleicao(6257)).toBe("e006257");
    expect(segEleicao(619)).toBe("e000619");
  });
});

describe("URLs reais verificadas", () => {
  test("config", () => {
    expect(eleC()).toBe(`${B}/comum/config/ele-c.json`);
    expect(cm(6257)).toBe(`${B}/ele2026/6257/config/mun-e006257-cm.json`);
  });
  test("monitoramento", () => {
    expect(ab(6257, "br")).toBe(`${B}/ele2026/6257/dados/br/br-e006257-ab.json`);
    expect(ab(6257, "sp")).toBe(`${B}/ele2026/6257/dados/sp/sp-e006257-ab.json`);
  });
  test("resultado em todos os níveis", () => {
    expect(u(6257, 1, "br")).toBe(`${B}/ele2026/6257/dados/br/br-c0001-e006257-u.json`);
    expect(u(6257, 1, "uf", "sp")).toBe(`${B}/ele2026/6257/dados/sp/sp-c0001-e006257-u.json`);
    expect(u(6257, 1, "mu", "sp", "71072")).toBe(`${B}/ele2026/6257/dados/sp/sp71072-c0001-e006257-u.json`);
    expect(u(6257, 1, "zona", "sp", "71072", "0001")).toBe(`${B}/ele2026/6257/dados/sp/sp71072-z0001-c0001-e006257-u.json`);
    expect(u(6257, 1, "zona", "sp", "71072", "1")).toBe(`${B}/ele2026/6257/dados/sp/sp71072-z0001-c0001-e006257-u.json`);
    expect(u(6259, 8, "uf", "df")).toBe(`${B}/ele2026/6259/dados/df/df-c0008-e006259-u.json`);
    expect(u(6261, 25, "mu", "pe", "30015")).toBe(`${B}/ele2026/6261/dados/pe/pe30015-c0025-e006261-u.json`);
  });
  test("agregado -e", () => {
    expect(e(6259, 6, "sp")).toBe(`${B}/ele2026/6259/dados/sp/sp-c0006-e006259-e.json`);
  });
  test("faltando uf ou município lança", () => {
    expect(() => u(6257, 1, "uf")).toThrow();
    expect(() => u(6257, 1, "mu", "sp")).toThrow();
    expect(() => u(6257, 1, "zona", "sp", "71072")).toThrow();
  });
  test("base alternativa", () => {
    expect(criarUrls("http://127.0.0.1:9999/x").eleC()).toBe("http://127.0.0.1:9999/x/comum/config/ele-c.json");
  });
});

describe("chaves", () => {
  test("formato tipo:ele:cargo:nivel:uf:mun:zona e ida e volta", () => {
    const k = keyU(6257, 1, "zona", "sp", "71072", "1");
    expect(chave(k)).toBe("u:6257:1:zona:sp:71072:0001");
    expect(parseChave("u:6257:1:zona:sp:71072:0001")).toEqual(k);
    expect(chave(keyAb(6257, "br"))).toBe("ab:6257::br:::");
    expect(chave(keyAb(6257, "sp"))).toBe("ab:6257::uf:sp::");
    expect(chave(keyU(6257, 1, "br", "sp"))).toBe("u:6257:1:br:::");
    expect(urlDe(parseChave("u:6261:25:mu:pe:30015:"))).toBe(`${B}/ele2026/6261/dados/pe/pe30015-c0025-e006261-u.json`);
    expect(urlDe(parseChave("ele-c::::::"))).toBe(`${B}/comum/config/ele-c.json`);
  });
  test("chave inválida lança", () => {
    expect(() => parseChave("u:1")).toThrow();
    expect(() => parseChave("x:6257:1:br:::")).toThrow();
    expect(() => parseChave("u:6257:1:pais:::")).toThrow();
  });
});

describe("registroDeArquivos", () => {
  const cms = new Map([
    [6257, lerCm("mun-e006257-cm.json")],
    [6259, lerCm("mun-e006259-cm.json")],
    [6261, lerCm("mun-e006261-cm.json")],
  ]);
  const linhas: ArquivoRegistro[] = [...registroDeArquivos(cms)];
  const contar = (f: (a: ArquivoRegistro) => boolean): number => linhas.filter(f).length;
  const de = (ele: number, tipo: string, nivel: string | null): ArquivoRegistro[] =>
    linhas.filter((a) => a.ele === ele && a.tipo === tipo && a.nivel === nivel);

  test("chaves e URLs únicas", () => {
    expect(new Set(linhas.map((a) => a.chave)).size).toBe(linhas.length);
    expect(new Set(linhas.map((a) => a.url)).size).toBe(linhas.length);
  });
  test("6257: 5.757 municípios, 6.292 zonas, 28 abrangências com zz", () => {
    expect(de(6257, "u", "mu").length).toBe(5757);
    expect(de(6257, "u", "zona").length).toBe(6292);
    const abUf = de(6257, "ab", "uf");
    expect(abUf.length).toBe(28);
    expect(abUf.some((a) => a.uf === "zz")).toBe(true);
    expect(de(6257, "u", "uf").length).toBe(28);
    expect(de(6257, "u", "br").length).toBe(1);
  });
  test("6259: 5.571 municípios × 4 cargos, 7 fora do DF e 8 só no DF", () => {
    const mu = de(6259, "u", "mu");
    expect(mu.length).toBe(5571 * 4);
    expect(new Set(mu.map((a) => a.mun)).size).toBe(5571);
    const zonas = de(6259, "u", "zona");
    expect(zonas.length).toBe(6106 * 4);
    expect(de(6259, "ab", "uf").length).toBe(27);
    expect(mu.some((a) => a.uf === "df" && a.cargo === 7)).toBe(false);
    expect(mu.some((a) => a.uf !== "df" && a.cargo === 8)).toBe(false);
    expect(mu.filter((a) => a.uf === "df" && a.cargo === 8).length).toBe(1);
    expect(de(6259, "u", "br").every((a) => a.tier === 4 && a.sonda)).toBe(true);
  });
  test("6261: só Fernando de Noronha, zona 0004", () => {
    const mu = de(6261, "u", "mu");
    expect(mu.map((a) => a.chave)).toEqual(["u:6261:25:mu:pe:30015:"]);
    expect(de(6261, "u", "zona").map((a) => a.chave)).toEqual(["u:6261:25:zona:pe:30015:0004"]);
  });
  test("tiers", () => {
    expect(contar((a) => a.tipo === "ele-c")).toBe(1);
    expect(contar((a) => a.tipo === "cm")).toBe(3);
    expect(contar((a) => a.tier === 1)).toBe(28 + 27 + 1);
    expect(contar((a) => a.tier === 2)).toBe(5757 + 5571 * 4 + 1);
    expect(contar((a) => a.tier === 3)).toBe(6292 + 6106 * 4 + 1);
    expect(contar((a) => a.tipo === "e")).toBe(28 + 27 * 4 + 1);
    expect(linhas.filter((a) => a.tier === 2).every((a) => a.tipo === "u" && a.nivel === "mu")).toBe(true);
  });
});
