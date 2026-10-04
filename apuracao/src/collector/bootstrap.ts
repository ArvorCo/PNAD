// Partida comum ao coletor e ao sweep-once: banco, ele-c, cm, registro e estado.
import type { Database } from "bun:sqlite";
import type { Config } from "../config.ts";
import { abrirEscrita } from "../db/abrir.ts";
import { Escritor } from "../db/escrita.ts";
import type { ItemLote } from "../db/escrita.ts";
import { normalizarEleC } from "../parse/normalizar.ts";
import { parseCorpo } from "../parse/schemas.ts";
import type { MunCm } from "../parse/schemas.ts";
import { keyCm, keyEleC, registroDeArquivos, urlDe, chave } from "../tse/urls.ts";
import type { FetchResult, FileKey, Job } from "../types.ts";
import type { CtxProc, Knobs } from "./contexto.ts";
import { EstadoArquivos } from "./estado-arquivos.ts";
import { fetchTse } from "./http.ts";
import type { OpcoesHttp } from "./http.ts";
import { Lote } from "./lote.ts";
import { processar } from "./processar.ts";
import { relogioReal } from "./relogio.ts";
import type { Relogio } from "./relogio.ts";

export interface Coletor {
  config: Config;
  db: Database;
  escritor: Escritor;
  lote: Lote;
  estado: EstadoArquivos;
  ctx: CtxProc;
  relogio: Relogio;
  http: OpcoesHttp;
}

export interface OpcoesInicio {
  relogio?: Relogio;
  http?: Partial<OpcoesHttp>;
  log?: (o: Record<string, unknown>) => void;
  /** APURACAO_ELEICOES definido: não exige as eleições padrão no ele-c */
  eleicoesForcadas?: boolean;
}

export function knobsDe(config: Config): Knobs {
  return { zonas: config.zonas, minIntervaloMuS: config.minIntervaloMuS, sweepMin: config.sweepMin, concurrency: config.concurrency };
}

async function buscar(url: string, http: OpcoesHttp, tentativas = 3): Promise<FetchResult> {
  let r: FetchResult | null = null;
  for (let i = 0; i < tentativas; i++) {
    r = await fetchTse({ url, motivo: "periodico" }, null, http);
    if (r.classe === "ok") return r;
    await Bun.sleep(1000 * 2 ** i);
  }
  return r as FetchResult;
}

const ERRO_CONFIG = "configuração do TSE inválida";

export async function inicializar(config: Config, o: OpcoesInicio = {}): Promise<Coletor> {
  const relogio = o.relogio ?? relogioReal;
  const log = o.log ?? ((x: Record<string, unknown>) => console.log(JSON.stringify(x)));
  const db = abrirEscrita(config.dbPath);
  const escritor = new Escritor(db);
  const http: OpcoesHttp = { ua: config.userAgent, timeoutMs: config.timeoutMs, baseUrl: config.baseUrl, ...o.http };
  const jaTemRegistro = (db.query<{ n: number }, []>("SELECT COUNT(*) AS n FROM arquivo").get()?.n ?? 0) > 0;

  const eleC = await buscar(urlDe(keyEleC()), http);
  if (eleC.classe === "ok" && eleC.body !== null) {
    const p = parseCorpo("ele-c", eleC.body);
    if (!p.ok || p.parsed.tipo !== "ele-c") throw new Error(`${ERRO_CONFIG}: ele-c ${p.ok ? "" : p.erro}`);
    const n = normalizarEleC(p.parsed.data, config.pleito);
    const cds = new Set(n.eleicoes.map((e) => e.cd));
    const faltam = config.eleicoes.filter((e) => !cds.has(e));
    const ciclo = n.eleicoes[0]?.ciclo ?? null;
    if (n.eleicoes.length === 0 || (ciclo !== null && ciclo !== config.ciclo)) throw new Error(`${ERRO_CONFIG}: pleito ${config.pleito}/${config.ciclo} ausente`);
    if (faltam.length > 0) {
      if (!o.eleicoesForcadas) throw new Error(`${ERRO_CONFIG}: eleições ${faltam.join(",")} fora do pleito ${config.pleito}`);
      log({ t: "aviso", msg: `eleições ${faltam.join(",")} fora do ele-c; seguindo por APURACAO_ELEICOES` });
    }
  } else if (!jaTemRegistro) {
    throw new Error(`ele-c indisponível (${eleC.classe} ${eleC.erro ?? ""}) e banco sem registro`);
  } else {
    log({ t: "aviso", msg: `ele-c indisponível (${eleC.classe}); seguindo com o registro do banco` });
  }

  const cms = new Map<number, { r: FetchResult; data: MunCm }>();
  for (const ele of config.eleicoes) {
    const r = await buscar(urlDe(keyCm(ele)), http);
    const p = r.classe === "ok" && r.body !== null ? parseCorpo("cm", r.body) : null;
    if (p?.ok && p.parsed.tipo === "cm") cms.set(ele, { r, data: p.parsed.data });
    else if (!jaTemRegistro) throw new Error(`cm ${ele} indisponível (${r.classe} ${p && !p.ok ? p.erro : ""})`);
    else log({ t: "aviso", msg: `cm ${ele} indisponível (${r.classe}); seguindo com o registro do banco` });
  }

  if (cms.size > 0) {
    const itens: ItemLote[] = [];
    const porEle = new Map([...cms].map(([ele, v]) => [ele, v.data] as const));
    for (const row of registroDeArquivos(porEle)) itens.push({ k: "arquivo", row });
    escritor.gravarLote(itens);
  }

  const estado = EstadoArquivos.carregarDoBanco(db);
  const lote = new Lote(escritor, relogio, config.loteMs, config.loteItens, (err, g) => {
    log({ t: "erro_gravacao", erro: err instanceof Error ? err.message : String(err), itens: g.map((x) => x.k).join(",") });
  });
  const ctx: CtxProc = {
    db, estado, lote, relogio, knobs: knobsDe(config), pleito: config.pleito, driftContagem: new Map(), driftVisto: new Set(),
  };

  const registrar = (k: FileKey, r: FetchResult): void => {
    const fs = estado.porChave.get(chave(k));
    if (!fs) return;
    const job: Job = { arquivoId: fs.id, chave: fs.chave, url: fs.url, prioridade: "t0", due: relogio.agora(), motivo: "periodico" };
    processar(ctx, job, fs, r, Date.parse(r.iniciadoEm) || relogio.agora());
  };
  if (eleC.classe === "ok") registrar(keyEleC(), eleC);
  for (const [ele, v] of cms) registrar(keyCm(ele), v.r);
  lote.gravar();
  return { config, db, escritor, lote, estado, ctx, relogio, http };
}
