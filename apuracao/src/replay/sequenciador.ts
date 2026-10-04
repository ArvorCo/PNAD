// Sequenciador mínimo de replay sobre as primitivas do B1:
// corpo → sha → parseCorpo → normalizar* → itensDe* → Escritor, com o estado de cada arquivo em memória.
// Não calcula anomalias nem agenda nada (isso é do coletor, B2). Quando src/collector/processar.ts
// estiver pronto, este módulo pode ser trocado por ele sem mudar o formato do banco.
import type { Database } from "bun:sqlite";
import { Escritor } from "../db/escrita.ts";
import type { ArquivoEstado, ItemLote, LinhaFetch } from "../db/escrita.ts";
import { comprimir, itensDeAb, itensDeCm, itensDeE, itensDeEleC, itensDeU, sha256Hex } from "../db/itens.ts";
import type { LinhaSnapshotMeta } from "../db/linhas.ts";
import { todosArquivos } from "../db/leitura.ts";
import { normalizarAb, normalizarCm, normalizarE, normalizarEleC, normalizarU, politicaPara } from "../parse/normalizar.ts";
import { parseCorpo } from "../parse/schemas.ts";
import type { ArquivoRegistro, ClasseFetch, Nivel, Tipo } from "../types.ts";

interface EstadoArq {
  id: number;
  tipo: Tipo;
  cargo: number | null;
  nivel: Nivel | null;
  uf: string | null;
  sha: string | null;
  idg: number | null;
  geradoEm: string | null;
  ultimoSnapshot: number | null;
  fps: Map<string, string>;
  nFetch: number;
  nMudancas: number;
}

export interface Contagem {
  fetches: number;
  snapshots: number;
  regressivos: number;
  iguais: number;
  nao_existe: number;
  parse_error: number;
}

export type Desfecho = "snapshot" | "regressivo" | "igual" | "nao_existe" | "parse_error";

export class Sequenciador {
  private readonly w: Escritor;
  private readonly arqs = new Map<string, EstadoArq>();
  readonly contagem: Contagem = { fetches: 0, snapshots: 0, regressivos: 0, iguais: 0, nao_existe: 0, parse_error: 0 };

  constructor(private readonly db: Database) {
    this.w = new Escritor(db);
    this.recarregar();
  }

  private recarregar(): void {
    for (const a of todosArquivos(this.db)) {
      if (this.arqs.has(a.chave)) continue;
      this.arqs.set(a.chave, {
        id: a.id, tipo: a.tipo, cargo: a.cargo_cd, nivel: a.nivel, uf: a.uf, sha: a.sha256, idg: a.idg, geradoEm: a.gerado_em,
        ultimoSnapshot: a.ultimo_snapshot_id, fps: new Map(), nFetch: a.n_fetch, nMudancas: a.n_mudancas,
      });
    }
  }

  /** Grava o registro em lotes e recarrega os ids. */
  registrar(regs: Iterable<ArquivoRegistro>): void {
    let lote: ItemLote[] = [];
    for (const row of regs) {
      if (this.arqs.has(row.chave)) continue;
      lote.push({ k: "arquivo", row });
      if (lote.length >= 5000) {
        this.w.gravarLote(lote);
        lote = [];
      }
    }
    if (lote.length > 0) this.w.gravarLote(lote);
    this.recarregar();
  }

  idDe(chave: string): number | null {
    return this.arqs.get(chave)?.id ?? null;
  }

  /** Grava itens avulsos (eventos de teste, meta). */
  gravar(itens: ItemLote[]): void {
    this.w.gravarLote(itens);
  }

  /** Processa uma leitura de arquivo: corpo null = arquivo inexistente no TSE. */
  processar(chave: string, corpo: Uint8Array<ArrayBuffer> | null, em: string): Desfecho {
    const a = this.arqs.get(chave);
    if (!a) throw new Error(`arquivo não registrado: ${chave}`);
    this.contagem.fetches += 1;
    a.nFetch += 1;
    const fetchRow = (classe: ClasseFetch, sha: string | null, status: number): LinhaFetch => ({
      arquivo_id: a.id, iniciado_em: em, duracao_ms: 0, motivo: "periodico", condicional: 0, http_status: status, classe,
      etag: null, last_modified: null, servidor_date: null, cache_hdr: null, age: null, bytes: corpo?.byteLength ?? 0,
      body_sha256: sha, mudou: 0, erro: null,
    });
    const estado = (status: string, sid: { ref: string } | number | null): ArquivoEstado => ({
      ativo: status === "nao_existe" ? 0 : 1, etag: null, last_modified: null, sha256: a.sha, idg: a.idg, gerado_em: a.geradoEm,
      ultimo_snapshot_id: sid, ultimo_fetch_em: em, ultimo_status: status, n_fetch: a.nFetch, n_mudancas: a.nMudancas,
      erros_seguidos: 0, backoff_ate: null, final_agendado: 0,
    });
    if (corpo === null) {
      this.contagem.nao_existe += 1;
      this.w.gravarLote([{ k: "fetch", row: fetchRow("nao_existe", null, 404) }, { k: "arquivo_estado", id: a.id, row: estado("nao_existe", a.ultimoSnapshot) }]);
      return "nao_existe";
    }
    const sha = sha256Hex(corpo);
    if (sha === a.sha) {
      this.contagem.iguais += 1;
      this.w.gravarLote([{ k: "fetch", row: fetchRow("igual", sha, 200) }, { k: "arquivo_estado", id: a.id, row: estado("igual", a.ultimoSnapshot) }]);
      return "igual";
    }
    const { gz, bytes } = comprimir(corpo);
    const blob: ItemLote = { k: "blob", sha256: sha, bytes, gz, criado_em: em };
    const r = parseCorpo(a.tipo, corpo);
    if (!r.ok) {
      this.contagem.parse_error += 1;
      this.w.gravarLote([
        { k: "fetch", row: fetchRow("corpo_invalido", sha, 200) },
        blob,
        { k: "evento", row: { em, tipo: "parse_error", severidade: "error", arquivo_id: a.id, detalhe: { erro: r.erro, chave } } },
      ]);
      return "parse_error";
    }
    let meta: LinhaSnapshotMeta;
    let itens: (snap: { ref: string }) => ItemLote[];
    let fps: Map<string, string> | null = null;
    const p = r.parsed;
    switch (p.tipo) {
      case "u": {
        const n = normalizarU(p.data, {
          uf: a.uf, politicaCandidatos: politicaPara(a.cargo ?? 0, a.nivel ?? "br"), primeiro: a.ultimoSnapshot === null,
        });
        meta = n.snapshotMeta;
        itens = (s) => itensDeU(n, s);
        break;
      }
      case "ab": {
        const n = normalizarAb(p.data, a.fps);
        meta = n.snapshotMeta;
        fps = n.fingerprints;
        itens = (s) => itensDeAb(n, s);
        break;
      }
      case "ele-c": {
        const n = normalizarEleC(p.data);
        meta = n.snapshotMeta;
        itens = () => itensDeEleC(n);
        break;
      }
      case "cm": {
        const n = normalizarCm(p.data);
        meta = n.snapshotMeta;
        itens = () => itensDeCm(n);
        break;
      }
      case "e": {
        const n = normalizarE(p.data);
        meta = n.snapshotMeta;
        itens = (s) => itensDeE(n, s);
        break;
      }
    }
    const regressivo = meta.idg !== null && a.idg !== null && meta.idg < a.idg;
    const s = { ref: "s" };
    const lote: ItemLote[] = [
      { k: "fetch", ref: "f", row: fetchRow("ok", sha, 200) },
      blob,
      {
        k: "snapshot", ref: "s",
        row: { ...meta, arquivo_id: a.id, fetch_id: { ref: "f" }, sha256: sha, capturado_em: em, regressivo: regressivo ? 1 : 0, anterior_id: a.ultimoSnapshot },
      },
    ];
    if (!regressivo) {
      lote.push(...itens(s));
      a.sha = sha;
      a.idg = meta.idg ?? a.idg;
      a.geradoEm = meta.gerado_em;
      a.nMudancas += 1;
    }
    lote.push({ k: "arquivo_estado", id: a.id, row: estado("ok", regressivo ? a.ultimoSnapshot : s) });
    const res = this.w.gravarLote(lote);
    if (regressivo) {
      this.contagem.regressivos += 1;
      return "regressivo";
    }
    a.ultimoSnapshot = res.ids.get("s") ?? a.ultimoSnapshot;
    if (fps) a.fps = fps;
    this.contagem.snapshots += 1;
    return "snapshot";
  }
}
