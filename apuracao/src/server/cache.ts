// Cache curto por chave: vale enquanto o max(snapshot.id) não mudar ou por `ttlMs`,
// o que vier primeiro a favor do reaproveitamento (limita recomputação a 1 a cada ttl).

interface Entrada<T> {
  maxId: number;
  em: number;
  valor: T;
}

export class CacheCurto<T> {
  private readonly m = new Map<string, Entrada<T>>();

  constructor(
    private readonly ttlMs: number,
    private readonly tamanho = 64,
    private readonly relogio: () => number = Date.now,
  ) {}

  obter(chave: string, maxId: number, calcular: () => T): T {
    const agora = this.relogio();
    const e = this.m.get(chave);
    if (e && (e.maxId === maxId || agora - e.em < this.ttlMs)) return e.valor;
    const valor = calcular();
    this.m.delete(chave);
    this.m.set(chave, { maxId, em: agora, valor });
    if (this.m.size > this.tamanho) {
      const primeira = this.m.keys().next().value;
      if (primeira !== undefined) this.m.delete(primeira);
    }
    return valor;
  }

  limpar(): void {
    this.m.clear();
  }
}
