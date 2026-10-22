// Contrato de /api/2t/pausas: pausa em curso e encerrada, soma das UFs contra o nacional,
// `at` de replay e a referência fixa do 1º turno.
import { afterAll, beforeAll, describe, expect, test } from "bun:test";
import { rmSync } from "node:fs";
import { join } from "node:path";
import { abrirEscrita, fecharEscrita } from "../src/db/abrir.ts";
import { Escritor } from "../src/db/escrita.ts";
import { criarServidor } from "../src/server/main.ts";
import type { Servidor } from "../src/server/main.ts";
import type { VersaoTeste } from "./helpers-2t.ts";
import { PausasSchema, semearVersoes, tmp } from "./helpers-2t.ts";

const T0 = Date.parse("2026-10-25T20:00:00.000Z");
const m = (min: number): string => new Date(T0 + min * 60_000).toISOString();

let dir: string;
let srv: Servidor;

beforeAll(() => {
  dir = tmp("pausas-api-");
  const path = join(dir, "t.sqlite");
  const db = abrirEscrita(path);
  const v: VersaoTeste[] = [];
  for (let i = 1; i <= 20; i++) {
    for (const uf of ["sp", "mg"]) v.push({ nivel: "uf", uf, gerado: m(i), st: i * 10, ts: 1000 });
    if (i <= 5) v.push({ nivel: "uf", uf: "ba", gerado: m(i), st: i * 10, ts: 1000 });
    if (i <= 4) v.push({ nivel: "br", gerado: m(i), st: i * 20, ts: 3000 });
  }
  v.push({ nivel: "br", gerado: m(15), st: 300, ts: 3000 });
  semearVersoes(db, 6258, v);
  new Escritor(db).gravarLote([
    { k: "pausa", row: { nivel: "nacional", uf: null, de: m(4), ate: m(15), minutos: 11, st_antes: 80, st_depois: 300, detectado_em: m(9.5) } },
    { k: "pausa", row: { nivel: "uf", uf: "ba", de: m(5), ate: null, minutos: null, st_antes: 50, st_depois: null, detectado_em: m(15.5) } },
    { k: "pausa", row: { nivel: "geral", uf: null, de: m(10), ate: m(16), minutos: 6, st_antes: 300, st_depois: 330, detectado_em: m(16) } },
    { k: "pausa", row: { nivel: "geral", uf: null, de: m(16.5), ate: m(18.5), minutos: 2, st_antes: 400, st_depois: 410, detectado_em: m(18) } },
    { k: "meta", chave: "turno2_config", valor: JSON.stringify({ pausas: { limiar_min: 5, limiar_uf_min: 10 } }) },
  ]);
  fecharEscrita(db);
  srv = criarServidor({ dbPath: path, port: 0, log: false, agora: () => m(20) });
});

afterAll(async () => {
  await srv.parar();
  rmSync(dir, { recursive: true, force: true });
});

const get = async (q = ""): Promise<ReturnType<typeof PausasSchema.parse>> => PausasSchema.parse(await (await fetch(`${srv.url}/api/2t/pausas${q}`)).json());

describe("/api/2t/pausas", () => {
  test("agora: nacional voltou, Bahia em pausa, soma das UFs à frente do nacional", async () => {
    const r = await get();
    expect(r.at).toBe(m(20));
    expect(r.min).toBe(20);
    expect(r.limiar_min).toBe(5);
    expect(r.nacional).toEqual({
      ultima_versao_em: m(15), idade_s: 300, st: 300, ts: 3000, em_pausa: false, pausa_atual: null,
      historico: [
        { de: m(4), ate: m(16), minutos: 12, st_antes: 80, st_depois: 330 },
        { de: m(16.5), ate: m(18.5), minutos: 2, st_antes: 400, st_depois: 410 },
      ],
    });
    expect(r.soma_ufs).toEqual({ st: 450, pst: 15, defasagem_secoes: 150, defasagem_min: 5 });
    expect(r.ufs.map((u) => [u.uf, u.em_pausa, u.st, u.idade_s, u.historico_n])).toEqual([
      ["BA", true, 50, 900, 0],
      ["MG", false, 200, 0, 0],
      ["SP", false, 200, 0, 0],
    ]);
    expect(r.referencia_1t).toEqual({ pausa_geral: { de: "19:32", ate: "20:02", minutos: 29.6 }, travamento_nacional: { de: "18:00", ate: "18:10" } });
  });

  test("at no meio da pausa nacional (replay)", async () => {
    const r = await get(`?at=${m(12)}`);
    expect(r.nacional).toMatchObject({ ultima_versao_em: m(4), st: 80, em_pausa: true, pausa_atual: { desde: m(4), minutos: 8 }, historico: [] });
    expect(r.ufs.find((u) => u.uf === "BA")?.em_pausa).toBe(false);
  });

  test("pausa geral entra no bloco nacional (o arquivo nacional também ficou sem versão)", async () => {
    // a 2ª pausa geral (16,5 a 18,5 min) foi detectada aos 18 min
    expect((await get(`?at=${m(17)}`)).nacional).toMatchObject({ em_pausa: false, historico: [{ de: m(4), ate: m(16), minutos: 12 }] });
    expect((await get(`?at=${m(18.2)}`)).nacional).toMatchObject({ em_pausa: true, pausa_atual: { desde: m(16.5), minutos: 1.7 } });
  });
});
