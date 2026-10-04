import { afterAll, describe, expect, test } from "bun:test";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { EstadoArquivos } from "../src/collector/estado-arquivos.ts";
import type { FileState } from "../src/collector/estado-arquivos.ts";
import { processar } from "../src/collector/processar.ts";
import { abrirEscrita, fecharEscrita } from "../src/db/abrir.ts";
import { chave, keyAb, keyU } from "../src/tse/urls.ts";
import { arquivo, jobDe, montar, ok, resultado } from "./coletor-util.ts";
import { bytes } from "./helpers.ts";

const dir = mkdtempSync(join(tmpdir(), "apuracao-estado-"));
afterAll(() => rmSync(dir, { recursive: true, force: true }));

const persistente = (fs: FileState): Record<string, unknown> => {
  const { emVoo: _e, shaRegressivo: _s, ...resto } = fs;
  return { ...resto, candidatosAnteriores: fs.candidatosAnteriores === null ? null : [...fs.candidatosAnteriores].sort((a, b) => a[0] - b[0]) };
};

describe("estado dos arquivos", () => {
  test("grava N respostas, reabre e reconstrói o mesmo estado", () => {
    const path = join(dir, "a.sqlite");
    const m = montar(path);
    const chaves = [
      chave(keyU(6257, 1, "br")),
      chave(keyU(6257, 1, "uf", "sp")),
      chave(keyU(6257, 1, "mu", "sp", "71072")),
      chave(keyU(6257, 1, "zona", "sp", "71072", "0001")),
      chave(keyAb(6257, "sp")),
      chave(keyAb(6257, "br")),
      chave(keyU(6257, 1, "zona", "sp", "71072", "0002")),
      chave(keyU(6257, 1, "mu", "sp", "62910")),
    ];
    const respostas = [
      ok(bytes("br-c0001-e006257-u.json"), '"b1"'),
      ok(bytes("sp-c0001-e006257-u.json"), '"s1"'),
      ok(bytes("sp71072-c0001-e006257-u.json"), '"m1"'),
      ok(bytes("sp71072-z0001-c0001-e006257-u.json")),
      ok(bytes("sp-e006257-ab.json"), '"a1"'),
      ok(bytes("br-e006257-ab.json")),
      resultado("nao_existe"),
      resultado("erro_servidor"),
    ];
    chaves.forEach((ch, i) => {
      const fs = arquivo(m, ch);
      const r = respostas[i];
      if (!r) throw new Error("resposta");
      processar(m.ctx, jobDe(fs), fs, r, m.relogio.agora());
      m.relogio.avancar(250);
    });
    m.lote.gravar();
    const antes = chaves.map((ch) => persistente(arquivo(m, ch)));
    const fps = new Map(m.estado.abFingerprints);
    const te = new Map(m.estado.teMunicipio);
    fecharEscrita(m.ctx.db);

    const db = abrirEscrita(path);
    const est = EstadoArquivos.carregarDoBanco(db);
    const depois = chaves.map((ch) => {
      const fs = est.porChave.get(ch);
      if (!fs) throw new Error(ch);
      return persistente(fs);
    });
    expect(depois).toEqual(antes);
    expect(est.abFingerprints).toEqual(fps);
    expect(est.teMunicipio).toEqual(te);
    expect(est.porId.size).toBe(m.estado.porId.size);
    expect(est.doMunicipio(6257, "sp", "71072").length).toBe(1);
    expect(est.zonasDoMunicipio(6257, "sp", "71072").length).toBe(57);
    db.close();
  });
});
