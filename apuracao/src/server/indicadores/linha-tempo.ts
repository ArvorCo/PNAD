// Linha do tempo dos arquivos de UF (nível uf) de uma eleição e cargo: todas as versões não
// regressivas lidas até `at`, com totais e votos, numa leitura só (duas consultas). Serve às rotas
// de regiões, UFs, estaduais e evolução, que depois só fazem contas em memória.
import type { Database } from "bun:sqlite";
import { maxSnapshotId } from "../../db/leitura.ts";
import type { N, S } from "../../db/linhas.ts";
import { CacheCurto } from "../cache.ts";
import { FIM } from "../consultas.ts";
import { RelogioArquivo, RelogioPublicacao } from "./base.ts";

export interface Versao {
  id: number;
  /** leitura (ms) */
  cap: number;
  /** instante da totalização que trouxe estas contagens (ms; ver RelogioArquivo), não decrescente */
  inst: number;
  /** publicação (gerado_em) da primeira versão com estas contagens (ms; ver RelogioPublicacao), não decrescente */
  pub: number;
  /** geração desta versão (gerado_em; sem ele, a leitura), mesmo regerada sem contagem nova (ms) */
  ger: number;
  ts: number;
  st: number;
  snt: number;
  te: number;
  est: number;
  comparecimento: number;
  abstencao: number;
  tv: number;
  vv: number;
  vb: number;
  vn: number;
  votos: ReadonlyMap<number, number>;
}

export interface LinhaUf {
  /** sigla em caixa alta */
  uf: string;
  arquivo_id: number;
  /** ordem de leitura (id); o instante corrigido também cresce nessa ordem */
  versoes: Versao[];
}

export interface LinhaTempo {
  ele: number;
  cargo: number;
  ufs: Map<string, LinhaUf>;
}

interface VersaoRow {
  arquivo_id: number;
  uf: S;
  id: number;
  capturado_em: string;
  gerado_em: S;
  totalizado_em: S;
  ts: N; st: N; snt: N; te: N; est: N; comparecimento: N; abstencao: N; tv: N; vv: N; vb: N; vn: N;
}

const n0 = (v: number | null | undefined): number => v ?? 0;

const FILTRO = `FROM arquivo a
  JOIN snapshot s ON s.arquivo_id = a.id AND s.regressivo = 0 AND s.capturado_em <= ?
  WHERE a.tipo = 'u' AND a.eleicao_cd = ? AND a.cargo_cd = ? AND a.nivel = 'uf'`;

export function carregarLinhaTempo(db: Database, ele: number, cargo: number, at?: string): LinhaTempo {
  const ate = at ?? FIM;
  const rows = db
    .query<VersaoRow, [string, number, number]>(
      `SELECT a.id AS arquivo_id, a.uf, s.id, s.capturado_em, s.gerado_em, s.totalizado_em,
              t.ts, t.st, t.snt, t.te, t.est, t.comparecimento, t.abstencao, t.tv, t.vv, t.vb, t.vn
       ${FILTRO.replace("WHERE", "JOIN totais t ON t.snapshot_id = s.id WHERE")} ORDER BY a.id, s.id`,
    )
    .all(ate, ele, cargo);
  const votos = new Map<number, Map<number, number>>();
  const vrows = db
    .query<{ snapshot_id: number; sqcand: number; vap: N }, [string, number, number]>(
      `SELECT vc.snapshot_id, vc.sqcand, vc.vap ${FILTRO.replace("WHERE", "JOIN voto_candidato vc ON vc.snapshot_id = s.id WHERE")}`,
    )
    .all(ate, ele, cargo);
  for (const v of vrows) {
    let m = votos.get(v.snapshot_id);
    if (!m) {
      m = new Map();
      votos.set(v.snapshot_id, m);
    }
    m.set(v.sqcand, n0(v.vap));
  }
  const ufs = new Map<string, LinhaUf>();
  const relogios = new Map<number, RelogioArquivo>();
  const publicacoes = new Map<number, RelogioPublicacao>();
  for (const r of rows) {
    const uf = (r.uf ?? "").toUpperCase();
    if (!uf) continue;
    let linha = ufs.get(uf);
    if (!linha) {
      linha = { uf, arquivo_id: r.arquivo_id, versoes: [] };
      ufs.set(uf, linha);
    }
    let rel = relogios.get(r.arquivo_id);
    if (!rel) {
      rel = new RelogioArquivo(uf);
      relogios.set(r.arquivo_id, rel);
    }
    let pub = publicacoes.get(r.arquivo_id);
    if (!pub) {
      pub = new RelogioPublicacao();
      publicacoes.set(r.arquivo_id, pub);
    }
    const contagens = `${r.st}|${r.tv}|${r.comparecimento}|${r.abstencao}`;
    const cap = Date.parse(r.capturado_em);
    const ger = r.gerado_em ? Date.parse(r.gerado_em) : Number.NaN;
    linha.versoes.push({
      id: r.id,
      cap,
      ger: Number.isFinite(ger) ? ger : cap,
      inst: rel.instante(contagens, r.totalizado_em, r.gerado_em, r.capturado_em),
      pub: pub.instante(contagens, r.gerado_em, r.capturado_em),
      ts: n0(r.ts), st: n0(r.st), snt: n0(r.snt), te: n0(r.te), est: n0(r.est),
      comparecimento: n0(r.comparecimento), abstencao: n0(r.abstencao),
      tv: n0(r.tv), vv: n0(r.vv), vb: n0(r.vb), vn: n0(r.vn),
      votos: votos.get(r.id) ?? new Map(),
    });
  }
  return { ele, cargo, ufs };
}

const cache = new CacheCurto<LinhaTempo>(3000, 16);

/** Linha do tempo com cache curto (no máximo um recálculo a cada 3 s com dados novos). */
export function linhaTempo(db: Database, ele: number, cargo: number, at?: string): LinhaTempo {
  const k = [db.filename, ele, cargo, at ?? ""].join("|");
  return cache.obter(k, maxSnapshotId(db), () => carregarLinhaTempo(db, ele, cargo, at));
}

/** Versão vigente para quem lia em `ms`: a de maior id entre as lidas até ali. */
export function versaoLidaAte(l: LinhaUf, ms: number): Versao | null {
  for (let i = l.versoes.length - 1; i >= 0; i -= 1) {
    const v = l.versoes[i];
    if (v && v.cap <= ms) return v;
  }
  return null;
}

/** Estado no relógio do TSE: a versão de maior instante corrigido até `ms`, entre as lidas até `lidoAteMs`. */
export function versaoNoInstante(l: LinhaUf, ms: number, lidoAteMs: number): Versao | null {
  for (let i = l.versoes.length - 1; i >= 0; i -= 1) {
    const v = l.versoes[i];
    if (v && v.cap <= lidoAteMs && v.inst <= ms) return v;
  }
  return null;
}

/** Estado no relógio de publicação: a versão de maior publicação até `ms`, entre as lidas até `lidoAteMs`. */
export function versaoPublicadaAte(l: LinhaUf, ms: number, lidoAteMs: number): Versao | null {
  for (let i = l.versoes.length - 1; i >= 0; i -= 1) {
    const v = l.versoes[i];
    if (v && v.cap <= lidoAteMs && v.pub <= ms) return v;
  }
  return null;
}

/** Primeira versão com todas as seções totalizadas (st = ts > 0). */
export function versaoFechamento(l: LinhaUf): Versao | null {
  for (const v of l.versoes) if (v.ts > 0 && v.st >= v.ts) return v;
  return null;
}

export function limparCacheLinhaTempo(): void {
  cache.limpar();
}
