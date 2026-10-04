// F3b registra aqui as telas gov, sen, fed-uf, est-uf, dis-df, ritmo e mov.
// Chamado por `registrarTelas()` depois dos placeholders; a última chamada vence.

import { criarAcumuladoView } from "./acumulado.ts";
import { criarGovernadores } from "./governadores.ts";
import { criarLotesView } from "./lotes.ts";
import { criarMovimento } from "./movimento.ts";
import { criarProporcional } from "./proporcional.ts";
import { register } from "./registry.ts";
import { criarRitmo } from "./ritmo.ts";
import { criarSenado } from "./senado.ts";

export function registrarLegislativas(): void {
  register("gov", criarGovernadores, "Governadores, 27 UFs");
  register("sen", criarSenado, "Senado, composição");
  register("fed-uf", () => criarProporcional({ id: "fed-uf", cargo: 6 }), "Deputados federais");
  register("est-uf", () => criarProporcional({ id: "est-uf", cargo: 7 }), "Deputados estaduais");
  register("dis-df", () => criarProporcional({ id: "dis-df", cargo: 8 }), "Deputados distritais");
  register("ritmo", criarRitmo, "Ritmo da apuração");
  register("mov", criarMovimento, "Movimento da apuração");
  register("acumulado", criarAcumuladoView, "Votos acumulados");
  register("lotes", criarLotesView, "O que chegou em cada atualização");
}
