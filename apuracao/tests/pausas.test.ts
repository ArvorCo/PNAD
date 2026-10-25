// Detector de pausas: início, fim, escalada, soma das UFs adiante, retomada do banco e nenhum
// falso positivo quando o país inteiro está parado (100% ou sem avanço em nenhum arquivo).
import { describe, expect, test } from "bun:test";
import { DetectorPausas, PAUSAS_PADRAO } from "../src/collector/pausas.ts";
import type { Frescor } from "../src/collector/pausas.ts";
import { abrirEscrita } from "../src/db/abrir.ts";
import { Escritor } from "../src/db/escrita.ts";
import type { ItemLote, LinhaPausa } from "../src/db/escrita.ts";
import { semearVersoes } from "./helpers-2t.ts";

const T0 = Date.parse("2026-10-25T20:00:00.000Z");
const m = (min: number): number => T0 + min * 60_000;
const iso = (ms: number): string => new Date(ms).toISOString();
const sempre: Frescor = () => true;

const eventos = (itens: readonly ItemLote[]): { tipo: string; severidade: string | undefined; uf: string | null | undefined; detalhe: Record<string, unknown> }[] =>
  itens.flatMap((x) => (x.k === "evento" ? [{ tipo: x.row.tipo, severidade: x.row.severidade, uf: x.row.uf, detalhe: x.row.detalhe as Record<string, unknown> }] : []));
const pausasDe = (itens: readonly ItemLote[]): LinhaPausa[] => itens.flatMap((x) => (x.k === "pausa" ? [x.row] : []));

/** Sem folga de entrega do CDN, para os tempos dos testes ficarem redondos (a folga tem teste próprio). */
function novo(folgaMin = 0): DetectorPausas {
  return new DetectorPausas({ ...PAUSAS_PADRAO, ele: 6258, folgaMin });
}

/** Três UFs avançando juntas a cada minuto até `ate`; o nacional acompanha até `brAte`. */
function apuracao(d: DetectorPausas, ate: number, brAte: number, ts = 1000): void {
  for (let i = 1; i <= ate; i++) {
    for (const uf of ["sp", "mg", "ba"]) d.observar(uf, { geradoMs: m(i), st: Math.min(ts, i * 10), ts }, iso(m(i)));
    if (i <= brAte) d.observar(null, { geradoMs: m(i), st: Math.min(3 * ts, i * 30), ts: 3 * ts }, iso(m(i)));
  }
}

describe("pausa nacional", () => {
  test("início depois de 5 min parado com UFs avançando, fim na versão nova", () => {
    const d = novo();
    apuracao(d, 10, 4);
    expect(eventos(d.avaliar(m(9), sempre))).toEqual([]); // 5 min exatos não passa do limiar
    const it = d.avaliar(m(9.5), sempre);
    const ev = eventos(it);
    expect(ev.map((e) => e.tipo)).toEqual(["pausa_nacional_inicio"]);
    expect(ev[0]?.severidade).toBe("warn");
    expect(ev[0]?.detalhe).toMatchObject({ desde: iso(m(4)), minutos: 5.5, st: 120, ts: 3000, soma_ufs_st: 300, soma_ufs_st_antes: 120 });
    expect(pausasDe(it)).toEqual([{ nivel: "nacional", uf: null, de: iso(m(4)), ate: null, minutos: null, st_antes: 120, st_depois: null, detectado_em: iso(m(9.5)) }]);
    expect(eventos(d.avaliar(m(10), sempre))).toEqual([]); // não repete
    const fim = d.observar(null, { geradoMs: m(11), st: 330, ts: 3000 }, iso(m(11)));
    expect(eventos(fim).map((e) => [e.tipo, e.severidade, e.detalhe.minutos])).toEqual([["pausa_nacional_fim", "info", 7]]);
    expect(pausasDe(fim)[0]).toMatchObject({ ate: iso(m(11)), minutos: 7, st_antes: 120, st_depois: 330 });
    expect(d.aberta(null)).toBeNull();
  });

  test("escala para error uma vez ao passar de 15 min", () => {
    const d = novo();
    apuracao(d, 30, 4);
    const pausa = (it: readonly ItemLote[]): [string, string | undefined][] => eventos(it).filter((e) => e.tipo.startsWith("pausa_")).map((e) => [e.tipo, e.severidade]);
    expect(pausa(d.avaliar(m(10), sempre))).toEqual([["pausa_nacional_inicio", "warn"]]);
    expect(pausa(d.avaliar(m(18), sempre))).toEqual([]);
    expect(pausa(d.avaliar(m(19.5), sempre))).toEqual([["pausa_nacional_longa", "error"]]);
    expect(pausa(d.avaliar(m(25), sempre))).toEqual([]);
  });

  test("detectada já longa (coletor religado tarde) sai como error", () => {
    const d = novo();
    apuracao(d, 30, 4);
    const ev = eventos(d.avaliar(m(25), sempre)).filter((e) => e.tipo === "pausa_nacional_inicio");
    expect(ev[0]?.severidade).toBe("error");
  });

  test("sem falso positivo: país inteiro 100% (nacional com st = ts)", () => {
    const d = novo();
    for (const uf of ["sp", "mg"]) d.observar(uf, { geradoMs: m(1), st: 1000, ts: 1000 }, iso(m(1)));
    d.observar(null, { geradoMs: m(1), st: 2000, ts: 2000 }, iso(m(1)));
    expect(d.avaliar(m(60), sempre)).toEqual([]);
  });

  test("sem falso positivo: nenhum arquivo avança (só a pausa geral)", () => {
    const d = novo();
    apuracao(d, 5, 5);
    const ev = eventos(d.avaliar(m(30), sempre));
    expect(ev.map((e) => [e.tipo, e.severidade])).toEqual([["pausa_geral_inicio", "error"]]);
  });

  test("coletor cego (arquivo sem leitura recente) não vira pausa", () => {
    const d = novo();
    apuracao(d, 10, 4);
    expect(d.avaliar(m(9.5), () => false)).toEqual([]);
  });
});

describe("pausa geral e por UF", () => {
  test("geral abre quando nada publica e fecha na primeira versão de qualquer arquivo", () => {
    const d = novo();
    apuracao(d, 5, 5);
    const it = d.avaliar(m(10.5), sempre);
    expect(eventos(it).map((e) => e.tipo)).toEqual(["pausa_geral_inicio"]);
    expect(pausasDe(it)[0]).toMatchObject({ nivel: "geral", de: iso(m(5)), st_antes: 150 });
    const fim = d.observar("mg", { geradoMs: m(12), st: 60, ts: 1000 }, iso(m(12)));
    expect(eventos(fim).map((e) => [e.tipo, e.detalhe.minutos])).toEqual([["pausa_geral_fim", 7]]);
  });

  test("geral não abre no fim da noite, com menos de 100 seções faltando no país", () => {
    const d = novo();
    // três UFs com 1.000 seções cada: 2.950 totalizadas, faltam 50
    for (const [uf, st] of [["sp", 1000], ["mg", 1000], ["ba", 950]] as const) d.observar(uf, { geradoMs: m(5), st, ts: 1000 }, iso(m(5)));
    d.observar(null, { geradoMs: m(5), st: 2950, ts: 3000 }, iso(m(5)));
    const it = d.avaliar(m(30), sempre);
    expect(eventos(it).filter((e) => e.tipo.startsWith("pausa_geral"))).toEqual([]);
    expect(d.aberta("geral")).toBeNull();
    // com 100 faltando, a regra volta a valer
    const d2 = novo();
    for (const [uf, st] of [["sp", 1000], ["mg", 1000], ["ba", 900]] as const) d2.observar(uf, { geradoMs: m(5), st, ts: 1000 }, iso(m(5)));
    expect(eventos(d2.avaliar(m(30), sempre)).map((e) => e.tipo)).toContain("pausa_geral_inicio");
  });

  test("geral não abre antes da primeira seção nem com tudo apurado", () => {
    const d = novo();
    d.observar("sp", { geradoMs: m(-60), st: 0, ts: 1000 }, iso(m(-60)));
    d.observar(null, { geradoMs: m(-60), st: 0, ts: 1000 }, iso(m(-60)));
    expect(d.avaliar(m(10), sempre)).toEqual([]);
  });

  test("UF parada mais de 10 min enquanto as outras andam", () => {
    const d = novo();
    for (let i = 1; i <= 20; i++) {
      d.observar("sp", { geradoMs: m(i), st: i * 10, ts: 1000 }, iso(m(i)));
      d.observar(null, { geradoMs: m(i), st: i * 20, ts: 2000 }, iso(m(i)));
      if (i <= 5) d.observar("ba", { geradoMs: m(i), st: i * 10, ts: 1000 }, iso(m(i)));
    }
    expect(eventos(d.avaliar(m(15), sempre))).toEqual([]);
    const ev = eventos(d.avaliar(m(15.5), sempre));
    expect(ev.map((e) => [e.tipo, e.uf])).toEqual([["pausa_uf_inicio", "ba"]]);
    expect(ev[0]?.detalhe).toMatchObject({ desde: iso(m(5)), minutos: 10.5, st: 50, ts: 1000, outras_ufs_st: 200, outras_ufs_st_antes: 50 });
    const fim = eventos(d.observar("ba", { geradoMs: m(21), st: 80, ts: 1000 }, iso(m(21))));
    expect(fim.map((e) => [e.tipo, e.uf, e.detalhe.minutos])).toEqual([["pausa_uf_fim", "ba", 16]]);
  });

  test("UF já fechada (st = ts) não entra em pausa", () => {
    const d = novo();
    d.observar("ba", { geradoMs: m(1), st: 1000, ts: 1000 }, iso(m(1)));
    for (let i = 1; i <= 30; i++) d.observar("sp", { geradoMs: m(i), st: i * 10, ts: 1000 }, iso(m(i)));
    expect(eventos(d.avaliar(m(30), sempre)).filter((e) => e.uf === "ba")).toEqual([]);
  });

  test("versão repetida ou mais velha não conta como nova", () => {
    const d = novo();
    apuracao(d, 10, 4);
    d.avaliar(m(9.5), sempre);
    expect(d.observar(null, { geradoMs: m(4), st: 120, ts: 3000 }, iso(m(10)))).toEqual([]);
    expect(d.aberta(null)).not.toBeNull();
  });
});

describe("regras que o replay do 1º turno exigiu", () => {
  test("folga de entrega do CDN: abre só depois do limiar mais a folga", () => {
    const d = novo(1);
    apuracao(d, 12, 4);
    expect(eventos(d.avaliar(m(9.5), sempre)).filter((e) => e.tipo.startsWith("pausa_"))).toEqual([]);
    expect(eventos(d.avaliar(m(10.5), sempre)).map((e) => e.tipo)).toContain("pausa_nacional_inicio");
  });

  test("travamento geral com retomada escalonada não vira pausa de UF em cascata", () => {
    const d = novo(1);
    const ufs = ["sp", "mg", "ba", "rj", "pr"];
    // todas publicam a cada minuto até ~10 min, param juntas e voltam entre 20 e 22,5 min
    for (let i = 1; i <= 10; i++) {
      ufs.forEach((uf, k) => d.observar(uf, { geradoMs: m(i) + k * 3000, st: i * 10, ts: 1000 }, iso(m(i) + k * 3000)));
      d.observar(null, { geradoMs: m(i), st: i * 50, ts: 5000 }, iso(m(i)));
    }
    const tipos: string[] = [];
    for (let t = 10.5; t <= 25; t += 0.5) {
      ufs.forEach((uf, k) => {
        const volta = 20 + k * 0.6;
        if (t >= volta + 1 && t - 0.5 < volta + 1) tipos.push(...eventos(d.observar(uf, { geradoMs: m(volta), st: 200, ts: 1000 }, iso(m(volta + 1)))).map((e) => e.tipo));
      });
      tipos.push(...eventos(d.avaliar(m(t), sempre)).map((e) => e.tipo));
    }
    expect(tipos.filter((x) => x === "pausa_uf_inicio")).toEqual([]);
    expect(tipos).toContain("pausa_geral_inicio");
    expect(tipos).toContain("pausa_geral_fim");
  });

  test("UFs publicando devagar (idade mediana acima da metade do limiar) não contam como país avançando", () => {
    const d = novo();
    for (let i = 0; i <= 30; i += 6) d.observar("sp", { geradoMs: m(i), st: i * 10, ts: 1000 }, iso(m(i)));
    d.observar("ba", { geradoMs: m(0), st: 5, ts: 1000 }, iso(m(0)));
    expect(eventos(d.avaliar(m(30.5), sempre)).filter((e) => e.tipo === "pausa_uf_inicio")).toEqual([]);
  });

  test("versão entregue tarde pelo CDN (gerada antes do limiar) não encerra a pausa", () => {
    const d = novo();
    apuracao(d, 12, 4);
    d.avaliar(m(9.5), sempre);
    expect(d.observar(null, { geradoMs: m(4.1), st: 130, ts: 3000 }, iso(m(12)))).toEqual([]);
    expect(d.aberta(null)?.de).toBe(iso(m(4)));
    expect(eventos(d.observar(null, { geradoMs: m(12.5), st: 360, ts: 3000 }, iso(m(12.6)))).map((e) => e.tipo)).toEqual(["pausa_nacional_fim"]);
  });
});

describe("soma das UFs adiante do nacional", () => {
  test("mais de 2% de ts por mais de 5 min: um evento; volta ao normal e pode repetir", () => {
    const d = novo();
    for (const uf of ["sp", "mg"]) d.observar(uf, { geradoMs: m(1), st: 100, ts: 1000 }, iso(m(1)));
    d.observar(null, { geradoMs: m(1), st: 150, ts: 2000 }, iso(m(1))); // 50/2000 = 2,5%
    expect(eventos(d.avaliar(m(2), () => false))).toEqual([]);
    expect(eventos(d.avaliar(m(7), () => false))).toEqual([]);
    const ev = eventos(d.avaliar(m(7.5), () => false));
    expect(ev.map((e) => e.tipo)).toEqual(["soma_ufs_adiante"]);
    expect(ev[0]?.detalhe).toMatchObject({ soma_ufs_st: 200, st: 150, ts: 2000, diferenca_secoes: 50, diferenca_pct: 2.5, minutos: 5.5 });
    expect(eventos(d.avaliar(m(9), () => false))).toEqual([]);
    d.observar(null, { geradoMs: m(10), st: 200, ts: 2000 }, iso(m(10)));
    d.avaliar(m(10), () => false);
    d.observar("sp", { geradoMs: m(11), st: 200, ts: 1000 }, iso(m(11)));
    d.avaliar(m(11), () => false);
    expect(eventos(d.avaliar(m(17), () => false)).map((e) => e.tipo)).toEqual(["soma_ufs_adiante"]);
  });
});

describe("persistência", () => {
  test("pausa abre e fecha na tabela pela mesma chave", () => {
    const db = abrirEscrita(":memory:");
    const w = new Escritor(db);
    const d = novo();
    apuracao(d, 10, 4);
    w.gravarLote(d.avaliar(m(9.5), sempre));
    expect(db.query("SELECT nivel, uf, de, ate, minutos FROM pausa").all()).toEqual([{ nivel: "nacional", uf: null, de: iso(m(4)), ate: null, minutos: null }]);
    w.gravarLote(d.observar(null, { geradoMs: m(11), st: 330, ts: 3000 }, iso(m(11))));
    expect(db.query("SELECT nivel, de, ate, minutos, st_antes, st_depois FROM pausa").all()).toEqual([
      { nivel: "nacional", de: iso(m(4)), ate: iso(m(11)), minutos: 7, st_antes: 120, st_depois: 330 },
    ]);
    expect(db.query("SELECT tipo, severidade, nivel FROM evento ORDER BY id").all()).toEqual([
      { tipo: "pausa_nacional_inicio", severidade: "warn", nivel: "br" },
      { tipo: "pausa_nacional_fim", severidade: "info", nivel: "br" },
    ]);
  });

  test("reinício: histórico e pausa aberta voltam do banco; versão gravada depois fecha na partida", () => {
    const db = abrirEscrita(":memory:");
    const versoes = [];
    for (let i = 1; i <= 10; i++) {
      for (const uf of ["sp", "mg"]) versoes.push({ nivel: "uf" as const, uf, gerado: iso(m(i)), st: i * 10, ts: 1000 });
      if (i <= 4) versoes.push({ nivel: "br" as const, gerado: iso(m(i)), st: i * 20, ts: 2000 });
    }
    semearVersoes(db, 6258, versoes);
    const w = new Escritor(db);
    const d1 = novo();
    w.gravarLote(d1.carregar(db, m(10)));
    w.gravarLote(d1.avaliar(m(10), sempre));
    expect(d1.aberta(null)?.de).toBe(iso(m(4)));

    const d2 = novo();
    expect(d2.carregar(db, m(11))).toEqual([]);
    expect(d2.aberta(null)?.de).toBe(iso(m(4)));
    expect(eventos(d2.avaliar(m(11), sempre)).filter((e) => e.tipo === "pausa_nacional_inicio")).toEqual([]);

    semearVersoes(db, 6258, [{ nivel: "br", gerado: iso(m(12)), st: 200, ts: 2000 }]);
    const d3 = novo();
    const it = d3.carregar(db, m(13));
    expect(eventos(it).map((e) => e.tipo)).toEqual(["pausa_nacional_fim"]);
    expect(pausasDe(it)[0]).toMatchObject({ ate: iso(m(12)), minutos: 8, st_depois: 200 });
    expect(d3.aberta(null)).toBeNull();
  });
});
