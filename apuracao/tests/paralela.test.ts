// Totalização paralela: conferência campo a campo (mesmas regras de
// ../scripts/totalizacao-conferir-tse.py), ponte com o Supabase falso, falha de rede sem
// derrubar nada e contrato da rota /api/2t/paralela.
import { afterAll, describe, expect, test } from "bun:test";
import { mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { RelogioFalso } from "../src/collector/relogio.ts";
import { abrirEscrita, fecharEscrita } from "../src/db/abrir.ts";
import { Escritor } from "../src/db/escrita.ts";
import type { ConfigParalela } from "../src/collector/turno2-config.ts";
import { cargosDoBu, comparar, qrComparavel, rotuloDiferenca } from "../src/paralela/conferir.ts";
import type { CargoPublico, VotoPublico } from "../src/paralela/conferir.ts";
import { PonteParalela, ROTULO_PARALELA } from "../src/paralela/ponte.ts";
import { ClienteSupabase } from "../src/paralela/supabase.ts";
import { buComparavel } from "../src/secoes2t/boletim.ts";
import { decodificarBu } from "../src/secoes2t/bu-decode.ts";
import { AmostraSecoes } from "../src/secoes2t/coletor.ts";
import type { Obter } from "../src/secoes2t/coletor.ts";
import { urlsUrna } from "../src/secoes2t/urls.ts";
import { criarServidor } from "../src/server/main.ts";
import { BU_FIXTURE, fixture2t, ParalelaSchema, supabaseFalso, tmp } from "./helpers-2t.ts";

const dirs: string[] = [];
afterAll(() => {
  for (const d of dirs) rmSync(d, { recursive: true, force: true });
});

const cargosFix = fixture2t("v_bu_cargo_publico.json") as CargoPublico[];
const votosFix = fixture2t("v_bu_voto_publico.json") as VotoPublico[];
const oficial = buComparavel(decodificarBu(new Uint8Array(readFileSync(BU_FIXTURE))).bu);
const qrDe = (id: number, votos: readonly VotoPublico[] = votosFix) =>
  qrComparavel(256, cargosDoBu(cargosFix.filter((c) => c.bu_id === id), votos.filter((v) => v.bu_id === id)));

describe("conferência campo a campo", () => {
  test("BU da paralela igual ao oficial: nenhuma diferença", () => {
    expect(comparar(qrDe(101), oficial)).toEqual([]);
  });

  test("voto trocado, legenda e cargo ausente aparecem como diferença", () => {
    const votos = votosFix.map((v) => (v.bu_id === 101 && v.cargo === 1 && v.candidato === "13" ? { ...v, votos: 120 } : v));
    const qr = qrDe(101, votos);
    delete qr.eleicoes["6259"]?.cargos["5"];
    const dif = comparar(qr, oficial);
    expect(dif).toEqual([
      { campo: "nominal", idel: 6257, cargo: 1, chave: "13", paralela: 120, tse: 121 },
      { campo: "cargo_ausente", idel: 6259, cargo: 5, chave: null, paralela: false, tse: true },
    ]);
    expect(dif.map(rotuloDiferenca)).toEqual(["presidente: votos no 13", "senador: cargo ausente"]);
  });

  test("ausente conta como zero (regra do script Python)", () => {
    const qr = qrDe(101);
    const c = qr.eleicoes["6257"]?.cargos["1"];
    if (!c) throw new Error("sem cargo");
    c.nominais["99"] = 0;
    expect(comparar(qr, oficial)).toEqual([]);
    expect(comparar({ ...qr, comparecimento: null }, { ...oficial, comparecimento: 0 })).toEqual([]);
  });
});

// ---------------------------------------------------------------- ponte

const CFG: ConfigParalela = { ativo: true, intervaloS: 60, url: "https://supabase.teste", chave: "chave-teste", janela: 2000 };

function montarPonte(dados: Record<string, unknown[]>, falhar: () => boolean = () => false) {
  const dir = tmp("paralela-");
  dirs.push(dir);
  const path = join(dir, "teste.sqlite");
  const db = abrirEscrita(path);
  const w = new Escritor(db);
  const relogio = new RelogioFalso(Date.parse("2026-10-04T21:00:00.000Z"));
  const urls = urlsUrna(3220);
  const bu = new Uint8Array(readFileSync(BU_FIXTURE));
  const aux = new TextEncoder().encode(JSON.stringify(fixture2t("aux-sp71072-z0001-s0001.json")));
  const obter: Obter = async (url) => {
    if (url === urls.aux({ uf: "sp", mun: "71072", zona: 1, secao: 1 })) return { status: 200, corpo: aux, retryAfter: null, erro: null };
    if (url.endsWith("/o03220sp7107200010001-bu.dat")) return { status: 200, corpo: bu, retryAfter: null, erro: null };
    return { status: 404, corpo: new TextEncoder().encode("<Code>NoSuchKey</Code>"), retryAfter: null, erro: "HTTP 404" };
  };
  const dirCs = join(dir, "cs");
  mkdirSync(dirCs);
  writeFileSync(join(dirCs, "vazio"), "");
  const amostra = new AmostraSecoes({
    cfg: { amostra: false, porUf: 0, estadual: 0, ufsEstaduais: [], intervaloS: 900, intervaloParalelaS: 300, rps: 1000, concorrencia: 2, semente: "t", inicioMs: 0, dirCs, timeoutMs: 1000 },
    pleito: 3220, eleFederal: 6257, t0Ms: Date.parse("2026-10-04T20:00:00.000Z"), db, gravar: (i) => w.gravarLote(i), relogio, urls, obter,
    dormir: (ms) => Bun.sleep(Math.min(ms, 5)),
  });
  const cliente = new ClienteSupabase({ url: CFG.url, chave: CFG.chave, fetchImpl: supabaseFalso(dados, falhar) });
  const ponte = new PonteParalela({ cfg: CFG, pleito: 3220, eleFederal: 6257, db, gravar: (i) => w.gravarLote(i), relogio, cliente, amostra });
  return { db, path, relogio, amostra, ponte };
}

const DADOS = (): Record<string, unknown[]> => ({
  v_bu_publico: fixture2t("v_bu_publico.json") as unknown[],
  v_bu_cargo_publico: cargosFix,
  v_bu_voto_publico: votosFix,
  v_estatisticas: fixture2t("v_estatisticas.json") as unknown[],
  v_cobertura_uf: fixture2t("v_cobertura_uf.json") as unknown[],
  v_conflito: [],
  v_totais_br: [],
  v_totais_uf: [],
});

async function buscar(amostra: AmostraSecoes): Promise<void> {
  const loop = amostra.rodar();
  const fim = Date.now() + 2000;
  while (amostra.estado({ uf: "sp", mun: "71072", zona: 1, secao: 1 })?.feito !== true) {
    if (Date.now() > fim) throw new Error("seção não foi buscada");
    await Bun.sleep(5);
  }
  await amostra.parar();
  await loop;
}

describe("ponte com o Supabase", () => {
  test("BUs novos entram, seção oficial é buscada com prioridade e conferida; teste fica fora do oficial", async () => {
    const { db, amostra, ponte } = montarPonte(DADOS());
    await amostra.preparar();
    const e1 = await ponte.ciclo();
    expect(e1.erro).toBeNull();
    expect(e1.estatisticas?.envios).toBe(5);
    expect(db.query("SELECT id, uf, mun, fase FROM paralela_bu ORDER BY id").all()).toEqual([
      { id: 101, uf: "sp", mun: "71072", fase: "O" },
      { id: 102, uf: "sp", mun: "71072", fase: "O" },
      { id: 103, uf: "ac", mun: "01066", fase: "S" },
    ]);
    expect(db.query("SELECT bu_id, situacao FROM paralela_conferencia ORDER BY bu_id").all()).toEqual([
      { bu_id: 101, situacao: "tse_ainda_nao_publicou" },
      { bu_id: 102, situacao: "tse_ainda_nao_publicou" },
      { bu_id: 103, situacao: "fora_do_oficial" },
    ]);
    expect(db.query("SELECT origem FROM secao_2t ORDER BY secao").all()).toEqual([{ origem: "paralela" }, { origem: "paralela" }]);
    await buscar(amostra);
    await ponte.ciclo();
    expect(db.query("SELECT situacao, tse_sha256 IS NOT NULL AS tem FROM paralela_conferencia WHERE bu_id = 101").get()).toEqual({ situacao: "igual", tem: 1 });
    const ev = db.query<{ tipo: string; severidade: string; detalhe: string }, []>("SELECT tipo, severidade, detalhe FROM evento WHERE tipo LIKE 'paralela%' OR tipo LIKE 'divergencia%'").all();
    expect(ev.map((e) => [e.tipo, e.severidade])).toEqual([["paralela_conferida", "info"]]);
    expect(JSON.parse(ev[0]?.detalhe ?? "{}")).toMatchObject({ conferidos: 1, iguais: 1, divergentes: 0, rotulo: ROTULO_PARALELA });
    // ciclo seguinte sem novidade não regrava nem repete evento
    const n = db.query<{ n: number }, []>("SELECT COUNT(*) AS n FROM evento").get()?.n;
    await ponte.ciclo();
    expect(db.query<{ n: number }, []>("SELECT COUNT(*) AS n FROM evento").get()?.n).toBe(n ?? -1);
  });

  test("divergência vira evento error com os campos", async () => {
    const dados = DADOS();
    dados.v_bu_voto_publico = votosFix.map((v) => (v.bu_id === 101 && v.cargo === 1 && v.candidato === "22" ? { ...v, votos: 99 } : v));
    const { db, amostra, ponte } = montarPonte(dados);
    await amostra.preparar();
    await ponte.ciclo();
    await buscar(amostra);
    await ponte.ciclo();
    const ev = db.query<{ tipo: string; severidade: string; nivel: string; uf: string; municipio_cd: string; zona_cd: string; detalhe: string }, []>(
      "SELECT tipo, severidade, nivel, uf, municipio_cd, zona_cd, detalhe FROM evento WHERE tipo = 'divergencia_paralela'",
    ).all();
    expect(ev).toHaveLength(1);
    expect(ev[0]).toMatchObject({ severidade: "error", nivel: "zona", uf: "sp", municipio_cd: "71072", zona_cd: "0001" });
    expect(JSON.parse(ev[0]?.detalhe ?? "{}")).toMatchObject({ secao: 1, bu_id: 101, campos: [{ campo: "presidente: votos no 22", paralela: 99, tse: 96 }] });
  });

  test("Supabase fora do ar: estado guarda o erro e os últimos dados; nada lança", async () => {
    let fora = false;
    const { ponte, amostra } = montarPonte(DADOS(), () => fora);
    await amostra.preparar();
    const ok = await ponte.ciclo();
    fora = true;
    const e = await ponte.ciclo();
    expect(e.erro).toContain("fetch failed");
    expect(e.atualizado_em).toBe(ok.atualizado_em);
    expect(e.cobertura_uf).toEqual(ok.cobertura_uf);
    expect(ponte.total).toBe(3);
  });

  test("leitura incremental: só ids novos (com janela para commit fora de ordem)", async () => {
    const dados = DADOS();
    const { ponte, amostra } = montarPonte(dados);
    await amostra.preparar();
    await ponte.ciclo();
    const bus = dados.v_bu_publico as { id: number }[];
    bus.push({ ...(bus[0] as { id: number }), id: 100 });
    (dados.v_bu_cargo_publico as { bu_id: number }[]).push({ ...(cargosFix[0] as CargoPublico), bu_id: 100 });
    await ponte.ciclo();
    expect(ponte.total).toBe(4);
  });
});

describe("/api/2t/paralela", () => {
  test("contrato, placar dos BUs com rótulo, conferência e Supabase fora do ar", async () => {
    let fora = false;
    const { path, amostra, ponte, db } = montarPonte(DADOS(), () => fora);
    await amostra.preparar();
    await ponte.ciclo();
    await buscar(amostra);
    fora = true;
    await ponte.ciclo();
    fecharEscrita(db);
    const srv = criarServidor({ dbPath: path, port: 0, log: false, agora: () => "2026-10-04T21:30:00.000Z" });
    try {
      const r = ParalelaSchema.parse(await (await fetch(`${srv.url}/api/2t/paralela`)).json());
      expect(r.erro).toContain("fetch failed");
      expect(r.atualizado_em).not.toBeNull();
      expect(r.recebidos).toEqual({ bus: 2, envios: 5, secoes: 2, ufs: 1, conflitos: 0 });
      expect(r.conferencia).toEqual({ iguais: 1, divergentes: 0, tse_ainda_nao_publicou: 1, erro: 0, fora_do_oficial: 1, pendentes: 0 });
      expect(r.placar_bus.rotulo).toBe("soma dos BUs recebidos, não projeção");
      expect(r.placar_bus.presidente).toEqual({
        votos: { 13: 221, 14: 7, 22: 186, 30: 3, 55: 13, 70: 4, 80: 1 }, comparecimento: 456, aptos: 662, brancos: 6, nulos: 15, secoes: 2,
      });
      expect(r.placar_bus.governador).toEqual({ SP: { votos: { 10: 124, 13: 115, 21: 1 }, secoes: 1 } });
      expect(r.cobertura_uf).toEqual([{ uf: "AC", bus: 0, secoes_total: 2411, pct: 0 }, { uf: "SP", bus: 2, secoes_total: 101234, pct: 0 }]);
      expect(r.ultimos.map((u) => [u.secao, u.situacao])).toEqual([[77, "fora_do_oficial"], [2, "tse_ainda_nao_publicou"], [1, "igual"]]);
      const cedo = ParalelaSchema.parse(await (await fetch(`${srv.url}/api/2t/paralela?at=2026-10-04T20:35:00.000Z`)).json());
      expect(cedo.recebidos.bus).toBe(1);
    } finally {
      await srv.parar();
    }
  });

  test("banco sem nada da paralela responde com erro preenchido, nunca vazio", async () => {
    const dir = tmp("paralela-vazio-");
    dirs.push(dir);
    const path = join(dir, "v.sqlite");
    fecharEscrita(abrirEscrita(path));
    const srv = criarServidor({ dbPath: path, port: 0, log: false });
    try {
      const r = ParalelaSchema.parse(await (await fetch(`${srv.url}/api/2t/paralela`)).json());
      expect(r.erro).toBe("totalização paralela ainda não consultada");
      expect(r.recebidos.bus).toBe(0);
    } finally {
      await srv.parar();
    }
  });
});
