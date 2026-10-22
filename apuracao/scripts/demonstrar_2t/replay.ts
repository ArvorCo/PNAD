// Parte (a) da demonstração: a noite real de 04/10/2026 relida pelo coletor do 2º turno.
// Cada leitura gravada na tabela fetch de data/apuracao.sqlite para os arquivos -u de presidente
// (br, 27 UFs e ZZ) e para os -ab das UFs volta a passar por processar(), o mesmo pipeline do
// coletor, com o relógio na hora em que a resposta chegou (capturado_em da versão; início mais
// duração nas demais). Corpo novo e corpo igual voltam com o blob original, para o próprio
// coletor decidir entre versão nova, cópia regressiva e corpo repetido. instalarTurno2 liga o
// detector de pausas, viradas, fechamentos e régua como no ar; o turno 1 (eleição 6257, t0 às
// 17:00 de 04/10) vem da configuração, sem tocar em src/turno2/comum.ts. A avaliação de 30 s
// roda pelo Agendador, com a fila vazia: o replay nunca busca nada na rede. O banco de origem
// é aberto só para leitura; tudo é gravado num banco novo com o esquema real.
import type { Database } from "bun:sqlite";
import { Agendador } from "../../src/collector/agendador.ts";
import type { Coletor } from "../../src/collector/bootstrap.ts";
import type { CtxProc } from "../../src/collector/contexto.ts";
import { EstadoArquivos } from "../../src/collector/estado-arquivos.ts";
import { Limitador } from "../../src/collector/limitador.ts";
import { Lote } from "../../src/collector/lote.ts";
import { processar } from "../../src/collector/processar.ts";
import { AlertasRegua, REGUA_PADRAO } from "../../src/collector/regua.ts";
import type { UfAndamento } from "../../src/collector/regua.ts";
import { isoDe, RelogioFalso } from "../../src/collector/relogio.ts";
import { AVALIACAO_MS, FRESCOR_MS, instalarTurno2 } from "../../src/collector/turno2.ts";
import { lerConfig } from "../../src/config.ts";
import { abrirEscrita, fecharEscrita } from "../../src/db/abrir.ts";
import { Escritor } from "../../src/db/escrita.ts";
import type { EventoNovo, ItemLote } from "../../src/db/escrita.ts";
import { parseCorpo } from "../../src/parse/schemas.ts";
import { bancoNovo } from "../../src/replay/main.ts";
import { chave, keyU, registroDeArquivos } from "../../src/tse/urls.ts";
import { minutosDesde17h, T0_1T_MS } from "../../src/turno2/comum.ts";
import { atrasoVsReferencia, carregarReferencia } from "../../src/turno2/referencia.ts";
import type { ClasseFetch, FetchResult } from "../../src/types.ts";

export const ELE_1T = 6257;

/** Fim padrão da janela: 13:00 de Brasília de 05/10, depois da última versão nacional (12:51:47). */
export const FIM_PADRAO = "2026-10-05T16:00:00.000Z";

interface LinhaFetch1t {
  id: number;
  aid: number;
  ini: string;
  dur: number | null;
  classe: string;
  status: number | null;
  sha: string | null;
  cap: string | null;
  reg: number | null;
  bytes: number | null;
  erro: string | null;
}

interface Leitura {
  t: number;
  id: number;
  chave: string;
  ini: string;
  iniMs: number;
  dur: number;
  classe: ClasseFetch;
  status: number | null;
  sha: string | null;
  bytes: number;
  erro: string | null;
  /** corpo que o coletor do 1º turno marcou como regressivo (regra anterior, por idg) */
  regressivo1t: boolean;
}

export interface Fonte1t {
  /** leituras em ordem de chegada da resposta */
  leituras: Leitura[];
  cm: Parameters<typeof registroDeArquivos>[0];
  arquivos: { u: number; ab: number };
  contagem: Record<string, number>;
  inicioMs: number;
  fimMs: number;
}

const CLASSES: ReadonlySet<string> = new Set([
  "ok", "igual", "nao_modificado", "nao_existe", "negado", "limite", "erro_servidor", "timeout", "erro_rede", "corpo_invalido",
]);

/** Lê do banco do 1º turno (somente leitura) tudo o que o replay precisa, uma vez. */
export function lerFonte1t(db1t: Database, fim: string = FIM_PADRAO): Fonte1t {
  const cmRow = db1t
    .query<{ gz: Uint8Array }, [number]>(
      `SELECT b.gz FROM arquivo a JOIN snapshot s ON s.id = a.ultimo_snapshot_id JOIN blob b ON b.sha256 = s.sha256
       WHERE a.tipo = 'cm' AND a.eleicao_cd = ?`,
    )
    .get(ELE_1T);
  if (!cmRow) throw new Error("cm da eleição 6257 ausente no banco do 1º turno");
  const p = parseCorpo("cm", Bun.gunzipSync(new Uint8Array(cmRow.gz)));
  if (!p.ok || p.parsed.tipo !== "cm") throw new Error("cm da eleição 6257 ilegível");
  const cm = new Map([[ELE_1T, p.parsed.data]]);

  const arqs = db1t
    .query<{ id: number; chave: string; tipo: string }, [number]>(
      `SELECT id, chave, tipo FROM arquivo WHERE eleicao_cd = ? AND nivel IN ('br', 'uf')
         AND ((tipo = 'u' AND cargo_cd = 1) OR (tipo = 'ab' AND nivel = 'uf'))`,
    )
    .all(ELE_1T);
  const chaves = new Map(arqs.map((a) => [a.id, a.chave] as const));
  const ids = (tipo: string): string => arqs.filter((a) => a.tipo === tipo).map((a) => a.id).join(",");
  const sel = `SELECT f.id, f.arquivo_id AS aid, f.iniciado_em AS ini, f.duracao_ms AS dur, f.classe, f.http_status AS status,
      COALESCE(s.sha256, f.body_sha256) AS sha, s.capturado_em AS cap, s.regressivo AS reg, f.bytes, f.erro
    FROM fetch f LEFT JOIN snapshot s ON s.id = f.snapshot_id`;
  // -u de presidente: toda leitura (o frescor do motor depende das 304 e dos erros);
  // -ab das UFs: só as leituras com corpo (a régua de abstenção lê o conteúdo, não o frescor)
  const linhas = [
    ...db1t.query<LinhaFetch1t, [string]>(`${sel} WHERE f.arquivo_id IN (${ids("u")}) AND f.iniciado_em < ?`).all(fim),
    ...db1t.query<LinhaFetch1t, [string]>(`${sel} WHERE f.arquivo_id IN (${ids("ab")}) AND f.classe IN ('ok', 'igual') AND f.iniciado_em < ?`).all(fim),
  ];
  // corpo repetido ("igual") de uma cópia que o 1º turno marcou como regressiva também era descartado
  const shaRegressivo = new Set(linhas.filter((l) => l.reg === 1 && l.sha !== null).map((l) => `${l.aid}|${l.sha}`));
  const contagem: Record<string, number> = {};
  const leituras: Leitura[] = [];
  for (const l of linhas) {
    const chave = chaves.get(l.aid);
    if (chave === undefined || !CLASSES.has(l.classe)) continue;
    const iniMs = Date.parse(l.ini);
    const dur = l.dur ?? 0;
    const t = l.cap !== null ? Date.parse(l.cap) : iniMs + dur;
    contagem[l.classe] = (contagem[l.classe] ?? 0) + 1;
    const regressivo1t = l.reg === 1 || (l.classe === "igual" && shaRegressivo.has(`${l.aid}|${l.sha}`));
    leituras.push({ t, id: l.id, chave, ini: l.ini, iniMs, dur, classe: l.classe as ClasseFetch, status: l.status, sha: l.sha, bytes: l.bytes ?? 0, erro: l.erro, regressivo1t });
  }
  leituras.sort((a, b) => a.t - b.t || a.id - b.id);
  const primeira = leituras[0];
  if (primeira === undefined) throw new Error("nenhuma leitura de presidente no banco do 1º turno");
  return {
    leituras, cm, contagem, arquivos: { u: arqs.filter((a) => a.tipo === "u").length, ab: arqs.filter((a) => a.tipo === "ab").length },
    inicioMs: primeira.t, fimMs: Date.parse(fim),
  };
}

export interface OpcoesReplay {
  db1t: Database;
  fonte: Fonte1t;
  /** banco de saída (recriado) */
  saida: string;
  referencia: string;
  /** APURACAO_PAUSA_MIN */
  limiarMin: number;
  /**
   * Contraprova da régua: um segundo AlertasRegua, fora do banco, lê os mesmos estados de UF com o
   * relógio adiantado deste tanto de minutos, como se o 2º turno repetisse o 1º com esse atraso.
   */
  contraprovaAtrasoMin?: number;
  /**
   * "anterior" reproduz a regra de versão do coletor até 22/10 (idg menor = cópia regressiva):
   * o corpo que o coletor do 1º turno marcou como regressivo volta como leitura sem corpo, que é
   * o efeito que ele tinha (frescor atualizado, nenhuma versão nova para o motor).
   */
  regra?: "atual" | "anterior";
}

/** Alerta de atraso recalculado pela régua anterior (interpolação linear entre versões), só para comparação. */
export interface AtrasoInterpolado {
  em: string;
  uf: string;
  patamar_min: number;
  atraso_min: number;
}

export interface ResumoReplay {
  saida: string;
  limiar_min: number;
  limiar_uf_min: number;
  leituras: number;
  avaliacoes: number;
  versoes_presidente: { aceitas: number; regressivas: number };
  regra: "atual" | "anterior";
  contraprova: EventoNovo[];
  atraso_interpolado: AtrasoInterpolado[];
  logs: Record<string, unknown>[];
  ms: number;
}

/** Relê a noite pelo coletor; devolve o resumo e deixa os eventos no banco `saida`. */
export async function replayNoite(o: OpcoesReplay): Promise<ResumoReplay> {
  const t0 = performance.now();
  const regra = o.regra ?? "atual";
  bancoNovo(o.saida);
  const db = abrirEscrita(o.saida);
  db.run("PRAGMA synchronous = OFF"); // banco descartável da demonstração: refeito a cada execução
  const escritor = new Escritor(db);
  const registro: ItemLote[] = [...registroDeArquivos(o.fonte.cm)].map((row) => ({ k: "arquivo", row }));
  escritor.gravarLote(registro);
  const relogio = new RelogioFalso(o.fonte.inicioMs);
  const estado = EstadoArquivos.carregarDoBanco(db);
  const lote = new Lote(escritor, relogio);
  const ctx: CtxProc = {
    db, estado, lote, relogio, knobs: { zonas: "final", minIntervaloMuS: 300, sweepMin: 0, concurrency: 32 }, pleito: 3220,
    driftContagem: new Map(), driftVisto: new Set(), aleatorio: () => 0.5,
  };
  const config = { ...lerConfig({ APURACAO_ELEICOES: String(ELE_1T), APURACAO_PLEITO: "3220" }), dbPath: o.saida };
  const c: Coletor = { config, db, escritor, lote, estado, ctx, relogio, http: {} };
  const limitador = new Limitador(relogio);
  const ag = new Agendador({
    relogio, ctx, limitador,
    fetcher: () => Promise.reject(new Error("o replay não busca nada na rede")),
  });
  const logs: Record<string, unknown>[] = [];
  const t2 = instalarTurno2(c, ag, limitador, (x) => { if (x.t !== "turno2") logs.push(x); }, {
    APURACAO_SECOES: "0", APURACAO_PARALELA: "0", APURACAO_REFERENCIA_1T: o.referencia, APURACAO_PAUSA_MIN: String(o.limiarMin),
  });

  const contraprova: EventoNovo[] = [];
  const atrasoInterpolado: AtrasoInterpolado[] = [];
  const ref = carregarReferencia(o.referencia);
  const atrasoMin = o.contraprovaAtrasoMin ?? 0;
  const regua2 = atrasoMin > 0 ? new AlertasRegua(ref, { ...REGUA_PADRAO, ele: ELE_1T, t0Ms: T0_1T_MS - atrasoMin * 60_000 }) : null;
  const patamarInterp = new Map<string, number>();
  // mesma seleção de UFs da avaliação de instalarTurno2: arquivo lido há menos de FRESCOR_MS e sem erro
  ag.aCada(AVALIACAO_MS, (agora) => {
    const ufs: UfAndamento[] = [];
    for (const uf of t2.detector.ufs) {
      const fs = estado.porChave.get(chave(keyU(ELE_1T, 1, "uf", uf)));
      const t = fs?.totaisAnteriores;
      if (!fs || !t || !fs.ativo || fs.errosSeguidos !== 0 || fs.ultimoFetchEm === null || agora - fs.ultimoFetchEm >= FRESCOR_MS) continue;
      ufs.push({ uf, pst: t.pst ?? 0, st: t.st ?? 0, ts: t.ts ?? 0 });
    }
    if (regua2) contraprova.push(...regua2.avaliarAtraso(agora, ufs));
    const min = minutosDesde17h(isoDe(agora), T0_1T_MS);
    if (ref === null || min === null || min < 0) return;
    for (const u of ufs) {
      const curva = ref.curvas.uf[u.uf.toUpperCase()];
      if (u.ts <= 0 || u.st >= u.ts || !curva || curva.length === 0) continue;
      const a = atrasoVsReferencia(curva, u.pst, min);
      if (a === null || a < REGUA_PADRAO.patamarMin) continue;
      const p = Math.floor(a / REGUA_PADRAO.patamarMin) * REGUA_PADRAO.patamarMin;
      if (p <= (patamarInterp.get(u.uf) ?? 0)) continue;
      patamarInterp.set(u.uf, p);
      atrasoInterpolado.push({ em: isoDe(agora), uf: u.uf, patamar_min: p, atraso_min: a });
    }
  });

  const blob = db1tBlob(o.db1t);
  let proxima = o.fonte.inicioMs + AVALIACAO_MS;
  let avaliacoes = 0;
  const avaliarAte = (t: number): void => {
    while (proxima <= t) {
      relogio.definir(proxima);
      ag.passo();
      avaliacoes += 1;
      proxima += AVALIACAO_MS;
    }
  };
  for (const l of o.fonte.leituras) {
    avaliarAte(l.t);
    relogio.definir(l.t);
    const fs = estado.porChave.get(l.chave);
    if (!fs) throw new Error(`arquivo fora do registro: ${l.chave}`);
    const retido = regra === "anterior" && l.regressivo1t;
    const comCorpo = (l.classe === "ok" || l.classe === "igual") && !retido;
    const body = comCorpo && l.sha !== null ? blob(l.sha) : null;
    const r: FetchResult = {
      classe: retido ? "nao_modificado" : comCorpo ? (body === null ? "erro_rede" : "ok") : l.classe, iniciadoEm: l.ini, duracaoMs: l.dur, condicional: !comCorpo,
      httpStatus: l.status, etag: null, lastModified: null, servidorDate: null, cacheHdr: null, age: null, retryAfterS: null,
      bytes: body?.byteLength ?? l.bytes, body, bodySha256: body === null ? null : l.sha, erro: body === null && comCorpo ? "blob ausente" : l.erro,
    };
    processar(ctx, { arquivoId: fs.id, chave: fs.chave, url: fs.url, prioridade: "t0", due: 0, motivo: "periodico" }, fs, r, l.iniMs);
    if (lote.tamanho >= 50) lote.gravar();
  }
  avaliarAte(o.fonte.fimMs);
  lote.gravar();
  await t2.parar();
  lote.gravar();
  const v = db
    .query<{ aceitas: number; regressivas: number }, [number]>(
      `SELECT COALESCE(SUM(s.regressivo = 0), 0) AS aceitas, COALESCE(SUM(s.regressivo = 1), 0) AS regressivas
       FROM snapshot s JOIN arquivo a ON a.id = s.arquivo_id WHERE a.tipo = 'u' AND a.eleicao_cd = ? AND a.cargo_cd = 1`,
    )
    .get(ELE_1T) ?? { aceitas: 0, regressivas: 0 };
  fecharEscrita(db);
  return {
    saida: o.saida, limiar_min: t2.cfg.pausas.limiarNacionalMin, limiar_uf_min: t2.cfg.pausas.limiarUfMin, leituras: o.fonte.leituras.length,
    avaliacoes, versoes_presidente: v, regra, contraprova, atraso_interpolado: atrasoInterpolado, logs, ms: Math.round(performance.now() - t0),
  };
}

function db1tBlob(db1t: Database): (sha: string) => Uint8Array<ArrayBuffer> | null {
  const q = db1t.query<{ gz: Uint8Array }, [string]>("SELECT gz FROM blob WHERE sha256 = ?");
  return (sha) => {
    const r = q.get(sha);
    return r ? new Uint8Array(Bun.gunzipSync(new Uint8Array(r.gz))) : null;
  };
}

export const isoBrt = (iso: string | null): string => {
  if (iso === null) return "";
  const t = Date.parse(iso);
  if (!Number.isFinite(t)) return "";
  return isoDe(t - 3 * 3600_000).slice(0, 19).replace("T", " ");
};
