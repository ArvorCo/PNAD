// Validação estrutural: somas, campos obrigatórios por origem e parâmetros do pleito.
import { describe, expect, test } from "bun:test";
import { interpretarConteudo, lerQrBu, type BoletimQr } from "../src/qrbu/parse.ts";
import { dataValida, horaValida, PERFIL_2T_2026, validarBoletim } from "../src/qrbu/validar.ts";
import { EXEMPLOS, exemplo } from "./helpers.ts";

function codigos(bu: BoletimQr, opcoes = {}): string[] {
  return validarBoletim(bu, { faseEsperada: "S", ...opcoes }).map((p) => p.codigo);
}

function copia(trecho: string): BoletimQr {
  return structuredClone(lerQrBu(exemplo(trecho).qrbu).boletim);
}

function cargo(bu: BoletimQr, idel: number, carg: number) {
  const c = bu.eleicoes.find((e) => e.IDEL === idel)?.cargos.find((x) => x.CARG === carg);
  if (!c) throw new Error(`cargo ${carg} da eleição ${idel} ausente`);
  return c;
}

// Boletim do 2º turno oficial de 25/10/2026 com os números do pleito informados pela coordenação.
const SEGUNDO_TURNO =
  "ORIG:VOTA ORLC:LEG PROC:1219 DTPL:20261025 PLEI:3221 TURN:2 FASE:O UNFE:SP MUNI:71072 ZONA:1 SECA:1 " +
  "IDUE:2250280 IDCA:593008544829562943979539 HIQT:1 HICA:1:593008544829562943979539 VERS:10.23.0.0 LOCA:1015 " +
  "APTO:300 APTS:298 APTT:2 COMP:250 FALT:50 HBBM:240 HBBG:8 HBSB:2 DTAB:20261025 HRAB:080001 DTFC:20261025 HRFC:170842 " +
  "IDEL:6260 CARG:3 TIPO:0 VERC:202610101200 10:120 22:110 APTA:298 APTS:298 APTT:0 NOMI:230 BRAN:8 NULO:10 TOTC:248 " +
  "IDEL:6258 CARG:1 TIPO:0 VERC:202610101200 13:125 22:110 APTA:300 APTS:298 APTT:2 NOMI:235 BRAN:6 NULO:9 TOTC:250";

describe("validação estrutural", () => {
  for (const e of EXEMPLOS) {
    test(`nenhum problema em ${e.arquivo.split("/").pop()} (fase simulada)`, () => {
      expect(validarBoletim(lerQrBu(e.qrbu).boletim, { faseEsperada: "S" })).toEqual([]);
    });
  }

  test("fase oficial é o padrão: exemplos simulados acusam FASE_INESPERADA", () => {
    const p = validarBoletim(lerQrBu(exemplo("UE2013").qrbu).boletim);
    expect(p).toEqual([{ codigo: "FASE_INESPERADA", mensagem: 'fase "S" diferente da esperada "O" (O oficial, S simulado, T treinamento)' }]);
  });

  test("turno, data, processo e pleito esperados", () => {
    const bu = copia("UE2013");
    expect(codigos(bu, { turno: 1, dataPleito: "20261004", processo: 2100, pleito: 2110 })).toEqual([]);
    expect(codigos(bu, { turno: 2, dataPleito: "20261025", processo: 1219, pleito: 3221 })).toEqual([
      "TURNO_INESPERADO", "DATA_PLEITO_INESPERADA", "PROCESSO_INESPERADO", "PLEITO_INESPERADO",
    ]);
  });

  test("perfil do 2º turno de 2026 aceita o boletim real e recusa os exemplos simulados", () => {
    const real = interpretarConteudo(SEGUNDO_TURNO);
    expect(validarBoletim(real, PERFIL_2T_2026)).toEqual([]);
    const soPresidente = interpretarConteudo(SEGUNDO_TURNO.replace(/IDEL:6260 .*? TOTC:248 /, ""));
    expect(validarBoletim(soPresidente, PERFIL_2T_2026)).toEqual([]);
    const simulado = validarBoletim(lerQrBu(exemplo("PresGov-T2").qrbu).boletim, PERFIL_2T_2026).map((p) => p.codigo);
    // O exemplo simulado já usa a data de 25/10/2026; processo, pleito, fase e eleições diferem.
    expect(simulado).toEqual(["FASE_INESPERADA", "PROCESSO_INESPERADO", "PLEITO_INESPERADO", "ELEICAO_INESPERADA", "ELEICAO_INESPERADA"]);
    const cargoErrado = interpretarConteudo(SEGUNDO_TURNO.replace("IDEL:6258 CARG:1", "IDEL:6258 CARG:3"));
    expect(validarBoletim(cargoErrado, PERFIL_2T_2026).map((p) => p.codigo)).toEqual(["CARGO_INESPERADO"]);
  });

  test("Senado com duas vagas: TOTC chega a 2 × COMP sem problema, e passa disso com problema", () => {
    const bu = copia("UE2013");
    const senado = cargo(bu, 2112, 5);
    expect(senado.TOTC).toBe(8);
    expect(codigos(bu)).toEqual([]);
    expect(codigos(bu, { votosPorEleitor: {} })).toEqual(["TOTAL_ACIMA_DO_COMPARECIMENTO"]);
    senado.BRAN = (senado.BRAN ?? 0) + 1;
    senado.TOTC = 9;
    expect(codigos(bu)).toEqual(["TOTAL_ACIMA_DO_COMPARECIMENTO"]);
  });

  test("somas que não fecham", () => {
    const bu = copia("UE2013");
    const presidente = cargo(bu, 2111, 1);
    presidente.votos[0] = { numero: 93, votos: 3 };
    expect(codigos(bu)).toEqual(["NOMINAIS_NAO_FECHAM"]);
    presidente.NOMI = 4;
    expect(codigos(bu)).toEqual(["TOTAL_NAO_FECHA"]);
    presidente.TOTC = 5;
    expect(codigos(bu)).toEqual(["TOTAL_ACIMA_DO_COMPARECIMENTO"]);
  });

  test("partidos e legendas", () => {
    const bu = copia("UE2013");
    const estadual = cargo(bu, 2112, 7);
    const p94 = estadual.partidos.find((p) => p.PART === 94);
    if (!p94) throw new Error("partido 94 ausente");
    p94.LEGP = 2;
    // TOTC fecha com o LEGC declarado; o que não fecha é o partido e a soma das legendas.
    expect(codigos(bu)).toEqual(["PARTIDO_NAO_FECHA", "LEGENDA_NAO_FECHA"]);
    p94.LEGP = 1;
    p94.votos[0] = { numero: 92009, votos: 1 };
    expect(codigos(bu)).toEqual(["CANDIDATO_FORA_DO_PARTIDO"]);
    p94.votos[0] = { numero: 94003, votos: 1 };
    expect(codigos(bu)).toEqual(["CANDIDATO_REPETIDO"]);
  });

  test("comparecimento e aptos da seção", () => {
    const bu = copia("UE2022");
    bu.cabecalho.COMP = 30;
    expect(codigos(bu)).toEqual(expect.arrayContaining(["COMPARECIMENTO_ACIMA_DE_APTOS", "COMPARECIMENTO_NAO_FECHA"]));
    const outro = copia("UE2022");
    outro.cabecalho.APTT = 3;
    expect(codigos(outro)).toEqual(["APTOS_NAO_FECHAM"]);
    const hab = copia("UE2022");
    hab.cabecalho.HBBM = 10;
    expect(codigos(hab)).toEqual(["HABILITADOS_ACIMA_DO_COMPARECIMENTO"]);
  });

  test("campos obrigatórios e exclusivos por origem", () => {
    const vota = copia("UE2020");
    delete vota.cabecalho.COMP;
    vota.cabecalho.JUNT = 1;
    expect(codigos(vota)).toEqual(["CAMPO_DE_OUTRA_ORIGEM", "CAMPO_OBRIGATORIO_AUSENTE"]);
    const sa = copia("imgbusa");
    delete sa.cabecalho.JUNT;
    expect(codigos(sa)).toEqual(["CAMPO_OBRIGATORIO_AUSENTE"]);
    const red = copia("RED_");
    delete red.cabecalho.DTEM;
    expect(codigos(red)).toEqual(["CAMPO_OBRIGATORIO_AUSENTE"]);
    const vota2 = copia("UE2015");
    vota2.eleicoes[0] = { ...(vota2.eleicoes[0] ?? { IDEL: 0, cargos: [] }), MAJO: 4 };
    expect(codigos(vota2)).toEqual(["CAMPO_DE_OUTRA_ORIGEM"]);
  });

  test("datas, horas, carga e seções agregadas", () => {
    const bu = copia("UE2013");
    bu.cabecalho.DTAB = "20261003";
    bu.cabecalho.HRFC = "246000";
    bu.cabecalho.HIQT = 2;
    bu.cabecalho.AGRE = [20, 110];
    expect(codigos(bu)).toEqual(["HORA_INVALIDA", "ABERTURA_FORA_DO_DIA", "HISTORICO_CARGA_INCONSISTENTE", "AGREGADAS_REPETIDAS"]);
    const fecha = copia("UE2013");
    fecha.cabecalho.HRFC = "170000";
    expect(codigos(fecha)).toEqual(["FECHAMENTO_ANTES_DA_ABERTURA"]);
    expect([dataValida("20261004"), dataValida("20260230"), dataValida("2026104")]).toEqual([true, false, false]);
    expect([horaValida("235959"), horaValida("240000"), horaValida("2359")]).toEqual([true, false, false]);
  });

  test("tipo de cargo e blocos de partido coerentes", () => {
    const bu = copia("UE2013");
    const federal = cargo(bu, 2112, 6);
    federal.TIPO = 0;
    expect(codigos(bu)).toEqual(["LEGENDA_EM_CARGO_NAO_PROPORCIONAL", "PARTIDO_EM_CARGO_NAO_PROPORCIONAL"]);
    const outro = copia("UE2013");
    cargo(outro, 2111, 1).TIPO = 7;
    expect(codigos(outro)).toEqual(["TIPO_CARGO_INVALIDO"]);
  });

  test("campos desconhecidos viram problema", () => {
    const bu = copia("UE2013");
    bu.camposDesconhecidos.push({ chave: "XPTO", valor: "1", contexto: "cabecalho", posicao: 3 });
    expect(codigos(bu)).toEqual(["CAMPO_DESCONHECIDO"]);
  });

  test("mensagens em português e sem travessão", () => {
    const bu = copia("UE2013");
    cargo(bu, 2111, 1).NOMI = 9;
    const todas = validarBoletim(bu).map((p) => p.mensagem).join("\n");
    expect(todas).toContain("eleição 2111, cargo 1");
    expect(todas.includes(String.fromCharCode(0x2014))).toBe(false);
  });
});
