// Indicadores do 2º turno: /api/2t/regioes, ufs, abstencao, estaduais e evolucao, mais o
// /api/config e o /api/estado no 2º turno. Banco semeado com arquivos reais zerados do pleito
// 3221 (tests/fixtures/2t) e versões derivadas: zerado, parcial com viradas e final; régua do
// 1º turno sintética (presente) e ausente.
import { afterAll, beforeAll, describe, expect, test } from "bun:test";
import { join } from "node:path";
import { criarServidor } from "../src/server/main.ts";
import type { Servidor } from "../src/server/main.ts";
import type { Semeado } from "./server-helpers.ts";
import { MUN_2T, SQ2T, escreverRegua2t, iso, seg2t, semear2t } from "./server-helpers.ts";
import { AbstencaoSchema, Config2tSchema, EstaduaisSchema, EvolucaoSchema, RegioesSchema, UfsSchema } from "./api-schemas-2t.ts";
import { EstadoSchema } from "./api-schemas.ts";
import { REGIOES } from "../src/turno2/comum.ts";

let s: Semeado;
let srv: Servidor;
let reguaPath = "";
const envAntes = process.env.APURACAO_REFERENCIA_1T;

const get = async (caminho: string): Promise<{ status: number; body: unknown }> => {
  const res = await fetch(`${srv.url}${caminho}`);
  expect(res.headers.get("cache-control")).toBe("no-store");
  return { status: res.status, body: (await res.json()) as unknown };
};
const em = (seg: number): string => `at=${encodeURIComponent(iso(seg2t(seg)))}`;

beforeAll(() => {
  s = semear2t();
  s.fechar();
  reguaPath = escreverRegua2t(s.dir);
  process.env.APURACAO_REFERENCIA_1T = reguaPath;
  srv = criarServidor({ dbPath: s.path, port: 0, log: false });
});

afterAll(async () => {
  await srv.parar();
  if (envAntes === undefined) delete process.env.APURACAO_REFERENCIA_1T;
  else process.env.APURACAO_REFERENCIA_1T = envAntes;
  s.limpar();
});

const L = String(SQ2T.lula);
const F = String(SQ2T.flavio);

describe("zerado (16:59, antes da divulgação)", () => {
  test("regiões e Brasil em zero, régua presente", async () => {
    const r = RegioesSchema.parse((await get(`/api/2t/regioes?${em(-60)}`)).body);
    expect(r).toMatchObject({ ele: 6258, cargo: 1, turno: 2, referencia_1t: true, min: -1 });
    expect(r.regioes.map((x) => x.sigla)).toEqual(["N", "NE", "CO", "SE", "S", "ZZ"]);
    expect(r.brasil).toMatchObject({ ts: 499_248, st: 0, pst: 0, lider: null, margem_pp: 0, vel_10min_spm: 0, eta_100_iso: null });
    expect(r.brasil.votos).toEqual({ [L]: { vap: 0, pvapn: 0 }, [F]: { vap: 0, pvapn: 0 } });
    // antes da primeira seção não há comparação com o 1º turno (pedido do telão)
    expect(r.brasil.ref_1t).toEqual({ pst_mesmo_relogio: null, atraso_min: null, pa_final_1t: r.brasil.ref_1t?.pa_final_1t ?? -1 });
    expect(r.brasil.ref_1t?.pa_final_1t).not.toBeNull();
    expect(r.regioes.find((x) => x.sigla === "ZZ")?.ref_1t).toBeNull();
  });

  test("UFs, abstenção, estaduais e evolução em zero", async () => {
    const u = UfsSchema.parse((await get(`/api/2t/ufs?${em(-60)}`)).body);
    expect(u.ufs.every((x) => x.st === 0 && !x.parada)).toBe(true);
    expect(u.ufs.map((x) => x.uf)).toEqual([...u.ufs.map((x) => x.uf)].sort());
    const a = AbstencaoSchema.parse((await get(`/api/2t/abstencao?${em(-60)}`)).body);
    expect(a.brasil).toMatchObject({ n_mun: 5757, n_mun_fechados: 0, pa_2t: null, pa_1t_mesmos: null, delta_pp: null });
    expect(a.destaques).toEqual({ subiu: [], caiu: [] });
    const e = EstaduaisSchema.parse((await get(`/api/2t/estaduais?${em(-60)}`)).body);
    expect(e).toMatchObject({ ele: 6260, cargo: 3 });
    expect(e.ufs.map((x) => x.uf)).toEqual(["AC", "AM", "DF", "ES", "RN", "TO"]);
    expect(e.ufs[0]?.cand.map((c) => [c.n, c.nome_urna, c.vap])).toEqual([["10", "ALAN RICK", 0], ["11", "MAILZA ASSIS", 0]]);
    expect(e.ufs.every((x) => x.viradas.length === 0 && x.lider === null)).toBe(true);
    const ev = EvolucaoSchema.parse((await get(`/api/2t/evolucao?${em(-60)}`)).body);
    expect(Object.values(ev.series).every((v) => v.length === 0)).toBe(true);
    expect(ev.candidatos.map((c) => c.n)).toEqual(["13", "22"]);
  });
});

describe("parcial (17:25): virada, fuso, arquivo parado", () => {
  test("regiões somam o Brasil e o Brasil soma as UFs", async () => {
    const r = RegioesSchema.parse((await get(`/api/2t/regioes?${em(1500)}`)).body);
    const b = r.brasil;
    for (const k of ["ts", "st", "snt", "te", "est", "comparecimento", "abstencao", "vv", "vb", "vn", "tv"] as const) {
      expect(r.regioes.reduce((acc, x) => acc + x[k], 0)).toBe(b[k]);
    }
    for (const sq of [L, F]) expect(r.regioes.reduce((acc, x) => acc + (x.votos[sq]?.vap ?? 0), 0)).toBe(b.votos[sq]?.vap ?? -1);
    expect(b.st).toBe(60_000 + 5_000 + 9_000 + 1_000 + 3_000);
    expect(b.votos[L]?.vap).toBe(8_710_000);
    expect(b.votos[F]?.vap).toBe(8_820_000);
    expect(b.votos[F]?.pvapn).toBe(Math.round((8_820_000 / 17_530_000) * 10_000) / 100);
    expect(b.lider).toBe(F);
    expect(b.margem_pp).toBe(Math.round(((8_820_000 - 8_710_000) / 17_530_000) * 10_000) / 100);
    expect(b.pa).toBe(20);
    // ritmo: o que estava lido às 17:15 (29.500 seções) contra 17:25 (78.000)
    expect(b.vel_10min_spm).toBe(4_850);
    expect(b.eta_100_iso).toBe(iso(seg2t(1500) + ((499_248 - 78_000) / 4_850) * 60_000));
    expect(b.atualizado_em).toBe(iso(seg2t(1180)));
    const se = r.regioes.find((x) => x.sigla === "SE");
    expect(se?.ufs).toEqual([...REGIOES.SE]);
    expect(se?.st).toBe(65_000);
    expect(se?.lider).toBe(F);
    const ne = r.regioes.find((x) => x.sigla === "NE");
    expect(ne?.lider).toBe(L);
    expect(ne?.votos[L]?.pvapn).toBe(75);
  });

  test("régua: mesmo relógio e atraso contra a curva agregada", async () => {
    const r = RegioesSchema.parse((await get(`/api/2t/regioes?${em(1500)}`)).body);
    // curva sintética: 10% aos 20 min e 50% aos 60 min em todas as UFs (exterior degenerado fica fora)
    expect(r.brasil.ref_1t?.pst_mesmo_relogio).toBeCloseTo(10, 1);
    // degrau: o 1º turno passou de 15,62% (Brasil) e de 31,98% (Sudeste) só aos 60 min; às 17:25 o
    // 2º turno está 35 min à frente
    expect(r.brasil.ref_1t?.atraso_min).toBe(25 - 60);
    expect(r.regioes.find((x) => x.sigla === "SE")?.ref_1t?.atraso_min).toBe(25 - 60);
  });

  test("UFs: fuso do AC corrigido, RJ parado, marcos saneados, municípios abertos", async () => {
    const u = UfsSchema.parse((await get(`/api/2t/ufs?${em(1500)}`)).body);
    const uf = (x: string) => u.ufs.find((l) => l.uf === x);
    for (let i = 1; i < u.ufs.length; i += 1) expect((u.ufs[i - 1]?.pst ?? 0) <= (u.ufs[i]?.pst ?? 0)).toBe(true);
    const ac = uf("AC");
    expect(ac?.ultima_versao_em).toBe(iso(seg2t(1180)));
    // idade pela publicação (gerado_em 17:19:50), não pelo carimbo de totalização (17:19:40)
    expect(ac?.idade_s).toBe(310);
    expect(ac?.ref_1t).toMatchObject({ p50_min: 60, p90_min: 120, p99_min: 180, p100_min: 180, pa_final: 20 });
    const sp = uf("SP");
    expect(sp).toMatchObject({ st: 60_000, pst: 57.88, munnr: 400, munpt: 230, munf: 15, lider: F, parada: false, vel_10min_spm: 4_000 });
    // 57,88% só foi passado no degrau de 90% (120 min)
    expect(sp?.ref_1t?.atraso_min).toBe(25 - 120);
    expect(sp?.pendentes_maiores.map((p) => p.nm)).toEqual(["São Paulo", "Guarulhos", "Campinas"]);
    expect(sp?.pendentes_maiores[0]).toMatchObject({ cd: "71072", te: 9_145_969, pst: 56.21 });
    const rj = uf("RJ");
    expect(rj).toMatchObject({ st: 5_000, parada: true, idade_s: 910, vel_10min_spm: 0, eta_100_iso: null });
    expect(rj?.pendentes_maiores[0]).toMatchObject({ cd: "60011", nm: "Rio de Janeiro" });
    expect(uf("ZZ")?.ref_1t).toBeNull();
    expect(uf("MG")).toMatchObject({ st: 0, parada: true });
    expect(uf("MG")?.ref_1t).toMatchObject({ pst_mesmo_relogio: null, atraso_min: null, p50_min: 60 });
    // às 17:15 o país começou havia 5 min (17:10): ninguém está parado ainda
    const cedo = UfsSchema.parse((await get(`/api/2t/ufs?${em(900)}`)).body);
    expect(cedo.ufs.some((l) => l.parada)).toBe(false);
    const folgado = UfsSchema.parse((await get(`/api/2t/ufs?${em(1500)}&limiar_parada_min=20`)).body);
    expect(folgado.limiar_parada_min).toBe(20);
    expect(folgado.ufs.find((l) => l.uf === "RJ")?.parada).toBe(false);
  });

  test("estaduais: virada no AC e no DF, ordem por número, régua só onde existe", async () => {
    const e = EstaduaisSchema.parse((await get(`/api/2t/estaduais?${em(1500)}`)).body);
    const ac = e.ufs.find((x) => x.uf === "AC");
    expect(ac?.lider).toBe(String(SQ2T.mailza));
    expect(ac?.viradas).toEqual([{ at: iso(seg2t(1180)), de: String(SQ2T.alanRick), para: String(SQ2T.mailza) }]);
    expect(ac?.cand.map((c) => c.n)).toEqual(["10", "11"]);
    expect(ac).toMatchObject({ munnr: 10, munpt: 11, munf: 1, ultima_versao_em: iso(seg2t(1180)), pa_final_1t: 21 });
    expect(ac?.ref_1t?.pst_mesmo_relogio ?? 0).toBeCloseTo(10, 1);
    const df = e.ufs.find((x) => x.uf === "DF");
    expect(df?.viradas.map((v) => [v.de, v.para])).toEqual([[String(SQ2T.leandro), String(SQ2T.celina)]]);
    expect(df?.cand.find((c) => c.n === "13")?.campo).toBe("esquerda");
    expect(e.ufs.find((x) => x.uf === "AM")).toMatchObject({ ref_1t: null, pa_final_1t: null });
  });

  test("evolução: grade, virada nacional, régua na mesma grade, limites de passo", async () => {
    const ev = EvolucaoSchema.parse((await get(`/api/2t/evolucao?${em(1500)}&passo=300`)).body);
    expect(ev.passo_s).toBe(300);
    expect(Object.keys(ev.series)).toEqual(["BR", "N", "NE", "CO", "SE", "S", "ZZ"]);
    const br = ev.series.BR ?? [];
    expect(br.map((p) => p[0])).toEqual([0, 5, 10, 15, 20, 25]);
    expect(br[2]).toEqual([10, 5.9, 56.38, 43.62, 29_500]);
    expect(br[4]).toEqual([20, 15.62, 49.69, 50.31, 78_000]);
    expect(ev.referencia_1t?.BR?.[4]?.[1] ?? 0).toBeCloseTo(10, 1);
    expect(ev.referencia_1t?.ZZ).toEqual([]);
    const uf = EvolucaoSchema.parse((await get(`/api/2t/evolucao?${em(1500)}&nivel=uf&passo=10`)).body);
    expect(uf.passo_s).toBe(30);
    expect(Object.keys(uf.series).length).toBe(29);
    expect(uf.series.AC?.find((p) => p[0] === 20)?.[4]).toBe(1_000);
    const longe = EvolucaoSchema.parse((await get(`/api/2t/evolucao?at=${encodeURIComponent(iso(seg2t(3 * 86_400)))}&passo=30`)).body);
    expect((longe.series.BR ?? []).length).toBeLessThanOrEqual(1_442);
    expect((await get(`/api/2t/evolucao?${em(1500)}&nivel=mun`)).status).toBe(400);
  });
});

describe("arquivo regerado sem nova totalização (17:36)", () => {
  test("o AC continua na hora corrigida da totalização e envelhece", async () => {
    const u = UfsSchema.parse((await get(`/api/2t/ufs?${em(2200)}`)).body);
    const ac = u.ufs.find((l) => l.uf === "AC");
    expect(ac?.ultima_versao_em).toBe(iso(seg2t(1180)));
    // regerado sem contagem nova: a publicação continua a das contagens (17:19:50) e envelhece
    expect(ac?.idade_s).toBe(1_010);
    // nenhuma UF andou entre 17:26:40 e 17:36:40: é pausa geral, não arquivo parado
    expect(u.ufs.some((l) => l.parada)).toBe(false);
  });
});

describe("final (19:05)", () => {
  test("tudo totalizado; atraso pelo minuto do fechamento, não pelo relógio", async () => {
    const r = RegioesSchema.parse((await get(`/api/2t/regioes?${em(7500)}`)).body);
    expect(r.brasil).toMatchObject({ st: 499_248, ts: 499_248, pst: 100, eta_100_iso: null });
    // RJ fecha por último (19:01, totalização 19:00:40); a curva sintética chega a 100% aos 180 min
    expect(r.brasil.ref_1t?.atraso_min).toBe(-59.3);
    const depois = RegioesSchema.parse((await get(`/api/2t/regioes?${em(9000)}`)).body);
    expect(depois.brasil.ref_1t?.atraso_min).toBe(-59.3);
    // fora do dia da eleição (três dias depois) o relógio não é comparável: sem atraso gigante
    const fora = RegioesSchema.parse((await get(`/api/2t/regioes?${em(3 * 86_400)}`)).body);
    expect(fora.brasil.ref_1t).toMatchObject({ pst_mesmo_relogio: null, atraso_min: null });
    const foraUfs = UfsSchema.parse((await get(`/api/2t/ufs?${em(3 * 86_400)}`)).body);
    expect(foraUfs.ufs.every((l) => l.ref_1t === null || (l.ref_1t.atraso_min === null && l.ref_1t.pst_mesmo_relogio === null))).toBe(true);
    const foraEst = EstaduaisSchema.parse((await get(`/api/2t/estaduais?${em(-5 * 86_400)}`)).body);
    expect(foraEst.ufs.every((x) => x.ref_1t === null || x.ref_1t.atraso_min === null)).toBe(true);
    const u = UfsSchema.parse((await get(`/api/2t/ufs?${em(7500)}`)).body);
    expect(u.ufs.every((l) => l.pst === 100 && !l.parada)).toBe(true);
    const e = EstaduaisSchema.parse((await get(`/api/2t/estaduais?${em(7500)}`)).body);
    const ac = e.ufs.find((x) => x.uf === "AC");
    expect(ac?.lider).toBe(String(SQ2T.alanRick));
    expect(ac?.viradas.length).toBe(2);
  });

  test("abstenção: municípios fechados contra os mesmos no 1º turno", async () => {
    const a = AbstencaoSchema.parse((await get(`/api/2t/abstencao?${em(7500)}`)).body);
    expect(a.destaques.subiu.map((m) => [m.nm, m.delta_pp])).toEqual([["Guarulhos", 4], ["Rio Branco", 3.2]]);
    expect(a.destaques.caiu.map((m) => [m.nm, m.delta_pp])).toEqual([["Campinas", -3.5]]);
    expect(a.destaques.subiu[0]).toMatchObject({ uf: "SP", cd: MUN_2T.guarulhos.cd, pa_1t: 20, pa_2t: 24, fechou_min: 29.7 });
    const sp = a.ufs.find((x) => x.uf === "SP");
    expect(sp).toMatchObject({ n_mun: 645, n_mun_fechados: 4, pa_corrente: 20, pa_final_1t: 20 });
    const ac = a.ufs.find((x) => x.uf === "AC");
    expect(ac).toMatchObject({ n_mun_fechados: 1, pa_2t: 22.2, pa_1t_mesmos: 19, delta_pp: 3.2 });
    expect(a.brasil.n_mun_fechados).toBe(5);
    expect(a.brasil.comparecimento).toBe(a.ufs.reduce((acc, x) => acc + x.comparecimento, 0));
    const pa2 = (100 * a.brasil.abstencao) / (a.brasil.comparecimento + a.brasil.abstencao);
    expect(a.brasil.pa_2t).toBe(Math.round(pa2 * 100) / 100);
    expect(a.brasil.delta_pp ?? Number.NaN).toBeCloseTo((a.brasil.pa_2t ?? 0) - (a.brasil.pa_1t_mesmos ?? 0), 1);
  });

  test("fechamento do município com fuso corrigido (Rio Branco)", async () => {
    const a = AbstencaoSchema.parse((await get(`/api/2t/abstencao?${em(7500)}`)).body);
    // totalização às 17:39:40 de Brasília, carimbada 15:39:40 (hora do Acre)
    expect(a.destaques.subiu.find((m) => m.cd === MUN_2T.rioBranco.cd)?.fechou_min).toBe(39.7);
    const u = UfsSchema.parse((await get(`/api/2t/ufs?${em(7500)}`)).body);
    expect(u.ufs.find((l) => l.uf === "AC")?.pendentes_maiores.some((p) => p.cd === MUN_2T.rioBranco.cd)).toBe(false);
  });
});

describe("régua ausente", () => {
  beforeAll(() => {
    process.env.APURACAO_REFERENCIA_1T = join(s.dir, "nao-existe.json");
  });
  afterAll(() => {
    process.env.APURACAO_REFERENCIA_1T = reguaPath;
  });

  test("todas as rotas respondem sem comparação", async () => {
    const r = RegioesSchema.parse((await get(`/api/2t/regioes?${em(1500)}`)).body);
    expect(r.referencia_1t).toBe(false);
    expect([r.brasil, ...r.regioes].every((x) => x.ref_1t === null)).toBe(true);
    expect(r.brasil.st).toBe(78_000);
    const u = UfsSchema.parse((await get(`/api/2t/ufs?${em(1500)}`)).body);
    expect(u.ufs.every((x) => x.ref_1t === null)).toBe(true);
    const a = AbstencaoSchema.parse((await get(`/api/2t/abstencao?${em(7500)}`)).body);
    expect(a.brasil).toMatchObject({ n_mun_fechados: 5, pa_1t_mesmos: null, delta_pp: null });
    expect(a.brasil.pa_2t).not.toBeNull();
    expect(a.ufs.every((x) => x.pa_final_1t === null)).toBe(true);
    expect(a.destaques).toEqual({ subiu: [], caiu: [] });
    const e = EstaduaisSchema.parse((await get(`/api/2t/estaduais?${em(1500)}`)).body);
    expect(e.ufs.every((x) => x.ref_1t === null && x.pa_final_1t === null)).toBe(true);
    const ev = EvolucaoSchema.parse((await get(`/api/2t/evolucao?${em(1500)}`)).body);
    expect(ev.referencia_1t).toBeNull();
  });
});

describe("configuração e estado no 2º turno", () => {
  test("/api/config com turno 2, eleições 6258/6260, UFs de governador e regiões", async () => {
    const c = Config2tSchema.parse((await get("/api/config")).body);
    expect(c.turno).toBe(2);
    expect(c.eleicoes).toEqual({ federal: 6258, estadual: 6260 });
    expect(c.ufs_governador_2t).toEqual(["AC", "AM", "DF", "ES", "RN", "TO"]);
    expect(c.regioes.NE).toEqual([...REGIOES.NE]);
    expect(c.ufs.length).toBe(28);
  });

  test("/api/estado no 2º turno", async () => {
    const e = EstadoSchema.parse((await get(`/api/estado?${em(1500)}`)).body);
    expect(e.turno).toBe(2);
    expect(e.ufs.find((u) => u.uf === "sp")).toMatchObject({ st: 60_000, munpt: 230 });
  });

  test("sem `at`, idade e ritmo seguem o relógio mesmo com o cache", async () => {
    let agora = seg2t(1500);
    const vivo = criarServidor({ dbPath: s.path, port: 0, log: false, agora: () => iso(agora) });
    try {
      const pedir = async (): Promise<number | null | undefined> => {
        const res = await fetch(`${vivo.url}/api/2t/ufs`);
        return UfsSchema.parse(await res.json()).ufs.find((l) => l.uf === "SP")?.idade_s;
      };
      const tempos: number[] = [];
      expect(await pedir()).toBe(310);
      agora += 60_000;
      const t = performance.now();
      expect(await pedir()).toBe(370);
      tempos.push(performance.now() - t);
      expect(tempos[0] ?? Infinity).toBeLessThan(500);
    } finally {
      await vivo.parar();
    }
  });
});
