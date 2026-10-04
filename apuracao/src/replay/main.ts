// Replay e ensaio a seco.
//   bun run replay tests/fixtures              → mapeia cada URL do registro para a fixture de mesmo nome
//                                                 (ausente = nao_existe) e grava data/replay.sqlite
//   bun run replay --db outro.sqlite [--speed 60] [--from ISO] [--out data/replay.sqlite]
//                                              → relê os blobs de outro banco em ordem de capturado_em,
//                                                 com relógio acelerado, num banco novo
// Usa o Sequenciador próprio (primitivas do B1); ver sequenciador.ts.
import { existsSync, readdirSync, readFileSync, rmSync, statSync } from "node:fs";
import { basename, join } from "node:path";
import { abrirEscrita, abrirLeitura, fecharEscrita } from "../db/abrir.ts";
import { parseCorpo } from "../parse/schemas.ts";
import type { MunCm } from "../parse/schemas.ts";
import { registroDeArquivos } from "../tse/urls.ts";
import type { Contagem } from "./sequenciador.ts";
import { Sequenciador } from "./sequenciador.ts";

const ORDEM_TIPO: Readonly<Record<string, number>> = { "ele-c": 0, cm: 1, ab: 2, u: 3, e: 4 };
const ORDEM_NIVEL: Readonly<Record<string, number>> = { br: 0, uf: 1, mu: 2, zona: 3 };

export function bancoNovo(path: string): void {
  for (const p of [path, `${path}-wal`, `${path}-shm`]) rmSync(p, { force: true });
}

export interface ResultadoReplay extends Contagem {
  arquivos: number;
  db: string;
}

/** Ensaio a seco: o registro inteiro "lido" contra um diretório de fixtures. */
export function replayFixtures(dir: string, out: string, inicio: Date = new Date()): ResultadoReplay {
  const fixtures = new Map<string, string>();
  for (const nome of readdirSync(dir)) {
    const p = join(dir, nome);
    if (nome.endsWith(".json") && statSync(p).isFile()) fixtures.set(nome, p);
  }
  const cms = new Map<number, MunCm>();
  for (const [nome, p] of fixtures) {
    const m = /^mun-e(\d{6})-cm\.json$/.exec(nome);
    if (!m) continue;
    const r = parseCorpo("cm", readFileSync(p));
    if (r.ok && r.parsed.tipo === "cm") cms.set(Number(m[1]), r.parsed.data);
  }
  bancoNovo(out);
  const db = abrirEscrita(out);
  try {
    const seq = new Sequenciador(db);
    const regs = [...registroDeArquivos(cms)];
    seq.registrar(regs);
    const ordenados = regs.sort(
      (a, b) => (ORDEM_TIPO[a.tipo] ?? 9) - (ORDEM_TIPO[b.tipo] ?? 9) || (ORDEM_NIVEL[a.nivel ?? "br"] ?? 9) - (ORDEM_NIVEL[b.nivel ?? "br"] ?? 9) || (a.chave < b.chave ? -1 : 1),
    );
    let t = inicio.getTime();
    for (const a of ordenados) {
      const p = fixtures.get(basename(a.url));
      seq.processar(a.chave, p ? new Uint8Array(readFileSync(p)) : null, new Date(t).toISOString());
      t += 1;
    }
    return { ...seq.contagem, arquivos: regs.length, db: out };
  } finally {
    fecharEscrita(db);
  }
}

export interface OpcoesReplayDb {
  speed: number;
  from?: string;
  dormir?: (ms: number) => Promise<void>;
  aoAvancar?: (capturadoEm: string, n: number) => void;
}

/** Relê os snapshots de `src` em ordem de captura, no ritmo `speed` (0 = sem pausa), num banco novo. */
export async function replayDb(src: string, out: string, o: OpcoesReplayDb): Promise<ResultadoReplay> {
  if (!existsSync(src)) throw new Error(`banco de origem não existe: ${src}`);
  bancoNovo(out);
  const db = abrirEscrita(out);
  const origem = abrirLeitura(src);
  const dormir = o.dormir ?? ((ms: number) => Bun.sleep(ms));
  try {
    db.run("ATTACH DATABASE ? AS fonte", [src]);
    db.transaction(() => {
      for (const t of ["uf", "municipio", "zona", "eleicao", "cargo", "partido", "federacao"]) db.run(`INSERT OR IGNORE INTO main.${t} SELECT * FROM fonte.${t}`);
      db.run(
        `INSERT OR IGNORE INTO main.arquivo (chave, url, tipo, eleicao_cd, cargo_cd, nivel, uf, municipio_cd, zona_cd, tier, sonda)
         SELECT chave, url, tipo, eleicao_cd, cargo_cd, nivel, uf, municipio_cd, zona_cd, tier, sonda FROM fonte.arquivo`,
      );
    })();
    db.run("DETACH DATABASE fonte");
    const seq = new Sequenciador(db);
    const from = o.from ?? "";
    const q = origem.query<{ id: number; chave: string; capturado_em: string; gz: Uint8Array }, [string, string, number, string]>(
      `SELECT s.id, a.chave, s.capturado_em, b.gz FROM snapshot s JOIN arquivo a ON a.id = s.arquivo_id JOIN blob b ON b.sha256 = s.sha256
       WHERE (s.capturado_em > ? OR (s.capturado_em = ? AND s.id > ?)) AND s.capturado_em >= ?
       ORDER BY s.capturado_em, s.id LIMIT 500`,
    );
    let ultimoEm = "";
    let ultimoId = 0;
    let t0: number | null = null;
    let w0 = 0;
    let n = 0;
    for (;;) {
      const pagina = q.all(ultimoEm, ultimoEm, ultimoId, from);
      if (pagina.length === 0) break;
      for (const r of pagina) {
        ultimoEm = r.capturado_em;
        ultimoId = r.id;
        const t = Date.parse(r.capturado_em);
        if (t0 === null) {
          t0 = t;
          w0 = Date.now();
        } else if (o.speed > 0) {
          const espera = w0 + (t - t0) / o.speed - Date.now();
          if (espera > 0) await dormir(espera);
        }
        seq.processar(r.chave, new Uint8Array(Bun.gunzipSync(new Uint8Array(r.gz))), r.capturado_em);
        n += 1;
        o.aoAvancar?.(r.capturado_em, n);
      }
    }
    const arquivos = db.query<{ n: number }, []>("SELECT COUNT(*) AS n FROM arquivo").get()?.n ?? 0;
    return { ...seq.contagem, arquivos, db: out };
  } finally {
    origem.close();
    fecharEscrita(db);
  }
}

function argumentos(argv: readonly string[]): { dir?: string; db?: string; out: string; speed: number; from?: string } {
  const r: { dir?: string; db?: string; out: string; speed: number; from?: string } = { out: "data/replay.sqlite", speed: 60 };
  for (let i = 0; i < argv.length; i += 1) {
    const a = argv[i] ?? "";
    const v = argv[i + 1];
    if (a === "--db" && v) { r.db = v; i += 1; }
    else if (a === "--out" && v) { r.out = v; i += 1; }
    else if (a === "--speed" && v) { r.speed = Number(v); i += 1; }
    else if (a === "--from" && v) { const t = Date.parse(v); if (Number.isFinite(t)) r.from = new Date(t).toISOString(); i += 1; }
    else if (!a.startsWith("--")) r.dir = a;
  }
  return r;
}

if (import.meta.main) {
  const a = argumentos(process.argv.slice(2));
  const inicio = performance.now();
  if (a.db) {
    const r = await replayDb(a.db, a.out, {
      speed: a.speed, ...(a.from ? { from: a.from } : {}),
      aoAvancar: (em, n) => { if (n % 500 === 0) console.log(JSON.stringify({ evento: "replay_progresso", capturado_em: em, n })); },
    });
    console.log(JSON.stringify({ evento: "replay_fim", modo: "db", ...r, ms: Math.round(performance.now() - inicio) }));
  } else {
    const dir = a.dir ?? "tests/fixtures";
    const r = replayFixtures(dir, a.out);
    console.log(JSON.stringify({ evento: "replay_fim", modo: "fixtures", dir, ...r, ms: Math.round(performance.now() - inicio) }));
    if (r.parse_error > 0) process.exitCode = 1;
  }
}

