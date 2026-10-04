// Escritor único: statements preparados e gravação de lotes numa transação.
import type { Database, Statement } from "bun:sqlite";
import type { ArquivoRegistro, ClasseFetch, MotivoFetch, Severidade } from "../types.ts";
import type {
  LinhaAbEstado, LinhaCandidato, LinhaCargo, LinhaEEntrada, LinhaEleicao, LinhaFederacao, LinhaMunicipio,
  LinhaPartido, LinhaSnapshotMeta, LinhaTotais, LinhaUf, LinhaVotoAgremiacao, LinhaVotoCandidato,
  LinhaVotoPartido, LinhaZona, N, S,
} from "./linhas.ts";

/** Id já conhecido ou referência a um id criado antes no mesmo lote. */
export type IdRef = number | { ref: string };

export interface LinhaFetch {
  arquivo_id: IdRef;
  iniciado_em: string;
  duracao_ms: N;
  motivo: MotivoFetch;
  condicional: 0 | 1;
  http_status: N;
  classe: ClasseFetch;
  etag: S;
  last_modified: S;
  servidor_date: S;
  cache_hdr: S;
  age: N;
  bytes: N;
  body_sha256: S;
  mudou: 0 | 1;
  erro: S;
}

export interface LinhaSnapshot extends LinhaSnapshotMeta {
  arquivo_id: IdRef;
  fetch_id: IdRef | null;
  sha256: string;
  capturado_em: string;
  regressivo: 0 | 1;
  anterior_id: IdRef | null;
}

/** Estado mutável de um arquivo; o coletor mantém tudo em memória e sobrescreve inteiro. */
export interface ArquivoEstado {
  ativo: 0 | 1;
  etag: S;
  last_modified: S;
  sha256: S;
  idg: N;
  gerado_em: S;
  ultimo_snapshot_id: IdRef | null;
  ultimo_fetch_em: S;
  ultimo_status: S;
  n_fetch: number;
  n_mudancas: number;
  erros_seguidos: number;
  backoff_ate: S;
  final_agendado: 0 | 1;
}

export interface EventoNovo {
  em: string;
  tipo: string;
  severidade?: Severidade;
  arquivo_id?: IdRef | null;
  snapshot_id?: IdRef | null;
  eleicao_cd?: N;
  cargo_cd?: N;
  nivel?: S;
  uf?: S;
  municipio_cd?: S;
  zona_cd?: S;
  /** objeto serializado em JSON */
  detalhe?: unknown;
}

export type ItemLote =
  | { k: "arquivo"; ref?: string; row: ArquivoRegistro }
  | { k: "arquivo_estado"; id: IdRef; row: ArquivoEstado }
  | { k: "fetch"; ref?: string; row: LinhaFetch }
  | { k: "blob"; sha256: string; bytes: number; gz: Uint8Array; criado_em: string }
  | { k: "snapshot"; ref?: string; row: LinhaSnapshot }
  | { k: "totais"; snapshot: IdRef; row: LinhaTotais }
  | { k: "voto_candidato"; snapshot: IdRef; rows: readonly LinhaVotoCandidato[] }
  | { k: "voto_partido"; snapshot: IdRef; rows: readonly LinhaVotoPartido[] }
  | { k: "voto_agremiacao"; snapshot: IdRef; rows: readonly LinhaVotoAgremiacao[] }
  | { k: "ab_estado"; snapshot: IdRef; rows: readonly LinhaAbEstado[] }
  | { k: "e_entrada"; snapshot: IdRef; rows: readonly LinhaEEntrada[] }
  | { k: "candidato"; snapshot: IdRef | null; rows: readonly LinhaCandidato[] }
  | { k: "partido"; rows: readonly LinhaPartido[] }
  | { k: "federacao"; rows: readonly LinhaFederacao[] }
  | { k: "evento"; ref?: string; row: EventoNovo }
  | { k: "municipio"; rows: readonly LinhaMunicipio[] }
  | { k: "zona"; rows: readonly LinhaZona[] }
  | { k: "eleicao"; rows: readonly LinhaEleicao[] }
  | { k: "cargo"; rows: readonly LinhaCargo[] }
  | { k: "uf"; rows: readonly LinhaUf[] }
  | { k: "meta"; chave: string; valor: string };

export interface ResultadoLote {
  /** ids criados, por ref */
  ids: Map<string, number>;
  itens: number;
}

type Params = Record<string, string | number | bigint | boolean | null | Uint8Array>;
type Stmt = Statement<unknown, [Params]>;

function insertSql(tabela: string, cols: readonly string[], sufixo = ""): string {
  return `INSERT INTO ${tabela} (${cols.join(", ")}) VALUES (${cols.map((c) => `$${c}`).join(", ")}) ${sufixo}`;
}

function upsertSql(tabela: string, cols: readonly string[], pk: readonly string[]): string {
  const sets = cols.filter((c) => !pk.includes(c)).map((c) => `${c} = COALESCE(excluded.${c}, ${tabela}.${c})`);
  return insertSql(tabela, cols, `ON CONFLICT (${pk.join(", ")}) DO UPDATE SET ${sets.join(", ")}`);
}

const COLS = {
  arquivo: ["chave", "url", "tipo", "eleicao_cd", "cargo_cd", "nivel", "uf", "municipio_cd", "zona_cd", "tier", "sonda"],
  fetch: [
    "arquivo_id", "iniciado_em", "duracao_ms", "motivo", "condicional", "http_status", "classe", "etag", "last_modified",
    "servidor_date", "cache_hdr", "age", "bytes", "body_sha256", "mudou", "erro",
  ],
  snapshot: [
    "arquivo_id", "fetch_id", "sha256", "capturado_em", "dg", "hg", "idg", "gerado_em", "dt", "ht", "totalizado_em",
    "tf", "andamento", "divulgacao", "turno", "regressivo", "anterior_id",
  ],
  totais: [
    "snapshot_id", "vagas", "ts", "st", "snt", "si", "sni", "sa", "sna", "pst", "te", "est", "esnt", "esi", "esni", "esa",
    "esna", "comparecimento", "abstencao", "pc", "pa", "tv", "vvc", "vv", "vnom", "vl", "van", "vansj", "vb", "tvn", "vn",
    "vnt", "vsan", "vscv", "pvvc", "pvb", "ptvn", "pvan", "pvn",
  ],
  voto_candidato: ["snapshot_id", "sqcand", "vap", "pvapn", "eleito", "st", "dvt"],
  voto_partido: ["snapshot_id", "agremiacao_n", "partido_n", "tvtn", "tvtl", "tval", "tvan", "dvt"],
  voto_agremiacao: ["snapshot_id", "agremiacao_n", "tp", "nome", "composicao", "tvtn", "tvtl", "tval", "tvan", "vagas"],
  ab_estado: [
    "snapshot_id", "tpabr", "cdabr", "andamento", "dt", "ht", "totalizado_em", "ts", "st", "pst", "snt", "si", "sni", "sa",
    "sna", "te", "est", "esnt", "esi", "esni", "esa", "esna", "comparecimento", "abstencao", "munnr", "munpt", "munf",
    "ufsnr", "ufspt", "ufsf",
  ],
  e_entrada: ["snapshot_id", "cdabr", "tpabr", "nome", "dt", "ht", "totalizado_em", "tvap", "cand"],
  candidato: [
    "sqcand", "eleicao_cd", "cargo_cd", "uf", "numero", "nome", "nome_urna", "nascimento", "partido_n", "federacao_n",
    "agremiacao_n", "vices", "primeiro_snapshot_id",
  ],
  partido: ["n", "sigla", "nome", "federacao_n"],
  federacao: ["n", "sigla", "nome", "composicao", "partidos"],
  evento: [
    "em", "tipo", "severidade", "arquivo_id", "snapshot_id", "eleicao_cd", "cargo_cd", "nivel", "uf", "municipio_cd",
    "zona_cd", "detalhe",
  ],
  municipio: ["cd", "uf", "ibge", "nome", "capital", "eleitores", "origem"],
  zona: ["municipio_cd", "cd", "uf"],
  eleicao: ["cd", "cdt2", "nome", "turno", "tipo", "pleito", "ciclo", "data"],
  cargo: ["eleicao_cd", "cd", "nome", "tp", "proporcional"],
  uf: ["sigla", "nome"],
} as const;

export class Escritor {
  private readonly st: Record<string, Stmt>;

  constructor(private readonly db: Database) {
    const q = (sql: string): Stmt => db.prepare<unknown, [Params]>(sql);
    this.st = {
      arquivo: q(insertSql("arquivo", COLS.arquivo, "ON CONFLICT (chave) DO NOTHING")),
      arquivoId: q("SELECT id FROM arquivo WHERE chave = $chave"),
      arquivoEstado: q(
        `UPDATE arquivo SET ativo = $ativo, etag = $etag, last_modified = $last_modified, sha256 = $sha256, idg = $idg,
         gerado_em = $gerado_em, ultimo_snapshot_id = $ultimo_snapshot_id, ultimo_fetch_em = $ultimo_fetch_em,
         ultimo_status = $ultimo_status, n_fetch = $n_fetch, n_mudancas = $n_mudancas, erros_seguidos = $erros_seguidos,
         backoff_ate = $backoff_ate, final_agendado = $final_agendado WHERE id = $id`,
      ),
      fetch: q(insertSql("fetch", COLS.fetch, "RETURNING id")),
      fetchSnapshot: q("UPDATE fetch SET snapshot_id = $snapshot_id, mudou = 1 WHERE id = $id"),
      blob: q(insertSql("blob", ["sha256", "bytes", "gz", "criado_em"], "ON CONFLICT (sha256) DO NOTHING")),
      snapshot: q(insertSql("snapshot", COLS.snapshot, "RETURNING id")),
      totais: q(insertSql("totais", COLS.totais, "ON CONFLICT (snapshot_id) DO NOTHING")),
      voto_candidato: q(insertSql("voto_candidato", COLS.voto_candidato, "ON CONFLICT DO NOTHING")),
      voto_partido: q(insertSql("voto_partido", COLS.voto_partido, "ON CONFLICT DO NOTHING")),
      voto_agremiacao: q(insertSql("voto_agremiacao", COLS.voto_agremiacao, "ON CONFLICT DO NOTHING")),
      ab_estado: q(insertSql("ab_estado", COLS.ab_estado, "ON CONFLICT DO NOTHING")),
      e_entrada: q(insertSql("e_entrada", COLS.e_entrada, "ON CONFLICT DO NOTHING")),
      candidato: q(insertSql("candidato", COLS.candidato, "ON CONFLICT (sqcand) DO NOTHING")),
      partido: q(upsertSql("partido", COLS.partido, ["n"])),
      federacao: q(upsertSql("federacao", COLS.federacao, ["n"])),
      evento: q(insertSql("evento", COLS.evento, "RETURNING id")),
      municipio: q(
        insertSql(
          "municipio",
          COLS.municipio,
          `ON CONFLICT (cd) DO UPDATE SET ibge = COALESCE(excluded.ibge, municipio.ibge),
           nome = COALESCE(excluded.nome, municipio.nome), capital = COALESCE(excluded.capital, municipio.capital),
           eleitores = COALESCE(excluded.eleitores, municipio.eleitores),
           origem = CASE WHEN municipio.origem = 'cm' THEN 'cm' ELSE excluded.origem END`,
        ),
      ),
      zona: q(insertSql("zona", COLS.zona, "ON CONFLICT DO NOTHING")),
      eleicao: q(upsertSql("eleicao", COLS.eleicao, ["cd"])),
      cargo: q(upsertSql("cargo", COLS.cargo, ["eleicao_cd", "cd"])),
      uf: q(upsertSql("uf", COLS.uf, ["sigla"])),
      meta: q("INSERT INTO meta (chave, valor) VALUES ($chave, $valor) ON CONFLICT (chave) DO UPDATE SET valor = excluded.valor"),
    };
  }

  private s(nome: string): Stmt {
    const st = this.st[nome];
    if (!st) throw new Error(`statement ausente: ${nome}`);
    return st;
  }

  /** Grava todos os itens numa transação; refs resolvem ids criados antes no mesmo lote. */
  gravarLote(itens: readonly ItemLote[]): ResultadoLote {
    const ids = new Map<string, number>();
    const id = (r: IdRef | null | undefined): number | null => {
      if (r === null || r === undefined) return null;
      if (typeof r === "number") return r;
      const v = ids.get(r.ref);
      if (v === undefined) throw new Error(`ref não resolvida no lote: ${r.ref}`);
      return v;
    };
    const exigir = (r: IdRef): number => id(r) as number;
    const guardar = (ref: string | undefined, v: number): void => {
      if (ref !== undefined) ids.set(ref, v);
    };
    const linhas = (nome: string, snap: number, rows: readonly object[]): void => {
      const st = this.s(nome);
      for (const r of rows) st.run({ ...(r as Params), snapshot_id: snap });
    };

    this.db.transaction(() => {
      for (const it of itens) {
        switch (it.k) {
          case "arquivo": {
            const r = it.row;
            this.s("arquivo").run({
              chave: r.chave, url: r.url, tipo: r.tipo, eleicao_cd: r.ele, cargo_cd: r.cargo, nivel: r.nivel, uf: r.uf,
              municipio_cd: r.mun, zona_cd: r.zona, tier: r.tier, sonda: r.sonda ? 1 : 0,
            });
            const row = this.s("arquivoId").get({ chave: r.chave }) as { id: number } | null;
            if (row) guardar(it.ref, row.id);
            break;
          }
          case "arquivo_estado":
            this.s("arquivoEstado").run({ ...it.row, ultimo_snapshot_id: id(it.row.ultimo_snapshot_id), id: exigir(it.id) });
            break;
          case "fetch": {
            const row = this.s("fetch").get({ ...it.row, arquivo_id: exigir(it.row.arquivo_id) }) as { id: number };
            guardar(it.ref, row.id);
            break;
          }
          case "blob":
            this.s("blob").run({ sha256: it.sha256, bytes: it.bytes, gz: it.gz, criado_em: it.criado_em });
            break;
          case "snapshot": {
            const fetchId = id(it.row.fetch_id);
            const row = this.s("snapshot").get({
              ...it.row, arquivo_id: exigir(it.row.arquivo_id), fetch_id: fetchId, anterior_id: id(it.row.anterior_id),
            }) as { id: number };
            if (fetchId !== null) this.s("fetchSnapshot").run({ snapshot_id: row.id, id: fetchId });
            guardar(it.ref, row.id);
            break;
          }
          case "totais":
            this.s("totais").run({ ...it.row, snapshot_id: exigir(it.snapshot) });
            break;
          case "voto_candidato":
          case "voto_partido":
          case "voto_agremiacao":
          case "ab_estado":
          case "e_entrada":
            linhas(it.k, exigir(it.snapshot), it.rows);
            break;
          case "candidato": {
            const snap = id(it.snapshot);
            const st = this.s("candidato");
            for (const r of it.rows) st.run({ ...r, primeiro_snapshot_id: snap });
            break;
          }
          case "evento": {
            const e = it.row;
            const row = this.s("evento").get({
              em: e.em, tipo: e.tipo, severidade: e.severidade ?? "info", arquivo_id: id(e.arquivo_id),
              snapshot_id: id(e.snapshot_id), eleicao_cd: e.eleicao_cd ?? null, cargo_cd: e.cargo_cd ?? null,
              nivel: e.nivel ?? null, uf: e.uf ?? null, municipio_cd: e.municipio_cd ?? null, zona_cd: e.zona_cd ?? null,
              detalhe: e.detalhe === undefined || e.detalhe === null ? null : JSON.stringify(e.detalhe),
            }) as { id: number };
            guardar(it.ref, row.id);
            break;
          }
          case "partido":
          case "federacao":
          case "municipio":
          case "zona":
          case "eleicao":
          case "cargo":
          case "uf": {
            const st = this.s(it.k);
            for (const r of it.rows) st.run(r as unknown as Params);
            break;
          }
          case "meta":
            this.s("meta").run({ chave: it.chave, valor: it.valor });
            break;
        }
      }
    })();
    return { ids, itens: itens.length };
  }
}
