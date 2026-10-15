// Leitura e remontagem dos QR Codes do boletim (VRQR 6.0).
import { describe, expect, test } from "bun:test";
import { ErroQrBu, interpretarConteudo, lerParteQrBu, lerQrBu, montarQrBu, type CodigoErroQrBu } from "../src/qrbu/parse.ts";
import { EXEMPLOS, exemplo } from "./helpers.ts";

function codigoDe(f: () => unknown): CodigoErroQrBu | null {
  try {
    f();
    return null;
  } catch (e) {
    if (e instanceof ErroQrBu) return e.codigo;
    throw e;
  }
}

describe("montagem do conjunto de QR Codes", () => {
  test("separa cabeçalho, dados, HASH e ASSI", () => {
    const e = exemplo("UE2013");
    const p = lerParteQrBu(e.qrbu[1] ?? "");
    expect(p.indice).toBe(2);
    expect(p.total).toBe(2);
    expect(p.versao).toBe("6.0");
    expect(p.dados.startsWith("APTA:25 APTS:23")).toBe(true);
    expect(p.hash).toHaveLength(128);
    expect(p.assinatura?.startsWith("308188")).toBe(true);
    expect(lerParteQrBu(e.qrbu[0] ?? "").assinatura).toBeNull();
  });

  test("remonta o conteúdo devolvendo o espaço da quebra entre QR Codes", () => {
    const e = exemplo("UE2013");
    const r = montarQrBu([...e.qrbu].reverse());
    expect(r.partes.map((p) => p.indice)).toEqual([1, 2]);
    expect(r.conteudo).toContain("92:3 93:1 APTA:25 APTS:23 APTT:2 NOMI:4");
    expect(r.conteudo.split(" ").every((t) => t.includes(":"))).toBe(true);
    expect(r.ultimoHash).toBe(r.partes[1]?.hash ?? "");
    expect(r.assinatura).toBe(r.partes[1]?.assinatura ?? null);
  });

  test("leitura repetida do mesmo QR Code é descartada e contada", () => {
    const e = exemplo("UE2022");
    const r = montarQrBu([...e.qrbu, e.qrbu[0] ?? "", ` ${e.qrbu[1] ?? ""}\n`]);
    expect(r.partes.length).toBe(2);
    expect(r.duplicadosDescartados).toBe(2);
  });

  test("conjunto com índice faltando é rejeitado", () => {
    const e = exemplo("UE2013");
    expect(codigoDe(() => montarQrBu([e.qrbu[1] ?? ""]))).toBe("QR_FALTANDO");
    expect(codigoDe(() => montarQrBu([e.qrbu[0] ?? ""]))).toBe("QR_FALTANDO");
  });

  test("dois textos diferentes com o mesmo índice são rejeitados", () => {
    const e = exemplo("UE2013");
    const outro = (e.qrbu[0] ?? "").replace("COMP:4 ", "COMP:5 ");
    expect(codigoDe(() => montarQrBu([...e.qrbu, outro]))).toBe("QR_DUPLICADO");
  });

  test("totais ou versões divergentes são rejeitados", () => {
    const e = exemplo("UE2013");
    const [q1, q2] = e.qrbu as [string, string];
    expect(codigoDe(() => montarQrBu([q1, q2.replace("QRBU:2:2", "QRBU:2:3")]))).toBe("QR_TOTAL_INCONSISTENTE");
    expect(codigoDe(() => montarQrBu([q1, q2.replace("VRQR:6.0", "VRQR:6.1")]))).toBe("VERSAO_INCONSISTENTE");
  });

  test("ASSI fora do último QR Code é rejeitado", () => {
    const e = exemplo("UE2013");
    const [q1, q2] = e.qrbu as [string, string];
    expect(codigoDe(() => montarQrBu([`${q1} ASSI:ABCD`, q2]))).toBe("ASSINATURA_FORA_DO_ULTIMO");
  });

  test("último QR Code sem ASSI fica com assinatura nula", () => {
    const e = exemplo("UE2013");
    const [q1, q2] = e.qrbu as [string, string];
    expect(montarQrBu([q1, q2.replace(/ ASSI:[0-9A-F]+$/, "")]).assinatura).toBeNull();
  });

  test("texto fora do formato é rejeitado", () => {
    const e = exemplo("UE2013");
    const q1 = e.qrbu[0] ?? "";
    expect(codigoDe(() => montarQrBu([]))).toBe("SEM_QR");
    expect(codigoDe(() => lerParteQrBu("QRBU:1:1 VRQR:6.0 ORIG:VOTA"))).toBe("QR_INVALIDO");
    expect(codigoDe(() => lerParteQrBu(q1.replace(/HASH:([0-9A-F]+)/, (_m, h: string) => `HASH:${h.toLowerCase()}`)))).toBe("QR_INVALIDO");
    expect(codigoDe(() => lerParteQrBu(q1.replace("ORIG:VOTA", "ORIG:Vota")))).toBe("QR_INVALIDO");
    expect(codigoDe(() => lerParteQrBu(q1.replace("QRBU:1:2", "QRBU:3:2")))).toBe("QR_INVALIDO");
    expect(codigoDe(() => lerParteQrBu(q1.replace("QRBU:1:2", "QRBU:0:2")))).toBe("QR_INVALIDO");
  });
});

describe("interpretação do conteúdo", () => {
  test("cabeçalho completo do exemplo UE2013", () => {
    const { boletim } = lerQrBu(exemplo("UE2013").qrbu);
    expect(boletim.cabecalho).toEqual({
      ORIG: "VOTA", ORLC: "LEG", PROC: 2100, DTPL: "20261004", PLEI: 2110, TURN: 1, FASE: "S", UNFE: "AC",
      MUNI: 1392, ZONA: 9, SECA: 110, AGRE: [20], IDUE: 1671722, IDCA: "469345627286673633315116", HIQT: 1,
      HICA: [{ sequencia: 1, codigo: "469345627286673633315116" }], VERS: "10.20.0.0", LOCA: 6, APTO: 25, APTS: 23,
      APTT: 2, COMP: 4, FALT: 21, HBBM: 2, HBBG: 1, HBSB: 1, DTAB: "20261004", HRAB: "182014", DTFC: "20261004", HRFC: "185024",
    });
    expect(boletim.camposDesconhecidos).toEqual([]);
  });

  test("eleições, cargos, partidos e votos do exemplo UE2013", () => {
    const { boletim } = lerQrBu(exemplo("UE2013").qrbu);
    expect(boletim.eleicoes.map((e) => [e.IDEL, e.cargos.map((c) => c.CARG)])).toEqual([[2112, [6, 7, 5, 3]], [2111, [1]]]);
    const [federal, estadual, senado, governo] = boletim.eleicoes[0]?.cargos ?? [];
    expect(federal).toEqual({
      CARG: 6, TIPO: 1, VERC: "202606161212", votos: [],
      partidos: [
        { PART: 92, votos: [{ numero: 9202, votos: 1 }, { numero: 9203, votos: 1 }], LEGP: 0, TOTP: 2 },
        { PART: 93, votos: [{ numero: 9302, votos: 1 }], LEGP: 0, TOTP: 1 },
        { PART: 95, votos: [{ numero: 9503, votos: 1 }], LEGP: 0, TOTP: 1 },
      ],
      APTA: 25, APTS: 23, APTT: 2, NOMI: 4, LEGC: 0, BRAN: 0, NULO: 0, TOTC: 4,
    });
    expect(estadual?.partidos.map((p) => [p.PART, p.LEGP, p.TOTP])).toEqual([[92, 0, 1], [94, 1, 3]]);
    expect(estadual?.LEGC).toBe(1);
    expect(senado?.votos).toEqual([{ numero: 921, votos: 2 }, { numero: 931, votos: 2 }, { numero: 951, votos: 2 }]);
    expect([senado?.NOMI, senado?.BRAN, senado?.NULO, senado?.TOTC]).toEqual([6, 1, 1, 8]);
    // O cargo de governador começa no QR 1 e termina no QR 2.
    expect(governo).toEqual({
      CARG: 3, TIPO: 0, VERC: "202606161212", votos: [{ numero: 92, votos: 3 }, { numero: 93, votos: 1 }], partidos: [],
      APTA: 25, APTS: 23, APTT: 2, NOMI: 4, BRAN: 0, NULO: 0, TOTC: 4,
    });
    const presidente = boletim.eleicoes[1]?.cargos[0];
    expect(presidente?.votos).toEqual([{ numero: 93, votos: 2 }, { numero: 95, votos: 1 }]);
    expect([presidente?.NOMI, presidente?.BRAN, presidente?.NULO, presidente?.TOTC]).toEqual([3, 0, 1, 4]);
  });

  test("boletim do Sistema de Apuração: dois HICA, junta, turma, MAJO e PROP", () => {
    const { boletim } = lerQrBu(exemplo("imgbusa").qrbu);
    const h = boletim.cabecalho;
    expect([h.ORIG, h.HIQT, h.HICA?.length, h.JUNT, h.TURM, h.DTEM, h.HREM]).toEqual(["SA", 2, 2, 1, 1, "20261004", "204414"]);
    expect(h.APTO).toBeUndefined();
    expect(boletim.eleicoes.map((e) => [e.IDEL, e.MAJO, e.PROP])).toEqual([[2112, 4, 4], [2111, 4, undefined]]);
    const legenda = boletim.eleicoes[0]?.cargos[0]?.partidos.find((p) => p.PART === 95);
    expect(legenda).toEqual({ PART: 95, votos: [], LEGP: 1, TOTP: 1 });
  });

  test("consulta popular (TIPO 2) e três eleições no 2º turno", () => {
    const { boletim } = lerQrBu(exemplo("PresGovConMunic").qrbu);
    expect(boletim.cabecalho.TURN).toBe(2);
    expect(boletim.eleicoes.map((e) => e.IDEL)).toEqual([2122, 2121, 2123]);
    const consulta = boletim.eleicoes[2]?.cargos[0];
    expect([consulta?.CARG, consulta?.TIPO]).toEqual([53, 2]);
    expect(consulta?.votos).toEqual([{ numero: 5, votos: 2 }, { numero: 7, votos: 1 }]);
  });

  test("em todos os exemplos, cada voto do texto aparece uma única vez na estrutura", () => {
    for (const e of EXEMPLOS) {
      const { conteudo, boletim } = lerQrBu(e.qrbu);
      const votosTexto = conteudo.split(" ").filter((t) => /^\d+:\d+$/.test(t)).map((t) => Number(t.split(":")[1]));
      const votosEstrutura = boletim.eleicoes.flatMap((el) => el.cargos.flatMap((c) => [...c.votos, ...c.partidos.flatMap((p) => p.votos)]));
      expect(votosEstrutura.length).toBe(votosTexto.length);
      expect(votosEstrutura.reduce((s, v) => s + v.votos, 0)).toBe(votosTexto.reduce((s, v) => s + v, 0));
    }
  });

  const BASE = "ORIG:VOTA IDEL:1 CARG:1 TIPO:0 VERC:1 92:1 APTA:1 APTS:1 APTT:0 NOMI:1 BRAN:0 NULO:0 TOTC:1";

  test("conteúdo mínimo bem formado", () => {
    const b = interpretarConteudo(BASE);
    expect(b.eleicoes[0]?.cargos[0]?.votos).toEqual([{ numero: 92, votos: 1 }]);
  });

  test("campo desconhecido não derruba a leitura e fica registrado", () => {
    const b = interpretarConteudo(BASE.replace("ORIG:VOTA", "ORIG:VOTA XPTO:7").replace("BRAN:0", "BRAN:0 ZZZZ:1"));
    expect(b.camposDesconhecidos).toEqual([
      { chave: "XPTO", valor: "7", contexto: "cabecalho", posicao: 1 },
      { chave: "ZZZZ", valor: "1", contexto: "resumo", posicao: 12 },
    ]);
  });

  const ERRADOS: [string, string][] = [
    ["voto antes de IDEL", "ORIG:VOTA 92:1 IDEL:1"],
    ["sem eleição", "ORIG:VOTA"],
    ["termina sem TOTC", BASE.replace(" TOTC:1", "")],
    ["registro sem dois-pontos", BASE.replace("ORIG:VOTA", "ORIG")],
    ["valor vazio", BASE.replace("ORIG:VOTA", "ORIG:")],
    ["espaço duplo", BASE.replace(" IDEL", "  IDEL")],
    ["chave minúscula", BASE.replace("ORIG", "orig")],
    ["campo de cabeçalho repetido", BASE.replace("ORIG:VOTA", "ORIG:VOTA ORIG:RED")],
    ["número não numérico", BASE.replace("APTA:1", "APTA:1A")],
    ["voto depois de TOTC", `${BASE} 93:1`],
    ["voto depois do resumo", BASE.replace("NOMI:1", "NOMI:1 93:1")],
    ["LEGP fora de partido", BASE.replace("92:1", "LEGP:0")],
    ["PART sem TOTP do anterior", BASE.replace("92:1", "PART:92 9201:1 PART:93")],
    ["resumo antes do TOTP", BASE.replace("92:1", "PART:92 9201:1 LEGP:0")],
    ["CARG antes de TOTC", BASE.replace(" APTA:1", " CARG:3")],
    ["IDEL antes de TOTC", BASE.replace(" APTA:1", " IDEL:2")],
    ["TIPO depois dos votos", BASE.replace("92:1", "92:1 TIPO:1")],
    ["MAJO depois de cargo", `${BASE} MAJO:1`],
    ["resumo fora de cargo", "ORIG:VOTA IDEL:1 TOTC:1"],
    ["HICA malformado", BASE.replace("ORIG:VOTA", "ORIG:VOTA HICA:1")],
    ["resumo repetido", BASE.replace("BRAN:0", "BRAN:0 BRAN:0")],
  ];
  for (const [nome, conteudo] of ERRADOS) {
    test(`rejeita: ${nome}`, () => {
      expect(codigoDe(() => interpretarConteudo(conteudo))).toBe("CONTEUDO_INVALIDO");
    });
  }
});
