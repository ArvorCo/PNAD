// Leitura das views públicas da totalização paralela no Supabase (projeto PNAD) pelo PostgREST,
// só com a chave publicável. URL e chave são as de ../scripts/totalizacao_comum.py e
// ../docs/assets/totalizacao/config.js: públicas por desenho (RLS nega tudo ao papel anônimo
// fora das views). APURACAO_PARALELA_URL e APURACAO_PARALELA_CHAVE trocam o destino (testes).

export const SUPABASE_URL = "https://brvjvizqbyfamtxogvqf.supabase.co";
export const CHAVE_PUBLICAVEL = "sb_publishable_OdrY6f2C-CdRzkorgyaudQ_taVWSIKw";

export type ParametrosPg = ReadonlyArray<readonly [string, string]>;

export interface OpcoesSupabase {
  url?: string | null;
  chave?: string | null;
  timeoutMs?: number;
  pagina?: number;
  fetchImpl?: (url: string, init: RequestInit) => Promise<Response>;
}

export class ErroSupabase extends Error {
  override name = "ErroSupabase";
}

export class ClienteSupabase {
  readonly url: string;
  private readonly chave: string;
  private readonly timeoutMs: number;
  readonly pagina: number;
  private readonly f: (url: string, init: RequestInit) => Promise<Response>;
  requisicoes = 0;

  constructor(o: OpcoesSupabase = {}) {
    this.url = (o.url ?? SUPABASE_URL).replace(/\/$/, "");
    this.chave = o.chave ?? CHAVE_PUBLICAVEL;
    this.timeoutMs = o.timeoutMs ?? 30_000;
    this.pagina = o.pagina ?? 1000;
    this.f = o.fetchImpl ?? ((u, i) => fetch(u, i));
  }

  /** Uma requisição; `total` vem do Content-Range quando o servidor contou (Prefer: count=exact). */
  private async pedir<T>(view: string, params: ParametrosPg, contar = false): Promise<{ linhas: T[]; total: number | null }> {
    const q = new URLSearchParams();
    for (const [k, v] of params) q.append(k, v);
    const qs = q.toString();
    const headers: Record<string, string> = { apikey: this.chave, Authorization: `Bearer ${this.chave}`, Accept: "application/json" };
    if (contar) headers.Prefer = "count=exact";
    let res: Response;
    try {
      this.requisicoes += 1;
      res = await this.f(`${this.url}/rest/v1/${view}${qs === "" ? "" : `?${qs}`}`, { headers, signal: AbortSignal.timeout(this.timeoutMs) });
    } catch (err) {
      throw new ErroSupabase(`${view}: ${err instanceof Error ? `${err.name}: ${err.message}` : String(err)}`.slice(0, 300));
    }
    const texto = await res.text();
    if (res.status !== 200 && res.status !== 206) throw new ErroSupabase(`${view}: HTTP ${res.status} ${texto.slice(0, 200)}`);
    let dados: unknown;
    try {
      dados = JSON.parse(texto);
    } catch {
      throw new ErroSupabase(`${view}: resposta não é JSON`);
    }
    if (!Array.isArray(dados)) throw new ErroSupabase(`${view}: resposta não é lista`);
    const faixa = res.headers.get("content-range") ?? "";
    const m = /\/(\d+)$/.exec(faixa);
    return { linhas: dados as T[], total: m ? Number(m[1]) : null };
  }

  /**
   * View inteira (pequena ou filtrada), por offset e limit. Com `contar` (padrão), pede
   * `count=exact` e para pelo total do Content-Range ou, sem total, na primeira página vazia: o
   * teto de linhas do servidor pode ser menor que a página pedida. Sem `contar` (views pequenas e
   * caras, como a cobertura: a contagem repetiria a consulta inteira no Postgres), para na primeira
   * página menor que a pedida; vale só para views bem abaixo do teto do servidor (1.000 linhas).
   * `params` precisa de `order` para a paginação ser estável.
   */
  async tudo<T>(view: string, params: ParametrosPg = [], contar = true): Promise<T[]> {
    const out: T[] = [];
    for (;;) {
      const { linhas, total } = await this.pedir<T>(view, [...params, ["offset", String(out.length)], ["limit", String(this.pagina)]], contar);
      out.push(...linhas);
      if (linhas.length === 0 || (total !== null && out.length >= total)) return out;
      if (!contar && linhas.length < this.pagina) return out;
    }
  }

  /** Só a contagem de linhas (`count=exact`, uma linha trazida); null se o servidor não contou. */
  async contar(view: string, params: ParametrosPg = []): Promise<number | null> {
    const { total } = await this.pedir<unknown>(view, [...params, ["limit", "1"]], true);
    return total;
  }

  /** Linhas com id maior que `depois`, em ordem de id, por chave (sem deslocamento de página). */
  async depoisDe<T extends { id: number }>(view: string, depois: number, params: ParametrosPg = []): Promise<T[]> {
    const out: T[] = [];
    let cursor = depois;
    for (;;) {
      const { linhas: lote } = await this.pedir<T>(view, [...params, ["id", `gt.${cursor}`], ["order", "id"], ["limit", String(this.pagina)]]);
      const ult = lote.at(-1);
      if (ult === undefined) return out;
      out.push(...lote);
      cursor = ult.id;
    }
  }
}
