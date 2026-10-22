// Eventos gravados pelo coletor (virada, uf_fechou), observador de versões no processamento,
// textos e categorias dos tipos novos, e a derivação do servidor só como reserva.
import { afterAll, beforeAll, describe, expect, test } from "bun:test";
import { Database } from "bun:sqlite";
import { versaoRegressiva } from "../src/collector/processar-corpo.ts";
import { processar } from "../src/collector/processar.ts";
import { eventosApuracao, liderDe } from "../src/collector/viradas.ts";
import type { CandResumo, TotaisResumo } from "../src/collector/estado-arquivos.ts";
import { criarServidor } from "../src/server/main.ts";
import type { Servidor } from "../src/server/main.ts";
import { categoria, textoEvento } from "../src/server/textos.ts";
import { chave, keyU } from "../src/tse/urls.ts";
import { arquivo, jobDe, montar, ok } from "./coletor-util.ts";
import type { Semeado } from "./server-helpers.ts";
import { semear, seg, versaoU } from "./server-helpers.ts";

const T = (o: Partial<TotaisResumo> = {}): TotaisResumo => ({ ts: 100, st: 50, pst: 50, vvc: 1, vv: 1, vnom: 1, tv: 1, comparecimento: 1, est: 1, ...o });
const C = (pares: [number, number][]): Map<number, CandResumo> => new Map(pares.map(([sq, vap]) => [sq, { vap, eleito: null }]));
const base = (key: ReturnType<typeof keyU>, extra: Partial<Parameters<typeof eventosApuracao>[4]> = {}): Parameters<typeof eventosApuracao>[4] => ({
  em: "2026-10-25T22:00:00.000Z", arquivoId: 1, snapshot: { ref: "s1" }, key, geradoEm: "2026-10-25T22:00:00.000Z", totalizadoEm: "2026-10-25T21:59:00.000Z",
  nomes: new Map([[1, "LULA"], [2, "FLAVIO BOLSONARO"]]), ...extra,
});

describe("virada e fechamento gravados pelo coletor", () => {
  test("líder: maior voto positivo e único", () => {
    expect(liderDe(C([[1, 10], [2, 5]]))).toEqual({ sq: 1, vap: 10 });
    expect(liderDe(C([[1, 10], [2, 10]]))).toBeNull();
    expect(liderDe(C([[1, 0], [2, 0]]))).toBeNull();
  });

  test("virada no nacional e na UF de presidente e no governador por UF; não em município", () => {
    const ant = C([[1, 100], [2, 90]]);
    const novo = C([[1, 110], [2, 120]]);
    const br = eventosApuracao(T(), T(), ant, novo, base(keyU(6258, 1, "br")));
    expect(br).toHaveLength(1);
    expect(br[0]).toMatchObject({ tipo: "virada", severidade: "warn", nivel: "br", snapshot_id: { ref: "s1" } });
    expect(br[0]?.detalhe).toEqual({ de: "1", para: "2", de_nome: "Lula", para_nome: "Flavio Bolsonaro", vap_de: 110, vap_para: 120, pst: 50 });
    expect(eventosApuracao(T(), T(), ant, novo, base(keyU(6260, 3, "uf", "am")))).toHaveLength(1);
    expect(eventosApuracao(T(), T(), ant, novo, base(keyU(6258, 1, "mu", "sp", "71072")))).toEqual([]);
    expect(eventosApuracao(T(), T(), C([[1, 0], [2, 0]]), novo, base(keyU(6258, 1, "br")))).toEqual([]);
    expect(eventosApuracao(T(), T(), ant, C([[1, 100], [2, 100]]), base(keyU(6258, 1, "br")))).toEqual([]);
  });

  test("uf_fechou na passagem para st = ts, com totalizado_em corrigido do fuso (AC +120 min)", () => {
    const k = keyU(6258, 1, "uf", "ac");
    const ev = eventosApuracao(T({ st: 99 }), T({ st: 100, pst: 100 }), null, null, base(k, { geradoEm: "2026-10-25T21:01:00.000Z", totalizadoEm: "2026-10-25T19:00:00.000Z" }));
    expect(ev.map((e) => [e.tipo, e.severidade])).toEqual([["uf_fechou", "info"]]);
    expect(ev[0]?.detalhe).toMatchObject({ totalizado_em: "2026-10-25T21:00:00.000Z", st: 100, ts: 100 });
    expect(eventosApuracao(T({ st: 100 }), T({ st: 100 }), null, null, base(k))).toEqual([]);
    expect(eventosApuracao(T({ st: 99 }), T({ st: 100 }), null, null, base(keyU(6258, 1, "br")))).toEqual([]);
  });

  test("processamento real: versão nova de -u chama o observador e grava a virada", () => {
    const m = montar();
    const vistos: { chave: string; gerado: string | null; st: number | null }[] = [];
    m.ctx.aoVersaoU = (fs, v) => {
      vistos.push({ chave: fs.chave, gerado: v.geradoEm, st: v.totais.st });
      return [];
    };
    const ch = chave(keyU(6257, 1, "br"));
    const rodar = (st: number, votos: Record<string, number>, idg: number): void => {
      const fs = arquivo(m, ch);
      processar(m.ctx, jobDe(fs), fs, ok(versaoU("br-c0001-e006257-u.json", { st, votos, idg, ger: seg(st), tot: seg(st - 10) })), m.relogio.agora());
      m.lote.gravar();
      m.relogio.avancar(1000);
    };
    rodar(100, { 13: 1000, 22: 900 }, 10);
    rodar(200, { 13: 1500, 22: 1600 }, 11);
    expect(vistos.map((v) => v.st)).toEqual([100, 200]);
    expect(vistos[1]?.gerado).toBe(new Date(seg(200)).toISOString());
    const ev = m.ctx.db.query<{ tipo: string; detalhe: string }, []>("SELECT tipo, detalhe FROM evento WHERE tipo = 'virada'").all();
    expect(ev).toHaveLength(1);
    expect(JSON.parse(ev[0]?.detalhe ?? "{}")).toMatchObject({ de_nome: "Lula", para_nome: "Flavio Bolsonaro" });
  });

  test("observador que falha não derruba o processamento", () => {
    const m = montar();
    const erros: unknown[] = [];
    m.ctx.aoVersaoU = () => {
      throw new Error("quebrou");
    };
    m.ctx.aoFalharObservador = (e) => erros.push(e);
    const fs = arquivo(m, chave(keyU(6257, 1, "br")));
    const s = processar(m.ctx, jobDe(fs), fs, ok(versaoU("br-c0001-e006257-u.json", { st: 1, votos: { 13: 1 }, idg: 1, ger: seg(1) })), m.relogio.agora());
    expect(s.mudou).toBe(true);
    expect(erros).toHaveLength(1);
  });
});

describe("regra de versão: a hora de geração manda, o idg só desempata", () => {
  test("versaoRegressiva", () => {
    const a = { idg: 1_680_211, geradoEm: "2026-10-04T22:31:33.000Z" };
    // caso do AP no 1º turno: gerada depois, idg menor; era descartada
    expect(versaoRegressiva({ idg: 1_679_679, gerado_em: "2026-10-04T22:32:03.000Z" }, a)).toBe(false);
    expect(versaoRegressiva({ idg: 1_700_000, gerado_em: "2026-10-04T22:30:00.000Z" }, a)).toBe(true);
    expect(versaoRegressiva({ idg: 1_679_679, gerado_em: a.geradoEm }, a)).toBe(true);
    expect(versaoRegressiva({ idg: 1_680_212, gerado_em: a.geradoEm }, a)).toBe(false);
    expect(versaoRegressiva({ idg: 1, gerado_em: null }, a)).toBe(true);
    expect(versaoRegressiva({ idg: null, gerado_em: null }, a)).toBe(false);
  });

  test("versão gerada depois com idg menor passa pelo motor; cópia mais velha não", () => {
    const m = montar();
    const fs = arquivo(m, chave(keyU(6257, 1, "br")));
    const vistos: (string | null)[] = [];
    m.ctx.aoVersaoU = (_fs, v) => {
      vistos.push(v.geradoEm);
      return [];
    };
    const rodar = (st: number, idg: number, ger: number): void => {
      processar(m.ctx, jobDe(fs), fs, ok(versaoU("br-c0001-e006257-u.json", { st, votos: { 13: st, 22: st - 1 }, idg, ger: seg(ger) })), m.relogio.agora());
      m.lote.gravar();
      m.relogio.avancar(1000);
    };
    rodar(100, 50, 60);
    rodar(120, 40, 120); // mais nova, idg menor
    rodar(110, 45, 90); // mais velha que a atual
    expect(vistos).toEqual([new Date(seg(60)).toISOString(), new Date(seg(120)).toISOString()]);
    expect(m.ctx.db.query<{ r: number }, []>("SELECT regressivo AS r FROM snapshot ORDER BY id").all().map((x) => x.r)).toEqual([0, 0, 1]);
  });
});

describe("textos e categorias", () => {
  const muns = new Map([["71072", { cd: "71072", uf: "sp", ibge: null, nome: "SÃO PAULO", capital: 1 }]]);
  const e = (tipo: string, detalhe: unknown, esc: Partial<{ nivel: string; uf: string; municipio_cd: string; zona_cd: string }> = {}): string =>
    textoEvento(tipo, "2026-10-25T22:00:00.000Z", { nivel: esc.nivel ?? "br", uf: esc.uf ?? null, municipio_cd: esc.municipio_cd ?? null, zona_cd: esc.zona_cd ?? null, cargo_cd: 1 }, detalhe, muns);
  const casos: [string, string, string][] = [
    ["pausa_nacional_inicio", e("pausa_nacional_inicio", { desde: "2026-10-25T22:32:00.000Z", minutos: 7 }), "pausa"],
    ["pausa_nacional_fim", e("pausa_nacional_fim", { ate: "2026-10-25T23:02:00.000Z", minutos: 29.6 }), "pausa"],
    ["pausa_nacional_longa", e("pausa_nacional_longa", { desde: "2026-10-25T22:32:00.000Z", minutos: 15 }), "pausa"],
    ["pausa_geral_inicio", e("pausa_geral_inicio", { desde: "2026-10-25T22:32:00.000Z", minutos: 6 }), "pausa"],
    ["pausa_uf_inicio", e("pausa_uf_inicio", { desde: "2026-10-25T22:40:00.000Z", minutos: 11 }, { nivel: "uf", uf: "ba" }), "pausa"],
    ["pausa_uf_fim", e("pausa_uf_fim", { ate: "2026-10-25T22:58:00.000Z", minutos: 18 }, { nivel: "uf", uf: "ba" }), "pausa"],
    ["soma_ufs_adiante", e("soma_ufs_adiante", { diferenca_pct: 3.14 }), "pausa"],
    ["uf_atrasada_1t", e("uf_atrasada_1t", { patamar_min: 20 }, { nivel: "uf", uf: "ba" }), "atraso"],
    ["abstencao_atipica_mun", e("abstencao_atipica_mun", { pa_2t: 31.25, pa_1t: 24 }, { nivel: "mu", uf: "sp", municipio_cd: "71072" }), "abstencao"],
    ["abstencao_atipica_uf", e("abstencao_atipica_uf", { pa_2t: 24.3, pa_1t_mesmos: 21.9 }, { nivel: "uf", uf: "ba" }), "abstencao"],
    ["secao_tardia", e("secao_tardia", { secao: 45, encerramento_hhmm: "18:42" }, { nivel: "zona", uf: "sp", municipio_cd: "71072", zona_cd: "0001" }), "atraso"],
    ["divergencia_paralela", e("divergencia_paralela", { secao: 45 }, { nivel: "zona", uf: "sp", municipio_cd: "71072", zona_cd: "0001" }), "divergencia"],
    ["paralela_conferida", e("paralela_conferida", { conferidos: 12, iguais: 12, divergentes: 0 }), "paralela"],
    ["uf_fechou", e("uf_fechou", { totalizado_em: "2026-10-25T21:01:00.000Z" }, { nivel: "uf", uf: "se" }), "fechou"],
  ];

  test("frases", () => {
    expect(Object.fromEntries(casos.map(([t, txt]) => [t, txt]))).toEqual({
      pausa_nacional_inicio: "Arquivo nacional sem versão nova desde 19:32 (7 min)",
      pausa_nacional_fim: "Arquivo nacional voltou a publicar às 20:02, após 29,6 min sem versão nova",
      pausa_nacional_longa: "Arquivo nacional segue sem versão nova desde 19:32 (15 min)",
      pausa_geral_inicio: "Nenhum arquivo do TSE com versão nova desde 19:32 (6 min)",
      pausa_uf_inicio: "Bahia sem versão nova desde 19:40 (11 min)",
      pausa_uf_fim: "Bahia voltou a publicar às 19:58, após 18 min sem versão nova",
      soma_ufs_adiante: "Soma das UFs 3,1% à frente do arquivo nacional",
      uf_atrasada_1t: "Bahia 20 min atrás do ritmo do 1º turno",
      abstencao_atipica_mun: "Abstenção em São Paulo (SP): 31,3% contra 24,0% no 1º turno",
      abstencao_atipica_uf: "Bahia: abstenção de 24,3% contra 21,9% no 1º turno nos municípios fechados",
      secao_tardia: "Seção 45 da zona 1 de São Paulo (SP) encerrou às 18:42",
      divergencia_paralela: "BU da totalização paralela difere do oficial na seção 45 da zona 1 de São Paulo (SP)",
      paralela_conferida: "Totalização paralela: 12 BUs conferidos, 12 iguais e 0 com diferença",
      uf_fechou: "Sergipe fechou às 18:01",
    });
  });

  test("fechamento: carimbo de totalização fora da janela da geração dá lugar à geração (casos do 1º turno)", () => {
    const fechou = (totalizado_em: string, gerado_em: string, uf: string): string => e("uf_fechou", { totalizado_em, gerado_em }, { nivel: "uf", uf });
    // exterior: totalização na hora da cidade, 09:19 do dia seguinte, arquivo gerado às 22:54:52
    expect(fechou("2026-10-05T12:19:47.000Z", "2026-10-05T01:54:52.000Z", "zz")).toBe("Exterior fechou às 22:54");
    // AM: carimbo parado 120,8 min antes da versão final
    expect(fechou("2026-10-05T03:58:39.000Z", "2026-10-05T05:59:27.000Z", "am")).toBe("Amazonas fechou às 02:59");
    // caso comum: totalização 0,9 min antes da geração
    expect(fechou("2026-10-04T23:11:33.000Z", "2026-10-04T23:12:24.000Z", "df")).toBe("Distrito Federal fechou às 20:11");
  });

  test("categorias do telão e nenhum travessão", () => {
    for (const [tipo, txt, cat] of casos) {
      expect(categoria(tipo)).toBe(cat as ReturnType<typeof categoria>);
      expect(txt.includes(String.fromCharCode(0x2014))).toBe(false);
    }
    expect(categoria("pausa_global")).toBe("outro");
    expect(categoria("secoes2t_pausa")).toBe("outro");
  });
});

describe("/api/anomalias: derivação só quando não há linha gravada", () => {
  let s: Semeado;
  let srv: Servidor;

  beforeAll(() => {
    s = semear();
    s.fechar();
    const db = new Database(s.path);
    const snap = s.id("presBr3");
    db.run(
      `INSERT INTO evento (em, tipo, severidade, eleicao_cd, cargo_cd, nivel, uf, snapshot_id, detalhe) VALUES
       ('${new Date(seg(360)).toISOString()}', 'virada', 'warn', 6257, 1, 'br', NULL, ${snap}, '{"de":"280002542548","para":"280002551544","de_nome":"Lula","para_nome":"Flavio Bolsonaro"}'),
       ('${new Date(seg(101)).toISOString()}', 'uf_fechou', 'info', 6257, 1, 'uf', 'se', NULL, '{"totalizado_em":"${new Date(seg(100)).toISOString()}"}')`,
    );
    db.close();
    srv = criarServidor({ dbPath: s.path, port: 0, log: false });
  });

  afterAll(async () => {
    await srv.parar();
    s.limpar();
  });

  test("virada nacional e fechamento de SE aparecem uma vez, gravados; virada de SP segue derivada", async () => {
    const a = (await (await fetch(`${srv.url}/api/anomalias`)).json()) as { tipo: string; abr: string; derivado: boolean; texto: string; categoria: string }[];
    const viradas = a.filter((x) => x.tipo === "virada");
    expect(viradas.map((x) => [x.abr, x.derivado]).sort()).toEqual([["br", false], ["sp", true]]);
    const fechou = a.filter((x) => x.texto.startsWith("Sergipe fechou"));
    expect(fechou.map((x) => [x.tipo, x.derivado, x.categoria])).toEqual([["uf_fechou", false, "fechou"]]);
  });
});
