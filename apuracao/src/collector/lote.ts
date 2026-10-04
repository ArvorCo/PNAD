// Lote de escrita: junta os itens de vários jobs e grava numa transação a cada
// 200 ms ou 50 grupos. Um grupo que falha não derruba os outros.
import type { Escritor, ItemLote } from "../db/escrita.ts";
import type { Relogio } from "./relogio.ts";

type Callback = (id: number) => void;

export class Lote {
  private grupos: ItemLote[][] = [];
  private primeiroEm: number | null = null;
  private seq = 0;
  private readonly pendentes = new Map<string, Callback[]>();
  /** refs de itens ainda não gravados */
  private readonly abertos = new Set<string>();
  falhas = 0;

  constructor(
    readonly escritor: Escritor,
    private readonly relogio: Relogio,
    private readonly maxMs = 200,
    private readonly maxGrupos = 50,
    private readonly aoFalhar: (erro: unknown, grupo: readonly ItemLote[]) => void = () => undefined,
  ) {}

  /** Ref única no processo. */
  ref(prefixo: string): string {
    const r = `${prefixo}${++this.seq}`;
    this.abertos.add(r);
    return r;
  }

  /** true se a ref ainda está num lote não gravado. */
  aberto(ref: string): boolean {
    return this.abertos.has(ref);
  }

  quandoGravado(ref: string, cb: Callback): void {
    const l = this.pendentes.get(ref);
    if (l) l.push(cb);
    else this.pendentes.set(ref, [cb]);
  }

  adicionar(grupo: ItemLote[]): void {
    if (grupo.length === 0) return;
    if (this.primeiroEm === null) this.primeiroEm = this.relogio.agora();
    this.grupos.push(grupo);
  }

  get tamanho(): number {
    return this.grupos.length;
  }

  precisaGravar(agora: number = this.relogio.agora()): boolean {
    if (this.grupos.length === 0) return false;
    return this.grupos.length >= this.maxGrupos || (this.primeiroEm !== null && agora - this.primeiroEm >= this.maxMs);
  }

  /** Grava tudo. Em falha da transação única, regrava grupo a grupo. */
  gravar(): number {
    const grupos = this.grupos;
    if (grupos.length === 0) return 0;
    this.grupos = [];
    this.primeiroEm = null;
    let gravados = 0;
    try {
      const r = this.escritor.gravarLote(grupos.flat());
      this.resolver(r.ids);
      gravados = grupos.length;
    } catch {
      for (const g of grupos) {
        try {
          this.resolver(this.escritor.gravarLote(g).ids);
          gravados++;
        } catch (err) {
          this.falhas++;
          for (const it of g) if ("ref" in it && it.ref !== undefined) this.pendentes.delete(it.ref);
          this.aoFalhar(err, g);
        }
      }
    }
    for (const g of grupos) for (const it of g) if ("ref" in it && it.ref !== undefined) this.abertos.delete(it.ref);
    return gravados;
  }

  private resolver(ids: ReadonlyMap<string, number>): void {
    for (const [ref, id] of ids) {
      this.abertos.delete(ref);
      const cbs = this.pendentes.get(ref);
      if (!cbs) continue;
      this.pendentes.delete(ref);
      for (const cb of cbs) cb(id);
    }
  }
}
