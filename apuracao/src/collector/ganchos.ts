// Tarefas periódicas do coletor: saúde (5 s), ajustes a quente (10 s), relógio (60 s).
import { INTERVALOS_S } from "../config.ts";
import { lerMeta } from "../db/leitura.ts";
import type { Agendador } from "./agendador.ts";
import type { Coletor } from "./bootstrap.ts";
import { isoDe } from "./relogio.ts";
import { linhaLog, tamanhoMb } from "./saude.ts";
import type { EstadoColetor } from "./saude.ts";

export const SKEW_LIMITE_MS = 3000;

export function estadoColetor(c: Coletor, ag: Agendador, agora: number): EstadoColetor {
  const j = ag.metricas.janela(agora);
  return {
    em: isoDe(agora),
    em_voo: ag.emVoo,
    concorrencia: ag.concorrencia,
    fila: ag.fila.tamanhoPorPrioridade(),
    taxas_60s: j.taxas,
    mudancas_60s: j.mudancas,
    bytes_60s: j.bytes,
    pausa_global_ate: null,
    nivel_pausa: 0,
    sweep: ag.resumoSweep(),
    skew_ms: ag.metricas.skewMs(),
    memoria_mb: Math.round(process.memoryUsage().rss / 1048576),
    heap_mb: Math.round(process.memoryUsage().heapUsed / 1048576),
    wal_mb: tamanhoMb(`${c.config.dbPath}-wal`),
    db_mb: tamanhoMb(c.config.dbPath),
    total_fetch: ag.metricas.total,
    ultimo_erro: ag.metricas.ultimoErro,
  };
}

type Ajustes = Record<string, unknown>;

/** Aplica meta.ajustes (mesmos nomes das variáveis de ambiente). Devolve o que mudou. */
export function aplicarAjustes(c: Coletor, ag: Agendador, a: Ajustes): string[] {
  const k = c.ctx.knobs;
  const mud: string[] = [];
  const num = (v: unknown): number | null => {
    const n = typeof v === "number" ? v : typeof v === "string" ? Number.parseInt(v, 10) : Number.NaN;
    return Number.isFinite(n) && n >= 0 ? n : null;
  };
  const sweep = num(a.APURACAO_SWEEP_MIN);
  if (sweep !== null && sweep !== k.sweepMin) {
    k.sweepMin = sweep;
    mud.push(`sweepMin=${sweep}`);
  }
  if (a.APURACAO_ZONAS === "final" || a.APURACAO_ZONAS === "sempre") {
    if (k.zonas !== a.APURACAO_ZONAS) mud.push(`zonas=${a.APURACAO_ZONAS}`);
    k.zonas = a.APURACAO_ZONAS;
  }
  const mu = num(a.APURACAO_MIN_INTERVALO_MU);
  if (mu !== null && mu !== k.minIntervaloMuS) {
    k.minIntervaloMuS = mu;
    mud.push(`minIntervaloMuS=${mu}`);
  }
  const conc = num(a.APURACAO_CONCURRENCY);
  if (conc !== null && conc > 0 && conc !== k.concurrency) {
    k.concurrency = conc;
    ag.concorrencia = conc;
    mud.push(`concurrency=${conc}`);
  }
  return mud;
}

export function instalarGanchos(c: Coletor, ag: Agendador, pausa: () => { ate: number | null; nivel: number }): void {
  const log = (o: Record<string, unknown>): void => console.log(JSON.stringify(o));
  ag.aCada(INTERVALOS_S.saude * 1000, (agora) => {
    const p = pausa();
    const e = { ...estadoColetor(c, ag, agora), pausa_global_ate: p.ate === null ? null : isoDe(p.ate), nivel_pausa: p.nivel };
    c.lote.adicionar([{ k: "meta", chave: "estado_coletor", valor: JSON.stringify(e) }]);
    console.log(linhaLog(e));
  });
  let ultimoAjuste = "";
  ag.aCada(INTERVALOS_S.ajustes * 1000, (agora) => {
    const txt = lerMeta(c.db, "ajustes");
    if (txt === null || txt === ultimoAjuste) return;
    ultimoAjuste = txt;
    try {
      const mud = aplicarAjustes(c, ag, JSON.parse(txt) as Ajustes);
      if (mud.length > 0) {
        ag.registrarEvento({ em: isoDe(agora), tipo: "ajustes", detalhe: { mudou: mud } });
        log({ t: "ajustes", mudou: mud });
      }
    } catch (err) {
      log({ t: "ajustes_invalidos", erro: err instanceof Error ? err.message : String(err) });
    }
  });
  ag.aCada(INTERVALOS_S.skew * 1000, (agora) => {
    const s = ag.metricas.skewMs();
    if (s !== null && Math.abs(s) > SKEW_LIMITE_MS) {
      ag.registrarEvento({ em: isoDe(agora), tipo: "skew_relogio", severidade: "warn", detalhe: { skew_ms: s } });
      log({ t: "skew_relogio", skew_ms: s });
    }
  });
}
