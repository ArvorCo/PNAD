// Corpo novo (sha diferente): parse, drift, blob, snapshot e normalização por tipo.
import { comprimir, itensDeCm, itensDeE, itensDeEleC } from "../db/itens.ts";
import { detectarDrift } from "../parse/drift.ts";
import { metaDe, normalizarCm, normalizarE, normalizarEleC } from "../parse/normalizar.ts";
import { parseCorpo } from "../parse/schemas.ts";
import type { CtxCorpo } from "./contexto.ts";
import { evento } from "./contexto.ts";
import { processarAb } from "./processar-ab.ts";
import { processarU, totaisRegressivo } from "./processar-u.ts";

/** Detecções de drift por tipo:nivel:cargo por execução (strict zod custa caro em arquivo grande). */
export const DRIFT_AMOSTRAS = 20;

function drift(c: CtxCorpo, json: unknown, snapRef: string | null): void {
  const { ctx, fs } = c;
  const g = `${fs.key.tipo}:${fs.key.nivel ?? ""}:${fs.key.cargo ?? ""}`;
  const n = ctx.driftContagem.get(g) ?? 0;
  if (n >= DRIFT_AMOSTRAS) return;
  ctx.driftContagem.set(g, n + 1);
  const d = detectarDrift(fs.key.tipo, json);
  const novo = (p: string): boolean => {
    const k = `${fs.key.tipo}${p}`;
    if (ctx.driftVisto.has(k)) return false;
    ctx.driftVisto.add(k);
    return true;
  };
  const desconhecidos = d.desconhecidos.filter(novo);
  const divergentes = d.divergentes.filter(novo);
  if (desconhecidos.length + divergentes.length > 0) {
    c.grupo.push(evento(fs, c.em, "schema_drift", "warn", { tipo: fs.key.tipo, desconhecidos, divergentes }, snapRef));
  }
}

/**
 * Cópia mais velha que a versão atual do arquivo (CDN entregando arquivo antigo). A ordem é a
 * hora de geração do TSE (dg/hg); o idg só desempata versões sem hora ou com a mesma hora.
 * O idg não acompanha a geração: no 1º turno, versões de presidente br/UF geradas depois da atual
 * chegaram com idg menor e eram descartadas como regressivas (contagem e efeito no replay da noite
 * em ../analysis/apuracao_2t_2026/demonstracao_1t.md).
 */
export function versaoRegressiva(nova: { idg: number | null; gerado_em: string | null }, atual: { idg: number | null; geradoEm: string | null }): boolean {
  if (nova.gerado_em !== null && atual.geradoEm !== null && nova.gerado_em !== atual.geradoEm) return nova.gerado_em < atual.geradoEm;
  return nova.idg !== null && atual.idg !== null && nova.idg < atual.idg;
}

export function processarCorpo(c: CtxCorpo): void {
  const { ctx, fs, r, grupo, saida } = c;
  const body = r.body;
  const sha = r.bodySha256;
  if (body === null || sha === null) return;
  const { gz, bytes } = comprimir(body);
  grupo.push({ k: "blob", sha256: sha, bytes, gz, criado_em: c.em });

  const p = parseCorpo(fs.key.tipo, body);
  if (!p.ok) {
    fs.sha256 = sha;
    grupo.push(evento(fs, c.em, "parse_error", "warn", { erro: p.erro, sha256: sha, bytes }));
    if (p.json !== undefined) drift(c, p.json, null);
    return;
  }
  const meta = metaDe(p.parsed.data);
  const regressivo = versaoRegressiva(meta, fs);
  const snapRef = ctx.lote.ref("s");
  grupo.push({
    k: "snapshot", ref: snapRef,
    row: {
      ...meta, arquivo_id: fs.id, fetch_id: { ref: c.fetchRef }, sha256: sha, capturado_em: c.em,
      regressivo: regressivo ? 1 : 0, anterior_id: fs.ultimoSnapshotId,
    },
  });
  saida.mudou = true;
  drift(c, p.json, snapRef);

  if (regressivo) {
    fs.shaRegressivo = sha;
    grupo.push(
      evento(fs, c.em, "idg_regressivo", "warn", {
        idg_anterior: fs.idg, idg: meta.idg, gerado_em_anterior: fs.geradoEm, gerado_em: meta.gerado_em,
      }, snapRef),
    );
    if (p.parsed.tipo === "u") grupo.push(...totaisRegressivo(p.parsed.data, fs, snapRef));
    return;
  }

  const primeiro = fs.ultimoSnapshotId === null;
  fs.sha256 = sha;
  fs.idg = meta.idg ?? fs.idg;
  fs.geradoEm = meta.gerado_em ?? fs.geradoEm;
  fs.nMudancas++;
  fs.ultimoSnapshotId = { ref: snapRef };
  ctx.lote.quandoGravado(snapRef, (id) => {
    const atual = fs.ultimoSnapshotId;
    if (atual !== null && typeof atual !== "number" && atual.ref === snapRef) fs.ultimoSnapshotId = id;
  });
  if (fs.sonda && primeiro) grupo.push(evento(fs, c.em, "e_file_appeared", "info", { chave: fs.chave, url: fs.url }, snapRef));

  switch (p.parsed.tipo) {
    case "u":
      processarU(c, p.parsed.data, snapRef, primeiro);
      break;
    case "ab":
      processarAb(c, p.parsed.data, snapRef);
      break;
    case "e":
      grupo.push(...itensDeE(normalizarE(p.parsed.data), { ref: snapRef }));
      break;
    case "ele-c":
      grupo.push(...itensDeEleC(normalizarEleC(p.parsed.data, ctx.pleito)));
      break;
    case "cm": {
      const n = normalizarCm(p.parsed.data);
      for (const m of n.municipios) if (m.capital === 1) ctx.estado.capitais.add(m.cd);
      grupo.push(...itensDeCm(n));
      break;
    }
  }
}
