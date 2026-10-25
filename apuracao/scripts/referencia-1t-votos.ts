// Uso: bun run scripts/referencia-1t-votos.ts [--db data/apuracao.sqlite] [--saida data/referencia_1t_votos.json]
//
// Régua de votos do 1º turno (04/10/2026) por município, para a projeção ao vivo do 2º turno
// (src/server/indicadores/projecao.ts). Lê, somente leitura, os arquivos `u` de nível `mu` da
// eleição 6257, cargo 1 (presidente), e guarda de cada município a versão final: o último
// snapshot não regressivo com totais. Grava, por UF e código TSE de 5 dígitos, os votos de
// Flávio Bolsonaro (22) e Lula (13), os válidos, o comparecimento e o eleitorado; mais os totais
// por UF e Brasil. Inclui o exterior (ZZ). Idempotente: só `meta.gerado_em` muda.
import { Database } from "bun:sqlite";
import { renameSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import type { MunVotos1T } from "../src/turno2/referencia.ts";

const RAIZ = resolve(dirname(fileURLToPath(import.meta.url)), "..");

function arg(nome: string, padrao: string): string {
  const i = process.argv.indexOf(nome);
  const v = i >= 0 ? process.argv[i + 1] : undefined;
  return v ? resolve(v) : padrao;
}

const DB = arg("--db", join(RAIZ, "data", "apuracao.sqlite"));
const SAIDA = arg("--saida", join(RAIZ, "data", "referencia_1t_votos.json"));
const ELEICAO = 6257;
const CARGO = 1;
const NUM_F = 22;
const NUM_L = 13;

interface Linha {
  uf: string | null;
  cd: string | null;
  vv: number | null;
  comparecimento: number | null;
  te: number | null;
  f: number | null;
  l: number | null;
}

const db = new Database(DB, { readonly: true });
const cand = db
  .query<{ sqcand: number; numero: number }, [number, number]>("SELECT sqcand, numero FROM candidato WHERE eleicao_cd = ? AND cargo_cd = ?")
  .all(ELEICAO, CARGO);
const sqF = cand.find((c) => c.numero === NUM_F)?.sqcand;
const sqL = cand.find((c) => c.numero === NUM_L)?.sqcand;
if (sqF === undefined || sqL === undefined) throw new Error("candidatos 22 e 13 não encontrados na eleição 6257");

const linhas = db
  .query<Linha, [number, number, number, number]>(
    `WITH fin AS (
       SELECT a.id, a.uf, a.municipio_cd AS cd,
              (SELECT MAX(s.id) FROM snapshot s JOIN totais t0 ON t0.snapshot_id = s.id
                WHERE s.arquivo_id = a.id AND s.regressivo = 0) AS sid
       FROM arquivo a WHERE a.tipo = 'u' AND a.nivel = 'mu' AND a.eleicao_cd = ? AND a.cargo_cd = ?
     )
     SELECT fin.uf, fin.cd, t.vv, t.comparecimento, t.te,
            (SELECT vap FROM voto_candidato v WHERE v.snapshot_id = fin.sid AND v.sqcand = ?) AS f,
            (SELECT vap FROM voto_candidato v WHERE v.snapshot_id = fin.sid AND v.sqcand = ?) AS l
     FROM fin JOIN totais t ON t.snapshot_id = fin.sid`,
  )
  .all(ELEICAO, CARGO, sqF, sqL);

// Trajetória de cada município na noite do 1º turno: [st, f, l] por versão, st crescente (a
// projeção compara o 2º turno com o 1º no mesmo estágio da contagem do município).
interface TrajRow {
  uf: string | null;
  cd: string | null;
  st: number | null;
  ts: number | null;
  f: number | null;
  l: number | null;
}
const traj = new Map<string, { ts: number; c: [number, number, number][] }>();
for (const r of db
  .query<TrajRow, [number, number, number, number]>(
    `SELECT a.uf, a.municipio_cd AS cd, t.st, t.ts,
            (SELECT vap FROM voto_candidato v WHERE v.snapshot_id = s.id AND v.sqcand = ?) AS f,
            (SELECT vap FROM voto_candidato v WHERE v.snapshot_id = s.id AND v.sqcand = ?) AS l
     FROM arquivo a JOIN snapshot s ON s.arquivo_id = a.id AND s.regressivo = 0 JOIN totais t ON t.snapshot_id = s.id
     WHERE a.tipo = 'u' AND a.nivel = 'mu' AND a.eleicao_cd = ? AND a.cargo_cd = ?
     ORDER BY a.id, s.id`,
  )
  .iterate(sqF, sqL, ELEICAO, CARGO)) {
  if (!r.uf || !r.cd) continue;
  const k = `${r.uf.toUpperCase()}|${r.cd.padStart(5, "0")}`;
  const st = r.st ?? 0;
  if (st <= 0) continue;
  const x = traj.get(k) ?? { ts: 0, c: [] };
  x.ts = r.ts ?? x.ts;
  // Mantém st estritamente crescente: versão posterior com st igual ou menor substitui as anteriores.
  while (x.c.length > 0 && (x.c[x.c.length - 1]?.[0] ?? 0) >= st) x.c.pop();
  x.c.push([st, r.f ?? 0, r.l ?? 0]);
  traj.set(k, x);
}

const municipios: Record<string, Record<string, MunVotos1T>> = {};
const ufs: Record<string, MunVotos1T & { municipios: number }> = {};
const br = { f1: 0, l1: 0, vv1: 0, comp1: 0, te1: 0, municipios: 0 };
let pontos = 0;
for (const r of linhas.sort((a, b) => `${a.uf}${a.cd}`.localeCompare(`${b.uf}${b.cd}`))) {
  if (!r.uf || !r.cd) continue;
  const uf = r.uf.toUpperCase();
  const cd = r.cd.padStart(5, "0");
  const t = traj.get(`${uf}|${cd}`);
  const m: MunVotos1T = { f1: r.f ?? 0, l1: r.l ?? 0, vv1: r.vv ?? 0, comp1: r.comparecimento ?? 0, te1: r.te ?? 0 };
  if (t && t.ts > 0 && t.c.length > 0) {
    m.ts1 = t.ts;
    m.c = t.c;
    pontos += t.c.length;
  }
  (municipios[uf] ??= {})[cd] = m;
  const u = (ufs[uf] ??= { f1: 0, l1: 0, vv1: 0, comp1: 0, te1: 0, municipios: 0 });
  for (const alvo of [u, br]) {
    alvo.f1 += m.f1;
    alvo.l1 += m.l1;
    alvo.vv1 += m.vv1;
    alvo.comp1 += m.comp1;
    alvo.te1 += m.te1;
    alvo.municipios += 1;
  }
}
db.close();

const saida = {
  meta: {
    gerado_em: new Date().toISOString(),
    fonte: "data/apuracao.sqlite, arquivos u de nível mu, eleição 6257, cargo 1; versão final = último snapshot não regressivo com totais",
    eleicao: ELEICAO,
    cargo: CARGO,
    candidatos: { f: { numero: NUM_F, sqcand: sqF }, l: { numero: NUM_L, sqcand: sqL } },
    campos: {
      f1: "votos de Flávio Bolsonaro (22)",
      l1: "votos de Lula (13)",
      vv1: "votos válidos",
      comp1: "comparecimento",
      te1: "eleitorado",
      ts1: "seções do município",
      c: "trajetória da noite: [seções totalizadas, votos de Flávio, votos de Lula], seções crescentes",
    },
  },
  brasil: br,
  ufs,
  municipios,
};
const tmp = `${SAIDA}.tmp`;
writeFileSync(tmp, `${JSON.stringify(saida)}\n`);
renameSync(tmp, SAIDA);
const pf = (100 * br.f1) / br.vv1;
const pl = (100 * br.l1) / br.vv1;
console.log(`${br.municipios} municípios; Flávio ${pf.toFixed(2)}% × Lula ${pl.toFixed(2)}% dos válidos; entre os dois, Flávio ${((100 * br.f1) / (br.f1 + br.l1)).toFixed(2)}%`);
console.log(`${pontos} pontos de trajetória; gravado ${SAIDA}`);
