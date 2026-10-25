-- Esquema do banco de auditoria da apuração. Idempotente: tabelas e índices com
-- IF NOT EXISTS; views recriadas a cada abertura do escritor.
-- Tempos em TEXT ISO-8601 UTC com milissegundos. Códigos TSE com zeros em TEXT.

CREATE TABLE IF NOT EXISTS meta (
  chave TEXT PRIMARY KEY,
  valor TEXT
);

-- ---------------------------------------------------------------- configuração
CREATE TABLE IF NOT EXISTS eleicao (
  cd INTEGER PRIMARY KEY,
  cdt2 INTEGER,
  nome TEXT,
  turno INTEGER,
  tipo TEXT,
  pleito INTEGER,
  ciclo TEXT,
  data TEXT
);

CREATE TABLE IF NOT EXISTS cargo (
  eleicao_cd INTEGER NOT NULL,
  cd INTEGER NOT NULL,
  nome TEXT,
  tp TEXT,
  proporcional INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (eleicao_cd, cd)
);

CREATE TABLE IF NOT EXISTS uf (
  sigla TEXT PRIMARY KEY,
  nome TEXT
);

CREATE TABLE IF NOT EXISTS municipio (
  cd TEXT PRIMARY KEY,
  uf TEXT NOT NULL,
  ibge TEXT,
  nome TEXT,
  capital INTEGER,
  eleitores INTEGER,
  origem TEXT NOT NULL DEFAULT 'cm' CHECK (origem IN ('cm', 'ab'))
);
CREATE INDEX IF NOT EXISTS municipio_uf ON municipio (uf);
CREATE INDEX IF NOT EXISTS municipio_ibge ON municipio (ibge);

CREATE TABLE IF NOT EXISTS zona (
  municipio_cd TEXT NOT NULL,
  cd TEXT NOT NULL,
  uf TEXT NOT NULL,
  PRIMARY KEY (municipio_cd, cd)
) WITHOUT ROWID;

CREATE TABLE IF NOT EXISTS partido (
  n INTEGER PRIMARY KEY,
  sigla TEXT,
  nome TEXT,
  federacao_n INTEGER
);

CREATE TABLE IF NOT EXISTS federacao (
  n INTEGER PRIMARY KEY,
  sigla TEXT,
  nome TEXT,
  composicao TEXT,
  partidos TEXT
);

CREATE TABLE IF NOT EXISTS candidato (
  sqcand INTEGER PRIMARY KEY,
  eleicao_cd INTEGER NOT NULL,
  cargo_cd INTEGER NOT NULL,
  uf TEXT,
  numero INTEGER,
  nome TEXT,
  nome_urna TEXT,
  nascimento TEXT,
  partido_n INTEGER,
  federacao_n INTEGER,
  agremiacao_n INTEGER,
  vices TEXT,
  primeiro_snapshot_id INTEGER
);
CREATE INDEX IF NOT EXISTS candidato_cargo ON candidato (eleicao_cd, cargo_cd, uf);

-- ---------------------------------------------------------------- registro
CREATE TABLE IF NOT EXISTS arquivo (
  id INTEGER PRIMARY KEY,
  chave TEXT NOT NULL UNIQUE,
  url TEXT NOT NULL UNIQUE,
  tipo TEXT NOT NULL CHECK (tipo IN ('ele-c', 'cm', 'ab', 'u', 'e')),
  eleicao_cd INTEGER,
  cargo_cd INTEGER,
  nivel TEXT CHECK (nivel IS NULL OR nivel IN ('br', 'uf', 'mu', 'zona')),
  uf TEXT,
  municipio_cd TEXT,
  zona_cd TEXT,
  tier INTEGER NOT NULL,
  sonda INTEGER NOT NULL DEFAULT 0,
  ativo INTEGER NOT NULL DEFAULT 1,
  etag TEXT,
  last_modified TEXT,
  sha256 TEXT,
  idg INTEGER,
  gerado_em TEXT,
  ultimo_snapshot_id INTEGER,
  ultimo_fetch_em TEXT,
  ultimo_status TEXT,
  n_fetch INTEGER NOT NULL DEFAULT 0,
  n_mudancas INTEGER NOT NULL DEFAULT 0,
  erros_seguidos INTEGER NOT NULL DEFAULT 0,
  backoff_ate TEXT,
  final_agendado INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS arquivo_escopo ON arquivo (eleicao_cd, cargo_cd, nivel, uf, municipio_cd);
CREATE INDEX IF NOT EXISTS arquivo_tier ON arquivo (tier);

-- ---------------------------------------------------------------- log de requisições
CREATE TABLE IF NOT EXISTS fetch (
  id INTEGER PRIMARY KEY,
  arquivo_id INTEGER NOT NULL REFERENCES arquivo (id),
  iniciado_em TEXT NOT NULL,
  duracao_ms INTEGER,
  motivo TEXT NOT NULL,
  condicional INTEGER NOT NULL DEFAULT 0,
  http_status INTEGER,
  classe TEXT NOT NULL,
  etag TEXT,
  last_modified TEXT,
  servidor_date TEXT,
  cache_hdr TEXT,
  age INTEGER,
  bytes INTEGER,
  body_sha256 TEXT,
  mudou INTEGER NOT NULL DEFAULT 0,
  snapshot_id INTEGER,
  erro TEXT
);
CREATE INDEX IF NOT EXISTS fetch_arquivo ON fetch (arquivo_id, id);
CREATE INDEX IF NOT EXISTS fetch_tempo ON fetch (iniciado_em);
CREATE INDEX IF NOT EXISTS fetch_classe ON fetch (classe, iniciado_em);

-- ---------------------------------------------------------------- corpos (gzip, dedupe por sha)
CREATE TABLE IF NOT EXISTS blob (
  sha256 TEXT PRIMARY KEY,
  bytes INTEGER NOT NULL,
  gz BLOB NOT NULL,
  criado_em TEXT NOT NULL
) WITHOUT ROWID;

-- ---------------------------------------------------------------- versões
CREATE TABLE IF NOT EXISTS snapshot (
  id INTEGER PRIMARY KEY,
  arquivo_id INTEGER NOT NULL REFERENCES arquivo (id),
  fetch_id INTEGER REFERENCES fetch (id),
  sha256 TEXT NOT NULL REFERENCES blob (sha256),
  capturado_em TEXT NOT NULL,
  dg TEXT,
  hg TEXT,
  idg INTEGER,
  gerado_em TEXT,
  dt TEXT,
  ht TEXT,
  totalizado_em TEXT,
  tf INTEGER,
  andamento TEXT,
  divulgacao TEXT,
  turno INTEGER,
  regressivo INTEGER NOT NULL DEFAULT 0,
  anterior_id INTEGER
);
CREATE INDEX IF NOT EXISTS snapshot_arquivo ON snapshot (arquivo_id, regressivo, id);
CREATE INDEX IF NOT EXISTS snapshot_capturado ON snapshot (capturado_em);

-- ---------------------------------------------------------------- séries normalizadas
CREATE TABLE IF NOT EXISTS totais (
  snapshot_id INTEGER PRIMARY KEY REFERENCES snapshot (id),
  vagas INTEGER,
  ts INTEGER, st INTEGER, snt INTEGER, si INTEGER, sni INTEGER, sa INTEGER, sna INTEGER, pst REAL,
  te INTEGER, est INTEGER, esnt INTEGER, esi INTEGER, esni INTEGER, esa INTEGER, esna INTEGER,
  comparecimento INTEGER, abstencao INTEGER, pc REAL, pa REAL,
  tv INTEGER, vvc INTEGER, vv INTEGER, vnom INTEGER, vl INTEGER, van INTEGER, vansj INTEGER,
  vb INTEGER, tvn INTEGER, vn INTEGER, vnt INTEGER, vsan INTEGER, vscv INTEGER,
  pvvc REAL, pvb REAL, ptvn REAL, pvan REAL, pvn REAL
);

CREATE TABLE IF NOT EXISTS voto_candidato (
  snapshot_id INTEGER NOT NULL,
  sqcand INTEGER NOT NULL,
  vap INTEGER,
  pvapn REAL,
  eleito INTEGER,
  st TEXT,
  dvt TEXT,
  PRIMARY KEY (snapshot_id, sqcand)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS voto_candidato_sq ON voto_candidato (sqcand, snapshot_id);

CREATE TABLE IF NOT EXISTS voto_partido (
  snapshot_id INTEGER NOT NULL,
  agremiacao_n INTEGER NOT NULL,
  partido_n INTEGER NOT NULL,
  tvtn INTEGER,
  tvtl INTEGER,
  tval INTEGER,
  tvan INTEGER,
  dvt TEXT,
  PRIMARY KEY (snapshot_id, agremiacao_n, partido_n)
) WITHOUT ROWID;

CREATE TABLE IF NOT EXISTS voto_agremiacao (
  snapshot_id INTEGER NOT NULL,
  agremiacao_n INTEGER NOT NULL,
  tp TEXT,
  nome TEXT,
  composicao TEXT,
  tvtn INTEGER,
  tvtl INTEGER,
  tval INTEGER,
  tvan INTEGER,
  vagas INTEGER,
  PRIMARY KEY (snapshot_id, agremiacao_n)
) WITHOUT ROWID;

-- ---------------------------------------------------------------- andamento (-ab), só entradas que mudaram
CREATE TABLE IF NOT EXISTS ab_estado (
  snapshot_id INTEGER NOT NULL,
  tpabr TEXT NOT NULL,
  cdabr TEXT NOT NULL,
  andamento TEXT,
  dt TEXT,
  ht TEXT,
  totalizado_em TEXT,
  ts INTEGER, st INTEGER, pst REAL, snt INTEGER, si INTEGER, sni INTEGER, sa INTEGER, sna INTEGER,
  te INTEGER, est INTEGER, esnt INTEGER, esi INTEGER, esni INTEGER, esa INTEGER, esna INTEGER,
  comparecimento INTEGER, abstencao INTEGER,
  munnr INTEGER, munpt INTEGER, munf INTEGER,
  ufsnr INTEGER, ufspt INTEGER, ufsf INTEGER,
  PRIMARY KEY (snapshot_id, cdabr)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS ab_estado_cdabr ON ab_estado (cdabr, snapshot_id);

-- ---------------------------------------------------------------- agregado por UF (-e), se aparecer
CREATE TABLE IF NOT EXISTS e_entrada (
  snapshot_id INTEGER NOT NULL,
  cdabr TEXT NOT NULL,
  tpabr TEXT,
  nome TEXT,
  dt TEXT,
  ht TEXT,
  totalizado_em TEXT,
  tvap INTEGER,
  cand TEXT,
  PRIMARY KEY (snapshot_id, cdabr)
) WITHOUT ROWID;

-- ---------------------------------------------------------------- eventos
CREATE TABLE IF NOT EXISTS evento (
  id INTEGER PRIMARY KEY,
  em TEXT NOT NULL,
  tipo TEXT NOT NULL,
  severidade TEXT NOT NULL DEFAULT 'info' CHECK (severidade IN ('info', 'warn', 'error')),
  arquivo_id INTEGER,
  snapshot_id INTEGER,
  eleicao_cd INTEGER,
  cargo_cd INTEGER,
  nivel TEXT,
  uf TEXT,
  municipio_cd TEXT,
  zona_cd TEXT,
  detalhe TEXT
);
CREATE INDEX IF NOT EXISTS evento_tempo ON evento (em);
CREATE INDEX IF NOT EXISTS evento_tipo ON evento (tipo, em);

-- ---------------------------------------------------------------- 2º turno: pausas detectadas
-- Intervalo sem versão nova (gerado_em) de um arquivo -u de presidente com st < ts enquanto
-- outro nível avança ('geral': nenhum arquivo publica). `de` = geração da última versão antes
-- da pausa; `ate` nulo = em curso.
CREATE TABLE IF NOT EXISTS pausa (
  id INTEGER PRIMARY KEY,
  nivel TEXT NOT NULL CHECK (nivel IN ('nacional', 'uf', 'geral')),
  uf TEXT,
  de TEXT NOT NULL,
  ate TEXT,
  minutos REAL,
  st_antes INTEGER,
  st_depois INTEGER,
  detectado_em TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS pausa_unica ON pausa (nivel, IFNULL(uf, ''), de);

-- ---------------------------------------------------------------- 2º turno: amostra de seções
-- aux.json -> hash -> BU do arquivo-urna. Horas *_iso em UTC; encerramento_local como na urna;
-- dr_hr como publicado (Brasília). votos_json no esqueleto da conferência (eleição, cargo).
CREATE TABLE IF NOT EXISTS secao_2t (
  uf TEXT NOT NULL,
  mun TEXT NOT NULL,
  zona INTEGER NOT NULL,
  secao INTEGER NOT NULL,
  origem TEXT NOT NULL CHECK (origem IN ('amostra', 'paralela')),
  status_aux TEXT,
  hash TEXT,
  bu_nome TEXT,
  dr_hr TEXT,
  encerramento_local TEXT,
  encerramento_iso TEXT,
  emissao_iso TEXT,
  recebido_iso TEXT,
  bu_sha256 TEXT,
  aptos INTEGER,
  comparecimento INTEGER,
  votos_json TEXT,
  totalizado_mun_iso TEXT,
  lag_encerr_recebimento_min REAL,
  lag_encerr_emissao_min REAL,
  lag_recebimento_totalizacao_min REAL,
  erro TEXT,
  tentativas INTEGER NOT NULL DEFAULT 0,
  atualizado_em TEXT NOT NULL,
  -- detalhamento do comparecimento e tipo da urna (acrescentados em 25/10; ver COLUNAS_ACRESCIDAS em abrir.ts)
  hab_biometria INTEGER,
  hab_ano_nascimento INTEGER,
  comp_sem_biometria INTEGER,
  tipo_arquivo INTEGER,
  tipo_urna INTEGER,
  n_cargas INTEGER,
  abertura_iso TEXT,
  PRIMARY KEY (uf, mun, zona, secao)
);
CREATE INDEX IF NOT EXISTS secao_2t_recebido ON secao_2t (recebido_iso);

-- ---------------------------------------------------------------- 2º turno: totalização paralela
-- Cópia local dos BUs aceitos (views públicas do Supabase, imutáveis) e a conferência de cada
-- um contra o BU oficial da mesma seção.
CREATE TABLE IF NOT EXISTS paralela_bu (
  id INTEGER PRIMARY KEY,
  recebido_em TEXT NOT NULL,
  uf TEXT NOT NULL,
  mun TEXT NOT NULL,
  zona INTEGER NOT NULL,
  secao INTEGER NOT NULL,
  fase TEXT,
  pleito INTEGER,
  turno INTEGER,
  orig TEXT,
  aptos INTEGER,
  comparecimento INTEGER,
  hash_final TEXT NOT NULL,
  cargos_json TEXT NOT NULL,
  lido_em TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS paralela_bu_secao ON paralela_bu (uf, mun, zona, secao);
CREATE INDEX IF NOT EXISTS paralela_bu_recebido ON paralela_bu (recebido_em);

CREATE TABLE IF NOT EXISTS paralela_conferencia (
  bu_id INTEGER PRIMARY KEY,
  uf TEXT NOT NULL,
  mun TEXT NOT NULL,
  zona INTEGER NOT NULL,
  secao INTEGER NOT NULL,
  hash_final TEXT,
  situacao TEXT NOT NULL CHECK (situacao IN ('igual', 'divergente', 'tse_ainda_nao_publicou', 'erro', 'fora_do_oficial')),
  diferencas_json TEXT,
  erro TEXT,
  tse_hash TEXT,
  tse_arquivo TEXT,
  tse_sha256 TEXT,
  tse_recebido_iso TEXT,
  primeira_em TEXT NOT NULL,
  conferido_em TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS paralela_conferencia_situacao ON paralela_conferencia (situacao, conferido_em);

-- ---------------------------------------------------------------- views
DROP VIEW IF EXISTS v_atual;
CREATE VIEW v_atual AS
SELECT
  a.id AS arquivo_id, a.chave, a.tipo, a.eleicao_cd, a.cargo_cd, a.nivel, a.uf, a.municipio_cd, a.zona_cd,
  s.id AS snapshot_id, s.capturado_em, s.gerado_em, s.totalizado_em, s.idg, s.tf, s.andamento, s.dg, s.hg, s.dt, s.ht,
  t.vagas, t.ts, t.st, t.pst, t.te, t.est, t.comparecimento, t.abstencao, t.pc, t.pa,
  t.tv, t.vvc, t.vv, t.vnom, t.vl, t.van, t.vansj, t.vb, t.tvn, t.vn, t.vnt, t.pvvc, t.pvb, t.ptvn, t.pvan, t.pvn
FROM arquivo a
JOIN snapshot s ON s.id = (
  SELECT s2.id FROM snapshot s2 WHERE s2.arquivo_id = a.id AND s2.regressivo = 0 ORDER BY s2.id DESC LIMIT 1
)
LEFT JOIN totais t ON t.snapshot_id = s.id;

DROP VIEW IF EXISTS v_snapshot_delta;
CREATE VIEW v_snapshot_delta AS
SELECT
  s.id AS snapshot_id, s.arquivo_id, a.chave, a.eleicao_cd, a.cargo_cd, a.nivel, a.uf, a.municipio_cd, a.zona_cd,
  s.capturado_em, s.gerado_em, s.totalizado_em, s.idg, s.regressivo,
  (julianday(s.capturado_em) - julianday(s.gerado_em)) * 86400.0 AS latencia_captura_s,
  (julianday(s.gerado_em) - julianday(s.totalizado_em)) * 86400.0 AS latencia_geracao_s,
  (julianday(s.gerado_em) - julianday(LAG(s.gerado_em) OVER w)) * 86400.0 AS intervalo_geracao_s,
  t.st, t.pst, t.vvc, t.tv, t.comparecimento,
  t.st - LAG(t.st) OVER w AS d_st,
  t.vvc - LAG(t.vvc) OVER w AS d_vvc,
  t.tv - LAG(t.tv) OVER w AS d_tv,
  t.pst - LAG(t.pst) OVER w AS d_pst,
  t.comparecimento - LAG(t.comparecimento) OVER w AS d_comparecimento
FROM snapshot s
JOIN arquivo a ON a.id = s.arquivo_id
LEFT JOIN totais t ON t.snapshot_id = s.id
WINDOW w AS (PARTITION BY s.arquivo_id ORDER BY s.id);

DROP VIEW IF EXISTS v_voto_candidato_delta;
CREATE VIEW v_voto_candidato_delta AS
SELECT
  vc.snapshot_id, s.arquivo_id, vc.sqcand, vc.vap, vc.pvapn, vc.eleito, vc.st, s.capturado_em, s.gerado_em,
  vc.vap - LAG(vc.vap) OVER w AS d_vap,
  (julianday(s.gerado_em) - julianday(LAG(s.gerado_em) OVER w)) * 86400.0 AS dt_s
FROM voto_candidato vc
JOIN snapshot s ON s.id = vc.snapshot_id
WHERE s.regressivo = 0
WINDOW w AS (PARTITION BY s.arquivo_id, vc.sqcand ORDER BY vc.snapshot_id);

DROP VIEW IF EXISTS v_municipio_fim;
CREATE VIEW v_municipio_fim AS
SELECT
  a.id AS arquivo_id, a.eleicao_cd, a.cargo_cd, a.uf, a.municipio_cd,
  MIN(s.id) AS snapshot_id, MIN(s.capturado_em) AS capturado_em, MIN(s.gerado_em) AS gerado_em,
  MIN(s.totalizado_em) AS totalizado_em
FROM arquivo a
JOIN snapshot s ON s.arquivo_id = a.id AND s.regressivo = 0
JOIN totais t ON t.snapshot_id = s.id
WHERE a.tipo = 'u' AND a.nivel = 'mu' AND t.ts > 0 AND t.st = t.ts
GROUP BY a.id;

DROP VIEW IF EXISTS v_ab_atual;
CREATE VIEW v_ab_atual AS
SELECT * FROM (
  SELECT
    a.id AS arquivo_id, a.eleicao_cd, a.nivel, a.uf AS uf_arquivo, s.capturado_em, s.gerado_em, e.*,
    ROW_NUMBER() OVER (PARTITION BY a.id, e.cdabr ORDER BY e.snapshot_id DESC) AS rn
  FROM ab_estado e
  JOIN snapshot s ON s.id = e.snapshot_id AND s.regressivo = 0
  JOIN arquivo a ON a.id = s.arquivo_id
) WHERE rn = 1;
