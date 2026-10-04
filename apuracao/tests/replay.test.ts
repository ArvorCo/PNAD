// Replay: ensaio a seco contra as fixtures e releitura de outro banco com relógio acelerado.
import { afterAll, describe, expect, test } from "bun:test";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { abrirLeitura } from "../src/db/abrir.ts";
import { ultimoSnapshotPorChave } from "../src/db/leitura.ts";
import { replayDb, replayFixtures } from "../src/replay/main.ts";
import { FIXTURES } from "./helpers.ts";
import { CHAVES, iso, seg, semear } from "./server-helpers.ts";

const dir = mkdtempSync(join(tmpdir(), "apuracao-replay-"));

afterAll(() => {
  rmSync(dir, { recursive: true, force: true });
});

describe("replay", () => {
  test("fixtures: registro inteiro, zero parse_error, ausentes como nao_existe", () => {
    const out = join(dir, "fixtures.sqlite");
    const r = replayFixtures(FIXTURES, out, new Date(seg(0)));
    expect(r.parse_error).toBe(0);
    expect(r.arquivos).toBeGreaterThan(59_000);
    expect(r.fetches).toBe(r.arquivos);
    expect(r.snapshots).toBe(15);
    expect(r.nao_existe).toBe(r.arquivos - r.snapshots);
    const db = abrirLeitura(out);
    try {
      expect(db.query<{ n: number }, []>("SELECT COUNT(*) AS n FROM municipio").get()?.n).toBe(5757);
      expect(db.query<{ n: number }, []>("SELECT COUNT(*) AS n FROM evento WHERE tipo = 'parse_error'").get()?.n).toBe(0);
      expect(ultimoSnapshotPorChave(db, CHAVES.presBr)?.ts).toBe(499_248);
      expect(db.query<{ n: number }, []>("SELECT COUNT(*) AS n FROM voto_candidato").get()?.n).toBeGreaterThan(1000);
    } finally {
      db.close();
    }
  });

  test("outro banco: mesma sequência de versões, ritmo pelo speed, filtro from", async () => {
    const s = semear();
    s.fechar();
    try {
      const esperas: number[] = [];
      const out = join(dir, "db.sqlite");
      const r = await replayDb(s.path, out, { speed: 60, dormir: async (ms) => { esperas.push(ms); } });
      expect(r.parse_error).toBe(0);
      expect(r.snapshots).toBe(Object.keys(s.ids).length - 1);
      expect(r.regressivos).toBe(1);
      // de -600 s a +600 s de captura = 1.200 s, a 60x = 20 s de relógio
      expect(Math.max(...esperas)).toBeGreaterThan(19_000);
      expect(Math.max(...esperas)).toBeLessThanOrEqual(20_000);
      const db = abrirLeitura(out);
      try {
        const ult = ultimoSnapshotPorChave(db, CHAVES.presBr);
        expect(ult?.st).toBe(200_000);
        expect(ult?.capturado_em).toBe(iso(seg(480)));
      } finally {
        db.close();
      }
      const parcial = await replayDb(s.path, join(dir, "parcial.sqlite"), { speed: 0, from: iso(seg(200)) });
      // capturados a partir de +200 s: presBr2, presBr3, presBr4, regressivo, abBr2, presSp2, presMun2
      expect(parcial.snapshots + parcial.regressivos).toBe(7);
    } finally {
      s.limpar();
    }
  });
});
