// Parte (b) da demonstração do 2º turno (scripts/demonstrar-2t.ts) com BUs reais pequenos: o BU
// oficial de SP 71072, zona 1, seção 1 (o mesmo de tests/secoes2t.test.ts) e o boletim do Sistema
// de Apuração de Katmandu, zona 1, seção 494 (tests/fixtures/2t-motor/bu-zz2917300010494-busa.json).
// O BU decodificado vira o registro da totalização paralela, passa pela conferência campo a campo
// e pela ponte real, e o texto do evento sai da rota /api/anomalias.
import { afterAll, describe, expect, test } from "bun:test";
import { readFileSync, rmSync } from "node:fs";
import { join } from "node:path";
import { cargosDoBu } from "../src/paralela/conferir.ts";
import type { CargoPublico, VotoPublico } from "../src/paralela/conferir.ts";
import {
  comComparecimento, compararComOficial, conferirPelaPonte, montarCasos, moverVoto, origemQr, registroParalela, rotulos, secaoReal,
} from "../scripts/demonstrar_2t/bu-real.ts";
import { BU_FIXTURE, DIR_2T, fixture2t, tmp } from "./helpers-2t.ts";

const dirs: string[] = [];
afterAll(() => {
  for (const d of dirs) rmSync(d, { recursive: true, force: true });
});

const aux = new TextEncoder().encode(JSON.stringify(fixture2t("aux-sp71072-z0001-s0001.json")));
const sp = secaoReal({ uf: "sp", mun: "71072", zona: 1, secao: 1 }, "São Paulo", aux, new Uint8Array(readFileSync(BU_FIXTURE)));
const OPC = { recebidoEm: "2026-10-04T23:50:00.000Z", hashFinal: "teste" };

interface FixtureBu {
  arquivo: string;
  secao: { uf: string; mun: string; zona: number; secao: number };
  sha256: string;
  base64: string;
}
const zzFix = JSON.parse(readFileSync(join(DIR_2T, "bu-zz2917300010494-busa.json"), "utf8")) as FixtureBu;
const zzBu = new Uint8Array(Buffer.from(zzFix.base64, "base64"));
const zzAux = new TextEncoder().encode(
  JSON.stringify({ st: "Recebida", hashes: [{ hash: "h", dr: "04/10/2026", hr: "20:00:58", arq: [{ nm: zzFix.arquivo, tp: "busa" }] }] }),
);
const zz = secaoReal(zzFix.secao, "Katmandu", zzAux, zzBu);

describe("BU real no formato da totalização paralela", () => {
  test("o registro do BU de SP reproduz as linhas das views da fixture da paralela (bu 101)", () => {
    const r = registroParalela(sp.boletim, sp.s, 101, OPC);
    const semTipo = ({ tipo: _t, ...c }: CargoPublico): Omit<CargoPublico, "tipo"> => c;
    const cargosFix = (fixture2t("v_bu_cargo_publico.json") as CargoPublico[]).filter((c) => c.bu_id === 101);
    const votosFix = (fixture2t("v_bu_voto_publico.json") as VotoPublico[]).filter((v) => v.bu_id === 101);
    expect(r.cargos.map(semTipo)).toEqual(cargosFix.map(semTipo));
    expect(cargosDoBu(r.cargos, r.votos)).toEqual(cargosDoBu(cargosFix, votosFix));
    expect(r.bu).toMatchObject({ uf: "sp", muni: 71072, zona: 1, secao: 1, fase: "O", orig: "VOTA", aptos: 362, comparecimento: 256 });
    expect(compararComOficial(r, sp)).toEqual([]);
  });

  test("um voto movido e o comparecimento mais 1 aparecem campo a campo", () => {
    const base = registroParalela(sp.boletim, sp.s, 1, OPC);
    const m = moverVoto(base);
    expect([m.de, m.para, m.antes]).toEqual(["13", "22", [121, 96]]);
    const dif = compararComOficial(m.reg, sp);
    expect(dif).toEqual([
      { campo: "nominal", idel: 6257, cargo: 1, chave: "13", paralela: 120, tse: 121 },
      { campo: "nominal", idel: 6257, cargo: 1, chave: "22", paralela: 97, tse: 96 },
    ]);
    expect(rotulos(dif)).toEqual(["presidente: votos no 13", "presidente: votos no 22"]);
    const c = comComparecimento(base, 1);
    expect(c.campo).toBe("COMP");
    expect(compararComOficial(c.reg, sp)).toEqual([{ campo: "comparecimento", idel: null, cargo: null, chave: null, paralela: 257, tse: 256 }]);
    expect(compararComOficial(base, sp)).toEqual([]); // as cópias não alteram o registro de origem
  });

  test("boletim do Sistema de Apuração: QR sem COMP nem APTO, comparecimento alterado no cargo", () => {
    expect(new Bun.CryptoHasher("sha256").update(zzBu).digest("hex")).toBe(zzFix.sha256);
    expect(origemQr(zz.boletim)).toBe("SA");
    expect(zz.boletim.qtdEleitoresCompareceram).toBe(0);
    const r = registroParalela(zz.boletim, zz.s, 7, OPC);
    expect(r.bu).toMatchObject({ orig: "SA", aptos: null, comparecimento: null });
    expect(compararComOficial(r, zz)).toEqual([]);
    const c = comComparecimento(r, 1);
    expect(c.campo).toBe("TOTC");
    expect(rotulos(compararComOficial(c.reg, zz))).toEqual(["presidente: comparecimento"]);
  });
});

describe("conferência pela ponte real", () => {
  test("igual, divergente e TSE sem aux.json; texto do evento pela rota /api/anomalias", async () => {
    const dir = tmp("demonstracao-2t-");
    dirs.push(dir);
    const semAux = secaoReal({ uf: "sp", mun: "71072", zona: 1, secao: 2 }, "São Paulo", aux, sp.bu);
    const casos = montarCasos([sp, zz], semAux, OPC.recebidoEm);
    expect(casos.map((c) => [c.id, c.tipo, c.esperado])).toEqual([
      [1, "igual", "igual"], [2, "voto_movido", "divergente"], [3, "comparecimento_mais_1", "divergente"],
      [4, "igual", "igual"], [5, "voto_movido", "divergente"], [6, "comparecimento_mais_1", "divergente"],
      [7, "aux_nao_publicado", "tse_ainda_nao_publicou"],
    ]);
    const r = await conferirPelaPonte(casos, {
      db: join(dir, "demo.sqlite"), agora: "2026-10-05T00:00:00.000Z",
      municipios: [
        { cd: "71072", uf: "sp", ibge: "3550308", nome: "SÃO PAULO", capital: 1, eleitores: null, origem: "cm" },
        { cd: "29173", uf: "zz", ibge: null, nome: "KATMANDU", capital: 0, eleitores: null, origem: "cm" },
      ],
    });
    expect(r.antes.every((x) => x.situacao === "tse_ainda_nao_publicou")).toBe(true);
    expect(r.depois.map((x) => [x.bu_id, x.situacao, x.diferencas.length])).toEqual([
      [1, "igual", 0], [2, "divergente", 2], [3, "divergente", 1], [4, "igual", 0], [5, "divergente", 2], [6, "divergente", 1], [7, "tse_ainda_nao_publicou", 0],
    ]);
    expect(r.depois.find((x) => x.bu_id === 1)?.tse_sha256).toBe(sp.buSha256);
    expect(r.requisicoes_tse.map((x) => `${x.status} ${x.url.split("/").at(-1) ?? ""}`).sort()).toEqual([
      "200 o03220sp7107200010001-bu.dat", `200 ${zzFix.arquivo}`, "200 p003220-sp-m71072-z0001-s0001-aux.json", "200 p003220-zz-m29173-z0001-s0494-aux.json",
      "404 p003220-sp-m71072-z0001-s0002-aux.json",
    ]);
    expect(r.paralela.conferencia).toEqual({ iguais: 2, divergentes: 4, tse_ainda_nao_publicou: 1, erro: 0, fora_do_oficial: 0, pendentes: 0 });
    const div = r.anomalias.filter((x) => x.tipo === "divergencia_paralela").sort((x, y) => x.id - y.id);
    expect(div.map((x) => [x.severidade, x.categoria, x.texto])).toEqual([
      ["error", "divergencia", "BU da totalização paralela difere do oficial na seção 1 da zona 1 de São Paulo (SP)"],
      ["error", "divergencia", "BU da totalização paralela difere do oficial na seção 1 da zona 1 de São Paulo (SP)"],
      ["error", "divergencia", "BU da totalização paralela difere do oficial na seção 494 da zona 1 de Katmandu (ZZ)"],
      ["error", "divergencia", "BU da totalização paralela difere do oficial na seção 494 da zona 1 de Katmandu (ZZ)"],
    ]);
    expect(div[0]?.detalhe).toMatchObject({
      secao: 1, zona: 1, bu_id: 2, tse_sha256: sp.buSha256, n_diferencas: 2,
      campos: [{ campo: "presidente: votos no 13", paralela: 120, tse: 121 }, { campo: "presidente: votos no 22", paralela: 97, tse: 96 }],
    });
    expect(div[3]?.detalhe).toMatchObject({ bu_id: 6, campos: [{ campo: "presidente: comparecimento", paralela: 14, tse: 13 }] });
    expect(r.anomalias.find((x) => x.tipo === "paralela_conferida")?.texto).toBe("Totalização paralela: 6 BUs conferidos, 2 iguais e 4 com diferença");
  }, 30_000);
});
