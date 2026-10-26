// Banco dos RDVs do 2º turno (data/rdv_2t_2026.sqlite), separado do banco dos BUs.
// Chaves como em secoes_2t_2026.sqlite: uf minúscula, mun com 5 dígitos, zona e secao inteiras.
import { Database } from "bun:sqlite";
import { mkdirSync } from "node:fs";
import { dirname } from "node:path";
import type { CargoRdv, Rdv } from "../../src/secoes2t/rdv-decode.ts";
import type { Aux } from "./secao.ts";
import { dataHoraTse } from "./secao.ts";

/** O RDV é só do 2º turno de 2026 aqui; URLs fixas para não depender de APURACAO_PLEITO. */
export const BASE_URNA_2T = "https://resultados.tse.jus.br/oficial/ele2026/arquivo-urna/3221";
const p4 = (n: number): string => String(n).padStart(4, "0");

export interface SecaoAlvo {
  uf: string;
  mun: string;
  zona: number;
  secao: number;
  /** seção principal, quando esta é agregada (o RDV fica na principal) */
  nsp: number | null;
}

export const dirSecao2t = (s: SecaoAlvo): string => `${BASE_URNA_2T}/dados/${s.uf}/${s.mun}/${p4(s.zona)}/${p4(s.secao)}`;
export const urlAux2t = (s: SecaoAlvo): string => `${dirSecao2t(s)}/p003221-${s.uf}-m${s.mun}-z${p4(s.zona)}-s${p4(s.secao)}-aux.json`;

export const ESQUEMA_RDV = `
CREATE TABLE IF NOT EXISTS meta (chave TEXT PRIMARY KEY, valor TEXT);

-- Uma linha por seção tentada. status: ok | sem_rdv (aux sem RDV) | agregada (seção agregada a
-- outra, sem arquivo próprio) | aux_404 | rdv_404 | erro.
CREATE TABLE IF NOT EXISTS rdv (
  uf TEXT NOT NULL,
  mun TEXT NOT NULL,
  zona INTEGER NOT NULL,
  secao INTEGER NOT NULL,
  status TEXT NOT NULL,
  aux_json TEXT,                -- só quando o aux foi pedido por esta coleta (senão está em secoes_2t_2026.sqlite)
  hash TEXT,
  mesmo_hash_bu INTEGER,        -- o hash do RDV também lista BU
  rdv_nome TEXT,
  bytes INTEGER,
  sha256 TEXT,
  rdv_gz BLOB,
  gerado_em TEXT,               -- cabecalho.dataGeracao (hora local da urna)
  fase INTEGER,
  pleito INTEGER,
  tipo_urna INTEGER,
  tipo_arquivo INTEGER,
  numero_interno_urna INTEGER,
  origem TEXT,                  -- vota | sa
  id_confere INTEGER,           -- município, zona e seção do RDV batem com o caminho
  confere INTEGER,              -- 1 contagens = BU; 0 diverge; NULL sem BU no banco dos BUs
  bu_nome TEXT,
  divergencias TEXT,            -- JSON, até 20
  conferido_em TEXT,
  erro TEXT,
  requisicoes INTEGER NOT NULL DEFAULT 0,
  baixado_em TEXT NOT NULL,
  PRIMARY KEY (uf, mun, zona, secao)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS rdv_status ON rdv (status);

-- Um cargo do RDV: lista própria por eleição e cargo, ordenada por tipo e digitação.
CREATE TABLE IF NOT EXISTS rdv_cargo (
  uf TEXT NOT NULL,
  mun TEXT NOT NULL,
  zona INTEGER NOT NULL,
  secao INTEGER NOT NULL,
  cargo INTEGER NOT NULL,       -- 1 presidente, 3 governador
  eleicao INTEGER NOT NULL,     -- 6258 federal, 6260 estadual
  escolhas INTEGER,
  votos INTEGER NOT NULL,       -- registros na lista
  ordenado INTEGER NOT NULL,    -- 1 se a lista segue (tipoVoto, digitação), como exige a especificação no VOTA e no RED
  PRIMARY KEY (uf, mun, zona, secao, cargo)
) WITHOUT ROWID;

-- Contagem por (tipo do RDV, digitação). tipo: 1 legenda, 2 nominal, 3 branco, 4 nulo,
-- 5 branco após suspensão, 6 nulo após suspensão, 7 nulo por repetição, 8 e 9 cargo sem candidato.
-- digitacao '' quando não há (branco). Nulo com digitação mostra o número que o eleitor teclou.
CREATE TABLE IF NOT EXISTS rdv_voto (
  uf TEXT NOT NULL,
  mun TEXT NOT NULL,
  zona INTEGER NOT NULL,
  secao INTEGER NOT NULL,
  cargo INTEGER NOT NULL,
  tipo INTEGER NOT NULL,
  digitacao TEXT NOT NULL,
  votos INTEGER NOT NULL,
  PRIMARY KEY (uf, mun, zona, secao, cargo, tipo, digitacao)
) WITHOUT ROWID;
`;

export function abrirRdv(path: string): Database {
  if (path !== ":memory:") mkdirSync(dirname(path), { recursive: true });
  const db = new Database(path, { create: true, strict: true });
  for (const p of ["PRAGMA journal_mode = WAL", "PRAGMA synchronous = NORMAL", "PRAGMA busy_timeout = 5000", "PRAGMA wal_autocheckpoint = 4000"]) db.run(p);
  db.run(ESQUEMA_RDV);
  return db;
}

export interface EscolhaRdv {
  hash: string;
  nome: string;
  /** o mesmo hash lista também um BU */
  temBu: boolean;
}

/** Hash com RDV mais recente pela data de recebimento (empate: o último da lista). `-rdv.dat` antes de `-rdvred.dat`. */
export function escolherRdv(aux: Aux): EscolhaRdv | null {
  let melhor: (EscolhaRdv & { drHr: string }) | null = null;
  for (const h of aux.hashes ?? []) {
    const arq = h.arq ?? [];
    const rdv = arq.find((x) => x.tp === "rdv") ?? arq.find((x) => x.nm.endsWith("-rdv.dat")) ?? arq.find((x) => x.nm.endsWith("-rdvred.dat"));
    if (rdv === undefined) continue;
    const temBu = arq.some((x) => x.tp === "bu" || x.tp === "busa" || x.nm.endsWith("-bu.dat") || x.nm.endsWith("-busa.dat"));
    const drHr = dataHoraTse(h.dr, h.hr) ?? "";
    if (melhor === null || drHr >= melhor.drHr) melhor = { hash: h.hash, nome: rdv.nm, temBu, drHr };
  }
  return melhor === null ? null : { hash: melhor.hash, nome: melhor.nome, temBu: melhor.temBu };
}

export interface ResultadoRdv extends SecaoAlvo {
  status: string;
  auxProprio: string | null;
  hash: string | null;
  rdvNome: string | null;
  mesmoHashBu: boolean | null;
  bytes: number | null;
  sha256: string | null;
  gz: Uint8Array<ArrayBuffer> | null;
  erro: string | null;
  requisicoes: number;
  rdv: Rdv | null;
  cargos: CargoRdv[] | null;
  confere: boolean | null;
  divergencias: string[] | null;
  buNome: string | null;
}

type Chave = Pick<SecaoAlvo, "uf" | "mun" | "zona" | "secao">;

export class EscritorRdv {
  private readonly ins;
  private readonly delCargo;
  private readonly delVoto;
  private readonly insCargo;
  private readonly insVoto;
  private readonly updConf;
  private readonly qCargo;
  private readonly qVoto;

  constructor(private readonly db: Database) {
    this.ins = db.prepare(`INSERT OR REPLACE INTO rdv (uf, mun, zona, secao, status, aux_json, hash, mesmo_hash_bu, rdv_nome, bytes, sha256, rdv_gz,
        gerado_em, fase, pleito, tipo_urna, tipo_arquivo, numero_interno_urna, origem, id_confere, confere, bu_nome, divergencias, conferido_em,
        erro, requisicoes, baixado_em)
      VALUES (${Array.from({ length: 27 }, (_, i) => `?${i + 1}`).join(", ")})`);
    const onde = "WHERE uf = ? AND mun = ? AND zona = ? AND secao = ?";
    this.delCargo = db.prepare(`DELETE FROM rdv_cargo ${onde}`);
    this.delVoto = db.prepare(`DELETE FROM rdv_voto ${onde}`);
    this.insCargo = db.prepare("INSERT INTO rdv_cargo (uf, mun, zona, secao, cargo, eleicao, escolhas, votos, ordenado) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)");
    this.insVoto = db.prepare(`INSERT INTO rdv_voto (uf, mun, zona, secao, cargo, tipo, digitacao, votos) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
      ON CONFLICT (uf, mun, zona, secao, cargo, tipo, digitacao) DO UPDATE SET votos = votos + excluded.votos`);
    this.updConf = db.prepare(`UPDATE rdv SET confere = ?5, divergencias = ?6, bu_nome = ?7, conferido_em = ?8
      WHERE uf = ?1 AND mun = ?2 AND zona = ?3 AND secao = ?4`);
    this.qCargo = db.query<{ cargo: number; eleicao: number; escolhas: number; votos: number; ordenado: number }, [string, string, number, number]>(
      `SELECT cargo, eleicao, escolhas, votos, ordenado FROM rdv_cargo ${onde}`,
    );
    this.qVoto = db.query<{ cargo: number; tipo: number; digitacao: string; votos: number }, [string, string, number, number]>(
      `SELECT cargo, tipo, digitacao, votos FROM rdv_voto ${onde}`,
    );
  }

  gravar(lote: readonly ResultadoRdv[], agoraIso: string): void {
    this.db.transaction(() => {
      for (const r of lote) this.gravarUm(r, agoraIso);
    })();
  }

  private gravarUm(r: ResultadoRdv, agoraIso: string): void {
    const k = [r.uf, r.mun, r.zona, r.secao] as const;
    const v = r.rdv;
    const id = v?.identificacao;
    const idConfere = id === undefined ? null : id.municipioZona.municipio === Number(r.mun) && id.municipioZona.zona === r.zona && id.secao === r.secao ? 1 : 0;
    const conf = r.confere === null ? null : r.confere ? 1 : 0;
    this.ins.run(
      ...k, r.status, r.auxProprio, r.hash, r.mesmoHashBu === null ? null : r.mesmoHashBu ? 1 : 0, r.rdvNome, r.bytes, r.sha256, r.gz,
      v?.cabecalho.dataGeracao ?? null, v?.fase ?? null, v?.pleito ?? null, v?.urna.tipoUrna ?? null, v?.urna.tipoArquivo ?? null,
      v?.urna.correspondenciaResultado.carga.numeroInternoUrna ?? null, v?.origem ?? null, idConfere, conf, r.buNome,
      r.divergencias === null ? null : JSON.stringify(r.divergencias), conf === null ? null : agoraIso, r.erro, r.requisicoes, agoraIso,
    );
    this.delCargo.run(...k);
    this.delVoto.run(...k);
    for (const c of r.cargos ?? []) {
      this.insCargo.run(...k, c.cargo, c.idEleicao, c.quantidadeEscolhas, c.nVotos, c.ordenado ? 1 : 0);
      for (const x of c.contagem) this.insVoto.run(...k, c.cargo, x.tipo, x.digitacao, x.votos);
    }
  }

  /** Cargos de uma seção já gravada, para reconferir sem reler o RDV. */
  cargosDe(k: Chave): CargoRdv[] {
    const votos = this.qVoto.all(k.uf, k.mun, k.zona, k.secao);
    return this.qCargo.all(k.uf, k.mun, k.zona, k.secao).map((c) => ({
      idEleicao: c.eleicao, cargo: c.cargo, quantidadeEscolhas: c.escolhas, nVotos: c.votos, ordenado: c.ordenado === 1,
      contagem: votos.filter((x) => x.cargo === c.cargo).map((x) => ({ tipo: x.tipo, digitacao: x.digitacao, votos: x.votos })),
    }));
  }

  gravarConferencia(k: Chave, confere: boolean, divergencias: string[], buNome: string | null, agoraIso: string): void {
    this.updConf.run(k.uf, k.mun, k.zona, k.secao, confere ? 1 : 0, JSON.stringify(divergencias), buNome, agoraIso);
  }
}
