// Estado em memória de cada arquivo do registro, reconstruível do banco na partida.
import type { Database } from "bun:sqlite";
import { CARGOS_MAJORITARIOS } from "../config.ts";
import type { ArquivoEstado, IdRef } from "../db/escrita.ts";
import { blobDoSnapshot, todosArquivos } from "../db/leitura.ts";
import type { ArquivoLido } from "../db/leitura.ts";
import type { LinhaTotais, N, S } from "../db/linhas.ts";
import { fingerprintAb } from "../parse/normalizar.ts";
import { intBR } from "../parse/numeros.ts";
import { parseCorpo } from "../parse/schemas.ts";
import type { AbFile } from "../parse/schemas.ts";
import type { ClasseFetch, FetchResult, FileKey, Tier } from "../types.ts";
import { isoDe, msDe } from "./relogio.ts";

/** Contagens que as anomalias comparam. */
export interface TotaisResumo {
  ts: N; st: N; pst: N; vvc: N; vv: N; vnom: N; tv: N; comparecimento: N; est: N;
}

export interface CandResumo {
  vap: N;
  eleito: 0 | 1 | null;
}

export interface FileState {
  id: number;
  chave: string;
  url: string;
  key: FileKey;
  tier: Tier;
  sonda: boolean;
  ativo: boolean;
  etag: S;
  lastModified: S;
  sha256: S;
  /** sha da última cópia regressiva vista, para não repetir snapshot dela */
  shaRegressivo: S;
  idg: N;
  geradoEm: S;
  ultimoSnapshotId: IdRef | null;
  /** epoch ms */
  ultimoFetchEm: number | null;
  ultimoStatus: S;
  nFetch: number;
  nMudancas: number;
  errosSeguidos: number;
  backoffAte: number | null;
  finalAgendado: boolean;
  totaisAnteriores: TotaisResumo | null;
  /** só para arquivos com política "sempre" (br, uf, majoritários) */
  candidatosAnteriores: Map<number, CandResumo> | null;
  emVoo: boolean;
}

export const resumoTotais = (t: Partial<LinhaTotais>): TotaisResumo => ({
  ts: t.ts ?? null, st: t.st ?? null, pst: t.pst ?? null, vvc: t.vvc ?? null, vv: t.vv ?? null, vnom: t.vnom ?? null,
  tv: t.tv ?? null, comparecimento: t.comparecimento ?? null, est: t.est ?? null,
});

/** Arquivo cujo voto_candidato é sempre normalizado (guarda candidatos em memória). */
export function candidatosSempre(k: FileKey): boolean {
  return k.tipo === "u" && (k.nivel === "br" || k.nivel === "uf" || (k.cargo !== null && CARGOS_MAJORITARIOS.has(k.cargo)));
}

export function estadoDeLinha(a: ArquivoLido): FileState {
  return {
    id: a.id, chave: a.chave, url: a.url,
    key: { tipo: a.tipo, ele: a.eleicao_cd, cargo: a.cargo_cd, nivel: a.nivel, uf: a.uf, mun: a.municipio_cd, zona: a.zona_cd },
    tier: a.tier as Tier, sonda: a.sonda === 1, ativo: a.ativo === 1, etag: a.etag, lastModified: a.last_modified,
    sha256: a.sha256, shaRegressivo: null, idg: a.idg, geradoEm: a.gerado_em, ultimoSnapshotId: a.ultimo_snapshot_id,
    ultimoFetchEm: msDe(a.ultimo_fetch_em), ultimoStatus: a.ultimo_status, nFetch: a.n_fetch, nMudancas: a.n_mudancas,
    errosSeguidos: a.erros_seguidos, backoffAte: msDe(a.backoff_ate), finalAgendado: a.final_agendado === 1,
    totaisAnteriores: null, candidatosAnteriores: null, emVoo: false,
  };
}

const chaveMun = (ele: number | null, uf: string | null, mun: string | null): string => `${ele ?? ""}:${uf ?? ""}:${mun ?? ""}`;

export class EstadoArquivos {
  readonly porId = new Map<number, FileState>();
  readonly porChave = new Map<string, FileState>();
  /** por arquivo -ab: cdabr → fingerprint */
  readonly abFingerprints = new Map<number, Map<string, string>>();
  /** "uf:mun" → eleitorado total visto no -ab */
  readonly teMunicipio = new Map<string, number>();
  /** códigos TSE de capitais */
  readonly capitais = new Set<string>();
  private readonly muIdx = new Map<string, number[]>();
  private readonly zonaIdx = new Map<string, number[]>();
  private readonly ufIdx = new Map<string, number[]>();

  adicionar(fs: FileState): void {
    this.porId.set(fs.id, fs);
    this.porChave.set(fs.chave, fs);
    const k = fs.key;
    const push = (m: Map<string, number[]>, chave: string): void => {
      const l = m.get(chave);
      if (l) l.push(fs.id);
      else m.set(chave, [fs.id]);
    };
    if (k.tipo === "u" && k.nivel === "mu") push(this.muIdx, chaveMun(k.ele, k.uf, k.mun));
    if (k.tipo === "u" && k.nivel === "zona") push(this.zonaIdx, chaveMun(k.ele, k.uf, k.mun));
    if ((k.tipo === "u" || k.tipo === "ab") && k.nivel === "uf") push(this.ufIdx, `${k.ele ?? ""}:${k.uf ?? ""}`);
  }

  get(id: number): FileState {
    const fs = this.porId.get(id);
    if (!fs) throw new Error(`arquivo ${id} fora do estado`);
    return fs;
  }

  doMunicipio(ele: number, uf: string, mun: string): FileState[] {
    return (this.muIdx.get(chaveMun(ele, uf, mun)) ?? []).map((id) => this.get(id));
  }

  zonasDoMunicipio(ele: number, uf: string, mun: string): FileState[] {
    return (this.zonaIdx.get(chaveMun(ele, uf, mun)) ?? []).map((id) => this.get(id));
  }

  /** ab e u de nível uf de uma eleição numa UF. */
  daUf(ele: number, uf: string): FileState[] {
    return (this.ufIdx.get(`${ele}:${uf}`) ?? []).map((id) => this.get(id));
  }

  /** Município grande: capital ou eleitorado ≥ limite. */
  municipioGrande(uf: string, mun: string, limite: number): boolean {
    return this.capitais.has(mun) || (this.teMunicipio.get(`${uf}:${mun}`) ?? 0) >= limite;
  }

  /** Lê um -ab já validado: fingerprints e eleitorado por município. */
  registrarAb(arquivoId: number, uf: string | null, p: AbFile): Map<string, string> {
    const fps = new Map<string, string>();
    for (const a of p.abr) {
      if (!a.cdabr) continue;
      fps.set(a.cdabr, fingerprintAb(a));
      const te = intBR(a.e?.te);
      if (uf !== null && te !== null && a.tpabr !== "uf") this.teMunicipio.set(`${uf}:${a.cdabr}`, te);
    }
    return fps;
  }

  /** Campos comuns de toda resposta: contadores, validadores, status. `inicio` = relógio do agendador no despacho. */
  aplicarResultado(fs: FileState, r: FetchResult, classe: ClasseFetch, inicio: number): void {
    fs.nFetch++;
    fs.ultimoFetchEm = inicio;
    fs.ultimoStatus = classe;
    if (classe === "ok" || classe === "igual" || classe === "nao_modificado") {
      if (r.etag !== null) fs.etag = r.etag;
      if (r.lastModified !== null) fs.lastModified = r.lastModified;
      fs.errosSeguidos = 0;
      fs.backoffAte = null;
    }
  }

  paraLinha(fs: FileState): ArquivoEstado {
    return {
      ativo: fs.ativo ? 1 : 0, etag: fs.etag, last_modified: fs.lastModified, sha256: fs.sha256, idg: fs.idg,
      gerado_em: fs.geradoEm, ultimo_snapshot_id: fs.ultimoSnapshotId,
      ultimo_fetch_em: fs.ultimoFetchEm === null ? null : isoDe(fs.ultimoFetchEm), ultimo_status: fs.ultimoStatus,
      n_fetch: fs.nFetch, n_mudancas: fs.nMudancas, erros_seguidos: fs.errosSeguidos,
      backoff_ate: fs.backoffAte === null ? null : isoDe(fs.backoffAte), final_agendado: fs.finalAgendado ? 1 : 0,
    };
  }

  /** Reconstrói tudo de `arquivo`, `totais`, `voto_candidato`, `municipio` e do último blob de cada -ab. */
  static carregarDoBanco(db: Database): EstadoArquivos {
    const est = new EstadoArquivos();
    for (const a of todosArquivos(db)) est.adicionar(estadoDeLinha(a));

    type LinhaT = Partial<LinhaTotais> & { arquivo_id: number };
    for (const t of db
      .query<LinhaT, []>(
        `SELECT a.id AS arquivo_id, t.ts, t.st, t.pst, t.vvc, t.vv, t.vnom, t.tv, t.comparecimento, t.est
         FROM arquivo a JOIN totais t ON t.snapshot_id = a.ultimo_snapshot_id`,
      )
      .iterate()) {
      const fs = est.porId.get(t.arquivo_id);
      if (fs) fs.totaisAnteriores = resumoTotais(t);
    }

    type LinhaC = { arquivo_id: number; sqcand: number; vap: N; eleito: 0 | 1 | null };
    for (const c of db
      .query<LinhaC, []>(
        `SELECT a.id AS arquivo_id, vc.sqcand, vc.vap, vc.eleito
         FROM arquivo a JOIN voto_candidato vc ON vc.snapshot_id = a.ultimo_snapshot_id
         WHERE a.tipo = 'u' AND (a.nivel IN ('br', 'uf') OR a.cargo_cd IN (1, 3, 5, 25))`,
      )
      .iterate()) {
      const fs = est.porId.get(c.arquivo_id);
      if (!fs) continue;
      fs.candidatosAnteriores ??= new Map();
      fs.candidatosAnteriores.set(c.sqcand, { vap: c.vap, eleito: c.eleito });
    }

    for (const m of db.query<{ cd: string }, []>("SELECT cd FROM municipio WHERE capital = 1").iterate()) est.capitais.add(m.cd);

    for (const fs of est.porId.values()) {
      if (fs.key.tipo !== "ab" || typeof fs.ultimoSnapshotId !== "number") continue;
      const gz = blobDoSnapshot(db, fs.ultimoSnapshotId);
      if (!gz) continue;
      const r = parseCorpo("ab", Bun.gunzipSync(gz));
      if (r.ok && r.parsed.tipo === "ab") est.abFingerprints.set(fs.id, est.registrarAb(fs.id, fs.key.uf, r.parsed.data));
    }
    return est;
  }
}
