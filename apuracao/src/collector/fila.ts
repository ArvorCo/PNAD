// Fila do agendador: um job por arquivo (coalescência), ordem (prioridade, due).
// Dois heaps: espera (por due) e prontos (por prioridade, due). Assim um job de
// prioridade alta com due futuro nunca bloqueia um job de prioridade baixa já vencido.
import { PRIORIDADE } from "../config.ts";
import type { Job, MotivoFetch, Prioridade } from "../types.ts";
import { HeapIndexado } from "./heap.ts";

/** Menor = mais urgente. */
export const URGENCIA_MOTIVO: Readonly<Record<MotivoFetch, number>> = {
  final: 0,
  gatilho_ab: 1,
  retry: 2,
  periodico: 3,
  probe: 4,
  sweep: 5,
};

const pri = (j: Job): number => PRIORIDADE[j.prioridade];

export class Fila {
  private readonly espera = new HeapIndexado<Job>((a, b) => a.due < b.due || (a.due === b.due && pri(a) < pri(b)), (j) => j.arquivoId);
  private readonly prontos = new HeapIndexado<Job>((a, b) => pri(a) < pri(b) || (pri(a) === pri(b) && a.due < b.due), (j) => j.arquivoId);

  get tamanho(): number {
    return this.espera.tamanho + this.prontos.tamanho;
  }

  tem(arquivoId: number): boolean {
    return this.espera.tem(arquivoId) || this.prontos.tem(arquivoId);
  }

  obter(arquivoId: number): Job | undefined {
    return this.prontos.obter(arquivoId) ?? this.espera.obter(arquivoId);
  }

  /** Insere ou coalesce: menor prioridade numérica, menor due, motivo mais urgente. */
  agendar(job: Job): void {
    const atual = this.obter(job.arquivoId);
    if (atual === undefined) {
      this.espera.inserir({ ...job });
      return;
    }
    const novo: Job = {
      ...atual,
      prioridade: PRIORIDADE[job.prioridade] < PRIORIDADE[atual.prioridade] ? job.prioridade : atual.prioridade,
      due: Math.min(job.due, atual.due),
      motivo: URGENCIA_MOTIVO[job.motivo] < URGENCIA_MOTIVO[atual.motivo] ? job.motivo : atual.motivo,
    };
    if (this.prontos.tem(job.arquivoId)) this.prontos.atualizar(novo);
    else this.espera.atualizar(novo);
  }

  remover(arquivoId: number): Job | undefined {
    return this.prontos.remover(arquivoId) ?? this.espera.remover(arquivoId);
  }

  /** O job vencido mais urgente, ou null. */
  popDue(agora: number): Job | null {
    for (let t = this.espera.topo(); t !== undefined && t.due <= agora; t = this.espera.topo()) {
      this.espera.extrair();
      this.prontos.inserir(t);
    }
    return this.prontos.extrair() ?? null;
  }

  /** Quando há trabalho: um job pronto já venceu, então basta o seu due; senão o topo da espera. */
  proximoDue(): number | null {
    const p = this.prontos.topo();
    const e = this.espera.topo();
    if (p === undefined) return e === undefined ? null : e.due;
    return e === undefined ? p.due : Math.min(p.due, e.due);
  }

  tamanhoPorPrioridade(): Record<Prioridade, number> {
    const out: Record<Prioridade, number> = { final: 0, t0: 0, t1: 0, gatilho: 0, probe: 0, sweep: 0 };
    for (const j of this.espera.valores()) out[j.prioridade]++;
    for (const j of this.prontos.valores()) out[j.prioridade]++;
    return out;
  }
}
