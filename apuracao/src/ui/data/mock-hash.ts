// Parâmetros extras do ensaio no hash (#mock=1&turno=2&t0=150&falha=paralela&sem1t=1), lidos
// só na carga da página. Sem DOM, para os testes.

import { ROTAS_2T } from "./doist.ts";
import type { Rota2T } from "./doist.ts";
import type { FalhaMock } from "./mock.ts";

export interface ParamsMock {
  turno: 1 | 2;
  /** Minutos após 17:00 em que o relógio simulado começa; null deixa o padrão (16:59:30). */
  inicioMin: number | null;
  falhas: Partial<Record<Rota2T, FalhaMock>>;
  sem1t: boolean;
  /** Relógio parado em `t0`: toda leitura devolve os mesmos números. */
  congelar: boolean;
}

const ROTA_VALIDA = new Set<string>(ROTAS_2T);
const FALHA_VALIDA = new Set<string>(["erro", "pendente", "fonte"]);

/**
 * `turno` (1 ou 2, padrão 2: o 1º turno já passou); `t0` em minutos; `falha=rota[:modo],rota...`
 * com modo `erro` (padrão), `pendente` ou `fonte`; `evolucao` vale para as duas rotas de evolução;
 * `sem1t=1` tira a régua do 1º turno; `congelar=1` para o relógio em `t0`.
 */
export function lerParamsMock(hash: string): ParamsMock {
  const p = new URLSearchParams(hash.replace(/^#/, ""));
  const turno = p.get("turno") === "1" ? 1 : 2;
  const t0 = p.get("t0");
  const inicioMin = t0 !== null && t0.trim() !== "" && Number.isFinite(Number(t0)) ? Number(t0) : null;
  const falhas: Partial<Record<Rota2T, FalhaMock>> = {};
  for (const item of (p.get("falha") ?? "").split(",")) {
    const [nome = "", modo = "erro"] = item.trim().split(":");
    const m = (FALHA_VALIDA.has(modo) ? modo : "erro") as FalhaMock;
    if (nome === "evolucao") {
      falhas["evolucao-regiao"] = m;
      falhas["evolucao-uf"] = m;
    } else if (ROTA_VALIDA.has(nome)) falhas[nome as Rota2T] = m;
  }
  const flag = (k: string): boolean => {
    const v = p.get(k);
    return v !== null && v !== "0" && v !== "false";
  };
  return { turno, inicioMin, falhas, sem1t: flag("sem1t"), congelar: flag("congelar") };
}
