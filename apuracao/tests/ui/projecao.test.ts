// Telão do 2º turno, tela "projecao": normalizador da rota /api/2t/projecao, mock coerente com o
// relógio (sem projeção antes de 1% das seções, faixa que estreita), funções puras da tela e registro.
import { describe, expect, test } from "bun:test";
import { readFileSync } from "node:fs";
import { TECLA_TELA_2T } from "../../src/ui/control/navegacao.ts";
import { normalizarProjecao, pedidoDaRota, ROTAS_2T, ROTULO_PROJECAO } from "../../src/ui/data/doist.ts";
import type { BlocoProjecao, PontoProjecao, Projecao } from "../../src/ui/data/doist.ts";
import { criarMock } from "../../src/ui/data/mock.ts";
import { TELAS_2T } from "../../src/ui/views/meta-2t.ts";
import { dominioProjecao, ufsQueMaisOscilaram } from "../../src/ui/views/projecao.ts";

const bloco = (sigla: string, extra: Record<string, unknown> = {}): Record<string, unknown> => ({
  sigla,
  nome: sigla,
  pst: 40,
  pct_vv_observado: 38.5,
  p1_f: 51.01,
  observado: { f: 1000, l: 900, p_f: 52.63 },
  projetado: { f: 52_000_000, l: 48_000_000, p_f: 52, p_l: 48, p_f_validos: 49.6, p_l_validos: 45.8, faixa90: [51.1, 52.9] },
  swing_pp: 1.62,
  ...extra,
});

describe("normalizarProjecao", () => {
  test("projeção cheia: blocos, parâmetros e série ordenada", () => {
    const r = normalizarProjecao({
      at: "2026-10-25T21:00:00.000Z",
      min: 60,
      ele: 6258,
      cargo: 1,
      rotulo: ROTULO_PROJECAO,
      candidatos: { f: { sqcand: "280002551544", n: "22", nome_urna: "FLAVIO BOLSONARO" }, l: { sqcand: "280002542548", n: "13", nome_urna: "LULA" } },
      cobertura: { pst: 40, st: 190_000, ts: 475_000, pct_vv_observado: 38.5, municipios_observados: 3000, municipios_fechados: 1200, municipios_total: 5757 },
      brasil: bloco("BR", { nome: "Brasil" }),
      regioes: [bloco("N", { nome: "Norte" })],
      ufs: [bloco("sp"), bloco("MG", { swing_pp: -3.2, projetado: null })],
      parametros: { K: 2000, K_uf: 20000, erro_comum_pp: 1, reps: 200, nivel_faixa: 90, minimo_pst: 1, metodo: "oscilação proporcional" },
      motivo_sem_projecao: null,
      serie: [
        [60, 52, 51.1, 52.9, 52.63, 40],
        [30, 53, 50, 56, 53.5, 10],
      ],
    });
    expect(r.situacao).toBe("ok");
    if (r.situacao !== "ok") return;
    const p = r.dados;
    expect(p.brasil.projetado?.faixa90).toEqual([51.1, 52.9]);
    expect(p.brasil.projetado?.p_l).toBe(48);
    expect(p.ufs.map(u => u.sigla)).toEqual(["SP", "MG"]);
    expect(p.ufs[1]?.projetado).toBeNull();
    expect(p.parametros.K).toBe(2000);
    expect(p.serie.map(s => s.min)).toEqual([30, 60]);
    expect(p.serie[1]).toEqual({ min: 60, proj: 52, a: 51.1, b: 52.9, obs: 52.63, pst: 40 });
    expect(p.candidatos.f.n).toBe("22");
  });

  test("sem base: projetado null, motivo preservado, série com nulos", () => {
    const r = normalizarProjecao({
      at: "2026-10-25T20:05:00.000Z",
      min: 5,
      cobertura: { pst: 0.4 },
      brasil: bloco("BR", { projetado: null, observado: { f: 10, l: 12, p_f: 45.45 } }),
      regioes: [],
      ufs: [],
      motivo_sem_projecao: "menos de 1% das seções totalizadas no país",
      serie: [[5, null, null, null, 45.45, 0.4]],
    });
    expect(r.situacao).toBe("ok");
    if (r.situacao !== "ok") return;
    expect(r.dados.brasil.projetado).toBeNull();
    expect(r.dados.motivo_sem_projecao).toContain("1%");
    expect(r.dados.rotulo).toBe(ROTULO_PROJECAO);
    expect(r.dados.serie[0]?.proj).toBeNull();
    expect(r.dados.candidatos.l.n).toBe("13");
  });

  test("corpo sem o Brasil, pendente ou erro não viram dados", () => {
    expect(normalizarProjecao({ at: "x" }).situacao).toBe("erro");
    expect(normalizarProjecao({ pendente: true }).situacao).toBe("pendente");
    expect(normalizarProjecao({ erro: "banco ocupado" })).toEqual({ situacao: "erro", mensagem: "banco ocupado" });
  });
});

describe("tela projecao", () => {
  test("rota, catálogo, atalho Shift+J e playlist logo depois do presidente", () => {
    expect(ROTAS_2T).toContain("projecao");
    expect(pedidoDaRota("projecao")).toEqual({ caminho: "/api/2t/projecao", params: {} });
    expect(TELAS_2T.find(t => t.id === "projecao")?.atalho).toBe("Shift+J");
    expect(TECLA_TELA_2T.j).toBe("projecao");
    const pl = JSON.parse(readFileSync(new URL("../../public/playlist-2t.json", import.meta.url), "utf8")) as { itens: { view: string; dwell?: number }[] };
    const i = pl.itens.findIndex(x => x.view === "pres");
    expect(pl.itens[i + 1]).toEqual({ view: "projecao", dwell: 24 });
  });

  test("UFs que mais oscilaram: módulo decrescente, só com oscilação medida, no máximo seis", () => {
    const u = (sigla: string, swing: number | null): BlocoProjecao =>
      ({ sigla, nome: sigla, pst: 1, pct_vv_observado: 1, p1_f: 50, observado: { f: 1, l: 1, p_f: 50 }, projetado: null, swing_pp: swing }) as BlocoProjecao;
    const top = ufsQueMaisOscilaram([u("SP", 1), u("MG", -4), u("RJ", null), u("BA", 2), u("PE", 0.5), u("RS", -3), u("PR", 0.1), u("SC", 0.2)]);
    expect(top.map(x => x.sigla)).toEqual(["MG", "RS", "BA", "SP", "PE", "SC"]);
  });

  test("domínio do gráfico: 40 a 60 quando cabe; simétrico em torno de 50 quando não cabe", () => {
    const p = (proj: number | null, obs: number | null): PontoProjecao => ({ min: 0, proj, a: proj, b: proj, obs, pst: 10 });
    expect(dominioProjecao([])).toEqual([40, 60]);
    expect(dominioProjecao([p(52, 53)])).toEqual([40, 60]);
    expect(dominioProjecao([p(63, 52)])).toEqual([35, 65]);
  });
});

describe("mock da projeção", () => {
  const mockEm = (min: number) => criarMock({ speed: 1, turno: 2, inicioMin: min, agoraReal: () => 0 });

  test("sem projeção antes de 1% das seções; depois, faixa que contém o ponto e estreita com o andamento", async () => {
    const cedo = (await mockEm(2).doisT("projecao")) as { situacao: string; dados?: Projecao };
    expect(cedo.situacao).toBe("ok");
    expect(cedo.dados?.cobertura.pst).toBeLessThan(1);
    expect(cedo.dados?.brasil.projetado).toBeNull();
    expect(cedo.dados?.motivo_sem_projecao).toContain("1%");

    const meio = (await mockEm(60).doisT("projecao")) as { dados?: Projecao };
    const tarde = (await mockEm(180).doisT("projecao")) as { dados?: Projecao };
    const pm = meio.dados?.brasil.projetado;
    const pt = tarde.dados?.brasil.projetado;
    expect(pm && pt).toBeTruthy();
    if (!pm || !pt) return;
    expect(pm.faixa90[0]).toBeLessThanOrEqual(pm.p_f);
    expect(pm.faixa90[1]).toBeGreaterThanOrEqual(pm.p_f);
    expect(pt.faixa90[1] - pt.faixa90[0]).toBeLessThan(pm.faixa90[1] - pm.faixa90[0]);
    const serie = tarde.dados?.serie ?? [];
    expect(serie.length).toBeGreaterThan(10);
    for (let i = 1; i < serie.length; i++) expect((serie[i]?.min ?? 0) > (serie[i - 1]?.min ?? 0)).toBe(true);
    expect(tarde.dados?.rotulo).toBe(ROTULO_PROJECAO);
  });
});
