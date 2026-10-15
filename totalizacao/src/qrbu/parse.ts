// Leitura dos QR Codes do boletim de urna, formato VRQR 6.0 (manual TSE 2026, seção 1.4).
//
// Cada QR Code: "QRBU:i:n VRQR:6.0 <dados> HASH:<SHA-512 hex>", e o último acrescenta
// " ASSI:<hex>". Os dados são registros "CHAVE:valor" separados por um espaço. Quando o boletim
// não cabe em um QR, o conteúdo é quebrado num espaço, que é retirado; na remontagem ele volta.
//
// Gramática do conteúdo, na ordem em que a urna grava:
//   cabeçalho do boletim (ORIG ... HREM)
//   para cada eleição: IDEL [MAJO] [PROP]
//     para cada cargo: CARG TIPO VERC
//       votos "numero:quantidade" (majoritário e consulta) ou blocos PART ... LEGP TOTP (proporcional)
//       resumo APTA APTS APTT [CSEC] NOMI [LEGC] BRAN NULO TOTC
//
// Campos desconhecidos não derrubam a leitura: ficam em `camposDesconhecidos` e a validação os
// aponta como problema. Já um registro fora de lugar ou um número malformado lança ErroQrBu,
// porque a estrutura deixaria de ser confiável.

export type CodigoErroQrBu =
  | "SEM_QR"
  | "QR_INVALIDO"
  | "QR_DUPLICADO"
  | "QR_TOTAL_INCONSISTENTE"
  | "QR_FALTANDO"
  | "VERSAO_INCONSISTENTE"
  | "ASSINATURA_FORA_DO_ULTIMO"
  | "CONTEUDO_INVALIDO";

export class ErroQrBu extends Error {
  readonly codigo: CodigoErroQrBu;
  constructor(codigo: CodigoErroQrBu, mensagem: string) {
    super(mensagem);
    this.name = "ErroQrBu";
    this.codigo = codigo;
  }
}

/** Um QR Code do boletim já separado em cabeçalho, dados e segurança. */
export interface ParteQrBu {
  indice: number;
  total: number;
  versao: string;
  dados: string;
  hash: string;
  assinatura: string | null;
  texto: string;
}

export interface HistoricoCarga {
  sequencia: number;
  codigo: string;
}

/** Cabeçalho do boletim com as chaves do manual. Campos ausentes ficam indefinidos. */
export interface CabecalhoBu {
  ORIG?: string;
  ORLC?: string;
  PROC?: number;
  DTPL?: string;
  PLEI?: number;
  TURN?: number;
  FASE?: string;
  UNFE?: string;
  MUNI?: number;
  ZONA?: number;
  SECA?: number;
  AGRE?: number[];
  IDUE?: number;
  IDCA?: string;
  HIQT?: number;
  HICA?: HistoricoCarga[];
  VERS?: string;
  LOCA?: number;
  APTO?: number;
  APTS?: number;
  APTT?: number;
  COMP?: number;
  FALT?: number;
  HBBM?: number;
  HBBG?: number;
  HBSB?: number;
  DTAB?: string;
  HRAB?: string;
  DTFC?: string;
  HRFC?: string;
  JUNT?: number;
  TURM?: number;
  DTEM?: string;
  HREM?: string;
}

export interface VotoBu {
  /** Número do candidato ou da resposta (consulta). */
  numero: number;
  votos: number;
}

export interface PartidoBu {
  PART: number;
  votos: VotoBu[];
  LEGP?: number;
  TOTP?: number;
}

export interface CargoBu {
  CARG: number;
  TIPO?: number;
  VERC?: string;
  /** Votos fora de bloco de partido (cargos majoritários e consultas). */
  votos: VotoBu[];
  /** Blocos de partido (cargos proporcionais). */
  partidos: PartidoBu[];
  APTA?: number;
  APTS?: number;
  APTT?: number;
  CSEC?: number;
  NOMI?: number;
  LEGC?: number;
  BRAN?: number;
  NULO?: number;
  TOTC?: number;
}

export interface EleicaoBu {
  IDEL: number;
  MAJO?: number;
  PROP?: number;
  cargos: CargoBu[];
}

export type ContextoCampo = "cabecalho" | "eleicao" | "cargo" | "partido" | "resumo";

export interface CampoDesconhecido {
  chave: string;
  valor: string;
  contexto: ContextoCampo;
  posicao: number;
}

export interface BoletimQr {
  cabecalho: CabecalhoBu;
  eleicoes: EleicaoBu[];
  camposDesconhecidos: CampoDesconhecido[];
}

export interface QrBuLido {
  /** Partes em ordem de índice. */
  partes: ParteQrBu[];
  versao: string;
  /** Conteúdo remontado: dados de cada QR unidos por um espaço. */
  conteudo: string;
  /** HASH declarado no último QR Code (o valor assinado). */
  ultimoHash: string;
  /** ASSI do último QR Code, ou null se ausente. */
  assinatura: string | null;
  /** Leituras repetidas do mesmo QR Code (texto idêntico) descartadas. */
  duplicadosDescartados: number;
}

/** Descrição de cada campo do cabeçalho, conforme a seção 1.4.2 do manual. */
export const CAMPOS_CABECALHO = {
  ORIG: "Origem do boletim de urna (VOTA, RED ou SA)",
  ORLC: "Origem da configuração do processo eleitoral (LEG, eleição oficial; COM, comunitária)",
  PROC: "Número do processo eleitoral",
  DTPL: "Data do pleito (aaaammdd)",
  PLEI: "Número do pleito",
  TURN: "Número do turno",
  FASE: "Fase dos dados (O oficial, S simulado, T treinamento)",
  UNFE: "Sigla da UF (ZZ no exterior)",
  MUNI: "Número do município",
  ZONA: "Número da zona eleitoral",
  SECA: "Número da seção eleitoral",
  AGRE: "Seções agregadas, separadas por ponto",
  IDUE: "Número de série da urna",
  IDCA: "Código de identificação da carga (24 dígitos)",
  HIQT: "Quantidade de códigos de carga no histórico",
  HICA: "Histórico de códigos de carga (sequência:código)",
  VERS: "Versão do software da urna",
  LOCA: "Número do local de votação",
  APTO: "Total de eleitores aptos",
  APTS: "Eleitores aptos originários da seção",
  APTT: "Eleitores aptos transferidos temporariamente para a seção",
  COMP: "Eleitores que compareceram",
  FALT: "Eleitores faltosos",
  HBBM: "Eleitores habilitados biometricamente",
  HBBG: "Eleitores com biometria não reconhecida, habilitados por ano de nascimento",
  HBSB: "Eleitores sem biometria, habilitados por ano de nascimento",
  DTAB: "Data da abertura da urna (aaaammdd)",
  HRAB: "Hora da abertura da urna (hhmmss)",
  DTFC: "Data do fechamento da urna (aaaammdd)",
  HRFC: "Hora do fechamento da urna (hhmmss)",
  JUNT: "Número da junta apuradora",
  TURM: "Número da turma apuradora",
  DTEM: "Data de emissão do boletim (aaaammdd)",
  HREM: "Hora de emissão do boletim (hhmmss)",
} as const satisfies Record<keyof CabecalhoBu, string>;

type ChaveCabecalho = keyof typeof CAMPOS_CABECALHO;

const CABECALHO_NUMERICO = new Set<ChaveCabecalho>([
  "PROC", "PLEI", "TURN", "MUNI", "ZONA", "SECA", "IDUE", "HIQT", "LOCA", "APTO", "APTS", "APTT",
  "COMP", "FALT", "HBBM", "HBBG", "HBSB", "JUNT", "TURM",
]);

const CAMPOS_RESUMO = ["APTA", "APTS", "APTT", "CSEC", "NOMI", "LEGC", "BRAN", "NULO", "TOTC"] as const;
type ChaveResumo = (typeof CAMPOS_RESUMO)[number];
const RESUMO = new Set<string>(CAMPOS_RESUMO);

// Caracteres do modo alfanumérico do QR Code (ISO/IEC 18004): 0-9, A-Z, espaço e $ % * + - . / :
const ALFANUMERICO = /^[0-9A-Z $%*+\-./:]+$/;
const PADRAO_QRBU = /^QRBU:(\d+):(\d+) VRQR:(\d+\.\d+) (.+?) HASH:([0-9A-F]{128})(?: ASSI:([0-9A-F]+))?$/;
const LIMITE_QR = 99;

/** Separa um texto de QR Code do boletim nas suas seções. */
export function lerParteQrBu(texto: string): ParteQrBu {
  const limpo = texto.trim();
  const m = PADRAO_QRBU.exec(limpo);
  if (!m) throw new ErroQrBu("QR_INVALIDO", "texto fora do formato QRBU:i:n VRQR:x.y <dados> HASH:<128 hex> [ASSI:<hex>]");
  const indice = Number(m[1]);
  const total = Number(m[2]);
  if (indice < 1 || total < 1 || indice > total || total > LIMITE_QR) {
    throw new ErroQrBu("QR_INVALIDO", `índice ${indice} de ${total} inválido`);
  }
  const dados = m[4] ?? "";
  if (!ALFANUMERICO.test(dados)) throw new ErroQrBu("QR_INVALIDO", `QR ${indice}: caractere fora do modo alfanumérico`);
  return { indice, total, versao: m[3] ?? "", dados, hash: m[5] ?? "", assinatura: m[6] ?? null, texto: limpo };
}

/**
 * Junta os QR Codes do boletim (em qualquer ordem) e confere que o conjunto está completo.
 * Leituras repetidas com texto idêntico são descartadas; índice repetido com texto diferente é erro.
 */
export function montarQrBu(textos: string[]): QrBuLido {
  if (textos.length === 0) throw new ErroQrBu("SEM_QR", "nenhum QR Code do boletim (QRBU)");
  const unicos = [...new Set(textos.map((t) => t.trim()))];
  const partes = unicos.map(lerParteQrBu).sort((a, b) => a.indice - b.indice);
  const primeira = partes[0];
  if (!primeira) throw new ErroQrBu("SEM_QR", "nenhum QR Code do boletim (QRBU)");
  const total = primeira.total;
  for (let i = 1; i < partes.length; i++) {
    const anterior = partes[i - 1];
    const atual = partes[i];
    if (anterior && atual && anterior.indice === atual.indice) {
      throw new ErroQrBu("QR_DUPLICADO", `dois QR Codes diferentes com o índice ${atual.indice}`);
    }
  }
  if (partes.some((p) => p.total !== total)) {
    throw new ErroQrBu("QR_TOTAL_INCONSISTENTE", "QR Codes do mesmo boletim declaram totais diferentes");
  }
  if (partes.some((p) => p.versao !== primeira.versao)) {
    throw new ErroQrBu("VERSAO_INCONSISTENTE", "QR Codes do mesmo boletim declaram versões VRQR diferentes");
  }
  const presentes = new Set(partes.map((p) => p.indice));
  const faltando: number[] = [];
  for (let i = 1; i <= total; i++) if (!presentes.has(i)) faltando.push(i);
  if (faltando.length > 0) {
    throw new ErroQrBu("QR_FALTANDO", `faltam os QR Codes ${faltando.join(", ")} de ${total}`);
  }
  const ultima = partes[partes.length - 1] ?? primeira;
  const assinaturaForaDoUltimo = partes.find((p) => p !== ultima && p.assinatura !== null);
  if (assinaturaForaDoUltimo) {
    throw new ErroQrBu("ASSINATURA_FORA_DO_ULTIMO", `ASSI no QR Code ${assinaturaForaDoUltimo.indice}, que não é o último`);
  }
  return {
    partes,
    versao: primeira.versao,
    conteudo: partes.map((p) => p.dados).join(" "),
    ultimoHash: ultima.hash,
    assinatura: ultima.assinatura,
    duplicadosDescartados: textos.length - unicos.length,
  };
}

function inteiro(valor: string, chave: string, posicao: number): number {
  if (!/^\d+$/.test(valor)) throw new ErroQrBu("CONTEUDO_INVALIDO", `${chave} na posição ${posicao}: valor não numérico "${valor}"`);
  const n = Number(valor);
  if (!Number.isSafeInteger(n)) throw new ErroQrBu("CONTEUDO_INVALIDO", `${chave} na posição ${posicao}: número grande demais`);
  return n;
}

type Estado = "cabecalho" | "eleicao" | "votos" | "partido" | "resumo";

const CHAVES_DE_CARGO = new Set(["TIPO", "VERC", "PART", "LEGP", "TOTP", ...CAMPOS_RESUMO]);

function erroConteudo(posicao: number, mensagem: string): never {
  throw new ErroQrBu("CONTEUDO_INVALIDO", `registro ${posicao}: ${mensagem}`);
}

/** Interpreta o conteúdo remontado do boletim. */
export function interpretarConteudo(conteudo: string): BoletimQr {
  const cabecalho: CabecalhoBu = {};
  const eleicoes: EleicaoBu[] = [];
  const camposDesconhecidos: CampoDesconhecido[] = [];
  let estado: Estado = "cabecalho";
  let eleicao: EleicaoBu | null = null;
  let cargo: CargoBu | null = null;
  let partido: PartidoBu | null = null;

  const registros = conteudo.split(" ");
  for (let posicao = 0; posicao < registros.length; posicao++) {
    const registro = registros[posicao] ?? "";
    const sep = registro.indexOf(":");
    if (sep <= 0 || sep === registro.length - 1) erroConteudo(posicao, `registro malformado "${registro}"`);
    const chave = registro.slice(0, sep);
    const valor = registro.slice(sep + 1);
    const ehVoto = /^\d+$/.test(chave);
    if (!ehVoto && !/^[A-Z]{4}$/.test(chave)) erroConteudo(posicao, `chave inválida "${chave}"`);

    if (chave === "IDEL") {
      if (estado !== "cabecalho" && estado !== "eleicao") erroConteudo(posicao, "IDEL antes do fim do cargo anterior (falta TOTC)");
      eleicao = { IDEL: inteiro(valor, chave, posicao), cargos: [] };
      eleicoes.push(eleicao);
      estado = "eleicao";
      continue;
    }

    if (estado === "cabecalho") {
      lerCampoCabecalho(cabecalho, camposDesconhecidos, chave, valor, ehVoto, posicao);
      continue;
    }
    if (!eleicao) erroConteudo(posicao, "registro fora de eleição");

    if (chave === "CARG") {
      if (estado !== "eleicao") erroConteudo(posicao, "CARG antes do fim do cargo anterior (falta TOTC)");
      cargo = { CARG: inteiro(valor, chave, posicao), votos: [], partidos: [] };
      eleicao.cargos.push(cargo);
      estado = "votos";
      continue;
    }

    if (estado === "eleicao") {
      if (chave === "MAJO" || chave === "PROP") {
        if (eleicao.cargos.length > 0 || eleicao[chave] !== undefined) erroConteudo(posicao, `${chave} fora do cabeçalho da eleição`);
        eleicao[chave] = inteiro(valor, chave, posicao);
      } else if (ehVoto || CHAVES_DE_CARGO.has(chave)) {
        erroConteudo(posicao, `${ehVoto ? "voto" : chave} fora de cargo`);
      } else {
        camposDesconhecidos.push({ chave, valor, contexto: "eleicao", posicao });
      }
      continue;
    }
    if (!cargo) erroConteudo(posicao, "registro fora de cargo");

    if (estado === "votos" || estado === "partido") {
      if (ehVoto) {
        const voto = { numero: inteiro(chave, "número", posicao), votos: inteiro(valor, chave, posicao) };
        (partido ?? cargo).votos.push(voto);
        continue;
      }
      if (chave === "TIPO" || chave === "VERC") {
        if (cargo[chave] !== undefined || cargo.votos.length > 0 || cargo.partidos.length > 0) {
          erroConteudo(posicao, `${chave} fora do cabeçalho do cargo`);
        }
        if (chave === "TIPO") {
          cargo.TIPO = inteiro(valor, chave, posicao);
        } else {
          // VERC tem 12 dígitos (aaaammddhhmm): guardado como texto para não perder zeros à esquerda.
          if (!/^\d+$/.test(valor)) erroConteudo(posicao, `VERC não numérico "${valor}"`);
          cargo.VERC = valor;
        }
        continue;
      }
      if (chave === "PART") {
        if (partido) erroConteudo(posicao, "PART antes do TOTP do partido anterior");
        partido = { PART: inteiro(valor, chave, posicao), votos: [] };
        cargo.partidos.push(partido);
        estado = "partido";
        continue;
      }
      if (chave === "LEGP" || chave === "TOTP") {
        if (!partido) erroConteudo(posicao, `${chave} fora de bloco de partido`);
        if (partido[chave] !== undefined) erroConteudo(posicao, `${chave} repetido no partido ${partido.PART}`);
        partido[chave] = inteiro(valor, chave, posicao);
        if (chave === "TOTP") {
          partido = null;
          estado = "votos";
        }
        continue;
      }
      if (!RESUMO.has(chave)) {
        camposDesconhecidos.push({ chave, valor, contexto: partido ? "partido" : "cargo", posicao });
        continue;
      }
      if (partido) erroConteudo(posicao, `${chave} antes do TOTP do partido ${partido.PART}`);
      estado = "resumo";
    }

    // Resumo do cargo.
    if (!RESUMO.has(chave)) {
      if (ehVoto) erroConteudo(posicao, "voto depois do resumo do cargo");
      camposDesconhecidos.push({ chave, valor, contexto: "resumo", posicao });
      continue;
    }
    const r = chave as ChaveResumo;
    if (cargo[r] !== undefined) erroConteudo(posicao, `${r} repetido no cargo ${cargo.CARG}`);
    cargo[r] = inteiro(valor, chave, posicao);
    if (r === "TOTC") {
      cargo = null;
      estado = "eleicao";
    }
  }

  if (eleicoes.length === 0) throw new ErroQrBu("CONTEUDO_INVALIDO", "boletim sem nenhuma eleição (IDEL)");
  if (estado !== "eleicao") throw new ErroQrBu("CONTEUDO_INVALIDO", "conteúdo termina no meio de um cargo (falta TOTC)");
  return { cabecalho, eleicoes, camposDesconhecidos };
}

function lerCampoCabecalho(
  cabecalho: CabecalhoBu,
  desconhecidos: CampoDesconhecido[],
  chave: string,
  valor: string,
  ehVoto: boolean,
  posicao: number,
): void {
  if (ehVoto) erroConteudo(posicao, "voto antes de IDEL");
  if (!(chave in CAMPOS_CABECALHO)) {
    desconhecidos.push({ chave, valor, contexto: "cabecalho", posicao });
    return;
  }
  const c = chave as ChaveCabecalho;
  if (c === "HICA") {
    const m = /^(\d+):(\d+)$/.exec(valor);
    if (!m) return erroConteudo(posicao, `HICA malformado "${valor}"`);
    (cabecalho.HICA ??= []).push({ sequencia: inteiro(m[1] ?? "", chave, posicao), codigo: m[2] ?? "" });
    return;
  }
  if (cabecalho[c] !== undefined) erroConteudo(posicao, `campo ${c} repetido no cabeçalho`);
  if (c === "AGRE") {
    cabecalho.AGRE = valor.split(".").map((s) => inteiro(s, chave, posicao));
  } else if (CABECALHO_NUMERICO.has(c)) {
    (cabecalho as Record<string, unknown>)[c] = inteiro(valor, chave, posicao);
  } else {
    (cabecalho as Record<string, unknown>)[c] = valor;
  }
}

/** Lê os QR Codes do boletim: monta, remonta o conteúdo e interpreta os campos. */
export function lerQrBu(textos: string[]): QrBuLido & { boletim: BoletimQr } {
  const montado = montarQrBu(textos);
  return { ...montado, boletim: interpretarConteudo(montado.conteudo) };
}
