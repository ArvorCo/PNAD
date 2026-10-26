// Decodificador do Registro Digital do Voto (RDV, `-rdv.dat`) do TSE, sem dependência externa.
//
// Especificação: `rdv.asn1` (ModuloRegistroDigitalVoto) do pacote oficial "Formato dos arquivos
// de BU, RDV e assinatura digital" de 2026 (data/originals/tse_formato_bu_rdv_2026/, SHA-256 em
// fonte.json), copiada em scripts/secoes/rdv.asn1. BER com IMPLICIT TAGS; ao contrário do BU, o
// arquivo não vem num envelope: a raiz já é a EntidadeResultadoRDV {cabecalho, urna, rdv}.
//
// O que o RDV é, pela própria especificação: os votos ficam guardados POR ELEIÇÃO e POR CARGO
// (presidente na eleição federal, governador na estadual), cada cargo numa lista própria, e cada
// lista vem ORDENADA por tipoVoto e digitação "para salvaguardar o sigilo" (README do pacote,
// p. 7). Não há registro por eleitor: a escolha de presidente e a de governador de uma mesma
// pessoa não estão ligadas em lugar nenhum do arquivo, e a posição na lista não é a ordem de
// votação. O que o RDV acrescenta ao BU é a digitação dos votos nulos e os tipos de voto
// após suspensão e por repetição.

import { Cursor, ErroBu, T, cabecalho, filhos, identificacaoSecao, inteiro, lerTlv, texto, urna } from "./bu-decode.ts";
import type { Cabecalho, IdentificacaoSecao, Urna } from "./bu-decode.ts";

/** TipoVoto do RDV (numeração diferente da do BU). */
export const TIPO_VOTO_RDV: Readonly<Record<number, string>> = {
  1: "legenda",
  2: "nominal",
  3: "branco",
  4: "nulo",
  5: "brancoAposSuspensao",
  6: "nuloAposSuspensao",
  7: "nuloPorRepeticao",
  8: "nuloCargoSemCandidato",
  9: "nuloAposSuspensaoCargoSemCandidato",
};

const NUMERIC_STRING = 0x12;

/** Contagem de votos de um cargo por (tipo, digitação). */
export interface ContagemVoto {
  tipo: number;
  /** como digitado pelo eleitor; "" quando o tipo não tem digitação (branco e afins) */
  digitacao: string;
  votos: number;
}

export interface CargoRdv {
  idEleicao: number;
  /** código constitucional (1 a 13) ou número livre de consulta (25 a 99) */
  cargo: number;
  quantidadeEscolhas: number;
  /** votos na lista do cargo (um por escolha registrada) */
  nVotos: number;
  /** a lista respeita a ordem (tipoVoto, digitação) que a especificação exige no VOTA e no RED */
  ordenado: boolean;
  contagem: ContagemVoto[];
}

export interface Rdv {
  cabecalho: Cabecalho;
  urna: Urna;
  pleito: number;
  fase: number;
  identificacao: IdentificacaoSecao;
  historicoCodigosCarga: string[];
  /** "vota" (urna e RED) ou "sa" (Sistema de Apuração) */
  origem: "vota" | "sa";
  cargos: CargoRdv[];
}

function compararChave(ta: number, da: string, tb: number, db: string): number {
  if (ta !== tb) return ta - tb;
  return da < db ? -1 : da > db ? 1 : 0;
}

function votosCargo(buf: Uint8Array, t: ReturnType<typeof lerTlv>, idEleicao: number, onde: string): CargoRdv {
  const c = new Cursor(buf, t, onde);
  const id = c.exigirUm([T.ctx(1), T.ctx(2)], "idCargo");
  const cargo = inteiro(buf, id);
  const quantidadeEscolhas = c.int("quantidadeEscolhas");
  const lista = c.exigir(T.SEQ, "votos");
  c.fim();
  const m = new Map<string, ContagemVoto>();
  let nVotos = 0;
  let ordenado = true;
  let antT = -1;
  let antD = "";
  for (const v of filhos(buf, lista)) {
    if (v.tag !== T.SEQ) throw new ErroBu(`${onde}.votos[${nVotos}]: esperava SEQUENCE`);
    const vc = new Cursor(buf, v, `${onde}.votos[${nVotos}]`);
    const tipo = vc.int("tipoVoto", T.ENUM);
    const dg = vc.opcional(NUMERIC_STRING);
    vc.fim();
    const digitacao = dg === null ? "" : texto(buf, dg);
    if (nVotos > 0 && compararChave(antT, antD, tipo, digitacao) > 0) ordenado = false;
    antT = tipo;
    antD = digitacao;
    nVotos += 1;
    const k = `${tipo}|${digitacao}`;
    const x = m.get(k);
    if (x === undefined) m.set(k, { tipo, digitacao, votos: 1 });
    else x.votos += 1;
  }
  const contagem = [...m.values()].sort((a, b) => compararChave(a.tipo, a.digitacao, b.tipo, b.digitacao));
  return { idEleicao, cargo, quantidadeEscolhas, nVotos, ordenado, contagem };
}

/** Decodifica um `-rdv.dat`. Lança ErroBu se a estrutura fugir da especificação. */
export function decodificarRdv(buf: Uint8Array): Rdv {
  const raiz = lerTlv(buf, 0);
  if (raiz.tag !== T.SEQ) throw new ErroBu(`RDV: esperava SEQUENCE, achou 0x${raiz.tag.toString(16)}`);
  if (raiz.prox !== buf.length) throw new ErroBu(`RDV: ${buf.length - raiz.prox} octetos após o fim`);
  const c = new Cursor(buf, raiz, "rdv");
  const cab = cabecalho(buf, c.exigir(T.SEQ, "cabecalho"), "rdv.cabecalho");
  const u = urna(buf, c.exigir(T.SEQ, "urna"), "rdv.urna");
  const r = new Cursor(buf, c.exigir(T.SEQ, "rdv"), "rdv.rdv");
  c.fim();
  const pleito = r.int("pleito");
  const fase = r.int("fase", T.ENUM);
  const ident = identificacaoSecao(buf, r.exigir(T.SEQ, "identificacao"), "rdv.rdv.identificacao");
  const hcc = r.exigir(T.SEQ, "historicoCodigosCarga");
  const historicoCodigosCarga = filhos(buf, hcc).map((x, i) => {
    if (x.tag !== T.GENSTR) throw new ErroBu(`rdv.historicoCodigosCarga[${i}]: esperava GeneralString`);
    return texto(buf, x);
  });
  const el = r.exigirUm([T.ctxC(1), T.ctxC(2)], "eleicoes");
  r.fim();
  const origem = el.tag === T.ctxC(1) ? "vota" : "sa";
  const cargos: CargoRdv[] = [];
  filhos(buf, el).forEach((e, i) => {
    const onde = `rdv.eleicoes[${i}]`;
    if (e.tag !== T.SEQ) throw new ErroBu(`${onde}: esperava SEQUENCE`);
    const ec = new Cursor(buf, e, onde);
    const idEleicao = ec.int("idEleicao");
    if (origem === "sa") {
      ec.int("tipoCedulaSA", T.ENUM);
      ec.int("origemVotosSA", T.ENUM);
    }
    const vcs = ec.exigir(T.SEQ, "votosCargos");
    ec.fim();
    filhos(buf, vcs).forEach((vc, j) => {
      if (vc.tag !== T.SEQ) throw new ErroBu(`${onde}.votosCargos[${j}]: esperava SEQUENCE`);
      cargos.push(votosCargo(buf, vc, idEleicao, `${onde}.votosCargos[${j}]`));
    });
  });
  return { cabecalho: cab, urna: u, pleito, fase, identificacao: ident, historicoCodigosCarga, origem, cargos };
}

/**
 * Tipo e número no vocabulário do BU (voto_secao): 1 nominal, 2 branco, 3 nulo, 4 legenda,
 * 5 cargo sem candidato. Brancos e nulos após suspensão e nulo por repetição somam no branco
 * e no nulo do BU, que não os distingue.
 */
export function paraBu(c: ContagemVoto): { tipo: number; numero: number } {
  const n = c.digitacao === "" ? 0 : Number.parseInt(c.digitacao, 10);
  switch (c.tipo) {
    case 1:
      return { tipo: 4, numero: n };
    case 2:
      return { tipo: 1, numero: n };
    case 3:
    case 5:
      return { tipo: 2, numero: 0 };
    case 8:
    case 9:
      return { tipo: 5, numero: 0 };
    default:
      return { tipo: 3, numero: 0 };
  }
}

export interface LinhaVotoBu {
  cargo: number;
  tipo: number;
  numero: number;
  votos: number;
}

export interface Conferencia {
  confere: boolean;
  /** até 20 diferenças, na forma `cargo:tipo:numero rdv=x bu=y` */
  divergencias: string[];
}

/**
 * Compara as contagens do RDV com as linhas de voto_secao do BU da mesma seção. Cargo sem
 * candidato (5) e nulo (3) são fundidos dos dois lados, porque a urna e o BU podem classificar
 * a digitação inexistente de um ou de outro modo.
 */
export function conferirComBu(cargos: readonly CargoRdv[], bu: readonly LinhaVotoBu[]): Conferencia {
  const norm = (tipo: number): number => (tipo === 5 ? 3 : tipo);
  const rdv = new Map<string, number>();
  for (const c of cargos) {
    for (const v of c.contagem) {
      const b = paraBu(v);
      const k = `${c.cargo}:${norm(b.tipo)}:${b.numero}`;
      rdv.set(k, (rdv.get(k) ?? 0) + v.votos);
    }
  }
  const cargosRdv = new Set(cargos.map((c) => c.cargo));
  const lado = new Map<string, number>();
  for (const l of bu) {
    if (!cargosRdv.has(l.cargo)) continue;
    const k = `${l.cargo}:${norm(l.tipo)}:${norm(l.tipo) === 3 || l.tipo === 2 ? 0 : l.numero}`;
    lado.set(k, (lado.get(k) ?? 0) + l.votos);
  }
  const divergencias: string[] = [];
  for (const k of new Set([...rdv.keys(), ...lado.keys()])) {
    const a = rdv.get(k) ?? 0;
    const b = lado.get(k) ?? 0;
    if (a !== b) divergencias.push(`${k} rdv=${a} bu=${b}`);
  }
  // cargo sem nenhum voto não gera linha em voto_secao: só é ausência se o RDV tem votos nele
  const cargosBu = new Set(bu.map((l) => l.cargo));
  for (const c of cargos) if (c.nVotos > 0 && !cargosBu.has(c.cargo)) divergencias.unshift(`cargo ${c.cargo} ausente do BU`);
  return { confere: divergencias.length === 0, divergencias: divergencias.slice(0, 20) };
}
