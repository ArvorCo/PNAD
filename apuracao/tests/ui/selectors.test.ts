import { describe, expect, test } from "bun:test";
import {
  agregarPorCampo,
  apuracaoComecou,
  colapsarOutros,
  composicaoVotos,
  disputa,
  ehOutros,
  estadoUfsOrdenado,
  ranking,
  rotuloOutros,
  ufsPorEleitorado,
} from "../../src/ui/state/selectors.ts";
import { atribuir, criarStore, diffNumerico } from "../../src/ui/state/store.ts";
import type { Campo, Estado, State } from "../../src/ui/state/types.ts";
import { abrDe } from "../../src/ui/state/types.ts";

const c = (n: string, vap: number, pvapn: number, campo: Campo = "indefinido") => ({ n, vap, pvapn, campo, sqcand: `s${n}` });

describe("ranking e disputa", () => {
  test("ordena por votos e desempata pelo número", () => {
    expect(ranking([c("22", 10, 10), c("13", 30, 30), c("14", 10, 10)]).map(x => x.n)).toEqual(["13", "14", "22"]);
  });

  test("líder, segundo e margem em pontos", () => {
    const d = disputa([c("22", 400, 40), c("13", 500, 50), c("30", 100, 10)]);
    expect(d.lider?.n).toBe("13");
    expect(d.segundo?.n).toBe("22");
    expect(d.margem).toBeCloseTo(10);
    expect(d.margemVotos).toBe(100);
    expect(d.empate).toBe(false);
  });

  test("empate exato não tem líder; sem voto também não", () => {
    expect(disputa([c("22", 5, 50), c("13", 5, 50)]).lider).toBeNull();
    expect(disputa([c("22", 5, 50), c("13", 5, 50)]).empate).toBe(true);
    expect(disputa([c("22", 0, 0), c("13", 0, 0)]).lider).toBeNull();
    expect(disputa([]).lider).toBeNull();
  });
});

describe("agregações", () => {
  test("soma por campo na ordem da esquerda para a direita", () => {
    const f = agregarPorCampo([c("1", 30, 0, "direita"), c("2", 50, 0, "esquerda"), c("3", 20, 0, "direita"), c("4", 0, 0, "centro")], x => x.campo, x => x.vap);
    expect(f.map(x => x.campo)).toEqual(["esquerda", "direita"]);
    expect(f[1]?.votos).toBe(50);
    expect(f[0]?.pct).toBeCloseTo(50);
  });

  test("válidos, brancos e nulos sobre o total", () => {
    const v = { tv: 1000, vv: 900, vvc: 900, vnom: 900, van: 0, vb: 40, vn: 60, pvb: 4, pvn: 6, pvan: 0 };
    expect(composicaoVotos(v)).toEqual({ validos: 90, brancos: 4, nulos: 6, total: 1000 });
    expect(composicaoVotos({ ...v, tv: 0 }).validos).toBe(0);
  });

  test("outros N junta a cauda", () => {
    const lista = [c("1", 50, 50), c("2", 30, 30), c("3", 10, 10), c("4", 6, 6), c("5", 4, 4)];
    const r = colapsarOutros(lista, 3);
    expect(r).toHaveLength(3);
    const ultimo = r[2];
    if (!ultimo || !ehOutros(ultimo)) throw new Error("esperava linha de outros");
    expect(ultimo.quantidade).toBe(3);
    expect(ultimo.vap).toBe(20);
    expect(rotuloOutros(ultimo)).toBe("outros 3");
    expect(colapsarOutros(lista, 5)).toHaveLength(5);
  });

  test("UFs por eleitorado", () => {
    const ufs = [
      { uf: "AC", nome: "Acre", cdi: "12", te: 600 },
      { uf: "SP", nome: "São Paulo", cdi: "35", te: 34000 },
      { uf: "MG", nome: "Minas Gerais", cdi: "31", te: 16000 },
    ];
    expect(ufsPorEleitorado(ufs).map(u => u.uf)).toEqual(["SP", "MG", "AC"]);
    const estado = {
      ufs: [
        { uf: "ac", pst: 1, st: 1, ts: 2, munnr: 0, munpt: 1, munf: 0, dt_ht: null },
        { uf: "sp", pst: 2, st: 1, ts: 2, munnr: 0, munpt: 1, munf: 0, dt_ht: null },
      ],
      br: { st: 0 },
    } as unknown as Estado;
    expect(estadoUfsOrdenado(estado, ufs).map(u => u.uf)).toEqual(["sp", "ac"]);
    expect(apuracaoComecou(estado)).toBe(false);
    expect(apuracaoComecou(null)).toBe(false);
  });
});

describe("abrangência no formato do TSE", () => {
  test("br, uf, município e zona", () => {
    expect(abrDe()).toBe("br");
    expect(abrDe("SP")).toBe("sp");
    expect(abrDe("SP", "71072")).toBe("sp71072");
    expect(abrDe("SP", "71072", "1")).toBe("sp71072-z0001");
  });
});

describe("store", () => {
  test("diff casa arrays pelo id e só traz folhas numéricas", () => {
    const de = { v: { tv: 10 }, cand: [{ sqcand: "a", vap: 1 }, { sqcand: "b", vap: 2 }], nome: "x" };
    const para = { v: { tv: 12 }, cand: [{ sqcand: "b", vap: 5 }, { sqcand: "a", vap: 1 }], nome: "y" };
    expect(diffNumerico(de, para, "r")).toEqual([
      { path: "r.v.tv", de: 10, para: 12 },
      { path: "r.cand[sqcand=b].vap", de: 2, para: 5 },
    ]);
  });

  test("atribuir preserva ramos intocados", () => {
    const raiz = { a: { x: 1 }, b: { y: 2 } };
    const nova = atribuir(raiz, ["a", "x"], 3);
    expect(nova.a.x).toBe(3);
    expect(nova.b).toBe(raiz.b);
    expect(raiz.a.x).toBe(1);
  });

  test("patch notifica uma vez por microtarefa com o diff acumulado", async () => {
    const s = criarStore({ resultados: {}, ui: { v: "pres" } } as unknown as State);
    const chamadas: number[] = [];
    s.subscribe((_st, diff) => chamadas.push(diff.length));
    s.patch("resultados.k", { v: { tv: 1 } });
    s.patch("resultados.k", { v: { tv: 2 } });
    s.ui({ v: "gov" });
    await Promise.resolve();
    expect(chamadas).toEqual([1]);
    expect(s.get().ui.v).toBe("gov");
    expect((s.get().resultados as Record<string, { v: { tv: number } }>).k?.v.tv).toBe(2);
  });
});
