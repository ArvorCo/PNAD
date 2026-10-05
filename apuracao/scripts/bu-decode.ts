// Decodificador do boletim de urna (BU) do TSE, sem dependência externa.
//
// Formato: ASN.1 em BER com IMPLICIT TAGS, especificação `bu.asn1` v2 do TSE para as
// eleições de 2024 em diante (módulo ModuloBU), guardada em scripts/secoes/bu.asn1: cópia
// verbatim de docv2/spec/bu.asn1 em github.com/doccaz/urnas-br (commit 6026afb6), que
// reproduz o pacote "formato-arquivos-bu-rdv-ass-digital-v2". O arquivo `-bu.dat` (e o
// `-busa.dat` do Sistema de Apuração) é um EntidadeEnvelopeGenerico cujo `conteudo`
// (OCTET STRING) carrega a EntidadeBoletimUrna. Gabarito independente: scripts/bu-referencia.py
// (asn1tools), conferido campo a campo em tests/bu-decode.test.ts.
//
// O BU não traz o modelo da urna (UE2009 a UE2022): não há campo para isso na
// especificação. O modelo sai do log da mesma urna (scripts/secoes/log-urna.ts).
//
// Uso direto: bun run scripts/bu-decode.ts arquivo-bu.dat  (imprime JSON)

export class ErroBu extends Error {
  override name = "ErroBu";
}

// ---------------------------------------------------------------- BER

/** Um elemento TLV. `tag` é o octeto identificador (classe, construído, número < 31). */
export interface Tlv {
  tag: number;
  construido: boolean;
  /** início do conteúdo */
  ini: number;
  /** fim do conteúdo (exclusivo) */
  fim: number;
  /** fim do elemento inteiro, incluindo fim de conteúdo indefinido */
  prox: number;
}

const INDEFINIDO = -1;

function lerComprimento(buf: Uint8Array, pos: number): { comp: number; pos: number } {
  const b = buf[pos];
  if (b === undefined) throw new ErroBu(`comprimento ausente em ${pos}`);
  if (b < 0x80) return { comp: b, pos: pos + 1 };
  if (b === 0x80) return { comp: INDEFINIDO, pos: pos + 1 };
  const n = b & 0x7f;
  if (n > 4) throw new ErroBu(`comprimento com ${n} octetos em ${pos}`);
  let comp = 0;
  for (let i = 1; i <= n; i += 1) {
    const o = buf[pos + i];
    if (o === undefined) throw new ErroBu(`comprimento truncado em ${pos}`);
    comp = comp * 256 + o;
  }
  return { comp, pos: pos + 1 + n };
}

/** Lê um TLV a partir de `pos`, sem passar de `limite`. */
export function lerTlv(buf: Uint8Array, pos: number, limite: number = buf.length): Tlv {
  const tag = buf[pos];
  if (tag === undefined || pos >= limite) throw new ErroBu(`TLV fora do buffer em ${pos}`);
  if ((tag & 0x1f) === 0x1f) throw new ErroBu(`tag de número alto em ${pos} (fora da especificação do BU)`);
  const construido = (tag & 0x20) !== 0;
  const { comp, pos: ini } = lerComprimento(buf, pos + 1);
  if (comp === INDEFINIDO) {
    if (!construido) throw new ErroBu(`comprimento indefinido em primitivo em ${pos}`);
    let p = ini;
    while (p < limite) {
      if (buf[p] === 0 && buf[p + 1] === 0) return { tag, construido, ini, fim: p, prox: p + 2 };
      p = lerTlv(buf, p, limite).prox;
    }
    throw new ErroBu(`fim de conteúdo ausente para TLV em ${pos}`);
  }
  const fim = ini + comp;
  if (fim > limite) throw new ErroBu(`TLV em ${pos} excede o limite (${fim} > ${limite})`);
  return { tag, construido, ini, fim, prox: fim };
}

/** Filhos diretos de um TLV construído. */
export function filhos(buf: Uint8Array, pai: Tlv): Tlv[] {
  if (!pai.construido) throw new ErroBu(`TLV primitivo 0x${pai.tag.toString(16)} não tem filhos`);
  const out: Tlv[] = [];
  let p = pai.ini;
  while (p < pai.fim) {
    const t = lerTlv(buf, p, pai.fim);
    out.push(t);
    p = t.prox;
  }
  return out;
}

/** INTEGER/ENUMERATED em complemento de dois. */
export function inteiro(buf: Uint8Array, t: Tlv): number {
  const n = t.fim - t.ini;
  if (n < 1 || n > 6) throw new ErroBu(`inteiro com ${n} octetos em ${t.ini}`);
  let v = 0;
  for (let i = t.ini; i < t.fim; i += 1) v = v * 256 + (buf[i] ?? 0);
  if (((buf[t.ini] ?? 0) & 0x80) !== 0) v -= 2 ** (8 * n);
  return v;
}

/** GeneralString: octetos em ISO-8859-1, um caractere por octeto. */
export function texto(buf: Uint8Array, t: Tlv): string {
  let s = "";
  for (let i = t.ini; i < t.fim; i += 1) s += String.fromCharCode(buf[i] ?? 0);
  return s;
}

export function hex(buf: Uint8Array, t: Tlv): string {
  let s = "";
  for (let i = t.ini; i < t.fim; i += 1) s += (buf[i] ?? 0).toString(16).padStart(2, "0");
  return s;
}

// Octetos identificadores usados pela especificação (IMPLICIT TAGS).
const T = {
  INTEGER: 0x02,
  OCTET: 0x04,
  ENUM: 0x0a,
  GENSTR: 0x1b,
  SEQ: 0x30,
  /** [n] primitivo de contexto */
  ctx: (n: number): number => 0x80 | n,
  /** [n] construído de contexto */
  ctxC: (n: number): number => 0xa0 | n,
} as const;

/** Percorre os filhos de uma SEQUENCE na ordem da especificação. */
class Cursor {
  private i = 0;
  private readonly itens: Tlv[];

  constructor(
    private readonly buf: Uint8Array,
    pai: Tlv,
    private readonly onde: string,
  ) {
    this.itens = filhos(buf, pai);
  }

  private desc(tag: number | undefined): string {
    return tag === undefined ? "fim" : `0x${tag.toString(16)}`;
  }

  exigir(tag: number, campo: string): Tlv {
    const t = this.itens[this.i];
    if (t === undefined || t.tag !== tag) {
      throw new ErroBu(`${this.onde}.${campo}: esperava 0x${tag.toString(16)}, achou ${this.desc(t?.tag)}`);
    }
    this.i += 1;
    return t;
  }

  /** Um de vários tags (CHOICE sem tag própria). */
  exigirUm(tags: readonly number[], campo: string): Tlv {
    const t = this.itens[this.i];
    if (t === undefined || !tags.includes(t.tag)) {
      throw new ErroBu(`${this.onde}.${campo}: esperava ${tags.map((x) => `0x${x.toString(16)}`).join("|")}, achou ${this.desc(t?.tag)}`);
    }
    this.i += 1;
    return t;
  }

  opcional(tag: number): Tlv | null {
    const t = this.itens[this.i];
    if (t === undefined || t.tag !== tag) return null;
    this.i += 1;
    return t;
  }

  opcionalUm(tags: readonly number[]): Tlv | null {
    const t = this.itens[this.i];
    if (t === undefined || !tags.includes(t.tag)) return null;
    this.i += 1;
    return t;
  }

  int(campo: string, tag: number = T.INTEGER): number {
    return inteiro(this.buf, this.exigir(tag, campo));
  }

  str(campo: string): string {
    return texto(this.buf, this.exigir(T.GENSTR, campo));
  }

  oct(campo: string): string {
    return hex(this.buf, this.exigir(T.OCTET, campo));
  }

  /** Extensões desconhecidas no fim da SEQUENCE seriam mudança de especificação: falha. */
  fim(): void {
    const t = this.itens[this.i];
    if (t !== undefined) throw new ErroBu(`${this.onde}: elemento inesperado 0x${t.tag.toString(16)} na posição ${this.i}`);
  }
}

// ---------------------------------------------------------------- enumerações da especificação

export const FASE: Readonly<Record<number, string>> = { 1: "simulado", 2: "oficial", 3: "treinamento" };
export const TIPO_URNA: Readonly<Record<number, string>> = {
  1: "secao",
  3: "contingencia",
  4: "reservaSecao",
  6: "reservaEncerrandoSecao",
};
export const TIPO_ARQUIVO: Readonly<Record<number, string>> = {
  1: "votacaoUE",
  2: "votacaoRED",
  3: "saMistaMRParcialCedula",
  4: "saMistaBUImpressoCedula",
  5: "saManual",
  6: "saEletronica",
};
export const TIPO_ENVELOPE: Readonly<Record<number, string>> = {
  1: "envelopeBoletimUrna",
  2: "envelopeRegistroDigitalVoto",
  4: "envelopeBoletimUrnaImpresso",
  5: "envelopeImagemBiometria",
};
export const TIPO_CARGO: Readonly<Record<number, string>> = { 1: "majoritario", 2: "proporcional", 3: "consulta" };
export const TIPO_VOTO: Readonly<Record<number, string>> = {
  1: "nominal",
  2: "branco",
  3: "nulo",
  4: "legenda",
  5: "cargoSemCandidato",
};
export const CARGO_CONSTITUCIONAL: Readonly<Record<number, string>> = {
  1: "presidente",
  2: "vicePresidente",
  3: "governador",
  4: "viceGovernador",
  5: "senador",
  6: "deputadoFederal",
  7: "deputadoEstadual",
  8: "deputadoDistrital",
  9: "primeiroSuplenteSenador",
  10: "segundoSuplenteSenador",
  11: "prefeito",
  12: "vicePrefeito",
  13: "vereador",
};
export const TIPO_APURACAO: Readonly<Record<number, string>> = {
  1: "totalmenteManual",
  2: "totalmenteEletronica",
  3: "mistaBU",
  4: "mistaMR",
};
/** Alternativas de TipoApuracaoSA, pela tag de contexto. */
export const ALTERNATIVA_SA: readonly string[] = ["apuracaoMistaMR", "apuracaoMistaBUAE", "apuracaoTotalmenteManual", "apuracaoEletronica"];

export function rotulo(tabela: Readonly<Record<number, string>>, v: number): string {
  return tabela[v] ?? `desconhecido(${v})`;
}

// ---------------------------------------------------------------- tipos decodificados

export type IdEleitoral = { tipo: "idProcessoEleitoral" | "idPleito" | "idEleicao"; valor: number };

export interface Cabecalho {
  dataGeracao: string;
  idEleitoral: IdEleitoral;
}

export interface MunicipioZona {
  municipio: number;
  zona: number;
}

export interface IdentificacaoSecao {
  municipioZona: MunicipioZona;
  local: number;
  secao: number;
}

export type IdentificacaoUrna =
  | { tipo: "identificacaoSecaoEleitoral"; secao: IdentificacaoSecao }
  | { tipo: "identificacaoContingencia"; municipioZona: MunicipioZona };

export interface Carga {
  numeroInternoUrna: number;
  numeroSerieFC: string;
  identificadorGeradorMidia: { nome: string; serialCertificadoTPM: string; serialInstalacao: string };
  dataHoraCarga: string;
  codigoCarga: string;
}

export interface MotivoSA {
  alternativa: string;
  tipoApuracao: number;
  motivoApuracao: number;
}

export interface Urna {
  tipoUrna: number;
  versaoVotacao: string;
  correspondenciaResultado: { identificacao: IdentificacaoUrna; carga: Carga };
  tipoArquivo: number;
  numeroSerieFV: string;
  motivoUtilizacaoSA: MotivoSA | null;
}

export interface DadosSecao {
  dataHoraAbertura: string;
  dataHoraEncerramento: string;
  dataHoraDesligamentoVotoImpresso: string | null;
}

export interface DadosSA {
  juntaApuradora: number;
  turmaApuradora: number;
  numeroInternoUrnaOrigem: number | null;
}

export interface VotoVotavel {
  tipoVoto: number;
  quantidadeVotos: number;
  /** null em branco e nulo */
  partido: number | null;
  codigo: number | null;
  ordemGeracaoHash: number;
  hash: string;
}

export interface CodigoCargo {
  tipo: "cargoConstitucional" | "numeroCargoConsultaLivre";
  /** código constitucional (1 a 13) ou número livre (25 a 99): não colidem */
  valor: number;
}

export interface TotalVotosCargo {
  codigoCargo: CodigoCargo;
  ordemImpressao: number;
  votosVotaveis: VotoVotavel[];
}

export interface ResultadoVotacao {
  tipoCargo: number;
  qtdComparecimento: number;
  totaisVotosCargo: TotalVotosCargo[];
}

export interface ResultadoEleicao {
  idEleicao: number;
  qtdEleitoresAptos: number;
  qtdEleitoresAptosSecao: number;
  qtdEleitoresAptosTTE: number;
  resultadosVotacao: ResultadoVotacao[];
  ultimoHashVotosVotavel: string;
  assinaturaUltimoHashVotosVotavel: string;
}

export interface BoletimUrna {
  cabecalho: Cabecalho;
  fase: number;
  urna: Urna;
  identificacaoSecao: IdentificacaoSecao;
  dataHoraEmissao: string;
  dadosSecao: DadosSecao | null;
  dadosSA: DadosSA | null;
  qtdEleitoresCompareceram: number;
  detalhamentoComparecimento: {
    qtdEleitoresCompareceramSemBiometria: number;
    qtdEleitoresHabilitadosPorBiometria: number;
    qtdEleitoresHabilitadosPorBiografia: number;
  } | null;
  resultadosVotacaoPorEleicao: ResultadoEleicao[];
  historicoCodigosCarga: string[];
  historicoVotoImpresso: Array<{ idImpressoraVotos: number; idRepositorioVotos: number; dataHoraLigamento: string }> | null;
}

export interface Envelope {
  cabecalho: Cabecalho;
  fase: number;
  /** presente no RDV, omitido no BU */
  temUrna: boolean;
  identificacao: IdentificacaoUrna;
  tipoEnvelope: number;
  /** com `seguranca` o conteúdo vem cifrado e não é decodificável */
  cifrado: boolean;
  conteudo: Uint8Array;
}

// ---------------------------------------------------------------- mapeamento

function cabecalho(buf: Uint8Array, t: Tlv, onde: string): Cabecalho {
  const c = new Cursor(buf, t, onde);
  const dataGeracao = c.str("dataGeracao");
  const id = c.exigirUm([T.ctx(1), T.ctx(2), T.ctx(3)], "idEleitoral");
  const tipos = ["idProcessoEleitoral", "idPleito", "idEleicao"] as const;
  const tipo = tipos[(id.tag & 0x1f) - 1];
  if (tipo === undefined) throw new ErroBu(`${onde}.idEleitoral: alternativa inválida`);
  c.fim();
  return { dataGeracao, idEleitoral: { tipo, valor: inteiro(buf, id) } };
}

function municipioZona(buf: Uint8Array, t: Tlv, onde: string): MunicipioZona {
  const c = new Cursor(buf, t, onde);
  const municipio = c.int("municipio");
  const zona = c.int("zona");
  c.fim();
  return { municipio, zona };
}

function identificacaoSecao(buf: Uint8Array, t: Tlv, onde: string): IdentificacaoSecao {
  const c = new Cursor(buf, t, onde);
  const mz = municipioZona(buf, c.exigir(T.SEQ, "municipioZona"), `${onde}.municipioZona`);
  const local = c.int("local");
  const secao = c.int("secao");
  c.fim();
  return { municipioZona: mz, local, secao };
}

function identificacaoUrna(buf: Uint8Array, t: Tlv, onde: string): IdentificacaoUrna {
  if (t.tag === T.ctxC(0)) return { tipo: "identificacaoSecaoEleitoral", secao: identificacaoSecao(buf, t, onde) };
  if (t.tag === T.ctxC(1)) {
    const c = new Cursor(buf, t, onde);
    const mz = municipioZona(buf, c.exigir(T.SEQ, "municipioZona"), `${onde}.municipioZona`);
    c.fim();
    return { tipo: "identificacaoContingencia", municipioZona: mz };
  }
  throw new ErroBu(`${onde}: alternativa 0x${t.tag.toString(16)} de IdentificacaoUrna`);
}

function carga(buf: Uint8Array, t: Tlv, onde: string): Carga {
  const c = new Cursor(buf, t, onde);
  const numeroInternoUrna = c.int("numeroInternoUrna");
  const numeroSerieFC = c.oct("numeroSerieFC");
  const g = new Cursor(buf, c.exigir(T.SEQ, "identificadorGeradorMidia"), `${onde}.identificadorGeradorMidia`);
  const identificadorGeradorMidia = { nome: g.str("nome"), serialCertificadoTPM: g.str("serialCertificadoTPM"), serialInstalacao: g.str("serialInstalacao") };
  g.fim();
  const dataHoraCarga = c.str("dataHoraCarga");
  const codigoCarga = c.str("codigoCarga");
  c.fim();
  return { numeroInternoUrna, numeroSerieFC, identificadorGeradorMidia, dataHoraCarga, codigoCarga };
}

const TAGS_ID_URNA = [T.ctxC(0), T.ctxC(1)] as const;

function urna(buf: Uint8Array, t: Tlv, onde: string): Urna {
  const c = new Cursor(buf, t, onde);
  const tipoUrna = c.int("tipoUrna", T.ENUM);
  const versaoVotacao = c.str("versaoVotacao");
  const cr = new Cursor(buf, c.exigir(T.SEQ, "correspondenciaResultado"), `${onde}.correspondenciaResultado`);
  const identificacao = identificacaoUrna(buf, cr.exigirUm(TAGS_ID_URNA, "identificacao"), `${onde}.correspondenciaResultado.identificacao`);
  const cg = carga(buf, cr.exigir(T.SEQ, "carga"), `${onde}.correspondenciaResultado.carga`);
  cr.fim();
  const tipoArquivo = c.int("tipoArquivo", T.ENUM);
  const numeroSerieFV = c.oct("numeroSerieFV");
  const sa = c.opcionalUm([T.ctxC(0), T.ctxC(1), T.ctxC(2), T.ctxC(3)]);
  let motivoUtilizacaoSA: MotivoSA | null = null;
  if (sa !== null) {
    const alternativa = ALTERNATIVA_SA[sa.tag & 0x1f] ?? "desconhecida";
    const m = new Cursor(buf, sa, `${onde}.motivoUtilizacaoSA`);
    motivoUtilizacaoSA = { alternativa, tipoApuracao: m.int("tipoApuracao", T.ENUM), motivoApuracao: m.int("motivoApuracao", T.ENUM) };
    m.fim();
  }
  c.fim();
  return { tipoUrna, versaoVotacao, correspondenciaResultado: { identificacao, carga: cg }, tipoArquivo, numeroSerieFV, motivoUtilizacaoSA };
}

function votoVotavel(buf: Uint8Array, t: Tlv, onde: string): VotoVotavel {
  const c = new Cursor(buf, t, onde);
  const tipoVoto = c.int("tipoVoto", T.ctx(1));
  const quantidadeVotos = c.int("quantidadeVotos", T.ctx(2));
  const id = c.opcional(T.ctxC(3));
  let partido: number | null = null;
  let codigo: number | null = null;
  if (id !== null) {
    const iv = new Cursor(buf, id, `${onde}.identificacaoVotavel`);
    partido = iv.int("partido");
    codigo = iv.int("codigo");
    iv.fim();
  }
  const ordemGeracaoHash = c.int("ordemGeracaoHash");
  const hash = c.oct("hash");
  c.fim();
  return { tipoVoto, quantidadeVotos, partido, codigo, ordemGeracaoHash, hash };
}

function totalVotosCargo(buf: Uint8Array, t: Tlv, onde: string): TotalVotosCargo {
  const c = new Cursor(buf, t, onde);
  const cc = c.exigirUm([T.ctx(1), T.ctx(2)], "codigoCargo");
  const codigoCargo: CodigoCargo = {
    tipo: cc.tag === T.ctx(1) ? "cargoConstitucional" : "numeroCargoConsultaLivre",
    valor: inteiro(buf, cc),
  };
  const ordemImpressao = c.int("ordemImpressao");
  const lista = c.exigir(T.SEQ, "votosVotaveis");
  const votosVotaveis = filhos(buf, lista).map((v, i) => {
    if (v.tag !== T.SEQ) throw new ErroBu(`${onde}.votosVotaveis[${i}]: esperava SEQUENCE`);
    return votoVotavel(buf, v, `${onde}.votosVotaveis[${i}]`);
  });
  c.fim();
  return { codigoCargo, ordemImpressao, votosVotaveis };
}

function resultadoVotacao(buf: Uint8Array, t: Tlv, onde: string): ResultadoVotacao {
  const c = new Cursor(buf, t, onde);
  const tipoCargo = c.int("tipoCargo", T.ENUM);
  const qtdComparecimento = c.int("qtdComparecimento");
  const lista = c.exigir(T.SEQ, "totaisVotosCargo");
  const totaisVotosCargo = filhos(buf, lista).map((x, i) => totalVotosCargo(buf, x, `${onde}.totaisVotosCargo[${i}]`));
  c.fim();
  return { tipoCargo, qtdComparecimento, totaisVotosCargo };
}

function resultadoEleicao(buf: Uint8Array, t: Tlv, onde: string): ResultadoEleicao {
  const c = new Cursor(buf, t, onde);
  const idEleicao = c.int("idEleicao");
  const qtdEleitoresAptos = c.int("qtdEleitoresAptos");
  const qtdEleitoresAptosSecao = c.int("qtdEleitoresAptosSecao");
  const qtdEleitoresAptosTTE = c.int("qtdEleitoresAptosTTE");
  const lista = c.exigir(T.SEQ, "resultadosVotacao");
  const resultadosVotacao = filhos(buf, lista).map((x, i) => resultadoVotacao(buf, x, `${onde}.resultadosVotacao[${i}]`));
  const ultimoHashVotosVotavel = c.oct("ultimoHashVotosVotavel");
  const assinaturaUltimoHashVotosVotavel = c.oct("assinaturaUltimoHashVotosVotavel");
  c.fim();
  return {
    idEleicao, qtdEleitoresAptos, qtdEleitoresAptosSecao, qtdEleitoresAptosTTE, resultadosVotacao,
    ultimoHashVotosVotavel, assinaturaUltimoHashVotosVotavel,
  };
}

/** Decodifica o envelope genérico (camada externa do `-bu.dat`). */
export function decodificarEnvelope(buf: Uint8Array): Envelope {
  const raiz = lerTlv(buf, 0);
  if (raiz.tag !== T.SEQ) throw new ErroBu(`envelope: esperava SEQUENCE, achou 0x${raiz.tag.toString(16)}`);
  const c = new Cursor(buf, raiz, "envelope");
  const cab = cabecalho(buf, c.exigir(T.SEQ, "cabecalho"), "envelope.cabecalho");
  const fase = c.int("fase", T.ENUM);
  // urna (SEQUENCE, opcional) vem antes de identificacao (CHOICE [0]/[1]): sem ambiguidade.
  const temUrna = c.opcional(T.SEQ) !== null;
  const identificacao = identificacaoUrna(buf, c.exigirUm(TAGS_ID_URNA, "identificacao"), "envelope.identificacao");
  const tipoEnvelope = c.int("tipoEnvelope", T.ENUM);
  const cifrado = c.opcional(T.SEQ) !== null;
  const cont = c.exigir(T.OCTET, "conteudo");
  c.fim();
  if (raiz.prox !== buf.length) throw new ErroBu(`envelope: ${buf.length - raiz.prox} octetos após o fim`);
  return { cabecalho: cab, fase, temUrna, identificacao, tipoEnvelope, cifrado, conteudo: buf.subarray(cont.ini, cont.fim) };
}

/** Decodifica a EntidadeBoletimUrna (conteúdo do envelope). */
export function decodificarEntidadeBu(buf: Uint8Array): BoletimUrna {
  const raiz = lerTlv(buf, 0);
  if (raiz.tag !== T.SEQ) throw new ErroBu(`BU: esperava SEQUENCE, achou 0x${raiz.tag.toString(16)}`);
  if (raiz.prox !== buf.length) throw new ErroBu(`BU: ${buf.length - raiz.prox} octetos após o fim`);
  const c = new Cursor(buf, raiz, "bu");
  const cab = cabecalho(buf, c.exigir(T.SEQ, "cabecalho"), "bu.cabecalho");
  const fase = c.int("fase", T.ENUM);
  const u = urna(buf, c.exigir(T.SEQ, "urna"), "bu.urna");
  const idSecao = identificacaoSecao(buf, c.exigir(T.SEQ, "identificacaoSecao"), "bu.identificacaoSecao");
  const dataHoraEmissao = c.str("dataHoraEmissao");
  const dsa = c.exigirUm([T.ctxC(0), T.ctxC(1)], "dadosSecaoSA");
  let dadosSecao: DadosSecao | null = null;
  let dadosSA: DadosSA | null = null;
  if (dsa.tag === T.ctxC(0)) {
    const d = new Cursor(buf, dsa, "bu.dadosSecao");
    dadosSecao = {
      dataHoraAbertura: d.str("dataHoraAbertura"),
      dataHoraEncerramento: d.str("dataHoraEncerramento"),
      dataHoraDesligamentoVotoImpresso: null,
    };
    const desl = d.opcional(T.GENSTR);
    if (desl !== null) dadosSecao.dataHoraDesligamentoVotoImpresso = texto(buf, desl);
    d.fim();
  } else {
    const d = new Cursor(buf, dsa, "bu.dadosSA");
    const juntaApuradora = d.int("juntaApuradora");
    const turmaApuradora = d.int("turmaApuradora");
    const orig = d.opcional(T.INTEGER);
    d.fim();
    dadosSA = { juntaApuradora, turmaApuradora, numeroInternoUrnaOrigem: orig === null ? null : inteiro(buf, orig) };
  }
  const qtdEleitoresCompareceram = c.int("qtdEleitoresCompareceram");
  const det = c.opcional(T.ctxC(1));
  let detalhamentoComparecimento: BoletimUrna["detalhamentoComparecimento"] = null;
  if (det !== null) {
    const d = new Cursor(buf, det, "bu.detalhamentoComparecimento");
    detalhamentoComparecimento = {
      qtdEleitoresCompareceramSemBiometria: d.int("qtdEleitoresCompareceramSemBiometria"),
      qtdEleitoresHabilitadosPorBiometria: d.int("qtdEleitoresHabilitadosPorBiometria"),
      qtdEleitoresHabilitadosPorBiografia: d.int("qtdEleitoresHabilitadosPorBiografia"),
    };
    d.fim();
  }
  const rve = c.exigir(T.SEQ, "resultadosVotacaoPorEleicao");
  const resultadosVotacaoPorEleicao = filhos(buf, rve).map((x, i) => resultadoEleicao(buf, x, `bu.resultadosVotacaoPorEleicao[${i}]`));
  const hcc = c.exigir(T.SEQ, "historicoCodigosCarga");
  const historicoCodigosCarga = filhos(buf, hcc).map((x, i) => {
    if (x.tag !== T.GENSTR) throw new ErroBu(`bu.historicoCodigosCarga[${i}]: esperava GeneralString`);
    return texto(buf, x);
  });
  const hvi = c.opcional(T.SEQ);
  const historicoVotoImpresso =
    hvi === null
      ? null
      : filhos(buf, hvi).map((x, i) => {
          const h = new Cursor(buf, x, `bu.historicoVotoImpresso[${i}]`);
          const r = { idImpressoraVotos: h.int("idImpressoraVotos"), idRepositorioVotos: h.int("idRepositorioVotos"), dataHoraLigamento: h.str("dataHoraLigamento") };
          h.fim();
          return r;
        });
  c.fim();
  return {
    cabecalho: cab, fase, urna: u, identificacaoSecao: idSecao, dataHoraEmissao, dadosSecao, dadosSA,
    qtdEleitoresCompareceram, detalhamentoComparecimento, resultadosVotacaoPorEleicao, historicoCodigosCarga, historicoVotoImpresso,
  };
}

/** `-bu.dat` inteiro: envelope e BU. Lança ErroBu se a estrutura fugir da especificação. */
export function decodificarBu(buf: Uint8Array): { envelope: Envelope; bu: BoletimUrna } {
  const envelope = decodificarEnvelope(buf);
  if (envelope.tipoEnvelope !== 1) throw new ErroBu(`envelope: tipoEnvelope ${envelope.tipoEnvelope}, esperava 1 (BU)`);
  if (envelope.cifrado) throw new ErroBu("envelope: conteúdo cifrado (campo seguranca presente)");
  return { envelope, bu: decodificarEntidadeBu(envelope.conteudo) };
}

/** 'YYYYMMDDThhmmss' (hora local da urna) para 'YYYY-MM-DD hh:mm:ss'. */
export function dataHoraJe(s: string | null): string | null {
  if (s === null) return null;
  const m = /^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})$/.exec(s);
  return m === null ? s : `${m[1]}-${m[2]}-${m[3]} ${m[4]}:${m[5]}:${m[6]}`;
}

if (import.meta.main) {
  const arq = process.argv[2];
  if (arq === undefined) {
    console.error("uso: bun run scripts/bu-decode.ts arquivo-bu.dat");
    process.exit(2);
  }
  const { envelope, bu } = decodificarBu(new Uint8Array(await Bun.file(arq).arrayBuffer()));
  console.log(JSON.stringify({ envelope: { ...envelope, conteudo: `${envelope.conteudo.length} octetos` }, bu }, null, 1));
}
