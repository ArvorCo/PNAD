// Teste de aceitação por zona: a soma dos BUs das seções tem de reproduzir, voto a voto,
// o arquivo de resultado da zona (`-u.json` de abrangência zona) que o coletor gravou em
// data/apuracao.sqlite. Lê o JSON original do TSE (blob gzip da última versão não regressiva),
// não as tabelas normalizadas.
import type { Database } from "bun:sqlite";
import { intBR } from "../../src/parse/numeros.ts";
import { parseJson } from "../../src/parse/schemas.ts";
import type { ResultadoU } from "../../src/parse/schemas.ts";

export const TIPO = { nominal: 1, branco: 2, nulo: 3, legenda: 4 } as const;

export interface SomaSecoes {
  secoesCs: number;
  secoesBu: number;
  aptos: number;
  comparecimento: number;
  votos: ReadonlyArray<{ tipo: number; numero: number; votos: number }>;
}

export interface Divergencia {
  campo: string;
  secoes: number | null;
  zona: number | null;
}

export interface Conferencia {
  tsZona: number | null;
  stZona: number | null;
  aptosZona: number | null;
  comparecimentoZona: number | null;
  brancosBu: number;
  brancosZona: number | null;
  nulosBu: number;
  nulosZona: number | null;
  foraListaBu: number;
  nulosTecnicosZona: number | null;
  anuladosZona: number | null;
  legendaBu: number;
  legendaZona: number | null;
  nominaisBu: number;
  candidatos: number;
  candidatosDivergentes: number;
  divergencias: Divergencia[];
  ok: boolean;
}

/** Compara a soma das seções de um cargo com o arquivo de zona do mesmo cargo. */
export function conferir(soma: SomaSecoes, zona: ResultadoU): Conferencia {
  const div: Divergencia[] = [];
  const cmp = (campo: string, secoes: number, z: number | null): void => {
    if (z === null || secoes !== z) div.push({ campo, secoes, zona: z });
  };
  const porTipo = (tipo: number): number => soma.votos.filter((v) => v.tipo === tipo).reduce((s, v) => s + v.votos, 0);
  const nominal = new Map<number, number>();
  const legenda = new Map<number, number>();
  for (const v of soma.votos) {
    if (v.tipo === TIPO.nominal) nominal.set(v.numero, (nominal.get(v.numero) ?? 0) + v.votos);
    if (v.tipo === TIPO.legenda) legenda.set(v.numero, (legenda.get(v.numero) ?? 0) + v.votos);
  }
  const candidatos = new Map<number, number | null>();
  const legendaZona = new Map<number, number | null>();
  for (const c of zona.carg) {
    for (const a of c.agr ?? []) {
      for (const p of a.par ?? []) {
        // tval: votos de legenda apurados do partido, válidos ou não. tvtl só conta os
        // válidos e fica 0 em partido "Anulado sub judice", cuja legenda vai para vansj.
        const np = intBR(p.n);
        const tval = p.tval ?? p.tvtl;
        if (np !== null && tval !== undefined) legendaZona.set(np, intBR(tval));
        for (const cd of p.cand ?? []) {
          const n = intBR(cd.n);
          if (n !== null) candidatos.set(n, intBR(cd.vap));
        }
      }
    }
  }
  const aptosZona = intBR(zona.e?.te);
  const comparecimentoZona = intBR(zona.e?.c);
  cmp("aptos", soma.aptos, aptosZona);
  cmp("comparecimento", soma.comparecimento, comparecimentoZona);
  const brancosBu = porTipo(TIPO.branco);
  const brancosZona = intBR(zona.v?.vb);
  cmp("brancos", brancosBu, brancosZona);
  const nulosBu = porTipo(TIPO.nulo);
  const nulosZona = intBR(zona.v?.vn);
  cmp("nulos", nulosBu, nulosZona);
  let candidatosDivergentes = 0;
  for (const [n, vap] of candidatos) {
    const s = nominal.get(n) ?? 0;
    if (vap === null || s !== vap) {
      candidatosDivergentes += 1;
      div.push({ campo: `candidato:${n}`, secoes: s, zona: vap });
    }
  }
  // Nulo técnico (vnt): voto que a urna aceitou para número ausente da lista da zona, seja
  // nominal (candidato fora da disputa) ou de legenda (partido sem lista no cargo). Exemplo:
  // SE 31003/0015, deputado federal, vnt 5 = nominal 7777 (1) + legenda 25 (2) + legenda 77 (2).
  let foraListaBu = 0;
  for (const [n, s] of nominal) if (!candidatos.has(n)) foraListaBu += s;
  for (const [p, s] of legenda) if (!legendaZona.has(p)) foraListaBu += s;
  const nulosTecnicosZona = intBR(zona.v?.vnt);
  cmp("fora_da_lista=nulos_tecnicos", foraListaBu, nulosTecnicosZona);
  let legendaBu = 0;
  for (const [p, s] of legenda) if (legendaZona.has(p)) legendaBu += s;
  let legendaZonaTotal: number | null = 0;
  for (const t of legendaZona.values()) legendaZonaTotal = t === null || legendaZonaTotal === null ? null : legendaZonaTotal + t;
  if (legendaBu > 0 || (legendaZonaTotal ?? 0) > 0) cmp("legenda", legendaBu, legendaZonaTotal);
  for (const [p, tval] of legendaZona) {
    const s = legenda.get(p) ?? 0;
    if (tval === null || s !== tval) div.push({ campo: `legenda:${p}`, secoes: s, zona: tval });
  }
  const van = intBR(zona.v?.van);
  const vansj = intBR(zona.v?.vansj);
  return {
    tsZona: intBR(zona.s?.ts), stZona: intBR(zona.s?.st), aptosZona, comparecimentoZona,
    brancosBu, brancosZona, nulosBu, nulosZona, foraListaBu, nulosTecnicosZona,
    anuladosZona: van === null && vansj === null ? null : (van ?? 0) + (vansj ?? 0),
    legendaBu, legendaZona: legendaZonaTotal, nominaisBu: porTipo(TIPO.nominal),
    candidatos: candidatos.size, candidatosDivergentes, divergencias: div, ok: div.length === 0,
  };
}

export interface ZonaArquivo {
  chave: string;
  snapshotId: number;
  geradoEm: string | null;
  json: ResultadoU;
}

/** Última versão não regressiva do arquivo de zona, ou null. */
export function lerZona(apuracao: Database, chave: string): ZonaArquivo | null {
  const r = apuracao
    .query<{ id: number; gerado_em: string | null; gz: Uint8Array<ArrayBuffer> }, [string]>(
      `SELECT s.id, s.gerado_em, b.gz FROM arquivo a
       JOIN snapshot s ON s.arquivo_id = a.id AND s.regressivo = 0
       JOIN blob b ON b.sha256 = s.sha256
       WHERE a.chave = ? ORDER BY s.id DESC LIMIT 1`,
    )
    .get(chave);
  if (r === null) return null;
  const p = parseJson("u", JSON.parse(new TextDecoder().decode(Bun.gunzipSync(r.gz))));
  if (!p.ok || p.parsed.tipo !== "u") throw new Error(`${chave}: JSON de zona inválido (${p.ok ? "tipo" : p.erro})`);
  return { chave, snapshotId: r.id, geradoEm: r.gerado_em, json: p.parsed.data };
}

export const chaveZona = (eleicao: number, cargo: number, uf: string, mun: string, zona: number): string =>
  `u:${eleicao}:${cargo}:zona:${uf}:${mun}:${String(zona).padStart(4, "0")}`;

/** Confere todos os cargos de uma zona e grava em conferencia_zona. Devolve as linhas. */
export function conferirZona(
  secoes: Database,
  apuracao: Database,
  uf: string,
  mun: string,
  zona: number,
  agoraIso: string,
): Array<{ cargo: number; chave: string; ok: boolean | null; divergencias: Divergencia[] }> {
  const secoesCs = secoes.query<{ n: number }, [string, string, number]>("SELECT COUNT(*) AS n FROM secao WHERE uf = ? AND mun = ? AND zona = ?").get(uf, mun, zona)?.n ?? 0;
  const cargos = secoes
    .query<{ cargo: number; eleicao: number; n: number; aptos: number; comparecimento: number }, [string, string, number]>(
      `SELECT cargo, MIN(eleicao) AS eleicao, COUNT(*) AS n, SUM(aptos) AS aptos, SUM(comparecimento) AS comparecimento
       FROM bu_cargo WHERE uf = ? AND mun = ? AND zona = ? GROUP BY cargo ORDER BY cargo`,
    )
    .all(uf, mun, zona);
  const votosQ = secoes.query<{ tipo: number; numero: number; votos: number }, [string, string, number, number]>(
    "SELECT tipo, numero, SUM(votos) AS votos FROM voto_secao WHERE uf = ? AND mun = ? AND zona = ? AND cargo = ? GROUP BY tipo, numero",
  );
  const ins = secoes.prepare(`INSERT OR REPLACE INTO conferencia_zona (uf, mun, zona, cargo, chave, snapshot_id, gerado_em, secoes_cs, secoes_bu,
      ts_zona, st_zona, aptos_bu, aptos_zona, comparecimento_bu, comparecimento_zona, brancos_bu, brancos_zona, nulos_bu, nulos_zona,
      fora_lista_bu, nulos_tecnicos_zona, anulados_zona, legenda_bu, legenda_zona, nominais_bu, candidatos, candidatos_divergentes,
      divergencias, ok, conferido_em)
    VALUES (${Array.from({ length: 30 }, () => "?").join(", ")})`);
  const out: Array<{ cargo: number; chave: string; ok: boolean | null; divergencias: Divergencia[] }> = [];
  for (const c of cargos) {
    const chave = chaveZona(c.eleicao, c.cargo, uf, mun, zona);
    const z = lerZona(apuracao, chave);
    const soma: SomaSecoes = { secoesCs, secoesBu: c.n, aptos: c.aptos, comparecimento: c.comparecimento, votos: votosQ.all(uf, mun, zona, c.cargo) };
    if (z === null) {
      ins.run(uf, mun, zona, c.cargo, chave, null, null, secoesCs, c.n, null, null, c.aptos, null, c.comparecimento, null,
        null, null, null, null, null, null, null, null, null, null, null, null, JSON.stringify([{ campo: "sem_arquivo_de_zona", secoes: null, zona: null }]), null, agoraIso);
      out.push({ cargo: c.cargo, chave, ok: null, divergencias: [] });
      continue;
    }
    const r = conferir(soma, z.json);
    ins.run(uf, mun, zona, c.cargo, chave, z.snapshotId, z.geradoEm, secoesCs, c.n, r.tsZona, r.stZona, c.aptos, r.aptosZona,
      c.comparecimento, r.comparecimentoZona, r.brancosBu, r.brancosZona, r.nulosBu, r.nulosZona, r.foraListaBu, r.nulosTecnicosZona,
      r.anuladosZona, r.legendaBu, r.legendaZona, r.nominaisBu, r.candidatos, r.candidatosDivergentes,
      r.divergencias.length === 0 ? null : JSON.stringify(r.divergencias), r.ok ? 1 : 0, agoraIso);
    out.push({ cargo: c.cargo, chave, ok: r.ok, divergencias: r.divergencias });
  }
  return out;
}
