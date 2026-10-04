import { describe, expect, test } from "bun:test";
import { compararU, MAX_EVENTOS_CANDIDATO } from "../src/collector/anomalias.ts";
import type { CandResumo, TotaisResumo } from "../src/collector/estado-arquivos.ts";
import { keyU } from "../src/tse/urls.ts";

const T = (o: Partial<TotaisResumo> = {}): TotaisResumo => ({
  ts: 100, st: 10, pst: 10, vvc: 1000, vv: 900, vnom: 900, tv: 1000, comparecimento: 1000, est: 1000, ...o,
});
const C = (pares: [number, number, 0 | 1 | null][]): Map<number, CandResumo> => new Map(pares.map(([sq, vap, eleito]) => [sq, { vap, eleito }]));
const ctx = { em: "2026-10-04T20:00:00.000Z", arquivoId: 1, snapshot: { ref: "s1" }, key: keyU(6257, 1, "br") };

describe("anomalias", () => {
  test("sem anterior não há evento", () => {
    expect(compararU(null, T(), null, C([[1, 5, 0]]), ctx)).toEqual({ eventos: [], alerta: false });
  });

  test("regressão de contagem e de pst", () => {
    const r = compararU(T(), T({ st: 9, tv: 999, pst: 9.5 }), null, null, ctx);
    expect(r.alerta).toBe(true);
    expect(r.eventos.map((e) => [e.tipo, (e.detalhe as { campo?: string }).campo])).toEqual([
      ["regressao_contagem", "st"], ["regressao_contagem", "tv"], ["regressao_pst", undefined],
    ]);
    expect(r.eventos[0]).toMatchObject({ severidade: "warn", eleicao_cd: 6257, cargo_cd: 1, nivel: "br", snapshot_id: { ref: "s1" } });
  });

  test("vap regressivo limitado a 20 eventos mais resumo", () => {
    const ant = C(Array.from({ length: 30 }, (_, i): [number, number, 0] => [i, 100, 0]));
    const novo = C(Array.from({ length: 30 }, (_, i): [number, number, 0] => [i, 50, 0]));
    const r = compararU(T(), T(), ant, novo, ctx);
    const vap = r.eventos.filter((e) => (e.detalhe as { campo?: string }).campo === "vap");
    expect(vap.length).toBe(MAX_EVENTOS_CANDIDATO + 1);
    expect(vap.at(-1)?.detalhe).toEqual({ campo: "vap", resumo: true, n_candidatos: 30 });
  });

  test("candidato novo, sumiu e eleito mudou", () => {
    const r = compararU(T(), T(), C([[1, 5, 0], [2, 5, 0]]), C([[1, 6, 1], [3, 1, 0]]), ctx);
    const tipos = r.eventos.map((e) => e.tipo).sort();
    expect(tipos).toEqual(["candidato_novo", "candidato_sumiu", "eleito_mudou"]);
    expect(r.alerta).toBe(true);
  });

  test("eleito_mudou só em br/uf", () => {
    const mu = { ...ctx, key: keyU(6257, 1, "mu", "sp", "71072") };
    expect(compararU(T(), T(), C([[1, 5, 0]]), C([[1, 6, 1]]), mu).eventos).toEqual([]);
  });
});
