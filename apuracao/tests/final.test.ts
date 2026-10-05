import { describe, expect, test } from "bun:test";
import { int, pct, pp, tabela, tabelaCampos } from "../scripts/final_2026/markdown.ts";
import {
  blocoDe, blocos, campoDe, classificador, contarPorCampo, eleitosMajoritario, eleitosProporcional, eleitoTse, governador, lacunas, vaoEstadual,
  type Cand, type Disputa,
} from "../scripts/final_2026/puro.ts";

const cl = classificador({
  partidos: { PL: "direita", PT: "esquerda", PSDB: "centro-esquerda", PSD: "centro", "PT/PC do B/PV": "esquerda", XX: "inválido" },
  excecoes: { "99": "centro-direita" },
});

let seq = 0;
const cand = (o: Partial<Cand> & { vap: number }): Cand => ({
  sq: String(++seq), nome: `C${seq}`, partido: "PL", federacao: null, agremiacao: o.partido ?? "PL", pct: 0, eleito: false, st: null, valido: true, campo: "direita", ...o,
});
const disputa = (o: Partial<Disputa>): Disputa => ({ uf: "xx", cargo: 6, tf: false, pst: 99, vagas: 0, vv: 0, cands: [], partidos: [], ...o });

describe("campo", () => {
  test("exceção por candidatura vence partido e federação; sigla em qualquer caixa", () => {
    expect(campoDe(cl, "99", "PSDB")).toBe("centro-direita");
    expect(campoDe(cl, "1", "psdb")).toBe("centro-esquerda");
    expect(campoDe(cl, null, "PCDOB", "PT/PC do B/PV")).toBe("esquerda");
    expect(campoDe(cl, null, "XX")).toBe("indefinido");
  });
  test("blocos somam campos vizinhos", () => {
    expect(blocoDe("centro-direita")).toBe("direita + centro-direita");
    expect(blocoDe("centro-esquerda")).toBe("esquerda + centro-esquerda");
    const r = contarPorCampo([{ campo: "direita" }, { campo: "centro-direita" }, { campo: "centro" }, { campo: "esquerda" }]);
    expect(blocos(r)).toEqual({ "direita + centro-direita": 2, "esquerda + centro-esquerda": 1, centro: 1, indefinido: 0 });
  });
});

describe("marca do TSE", () => {
  test("eleito = 1 com situação 2º turno não é eleito", () => {
    expect(eleitoTse(cand({ vap: 1, eleito: true, st: "2º turno" }))).toBe(false);
    expect(eleitoTse(cand({ vap: 1, eleito: true, st: "Eleito por média" }))).toBe(true);
    expect(eleitoTse(cand({ vap: 1, eleito: true, st: null }))).toBe(true);
  });
  test("governador: arquivo final com dois em 2º turno", () => {
    const a = cand({ vap: 49, pct: 49.7, eleito: true, st: "2º turno" });
    const b = cand({ vap: 32, pct: 32, eleito: true, st: "2º turno" });
    const g = governador(disputa({ cargo: 3, tf: true, cands: [a, b, cand({ vap: 10, pct: 10, st: "Não eleito" })] }));
    expect(g.fonte).toBe("tse");
    expect(g.decisao).toBe("segundo_turno");
    expect(g.candidatos.map((c) => c.sq)).toEqual([a.sq, b.sq]);
  });
  test("governador provisório: mais da metade elege, senão os dois primeiros", () => {
    expect(governador(disputa({ cargo: 3, cands: [cand({ vap: 51, pct: 50.1 }), cand({ vap: 49, pct: 49.9 })] })).decisao).toBe("eleito");
    const g = governador(disputa({ cargo: 3, cands: [cand({ vap: 50, pct: 50 }), cand({ vap: 30, pct: 30 }), cand({ vap: 20, pct: 20 })] }));
    expect(g.decisao).toBe("segundo_turno");
    expect(g.terceiro?.vap).toBe(20);
  });
  test("senado provisório pega os dois válidos mais votados e avisa voto sub judice", () => {
    const sj = cand({ vap: 90, valido: false, nome: "SJ" });
    const e = eleitosMajoritario(disputa({ cargo: 5, cands: [sj, cand({ vap: 80 }), cand({ vap: 70 }), cand({ vap: 60 })] }), 2);
    expect(e.fonte).toBe("provisorio");
    expect(e.eleitos.map((c) => c.vap)).toEqual([80, 70]);
    expect(e.alertas[0]).toContain("SJ");
  });
});

describe("proporcional", () => {
  // Acre 2026, deputado federal: 8 vagas, válidos 462.485; a regra reproduz QP 6 + 2 sobras do TSE.
  const ag = (id: string, tvtn: number, tvtl: number, cands: number[]): { p: Disputa["partidos"][number]; c: Cand[] } => ({
    p: { agremiacao: id, sigla: id, tvtn, tvtl },
    c: cands.map((vap) => cand({ vap, agremiacao: id, partido: id })),
  });
  const dados = [
    ag("UP", 169443, 4467, [39587, 33203, 33155, 23810, 20902, 13142]),
    ag("MDB", 83091, 768, [26263, 22775, 20499]),
    ag("REP", 67366, 1155, [24854, 18386]),
    ag("PL", 57025, 2214, [13732, 13440]),
    ag("FE", 44543, 1967, [15800, 9000]),
    ag("PSDB", 21150, 469, [9000]),
  ];
  const d = disputa({ vagas: 8, vv: 462485, partidos: dados.map((x) => x.p), cands: dados.flatMap((x) => x.c) });
  test("votos da agremiação = nominais + legenda, sem os anulados sub judice", () => {
    const e = eleitosProporcional(d);
    expect(e.fonte).toBe("provisorio");
    expect(e.qe).toBe(57811);
    const por = (sg: string): number => e.eleitos.filter((c) => c.partido === sg).length;
    expect([por("UP"), por("MDB"), por("REP"), por("PL"), por("FE"), por("PSDB")]).toEqual([4, 1, 1, 1, 1, 0]);
    expect(e.alertas).toEqual([]);
  });
  test("com tf = 1 usa a marca do TSE e acusa contagem diferente das vagas", () => {
    const cs = d.cands.map((c, i) => ({ ...c, eleito: i < 7, st: i < 7 ? "Eleito por QP" : "Suplente" }));
    const e = eleitosProporcional({ ...d, tf: true, cands: cs });
    expect(e.fonte).toBe("tse");
    expect(e.eleitos).toHaveLength(7);
    expect(e.alertas[0]).toContain("7 eleitos para 8 vagas");
  });
});

describe("linha do tempo e vão", () => {
  test("lacunas acima do limiar, da maior para a menor", () => {
    const l = lacunas(["2026-10-04T21:48:59Z", "2026-10-04T21:50:00Z", "2026-10-04T22:14:08Z", "2026-10-04T21:48:59Z"], 10);
    expect(l).toEqual([{ de: "2026-10-04T21:50:00Z", ate: "2026-10-04T22:14:08Z", minutos: 24.1 }]);
  });
  test("vão estadual compara com o finalista do mesmo bloco e ignora o centro", () => {
    const flavio = cand({ vap: 1, nome: "FLAVIO", campo: "direita" });
    const lula = cand({ vap: 1, nome: "LULA", partido: "PT", campo: "esquerda" });
    const tarc = cand({ vap: 1, nome: "TARCISIO", pct: 62.65, campo: "direita" });
    const centro = cand({ vap: 1, nome: "PAES", pct: 42, campo: "centro" });
    const govs = [{ uf: "sp", fonte: "provisorio" as const, pst: 99, decisao: "segundo_turno" as const, candidatos: [tarc, centro], terceiro: null }];
    const v = vaoEstadual(govs, [flavio, lula], new Map([["sp", [{ ...flavio, pct: 51.93 }, { ...lula, pct: 40 }]]]));
    expect(v).toHaveLength(1);
    expect(v[0]?.vao_pp).toBe(10.72);
    expect(v[0]?.presidenciavel).toBe("FLAVIO");
  });
});

describe("markdown", () => {
  test("números em pt-BR, pontos para diferença e nenhum travessão", () => {
    expect(int(1234567)).toBe("1.234.567");
    expect(pct(47.0625)).toBe("47,06%");
    expect(pp(1.925)).toBe("1,93 pontos");
    const t = tabelaCampos([{ nome: "Cadeiras", dados: { esquerda: 2, "centro-esquerda": 0, centro: 1, "centro-direita": 0, direita: 1, indefinido: 0 } }], true);
    expect(t).toContain("| Esquerda | 2 | 50,0% |");
    expect(t).not.toContain("Centro-esquerda");
    expect(t).not.toContain("—");
    expect(tabela(["UF", "Nome", "Votos"], [["SP", "A", "1.000"]])).toContain("| --- | --- | ---: |");
  });
});
