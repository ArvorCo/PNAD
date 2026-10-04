import { describe, expect, test } from "bun:test";
import { escreverHash, lerHash, lerReplay, UI_PADRAO } from "../../src/ui/control/router.ts";
import { criarLeitorUf, destinoDaUf, destinoDoDigito, subirNivel } from "../../src/ui/control/navegacao.ts";
import { expandirPlaylist, normalizarPlaylist, proximoIndice } from "../../src/ui/control/rotation.ts";
import { criarIndice, normalizar } from "../../src/ui/control/search.ts";
import { AMOSTRA_CONFIG } from "../../src/ui/data/amostra.ts";
import type { Estado } from "../../src/ui/state/types.ts";

describe("hash", () => {
  test("padrão sem hash", () => {
    expect(lerHash("")).toEqual(UI_PADRAO);
    expect(escreverHash(UI_PADRAO)).toBe("#v=pres");
  });

  test("ida e volta com todos os campos", () => {
    const h = "#v=mun&uf=SP&mun=71072&z=0248&auto=0&hud=0&replay=2026-10-04T17:30:00-03:00,60";
    const ui = lerHash(h);
    expect(ui).toMatchObject({ v: "mun", uf: "SP", mun: "71072", zonas: true, zona: "0248", auto: false, hud: false });
    expect(ui.replay).toEqual({ inicio: "2026-10-04T17:30:00-03:00", speed: 60 });
    expect(escreverHash(ui)).toBe(h);
  });

  test("mock assume speed 60 e z=1 liga zonas sem zona escolhida", () => {
    const ui = lerHash("mock=1&v=pres-uf&uf=mg&z=1");
    expect(ui.mock).toBe(true);
    expect(ui.speed).toBe(60);
    expect(ui.uf).toBe("MG");
    expect(ui.zonas).toBe(true);
    expect(ui.zona).toBeNull();
    expect(escreverHash(ui)).toBe("#v=pres-uf&uf=MG&z=1&mock=1");
  });

  test("valores inválidos caem no padrão", () => {
    const ui = lerHash("v=<script>&uf=xyz&mun=abc&speed=-3");
    expect(ui.v).toBe("pres");
    expect(ui.uf).toBeNull();
    expect(ui.mun).toBeNull();
    expect(ui.speed).toBe(0.1);
    expect(lerReplay("ontem,60")).toBeNull();
  });
});

describe("navegação", () => {
  test("dígitos de cargo", () => {
    expect(destinoDoDigito("1", "SP")?.v).toBe("pres");
    expect(destinoDoDigito("6", null)).toMatchObject({ v: "fed-uf", uf: "SP" });
    expect(destinoDoDigito("7", "DF")).toMatchObject({ v: "dis-df", uf: "DF" });
    expect(destinoDoDigito("8", "SP")).toMatchObject({ v: "dis-df", uf: "DF" });
    expect(destinoDoDigito("9", null)?.v).toBe("ritmo");
    expect(destinoDoDigito("0", null)?.v).toBe("mov");
    expect(destinoDoDigito("2", null)).toBeNull();
  });

  test("variante por UF", () => {
    expect(destinoDaUf("pres", "rj")).toMatchObject({ v: "pres-uf", uf: "RJ" });
    expect(destinoDaUf("gov", "BA").v).toBe("gov-uf");
    expect(destinoDaUf("est-uf", "DF").v).toBe("dis-df");
    expect(destinoDaUf("dis-df", "SP").v).toBe("est-uf");
  });

  test("Backspace sobe um nível por vez", () => {
    let d = subirNivel({ v: "mun", uf: "SP", mun: "71072", zonas: true, zona: "0001" });
    expect(d).toMatchObject({ zona: null, zonas: true });
    d = subirNivel(d ?? UI_PADRAO);
    expect(d).toMatchObject({ zonas: false, v: "mun" });
    d = subirNivel(d ?? UI_PADRAO);
    expect(d).toMatchObject({ v: "pres-uf", uf: "SP", mun: null });
    d = subirNivel(d ?? UI_PADRAO);
    expect(d).toMatchObject({ v: "pres", uf: null });
    expect(subirNivel({ v: "pres", uf: null, mun: null, zonas: false, zona: null })).toBeNull();
  });

  test("duas letras em 900 ms viram UF", () => {
    const ler = criarLeitorUf(900);
    expect(ler("s", 0)).toBeNull();
    expect(ler("p", 500)).toBe("SP");
    expect(ler("r", 1000)).toBeNull();
    expect(ler("j", 2500)).toBeNull(); // passou da janela
    expect(ler("x", 2600)).toBeNull();
  });
});

describe("playlist", () => {
  const estado = (pst: Record<string, number>) =>
    ({ ufs: Object.entries(pst).map(([uf, p]) => ({ uf, pst: p })), br: { st: 1 } }) as unknown as Estado;

  test("$destaque pula UFs com pst < 5 e ordena por eleitorado", () => {
    const pl = normalizarPlaylist({ dwell: 15, itens: [{ v: "pres" }, { v: "pres-uf", uf: "$destaque", max: 3 }, "ritmo"] });
    const e = expandirPlaylist(pl, estado({ SP: 3, MG: 10, RJ: 50, BA: 7, AC: 90 }), AMOSTRA_CONFIG, null);
    expect(e.map(x => `${x.v}${x.uf ? `:${x.uf}` : ""}`)).toEqual(["pres", "pres-uf:MG", "pres-uf:RJ", "pres-uf:BA", "ritmo"]);
    expect(e[0]?.dwellMs).toBe(15_000);
    expect(expandirPlaylist(pl, null, AMOSTRA_CONFIG, 5)[0]?.dwellMs).toBe(5000);
  });

  test("índice circular", () => {
    expect(proximoIndice(2, 3, 1)).toBe(0);
    expect(proximoIndice(0, 3, -1)).toBe(2);
    expect(proximoIndice(0, 0, 1)).toBe(0);
  });

  test("playlist inválida cai na padrão", () => {
    expect(normalizarPlaylist(null).itens.length).toBeGreaterThan(0);
    expect(normalizarPlaylist(["pres", "gov"]).itens.map(i => i.v)).toEqual(["pres", "gov"]);
  });

  test("formato de public/playlist.json: view e lista de destaque", () => {
    const pl = normalizarPlaylist({ itens: [{ view: "pres", dwell: 40 }, { view: "pres-uf", uf: "$destaque", dwell: 25 }], destaque: ["rj", "SP", "AC"] });
    const e = expandirPlaylist(pl, estado({ SP: 10, RJ: 50, AC: 1 }), AMOSTRA_CONFIG, null);
    expect(e.map(x => `${x.v}${x.uf ? `:${x.uf}` : ""}`)).toEqual(["pres", "pres-uf:RJ", "pres-uf:SP"]);
    expect(e[0]?.dwellMs).toBe(40_000);
  });
});

describe("busca", () => {
  test("sem acento, capital antes", () => {
    expect(normalizar("São Paulo")).toBe("sao paulo");
    const i = criarIndice();
    i.adicionarConfig(AMOSTRA_CONFIG);
    const r = i.buscar("sao pau");
    expect(r.slice(0, 2).some(a => a.tipo === "mun" && a.cd === "71072")).toBe(true);
    expect(i.buscar("belo hor")[0]).toMatchObject({ tipo: "mun", uf: "MG", cd: "41238" });
    expect(i.buscar("minas")[0]).toMatchObject({ tipo: "uf", uf: "MG" });
    expect(i.buscar("bh").length).toBeLessThanOrEqual(8);
    expect(i.buscar("")).toEqual([]);
  });
});
