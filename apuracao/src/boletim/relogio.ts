// Relógio do boletim: ciclos alinhados aos múltiplos do intervalo a partir do início (17:10 de Brasília).

/** Início do relógio: "HH:MM" (Brasília, no dia de `agora`) ou ISO completo. */
export function inicioDoRelogio(texto: string | undefined, agora: Date): number {
  const t = (texto ?? "17:10").trim();
  const m = /^(\d{1,2}):(\d{2})$/.exec(t);
  if (m) {
    const dia = agora.toLocaleDateString("en-CA", { timeZone: "America/Sao_Paulo" });
    const iso = `${dia}T${m[1]?.padStart(2, "0")}:${m[2]}:00-03:00`;
    return Date.parse(iso);
  }
  const ms = Date.parse(t);
  if (!Number.isFinite(ms)) throw new Error(`APURACAO_BOLETIM_INICIO inválido: ${t}`);
  return ms;
}

/** Primeiro ciclo em ou depois de `agoraMs`. */
export function proximoCiclo(inicioMs: number, intervaloS: number, agoraMs: number): number {
  if (agoraMs <= inicioMs) return inicioMs;
  const passo = intervaloS * 1000;
  return inicioMs + Math.ceil((agoraMs - inicioMs) / passo) * passo;
}

/** Id livre: HHMM e, se já existir, HHMM-2, HHMM-3... */
export function idLivre(hhmm: string, existe: (id: string) => boolean): string {
  if (!existe(hhmm)) return hhmm;
  for (let k = 2; k < 100; k += 1) if (!existe(`${hhmm}-${k}`)) return `${hhmm}-${k}`;
  throw new Error(`sem id livre para ${hhmm}`);
}
