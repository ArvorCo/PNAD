// Modelo da urna a partir do log da urna (`-log.jez`).
//
// O BU não tem campo de modelo (ver scripts/bu-decode.ts). Em 2026 o `-log.jez` é um ZIP
// (deflate) com `logd.dat` em ISO-8859-1, uma linha por evento, separada por tabulação:
//   data hora | tipo (INFO, ALERTA, ERRO) | número interno da urna (8 dígitos) | aplicação | descrição | código
// A urna registra o próprio modelo a cada partida de aplicação, por exemplo:
//   23/09/2026 11:21:04  INFO  02027601  SCUE  Identificação do Modelo de Urna: UE2020  6E74F85CD80F3035
// O número da terceira coluna é o mesmo `numeroInternoUrna` da carga gravada no BU, o que
// liga o modelo à urna que produziu o boletim mesmo quando o log traz mais de uma urna.
import { inflateRawSync } from "node:zlib";

export class ErroZip extends Error {
  override name = "ErroZip";
}

export interface EntradaZip {
  nome: string;
  dados: Uint8Array;
}

const u16 = (b: Uint8Array, p: number): number => (b[p] ?? 0) | ((b[p + 1] ?? 0) << 8);
const u32 = (b: Uint8Array, p: number): number => (u16(b, p) + u16(b, p + 2) * 65536) >>> 0;

/** ISO-8859-1: um caractere por octeto. */
const latin1 = (b: Uint8Array, ini: number, fim: number): string => Buffer.from(b.buffer, b.byteOffset + ini, fim - ini).toString("latin1");

/** Lê um ZIP pelo diretório central (deflate e stored; sem ZIP64). */
export function lerZip(buf: Uint8Array): EntradaZip[] {
  let eocd = -1;
  for (let p = buf.length - 22; p >= Math.max(0, buf.length - 65_557); p -= 1) {
    if (u32(buf, p) === 0x06054b50) {
      eocd = p;
      break;
    }
  }
  if (eocd < 0) throw new ErroZip("fim do diretório central não encontrado");
  const n = u16(buf, eocd + 10);
  let p = u32(buf, eocd + 16);
  const out: EntradaZip[] = [];
  for (let i = 0; i < n; i += 1) {
    if (u32(buf, p) !== 0x02014b50) throw new ErroZip(`entrada ${i} do diretório central inválida`);
    const metodo = u16(buf, p + 10);
    const comp = u32(buf, p + 20);
    const tam = u32(buf, p + 24);
    const nNome = u16(buf, p + 28);
    const nExtra = u16(buf, p + 30);
    const nCom = u16(buf, p + 32);
    const local = u32(buf, p + 42);
    const nome = latin1(buf, p + 46, p + 46 + nNome);
    if (comp === 0xffffffff || tam === 0xffffffff || local === 0xffffffff) throw new ErroZip("ZIP64 não suportado");
    if (u32(buf, local) !== 0x04034b50) throw new ErroZip(`cabeçalho local de ${nome} inválido`);
    const ini = local + 30 + u16(buf, local + 26) + u16(buf, local + 28);
    if (ini + comp > buf.length) throw new ErroZip(`${nome} truncado`);
    const bruto = buf.subarray(ini, ini + comp);
    let dados: Uint8Array;
    if (metodo === 0) dados = bruto;
    else if (metodo === 8) dados = new Uint8Array(inflateRawSync(bruto));
    else throw new ErroZip(`${nome}: método de compressão ${metodo}`);
    if (dados.length !== tam) throw new ErroZip(`${nome}: ${dados.length} octetos, esperava ${tam}`);
    out.push({ nome, dados });
    p += 46 + nNome + nExtra + nCom;
  }
  return out;
}

export interface UrnaNoLog {
  /** número interno com 8 dígitos, como no log */
  id: string;
  modelos: string[];
  linhas: number;
}

export interface ResumoLog {
  arquivos: string[];
  linhas: number;
  urnas: UrnaNoLog[];
}

const RE_MODELO = /^[^\t\n]*\t[^\t\n]*\t(\d{8})\t[^\t\n]*\t[^\t\n]*Modelo de Urna:\s*(UE\d{4})/gm;
const RE_URNA = /^[^\t\n]*\t[^\t\n]*\t(\d{8})\t/gm;

/** Urnas e modelos declarados em um ou mais arquivos de log já descomprimidos. */
export function resumirLog(entradas: readonly EntradaZip[]): ResumoLog {
  const urnas = new Map<string, { modelos: Set<string>; linhas: number }>();
  let total = 0;
  const pegar = (id: string): { modelos: Set<string>; linhas: number } => {
    let u = urnas.get(id);
    if (u === undefined) {
      u = { modelos: new Set(), linhas: 0 };
      urnas.set(id, u);
    }
    return u;
  };
  for (const e of entradas) {
    const t = latin1(e.dados, 0, e.dados.length);
    for (const m of t.matchAll(RE_URNA)) {
      pegar(m[1] ?? "").linhas += 1;
      total += 1;
    }
    for (const m of t.matchAll(RE_MODELO)) pegar(m[1] ?? "").modelos.add(m[2] ?? "");
  }
  return {
    arquivos: entradas.map((e) => e.nome),
    linhas: total,
    urnas: [...urnas.entries()].map(([id, u]) => ({ id, modelos: [...u.modelos].sort(), linhas: u.linhas })),
  };
}

export type FonteModelo =
  /** linha de modelo da mesma urna que gravou o BU */
  | "log_mesma_urna"
  /** a urna do BU não declara modelo no log, mas todas as que declaram têm o mesmo */
  | "log_modelo_unico"
  /** a urna do BU declara mais de um modelo (não deveria acontecer) */
  | "log_ambiguo"
  | "log_sem_modelo";

/** Modelo da urna que gravou o BU (`numeroInternoUrna` da carga). */
export function modeloDaUrna(resumo: ResumoLog, numeroInternoUrna: number): { modelo: string | null; fonte: FonteModelo } {
  const id = String(numeroInternoUrna).padStart(8, "0");
  const propria = resumo.urnas.find((u) => u.id === id);
  if (propria !== undefined && propria.modelos.length === 1) return { modelo: propria.modelos[0] ?? null, fonte: "log_mesma_urna" };
  if (propria !== undefined && propria.modelos.length > 1) return { modelo: propria.modelos.join("/"), fonte: "log_ambiguo" };
  const todos = new Set(resumo.urnas.flatMap((u) => u.modelos));
  if (todos.size === 1) return { modelo: [...todos][0] ?? null, fonte: "log_modelo_unico" };
  return { modelo: null, fonte: "log_sem_modelo" };
}
