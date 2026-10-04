// Resultado -u: normalização com política de candidatos, anomalias e zonas finais.
import type { ItemLote } from "../db/escrita.ts";
import { itensDeU } from "../db/itens.ts";
import { normalizarU, politicaPara } from "../parse/normalizar.ts";
import type { ResultadoU } from "../parse/schemas.ts";
import { candidatosDe, compararU } from "./anomalias.ts";
import type { CtxCorpo } from "./contexto.ts";
import { candidatosSempre, resumoTotais } from "./estado-arquivos.ts";
import type { FileState } from "./estado-arquivos.ts";

/** Cópia regressiva: só os totais, para auditoria. */
export function totaisRegressivo(p: ResultadoU, fs: FileState, snapRef: string): ItemLote[] {
  const n = normalizarU(p, { uf: fs.key.uf, politicaCandidatos: "primeiro_e_final", primeiro: false });
  return [{ k: "totais", snapshot: { ref: snapRef }, row: n.totais }];
}

export function processarU(c: CtxCorpo, p: ResultadoU, snapRef: string, primeiro: boolean): void {
  const { ctx, fs, grupo } = c;
  const k = fs.key;
  const cargo = k.cargo ?? 0;
  const nivel = k.nivel ?? "br";
  const base = { uf: k.uf, politicaCandidatos: politicaPara(cargo, nivel), primeiro };
  let n = normalizarU(p, base);
  const novoT = resumoTotais(n.totais);
  const guarda = candidatosSempre(k);
  const novoC = guarda && n.incluiuCandidatos ? candidatosDe(n.votoCandidato) : null;
  const an = compararU(fs.totaisAnteriores, novoT, fs.candidatosAnteriores, novoC, {
    em: c.em, arquivoId: fs.id, snapshot: { ref: snapRef }, key: k,
  });
  if (an.alerta && !n.incluiuCandidatos) n = normalizarU(p, { ...base, forcarCandidatos: true });
  grupo.push(...itensDeU(n, { ref: snapRef }));
  for (const ev of an.eventos) grupo.push({ k: "evento", row: ev });
  fs.totaisAnteriores = novoT;
  if (guarda && novoC !== null) fs.candidatosAnteriores = novoC;

  // município finalizado no -u (tf = s ou pst = 100): zonas dele como final, uma vez
  if (n.final && k.nivel === "mu" && k.ele !== null && k.uf !== null && k.mun !== null) {
    for (const z of ctx.estado.zonasDoMunicipio(k.ele, k.uf, k.mun)) {
      if (z.finalAgendado) continue;
      z.finalAgendado = true;
      c.saida.jobs.push({ arquivoId: z.id, prioridade: "final", due: c.agora, motivo: "final" });
      grupo.push({ k: "arquivo_estado", id: z.id, row: ctx.estado.paraLinha(z) });
    }
  }
}
