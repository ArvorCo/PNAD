// Contexto do servidor: conexão de leitura tolerante a banco ausente e campos.json com recarga por mtime.
import type { Database } from "bun:sqlite";
import { existsSync, readFileSync, statSync } from "node:fs";
import { abrirLeitura } from "../db/abrir.ts";

/** Abre o banco só quando ele existir com o esquema; reabre se ainda não estiver pronto. */
export class FonteBanco {
  private db: Database | null = null;
  private tentativaEm = 0;

  constructor(
    readonly path: string,
    private readonly intervaloMs = 1000,
  ) {}

  obter(): Database | null {
    if (this.db) return this.db;
    const agora = Date.now();
    if (agora - this.tentativaEm < this.intervaloMs) return null;
    this.tentativaEm = agora;
    if (!existsSync(this.path)) return null;
    let db: Database | null = null;
    try {
      db = abrirLeitura(this.path);
      const ok = db.query<{ n: number }, []>("SELECT COUNT(*) AS n FROM sqlite_master WHERE type = 'table' AND name IN ('snapshot', 'arquivo', 'evento')").get();
      if ((ok?.n ?? 0) < 3) {
        db.close();
        return null;
      }
      this.db = db;
      return db;
    } catch {
      db?.close();
      return null;
    }
  }

  /** Tamanho do banco mais o WAL, em MB. */
  tamanhoMb(): number {
    let bytes = 0;
    for (const p of [this.path, `${this.path}-wal`]) {
      try {
        bytes += statSync(p).size;
      } catch {
        // arquivo ausente conta zero
      }
    }
    return Math.round((bytes / 1048576) * 10) / 10;
  }

  fechar(): void {
    this.db?.close();
    this.db = null;
  }
}

export type Campo = "esquerda" | "centro-esquerda" | "centro" | "centro-direita" | "direita" | "indefinido";

const CAMPOS_VALIDOS: ReadonlySet<string> = new Set(["esquerda", "centro-esquerda", "centro", "centro-direita", "direita", "indefinido"]);

/** Partido → campo a partir de public/campos.json; relê quando o mtime muda (checagem a cada 2 s). */
export class Campos {
  private mapa = new Map<string, Campo>();
  private excecoes = new Map<string, Campo>();
  private mtime = -1;
  private checadoEm = 0;

  constructor(private readonly path: string) {
    this.recarregar();
  }

  private recarregar(): void {
    this.checadoEm = Date.now();
    let mt: number;
    try {
      mt = statSync(this.path).mtimeMs;
    } catch {
      return;
    }
    if (mt === this.mtime) return;
    try {
      const bruto = JSON.parse(readFileSync(this.path, "utf8")) as { partidos?: Record<string, unknown>; excecoes?: Record<string, unknown> };
      const novo = new Map<string, Campo>();
      for (const [sg, c] of Object.entries(bruto.partidos ?? {})) {
        if (typeof c === "string" && CAMPOS_VALIDOS.has(c)) novo.set(sg.toUpperCase(), c as Campo);
      }
      // Exceções por candidatura (sqcand), declaradas em scripts/gerar-campos.py.
      const exc = new Map<string, Campo>();
      for (const [sq, c] of Object.entries(bruto.excecoes ?? {})) {
        if (typeof c === "string" && CAMPOS_VALIDOS.has(c)) exc.set(sq, c as Campo);
      }
      this.mapa = novo;
      this.excecoes = exc;
      this.mtime = mt;
    } catch {
      // arquivo sendo regravado: mantém o mapa anterior e tenta de novo
    }
  }

  /** Campo de uma candidatura: exceção declarada por sqcand ou, na falta, o campo do partido/federação. */
  campoCandidato(sqcand: string | number | null | undefined, ...siglas: (string | null | undefined)[]): Campo {
    if (Date.now() - this.checadoEm > 2000) this.recarregar();
    const e = sqcand !== null && sqcand !== undefined ? this.excecoes.get(String(sqcand)) : undefined;
    return e ?? this.campo(...siglas);
  }

  campo(...siglas: (string | null | undefined)[]): Campo {
    if (Date.now() - this.checadoEm > 2000) this.recarregar();
    for (const sg of siglas) {
      if (!sg) continue;
      const c = this.mapa.get(sg.toUpperCase());
      if (c) return c;
    }
    return "indefinido";
  }
}

export interface Contexto {
  banco: FonteBanco;
  campos: Campos;
  publicDir: string;
  agora(): string;
}
