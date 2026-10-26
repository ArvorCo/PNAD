// Leitor do `.vsc` contra três arquivos reais do 2º turno de 2026: urna UE2022 (Ed521, certificado
// PEM da AC UE2022), urna UE2013 (ECDSA P-521, certificado DER da AC URNA) e sistema de apuração.
import { describe, expect, test } from "bun:test";
import type { Database } from "bun:sqlite";
import { conferirArquivo, decodificarVsc, ErroVsc, resumirVsc } from "../src/secoes2t/vsc-decode.ts";
import { abrirVsc, escolherVsc, EscritorVsc, prefixoSecao, urlAuxTurno } from "../scripts/secoes/vsc-banco.ts";
import type { ResultadoVsc } from "../scripts/secoes/vsc-banco.ts";
import { AuxSchema } from "../scripts/secoes/secao.ts";
import { bytes } from "./helpers.ts";

const UE2022 = "vsc/o03221ac0100700090001-vota.vsc";
const UE2013 = "vsc/o03221al2701400390015-vota.vsc";
const SA = "vsc/o03221zz2917300010494-sa.vsc";

describe("vsc-decode", () => {
  test("UE2022: estrutura, certificado PEM e cadeia até a AC UE2022", () => {
    const v = decodificarVsc(bytes(UE2022));
    expect(v.sw.usuario).toBe("SEVIN");
    expect(v.hw.usuario).toBe("UEAO");
    expect(v.hw.usuarioSerial).toBe("2468149");
    expect(v.modeloCodigo).toBe(22);
    expect(v.algoritmoHwCodigo).toBe(4);
    expect(v.hw.arquivos.map((a) => a.nome.split("-")[1])).toEqual([
      "bu.dat", "rdv.dat", "jufa.dat", "imgbu.dat", "imgze.dat", "hash.dat", "wsqbio.jez", "wsqman.jez", "wsqmes.jez", "mr.ver", "log.jez",
    ]);
    const r = resumirVsc(v);
    expect(r.swResumoConfere && r.hwResumoConfere && r.listasConferem).toBe(true);
    expect(r.swChaveData).toBe("202607021654");
    expect(r.certificado?.formato).toBe("PEM");
    expect(r.certificado?.titularCN).toBe("UEAO02468149");
    expect(r.certificado?.emissorCN).toBe("AC UE2022");
    expect(r.certificado?.serial).toBe("1360237");
    expect(r.certificado?.cadeiaValida).toBe(true);
    expect(r.certificado?.sha256).toBe("eaf31f6703c2bd2879dfd3a3e309d9809ed524e70c95f5841287edd15f8cb8b1");
    expect(r.cnConfereUsuario).toBe(true);
    expect(r.hwAlgoritmoNome).toBe("EdDSA Ed521");
    expect(r.hwAssinaturaValida).toBe(true);
    expect(r.hwAssinaturaBuValida).toBe(true);
  });

  test("UE2013: certificado DER, ECDSA P-521 e AC URNA", () => {
    const r = resumirVsc(decodificarVsc(bytes(UE2013)));
    expect(r.modeloCodigo).toBe(13);
    expect(r.hwSerial).toBe("1672941");
    expect(r.certificado?.formato).toBe("DER");
    expect(r.certificado?.ac).toBe("AC URNA");
    expect(r.certificado?.cadeiaValida).toBe(true);
    expect(r.hwAlgoritmoNome).toBe("ECDSA P-521");
    expect(r.hwAssinaturaValida).toBe(true);
    expect(r.hwAssinaturaBuValida).toBe(true);
  });

  test("sistema de apuração: assinado pela urna da junta, entrada busa.dat", () => {
    const r = resumirVsc(decodificarVsc(bytes(SA)));
    expect(r.modeloCodigo).toBe(15);
    expect(r.hwSerial).toBe("1808076");
    expect(r.arquivos.some((a) => a.nome.endsWith("-busa.dat"))).toBe(true);
    expect(r.hwAssinaturaValida).toBe(true);
    expect(r.hwAssinaturaBuValida).toBe(true);
  });

  test("BU publicado confere com a entrada do .vsc; um byte alterado reprova", () => {
    for (const [vsc, nome] of [[UE2022, "o03221ac0100700090001-bu.dat"], [UE2013, "o03221al2701400390015-bu.dat"]] as const) {
      const arqs = decodificarVsc(bytes(vsc)).hw.arquivos;
      const bu = bytes(`vsc/${nome}`);
      expect(conferirArquivo(arqs, nome, bu)).toBe(true);
      const mexido = bu.slice();
      mexido[100] = (mexido[100] ?? 0) ^ 1;
      expect(conferirArquivo(arqs, nome, mexido)).toBe(false);
      expect(conferirArquivo(arqs, "outro-bu.dat", bu)).toBeNull();
    }
  });

  test("assinatura alterada reprova; sem verificação fica null", () => {
    const b = bytes(UE2022);
    const v = decodificarVsc(b);
    const sig = v.hw.assinaturaConteudo;
    sig[10] = (sig[10] ?? 0) ^ 1;
    expect(resumirVsc(v).hwAssinaturaValida).toBe(false);
    expect(resumirVsc(decodificarVsc(bytes(UE2022)), { verificarAssinatura: false }).hwAssinaturaValida).toBeNull();
  });

  test("resumo de conteúdo alterado é detectado sem verificar assinatura", () => {
    const v = decodificarVsc(bytes(UE2022));
    const c = v.hw.conteudo;
    c[c.length - 1] = (c[c.length - 1] ?? 0) ^ 1;
    expect(resumirVsc(v, { verificarAssinatura: false }).hwResumoConfere).toBe(false);
  });

  test("lixo e arquivo truncado lançam", () => {
    expect(() => decodificarVsc(new Uint8Array([0x30, 0x03, 0x02, 0x01, 0x01]))).toThrow(ErroVsc);
    const b = bytes(UE2022);
    expect(() => decodificarVsc(b.subarray(0, b.length - 10))).toThrow();
  });
});

describe("vsc-banco", () => {
  const aux = AuxSchema.parse({
    hashes: [
      { hash: "aa", dr: "25/10/2026", hr: "18:00:00", arq: [{ nm: "o03221ac0100700090001-vota.vsc", tp: "vota" }, { nm: "x-bu.dat", tp: "bu" }] },
      { hash: "bb", dr: "25/10/2026", hr: "19:00:00", arq: [{ nm: "o03221ac0100700090001-sa.vsc", tp: "sa" }, { nm: "x-busa.dat", tp: "busa" }] },
    ],
  });

  test("escolhe o .vsc do hash do BU; sem ele, o mais recente", () => {
    expect(escolherVsc(aux, "aa")).toMatchObject({ hash: "aa", origem: "vota", nHashes: 2 });
    expect(escolherVsc(aux, null)).toMatchObject({ hash: "bb", origem: "sa" });
    expect(escolherVsc(AuxSchema.parse({ hashes: [{ hash: "cc", arq: [{ nm: "x-bu.dat", tp: "bu" }] }] }), "cc")).toBeNull();
  });

  test("URLs e prefixo por turno", () => {
    const s = { turno: 1 as const, uf: "ac", mun: "01007", zona: 9, secao: 1, nsp: null };
    expect(urlAuxTurno(s)).toBe("https://resultados.tse.jus.br/oficial/ele2026/arquivo-urna/3220/dados/ac/01007/0009/0001/p003220-ac-m01007-z0009-s0001-aux.json");
    expect(prefixoSecao({ ...s, turno: 2 })).toBe("o03221ac0100700090001");
  });

  test("grava resumo, certificado e arquivos", () => {
    const db: Database = abrirVsc(":memory:");
    const resumo = resumirVsc(decodificarVsc(bytes(UE2022)));
    const r: ResultadoVsc = {
      turno: 2, uf: "ac", mun: "01007", zona: 9, secao: 1, nsp: null, status: "ok", auxProprio: null,
      escolha: { hash: "aa", nome: "o03221ac0100700090001-vota.vsc", origem: "vota", recebidoEm: "2026-10-25 19:57:33", nHashes: 1 },
      mesmoHashBu: true, bytes: 62605, sha256: "x", gz: null, resumo, buNome: "o03221ac0100700090001-bu.dat", buConfere: true, erro: null, requisicoes: 1,
    };
    new EscritorVsc(db).gravar([r], "2026-10-26T10:00:00Z");
    const l = db.query<Record<string, unknown>, []>("SELECT * FROM vsc").get();
    expect(l).toMatchObject({ hw_serial: "2468149", cert_titular_cn: "UEAO02468149", ac: "AC UE2022", cadeia_valida: 1, hw_assinatura_ok: 1, bu_confere_vsc: 1, n_arquivos: 11 });
    const arqs = db.query<{ sufixo: string; nome_confere: number }, []>("SELECT sufixo, nome_confere FROM vsc_arquivo ORDER BY ordem").all();
    expect(arqs).toHaveLength(11);
    expect(arqs.every((x) => x.nome_confere === 1)).toBe(true);
    expect(arqs[0]?.sufixo).toBe("bu.dat");
  });
});
