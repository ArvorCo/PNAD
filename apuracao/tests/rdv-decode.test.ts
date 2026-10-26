import { describe, expect, test } from "bun:test";
import { join } from "node:path";
import { decodificarBu } from "../src/secoes2t/bu-decode.ts";
import { conferirComBu, decodificarRdv, paraBu } from "../src/secoes2t/rdv-decode.ts";
import { linhasVoto } from "../scripts/secoes/banco.ts";
import { escolherRdv } from "../scripts/secoes/rdv-banco.ts";
import { AuxSchema } from "../scripts/secoes/secao.ts";

const DIR = join(import.meta.dir, "fixtures", "rdv");
const ler = async (n: string): Promise<Uint8Array> => new Uint8Array(await Bun.file(join(DIR, n)).arrayBuffer());

describe("RDV do 2º turno (AC, município 01007, zona 9, seção 1)", () => {
  test("decodifica cabeçalho, seção e as duas listas", async () => {
    const r = decodificarRdv(await ler("o03221ac0100700090001-rdv.dat"));
    expect(r.pleito).toBe(3221);
    expect(r.fase).toBe(2);
    expect(r.origem).toBe("vota");
    expect(r.identificacao).toEqual({ municipioZona: { municipio: 1007, zona: 9 }, local: 1104, secao: 1 });
    expect(r.cargos.map((c) => [c.idEleicao, c.cargo, c.nVotos, c.ordenado])).toEqual([
      [6258, 1, 232, true],
      [6260, 3, 232, true],
    ]);
    // gabarito: asn1tools sobre spec/rdv.asn1 do pacote oficial
    expect(r.cargos[0]?.contagem).toEqual([
      { tipo: 2, digitacao: "13", votos: 68 },
      { tipo: 2, digitacao: "22", votos: 149 },
      { tipo: 3, digitacao: "", votos: 2 },
      { tipo: 4, digitacao: "00", votos: 2 },
      { tipo: 4, digitacao: "10", votos: 3 },
      { tipo: 4, digitacao: "11", votos: 6 },
      { tipo: 4, digitacao: "26", votos: 1 },
      { tipo: 4, digitacao: "31", votos: 1 },
    ]);
    expect(r.cargos[1]?.contagem.find((c) => c.tipo === 4 && c.digitacao === "22")?.votos).toBe(16);
  });

  test("confere com o BU da mesma seção", async () => {
    const r = decodificarRdv(await ler("o03221ac0100700090001-rdv.dat"));
    const { bu } = decodificarBu(await ler("o03221ac0100700090001-bu.dat"));
    const linhas = linhasVoto(bu);
    expect(conferirComBu(r.cargos, linhas)).toEqual({ confere: true, divergencias: [] });
    const alterado = linhas.map((l) => (l.cargo === 3 && l.tipo === 1 && l.numero === 10 ? { ...l, votos: l.votos + 1 } : l));
    const c = conferirComBu(r.cargos, alterado);
    expect(c.confere).toBe(false);
    expect(c.divergencias).toEqual(["3:1:10 rdv=49 bu=50"]);
  });

  test("cargo sem votos nos dois lados confere (busa do SA no exterior)", () => {
    const vazio = [{ idEleicao: 6258, cargo: 1, quantidadeEscolhas: 1, nVotos: 0, ordenado: true, contagem: [] }];
    expect(conferirComBu(vazio, [])).toEqual({ confere: true, divergencias: [] });
    const comVoto = [{ ...vazio[0]!, nVotos: 1, contagem: [{ tipo: 2, digitacao: "13", votos: 1 }] }];
    expect(conferirComBu(comVoto, []).divergencias[0]).toBe("cargo 1 ausente do BU");
  });

  test("mapeia tipos do RDV para o BU", () => {
    expect(paraBu({ tipo: 2, digitacao: "22", votos: 1 })).toEqual({ tipo: 1, numero: 22 });
    expect(paraBu({ tipo: 1, digitacao: "13", votos: 1 })).toEqual({ tipo: 4, numero: 13 });
    expect(paraBu({ tipo: 5, digitacao: "", votos: 1 })).toEqual({ tipo: 2, numero: 0 });
    expect(paraBu({ tipo: 7, digitacao: "13", votos: 1 })).toEqual({ tipo: 3, numero: 0 });
  });

  test("lista fora de ordem é marcada", async () => {
    const b = await ler("o03221ac0100700090001-rdv.dat");
    // troca o primeiro voto nominal '13' por '99': a lista deixa de estar ordenada
    const i = Buffer.from(b).indexOf(Buffer.from([0x30, 0x07, 0x0a, 0x01, 0x02, 0x12, 0x02, 0x31, 0x33]));
    const c = new Uint8Array(b);
    c[i + 7] = 0x39;
    c[i + 8] = 0x39;
    expect(decodificarRdv(c).cargos[0]?.ordenado).toBe(false);
  });

  test("escolhe o hash com RDV", () => {
    const aux = AuxSchema.parse({
      hashes: [
        { hash: "a", dr: "25/10/2026", hr: "19:00:00", arq: [{ nm: "x-bu.dat", tp: "bu" }] },
        { hash: "b", dr: "25/10/2026", hr: "19:57:33", arq: [{ nm: "x-rdv.dat", tp: "rdv" }, { nm: "x-bu.dat", tp: "bu" }] },
      ],
    });
    expect(escolherRdv(aux)).toEqual({ hash: "b", nome: "x-rdv.dat", temBu: true });
    expect(escolherRdv(AuxSchema.parse({ hashes: [] }))).toBeNull();
  });
});
