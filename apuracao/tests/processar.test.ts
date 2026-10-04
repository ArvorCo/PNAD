import { describe, expect, test } from "bun:test";
import { processar } from "../src/collector/processar.ts";
import { arquivoPorChave, ultimoSnapshotPorChave } from "../src/db/leitura.ts";
import { chave, keyAb, keyU } from "../src/tse/urls.ts";
import { arquivo, contar, jobDe, montar, ok, resultado } from "./coletor-util.ts";
import type { Montagem } from "./coletor-util.ts";
import { json } from "./helpers.ts";

const BR = chave(keyU(6257, 1, "br"));
const SP = chave(keyU(6257, 1, "uf", "sp"));

/** fixture de presidente BR com idg e votos alterados */
function corpoBr(idg: number, vapExtra = 0): string {
  const j = json("br-c0001-e006257-u.json") as { idg: string; carg: { agr: { par: { cand: { vap: string }[] }[] }[] }[] };
  j.idg = String(idg);
  const c = j.carg[0]?.agr[0]?.par[0]?.cand[0];
  if (c) c.vap = String(vapExtra);
  return JSON.stringify(j);
}

function rodar(m: Montagem, ch: string, r: ReturnType<typeof ok>): ReturnType<typeof processar> {
  const fs = arquivo(m, ch);
  const s = processar(m.ctx, jobDe(fs), fs, r, m.relogio.agora());
  m.lote.gravar();
  m.relogio.avancar(1000);
  return s;
}

describe("processar", () => {
  test("corpo repetido vira igual sem snapshot; fetch sempre gravado", () => {
    const m = montar();
    const corpo = corpoBr(2_000_000);
    expect(rodar(m, BR, ok(corpo, '"e1"')).classe).toBe("ok");
    const s = rodar(m, BR, ok(corpo, '"e1"'));
    expect(s.classe).toBe("igual");
    expect(s.mudou).toBe(false);
    expect(contar(m, "SELECT COUNT(*) AS n FROM snapshot")).toBe(1);
    expect(contar(m, "SELECT COUNT(*) AS n FROM fetch")).toBe(2);
    expect(contar(m, "SELECT COUNT(*) AS n FROM fetch WHERE classe = 'igual' AND mudou = 0")).toBe(1);
    const a = arquivoPorChave(m.ctx.db, BR);
    expect(a?.n_fetch).toBe(2);
    expect(a?.n_mudancas).toBe(1);
    expect(a?.etag).toBe('"e1"');
  });

  test("blob deduplicado entre arquivos com corpo igual", () => {
    const m = montar();
    const corpo = corpoBr(2_000_000);
    rodar(m, BR, ok(corpo));
    rodar(m, SP, ok(corpo));
    expect(contar(m, "SELECT COUNT(*) AS n FROM snapshot")).toBe(2);
    expect(contar(m, "SELECT COUNT(*) AS n FROM blob")).toBe(1);
  });

  test("cadeia anterior_id e primeiro_snapshot_id gravado uma vez", () => {
    const m = montar();
    rodar(m, BR, ok(corpoBr(2_000_000, 0)));
    rodar(m, BR, ok(corpoBr(2_000_010, 7)));
    const snaps = m.ctx.db
      .query<{ id: number; anterior_id: number | null; regressivo: number }, []>("SELECT id, anterior_id, regressivo FROM snapshot ORDER BY id")
      .all();
    expect(snaps.length).toBe(2);
    expect(snaps[0]?.anterior_id).toBeNull();
    expect(snaps[1]?.anterior_id).toBe(snaps[0]?.id ?? -1);
    expect(contar(m, `SELECT COUNT(*) AS n FROM candidato WHERE primeiro_snapshot_id = ${snaps[0]?.id ?? -1}`)).toBeGreaterThan(0);
    expect(contar(m, `SELECT COUNT(*) AS n FROM candidato WHERE primeiro_snapshot_id <> ${snaps[0]?.id ?? -1}`)).toBe(0);
    expect(arquivoPorChave(m.ctx.db, BR)?.ultimo_snapshot_id).toBe(snaps[1]?.id ?? -1);
  });

  test("idg menor: snapshot regressivo, atual não muda, evento idg_regressivo", () => {
    const m = montar();
    rodar(m, BR, ok(corpoBr(2_000_010, 5)));
    const atual = ultimoSnapshotPorChave(m.ctx.db, BR)?.snapshot_id;
    rodar(m, BR, ok(corpoBr(2_000_000, 9)));
    expect(contar(m, "SELECT COUNT(*) AS n FROM snapshot WHERE regressivo = 1")).toBe(1);
    expect(ultimoSnapshotPorChave(m.ctx.db, BR)?.snapshot_id).toBe(atual ?? -1);
    expect(arquivoPorChave(m.ctx.db, BR)?.idg).toBe(2_000_010);
    expect(contar(m, "SELECT COUNT(*) AS n FROM evento WHERE tipo = 'idg_regressivo'")).toBe(1);
    // a mesma cópia velha de novo não gera outro snapshot
    expect(rodar(m, BR, ok(corpoBr(2_000_000, 9))).classe).toBe("igual");
    expect(contar(m, "SELECT COUNT(*) AS n FROM snapshot")).toBe(2);
  });

  test("regressão de votos dispara anomalia", () => {
    const m = montar();
    rodar(m, BR, ok(corpoBr(2_000_000, 50)));
    rodar(m, BR, ok(corpoBr(2_000_001, 10)));
    expect(contar(m, "SELECT COUNT(*) AS n FROM evento WHERE tipo = 'regressao_contagem'")).toBe(1);
  });

  test("parse inválido grava blob e evento, sem snapshot", () => {
    const m = montar();
    const s = rodar(m, BR, ok('{"carg": "não é lista"}'));
    expect(s.classe).toBe("ok");
    expect(contar(m, "SELECT COUNT(*) AS n FROM blob")).toBe(1);
    expect(contar(m, "SELECT COUNT(*) AS n FROM snapshot")).toBe(0);
    expect(contar(m, "SELECT COUNT(*) AS n FROM evento WHERE tipo = 'parse_error'")).toBe(1);
  });

  test("nao_existe desativa; erro faz backoff e evento no 3º", () => {
    const m = montar();
    const z = chave(keyU(6257, 1, "zona", "sp", "71072", "0001"));
    const s = rodar(m, z, resultado("nao_existe"));
    expect(arquivo(m, z).ativo).toBe(false);
    expect(s.jobs[0]).toMatchObject({ prioridade: "probe", motivo: "probe" });
    for (let i = 0; i < 3; i++) rodar(m, BR, resultado("erro_servidor"));
    const fs = arquivo(m, BR);
    expect(fs.errosSeguidos).toBe(3);
    expect(contar(m, "SELECT COUNT(*) AS n FROM evento WHERE tipo = 'erros_seguidos'")).toBe(1);
    expect(rodar(m, BR, resultado("negado")).pausar).toEqual({ retryAfterS: null });
  });

  test("primeiro -ab não espalha; mudança agenda o município", () => {
    const m = montar();
    const ab = chave(keyAb(6257, "sp"));
    const base = json("sp-e006257-ab.json") as { idg: string; abr: { cdabr: string; dt: string; s: { st: string } }[] };
    expect(rodar(m, ab, ok(JSON.stringify(base))).jobs).toEqual([]);
    const e = base.abr.find((x) => x.cdabr === "71072");
    if (!e) throw new Error("71072");
    e.dt = "04/10/2026";
    e.s.st = "10";
    base.idg = String(Number(base.idg) + 1);
    const s = rodar(m, ab, ok(JSON.stringify(base)));
    const ids = new Set(s.jobs.map((j) => j.arquivoId));
    expect(ids.has(arquivo(m, chave(keyU(6257, 1, "mu", "sp", "71072"))).id)).toBe(true);
    expect(ids.has(arquivo(m, chave(keyU(6257, 1, "zona", "sp", "71072", "0001"))).id)).toBe(true);
    expect(s.jobs.every((j) => j.motivo === "gatilho_ab")).toBe(true);
    expect(contar(m, "SELECT COUNT(*) AS n FROM ab_estado")).toBe(base.abr.length + 1);
  });
});
