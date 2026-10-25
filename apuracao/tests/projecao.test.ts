// Projeção do resultado final (/api/2t/projecao): motor puro em casos sintéticos e a rota sobre o
// banco semeado do 2º turno, com uma régua de votos do 1º turno sintética.
import { afterAll, beforeAll, describe, expect, test } from "bun:test";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { criarServidor } from "../src/server/main.ts";
import type { Servidor } from "../src/server/main.ts";
import { ROTULO_PROJECAO, estagio1T, projetar } from "../src/server/indicadores/projecao.ts";
import type { ObsMun } from "../src/server/indicadores/projecao.ts";
import type { MunVotos1T } from "../src/turno2/referencia.ts";
import { ProjecaoSchema } from "./api-schemas-2t.ts";
import type { Semeado } from "./server-helpers.ts";
import { MUN_2T, iso, seg2t, semear2t } from "./server-helpers.ts";

const ref1 = (f1: number, l1: number, extra: Partial<MunVotos1T> = {}): MunVotos1T => ({ f1, l1, vv1: f1 + l1, comp1: f1 + l1, te1: f1 + l1, ...extra });
const obs = (uf: string, cd: string, st: number, ts: number, f2: number, l2: number): ObsMun => ({ uf, cd, st, ts, f2, l2, vv2: f2 + l2 });

// Três municípios do AC com oscilação uniforme de +5 pontos para Flávio e 90% dos votos dos dois do
// 1º turno: A fechado, B na metade, C num quarto. D, no AL, ainda sem seção.
const REF = {
  AC: { "00001": ref1(600, 400), "00002": ref1(3000, 7000), "00003": ref1(20000, 20000) },
  AL: { "00004": ref1(1000, 1000) },
};
const OBS: ObsMun[] = [
  obs("AC", "00001", 10, 10, 585, 315),
  obs("AC", "00002", 50, 100, 1575, 2925),
  obs("AC", "00003", 25, 100, 4950, 4050),
  obs("AL", "00004", 0, 50, 0, 0),
];

describe("motor da projeção", () => {
  test("oscilação uniforme recupera o resultado final exato", () => {
    const r = projetar({ ref: REF, obs: OBS });
    expect(r.motivo_sem_projecao).toBeNull();
    const ac = r.ufs.find((u) => u.sigla === "AC");
    // finais verdadeiros: A 585/315, B 3150/5850, C 19800/16200
    expect(ac?.projetado?.f).toBe(23535);
    expect(ac?.projetado?.l).toBe(22365);
    expect(ac?.projetado?.p_f).toBeCloseTo((100 * 23535) / 45900, 2);
    expect(ac?.swing_pp).toBeCloseTo(5, 6);
    expect(ac?.p1_f).toBeCloseTo((100 * 23600) / 51000, 2);
    expect(ac?.observado).toEqual({ f: 585 + 1575 + 4950, l: 315 + 2925 + 4050, p_f: expect.any(Number) });
    expect(r.cobertura).toMatchObject({ municipios_observados: 3, municipios_fechados: 1, municipios_total: 4 });
  });

  test("UF sem observação usa a oscilação nacional e a razão de comparecimento nacional", () => {
    const r = projetar({ ref: REF, obs: OBS });
    const al = r.ufs.find((u) => u.sigla === "AL");
    expect(al?.observado.p_f).toBeNull();
    expect(al?.swing_pp).toBeNull();
    expect(al?.projetado?.f).toBe(990);
    expect(al?.projetado?.l).toBe(810);
    expect(al?.projetado?.p_f).toBe(55);
    const br = r.brasil.projetado;
    expect(br?.f).toBe(23535 + 990);
    expect(br?.l).toBe(22365 + 810);
    // UF sem município na régua nem no arquivo: sem projeção
    expect(r.ufs.find((u) => u.sigla === "SP")?.projetado).toBeNull();
  });

  test("município parcial compara com o 1º turno no mesmo estágio da contagem", () => {
    // No 1º turno, as cinco primeiras seções deram 400 × 100 (80% Flávio); o final foi 600 × 400.
    const m = ref1(600, 400, { ts1: 10, c: [[5, 400, 100], [10, 600, 400]] });
    expect(estagio1T(m, 0.25)).toEqual([200, 50]);
    expect(estagio1T(m, 0.5)).toEqual([400, 100]);
    expect(estagio1T(m, 1)).toEqual([600, 400]);
    const o = [obs("AC", "00009", 5, 10, 360, 90)];
    const r = projetar({ ref: { AC: { "00009": m } }, obs: o });
    const ac = r.ufs.find((u) => u.sigla === "AC");
    // mesma parte de Flávio que o 1º turno no mesmo estágio: oscilação zero e o final repete os 60%
    expect(ac?.swing_pp).toBeCloseTo(0, 6);
    expect(ac?.projetado?.p_f).toBe(60);
    expect(ac?.projetado?.f).toBe(540);
    expect(ac?.projetado?.l).toBe(360);
    // contra o final do 1º turno, o viés de ordem viraria 20 pontos de oscilação
    const semEstagio = projetar({ ref: { AC: { "00009": m } }, obs: o, mesmoEstagio: false });
    expect(semEstagio.ufs.find((u) => u.sigla === "AC")?.swing_pp).toBeCloseTo(20, 6);
    expect(semEstagio.parametros.mesmo_estagio).toBe(false);
  });

  test("Sergipe e Sudeste têm faixas próprias (a sigla SE é das duas)", () => {
    const r = projetar({
      ref: { SE: { "31000": ref1(3000, 7000), "31001": ref1(2000, 8000) }, SP: { "70000": ref1(60000, 40000), "70001": ref1(50000, 50000) } },
      obs: [obs("SE", "31000", 50, 100, 1575, 2925), obs("SE", "31001", 10, 100, 225, 675), obs("SP", "70000", 25, 100, 14850, 7650), obs("SP", "70001", 20, 100, 9900, 8100)],
    });
    const se = r.ufs.find((u) => u.sigla === "SE")?.projetado;
    const sud = r.regioes.find((u) => u.sigla === "SE")?.projetado;
    expect(se && sud).toBeTruthy();
    if (!se || !sud) return;
    expect(se.p_f).toBeLessThan(40);
    expect(sud.p_f).toBeGreaterThan(55);
    expect(se.faixa90[1]).toBeLessThan(40);
    expect(sud.faixa90[0]).toBeGreaterThan(50);
  });

  test("abaixo de 1% das seções do país não projeta e diz por quê", () => {
    const r = projetar({ ref: REF, obs: [obs("AC", "00003", 1, 1000, 40, 30), obs("AL", "00004", 0, 1000, 0, 0)] });
    expect(r.cobertura.pst).toBeLessThan(1);
    expect(r.brasil.projetado).toBeNull();
    expect(r.ufs.every((u) => u.projetado === null)).toBe(true);
    expect(r.motivo_sem_projecao).toContain("menos de 1%");
    expect(r.brasil.observado.p_f).toBeCloseTo((100 * 40) / 70, 2);
    expect(projetar({ ref: REF, obs: [] }).motivo_sem_projecao).toContain("nenhum município");
  });

  test("faixa de 90% contém a projeção e fecha quando tudo foi totalizado", () => {
    const r = projetar({ ref: REF, obs: OBS });
    const p = r.brasil.projetado;
    expect(p).not.toBeNull();
    if (!p) return;
    expect(p.faixa90[0]).toBeLessThanOrEqual(p.p_f);
    expect(p.faixa90[1]).toBeGreaterThanOrEqual(p.p_f);
    expect(p.faixa90[1] - p.faixa90[0]).toBeGreaterThan(0);
    // determinística: a mesma entrada devolve a mesma faixa
    expect(projetar({ ref: REF, obs: OBS }).brasil.projetado?.faixa90).toEqual(p.faixa90);
    const fechado = projetar({
      ref: REF,
      obs: [obs("AC", "00001", 10, 10, 585, 315), obs("AC", "00002", 100, 100, 3150, 5850), obs("AC", "00003", 100, 100, 19800, 16200), obs("AL", "00004", 50, 50, 990, 810)],
    });
    const pf = fechado.brasil.projetado;
    expect(pf?.faixa90).toEqual([pf?.p_f ?? -1, pf?.p_f ?? -1]);
    expect(fechado.brasil.pct_vv_observado).toBe(100);
  });
});

// ---------------------------------------------------------------- rota

let s: Semeado;
let srv: Servidor;
let agora = iso(seg2t(1200));
const envAntes = process.env.APURACAO_REFERENCIA_1T_VOTOS;

beforeAll(() => {
  s = semear2t();
  s.fechar();
  const municipios: Record<string, Record<string, MunVotos1T>> = {};
  for (const m of Object.values(MUN_2T)) (municipios[m.uf.toUpperCase()] ??= {})[m.cd] = ref1(1_000_000, 1_000_000);
  const caminho = join(s.dir, "referencia_1t_votos.json");
  writeFileSync(caminho, JSON.stringify({ meta: { gerado_em: iso(seg2t(-86_400)), eleicao: 6257, cargo: 1 }, brasil: ref1(0, 0), ufs: {}, municipios }));
  process.env.APURACAO_REFERENCIA_1T_VOTOS = caminho;
  srv = criarServidor({ dbPath: s.path, port: 0, log: false, agora: () => agora });
});

afterAll(async () => {
  await srv.parar();
  if (envAntes === undefined) delete process.env.APURACAO_REFERENCIA_1T_VOTOS;
  else process.env.APURACAO_REFERENCIA_1T_VOTOS = envAntes;
  s.limpar();
});

const get = async (caminho: string): Promise<{ status: number; body: unknown }> => {
  const res = await fetch(`${srv.url}${caminho}`);
  expect(res.headers.get("cache-control")).toBe("no-store");
  return { status: res.status, body: (await res.json()) as unknown };
};

describe("/api/2t/projecao", () => {
  test("antes da primeira seção: sem projeção, com o rótulo e o motivo", async () => {
    const r = ProjecaoSchema.parse((await get(`/api/2t/projecao?at=${encodeURIComponent(iso(seg2t(-60)))}`)).body);
    expect(r.rotulo).toBe(ROTULO_PROJECAO);
    expect(r.brasil.projetado).toBeNull();
    expect(r.motivo_sem_projecao).not.toBeNull();
    expect(r.candidatos?.f.n).toBe("22");
    expect(r.candidatos?.l.n).toBe("13");
  });

  test("17:20: projeção com faixa, regiões e UFs no contrato", async () => {
    const r = ProjecaoSchema.parse((await get(`/api/2t/projecao?at=${encodeURIComponent(iso(seg2t(1200)))}`)).body);
    expect(r.motivo_sem_projecao).toBeNull();
    expect(r.brasil.projetado).not.toBeNull();
    expect(r.cobertura.municipios_observados).toBeGreaterThanOrEqual(3);
    expect(r.ufs.find((u) => u.sigla === "SP")?.projetado).not.toBeNull();
    expect(r.regioes.map((x) => x.sigla)).toEqual(["N", "NE", "CO", "SE", "S", "ZZ"]);
  });

  test("ao vivo: série reconstruída na grade de 5 min e gravada ao lado do banco", async () => {
    agora = iso(seg2t(1260));
    const r = ProjecaoSchema.parse((await get("/api/2t/projecao")).body);
    expect(r.serie.length).toBeGreaterThanOrEqual(4);
    expect(r.serie.at(-1)?.[0]).toBe(21);
    expect(r.serie.every((p, i, a) => i === 0 || p[0] > (a[i - 1]?.[0] ?? -1))).toBe(true);
    const arq = join(s.dir, "projecao_2t_serie.json");
    expect(existsSync(arq)).toBe(true);
    expect((JSON.parse(readFileSync(arq, "utf8")) as { serie: unknown[] }).serie.length).toBe(r.serie.length);
  });
});
