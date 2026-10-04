// Abertura do SQLite: escritor único (WAL + esquema) e leitores somente leitura.
import { Database } from "bun:sqlite";
import { existsSync, mkdirSync } from "node:fs";
import { dirname } from "node:path";
import schemaSql from "./schema.sql" with { type: "text" };

export const SCHEMA_VERSION = 1;

const PRAGMAS_ESCRITA = [
  "PRAGMA journal_mode = WAL",
  "PRAGMA synchronous = NORMAL",
  "PRAGMA foreign_keys = ON",
  "PRAGMA busy_timeout = 5000",
  "PRAGMA cache_size = -262144",
  "PRAGMA temp_store = MEMORY",
  "PRAGMA mmap_size = 1073741824",
  "PRAGMA wal_autocheckpoint = 2000",
  "PRAGMA journal_size_limit = 268435456",
];

export function aplicarEsquema(db: Database): void {
  db.transaction(() => {
    db.run(schemaSql);
    db.query("INSERT INTO meta (chave, valor) VALUES ('schema_version', $v) ON CONFLICT (chave) DO UPDATE SET valor = excluded.valor").run({
      v: String(SCHEMA_VERSION),
    });
  })();
}

/** Abre (criando) o banco do coletor. `:memory:` funciona para testes. */
export function abrirEscrita(path: string): Database {
  if (path !== ":memory:") mkdirSync(dirname(path), { recursive: true });
  const db = new Database(path, { create: true, strict: true });
  for (const p of PRAGMAS_ESCRITA) db.run(p);
  aplicarEsquema(db);
  return db;
}

/** Abre o banco para leitura (servidor, replay). Nunca escreve. */
export function abrirLeitura(path: string): Database {
  let db: Database | null = null;
  try {
    db = new Database(path, { readonly: true, strict: true });
    db.query("SELECT 1 FROM sqlite_master LIMIT 1").get();
  } catch (e) {
    db?.close();
    // Banco em WAL sem o -shm (coletor parado depois do checkpoint final): a conexão
    // readonly não consegue criar o -shm e o SQLite recusa a abertura. Abre sem criar
    // o banco e trava a escrita por query_only; só o -shm e o -wal vazios aparecem.
    if (existsSync(`${path}-shm`) || !existsSync(path)) throw e;
    db = new Database(path, { readwrite: true, create: false, strict: true });
  }
  db.run("PRAGMA busy_timeout = 5000");
  db.run("PRAGMA query_only = 1");
  db.run("PRAGMA mmap_size = 1073741824");
  db.run("PRAGMA cache_size = -131072");
  return db;
}

/** checkpoint final no desligamento do coletor. */
export function fecharEscrita(db: Database): void {
  db.run("PRAGMA wal_checkpoint(TRUNCATE)");
  db.close();
}
