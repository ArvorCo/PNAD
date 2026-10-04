// Heap binário mínimo indexado por id: inserção, remoção e atualização de chave em O(log n).

export class HeapIndexado<T> {
  private readonly itens: T[] = [];
  private readonly pos = new Map<number, number>();

  constructor(
    private readonly menor: (a: T, b: T) => boolean,
    private readonly idDe: (x: T) => number,
  ) {}

  get tamanho(): number {
    return this.itens.length;
  }

  tem(id: number): boolean {
    return this.pos.has(id);
  }

  obter(id: number): T | undefined {
    const i = this.pos.get(id);
    return i === undefined ? undefined : this.itens[i];
  }

  topo(): T | undefined {
    return this.itens[0];
  }

  inserir(x: T): void {
    this.itens.push(x);
    this.pos.set(this.idDe(x), this.itens.length - 1);
    this.subir(this.itens.length - 1);
  }

  /** Substitui o item de mesmo id e reordena. */
  atualizar(x: T): void {
    const i = this.pos.get(this.idDe(x));
    if (i === undefined) {
      this.inserir(x);
      return;
    }
    this.itens[i] = x;
    this.subir(i);
    this.descer(this.pos.get(this.idDe(x)) ?? i);
  }

  remover(id: number): T | undefined {
    const i = this.pos.get(id);
    if (i === undefined) return undefined;
    const alvo = this.itens[i] as T;
    const ultimo = this.itens.pop() as T;
    this.pos.delete(id);
    if (i < this.itens.length) {
      this.itens[i] = ultimo;
      this.pos.set(this.idDe(ultimo), i);
      this.subir(i);
      this.descer(this.pos.get(this.idDe(ultimo)) ?? i);
    }
    return alvo;
  }

  extrair(): T | undefined {
    const t = this.itens[0];
    if (t === undefined) return undefined;
    this.remover(this.idDe(t));
    return t;
  }

  *valores(): Generator<T> {
    yield* this.itens;
  }

  private trocar(i: number, j: number): void {
    const a = this.itens[i] as T;
    const b = this.itens[j] as T;
    this.itens[i] = b;
    this.itens[j] = a;
    this.pos.set(this.idDe(b), i);
    this.pos.set(this.idDe(a), j);
  }

  private subir(i: number): void {
    let k = i;
    while (k > 0) {
      const p = (k - 1) >> 1;
      if (!this.menor(this.itens[k] as T, this.itens[p] as T)) break;
      this.trocar(k, p);
      k = p;
    }
  }

  private descer(i: number): void {
    let k = i;
    const n = this.itens.length;
    for (;;) {
      const l = 2 * k + 1;
      const r = l + 1;
      let m = k;
      if (l < n && this.menor(this.itens[l] as T, this.itens[m] as T)) m = l;
      if (r < n && this.menor(this.itens[r] as T, this.itens[m] as T)) m = r;
      if (m === k) break;
      this.trocar(k, m);
      k = m;
    }
  }
}
