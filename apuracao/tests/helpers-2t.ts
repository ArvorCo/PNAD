// Utilitários dos testes do motor do 2º turno: contratos zod das rotas /api/2t/pausas,
// /api/2t/secoes e /api/2t/paralela (CONTRATO.md), banco temporário semeado por versões de
// arquivo e respostas falsas do TSE e do Supabase.
import type { Database } from "bun:sqlite";
import { mkdtempSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { z } from "zod";
import { Escritor } from "../src/db/escrita.ts";
import type { ItemLote } from "../src/db/escrita.ts";
import { sha256Hex } from "../src/db/itens.ts";
import { chave, keyAb, keyU, urlDe } from "../src/tse/urls.ts";
import type { Nivel } from "../src/types.ts";
import { FIXTURES } from "./helpers.ts";

export const DIR_2T = join(FIXTURES, "2t-motor");
export const fixture2t = (nome: string): unknown => JSON.parse(readFileSync(join(DIR_2T, nome), "utf8"));
export const BU_FIXTURE = join(FIXTURES, "bu", "o03220sp7107200010001-bu.dat");

export const tmp = (prefixo: string): string => mkdtempSync(join(tmpdir(), prefixo));

// ---------------------------------------------------------------- contratos

const Iso = z.string().regex(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/);
const Uf = z.string().regex(/^[A-Z]{2}$/);
const Hhmm = z.string().regex(/^\d{2}:\d{2}( \(\+\d\))?$/);

const Historico = z.object({ de: Iso, ate: Iso, minutos: z.number(), st_antes: z.number().nullable(), st_depois: z.number().nullable() }).strict();
const PausaAtual = z.object({ desde: Iso, minutos: z.number() }).strict().nullable();

export const PausasSchema = z
  .object({
    at: Iso,
    min: z.number().nullable(),
    limiar_min: z.number(),
    nacional: z
      .object({
        ultima_versao_em: Iso.nullable(), idade_s: z.number().nullable(), st: z.number(), ts: z.number(), em_pausa: z.boolean(),
        pausa_atual: PausaAtual, historico: z.array(Historico),
      })
      .strict(),
    soma_ufs: z.object({ st: z.number(), pst: z.number(), defasagem_secoes: z.number(), defasagem_min: z.number() }).strict(),
    ufs: z.array(
      z
        .object({
          uf: Uf, ultima_versao_em: Iso.nullable(), idade_s: z.number().nullable(), em_pausa: z.boolean(), st: z.number(), ts: z.number(),
          historico_n: z.number().int(),
        })
        .strict(),
    ),
    referencia_1t: z
      .object({
        pausa_geral: z.object({ de: z.literal("19:32"), ate: z.literal("20:02"), minutos: z.literal(29.6) }).strict(),
        travamento_nacional: z.object({ de: z.literal("18:00"), ate: z.literal("18:10") }).strict(),
      })
      .strict(),
  })
  .strict();

const BlocoSecoes = {
  alvo: z.number().int(),
  recebidas: z.number().int(),
  encerramento_p50_hhmm: Hhmm.nullable(),
  encerramento_p90_hhmm: Hhmm.nullable(),
  tarde_apos_1730_pct: z.number().nullable(),
  lag_encerr_recebimento_min: z.object({ p50: z.number().nullable(), p90: z.number().nullable(), p99: z.number().nullable() }).strict(),
  lag_encerr_emissao_min: z.object({ p50: z.number().nullable(), p90: z.number().nullable() }).strict(),
  lag_recebimento_totalizacao_min: z.object({ p50: z.number().nullable(), p90: z.number().nullable(), p99: z.number().nullable() }).strict(),
  ref_1t: z.object({ lag_p50: z.number().nullable(), lag_p90: z.number().nullable(), enc_p90_hhmm: z.string().nullable() }).strict().nullable(),
};

export const SecoesSchema = z
  .object({
    at: Iso,
    min: z.number().nullable(),
    desenho: z.object({ nacional_por_uf: z.number(), estaduais_por_uf: z.number(), inclui_paralela: z.literal(true), intervalo_s: z.number() }).strict(),
    totais: z.object({ alvo: z.number().int(), recebidas: z.number().int(), pendentes: z.number().int(), tardias: z.number().int() }).strict(),
    por_uf: z.array(z.object({ uf: Uf, ...BlocoSecoes }).strict()),
    brasil: z.object(BlocoSecoes).strict(),
    tardias: z.array(
      z
        .object({
          uf: Uf, mun: z.string().regex(/^\d{5}$/), nm: z.string(), zona: z.number().int(), secao: z.number().int(), encerramento_hhmm: Hhmm,
          recebido_hhmm: Hhmm.nullable(), lag_min: z.number().nullable(),
        })
        .strict(),
    ),
    ultimas: z.array(
      z.object({ uf: Uf, mun: z.string().regex(/^\d{5}$/), zona: z.number().int(), secao: z.number().int(), recebido_em: Iso, lag_min: z.number().nullable() }).strict(),
    ),
  })
  .strict();

const Situacao = z.enum(["igual", "divergente", "tse_ainda_nao_publicou", "erro", "fora_do_oficial"]);
const Valor = z.union([z.number(), z.boolean(), z.null()]);

export const ParalelaSchema = z
  .object({
    at: Iso,
    fonte: z.literal("supabase"),
    atualizado_em: Iso.nullable(),
    erro: z.string().nullable(),
    recebidos: z.object({ bus: z.number().int(), envios: z.number().int(), secoes: z.number().int(), ufs: z.number().int(), conflitos: z.number().int() }).strict(),
    conferencia: z
      .object({
        iguais: z.number().int(), divergentes: z.number().int(), tse_ainda_nao_publicou: z.number().int(), erro: z.number().int(),
        fora_do_oficial: z.number().int(), pendentes: z.number().int(),
      })
      .strict(),
    cobertura_uf: z.array(z.object({ uf: Uf, bus: z.number().int(), secoes_total: z.number().int(), pct: z.number() }).strict()),
    placar_bus: z
      .object({
        rotulo: z.literal("soma dos BUs recebidos, não projeção"),
        presidente: z
          .object({
            votos: z.record(z.string().regex(/^\d+$/), z.number().int()), comparecimento: z.number().int(), aptos: z.number().int(),
            brancos: z.number().int(), nulos: z.number().int(), secoes: z.number().int(),
          })
          .strict(),
        governador: z.record(Uf, z.object({ votos: z.record(z.string().regex(/^\d+$/), z.number().int()), secoes: z.number().int() }).strict()),
      })
      .strict(),
    divergencias: z.array(
      z
        .object({
          uf: Uf, mun: z.string(), zona: z.number().int(), secao: z.number().int(), recebido_em: Iso, conferido_em: Iso,
          campos: z.array(z.object({ campo: z.string().min(1), paralela: Valor, tse: Valor }).strict()),
        })
        .strict(),
    ),
    ultimos: z.array(
      z
        .object({ uf: Uf, mun: z.string(), zona: z.number().int(), secao: z.number().int(), recebido_em: Iso, situacao: z.union([Situacao, z.literal("pendente")]) })
        .strict(),
    ),
  })
  .strict();

// ---------------------------------------------------------------- banco semeado

export interface VersaoTeste {
  nivel: Extract<Nivel, "br" | "uf" | "mu">;
  uf?: string;
  mun?: string;
  gerado: string;
  st: number;
  ts: number;
  /** captura (padrão: geração + 5 s) */
  capturado?: string;
  totalizado?: string;
}

/** Registra os arquivos -u (presidente) e grava as versões com totais (totalizado_em como publicado). */
export function semearVersoes(db: Database, ele: number, versoes: readonly VersaoTeste[]): void {
  const w = new Escritor(db);
  const itens: ItemLote[] = [];
  const vistos = new Set<string>();
  for (const v of versoes) {
    const k = keyU(ele, 1, v.nivel, v.uf ?? null, v.mun ?? null);
    const ch = chave(k);
    if (!vistos.has(ch)) {
      vistos.add(ch);
      itens.push({ k: "arquivo", row: { ...k, chave: ch, url: urlDe(k), tier: 0, sonda: false } });
    }
  }
  w.gravarLote(itens);
  for (const v of versoes) {
    const ch = chave(keyU(ele, 1, v.nivel, v.uf ?? null, v.mun ?? null));
    const id = db.query<{ id: number }, [string]>("SELECT id FROM arquivo WHERE chave = ?").get(ch)?.id;
    if (id === undefined) throw new Error(`arquivo ${ch}`);
    const corpo = new TextEncoder().encode(JSON.stringify(v));
    const sha = sha256Hex(corpo);
    const cap = v.capturado ?? new Date(Date.parse(v.gerado) + 5000).toISOString();
    const pst = v.ts > 0 ? (100 * v.st) / v.ts : 0;
    w.gravarLote([
      { k: "blob", sha256: sha, bytes: corpo.byteLength, gz: Bun.gzipSync(corpo), criado_em: cap },
      {
        k: "snapshot", ref: "s",
        row: {
          arquivo_id: id, fetch_id: null, sha256: sha, capturado_em: cap, dg: null, hg: null, idg: null, gerado_em: v.gerado, dt: null, ht: null,
          totalizado_em: v.totalizado ?? v.gerado, tf: 0, andamento: null, divulgacao: null, turno: 2, regressivo: 0, anterior_id: null,
        },
      },
      {
        k: "totais", snapshot: { ref: "s" },
        row: {
          vagas: null, ts: v.ts, st: v.st, snt: null, si: null, sni: null, sa: null, sna: null, pst, te: null, est: null, esnt: null, esi: null, esni: null,
          esa: null, esna: null, comparecimento: null, abstencao: null, pc: null, pa: null, tv: null, vvc: null, vv: null, vnom: null, vl: null, van: null,
          vansj: null, vb: null, tvn: null, vn: null, vnt: null, vsan: null, vscv: null, pvvc: null, pvb: null, ptvn: null, pvan: null, pvn: null,
        },
      },
    ]);
  }
}

/** Arquivo -ab de UF com a entrada de um município (totalizado_em como publicado). */
export function semearAbMunicipio(db: Database, ele: number, uf: string, mun: string, entradas: readonly { gerado: string; totalizado: string; st: number; ts: number }[]): void {
  const w = new Escritor(db);
  const k = keyAb(ele, uf);
  const ch = chave(k);
  w.gravarLote([{ k: "arquivo", row: { ...k, chave: ch, url: urlDe(k), tier: 1, sonda: false } }]);
  const id = db.query<{ id: number }, [string]>("SELECT id FROM arquivo WHERE chave = ?").get(ch)?.id ?? 0;
  for (const e of entradas) {
    const corpo = new TextEncoder().encode(JSON.stringify({ ...e, mun }));
    const sha = sha256Hex(corpo);
    w.gravarLote([
      { k: "blob", sha256: sha, bytes: corpo.byteLength, gz: Bun.gzipSync(corpo), criado_em: e.gerado },
      {
        k: "snapshot", ref: "s",
        row: {
          arquivo_id: id, fetch_id: null, sha256: sha, capturado_em: e.gerado, dg: null, hg: null, idg: null, gerado_em: e.gerado, dt: null, ht: null,
          totalizado_em: null, tf: 0, andamento: null, divulgacao: null, turno: 2, regressivo: 0, anterior_id: null,
        },
      },
      {
        k: "ab_estado", snapshot: { ref: "s" },
        rows: [
          {
            tpabr: "mun", cdabr: mun, andamento: null, dt: null, ht: null, totalizado_em: e.totalizado, ts: e.ts, st: e.st, pst: null, snt: null,
            si: null, sni: null, sa: null, sna: null, te: null, est: null, esnt: null, esi: null, esni: null, esa: null, esna: null,
            comparecimento: null, abstencao: null, munnr: null, munpt: null, munf: null, ufsnr: null, ufspt: null, ufsf: null,
          },
        ],
      },
    ]);
  }
}

// ---------------------------------------------------------------- respostas falsas

/** fetch falso do PostgREST: devolve as fixtures por view, respeitando offset/limit e id=gt. */
export function supabaseFalso(dados: Record<string, unknown[]>, falhar: (url: string) => boolean = () => false): (url: string) => Promise<Response> {
  return async (url: string) => {
    if (falhar(url)) throw new TypeError("fetch failed");
    const u = new URL(url);
    const view = u.pathname.split("/").pop() ?? "";
    let linhas = [...(dados[view] ?? [])] as Record<string, number>[];
    for (const [k, v] of u.searchParams) {
      const m = /^(gt|gte|lte)\.(\d+)$/.exec(v);
      if (!m) continue;
      const n = Number(m[2]);
      linhas = linhas.filter((x) => (m[1] === "gt" ? (x[k] ?? 0) > n : m[1] === "gte" ? (x[k] ?? 0) >= n : (x[k] ?? 0) <= n));
    }
    const offset = Number(u.searchParams.get("offset") ?? 0);
    const limit = Number(u.searchParams.get("limit") ?? 1000);
    const pagina = linhas.slice(offset, offset + limit);
    const faixa = pagina.length === 0 ? `*/${linhas.length}` : `${offset}-${offset + pagina.length - 1}/${linhas.length}`;
    return new Response(JSON.stringify(pagina), { status: 200, headers: { "content-range": faixa } });
  };
}
