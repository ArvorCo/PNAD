// Respostas JSON, erros e leitura de parâmetros de consulta.

export class ErroHttp extends Error {
  constructor(
    readonly status: 400 | 404 | 503,
    mensagem: string,
  ) {
    super(mensagem);
  }
}

const NO_STORE = "no-store";

export function json(dados: unknown, status = 200): Response {
  return new Response(JSON.stringify(dados), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": NO_STORE },
  });
}

export function erro(status: number, mensagem: string): Response {
  return json({ erro: mensagem }, status);
}

/** ISO qualquer (com deslocamento) → ISO UTC com milissegundos, o formato gravado no banco. */
export function normalizarIso(v: string): string | null {
  const t = Date.parse(v);
  return Number.isFinite(t) ? new Date(t).toISOString() : null;
}

export class Params {
  constructor(private readonly q: URLSearchParams) {}

  texto(nome: string): string | undefined {
    const v = this.q.get(nome);
    return v === null || v.trim() === "" ? undefined : v.trim();
  }

  exigirTexto(nome: string): string {
    const v = this.texto(nome);
    if (v === undefined) throw new ErroHttp(400, `parâmetro ${nome} obrigatório`);
    return v;
  }

  int(nome: string): number | undefined {
    const v = this.texto(nome);
    if (v === undefined) return undefined;
    if (!/^-?\d+$/.test(v)) throw new ErroHttp(400, `parâmetro ${nome} precisa ser inteiro`);
    return Number.parseInt(v, 10);
  }

  exigirInt(nome: string): number {
    const v = this.int(nome);
    if (v === undefined) throw new ErroHttp(400, `parâmetro ${nome} obrigatório`);
    return v;
  }

  /** Inteiro limitado ao intervalo [min, max], com padrão. */
  limite(nome: string, padrao: number, max: number, min = 1): number {
    const v = this.int(nome) ?? padrao;
    return Math.min(Math.max(v, min), max);
  }

  iso(nome: string): string | undefined {
    const v = this.texto(nome);
    if (v === undefined) return undefined;
    const iso = normalizarIso(v);
    if (iso === null) throw new ErroHttp(400, `parâmetro ${nome} não é data ISO válida`);
    return iso;
  }

  /** `at` do replay: "até este instante". */
  at(): string | undefined {
    return this.iso("at");
  }
}
