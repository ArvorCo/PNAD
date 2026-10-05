// Banco das seções (data/secoes_2026.sqlite): boletim de urna bruto (gzip), BU decodificado,
// voto por seção e a conferência por zona contra os arquivos de zona do coletor.
// Escritor único. Chaves: uf minúscula ('sp', 'zz' no exterior), mun com 5 dígitos como no TSE
// e em apuracao.sqlite (municipio_cd), zona e secao inteiras.
import { Database } from "bun:sqlite";
import { mkdirSync } from "node:fs";
import { dirname } from "node:path";
import { dataHoraJe } from "../bu-decode.ts";
import type { BoletimUrna } from "../bu-decode.ts";
import type { FonteModelo, ResumoLog } from "./log-urna.ts";

export const ESQUEMA = `
CREATE TABLE IF NOT EXISTS meta (chave TEXT PRIMARY KEY, valor TEXT);

-- Configuração de seções por UF (arquivo -cs.json), uma linha por download.
CREATE TABLE IF NOT EXISTS cs (
  uf TEXT PRIMARY KEY,
  dg TEXT, hg TEXT, idg TEXT,
  secoes INTEGER,
  bytes INTEGER,
  sha256 TEXT,
  baixado_em TEXT
);

-- Uma linha por seção do -cs.json. status_aux = campo st do aux (ex.: 'Recebida'), ou
-- 'aux_404' / 'aux_erro' quando o aux não veio. Sem BU, bu_gz fica nulo.
CREATE TABLE IF NOT EXISTS secao (
  uf TEXT NOT NULL,
  mun TEXT NOT NULL,
  zona INTEGER NOT NULL,
  secao INTEGER NOT NULL,
  nsp INTEGER,            -- seção principal, quando esta é agregada
  nsa TEXT,               -- seções agregadas a esta (JSON)
  status_aux TEXT,
  aux_dg_hg TEXT,         -- geração do aux no TSE (dd/mm/aaaa hh:mm:ss)
  aux_json TEXT,          -- aux.json original
  n_hashes INTEGER,
  hash TEXT,              -- hash escolhido (o último que lista arquivo tp 'bu')
  hash_st TEXT,
  dr_hr TEXT,             -- recebimento do hash (aaaa-mm-dd hh:mm:ss, como publicado)
  bu_nome TEXT,
  bu_bytes INTEGER,
  bu_sha256 TEXT,
  bu_gz BLOB,
  log_nome TEXT,
  log_bytes INTEGER,
  log_sha256 TEXT,
  erro TEXT,
  requisicoes INTEGER NOT NULL DEFAULT 0,
  baixado_em TEXT,
  PRIMARY KEY (uf, mun, zona, secao)
);
CREATE INDEX IF NOT EXISTS secao_status ON secao (status_aux);

-- BU decodificado. Horas do BU são locais da urna (YYYY-MM-DD hh:mm:ss, sem fuso).
CREATE TABLE IF NOT EXISTS bu (
  uf TEXT NOT NULL,
  mun TEXT NOT NULL,
  zona INTEGER NOT NULL,
  secao INTEGER NOT NULL,
  local INTEGER,
  modelo_urna TEXT,               -- UE2009 ... UE2022, do log da urna
  modelo_fonte TEXT,              -- log_mesma_urna | log_modelo_unico | log_ambiguo | log_sem_modelo | sem_log | log_invalido
  numero_interno_urna INTEGER,    -- urna.correspondenciaResultado.carga.numeroInternoUrna (série da urna)
  tipo_urna INTEGER,              -- 1 secao, 3 contingencia, 4 reservaSecao, 6 reservaEncerrandoSecao
  tipo_arquivo INTEGER,           -- 1 votacaoUE, 2 votacaoRED, 3..6 sistema de apuração
  fase INTEGER,
  pleito INTEGER,
  versao_votacao TEXT,
  aptos INTEGER,                  -- eleição federal (6257): aptos da urna = aptos_secao + aptos_tte
  aptos_secao INTEGER,
  aptos_tte INTEGER,
  aptos_estadual INTEGER,         -- eleição estadual (6259), sem trânsito
  comparecimento INTEGER,         -- qtdEleitoresCompareceram
  comp_sem_biometria INTEGER,
  hab_biometria INTEGER,
  hab_ano_nascimento INTEGER,     -- qtdEleitoresHabilitadosPorBiografia
  abertura TEXT,                  -- primeiro voto
  encerramento TEXT,              -- último voto
  emissao TEXT,
  desligamento_voto_impresso TEXT,
  gerado_em TEXT,                 -- cabecalho.dataGeracao
  carga_em TEXT,
  codigo_carga TEXT,
  n_cargas INTEGER,               -- tamanho de historicoCodigosCarga
  numero_serie_fc TEXT,
  numero_serie_fv TEXT,
  gerador_midia TEXT,
  sa_junta INTEGER, sa_turma INTEGER, sa_urna_origem INTEGER,
  sa_alternativa TEXT, sa_tipo_apuracao INTEGER, sa_motivo INTEGER,
  id_confere INTEGER NOT NULL,    -- 1 se município, zona e seção do BU batem com o caminho
  log_urnas TEXT,                 -- JSON [{id, modelos, linhas}] de todas as urnas do log
  PRIMARY KEY (uf, mun, zona, secao)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS bu_modelo ON bu (modelo_urna);

-- Totais por cargo no BU: aptos da eleição do cargo e comparecimento do cargo.
CREATE TABLE IF NOT EXISTS bu_cargo (
  uf TEXT NOT NULL,
  mun TEXT NOT NULL,
  zona INTEGER NOT NULL,
  secao INTEGER NOT NULL,
  cargo INTEGER NOT NULL,         -- código constitucional (1 presidente, 3 governador, 5 senador, 6, 7, 8) ou livre (25..99)
  eleicao INTEGER NOT NULL,
  tipo_cargo INTEGER,             -- 1 majoritário, 2 proporcional, 3 consulta
  aptos INTEGER,
  comparecimento INTEGER,
  votos INTEGER,                  -- soma de quantidadeVotos (senador com duas vagas soma 2x)
  PRIMARY KEY (uf, mun, zona, secao, cargo)
) WITHOUT ROWID;

-- Voto por seção. tipo: 1 nominal, 2 branco, 3 nulo, 4 legenda, 5 cargo sem candidato.
-- numero: número do votável (legenda: número do partido); 0 em branco e nulo.
CREATE TABLE IF NOT EXISTS voto_secao (
  uf TEXT NOT NULL,
  mun TEXT NOT NULL,
  zona INTEGER NOT NULL,
  secao INTEGER NOT NULL,
  cargo INTEGER NOT NULL,
  tipo INTEGER NOT NULL,
  numero INTEGER NOT NULL,
  votos INTEGER NOT NULL,
  PRIMARY KEY (uf, mun, zona, secao, cargo, tipo, numero)
) WITHOUT ROWID;

-- Conferência: soma das seções contra o arquivo de zona do coletor (apuracao.sqlite).
CREATE TABLE IF NOT EXISTS conferencia_zona (
  uf TEXT NOT NULL,
  mun TEXT NOT NULL,
  zona INTEGER NOT NULL,
  cargo INTEGER NOT NULL,
  chave TEXT,                     -- arquivo de zona em apuracao.sqlite
  snapshot_id INTEGER,
  gerado_em TEXT,
  secoes_cs INTEGER,
  secoes_bu INTEGER,
  ts_zona INTEGER, st_zona INTEGER,
  aptos_bu INTEGER, aptos_zona INTEGER,
  comparecimento_bu INTEGER, comparecimento_zona INTEGER,
  brancos_bu INTEGER, brancos_zona INTEGER,
  nulos_bu INTEGER, nulos_zona INTEGER,
  fora_lista_bu INTEGER,          -- votos (nominais e de legenda) para números ausentes da lista da zona
  nulos_tecnicos_zona INTEGER,    -- vnt
  anulados_zona INTEGER,          -- van + vansj
  legenda_bu INTEGER, legenda_zona INTEGER,  -- partidos da lista; legenda_zona soma tval (apurados)
  nominais_bu INTEGER,
  candidatos INTEGER,
  candidatos_divergentes INTEGER,
  divergencias TEXT,              -- JSON [{campo, secoes, zona}]
  ok INTEGER,                     -- 1 confere, 0 diverge, NULL sem arquivo de zona
  conferido_em TEXT NOT NULL,
  PRIMARY KEY (uf, mun, zona, cargo)
);

-- Log bruto da urna (ZIP original), só com --guardar-log.
CREATE TABLE IF NOT EXISTS log_urna (
  uf TEXT NOT NULL,
  mun TEXT NOT NULL,
  zona INTEGER NOT NULL,
  secao INTEGER NOT NULL,
  zip BLOB NOT NULL,
  PRIMARY KEY (uf, mun, zona, secao)
) WITHOUT ROWID;

DROP VIEW IF EXISTS v_voto_secao;
CREATE VIEW v_voto_secao AS
SELECT v.*, CASE v.tipo WHEN 1 THEN 'nominal' WHEN 2 THEN 'branco' WHEN 3 THEN 'nulo' WHEN 4 THEN 'legenda'
  WHEN 5 THEN 'cargoSemCandidato' ELSE 'desconhecido' END AS tipo_nome,
  b.modelo_urna, c.aptos, c.comparecimento
FROM voto_secao v
JOIN bu b USING (uf, mun, zona, secao)
JOIN bu_cargo c USING (uf, mun, zona, secao, cargo);
`;

export function abrirSecoes(path: string): Database {
  if (path !== ":memory:") mkdirSync(dirname(path), { recursive: true });
  const db = new Database(path, { create: true, strict: true });
  for (const p of [
    "PRAGMA journal_mode = WAL",
    "PRAGMA synchronous = NORMAL",
    "PRAGMA busy_timeout = 5000",
    "PRAGMA cache_size = -131072",
    "PRAGMA temp_store = MEMORY",
    "PRAGMA wal_autocheckpoint = 4000",
  ]) {
    db.run(p);
  }
  db.run(ESQUEMA);
  return db;
}

export interface ChaveSecao {
  uf: string;
  mun: string;
  zona: number;
  secao: number;
}

export interface SecaoCs extends ChaveSecao {
  nsp: number | null;
  nsa: string | null;
}

export interface Modelo {
  modelo: string | null;
  fonte: FonteModelo | "sem_log" | "log_invalido";
}

/** Tudo o que a coleta de uma seção produziu. */
export interface ResultadoSecao extends ChaveSecao {
  statusAux: string;
  auxDgHg: string | null;
  auxJson: string | null;
  nHashes: number | null;
  hash: string | null;
  hashSt: string | null;
  drHr: string | null;
  buNome: string | null;
  buBytes: number | null;
  buSha256: string | null;
  buGz: Uint8Array<ArrayBuffer> | null;
  logNome: string | null;
  logBytes: number | null;
  logSha256: string | null;
  logZip: Uint8Array<ArrayBuffer> | null;
  erro: string | null;
  requisicoes: number;
  bu: BoletimUrna | null;
  modelo: Modelo | null;
  resumoLog: ResumoLog | null;
}

/** Linhas de voto_secao de um BU, somando eventuais repetições da mesma chave. */
export function linhasVoto(bu: BoletimUrna): Array<{ cargo: number; tipo: number; numero: number; votos: number }> {
  const m = new Map<string, { cargo: number; tipo: number; numero: number; votos: number }>();
  for (const e of bu.resultadosVotacaoPorEleicao) {
    for (const r of e.resultadosVotacao) {
      for (const t of r.totaisVotosCargo) {
        for (const v of t.votosVotaveis) {
          const numero = v.codigo ?? 0;
          const k = `${t.codigoCargo.valor}:${v.tipoVoto}:${numero}`;
          const x = m.get(k);
          if (x === undefined) m.set(k, { cargo: t.codigoCargo.valor, tipo: v.tipoVoto, numero, votos: v.quantidadeVotos });
          else x.votos += v.quantidadeVotos;
        }
      }
    }
  }
  return [...m.values()];
}

export interface LinhaCargo {
  cargo: number;
  eleicao: number;
  tipoCargo: number;
  aptos: number;
  comparecimento: number;
  votos: number;
}

/** Linhas de bu_cargo (um cargo repetido soma os votos e mantém a primeira ocorrência). */
export function linhasCargo(bu: BoletimUrna): LinhaCargo[] {
  const m = new Map<number, LinhaCargo>();
  for (const e of bu.resultadosVotacaoPorEleicao) {
    for (const r of e.resultadosVotacao) {
      for (const t of r.totaisVotosCargo) {
        const votos = t.votosVotaveis.reduce((s, v) => s + v.quantidadeVotos, 0);
        const x = m.get(t.codigoCargo.valor);
        if (x !== undefined) x.votos += votos;
        else {
          m.set(t.codigoCargo.valor, {
            cargo: t.codigoCargo.valor, eleicao: e.idEleicao, tipoCargo: r.tipoCargo, aptos: e.qtdEleitoresAptos,
            comparecimento: r.qtdComparecimento, votos,
          });
        }
      }
    }
  }
  return [...m.values()];
}

const FEDERAL = 6257;
const ESTADUAL = 6259;

export class EscritorSecoes {
  private readonly insSecao;
  private readonly delBu;
  private readonly delCargo;
  private readonly delVoto;
  private readonly delLog;
  private readonly insBu;
  private readonly insCargo;
  private readonly insVoto;
  private readonly insLog;

  constructor(private readonly db: Database) {
    this.insSecao = db.prepare(`INSERT INTO secao (uf, mun, zona, secao, nsp, nsa, status_aux, aux_dg_hg, aux_json, n_hashes, hash, hash_st, dr_hr,
        bu_nome, bu_bytes, bu_sha256, bu_gz, log_nome, log_bytes, log_sha256, erro, requisicoes, baixado_em)
      VALUES (?1, ?2, ?3, ?4, NULL, NULL, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12, ?13, ?14, ?15, ?16, ?17, ?18, ?19, ?20, ?21)
      ON CONFLICT (uf, mun, zona, secao) DO UPDATE SET status_aux = excluded.status_aux, aux_dg_hg = excluded.aux_dg_hg, aux_json = excluded.aux_json,
        n_hashes = excluded.n_hashes, hash = excluded.hash, hash_st = excluded.hash_st, dr_hr = excluded.dr_hr, bu_nome = excluded.bu_nome,
        bu_bytes = excluded.bu_bytes, bu_sha256 = excluded.bu_sha256, bu_gz = excluded.bu_gz, log_nome = excluded.log_nome,
        log_bytes = excluded.log_bytes, log_sha256 = excluded.log_sha256, erro = excluded.erro,
        requisicoes = secao.requisicoes + excluded.requisicoes, baixado_em = excluded.baixado_em`);
    const onde = "WHERE uf = ? AND mun = ? AND zona = ? AND secao = ?";
    this.delBu = db.prepare(`DELETE FROM bu ${onde}`);
    this.delCargo = db.prepare(`DELETE FROM bu_cargo ${onde}`);
    this.delVoto = db.prepare(`DELETE FROM voto_secao ${onde}`);
    this.delLog = db.prepare(`DELETE FROM log_urna ${onde}`);
    this.insBu = db.prepare(`INSERT INTO bu (uf, mun, zona, secao, local, modelo_urna, modelo_fonte, numero_interno_urna, tipo_urna, tipo_arquivo,
        fase, pleito, versao_votacao, aptos, aptos_secao, aptos_tte, aptos_estadual, comparecimento, comp_sem_biometria, hab_biometria,
        hab_ano_nascimento, abertura, encerramento, emissao, desligamento_voto_impresso, gerado_em, carga_em, codigo_carga, n_cargas,
        numero_serie_fc, numero_serie_fv, gerador_midia, sa_junta, sa_turma, sa_urna_origem, sa_alternativa, sa_tipo_apuracao, sa_motivo,
        id_confere, log_urnas)
      VALUES (${Array.from({ length: 40 }, (_, i) => `?${i + 1}`).join(", ")})`);
    this.insCargo = db.prepare(`INSERT INTO bu_cargo (uf, mun, zona, secao, cargo, eleicao, tipo_cargo, aptos, comparecimento, votos)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`);
    this.insVoto = db.prepare("INSERT INTO voto_secao (uf, mun, zona, secao, cargo, tipo, numero, votos) VALUES (?, ?, ?, ?, ?, ?, ?, ?)");
    this.insLog = db.prepare("INSERT INTO log_urna (uf, mun, zona, secao, zip) VALUES (?, ?, ?, ?, ?)");
  }

  /** Semeia as seções do -cs.json (não sobrescreve o que já foi baixado). */
  semear(secoes: readonly SecaoCs[]): number {
    const ins = this.db.prepare(`INSERT INTO secao (uf, mun, zona, secao, nsp, nsa) VALUES (?, ?, ?, ?, ?, ?)
      ON CONFLICT (uf, mun, zona, secao) DO UPDATE SET nsp = excluded.nsp, nsa = excluded.nsa`);
    let n = 0;
    this.db.transaction(() => {
      for (const s of secoes) n += ins.run(s.uf, s.mun, s.zona, s.secao, s.nsp, s.nsa).changes;
    })();
    return n;
  }

  /** Grava um lote de seções numa transação. */
  gravar(lote: readonly ResultadoSecao[], agoraIso: string): void {
    this.db.transaction(() => {
      for (const r of lote) this.gravarUm(r, agoraIso);
    })();
  }

  private gravarUm(r: ResultadoSecao, agoraIso: string): void {
    const k = [r.uf, r.mun, r.zona, r.secao] as const;
    this.insSecao.run(
      ...k, r.statusAux, r.auxDgHg, r.auxJson, r.nHashes, r.hash, r.hashSt, r.drHr, r.buNome, r.buBytes, r.buSha256, r.buGz,
      r.logNome, r.logBytes, r.logSha256, r.erro, r.requisicoes, agoraIso,
    );
    this.delBu.run(...k);
    this.delCargo.run(...k);
    this.delVoto.run(...k);
    this.delLog.run(...k);
    if (r.logZip !== null) this.insLog.run(...k, r.logZip);
    const bu = r.bu;
    if (bu === null) return;
    const u = bu.urna;
    const cg = u.correspondenciaResultado.carga;
    const fed = bu.resultadosVotacaoPorEleicao.find((e) => e.idEleicao === FEDERAL) ?? bu.resultadosVotacaoPorEleicao[0];
    const est = bu.resultadosVotacaoPorEleicao.find((e) => e.idEleicao === ESTADUAL);
    const id = bu.identificacaoSecao;
    const idConfere = id.municipioZona.municipio === Number(r.mun) && id.municipioZona.zona === r.zona && id.secao === r.secao ? 1 : 0;
    const det = bu.detalhamentoComparecimento;
    const g = cg.identificadorGeradorMidia;
    this.insBu.run(
      ...k, id.local, r.modelo?.modelo ?? null, r.modelo?.fonte ?? null, cg.numeroInternoUrna, u.tipoUrna, u.tipoArquivo,
      bu.fase, bu.cabecalho.idEleitoral.valor, u.versaoVotacao,
      fed?.qtdEleitoresAptos ?? null, fed?.qtdEleitoresAptosSecao ?? null, fed?.qtdEleitoresAptosTTE ?? null, est?.qtdEleitoresAptos ?? null,
      bu.qtdEleitoresCompareceram, det?.qtdEleitoresCompareceramSemBiometria ?? null, det?.qtdEleitoresHabilitadosPorBiometria ?? null,
      det?.qtdEleitoresHabilitadosPorBiografia ?? null,
      dataHoraJe(bu.dadosSecao?.dataHoraAbertura ?? null), dataHoraJe(bu.dadosSecao?.dataHoraEncerramento ?? null), dataHoraJe(bu.dataHoraEmissao),
      dataHoraJe(bu.dadosSecao?.dataHoraDesligamentoVotoImpresso ?? null), dataHoraJe(bu.cabecalho.dataGeracao), dataHoraJe(cg.dataHoraCarga),
      cg.codigoCarga, bu.historicoCodigosCarga.length, cg.numeroSerieFC, u.numeroSerieFV, `${g.nome}|${g.serialCertificadoTPM}|${g.serialInstalacao}`,
      bu.dadosSA?.juntaApuradora ?? null, bu.dadosSA?.turmaApuradora ?? null, bu.dadosSA?.numeroInternoUrnaOrigem ?? null,
      u.motivoUtilizacaoSA?.alternativa ?? null, u.motivoUtilizacaoSA?.tipoApuracao ?? null, u.motivoUtilizacaoSA?.motivoApuracao ?? null,
      idConfere, r.resumoLog === null ? null : JSON.stringify(r.resumoLog.urnas),
    );
    for (const c of linhasCargo(bu)) this.insCargo.run(...k, c.cargo, c.eleicao, c.tipoCargo, c.aptos, c.comparecimento, c.votos);
    for (const v of linhasVoto(bu)) this.insVoto.run(...k, v.cargo, v.tipo, v.numero, v.votos);
  }
}
