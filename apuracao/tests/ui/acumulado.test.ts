import { describe, expect, test } from "bun:test";
import { ganhoDesde, lotesDesde, maisProximo, tetoRedondo, ticksVotos, votosEixo } from "../../src/ui/components/acumulado.ts";
import { posicionarFicha } from "../../src/ui/components/tooltip.ts";
import { CORES_PADRAO } from "../../src/ui/data/cores.ts";
import type { Lote, Lotes } from "../../src/ui/state/types.ts";
import { comSinalInteiro, infoDosLotes } from "../../src/ui/views/acumulado.ts";

const T = Date.parse("2026-10-04T20:00:00.000Z");
const MIN = 60_000;

function lote(min: number, lula: number, flavio: number): Lote {
  return {
    snapshot_id: min,
    at: new Date(T + min * MIN).toISOString(),
    capturado_em: new Date(T + min * MIN + 12_000).toISOString(),
    st: min * 100,
    d_st: 100,
    pst: min,
    vv: lula + flavio,
    d_vv: 0,
    tv: lula + flavio,
    d_tv: 0,
    cand: { l: { vap: lula, d_vap: 0 }, f: { vap: flavio, d_vap: 0 } },
  };
}

describe("eixo compacto em votos", () => {
  test("rótulos pt-BR: mil e mi, casas só quando precisa", () => {
    expect(votosEixo(0)).toBe("0");
    expect(votosEixo(800)).toBe("800");
    expect(votosEixo(500_000)).toBe("500 mil");
    expect(votosEixo(2_500)).toBe("2,5 mil");
    expect(votosEixo(10_000_000)).toBe("10 mi");
    expect(votosEixo(2_500_000)).toBe("2,5 mi");
    expect(votosEixo(1_250_000)).toBe("1,25 mi");
    expect(votosEixo(-500_000)).toBe("−500 mil");
  });

  test("ticks redondos cobrem o máximo e começam no zero", () => {
    const t = ticksVotos(0, tetoRedondo(23_400_000));
    expect(t[0]).toEqual({ v: 0, texto: "0" });
    expect(t.map(x => x.texto)).toContain("10 mi");
    expect(t[t.length - 1]?.v ?? 0).toBeGreaterThanOrEqual(23_400_000);
    expect(tetoRedondo(0)).toBe(1);
    expect(tetoRedondo(47)).toBe(50);
    expect(tetoRedondo(100)).toBe(100);
  });
});

describe("leitura e janelas", () => {
  test("lote mais próximo por busca binária, empates para a esquerda", () => {
    const xs = [0, 10, 20, 40];
    expect(maisProximo(xs, -5)).toBe(0);
    expect(maisProximo(xs, 14)).toBe(1);
    expect(maisProximo(xs, 15)).toBe(1);
    expect(maisProximo(xs, 31)).toBe(3);
    expect(maisProximo(xs, 99)).toBe(3);
    expect(maisProximo([], 3)).toBe(-1);
    expect(maisProximo([7], 3)).toBe(0);
  });

  test("ganho nos últimos 10 minutos usa o último lote antes da janela", () => {
    const ls = [lote(0, 100, 90), lote(5, 200, 150), lote(12, 260, 300), lote(17, 400, 310)];
    const agora = T + 17 * MIN;
    expect(ganhoDesde(ls, "l", agora - 10 * MIN)).toBe(400 - 200);
    expect(ganhoDesde(ls, "f", agora - 10 * MIN)).toBe(310 - 150);
    expect(ganhoDesde(ls, "l", T - MIN)).toBe(400);
    expect(ganhoDesde([], "l", T)).toBe(0);
    expect(lotesDesde(ls, T + 5 * MIN).map(l => l.snapshot_id)).toEqual([5, 12, 17]);
  });

  test("candidaturas na ordem do ranking com a cor fixa por número", () => {
    const l: Lotes = {
      abr: "br",
      candidatos: [
        { sqcand: "f", n: "22", nmu: "FLAVIO BOLSONARO", sg: "PL" },
        { sqcand: "l", n: "13", nmu: "LULA", sg: "PT" },
        { sqcand: "z", n: "30", nmu: "ZEMA", sg: "NOVO" },
      ],
      lotes: [],
    };
    const info = infoDosLotes(l, CORES_PADRAO);
    expect(info.map(c => c.nome)).toEqual(["Flavio Bolsonaro", "Lula", "Zema"]);
    expect(info[0]?.cor).toBe("#1457aa");
    expect(info[1]?.cor).toBe("#b02f21");
    expect(info[2]?.cor).toBe(CORES_PADRAO.sequencia[2]);
    expect(comSinalInteiro(1234)).toBe("+1.234");
    expect(comSinalInteiro(-56)).toBe("−56");
    expect(comSinalInteiro(0)).toBe("0");
  });
});

describe("ficha dentro do telão", () => {
  const caixa = { w: 1920, h: 1080 };
  const card = { w: 500, h: 300 };

  test("à direita da âncora quando cabe", () => {
    expect(posicionarFicha(400, 500, card, caixa)).toEqual({ x: 428, y: 350, lado: "dir" });
  });

  test("vira à esquerda perto da borda direita e nunca sai da caixa", () => {
    const p = posicionarFicha(1700, 500, card, caixa);
    expect(p.lado).toBe("esq");
    expect(p.x).toBe(1700 - 28 - 500);
    const q = posicionarFicha(1910, 1070, card, caixa);
    expect(q.x + card.w).toBeLessThanOrEqual(caixa.w - 16);
    expect(q.y + card.h).toBeLessThanOrEqual(caixa.h - 16);
    const r = posicionarFicha(5, 5, card, caixa);
    expect(r.x).toBeGreaterThanOrEqual(16);
    expect(r.y).toBe(16);
  });

  test("cartão maior que a caixa fica preso na margem esquerda", () => {
    const p = posicionarFicha(100, 100, { w: 3000, h: 200 }, caixa);
    expect(p.x).toBe(16);
  });
});
