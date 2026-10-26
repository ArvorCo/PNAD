// Leitor do arquivo de assinaturas da seção (`-vota.vsc` da urna, `-sa.vsc` do sistema de apuração).
//
// Formato observado nos arquivos do 2º turno de 2026 (DER, tags conferidas em UE2013, UE2022 e SA):
//
//   SEQUENCE {
//     assinaturaSW  EntidadeVsc       -- chave de software do TSE (usuário "SEVIN")
//     assinaturaHW  EntidadeVsc       -- chave de hardware da urna (usuário "UEAO" + série)
//     SEQUENCE { ENUMERATED modelo (13, 15, 20, 22), ENUMERATED algoritmo da chave de hardware }
//   }
//   EntidadeVsc ::= SEQUENCE {
//     criadoEm GeneralString "AAAAMMDDThhmmss",  versao INTEGER,
//     autoAssinado SEQUENCE {
//       usuario SEQUENCE { nome GeneralString, serial INTEGER },
//       SEQUENCE { ENUMERATED algoritmo de hash },          -- 4 = SHA-512
//       SEQUENCE { ENUMERATED algoritmo, INTEGER bits },     -- HW: 2 ECDSA P-521, 4 Ed521; SW: 3 / 256
//       SEQUENCE { INTEGER tamanho, OCTET STRING sha512(conteudo), OCTET STRING assinatura } },
//     conteudo OCTET STRING  -- DER: SEQUENCE { SEQUENCE OF SEQUENCE { nome GeneralString,
//                            --        SEQUENCE { INTEGER tamanho, OCTET STRING sha512, OCTET STRING assinatura } } }
//     [0] data da chave (só SW) | [1] certificado da urna, PEM ou DER (só HW)
//   }
//
// A assinatura de hardware segue a regra do QR Code do BU: a urna assina SHA-512 do resumo
// SHA-512 (Ed521 nas UE2020/2022, ECDSA P-521 com DER nas UE2013/2015). Conferido aqui: a
// autoassinatura cobre o conteúdo, que lista o resumo de cada arquivo da seção, e a entrada do
// BU bate com o SHA-512 do `-bu.dat` publicado. A assinatura SW usa algoritmo que este leitor
// não verifica; o resumo dela é conferido.
import { createHash } from "node:crypto";
import { verificarAssinatura } from "../../../totalizacao/src/qrbu/assinatura.ts";
import { verificarCadeiaCertificado } from "../../../totalizacao/src/qrbu/cadeia.ts";
import type { NomeAc } from "../../../totalizacao/src/qrbu/cadeia.ts";
import { decodificarCertificado } from "../../../totalizacao/src/qrbu/certificado.ts";
import type { CertificadoX509 } from "../../../totalizacao/src/qrbu/certificado.ts";
import { filhos, lerInteiro, lerTlv } from "../../../totalizacao/src/qrbu/der.ts";
import type { Tlv } from "../../../totalizacao/src/qrbu/der.ts";

export class ErroVsc extends Error {
  constructor(mensagem: string) {
    super(mensagem);
    this.name = "ErroVsc";
  }
}

export interface ArquivoVsc {
  nome: string;
  tamanho: number;
  sha512: string;
  assinatura: Uint8Array;
}

export interface EntidadeVsc {
  criadoEm: string;
  versao: number;
  usuario: string;
  usuarioSerial: string;
  algoritmoHash: number;
  algoritmo: number;
  bits: number;
  tamanhoConteudo: number;
  sha512Conteudo: string;
  assinaturaConteudo: Uint8Array;
  conteudo: Uint8Array;
  arquivos: ArquivoVsc[];
  /** [0] na SW (texto, data da chave), [1] na HW (certificado). */
  extra: { tag: number; valor: Uint8Array } | null;
}

export interface Vsc {
  sw: EntidadeVsc;
  hw: EntidadeVsc;
  modeloCodigo: number | null;
  algoritmoHwCodigo: number | null;
}

const hex = (b: Uint8Array): string => Buffer.from(b).toString("hex");
const HEX = (b: Uint8Array): string => hex(b).toUpperCase();
export const sha512Hex = (b: Uint8Array): string => createHash("sha512").update(b).digest("hex");
const texto = (t: Tlv): string => new TextDecoder("latin1").decode(t.valor);
const inteiro = (t: Tlv | undefined, rotulo: string): bigint => {
  if (t === undefined || (t.tag !== 0x02 && t.tag !== 0x0a)) throw new ErroVsc(`${rotulo}: esperado INTEGER/ENUMERATED`);
  return lerInteiro({ ...t, tag: 0x02 });
};
const exigir = (t: Tlv | undefined, tag: number, rotulo: string): Tlv => {
  if (t === undefined || t.tag !== tag) throw new ErroVsc(`${rotulo}: tag ${t?.tag.toString(16) ?? "ausente"}, esperado ${tag.toString(16)}`);
  return t;
};

function lerArquivos(conteudo: Uint8Array): ArquivoVsc[] {
  const externo = exigir(lerTlv(conteudo, 0), 0x30, "conteudo");
  const lista = exigir(filhos(externo)[0], 0x30, "lista de arquivos");
  return filhos(lista).map((item, i) => {
    const [nome, ass] = filhos(exigir(item, 0x30, `arquivo ${i}`));
    const [tam, resumo, sig] = filhos(exigir(ass, 0x30, `assinatura do arquivo ${i}`));
    return {
      nome: texto(exigir(nome, 0x1b, `nome do arquivo ${i}`)),
      tamanho: Number(inteiro(tam, "tamanho")),
      sha512: hex(exigir(resumo, 0x04, "resumo").valor),
      assinatura: exigir(sig, 0x04, "assinatura").valor,
    };
  });
}

function lerEntidade(t: Tlv | undefined, rotulo: string): EntidadeVsc {
  const partes = filhos(exigir(t, 0x30, rotulo));
  const [data, versao, auto, conteudo] = partes;
  const [usuario, algHash, alg, ass] = filhos(exigir(auto, 0x30, `${rotulo}.autoAssinado`));
  const [nome, serial] = filhos(exigir(usuario, 0x30, `${rotulo}.usuario`));
  const [bitsAlg, bits] = filhos(exigir(alg, 0x30, `${rotulo}.algoritmo`));
  const [tam, resumo, sig] = filhos(exigir(ass, 0x30, `${rotulo}.assinatura`));
  const corpo = exigir(conteudo, 0x04, `${rotulo}.conteudo`).valor;
  const extra = partes.slice(4).find((p) => p.tag === 0x80 || p.tag === 0x81);
  return {
    criadoEm: texto(exigir(data, 0x1b, `${rotulo}.criadoEm`)),
    versao: Number(inteiro(versao, "versao")),
    usuario: texto(exigir(nome, 0x1b, `${rotulo}.usuario.nome`)),
    usuarioSerial: inteiro(serial, "serial").toString(10),
    algoritmoHash: Number(inteiro(filhos(exigir(algHash, 0x30, "algoritmoHash"))[0], "algoritmoHash")),
    algoritmo: Number(inteiro(bitsAlg, "algoritmo")),
    bits: Number(inteiro(bits, "bits")),
    tamanhoConteudo: Number(inteiro(tam, "tamanho")),
    sha512Conteudo: hex(exigir(resumo, 0x04, "resumo").valor),
    assinaturaConteudo: exigir(sig, 0x04, "assinatura").valor,
    conteudo: corpo,
    arquivos: lerArquivos(corpo),
    extra: extra === undefined ? null : { tag: extra.tag, valor: extra.valor },
  };
}

/** Decodifica um `.vsc`. Lança ErroVsc (ou erro do leitor DER) quando a estrutura não é a esperada. */
export function decodificarVsc(bytes: Uint8Array): Vsc {
  const raiz = lerTlv(bytes, 0);
  if (raiz.fim !== bytes.length) throw new ErroVsc(`bytes depois da estrutura: ${bytes.length - raiz.fim}`);
  const [sw, hw, rodape] = filhos(exigir(raiz, 0x30, "vsc"));
  const r = rodape?.tag === 0x30 ? filhos(rodape) : [];
  return {
    sw: lerEntidade(sw, "assinaturaSW"),
    hw: lerEntidade(hw, "assinaturaHW"),
    modeloCodigo: r[0] === undefined ? null : Number(inteiro(r[0], "modelo")),
    algoritmoHwCodigo: r[1] === undefined ? null : Number(inteiro(r[1], "algoritmo")),
  };
}

export interface ResumoVsc {
  swCriadoEm: string;
  swUsuario: string;
  swSerial: string;
  swChaveData: string | null;
  swResumoConfere: boolean;
  hwCriadoEm: string;
  hwUsuario: string;
  hwSerial: string;
  hwAlgoritmo: number;
  hwBits: number;
  hwResumoConfere: boolean;
  modeloCodigo: number | null;
  algoritmoHwCodigo: number | null;
  /** nomes dos arquivos iguais e na mesma ordem nas duas assinaturas, com o mesmo resumo */
  listasConferem: boolean;
  arquivos: ArquivoVsc[];
  certificado: {
    formato: string;
    der: Uint8Array;
    sha256: string;
    serial: string;
    serialHex: string;
    emissorCN: string | null;
    titularCN: string | null;
    titular: string;
    validadeInicio: string;
    validadeFim: string;
    algoritmoChave: string;
    parametroChave: string | null;
    chavePublicaSha256: string;
    aki: string | null;
    ski: string | null;
    cadeiaValida: boolean;
    ac: NomeAc | null;
    motivoCadeia: string | null;
  } | null;
  erroCertificado: string | null;
  /** autoassinatura de hardware conferida com a chave do certificado; null sem certificado */
  hwAssinaturaValida: boolean | null;
  hwAlgoritmoNome: string | null;
  /** assinatura de hardware da entrada do BU (`-bu.dat` ou `-busa.dat`); null sem entrada ou sem verificação */
  hwAssinaturaBuValida: boolean | null;
  /** série do CN do certificado = série do usuário HW */
  cnConfereUsuario: boolean | null;
}

const sha256Hex = (b: Uint8Array): string => createHash("sha256").update(b).digest("hex");

export interface OpcoesResumo {
  /** verifica a autoassinatura de hardware (custa uma verificação Ed521/ECDSA) */
  verificarAssinatura?: boolean;
}

/** Resume um `.vsc` decodificado: certificado, cadeia até a AC e coerência interna. */
export function resumirVsc(v: Vsc, o: OpcoesResumo = {}): ResumoVsc {
  let cert: CertificadoX509 | null = null;
  let erroCertificado: string | null = null;
  if (v.hw.extra?.tag === 0x81) {
    try {
      cert = decodificarCertificado(v.hw.extra.valor);
    } catch (e) {
      erroCertificado = e instanceof Error ? e.message : String(e);
    }
  } else erroCertificado = "assinatura de hardware sem certificado";
  const cadeia = cert === null ? null : verificarCadeiaCertificado(cert);
  let hwValida: boolean | null = null;
  let hwAlg: string | null = null;
  let buValida: boolean | null = null;
  if (cert !== null && o.verificarAssinatura !== false) {
    const r = verificarAssinatura(v.hw.sha512Conteudo.toUpperCase(), HEX(v.hw.assinaturaConteudo), cert);
    hwValida = r.valido;
    hwAlg = r.algoritmo;
    const bu = v.hw.arquivos.find((a) => /-bu(sa)?\.dat$/.test(a.nome));
    if (bu !== undefined) buValida = verificarAssinatura(bu.sha512.toUpperCase(), HEX(bu.assinatura), cert).valido;
  }
  const sw = v.sw.arquivos;
  const hw = v.hw.arquivos;
  const listas = sw.length === hw.length && sw.every((a, i) => a.nome === hw[i]?.nome && a.sha512 === hw[i]?.sha512 && a.tamanho === hw[i]?.tamanho);
  const cn = cert?.titular.campos.CN ?? null;
  const serieCn = cn === null ? null : (/(\d+)$/.exec(cn)?.[1] ?? null);
  return {
    swCriadoEm: v.sw.criadoEm,
    swUsuario: v.sw.usuario,
    swSerial: v.sw.usuarioSerial,
    swChaveData: v.sw.extra?.tag === 0x80 ? new TextDecoder().decode(v.sw.extra.valor) : null,
    swResumoConfere: sha512Hex(v.sw.conteudo) === v.sw.sha512Conteudo && v.sw.tamanhoConteudo === v.sw.conteudo.length,
    hwCriadoEm: v.hw.criadoEm,
    hwUsuario: v.hw.usuario,
    hwSerial: v.hw.usuarioSerial,
    hwAlgoritmo: v.hw.algoritmo,
    hwBits: v.hw.bits,
    hwResumoConfere: sha512Hex(v.hw.conteudo) === v.hw.sha512Conteudo && v.hw.tamanhoConteudo === v.hw.conteudo.length,
    modeloCodigo: v.modeloCodigo,
    algoritmoHwCodigo: v.algoritmoHwCodigo,
    listasConferem: listas,
    arquivos: hw,
    certificado: cert === null || cadeia === null ? null : {
      formato: cert.formato,
      der: cert.der,
      sha256: sha256Hex(cert.der),
      serial: cert.serial.toString(10),
      serialHex: cert.serial.toString(16).toUpperCase(),
      emissorCN: cert.emissor.campos.CN ?? null,
      titularCN: cn,
      titular: cert.titular.atributos.map((x) => `${x.rotulo ?? x.oid}=${x.valor}`).join(","),
      validadeInicio: cert.validadeInicio,
      validadeFim: cert.validadeFim,
      algoritmoChave: cert.chavePublica.algoritmo,
      parametroChave: cert.chavePublica.parametro,
      chavePublicaSha256: sha256Hex(cert.chavePublica.bytes),
      aki: cert.identificadorChaveAutoridade,
      ski: cert.identificadorChaveTitular,
      cadeiaValida: cadeia.valida,
      ac: cadeia.ac,
      motivoCadeia: cadeia.motivo,
    },
    erroCertificado,
    hwAssinaturaValida: hwValida,
    hwAlgoritmoNome: hwAlg,
    hwAssinaturaBuValida: buValida,
    cnConfereUsuario: serieCn === null ? null : BigInt(serieCn) === BigInt(v.hw.usuarioSerial),
  };
}

/** Confere um arquivo da seção contra a entrada do `.vsc` (tamanho e SHA-512). null se o arquivo não está listado. */
export function conferirArquivo(arquivos: readonly ArquivoVsc[], nome: string, bytes: Uint8Array): boolean | null {
  const a = arquivos.find((x) => x.nome === nome);
  if (a === undefined) return null;
  return a.tamanho === bytes.length && a.sha512 === sha512Hex(bytes);
}
