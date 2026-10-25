// Contrato de /api/2t/secoes: totais, cadeia de tempos por UF e no Brasil, seções tardias,
// últimas recebidas, régua do 1º turno e `at`.
import { afterAll, beforeAll, describe, expect, test } from "bun:test";
import { rmSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { abrirEscrita, fecharEscrita } from "../src/db/abrir.ts";
import { Escritor } from "../src/db/escrita.ts";
import type { LinhaSecao2t } from "../src/db/escrita.ts";
import { criarServidor } from "../src/server/main.ts";
import type { Servidor } from "../src/server/main.ts";
import { SecoesSchema, semearVersoes, tmp } from "./helpers-2t.ts";

const T0 = Date.parse("2026-10-25T20:00:00.000Z");
const m = (min: number): string => new Date(T0 + min * 60_000).toISOString();

function linha(uf: string, mun: string, secao: number, enc: number | null, rec: number | null, tot: number | null = null): LinhaSecao2t {
  const recebida = enc !== null && rec !== null;
  return {
    uf, mun, zona: 1, secao, origem: "amostra", status_aux: recebida ? "Totalizada" : "aux_404", hash: null, bu_nome: null, dr_hr: null,
    encerramento_local: null, encerramento_iso: enc === null ? null : m(enc), emissao_iso: enc === null ? null : m(enc + 2), recebido_iso: rec === null ? null : m(rec),
    bu_sha256: recebida ? "f".repeat(64) : null, aptos: null, comparecimento: null, votos_json: null, totalizado_mun_iso: tot === null ? null : m(tot),
    lag_encerr_recebimento_min: recebida ? rec - enc : null, lag_encerr_emissao_min: recebida ? 2 : null,
    lag_recebimento_totalizacao_min: tot === null || rec === null ? null : tot - rec, erro: null,
    tentativas: 1, atualizado_em: m(200), hab_biometria: null, hab_ano_nascimento: null, comp_sem_biometria: null, tipo_arquivo: null,
    tipo_urna: null, n_cargas: null, abertura_iso: null,
  };
}

let dir: string;
let srv: Servidor;
const antes = process.env.APURACAO_REFERENCIA_1T;

beforeAll(() => {
  dir = tmp("secoes2t-api-");
  const ref = join(dir, "ref.json");
  writeFileSync(
    ref,
    JSON.stringify({
      meta: {}, curvas: { br: [], uf: {} }, marcos: { br: {}, uf: {} }, municipios: {}, abstencao_uf: {}, governador_1t: {},
      secoes_lag: {
        uf: { SP: { n: 10, encerramento_p50_hhmm: "17:03", encerramento_p90_hhmm: "17:28", lag_encerr_recebimento_min: { p50: 60, p90: 100, p99: 150 }, lag_encerr_emissao_min: { p50: 2, p90: 3 } } },
        municipio: {},
      },
    }),
  );
  process.env.APURACAO_REFERENCIA_1T = ref;
  const path = join(dir, "t.sqlite");
  const db = abrirEscrita(path);
  semearVersoes(db, 6258, [{ nivel: "br", gerado: m(0), st: 0, ts: 10 }]);
  new Escritor(db).gravarLote([
    { k: "municipio", rows: [{ cd: "71072", uf: "sp", ibge: "3550308", nome: "SÃO PAULO", capital: 1, eleitores: null, origem: "cm" }] },
    { k: "secao_2t", row: linha("sp", "71072", 1, 5, 65, 68) },
    { k: "secao_2t", row: linha("sp", "71072", 2, 90, 100, 101) },
    { k: "secao_2t", row: linha("sp", "71072", 3, 20, 50, 58) },
    { k: "secao_2t", row: linha("sp", "71072", 4, null, null) },
    { k: "secao_2t", row: linha("ac", "01066", 77, 1, 81) },
    { k: "meta", chave: "turno2_config", valor: JSON.stringify({ secoes: { nacional_por_uf: 150, estaduais_por_uf: 600, intervalo_s: 900 } }) },
  ]);
  fecharEscrita(db);
  srv = criarServidor({ dbPath: path, port: 0, log: false, agora: () => m(200) });
});

afterAll(async () => {
  await srv.parar();
  if (antes === undefined) delete process.env.APURACAO_REFERENCIA_1T;
  else process.env.APURACAO_REFERENCIA_1T = antes;
  rmSync(dir, { recursive: true, force: true });
});

const get = async (q = ""): Promise<ReturnType<typeof SecoesSchema.parse>> => SecoesSchema.parse(await (await fetch(`${srv.url}/api/2t/secoes${q}`)).json());

describe("/api/2t/secoes", () => {
  test("totais, blocos por UF e Brasil, tardias e últimas", async () => {
    const r = await get();
    expect(r.desenho).toEqual({ nacional_por_uf: 150, estaduais_por_uf: 600, inclui_paralela: true, intervalo_s: 900 });
    expect(r.totais).toEqual({ alvo: 5, recebidas: 4, pendentes: 1, tardias: 1 });
    const sp = r.por_uf.find((u) => u.uf === "SP");
    // encerramentos de SP aos 5, 20 e 90 min: p50 17:20, p90 18:30; 1 de 3 depois das 17:30
    expect(sp).toEqual({
      uf: "SP", alvo: 4, recebidas: 3, encerramento_p50_hhmm: "17:20", encerramento_p90_hhmm: "18:30", tarde_apos_1730_pct: 33.33,
      lag_encerr_recebimento_min: { p50: 30, p90: 60, p99: 60 }, lag_encerr_emissao_min: { p50: 2, p90: 2 },
      lag_recebimento_totalizacao_min: { p50: 3, p90: 8, p99: 8 },
      ref_1t: { lag_p50: 60, lag_p90: 100, enc_p90_hhmm: "17:28" },
    });
    expect(r.por_uf.find((u) => u.uf === "AC")).toMatchObject({ ref_1t: null, lag_recebimento_totalizacao_min: { p50: null, p90: null, p99: null } });
    expect(r.brasil).toMatchObject({ alvo: 5, recebidas: 4, lag_encerr_recebimento_min: { p50: 30, p90: 80, p99: 80 }, ref_1t: null });
    expect(r.tardias).toEqual([{ uf: "SP", mun: "71072", nm: "SÃO PAULO", zona: 1, secao: 2, encerramento_hhmm: "18:30", recebido_hhmm: "18:40", lag_min: 10 }]);
    expect(r.ultimas.map((u) => [u.uf, u.secao, u.recebido_em])).toEqual([["SP", 2, m(100)], ["AC", 77, m(81)], ["SP", 1, m(65)], ["SP", 3, m(50)]]);
  });

  test("at: só o que o TSE tinha recebido até o instante", async () => {
    const r = await get(`?at=${m(70)}`);
    expect(r.totais).toEqual({ alvo: 5, recebidas: 2, pendentes: 3, tardias: 0 });
    // totalizações aos 58 e 68 min; a de 101 ainda não tinha acontecido
    expect(r.por_uf.find((u) => u.uf === "SP")?.lag_recebimento_totalizacao_min).toEqual({ p50: 3, p90: 8, p99: 8 });
    expect(r.min).toBe(70);
  });
});
