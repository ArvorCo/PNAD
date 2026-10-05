// Cliente HTTP da coleta de seções: teto de requisições por segundo (balde de fichas do
// coletor), pausa global escalonada em 403/429 e nova tentativa com espera exponencial em
// erro de rede, tempo esgotado e 5xx. 404 volta na hora: é resposta, não falha.
import { Limitador } from "../../src/collector/limitador.ts";
import type { Relogio } from "../../src/collector/relogio.ts";
import { relogioReal } from "../../src/collector/relogio.ts";
import { retryAfterS } from "../../src/collector/http.ts";
import { UA_PADRAO } from "../../src/config.ts";

export interface Resposta {
  status: number | null;
  corpo: Uint8Array<ArrayBuffer> | null;
  erro: string | null;
  /** requisições feitas, contando as repetições */
  requisicoes: number;
}

export interface OpcoesCliente {
  /** teto de requisições por segundo */
  rps: number;
  /** fichas acumuláveis; o pico em 1 s fica em rps + rajada */
  rajada?: number;
  ua?: string;
  timeoutMs?: number;
  /** tentativas para erro de rede, tempo esgotado e 5xx */
  maxTentativas?: number;
  /** pausas por 403/429 toleradas numa mesma URL antes de desistir */
  maxPausas?: number;
  esperaBaseMs?: number;
  relogio?: Relogio;
  fetchImpl?: (url: string, init: RequestInit) => Promise<Response>;
  dormir?: (ms: number) => Promise<void>;
  log?: (o: Record<string, unknown>) => void;
}

export type ClasseResposta = "ok" | "nao_existe" | "limite" | "erro_servidor" | "erro_rede" | "outro";

export function classe(status: number | null): ClasseResposta {
  if (status === null) return "erro_rede";
  if (status === 200) return "ok";
  if (status === 404) return "nao_existe";
  if (status === 403 || status === 429) return "limite";
  if (status >= 500) return "erro_servidor";
  return "outro";
}

export class ClienteTse {
  readonly limitador: Limitador;
  /** contagem por classe desde o início */
  readonly contagem: Record<ClasseResposta, number> = { ok: 0, nao_existe: 0, limite: 0, erro_servidor: 0, erro_rede: 0, outro: 0 };
  bytes = 0;
  private readonly o: Required<Omit<OpcoesCliente, "log" | "fetchImpl">> & Pick<OpcoesCliente, "log" | "fetchImpl">;

  constructor(opts: OpcoesCliente) {
    this.o = {
      rajada: 4, ua: UA_PADRAO, timeoutMs: 30_000, maxTentativas: 7, maxPausas: 30, esperaBaseMs: 1_000,
      relogio: relogioReal, dormir: (ms) => Bun.sleep(ms), ...opts,
    };
    const rajada = Math.max(1, this.o.rajada);
    this.limitador = new Limitador(this.o.relogio, { global: { taxa: this.o.rps, rajada }, sweep: { taxa: this.o.rps, rajada } });
  }

  private async ficha(): Promise<void> {
    while (!this.limitador.tentar(false)) await this.o.dormir(Math.max(2, this.limitador.esperaMs(false)));
  }

  private async uma(url: string): Promise<{ status: number | null; corpo: Uint8Array<ArrayBuffer> | null; erro: string | null; retryAfter: number | null }> {
    const f = this.o.fetchImpl ?? ((u: string, i: RequestInit) => fetch(u, i));
    try {
      const res = await f(url, {
        headers: { "User-Agent": this.o.ua, "Accept-Encoding": "gzip", Accept: "*/*" },
        signal: AbortSignal.timeout(this.o.timeoutMs),
      });
      const corpo = new Uint8Array(await res.arrayBuffer());
      this.bytes += corpo.byteLength;
      return {
        status: res.status,
        corpo: res.status === 200 ? corpo : null,
        erro: res.status === 200 ? null : `HTTP ${res.status}`,
        retryAfter: retryAfterS(res.headers.get("retry-after"), this.o.relogio.agora()),
      };
    } catch (err) {
      const nome = err instanceof Error ? err.name : "";
      const msg = err instanceof Error ? err.message : String(err);
      return { status: null, corpo: null, erro: `${nome}: ${msg}`.slice(0, 300), retryAfter: null };
    }
  }

  /** GET com teto de taxa e repetição. Nunca lança. */
  async obter(url: string): Promise<Resposta> {
    let requisicoes = 0;
    let falhas = 0;
    let pausas = 0;
    for (;;) {
      await this.ficha();
      const r = await this.uma(url);
      requisicoes += 1;
      const c = classe(r.status);
      this.contagem[c] += 1;
      if (c === "ok" || c === "nao_existe" || c === "outro") return { status: r.status, corpo: r.corpo, erro: r.erro, requisicoes };
      if (c === "limite") {
        pausas += 1;
        const ate = this.limitador.pausar(r.retryAfter);
        this.o.log?.({ t: "pausa", url, status: r.status, ate: new Date(ate).toISOString(), pausas });
        if (pausas >= this.o.maxPausas) return { status: r.status, corpo: null, erro: r.erro, requisicoes };
        continue;
      }
      falhas += 1;
      if (falhas >= this.o.maxTentativas) return { status: r.status, corpo: null, erro: r.erro, requisicoes };
      await this.o.dormir(Math.min(30_000, this.o.esperaBaseMs * 2 ** (falhas - 1)));
    }
  }
}
