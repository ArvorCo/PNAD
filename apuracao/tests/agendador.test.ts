import { describe, expect, test } from "bun:test";
import { Agendador } from "../src/collector/agendador.ts";
import type { FileState } from "../src/collector/estado-arquivos.ts";
import { Limitador } from "../src/collector/limitador.ts";
import { chave, keyAb, keyU } from "../src/tse/urls.ts";
import type { FetchResult, Job } from "../src/types.ts";
import { arquivo, contar, montar, ok, resultado } from "./coletor-util.ts";
import type { Montagem } from "./coletor-util.ts";
import { json } from "./helpers.ts";

interface Chamada {
  chave: string;
  t: number;
  motivo: Job["motivo"];
  prioridade: Job["prioridade"];
}

type Resposta = (n: number) => FetchResult;

function cenario(respostas: Record<string, Resposta> = {}, conc = 32, limites = { g: 10_000, s: 10_000 }) {
  const m: Montagem = montar(":memory:", { concurrency: conc });
  const t0 = m.relogio.agora();
  const chamadas: Chamada[] = [];
  const contagem = new Map<string, number>();
  const limitador = new Limitador(m.relogio, { global: { taxa: limites.g, rajada: limites.g }, sweep: { taxa: limites.s, rajada: limites.s } });
  const ag = new Agendador({
    relogio: m.relogio, ctx: m.ctx, limitador,
    fetcher: (job: Job, fs: FileState) => {
      const n = (contagem.get(fs.chave) ?? 0) + 1;
      contagem.set(fs.chave, n);
      chamadas.push({ chave: fs.chave, t: m.relogio.agora() - t0, motivo: job.motivo, prioridade: job.prioridade });
      const r = respostas[fs.chave];
      return Promise.resolve(r ? r(n) : resultado("nao_modificado"));
    },
  });
  const drenar = async (): Promise<void> => {
    for (let i = 0; i < 1000; i++) {
      const n = ag.passo();
      await ag.esperarVoo();
      if (n === 0) break;
    }
  };
  /** avança o relógio de 1 s em 1 s até t (ms desde o início), drenando a cada passo */
  const ate = async (t: number, passo = 1000): Promise<void> => {
    while (m.relogio.agora() - t0 < t) {
      m.relogio.avancar(Math.min(passo, t - (m.relogio.agora() - t0)));
      await drenar();
    }
  };
  const vezes = (ch: string): number[] => chamadas.filter((c) => c.chave === ch).map((c) => c.t);
  return { m, ag, limitador, chamadas, drenar, ate, vezes };
}

const AB_BR = chave(keyAb(6257, "br"));
const AB_SP = chave(keyAb(6257, "sp"));
const U_BR = chave(keyU(6257, 1, "br"));
const MU_SP = chave(keyU(6257, 1, "mu", "sp", "71072"));
const Z1 = chave(keyU(6257, 1, "zona", "sp", "71072", "0001"));

type Ab = { idg: string; abr: { cdabr: string; dt: string; ht: string; s: { st: string; ts: string } }[] };

/** -ab de SP com o município 71072 alterado conforme a versão (0 = fixture). */
function abSp(versao: number, final = false): FetchResult {
  const j = json("sp-e006257-ab.json") as Ab;
  j.idg = String(Number(j.idg) + versao);
  const e = j.abr.find((x) => x.cdabr === "71072");
  if (e && versao > 0) {
    e.dt = "04/10/2026";
    e.ht = `17:0${versao}:00`;
    e.s.st = final ? e.s.ts : String(versao * 10);
  }
  return ok(JSON.stringify(j));
}

describe("agendador", () => {
  test("cadências de T0 e T1", async () => {
    const c = cenario();
    c.ag.semear();
    await c.drenar();
    await c.ate(60_000);
    expect(c.vezes(AB_BR)).toEqual([0, 20_000, 40_000, 60_000]);
    expect(c.vezes(U_BR)).toEqual([0, 30_000, 60_000]);
    expect(c.vezes(AB_SP)).toEqual([0, 60_000]);
    expect(c.vezes(MU_SP)).toEqual([]);
  });

  test("mudança no -ab agenda T2 e T3 com intervalo mínimo; final fura o intervalo", async () => {
    const versoes = [abSp(0), abSp(1), abSp(2), abSp(2), abSp(3, true)];
    const c = cenario({ [AB_SP]: (n) => versoes[Math.min(n, versoes.length) - 1] as FetchResult });
    c.m.estado.capitais.add("71072");
    c.ag.semear();
    await c.drenar();
    expect(c.vezes(MU_SP)).toEqual([]);
    await c.ate(60_000);
    expect(c.vezes(MU_SP)).toEqual([60_000]);
    expect(c.vezes(Z1)).toEqual([60_000]);
    await c.ate(170_000);
    expect(c.vezes(MU_SP)).toEqual([60_000]);
    await c.ate(180_000);
    expect(c.vezes(MU_SP)).toEqual([60_000, 180_000]);
    expect(c.vezes(Z1)).toEqual([60_000]);
    await c.ate(240_000);
    expect(c.vezes(MU_SP)).toEqual([60_000, 180_000, 240_000]);
    expect(c.vezes(Z1)).toEqual([60_000, 240_000]);
    expect(c.chamadas.filter((x) => x.chave === MU_SP).at(-1)?.motivo).toBe("final");
    expect(arquivo(c.m, Z1).finalAgendado).toBe(true);
    c.m.lote.gravar();
    expect(contar(c.m, "SELECT COUNT(*) AS n FROM evento WHERE tipo = 'municipio_finalizado'")).toBe(1);
  });

  test("varredura cede a prioridade maior e respeita o balde de 40/s", async () => {
    const c = cenario({}, 1, { g: 1000, s: 40 });
    c.ag.varredura.iniciar(c.m.relogio.agora());
    c.ag.semear();
    await c.drenar();
    const primeiraVarredura = c.chamadas.findIndex((x) => x.prioridade === "sweep");
    expect(primeiraVarredura).toBeGreaterThan(0);
    expect(c.chamadas.slice(primeiraVarredura).every((x) => x.prioridade === "sweep")).toBe(true);
    expect(c.chamadas.length - primeiraVarredura).toBe(40);
  });

  test("404 desativa e re-sonda em 10 min na primeira hora após 17h", async () => {
    const c = cenario({ [Z1]: () => resultado("nao_existe") });
    const z = arquivo(c.m, Z1);
    c.ag.fila.agendar({ arquivoId: z.id, chave: z.chave, url: z.url, prioridade: "gatilho", due: c.m.relogio.agora(), motivo: "gatilho_ab" });
    await c.drenar();
    expect(z.ativo).toBe(false);
    await c.ate(600_000, 10_000);
    expect(c.vezes(Z1)).toEqual([0, 600_000]);
    expect(c.chamadas.filter((x) => x.chave === Z1).at(-1)?.motivo).toBe("probe");
  });

  test("403 pausa com escalada e corta a concorrência pela metade", async () => {
    let negar = true;
    const c = cenario({ [AB_BR]: () => (negar ? resultado("negado") : resultado("nao_modificado")) });
    c.ag.semear();
    await c.drenar();
    expect(c.limitador.pausado()).toBe(true);
    expect(c.ag.concorrencia).toBe(16);
    const n = c.chamadas.length;
    await c.ate(29_000);
    expect(c.chamadas.length).toBe(n);
    await c.ate(30_000);
    expect(c.vezes(AB_BR)).toEqual([0, 30_000]);
    expect(c.ag.concorrencia).toBe(8);
    await c.ate(89_000);
    expect(c.vezes(AB_BR)).toEqual([0, 30_000]);
    negar = false;
    await c.ate(90_000);
    expect(c.vezes(AB_BR)).toEqual([0, 30_000, 90_000]);
    await c.ate(700_000, 20_000);
    expect(c.ag.concorrencia).toBe(32);
    c.m.lote.gravar();
    expect(contar(c.m, "SELECT COUNT(*) AS n FROM evento WHERE tipo = 'pausa_global'")).toBe(2);
  });

  test("backoff por arquivo 5 s × 2^n com evento no 3º erro", async () => {
    const c = cenario({ [U_BR]: () => resultado("erro_servidor") });
    c.ag.semear();
    await c.drenar();
    await c.ate(36_000);
    expect(c.vezes(U_BR)).toEqual([0, 5_000, 15_000, 35_000]);
    c.m.lote.gravar();
    expect(contar(c.m, "SELECT COUNT(*) AS n FROM evento WHERE tipo = 'erros_seguidos'")).toBe(1);
    expect(arquivo(c.m, U_BR).errosSeguidos).toBe(4);
  });
});
