// Coleta de seções: log da urna (modelo), aux, cs, conferência por zona, cliente HTTP e banco.
import { describe, expect, test } from "bun:test";
import { decodificarBu } from "../scripts/bu-decode.ts";
import { abrirSecoes, EscritorSecoes } from "../scripts/secoes/banco.ts";
import type { ResultadoSecao } from "../scripts/secoes/banco.ts";
import { chaveZona, conferir } from "../scripts/secoes/conferencia.ts";
import { secoesDoCs } from "../scripts/secoes/cs.ts";
import { ClienteTse } from "../scripts/secoes/http.ts";
import { lerZip, modeloDaUrna, resumirLog } from "../scripts/secoes/log-urna.ts";
import { coletarSecao, dataHoraTse, escolherHash, urlAux } from "../scripts/secoes/secao.ts";
import type { ResultadoU } from "../src/parse/schemas.ts";
import { RelogioFalso } from "../src/collector/relogio.ts";
import { bytes } from "./helpers.ts";

const LOG = "bu/o03220sp7107200010001-log.jez";
const BU = "bu/o03220sp7107200010001-bu.dat";

describe("log da urna", () => {
  test("ZIP com logd.dat e modelo UE2020 da urna 02027601", () => {
    const zip = lerZip(bytes(LOG));
    expect(zip.map((e) => [e.nome, e.dados.length])).toEqual([["logd.dat", 623_346]]);
    const r = resumirLog(zip);
    expect(r.linhas).toBe(6451);
    expect(r.urnas).toEqual([{ id: "02027601", modelos: ["UE2020"], linhas: 6451 }]);
    expect(modeloDaUrna(r, 2027601)).toEqual({ modelo: "UE2020", fonte: "log_mesma_urna" });
    expect(modeloDaUrna(r, 1234567)).toEqual({ modelo: "UE2020", fonte: "log_modelo_unico" });
  });

  test("duas urnas no log: o modelo é o da urna do BU", () => {
    const linha = (id: string, m: string): string => `04/10/2026 07:20:21\tINFO\t${id}\tGAP\tIdentificação do Modelo de Urna: ${m}\tAA2A40C3483E7BBC\n`;
    const txt = linha("01000001", "UE2010") + linha("02000002", "UE2022") + "04/10/2026 08:00:00\tINFO\t02000002\tVOTA\tVoto confirmado\tX\n";
    const dados = new Uint8Array([...txt].map((c) => c.charCodeAt(0) & 0xff));
    const r = resumirLog([{ nome: "logd.dat", dados }]);
    expect(modeloDaUrna(r, 2000002)).toEqual({ modelo: "UE2022", fonte: "log_mesma_urna" });
    expect(modeloDaUrna(r, 3)).toEqual({ modelo: null, fonte: "log_sem_modelo" });
    expect(r.urnas.find((u) => u.id === "02000002")?.linhas).toBe(2);
  });

  test("lixo não é ZIP", () => {
    expect(() => lerZip(new Uint8Array(100))).toThrow();
  });
});

describe("aux e cs", () => {
  test("escolhe o hash mais recente que tem boletim", () => {
    const aux = {
      st: "Recebida",
      hashes: [
        { hash: "a", dr: "04/10/2026", hr: "19:17:07", st: "Recebido", arq: [{ nm: "x-bu.dat", tp: "bu" }, { nm: "x-log.jez", tp: "log" }] },
        { hash: "b", dr: "04/10/2026", hr: "21:00:00", st: "Recebido", arq: [{ nm: "y-bu.dat", tp: "bu" }] },
        { hash: "c", dr: "05/10/2026", hr: "01:00:00", st: "Recebido", arq: [{ nm: "z-rdv.dat", tp: "rdv" }] },
      ],
    };
    expect(escolherHash(aux)).toEqual({ hash: "b", st: "Recebido", drHr: "2026-10-04 21:00:00", bu: "y-bu.dat", log: null });
    expect(escolherHash({ st: "Não instalada" })).toBeNull();
    const sa = { hashes: [{ hash: "d", dr: "04/10/2026", hr: "20:00:58", arq: [{ nm: "w-imgbusa.dat", tp: "imgbusa" }, { nm: "w-busa.dat", tp: "busa" }, { nm: "w-sa.vsc", tp: "sa" }] }] };
    expect(escolherHash(sa)).toEqual({ hash: "d", st: null, drHr: "2026-10-04 20:00:58", bu: "w-busa.dat", log: null });
    const mista = { hashes: [{ hash: "e", arq: [{ nm: "v-bu.dat", tp: "bu" }, { nm: "v-busa.dat", tp: "busa" }, { nm: "v-log.jez", tp: "log" }] }] };
    expect(escolherHash(mista)?.bu).toBe("v-busa.dat");
    expect(dataHoraTse("04/10/2026", "19:17:07")).toBe("2026-10-04 19:17:07");
  });

  test("URL do aux", () => {
    expect(urlAux({ uf: "sp", mun: "71072", zona: 1, secao: 1 })).toBe(
      "https://resultados.tse.jus.br/oficial/ele2026/arquivo-urna/3220/dados/sp/71072/0001/0001/p003220-sp-m71072-z0001-s0001-aux.json",
    );
  });

  test("seções do cs em ordem, com agregação", () => {
    const cs = {
      abr: [{ cd: "AC", mu: [
        { cd: "1392", zon: [{ cd: "0009", sec: [{ ns: "0002" }, { ns: "0001", nsa: ["0003"] }, { ns: "0003", nsp: "0001" }] }] },
        { cd: "01007", zon: [{ cd: "0004", sec: [{ ns: "0010" }] }] },
      ] }],
    };
    expect(secoesDoCs(cs)).toEqual([
      { uf: "ac", mun: "01007", zona: 4, secao: 10, nsp: null, nsa: null },
      { uf: "ac", mun: "01392", zona: 9, secao: 1, nsp: null, nsa: "[3]" },
      { uf: "ac", mun: "01392", zona: 9, secao: 2, nsp: null, nsa: null },
      { uf: "ac", mun: "01392", zona: 9, secao: 3, nsp: 1, nsa: null },
    ]);
  });
});

function zonaFake(
  cand: Array<[string, string]>,
  v: Record<string, string>,
  e: Record<string, string>,
  partidos: Array<{ n: string; tvtl: string; tval: string; dvt?: string }> = [],
): ResultadoU {
  return {
    carg: [{ agr: [{ par: [{ n: "99", cand: cand.map(([n, vap]) => ({ n, vap })) }, ...partidos] }] }],
    s: { ts: "2", st: "2" },
    e,
    v,
  } as ResultadoU;
}

describe("conferência por zona", () => {
  const soma = {
    secoesCs: 2, secoesBu: 2, aptos: 700, comparecimento: 500,
    votos: [
      { tipo: 1, numero: 13, votos: 200 }, { tipo: 1, numero: 22, votos: 250 }, { tipo: 1, numero: 77, votos: 5 },
      { tipo: 2, numero: 0, votos: 15 }, { tipo: 3, numero: 0, votos: 30 },
    ],
  };

  test("confere quando cada voto bate", () => {
    const z = zonaFake([["13", "200"], ["22", "250"], ["30", "0"]], { vb: "15", vn: "30", vnt: "5", van: "0", vansj: "0" }, { te: "700", c: "500" });
    const r = conferir(soma, z);
    expect(r.divergencias).toEqual([]);
    expect(r.ok).toBe(true);
    expect(r.foraListaBu).toBe(5);
    expect(r.candidatos).toBe(3);
  });

  test("aponta candidato, nulo técnico e legenda divergentes", () => {
    const z = zonaFake([["13", "201"], ["22", "250"]], { vb: "15", vn: "30", vnt: "4", vl: "3" }, { te: "700", c: "500" }, [{ n: "13", tvtl: "3", tval: "3" }]);
    const r = conferir(soma, z);
    expect(r.ok).toBe(false);
    expect(r.divergencias.map((d) => d.campo)).toEqual(["candidato:13", "fora_da_lista=nulos_tecnicos", "legenda", "legenda:13"]);
    expect(r.candidatosDivergentes).toBe(1);
  });

  test("legenda de partido anulado sub judice confere por tval, não por tvtl", () => {
    // RO 00019/0001, deputado federal: MOBILIZA (33) com DRAP anulado sub judice, tvtl 0 e tval 2.
    const comLegenda = { ...soma, votos: [...soma.votos, { tipo: 4, numero: 33, votos: 2 }, { tipo: 4, numero: 22, votos: 7 }] };
    const z = zonaFake(
      [["13", "200"], ["22", "250"]],
      { vb: "15", vn: "30", vnt: "5", vl: "7", vansj: "2" },
      { te: "700", c: "500" },
      [{ n: "33", tvtl: "0", tval: "2", dvt: "Anulado sub judice" }, { n: "22", tvtl: "7", tval: "7" }],
    );
    const r = conferir(comLegenda, z);
    expect(r.divergencias).toEqual([]);
    expect([r.legendaBu, r.legendaZona]).toEqual([9, 9]);
  });

  test("legenda de partido sem lista no cargo é nulo técnico", () => {
    // SE 31003/0015, deputado federal: vnt 5 = nominal 7777 (1) + legenda 25 (2) + legenda 77 (2).
    const votos = [
      { tipo: 1, numero: 2222, votos: 40 }, { tipo: 1, numero: 7777, votos: 1 },
      { tipo: 4, numero: 22, votos: 3 }, { tipo: 4, numero: 25, votos: 2 }, { tipo: 4, numero: 77, votos: 2 },
      { tipo: 2, numero: 0, votos: 4 }, { tipo: 3, numero: 0, votos: 1 },
    ];
    const z = zonaFake([["2222", "40"]], { vb: "4", vn: "1", vnt: "5", vl: "3" }, { te: "80", c: "53" }, [{ n: "22", tvtl: "3", tval: "3" }]);
    const r = conferir({ secoesCs: 1, secoesBu: 1, aptos: 80, comparecimento: 53, votos }, z);
    expect(r.divergencias).toEqual([]);
    expect([r.foraListaBu, r.nulosTecnicosZona, r.legendaBu]).toEqual([5, 5, 3]);
  });

  test("chave do arquivo de zona do coletor", () => {
    expect(chaveZona(6257, 1, "sp", "71072", 1)).toBe("u:6257:1:zona:sp:71072:0001");
  });
});

describe("cliente HTTP", () => {
  const sem = (): Promise<void> => Promise.resolve();

  test("404 volta sem repetir; 500 repete com espera", async () => {
    const urls: string[] = [];
    let n = 0;
    const c = new ClienteTse({
      rps: 1000, rajada: 1000, dormir: sem,
      fetchImpl: (u) => {
        urls.push(u);
        n += 1;
        if (u.endsWith("404")) return Promise.resolve(new Response("x", { status: 404 }));
        return Promise.resolve(n < 4 ? new Response("erro", { status: 503 }) : new Response("ok", { status: 200 }));
      },
    });
    const a = await c.obter("https://h/404");
    expect([a.status, a.requisicoes, a.corpo]).toEqual([404, 1, null]);
    const b = await c.obter("https://h/x");
    expect([b.status, b.requisicoes, new TextDecoder().decode(b.corpo ?? new Uint8Array())]).toEqual([200, 3, "ok"]);
    expect(c.contagem).toEqual({ ok: 1, nao_existe: 1, limite: 0, erro_servidor: 2, erro_rede: 0, outro: 0 });
  });

  test("429 pausa o balde global e tenta de novo", async () => {
    const relogio = new RelogioFalso();
    let n = 0;
    const c = new ClienteTse({
      rps: 10, rajada: 10, relogio,
      dormir: (ms) => {
        relogio.avancar(ms);
        return Promise.resolve();
      },
      fetchImpl: () => {
        n += 1;
        return Promise.resolve(n === 1 ? new Response("", { status: 429, headers: { "retry-after": "5" } }) : new Response("ok", { status: 200 }));
      },
    });
    const t0 = relogio.agora();
    const r = await c.obter("https://h/y");
    expect(r.status).toBe(200);
    expect(r.requisicoes).toBe(2);
    expect(relogio.agora() - t0).toBeGreaterThanOrEqual(30_000);
  });

  test("teto de taxa: 20 requisições a 10/s levam pelo menos 1,6 s de relógio", async () => {
    const relogio = new RelogioFalso();
    const c = new ClienteTse({
      rps: 10, rajada: 4, relogio,
      dormir: (ms) => {
        relogio.avancar(ms);
        return Promise.resolve();
      },
      fetchImpl: () => Promise.resolve(new Response("ok", { status: 200 })),
    });
    const t0 = relogio.agora();
    for (let i = 0; i < 20; i += 1) await c.obter("https://h/z");
    expect(relogio.agora() - t0).toBeGreaterThanOrEqual(1_600);
  });
});

describe("coleta e banco", () => {
  test("seção completa: aux, BU e log viram bu, bu_cargo e voto_secao", async () => {
    const aux = JSON.stringify({
      dg: "04/10/2026", hg: "19:17:07", st: "Recebida",
      hashes: [{ hash: "h1", dr: "04/10/2026", hr: "19:17:07", st: "Recebido", arq: [
        { nm: "o03220sp7107200010001-bu.dat", tp: "bu" }, { nm: "o03220sp7107200010001-log.jez", tp: "log" },
      ] }],
    });
    const corpos: Record<string, Uint8Array<ArrayBuffer>> = {
      "-aux.json": new TextEncoder().encode(aux),
      "-bu.dat": bytes(BU),
      "-log.jez": bytes(LOG),
    };
    const obter = (u: string): Promise<{ status: number; corpo: Uint8Array<ArrayBuffer> | null; erro: string | null; requisicoes: number }> => {
      const k = Object.keys(corpos).find((s) => u.endsWith(s));
      const corpo = k === undefined ? null : (corpos[k] ?? null);
      return Promise.resolve({ status: corpo === null ? 404 : 200, corpo, erro: corpo === null ? "HTTP 404" : null, requisicoes: 1 });
    };
    const s = { uf: "sp", mun: "71072", zona: 1, secao: 1, nsp: null, nsa: null };
    const r: ResultadoSecao = await coletarSecao(s, { obter, guardarLog: false });
    expect(r.erro).toBeNull();
    expect(r.requisicoes).toBe(3);
    expect(r.modelo).toEqual({ modelo: "UE2020", fonte: "log_mesma_urna" });
    expect(Bun.gunzipSync(r.buGz ?? new Uint8Array())).toEqual(bytes(BU));

    const db = abrirSecoes(":memory:");
    const w = new EscritorSecoes(db);
    w.semear([s]);
    w.gravar([r], "2026-10-05T09:00:00.000Z");
    w.gravar([r], "2026-10-05T09:00:01.000Z"); // regravar é idempotente
    const bu = db.query("SELECT modelo_urna, numero_interno_urna, aptos, comparecimento, abertura, encerramento, id_confere FROM bu").all();
    expect(bu).toEqual([{ modelo_urna: "UE2020", numero_interno_urna: 2027601, aptos: 362, comparecimento: 256, abertura: "2026-10-04 08:00:01", encerramento: "2026-10-04 17:08:42", id_confere: 1 }]);
    const pres = db.query<{ numero: number; votos: number }, []>("SELECT numero, votos FROM voto_secao WHERE cargo = 1 AND tipo = 1 ORDER BY numero").all();
    expect(pres.find((p) => p.numero === 22)?.votos).toBe(96);
    expect(db.query<{ n: number }, []>("SELECT COUNT(*) AS n FROM voto_secao").get()?.n).toBe(205);
    expect(db.query<{ r: number }, []>("SELECT requisicoes AS r FROM secao").get()?.r).toBe(6);
    expect(decodificarBu(bytes(BU)).bu.qtdEleitoresCompareceram).toBe(256);
  });

  test("aux 404 e aux sem boletim", async () => {
    const s = { uf: "ac", mun: "01007", zona: 4, secao: 10, nsp: null, nsa: null };
    const nada = await coletarSecao(s, { obter: () => Promise.resolve({ status: 404, corpo: null, erro: "HTTP 404", requisicoes: 1 }), guardarLog: false });
    expect([nada.statusAux, nada.erro, nada.buGz]).toEqual(["aux_404", null, null]);
    const corpo = new TextEncoder().encode(JSON.stringify({ st: "Não instalada", hashes: [] }));
    const sem = await coletarSecao(s, { obter: () => Promise.resolve({ status: 200, corpo, erro: null, requisicoes: 1 }), guardarLog: false });
    expect([sem.statusAux, sem.hash, sem.requisicoes]).toEqual(["Não instalada", null, 1]);
  });
});
