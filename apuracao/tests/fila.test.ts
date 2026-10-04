import { describe, expect, test } from "bun:test";
import { Fila } from "../src/collector/fila.ts";
import type { Job } from "../src/types.ts";

const job = (id: number, p: Job["prioridade"], due: number, motivo: Job["motivo"] = "periodico"): Job => ({
  arquivoId: id, chave: `k${id}`, url: `u${id}`, prioridade: p, due, motivo,
});

describe("Fila", () => {
  test("ordem por prioridade entre vencidos, depois por due", () => {
    const f = new Fila();
    f.agendar(job(1, "sweep", 0));
    f.agendar(job(2, "t1", 5));
    f.agendar(job(3, "t0", 10));
    f.agendar(job(4, "final", 20));
    f.agendar(job(5, "t1", 2));
    expect(f.popDue(10)?.arquivoId).toBe(3);
    expect(f.popDue(10)?.arquivoId).toBe(5);
    expect(f.popDue(10)?.arquivoId).toBe(2);
    expect(f.popDue(10)?.arquivoId).toBe(1);
    expect(f.popDue(10)).toBeNull();
    expect(f.proximoDue()).toBe(20);
    expect(f.popDue(20)?.arquivoId).toBe(4);
    expect(f.tamanho).toBe(0);
  });

  test("job urgente com due futuro não bloqueia varredura vencida", () => {
    const f = new Fila();
    f.agendar(job(1, "final", 1000));
    f.agendar(job(2, "sweep", 0));
    expect(f.popDue(0)?.arquivoId).toBe(2);
  });

  test("coalescência: menor prioridade, menor due, motivo mais urgente", () => {
    const f = new Fila();
    f.agendar(job(7, "sweep", 100, "sweep"));
    f.agendar(job(7, "gatilho", 300, "gatilho_ab"));
    expect(f.tamanho).toBe(1);
    expect(f.obter(7)).toMatchObject({ prioridade: "gatilho", due: 100, motivo: "gatilho_ab" });
    f.agendar(job(7, "final", 500, "final"));
    expect(f.obter(7)).toMatchObject({ prioridade: "final", due: 100, motivo: "final" });
    f.agendar(job(7, "sweep", 50, "sweep"));
    expect(f.obter(7)).toMatchObject({ prioridade: "final", due: 50, motivo: "final" });
  });

  test("coalescência de job já pronto atualiza a ordem", () => {
    const f = new Fila();
    f.agendar(job(1, "sweep", 0));
    f.agendar(job(2, "probe", 0));
    expect(f.popDue(0)?.arquivoId).toBe(2);
    f.agendar(job(3, "sweep", 0));
    f.popDue(0);
    f.agendar(job(1, "sweep", 0));
    f.agendar(job(4, "probe", 1));
    expect(f.popDue(5)?.arquivoId).toBe(4);
  });

  test("tamanhoPorPrioridade e remover", () => {
    const f = new Fila();
    for (let i = 0; i < 10; i++) f.agendar(job(i, i % 2 === 0 ? "sweep" : "t0", i));
    expect(f.tamanhoPorPrioridade()).toMatchObject({ sweep: 5, t0: 5, final: 0 });
    f.remover(3);
    expect(f.tem(3)).toBe(false);
    expect(f.tamanhoPorPrioridade().t0).toBe(4);
  });

  test("heap aguenta muitos jobs e devolve em ordem", () => {
    const f = new Fila();
    const n = 5000;
    for (let i = 0; i < n; i++) f.agendar(job(i, "sweep", (i * 7919) % n));
    let ultimo = -1;
    for (let i = 0; i < n; i++) {
      const j = f.popDue(n);
      if (!j) throw new Error("vazio");
      expect(j.due).toBeGreaterThanOrEqual(ultimo);
      ultimo = j.due;
    }
    expect(f.popDue(n)).toBeNull();
  });
});
