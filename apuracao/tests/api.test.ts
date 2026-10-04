// Contrato da API do servidor: cada endpoint validado por um esquema zod estrito (documenta o formato).
import { afterAll, beforeAll, describe, expect, test } from "bun:test";
import { mkdirSync, writeFileSync } from "node:fs";
import { z } from "zod";
import { criarServidor } from "../src/server/main.ts";
import type { Servidor } from "../src/server/main.ts";
import type { Semeado } from "./server-helpers.ts";
import { CHAVES, SQ, iso, seg, semear, versaoAb, versaoU } from "./server-helpers.ts";
import { chave, keyU } from "../src/tse/urls.ts";
import {
  AnomaliasSchema, ConfigSchema, EstadoSchema, LotesSchema, MapaSchema, ResultadoSchema, SerieSchema,
} from "./api-schemas.ts";

let s: Semeado;
let srv: Servidor;
const get = async (caminho: string): Promise<{ status: number; body: unknown; res: Response }> => {
  const res = await fetch(`${srv.url}${caminho}`);
  const texto = await res.text();
  let body: unknown = texto;
  try {
    body = JSON.parse(texto);
  } catch {
    // corpo não JSON (estático)
  }
  return { status: res.status, body, res };
};

beforeAll(() => {
  s = semear({ municipiosSp: true });
  s.fechar();
  srv = criarServidor({ dbPath: s.path, port: 0, log: false });
});

afterAll(async () => {
  await srv.parar();
  s.limpar();
});

describe("configuração e estado", () => {
  test("/api/config", async () => {
    const { status, body, res } = await get("/api/config");
    expect(status).toBe(200);
    expect(res.headers.get("cache-control")).toBe("no-store");
    const c = ConfigSchema.parse(body);
    expect(c.eleicoes).toEqual({ federal: 6257, estadual: 6259 });
    expect(c.ufs.length).toBe(28);
    expect(c.ufs.find((u) => u.uf === "sp")).toMatchObject({ nome: "São Paulo", cdi: "35" });
    const sp = c.municipios.SP ?? [];
    expect(sp.length).toBe(645);
    const capital = sp.find((m) => m.cd === "71072");
    expect(capital).toMatchObject({ nm: "São Paulo", cdi: "3550308", c: true, te: 9145124 });
    expect(capital?.z.length).toBe(57);
  });

  test("/api/estado ao vivo e com at", async () => {
    const e = EstadoSchema.parse((await get("/api/estado")).body);
    expect(e.pronto).toBe(true);
    expect(e.br?.st).toBe(200_000);
    expect(e.br?.atraso_s).toBe(10);
    expect(e.historico.map((h) => h.st)).toEqual([0, 50_000, 100_000, 150_000, 200_000]);
    expect(e.ufs.length).toBe(28);
    expect(e.ufs.find((u) => u.uf === "se")?.fechou_em).toBe(iso(seg(100)));
    expect(e.ufs.find((u) => u.uf === "pr")?.st).toBe(900);
    expect(e.coletor).toEqual({ em_voo: 3, fila: { t0: 1 } });
    expect(e.db?.eventos_warn).toBe(1);
    expect(e.latencias.leitura_menos_hg.length).toBeGreaterThan(5);
    const passado = EstadoSchema.parse((await get(`/api/estado?at=${encodeURIComponent("2026-10-04T17:03:00-03:00")}`)).body);
    expect(passado.agora).toBe(iso(seg(180)));
    expect(passado.br?.st).toBe(50_000);
    expect(passado.historico.length).toBe(2);
    expect(passado.ufs.find((u) => u.uf === "pr")?.st).toBe(0);
  });
});

describe("/api/resultado", () => {
  test("presidente br: última versão não regressiva, ordem por votos, d_vap", async () => {
    const r = ResultadoSchema.parse((await get("/api/resultado?ele=6257&cargo=1&abr=br")).body);
    expect(r.snapshot_id).toBe(s.id("presBr4"));
    expect(r.anterior_id).toBe(s.id("presBr3"));
    expect(r.nome_escopo).toBe("Brasil");
    expect(r.cargo).toEqual({ cd: 1, nome: "Presidente", nome_f: "Presidente", nv: 1 });
    expect(r.cand[0]).toMatchObject({ sqcand: String(SQ.flavio), n: "22", sg: "PL", campo: "direita", vap: 14_000_000, d_vap: 2_500_000 });
    expect(r.cand[1]).toMatchObject({ sqcand: String(SQ.lula), campo: "esquerda", vap: 13_000_000 });
    expect(r.cand[0]?.vs[0]).toEqual({ tp: "v", nmu: "ALFREDO GASPAR", sgp: "PL" });
    expect(r.v.vv).toBe(28_000_000);
    expect(r.candidatos_normalizados).toBe(true);
    expect(r.partidos.find((p) => p.sg === "PT")).toMatchObject({ campo: "esquerda", tvtn: 13_000_000, n_cand: 1 });
    expect(r.blob_url).toBe(`/api/blob/${r.snapshot_id}`);
    expect(r.fonte).toBe("tse");
    expect(r.nacional_tse).toBeUndefined();
  });

  test("arquivo nacional do TSE em dia: fonte tse no resultado e no estado", async () => {
    const r = ResultadoSchema.parse((await get("/api/resultado?ele=6257&cargo=1&abr=br")).body);
    expect(r.fonte).toBe("tse");
    expect(r.s.st).toBe(200_000);
    expect(EstadoSchema.parse((await get("/api/estado")).body).br?.fonte).toBe("tse");
  });

  test("at e snapshot_id escolhem a versão", async () => {
    const at = ResultadoSchema.parse((await get(`/api/resultado?ele=6257&cargo=1&abr=br&at=${encodeURIComponent("2026-10-04T17:05:00-03:00")}`)).body);
    expect(at.snapshot_id).toBe(s.id("presBr2"));
    expect(at.cand[0]?.sqcand).toBe(String(SQ.lula));
    const sid = ResultadoSchema.parse((await get(`/api/resultado?ele=6257&cargo=1&abr=br&snapshot_id=${s.id("presBr1")}`)).body);
    expect(sid.s.st).toBe(50_000);
    expect((await get(`/api/resultado?ele=6257&cargo=1&abr=sp&snapshot_id=${s.id("presBr1")}`)).status).toBe(404);
  });

  test("proporcional em município sem candidatos normalizados lê o blob", async () => {
    const r = ResultadoSchema.parse((await get("/api/resultado?ele=6259&cargo=7&abr=sp71072")).body);
    expect(r.candidatos_normalizados).toBe(false);
    expect(r.cargo.nome_f).toBe("Deputada Estadual");
    expect(r.cand[0]).toMatchObject({ n: "12136", vap: 50_000, d_vap: 50_000 });
    expect(r.cand.length).toBeGreaterThan(1000);
  });

  test("zona e governador", async () => {
    const z = ResultadoSchema.parse((await get("/api/resultado?ele=6257&cargo=1&abr=SP71072-z0001")).body);
    expect(z.tpabr).toBe("zona");
    expect(z.nome_escopo).toBe("São Paulo, zona 1");
    const g = ResultadoSchema.parse((await get("/api/resultado?ele=6259&cargo=3&abr=sp")).body);
    expect(g.cand[0]).toMatchObject({ n: "10", sg: "REPUBLICANOS" });
  });

  test("erros", async () => {
    expect((await get("/api/resultado?cargo=1&abr=br")).body).toEqual({ erro: "parâmetro ele obrigatório" });
    expect((await get("/api/resultado?ele=6257&cargo=1&abr=s1")).status).toBe(400);
    expect((await get("/api/resultado?ele=6257&cargo=1&abr=rj")).status).toBe(404);
    expect((await get("/api/resultado?ele=6257&cargo=1&abr=br&at=ontem")).status).toBe(400);
    expect((await get("/api/nada")).status).toBe(404);
  });
});

describe("/api/mapa", () => {
  test("nível uf", async () => {
    const m = MapaSchema.parse((await get("/api/mapa?ele=6257&cargo=1&nivel=uf")).body);
    expect(m.unidades.length).toBe(28);
    const sp = m.unidades.find((u) => u.cd === "sp");
    expect(sp).toMatchObject({ nm: "São Paulo", cdi: "35", lider: { sqcand: String(SQ.flavio) }, segundo: { sqcand: String(SQ.lula) } });
    expect(sp?.margem).toBeCloseTo((3 / 5.5) * 100 - (2.5 / 5.5) * 100, 2);
    expect(m.unidades.find((u) => u.cd === "rj")?.lider).toBeUndefined();
  });

  test("nível mun em SP: 645 unidades, rápido", async () => {
    const t = performance.now();
    const m = MapaSchema.parse((await get("/api/mapa?ele=6257&cargo=1&nivel=mun&pai=sp")).body);
    const ms = performance.now() - t;
    expect(m.unidades.length).toBe(645);
    expect(m.unidades.filter((u) => u.lider !== undefined).length).toBe(645);
    expect(m.unidades.find((u) => u.cd === "71072")).toMatchObject({ nm: "São Paulo", cdi: "3550308", tf: false, pst: 100 });
    expect(ms).toBeLessThan(500);
    console.log(`mapa mun sp: ${ms.toFixed(1)} ms (primeira chamada)`);
  });

  test("nível zona, at e erros", async () => {
    const m = MapaSchema.parse((await get("/api/mapa?ele=6257&cargo=1&nivel=zona&pai=sp71072")).body);
    expect(m.unidades.length).toBe(57);
    expect(m.unidades.find((u) => u.cd === "0001")?.lider?.n).toBe("13");
    const antes = MapaSchema.parse((await get(`/api/mapa?ele=6257&cargo=1&nivel=zona&pai=sp71072&at=${iso(seg(149))}`)).body);
    expect(antes.unidades.every((u) => u.lider === undefined)).toBe(true);
    expect((await get("/api/mapa?ele=6257&cargo=1&nivel=x")).status).toBe(400);
    expect((await get("/api/mapa?ele=6257&cargo=1&nivel=mun")).status).toBe(400);
    expect((await get("/api/mapa?ele=6257&cargo=1&nivel=zona&pai=sp")).status).toBe(400);
  });
});

describe("séries e anomalias", () => {
  test("/api/serie com virada", async () => {
    const r = SerieSchema.parse((await get("/api/serie?ele=6257&cargo=1&abr=br&top=3")).body);
    expect(r.pontos.length).toBe(5);
    expect(r.viradas).toEqual([{ at: iso(seg(350)), snapshot_id: s.id("presBr3"), de: String(SQ.lula), para: String(SQ.flavio) }]);
    expect(Object.keys(r.pontos[1]?.cand ?? {}).length).toBe(3);
  });

  test("/api/lotes: deltas por versão não regressiva, candidaturas com voto e top", async () => {
    const t0 = performance.now();
    const r = LotesSchema.parse((await get("/api/lotes?ele=6257&cargo=1&abr=br&top=3")).body);
    expect(performance.now() - t0).toBeLessThan(200);
    expect(r.abr).toBe("br");
    expect(r.candidatos.map((c) => c.n)).toEqual(["22", "13", "14"]);
    expect(r.lotes.map((l) => l.snapshot_id)).toEqual(["presBr0", "presBr1", "presBr2", "presBr3", "presBr4"].map((k) => s.id(k)));
    expect(r.lotes.some((l) => l.snapshot_id === s.id("presBrRegressivo"))).toBe(false);
    const [l0, l1, , l3, l4] = r.lotes;
    expect(l0?.d_st).toBe(l0?.st ?? -1);
    expect(l0?.d_vv).toBe(l0?.vv ?? -1);
    expect(l1?.at).toBe(iso(seg(120) - 10_000));
    expect(l1?.capturado_em).toBe(iso(seg(120)));
    expect(l4?.st).toBe(200_000);
    expect(l4?.d_st).toBe(50_000);
    expect(l4?.vv).toBe(28_000_000);
    expect(l4?.d_vv).toBe(28_000_000 - 23_400_000);
    expect(l4?.d_tv).toBe((l4?.tv ?? 0) - (l3?.tv ?? 0));
    expect(l4?.cand[String(SQ.lula)]).toEqual({ vap: 13_000_000, d_vap: 2_000_000 });
    expect(l4?.cand[String(SQ.flavio)]).toEqual({ vap: 14_000_000, d_vap: 2_500_000 });
    const soma = r.lotes.reduce((acc, l) => acc + (l.cand[String(SQ.flavio)]?.d_vap ?? 0), 0);
    expect(soma).toBe(14_000_000);
    const cedo = LotesSchema.parse((await get(`/api/lotes?ele=6257&cargo=1&abr=br&at=${iso(seg(250))}`)).body);
    expect(cedo.lotes.length).toBe(3);
    expect(LotesSchema.parse((await get("/api/lotes?ele=6257&cargo=1&abr=ac")).body)).toEqual({ abr: "ac", candidatos: [], lotes: [], fonte: "tse" });
    expect((await get("/api/lotes?ele=6257&cargo=1")).status).toBe(400);
  });

  test("/api/anomalias: gravadas, derivadas e filtros", async () => {
    const a = AnomaliasSchema.parse((await get("/api/anomalias")).body);
    const textos = a.map((x) => x.texto);
    expect(textos).toContain("Virada em Brasil: Flavio Bolsonaro passa Lula");
    expect(textos).toContain("Virada em SP: Flavio Bolsonaro passa Lula");
    expect(textos).toContain("Regressão de seções em zona 1 de São Paulo (SP) (presidente)");
    expect(textos).toContain("Sergipe fechou às 17:01");
    expect(textos).toContain("São Paulo (SP) terminou a apuração às 17:04");
    expect(a.map((x) => x.at)).toEqual([...a.map((x) => x.at)].sort().reverse());
    const warn = AnomaliasSchema.parse((await get("/api/anomalias?severidade=warn")).body);
    expect(warn.every((x) => x.severidade !== "info")).toBe(true);
    expect(warn.length).toBe(3);
    const viradas = AnomaliasSchema.parse((await get("/api/anomalias?tipo=virada&uf=sp")).body);
    expect(viradas.map((x) => x.abr)).toEqual(["sp"]);
    const cedo = AnomaliasSchema.parse((await get(`/api/anomalias?at=${iso(seg(200))}`)).body);
    expect(cedo.some((x) => x.tipo === "virada")).toBe(false);
  });
});

describe("auditoria", () => {
  test("/api/snapshots", async () => {
    const r = z.object({ abr: z.string(), snapshots: z.array(z.record(z.union([z.string(), z.number(), z.null()]))) }).parse(
      (await get("/api/snapshots?ele=6257&cargo=1&abr=br&limit=3")).body,
    );
    expect(r.snapshots.map((x) => x.snapshot_id)).toEqual([s.id("presBrRegressivo"), s.id("presBr4"), s.id("presBr3")]);
    expect(r.snapshots[1]).toMatchObject({ latencia_captura_s: 10, latencia_geracao_s: 20, intervalo_geracao_s: 120, d_st: 50_000, regressivo: 0 });
    const antes = z.object({ snapshots: z.array(z.object({ snapshot_id: z.number() }).passthrough()) }).parse(
      (await get(`/api/snapshots?ele=6257&cargo=1&abr=br&antes=${s.id("presBr2")}`)).body,
    );
    expect(antes.snapshots.map((x) => x.snapshot_id)).toEqual([s.id("presBr1"), s.id("presBr0")]);
  });

  test("/api/latencia, /api/fim, /api/velocidade, /api/andamento", async () => {
    const resumo = z.object({ n: z.number(), p50: z.number().nullable(), p95: z.number().nullable(), max: z.number().nullable() });
    const lat = z.object({ nivel: z.string(), escopos: z.array(z.object({ abr: z.string(), nome: z.string(), captura: resumo, geracao: resumo })), geral: z.object({ captura: resumo, geracao: resumo }) })
      .parse((await get("/api/latencia?ele=6257&cargo=1&nivel=br")).body);
    expect(lat.escopos[0]?.geracao).toEqual({ n: 4, p50: 20, p95: 20, max: 20 });
    const fim = z.object({ total_fechados: z.number(), pendentes: z.number(), fechados: z.array(z.object({ cd: z.string(), nm: z.string(), snapshot_id: z.number() }).passthrough()) })
      .parse((await get("/api/fim?ele=6257&cargo=1&uf=sp")).body);
    expect(fim).toMatchObject({ total_fechados: 1, pendentes: 644 });
    expect(fim.fechados[0]).toMatchObject({ cd: "71072", nm: "São Paulo", snapshot_id: s.id("presMun2") });
    const vel = z.object({ secoes_por_min: z.number().nullable(), eta_100: z.string().nullable(), de: z.string().nullable() }).passthrough()
      .parse((await get("/api/velocidade?ele=6257&cargo=1&abr=br")).body);
    expect(vel.secoes_por_min).toBe(25_000);
    expect(vel.de).toBe(iso(seg(110)));
    const and = z.object({ abr: z.string(), entradas: z.array(z.object({ cdabr: z.string(), nome: z.string(), st: z.number() }).passthrough()) }).passthrough()
      .parse((await get("/api/andamento?ele=6257&uf=sp")).body);
    expect(and.entradas.length).toBe(646);
    expect(and.entradas.find((x) => x.cdabr === "71072")).toMatchObject({ nome: "São Paulo", st: 10_000 });
  });

  test("/api/fetches e /api/blob", async () => {
    const f = z.array(z.object({ chave: z.string(), classe: z.string(), snapshot_id: z.number().nullable() }).passthrough())
      .parse((await get("/api/fetches?chave=u:6257:1:br:::")).body);
    expect(f.length).toBe(6);
    expect((await get("/api/fetches?chave=xyz")).status).toBe(400);
    const b = await get(`/api/blob/${s.id("presBr4")}`);
    expect(b.res.headers.get("content-type")).toContain("application/json");
    expect((b.body as { idg: string }).idg).toBe("1100040");
    expect((await get("/api/blob/999999")).status).toBe(404);
  });
});

describe("estáticos", () => {
  test("index, tipos e travessia", async () => {
    const i = await get("/");
    expect(i.status).toBe(200);
    expect(i.res.headers.get("content-type")).toContain("text/html");
    expect(i.res.headers.get("cache-control")).toBe("no-cache");
    expect((await get("/campos.json")).res.headers.get("content-type")).toContain("application/json");
    expect((await get("/%2e%2e/package.json")).status).toBe(404);
    expect((await get("/nao-existe.css")).status).toBe(404);
  });

  test("fontes com cache longo (public/ próprio: fonts/ é gerado por bun run assets e fica fora do git)", async () => {
    const pub = `${s.dir}/public-fontes`;
    mkdirSync(`${pub}/fonts`, { recursive: true });
    writeFileSync(`${pub}/fonts/teste.woff2`, new Uint8Array([0x77, 0x4f, 0x46, 0x32]));
    const proprio = criarServidor({ dbPath: s.path, publicDir: pub, port: 0, log: false });
    try {
      const r = await fetch(`${proprio.url}/fonts/teste.woff2`);
      expect(r.status).toBe(200);
      expect(r.headers.get("cache-control")).toBe("public, max-age=3600");
      expect(r.headers.get("content-type")).toBe("font/woff2");
    } finally {
      await proprio.parar();
    }
  });
});

describe("banco ausente", () => {
  test("serve estáticos e estado sem banco", async () => {
    const vazio = criarServidor({ dbPath: `${s.dir}/nao-existe.sqlite`, port: 0, log: false });
    try {
      const e = EstadoSchema.parse(await (await fetch(`${vazio.url}/api/estado`)).json());
      expect(e.pronto).toBe(false);
      expect((await fetch(`${vazio.url}/api/resultado?ele=6257&cargo=1&abr=br`)).status).toBe(503);
      expect(ConfigSchema.parse(await (await fetch(`${vazio.url}/api/config`)).json()).ufs).toEqual([]);
      expect((await fetch(`${vazio.url}/`)).status).toBe(200);
    } finally {
      await vazio.parar();
    }
  });
});

describe("agregado nacional pela soma das UFs", () => {
  let sd: Semeado;
  let srvSoma: Servidor;
  let ufs: string[] = [];

  beforeAll(() => {
    sd = semear();
    ufs = sd.db
      .query<{ uf: string }, []>("SELECT uf FROM arquivo WHERE tipo = 'u' AND eleicao_cd = 6257 AND cargo_cd = 1 AND nivel = 'uf' ORDER BY uf")
      .all()
      .map((u) => u.uf);
    // As 28 UFs andam depois da última versão do arquivo nacional (st 200.000, gerado em seg(470)).
    ufs.forEach((uf, i) => {
      const corpo = versaoU("sp-c0001-e006257-u.json", { st: 10_000 + i, votos: { 13: 100_000 + i, 22: 90_000 + 2 * i }, idg: 1_300_000 + i, ger: seg(700) + i * 1000, tot: seg(690), cdabr: uf });
      sd.seq.processar(chave(keyU(6257, 1, "uf", uf)), corpo, iso(seg(700) + i * 1000 + 500));
    });
    sd.seq.processar(CHAVES.abBr, versaoAb("br-e006257-ab.json", 1_300_100, seg(760), { br: { st: 300_000, tot: seg(750) } }), iso(seg(765)));
    sd.fechar();
    srvSoma = criarServidor({ dbPath: sd.path, port: 0, log: false });
  });

  afterAll(async () => {
    await srvSoma.parar();
    sd.limpar();
  });

  const pegar = async (caminho: string): Promise<unknown> => (await fetch(`${srvSoma.url}${caminho}`)).json();

  test("arquivo nacional parado: resultado br é a soma das 28 UFs", async () => {
    expect(ufs.length).toBe(28);
    const r = ResultadoSchema.parse(await pegar("/api/resultado?ele=6257&cargo=1&abr=br"));
    expect(r.fonte).toBe("soma_ufs");
    expect(r.ufs_usadas).toBe(28);
    expect(r.nacional_tse).toMatchObject({ hg: iso(seg(480) - 10_000), st: 200_000 });
    expect(r.nacional_tse?.pst).toBeCloseTo((200_000 / 499_248) * 100, 3);
    const porUf = await Promise.all(ufs.map(async (uf) => ResultadoSchema.parse(await pegar(`/api/resultado?ele=6257&cargo=1&abr=${uf}`))));
    const soma = (f: (x: (typeof porUf)[number]) => number): number => porUf.reduce((a, x) => a + f(x), 0);
    const vap = (x: (typeof porUf)[number], sq: number): number => x.cand.find((c) => c.sqcand === String(sq))?.vap ?? 0;
    expect(r.s.st).toBe(soma((x) => x.s.st));
    expect(r.s.ts).toBe(soma((x) => x.s.ts));
    expect(r.s.pst).toBeCloseTo((100 * r.s.st) / r.s.ts, 9);
    expect(r.v.vv).toBe(soma((x) => x.v.vv));
    expect(r.v.tv).toBe(soma((x) => x.v.tv));
    expect(r.e.c).toBe(soma((x) => x.e.c));
    const lula = r.cand.find((c) => c.sqcand === String(SQ.lula));
    const flavio = r.cand.find((c) => c.sqcand === String(SQ.flavio));
    expect(lula?.vap).toBe(soma((x) => vap(x, SQ.lula)));
    expect(flavio?.vap).toBe(soma((x) => vap(x, SQ.flavio)));
    expect(lula?.vap).toBe(28 * 100_000 + (27 * 28) / 2);
    expect(lula?.pvapn).toBeCloseTo((100 * (lula?.vap ?? 0)) / r.v.vv, 9);
    expect(r.cand[0]?.sqcand).toBe(String(SQ.lula));
    expect(r.partidos.find((p) => p.sg === "PT")?.tvtn).toBe(lula?.vap ?? -1);
    expect(r.dg_hg).toBe(iso(seg(700) + 27_000));
    expect(r.dt_ht).toBe(iso(seg(690)));
    expect(r.snapshot_id).toBe(Math.max(...porUf.map((x) => x.snapshot_id)));
  });

  test("estado br segue a soma; at antes das UFs e snapshot_id explícito voltam ao arquivo do TSE", async () => {
    const e = EstadoSchema.parse(await pegar("/api/estado"));
    expect(e.br?.fonte).toBe("soma_ufs");
    expect(e.br?.st).toBe(28 * 10_000 + (27 * 28) / 2);
    expect(e.br?.nacional_tse?.st).toBe(200_000);
    const antes = ResultadoSchema.parse(await pegar(`/api/resultado?ele=6257&cargo=1&abr=br&at=${iso(seg(650))}`));
    expect(antes.fonte).toBe("tse");
    expect(antes.s.st).toBe(200_000);
    const sid = ResultadoSchema.parse(await pegar(`/api/resultado?ele=6257&cargo=1&abr=br&snapshot_id=${sd.id("presBr4")}`));
    expect(sid.fonte).toBe("tse");
    expect(SerieSchema.parse(await pegar("/api/serie?ele=6257&cargo=1&abr=br")).fonte).toBe("tse");
    expect(LotesSchema.parse(await pegar("/api/lotes?ele=6257&cargo=1&abr=br")).fonte).toBe("tse");
  });
});
