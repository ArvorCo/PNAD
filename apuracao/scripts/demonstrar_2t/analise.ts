// Leitura do banco gerado pelo replay (parte a) e comparação com a régua publicada no dossiê do
// 1º turno (../analysis/apuracao_2026/dados/linha_do_tempo.json, gerado por
// ../scripts/apuracao-2026-dados.py a partir do mesmo banco). Tudo aqui é leitura.
import type { Database } from "bun:sqlite";
import { readFileSync } from "node:fs";
import { minutoQuePassou } from "../../src/collector/regua.ts";
import { municipiosIndex } from "../../src/server/consultas.ts";
import { textoEvento } from "../../src/server/textos.ts";
import { hhmmDeMinutos, minutosDesde17h, T0_1T_MS } from "../../src/turno2/comum.ts";
import type { Referencia1T } from "../../src/turno2/referencia.ts";
import { ELE_1T, isoBrt } from "./replay.ts";

// ---------------------------------------------------------------- régua do dossiê

export type NivelPausa = "nacional" | "geral" | "uf";

export interface IntervaloRegua {
  fonte: string;
  nivel: NivelPausa;
  /** sigla minúscula na régua de UF */
  uf: string | null;
  de: string;
  ate: string;
  minutos: number;
}

export interface ReguaDossie {
  arquivo: string;
  limiar_min: number;
  regra: string;
  intervalos: IntervaloRegua[];
  conclusao_ufs: ConclusaoUf[];
}

export interface ConclusaoUf {
  uf: string;
  gerado_brt: string;
  capturado_brt: string;
  /** minutos que a regra de versão do coletor do 1º turno atrasou o fechamento (dossiê) */
  atraso_da_regra_do_coletor_min: number;
}

interface Lacuna {
  arquivo?: string;
  de: string;
  ate: string;
  minutos: number;
}

interface LinhaDoTempo {
  travamentos: { limiar_min: number; regra: string; nacional: Lacuna[]; ufs: Lacuna[]; todas_as_ufs_sem_versao_nova: Lacuna[] };
  pausa_geral: { lacunas: Lacuna[] };
  conclusao_ufs: ConclusaoUf[];
}

export function lerReguaDossie(path: string): ReguaDossie {
  const d = JSON.parse(readFileSync(path, "utf8")) as LinhaDoTempo;
  const t = d.travamentos;
  const de = (fonte: string, nivel: NivelPausa, l: readonly Lacuna[]): IntervaloRegua[] =>
    l.map((x) => ({ fonte, nivel, uf: nivel === "uf" ? (x.arquivo ?? "").toLowerCase() : null, de: x.de, ate: x.ate, minutos: x.minutos }));
  return {
    arquivo: path,
    limiar_min: t.limiar_min,
    regra: t.regra,
    intervalos: [
      ...de("travamentos.nacional", "nacional", t.nacional),
      ...de("pausa_geral.lacunas", "geral", d.pausa_geral.lacunas),
      ...de("travamentos.todas_as_ufs_sem_versao_nova", "geral", t.todas_as_ufs_sem_versao_nova),
      ...de("travamentos.ufs", "uf", t.ufs),
    ],
    conclusao_ufs: d.conclusao_ufs,
  };
}

/** Os três marcos citados no pedido, conferidos contra a régua (não digitados como verdade). */
export const MARCOS_PEDIDO: readonly { nome: string; nivel: NivelPausa; de_brt: string; ate_brt: string }[] = [
  { nome: "travamento nacional", nivel: "nacional", de_brt: "2026-10-04 18:00:33", ate_brt: "2026-10-04 18:10:48" },
  { nome: "parada do arquivo nacional", nivel: "nacional", de_brt: "2026-10-04 18:48:59", ate_brt: "2026-10-04 19:14:08" },
  { nome: "pausa geral", nivel: "geral", de_brt: "2026-10-04 19:32:47", ate_brt: "2026-10-04 20:01:55" },
];

const ms = (iso: string): number => Date.parse(iso);
const sobreposicao = (a0: number, a1: number, b0: number, b1: number): number => Math.max(0, Math.min(a1, b1) - Math.max(a0, b0));
const min1 = (x: number): number => Math.round(x / 6000) / 10;

// ---------------------------------------------------------------- pausas detectadas

export interface PausaDetectada {
  nivel: NivelPausa;
  uf: string | null;
  de: string;
  ate: string | null;
  minutos: number | null;
  st_antes: number | null;
  st_depois: number | null;
  detectado_em: string;
  /** lacuna da régua do mesmo nível com maior sobreposição */
  regua: (IntervaloRegua & { dif_de_s: number; dif_ate_s: number }) | null;
  classe: "na_regua" | "abaixo_da_regua";
}

const COMPATIVEL: Readonly<Record<NivelPausa, readonly NivelPausa[]>> = { nacional: ["nacional"], geral: ["geral"], uf: ["uf"] };

export function pausasDetectadas(db: Database, regua: ReguaDossie): PausaDetectada[] {
  type L = Omit<PausaDetectada, "regua" | "classe">;
  return db
    .query<L, []>("SELECT nivel, uf, de, ate, minutos, st_antes, st_depois, detectado_em FROM pausa ORDER BY de, nivel")
    .all()
    .map((p) => {
      const a0 = ms(p.de);
      const a1 = p.ate === null ? a0 : ms(p.ate);
      let melhor: PausaDetectada["regua"] = null;
      let sob = 0;
      for (const r of regua.intervalos) {
        if (!COMPATIVEL[p.nivel].includes(r.nivel) || (p.nivel === "uf" && r.uf !== p.uf)) continue;
        const s = sobreposicao(a0, a1, ms(r.de), ms(r.ate));
        if (s > sob) {
          sob = s;
          melhor = { ...r, dif_de_s: Math.round((a0 - ms(r.de)) / 1000), dif_ate_s: Math.round((a1 - ms(r.ate)) / 1000) };
        }
      }
      return { ...p, regua: melhor, classe: melhor === null ? "abaixo_da_regua" : "na_regua" };
    });
}

export interface CoberturaMarco {
  nome: string;
  nivel: NivelPausa;
  de_brt: string;
  ate_brt: string;
  na_regua: boolean;
  minutos: number;
  /** pausas do motor (qualquer nível) que cobrem o intervalo */
  pausas: { nivel: NivelPausa; uf: string | null; de_brt: string; ate_brt: string; minutos: number | null }[];
  coberto_min: number;
  /** trechos do intervalo sem pausa do motor (ISO) */
  descobertos: { de: string; ate: string }[];
  mesmo_nivel: boolean;
}

/** Cada intervalo nacional e geral da régua contra as pausas do motor (todas as que tocam nele). */
export function coberturaDaRegua(pausas: readonly PausaDetectada[], regua: ReguaDossie): CoberturaMarco[] {
  const brtIso = (brt: string): number => Date.parse(`${brt.replace(" ", "T")}.000-03:00`);
  const alvos = [
    ...MARCOS_PEDIDO.map((m) => ({ ...m, a0: brtIso(m.de_brt), a1: brtIso(m.ate_brt) })),
    ...regua.intervalos
      .filter((r) => r.fonte === "travamentos.nacional" || r.fonte === "travamentos.todas_as_ufs_sem_versao_nova")
      .map((r) => ({
        nome: r.fonte === "travamentos.nacional" ? "arquivo nacional sem versão nova" : "nenhuma UF com versão nova", nivel: r.nivel,
        de_brt: isoBrt(r.de), ate_brt: isoBrt(r.ate), a0: ms(r.de), a1: ms(r.ate),
      })),
  ];
  const vistos = new Set<string>();
  const out: CoberturaMarco[] = [];
  for (const a of alvos) {
    const k = `${a.nivel}|${a.a0}|${a.a1}`;
    if (vistos.has(k)) continue;
    vistos.add(k);
    const toca = pausas.filter((p) => p.nivel !== "uf" && sobreposicao(a.a0, a.a1, ms(p.de), p.ate === null ? ms(p.de) : ms(p.ate)) > 0);
    const iv = toca.map((p) => [ms(p.de), p.ate === null ? ms(p.de) : ms(p.ate)] as const);
    const coberto = uniaoSobre(a.a0, a.a1, iv);
    out.push({
      nome: a.nome, nivel: a.nivel, de_brt: a.de_brt, ate_brt: a.ate_brt, minutos: min1(a.a1 - a.a0),
      na_regua: regua.intervalos.some((r) => r.nivel === a.nivel && Math.abs(ms(r.de) - a.a0) < 1000 && Math.abs(ms(r.ate) - a.a1) < 1000),
      pausas: toca.map((p) => ({ nivel: p.nivel, uf: p.uf, de_brt: isoBrt(p.de), ate_brt: isoBrt(p.ate), minutos: p.minutos })),
      coberto_min: min1(coberto), descobertos: lacunas(a.a0, a.a1, iv), mesmo_nivel: toca.some((p) => p.nivel === a.nivel),
    });
  }
  return out.sort((x, y) => (x.de_brt < y.de_brt ? -1 : x.de_brt > y.de_brt ? 1 : x.nivel < y.nivel ? -1 : 1));
}

/** Trechos de [a0, a1] fora de todos os intervalos. */
function lacunas(a0: number, a1: number, iv: readonly (readonly [number, number])[]): { de: string; ate: string }[] {
  const out: { de: string; ate: string }[] = [];
  let t = a0;
  for (const [b0, b1] of [...iv].sort((x, y) => x[0] - y[0])) {
    if (b0 > t) out.push({ de: new Date(t).toISOString(), ate: new Date(Math.min(b0, a1)).toISOString() });
    t = Math.max(t, b1);
    if (t >= a1) break;
  }
  if (t < a1) out.push({ de: new Date(t).toISOString(), ate: new Date(a1).toISOString() });
  return out.filter((x) => Date.parse(x.ate) > Date.parse(x.de));
}

function uniaoSobre(a0: number, a1: number, iv: readonly (readonly [number, number])[]): number {
  const cortes = iv.map(([b0, b1]) => [Math.max(a0, b0), Math.min(a1, b1)] as const).filter(([b0, b1]) => b1 > b0).sort((x, y) => x[0] - y[0]);
  let total = 0;
  let fim = Number.NEGATIVE_INFINITY;
  for (const [b0, b1] of cortes) {
    const ini = Math.max(b0, fim);
    if (b1 > ini) total += b1 - ini;
    fim = Math.max(fim, b1);
  }
  return total;
}

// ---------------------------------------------------------------- eventos com o texto do telão

export interface EventoLido {
  id: number;
  em: string;
  em_brt: string;
  tipo: string;
  severidade: string;
  nivel: string | null;
  uf: string | null;
  municipio_cd: string | null;
  detalhe: Record<string, unknown>;
  texto: string;
}

export function eventos(db: Database, tipos: readonly string[]): EventoLido[] {
  const muns = municipiosIndex(db);
  type R = { id: number; em: string; tipo: string; severidade: string; nivel: string | null; uf: string | null; municipio_cd: string | null; zona_cd: string | null; cargo_cd: number | null; detalhe: string | null };
  return db
    .query<R, []>(
      `SELECT id, em, tipo, severidade, nivel, uf, municipio_cd, zona_cd, cargo_cd, detalhe FROM evento
       WHERE tipo IN (${tipos.map((t) => `'${t}'`).join(", ")}) ORDER BY em, id`,
    )
    .all()
    .map((r) => {
      const detalhe = (r.detalhe === null ? {} : JSON.parse(r.detalhe)) as Record<string, unknown>;
      return {
        id: r.id, em: r.em, em_brt: isoBrt(r.em), tipo: r.tipo, severidade: r.severidade, nivel: r.nivel, uf: r.uf, municipio_cd: r.municipio_cd, detalhe,
        texto: textoEvento(r.tipo, r.em, r, detalhe, muns),
      };
    });
}

export function contagemPorTipo(db: Database): Record<string, number> {
  const out: Record<string, number> = {};
  for (const r of db.query<{ tipo: string; n: number }, []>("SELECT tipo, COUNT(*) AS n FROM evento GROUP BY tipo ORDER BY tipo").all()) out[r.tipo] = r.n;
  return out;
}

// ---------------------------------------------------------------- viradas: consistência

export interface LiderUf {
  uf: string;
  primeiro: string | null;
  final: string | null;
  viradas: number;
  coerente: boolean;
}

/**
 * Líder (maior vap, sem empate) na primeira versão com voto e na última, por arquivo de UF.
 * Com a lista de viradas completa, líder inicial seguido das viradas termina no líder final.
 */
export function coerenciaViradas(db: Database, viradas: readonly EventoLido[]): LiderUf[] {
  type R = { uf: string; sid: number; nome: string | null; vap: number };
  const linhas = db
    .query<R, [number]>(
      `SELECT a.uf, s.id AS sid, c.nome_urna AS nome, vc.vap FROM arquivo a JOIN snapshot s ON s.arquivo_id = a.id AND s.regressivo = 0
       JOIN voto_candidato vc ON vc.snapshot_id = s.id LEFT JOIN candidato c ON c.sqcand = vc.sqcand
       WHERE a.tipo = 'u' AND a.eleicao_cd = ? AND a.cargo_cd = 1 AND a.nivel = 'uf' AND vc.vap > 0 ORDER BY a.uf, s.id`,
    )
    .all(ELE_1T);
  const porUf = new Map<string, Map<number, { nome: string | null; vap: number }[]>>();
  for (const l of linhas) {
    const m = porUf.get(l.uf) ?? new Map<number, { nome: string | null; vap: number }[]>();
    porUf.set(l.uf, m);
    const v = m.get(l.sid) ?? [];
    m.set(l.sid, v);
    v.push({ nome: l.nome, vap: l.vap });
  }
  const lider = (v: readonly { nome: string | null; vap: number }[]): string | null => {
    const o = [...v].sort((a, b) => b.vap - a.vap);
    const a = o[0];
    const b = o[1];
    return a === undefined || (b !== undefined && b.vap === a.vap) ? null : a.nome;
  };
  const out: LiderUf[] = [];
  for (const [uf, m] of [...porUf].sort((x, y) => (x[0] < y[0] ? -1 : 1))) {
    const sids = [...m.keys()].sort((a, b) => a - b);
    const primeiro = lider(m.get(sids[0] ?? -1) ?? []);
    const final = lider(m.get(sids.at(-1) ?? -1) ?? []);
    const n = viradas.filter((v) => v.uf === uf).length;
    out.push({ uf, primeiro, final, viradas: n, coerente: (primeiro === final) === (n % 2 === 0) });
  }
  return out;
}

// ---------------------------------------------------------------- régua: alertas residuais

export interface AtrasoExplicado {
  em_brt: string;
  uf: string;
  patamar_min: number;
  pst_2t: number;
  st_2t: number;
  /** ponto da curva do 1º turno que passou do pst da UF */
  regua_min: number | null;
  regua_hhmm: string | null;
  regua_st: number | null;
  /** primeira versão do 1º turno (por gerado_em) com pelo menos aquele st */
  versao_gerada_brt: string | null;
  versao_totalizada_brt: string | null;
  adiantamento_min: number | null;
}

export function explicarAtrasos(db1t: Database, ref: Referencia1T, atrasos: readonly EventoLido[]): AtrasoExplicado[] {
  const q = db1t.query<{ gerado_em: string | null; totalizado_em: string | null }, [string, number]>(
    `SELECT s.gerado_em, s.totalizado_em FROM arquivo a JOIN snapshot s ON s.arquivo_id = a.id JOIN totais t ON t.snapshot_id = s.id
     WHERE a.tipo = 'u' AND a.eleicao_cd = ${ELE_1T} AND a.cargo_cd = 1 AND a.nivel = 'uf' AND a.uf = ? AND t.st >= ? AND s.gerado_em IS NOT NULL
     ORDER BY s.gerado_em LIMIT 1`,
  );
  return atrasos.map((e) => {
    const uf = e.uf ?? "";
    // o detalhe guarda o pst com duas casas; a régua comparou o valor exato, st / ts
    const st = Number(e.detalhe.st);
    const pst = (100 * st) / Number(e.detalhe.ts);
    const curva = ref.curvas.uf[uf.toUpperCase()] ?? [];
    const m = minutoQuePassou(curva, pst);
    const ponto = m === null ? undefined : curva.find((p) => p[0] === m && p[1] > pst);
    const v = ponto === undefined ? null : q.get(uf, ponto[2]);
    const gerado = v?.gerado_em ?? null;
    const regMin = m;
    const gMin = gerado === null ? null : minutosDesde17h(gerado, T0_1T_MS);
    return {
      em_brt: e.em_brt, uf, patamar_min: Number(e.detalhe.patamar_min), pst_2t: Math.round(pst * 1000) / 1000, st_2t: st,
      regua_min: regMin, regua_hhmm: regMin === null ? null : hhmmDeMinutos(regMin), regua_st: ponto?.[2] ?? null,
      versao_gerada_brt: isoBrt(gerado) || null, versao_totalizada_brt: isoBrt(v?.totalizado_em ?? null) || null,
      adiantamento_min: regMin === null || gMin === null ? null : Math.round((gMin - regMin) * 10) / 10,
    };
  });
}

// ---------------------------------------------------------------- abstenção: por que zero

export interface ConferenciaAbstencao {
  municipios_fechados: number;
  fechados_te_20mil: number;
  com_referencia: number;
  max_delta_pp: number;
  ufs: number;
}

export function conferirAbstencao(db: Database, ref: Referencia1T): ConferenciaAbstencao {
  type R = { uf: string; cdabr: string; ts: number | null; st: number | null; te: number | null; c: number | null; a: number | null };
  const linhas = db
    .query<R, [number]>(
      `SELECT uf_arquivo AS uf, cdabr, ts, st, te, comparecimento AS c, abstencao AS a FROM v_ab_atual
       WHERE eleicao_cd = ? AND nivel = 'uf' AND tpabr <> 'uf'`,
    )
    .all(ELE_1T);
  let fechados = 0;
  let grandes = 0;
  let comRef = 0;
  let max = 0;
  const ufs = new Set<string>();
  for (const l of linhas) {
    if ((l.ts ?? 0) <= 0 || l.st !== l.ts) continue;
    fechados += 1;
    if ((l.te ?? 0) >= 20_000) grandes += 1;
    const r1 = ref.municipios[l.uf.toUpperCase()]?.[l.cdabr];
    const c = l.c ?? 0;
    const a = l.a ?? 0;
    if (!r1 || c + a <= 0) continue;
    comRef += 1;
    ufs.add(l.uf);
    max = Math.max(max, Math.abs((100 * a) / (c + a) - r1.pa));
  }
  return { municipios_fechados: fechados, fechados_te_20mil: grandes, com_referencia: comRef, max_delta_pp: Math.round(max * 1000) / 1000, ufs: ufs.size };
}

// ---------------------------------------------------------------- regra de versão

export interface RegraVersao {
  /** flags gravadas pelo coletor do 1º turno (regra anterior, idg) */
  anterior: { aceitas: number; regressivas: number };
  /** replay com a regra corrigida (gerado_em) */
  atual: { aceitas: number; regressivas: number };
  /** versões que a regra anterior descartou e a atual aceita (mesmo arquivo, corpo e captura) */
  recuperadas: number;
  /** versões aceitas pela regra atual com st menor que a aceita anterior do mesmo arquivo */
  st_regrediu: number;
}

export function regraVersao(db1t: Database, db: Database): RegraVersao {
  const where = `a.tipo = 'u' AND a.eleicao_cd = ${ELE_1T} AND a.cargo_cd = 1 AND a.nivel IN ('br', 'uf')`;
  const contar = (d: Database): { aceitas: number; regressivas: number } =>
    d
      .query<{ aceitas: number; regressivas: number }, []>(
        `SELECT COALESCE(SUM(s.regressivo = 0), 0) AS aceitas, COALESCE(SUM(s.regressivo = 1), 0) AS regressivas
         FROM snapshot s JOIN arquivo a ON a.id = s.arquivo_id WHERE ${where}`,
      )
      .get() ?? { aceitas: 0, regressivas: 0 };
  const chave = (r: { chave: string; sha256: string; capturado_em: string }): string => `${r.chave}|${r.sha256}|${r.capturado_em}`;
  type K = { chave: string; sha256: string; capturado_em: string };
  const descartadas = new Set(
    db1t.query<K, []>(`SELECT a.chave, s.sha256, s.capturado_em FROM snapshot s JOIN arquivo a ON a.id = s.arquivo_id WHERE ${where} AND s.regressivo = 1`).all().map(chave),
  );
  let recuperadas = 0;
  for (const r of db.query<K, []>(`SELECT a.chave, s.sha256, s.capturado_em FROM snapshot s JOIN arquivo a ON a.id = s.arquivo_id WHERE ${where} AND s.regressivo = 0`).all()) {
    if (descartadas.has(chave(r))) recuperadas += 1;
  }
  let stRegrediu = 0;
  const ultimo = new Map<string, number>();
  for (const r of db
    .query<{ chave: string; st: number | null }, []>(
      `SELECT a.chave, t.st FROM snapshot s JOIN arquivo a ON a.id = s.arquivo_id JOIN totais t ON t.snapshot_id = s.id WHERE ${where} AND s.regressivo = 0 ORDER BY s.id`,
    )
    .all()) {
    const ant = ultimo.get(r.chave);
    if (ant !== undefined && r.st !== null && r.st < ant) stRegrediu += 1;
    if (r.st !== null) ultimo.set(r.chave, r.st);
  }
  return { anterior: contar(db1t), atual: contar(db), recuperadas, st_regrediu: stRegrediu };
}

// ---------------------------------------------------------------- critério "o país publica"

export interface IdadeUfs {
  em_brt: string;
  mediana_min: number | null;
  ufs: number;
}

/**
 * Idade mediana da última versão das UFs (gerado_em até o instante), a cada 30 s, como o
 * detector calcula para decidir se "o país publica" (src/collector/pausas.ts, idadeMedianaUfs).
 */
export function idadeMedianaUfs(db: Database, de: string, ate: string): IdadeUfs[] {
  const versoes = db
    .query<{ uf: string; g: string }, [number]>(
      `SELECT a.uf, s.gerado_em AS g FROM snapshot s JOIN arquivo a ON a.id = s.arquivo_id
       WHERE a.tipo = 'u' AND a.eleicao_cd = ? AND a.cargo_cd = 1 AND a.nivel = 'uf' AND s.regressivo = 0 AND s.gerado_em IS NOT NULL ORDER BY s.gerado_em`,
    )
    .all(ELE_1T);
  const porUf = new Map<string, number[]>();
  for (const v of versoes) {
    const l = porUf.get(v.uf) ?? [];
    porUf.set(v.uf, l);
    l.push(ms(v.g));
  }
  const out: IdadeUfs[] = [];
  for (let t = ms(de); t <= ms(ate); t += 30_000) {
    const idades: number[] = [];
    for (const l of porUf.values()) {
      let g: number | null = null;
      for (const x of l) {
        if (x > t) break;
        g = x;
      }
      if (g !== null) idades.push(t - g);
    }
    idades.sort((a, b) => a - b);
    const m = idades[Math.floor((idades.length - 1) / 2)];
    out.push({ em_brt: isoBrt(new Date(t).toISOString()), mediana_min: m === undefined ? null : min1(m), ufs: idades.length });
  }
  return out;
}

// ---------------------------------------------------------------- exemplo da regra de versão

export interface ExemploVersao {
  uf: string;
  gerado_brt: string;
  capturado_brt: string;
  pst: number;
  idg: number;
  /** versão que a regra anterior manteve como atual */
  idg_atual: number;
  gerado_atual_brt: string;
  pst_atual: number;
  /** captura da versão seguinte que a regra anterior aceitou */
  volta_brt: string;
  parado_min: number;
}

/**
 * Versão de UF descartada pela regra anterior (flag do banco do 1º turno) com geração posterior à
 * versão mantida como atual, com a UF ainda abaixo de 99% das seções; devolve a que deixou o
 * arquivo parado por mais tempo.
 */
export function exemploRecuperada(db1t: Database): ExemploVersao | null {
  type R = { uf: string; cap: string; ger: string | null; idg: number | null; reg: number; pst: number | null };
  const rows = db1t
    .query<R, [number]>(
      `SELECT a.uf, s.capturado_em AS cap, s.gerado_em AS ger, s.idg, s.regressivo AS reg, t.pst FROM snapshot s
       JOIN arquivo a ON a.id = s.arquivo_id JOIN totais t ON t.snapshot_id = s.id
       WHERE a.tipo = 'u' AND a.eleicao_cd = ? AND a.cargo_cd = 1 AND a.nivel = 'uf' ORDER BY s.capturado_em, s.id`,
    )
    .all(ELE_1T);
  const atual = new Map<string, R>();
  const esperando = new Map<string, { r: R; atual: R }>();
  let melhor: ExemploVersao | null = null;
  for (const r of rows) {
    const a = atual.get(r.uf);
    if (r.reg === 0) {
      const e = esperando.get(r.uf);
      if (e && e.r.ger !== null && e.atual.ger !== null && e.r.idg !== null && e.atual.idg !== null) {
        const parado = min1(ms(r.cap) - ms(e.r.cap));
        if (melhor === null || parado > melhor.parado_min) {
          melhor = {
            uf: r.uf, gerado_brt: isoBrt(e.r.ger), capturado_brt: isoBrt(e.r.cap), pst: Math.round((e.r.pst ?? 0) * 100) / 100, idg: e.r.idg,
            idg_atual: e.atual.idg, gerado_atual_brt: isoBrt(e.atual.ger), pst_atual: Math.round((e.atual.pst ?? 0) * 100) / 100, volta_brt: isoBrt(r.cap), parado_min: parado,
          };
        }
      }
      esperando.delete(r.uf);
      atual.set(r.uf, r);
    } else if (a && r.ger !== null && a.ger !== null && r.ger > a.ger && (a.pst ?? 100) < 99 && !esperando.has(r.uf)) {
      esperando.set(r.uf, { r, atual: a });
    }
  }
  return melhor;
}

/** Seções na última versão (gerada até `iso`) do arquivo nacional e na soma dos arquivos de UF. */
export function secoesEm(db: Database, iso: string): { nacional: number; soma_ufs: number } {
  type R = { nivel: string; st: number | null };
  const rows = db
    .query<R, [number, string]>(
      `SELECT a.nivel, (SELECT t.st FROM snapshot s JOIN totais t ON t.snapshot_id = s.id
                        WHERE s.arquivo_id = a.id AND s.regressivo = 0 AND s.gerado_em <= ?2 ORDER BY s.gerado_em DESC LIMIT 1) AS st
       FROM arquivo a WHERE a.tipo = 'u' AND a.eleicao_cd = ?1 AND a.cargo_cd = 1 AND a.nivel IN ('br', 'uf')`,
    )
    .all(ELE_1T, iso);
  let nacional = 0;
  let soma = 0;
  for (const r of rows) {
    if (r.nivel === "br") nacional = r.st ?? 0;
    else soma += r.st ?? 0;
  }
  return { nacional, soma_ufs: soma };
}
