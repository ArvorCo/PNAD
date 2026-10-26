// Banco dos arquivos de assinatura da seção (`.vsc`) do 1º e do 2º turno de 2026
// (data/vsc_2t_2026.sqlite), separado dos bancos dos BUs. Chaves como em secoes_2t_2026.sqlite:
// uf minúscula, mun com 5 dígitos, zona e secao inteiras, mais o turno.
import { Database } from "bun:sqlite";
import { mkdirSync } from "node:fs";
import { dirname } from "node:path";
import type { ResumoVsc } from "../../src/secoes2t/vsc-decode.ts";
import type { Aux } from "./secao.ts";
import { dataHoraTse } from "./secao.ts";

export const PLEITO_TURNO: Record<1 | 2, string> = { 1: "3220", 2: "3221" };
const p4 = (n: number): string => String(n).padStart(4, "0");

export interface SecaoAlvoVsc {
  turno: 1 | 2;
  uf: string;
  mun: string;
  zona: number;
  secao: number;
  nsp: number | null;
}

export const baseUrna = (turno: 1 | 2): string => `https://resultados.tse.jus.br/oficial/ele2026/arquivo-urna/${PLEITO_TURNO[turno]}`;
export const dirSecaoTurno = (s: SecaoAlvoVsc): string => `${baseUrna(s.turno)}/dados/${s.uf}/${s.mun}/${p4(s.zona)}/${p4(s.secao)}`;
export const urlAuxTurno = (s: SecaoAlvoVsc): string =>
  `${dirSecaoTurno(s)}/p00${PLEITO_TURNO[s.turno]}-${s.uf}-m${s.mun}-z${p4(s.zona)}-s${p4(s.secao)}-aux.json`;

export const ESQUEMA_VSC = `
CREATE TABLE IF NOT EXISTS meta (chave TEXT PRIMARY KEY, valor TEXT);

-- Uma linha por seção e turno. status: ok | sem_vsc (aux sem .vsc) | agregada | aux_404 | vsc_404 | erro.
CREATE TABLE IF NOT EXISTS vsc (
  turno INTEGER NOT NULL,
  uf TEXT NOT NULL,
  mun TEXT NOT NULL,
  zona INTEGER NOT NULL,
  secao INTEGER NOT NULL,
  status TEXT NOT NULL,
  aux_json TEXT,                -- só quando o aux foi pedido por esta coleta
  hash TEXT,
  mesmo_hash_bu INTEGER,        -- o hash do .vsc é o mesmo do BU escolhido no banco dos BUs
  vsc_nome TEXT,
  origem TEXT,                  -- vota (urna) | sa (sistema de apuração)
  recebido_em TEXT,             -- dr/hr do hash no aux
  n_hashes_vsc INTEGER,         -- quantos hashes do aux listam .vsc
  bytes INTEGER,
  sha256 TEXT,
  vsc_gz BLOB,                  -- só com --guardar-vsc
  sw_criado_em TEXT, sw_usuario TEXT, sw_serial TEXT, sw_chave_data TEXT, sw_resumo_ok INTEGER,
  hw_criado_em TEXT, hw_usuario TEXT, hw_serial TEXT, hw_algoritmo INTEGER, hw_bits INTEGER, hw_resumo_ok INTEGER,
  modelo_codigo INTEGER, algoritmo_hw_codigo INTEGER,
  listas_ok INTEGER,            -- SW e HW listam os mesmos arquivos, tamanhos e resumos
  n_arquivos INTEGER,
  cert_formato TEXT, cert_der BLOB, cert_sha256 TEXT, cert_serial TEXT, cert_serial_hex TEXT,
  cert_emissor_cn TEXT, cert_titular_cn TEXT, cert_titular TEXT,
  cert_validade_inicio TEXT, cert_validade_fim TEXT,
  cert_alg_chave TEXT, cert_param_chave TEXT, cert_chave_sha256 TEXT, cert_aki TEXT, cert_ski TEXT,
  cadeia_valida INTEGER, ac TEXT, cadeia_motivo TEXT, erro_certificado TEXT,
  cn_confere_usuario INTEGER,   -- série do CN = série do usuário HW
  hw_assinatura_ok INTEGER,     -- autoassinatura de hardware conferida com a chave do certificado
  hw_bu_assinatura_ok INTEGER,  -- assinatura de hardware da entrada do BU
  bu_nome TEXT,
  bu_confere_vsc INTEGER,       -- SHA-512 e tamanho do BU guardado = entrada do .vsc; NULL sem BU do mesmo hash
  erro TEXT,
  requisicoes INTEGER NOT NULL DEFAULT 0,
  baixado_em TEXT NOT NULL,
  PRIMARY KEY (turno, uf, mun, zona, secao)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS vsc_status ON vsc (turno, status);
CREATE INDEX IF NOT EXISTS vsc_cert ON vsc (cert_sha256);
CREATE INDEX IF NOT EXISTS vsc_hw_serial ON vsc (hw_serial);

-- Arquivos listados na assinatura de hardware, com o resumo SHA-512 (64 bytes).
CREATE TABLE IF NOT EXISTS vsc_arquivo (
  turno INTEGER NOT NULL,
  uf TEXT NOT NULL,
  mun TEXT NOT NULL,
  zona INTEGER NOT NULL,
  secao INTEGER NOT NULL,
  ordem INTEGER NOT NULL,
  sufixo TEXT NOT NULL,         -- parte do nome depois do último '-' (bu.dat, log.jez, ...)
  nome_confere INTEGER NOT NULL, -- o prefixo do nome é o da própria seção
  tamanho INTEGER NOT NULL,
  sha512 BLOB NOT NULL,
  PRIMARY KEY (turno, uf, mun, zona, secao, ordem)
) WITHOUT ROWID;
`;

export function abrirVsc(path: string): Database {
  if (path !== ":memory:") mkdirSync(dirname(path), { recursive: true });
  const db = new Database(path, { create: true, strict: true });
  for (const p of ["PRAGMA journal_mode = WAL", "PRAGMA synchronous = NORMAL", "PRAGMA busy_timeout = 5000", "PRAGMA wal_autocheckpoint = 4000"]) db.run(p);
  db.run(ESQUEMA_VSC);
  return db;
}

export interface EscolhaVsc {
  hash: string;
  nome: string;
  origem: "vota" | "sa";
  recebidoEm: string | null;
  nHashes: number;
}

const ehVsc = (x: { nm: string; tp?: string | undefined }): "vota" | "sa" | null => {
  if (x.tp === "vota" || x.nm.endsWith("-vota.vsc")) return "vota";
  if (x.tp === "sa" || x.nm.endsWith("-sa.vsc")) return "sa";
  return null;
};

/** O `.vsc` do hash do BU escolhido, quando houver; senão o do hash mais recente que lista `.vsc`. */
export function escolherVsc(aux: Aux, hashBu: string | null): EscolhaVsc | null {
  const cands: Array<EscolhaVsc & { drHr: string }> = [];
  for (const h of aux.hashes ?? []) {
    for (const x of h.arq ?? []) {
      const origem = ehVsc(x);
      if (origem === null) continue;
      const drHr = dataHoraTse(h.dr, h.hr) ?? "";
      cands.push({ hash: h.hash, nome: x.nm, origem, recebidoEm: drHr || null, nHashes: 0, drHr });
      break;
    }
  }
  if (cands.length === 0) return null;
  const doBu = hashBu === null ? undefined : cands.find((c) => c.hash === hashBu);
  let melhor = doBu ?? cands[0];
  if (doBu === undefined) for (const c of cands) if (melhor === undefined || c.drHr >= melhor.drHr) melhor = c;
  if (melhor === undefined) return null;
  return { hash: melhor.hash, nome: melhor.nome, origem: melhor.origem, recebidoEm: melhor.recebidoEm, nHashes: cands.length };
}

/** Prefixo esperado dos arquivos da seção: o0<pleito><uf><mun><zona><secao>. */
export const prefixoSecao = (s: SecaoAlvoVsc): string => `o0${PLEITO_TURNO[s.turno]}${s.uf}${s.mun}${p4(s.zona)}${p4(s.secao)}`;

export interface ResultadoVsc extends SecaoAlvoVsc {
  status: string;
  auxProprio: string | null;
  escolha: EscolhaVsc | null;
  mesmoHashBu: boolean | null;
  bytes: number | null;
  sha256: string | null;
  gz: Uint8Array | null;
  resumo: ResumoVsc | null;
  buNome: string | null;
  buConfere: boolean | null;
  erro: string | null;
  requisicoes: number;
}

const b = (x: boolean | null | undefined): number | null => (x === null || x === undefined ? null : x ? 1 : 0);

export class EscritorVsc {
  private readonly ins;
  private readonly delArq;
  private readonly insArq;

  constructor(private readonly db: Database) {
    const cols = [
      "turno", "uf", "mun", "zona", "secao", "status", "aux_json", "hash", "mesmo_hash_bu", "vsc_nome", "origem", "recebido_em", "n_hashes_vsc",
      "bytes", "sha256", "vsc_gz", "sw_criado_em", "sw_usuario", "sw_serial", "sw_chave_data", "sw_resumo_ok", "hw_criado_em", "hw_usuario",
      "hw_serial", "hw_algoritmo", "hw_bits", "hw_resumo_ok", "modelo_codigo", "algoritmo_hw_codigo", "listas_ok", "n_arquivos", "cert_formato",
      "cert_der", "cert_sha256", "cert_serial", "cert_serial_hex", "cert_emissor_cn", "cert_titular_cn", "cert_titular", "cert_validade_inicio",
      "cert_validade_fim", "cert_alg_chave", "cert_param_chave", "cert_chave_sha256", "cert_aki", "cert_ski", "cadeia_valida", "ac", "cadeia_motivo",
      "erro_certificado", "cn_confere_usuario", "hw_assinatura_ok", "hw_bu_assinatura_ok", "bu_nome", "bu_confere_vsc", "erro", "requisicoes", "baixado_em",
    ];
    this.ins = db.prepare(`INSERT OR REPLACE INTO vsc (${cols.join(", ")}) VALUES (${cols.map((_, i) => `?${i + 1}`).join(", ")})`);
    const onde = "WHERE turno = ? AND uf = ? AND mun = ? AND zona = ? AND secao = ?";
    this.delArq = db.prepare(`DELETE FROM vsc_arquivo ${onde}`);
    this.insArq = db.prepare("INSERT INTO vsc_arquivo (turno, uf, mun, zona, secao, ordem, sufixo, nome_confere, tamanho, sha512) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)");
  }

  gravar(lote: readonly ResultadoVsc[], agoraIso: string): void {
    this.db.transaction(() => {
      for (const r of lote) this.gravarUm(r, agoraIso);
    })();
  }

  private gravarUm(r: ResultadoVsc, agoraIso: string): void {
    const k = [r.turno, r.uf, r.mun, r.zona, r.secao] as const;
    const v = r.resumo;
    const c = v?.certificado ?? null;
    const e = r.escolha;
    this.ins.run(
      ...k, r.status, r.auxProprio, e?.hash ?? null, b(r.mesmoHashBu), e?.nome ?? null, e?.origem ?? null, e?.recebidoEm ?? null, e?.nHashes ?? null,
      r.bytes, r.sha256, r.gz, v?.swCriadoEm ?? null, v?.swUsuario ?? null, v?.swSerial ?? null, v?.swChaveData ?? null, b(v?.swResumoConfere),
      v?.hwCriadoEm ?? null, v?.hwUsuario ?? null, v?.hwSerial ?? null, v?.hwAlgoritmo ?? null, v?.hwBits ?? null, b(v?.hwResumoConfere),
      v?.modeloCodigo ?? null, v?.algoritmoHwCodigo ?? null, b(v?.listasConferem), v?.arquivos.length ?? null, c?.formato ?? null, c?.der ?? null,
      c?.sha256 ?? null, c?.serial ?? null, c?.serialHex ?? null, c?.emissorCN ?? null, c?.titularCN ?? null, c?.titular ?? null,
      c?.validadeInicio ?? null, c?.validadeFim ?? null, c?.algoritmoChave ?? null, c?.parametroChave ?? null, c?.chavePublicaSha256 ?? null,
      c?.aki ?? null, c?.ski ?? null, b(c?.cadeiaValida), c?.ac ?? null, c?.motivoCadeia ?? null, v?.erroCertificado ?? null,
      b(v?.cnConfereUsuario), b(v?.hwAssinaturaValida), b(v?.hwAssinaturaBuValida), r.buNome, b(r.buConfere), r.erro, r.requisicoes, agoraIso,
    );
    this.delArq.run(...k);
    const pref = prefixoSecao(r);
    v?.arquivos.forEach((a, i) => {
      const corte = a.nome.lastIndexOf("-");
      this.insArq.run(...k, i, a.nome.slice(corte + 1), a.nome.slice(0, corte) === pref ? 1 : 0, a.tamanho, Buffer.from(a.sha512, "hex"));
    });
  }
}
