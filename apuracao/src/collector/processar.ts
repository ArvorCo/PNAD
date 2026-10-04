// Pipeline por resposta do TSE: linha em fetch sempre; corpo novo vira blob + snapshot +
// normalização; erros viram backoff; 403/429 viram pausa global. Sem I/O de rede.
import type { ClasseFetch, FetchResult, Job } from "../types.ts";
import type { CtxCorpo, CtxProc, SaidaProc } from "./contexto.ts";
import { evento, linhaFetch } from "./contexto.ts";
import type { FileState } from "./estado-arquivos.ts";
import { processarCorpo } from "./processar-corpo.ts";
import { intervaloResondagemS, isoDe } from "./relogio.ts";

export const BACKOFF_BASE_S = 5;
export const BACKOFF_MAX_S = 300;

/** Backoff exponencial 5 s × 2^(n−1), teto 300 s, ±20% de jitter. */
export function backoffMs(n: number, aleatorio: () => number = Math.random): number {
  const s = Math.min(BACKOFF_MAX_S, BACKOFF_BASE_S * 2 ** Math.max(0, n - 1));
  return Math.round(s * 1000 * (0.8 + 0.4 * aleatorio()));
}

const ERROS: ReadonlySet<ClasseFetch> = new Set(["erro_servidor", "timeout", "erro_rede", "corpo_invalido"]);

/** Garante que o snapshot anterior do arquivo já tem id (refs não cruzam lotes). */
function resolverAnterior(ctx: CtxProc, fs: FileState): void {
  const a = fs.ultimoSnapshotId;
  if (a === null || typeof a === "number") return;
  if (ctx.lote.aberto(a.ref)) ctx.lote.gravar();
  const b = fs.ultimoSnapshotId;
  if (b !== null && typeof b !== "number") fs.ultimoSnapshotId = null;
}

/**
 * Processa uma resposta. `inicio` = relógio do agendador no despacho.
 * Devolve a classe final (ok pode virar igual), jobs derivados e sinais de pausa/retry.
 */
export function processar(ctx: CtxProc, job: Job, fs: FileState, r: FetchResult, inicio: number): SaidaProc {
  resolverAnterior(ctx, fs);
  const agora = ctx.relogio.agora();
  const em = isoDe(agora);
  let classe = r.classe;
  if (classe === "ok" && r.bodySha256 !== null && (r.bodySha256 === fs.sha256 || r.bodySha256 === fs.shaRegressivo)) {
    classe = "igual";
  }
  const fetchRef = ctx.lote.ref("f");
  const grupo: CtxCorpo["grupo"] = [{ k: "fetch", ref: fetchRef, row: linhaFetch(job, fs, r, classe) }];
  const saida: SaidaProc = { classe, mudou: false, jobs: [], pausar: null, retryEm: null };
  ctx.estado.aplicarResultado(fs, r, classe, inicio);

  const reativar = (): void => {
    if (fs.ativo) return;
    fs.ativo = true;
    grupo.push(evento(fs, em, "arquivo_apareceu", "info", { chave: fs.chave }));
  };

  switch (classe) {
    case "ok":
      reativar();
      processarCorpo({ ctx, job, fs, r, fetchRef, em, agora, grupo, saida });
      break;
    case "igual":
    case "nao_modificado":
      reativar();
      break;
    case "nao_existe":
      if (fs.ativo) {
        fs.ativo = false;
        if (fs.tier < 2) grupo.push(evento(fs, em, "arquivo_inexistente", fs.sonda ? "info" : "warn", { chave: fs.chave, url: fs.url }));
      }
      if (fs.tier >= 2) saida.jobs.push({ arquivoId: fs.id, prioridade: "probe", due: agora + intervaloResondagemS(agora) * 1000, motivo: "probe" });
      break;
    case "negado":
    case "limite":
      saida.pausar = { retryAfterS: r.retryAfterS };
      break;
    default:
      if (ERROS.has(classe)) {
        fs.errosSeguidos++;
        fs.backoffAte = agora + backoffMs(fs.errosSeguidos, ctx.aleatorio);
        saida.retryEm = fs.backoffAte;
        if (classe === "corpo_invalido" && r.body !== null) {
          grupo.push(...blobItens(r.body, em));
        }
        if (fs.errosSeguidos === 3 || fs.errosSeguidos === 10) {
          grupo.push(
            evento(fs, em, "erros_seguidos", fs.errosSeguidos >= 10 ? "error" : "warn", {
              n: fs.errosSeguidos, classe, erro: r.erro, http_status: r.httpStatus, backoff_ate: isoDe(fs.backoffAte),
            }),
          );
        }
      }
  }
  grupo.push({ k: "arquivo_estado", id: fs.id, row: ctx.estado.paraLinha(fs) });
  ctx.lote.adicionar(grupo);
  return saida;
}

function blobItens(body: Uint8Array<ArrayBuffer>, em: string): CtxCorpo["grupo"] {
  const sha = new Bun.CryptoHasher("sha256").update(body).digest("hex");
  return [{ k: "blob", sha256: sha, bytes: body.byteLength, gz: Bun.gzipSync(body, { level: 6 }), criado_em: em }];
}
