import { describe, expect, test } from "bun:test";
import { criarMock, INICIO_MOCK, PRESIDENTE_2026 } from "../../src/ui/data/mock.ts";
import { disputa } from "../../src/ui/state/selectors.ts";

const HORA = 3_600_000;

function mockEm(msDepoisDoInicio: number) {
  let real = 0;
  const m = criarMock({ speed: 1, agoraReal: () => real });
  real = msDepoisDoInicio;
  return m;
}

describe("mock determinístico", () => {
  test("antes das 17:00 nada foi totalizado", async () => {
    const e = await mockEm(0).estado();
    expect(e.br.st).toBe(0);
    expect(e.br.ts).toBeGreaterThan(0);
  });

  test("às 19:00 há seções, votos e 12 candidaturas reais", async () => {
    const m = mockEm(2 * HORA);
    const e = await m.estado();
    expect(e.br.pst).toBeGreaterThan(5);
    expect(e.br.pst).toBeLessThan(100);
    const r = await m.resultado({ ele: 6257, cargo: 1, abr: "br" });
    expect(r.cand.map(c => c.sqcand).sort()).toEqual(PRESIDENTE_2026.map(c => c.sqcand).sort());
    const soma = r.cand.reduce((s, c) => s + c.pvapn, 0);
    expect(soma).toBeCloseTo(100, 5);
    expect(r.v.tv).toBe(r.v.vv + r.v.vb + r.v.vn);
  });

  test("é determinístico", async () => {
    const a = await mockEm(2 * HORA).resultado({ ele: 6257, cargo: 1, abr: "sp" });
    const b = await mockEm(2 * HORA).resultado({ ele: 6257, cargo: 1, abr: "sp" });
    expect(a).toEqual(b);
  });

  test("virada forçada em MG e regressão de seções na BA", async () => {
    const cedo = disputa((await mockEm(0.6 * HORA).resultado({ ele: 6257, cargo: 1, abr: "mg" })).cand).lider?.n;
    const tarde = disputa((await mockEm(7 * HORA).resultado({ ele: 6257, cargo: 1, abr: "mg" })).cand).lider?.n;
    expect(cedo).toBe("13");
    expect(tarde).toBe("22");
    const t1 = Date.parse("2026-10-04T18:39:30-03:00") - INICIO_MOCK;
    const t2 = Date.parse("2026-10-04T18:41:00-03:00") - INICIO_MOCK;
    const antes = (await mockEm(t1).estado()).ufs.find(u => u.uf === "BA")?.st ?? 0;
    const depois = (await mockEm(t2).estado()).ufs.find(u => u.uf === "BA")?.st ?? 0;
    expect(depois).toBeLessThan(antes);
    const anomalias = await mockEm(7 * HORA).anomalias();
    expect(anomalias.some(a => a.tipo === "virada" && a.abr === "mg")).toBe(true);
    expect(anomalias.some(a => a.tipo === "regressao")).toBe(true);
    expect(anomalias.some(a => a.tipo === "fechou")).toBe(true);
  });

  test("mapas por UF, município e zona", async () => {
    const m = mockEm(3 * HORA);
    expect((await m.mapa({ ele: 6257, cargo: 1, nivel: "uf", pai: "br" })).unidades).toHaveLength(27);
    const mun = await m.mapa({ ele: 6257, cargo: 1, nivel: "mun", pai: "sp" });
    expect(mun.unidades.length).toBeGreaterThan(0);
    const zonas = await m.mapa({ ele: 6257, cargo: 1, nivel: "zona", pai: "sp71072" });
    expect(zonas.unidades).toHaveLength(57);
    const z = await m.resultado({ ele: 6257, cargo: 1, abr: "sp71072-z0001" });
    expect(z.tpabr).toBe("zona");
    const gov = await m.resultado({ ele: 6259, cargo: 3, abr: "sp" });
    expect(gov.cargo.nv).toBe(1);
    const sen = await m.resultado({ ele: 6259, cargo: 5, abr: "sp" });
    expect(sen.cargo.nv).toBe(2);
    await expect(m.resultado({ ele: 6259, cargo: 3, abr: "br" })).rejects.toThrow();
  });

  test("série tem pontos e registra a virada de MG", async () => {
    const s = await mockEm(7 * HORA).serie({ ele: 6257, cargo: 1, abr: "mg" });
    expect(s.pontos.length).toBeGreaterThan(10);
    expect(s.viradas.length).toBeGreaterThan(0);
  });
});
