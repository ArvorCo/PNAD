// GET /events: Server-Sent Events por sondagem leve do banco (snapshot.id e evento.id).
// id: = snapshot.id; Last-Event-ID retoma do ponto. Padrão: resultados br/uf + todo -ab + config;
// tudo=1 inclui município e zona; nivel=br,uf,mun,zona escolhe os níveis.
import type { Database } from "bun:sqlite";
import { maxSnapshotId } from "../db/leitura.ts";
import { abrTexto } from "./abr.ts";
import type { MunicipioInfo } from "./consultas.ts";
import { municipiosIndex } from "./consultas.ts";
import type { Contexto } from "./contexto.ts";
import { textoEvento } from "./textos.ts";

export interface OpcoesSse {
  pollMs?: number;
  heartbeatMs?: number;
  lote?: number;
}

interface SnapRow {
  id: number;
  capturado_em: string;
  tf: number | null;
  regressivo: number;
  tipo: string;
  eleicao_cd: number | null;
  cargo_cd: number | null;
  nivel: string | null;
  uf: string | null;
  municipio_cd: string | null;
  zona_cd: string | null;
  pst: number | null;
}

interface EvRow {
  id: number;
  em: string;
  tipo: string;
  severidade: string;
  nivel: string | null;
  uf: string | null;
  municipio_cd: string | null;
  zona_cd: string | null;
  cargo_cd: number | null;
  eleicao_cd: number | null;
  snapshot_id: number | null;
  detalhe: string | null;
}

let abertas = 0;
export const conexoesSse = (): number => abertas;

const NIVEL_ALIAS: Readonly<Record<string, string>> = { br: "br", uf: "uf", mu: "mu", mun: "mu", zona: "zona" };

function niveisDe(url: URL): Set<string> {
  if (url.searchParams.get("tudo") === "1") return new Set(["br", "uf", "mu", "zona"]);
  const lista = (url.searchParams.get("nivel") ?? "br,uf").split(",").map((s) => NIVEL_ALIAS[s.trim()]).filter((s): s is string => s !== undefined);
  return new Set(lista.length > 0 ? lista : ["br", "uf"]);
}

function kindDe(tipo: string): "resultado" | "ab" | "config" | null {
  if (tipo === "u") return "resultado";
  if (tipo === "ab") return "ab";
  if (tipo === "ele-c" || tipo === "cm") return "config";
  return null;
}

function parseDetalhe(s: string | null): unknown {
  if (s === null) return null;
  try {
    return JSON.parse(s) as unknown;
  } catch {
    return s;
  }
}

export function responderSse(ctx: Contexto, req: Request, url: URL, o: OpcoesSse = {}): Response {
  const pollMs = o.pollMs ?? 500;
  const hbMs = o.heartbeatMs ?? 5000;
  const lote = o.lote ?? 2000;
  const niveis = niveisDe(url);
  const ultimoTxt = req.headers.get("last-event-id") ?? url.searchParams.get("ultimo");
  const ultimo = ultimoTxt !== null && /^\d+$/.test(ultimoTxt) ? Number(ultimoTxt) : null;
  const enc = new TextEncoder();
  let cursor: number | null = null;
  let cursorEv = 0;
  let muns: Map<string, MunicipioInfo> | null = null;
  let timers: ReturnType<typeof setInterval>[] = [];
  let ativo = true;

  const parar = (): void => {
    if (!ativo) return;
    ativo = false;
    abertas -= 1;
    for (const t of timers) clearInterval(t);
    timers = [];
  };

  const iniciarCursores = (db: Database): void => {
    if (cursor !== null) return;
    cursor = ultimo ?? maxSnapshotId(db);
    if (ultimo !== null) {
      const em = db.query<{ capturado_em: string }, [number]>("SELECT capturado_em FROM snapshot WHERE id = ?").get(ultimo)?.capturado_em;
      cursorEv = em
        ? (db.query<{ m: number | null }, [string]>("SELECT MAX(id) AS m FROM evento WHERE em <= ?").get(em)?.m ?? 0)
        : (db.query<{ m: number | null }, []>("SELECT MAX(id) AS m FROM evento").get()?.m ?? 0);
    } else {
      cursorEv = db.query<{ m: number | null }, []>("SELECT MAX(id) AS m FROM evento").get()?.m ?? 0;
    }
  };

  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      abertas += 1;
      const enviar = (s: string): void => {
        if (!ativo) return;
        try {
          controller.enqueue(enc.encode(s));
        } catch {
          parar();
        }
      };
      const estado = (): void => {
        const db = ctx.banco.obter();
        enviar(`event: estado\ndata: ${JSON.stringify({ kind: "estado", agora: ctx.agora(), pronto: db !== null, max_snapshot_id: db ? maxSnapshotId(db) : 0 })}\n\n`);
      };
      const tick = (): void => {
        if (!ativo) return;
        const db = ctx.banco.obter();
        if (!db) return;
        try {
          iniciarCursores(db);
          const snaps = db
            .query<SnapRow, [number, number]>(
              `SELECT s.id, s.capturado_em, s.tf, s.regressivo, a.tipo, a.eleicao_cd, a.cargo_cd, a.nivel, a.uf, a.municipio_cd, a.zona_cd, t.pst
               FROM snapshot s JOIN arquivo a ON a.id = s.arquivo_id LEFT JOIN totais t ON t.snapshot_id = s.id
               WHERE s.id > ? ORDER BY s.id LIMIT ?`,
            )
            .all(cursor ?? 0, lote);
          for (const s of snaps) {
            cursor = s.id;
            const kind = kindDe(s.tipo);
            if (s.regressivo === 1 || kind === null) continue;
            if (kind === "resultado" && !niveis.has(s.nivel ?? "")) continue;
            const nivel = s.nivel === "br" || s.nivel === "uf" || s.nivel === "mu" || s.nivel === "zona" ? s.nivel : null;
            const dado = {
              kind, ele: s.eleicao_cd, cargo: s.cargo_cd, abr: abrTexto({ nivel, uf: s.uf, municipio_cd: s.municipio_cd, zona_cd: s.zona_cd }),
              nivel: s.nivel, snapshot_id: s.id, at: s.capturado_em, pst: s.pst, tf: s.tf === 1,
            };
            enviar(`id: ${s.id}\nevent: snapshot\ndata: ${JSON.stringify(dado)}\n\n`);
          }
          const evs = db
            .query<EvRow, [number]>(
              `SELECT id, em, tipo, severidade, nivel, uf, municipio_cd, zona_cd, cargo_cd, eleicao_cd, snapshot_id, detalhe
               FROM evento WHERE id > ? ORDER BY id LIMIT 500`,
            )
            .all(cursorEv);
          for (const e of evs) {
            cursorEv = e.id;
            if (e.severidade !== "warn" && e.severidade !== "error") continue;
            muns ??= municipiosIndex(db);
            const nivel = e.nivel === "br" || e.nivel === "uf" || e.nivel === "mu" || e.nivel === "zona" ? e.nivel : null;
            const dado = {
              kind: "anomalia", id: e.id, at: e.em, tipo: e.tipo, severidade: e.severidade, ele: e.eleicao_cd, cargo: e.cargo_cd,
              abr: abrTexto({ nivel, uf: e.uf, municipio_cd: e.municipio_cd, zona_cd: e.zona_cd }), snapshot_id: e.snapshot_id,
              texto: textoEvento(e.tipo, e.em, e, parseDetalhe(e.detalhe), muns),
            };
            enviar(`event: evento\ndata: ${JSON.stringify(dado)}\n\n`);
          }
        } catch {
          // banco ocupado ou em migração: tenta no próximo ciclo
        }
      };
      enviar(`retry: 2000\n\n`);
      estado();
      tick();
      timers = [setInterval(tick, pollMs), setInterval(estado, hbMs)];
      req.signal.addEventListener("abort", () => {
        parar();
        try {
          controller.close();
        } catch {
          // já fechado
        }
      });
    },
    cancel() {
      parar();
    },
  });

  return new Response(stream, {
    headers: {
      "content-type": "text/event-stream; charset=utf-8",
      "cache-control": "no-store",
      connection: "keep-alive",
      "x-accel-buffering": "no",
    },
  });
}
