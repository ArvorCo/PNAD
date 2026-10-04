// Views de auditoria contra valores calculados à mão a partir do semeio.
import { afterAll, beforeAll, describe, expect, test } from "bun:test";
import { arquivoPorChave } from "../src/db/leitura.ts";
import type { Semeado } from "./server-helpers.ts";
import { CHAVES, iso, seg, semear } from "./server-helpers.ts";

let s: Semeado;

beforeAll(() => {
  s = semear();
});

afterAll(() => {
  s.fechar();
  s.limpar();
});

interface Delta {
  snapshot_id: number;
  regressivo: number;
  latencia_captura_s: number | null;
  latencia_geracao_s: number | null;
  intervalo_geracao_s: number | null;
  d_st: number | null;
  d_vvc: number | null;
}

describe("views", () => {
  test("v_snapshot_delta: latências, intervalos e deltas por arquivo", () => {
    const arq = arquivoPorChave(s.db, CHAVES.presBr);
    if (!arq) throw new Error("arquivo");
    const rows = s.db
      .query<Delta, [number]>(
        "SELECT snapshot_id, regressivo, latencia_captura_s, latencia_geracao_s, intervalo_geracao_s, d_st, d_vvc FROM v_snapshot_delta WHERE arquivo_id = ? ORDER BY snapshot_id",
      )
      .all(arq.id);
    expect(rows.map((r) => r.snapshot_id)).toEqual([s.id("presBr0"), s.id("presBr1"), s.id("presBr2"), s.id("presBr3"), s.id("presBr4"), s.id("presBrRegressivo")]);
    const [v0, v1, v2, v3, v4, reg] = rows;
    // versões semeadas: captura = geração + 10 s, geração = totalização + 20 s, uma geração a cada 120 s
    for (const v of [v1, v2, v3, v4]) {
      expect(v?.latencia_captura_s ?? 0).toBeCloseTo(10, 1);
      expect(v?.latencia_geracao_s ?? 0).toBeCloseTo(20, 1);
    }
    for (const v of [v2, v3, v4]) {
      expect(v?.intervalo_geracao_s ?? 0).toBeCloseTo(120, 1);
      expect(v?.d_st).toBe(50_000);
    }
    expect(v0?.intervalo_geracao_s).toBeNull();
    expect(v0?.latencia_geracao_s).toBeNull();
    // fixture gerada em 03/10 14:47:37 BRT, lida em 04/10 16:55 BRT
    expect(v0?.latencia_captura_s ?? 0).toBeCloseTo((Date.parse(iso(seg(-300))) - Date.parse("2026-10-03T17:47:37.000Z")) / 1000, 1);
    expect(v1?.d_st).toBe(50_000);
    expect(v2?.d_vvc).toBe(17_900_000 + 700_000 - 11_500_000);
    expect(reg?.regressivo).toBe(1);
    expect(reg?.d_st).toBeNull();
  });

  test("v_municipio_fim: primeiro snapshot completo do município", () => {
    const rows = s.db
      .query<{ municipio_cd: string; cargo_cd: number; snapshot_id: number; capturado_em: string; totalizado_em: string }, []>(
        "SELECT municipio_cd, cargo_cd, snapshot_id, capturado_em, totalizado_em FROM v_municipio_fim",
      )
      .all();
    expect(rows).toEqual([{ municipio_cd: "71072", cargo_cd: 1, snapshot_id: s.id("presMun2"), capturado_em: iso(seg(260)), totalizado_em: iso(seg(240)) }]);
  });

  test("v_ab_atual: última entrada por cdabr, só mudanças gravadas", () => {
    const br = s.db
      .query<{ cdabr: string; st: number; ts: number; snapshot_id: number; totalizado_em: string | null }, []>(
        "SELECT cdabr, st, ts, snapshot_id, totalizado_em FROM v_ab_atual WHERE eleicao_cd = 6257 AND nivel = 'br' ORDER BY cdabr",
      )
      .all();
    expect(br.length).toBe(29);
    const por = new Map(br.map((r) => [r.cdabr, r]));
    expect(por.get("se")).toMatchObject({ st: 5923, ts: 5923, snapshot_id: s.id("abBr1"), totalizado_em: iso(seg(100)) });
    expect(por.get("sp")).toMatchObject({ st: 50_000, snapshot_id: s.id("abBr2") });
    expect(por.get("pr")).toMatchObject({ st: 900, snapshot_id: s.id("abBr2") });
    expect(por.get("ac")).toMatchObject({ st: 0, snapshot_id: s.id("abBr0") });
    const gravadas = s.db.query<{ n: number }, [number]>("SELECT COUNT(*) AS n FROM ab_estado WHERE snapshot_id = ?").get(s.id("abBr2"));
    expect(gravadas?.n).toBe(2);
    const sp = s.db.query<{ st: number }, []>("SELECT st FROM v_ab_atual WHERE uf_arquivo = 'sp' AND cdabr = '71072'").get();
    expect(sp?.st).toBe(10_000);
  });
});
