// Cadência e prioridade de cada arquivo (tabela do agendador no plano).
import { INTERVALOS_S } from "../config.ts";
import type { MotivoFetch, Prioridade } from "../types.ts";
import type { FileState } from "./estado-arquivos.ts";

/** Segundos entre leituras periódicas; null = só por gatilho ou varredura. */
export function cadenciaS(fs: FileState): number | null {
  const k = fs.key;
  if (k.tipo === "ele-c") return INTERVALOS_S.eleC;
  if (k.tipo === "cm") return INTERVALOS_S.sonda;
  if (k.tipo === "ab") return k.nivel === "br" ? INTERVALOS_S.abBr : INTERVALOS_S.abUf;
  if (fs.tier === 4 || fs.sonda) return INTERVALOS_S.sonda;
  if (fs.tier === 0) return INTERVALOS_S.uBrUf;
  return null;
}

export function prioridadePeriodica(fs: FileState): Prioridade {
  if (fs.tier === 4 || fs.sonda || fs.key.tipo === "cm") return "probe";
  if (fs.tier === 1) return "t1";
  return "t0";
}

export function motivoPeriodico(fs: FileState): MotivoFetch {
  return prioridadePeriodica(fs) === "probe" ? "probe" : "periodico";
}
