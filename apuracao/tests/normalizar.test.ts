import { describe, expect, test } from "bun:test";
import {
  normalizarAb, normalizarCm, normalizarE, normalizarEleC, normalizarU, politicaPara,
} from "../src/parse/normalizar.ts";
import { lerConfig } from "../src/config.ts";
import { lerAb, lerCm, lerE, lerEleC, lerU } from "./helpers.ts";

const sempre = { uf: "sp", politicaCandidatos: "sempre", primeiro: false } as const;

describe("normalizarU, vereador SP 2024 (55 vagas, valores reais)", () => {
  const p = lerU("2024/sp71072-c0013-e000619-u.json");
  const n = normalizarU(p, sempre);
  const totalCand = p.carg.flatMap((c) => (c.agr ?? []).flatMap((a) => (a.par ?? []).flatMap((x) => x.cand ?? []))).length;

  test("metadados e totais", () => {
    expect(n.totais.vagas).toBe(55);
    expect(n.totais.tv).toBe(6773587);
    expect(n.totais.vvc).toBe(5794164);
    expect(n.totais.vl).toBe(674061);
    expect(n.totais.pvvc).toBeCloseTo(85.540556281, 9);
    expect(n.totais.est).toBe(n.totais.te);
    expect(n.snapshotMeta.tf).toBe(1);
    expect(n.snapshotMeta.andamento).toBe("f");
    expect(n.snapshotMeta.gerado_em).toBe("2026-09-29T22:31:54.000Z");
    expect(n.snapshotMeta.totalizado_em).toBe("2024-12-03T13:22:15.000Z");
    expect(n.snapshotMeta.idg).toBe(596176);
    expect(n.final).toBe(true);
    expect(n.cargo).toBe(13);
    expect(n.ele).toBe(619);
  });
  test("uma linha por candidato e eleitos iguais aos e=s", () => {
    expect(totalCand).toBe(979);
    expect(n.votoCandidato.length).toBe(totalCand);
    expect(n.candidatos.length).toBe(totalCand);
    expect(n.votoCandidato.filter((c) => c.eleito === 1).length).toBe(55);
    const st = new Set(n.votoCandidato.map((c) => c.st));
    expect(st).toEqual(new Set(["Eleito por QP", "Eleito por média", "Não eleito", "Suplente"]));
    const marina = n.votoCandidato.find((c) => c.sqcand === 250002052100);
    expect(marina).toEqual({ sqcand: 250002052100, vap: 39147, pvapn: 0.675628098, eleito: 1, st: "Eleito por QP", dvt: "Válido" });
  });
  test("partidos com legenda e agremiações com vagas", () => {
    const rede = n.votoPartido.find((x) => x.partido_n === 18);
    expect(rede).toEqual({ partido_n: 18, agremiacao_n: 250001712735, tvtn: 46304, tvtl: 1721, tval: 1721, tvan: 46304, dvt: "Válido (legenda)" });
    expect(n.votoPartido.every((x) => x.tvtl !== null && x.tval !== null)).toBe(true);
    const psolRede = n.votoAgremiacao.find((a) => a.agremiacao_n === 250001712735);
    expect(psolRede?.vagas).toBe(7);
    expect(psolRede?.tvtl).toBe(107361);
    expect(n.votoAgremiacao.reduce((s, a) => s + (a.vagas ?? 0), 0)).toBe(55);
    expect(n.federacoes.length).toBe(3);
    expect(JSON.parse(n.federacoes[0]?.partidos ?? "[]")).toContain(13);
  });
});

describe("normalizarU, presidente 2026 zerado", () => {
  const n = normalizarU(lerU("br-c0001-e006257-u.json"), { uf: null, politicaCandidatos: politicaPara(1, "br"), primeiro: false });
  test("12 candidatos com vices", () => {
    expect(n.candidatos.length).toBe(12);
    expect(n.votoCandidato.length).toBe(12);
    expect(n.candidatos.every((c) => c.vices !== null)).toBe(true);
    const flavio = n.candidatos.find((c) => c.numero === 22);
    expect(flavio?.nome_urna).toBe("FLAVIO BOLSONARO");
    const vices = JSON.parse(flavio?.vices ?? "[]") as Array<{ nmu: string; tp: string }>;
    expect(vices[0]?.nmu).toBe("ALFREDO GASPAR");
    expect(vices[0]?.tp).toBe("v");
    expect(flavio?.uf).toBeNull();
  });
  test("zerado: totais em zero, sem totalização, não final", () => {
    expect(n.totais.tv).toBe(0);
    expect(n.totais.pst).toBe(0);
    expect(n.snapshotMeta.totalizado_em).toBeNull();
    expect(n.snapshotMeta.tf).toBe(0);
    expect(n.final).toBe(false);
    expect(n.votoCandidato.every((c) => c.vap === 0 && c.st === null)).toBe(true);
  });
});

describe("política de candidatos", () => {
  const p = lerU("sp71072-c0007-e006259-u.json");
  test("politicaPara", () => {
    expect(politicaPara(7, "mu")).toBe("primeiro_e_final");
    expect(politicaPara(6, "zona")).toBe("primeiro_e_final");
    expect(politicaPara(7, "uf")).toBe("sempre");
    expect(politicaPara(1, "zona")).toBe("sempre");
    expect(politicaPara(25, "mu")).toBe("sempre");
  });
  test("proporcional em município só no primeiro, no final ou forçado", () => {
    const base = { uf: "sp", politicaCandidatos: "primeiro_e_final" } as const;
    const meio = normalizarU(p, { ...base, primeiro: false });
    expect(meio.incluiuCandidatos).toBe(false);
    expect(meio.votoCandidato.length).toBe(0);
    expect(meio.candidatos.length).toBe(0);
    expect(meio.votoPartido.length).toBeGreaterThan(0);
    expect(normalizarU(p, { ...base, primeiro: true }).votoCandidato.length).toBe(1346);
    expect(normalizarU(p, { ...base, primeiro: false, forcarCandidatos: true }).votoCandidato.length).toBe(1346);
    const final = normalizarU({ ...p, tf: "s" }, { ...base, primeiro: false });
    expect(final.final).toBe(true);
    expect(final.votoCandidato.length).toBe(1346);
  });
});

describe("normalizarAb", () => {
  test("br 2026: 28 UFs (27 e zz) com munnr/munpt/munf e a linha br", () => {
    const n = normalizarAb(lerAb("br-e006257-ab.json"), new Map());
    expect(n.primeiro).toBe(true);
    expect(n.entradas.length).toBe(29);
    const ufs = n.entradas.filter((e) => e.tpabr === "uf");
    expect(ufs.length).toBe(28);
    expect(ufs.every((e) => e.munnr !== null && e.munpt === 0 && e.munf === 0)).toBe(true);
    const sp = ufs.find((e) => e.cdabr === "sp");
    expect(sp?.munnr).toBe(645);
    const br = n.entradas.find((e) => e.tpabr === "br");
    expect(br?.ufsnr).toBe(28);
    expect(br?.munnr).toBeNull();
  });
  test("br 2024: 27 entradas (26 UFs e br), munf com valores reais", () => {
    const n = normalizarAb(lerAb("2024/br-e000619-ab.json"), new Map());
    expect(n.entradas.length).toBe(27);
    const ac = n.entradas.find((e) => e.cdabr === "ac");
    expect(ac?.munf).toBe(22);
    expect(ac?.totalizado_em).toBe("2025-12-03T14:11:03.000Z");
    expect(n.entradas.find((e) => e.cdabr === "br")?.ufspt).toBe(5);
  });
  test("SP: 646 entradas (645 municípios e a UF)", () => {
    const n = normalizarAb(lerAb("sp-e006257-ab.json"), new Map());
    expect(n.entradas.length).toBe(646);
    expect(n.entradas.filter((e) => e.tpabr === "mun").length).toBe(645);
    expect(n.fingerprints.size).toBe(646);
  });
});

describe("configuração e -e", () => {
  test("ele-c: três eleições do pleito 3220 e seus cargos", () => {
    const n = normalizarEleC(lerEleC("ele-c.json"));
    expect(n.eleicoes.map((e) => e.cd)).toEqual([6257, 6259, 6261]);
    expect(n.eleicoes[0]?.cdt2).toBe(6258);
    expect(n.eleicoes[2]?.cdt2).toBeNull();
    expect(n.cargos.filter((c) => c.eleicao_cd === 6259).map((c) => c.cd)).toEqual([3, 5, 6, 7, 8]);
    expect(n.cargos.filter((c) => c.proporcional === 1).map((c) => c.cd)).toEqual([6, 7, 8]);
  });
  test("2º turno em pleito próprio (2024: 452 e 453): APURACAO_PLEITO troca o filtro", () => {
    expect(lerConfig({}).pleito).toBe(3220);
    expect(lerConfig({ APURACAO_PLEITO: "453" }).pleito).toBe(453);
    const n = normalizarEleC(lerEleC("ele-c.json"), lerConfig({ APURACAO_PLEITO: "453" }).pleito);
    expect(n.eleicoes.map((e) => [e.cd, e.turno])).toEqual([[620, 2]]);
  });
  test("cm: municípios e zonas", () => {
    const n = normalizarCm(lerCm("mun-e006257-cm.json"));
    expect(n.ufs.length).toBe(28);
    expect(n.municipios.length).toBe(5757);
    expect(n.zonas.length).toBe(6292);
    const sp = n.municipios.find((m) => m.cd === "71072");
    expect(sp?.capital).toBe(1);
    expect(sp?.ibge).toBe("3550308");
    expect(n.zonas.filter((z) => z.municipio_cd === "71072").length).toBe(57);
  });
  test("-e de 2024: 645 municípios", () => {
    const n = normalizarE(lerE("2024/sp-c0011-e000619-e.json"));
    expect(n.cargo).toBe(11);
    expect(n.uf).toBe("sp");
    expect(n.entradas.length).toBe(645);
    const cand = JSON.parse(n.entradas[0]?.cand ?? "[]") as Array<{ vap: number }>;
    expect(cand.length).toBeGreaterThan(0);
  });
});
