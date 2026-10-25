// Boletim falado no servidor: lista e controle (no ar, parar, descartar, fim), pedido de geração ao
// processo gerador, mp3 com Range e eventos `boletim` para o SSE. O servidor só escreve
// controle.json e pedido.json em data/boletins-2t/; a geração é do processo `bun run boletim`.
import { existsSync, readFileSync, statSync } from "node:fs";
import { caminho, gravarJson, lerControle, lerGerador, lerIndice, lerJson, listar, RE_ID } from "../boletim/estado.ts";
import type { Controle, ItemBoletim } from "../boletim/estado.ts";
import { erro, json } from "./http.ts";

export interface EventoBoletim {
  kind: "gerando" | "pronto" | "erro" | "no_ar" | "fim" | "descartado";
  id: string;
  hora?: string;
  desde?: string;
  duracao_s?: number | null;
  motivo?: string;
}

type Ouvinte = (e: EventoBoletim) => void;

const RE_ITEM = /^\/api\/boletins\/([0-9-]+)(?:\/(tocar|descartar|fim))?$/;
const RE_MP3 = /^\/boletins\/([0-9-]+)\.mp3$/;
const LOOPBACK = new Set(["127.0.0.1", "::1", "::ffff:127.0.0.1", "localhost", "[::1]"]);
/** Folga depois do fim previsto: sem o `fim` do player, o servidor encerra sozinho. */
const FOLGA_FIM_MS = 30_000;
/** Batimento do gerador mais velho que isso: gerador fora do ar. */
const GERADOR_VIVO_MS = 10_000;

export class Boletins {
  private ouvintes = new Set<Ouvinte>();
  private timer: ReturnType<typeof setInterval> | null = null;
  private estados: Map<string, string> | null = null;
  private mtime = -1;

  constructor(
    readonly dir: string,
    private readonly agora: () => number = () => Date.now(),
  ) {}

  assinar(fn: Ouvinte): () => void {
    this.ouvintes.add(fn);
    return () => this.ouvintes.delete(fn);
  }

  private emitir(e: EventoBoletim): void {
    for (const fn of this.ouvintes) {
      try {
        fn(e);
      } catch {
        // um ouvinte quebrado não derruba os outros
      }
    }
  }

  iniciar(intervaloMs = 1000): void {
    if (this.timer) return;
    this.observar();
    this.timer = setInterval(() => this.observar(), intervaloMs);
  }

  parar(): void {
    if (this.timer) clearInterval(this.timer);
    this.timer = null;
  }

  /** Mudanças do gerador (indice.json) viram eventos; no ar sem `fim` encerra pelo tempo. */
  observar(): void {
    try {
      const path = caminho(this.dir, "indice.json");
      const mt = existsSync(path) ? statSync(path).mtimeMs : -1;
      if (mt !== this.mtime) {
        this.mtime = mt;
        const ind = lerIndice(this.dir);
        const novo = new Map(ind.itens.map(i => [i.id, i.estado]));
        if (this.estados) {
          for (const i of ind.itens) {
            const antes = this.estados.get(i.id);
            if (antes === i.estado) continue;
            if (i.estado === "gerando" && antes === undefined) this.emitir({ kind: "gerando", id: i.id, hora: i.hora });
            if (i.estado === "pronto" || i.estado === "erro") this.emitir({ kind: i.estado, id: i.id, hora: i.hora });
          }
        }
        this.estados = novo;
      }
      const c = lerControle(this.dir);
      if (c.no_ar) {
        const fimPrevisto = Date.parse(c.no_ar.desde) + (c.no_ar.duracao_s ?? 600) * 1000 + FOLGA_FIM_MS;
        if (this.agora() > fimPrevisto) this.encerrar(c, "tempo");
      }
    } catch {
      // arquivo sendo regravado: tenta no próximo ciclo
    }
  }

  private gravarControle(c: Controle): void {
    c.atualizado_em = new Date(this.agora()).toISOString();
    gravarJson(caminho(this.dir, "controle.json"), c);
  }

  private encerrar(c: Controle, motivo: string): string | null {
    if (!c.no_ar) return null;
    const id = c.no_ar.id;
    c.tocados[id] = new Date(this.agora()).toISOString();
    c.no_ar = null;
    this.gravarControle(c);
    this.emitir({ kind: "fim", id, motivo });
    return id;
  }

  private item(id: string): ItemBoletim | null {
    return listar(lerIndice(this.dir), lerControle(this.dir), true).find(i => i.id === id) ?? null;
  }

  private gerador(): Record<string, unknown> {
    const g = lerGerador(this.dir);
    const vivo = g !== null && this.agora() - Date.parse(g.batimento_em) < GERADOR_VIVO_MS;
    return { vivo, ...(g ?? {}) };
  }

  lista(todos: boolean): Record<string, unknown> {
    const c = lerControle(this.dir);
    const itens = listar(lerIndice(this.dir), c, todos);
    const g = this.gerador();
    const noAr = c.no_ar
      ? { ...c.no_ar, hora: itens.find(i => i.id === c.no_ar?.id)?.hora ?? null, decorrido_s: Math.round((this.agora() - Date.parse(c.no_ar.desde)) / 100) / 10 }
      : null;
    return { agora: new Date(this.agora()).toISOString(), gerador: g, no_ar: noAr, itens };
  }

  /** Rotas /api/boletins* e /boletins/*.mp3; null quando o caminho não é do boletim. */
  responder(req: Request, url: URL, ip: string | null): Response | null {
    const p = url.pathname;
    const mp3 = RE_MP3.exec(p);
    if (mp3) return this.servirMp3(req, mp3[1] ?? "");
    if (p !== "/api/boletins" && !p.startsWith("/api/boletins/")) return null;
    try {
      if (req.method === "GET" || req.method === "HEAD") return this.get(p, url);
      if (req.method === "POST") {
        const negado = this.recusarPost(req, ip);
        if (negado) return negado;
        return this.post(p);
      }
      return erro(405, "método não permitido");
    } catch (e) {
      return erro(500, e instanceof Error ? e.message : String(e));
    }
  }

  private get(p: string, url: URL): Response {
    if (p === "/api/boletins") return json(this.lista(url.searchParams.get("todos") === "1"));
    const m = RE_ITEM.exec(p);
    if (!m || m[2] || !RE_ID.test(m[1] ?? "")) return erro(404, `rota desconhecida: ${p}`);
    const id = m[1] ?? "";
    const it = this.item(id);
    if (!it) return erro(404, `boletim ${id} não existe`);
    let texto: string | null = null;
    try {
      texto = readFileSync(caminho(this.dir, `${id}.txt`), "utf8");
    } catch {
      texto = null;
    }
    return json({ item: it, texto, meta: lerJson(caminho(this.dir, `${id}.meta.json`)), mp3: existsSync(caminho(this.dir, `${id}.mp3`)) ? `/boletins/${id}.mp3` : null });
  }

  /** POST só de 127.0.0.1, com o cabeçalho da casa e, se houver Origin, de origem local. */
  private recusarPost(req: Request, ip: string | null): Response | null {
    if (ip === null || !LOOPBACK.has(ip)) return erro(403, "controle do boletim só a partir de 127.0.0.1");
    if (req.headers.get("x-apuracao") !== "boletim") return erro(403, "cabeçalho x-apuracao: boletim obrigatório");
    const origem = req.headers.get("origin");
    if (origem && origem !== "null") {
      try {
        if (!LOOPBACK.has(new URL(origem).hostname)) return erro(403, "origem não local");
      } catch {
        return erro(403, "origem inválida");
      }
    }
    return null;
  }

  private post(p: string): Response {
    if (p === "/api/boletins/gerar") {
      const g = this.gerador();
      if (!g.vivo) return erro(503, "gerador do boletim fora do ar (scripts/start-boletim.sh)");
      if (g.gerando) return erro(409, `geração ${String(g.gerando)} em andamento`);
      const em = new Date(this.agora()).toISOString();
      gravarJson(caminho(this.dir, "pedido.json"), { em });
      return json({ ok: true, pedido_em: em }, 202);
    }
    if (p === "/api/boletins/parar") {
      const id = this.encerrar(lerControle(this.dir), "parado");
      return json({ ok: true, parado: id });
    }
    const m = RE_ITEM.exec(p);
    const id = m?.[1] ?? "";
    const acao = m?.[2];
    if (!m || !acao || !RE_ID.test(id)) return erro(404, `rota desconhecida: ${p}`);
    const it = this.item(id);
    if (!it) return erro(404, `boletim ${id} não existe`);
    const c = lerControle(this.dir);
    const agora = new Date(this.agora()).toISOString();
    if (acao === "tocar") {
      if (!["pronto", "tocado", "no_ar"].includes(it.estado)) return erro(409, `boletim ${id} está ${it.estado}`);
      if (!existsSync(caminho(this.dir, `${id}.mp3`))) return erro(409, `boletim ${id} sem áudio`);
      if (c.no_ar && c.no_ar.id !== id) {
        c.tocados[c.no_ar.id] = agora;
        this.emitir({ kind: "fim", id: c.no_ar.id, motivo: "substituido" });
      }
      c.no_ar = { id, desde: agora, duracao_s: it.duracao_s };
      this.gravarControle(c);
      this.emitir({ kind: "no_ar", id, hora: it.hora, desde: agora, duracao_s: it.duracao_s });
      return json({ ok: true, no_ar: c.no_ar });
    }
    if (acao === "descartar") {
      if (c.no_ar?.id === id) this.encerrar(c, "descartado");
      const c2 = lerControle(this.dir);
      c2.descartados[id] = agora;
      this.gravarControle(c2);
      this.emitir({ kind: "descartado", id });
      return json({ ok: true, descartado: id });
    }
    // fim: o player avisa que o áudio terminou; só vale para o que está no ar.
    if (c.no_ar?.id !== id) return json({ ok: true, efeito: false });
    this.encerrar(c, "terminou");
    return json({ ok: true, efeito: true });
  }

  private servirMp3(req: Request, id: string): Response {
    if (!RE_ID.test(id)) return erro(404, "não encontrado");
    const path = caminho(this.dir, `${id}.mp3`);
    if (!existsSync(path)) return erro(404, `áudio ${id} não existe`);
    const arq = Bun.file(path);
    const tam = arq.size;
    const base = { "content-type": "audio/mpeg", "accept-ranges": "bytes", "cache-control": "no-cache" };
    const range = req.headers.get("range");
    const m = range ? /^bytes=(\d*)-(\d*)$/.exec(range.trim()) : null;
    if (range && !m) return new Response(null, { status: 416, headers: { ...base, "content-range": `bytes */${tam}` } });
    if (m) {
      let ini: number;
      let fim: number;
      if (m[1] === "" && m[2] !== "") {
        ini = Math.max(0, tam - Number(m[2]));
        fim = tam - 1;
      } else {
        ini = Number(m[1] ?? 0);
        fim = m[2] ? Math.min(Number(m[2]), tam - 1) : tam - 1;
      }
      if (!Number.isFinite(ini) || ini >= tam || ini > fim) return new Response(null, { status: 416, headers: { ...base, "content-range": `bytes */${tam}` } });
      return new Response(req.method === "HEAD" ? null : arq.slice(ini, fim + 1), {
        status: 206,
        headers: { ...base, "content-range": `bytes ${ini}-${fim}/${tam}`, "content-length": String(fim - ini + 1) },
      });
    }
    return new Response(req.method === "HEAD" ? null : arq, { headers: { ...base, "content-length": String(tam) } });
  }
}
