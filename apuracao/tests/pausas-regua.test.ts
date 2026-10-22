// Alertas contra a régua do 1º turno: atraso por patamar e abstenção atípica (município e UF).
import { describe, expect, test } from "bun:test";
import { AlertasRegua, REGUA_PADRAO } from "../src/collector/regua.ts";
import type { MunAb } from "../src/collector/regua.ts";
import { abrirEscrita } from "../src/db/abrir.ts";
import { Escritor } from "../src/db/escrita.ts";
import type { EventoNovo } from "../src/db/escrita.ts";
import type { PontoCurva, Referencia1T } from "../src/turno2/referencia.ts";

const T0 = Date.parse("2026-10-25T20:00:00.000Z");
const m = (min: number): number => T0 + min * 60_000;
const ponto = (min: number, pst: number): PontoCurva => [min, pst, pst * 10, 1000, 0, 0, 0];
const mun = (nm: string, te: number, comparecimento: number, abstencao: number, pa: number) => ({
  nm, te, ts: 100, st: 100, comparecimento, abstencao, pa, fechou_min: 90, apareceu_min: 30,
});

const REF: Referencia1T = {
  meta: { gerado_em: "2026-10-22T00:00:00.000Z", turno: 1, eleicoes: { presidente: 6257, governador: 6259 }, regioes: {} },
  curvas: { br: [], uf: { BA: [ponto(20, 1), ponto(60, 50), ponto(120, 100)] } },
  marcos: { br: { p50: null, p90: null, p99: null, p100: null }, uf: {} },
  municipios: { BA: { "38490": mun("SALVADOR", 30_000, 22_500, 7_500, 25), "38491": mun("PEQUENA", 10_000, 8_000, 2_000, 20), "38492": mun("ABERTA", 50_000, 40_000, 10_000, 20) } },
  abstencao_uf: {},
  secoes_lag: { uf: {}, municipio: {} },
  governador_1t: {},
};

const regua = (): AlertasRegua => new AlertasRegua(REF, { ...REGUA_PADRAO, ele: 6258, t0Ms: T0 });
const tipos = (l: readonly EventoNovo[]): [string, unknown][] => l.map((e) => [e.tipo, (e.detalhe as { patamar_min?: number }).patamar_min]);

describe("UF atrasada contra a curva do 1º turno", () => {
  test("um evento por patamar novo, pulando o patamar já ultrapassado", () => {
    const r = regua();
    const ba = (pst: number) => [{ uf: "ba", pst, st: pst * 10, ts: 1000 }];
    expect(r.avaliarAtraso(m(75), ba(50))).toEqual([]); // 15 min atrás
    const e40 = r.avaliarAtraso(m(100), ba(50));
    expect(tipos(e40)).toEqual([["uf_atrasada_1t", 40]]);
    expect(e40[0]).toMatchObject({ severidade: "warn", nivel: "uf", uf: "ba", eleicao_cd: 6258 });
    expect(e40[0]?.detalhe).toMatchObject({ atraso_min: 40, min: 100, pst: 50, pst_1t_mesmo_relogio: 50, rotulo: "pede explicação, não indica irregularidade" });
    expect(r.avaliarAtraso(m(105), ba(50))).toEqual([]);
    expect(tipos(r.avaliarAtraso(m(121), ba(50)))).toEqual([["uf_atrasada_1t", 60]]);
  });

  test("interpolação da curva: pst 25,5 foi alcançado no minuto 40 do 1º turno", () => {
    expect(tipos(regua().avaliarAtraso(m(61), [{ uf: "ba", pst: 25.5, st: 255, ts: 1000 }]))).toEqual([["uf_atrasada_1t", 20]]);
  });

  test("UF fechada, antes das 17h ou sem curva: nada", () => {
    const r = regua();
    expect(r.avaliarAtraso(m(300), [{ uf: "ba", pst: 100, st: 1000, ts: 1000 }])).toEqual([]);
    expect(r.avaliarAtraso(m(-10), [{ uf: "ba", pst: 0, st: 0, ts: 1000 }])).toEqual([]);
    expect(r.avaliarAtraso(m(300), [{ uf: "sp", pst: 1, st: 1, ts: 1000 }])).toEqual([]);
    expect(new AlertasRegua(null, { ...REGUA_PADRAO, ele: 6258 }).avaliarAtraso(m(300), [{ uf: "ba", pst: 1, st: 1, ts: 1000 }])).toEqual([]);
  });
});

describe("abstenção atípica", () => {
  const muns = (): MunAb[] => [
    { uf: "ba", mun: "38490", ts: 100, st: 100, te: 30_000, c: 20_000, a: 10_000 },
    { uf: "ba", mun: "38491", ts: 100, st: 100, te: 10_000, c: 5_000, a: 5_000 },
    { uf: "ba", mun: "38492", ts: 100, st: 40, te: 50_000, c: 15_000, a: 5_000 },
  ];

  test("município grande fechado com 5 pp ou mais; UF com 30% do eleitorado fechado e 2 pp ou mais", () => {
    const r = regua();
    const ev = r.avaliarAbstencao(m(120), muns());
    expect(ev.map((e) => [e.tipo, e.municipio_cd ?? null])).toEqual([
      ["abstencao_atipica_mun", "38490"],
      ["abstencao_atipica_uf", null],
    ]);
    expect(ev[0]?.detalhe).toMatchObject({ nm: "SALVADOR", te: 30_000, pa_2t: 33.33, pa_1t: 25, delta_pp: 8.33 });
    // UF: 2º turno (10.000 + 5.000) / 40.000 = 37,5%; 1º turno nos mesmos (7.500 + 2.000) / 40.000 = 23,75%
    expect(ev[1]?.detalhe).toMatchObject({ sentido: "subiu", pa_2t: 37.5, pa_1t_mesmos: 23.75, delta_pp: 13.75, pct_te_fechado: 44.44, n_mun_fechados: 2 });
    expect(r.avaliarAbstencao(m(130), muns())).toEqual([]);
  });

  test("menos de 30% do eleitorado fechado: sem alerta de UF", () => {
    const l = muns().map((x) => (x.mun === "38492" ? { ...x, te: 200_000 } : x));
    expect(regua().avaliarAbstencao(m(120), l).map((e) => e.tipo)).toEqual(["abstencao_atipica_mun"]);
  });

  test("estado volta da tabela evento (sem repetir depois de reinício)", () => {
    const db = abrirEscrita(":memory:");
    const w = new Escritor(db);
    const r1 = regua();
    const evs = [...r1.avaliarAtraso(m(100), [{ uf: "ba", pst: 50, st: 500, ts: 1000 }]), ...r1.avaliarAbstencao(m(120), muns())];
    w.gravarLote(evs.map((row) => ({ k: "evento", row })));
    const r2 = regua();
    r2.carregar(db);
    expect(r2.avaliarAtraso(m(105), [{ uf: "ba", pst: 50, st: 500, ts: 1000 }])).toEqual([]);
    expect(r2.avaliarAbstencao(m(130), muns())).toEqual([]);
    expect(tipos(r2.avaliarAtraso(m(121), [{ uf: "ba", pst: 50, st: 500, ts: 1000 }]))).toEqual([["uf_atrasada_1t", 60]]);
  });
});
