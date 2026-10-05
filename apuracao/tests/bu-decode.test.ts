// Decodificador do BU contra a fixture real da seção SP 71072/0001/0001 (1º turno de 2026)
// e contra a decodificação independente do asn1tools 0.169.0 com o bu.asn1 v2 do TSE.
import { describe, expect, test } from "bun:test";
import {
  CARGO_CONSTITUCIONAL, decodificarBu, decodificarEntidadeBu, ErroBu, lerTlv, rotulo, TIPO_URNA, TIPO_VOTO, dataHoraJe,
} from "../scripts/bu-decode.ts";
import { linhasCargo, linhasVoto } from "../scripts/secoes/banco.ts";
import { bytes, json } from "./helpers.ts";

const BU = "bu/o03220sp7107200010001-bu.dat";

describe("bu-decode", () => {
  test("reproduz a decodificação do asn1tools campo a campo", () => {
    const { envelope, bu } = decodificarBu(bytes(BU));
    const { conteudo: _c, ...env } = envelope;
    expect({ envelope: env, bu }).toEqual(json("bu/o03220sp7107200010001-bu.asn1tools.json") as never);
  });

  test("identificação, urna e totais da seção", () => {
    const { bu } = decodificarBu(bytes(BU));
    expect(bu.identificacaoSecao).toEqual({ municipioZona: { municipio: 71072, zona: 1 }, local: 1015, secao: 1 });
    expect(rotulo(TIPO_URNA, bu.urna.tipoUrna)).toBe("secao");
    expect(bu.urna.correspondenciaResultado.carga.numeroInternoUrna).toBe(2027601);
    expect(bu.urna.versaoVotacao).toBe("10.23.0.0 - Praia da Barra do Cahy");
    expect(bu.qtdEleitoresCompareceram).toBe(256);
    expect(dataHoraJe(bu.dadosSecao?.dataHoraAbertura ?? null)).toBe("2026-10-04 08:00:01");
    expect(dataHoraJe(bu.dadosSecao?.dataHoraEncerramento ?? null)).toBe("2026-10-04 17:08:42");
    const fed = bu.resultadosVotacaoPorEleicao.find((e) => e.idEleicao === 6257);
    expect(fed?.qtdEleitoresAptos).toBe(362);
    const pres = fed?.resultadosVotacao[0]?.totaisVotosCargo[0];
    expect(rotulo(CARGO_CONSTITUCIONAL, pres?.codigoCargo.valor ?? 0)).toBe("presidente");
    const por = new Map(pres?.votosVotaveis.map((v) => [`${rotulo(TIPO_VOTO, v.tipoVoto)}:${v.codigo ?? ""}`, v.quantidadeVotos]));
    expect(por.get("nominal:13")).toBe(121);
    expect(por.get("nominal:22")).toBe(96);
    expect(por.get("branco:")).toBe(2);
    expect(por.get("nulo:")).toBe(9);
  });

  test("linhas de voto e de cargo", () => {
    const { bu } = decodificarBu(bytes(BU));
    const votos = linhasVoto(bu);
    expect(votos.length).toBe(9 + 81 + 101 + 9 + 5);
    expect(votos.filter((v) => v.cargo === 1).reduce((s, v) => s + v.votos, 0)).toBe(256);
    const cargos = new Map(linhasCargo(bu).map((c) => [c.cargo, c]));
    expect(cargos.get(5)?.votos).toBe(512); // senador: duas vagas
    expect(cargos.get(1)).toEqual({ cargo: 1, eleicao: 6257, tipoCargo: 1, aptos: 362, comparecimento: 256, votos: 256 });
    expect(cargos.get(3)?.eleicao).toBe(6259);
  });

  test("estrutura fora da especificação falha com ErroBu", () => {
    const b = bytes(BU);
    expect(() => decodificarBu(b.subarray(0, b.length - 1))).toThrow(ErroBu);
    const sobra = new Uint8Array(b.length + 2);
    sobra.set(b);
    expect(() => decodificarBu(sobra)).toThrow(ErroBu);
    expect(() => decodificarEntidadeBu(new Uint8Array([0x30, 0x03, 0x02, 0x01, 0x01]))).toThrow(ErroBu);
  });

  test("BER: comprimento longo e indefinido", () => {
    const longo = new Uint8Array([0x04, 0x81, 0x02, 0xaa, 0xbb]);
    expect(lerTlv(longo, 0)).toEqual({ tag: 0x04, construido: false, ini: 3, fim: 5, prox: 5 });
    const indef = new Uint8Array([0x30, 0x80, 0x02, 0x01, 0x07, 0x00, 0x00]);
    expect(lerTlv(indef, 0)).toEqual({ tag: 0x30, construido: true, ini: 2, fim: 5, prox: 7 });
    expect(() => lerTlv(new Uint8Array([0x02, 0x80]), 0)).toThrow(ErroBu);
  });
});
