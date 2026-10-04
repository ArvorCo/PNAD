import { describe, expect, test } from "bun:test";
import {
  COR_OUTROS,
  coresEstaduais,
  coresPresidente,
  empateNoTopo,
  lideres,
  linhasRanking,
  MISTURA_MESMO_CAMPO,
  votoValido,
} from "../../src/ui/components/ranking.ts";
import { CORES_CAMPO_PADRAO, CORES_PADRAO, mix, PAPEL } from "../../src/ui/data/cores.ts";
import type { Campo, Candidato } from "../../src/ui/state/types.ts";
import { textoDiferenca, votosPorExtenso } from "../../src/ui/views/executivo.ts";
import { corDuelo, parDoDuelo } from "../../src/ui/views/presidente.ts";

const cand = (n: string, vap: number, total: number, campo: Campo = "indefinido", extra: Partial<Candidato> = {}): Candidato => ({
  sqcand: `s${n}`,
  n,
  nm: `CANDIDATO ${n}`,
  nmu: `CANDIDATO ${n}`,
  sg: "P",
  campo,
  e: false,
  st: "",
  dvt: "Válido",
  vap,
  pvapn: total > 0 ? (100 * vap) / total : 0,
  vs: [],
  ...extra,
});

const lista = (votos: Record<string, number>, campo: Campo = "indefinido"): Candidato[] => {
  const total = Object.values(votos).reduce((a, b) => a + b, 0);
  return Object.entries(votos).map(([n, v]) => cand(n, v, total, campo));
};

describe("linhasRanking", () => {
  test("ordena por votos e mantém zerados pela ordem do número", () => {
    const c = lista({ "30": 0, "13": 500, "22": 700, "16": 0, "55": 100 });
    const l = linhasRanking(c, 7, new Map());
    expect(l.map(x => x.numero)).toEqual(["22", "13", "55", "16", "30"]);
    expect(l.filter(x => x.semVoto).map(x => x.numero)).toEqual(["16", "30"]);
  });

  test("junta o excedente em outros N com votos e percentuais somados", () => {
    const c = lista({ "1": 60, "2": 50, "3": 40, "4": 30, "5": 20, "6": 10, "7": 5, "8": 3, "9": 2 });
    const l = linhasRanking(c, 7, new Map());
    expect(l).toHaveLength(7);
    const o = l[6];
    expect(o?.outros).toBe(true);
    expect(o?.nome).toBe("outros 3");
    expect(o?.vap).toBe(10);
    expect(o?.pvapn).toBeCloseTo((100 * 10) / 220, 6);
    expect(o?.cor).toBe(COR_OUTROS);
  });

  test("sem colapso quando cabe", () => {
    const c = lista({ "1": 3, "2": 2, "3": 1, "4": 0 });
    expect(linhasRanking(c, 5, new Map()).some(x => x.outros)).toBe(false);
  });

  test("sub judice fica marcado como não válido", () => {
    const c = [cand("1", 10, 20), cand("2", 10, 20, "indefinido", { dvt: "Anulado sub judice" })];
    expect(linhasRanking(c, 5, new Map()).map(x => x.valido)).toEqual([true, false]);
    expect(votoValido("Válido")).toBe(true);
    expect(votoValido("")).toBe(true);
  });
});

describe("empate", () => {
  test("detecta empate exato no topo, nunca com zero votos", () => {
    expect(empateNoTopo(lista({ "1": 10, "2": 10, "3": 4 }))).toBe(true);
    expect(empateNoTopo(lista({ "1": 11, "2": 10 }))).toBe(false);
    expect(empateNoTopo(lista({ "1": 0, "2": 0 }))).toBe(false);
  });

  test("texto da diferença diz empate e não aponta líder", () => {
    expect(textoDiferenca(lista({ "1": 10, "2": 10 }))).toBe("empate entre Candidato 1 e Candidato 2");
    expect(textoDiferenca(lista({ "1": 0, "2": 0 }))).toBe("nenhum voto totalizado ainda");
  });

  test("texto da diferença em pontos e votos", () => {
    const c = [cand("13", 52_450_000, 100_000_000), cand("22", 47_550_000, 100_000_000)];
    expect(textoDiferenca(c)).toBe("diferença 4,9 pontos, 4,9 milhões de votos");
    expect(votosPorExtenso(1_200_000)).toBe("1,2 milhão de votos");
    expect(votosPorExtenso(320_400)).toBe("320 mil votos");
    expect(votosPorExtenso(1)).toBe("1 voto");
  });

  test("chip lidera respeita vagas e não decide empate na última vaga", () => {
    expect([...lideres(lista({ "1": 30, "2": 20, "3": 10 }), 2)].sort()).toEqual(["s1", "s2"]);
    expect([...lideres(lista({ "1": 30, "2": 20, "3": 20 }), 2)]).toEqual(["s1"]);
    expect(lideres(lista({ "1": 30 }), 0).size).toBe(0);
    expect(lideres(lista({ "1": 0, "2": 0 }), 1).size).toBe(0);
  });
});

describe("cores", () => {
  test("presidente: número fixo e sequência pela ordem de referência", () => {
    const nacional = lista({ "13": 50, "22": 45, "55": 3, "30": 2 });
    const uf = lista({ "13": 10, "22": 20, "30": 9, "55": 1 });
    const m = coresPresidente(uf, CORES_PADRAO, nacional);
    expect(m.get("s13")).toBe("#b02f21");
    expect(m.get("s22")).toBe("#1457aa");
    // 55 é o terceiro nacional: primeira cor da sequência, mesmo atrás do 30 na UF.
    expect(m.get("s55")).toBe(CORES_PADRAO.sequencia[0]);
    expect(m.get("s30")).toBe(CORES_PADRAO.sequencia[1]);
  });

  test("estaduais: cor do campo e mistura de 35% de papel para quem divide o campo com o líder", () => {
    const c = [cand("1", 50, 100, "direita"), cand("2", 40, 100, "direita"), cand("3", 10, 100, "esquerda")];
    const m = coresEstaduais(c);
    expect(m.get("s1")).toBe(CORES_CAMPO_PADRAO.direita);
    expect(m.get("s2")).toBe(mix(CORES_CAMPO_PADRAO.direita, PAPEL, MISTURA_MESMO_CAMPO));
    expect(m.get("s3")).toBe(CORES_CAMPO_PADRAO.esquerda);
  });

  test("estaduais: campos diferentes ficam puros", () => {
    const m = coresEstaduais([cand("1", 50, 100, "centro"), cand("2", 40, 100, "esquerda")]);
    expect(m.get("s2")).toBe(CORES_CAMPO_PADRAO.esquerda);
  });
});

describe("duelo", () => {
  test("par em ordem fixa pelo número, mesmo com virada", () => {
    const a = parDoDuelo(lista({ "22": 60, "13": 40 }));
    const b = parDoDuelo(lista({ "22": 40, "13": 60 }));
    expect(a?.map(c => c.n)).toEqual(["13", "22"]);
    expect(b?.map(c => c.n)).toEqual(["13", "22"]);
    expect(parDoDuelo(lista({ "13": 1 }))).toBeNull();
  });

  test("cor divergente: papel no empate, cheia na margem de saturação, cinza sem voto", () => {
    const cores = new Map([["s13", "#b02f21"]]);
    const lider = { sqcand: "s13", n: "13", nmu: "LULA", sg: "PT", campo: "esquerda" as Campo, vap: 10, pvapn: 60 };
    expect(corDuelo({ cd: "SP", nm: "SP", pst: 50, tf: false, lider, segundo: { ...lider, sqcand: "s22", n: "22" }, margem: 0 }, cores)).toBe(PAPEL);
    expect(corDuelo({ cd: "SP", nm: "SP", pst: 50, tf: false, lider, margem: 25 }, cores)).toBe(mix(PAPEL, "#b02f21", 1));
    expect(corDuelo({ cd: "SP", nm: "SP", pst: 0, tf: false }, cores)).toBe("#d9d6cc");
  });
});
