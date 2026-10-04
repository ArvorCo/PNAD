// Monitoramento -ab: diff por município, gatilhos de T2/T3, finais e municípios desconhecidos.
import { cargosDe, ELEITORADO_GRANDE, INTERVALOS_S } from "../config.ts";
import type { ItemLote } from "../db/escrita.ts";
import { itensDeAb } from "../db/itens.ts";
import { arquivoPorChave } from "../db/leitura.ts";
import type { LinhaMunicipio } from "../db/linhas.ts";
import { normalizarAb } from "../parse/normalizar.ts";
import type { AbFile } from "../parse/schemas.ts";
import { chave, keyU, urlDe } from "../tse/urls.ts";
import type { ArquivoRegistro } from "../types.ts";
import type { CtxCorpo, CtxProc, JobNovo } from "./contexto.ts";
import { evento } from "./contexto.ts";
import { estadoDeLinha } from "./estado-arquivos.ts";
import type { FileState } from "./estado-arquivos.ts";

/** Intervalo mínimo de um município: capitais e grandes proporcional a 120/300 do knob. */
export function intervaloMinMuS(ctx: CtxProc, uf: string, mun: string): number {
  const base = ctx.knobs.minIntervaloMuS;
  if (!ctx.estado.municipioGrande(uf, mun, ELEITORADO_GRANDE)) return base;
  return Math.max(30, Math.round((base * INTERVALOS_S.muMinCapital) / INTERVALOS_S.muMin));
}

function dueComMinimo(fs: FileState, agora: number, minS: number): number {
  const ultimo = fs.emVoo ? agora : fs.ultimoFetchEm;
  return ultimo === null ? agora : Math.max(agora, ultimo + minS * 1000);
}

/** Cria município placeholder + arquivos mu para cdabr ausente do cm. Grava na hora (raro). */
function criarDesconhecidos(c: CtxCorpo, ele: number, uf: string, muns: readonly string[]): FileState[] {
  const { ctx } = c;
  ctx.lote.gravar();
  const regs: ArquivoRegistro[] = [];
  for (const mun of muns) {
    for (const cargo of cargosDe(ele, uf)) {
      const k = keyU(ele, cargo, "mu", uf, mun);
      regs.push({ ...k, chave: chave(k), url: urlDe(k), tier: 2, sonda: false });
    }
  }
  const municipios: LinhaMunicipio[] = muns.map((cd) => ({ cd, uf, ibge: null, nome: null, capital: null, eleitores: null, origem: "ab" }));
  const itens: ItemLote[] = [{ k: "municipio", rows: municipios }, ...regs.map((row): ItemLote => ({ k: "arquivo", row }))];
  ctx.lote.escritor.gravarLote(itens);
  const out: FileState[] = [];
  for (const r of regs) {
    if (ctx.estado.porChave.has(r.chave)) continue;
    const a = arquivoPorChave(ctx.db, r.chave);
    if (!a) continue;
    const fs = estadoDeLinha(a);
    ctx.estado.adicionar(fs);
    out.push(fs);
  }
  return out;
}

export function processarAb(c: CtxCorpo, p: AbFile, snapRef: string): void {
  const { ctx, fs, grupo, agora } = c;
  const ele = fs.key.ele;
  if (ele === null) return;
  const anteriores = ctx.estado.abFingerprints.get(fs.id) ?? new Map<string, string>();
  const n = normalizarAb(p, anteriores);
  grupo.push(...itensDeAb(n, { ref: snapRef }));
  ctx.estado.abFingerprints.set(fs.id, ctx.estado.registrarAb(fs.id, fs.key.uf, p));
  const jobs: JobNovo[] = c.saida.jobs;

  if (fs.key.nivel === "br") {
    if (n.primeiro) return;
    for (const m of n.mudancas) {
      if (m.tpabr !== "uf") continue;
      for (const alvo of ctx.estado.daUf(ele, m.cdabr)) {
        jobs.push({ arquivoId: alvo.id, prioridade: alvo.key.tipo === "ab" ? "t1" : "t0", due: agora, motivo: "gatilho_ab" });
      }
    }
    return;
  }

  const uf = fs.key.uf;
  if (uf === null) return;
  const desconhecidos: string[] = [];
  for (const m of n.mudancas) {
    if (m.tpabr === "uf" || m.tpabr === "br") continue;
    const mun = m.cdabr;
    const mus = ctx.estado.doMunicipio(ele, uf, mun);
    if (mus.length === 0) {
      desconhecidos.push(mun);
      continue;
    }
    const zonas = ctx.estado.zonasDoMunicipio(ele, uf, mun);
    const pendentesFinal = [...mus, ...zonas].filter((x) => !x.finalAgendado);
    if (m.final && pendentesFinal.length > 0) {
      if (mus.some((x) => !x.finalAgendado)) {
        grupo.push(evento(fs, c.em, "municipio_finalizado", "info", { uf, municipio: mun, ele }, snapRef));
      }
      for (const x of pendentesFinal) {
        x.finalAgendado = true;
        jobs.push({ arquivoId: x.id, prioridade: "final", due: agora, motivo: "final" });
        grupo.push({ k: "arquivo_estado", id: x.id, row: ctx.estado.paraLinha(x) });
      }
      continue;
    }
    if (n.primeiro) continue;
    const minMu = intervaloMinMuS(ctx, uf, mun);
    for (const x of mus) jobs.push({ arquivoId: x.id, prioridade: "gatilho", due: dueComMinimo(x, agora, minMu), motivo: "gatilho_ab" });
    if (ctx.knobs.zonas === "sempre") {
      for (const z of zonas) {
        jobs.push({ arquivoId: z.id, prioridade: "gatilho", due: dueComMinimo(z, agora, INTERVALOS_S.zonaMin), motivo: "gatilho_ab" });
      }
    }
  }
  if (desconhecidos.length > 0) {
    const novos = criarDesconhecidos(c, ele, uf, desconhecidos);
    for (const mun of desconhecidos) grupo.push(evento(fs, c.em, "municipio_desconhecido", "warn", { uf, municipio: mun, ele }, snapRef));
    for (const x of novos) jobs.push({ arquivoId: x.id, prioridade: "gatilho", due: agora, motivo: "gatilho_ab" });
  }
}
