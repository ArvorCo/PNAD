// /api/2t/secoes: cadeia de tempos das seções amostradas (encerramento → emissão do BU →
// recebimento no TSE → totalização do município), por UF e no Brasil, com a régua do 1º turno.
// Só leitura de secao_2t. Com `at`, uma seção conta como recebida se o TSE a recebeu até `at`,
// e o lag de totalização entra se a totalização do município aconteceu até `at`.
import type { Database } from "bun:sqlite";
import { hhmmDeMinutos, minutosDesde17h, percentil } from "../turno2/comum.ts";
import type { Referencia1T, SecoesLagUf } from "../turno2/referencia.ts";

export interface Desenho {
  nacional_por_uf: number;
  estaduais_por_uf: number;
  inclui_paralela: true;
  intervalo_s: number;
}

interface Linha {
  uf: string;
  mun: string;
  zona: number;
  secao: number;
  origem: string;
  encerramento_iso: string | null;
  emissao_iso: string | null;
  recebido_iso: string | null;
  bu_sha256: string | null;
  lag_encerr_recebimento_min: number | null;
  lag_encerr_emissao_min: number | null;
  totalizado_mun_iso: string | null;
  lag_recebimento_totalizacao_min: number | null;
}

export interface Bloco {
  alvo: number;
  recebidas: number;
  encerramento_p50_hhmm: string | null;
  encerramento_p90_hhmm: string | null;
  tarde_apos_1730_pct: number | null;
  lag_encerr_recebimento_min: { p50: number | null; p90: number | null; p99: number | null };
  lag_encerr_emissao_min: { p50: number | null; p90: number | null };
  /** recebimento no TSE até a primeira totalização do município que pode incluí-la */
  lag_recebimento_totalizacao_min: { p50: number | null; p90: number | null; p99: number | null };
  ref_1t: { lag_p50: number | null; lag_p90: number | null; enc_p90_hhmm: string | null } | null;
}

export interface SecoesOut {
  at: string;
  min: number | null;
  desenho: Desenho;
  totais: { alvo: number; recebidas: number; pendentes: number; tardias: number };
  por_uf: (Bloco & { uf: string })[];
  brasil: Bloco;
  tardias: { uf: string; mun: string; nm: string; zona: number; secao: number; encerramento_hhmm: string; recebido_hhmm: string | null; lag_min: number | null }[];
  ultimas: { uf: string; mun: string; zona: number; secao: number; recebido_em: string; lag_min: number | null }[];
}

export interface OpcoesResumo {
  at: string | undefined;
  agora: string;
  t0Ms: number;
  ref: Referencia1T | null;
  desenho: Desenho;
  nome: (cd: string) => string | null;
}

const r1 = (x: number | null): number | null => (x === null ? null : Math.round(x * 10) / 10);
const r2 = (x: number): number => Math.round(x * 100) / 100;
const ordenados = (l: readonly (number | null)[]): number[] => l.filter((x): x is number => x !== null && Number.isFinite(x)).sort((a, b) => a - b);

function refDe(r: SecoesLagUf | undefined): Bloco["ref_1t"] {
  if (!r) return null;
  return { lag_p50: r.lag_encerr_recebimento_min.p50, lag_p90: r.lag_encerr_recebimento_min.p90, enc_p90_hhmm: r.encerramento_p90_hhmm };
}

function bloco(linhas: readonly Linha[], recebida: (l: Linha) => boolean, totalizada: (l: Linha) => boolean, t0Ms: number, ref: Bloco["ref_1t"]): Bloco {
  const rec = linhas.filter(recebida);
  // exterior: hora da urna sem fuso conhecido, fora dos tempos
  const tempos = rec.filter((l) => l.uf !== "zz");
  const enc = ordenados(tempos.map((l) => (l.encerramento_iso === null ? null : minutosDesde17h(l.encerramento_iso, t0Ms))));
  const lagRec = ordenados(tempos.map((l) => l.lag_encerr_recebimento_min));
  const lagEmi = ordenados(tempos.map((l) => l.lag_encerr_emissao_min));
  const lagTot = ordenados(tempos.filter(totalizada).map((l) => l.lag_recebimento_totalizacao_min));
  const hh = (p: number): string | null => {
    const v = percentil(enc, p);
    return v === null ? null : hhmmDeMinutos(Math.floor(v));
  };
  return {
    alvo: linhas.length,
    recebidas: rec.length,
    encerramento_p50_hhmm: hh(50),
    encerramento_p90_hhmm: hh(90),
    tarde_apos_1730_pct: enc.length === 0 ? null : r2((100 * enc.filter((m) => m > 30).length) / enc.length),
    lag_encerr_recebimento_min: { p50: r1(percentil(lagRec, 50)), p90: r1(percentil(lagRec, 90)), p99: r1(percentil(lagRec, 99)) },
    lag_encerr_emissao_min: { p50: r1(percentil(lagEmi, 50)), p90: r1(percentil(lagEmi, 90)) },
    lag_recebimento_totalizacao_min: { p50: r1(percentil(lagTot, 50)), p90: r1(percentil(lagTot, 90)), p99: r1(percentil(lagTot, 99)) },
    ref_1t: ref,
  };
}

export function tabelaExiste(db: Database, nome: string): boolean {
  return db.query<{ x: number }, [string]>("SELECT 1 AS x FROM sqlite_master WHERE type = 'table' AND name = ?").get(nome) !== null;
}

export function resumoSecoes(db: Database, o: OpcoesResumo): SecoesOut {
  const at = o.at ?? o.agora;
  const linhas = tabelaExiste(db, "secao_2t")
    ? db
        .query<Linha, []>(
          `SELECT uf, mun, zona, secao, origem, encerramento_iso, emissao_iso, recebido_iso, bu_sha256,
                  lag_encerr_recebimento_min, lag_encerr_emissao_min, totalizado_mun_iso, lag_recebimento_totalizacao_min FROM secao_2t`,
        )
        .all()
    : [];
  const recebida = (l: Linha): boolean => l.bu_sha256 !== null && l.recebido_iso !== null && l.recebido_iso <= at;
  const totalizada = (l: Linha): boolean => l.totalizado_mun_iso !== null && l.totalizado_mun_iso <= at;
  const t18 = o.t0Ms + 60 * 60_000;
  const tardiasL = linhas.filter((l) => recebida(l) && l.uf !== "zz" && l.encerramento_iso !== null && Date.parse(l.encerramento_iso) > t18);
  const porUf = new Map<string, Linha[]>();
  for (const l of linhas) {
    const g = porUf.get(l.uf);
    if (g) g.push(l);
    else porUf.set(l.uf, [l]);
  }
  const lagRef = o.ref?.secoes_lag as { uf: Record<string, SecoesLagUf>; br?: SecoesLagUf } | undefined;
  // hora de relógio truncada no minuto (17:08:42 é 17:08)
  const hhIso = (iso: string | null): string | null => {
    const m = iso === null ? null : minutosDesde17h(iso, o.t0Ms);
    return m === null ? null : hhmmDeMinutos(Math.floor(m));
  };
  const recebidas = linhas.filter(recebida).length;
  return {
    at,
    min: minutosDesde17h(at, o.t0Ms),
    desenho: o.desenho,
    totais: { alvo: linhas.length, recebidas, pendentes: linhas.length - recebidas, tardias: tardiasL.length },
    por_uf: [...porUf.entries()]
      .sort((a, b) => (a[0] < b[0] ? -1 : 1))
      .map(([uf, l]) => ({ uf: uf.toUpperCase(), ...bloco(l, recebida, totalizada, o.t0Ms, refDe(lagRef?.uf[uf.toUpperCase()])) })),
    brasil: bloco(linhas, recebida, totalizada, o.t0Ms, refDe(lagRef?.br)),
    tardias: tardiasL
      .sort((a, b) => ((a.encerramento_iso ?? "") < (b.encerramento_iso ?? "") ? 1 : -1))
      .slice(0, 50)
      .map((l) => ({
        uf: l.uf.toUpperCase(), mun: l.mun, nm: o.nome(l.mun) ?? l.mun, zona: l.zona, secao: l.secao,
        encerramento_hhmm: hhIso(l.encerramento_iso) ?? "", recebido_hhmm: hhIso(l.recebido_iso), lag_min: l.lag_encerr_recebimento_min,
      })),
    ultimas: linhas
      .filter(recebida)
      .sort((a, b) => ((a.recebido_iso ?? "") < (b.recebido_iso ?? "") ? 1 : -1))
      .slice(0, 20)
      .map((l) => ({ uf: l.uf.toUpperCase(), mun: l.mun, zona: l.zona, secao: l.secao, recebido_em: l.recebido_iso ?? "", lag_min: l.lag_encerr_recebimento_min })),
  };
}
