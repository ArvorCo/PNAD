// Banco de ensaio do 2º turno (25/10/2026): apuração sintética e determinística sobre as fixtures
// de tests/fixtures/2t/. Chamado por `bun run scripts/semear-ensaio.ts --turno 2`.
//
// Presidente (6258) em br, nas 27 UFs e no exterior; governador (6260) nas 6 UFs com fixture;
// os 645 municípios de SP (clones da capital, com abstenção própria) e os municípios com fixture
// (Rio Branco e Rio de Janeiro). Passos de 6 min a partir das 17:00 de Brasília.
//
// Cenário: duelo Flávio Bolsonaro (22) × Lula (13) com viradas em MG, GO e PR; UFs com ritmos
// diferentes (AM, PA e BA lentas); RJ parado por 24 min (pausa de UF); pausa geral sintética de
// 12 min (nenhum arquivo muda no passo 25); abstenção de cada município ±6 pp em torno da régua.
// Governadores e senadores são nomes de ENSAIO. Nunca usar este banco como dado.
import { existsSync, mkdirSync, rmSync } from "node:fs";
import { basename, dirname } from "node:path";
import { abrirEscrita, fecharEscrita } from "../src/db/abrir.ts";
import { lerMeta } from "../src/db/leitura.ts";
import { Sequenciador } from "../src/replay/sequenciador.ts";
import { carregarReferencia } from "../src/turno2/referencia.ts";
import { chave, keyAb, keyCm, keyEleC, keyU, registroDeArquivos } from "../src/tse/urls.ts";
import { json, lerCm } from "../tests/helpers.ts";
import { T0_2T, UFS_2T, versaoAb2t, versaoU2t } from "../tests/server-helpers.ts";

type Obj = Record<string, unknown>;
const obj = (v: unknown): Obj => v as Obj;
const arr = (v: unknown): Obj[] => (Array.isArray(v) ? (v as Obj[]) : []);
const iso = (ms: number): string => new Date(ms).toISOString();
const enc = (nome: string): Uint8Array<ArrayBuffer> => new TextEncoder().encode(JSON.stringify(json(nome)));

export interface OpcoesEnsaio2t {
  db: string;
  passos: number;
  /** acrescenta passos a um banco existente */
  mais?: number;
}

const PASSO_MS = 6 * 60_000;
/** Passo sem nenhuma versão nova em todo o país (pausa geral de 12 min). */
const PASSO_PAUSA_GERAL = 25;
/** RJ não publica nada nestes passos (parada de 24 min) e retoma do ponto em que parou. */
const RJ_PARADO = { de: 10, ate: 12 } as const;
const UFS_LENTAS: ReadonlySet<string> = new Set(["am", "pa", "ba"]);

/** Pseudoaleatório determinístico em [0, 1) a partir de um texto. */
function hash01(s: string): number {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 16777619);
  return ((h >>> 0) % 100_000) / 100_000;
}

/** Fração de seções totalizadas no passo `k`: cada unidade tem início e duração próprios. */
function fracao(id: string, k: number): number {
  const lenta = UFS_LENTAS.has(id) ? 1.7 : 1;
  const dur = (14 + hash01(`dur:${id}`) * 16) * lenta;
  const atraso = 1 + hash01(`atr:${id}`) * 3;
  const x = (k - atraso) / dur;
  return Math.max(0, Math.min(1, x));
}

/** Passo efetivo da UF: RJ congela durante a parada e continua do mesmo ponto. */
function passoEfetivo(uf: string, k: number): number {
  if (uf !== "rj") return k;
  if (k < RJ_PARADO.de) return k;
  if (k <= RJ_PARADO.ate) return RJ_PARADO.de - 1;
  return k - (RJ_PARADO.ate - RJ_PARADO.de + 1);
}

// Fração de Lula entre os dois finalistas ao fim; a deriva inverte a liderança durante a apuração.
const LEAN: Readonly<Record<string, number>> = {
  ac: 0.32, al: 0.62, am: 0.5, ap: 0.48, ba: 0.7, ce: 0.68, df: 0.4, es: 0.42, go: 0.44, ma: 0.7, mg: 0.48, ms: 0.38,
  mt: 0.33, pa: 0.56, pb: 0.66, pe: 0.68, pi: 0.74, pr: 0.4, rj: 0.44, rn: 0.64, ro: 0.3, rr: 0.28, rs: 0.42, sc: 0.32,
  se: 0.66, sp: 0.46, to: 0.52, zz: 0.45,
};
/** Deriva positiva: Lula começa à frente e perde; negativa: começa atrás e vira. */
const DERIVA: Readonly<Record<string, number>> = { mg: 0.12, go: 0.25, pr: -0.25, sp: 0.06 };

function votosPres(lean: number, deriva: number, vv: number, f: number): Record<string, number> {
  const p = Math.max(0.05, Math.min(0.95, lean + deriva * (0.5 - f)));
  const lula = Math.round(vv * p);
  return { 13: lula, 22: vv - lula };
}

/** Rótulo de ensaio nos nomes dos candidatos a governador. */
function rotularGov(corpo: Uint8Array<ArrayBuffer>, uf: string): Uint8Array<ArrayBuffer> {
  const d = obj(JSON.parse(new TextDecoder().decode(corpo)));
  let i = 0;
  for (const cargo of arr(d.carg)) {
    for (const agr of arr(cargo.agr)) {
      for (const par of arr(agr.par)) {
        for (const c of arr(par.cand)) {
          const nome = `ENSAIO GOV ${uf.toUpperCase()} ${String.fromCharCode(65 + i)}`;
          Object.assign(c, { nm: nome, nmu: nome });
          i += 1;
        }
      }
    }
  }
  return new TextEncoder().encode(JSON.stringify(d));
}

export function semearEnsaio2t(o: OpcoesEnsaio2t): void {
  const nome = basename(o.db);
  if (nome === "apuracao.sqlite" || nome === "apuracao-2t.sqlite") throw new Error(`o ensaio nunca escreve em ${nome}`);
  mkdirSync(dirname(o.db), { recursive: true });
  if (o.mais === undefined) for (const suf of ["", "-wal", "-shm"]) if (existsSync(o.db + suf)) rmSync(o.db + suf);

  const ref = carregarReferencia();
  const cm58 = lerCm("mun-e006257-cm.json");
  const cm60 = lerCm("2t/mun-e006260-cm.json");
  const abBr = arr(obj(json("2t/br-e006258-ab.json")).abr);
  const abGov = arr(obj(json("2t/br-e006260-ab.json")).abr);
  const ufsPres = abBr.map(a => String(a.cdabr)).filter(u => (UFS_2T as readonly string[]).includes(u));
  const tsUf = new Map(abBr.map(a => [String(a.cdabr), Number(obj(a.s).ts)]));
  const teUf = new Map(abBr.map(a => [String(a.cdabr), Number(obj(a.e).te)]));
  const munNrUf = new Map(abBr.map(a => [String(a.cdabr), Number(a.munnr ?? 0) + Number(a.munpt ?? 0) + Number(a.munf ?? 0)]));
  const ufsGov = abGov.map(a => String(a.cdabr)).filter(u => u !== "br");
  const abSp1t = arr(obj(json("sp-e006257-ab.json")).abr).filter(a => a.tpabr === "mun");
  const munSp = abSp1t.map(a => ({ cd: String(a.cdabr), ts: Number(obj(a.s).ts), te: Number(obj(a.e).te) }));
  const fixturesMun: Record<string, string> = {
    "ac:01392": "2t/ac01392-c0001-e006258-u.json",
    "rj:60011": "2t/rj60011-c0001-e006258-u.json",
    "sp:61018": "2t/sp61018-c0001-e006258-u.json",
    "sp:62910": "2t/sp62910-c0001-e006258-u.json",
    "sp:64777": "2t/sp64777-c0001-e006258-u.json",
    "sp:71072": "2t/sp71072-c0001-e006258-u.json",
  };

  /** Abstenção (%) da UF no 1º turno pela régua; padrão 20. */
  const paUf = (uf: string): number => ref?.abstencao_uf[uf.toUpperCase()]?.pa ?? (uf === "zz" ? 60 : 20);
  /** Abstenção do município: a da régua ± 6 pp (determinística), para acionar os destaques. */
  const paMun = (uf: string, cd: string): number => {
    const base = ref?.municipios[uf.toUpperCase()]?.[cd]?.pa ?? paUf(uf);
    const desvio = (hash01(`pa:${cd}`) - 0.5) * 12;
    return Math.max(2, Math.min(60, base + desvio));
  };

  const db = abrirEscrita(o.db);
  const seq = new Sequenciador(db);
  let passoInicial = 1;
  let idg = 4_000_000;
  const ultimo = new Map<string, number>();
  if (o.mais === undefined) {
    const t = T0_2T - 7_200_000;
    seq.registrar(registroDeArquivos(new Map([[6258, cm58], [6260, cm60]])));
    seq.processar(chave(keyEleC()), enc("ele-c.json"), iso(t));
    seq.processar(chave(keyCm(6258)), enc("mun-e006257-cm.json"), iso(t));
    seq.processar(chave(keyCm(6260)), enc("2t/mun-e006260-cm.json"), iso(t));
    // zerados às 16:00
    const z = T0_2T - 3_600_000;
    seq.processar(chave(keyAb(6258, "br")), enc("2t/br-e006258-ab.json"), iso(z));
    seq.processar(chave(keyAb(6260, "br")), enc("2t/br-e006260-ab.json"), iso(z));
    seq.processar(chave(keyU(6258, 1, "br")), enc("2t/br-c0001-e006258-u.json"), iso(z));
    for (const uf of ufsPres) seq.processar(chave(keyU(6258, 1, "uf", uf)), enc(`2t/${uf}-c0001-e006258-u.json`), iso(z));
    for (const uf of ufsGov) seq.processar(chave(keyU(6260, 3, "uf", uf)), rotularGov(enc(`2t/${uf}-c0003-e006260-u.json`), uf), iso(z));
  } else {
    passoInicial = Number(lerMeta(db, "ensaio_passo") ?? "0") + 1;
    idg = Number(lerMeta(db, "ensaio_idg") ?? String(idg));
    for (const [id, f] of Object.entries(JSON.parse(lerMeta(db, "ensaio_ultimo") ?? "{}") as Record<string, number>)) ultimo.set(id, f);
  }

  /** Emite o arquivo se a unidade avançou ou ainda está em andamento; devolve se emitiu. */
  const mudou = (id: string, f: number): boolean => {
    const ant = ultimo.get(id);
    if (ant !== undefined && ant >= 1 && f >= 1) return false;
    ultimo.set(id, f);
    return true;
  };

  function passo(k: number): void {
    if (k === PASSO_PAUSA_GERAL) return;
    const ger = T0_2T + k * PASSO_MS;
    const tot = ger - 20_000;
    const fuso = (uf: string): number => (uf === "ac" ? -120 : uf === "am" ? -60 : 0);
    let off = 0;
    const proc = (ch: string, corpo: Uint8Array<ArrayBuffer>): void => {
      seq.processar(ch, corpo, iso(ger + 8_000 + off));
      off += 5;
    };
    const rjParado = k >= RJ_PARADO.de && k <= RJ_PARADO.ate;

    // ---- presidente por UF e nacional
    const entradasBr: Record<string, { st: number; munnr?: number; munpt?: number; munf?: number }> = {};
    let stBr = 0;
    let teBr = 0;
    let abstBr = 0;
    const votosBr: Record<string, number> = { 13: 0, 22: 0 };
    for (const uf of ufsPres) {
      const ts = tsUf.get(uf) ?? 0;
      const te = teUf.get(uf) ?? 0;
      const f = fracao(uf, passoEfetivo(uf, k));
      const st = Math.round(ts * f);
      const pa = paUf(uf) + (hash01(`dpa:${uf}`) - 0.5) * 3;
      const vv = Math.round(te * (1 - pa / 100) * 0.95 * f);
      const votos = votosPres(LEAN[uf] ?? 0.5, DERIVA[uf] ?? 0, vv, f);
      for (const [n, v] of Object.entries(votos)) votosBr[n] = (votosBr[n] ?? 0) + v;
      stBr += st;
      teBr += te * f;
      abstBr += te * f * (pa / 100);
      const total = munNrUf.get(uf) ?? 0;
      const munf = f >= 1 ? total : Math.round(total * f ** 3);
      entradasBr[uf] = { st, munf, munpt: f > 0 && f < 1 ? Math.max(1, total - munf) : 0, munnr: f > 0 ? 0 : total };
      if (uf === "rj" && rjParado) continue;
      if (!mudou(`pres:${uf}`, f)) continue;
      idg += 1;
      proc(chave(keyU(6258, 1, "uf", uf)), versaoU2t(`2t/${uf}-c0001-e006258-u.json`, { st, votos, idg, ger, tot, fusoMin: fuso(uf), pa }));
    }
    const tsBr = tsUf.get("br") ?? 0;
    const paBr = teBr > 0 ? (abstBr / teBr) * 100 : 20;
    idg += 1;
    proc(chave(keyU(6258, 1, "br")), versaoU2t("2t/br-c0001-e006258-u.json", { st: Math.min(stBr, tsBr), votos: votosBr, idg, ger, tot, pa: paBr }));

    // ---- municípios de SP (clones da capital) e municípios com fixture fora de SP
    let munfSp = 0;
    let munptSp = 0;
    for (const m of munSp) {
      const id = `sp:${m.cd}`;
      const f = fracao(`sp${m.cd}`, k);
      const st = Math.round(m.ts * f);
      if (st === 0) continue;
      if (f >= 1) munfSp += 1;
      else munptSp += 1;
      if (!mudou(`mun:${id}`, f)) continue;
      const pa = paMun("sp", m.cd);
      const vv = Math.round(m.te * (1 - pa / 100) * 0.95 * f);
      const lean = (LEAN.sp ?? 0.5) + (hash01(`lean:${m.cd}`) - 0.5) * 0.4;
      const votos = votosPres(lean, 0.04, vv, f);
      idg += 1;
      const fixture = fixturesMun[id] ?? fixturesMun["sp:71072"] ?? "";
      const proprio = fixturesMun[id] !== undefined;
      proc(
        chave(keyU(6258, 1, "mu", "sp", m.cd)),
        versaoU2t(fixture, { st, votos, idg, ger, tot, pa, ...(proprio ? {} : { ts: m.ts, te: m.te, cdabr: m.cd }) }),
      );
    }
    for (const [id, fixture] of Object.entries(fixturesMun)) {
      const [uf, cd] = id.split(":") as [string, string];
      if (uf === "sp") continue;
      const d = obj(json(fixture));
      const ts = Number(obj(d.s).ts);
      const te = Number(obj(d.e).te);
      const f = fracao(`${uf}${cd}`, passoEfetivo(uf, k));
      const st = Math.round(ts * f);
      if (st === 0 || (uf === "rj" && rjParado) || !mudou(`mun:${id}`, f)) continue;
      const pa = paMun(uf, cd);
      const vv = Math.round(te * (1 - pa / 100) * 0.95 * f);
      idg += 1;
      proc(chave(keyU(6258, 1, "mu", uf, cd)), versaoU2t(fixture, { st, votos: votosPres(LEAN[uf] ?? 0.5, 0, vv, f), idg, ger, tot, fusoMin: fuso(uf), pa }));
    }

    // ---- monitoramento (-ab): SP com municípios por situação, nacional com todas as UFs
    const sp = entradasBr.sp;
    if (sp) {
      sp.munf = munfSp;
      sp.munpt = munptSp;
      sp.munnr = Math.max(0, munSp.length - munfSp - munptSp);
    }
    entradasBr.br = { st: Math.min(stBr, tsBr) };
    idg += 1;
    proc(chave(keyAb(6258, "br")), versaoAb2t("2t/br-e006258-ab.json", idg, ger, entradasBr));

    // ---- governador
    const entradasGov: Record<string, { st: number }> = {};
    let stGov = 0;
    for (const uf of ufsGov) {
      const fixture = `2t/${uf}-c0003-e006260-u.json`;
      const d = obj(json(fixture));
      const ts = Number(obj(d.s).ts);
      const te = Number(obj(d.e).te);
      const f = fracao(`gov${uf}`, k);
      const st = Math.round(ts * f);
      stGov += st;
      entradasGov[uf] = { st };
      if (!mudou(`gov:${uf}`, f)) continue;
      const pa = paUf(uf) + (hash01(`dpag:${uf}`) - 0.5) * 3;
      const vv = Math.round(te * (1 - pa / 100) * 0.95 * f);
      const cands = arr(d.carg).flatMap(c => arr(c.agr).flatMap(a => arr(a.par).flatMap(p => arr(p.cand).map(x => String(x.n))))).sort();
      const [c1 = "1", c2 = "2"] = cands;
      const lean = 0.5 + (hash01(`gl:${uf}`) - 0.5) * 0.3;
      const deriva = uf === "df" ? 0.3 : uf === "ac" ? -0.3 : 0;
      const p = Math.max(0.05, Math.min(0.95, lean + deriva * (0.5 - f)));
      const v1 = Math.round(vv * p);
      idg += 1;
      proc(
        chave(keyU(6260, 3, "uf", uf)),
        rotularGov(versaoU2t(fixture, { st, votos: { [c1]: v1, [c2]: vv - v1 }, idg, ger, tot, fusoMin: fuso(uf), pa }), uf),
      );
    }
    entradasGov.br = { st: stGov };
    idg += 1;
    proc(chave(keyAb(6260, "br")), versaoAb2t("2t/br-e006260-ab.json", idg, ger, entradasGov));
  }

  const inicio = performance.now();
  const n = o.mais ?? o.passos;
  for (let k = passoInicial; k < passoInicial + n; k++) {
    passo(k);
    seq.gravar([
      { k: "meta", chave: "ensaio_passo", valor: String(k) },
      { k: "meta", chave: "ensaio_idg", valor: String(idg) },
      { k: "meta", chave: "ensaio_ultimo", valor: JSON.stringify(Object.fromEntries(ultimo)) },
    ]);
  }
  fecharEscrita(db);
  console.log(JSON.stringify({ db: o.db, turno: 2, passos: [passoInicial, passoInicial + n - 1], ...seq.contagem, ms: Math.round(performance.now() - inicio) }));
}
