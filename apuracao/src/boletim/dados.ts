// Resumo compacto das rotas locais do 2º turno para o roteiro do boletim, mais o delta desde o
// boletim anterior (calculado aqui, pela base gravada em cada HHMM.dados.json). Só lê a API local
// e, uma vez, o resultado final do 1º turno no banco do 1T (só leitura). Nenhum número inventado:
// tudo o que o roteiro pode dizer está neste JSON.
import { Database } from "bun:sqlite";
import { existsSync } from "node:fs";
import { join } from "node:path";
import { RAIZ_APURACAO, horaBrt } from "./estado.ts";
import type { Modo } from "./estado.ts";

type Num = number;

interface Cand { sqcand: string; n: string; nmu: string; sg: string; vap: Num; pvapn: Num; e?: boolean; campo?: string }
interface Resultado {
  s: { ts: Num; st: Num; pst: Num };
  e: { te: Num; c: Num; a: Num };
  v: { tv: Num; vv: Num; vb: Num };
  dt_ht: string | null;
  dg_hg: string | null;
  cand: Cand[];
  fonte?: string;
  nacional_tse?: { hg: string | null; st: Num; pst: Num } | null;
}
interface Estado { agora: string; turno: number; br: { ts: Num; st: Num; pst: Num; dt_ht: string | null; hg: string | null } | null }
interface Ref1t { pst_mesmo_relogio: Num | null; atraso_min: Num | null; pa_final_1t?: Num | null; p100_min?: Num | null; pa_final?: Num | null }
interface Agregado {
  sigla: string; nome: string; ts: Num; st: Num; pst: Num; comparecimento: Num; abstencao: Num; pa: Num;
  votos: Record<string, { vap: Num; pvapn: Num }>; vv: Num; vb: Num; tv: Num; lider: string | null; margem_pp: Num;
  vel_10min_spm: Num; eta_100_iso: string | null; ref_1t: Ref1t | null;
}
interface Regioes { min: Num; brasil: Agregado; regioes: Agregado[] }
interface UfLinha {
  uf: string; nome: string; regiao: string; ts: Num; st: Num; pst: Num; pa: Num; munnr: Num; munpt: Num; munf: Num;
  votos: Record<string, { vap: Num; pvapn: Num }>; lider: string | null; margem_pp: Num; idade_s: Num | null;
  vel_10min_spm: Num; eta_100_iso: string | null; parada: boolean; ref_1t: Ref1t | null; pendentes_maiores: { nm: string; te: Num; pst: Num }[];
}
interface Ufs { limiar_parada_min: Num; ufs: UfLinha[] }
interface Bloco { n_mun_fechados: Num; te_fechado: Num; pct_te_fechado: Num; pa_2t: Num | null; pa_1t_mesmos: Num | null; delta_pp: Num | null; sigla?: string; uf?: string; nome: string }
interface MunAbs { uf: string; nm: string; te: Num; pa_2t: Num; pa_1t: Num; delta_pp: Num }
interface Abstencao { brasil: Bloco; regioes: Bloco[]; ufs: Bloco[]; destaques: { subiu: MunAbs[]; caiu: MunAbs[] } }
interface Estadual {
  uf: string; nome: string; ts: Num; st: Num; pst: Num; pa: Num; cand: { sqcand: string; n: string; nome_urna: string; partido: string; vap: Num; pvapn: Num; campo?: string }[];
  lider: string | null; margem_pp: Num; viradas: { at: string; de: string; para: string }[]; ref_1t: Ref1t | null; pa_final_1t: Num | null;
}
interface Estaduais { ufs: Estadual[] }
interface Pausas {
  limiar_min: Num;
  nacional: { em_pausa: boolean; pausa_atual: { desde: string; minutos: Num } | null; historico: { de: string; ate: string | null; minutos: Num }[]; idade_s: Num | null };
  soma_ufs: { st: Num; pst: Num; defasagem_secoes: Num; defasagem_min: Num };
  ufs: { uf: string; em_pausa: boolean; idade_s: Num | null; historico_n: Num; st: Num; ts: Num }[];
}
interface Paralela {
  erro: string | null; atualizado_em: string | null;
  recebidos: { bus: Num; envios: Num; secoes: Num; ufs: Num; conflitos: Num };
  conferencia: { iguais: Num; divergentes: Num; tse_ainda_nao_publicou: Num; erro: Num; fora_do_oficial: Num; pendentes: Num };
  placar_bus: { presidente: { votos: Record<string, Num>; comparecimento: Num; brancos: Num; nulos: Num; secoes: Num } };
  divergencias: { uf: string; mun: string; zona: string; secao: string; campos: { campo: string }[] }[];
}
interface Secoes {
  totais: { alvo: Num; recebidas: Num; pendentes: Num; tardias: Num };
  brasil: { encerramento_p50_hhmm: string | null; encerramento_p90_hhmm: string | null; lag_encerr_recebimento_min: { p50: Num | null; p90: Num | null }; ref_1t: { lag_p50: Num | null; lag_p90: Num | null } | null };
}
interface Anomalia { at: string; tipo: string; tipo_bruto?: string; categoria: string; severidade: string; uf?: string | null; texto: string }
interface Lote { at: string; d_st: Num; d_vv: Num; cand: Record<string, { vap: Num; d_vap: Num }> }
interface Lotes { lotes: Lote[] }

/** Base gravada em cada boletim para o delta do seguinte. */
export interface Base {
  at: string;
  st: Num;
  ts: Num;
  pst: Num;
  vv: Num;
  votos: Record<string, Num>;
  diferenca_pp: Num | null;
  diferenca_votos: Num | null;
  lideres_uf: Record<string, string>;
  ufs_fechadas: string[];
  pausa_nacional: boolean;
  pausas_nacionais_n: Num;
  ufs_em_pausa: string[];
  divergentes: Num;
  lideres_gov: Record<string, string>;
}

export interface Resumo {
  hora_brt: string;
  agora_iso: string;
  relogio_min: Num;
  modo: Modo;
  motivos_modo: string[];
  [k: string]: unknown;
}

export interface SaidaDados {
  resumo: Resumo;
  base: Base;
  linha: string;
}

const r1 = (x: Num): Num => Math.round(x * 10) / 10;
const r2 = (x: Num): Num => Math.round(x * 100) / 100;
const brt = (iso: string | null | undefined): string | null => (iso ? horaBrt(iso) : null);
const pctBr = (x: Num, casas = 1): string => x.toLocaleString("pt-BR", { minimumFractionDigits: casas, maximumFractionDigits: casas });

const NOMES: Readonly<Record<string, string>> = { "FLAVIO BOLSONARO": "Flávio Bolsonaro", LULA: "Lula" };
/** Nome falado: mapa dos dois finalistas; o resto em caixa de título, sem inventar acento. */
export function nomeFalado(nmu: string): string {
  const k = nmu.trim().toUpperCase();
  return NOMES[k] ?? k.toLowerCase().replace(/(^|[\s-])(\p{L})/gu, (_m, a: string, b: string) => a + b.toUpperCase());
}

/** Resultado final do presidente no 1º turno (data/apuracao.sqlite, só leitura). */
export interface Final1T { brancos_pct: Num; nulos_pct: Num; comparecimento_pct: Num; abstencao_pct: Num; fonte: string }
let final1tCache: Final1T | null | undefined;
export function final1T(path = join(RAIZ_APURACAO, "data/apuracao.sqlite")): Final1T | null {
  if (final1tCache !== undefined) return final1tCache;
  final1tCache = null;
  if (!existsSync(path)) return null;
  let db: Database | null = null;
  try {
    db = new Database(path, { readonly: true });
    const t = db
      .query<{ tv: Num; vv: Num; vb: Num; comparecimento: Num; abstencao: Num }, []>(
        `SELECT t.tv, t.vv, t.vb, t.comparecimento, t.abstencao FROM arquivo a JOIN totais t ON t.snapshot_id = a.ultimo_snapshot_id WHERE a.chave = 'u:6257:1:br:::'`,
      )
      .get();
    if (t && t.tv > 0) {
      const el = t.comparecimento + t.abstencao;
      final1tCache = {
        brancos_pct: r2((100 * t.vb) / t.tv),
        nulos_pct: r2((100 * (t.tv - t.vv - t.vb)) / t.tv),
        comparecimento_pct: r2((100 * t.comparecimento) / el),
        abstencao_pct: r2((100 * t.abstencao) / el),
        fonte: "data/apuracao.sqlite, arquivo u:6257:1:br, versão final do 1º turno",
      };
    }
  } catch {
    final1tCache = null;
  } finally {
    db?.close();
  }
  return final1tCache;
}

export interface OpcoesDados {
  base: string;
  /** Instante avaliado (replay e ensaio); sem ele, agora. */
  at?: string;
  anterior: Base | null;
  /** Hora do boletim (id); padrão, a hora do dado. */
  hora?: string;
  timeoutMs?: number;
}

export async function coletarDados(o: OpcoesDados): Promise<SaidaDados> {
  const timeout = o.timeoutMs ?? 15_000;
  const comAt = (p: string): string => (o.at ? `${p}${p.includes("?") ? "&" : "?"}at=${encodeURIComponent(o.at)}` : p);
  async function j<T>(p: string): Promise<T> {
    const r = await fetch(o.base + comAt(p), { signal: AbortSignal.timeout(timeout) });
    if (!r.ok) throw new Error(`${p}: HTTP ${r.status}`);
    return (await r.json()) as T;
  }
  const talvez = <T>(p: string): Promise<T | null> => j<T>(p).catch(() => null);

  const [estado, br, regioes, ufs, abst, est, pausas, secoes, paralela, anomalias, lotes] = await Promise.all([
    j<Estado>("/api/estado"),
    j<Resultado>("/api/resultado?ele=6258&cargo=1&abr=br"),
    talvez<Regioes>("/api/2t/regioes"),
    talvez<Ufs>("/api/2t/ufs"),
    talvez<Abstencao>("/api/2t/abstencao"),
    talvez<Estaduais>("/api/2t/estaduais"),
    talvez<Pausas>("/api/2t/pausas"),
    talvez<Secoes>("/api/2t/secoes"),
    talvez<Paralela>("/api/2t/paralela"),
    talvez<Anomalia[]>("/api/anomalias?limit=60"),
    talvez<Lotes>("/api/lotes?ele=6258&cargo=1&abr=br&top=2"),
  ]);

  const agoraIso = o.at ?? estado.agora;
  const agoraMs = Date.parse(agoraIso);
  const t17 = Date.parse("2026-10-25T20:00:00.000Z");
  const relogioMin = r1((agoraMs - t17) / 60_000);
  // Boletim anterior com mais de 30 min (ensaio da tarde, gerador parado): a janela volta a ser
  // os últimos dez minutos de versões, e o delta fica nulo.
  const ant = o.anterior && agoraMs - Date.parse(o.anterior.at) <= 30 * 60_000 ? o.anterior : null;
  const desdeMs = ant ? Date.parse(ant.at) : agoraMs - 10 * 60_000;

  // ---------- nacional ----------
  const cands = [...br.cand].sort((a, b) => b.vap - a.vap);
  const nome = new Map(br.cand.map(c => [c.sqcand, nomeFalado(c.nmu)]));
  const st = br.s.st;
  const ts = br.s.ts;
  const pst = br.s.pst;
  const tv = br.v.tv;
  const vv = br.v.vv;
  const vb = br.v.vb;
  const nulos = Math.max(0, tv - vv - vb);
  const el = br.e.c + br.e.a;
  const c0 = cands[0];
  const c1 = cands[1];
  const difPp = c0 && c1 && vv > 0 ? r2(c0.pvapn - c1.pvapn) : null;
  const difVotos = c0 && c1 ? c0.vap - c1.vap : null;
  // Ordem F × L para a locução, com quem está à frente marcado.
  const fl = [...br.cand].sort((a, b) => (nomeFalado(a.nmu).startsWith("Flávio") ? -1 : nomeFalado(b.nmu).startsWith("Flávio") ? 1 : 0));
  const f1 = final1T();
  const nacional = {
    secoes_totalizadas: st,
    secoes_total: ts,
    pct_secoes: r2(pst),
    totalizacao_tse_brt: brt(br.dt_ht),
    fonte_placar: br.fonte ?? "tse",
    nota_fonte: br.fonte === "soma_ufs" && br.nacional_tse
      ? `arquivo nacional do TSE atrasado (gerado às ${brt(br.nacional_tse.hg)} com ${pctBr(br.nacional_tse.pst, 2)}% das seções); placar = soma dos arquivos das 27 UFs e do exterior`
      : null,
    placar_f_x_l: fl.map(c => ({ nome: nomeFalado(c.nmu), numero: c.n, partido: c.sg, votos: c.vap, pct_validos: r2(c.pvapn), eleito_tse: c.e === true })),
    a_frente: vv > 0 && c0 ? nomeFalado(c0.nmu) : null,
    diferenca_pp: difPp,
    diferenca_votos: difVotos,
    votos_validos: vv,
    total_votos: tv,
    brancos: vb,
    brancos_pct_do_total: tv > 0 ? r2((100 * vb) / tv) : null,
    nulos,
    nulos_pct_do_total: tv > 0 ? r2((100 * nulos) / tv) : null,
    eleitorado_apto: br.e.te,
    comparecimento: br.e.c,
    abstencao: br.e.a,
    comparecimento_pct_nas_secoes_apuradas: el > 0 ? r2((100 * br.e.c) / el) : null,
    abstencao_pct_nas_secoes_apuradas: el > 0 ? r2((100 * br.e.a) / el) : null,
  };

  // ---------- 1º turno como régua ----------
  const absBr = abst?.brasil ?? null;
  const primeiroTurno = {
    resultado_final_1t: f1,
    nota: "as seções apuradas cedo não representam o país; a comparação justa da abstenção é a dos municípios já fechados contra os mesmos municípios no 1º turno",
    abstencao_municipios_fechados: absBr && absBr.n_mun_fechados > 0
      ? { municipios_fechados: absBr.n_mun_fechados, pct_do_eleitorado_fechado: r1(absBr.pct_te_fechado), abstencao_2t_pct: absBr.pa_2t, abstencao_1t_mesmos_pct: absBr.pa_1t_mesmos, diferenca_pp: absBr.delta_pp }
      : null,
    ritmo_mesmo_relogio: regioes?.brasil.ref_1t
      ? { pct_secoes_1t_no_mesmo_horario: regioes.brasil.ref_1t.pst_mesmo_relogio, atraso_min_vs_1t: regioes.brasil.ref_1t.atraso_min, nota: "atraso positivo = mais lento que o 1º turno no mesmo horário; negativo = mais rápido" }
      : null,
    abstencao_destaques: abst
      ? {
          subiu: abst.destaques.subiu.slice(0, 4).map(m => ({ uf: m.uf, municipio: m.nm, eleitorado: m.te, abstencao_2t: m.pa_2t, abstencao_1t: m.pa_1t, diferenca_pp: m.delta_pp })),
          caiu: abst.destaques.caiu.slice(0, 4).map(m => ({ uf: m.uf, municipio: m.nm, eleitorado: m.te, abstencao_2t: m.pa_2t, abstencao_1t: m.pa_1t, diferenca_pp: m.delta_pp })),
          rotulo: "abstenção atípica pede explicação, não indica irregularidade",
        }
      : null,
  };

  // ---------- janela desde o boletim anterior ----------
  const ganhos = br.cand.map(c => {
    const antes = ant ? (ant.votos[c.sqcand] ?? 0) : null;
    let ganho: Num;
    if (antes !== null) ganho = c.vap - antes;
    else ganho = (lotes?.lotes ?? []).filter(l => Date.parse(l.at) >= desdeMs).reduce((a, l) => a + (l.cand[c.sqcand]?.d_vap ?? 0), 0);
    return { sqcand: c.sqcand, nome: nomeFalado(c.nmu), ganho };
  });
  const somaGanho = ganhos.reduce((a, g) => a + Math.max(0, g.ganho), 0);
  const versoes = (lotes?.lotes ?? []).filter(l => Date.parse(l.at) > desdeMs);
  const secoesJanela = ant ? st - ant.st : versoes.reduce((a, l) => a + l.d_st, 0);
  const validosJanela = ant ? vv - ant.vv : versoes.reduce((a, l) => a + l.d_vv, 0);
  const gF = ganhos[0];
  const gL = ganhos[1];
  const saldo = gF && gL ? { para: gF.ganho >= gL.ganho ? gF.nome : gL.nome, votos: Math.abs(gF.ganho - gL.ganho) } : null;
  const difAntes = ant?.diferenca_pp ?? null;
  const janela = {
    desde_brt: ant ? horaBrt(ant.at) : horaBrt(desdeMs),
    minutos: r1((agoraMs - desdeMs) / 60_000),
    base: ant ? "boletim anterior" : "últimos dez minutos de versões do arquivo nacional",
    versoes_novas_do_arquivo_nacional: versoes.length,
    ultima_versao_brt: brt(versoes.at(-1)?.at ?? null),
    secoes_que_chegaram: secoesJanela,
    pontos_percentuais_de_secoes: ant ? r2(pst - ant.pst) : null,
    votos_validos_que_chegaram: validosJanela,
    para_quem: ganhos.map(g => ({ nome: g.nome, votos: g.ganho, pct_do_bloco: somaGanho > 0 ? r1((100 * Math.max(0, g.ganho)) / somaGanho) : null })),
    saldo_do_bloco: saldo && saldo.votos > 0 ? saldo : null,
    diferenca_no_boletim_anterior_pp: difAntes,
    lider_no_boletim_anterior: ant ? liderDe(ant.votos, nome) : null,
    diferenca_agora_pp: difPp,
    movimento: difAntes !== null && difPp !== null && ant && liderDe(ant.votos, nome) === (c0 ? nomeFalado(c0.nmu) : null)
      ? (Math.abs(difPp - difAntes) < 0.05 ? "estável" : difPp > difAntes ? "a diferença abriu" : "a diferença fechou")
      : ant && liderDe(ant.votos, nome) !== (c0 ? nomeFalado(c0.nmu) : null) ? "mudou quem está à frente" : null,
  };

  // ---------- regiões ----------
  const pctDe = (votos: Record<string, { pvapn: Num }>, nomeAlvo: string): Num | null => {
    const sq = [...nome.entries()].find(([, n]) => n.startsWith(nomeAlvo))?.[0];
    return sq ? (votos[sq]?.pvapn ?? null) : null;
  };
  const regioesOut = (regioes?.regioes ?? []).map(r => ({
    regiao: r.nome,
    pct_secoes: r2(r.pst),
    flavio_pct: pctDe(r.votos, "Flávio"),
    lula_pct: pctDe(r.votos, "Lula"),
    a_frente: r.lider ? (nome.get(r.lider) ?? null) : null,
    margem_pp: r.lider ? r2(r.margem_pp) : null,
    abstencao_pct_nas_secoes_apuradas: r.st > 0 ? r2(r.pa) : null,
    secoes_por_min_10min: r1(r.vel_10min_spm),
    atraso_min_vs_1t: r.ref_1t?.atraso_min ?? null,
    previsao_100_brt_projecao_simples: brt(r.eta_100_iso),
  }));

  // ---------- UFs ----------
  const linhas = (ufs?.ufs ?? []).filter(u => u.ts > 0);
  const nomeUf = new Map(linhas.map(u => [u.uf, u.nome]));
  const nUf = (uf: string): string => nomeUf.get(uf) ?? uf;
  const abertas = linhas.filter(u => u.st < u.ts);
  const fechadas = linhas.filter(u => u.st >= u.ts).map(u => u.uf);
  const ufLinha = (u: UfLinha): Record<string, unknown> => ({
    uf: u.uf,
    nome: u.nome,
    pct_secoes: r2(u.pst),
    faltam_secoes: u.ts - u.st,
    municipios_sem_totalizar: u.munnr + u.munpt,
    atraso_min_vs_1t: u.ref_1t?.atraso_min ?? null,
    hora_que_fechou_no_1t: u.ref_1t?.p100_min !== null && u.ref_1t?.p100_min !== undefined ? hhmm17(u.ref_1t.p100_min) : null,
    parada: u.parada,
    minutos_sem_versao_nova: u.idade_s !== null ? r1(u.idade_s / 60) : null,
    previsao_100_brt_projecao_simples: brt(u.eta_100_iso),
    maiores_municipios_abertos: u.pendentes_maiores.slice(0, 3).map(m => `${m.nm} (${pctBr(m.pst)}%)`),
  });
  const maisLentas = [...abertas].sort((a, b) => a.pst - b.pst).slice(0, 6).map(ufLinha);
  const atrasadas = [...abertas].filter(u => (u.ref_1t?.atraso_min ?? 0) >= 10).sort((a, b) => (b.ref_1t?.atraso_min ?? 0) - (a.ref_1t?.atraso_min ?? 0)).slice(0, 5).map(ufLinha);
  const ultimas = [...abertas].filter(u => u.eta_100_iso).sort((a, b) => String(b.eta_100_iso).localeCompare(String(a.eta_100_iso))).slice(0, 3).map(u => ({ uf: u.uf, previsao_100_brt_projecao_simples: brt(u.eta_100_iso) }));
  const ultimasNo1t = [...abertas].filter(u => u.ref_1t?.p100_min !== null && u.ref_1t?.p100_min !== undefined).sort((a, b) => (b.ref_1t?.p100_min ?? 0) - (a.ref_1t?.p100_min ?? 0)).slice(0, 3).map(u => ({ uf: u.uf, fechou_no_1t_as: hhmm17(u.ref_1t?.p100_min ?? 0) }));
  const porUf = linhas.filter(u => u.st > 0).map(u => ({ uf: u.uf, pct_secoes: r1(u.pst), flavio_pct: pctDe(u.votos, "Flávio"), lula_pct: pctDe(u.votos, "Lula"), a_frente: u.lider ? (nome.get(u.lider) ?? null) : null, margem_pp: u.lider ? r1(u.margem_pp) : null }));
  const lideresUf: Record<string, string> = {};
  for (const u of linhas) if (u.lider && u.st > 0) lideresUf[u.uf] = u.lider;
  const viradasUf = ant
    ? Object.entries(lideresUf).filter(([uf, sq]) => ant.lideres_uf[uf] !== undefined && ant.lideres_uf[uf] !== sq).map(([uf, sq]) => `${nUf(uf)}: ${nome.get(sq) ?? sq} passou à frente`)
    : [];
  const apertadas = porUf.filter(u => u.margem_pp !== null && u.pct_secoes >= 10).sort((a, b) => (a.margem_pp ?? 99) - (b.margem_pp ?? 99)).slice(0, 5);

  // ---------- governadores ----------
  const lideresGov: Record<string, string> = {};
  const estaduais = (est?.ufs ?? []).map(e => {
    if (e.lider && e.st > 0) lideresGov[e.uf] = e.lider;
    const nomeGov = new Map(e.cand.map(c => [c.sqcand, nomeFalado(c.nome_urna)]));
    const virouAgora = ant && e.lider && ant.lideres_gov[e.uf] !== undefined && ant.lideres_gov[e.uf] !== e.lider;
    return {
      uf: e.uf,
      estado: e.nome,
      pct_secoes: r2(e.pst),
      candidatos: [...e.cand].sort((a, b) => b.vap - a.vap).map(c => ({ nome: nomeGov.get(c.sqcand), partido: c.partido, campo: c.campo ?? null, votos: c.vap, pct_validos: r2(c.pvapn) })),
      a_frente: e.lider && e.st > 0 ? (nomeGov.get(e.lider) ?? null) : null,
      margem_pp: e.lider && e.st > 0 ? r2(e.margem_pp) : null,
      virou_desde_o_boletim_anterior: virouAgora ? true : false,
      viradas_na_noite: e.viradas.length,
      abstencao_pct_nas_secoes_apuradas: e.st > 0 ? r2(e.pa) : null,
      abstencao_final_1t: e.pa_final_1t,
      atraso_min_vs_1t: e.ref_1t?.atraso_min ?? null,
    };
  });
  const viradasGov = estaduais.filter(e => e.virou_desde_o_boletim_anterior).map(e => `${e.uf}: ${e.a_frente} passou à frente`);

  // ---------- pausas ----------
  const pausaHist = pausas?.nacional.historico ?? [];
  const ufsEmPausa = (pausas?.ufs ?? []).filter(u => u.em_pausa).map(u => u.uf);
  const pausasOut = pausas
    ? {
        rotulo: "pausa = intervalo sem versão nova publicada; não é acusação",
        limiar_min: pausas.limiar_min,
        arquivo_nacional_em_pausa: pausas.nacional.em_pausa,
        pausa_atual: pausas.nacional.pausa_atual ? { desde_brt: brt(pausas.nacional.pausa_atual.desde), minutos: r1(pausas.nacional.pausa_atual.minutos) } : null,
        pausas_da_noite: pausaHist.map(p => ({ de_brt: brt(p.de), ate_brt: brt(p.ate), minutos: r1(p.minutos) })),
        ufs_em_pausa: ufsEmPausa.map(nUf),
        soma_das_ufs_a_frente_do_nacional_secoes: pausas.soma_ufs.defasagem_secoes,
        referencia_1t: "no 1º turno houve um intervalo geral sem versão nova das 19:32 às 20:02",
      }
    : null;

  // ---------- totalização paralela ----------
  const parOut = paralela
    ? {
        rotulo_obrigatorio: "soma dos BUs recebidos, não projeção",
        fonte_indisponivel: paralela.erro,
        bus_recebidos: paralela.recebidos.bus,
        secoes: paralela.recebidos.secoes,
        ufs: paralela.recebidos.ufs,
        conflitos: paralela.recebidos.conflitos,
        conferidos_iguais_ao_tse: paralela.conferencia.iguais,
        divergentes_do_tse: paralela.conferencia.divergentes,
        tse_ainda_nao_publicou: paralela.conferencia.tse_ainda_nao_publicou,
        pendentes: paralela.conferencia.pendentes,
        placar_dos_bus: placarBus(paralela, br.cand),
        divergencias_recentes: paralela.divergencias.slice(0, 5).map(d => ({ uf: d.uf, municipio: d.mun, zona: d.zona, secao: d.secao, campos: d.campos.map(c => c.campo) })),
      }
    : null;

  // ---------- amostra de seções ----------
  const secOut = secoes && secoes.totais.recebidas > 0
    ? {
        amostra_recebidas: secoes.totais.recebidas,
        amostra_alvo: secoes.totais.alvo,
        encerramento_mediano_brt: secoes.brasil.encerramento_p50_hhmm,
        encerramento_p90_brt: secoes.brasil.encerramento_p90_hhmm,
        minutos_encerramento_ate_recebimento_mediana: secoes.brasil.lag_encerr_recebimento_min.p50,
        mesma_medida_no_1t: secoes.brasil.ref_1t?.lag_p50 ?? null,
        secoes_encerradas_depois_das_18h: secoes.totais.tardias,
      }
    : null;

  // ---------- alertas desde o anterior ----------
  const alertas = (anomalias ?? [])
    .filter(a => Date.parse(a.at) > desdeMs && a.categoria !== "outro" && a.tipo_bruto !== "idg_regressivo" && (a.severidade === "warn" || a.severidade === "error"))
    .slice(0, 12)
    .map(a => ({ hora_brt: brt(a.at), categoria: a.categoria, severidade: a.severidade, texto: a.texto }));
  const viradasAnomalia = alertas.filter(a => a.categoria === "virada").map(a => a.texto);

  // ---------- delta ----------
  const divergentes = paralela?.conferencia.divergentes ?? 0;
  const delta = ant
    ? {
        secoes: st - ant.st,
        pontos_percentuais_de_secoes: r2(pst - ant.pst),
        votos_validos: vv - ant.vv,
        diferenca_pp_antes: ant.diferenca_pp,
        diferenca_pp_agora: difPp,
        diferenca_votos_antes: ant.diferenca_votos,
        diferenca_votos_agora: difVotos,
        viradas_presidente_por_uf: viradasUf,
        viradas_governador: viradasGov,
        viradas_nos_alertas: viradasAnomalia,
        ufs_que_fecharam: fechadas.filter(u => !ant.ufs_fechadas.includes(u)).map(nUf),
        pausa_nacional_abriu: (pausas?.nacional.em_pausa ?? false) && !ant.pausa_nacional,
        pausa_nacional_fechou: !(pausas?.nacional.em_pausa ?? false) && ant.pausa_nacional,
        pausas_nacionais_novas: Math.max(0, pausaHist.length - ant.pausas_nacionais_n),
        ufs_entraram_em_pausa: ufsEmPausa.filter(u => !ant.ufs_em_pausa.includes(u)).map(nUf),
        ufs_sairam_de_pausa: ant.ufs_em_pausa.filter(u => !ufsEmPausa.includes(u)).map(nUf),
        divergencias_novas_na_paralela: Math.max(0, divergentes - ant.divergentes),
      }
    : null;

  // ---------- modo e tamanho ----------
  const motivos: string[] = [];
  let modo: Modo;
  if (agoraMs < t17 || st === 0) {
    modo = "abertura";
    motivos.push(agoraMs < t17 ? "antes das 17:00" : "nenhuma seção totalizada");
  } else if (!delta) {
    modo = "muita";
    motivos.push("primeiro boletim com seções totalizadas");
  } else {
    if (delta.pontos_percentuais_de_secoes >= 2) motivos.push(`${pctBr(delta.pontos_percentuais_de_secoes)} pontos de seções desde o anterior`);
    if (delta.viradas_presidente_por_uf.length + delta.viradas_governador.length + delta.viradas_nos_alertas.length > 0) motivos.push("virada");
    if (delta.ufs_que_fecharam.length > 0) motivos.push("UF fechou");
    if (delta.pausa_nacional_abriu || delta.pausa_nacional_fechou || delta.pausas_nacionais_novas > 0 || delta.ufs_entraram_em_pausa.length > 0) motivos.push("pausa");
    if (delta.divergencias_novas_na_paralela > 0) motivos.push("divergência nova na totalização paralela");
    if (ant && liderDe(ant.votos, nome) !== (c0 ? nomeFalado(c0.nmu) : null)) motivos.push("mudou quem está à frente no país");
    modo = motivos.length > 0 ? "muita" : "pouca";
    if (modo === "pouca") motivos.push("pouca mudança desde o anterior");
  }

  const resumo: Resumo = {
    hora_brt: o.hora ?? horaBrt(agoraMs),
    agora_iso: new Date(agoraMs).toISOString(),
    relogio_min: relogioMin,
    modo,
    motivos_modo: motivos,
    turno: estado.turno,
    nacional,
    primeiro_turno_como_regua: primeiroTurno,
    desde_o_boletim_anterior: janela,
    delta,
    ritmo: regioes
      ? { secoes_por_min_ultimos_10min: r1(regioes.brasil.vel_10min_spm), faltam_secoes: ts - st, previsao_100_brt_projecao_simples: brt(regioes.brasil.eta_100_iso) }
      : null,
    regioes: regioesOut,
    ufs: {
      fechadas: fechadas.map(nUf),
      mais_lentas: maisLentas,
      mais_atrasadas_vs_1t: atrasadas,
      quem_deve_fechar_por_ultimo_projecao_simples: ultimas,
      quem_fechou_por_ultimo_no_1t_entre_as_abertas: ultimasNo1t,
      paradas: abertas.filter(u => u.parada).map(u => u.nome),
      disputas_mais_apertadas: apertadas,
      por_uf: porUf,
      rotulo_atraso: "atraso pede explicação, não indica irregularidade",
    },
    governadores_2t: { ufs: ["AC", "AM", "DF", "ES", "RN", "TO"], estaduais },
    pausas: pausasOut,
    totalizacao_paralela: parOut,
    amostra_de_secoes: secOut,
    alertas_desde_o_anterior: alertas,
  };

  const base: Base = {
    at: new Date(agoraMs).toISOString(),
    st,
    ts,
    pst,
    vv,
    votos: Object.fromEntries(br.cand.map(c => [c.sqcand, c.vap])),
    diferenca_pp: difPp,
    diferenca_votos: difVotos,
    lideres_uf: lideresUf,
    ufs_fechadas: fechadas,
    pausa_nacional: pausas?.nacional.em_pausa ?? false,
    pausas_nacionais_n: pausaHist.length,
    ufs_em_pausa: ufsEmPausa,
    divergentes,
    lideres_gov: lideresGov,
  };

  // Resumo de uma linha, sem LLM.
  const partes = [resumo.hora_brt, `${pctBr(pst, 1)}% das seções`];
  const pF = fl[0];
  const pL = fl[1];
  if (st > 0 && pF && pL) partes.push(`${nomeFalado(pF.nmu).split(" ")[0]} ${pctBr(pF.pvapn, 2)} × ${nomeFalado(pL.nmu).split(" ")[0]} ${pctBr(pL.pvapn, 2)}`);
  if (delta) partes.push(`+${delta.secoes.toLocaleString("pt-BR")} seções`);
  if (modo === "abertura") partes.push("abertura");
  for (const m of motivos) if (["virada", "UF fechou", "pausa", "divergência nova na totalização paralela", "mudou quem está à frente no país"].includes(m)) partes.push(m);
  return { resumo, base, linha: partes.join(" · ") };
}

function liderDe(votos: Record<string, Num>, nome: Map<string, string>): string | null {
  const ord = Object.entries(votos).sort((a, b) => b[1] - a[1]);
  const [a, b] = ord;
  if (!a || a[1] <= 0 || (b && a[1] === b[1])) return null;
  return nome.get(a[0]) ?? a[0];
}

function hhmm17(min: Num): string {
  const t = Date.parse("2026-10-25T20:00:00.000Z") + min * 60_000;
  return horaBrt(t);
}

function placarBus(p: Paralela, cands: Cand[]): Record<string, unknown> | null {
  const pres = p.placar_bus.presidente;
  const total = Object.values(pres.votos).reduce((a, v) => a + v, 0);
  if (pres.secoes <= 0 || total <= 0) return null;
  return {
    secoes: pres.secoes,
    votos: cands.map(c => ({ nome: nomeFalado(c.nmu), votos: pres.votos[c.n] ?? 0, pct_validos_dos_bus: r2((100 * (pres.votos[c.n] ?? 0)) / total) })),
    brancos: pres.brancos,
    nulos: pres.nulos,
  };
}
