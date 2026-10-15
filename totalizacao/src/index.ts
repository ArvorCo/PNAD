// Ponto de entrada da biblioteca: lê os textos dos QR Codes de um boletim de urna (QRBU e QRCE,
// em qualquer ordem e com leituras repetidas), confere a cadeia de hashes, o certificado da urna
// e sua cadeia até a AC do TSE, a assinatura da urna e a coerência das somas, e devolve tudo
// num único resultado. Um boletim só é autêntico com cadeia de hashes íntegra, assinatura válida
// com a chave do certificado, certificado emitido para a mesma urna e certificado assinado por
// uma das ACs de urna (AC URNA, AC UE2020 ou AC UE2022).
import { verificarAssinatura, type ResultadoAssinatura } from "./qrbu/assinatura.ts";
import { verificarCadeiaCertificado, type ResultadoCadeiaCertificado } from "./qrbu/cadeia.ts";
import { ErroCertificado, montarCertificado, resumirCertificado, type CertificadoUrna, type ResumoCertificado } from "./qrbu/certificado.ts";
import { verificarCadeia, type ResultadoCadeia } from "./qrbu/hash.ts";
import { ErroQrBu, interpretarConteudo, montarQrBu, type BoletimQr, type QrBuLido } from "./qrbu/parse.ts";
import { validarBoletim, type OpcoesValidacao, type Problema } from "./qrbu/validar.ts";

export type { ResultadoAssinatura, AlgoritmoAssinatura } from "./qrbu/assinatura.ts";
export type { NomeAc, ResultadoCadeiaCertificado } from "./qrbu/cadeia.ts";
export type { ResumoCertificado } from "./qrbu/certificado.ts";
export type { EloCadeia, ResultadoCadeia } from "./qrbu/hash.ts";
export type {
  BoletimQr, CabecalhoBu, CampoDesconhecido, CargoBu, EleicaoBu, HistoricoCarga, PartidoBu, VotoBu,
} from "./qrbu/parse.ts";
export type { OpcoesValidacao, Problema } from "./qrbu/validar.ts";
export { PERFIL_2T_2026, VOTOS_POR_ELEITOR_2026 } from "./qrbu/validar.ts";

export interface OpcoesLeitura extends OpcoesValidacao {
  /** Versão do formato aceita (VRQR). Padrão "6.0", a de 2026. */
  versaoEsperada?: string;
}

/** Resumo do certificado da urna com o resultado da cadeia até a AC. */
export interface CertificadoVerificado extends ResumoCertificado {
  cadeia: ResultadoCadeiaCertificado;
}

export interface ResultadoLeitura {
  /** Boletim interpretado, ou null se o conjunto de QR Codes ou o conteúdo não puderam ser lidos. */
  boletim: BoletimQr | null;
  /** Conteúdo remontado (dados dos QR unidos por espaço). */
  conteudo: string | null;
  versao: string | null;
  /** Quantidade de QR Codes do boletim e leituras repetidas descartadas. */
  quantidadeQr: number;
  duplicadosDescartados: number;
  ultimoHash: string | null;
  assinaturaHex: string | null;
  cadeia: ResultadoCadeia | null;
  assinatura: ResultadoAssinatura | null;
  certificado: CertificadoVerificado | null;
  /**
   * Cadeia de hashes íntegra, assinatura válida com a chave do certificado, certificado emitido
   * para a mesma urna do boletim e assinado por uma AC de urna.
   */
  autentico: boolean;
  /** Autêntico e sem nenhum problema estrutural. */
  valido: boolean;
  problemas: Problema[];
}

const MODELOS_ECDSA = new Set(["2013", "2015"]);
const MODELOS_EDDSA = new Set(["2020", "2022"]);

/** Problemas de coerência entre certificado, assinatura e boletim. O primeiro grupo invalida a autenticidade. */
function conferirCertificado(cert: CertificadoUrna, bu: BoletimQr | null, algoritmo: string | null): { graves: Problema[]; avisos: Problema[] } {
  const graves: Problema[] = [];
  const avisos: Problema[] = [];
  const idue = bu?.cabecalho.IDUE;
  if (idue !== undefined && Number(cert.idue) !== idue) {
    graves.push({ codigo: "CERTIFICADO_DE_OUTRA_URNA", mensagem: `certificado da urna ${cert.idue}, boletim da urna ${idue}` });
  }
  const cn = cert.titular.campos.CN ?? "";
  const serieCn = /(\d+)$/.exec(cn)?.[1];
  if (serieCn === undefined || Number(serieCn) !== Number(cert.idue)) {
    graves.push({ codigo: "CN_DIFERENTE_DA_URNA", mensagem: `titular do certificado "${cn}" não corresponde à urna ${cert.idue}` });
  }
  if (MODELOS_ECDSA.has(cert.modelo) && (algoritmo !== "ECDSA P-521" || cert.formato !== "DER")) {
    avisos.push({ codigo: "MODELO_INCOMPATIVEL", mensagem: `urna ${cert.modelo} deveria ter certificado DER com ECDSA P-521` });
  }
  if (MODELOS_EDDSA.has(cert.modelo) && (algoritmo !== "EdDSA Ed521" || cert.formato !== "PEM")) {
    avisos.push({ codigo: "MODELO_INCOMPATIVEL", mensagem: `urna ${cert.modelo} deveria ter certificado PEM com EdDSA Ed521` });
  }
  if (!MODELOS_ECDSA.has(cert.modelo) && !MODELOS_EDDSA.has(cert.modelo)) {
    avisos.push({ codigo: "MODELO_DESCONHECIDO", mensagem: `modelo de urna ${cert.modelo} desconhecido` });
  }
  const dtpl = bu?.cabecalho.DTPL;
  if (dtpl && /^\d{8}$/.test(dtpl)) {
    const dia = `${dtpl.slice(0, 4)}-${dtpl.slice(4, 6)}-${dtpl.slice(6, 8)}`;
    if (dia < cert.validadeInicio.slice(0, 10) || dia > cert.validadeFim.slice(0, 10)) {
      avisos.push({
        codigo: "CERTIFICADO_FORA_DA_VALIDADE",
        mensagem: `pleito em ${dia}, certificado válido de ${cert.validadeInicio} a ${cert.validadeFim}`,
      });
    }
  }
  return { graves, avisos };
}

/**
 * Lê e verifica um boletim de urna a partir dos textos dos seus QR Codes (QRBU e QRCE).
 * Nunca lança por causa do conteúdo: toda falha vira item de `problemas`.
 */
export function lerBoletim(qrTexts: string[], opcoes: OpcoesLeitura = {}): ResultadoLeitura {
  const problemas: Problema[] = [];
  const textosBu: string[] = [];
  const textosCe: string[] = [];
  for (const bruto of qrTexts) {
    const t = bruto.trim();
    if (t.startsWith("QRBU:")) textosBu.push(t);
    else if (t.startsWith("QRCE:")) textosCe.push(t);
    else problemas.push({ codigo: "QR_DESCONHECIDO", mensagem: `QR Code que não é do boletim nem do certificado: "${t.slice(0, 20)}"` });
  }

  const resultado: ResultadoLeitura = {
    boletim: null,
    conteudo: null,
    versao: null,
    quantidadeQr: 0,
    duplicadosDescartados: 0,
    ultimoHash: null,
    assinaturaHex: null,
    cadeia: null,
    assinatura: null,
    certificado: null,
    autentico: false,
    valido: false,
    problemas,
  };

  let montado: QrBuLido;
  try {
    montado = montarQrBu(textosBu);
  } catch (e) {
    if (!(e instanceof ErroQrBu)) throw e;
    problemas.push({ codigo: e.codigo, mensagem: e.message });
    return resultado;
  }
  resultado.conteudo = montado.conteudo;
  resultado.versao = montado.versao;
  resultado.quantidadeQr = montado.partes.length;
  resultado.duplicadosDescartados = montado.duplicadosDescartados;
  resultado.ultimoHash = montado.ultimoHash;
  resultado.assinaturaHex = montado.assinatura;

  const versaoEsperada = opcoes.versaoEsperada ?? "6.0";
  if (montado.versao !== versaoEsperada) {
    problemas.push({ codigo: "VERSAO_NAO_SUPORTADA", mensagem: `formato VRQR ${montado.versao}, esperado ${versaoEsperada}` });
  }

  const cadeia = verificarCadeia(montado.partes);
  resultado.cadeia = cadeia;
  if (!cadeia.ok) {
    const quebrados = cadeia.elos.filter((e) => !e.confere).map((e) => e.indice);
    problemas.push({ codigo: "CADEIA_HASH_INVALIDA", mensagem: `HASH não confere nos QR Codes ${quebrados.join(", ")}` });
  }

  try {
    resultado.boletim = interpretarConteudo(montado.conteudo);
  } catch (e) {
    if (!(e instanceof ErroQrBu)) throw e;
    problemas.push({ codigo: e.codigo, mensagem: e.message });
  }

  let certificado: CertificadoUrna | null = null;
  try {
    certificado = montarCertificado(textosCe);
    const cadeiaCertificado = verificarCadeiaCertificado(certificado);
    resultado.certificado = { ...resumirCertificado(certificado), cadeia: cadeiaCertificado };
    if (!cadeiaCertificado.valida) {
      problemas.push({ codigo: "CADEIA_CERTIFICADO_INVALIDA", mensagem: cadeiaCertificado.motivo ?? "certificado não emitido por AC de urna" });
    }
  } catch (e) {
    if (!(e instanceof ErroCertificado)) throw e;
    problemas.push({ codigo: e.codigo, mensagem: e.message });
  }

  let graves: Problema[] = [];
  if (montado.assinatura === null) {
    problemas.push({ codigo: "ASSINATURA_AUSENTE", mensagem: "o último QR Code não traz ASSI" });
  } else if (certificado) {
    const assinatura = verificarAssinatura(montado.ultimoHash, montado.assinatura, certificado);
    resultado.assinatura = assinatura;
    if (!assinatura.valido) {
      problemas.push({ codigo: "ASSINATURA_INVALIDA", mensagem: assinatura.motivo ?? "assinatura inválida" });
    }
    const conferencia = conferirCertificado(certificado, resultado.boletim, assinatura.algoritmo);
    graves = conferencia.graves;
    problemas.push(...conferencia.graves, ...conferencia.avisos);
  }

  if (resultado.boletim) problemas.push(...validarBoletim(resultado.boletim, opcoes));

  resultado.autentico =
    cadeia.ok && resultado.assinatura?.valido === true && resultado.certificado?.cadeia.valida === true && graves.length === 0;
  resultado.valido = resultado.autentico && resultado.boletim !== null && problemas.length === 0;
  return resultado;
}
