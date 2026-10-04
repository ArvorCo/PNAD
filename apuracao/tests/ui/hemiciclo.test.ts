import { describe, expect, test } from "bun:test";
import type { Assento } from "../../src/ui/components/hemiciclo.ts";
import {
  ALTURA,
  assentosPorArco,
  composicao,
  LARGURA,
  ordenarAssentos,
  posicoesHemiciclo,
  RAIO_ASSENTO,
} from "../../src/ui/components/hemiciclo.ts";

const a = (tipo: Assento["tipo"], campo: Assento["campo"], uf: string, pst = 0): Assento => ({ tipo, campo, uf, pst, nome: uf });

describe("geometria do hemiciclo", () => {
  test("81 assentos em quatro arcos, como no hemiciclo.py", () => {
    expect(assentosPorArco()).toEqual([14, 18, 22, 27]);
    expect(posicoesHemiciclo()).toHaveLength(81);
  });

  test("cabe em 1152 × 594 e vai da esquerda para a direita", () => {
    expect(LARGURA).toBeCloseTo(1152, 6);
    expect(ALTURA).toBeCloseTo(594, 6);
    const p = posicoesHemiciclo();
    for (const q of p) {
      expect(q.x - RAIO_ASSENTO).toBeGreaterThanOrEqual(0);
      expect(q.x + RAIO_ASSENTO).toBeLessThanOrEqual(LARGURA + 1e-9);
      expect(q.y - RAIO_ASSENTO).toBeGreaterThanOrEqual(0);
      expect(q.y + RAIO_ASSENTO).toBeLessThanOrEqual(ALTURA + 1e-9);
    }
    const primeiro = p[0];
    const ultimo = p[80];
    expect(primeiro && ultimo && primeiro.x < ultimo.x).toBe(true);
    // Os quatro primeiros são a ponta esquerda de cada arco, do menor raio ao maior.
    expect(p.slice(0, 4).map(q => Math.round(q.y))).toEqual([569, 569, 569, 569]);
  });

  test("assentos não se sobrepõem", () => {
    const p = posicoesHemiciclo();
    let menor = Infinity;
    for (let i = 0; i < p.length; i++) {
      for (let j = i + 1; j < p.length; j++) {
        const pi = p[i];
        const pj = p[j];
        if (pi && pj) menor = Math.min(menor, Math.hypot(pi.x - pj.x, pi.y - pj.y));
      }
    }
    expect(menor).toBeGreaterThan(2 * RAIO_ASSENTO - 2);
  });
});

describe("ordem e composição", () => {
  test("campo da esquerda para a direita, contorno antes do cheio, aguardando no fim", () => {
    const ordem = ordenarAssentos([
      a("lider", "direita", "SP", 40),
      a("aguardando", "indefinido", "AC"),
      a("continua", "direita", "RJ"),
      a("lider", "esquerda", "BA", 30),
      a("lider", "direita", "PR", 80),
      a("eleito", "direita", "SC", 100),
      a("lider", "indefinido", "AP", 10),
    ]);
    expect(ordem.map(x => x.uf)).toEqual(["BA", "RJ", "SC", "PR", "SP", "AP", "AC"]);
  });

  test("composição por campo separa os que continuam e conta as vagas aguardando", () => {
    const c = composicao([
      a("continua", "esquerda", "BA"),
      a("lider", "esquerda", "BA", 20),
      a("lider", "direita", "SP", 20),
      a("aguardando", "indefinido", "AC"),
      a("aguardando", "indefinido", "AC"),
    ]);
    expect(c).toEqual([
      { campo: "esquerda", n: 2, continuam: 1 },
      { campo: "direita", n: 1, continuam: 0 },
      { campo: "aguardando", n: 2, continuam: 0 },
    ]);
  });
});
