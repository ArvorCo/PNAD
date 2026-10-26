import { describe, expect, test } from "bun:test";
import { escreverHash, lerHash } from "../../src/ui/control/router.ts";
import { baseDe, paradaLonga, quaseCompleta, resolverAlvo, textoRetomada, versaoNova } from "../../src/ui/control/vigilia.ts";
import type { Estado } from "../../src/ui/state/types.ts";

const estado = (st: number, ufs: Record<string, number>, dt = "2026-10-25T20:06:00.000Z"): Estado =>
  ({
    agora: "2026-10-25T20:30:00.000Z",
    turno: 2,
    br: { ts: 1000, st, pst: 0.25, dt_ht: dt, hg: null, lido_em: null, atraso_s: null },
    ufs: Object.entries(ufs).map(([uf, n]) => ({ uf, st: n, ts: 100, pst: 0, munnr: 0, munpt: 0, munf: 0, dt_ht: null })),
    historico: [],
    latencias: { leitura_menos_hg: [], hg_menos_ht: [] },
  }) as Estado;

describe("alvo", () => {
  const agora = new Date("2026-10-25T20:30:00.000Z"); // 17:30 em Brasília
  test("HH:MM é hoje em Brasília", () => {
    expect(resolverAlvo("19:00", agora)).toBe(Date.parse("2026-10-25T19:00:00-03:00"));
    expect(resolverAlvo("7:05", agora)).toBe(Date.parse("2026-10-25T07:05:00-03:00"));
  });
  test("ISO, inválido e ausente", () => {
    expect(resolverAlvo("2026-10-25T19:00:00-03:00", agora)).toBe(Date.parse("2026-10-25T22:00:00Z"));
    expect(resolverAlvo("2026-10-25T19:00:00+00:00", agora)).toBe(Date.parse("2026-10-25T19:00:00Z"));
    expect(resolverAlvo("25:00", agora)).toBeNull();
    expect(resolverAlvo("lixo", agora)).toBeNull();
    expect(resolverAlvo(null, agora)).toBeNull();
  });
  test("hash ida e volta", () => {
    const h = lerHash("#v=espera&alvo=19:00&vigilia=1&auto=0");
    expect(h.alvo).toBe("19:00");
    expect(h.vigilia).toBe(true);
    expect(h.auto).toBe(false);
    expect(escreverHash(h)).toBe("#v=espera&auto=0&alvo=19:00&vigilia=1");
    expect(lerHash("#v=espera").vigilia).toBe(false);
  });
});

describe("versão nova", () => {
  const base = baseDe(estado(1225, { SP: 100, MG: 50 }));
  test("nada mudou", () => expect(versaoNova(base, estado(1225, { SP: 100, MG: 50 }))).toBeNull());
  test("st nacional maior", () => expect(versaoNova(base, estado(1300, { SP: 100, MG: 50 }))).toBe(75));
  test("só uma UF maior não conta: os arquivos de UF se alinham ao nacional depois da parada", () => expect(versaoNova(base, estado(1225, { SP: 100, MG: 80 }))).toBeNull());
  test("só a hora mudou não conta", () => expect(versaoNova(base, estado(1225, { SP: 100, MG: 50 }, "2026-10-25T22:10:00.000Z"))).toBeNull());
  test("texto", () => expect(textoRetomada("19:04", 75)).toBe("divulgação retomada às 19:04: 75 seções novas"));
});

describe("paradaLonga com apuração quase completa", () => {
  const quase = (st: number, ts: number): Estado => {
    const e = estado(st, {});
    e.br.ts = ts;
    e.br.idade_s = 3_600;
    return e;
  };
  test("faltando 2 de 499.248 seções não é parada e não toca a vinheta de novo", () => {
    expect(quaseCompleta(quase(499_246, 499_248))).toBe(true);
    expect(paradaLonga(quase(499_246, 499_248))).toBe(false);
  });
  test("com 1% faltando e uma hora sem versão continua sendo parada", () => {
    expect(quaseCompleta(quase(494_000, 499_248))).toBe(false);
    expect(paradaLonga(quase(494_000, 499_248))).toBe(true);
  });
});
