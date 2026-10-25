// Contrato de /api/2t/comparecimento: sinais por seção contra a própria seção no 1º turno,
// contingência, votos da prorrogação (n mínimo), camada municipal (pst ≥ 30%) e `at`.
import { afterAll, beforeAll, describe, expect, test } from "bun:test";
import { rmSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { abrirEscrita, fecharEscrita } from "../src/db/abrir.ts";
import { Escritor } from "../src/db/escrita.ts";
import type { LinhaSecao2t } from "../src/db/escrita.ts";
import { ROTULO_COMPARECIMENTO } from "../src/secoes2t/comparecimento-tipos.ts";
import { criarServidor } from "../src/server/main.ts";
import type { Servidor } from "../src/server/main.ts";
import { ComparecimentoSchema } from "./api-schemas-2t.ts";
import { semearVersoes, tmp } from "./helpers-2t.ts";

const T0 = Date.parse("2026-10-25T20:00:00.000Z");
const m = (min: number): string => new Date(T0 + min * 60_000).toISOString();

interface Extra {
  aptos: number;
  comp: number;
  enc: number;
  rec: number;
  semBio?: number;
  anoNasc?: number;
  tipoArquivo?: number;
  tipoUrna?: number;
  nCargas?: number;
  fl?: [number, number];
}

function linha(uf: string, mun: string, zona: number, secao: number, e: Extra | null): LinhaSecao2t {
  const votos =
    e?.fl === undefined
      ? null
      : JSON.stringify({ comparecimento: e.comp, eleicoes: { "6258": { aptos: e.aptos, cargos: { "1": { nominais: { "22": e.fl[0], "13": e.fl[1] }, legenda: {}, branco: 0, nulo: 0, comparecimento: e.comp } } } } });
  return {
    uf, mun, zona, secao, origem: "amostra", status_aux: e ? "Totalizada" : "aux_404", hash: null, bu_nome: null, dr_hr: null, encerramento_local: null,
    encerramento_iso: e ? m(e.enc) : null, emissao_iso: null, recebido_iso: e ? m(e.rec) : null, bu_sha256: e ? "f".repeat(64) : null,
    aptos: e?.aptos ?? null, comparecimento: e?.comp ?? null, votos_json: votos, totalizado_mun_iso: null, lag_encerr_recebimento_min: null,
    lag_encerr_emissao_min: null, lag_recebimento_totalizacao_min: null, erro: null, tentativas: 1, atualizado_em: m(300),
    hab_biometria: null, hab_ano_nascimento: e?.anoNasc ?? null, comp_sem_biometria: e?.semBio ?? null, tipo_arquivo: e?.tipoArquivo ?? 1,
    tipo_urna: e?.tipoUrna ?? 1, n_cargas: e?.nCargas ?? 1, abertura_iso: null,
  };
}

let dir: string;
let srv: Servidor;
const antes = { r: process.env.APURACAO_REFERENCIA_1T, s: process.env.APURACAO_REFERENCIA_1T_SECOES };

beforeAll(() => {
  dir = tmp("comparecimento2t-api-");
  const ref = join(dir, "ref.json");
  writeFileSync(
    ref,
    JSON.stringify({
      meta: {}, curvas: { br: [], uf: {} }, marcos: { br: {}, uf: {} }, abstencao_uf: {}, governador_1t: {}, secoes_lag: { uf: {}, municipio: {} },
      municipios: {
        SP: {
          "71072": { te: 1000, st: 10, comparecimento: 750, abstencao: 250, pa: 25, fechou_min: 60, apareceu_min: 5 },
          "62919": { te: 500, st: 10, comparecimento: 400, abstencao: 100, pa: 20, fechou_min: 60, apareceu_min: 5 },
        },
      },
    }),
  );
  const refSecoes = join(dir, "ref_secoes.json");
  writeFileSync(
    refSecoes,
    JSON.stringify({
      meta: { gerado_em: "2026-10-25T21:00:00.000Z", campos_secao: [], n_secoes: 2, enc_1t_pct: { apos_1700: 92.38, apos_1800: 8.42, apos_1900: 1.63 } },
      locais: [[-46.63, -23.55]],
      // [secao, aptos1, comp1, sem_bio1, ano_nasc1, enc1_min, local, fl1, lu1]
      secoes: { sp: { "71072": { "1": [[1, 300, 240, 5, 4, 3, 0, 120, 100], [2, 300, 240, 5, 4, 3, 0, 100, 100]] } } },
      municipios: { sp: { "71072": { n: 2, comp_p50: 80, comp_p90: 80, sem_bio_p50: 2, sem_bio_p90: 3, lon: -46.63, lat: -23.55 } } },
    }),
  );
  process.env.APURACAO_REFERENCIA_1T = ref;
  process.env.APURACAO_REFERENCIA_1T_SECOES = refSecoes;
  const path = join(dir, "t.sqlite");
  const db = abrirEscrita(path);
  semearVersoes(db, 6258, [
    { nivel: "br", gerado: m(0), st: 0, ts: 10 },
    { nivel: "mu", uf: "sp", mun: "71072", gerado: m(30), st: 5, ts: 10 },
    { nivel: "mu", uf: "sp", mun: "62919", gerado: m(30), st: 1, ts: 10 },
  ]);
  db.run("UPDATE totais SET comparecimento = 800, abstencao = 200, te = 1000 WHERE st = 5");
  db.run("UPDATE totais SET comparecimento = 90, abstencao = 10, te = 500 WHERE st = 1");
  new Escritor(db).gravarLote([
    { k: "municipio", rows: [{ cd: "71072", uf: "sp", ibge: "3550308", nome: "SÃO PAULO", capital: 1, eleitores: null, origem: "cm" }] },
    // +10 pp, 11,1% sem biometria (5× a mediana), encerrada 17:30: escore 3
    { k: "secao_2t", row: linha("sp", "71072", 1, 1, { aptos: 300, comp: 270, enc: 30, rec: 40, semBio: 30, anoNasc: 30, fl: [150, 100] }) },
    // encerrada antes das 17:00, BU de cédula, urna de contingência: escore 1
    { k: "secao_2t", row: linha("sp", "71072", 1, 2, { aptos: 300, comp: 240, enc: -2, rec: 10, tipoArquivo: 4, tipoUrna: 3, fl: [100, 120] }) },
    // sem régua, depois das 19:00, duas cargas
    { k: "secao_2t", row: linha("sp", "71072", 1, 9, { aptos: 200, comp: 150, enc: 130, rec: 140, nCargas: 2, fl: [80, 60] }) },
    // 17:00:30 conta como 17:00 (pontual)
    { k: "secao_2t", row: linha("ac", "01066", 1, 77, { aptos: 100, comp: 70, enc: 0.5, rec: 20 }) },
    { k: "secao_2t", row: linha("sp", "71072", 1, 4, null) },
  ]);
  fecharEscrita(db);
  srv = criarServidor({ dbPath: path, port: 0, log: false, agora: () => m(200) });
});

afterAll(async () => {
  await srv.parar();
  for (const [k, v] of [["APURACAO_REFERENCIA_1T", antes.r], ["APURACAO_REFERENCIA_1T_SECOES", antes.s]] as const) {
    if (v === undefined) delete process.env[k];
    else process.env[k] = v;
  }
  rmSync(dir, { recursive: true, force: true });
});

const get = async (q = ""): Promise<ReturnType<typeof ComparecimentoSchema.parse>> =>
  ComparecimentoSchema.parse(await (await fetch(`${srv.url}/api/2t/comparecimento${q}`)).json());

describe("/api/2t/comparecimento", () => {
  test("sinais, escore, contingência e rótulo", async () => {
    const r = await get();
    expect(r.rotulo).toBe(ROTULO_COMPARECIMENTO);
    expect(r.totais).toEqual({ recebidas: 4, com_ref_1t: 2, com_coord: 2, amostra: 4, paralela: 0 });
    expect(r.sinais).toEqual({ delta: 1, sem_bio: 1, tarde: 2, apos_19h: 1, papel: 1, contingencia: 2, escore_2_mais: 1 });
    const s1 = r.top[0];
    expect(s1).toMatchObject({
      uf: "SP", nm: "SÃO PAULO", secao: 1, taxa_comp: 90, taxa_comp_1t: 80, delta_pp: 10, sem_bio_pct: 11.11, sem_bio_mun_p50_1t: 2, ano_nasc_pct: 11.11,
      encerramento_hhmm: "17:30", encerrou_apos_17h: true, apos_19h: false, papel: false, contingencia: false, fatia_flavio: 60, fatia_flavio_1t: 54.55,
      escore: 3, lon: -46.63, lat: -23.55,
    });
    expect(r.contingencia.map((s) => s.secao).sort()).toEqual([2, 9]);
    const s2 = r.top.find((s) => s.secao === 2);
    expect(s2).toMatchObject({ papel: true, contingencia: true, encerramento_hhmm: "16:58", encerrou_apos_17h: false, escore: 1 });
    expect(r.top.find((s) => s.secao === 77)).toMatchObject({ encerramento_hhmm: "17:00", encerrou_apos_17h: false, delta_pp: null });
    expect(r.delta).toEqual({ n: 2, p50: 0, p90: 10 });
    expect(r.pontos).toHaveLength(2);
    expect(r.referencia.enc_1t_pct.apos_1900).toBe(1.63);
  });

  test("votos da prorrogação: n ao lado, delta de fatia só com n ≥ 20", async () => {
    const { prorrogacao: p } = await get();
    expect(p.n_min).toBe(20);
    expect(p.brasil).toMatchObject({
      uf: "BR", n_tardias: 2, n_apos_19h: 1, n_pontuais: 2, delta_comp_tardias: 10, delta_comp_pontuais: 0, n_vs_1t: 1, delta_fatia_vs_1t_pp: null,
      n_vs_pontuais: 2, delta_fatia_vs_pontuais_pp: null,
    });
    expect(p.por_uf.map((b) => b.uf)).toEqual(["AC", "SP"]);
  });

  test("camada municipal: só pst ≥ 30%, taxa contra 100 − pa do 1º turno", async () => {
    const r = await get();
    expect(r.municipios).toEqual([{ uf: "SP", cd: "71072", nm: "São Paulo", lat: -23.55, lon: -46.63, te: 1000, pst: 50, taxa_2t: 80, taxa_1t: 75, delta_pp: 5 }]);
    expect(r.municipios_top.map((x) => x.cd)).toEqual(["71072"]);
    expect(r.municipios_uf).toEqual([{ uf: "SP", n: 1, delta: { n: 1, p50: 5, p90: 5 } }]);
  });

  test("at: só as seções recebidas até o instante", async () => {
    const r = await get(`?at=${encodeURIComponent(m(25))}`);
    expect(r.totais.recebidas).toBe(2);
    expect(r.municipios).toEqual([]);
  });
});
