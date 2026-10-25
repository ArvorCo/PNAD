// Telão do 2º turno, tela "comparecimento": normalizador de /api/2t/comparecimento, mock do ensaio
// (vazio no início, sinais raros, prorrogação com n mínimo), funções puras da tela e registro
// (catálogo, Shift+C, playlist depois da abstenção).
import { describe, expect, test } from "bun:test";
import { readFileSync } from "node:fs";
import { ROTULO_COMPARECIMENTO } from "../../src/secoes2t/comparecimento-tipos.ts";
import { TECLA_TELA_2T } from "../../src/ui/control/navegacao.ts";
import { normalizarComparecimento, pedidoDaRota, ROTAS_2T } from "../../src/ui/data/doist.ts";
import type { ComparecimentoOut } from "../../src/secoes2t/comparecimento-tipos.ts";
import { criarMock } from "../../src/ui/data/mock.ts";
import { camadaDe, ordemDesenho, raioMunicipio, raioSecao, textoFatia } from "../../src/ui/views/comparecimento.ts";
import { TELAS_2T } from "../../src/ui/views/meta-2t.ts";

const mockEm = (min: number) => criarMock({ speed: 1, turno: 2, inicioMin: min, agoraReal: () => 0 });

async function comparecimentoEm(min: number): Promise<ComparecimentoOut> {
  const r = await mockEm(min).doisT("comparecimento");
  if (r.situacao !== "ok") throw new Error(`mock sem dados: ${r.situacao}`);
  return r.dados;
}

describe("rota /api/2t/comparecimento no telão", () => {
  test("normalizador: corpo vazio, pendente e erro viram aviso; corpo mínimo vira zeros", () => {
    expect(normalizarComparecimento(null).situacao).toBe("erro");
    expect(normalizarComparecimento({ pendente: true }).situacao).toBe("pendente");
    expect(normalizarComparecimento({ erro: "banco ocupado" })).toEqual({ situacao: "erro", mensagem: "banco ocupado" });
    expect(normalizarComparecimento({ at: "x" }).situacao).toBe("erro");
    const r = normalizarComparecimento({ at: "x", sinais: {}, totais: {}, pontos: [[-47, -15, null, 2, 300, 1], [null, 1], "lixo"] });
    expect(r.situacao).toBe("ok");
    if (r.situacao !== "ok") return;
    expect(r.dados.rotulo).toBe(ROTULO_COMPARECIMENTO);
    expect(r.dados.totais.recebidas).toBe(0);
    expect(r.dados.pontos).toEqual([[-47, -15, null, 2, 300, 1]]);
    expect(r.dados.prorrogacao.n_min).toBe(20);
    expect(r.dados.prorrogacao.brasil.delta_fatia_vs_1t_pp).toBeNull();
  });

  test("mock: sem boletins no começo, depois seções com sinais e municípios com 30% apurado", async () => {
    const vazio = await comparecimentoEm(1);
    expect(vazio.totais.recebidas).toBe(0);
    expect(vazio.pontos).toHaveLength(0);
    const cheio = await comparecimentoEm(150);
    expect(cheio.totais.recebidas).toBeGreaterThan(250);
    expect(cheio.pontos).toHaveLength(cheio.totais.recebidas);
    expect(cheio.sinais.escore_2_mais).toBeGreaterThan(0);
    expect(cheio.sinais.contingencia).toBeGreaterThan(0);
    expect(cheio.top[0]?.escore).toBeGreaterThanOrEqual(cheio.top[cheio.top.length - 1]?.escore ?? 0);
    for (const s of cheio.top) expect(s.escore).toBe([s.sinais.delta, s.sinais.sem_bio, s.sinais.tardia, s.sinais.papel].filter(Boolean).length);
    expect(cheio.municipios.every(m => m.pst >= 30)).toBe(true);
    expect(cheio.municipios_top.every(m => m.delta_pp > 0)).toBe(true);
    const ns = cheio.prorrogacao.por_uf.map(u => u.n_tardias);
    expect(ns.some(n => n >= 20)).toBe(true);
    expect(cheio.prorrogacao.por_uf.filter(u => u.n_tardias < 20).every(u => u.delta_fatia_vs_1t_pp === null)).toBe(true);
  });
});

describe("tela comparecimento", () => {
  test("rota, catálogo, atalho Shift+C e playlist logo depois da abstenção", () => {
    expect(ROTAS_2T).toContain("comparecimento");
    expect(pedidoDaRota("comparecimento")).toEqual({ caminho: "/api/2t/comparecimento", params: {} });
    const t = TELAS_2T.find(x => x.id === "comparecimento");
    expect(t?.atalho).toBe("Shift+C");
    expect(`${t?.titulo ?? ""}${t?.rotulo ?? ""}${ROTULO_COMPARECIMENTO}`).not.toContain("—");
    expect(TECLA_TELA_2T.c).toBe("comparecimento");
    const pl = JSON.parse(readFileSync(new URL("../../public/playlist-2t.json", import.meta.url), "utf8")) as { itens: { view: string; dwell?: number }[] };
    const i = pl.itens.findIndex(x => x.view === "abstencao");
    expect(pl.itens[i + 1]).toEqual({ view: "comparecimento", dwell: 24 });
  });

  test("a tecla m alterna seções e municípios; raios crescem com aptos e eleitorado", () => {
    expect(camadaDe(0)).toBe("secoes");
    expect(camadaDe(1)).toBe("municipios");
    expect(camadaDe(2)).toBe("secoes");
    expect(raioSecao(400)).toBeGreaterThan(raioSecao(100));
    expect(raioSecao(1e6)).toBeLessThanOrEqual(8.5);
    expect(raioMunicipio(1_000_000)).toBeGreaterThan(raioMunicipio(10_000));
    expect(raioMunicipio(1e9)).toBe(20);
  });

  test("delta de fatia só com n mínimo, sempre com o n ao lado; alerta desenhado por cima", () => {
    expect(textoFatia(1.234, 25, 20)).toBe("+1,2 pp (n = 25)");
    expect(textoFatia(1.234, 19, 20)).toBe("n < 20 (n = 19)");
    expect(textoFatia(null, 40, 20)).toBe("sem dado (n = 40)");
    const o = ordemDesenho([[0, 0, 9, 3, 100, 0], [0, 0, 1, 0, 100, 0], [0, 0, 2, 0, 100, 1]]);
    expect(o.map(p => p[3])).toEqual([0, 0, 3]);
    expect(o[1]?.[5]).toBe(1);
  });
});
