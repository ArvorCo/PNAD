import { afterAll, describe, expect, test } from "bun:test";
import { Database } from "bun:sqlite";
import { existsSync, mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { SCHEMA_VERSION, abrirEscrita, abrirLeitura, aplicarEsquema, fecharEscrita } from "../src/db/abrir.ts";
import { lerMeta } from "../src/db/leitura.ts";

const dir = mkdtempSync(join(tmpdir(), "apuracao-schema-"));
afterAll(() => rmSync(dir, { recursive: true, force: true }));

const TABELAS = [
  "meta", "eleicao", "cargo", "uf", "municipio", "zona", "partido", "federacao", "candidato", "arquivo", "fetch", "blob",
  "snapshot", "totais", "voto_candidato", "voto_partido", "voto_agremiacao", "ab_estado", "e_entrada", "evento",
];
const VIEWS = ["v_atual", "v_snapshot_delta", "v_voto_candidato_delta", "v_municipio_fim", "v_ab_atual"];

function nomes(db: ReturnType<typeof abrirEscrita>, tipo: string): string[] {
  return db.query<{ name: string }, [string]>("SELECT name FROM sqlite_master WHERE type = ? ORDER BY name").all(tipo).map((r) => r.name);
}

describe("esquema", () => {
  test("aplica em memória e reaplica sem erro", () => {
    const db = abrirEscrita(":memory:");
    aplicarEsquema(db);
    aplicarEsquema(db);
    for (const t of TABELAS) expect(nomes(db, "table")).toContain(t);
    expect(nomes(db, "view").sort()).toEqual([...VIEWS].sort());
    expect(lerMeta(db, "schema_version")).toBe(String(SCHEMA_VERSION));
    for (const v of VIEWS) expect(db.query(`SELECT * FROM ${v} LIMIT 1`).all()).toEqual([]);
    db.close();
  });

  test("coluna and do TSE vira andamento; tf é inteiro", () => {
    const db = abrirEscrita(":memory:");
    const cols = db.query<{ name: string; type: string }, []>("PRAGMA table_info(snapshot)").all();
    expect(cols.map((c) => c.name)).toContain("andamento");
    expect(cols.map((c) => c.name)).not.toContain("and");
    expect(cols.find((c) => c.name === "tf")?.type).toBe("INTEGER");
    db.close();
  });

  test("pragmas do escritor em arquivo", () => {
    const path = join(dir, "sub", "a.sqlite");
    const db = abrirEscrita(path);
    const p = (nome: string): unknown => Object.values(db.query(`PRAGMA ${nome}`).get() as Record<string, unknown>)[0];
    expect(p("journal_mode")).toBe("wal");
    expect(p("synchronous")).toBe(1);
    expect(p("foreign_keys")).toBe(1);
    expect(p("busy_timeout")).toBe(5000);
    expect(p("cache_size")).toBe(-262144);
    expect(p("temp_store")).toBe(2);
    expect(p("wal_autocheckpoint")).toBe(2000);
    expect(p("journal_size_limit")).toBe(268435456);
    db.close();
    // reabrir é idempotente
    const db2 = abrirEscrita(path);
    expect(nomes(db2, "view").length).toBe(VIEWS.length);
    db2.close();
  });

  test("leitor é somente leitura", () => {
    const path = join(dir, "b.sqlite");
    const w = abrirEscrita(path);
    const r = abrirLeitura(path);
    expect(lerMeta(r, "schema_version")).toBe(String(SCHEMA_VERSION));
    expect(() => r.run("INSERT INTO meta (chave, valor) VALUES ('x', 'y')")).toThrow();
    r.close();
    w.close();
  });

  test("leitor abre banco WAL fechado pelo coletor (sem -shm) e continua somente leitura", () => {
    const path = join(dir, "c.sqlite");
    fecharEscrita(abrirEscrita(path));
    // o SQLite do macOS mantém o -shm; o sqlite3 do preflight (quick_check) o apaga ao sair
    for (const x of ["-wal", "-shm"]) rmSync(`${path}${x}`, { force: true });
    expect(() => new Database(path, { readonly: true }).query("SELECT 1 FROM sqlite_master").get()).toThrow();
    const r = abrirLeitura(path);
    expect(lerMeta(r, "schema_version")).toBe(String(SCHEMA_VERSION));
    expect(() => r.run("INSERT INTO meta (chave, valor) VALUES ('x', 'y')")).toThrow();
    const w = abrirEscrita(path);
    w.run("INSERT INTO meta (chave, valor) VALUES ('depois', '1')");
    expect(lerMeta(r, "depois")).toBe("1");
    w.close();
    r.close();
    expect(() => abrirLeitura(join(dir, "nao-existe.sqlite"))).toThrow();
    expect(existsSync(join(dir, "nao-existe.sqlite"))).toBe(false);
  });

  test("chave estrangeira ativa", () => {
    const db = abrirEscrita(":memory:");
    expect(() =>
      db.run("INSERT INTO fetch (arquivo_id, iniciado_em, motivo, classe) VALUES (999, '2026-10-04T20:00:00.000Z', 'periodico', 'ok')"),
    ).toThrow();
    db.close();
  });
});
