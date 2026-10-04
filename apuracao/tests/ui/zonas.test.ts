import { describe, expect, test } from "bun:test";
import { assinatura, LARGURA_NUMERO, layoutZonas, nivelRotulo, numeroZona, pesosZonas } from "../../src/ui/components/zonas.ts";
import type { UnidadeMapa } from "../../src/ui/state/types.ts";

const z = (cd: string, te?: number): UnidadeMapa => ({ cd, nm: `Zona ${cd}`, te, pst: 0, tf: false });
const area = (t: { x0: number; y0: number; x1: number; y1: number }): number => (t.x1 - t.x0) * (t.y1 - t.y0);

describe("pesos", () => {
  test("sem eleitorado, áreas iguais", () => {
    expect(pesosZonas([z("1"), z("2", 0)])).toEqual([1, 1]);
  });
  test("eleitorado ausente vira a mediana dos presentes", () => {
    expect(pesosZonas([z("1", 100), z("2"), z("3", 300)])).toEqual([100, 200, 300]);
  });
});

describe("layoutZonas", () => {
  test("áreas proporcionais ao eleitorado e tudo dentro da caixa", () => {
    const zonas = [z("0005", 400), z("0001", 100), z("0003", 300), z("0002", 200)];
    const tiles = layoutZonas(zonas, 1152, 800, 0);
    expect(tiles.map(t => t.cd)).toEqual(["0001", "0002", "0003", "0005"]);
    const total = tiles.reduce((s, t) => s + area(t), 0);
    expect(total).toBeCloseTo(1152 * 800, 3);
    const a1 = tiles[0];
    const a5 = tiles[3];
    if (!a1 || !a5) throw new Error("faltou tile");
    expect(area(a5) / area(a1)).toBeCloseTo(4, 6);
    for (const t of tiles) {
      expect(t.x0).toBeGreaterThanOrEqual(0);
      expect(t.y1).toBeLessThanOrEqual(800 + 1e-9);
    }
  });

  test("57 zonas com espaçamento 4 cabem e não se sobrepõem", () => {
    const zonas = Array.from({ length: 57 }, (_, i) => z(String(i + 1).padStart(4, "0"), 50000 + ((i * 7919) % 400000)));
    const tiles = layoutZonas(zonas);
    expect(tiles.length).toBe(57);
    for (let i = 0; i < tiles.length; i++) {
      for (let j = i + 1; j < tiles.length; j++) {
        const a = tiles[i];
        const b = tiles[j];
        if (!a || !b) continue;
        const cruza = a.x0 < b.x1 - 1e-6 && b.x0 < a.x1 - 1e-6 && a.y0 < b.y1 - 1e-6 && b.y0 < a.y1 - 1e-6;
        expect(cruza).toBe(false);
      }
    }
  });

  test("zona única ocupa a caixa inteira", () => {
    const [t] = layoutZonas([z("0001", 1000)], 1152, 800, 4);
    expect(t && area(t)).toBeCloseTo(1152 * 800, 3);
  });

  test("lista vazia não quebra", () => {
    expect(layoutZonas([])).toEqual([]);
  });
});

describe("rótulos", () => {
  test("limiares 140 × 70 e 40 × 24", () => {
    expect(nivelRotulo(140, 70)).toBe("completo");
    expect(nivelRotulo(139, 200)).toBe("numero");
    expect(nivelRotulo(40, 24)).toBe("numero");
    expect(nivelRotulo(39, 100)).toBe("nada");
    expect(nivelRotulo(100, 23)).toBe("nada");
  });

  test("número só aparece quando cabe na largura do tile", () => {
    expect(nivelRotulo(44, 100, LARGURA_NUMERO)).toBe("nada");
    expect(nivelRotulo(LARGURA_NUMERO + 8, 30, LARGURA_NUMERO)).toBe("numero");
  });

  test("número da zona com 4 dígitos", () => {
    expect(numeroZona("248")).toBe("0248");
    expect(numeroZona("sp71072-z0248")).toBe("0248");
    expect(numeroZona("0001")).toBe("0001");
  });

  test("assinatura independe da ordem e muda com o eleitorado", () => {
    expect(assinatura([z("2", 5), z("1", 3)])).toBe(assinatura([z("1", 3), z("2", 5)]));
    expect(assinatura([z("1", 3)])).not.toBe(assinatura([z("1", 4)]));
  });
});
