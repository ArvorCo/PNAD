// Registro das telas. As que ainda não existem entram como placeholder para a
// playlist rodar de ponta a ponta. Pacotes seguintes (F3a, F3b) trocam a linha do
// placeholder por `register("pres", criarPresidente, TITULOS.pres)`; a última chamada vence.

import type { State } from "../state/types.ts";
import { criarEspera } from "./espera.ts";
import { nomeUf, placeholder, register } from "./registry.ts";
import { registrarLegislativas } from "./registrar-legislativas.ts";
import { registrarMajoritarias } from "./registrar-majoritarias.ts";

export const TITULOS: Readonly<Record<string, string>> = {
  pres: "Presidente",
  "pres-uf": "Presidente",
  gov: "Governadores",
  "gov-uf": "Governador",
  sen: "Senado",
  "sen-uf": "Senado",
  "fed-uf": "Deputados federais",
  "est-uf": "Deputados estaduais",
  "dis-df": "Deputados distritais",
  ritmo: "Ritmo da apuração",
  mov: "Movimento da apuração",
  mun: "Município",
  exterior: "Voto no exterior",
  acumulado: "Votos acumulados",
  lotes: "O que chegou em cada atualização",
  espera: "Espera",
};

/** Rótulos sem ambiguidade para o diretor e o HUD. */
export const ROTULOS: Readonly<Record<string, string>> = {
  pres: "Presidente, Brasil",
  "pres-uf": "Presidente por UF",
  gov: "Governadores, 27 UFs",
  "gov-uf": "Governador por UF",
  sen: "Senado, composição",
  "sen-uf": "Senado por UF",
  "fed-uf": "Deputados federais",
  "est-uf": "Deputados estaduais",
  "dis-df": "Deputados distritais",
  ritmo: "Ritmo da apuração",
  mov: "Movimento da apuração",
  mun: "Município",
  exterior: "Voto no exterior",
  acumulado: "Votos acumulados",
  lotes: "O que chegou em cada atualização",
  espera: "Espera",
};

/** Título de uma entrada de playlist ou de navegação, sem montar a tela. */
export function tituloDaTela(id: string, s: State, uf: string | null, mun: string | null = null): string {
  const base = TITULOS[id] ?? id;
  if (id === "pres") return "Presidente, Brasil";
  if (id === "gov" || id === "sen" || id === "ritmo" || id === "mov" || id === "exterior" || id === "espera") return base;
  if (id === "mun" && uf && mun) {
    const m = s.config?.municipios[uf]?.find(x => x.cd === mun);
    return m ? `${m.nm}, ${uf}` : base;
  }
  return uf ? `${base}, ${nomeUf(s, uf)}` : base;
}

export function registrarTelas(): void {
  for (const [id, t] of Object.entries(TITULOS)) {
    if (id === "espera") continue;
    register(id, placeholder(id, s => tituloDaTela(id, s, s.ui.uf, s.ui.mun)), ROTULOS[id] ?? t);
  }
  register("espera", () => criarEspera(tituloDaTela), ROTULOS.espera);
  registrarMajoritarias();
  registrarLegislativas();
}
