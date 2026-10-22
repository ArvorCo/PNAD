// Alertas do 2º turno contra a régua do 1º (data/referencia_1t.json): UF atrasada no ritmo,
// abstenção atípica em município fechado e na UF. Atraso e abstenção atípica pedem explicação,
// não indicam irregularidade. Cada alerta sai uma vez (por patamar, município ou sentido);
// o estado volta da tabela evento na partida.
import type { Database } from "bun:sqlite";
import type { EventoNovo } from "../db/escrita.ts";
import { minutosDesde17h, T0_2T_MS } from "../turno2/comum.ts";
import type { Referencia1T } from "../turno2/referencia.ts";
import { atrasoVsReferencia, pstNoMinuto } from "../turno2/referencia.ts";
import { isoDe } from "./relogio.ts";

export const ROTULO_REGUA = "pede explicação, não indica irregularidade";

export interface OpcoesRegua {
  ele: number;
  t0Ms: number;
  /** patamar de atraso em minutos (20, 40, 60...) */
  patamarMin: number;
  munTeMin: number;
  munDeltaPp: number;
  /** fração mínima do eleitorado da UF em municípios fechados (%) */
  ufPctTe: number;
  ufDeltaPp: number;
}

export const REGUA_PADRAO: Omit<OpcoesRegua, "ele"> = {
  t0Ms: T0_2T_MS,
  patamarMin: 20,
  munTeMin: 20_000,
  munDeltaPp: 5,
  ufPctTe: 30,
  ufDeltaPp: 2,
};

export interface UfAndamento {
  /** sigla minúscula */
  uf: string;
  pst: number;
  st: number;
  ts: number;
}

/** Município no -ab da UF (2º turno). */
export interface MunAb {
  uf: string;
  mun: string;
  ts: number;
  st: number;
  te: number;
  c: number;
  a: number;
}

const r2 = (x: number): number => Math.round(x * 100) / 100;
const paDe = (c: number, a: number): number | null => (c + a > 0 ? (100 * a) / (c + a) : null);

export class AlertasRegua {
  private readonly patamar = new Map<string, number>();
  private readonly munsEmitidos = new Set<string>();
  private readonly ufsEmitidas = new Set<string>();

  constructor(
    private readonly ref: Referencia1T | null,
    private readonly o: OpcoesRegua,
  ) {}

  get ativo(): boolean {
    return this.ref !== null;
  }

  /** Estado dos alertas já gravados (sobrevive a reinício do coletor). */
  carregar(db: Database): void {
    const pat = db
      .query<{ uf: string | null; p: number | null }, []>(
        "SELECT uf, MAX(CAST(json_extract(detalhe, '$.patamar_min') AS INTEGER)) AS p FROM evento WHERE tipo = 'uf_atrasada_1t' GROUP BY uf",
      )
      .all();
    for (const r of pat) if (r.uf !== null && r.p !== null) this.patamar.set(r.uf, r.p);
    for (const r of db.query<{ uf: string | null; m: string | null }, []>("SELECT uf, municipio_cd AS m FROM evento WHERE tipo = 'abstencao_atipica_mun'").all()) {
      if (r.uf !== null && r.m !== null) this.munsEmitidos.add(`${r.uf}:${r.m}`);
    }
    for (const r of db
      .query<{ uf: string | null; s: string | null }, []>("SELECT uf, json_extract(detalhe, '$.sentido') AS s FROM evento WHERE tipo = 'abstencao_atipica_uf'")
      .all()) {
      if (r.uf !== null && r.s !== null) this.ufsEmitidas.add(`${r.uf}:${r.s}`);
    }
  }

  private ev(em: string, tipo: string, nivel: string, uf: string, mun: string | null, detalhe: unknown): EventoNovo {
    return { em, tipo, severidade: "warn", eleicao_cd: this.o.ele, cargo_cd: 1, nivel, uf, municipio_cd: mun, detalhe };
  }

  /** UF aberta (st < ts) atrás da curva do 1º turno: um evento por patamar novo. */
  avaliarAtraso(agora: number, ufs: readonly UfAndamento[]): EventoNovo[] {
    const ref = this.ref;
    if (!ref) return [];
    const min = minutosDesde17h(isoDe(agora), this.o.t0Ms);
    if (min === null || min < 0) return [];
    const out: EventoNovo[] = [];
    for (const u of ufs) {
      if (u.ts <= 0 || u.st >= u.ts) continue;
      const curva = ref.curvas.uf[u.uf.toUpperCase()];
      if (!curva || curva.length === 0) continue;
      const atraso = atrasoVsReferencia(curva, u.pst, min);
      if (atraso === null || atraso < this.o.patamarMin) continue;
      const patamar = Math.floor(atraso / this.o.patamarMin) * this.o.patamarMin;
      if (patamar <= (this.patamar.get(u.uf) ?? 0)) continue;
      this.patamar.set(u.uf, patamar);
      out.push(
        this.ev(isoDe(agora), "uf_atrasada_1t", "uf", u.uf, null, {
          patamar_min: patamar, atraso_min: atraso, min, pst: r2(u.pst), pst_1t_mesmo_relogio: r2(pstNoMinuto(curva, min)), st: u.st, ts: u.ts,
          rotulo: ROTULO_REGUA,
        }),
      );
    }
    return out;
  }

  /** Abstenção em municípios fechados contra os mesmos municípios no 1º turno. */
  avaliarAbstencao(agora: number, muns: Iterable<MunAb>): EventoNovo[] {
    const ref = this.ref;
    if (!ref) return [];
    const em = isoDe(agora);
    const out: EventoNovo[] = [];
    interface Acc { te: number; teFechado: number; c2: number; a2: number; c1: number; a1: number; n: number }
    const porUf = new Map<string, Acc>();
    for (const m of muns) {
      const acc = porUf.get(m.uf) ?? { te: 0, teFechado: 0, c2: 0, a2: 0, c1: 0, a1: 0, n: 0 };
      porUf.set(m.uf, acc);
      acc.te += m.te;
      if (m.ts <= 0 || m.st !== m.ts) continue;
      acc.teFechado += m.te;
      const r1 = ref.municipios[m.uf.toUpperCase()]?.[m.mun];
      if (!r1) continue;
      acc.c2 += m.c;
      acc.a2 += m.a;
      acc.c1 += r1.comparecimento;
      acc.a1 += r1.abstencao;
      acc.n += 1;
      const pa2 = paDe(m.c, m.a);
      const k = `${m.uf}:${m.mun}`;
      if (pa2 === null || m.te < this.o.munTeMin || this.munsEmitidos.has(k)) continue;
      const delta = pa2 - r1.pa;
      if (Math.abs(delta) < this.o.munDeltaPp) continue;
      this.munsEmitidos.add(k);
      out.push(
        this.ev(em, "abstencao_atipica_mun", "mu", m.uf, m.mun, {
          nm: r1.nm ?? null, te: m.te, comparecimento: m.c, abstencao: m.a, pa_2t: r2(pa2), pa_1t: r1.pa, delta_pp: r2(delta), rotulo: ROTULO_REGUA,
        }),
      );
    }
    for (const [uf, acc] of porUf) {
      if (acc.te <= 0 || acc.n === 0) continue;
      const pct = (100 * acc.teFechado) / acc.te;
      const pa2 = paDe(acc.c2, acc.a2);
      const pa1 = paDe(acc.c1, acc.a1);
      if (pa2 === null || pa1 === null || pct < this.o.ufPctTe) continue;
      const delta = pa2 - pa1;
      if (Math.abs(delta) < this.o.ufDeltaPp) continue;
      const sentido = delta > 0 ? "subiu" : "caiu";
      const k = `${uf}:${sentido}`;
      if (this.ufsEmitidas.has(k)) continue;
      this.ufsEmitidas.add(k);
      out.push(
        this.ev(em, "abstencao_atipica_uf", "uf", uf, null, {
          sentido, pa_2t: r2(pa2), pa_1t_mesmos: r2(pa1), delta_pp: r2(delta), pct_te_fechado: r2(pct), n_mun_fechados: acc.n,
          te_fechado: acc.teFechado, te: acc.te, base: "municipios_fechados", rotulo: ROTULO_REGUA,
        }),
      );
    }
    return out;
  }
}
