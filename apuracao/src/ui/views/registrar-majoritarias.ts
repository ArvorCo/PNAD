// Telas majoritárias (F3a): pres, pres-uf, gov-uf, sen-uf e mun (template executivo).
// Chamado por `registrarTelas()` depois dos placeholders; a última chamada vence.

import { criarExecutivo } from "./executivo.ts";
import { criarPresidente } from "./presidente.ts";
import { register } from "./registry.ts";

export function registrarMajoritarias(): void {
  register("pres", criarPresidente, "Presidente, Brasil");
  register("pres-uf", () => criarExecutivo({ id: "pres-uf", cargo: 1, max: 7, nvLidera: 0 }), "Presidente por UF");
  register("gov-uf", () => criarExecutivo({ id: "gov-uf", cargo: 3, max: 7, nvLidera: 1 }), "Governador por UF");
  register("sen-uf", () => criarExecutivo({ id: "sen-uf", cargo: 5, max: 5, nvLidera: 2 }), "Senado por UF");
  register("mun", () => criarExecutivo({ id: "mun", cargo: null, max: 6, nvLidera: 0, dwell: 15 }), "Município");
}
