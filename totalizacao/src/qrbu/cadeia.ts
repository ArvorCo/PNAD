// Cadeia de certificação do certificado da urna até a autoridade certificadora do TSE.
//
// O certificado que chega nos QR Codes QRCE é emitido por uma de três ACs, fixadas aqui como
// âncoras de confiança (certificados em ./ac/):
//   AC URNA   urnas 2013 e 2015  ECDSA P-521 com SHA-512 (OID 1.2.840.10045.4.3.4): a mensagem é
//                                 o SHA-512 do tbsCertificate e a assinatura é DER no signatureValue
//   AC UE2020 urnas 2020         EdDSA Ed521 (OID 1.3.6.1.4.1.44588.2.1) sobre os bytes crus do
//   AC UE2022 urnas 2022         tbsCertificate, assinatura de 132 bytes
//
// Para aceitar, exige-se: CN do emissor igual ao de uma AC conhecida; Name do emissor idêntico,
// byte a byte, ao titular da AC; identificador de chave da autoridade igual ao identificador de
// chave da AC (quando os dois existem); algoritmo de assinatura compatível com a chave da AC; e
// assinatura válida. A validade temporal da AC é informada e não é critério: a AC URNA expirou
// em 18/07/2026, e os certificados das urnas 2013 e 2015 que ela emitiu valem até 2027 e 2030.
import { sha512 } from "@noble/hashes/sha2.js";
import { PEM_AC_UE2020, PEM_AC_UE2022, PEM_AC_URNA } from "./ac/certificados.ts";
import { algoritmoDoCertificado, type AlgoritmoAssinatura } from "./assinatura.ts";
import { asciiParaBytes, bytesIguais } from "./bytes.ts";
import { decodificarCertificado, OID, type CertificadoX509 } from "./certificado.ts";
import { verificarEcdsaP521 } from "./ecdsa.ts";
import { verificarEd521 } from "./ed521.ts";

export type NomeAc = "AC URNA" | "AC UE2020" | "AC UE2022";

export interface AutoridadeCertificadora {
  nome: NomeAc;
  certificado: CertificadoX509;
  algoritmo: AlgoritmoAssinatura;
}

export interface ResultadoCadeiaCertificado {
  valida: boolean;
  /** AC emissora reconhecida pelo nome, mesmo quando a assinatura não confere. */
  ac: NomeAc | null;
  motivo: string | null;
  /** Validade da AC, só como informação. */
  acValidadeInicio: string | null;
  acValidadeFim: string | null;
}

function carregar(nome: NomeAc, pem: string): AutoridadeCertificadora {
  const certificado = decodificarCertificado(asciiParaBytes(pem));
  const algoritmo = algoritmoDoCertificado(certificado);
  if (certificado.titular.campos.CN !== nome || !algoritmo) {
    throw new Error(`certificado embutido da ${nome} não confere`);
  }
  return { nome, certificado, algoritmo };
}

/** As três ACs que emitem certificados de urna. */
export const AUTORIDADES: readonly AutoridadeCertificadora[] = [
  carregar("AC URNA", PEM_AC_URNA),
  carregar("AC UE2020", PEM_AC_UE2020),
  carregar("AC UE2022", PEM_AC_UE2022),
];

/** Verifica se o certificado foi emitido e assinado por uma das ACs de urna. Nunca lança. */
export function verificarCadeiaCertificado(
  cert: CertificadoX509,
  autoridades: readonly AutoridadeCertificadora[] = AUTORIDADES,
): ResultadoCadeiaCertificado {
  const cn = cert.emissor.campos.CN ?? null;
  const ac = autoridades.find((a) => a.certificado.titular.campos.CN === cn);
  if (!ac) {
    return { valida: false, ac: null, motivo: `emissor "${cn ?? "sem CN"}" não é uma AC de urna conhecida`, acValidadeInicio: null, acValidadeFim: null };
  }
  const base = { ac: ac.nome, acValidadeInicio: ac.certificado.validadeInicio, acValidadeFim: ac.certificado.validadeFim };
  const reprovar = (motivo: string): ResultadoCadeiaCertificado => ({ valida: false, motivo, ...base });

  if (!bytesIguais(cert.emissorDer, ac.certificado.titularDer)) return reprovar(`nome do emissor difere do titular da ${ac.nome}`);
  const aki = cert.identificadorChaveAutoridade;
  const ski = ac.certificado.identificadorChaveTitular;
  if (aki !== null && ski !== null && aki !== ski) return reprovar(`identificador de chave da autoridade difere do da ${ac.nome}`);

  let valida: boolean;
  try {
    if (ac.algoritmo === "ECDSA P-521") {
      if (cert.algoritmoAssinatura !== OID.ECDSA_SHA512) return reprovar(`algoritmo ${cert.algoritmoAssinatura} incompatível com a ${ac.nome}`);
      valida = verificarEcdsaP521(sha512(cert.tbs), cert.assinaturaEmissor, ac.certificado.chavePublica.bytes);
    } else {
      if (cert.algoritmoAssinatura !== OID.ED521) return reprovar(`algoritmo ${cert.algoritmoAssinatura} incompatível com a ${ac.nome}`);
      valida = verificarEd521(cert.tbs, cert.assinaturaEmissor, ac.certificado.chavePublica.bytes);
    }
  } catch (e) {
    return reprovar(`assinatura do certificado malformada: ${(e as Error).message}`);
  }
  return valida ? { valida: true, motivo: null, ...base } : reprovar(`assinatura do certificado não confere com a chave da ${ac.nome}`);
}
