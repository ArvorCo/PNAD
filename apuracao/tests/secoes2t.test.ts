// Amostra ao vivo de seções: desenho, quadro do -cs, horas da urna, coleta aux → BU com
// respostas falsas, pausa por 429 e pela pausa global do coletor, totalização do município.
import { afterAll, describe, expect, test } from "bun:test";
import { mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { RelogioFalso } from "../src/collector/relogio.ts";
import type { ConfigSecoes } from "../src/collector/turno2-config.ts";
import { abrirEscrita } from "../src/db/abrir.ts";
import { Escritor } from "../src/db/escrita.ts";
import type { LinhaSecao2t } from "../src/db/escrita.ts";
import { amostrarUf, desenharUf, gerador } from "../src/secoes2t/amostra.ts";
import { buComparavel, escolherHash, resumoBu } from "../src/secoes2t/boletim.ts";
import type { Aux } from "../src/secoes2t/boletim.ts";
import { decodificarBu } from "../src/secoes2t/bu-decode.ts";
import { AmostraSecoes, classeDe } from "../src/secoes2t/coletor.ts";
import type { Obter, RespostaHttp } from "../src/secoes2t/coletor.ts";
import { quadroDoCs } from "../src/secoes2t/cs.ts";
import type { Cs } from "../src/secoes2t/cs.ts";
import { urlsUrna } from "../src/secoes2t/urls.ts";
import type { SecaoChave } from "../src/secoes2t/urls.ts";
import { horaBrasiliaParaIso, horaLocalUrnaParaIso } from "../src/turno2/comum.ts";
import { BU_FIXTURE, fixture2t, semearAbMunicipio, semearVersoes, tmp } from "./helpers-2t.ts";

const dirs: string[] = [];
afterAll(() => {
  for (const d of dirs) rmSync(d, { recursive: true, force: true });
});

const sec = (mun: string, zona: number, secao: number, uf = "sp"): SecaoChave => ({ uf, mun, zona, secao });

describe("desenho da amostra", () => {
  const quadro = (tamanhos: Record<string, number>): SecaoChave[] =>
    Object.entries(tamanhos).flatMap(([mun, n]) => Array.from({ length: n }, (_, i) => sec(mun, 1, i + 1)));

  test("alocação proporcional ao município e tamanho exato", () => {
    const q = quadro({ "00001": 600, "00002": 300, "00003": 100 });
    const a = amostrarUf(q, 10, "s");
    expect(a).toHaveLength(10);
    const por = (mun: string): number => a.filter((s) => s.mun === mun).length;
    expect([por("00001"), por("00002"), por("00003")]).toEqual([6, 3, 1]);
    expect(new Set(a.map((s) => `${s.mun}|${s.secao}`)).size).toBe(10);
  });

  test("maiores restos e semente fixa: reprodutível, muda com a semente", () => {
    const q = quadro({ "00001": 5, "00002": 5, "00003": 5 });
    const a = amostrarUf(q, 4, "fixa");
    expect(a).toEqual(amostrarUf(q, 4, "fixa"));
    expect(a).toHaveLength(4);
    expect(JSON.stringify(amostrarUf(q, 4, "outra"))).not.toBe(JSON.stringify(a));
    expect(amostrarUf(q, 99, "x")).toHaveLength(15);
    expect(amostrarUf(q, 0, "x")).toEqual([]);
  });

  test("inclusão equiprovável: frequência de cada seção perto de n/N em 4.000 sorteios", () => {
    const q = quadro({ "00001": 7, "00002": 13, "00003": 30 });
    const cont = new Map<string, number>();
    for (let r = 0; r < 4000; r++) for (const s of amostrarUf(q, 10, `r${r}`)) cont.set(`${s.mun}|${s.secao}`, (cont.get(`${s.mun}|${s.secao}`) ?? 0) + 1);
    const p = [...cont.values()].map((c) => c / 4000);
    expect(cont.size).toBe(50);
    for (const x of p) expect(Math.abs(x - 0.2)).toBeLessThan(0.03); // cerca de 4,7 erros-padrão (0,0063)
  });

  test("UF com 2º turno estadual recebe o segundo sorteio; as outras não", () => {
    const q = quadro({ "00001": 300, "00002": 200 });
    const d = { porUf: 5, estadual: 20, ufsEstaduais: ["ac"], semente: "s" };
    expect(desenharUf("sp", q, d).size).toBe(5);
    const ac = desenharUf("ac", q.map((s) => ({ ...s, uf: "ac" })), d).size;
    expect(ac).toBeGreaterThanOrEqual(20);
    expect(ac).toBeLessThanOrEqual(25);
  });

  test("gerador em [0, 1) e determinístico", () => {
    const g = gerador("a");
    const v = Array.from({ length: 1000 }, () => g());
    expect(v.every((x) => x >= 0 && x < 1)).toBe(true);
    expect(gerador("a")()).toBe(v[0] as number);
  });

  test("quadro do -cs: agregada fora, município com 5 dígitos", () => {
    const cs: Cs = {
      abr: [{ cd: "ac", mu: [{ cd: "1066", nm: "PORTO WALTER", zon: [{ cd: "0004", sec: [{ ns: "0077" }, { ns: "0078", nsp: "0077" }, { ns: "0079", nsa: ["0080"] }] }] }] }],
    };
    const q = quadroDoCs(cs);
    expect(q.secoes).toEqual([sec("01066", 4, 77, "ac"), sec("01066", 4, 79, "ac")]);
    expect(q.agregadas).toBe(1);
    expect(q.nomes.get("01066")).toBe("PORTO WALTER");
  });
});

describe("horas da urna e do TSE", () => {
  test("hora local da urna para UTC: AC (-2 h), AM (-1 h), SP e Brasília", () => {
    expect(horaLocalUrnaParaIso("ac", "2026-10-25 15:00:00")).toBe("2026-10-25T20:00:00.000Z");
    expect(horaLocalUrnaParaIso("AM", "2026-10-25 16:00:00")).toBe("2026-10-25T20:00:00.000Z");
    expect(horaLocalUrnaParaIso("sp", "2026-10-25 17:00:00")).toBe("2026-10-25T20:00:00.000Z");
    expect(horaBrasiliaParaIso("2026-10-25 18:34:08")).toBe("2026-10-25T21:34:08.000Z");
    expect(horaLocalUrnaParaIso("ac", "25/10/2026 23:30:00")).toBe("2026-10-26T04:30:00.000Z");
  });

  test("BU real: encerramento e emissão convertidos pelo fuso; exterior sem conversão", () => {
    const bu = decodificarBu(new Uint8Array(readFileSync(BU_FIXTURE))).bu;
    const sp = resumoBu(bu, "sp", 6257);
    expect(sp).toMatchObject({ encerramentoLocal: "2026-10-04 17:08:42", encerramentoIso: "2026-10-04T20:08:42.000Z", emissaoIso: "2026-10-04T20:10:28.000Z", aptos: 362, comparecimento: 256 });
    expect(resumoBu(bu, "ac", 6257).encerramentoIso).toBe("2026-10-04T22:08:42.000Z");
    expect(resumoBu(bu, "am", 6257).encerramentoIso).toBe("2026-10-04T21:08:42.000Z");
    expect(resumoBu(bu, "zz", 6257)).toMatchObject({ encerramentoLocal: "2026-10-04 17:08:42", encerramentoIso: null, emissaoIso: null });
    const c = buComparavel(bu);
    expect(c.eleicoes["6257"]?.cargos["1"]).toEqual({ nominais: { 13: 121, 14: 7, 22: 96, 30: 3, 55: 13, 70: 4, 80: 1 }, legenda: {}, branco: 2, nulo: 9, comparecimento: 256 });
  });

  test("aux: hash mais recente com boletim, busa vale mais que bu", () => {
    const aux: Aux = {
      hashes: [
        { hash: "a", dr: "25/10/2026", hr: "18:00:00", arq: [{ nm: "x-bu.dat", tp: "bu" }] },
        { hash: "b", dr: "25/10/2026", hr: "18:30:00", arq: [{ nm: "x-bu.dat", tp: "bu" }, { nm: "x-busa.dat", tp: "busa" }] },
        { hash: "c", dr: "25/10/2026", hr: "19:00:00", arq: [{ nm: "x-log.jez", tp: "log" }] },
      ],
    };
    expect(escolherHash(aux)).toEqual({ hash: "b", st: null, drHr: "2026-10-25 18:30:00", bu: "x-busa.dat" });
    expect(escolherHash({})).toBeNull();
  });

  test("classe da resposta: JSON pelo classificador do coletor, binário pelo status", () => {
    const r = (status: number | null, texto: string): RespostaHttp => ({ status, corpo: new TextEncoder().encode(texto), retryAfter: null, erro: null });
    expect(classeDe(r(200, "{}"), true)).toBe("ok");
    expect(classeDe(r(404, "<Error><Code>NoSuchKey</Code></Error>"), true)).toBe("nao_existe");
    expect(classeDe(r(403, "Access Denied"), true)).toBe("negado");
    expect(classeDe(r(429, ""), true)).toBe("limite");
    expect(classeDe(r(200, "0\u0082binario"), false)).toBe("ok");
    expect(classeDe(r(200, "<html>Access Denied</html>"), false)).toBe("negado");
    expect(classeDe({ status: null, corpo: null, retryAfter: null, erro: "TimeoutError: x" }, true)).toBe("timeout");
  });
});

// ---------------------------------------------------------------- coleta com respostas falsas

const T1 = Date.parse("2026-10-04T20:00:00.000Z");

function cfgTeste(dirCs: string, extra: Partial<ConfigSecoes> = {}): ConfigSecoes {
  return {
    amostra: true, porUf: 3, estadual: 0, ufsEstaduais: [], intervaloS: 900, intervaloParalelaS: 300, rps: 1000, concorrencia: 2, semente: "t",
    inicioMs: 0, dirCs, timeoutMs: 1000, ...extra,
  };
}

function montarAmostra(extra: Partial<ConfigSecoes> = {}, respostas: (url: string) => RespostaHttp | null = () => null, pausaPrincipal = (): boolean => false) {
  const dir = tmp("secoes2t-");
  dirs.push(dir);
  const dirCs = join(dir, "cs");
  mkdirSync(dirCs, { recursive: true });
  const cs = { abr: [{ cd: "sp", mu: [{ cd: "71072", nm: "SÃO PAULO", zon: [{ cd: "0001", sec: [{ ns: "0001" }, { ns: "0002" }, { ns: "0003" }] }] }] }] };
  writeFileSync(join(dirCs, "sp-p003220-cs.json"), JSON.stringify(cs));
  const db = abrirEscrita(":memory:");
  const w = new Escritor(db);
  const relogio = new RelogioFalso(T1 + 3600_000);
  const urls = urlsUrna(3220);
  const bu = new Uint8Array(readFileSync(BU_FIXTURE));
  const auxOk = new TextEncoder().encode(JSON.stringify(fixture2t("aux-sp71072-z0001-s0001.json")));
  const pedidos: string[] = [];
  const obter: Obter = async (url) => {
    pedidos.push(url);
    const r = respostas(url);
    if (r) return r;
    if (url === urls.aux({ uf: "sp", mun: "71072", zona: 1, secao: 1 })) return { status: 200, corpo: auxOk, retryAfter: null, erro: null };
    if (url.endsWith("/6162/o03220sp7107200010001-bu.dat")) return { status: 200, corpo: bu, retryAfter: null, erro: null };
    return { status: 404, corpo: new TextEncoder().encode("<Error><Code>NoSuchKey</Code></Error>"), retryAfter: null, erro: "HTTP 404" };
  };
  const a = new AmostraSecoes({
    cfg: cfgTeste(dirCs, extra), pleito: 3220, eleFederal: 6257, t0Ms: T1 - 3600_000, db, gravar: (itens) => w.gravarLote(itens), relogio, urls, obter,
    pausaPrincipal, ufs: ["sp"], dormir: (ms) => Bun.sleep(Math.min(ms, 5)),
  });
  return { a, db, relogio, pedidos };
}

async function ate(cond: () => boolean, ms = 2000): Promise<void> {
  const fim = Date.now() + ms;
  while (!cond()) {
    if (Date.now() > fim) throw new Error("condição não chegou");
    await Bun.sleep(5);
  }
}

describe("coleta aux → BU", () => {
  test("seção com BU vira linha completa com lags e totalização do município; sem BU fica pendente", async () => {
    const { a, db, relogio, pedidos } = montarAmostra();
    semearAbMunicipio(db, 6257, "sp", "71072", [
      { gerado: "2026-10-04T20:30:00.000Z", totalizado: "2026-10-04T20:29:00.000Z", st: 10, ts: 100 },
      { gerado: "2026-10-04T20:35:00.000Z", totalizado: "2026-10-04T20:33:00.000Z", st: 20, ts: 100 },
    ]);
    await a.preparar();
    expect(db.query("SELECT COUNT(*) AS n FROM secao_2t WHERE origem = 'amostra'").get()).toEqual({ n: 3 });
    relogio.avancar(901_000);
    const loop = a.rodar();
    await ate(() => a.estado(sec("71072", 1, 1))?.feito === true && pedidos.length >= 4);
    await a.parar();
    await loop;
    const l = db.query<LinhaSecao2t, []>("SELECT * FROM secao_2t WHERE secao = 1").get();
    expect(l).toMatchObject({
      status_aux: "Totalizada", hash: "6162", bu_nome: "o03220sp7107200010001-bu.dat", dr_hr: "2026-10-04 17:31:05", recebido_iso: "2026-10-04T20:31:05.000Z",
      encerramento_local: "2026-10-04 17:08:42", encerramento_iso: "2026-10-04T20:08:42.000Z", emissao_iso: "2026-10-04T20:10:28.000Z", aptos: 362,
      comparecimento: 256, lag_encerr_recebimento_min: 22.4, lag_encerr_emissao_min: 1.8, totalizado_mun_iso: "2026-10-04T20:33:00.000Z",
      lag_recebimento_totalizacao_min: 1.9, erro: null,
    });
    expect(l?.bu_sha256).toMatch(/^[0-9a-f]{64}$/);
    expect(db.query<{ status_aux: string }, []>("SELECT status_aux FROM secao_2t WHERE secao <> 1").all().map((x) => x.status_aux)).toEqual(["aux_404", "aux_404"]);
    const tardia = db.query<{ tipo: string; detalhe: string }, []>("SELECT tipo, detalhe FROM evento WHERE tipo = 'secao_tardia'").all();
    expect(tardia).toHaveLength(1);
    expect(JSON.parse(tardia[0]?.detalhe ?? "{}")).toMatchObject({ secao: 1, encerramento_hhmm: "18:08" });
  });

  test("totalização do município: a primeira versão do arquivo mu (ou do -ab) depois do recebimento", async () => {
    const { a, db, relogio } = montarAmostra({ porUf: 1 });
    // mu de São Paulo: versão totalizada antes do recebimento (20:31:05) e outra às 20:32:10
    semearVersoes(db, 6257, [
      { nivel: "mu", uf: "sp", mun: "71072", gerado: "2026-10-04T20:30:30.000Z", totalizado: "2026-10-04T20:30:00.000Z", st: 5, ts: 100 },
      { nivel: "mu", uf: "sp", mun: "71072", gerado: "2026-10-04T20:32:40.000Z", totalizado: "2026-10-04T20:32:10.000Z", st: 9, ts: 100 },
    ]);
    semearAbMunicipio(db, 6257, "sp", "71072", [{ gerado: "2026-10-04T20:35:00.000Z", totalizado: "2026-10-04T20:33:00.000Z", st: 20, ts: 100 }]);
    await a.preparar();
    a.adicionarParalela(sec("71072", 1, 1));
    relogio.avancar(901_000);
    const loop = a.rodar();
    await ate(() => a.estado(sec("71072", 1, 1))?.feito === true);
    await a.parar();
    await loop;
    expect(db.query("SELECT totalizado_mun_iso, lag_recebimento_totalizacao_min FROM secao_2t WHERE secao = 1").get()).toEqual({
      totalizado_mun_iso: "2026-10-04T20:32:10.000Z", lag_recebimento_totalizacao_min: 1.1,
    });
  });

  test("retomada: amostra não é redesenhada e seção feita não volta à fila", async () => {
    const { a, db, relogio } = montarAmostra();
    await a.preparar();
    relogio.avancar(901_000);
    const loop = a.rodar();
    await ate(() => a.estado(sec("71072", 1, 1))?.feito === true);
    await a.parar();
    await loop;
    const pedidos: string[] = [];
    const b = new AmostraSecoes({
      cfg: cfgTeste("/nao/existe"), pleito: 3220, eleFederal: 6257, t0Ms: T1, db, gravar: () => undefined, relogio, ufs: ["sp"],
      obter: async (u) => {
        pedidos.push(u);
        return { status: 404, corpo: null, retryAfter: null, erro: null };
      },
    });
    await b.preparar();
    expect(b.estado(sec("71072", 1, 1))?.feito).toBe(true);
    expect(b.estado(sec("71072", 1, 1))?.votos?.eleicoes["6257"]?.aptos).toBe(362);
    expect(pedidos).toEqual([]);
  });

  test("429 pausa o balde próprio e grava o evento; seção volta depois", async () => {
    let n = 0;
    const { a, db, relogio, pedidos } = montarAmostra({ porUf: 1 }, (url) => (url.endsWith("-aux.json") && n++ === 0 ? { status: 429, corpo: new Uint8Array(), retryAfter: 120, erro: "HTTP 429" } : null));
    await a.preparar();
    relogio.avancar(901_000);
    const loop = a.rodar();
    await ate(() => db.query("SELECT 1 FROM evento WHERE tipo = 'secoes2t_pausa'").get() !== null);
    const antes = pedidos.length;
    await Bun.sleep(30);
    expect(pedidos.length).toBe(antes);
    relogio.avancar(121_000);
    await ate(() => pedidos.length > antes);
    await a.parar();
    await loop;
    const ev = db.query<{ detalhe: string }, []>("SELECT detalhe FROM evento WHERE tipo = 'secoes2t_pausa'").get();
    expect(JSON.parse(ev?.detalhe ?? "{}")).toMatchObject({ classe: "limite", retry_after_s: 120 });
  });

  test("pausa global do coletor principal segura toda requisição", async () => {
    let pausado = true;
    const { a, relogio, pedidos } = montarAmostra({}, () => null, () => pausado);
    await a.preparar();
    relogio.avancar(901_000);
    const loop = a.rodar();
    await Bun.sleep(40);
    expect(pedidos).toEqual([]);
    pausado = false;
    await ate(() => pedidos.length > 0);
    await a.parar();
    await loop;
  });

  test("seção da paralela fura a fila e roda antes do início da amostra", async () => {
    const { a, pedidos } = montarAmostra({ inicioMs: Date.parse("2030-01-01T00:00:00Z") });
    await a.preparar();
    a.adicionarParalela(sec("71072", 1, 1));
    const loop = a.rodar();
    await ate(() => a.estado(sec("71072", 1, 1))?.feito === true);
    await a.parar();
    await loop;
    expect(pedidos.every((u) => u.includes("/0001/0001/"))).toBe(true);
  });
});
