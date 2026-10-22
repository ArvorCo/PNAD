// Registro das telas. As que ainda não existem entram como placeholder para a
// playlist rodar de ponta a ponta. Pacotes seguintes (F3a, F3b) trocam a linha do
// placeholder por `register("pres", criarPresidente, TITULOS.pres)`; a última chamada vence.

import type { State } from "../state/types.ts";
import { criarEspera } from "./espera.ts";
import { criarPresidente } from "./presidente.ts";
import { nomeUf, placeholder, register } from "./registry.ts";
import { registrarLegislativas } from "./registrar-legislativas.ts";
import { registrarMajoritarias } from "./registrar-majoritarias.ts";
import { registrar2T } from "./registrar-2t.ts";
import { IDS_2T, TELAS_2T } from "./meta-2t.ts";

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
  ...Object.fromEntries(TELAS_2T.map(t => [t.id, t.titulo])),
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
  ...Object.fromEntries(TELAS_2T.map(t => [t.id, t.rotulo])),
};

/** O 2º turno chama o duelo de "Presidente, 2º turno" (ROTULOS fica no 1º turno até a config chegar). */
export const ROTULO_PRES_2T = "Presidente, 2º turno";

export const ehSegundoTurno = (s: State): boolean => (s.config?.turno ?? s.estado?.turno ?? 1) === 2;

/** Título de uma entrada de playlist ou de navegação, sem montar a tela. */
export function tituloDaTela(id: string, s: State, uf: string | null, mun: string | null = null): string {
  const base = TITULOS[id] ?? id;
  if (id === "pres") return ehSegundoTurno(s) ? ROTULO_PRES_2T : "Presidente, Brasil";
  if (IDS_2T.has(id)) return base;
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
  registrar2T();
}

/** Com a config em mãos: no 2º turno o rótulo curto do duelo vira "Presidente, 2º turno". */
export function aplicarTurno(turno: number): void {
  if (turno === 2) register("pres", criarPresidente, ROTULO_PRES_2T);
}
