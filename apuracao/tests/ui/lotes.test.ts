import { describe, expect, test } from "bun:test";
import { agrupar, barras, blocoDe, extremos, indicesDeHora, liderDoBloco, OUTROS, participacao, pilha } from "../../src/ui/components/lotes.ts";
import { criarMock } from "../../src/ui/data/mock.ts";
import type { Lote } from "../../src/ui/state/types.ts";
import type { InfoCand } from "../../src/ui/views/acumulado.ts";
import { fichaDoBloco, latenciaS, linhaDoBloco, moverSelecao, TECLAS_ANTERIOR, TECLAS_PROXIMA } from "../../src/ui/views/lotes.ts";

const T = Date.parse("2026-10-04T20:00:00.000Z");
const SEG = 1000;

function lote(seg: number, d: Record<string, number>, extra: Partial<Lote> = {}): Lote {
  const cand: Lote["cand"] = {};
  for (const [k, v] of Object.entries(d)) cand[k] = { vap: 0, d_vap: v };
  const dvv = Object.values(d).reduce((a, b) => a + b, 0);
  return {
    snapshot_id: seg,
    at: new Date(T + seg * SEG).toISOString(),
    capturado_em: new Date(T + seg * SEG + 14 * SEG).toISOString(),
    st: 0,
    d_st: 10,
    pst: 1,
    vv: 0,
    d_vv: dvv,
    tv: 0,
    d_tv: dvv,
    cand,
    ...extra,
  };
}

const INFO: InfoCand[] = [
  { sqcand: "l", nome: "Lula", cor: "#b02f21" },
  { sqcand: "f", nome: "Flavio Bolsonaro", cor: "#1457aa" },
  { sqcand: "z", nome: "Zema", cor: "#0f7f5f" },
];
const ORDEM = INFO.map(c => c.sqcand);

describe("pilhas por lote", () => {
  test("positivos de baixo para cima na ordem do ranking e resto como outros", () => {
    const b = blocoDe(lote(0, { l: 120_000, f: 100_000, z: 0 }, { d_vv: 249_000 }));
    expect(pilha(b, ORDEM)).toEqual([
      { id: "l", y0: 0, y1: 120_000, negativo: false },
      { id: "f", y0: 120_000, y1: 220_000, negativo: false },
      { id: OUTROS, y0: 220_000, y1: 249_000, negativo: false },
    ]);
    expect(participacao(b, "l")).toBeCloseTo(48.19, 2);
    expect(liderDoBloco(b, ORDEM)).toBe("l");
  });

  test("regressão desce do zero e entra nos extremos", () => {
    const b = blocoDe(lote(0, { l: -300, f: 500, z: -200 }));
    const p = pilha(b, ORDEM);
    expect(p).toEqual([
      { id: "l", y0: -300, y1: 0, negativo: true },
      { id: "f", y0: 0, y1: 500, negativo: false },
      { id: "z", y0: -500, y1: -300, negativo: true },
    ]);
    expect(extremos([p])).toEqual({ min: -500, max: 500 });
    expect(liderDoBloco(blocoDe(lote(0, { l: -1 })), ORDEM)).toBeNull();
  });
});

describe("agrupamento em janelas de 5 minutos", () => {
  test("até o limite, uma barra por lote", () => {
    const ls = [lote(0, { l: 1 }), lote(30, { l: 2 })];
    const g = agrupar(ls, 300);
    expect(g.agrupado).toBe(false);
    expect(g.blocos.map(b => b.n)).toEqual([1, 1]);
  });

  test("acima do limite, soma lotes vizinhos da mesma janela", () => {
    const ls = Array.from({ length: 12 }, (_, i) => lote(i * 60, { l: 10, f: 5 }));
    const g = agrupar(ls, 5, 5 * 60 * SEG);
    expect(g.agrupado).toBe(true);
    expect(g.blocos.map(b => b.n)).toEqual([5, 5, 2]);
    const b0 = g.blocos[0];
    expect(b0?.d_cand).toEqual({ l: 50, f: 25 });
    expect(b0?.d_st).toBe(50);
    expect(b0?.d_vv).toBe(75);
    expect(b0?.ini).toBe(T);
    expect(b0?.fim).toBe(T + 4 * 60 * SEG);
    expect(b0?.ultimo.snapshot_id).toBe(240);
    const total = g.blocos.reduce((a, b) => a + (b.d_cand.l ?? 0), 0);
    expect(total).toBe(120);
  });
});

describe("geometria e eixos", () => {
  test("barras de largura igual com 2 px de intervalo", () => {
    const g = barras(4, 100, 500, 2, 1000);
    expect(g.w).toBe((400 - 6) / 4);
    expect(g.x).toEqual([100, 100 + g.w + 2, 100 + 2 * (g.w + 2), 100 + 3 * (g.w + 2)]);
    expect(barras(2, 0, 1000).w).toBe(48);
    expect(barras(0, 0, 10)).toEqual({ x: [], w: 0 });
  });

  test("rótulos de hora sem colisão", () => {
    expect(indicesDeHora(10, 120)).toEqual([0, 1, 2, 3, 4, 5, 6, 7, 8, 9]);
    // O último lote sempre recebe rótulo; o anterior (297) sai porque ficaria colado nele.
    expect(indicesDeHora(300, 3.4)).toEqual([...Array.from({ length: 9 }, (_, i) => i * 33), 299]);
    expect(indicesDeHora(195, 5).at(-1)).toBe(194);
    expect(indicesDeHora(0, 10)).toEqual([]);
  });
});

describe("ficha e teclas", () => {
  test("linha por candidatura e latência do arquivo", () => {
    const b = blocoDe(lote(0, { l: 120_000, f: 100_000, z: 29_000 }));
    expect(linhaDoBloco(b, INFO[0] as InfoCand)).toEqual({ cor: "#b02f21", rotulo: "Lula", valor: "+120 mil", extra: "48,2% do lote" });
    expect(latenciaS(b)).toBe(14);
    const f = fichaDoBloco(b, INFO);
    expect(f.fatos).toEqual([
      { rotulo: "seções", valor: "+10" },
      { rotulo: "votos válidos", valor: "+249.000" },
    ]);
    expect(f.notas?.[0]).toBe("arquivo gerado às 17:00:00, lido 14 s depois");
    expect(f.linhas?.map(l => l.rotulo)).toEqual(["Lula", "Flavio Bolsonaro", "Zema"]);
  });

  test("seleção anda e para nas pontas", () => {
    expect(moverSelecao(null, -1, 5)).toBe(4);
    expect(moverSelecao(4, 1, 5)).toBe(4);
    expect(moverSelecao(4, -1, 5)).toBe(3);
    expect(moverSelecao(0, -1, 5)).toBe(0);
    expect(moverSelecao(2, 1, 0)).toBeNull();
    expect(TECLAS_ANTERIOR.has(",")).toBe(true);
    expect(TECLAS_PROXIMA.has(".")).toBe(true);
  });
});

describe("lotes do mock", () => {
  test("deltas fecham com os acumulados e a ordem segue os votos", async () => {
    let real = 0;
    const m = criarMock({ speed: 1, agoraReal: () => real });
    real = 2 * 3_600_000;
    const r = await m.lotes({ ele: 6257, cargo: 1, abr: "br" });
    expect(r.lotes.length).toBeGreaterThan(40);
    const ult = r.lotes[r.lotes.length - 1];
    for (const c of r.candidatos) {
      const soma = r.lotes.reduce((a, l) => a + (l.cand[c.sqcand]?.d_vap ?? 0), 0);
      expect(soma).toBe(ult?.cand[c.sqcand]?.vap ?? -1);
    }
    expect(r.lotes.reduce((a, l) => a + l.d_st, 0)).toBe(ult?.st ?? -1);
    const vaps = r.candidatos.map(c => ult?.cand[c.sqcand]?.vap ?? 0);
    expect(vaps).toEqual([...vaps].sort((a, b) => b - a));
    const res = await m.resultado({ ele: 6257, cargo: 1, abr: "br" });
    expect(ult?.vv ?? 0).toBeLessThanOrEqual(res.v.vv);
  });
});
