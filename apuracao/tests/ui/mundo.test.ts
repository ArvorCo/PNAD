import { describe, expect, test } from "bun:test";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import {
  ajusteMundo,
  CAIXA_MUNDO,
  ordemDeDesenho,
  RAIO_EXTRA,
  RAIO_MIN,
  raioBolha,
  rotulosSemSobreposicao,
} from "../../src/ui/components/mundo.ts";
import type { CidadeExterior, PedidoRotulo } from "../../src/ui/components/mundo.ts";
import { maioresCidades, unidadesDoExterior } from "../../src/ui/views/exterior.ts";
import type { State, UnidadeMapa } from "../../src/ui/state/types.ts";

const RAIZ = join(import.meta.dir, "../..");

describe("projeção do mundo", () => {
  test("a caixa inteira cabe em 1152 × 800 com a margem", () => {
    const a = ajusteMundo(1152, 800, 8);
    const [x0, y0] = a.projetar(CAIXA_MUNDO.lon0, CAIXA_MUNDO.lat1);
    const [x1, y1] = a.projetar(CAIXA_MUNDO.lon1, CAIXA_MUNDO.lat0);
    expect(x0).toBeGreaterThanOrEqual(8 - 1e-9);
    expect(x1).toBeLessThanOrEqual(1152 - 8 + 1e-9);
    expect(y0).toBeGreaterThanOrEqual(8 - 1e-9);
    expect(y1).toBeLessThanOrEqual(800 - 8 + 1e-9);
    // A largura limita: ocupa toda a largura útil e centraliza na vertical.
    expect(x1 - x0).toBeCloseTo(1152 - 16, 6);
    expect((y0 + y1) / 2).toBeCloseTo(400, 6);
  });

  test("cosseno de 20° na longitude, norte para cima", () => {
    const a = ajusteMundo();
    expect(a.cos).toBeCloseTo(Math.cos((20 * Math.PI) / 180), 12);
    const [xl, yl] = a.projetar(-9.14, 38.72); // Lisboa
    const [xt, yt] = a.projetar(139.69, 35.69); // Tóquio
    const [, ys] = a.projetar(151.21, -33.87); // Sydney
    expect(xt).toBeGreaterThan(xl);
    expect(yt).toBeGreaterThan(yl);
    expect(ys).toBeGreaterThan(yt);
  });
});

describe("raio da bolha", () => {
  test("6 px no mínimo e 28 px no maior eleitorado, pela raiz", () => {
    expect(raioBolha(0, 1000)).toBe(RAIO_MIN);
    expect(raioBolha(undefined, 1000)).toBe(RAIO_MIN);
    expect(raioBolha(500, 0)).toBe(RAIO_MIN);
    expect(raioBolha(1000, 1000)).toBe(RAIO_MIN + RAIO_EXTRA);
    expect(raioBolha(250, 1000)).toBeCloseTo(RAIO_MIN + RAIO_EXTRA / 2, 12);
    expect(raioBolha(2000, 1000)).toBe(RAIO_MIN + RAIO_EXTRA);
  });

  test("bolhas pequenas desenhadas por último", () => {
    const ordem = ordemDeDesenho([
      { cd: "b", r: 6 },
      { cd: "a", r: 28 },
      { cd: "c", r: 12 },
      { cd: "d", r: 6 },
    ]);
    expect(ordem.map(o => o.cd)).toEqual(["a", "c", "b", "d"]);
  });
});

describe("rótulos sem sobreposição", () => {
  const pedido = (cd: string, x: number, y: number, w = 100): PedidoRotulo => ({ cd, x, y, r: 10, w, h: 32 });

  test("à direita da bolha quando cabe", () => {
    const [p] = rotulosSemSobreposicao([pedido("a", 100, 100)], 1152, 800);
    expect(p).toEqual({ cd: "a", x: 116, y: 84, w: 100, h: 32 });
  });

  test("vira para a esquerda na borda direita", () => {
    const [p] = rotulosSemSobreposicao([pedido("a", 1100, 100)], 1152, 800);
    expect(p?.x).toBe(1100 - 10 - 6 - 100);
  });

  test("o rótulo da cidade menor some quando cruza o de uma maior nos dois lados", () => {
    const postos = rotulosSemSobreposicao([pedido("grande", 300, 100), pedido("pequena", 380, 110)], 1152, 800);
    expect(postos.map(p => p.cd)).toEqual(["grande"]);
  });

  test("a cidade menor usa a esquerda quando a direita está ocupada", () => {
    const postos = rotulosSemSobreposicao([pedido("grande", 300, 100), pedido("pequena", 330, 100)], 1152, 800);
    expect(postos.map(p => p.cd)).toEqual(["grande", "pequena"]);
    expect(postos[1]?.x).toBe(330 - 10 - 6 - 100);
  });
});

describe("unidades do exterior", () => {
  const estado = (municipios: { cd: string; nm: string; te?: number }[]): State =>
    ({ config: { municipios: { ZZ: municipios.map(m => ({ ...m, cdi: "", c: false, z: ["0001"] })) } } }) as unknown as State;

  test("cadastro como base cinza e o mapa do TSE por cima, preservando o eleitorado", () => {
    const s = estado([
      { cd: "1", nm: "LISBOA", te: 100 },
      { cd: "2", nm: "PORTO", te: 50 },
    ]);
    const mapa: UnidadeMapa[] = [{ cd: "1", nm: "Lisboa", pst: 40, tf: false }];
    const u = unidadesDoExterior(s, mapa);
    expect(u.find(x => x.cd === "1")).toEqual({ cd: "1", nm: "Lisboa", pst: 40, tf: false, te: 100 });
    expect(u.find(x => x.cd === "2")).toEqual({ cd: "2", nm: "PORTO", pst: 0, tf: false, te: 50 });
    expect(maioresCidades(u, 1).map(x => x.cd)).toEqual(["1"]);
  });
});

describe("public/exterior_cidades.json", () => {
  const cidades = JSON.parse(readFileSync(join(RAIZ, "public/exterior_cidades.json"), "utf8")) as CidadeExterior[];
  const cm = JSON.parse(readFileSync(join(RAIZ, "tests/fixtures/mun-e006257-cm.json"), "utf8")) as {
    abr: { cd: string; mu: { cd: string }[] }[];
  };
  const zz = new Set(cm.abr.find(a => a.cd.toLowerCase() === "zz")?.mu.map(m => m.cd) ?? []);

  test("186 cidades com código único, todas no cadastro do TSE", () => {
    expect(zz.size).toBe(186);
    expect(cidades).toHaveLength(186);
    expect(new Set(cidades.map(c => c.cd)).size).toBe(186);
    for (const c of cidades) expect(zz.has(c.cd)).toBe(true);
  });

  test("coordenadas válidas e fora do Brasil, com país ISO-2", () => {
    for (const c of cidades) {
      expect(c.lat).toBeGreaterThanOrEqual(-60);
      expect(c.lat).toBeLessThanOrEqual(85);
      expect(c.lon).toBeGreaterThanOrEqual(-180);
      expect(c.lon).toBeLessThanOrEqual(180);
      expect(c.pais).toMatch(/^[A-Z]{2}$/);
      expect(c.pais).not.toBe("BR");
    }
  });

  test("cidades de consulado no país certo", () => {
    const pais = (cd: string): string | undefined => cidades.find(c => c.cd === cd)?.pais;
    const porNome = new Map(cidades.map(c => [c.nm, c.pais]));
    expect(porNome.get("LISBOA")).toBe("PT");
    expect(porNome.get("RIO BRANCO")).toBe("UY");
    expect(porNome.get("SÃO JOSÉ")).toBe("CR");
    expect(porNome.get("GEORGETOWN")).toBe("GY");
    expect(porNome.get("CONCEPCIÓN")).toBe("PY");
    expect(pais("29254")).toBe("CI"); // Abidjã
  });
});
