// Pleito e eleições da coleta de seções, por variável de ambiente, sem quebrar o 1º turno.
//   APURACAO_PLEITO   código do pleito no arquivo-urna (padrão 003220, 1º turno de 2026;
//                     003221 é o 2º turno)
//   APURACAO_ELEICAO  id da eleição federal do pleito; a estadual é a seguinte do mesmo
//                     pleito (federal + 2). Padrão pela tabela abaixo.
// O BU de cada seção traz as eleições que contém; estes ids só escolhem qual delas preenche
// as colunas `aptos*` de bu e qual vira `aptos_estadual`.

/** Eleições federal e estadual de cada pleito conhecido de 2026. */
export const ELEICOES_POR_PLEITO: Readonly<Record<string, { federal: number; estadual: number }>> = {
  "003220": { federal: 6257, estadual: 6259 },
  "003221": { federal: 6258, estadual: 6260 },
};

export interface Pleito {
  /** seis dígitos, como no nome dos arquivos (p003220) */
  codigo: string;
  /** sem zeros à esquerda, como no caminho (arquivo-urna/3220) */
  numero: number;
  federal: number;
  estadual: number;
  /** 1 ou 2 quando o pleito é conhecido; null caso contrário */
  turno: number | null;
}

export function resolverPleito(env: Readonly<Record<string, string | undefined>> = process.env): Pleito {
  const bruto = (env.APURACAO_PLEITO ?? "003220").trim();
  if (!/^\d{1,6}$/.test(bruto)) throw new Error(`APURACAO_PLEITO inválido: ${bruto}`);
  const codigo = bruto.padStart(6, "0");
  const tabela = ELEICOES_POR_PLEITO[codigo];
  const eleicaoEnv = env.APURACAO_ELEICAO?.trim();
  let federal: number;
  if (eleicaoEnv !== undefined && eleicaoEnv !== "") {
    federal = Number.parseInt(eleicaoEnv, 10);
    if (!Number.isFinite(federal) || federal <= 0) throw new Error(`APURACAO_ELEICAO inválido: ${eleicaoEnv}`);
  } else if (tabela !== undefined) {
    federal = tabela.federal;
  } else {
    throw new Error(`pleito ${codigo} sem eleição conhecida: defina APURACAO_ELEICAO`);
  }
  const estadual = tabela !== undefined && tabela.federal === federal ? tabela.estadual : federal + 2;
  const turno = codigo === "003220" ? 1 : codigo === "003221" ? 2 : null;
  return { codigo, numero: Number.parseInt(codigo, 10), federal, estadual, turno };
}

export const PLEITO_ATUAL: Pleito = resolverPleito();
