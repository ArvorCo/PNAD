import { describe, expect, test } from "bun:test";
import {
  afastarRotulos,
  chaveFeicao,
  chaveUnidade,
  FORA,
  IBGE_UF,
  LABEL_NUDGE,
  semGeometria,
} from "../../src/ui/components/mapa.ts";
import type { UnidadeMapa } from "../../src/ui/state/types.ts";

const un = (cd: string, cdi?: string): UnidadeMapa => ({ cd, cdi, nm: cd, pst: 0, tf: false });

describe("tabela IBGE → sigla", () => {
  test("27 UFs, siglas únicas e códigos de 2 dígitos", () => {
    const siglas = Object.values(IBGE_UF);
    expect(siglas.length).toBe(27);
    expect(new Set(siglas).size).toBe(27);
    expect(IBGE_UF["35"]).toBe("SP");
    expect(IBGE_UF["53"]).toBe("DF");
    for (const k of Object.keys(IBGE_UF)) expect(k).toMatch(/^[1-5]\d$/);
  });

  test("rótulos deslocados e ajustes só para siglas existentes", () => {
    const siglas = new Set(Object.values(IBGE_UF));
    for (const s of [...Object.keys(FORA), ...Object.keys(LABEL_NUDGE)]) expect(siglas.has(s)).toBe(true);
  });
});

describe("chaves", () => {
  test("UF casa codarea com cd minúsculo do TSE", () => {
    expect(chaveFeicao("uf", "35")).toBe("sp");
    expect(chaveUnidade("uf", un("SP"))).toBe("sp");
  });

  test("município casa codarea com cdi", () => {
    expect(chaveFeicao("mun", "3550308")).toBe("3550308");
    expect(chaveUnidade("mun", un("71072", "3550308"))).toBe("3550308");
  });

  test("município do TSE sem polígono é listado, não quebra", () => {
    const chaves = new Set(["5103403"]);
    const sem = semGeometria("mun", [un("90670", "5103403"), un("89958", "5101837"), un("99999")], chaves);
    expect(sem.map(u => u.cd)).toEqual(["89958", "99999"]);
  });
});

describe("afastarRotulos", () => {
  test("empurra para baixo os que se cruzam na horizontal", () => {
    const out = afastarRotulos(
      [
        { id: "a", x: 0, y: 30, w: 40, h: 30 },
        { id: "b", x: 10, y: 40, w: 40, h: 30 },
        { id: "c", x: 200, y: 41, w: 40, h: 30 },
      ],
      4,
    );
    const b = out.find(r => r.id === "b");
    const c = out.find(r => r.id === "c");
    expect(b?.y).toBe(64);
    expect(c?.y).toBe(41);
  });

  test("não altera a entrada", () => {
    const entrada = [
      { id: "a", x: 0, y: 10, w: 10, h: 10 },
      { id: "b", x: 0, y: 12, w: 10, h: 10 },
    ];
    afastarRotulos(entrada);
    expect(entrada[1]?.y).toBe(12);
  });
});
