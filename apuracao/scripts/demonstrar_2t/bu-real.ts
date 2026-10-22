// Parte (b) da demonstração: a conferência da totalização paralela contra BUs reais do 1º turno.
// O BU oficial de cada seção (-bu.dat ou -busa.dat, guardado em data/secoes_2026.sqlite) é
// decodificado por src/secoes2t/bu-decode.ts e vira o registro que as views públicas do Supabase
// entregariam (v_bu_publico, v_bu_cargo_publico, v_bu_voto_publico). Esse registro passa pela
// ponte real (PonteParalela + AmostraSecoes), com um Supabase falso que serve as views e um TSE
// falso que serve o aux.json e o BU originais. O texto do evento vem da rota /api/anomalias do
// servidor, a mesma que o telão lê.
import type { Database } from "bun:sqlite";
import { dirname } from "node:path";
import { RelogioFalso } from "../../src/collector/relogio.ts";
import type { ConfigParalela, ConfigSecoes } from "../../src/collector/turno2-config.ts";
import { abrirEscrita, fecharEscrita } from "../../src/db/abrir.ts";
import { Escritor } from "../../src/db/escrita.ts";
import type { ItemLote } from "../../src/db/escrita.ts";
import type { LinhaMunicipio } from "../../src/db/linhas.ts";
import { cargosDoBu, comparar, qrComparavel, rotuloDiferenca } from "../../src/paralela/conferir.ts";
import type { BuPublico, CargoPublico, Diferenca, Situacao, VotoPublico } from "../../src/paralela/conferir.ts";
import { PonteParalela } from "../../src/paralela/ponte.ts";
import { ClienteSupabase } from "../../src/paralela/supabase.ts";
import { bancoNovo } from "../../src/replay/main.ts";
import { AuxSchema, escolherHash, resumoBu } from "../../src/secoes2t/boletim.ts";
import type { BoletimUrna } from "../../src/secoes2t/bu-decode.ts";
import { decodificarBu } from "../../src/secoes2t/bu-decode.ts";
import { AmostraSecoes } from "../../src/secoes2t/coletor.ts";
import type { Obter } from "../../src/secoes2t/coletor.ts";
import { chaveSecao, urlsUrna } from "../../src/secoes2t/urls.ts";
import type { SecaoChave } from "../../src/secoes2t/urls.ts";
import type { AnomaliaOut } from "../../src/server/api-anomalias.ts";
import { criarServidor } from "../../src/server/main.ts";
import { T0_1T_MS } from "../../src/turno2/comum.ts";

export const PLEITO_1T = 3220;
export const ELE_FEDERAL_1T = 6257;
const PRESIDENTE = 1;

const sha256 = (b: Uint8Array): string => new Bun.CryptoHasher("sha256").update(b).digest("hex");

// ---------------------------------------------------------------- seção real

export interface SecaoReal {
  s: SecaoChave;
  municipio: string | null;
  aux: Uint8Array<ArrayBuffer>;
  bu: Uint8Array<ArrayBuffer>;
  /** hash e arquivo escolhidos pelo próprio coletor (escolherHash) a partir do aux.json */
  hash: string;
  buNome: string;
  buSha256: string;
  boletim: BoletimUrna;
}

/** Junta aux.json e BU originais; falha se o aux não apontar um BU. */
export function secaoReal(s: SecaoChave, municipio: string | null, aux: Uint8Array<ArrayBuffer>, bu: Uint8Array<ArrayBuffer>): SecaoReal {
  const esc = escolherHash(AuxSchema.parse(JSON.parse(new TextDecoder().decode(aux))));
  if (esc === null) throw new Error(`aux.json sem BU: ${chaveSecao(s)}`);
  return { s, municipio, aux, bu, hash: esc.hash, buNome: esc.bu, buSha256: sha256(bu), boletim: decodificarBu(bu).bu };
}

/** Presidente com pelo menos dois números votados e o mais votado com voto: dá para mover um voto. */
function servePraMover(b: BoletimUrna): boolean {
  const pres = b.resultadosVotacaoPorEleicao.find((e) => e.idEleicao === ELE_FEDERAL_1T)?.resultadosVotacao.flatMap((r) => r.totaisVotosCargo)
    .find((t) => t.codigoCargo.valor === PRESIDENTE);
  return (pres?.votosVotaveis.filter((v) => v.tipoVoto === 1 && v.quantidadeVotos > 0).length ?? 0) >= 2;
}

export interface ConferenciaBanco {
  hash_igual: boolean;
  arquivo_igual: boolean;
  sha256_igual: boolean;
}

/**
 * Regra declarada: em cada UF pedida, a primeira seção por (município, zona, seção) com BU
 * guardado cujo presidente tenha dois números votados. `segunda` pega a seguinte da mesma UF.
 */
export function lerSecoesReais(db: Database, ufs: readonly string[], segunda = false): (SecaoReal & { banco: ConferenciaBanco })[] {
  type R = { uf: string; mun: string; zona: number; secao: number; aux_json: string; bu_gz: Uint8Array; hash: string | null; bu_nome: string | null; bu_sha256: string | null };
  const q = db.query<R, [string]>(
    `SELECT uf, mun, zona, secao, aux_json, bu_gz, hash, bu_nome, bu_sha256 FROM secao
     WHERE uf = ? AND bu_gz IS NOT NULL AND aux_json IS NOT NULL ORDER BY mun, zona, secao LIMIT 40`,
  );
  const out: (SecaoReal & { banco: ConferenciaBanco })[] = [];
  for (const uf of ufs) {
    let achadas = 0;
    for (const r of q.all(uf)) {
      const sec = secaoReal(
        { uf: r.uf, mun: r.mun, zona: r.zona, secao: r.secao }, null, new TextEncoder().encode(r.aux_json), new Uint8Array(Bun.gunzipSync(new Uint8Array(r.bu_gz))),
      );
      if (!servePraMover(sec.boletim)) continue;
      achadas += 1;
      if (segunda && achadas < 2) continue;
      out.push({ ...sec, banco: { hash_igual: r.hash === sec.hash, arquivo_igual: r.bu_nome === sec.buNome, sha256_igual: r.bu_sha256 === sec.buSha256 } });
      break;
    }
  }
  return out;
}

// ---------------------------------------------------------------- registro da paralela

export interface RegistroParalela {
  bu: BuPublico;
  cargos: CargoPublico[];
  votos: VotoPublico[];
}

export interface OpcoesRegistro {
  recebidoEm: string;
  hashFinal: string;
  pleito?: number;
  turno?: number;
}

const TIPO = { nominal: 1, branco: 2, nulo: 3, legenda: 4 } as const;

/** ORIG do QR pela origem do arquivo (manual do QR do BU, seção 1.4.2): urna, RED ou Sistema de Apuração. */
export function origemQr(b: BoletimUrna): "VOTA" | "RED" | "SA" {
  if (b.urna.tipoArquivo >= 3) return "SA";
  return b.urna.tipoArquivo === 2 ? "RED" : "VOTA";
}

/**
 * O BU decodificado no formato das views públicas da totalização paralela: uma linha por cargo
 * (aptos, nominais, legenda, brancos, nulos, comparecimento) e uma por número votado; legenda
 * como "LEGP<partido>", igual ao QR. No Sistema de Apuração o QR não traz APTO nem COMP (manual,
 * seção 1.4.2): aptos e comparecimento do boletim ficam nulos, como chegariam do Supabase.
 */
export function registroParalela(b: BoletimUrna, s: SecaoChave, id: number, o: OpcoesRegistro): RegistroParalela {
  const cargos: CargoPublico[] = [];
  const votos: VotoPublico[] = [];
  for (const e of b.resultadosVotacaoPorEleicao) {
    for (const rv of e.resultadosVotacao) {
      for (const tc of rv.totaisVotosCargo) {
        const cargo = tc.codigoCargo.valor;
        const c: CargoPublico = { bu_id: id, idel: e.idEleicao, cargo, tipo: rv.tipoCargo, apta: e.qtdEleitoresAptos, nomi: 0, legc: 0, bran: 0, nulo: 0, totc: rv.qtdComparecimento };
        const porNumero = new Map<string, VotoPublico>();
        for (const v of tc.votosVotaveis) {
          const q = v.quantidadeVotos;
          let chave: string | null = null;
          if (v.tipoVoto === TIPO.nominal) {
            c.nomi += q;
            chave = String(v.codigo);
          } else if (v.tipoVoto === TIPO.legenda) {
            c.legc += q;
            chave = `LEGP${v.partido}`;
          } else if (v.tipoVoto === TIPO.branco) {
            c.bran += q;
          } else if (v.tipoVoto === TIPO.nulo) {
            c.nulo += q;
          }
          if (chave === null) continue;
          const atual = porNumero.get(chave);
          if (atual) atual.votos += q;
          else porNumero.set(chave, { bu_id: id, idel: e.idEleicao, cargo, partido: v.tipoVoto === TIPO.legenda ? v.partido : null, candidato: chave, votos: q });
        }
        cargos.push(c);
        votos.push(...porNumero.values());
      }
    }
  }
  // mesma ordem das views (order=bu_id,idel,cargo e bu_id,idel,cargo,candidato)
  cargos.sort((x, y) => x.idel - y.idel || x.cargo - y.cargo);
  votos.sort((x, y) => x.idel - y.idel || x.cargo - y.cargo || (x.candidato < y.candidato ? -1 : x.candidato > y.candidato ? 1 : 0));
  const fed = b.resultadosVotacaoPorEleicao.find((e) => e.idEleicao === ELE_FEDERAL_1T) ?? b.resultadosVotacaoPorEleicao[0];
  const orig = origemQr(b);
  const bu: BuPublico = {
    id, recebido_em: o.recebidoEm, uf: s.uf, muni: Number(s.mun), zona: s.zona, secao: s.secao, fase: "O", pleito: o.pleito ?? PLEITO_1T, turno: o.turno ?? 1,
    orig, aptos: orig === "SA" ? null : (fed?.qtdEleitoresAptos ?? null), comparecimento: orig === "SA" ? null : b.qtdEleitoresCompareceram, hash_final: o.hashFinal,
  };
  return { bu, cargos, votos };
}

/** Cópia com um voto de presidente movido do número mais votado para o segundo. */
export function moverVoto(r: RegistroParalela): { reg: RegistroParalela; de: string; para: string; antes: [number, number] } {
  const nominais = r.votos
    .filter((v) => v.idel === ELE_FEDERAL_1T && v.cargo === PRESIDENTE && !v.candidato.startsWith("LEGP"))
    .sort((a, b) => b.votos - a.votos || Number(a.candidato) - Number(b.candidato));
  const de = nominais[0];
  const para = nominais[1];
  if (de === undefined || para === undefined || de.votos < 1) throw new Error("presidente sem dois números votados");
  const votos = r.votos.map((v) => (v === de ? { ...v, votos: v.votos - 1 } : v === para ? { ...v, votos: v.votos + 1 } : { ...v }));
  return { reg: { bu: { ...r.bu }, cargos: r.cargos.map((c) => ({ ...c })), votos }, de: de.candidato, para: para.candidato, antes: [de.votos, para.votos] };
}

/**
 * Cópia com o comparecimento alterado em `delta`: o do boletim (COMP) quando o QR o traz; no
 * Sistema de Apuração, que não traz COMP, o do cargo de presidente (TOTC).
 */
export function comComparecimento(r: RegistroParalela, delta: number): { reg: RegistroParalela; campo: "COMP" | "TOTC" } {
  const cargos = r.cargos.map((c) => ({ ...c }));
  const votos = r.votos.map((v) => ({ ...v }));
  if (r.bu.comparecimento !== null) return { reg: { bu: { ...r.bu, comparecimento: r.bu.comparecimento + delta }, cargos, votos }, campo: "COMP" };
  const pres = cargos.find((c) => c.idel === ELE_FEDERAL_1T && c.cargo === PRESIDENTE);
  if (!pres) throw new Error("BU sem presidente");
  pres.totc += delta;
  return { reg: { bu: { ...r.bu }, cargos, votos }, campo: "TOTC" };
}

/** Comparação pura, pelas mesmas funções da ponte: qrComparavel(cargosDoBu(...)) contra resumoBu(...).votos. */
export function compararComOficial(r: RegistroParalela, sec: SecaoReal): Diferenca[] {
  const oficial = resumoBu(sec.boletim, sec.s.uf, ELE_FEDERAL_1T).votos;
  return comparar(qrComparavel(r.bu.comparecimento, cargosDoBu(r.cargos, r.votos)), oficial);
}

// ---------------------------------------------------------------- casos

export type TipoCaso = "igual" | "voto_movido" | "comparecimento_mais_1" | "aux_nao_publicado";

export interface Caso {
  id: number;
  tipo: TipoCaso;
  secao: SecaoReal;
  reg: RegistroParalela;
  esperado: Situacao;
  nota: string;
}

/**
 * Para cada seção publicada: o próprio BU (igual), um voto movido (divergente) e o comparecimento
 * mais 1 (divergente). A seção `semAux` entra com o próprio BU, mas o TSE falso ainda não publicou
 * o aux.json dela (404), o estado em que a paralela recebe o BU antes do TSE.
 */
export function montarCasos(publicadas: readonly SecaoReal[], semAux: SecaoReal, recebidoEm: string): Caso[] {
  const casos: Caso[] = [];
  const reg = (sec: SecaoReal, id: number): RegistroParalela =>
    registroParalela(sec.boletim, sec.s, id, { recebidoEm, hashFinal: `sha256 do ${sec.buNome}: ${sec.buSha256}` });
  for (const sec of publicadas) {
    let id = casos.length + 1;
    casos.push({ id, tipo: "igual", secao: sec, reg: reg(sec, id), esperado: "igual", nota: "BU idêntico ao oficial" });
    id += 1;
    const m = moverVoto(reg(sec, id));
    casos.push({ id, tipo: "voto_movido", secao: sec, reg: m.reg, esperado: "divergente", nota: `um voto de presidente do ${m.de} (${m.antes[0]}) para o ${m.para} (${m.antes[1]})` });
    id += 1;
    const c = comComparecimento(reg(sec, id), 1);
    const onde = c.campo === "COMP" ? "do boletim (COMP)" : "de presidente (TOTC; o QR do Sistema de Apuração não traz COMP)";
    casos.push({ id, tipo: "comparecimento_mais_1", secao: sec, reg: c.reg, esperado: "divergente", nota: `comparecimento ${onde} mais 1` });
  }
  const id = casos.length + 1;
  casos.push({ id, tipo: "aux_nao_publicado", secao: semAux, reg: reg(semAux, id), esperado: "tse_ainda_nao_publicou", nota: "aux.json ainda não publicado pelo TSE (404)" });
  return casos;
}

// ---------------------------------------------------------------- ponte real com fontes falsas

/** PostgREST mínimo: filtros gt/gte/lte numéricos, offset/limit e Content-Range. */
export function supabaseFalso(dados: Readonly<Record<string, readonly unknown[]>>): (url: string) => Promise<Response> {
  return (url) => {
    const u = new URL(url);
    const view = u.pathname.split("/").pop() ?? "";
    let linhas = [...(dados[view] ?? [])] as Record<string, number>[];
    for (const [k, v] of u.searchParams) {
      const m = /^(gt|gte|lte)\.(\d+)$/.exec(v);
      if (!m) continue;
      const n = Number(m[2]);
      linhas = linhas.filter((x) => (m[1] === "gt" ? (x[k] ?? 0) > n : m[1] === "gte" ? (x[k] ?? 0) >= n : (x[k] ?? 0) <= n));
    }
    const offset = Number(u.searchParams.get("offset") ?? 0);
    const limit = Number(u.searchParams.get("limit") ?? 1000);
    const pagina = linhas.slice(offset, offset + limit);
    const faixa = pagina.length === 0 ? `*/${linhas.length}` : `${offset}-${offset + pagina.length - 1}/${linhas.length}`;
    return Promise.resolve(new Response(JSON.stringify(pagina), { status: 200, headers: { "content-range": faixa } }));
  };
}

export interface ConferenciaLida {
  bu_id: number;
  situacao: Situacao;
  diferencas: Diferenca[];
  tse_sha256: string | null;
}

export interface ResultadoPonte {
  db: string;
  /** primeiro ciclo, antes de a amostra buscar qualquer seção */
  antes: ConferenciaLida[];
  /** segundo ciclo, depois da busca de aux.json e BU */
  depois: ConferenciaLida[];
  requisicoes_tse: { url: string; status: number }[];
  /** /api/anomalias do servidor sobre o banco da demonstração */
  anomalias: AnomaliaOut[];
  /** /api/2t/paralela */
  paralela: { conferencia: Record<string, number>; recebidos: Record<string, number>; erro: string | null };
}

export interface OpcoesPonte {
  db: string;
  municipios: readonly LinhaMunicipio[];
  /** relógio da demonstração (ISO) */
  agora: string;
}

const cfgSecoes = (dirCs: string): ConfigSecoes => ({
  amostra: false, porUf: 0, estadual: 0, ufsEstaduais: [], intervaloS: 900, intervaloParalelaS: 300, rps: 1000, concorrencia: 4,
  semente: "demonstracao", inicioMs: 0, dirCs, timeoutMs: 1000,
});

const SUPABASE_DEMO = "https://supabase.demonstracao.invalid";

export async function conferirPelaPonte(casos: readonly Caso[], o: OpcoesPonte): Promise<ResultadoPonte> {
  bancoNovo(o.db);
  const db = abrirEscrita(o.db);
  const w = new Escritor(db);
  const gravar = (i: ItemLote[]): void => {
    w.gravarLote(i);
  };
  gravar([{ k: "municipio", rows: o.municipios }]);
  const relogio = new RelogioFalso(Date.parse(o.agora));
  const urls = urlsUrna(PLEITO_1T);
  const tse = new Map<string, Uint8Array<ArrayBuffer>>();
  for (const c of casos) {
    if (c.tipo === "aux_nao_publicado") continue;
    tse.set(urls.aux(c.secao.s), c.secao.aux);
    tse.set(urls.arquivo(c.secao.s, c.secao.hash, c.secao.buNome), c.secao.bu);
  }
  const requisicoes: { url: string; status: number }[] = [];
  const obter: Obter = (url) => {
    const corpo = tse.get(url);
    requisicoes.push({ url, status: corpo === undefined ? 404 : 200 });
    return Promise.resolve(
      corpo === undefined
        ? { status: 404, corpo: new TextEncoder().encode("<Code>NoSuchKey</Code>"), retryAfter: null, erro: "HTTP 404" }
        : { status: 200, corpo, retryAfter: null, erro: null },
    );
  };
  const amostra = new AmostraSecoes({
    cfg: cfgSecoes(dirname(o.db)), pleito: PLEITO_1T, eleFederal: ELE_FEDERAL_1T, t0Ms: T0_1T_MS, db, gravar, relogio, urls, obter,
    dormir: (ms) => Bun.sleep(Math.min(ms, 5)),
  });
  const ordenar = <T extends { bu_id: number; idel: number; cargo: number }>(l: T[]): T[] => l.sort((a, b) => a.bu_id - b.bu_id || a.idel - b.idel || a.cargo - b.cargo);
  const dados: Record<string, unknown[]> = {
    v_bu_publico: casos.map((c) => c.reg.bu),
    v_bu_cargo_publico: ordenar(casos.flatMap((c) => c.reg.cargos)),
    v_bu_voto_publico: ordenar(casos.flatMap((c) => c.reg.votos)),
    v_estatisticas: [], v_cobertura_uf: [], v_conflito: [], v_totais_br: [], v_totais_uf: [],
  };
  const cfg: ConfigParalela = { ativo: true, intervaloS: 60, url: SUPABASE_DEMO, chave: "demonstracao", janela: 2000 };
  const cliente = new ClienteSupabase({ url: SUPABASE_DEMO, chave: "demonstracao", fetchImpl: supabaseFalso(dados) });
  const ponte = new PonteParalela({ cfg, pleito: PLEITO_1T, eleFederal: ELE_FEDERAL_1T, db, gravar, relogio, cliente, amostra });
  const lerConferencias = (): ConferenciaLida[] =>
    db
      .query<{ bu_id: number; situacao: Situacao; diferencas_json: string | null; tse_sha256: string | null }, []>(
        "SELECT bu_id, situacao, diferencas_json, tse_sha256 FROM paralela_conferencia ORDER BY bu_id",
      )
      .all()
      .map((r) => ({ bu_id: r.bu_id, situacao: r.situacao, diferencas: r.diferencas_json === null ? [] : (JSON.parse(r.diferencas_json) as Diferenca[]), tse_sha256: r.tse_sha256 }));

  await amostra.preparar();
  await ponte.ciclo();
  const antes = lerConferencias();
  const loop = amostra.rodar();
  const fim = Date.now() + 10_000;
  const pronta = (c: Caso): boolean => {
    const e = amostra.estado(c.secao.s);
    return e !== null && (e.feito || e.status === "aux_404");
  };
  while (!casos.every(pronta)) {
    if (Date.now() > fim) throw new Error("a amostra não buscou as seções em 10 s");
    await Bun.sleep(5);
  }
  await amostra.parar();
  await loop;
  relogio.avancar(60_000);
  await ponte.ciclo();
  const depois = lerConferencias();
  fecharEscrita(db);

  const srv = criarServidor({ dbPath: o.db, port: 0, log: false, agora: () => new Date(relogio.agora()).toISOString() });
  try {
    const anomalias = (await (await fetch(`${srv.url}/api/anomalias?limit=200`)).json()) as AnomaliaOut[];
    const p = (await (await fetch(`${srv.url}/api/2t/paralela`)).json()) as ResultadoPonte["paralela"];
    return { db: o.db, antes, depois, requisicoes_tse: requisicoes, anomalias, paralela: { conferencia: p.conferencia, recebidos: p.recebidos, erro: p.erro } };
  } finally {
    await srv.parar();
  }
}

/** Rótulos curtos das diferenças (o que o telão escreve). */
export const rotulos = (d: readonly Diferenca[]): string[] => d.map(rotuloDiferenca);
