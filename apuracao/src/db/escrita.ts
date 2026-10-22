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

/** Pausa do 2º turno: abre com `ate` nulo e fecha pela mesma chave (nivel, uf, de). */
export interface LinhaPausa {
  nivel: "nacional" | "uf" | "geral";
  uf: S;
  de: string;
  ate: S;
  minutos: N;
  st_antes: N;
  st_depois: N;
  detectado_em: string;
}

/** Seção da amostra ao vivo do 2º turno (linha inteira, regravada a cada mudança). */
export interface LinhaSecao2t {
  uf: string;
  mun: string;
  zona: number;
  secao: number;
  origem: "amostra" | "paralela";
  status_aux: S;
  hash: S;
  bu_nome: S;
  dr_hr: S;
  encerramento_local: S;
  encerramento_iso: S;
  emissao_iso: S;
  recebido_iso: S;
  bu_sha256: S;
  aptos: N;
  comparecimento: N;
  votos_json: S;
  totalizado_mun_iso: S;
  lag_encerr_recebimento_min: N;
  lag_encerr_emissao_min: N;
  lag_recebimento_totalizacao_min: N;
  erro: S;
  tentativas: number;
  atualizado_em: string;
}

/** BU aceito pela totalização paralela (cópia local, imutável como na origem). */
export interface LinhaParalelaBu {
  id: number;
  recebido_em: string;
  uf: string;
  mun: string;
  zona: number;
  secao: number;
  fase: S;
  pleito: N;
  turno: N;
  orig: S;
  aptos: N;
  comparecimento: N;
  hash_final: string;
  cargos_json: string;
  lido_em: string;
}

export interface LinhaParalelaConferencia {
  bu_id: number;
  uf: string;
  mun: string;
  zona: number;
  secao: number;
  hash_final: S;
  situacao: "igual" | "divergente" | "tse_ainda_nao_publicou" | "erro" | "fora_do_oficial";
  diferencas_json: S;
  erro: S;
  tse_hash: S;
  tse_arquivo: S;
  tse_sha256: S;
  tse_recebido_iso: S;
  primeira_em: string;
  conferido_em: string;
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
  | { k: "meta"; chave: string; valor: string }
  | { k: "pausa"; row: LinhaPausa }
  | { k: "secao_2t"; row: LinhaSecao2t }
  | { k: "paralela_bu"; rows: readonly LinhaParalelaBu[] }
  | { k: "paralela_conferencia"; row: LinhaParalelaConferencia };

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
  pausa: ["nivel", "uf", "de", "ate", "minutos", "st_antes", "st_depois", "detectado_em"],
  secao_2t: [
    "uf", "mun", "zona", "secao", "origem", "status_aux", "hash", "bu_nome", "dr_hr", "encerramento_local", "encerramento_iso",
    "emissao_iso", "recebido_iso", "bu_sha256", "aptos", "comparecimento", "votos_json", "totalizado_mun_iso",
    "lag_encerr_recebimento_min", "lag_encerr_emissao_min", "lag_recebimento_totalizacao_min", "erro", "tentativas", "atualizado_em",
  ],
  paralela_bu: [
    "id", "recebido_em", "uf", "mun", "zona", "secao", "fase", "pleito", "turno", "orig", "aptos", "comparecimento", "hash_final",
    "cargos_json", "lido_em",
  ],
  paralela_conferencia: [
    "bu_id", "uf", "mun", "zona", "secao", "hash_final", "situacao", "diferencas_json", "erro", "tse_hash", "tse_arquivo",
    "tse_sha256", "tse_recebido_iso", "primeira_em", "conferido_em",
  ],
} as const;

/** Sobrescreve todas as colunas fora da chave primária (linha inteira). */
function upsertTudoSql(tabela: string, cols: readonly string[], pk: readonly string[], manter: Readonly<Record<string, string>> = {}): string {
  const sets = cols.filter((c) => !pk.includes(c)).map((c) => `${c} = ${manter[c] ?? `excluded.${c}`}`);
  return insertSql(tabela, cols, `ON CONFLICT (${pk.join(", ")}) DO UPDATE SET ${sets.join(", ")}`);
}

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
      pausaFechar: q(
        `UPDATE pausa SET ate = $ate, minutos = $minutos, st_depois = $st_depois
         WHERE nivel = $nivel AND IFNULL(uf, '') = IFNULL($uf, '') AND de = $de`,
      ),
      pausa: q(insertSql("pausa", COLS.pausa, "ON CONFLICT DO NOTHING")),
      secao_2t: q(
        upsertTudoSql("secao_2t", COLS.secao_2t, ["uf", "mun", "zona", "secao"], {
          origem: "CASE WHEN secao_2t.origem = 'amostra' THEN 'amostra' ELSE excluded.origem END",
        }),
      ),
      paralela_bu: q(insertSql("paralela_bu", COLS.paralela_bu, "ON CONFLICT (id) DO NOTHING")),
      paralela_conferencia: q(
        upsertTudoSql("paralela_conferencia", COLS.paralela_conferencia, ["bu_id"], { primeira_em: "paralela_conferencia.primeira_em" }),
      ),
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
          case "pausa": {
            const r = it.row;
            const fechou = this.s("pausaFechar").run({ ate: r.ate, minutos: r.minutos, st_depois: r.st_depois, nivel: r.nivel, uf: r.uf, de: r.de });
            if (fechou.changes === 0) this.s("pausa").run({ ...r });
            break;
          }
          case "secao_2t":
            this.s("secao_2t").run({ ...it.row });
            break;
          case "paralela_bu": {
            const st = this.s("paralela_bu");
            for (const r of it.rows) st.run({ ...r });
            break;
          }
          case "paralela_conferencia":
            this.s("paralela_conferencia").run({ ...it.row });
            break;
        }
      }
    })();
    return { ids, itens: itens.length };
  }
}
