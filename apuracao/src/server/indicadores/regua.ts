// Régua do 1º turno pronta para comparação: curvas saneadas, curvas agregadas por conjunto de UFs
// e marcos recalculados. Carregada de src/turno2/referencia.ts; tudo devolve null sem a régua.
//
// Saneamento de defeitos de carimbo da régua de 22/10 (a correção de fato é gerar a régua com
// RelogioArquivo, de ./base.ts; com ela o saneamento não muda nada):
// 1. Versões regeradas sem nova totalização nas UFs com fuso ficaram em hora local, duas horas
//    antes (AC com 98% às 17:28): fica só o ponto cujo st não passa de nenhum st posterior, o que
//    remove esses pontos adiantados e deixa a curva monotônica.
// 2. O exterior traz o carimbo do dia seguinte em todas as versões: a curva inteira cai num único
//    minuto (979,8). Curva degenerada (3 pontos ou mais em menos de 1 min) é tratada como ausente.
// 3. PE teve carimbo uma hora adiantado entre 18:09 e 20:15: a curva fica até 55 min atrasada
//    nesse trecho e o arquivo da régua não tem a geração para corrigir aqui.
import type { PontoCurva, Referencia1T } from "../../turno2/referencia.ts";
import { atrasoVsReferencia, carregarReferencia, pstNoMinuto } from "../../turno2/referencia.ts";
import { paOuNull } from "./base.ts";

export interface MarcosRegua {
  p50: number | null;
  p90: number | null;
  p99: number | null;
  p100: number | null;
}

export interface Regua {
  ref: Referencia1T;
  /** curva saneada por UF (caixa alta); ausente = sem curva utilizável */
  uf(uf: string): PontoCurva[] | null;
  gov(uf: string): PontoCurva[] | null;
  /** curva agregada (soma de st, ts, comparecimento e abstenção) das UFs com curva */
  agregada(ufs: readonly string[]): PontoCurva[] | null;
  marcosUf(uf: string): MarcosRegua | null;
  /** abstenção final do 1º turno somada nas UFs (pa no critério abstencao/(c+a)) */
  paFinal(ufs: readonly string[]): number | null;
  paFinalGov(uf: string): number | null;
}

/** Saneia uma curva: ordena, mantém só pontos com st menor ou igual a todo st posterior. */
export function sanearCurva(curva: readonly PontoCurva[] | undefined): PontoCurva[] | null {
  if (!curva || curva.length === 0) return null;
  const ord = curva.map((p, i) => ({ p, i })).sort((a, b) => a.p[0] - b.p[0] || a.i - b.i).map((x) => x.p);
  const primeiro = ord[0];
  const ultimo = ord[ord.length - 1];
  if (!primeiro || !ultimo) return null;
  if (ord.length >= 3 && ultimo[0] - primeiro[0] < 1) return null;
  const out: PontoCurva[] = [];
  let minSufixo = Number.POSITIVE_INFINITY;
  const manter: boolean[] = new Array<boolean>(ord.length).fill(false);
  for (let i = ord.length - 1; i >= 0; i -= 1) {
    const p = ord[i];
    if (!p || p[3] <= 0) continue;
    if (p[2] <= minSufixo) {
      manter[i] = true;
      minSufixo = p[2];
    }
  }
  let chaveAnt = "";
  ord.forEach((p, i) => {
    if (!manter[i]) return;
    const chave = `${p[2]}|${p[4]}|${p[5]}`;
    if (chave === chaveAnt) return;
    chaveAnt = chave;
    out.push(p);
  });
  return out.length > 0 ? out : null;
}

/** Soma de curvas no mesmo relógio: cada UF entra com o último ponto até o minuto (zero antes do primeiro). */
export function agregarCurvas(curvas: readonly (readonly PontoCurva[])[]): PontoCurva[] {
  const minutos = [...new Set(curvas.flatMap((c) => c.map((p) => p[0])))].sort((a, b) => a - b);
  const pos = curvas.map(() => -1);
  const tsUf = curvas.map((c) => c[c.length - 1]?.[3] ?? 0);
  const out: PontoCurva[] = [];
  let chaveAnt = "";
  for (const m of minutos) {
    let st = 0;
    let ts = 0;
    let c = 0;
    let a = 0;
    curvas.forEach((curva, i) => {
      let p = pos[i] ?? -1;
      while (p + 1 < curva.length && (curva[p + 1]?.[0] ?? Infinity) <= m) p += 1;
      pos[i] = p;
      ts += tsUf[i] ?? 0;
      const pt = p >= 0 ? curva[p] : undefined;
      if (pt) {
        st += pt[2];
        c += pt[4];
        a += pt[5];
      }
    });
    const chave = `${st}|${c}|${a}`;
    if (chave === chaveAnt) continue;
    chaveAnt = chave;
    const pst = ts > 0 ? Math.round(((100 * st) / ts) * 1000) / 1000 : 0;
    out.push([m, pst, st, ts, c, a, paOuNull(c, a) ?? 0]);
  }
  return out;
}

/** Marcos no mesmo critério do gerador: primeiro ponto com pst >= 50/90/99; p100 = st >= ts. */
export function marcosDe(curva: readonly PontoCurva[]): MarcosRegua {
  const alcanca = (lim: number): number | null => curva.find((p) => p[1] >= lim)?.[0] ?? null;
  return { p50: alcanca(50), p90: alcanca(90), p99: alcanca(99), p100: curva.find((p) => p[3] > 0 && p[2] >= p[3])?.[0] ?? null };
}

function construir(ref: Referencia1T): Regua {
  const ufs = new Map<string, PontoCurva[] | null>();
  const gov = new Map<string, PontoCurva[] | null>();
  const agregadas = new Map<string, PontoCurva[] | null>();
  const marcos = new Map<string, MarcosRegua | null>();
  const curvaUf = (uf: string): PontoCurva[] | null => {
    const k = uf.toUpperCase();
    if (!ufs.has(k)) ufs.set(k, sanearCurva(ref.curvas?.uf?.[k]));
    return ufs.get(k) ?? null;
  };
  return {
    ref,
    uf: curvaUf,
    gov(uf) {
      const k = uf.toUpperCase();
      if (!gov.has(k)) gov.set(k, sanearCurva(ref.governador_1t?.[k]?.curva));
      return gov.get(k) ?? null;
    },
    agregada(lista) {
      const k = [...lista].map((u) => u.toUpperCase()).sort().join(",");
      if (!agregadas.has(k)) {
        const curvas = lista.flatMap((u) => {
          const c = curvaUf(u);
          return c ? [c] : [];
        });
        agregadas.set(k, curvas.length > 0 ? agregarCurvas(curvas) : null);
      }
      return agregadas.get(k) ?? null;
    },
    marcosUf(uf) {
      const k = uf.toUpperCase();
      if (!marcos.has(k)) {
        const c = curvaUf(k);
        marcos.set(k, c ? marcosDe(c) : null);
      }
      return marcos.get(k) ?? null;
    },
    paFinal(lista) {
      let c = 0;
      let a = 0;
      let algum = false;
      for (const u of lista) {
        const x = ref.abstencao_uf?.[u.toUpperCase()];
        if (!x) continue;
        algum = true;
        c += x.comparecimento;
        a += x.abstencao;
      }
      return algum ? paOuNull(c, a) : null;
    },
    paFinalGov(uf) {
      const g = ref.governador_1t?.[uf.toUpperCase()];
      if (!g) return null;
      const f = g.final as { comparecimento?: unknown; abstencao?: unknown } | undefined;
      if (f && typeof f.comparecimento === "number" && typeof f.abstencao === "number") return paOuNull(f.comparecimento, f.abstencao);
      const ult = g.curva[g.curva.length - 1];
      return ult ? paOuNull(ult[4], ult[5]) : null;
    },
  };
}

const porReferencia = new WeakMap<Referencia1T, Regua>();

/** Régua atual (relida quando o arquivo muda) ou null sem o arquivo. */
export function regua(): Regua | null {
  const ref = carregarReferencia();
  if (!ref) return null;
  let r = porReferencia.get(ref);
  if (!r) {
    r = construir(ref);
    porReferencia.set(ref, r);
  }
  return r;
}

/**
 * Janela em que a comparação com o 1º turno faz sentido, em minutos após 17:00 do dia da eleição:
 * de 00:00 do dia da eleição a 24:00 do dia seguinte (a apuração do 1º turno terminou às 02:59).
 * Fora dela (banco de ensaio de outra data, por exemplo) o relógio não é comparável.
 */
export const JANELA_REGUA_MIN = { de: -17 * 60, ate: 31 * 60 } as const;

export function dentroDaJanela(minAgora: number): boolean {
  return minAgora >= JANELA_REGUA_MIN.de && minAgora <= JANELA_REGUA_MIN.ate;
}

/**
 * Atraso do 2º turno contra uma curva do 1º: o tempo que o 1º turno levou para chegar ao pst atual
 * menos o relógio de comparação. O relógio é `agora`, ou o minuto do fechamento quando tudo já foi
 * totalizado (senão o atraso cresceria depois do fim). Null sem seção totalizada ou quando o 1º
 * turno nunca chegou ao pst atual.
 */
export function atrasoMin(curva: readonly PontoCurva[], st: number, ts: number, minAgora: number, minFechou: number | null): number | null {
  if (curva.length === 0 || st <= 0 || ts <= 0) return null;
  const relogio = st >= ts && minFechou !== null ? minFechou : minAgora;
  const pst = st >= ts ? 100 : (100 * st) / ts;
  return atrasoVsReferencia(curva, pst, relogio);
}

/** pst do 1º turno no mesmo relógio (2 casas, truncado como o do 2º turno). */
export function pstMesmoRelogio(curva: readonly PontoCurva[], minAgora: number): number {
  const v = pstNoMinuto(curva, minAgora);
  return v >= 100 ? 100 : Math.floor(v * 100) / 100;
}

export interface Comparacao {
  pst_mesmo_relogio: number | null;
  atraso_min: number | null;
}

/**
 * Comparação com o 1º turno no mesmo relógio. Ambos null antes da primeira seção (st = 0) e fora
 * da janela do dia da eleição, para não produzir atrasos gigantes.
 */
export function comparar(curva: readonly PontoCurva[], st: number, ts: number, minAgora: number, minFechou: number | null): Comparacao {
  if (st <= 0 || !dentroDaJanela(minAgora)) return { pst_mesmo_relogio: null, atraso_min: null };
  return { pst_mesmo_relogio: pstMesmoRelogio(curva, minAgora), atraso_min: atrasoMin(curva, st, ts, minAgora, minFechou) };
}
