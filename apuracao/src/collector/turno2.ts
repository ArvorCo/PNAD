// Motor do 2º turno dentro do coletor (escritor único): detector de pausas, alertas contra a
// régua do 1º turno, amostra ao vivo de seções e ponte com a totalização paralela. Tudo grava
// pelo mesmo lote do coletor; nada usa a fila nem o balde de fichas do coletor principal.
import { carregarReferencia } from "../turno2/referencia.ts";
import { chave, keyU } from "../tse/urls.ts";
import { ClienteSupabase } from "../paralela/supabase.ts";
import { PonteParalela } from "../paralela/ponte.ts";
import { AmostraSecoes } from "../secoes2t/coletor.ts";
import { urlsUrna } from "../secoes2t/urls.ts";
import type { Agendador } from "./agendador.ts";
import type { Coletor } from "./bootstrap.ts";
import type { Limitador } from "./limitador.ts";
import { DetectorPausas } from "./pausas.ts";
import { AlertasRegua } from "./regua.ts";
import type { UfAndamento } from "./regua.ts";
import { isoDe } from "./relogio.ts";
import { lerConfigTurno2 } from "./turno2-config.ts";
import type { ConfigTurno2 } from "./turno2-config.ts";

/** Avaliação periódica de pausas e régua (o contrato pede 30 s). */
export const AVALIACAO_MS = 30_000;
/** Arquivo lido com sucesso há menos que isto conta como visto: sem isso, cegueira nossa viraria pausa. */
export const FRESCOR_MS = 180_000;

export interface Turno2 {
  cfg: ConfigTurno2;
  detector: DetectorPausas;
  amostra: AmostraSecoes | null;
  ponte: PonteParalela | null;
  parar(): Promise<void>;
}

type Log = (o: Record<string, unknown>) => void;

export function instalarTurno2(c: Coletor, ag: Agendador, limitador: Limitador, log: Log, env: Readonly<Record<string, string | undefined>> = process.env): Turno2 {
  const cfg = lerConfigTurno2(c.config, env);
  const msg = (err: unknown): string => (err instanceof Error ? err.message : String(err));
  c.ctx.aoFalharObservador = (err) => log({ t: "turno2_erro", onde: "observador", erro: msg(err) });
  const agora0 = c.relogio.agora();

  c.lote.adicionar([
    {
      k: "meta", chave: "turno2_config",
      valor: JSON.stringify({
        turno: cfg.turno, ele_federal: cfg.eleFederal, ele_estadual: cfg.eleEstadual, pleito: cfg.pleito, t0: isoDe(cfg.t0Ms),
        pausas: { limiar_min: cfg.pausas.limiarNacionalMin, limiar_uf_min: cfg.pausas.limiarUfMin },
        secoes: {
          amostra: cfg.secoes.amostra, nacional_por_uf: cfg.secoes.porUf, estaduais_por_uf: cfg.secoes.estadual, ufs_estaduais: cfg.secoes.ufsEstaduais,
          intervalo_s: cfg.secoes.intervaloS, rps: cfg.secoes.rps, concorrencia: cfg.secoes.concorrencia, inicio: isoDe(cfg.secoes.inicioMs),
        },
        paralela: { ativo: cfg.paralela.ativo, intervalo_s: cfg.paralela.intervaloS },
      }),
    },
  ]);

  // ---------------------------------------------------------------- pausas
  const detector = new DetectorPausas(cfg.pausas);
  c.lote.adicionar(detector.carregar(c.db, agora0));
  c.ctx.aoVersaoU = (fs, v) => {
    const k = fs.key;
    if (k.ele !== cfg.eleFederal || k.cargo !== 1 || (k.nivel !== "br" && k.nivel !== "uf")) return [];
    const g = v.geradoEm === null ? Number.NaN : Date.parse(v.geradoEm);
    if (!Number.isFinite(g)) return [];
    return detector.observar(k.nivel === "br" ? null : k.uf, { geradoMs: g, st: v.totais.st ?? 0, ts: v.totais.ts ?? 0 }, v.em);
  };
  const arquivoPres = (uf: string | null) => c.estado.porChave.get(chave(keyU(cfg.eleFederal, 1, uf === null ? "br" : "uf", uf)));
  const fresco = (uf: string | null): boolean => {
    const fs = arquivoPres(uf);
    return fs !== undefined && fs.ativo && fs.errosSeguidos === 0 && fs.ultimoFetchEm !== null && c.relogio.agora() - fs.ultimoFetchEm < FRESCOR_MS;
  };

  // ---------------------------------------------------------------- régua do 1º turno
  let referencia: ReturnType<typeof carregarReferencia> = null;
  try {
    referencia = carregarReferencia(env.APURACAO_REFERENCIA_1T);
  } catch (err) {
    log({ t: "turno2_erro", onde: "referencia_1t", erro: msg(err) });
  }
  const regua = new AlertasRegua(referencia, cfg.regua);
  regua.carregar(c.db);
  if (!regua.ativo) log({ t: "aviso", msg: "régua do 1º turno ausente (data/referencia_1t.json): alertas de atraso e abstenção desligados" });

  ag.aCada(AVALIACAO_MS, (agora) => {
    try {
      const itens = detector.avaliar(agora, fresco);
      const ufs: UfAndamento[] = [];
      for (const uf of detector.ufs) {
        const t = arquivoPres(uf)?.totaisAnteriores;
        if (!t || !fresco(uf)) continue;
        ufs.push({ uf, pst: t.pst ?? 0, st: t.st ?? 0, ts: t.ts ?? 0 });
      }
      const eventos = [...regua.avaliarAtraso(agora, ufs), ...regua.avaliarAbstencao(agora, c.estado.municipiosAb(cfg.eleFederal))];
      c.lote.adicionar([...itens, ...eventos.map((row) => ({ k: "evento" as const, row }))]);
    } catch (err) {
      log({ t: "turno2_erro", onde: "avaliacao", erro: msg(err) });
    }
  });

  // ---------------------------------------------------------------- seções e paralela
  const fundo: Promise<void>[] = [];
  const gravar = (itens: Parameters<typeof c.lote.adicionar>[0]): void => c.lote.adicionar(itens);
  let amostra: AmostraSecoes | null = null;
  if (cfg.secoes.amostra || cfg.paralela.ativo) {
    const a = new AmostraSecoes({
      cfg: cfg.secoes, pleito: cfg.pleito, eleFederal: cfg.eleFederal, t0Ms: cfg.t0Ms, db: c.db, gravar, relogio: c.relogio,
      urls: urlsUrna(cfg.pleito, c.config.baseUrl), pausaPrincipal: () => limitador.pausado(), log, ua: c.config.userAgent,
    });
    amostra = a;
    fundo.push(
      (async () => {
        await a.preparar();
        await a.rodar();
      })().catch((err: unknown) => log({ t: "turno2_erro", onde: "secoes", erro: msg(err) })),
    );
  }
  let ponte: PonteParalela | null = null;
  if (cfg.paralela.ativo) {
    const p = new PonteParalela({
      cfg: cfg.paralela, pleito: cfg.pleito, eleFederal: cfg.eleFederal, db: c.db, gravar, relogio: c.relogio,
      cliente: new ClienteSupabase({ url: cfg.paralela.url, chave: cfg.paralela.chave }), amostra, log,
    });
    p.carregar();
    ponte = p;
    fundo.push(p.rodar().catch((err: unknown) => log({ t: "turno2_erro", onde: "paralela", erro: msg(err) })));
  }

  ag.aCada(AVALIACAO_MS, (agora) => {
    const estado = {
      em: isoDe(agora),
      pausas_abertas: { geral: detector.aberta("geral"), nacional: detector.aberta(null), ufs: detector.ufs.filter((u) => detector.aberta(u) !== null) },
      secoes: amostra?.metricas(agora) ?? null,
      paralela: ponte?.metricas() ?? null,
    };
    c.lote.adicionar([{ k: "meta", chave: "turno2_estado", valor: JSON.stringify(estado) }]);
    log({ t: "turno2", ...estado });
  });

  log({
    t: "turno2_ligado", turno: cfg.turno, ele: cfg.eleFederal, pleito: cfg.pleito, regua: regua.ativo, secoes: cfg.secoes.amostra,
    busca_paralela: amostra !== null, paralela: cfg.paralela.ativo,
  });

  return {
    cfg, detector, amostra, ponte,
    async parar() {
      ponte?.parar();
      await amostra?.parar();
      await Promise.race([Promise.allSettled(fundo), Bun.sleep(5000)]);
    },
  };
}
