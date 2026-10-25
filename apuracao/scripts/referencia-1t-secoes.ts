// Uso: bun run scripts/referencia-1t-secoes.ts [--saida data/referencia_1t_secoes.json]
//
// Régua do 1º turno por seção para a vigilância de comparecimento do 2º turno
// (/api/2t/comparecimento). Lê, somente leitura:
//   data/secoes_2026.sqlite, tabela `bu` (BU de cada seção no 1º turno): aptos, comparecimento,
//     compareceram sem biometria, habilitados por ano de nascimento e encerramento (último voto);
//   ../docs/assets/politize/dados/zona/<UF>/<zona>.json: local de votação e votos de Flávio e
//     Lula por seção principal no 1º turno;
//   ../docs/assets/politize/dados/mun/<UF>/<mun>.json: coordenadas de cada local.
// Grava o universo inteiro em formato compacto (cabe abaixo de 30 MB):
//   secoes[uf][mun][zona] = [[secao, aptos1, comp1, sem_bio1, ano_nasc1, enc1_min, local, fl1, lu1], ...]
//   locais = [[lon, lat], ...] (índice `local` das seções; -1 sem coordenada)
//   municipios[uf][mun] = { n, comp_p50, comp_p90, sem_bio_p50, sem_bio_p90, lon, lat }
// enc1_min: minutos após 17:00 de Brasília de 04/10/2026 (hora local da urna convertida pelo fuso
// da UF). Taxas em % de 0 a 100: comparecimento / aptos e sem biometria / comparecimento.
import { Database } from "bun:sqlite";
import { existsSync, readdirSync, readFileSync, renameSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { horaLocalUrnaParaIso, minutosDesde17h, percentil, T0_1T_MS } from "../src/turno2/comum.ts";

const RAIZ = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const DB_SECOES = join(RAIZ, "data", "secoes_2026.sqlite");
const POLITIZE = resolve(RAIZ, "..", "docs", "assets", "politize", "dados");

interface BuRow {
  uf: string;
  mun: string;
  zona: number;
  secao: number;
  aptos: number | null;
  comparecimento: number | null;
  comp_sem_biometria: number | null;
  hab_ano_nascimento: number | null;
  encerramento: string | null;
}

interface Tabela {
  colunas: string[];
  linhas: unknown[][];
}

const r2 = (x: number): number => Math.round(x * 100) / 100;
const r4 = (x: number): number => Math.round(x * 10000) / 10000;

function argSaida(): string {
  const i = process.argv.indexOf("--saida");
  return resolve(RAIZ, i >= 0 ? (process.argv[i + 1] ?? "") : "data/referencia_1t_secoes.json");
}

/** local_id do Politize (AC-01392-1-1279) → [lon, lat] e aptos do local. */
function lerLocais(): Map<string, { lon: number; lat: number; aptos: number }> {
  const out = new Map<string, { lon: number; lat: number; aptos: number }>();
  const dirMun = join(POLITIZE, "mun");
  for (const uf of readdirSync(dirMun)) {
    if (uf === "ZZ") continue;
    for (const arq of readdirSync(join(dirMun, uf))) {
      if (!arq.endsWith(".json")) continue;
      const d = JSON.parse(readFileSync(join(dirMun, uf, arq), "utf8")) as { locais?: Tabela };
      const t = d.locais;
      if (!t) continue;
      const iId = t.colunas.indexOf("local_id");
      const iLat = t.colunas.indexOf("lat");
      const iLon = t.colunas.indexOf("lon");
      const iAptos = t.colunas.indexOf("aptos");
      for (const l of t.linhas) {
        const id = l[iId];
        const lat = l[iLat];
        const lon = l[iLon];
        if (typeof id !== "string" || typeof lat !== "number" || typeof lon !== "number") continue;
        out.set(id, { lon, lat, aptos: typeof l[iAptos] === "number" ? (l[iAptos] as number) : 0 });
      }
    }
  }
  return out;
}

/** uf:mun:zona:secao → { local_id, flavio, lula } do 1º turno (seção principal). */
function lerSecoesPolitize(): Map<string, { local: string | null; fl: number | null; lu: number | null }> {
  const out = new Map<string, { local: string | null; fl: number | null; lu: number | null }>();
  const dirZona = join(POLITIZE, "zona");
  for (const uf of readdirSync(dirZona)) {
    if (uf === "ZZ") continue;
    for (const arq of readdirSync(join(dirZona, uf))) {
      if (!arq.endsWith(".json")) continue;
      const d = JSON.parse(readFileSync(join(dirZona, uf, arq), "utf8")) as { zona: number; secoes?: Tabela };
      const t = d.secoes;
      if (!t) continue;
      const c = (n: string): number => t.colunas.indexOf(n);
      const [iS, iL, iM, iF, iLu] = [c("secao"), c("local_id"), c("mun_tse"), c("flavio"), c("lula")];
      for (const l of t.linhas) {
        const k = `${uf.toLowerCase()}:${String(l[iM])}:${d.zona}:${String(l[iS])}`;
        out.set(k, {
          local: typeof l[iL] === "string" ? (l[iL] as string) : null,
          fl: typeof l[iF] === "number" ? (l[iF] as number) : null,
          lu: typeof l[iLu] === "number" ? (l[iLu] as number) : null,
        });
      }
    }
  }
  return out;
}

function main(): void {
  if (!existsSync(DB_SECOES)) throw new Error(`sem ${DB_SECOES}`);
  const t0 = Date.now();
  const locais = lerLocais();
  const pol = lerSecoesPolitize();
  console.error(`politize: ${locais.size} locais, ${pol.size} seções (${((Date.now() - t0) / 1000).toFixed(1)} s)`);

  const listaLocais: [number, number][] = [];
  const idxLocal = new Map<string, number>();
  const indiceDe = (id: string | null): number => {
    if (id === null) return -1;
    const ja = idxLocal.get(id);
    if (ja !== undefined) return ja;
    const p = locais.get(id);
    if (!p) return -1;
    listaLocais.push([r4(p.lon), r4(p.lat)]);
    idxLocal.set(id, listaLocais.length - 1);
    return listaLocais.length - 1;
  };

  const db = new Database(DB_SECOES, { readonly: true, strict: true });
  const secoes: Record<string, Record<string, Record<string, (number | null)[][]>>> = {};
  const porMun = new Map<string, { comp: number[]; semBio: number[]; locais: Set<number> }>();
  let n = 0;
  let semPolitize = 0;
  // linha de base do encerramento no 1T: parcela de seções com hora (hh:mm) depois de 17:00, 18:00 e 19:00
  const encs: number[] = [];
  for (const r of db
    .query<BuRow, []>(
      "SELECT uf, mun, zona, secao, aptos, comparecimento, comp_sem_biometria, hab_ano_nascimento, encerramento FROM bu WHERE uf <> 'zz' AND id_confere = 1",
    )
    .iterate()) {
    n += 1;
    const k = `${r.uf}:${r.mun}:${r.zona}:${r.secao}`;
    const p = pol.get(k);
    if (!p) semPolitize += 1;
    const iso = horaLocalUrnaParaIso(r.uf, r.encerramento);
    const enc = iso === null ? null : minutosDesde17h(iso, T0_1T_MS);
    if (enc !== null) encs.push(Math.floor(enc));
    const li = indiceDe(p?.local ?? null);
    const linha = [r.secao, r.aptos, r.comparecimento, r.comp_sem_biometria, r.hab_ano_nascimento, enc === null ? null : Math.round(enc), li, p?.fl ?? null, p?.lu ?? null];
    const u = (secoes[r.uf] ??= {});
    const m = (u[r.mun] ??= {});
    (m[String(r.zona)] ??= []).push(linha);
    const km = `${r.uf}:${r.mun}`;
    let g = porMun.get(km);
    if (!g) {
      g = { comp: [], semBio: [], locais: new Set() };
      porMun.set(km, g);
    }
    if (r.aptos !== null && r.aptos > 0 && r.comparecimento !== null) g.comp.push((100 * r.comparecimento) / r.aptos);
    if (r.comparecimento !== null && r.comparecimento > 0 && r.comp_sem_biometria !== null) g.semBio.push((100 * r.comp_sem_biometria) / r.comparecimento);
    if (li >= 0) g.locais.add(li);
  }
  db.close();

  // centroide do município: média dos locais ponderada pelos aptos do local
  const aptosLocal = new Map<number, number>();
  for (const [id, i] of idxLocal) aptosLocal.set(i, locais.get(id)?.aptos ?? 0);
  const municipios: Record<string, Record<string, Record<string, number | null>>> = {};
  for (const [km, g] of porMun) {
    const [uf = "", mun = ""] = km.split(":");
    const comp = [...g.comp].sort((a, b) => a - b);
    const sb = [...g.semBio].sort((a, b) => a - b);
    let sw = 0;
    let sx = 0;
    let sy = 0;
    for (const i of g.locais) {
      const w = Math.max(1, aptosLocal.get(i) ?? 0);
      const c = listaLocais[i];
      if (!c) continue;
      sw += w;
      sx += w * c[0];
      sy += w * c[1];
    }
    const pc = (l: number[], p: number): number | null => {
      const v = percentil(l, p);
      return v === null ? null : r2(v);
    };
    (municipios[uf] ??= {})[mun] = {
      n: comp.length, comp_p50: pc(comp, 50), comp_p90: pc(comp, 90), sem_bio_p50: pc(sb, 50), sem_bio_p90: pc(sb, 90),
      lon: sw > 0 ? r4(sx / sw) : null, lat: sw > 0 ? r4(sy / sw) : null,
    };
  }

  const saida = argSaida();
  const doc = {
    meta: {
      gerado_em: new Date().toISOString(),
      turno: 1,
      fontes: ["data/secoes_2026.sqlite (bu)", "docs/assets/politize/dados/zona/*/*.json", "docs/assets/politize/dados/mun/*/*.json"],
      campos_secao: ["secao", "aptos1", "comp1", "sem_bio1", "ano_nasc1", "enc1_min", "local", "fl1", "lu1"],
      convencoes: {
        enc1_min: "minutos após 17:00 de Brasília de 04/10/2026 (último voto, hora local convertida pelo fuso da UF)",
        local: "índice em `locais` ([lon, lat] do local de votação no Politize); -1 sem coordenada",
        fl1_lu1: "votos de Flávio e Lula na seção principal no 1º turno (Politize)",
        municipios: "percentis por seção do município: comparecimento/aptos e sem biometria/comparecimento, em %",
      },
      n_secoes: n,
      enc_1t_pct: Object.fromEntries(
        [["apos_1700", 0], ["apos_1800", 60], ["apos_1900", 120]].map(([k, m]) => [k, encs.length === 0 ? null : r2((100 * encs.filter((x) => x >= Number(m) + 1).length) / encs.length)]),
      ),
      sem_politize: semPolitize,
      n_locais: listaLocais.length,
    },
    locais: listaLocais,
    secoes,
    municipios,
  };
  const tmp = `${saida}.tmp`;
  writeFileSync(tmp, JSON.stringify(doc));
  renameSync(tmp, saida);
  const mb = Buffer.byteLength(JSON.stringify(doc)) / 1e6;
  console.error(`${saida}: ${n} seções, ${semPolitize} sem Politize, ${listaLocais.length} locais, ${mb.toFixed(1)} MB, ${((Date.now() - t0) / 1000).toFixed(1)} s`);
}

main();
