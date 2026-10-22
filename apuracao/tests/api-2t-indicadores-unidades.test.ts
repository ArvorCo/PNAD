// Unidades dos indicadores do 2º turno: relógio dos arquivos (fuso, carimbo adiantado, versão
// regerada), saneamento e soma das curvas da régua, atraso, grade da evolução e turno.
import { afterAll, beforeAll, describe, expect, test } from "bun:test";
import { eleicoes } from "../src/server/api-config.ts";
import { liderMargem } from "../src/server/indicadores/agregados.ts";
import { CorretorTotalizacao, RelogioArquivo, paDe, paOuNull, pstDe, t0De, turnoDe } from "../src/server/indicadores/base.ts";
import { MAX_CELULAS, MAX_PONTOS, grade } from "../src/server/indicadores/evolucao.ts";
import { agregarCurvas, atrasoMin, comparar, dentroDaJanela, marcosDe, sanearCurva } from "../src/server/indicadores/regua.ts";
import { gradeSoma, inicioGrade } from "../src/server/nacional-serie.ts";
import { T0_1T_MS, T0_2T_MS, corrigirTotalizadoEm } from "../src/turno2/comum.ts";
import type { PontoCurva } from "../src/turno2/referencia.ts";
import type { Semeado } from "./server-helpers.ts";
import { semear2t } from "./server-helpers.ts";

const iso = (ms: number): string => new Date(ms).toISOString();
const min = (m: number): number => T0_2T_MS + m * 60_000;

describe("percentuais", () => {
  test("pst trunca: 99,996% não vira 100% com seção faltando", () => {
    expect(pstDe(499_247, 499_248)).toBe(99.99);
    expect(pstDe(499_248, 499_248)).toBe(100);
    expect(pstDe(0, 0)).toBe(0);
    expect(pstDe(60_000, 103_656)).toBe(57.88);
  });

  test("pa = abstenção / (comparecimento + abstenção)", () => {
    expect(paDe(125_275_835, 33_469_244)).toBe(21.08);
    expect(paDe(0, 0)).toBe(0);
    expect(paOuNull(0, 0)).toBeNull();
  });

  test("líder e margem; empate no topo não tem líder", () => {
    expect(liderMargem(new Map([[13, 60], [22, 40]]), 100)).toEqual({ lider: "13", margem_pp: 20 });
    expect(liderMargem(new Map([[13, 50], [22, 50]]), 100)).toEqual({ lider: null, margem_pp: 0 });
    expect(liderMargem(new Map([[13, 0], [22, 0]]), 0)).toEqual({ lider: null, margem_pp: 0 });
  });

  test("turno e 17:00 pelo código da eleição", () => {
    expect(t0De(6257)).toBe(T0_1T_MS);
    expect(t0De(6259)).toBe(T0_1T_MS);
    expect(t0De(6258)).toBe(T0_2T_MS);
    expect(turnoDe(6260)).toBe(2);
    expect(turnoDe(6257)).toBe(1);
    expect(turnoDe(6282)).toBeNull();
  });
});

describe("relógio dos arquivos", () => {
  // carimbo em hora local rotulada como Brasília: o instante real menos o deslocamento
  const local = (ms: number, fusoMin: number): string => iso(ms + fusoMin * 60_000);

  test("fuso do AC decidido na primeira aparição do carimbo", () => {
    const tot = min(20);
    const c = new CorretorTotalizacao("AC");
    expect(c.instante(local(tot, -120), iso(tot + 20_000), iso(tot + 30_000))).toBe(tot);
    // regerado 40 min depois: a regra simples já não corrige, a decisão guardada sim
    expect(corrigirTotalizadoEm("AC", local(tot, -120), iso(tot + 40 * 60_000))).toBe(local(tot, -120));
    expect(c.instante(local(tot, -120), iso(tot + 40 * 60_000), iso(tot + 41 * 60_000))).toBe(tot);
  });

  test("carimbo depois da geração vale a geração (exterior e PE no 1º turno)", () => {
    const c = new CorretorTotalizacao("ZZ");
    const ger = min(30);
    expect(c.instante(iso(ger + 16 * 3_600_000), iso(ger), iso(ger + 5_000))).toBe(ger);
    expect(new CorretorTotalizacao("PE").instante(iso(ger + 55 * 60_000), iso(ger), iso(ger + 5_000))).toBe(ger);
    expect(new CorretorTotalizacao("SP").instante(null, null, iso(ger))).toBe(ger);
  });

  test("versão regerada com as mesmas contagens mantém o instante (arquivo parado envelhece)", () => {
    const r = new RelogioArquivo("ZZ");
    const amanha = iso(min(16 * 60));
    expect(r.instante("10|900", amanha, iso(min(20)), iso(min(20.5)))).toBe(min(20));
    expect(r.instante("10|900", amanha, iso(min(45)), iso(min(45.5)))).toBe(min(20));
    expect(r.instante("12|950", amanha, iso(min(50)), iso(min(50.5)))).toBe(min(50));
  });

  test("totalização nova nunca volta no tempo", () => {
    const r = new RelogioArquivo("SP");
    expect(r.instante("1", iso(min(30)), iso(min(30.2)), iso(min(30.5)))).toBe(min(30));
    expect(r.instante("2", iso(min(25)), iso(min(31)), iso(min(31.5)))).toBe(min(30));
  });

  test("AC regerado sem o guarda da primeira aparição cai duas horas antes; com ele, não", () => {
    const r = new RelogioArquivo("AC");
    const tot = min(20);
    expect(r.instante("5|1000", local(tot, -120), iso(tot + 10_000), iso(tot + 15_000))).toBe(tot);
    expect(r.instante("5|1000", local(tot, -120), iso(tot + 35 * 60_000), iso(tot + 36 * 60_000))).toBe(tot);
  });
});

const ponto = (m: number, st: number, ts: number, c = 0, a = 0): PontoCurva => [m, Math.round(((100 * st) / ts) * 1000) / 1000, st, ts, c, a, c + a > 0 ? (100 * a) / (c + a) : 0];

describe("régua: saneamento, soma e marcos", () => {
  test("ponto adiantado (versão regerada em hora local) sai; curva fica monotônica", () => {
    const curva = [ponto(28.1, 2226, 2270), ponto(20, 100, 2270), ponto(58.6, 656, 2270), ponto(148.1, 2226, 2270), ponto(234.4, 2270, 2270)];
    const s = sanearCurva(curva);
    expect(s?.map((p) => p[0])).toEqual([20, 58.6, 148.1, 234.4]);
    expect(marcosDe(s ?? [])).toEqual({ p50: 148.1, p90: 148.1, p99: 234.4, p100: 234.4 });
  });

  test("curva num minuto só (exterior com carimbo do dia seguinte) é tratada como ausente", () => {
    expect(sanearCurva([ponto(979.8, 656, 1351), ponto(979.8, 900, 1351), ponto(979.8, 1351, 1351)])).toBeNull();
    expect(sanearCurva([])).toBeNull();
    expect(sanearCurva(undefined)).toBeNull();
  });

  test("soma de curvas no mesmo relógio", () => {
    const a = [ponto(10, 50, 100, 400, 100), ponto(30, 100, 100, 800, 200)];
    const b = [ponto(20, 100, 300, 800, 200)];
    const s = agregarCurvas([a, b]);
    expect(s.map((p) => [p[0], p[2], p[3]])).toEqual([[10, 50, 400], [20, 150, 400], [30, 200, 400]]);
    expect(s[1]?.[1]).toBe(37.5);
    expect(s[2]?.[6]).toBe(20);
  });

  test("atraso: antes da primeira seção, durante e depois do fechamento", () => {
    const c = [ponto(20, 10, 100), ponto(60, 50, 100), ponto(180, 100, 100)];
    expect(atrasoMin(c, 0, 100, 35, null)).toBeNull();
    expect(atrasoMin(c, 30, 100, 50, null)).toBe(10);
    expect(atrasoMin(c, 30, 100, 30, null)).toBe(-10);
    expect(atrasoMin(c, 100, 100, 400, 150)).toBe(-30);
    expect(atrasoMin([], 30, 100, 30, null)).toBeNull();
  });

  test("comparação só com seção totalizada e dentro do dia da eleição", () => {
    const c = [ponto(20, 10, 100), ponto(60, 50, 100), ponto(180, 100, 100)];
    expect(comparar(c, 0, 100, 35, null)).toEqual({ pst_mesmo_relogio: null, atraso_min: null });
    expect(comparar(c, 30, 100, 50, null)).toEqual({ pst_mesmo_relogio: 10, atraso_min: 10 });
    expect(comparar(c, 30, 100, -30_000, null)).toEqual({ pst_mesmo_relogio: null, atraso_min: null });
    expect(dentroDaJanela(-17 * 60)).toBe(true);
    expect(dentroDaJanela(-17 * 60 - 1)).toBe(false);
    expect(dentroDaJanela(31 * 60)).toBe(true);
    expect(dentroDaJanela(31 * 60 + 1)).toBe(false);
  });
});

describe("grade da evolução", () => {
  test("passo mínimo, ponto final no agora e teto de pontos", () => {
    expect(grade(T0_2T_MS, T0_2T_MS - 1, 60).instantes).toEqual([]);
    const g = grade(T0_2T_MS, min(5.5), 60);
    expect(g.instantes.map((t) => (t - T0_2T_MS) / 60_000)).toEqual([0, 1, 2, 3, 4, 5, 5.5]);
    const longa = grade(T0_2T_MS, min(3 * 1440), 30);
    expect(longa.instantes.length).toBeLessThanOrEqual(MAX_PONTOS + 2);
    expect(longa.passo_s % 30).toBe(0);
    // noite de 10 h no nível uf (29 séries): o passo sobe para caber no teto de células
    const uf = grade(T0_2T_MS, min(600), 30, 29);
    expect(uf.passo_s).toBe(90);
    expect(uf.instantes.length * 29).toBeLessThanOrEqual(MAX_CELULAS + 29);
    expect(grade(T0_2T_MS, min(600), 30, 7).passo_s).toBe(30);
  });
});

describe("turno e grade nacional", () => {
  let s: Semeado;
  const env = { turno: process.env.APURACAO_TURNO, eleicoes: process.env.APURACAO_ELEICOES };
  beforeAll(() => {
    s = semear2t();
  });
  afterAll(() => {
    s.fechar();
    s.limpar();
    const volta = (k: string, v: string | undefined): void => {
      if (v === undefined) delete process.env[k];
      else process.env[k] = v;
    };
    volta("APURACAO_TURNO", env.turno);
    volta("APURACAO_ELEICOES", env.eleicoes);
  });

  test("a soma nacional do 2º turno começa às 17:00 de 25/10", () => {
    expect(inicioGrade(6258)).toBe(T0_2T_MS);
    expect(inicioGrade(6257)).toBe(T0_1T_MS);
    const g = gradeSoma(s.db, 6258, 1, iso(min(30)));
    expect(g[0]?.t).toBe(T0_2T_MS);
    expect(g.at(-1)?.st).toBe(78_000);
  });

  test("2º turno pelo banco, pelo coletor configurado e forçado", () => {
    delete process.env.APURACAO_TURNO;
    delete process.env.APURACAO_ELEICOES;
    expect(eleicoes(s.db)).toEqual({ turno: 2, federal: 6258, estadual: 6260 });
    expect(eleicoes(null).turno).toBe(1);
    process.env.APURACAO_ELEICOES = "6258,6260";
    expect(eleicoes(null)).toEqual({ turno: 2, federal: 6258, estadual: 6260 });
    process.env.APURACAO_TURNO = "1";
    expect(eleicoes(s.db).turno).toBe(1);
  });
});
