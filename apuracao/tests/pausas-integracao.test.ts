// Integração no coletor: instalarTurno2 liga o observador de versões e a avaliação periódica no
// agendador; versões reais processadas pelo pipeline abrem e fecham a pausa nacional no banco.
import { describe, expect, test } from "bun:test";
import { Agendador } from "../src/collector/agendador.ts";
import type { Coletor } from "../src/collector/bootstrap.ts";
import { Limitador } from "../src/collector/limitador.ts";
import { processar } from "../src/collector/processar.ts";
import { instalarTurno2 } from "../src/collector/turno2.ts";
import { lerConfig } from "../src/config.ts";
import { chave, keyU } from "../src/tse/urls.ts";
import { arquivo, jobDe, montar, ok, resultado } from "./coletor-util.ts";
import { versaoU } from "./server-helpers.ts";

describe("motor do 2º turno dentro do coletor", () => {
  test("pausa nacional detectada pelo relógio de 30 s e encerrada pela versão nova", async () => {
    const m = montar();
    const config = { ...lerConfig({ APURACAO_ELEICOES: "6257" }), dbPath: ":memory:" };
    const c: Coletor = { config, db: m.ctx.db, escritor: m.lote.escritor, lote: m.lote, estado: m.estado, ctx: m.ctx, relogio: m.relogio, http: {} };
    const limitador = new Limitador(m.relogio);
    const ag = new Agendador({ relogio: m.relogio, ctx: m.ctx, limitador, fetcher: async () => resultado("nao_modificado") });
    const logs: Record<string, unknown>[] = [];
    const t2 = instalarTurno2(c, ag, limitador, (o) => logs.push(o), { APURACAO_SECOES: "0", APURACAO_PARALELA: "0", APURACAO_REFERENCIA_1T: "/nao/existe.json" });
    expect(t2.cfg.turno).toBe(1);
    expect(t2.amostra).toBeNull();
    expect(t2.ponte).toBeNull();

    const BR = chave(keyU(6257, 1, "br"));
    const SP = chave(keyU(6257, 1, "uf", "sp"));
    const versao = (ch: string, arq: string, st: number, idg: number): void => {
      const fs = arquivo(m, ch);
      const ger = m.relogio.agora() - 2000;
      processar(m.ctx, jobDe(fs), fs, ok(versaoU(arq, { st, votos: { 13: st, 22: st - 1 }, idg, ger })), m.relogio.agora());
    };
    versao(BR, "br-c0001-e006257-u.json", 100, 1);
    const semMudanca = (ch: string): void => {
      const fs = arquivo(m, ch);
      processar(m.ctx, jobDe(fs), fs, resultado("nao_modificado"), m.relogio.agora());
    };
    for (let i = 1; i <= 8; i++) {
      m.relogio.avancar(60_000);
      versao(SP, "sp-c0001-e006257-u.json", 100 * i, 10 + i);
      semMudanca(BR); // o coletor segue lendo o nacional (304): a pausa é do TSE, não nossa
      ag.passo();
    }
    m.lote.gravar();
    const pausas = m.ctx.db.query<{ nivel: string; ate: string | null }, []>("SELECT nivel, ate FROM pausa").all();
    expect(pausas).toEqual([{ nivel: "nacional", ate: null }]);
    expect(m.ctx.db.query<{ tipo: string }, []>("SELECT tipo FROM evento WHERE tipo LIKE 'pausa%'").all()).toEqual([{ tipo: "pausa_nacional_inicio" }]);

    m.relogio.avancar(10_000);
    versao(BR, "br-c0001-e006257-u.json", 900, 50);
    m.lote.gravar();
    expect(m.ctx.db.query<{ nivel: string; minutos: number }, []>("SELECT nivel, minutos FROM pausa WHERE ate IS NOT NULL").all()).toEqual([{ nivel: "nacional", minutos: 8.2 }]);
    expect(m.ctx.db.query<{ valor: string }, []>("SELECT valor FROM meta WHERE chave = 'turno2_config'").get()?.valor).toContain('"limiar_min":5');
    await t2.parar();
    expect(logs.some((l) => l.t === "aviso")).toBe(true);
  });
});
