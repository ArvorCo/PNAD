// Telas do 2º turno (25/10/2026): regiões, UFs, atraso, abstenção, seções, pausas, governadores,
// paralela, alertas, evolução e projeção. Chamado por `registrarTelas()`; a última chamada de `register` vence.

import { criarAbstencao } from "./abstencao.ts";
import { criarAlertas } from "./alertas.ts";
import { criarAtraso } from "./atraso.ts";
import { criarEvolucaoTela } from "./evolucao.ts";
import { criarGov2T } from "./gov2t.ts";
import { TELAS_2T } from "./meta-2t.ts";
import { criarParalela } from "./paralela.ts";
import { criarPausas } from "./pausas.ts";
import { criarProjecao } from "./projecao.ts";
import { criarRegioes } from "./regioes.ts";
import { register } from "./registry.ts";
import type { FabricaView } from "./registry.ts";
import { criarSecoes } from "./secoes.ts";
import { criarUfs } from "./ufs.ts";

const FABRICAS: Readonly<Record<string, FabricaView>> = {
  regioes: criarRegioes,
  ufs: criarUfs,
  atraso: criarAtraso,
  abstencao: criarAbstencao,
  secoes: criarSecoes,
  pausas: criarPausas,
  "gov-2t": criarGov2T,
  paralela: criarParalela,
  alertas: criarAlertas,
  evolucao: criarEvolucaoTela,
  projecao: criarProjecao,
};

export function registrar2T(): void {
  for (const t of TELAS_2T) {
    const f = FABRICAS[t.id];
    if (f) register(t.id, f, t.rotulo);
  }
}
