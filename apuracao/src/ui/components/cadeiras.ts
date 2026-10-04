// Alocação provisória de cadeiras pela regra brasileira (Código Eleitoral, arts. 106 a 111,
// com a Lei 14.211/2021 e o entendimento do STF nas ADIs 7228, 7263 e 7325, de 2024):
//
// 1. Quociente eleitoral (QE) = válidos / vagas, desprezada a fração igual ou inferior a
//    meio e arredondada para cima a fração superior a meio (art. 106).
// 2. Quociente partidário (QP) = floor(votos da agremiação / QE); cada agremiação elege no
//    máximo tantos quantos candidatos tiverem pelo menos 10% do QE (art. 108).
// 3. Sobras por maiores médias, votos / (lugares + 1), só entre agremiações com pelo menos
//    80% do QE e candidatos com pelo menos 20% do QE ainda não eleitos (art. 109, I e II).
// 4. Sem agremiação que cumpra o passo 3, as cadeiras restantes vão por maiores médias entre
//    todas as agremiações com candidato disponível (STF, 2024, terceira fase das sobras).
// 5. Se nenhuma agremiação alcançar o QE, elegem-se os candidatos mais votados (art. 111).
//
// Federação conta como uma agremiação só. Módulo puro: nenhum acesso ao DOM.

export interface AgremiacaoEntrada {
  id: string;
  /** Votos nominais mais votos de legenda da agremiação. */
  votos: number;
  /** Votos nominais de cada candidato da agremiação (qualquer ordem). */
  candidatos: readonly number[];
}

export interface CadeirasAgremiacao {
  qp: number; // cadeiras pelo quociente partidário (já limitadas pelos 10%)
  sobras: number;
  total: number;
}

export interface ResultadoCadeiras {
  vagas: number;
  validos: number;
  qe: number;
  /** Nenhuma agremiação alcançou o QE: valeu o art. 111. */
  semQuociente: boolean;
  porAgremiacao: Record<string, CadeirasAgremiacao>;
}

/** QE com a regra de arredondamento do art. 106. */
export function quocienteEleitoral(validos: number, vagas: number): number {
  if (!(validos > 0) || !(vagas > 0)) return 0;
  const q = validos / vagas;
  const base = Math.floor(q);
  return q - base > 0.5 ? base + 1 : base;
}

interface Trabalho {
  id: string;
  votos: number;
  cands: number[]; // ordenados do mais votado ao menos votado
  qp: number;
  sobras: number;
}

const total = (t: Trabalho): number => t.qp + t.sobras;

/** Maior média entre os elegíveis; empate pelo maior número de votos e depois pelo id. */
function maiorMedia(lista: readonly Trabalho[]): Trabalho | null {
  let melhor: Trabalho | null = null;
  let melhorMedia = -1;
  for (const t of lista) {
    const media = t.votos / (total(t) + 1);
    if (
      melhor === null ||
      media > melhorMedia ||
      (media === melhorMedia && (t.votos > melhor.votos || (t.votos === melhor.votos && t.id < melhor.id)))
    ) {
      melhor = t;
      melhorMedia = media;
    }
  }
  return melhor;
}

export function alocarCadeiras(vagas: number, agremiacoes: readonly AgremiacaoEntrada[], validos?: number): ResultadoCadeiras {
  const v = validos ?? agremiacoes.reduce((s, a) => s + Math.max(0, a.votos), 0);
  const qe = quocienteEleitoral(v, vagas);
  const trabalho: Trabalho[] = agremiacoes.map(a => ({
    id: a.id,
    votos: Math.max(0, a.votos),
    cands: [...a.candidatos].filter(x => Number.isFinite(x) && x >= 0).sort((x, y) => y - x),
    qp: 0,
    sobras: 0,
  }));
  const saida = (semQuociente: boolean): ResultadoCadeiras => ({
    vagas,
    validos: v,
    qe,
    semQuociente,
    porAgremiacao: Object.fromEntries(trabalho.map(t => [t.id, { qp: t.qp, sobras: t.sobras, total: total(t) }])),
  });
  if (qe <= 0 || vagas <= 0) return saida(false);

  // Art. 111: ninguém alcançou o QE, valem os candidatos mais votados.
  if (trabalho.every(t => t.votos < qe)) {
    const todos = trabalho.flatMap(t => t.cands.map(c => ({ t, c })));
    todos.sort((a, b) => b.c - a.c || a.t.id.localeCompare(b.t.id));
    for (const { t } of todos.slice(0, vagas)) t.sobras += 1;
    return saida(true);
  }

  // Quociente partidário limitado pelos candidatos com 10% do QE.
  for (const t of trabalho) {
    const com10 = t.cands.filter(c => c >= 0.1 * qe).length;
    t.qp = Math.min(Math.floor(t.votos / qe), com10);
  }
  let restantes = vagas - trabalho.reduce((s, t) => s + t.qp, 0);

  // Sobras com as cláusulas de 80% (agremiação) e 20% (candidato).
  while (restantes > 0) {
    const aptas = trabalho.filter(t => t.votos >= 0.8 * qe && t.cands.filter(c => c >= 0.2 * qe).length > total(t));
    const escolhida = maiorMedia(aptas);
    if (!escolhida) break;
    escolhida.sobras += 1;
    restantes -= 1;
  }

  // Terceira fase: todas as agremiações com candidato disponível.
  while (restantes > 0) {
    const aptas = trabalho.filter(t => t.votos > 0 && t.cands.length > total(t));
    const escolhida = maiorMedia(aptas);
    if (!escolhida) break;
    escolhida.sobras += 1;
    restantes -= 1;
  }
  return saida(false);
}
