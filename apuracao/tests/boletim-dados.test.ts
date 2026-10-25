// Resumo do boletim contra respostas reais da API sobre o banco de ensaio (tests/fixtures/boletim/2120 e 2130).
import { afterAll, beforeAll, describe, expect, test } from "bun:test";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { coletarDados, nomeFalado } from "../src/boletim/dados.ts";

const FIX = join(import.meta.dir, "fixtures/boletim");
let pasta = "2120";
let srv: ReturnType<typeof Bun.serve>;
let base = "";

beforeAll(() => {
  srv = Bun.serve({
    hostname: "127.0.0.1",
    port: 0,
    fetch(req) {
      const nome = new URL(req.url).pathname.replace(/^\/api\//, "").replace(/\//g, "_");
      try {
        return new Response(readFileSync(join(FIX, pasta, `${nome}.json`)), { headers: { "content-type": "application/json" } });
      } catch {
        return new Response("{}", { status: 404 });
      }
    },
  });
  base = srv.url.toString().replace(/\/$/, "");
});

afterAll(() => {
  void srv.stop(true);
});

describe("dados do boletim", () => {
  test("nomes falados dos finalistas", () => {
    expect(nomeFalado("FLAVIO BOLSONARO")).toBe("Flávio Bolsonaro");
    expect(nomeFalado("LULA")).toBe("Lula");
    expect(nomeFalado("ALAN RICK")).toBe("Alan Rick");
  });

  test("antes das 17:00 é abertura", async () => {
    pasta = "2120";
    const d = await coletarDados({ base, anterior: null, at: "2026-10-25T19:55:00.000Z" });
    expect(d.resumo.modo).toBe("abertura");
  });

  test("primeiro boletim com seções e delta contra o anterior", async () => {
    pasta = "2120";
    const a = await coletarDados({ base, anterior: null, at: "2026-10-25T21:20:00.000Z", hora: "18:20" });
    expect(a.resumo.modo).toBe("muita");
    expect(a.resumo.motivos_modo).toContain("primeiro boletim com seções totalizadas");
    expect(a.resumo.delta).toBeNull();
    const nac = a.resumo.nacional as { placar_f_x_l: { nome: string; pct_validos: number }[]; secoes_totalizadas: number };
    expect(nac.placar_f_x_l[0]?.nome).toBe("Flávio Bolsonaro");
    expect(a.base.st).toBe(nac.secoes_totalizadas);
    expect(a.linha.startsWith("18:20 · ")).toBe(true);

    pasta = "2130";
    const b = await coletarDados({ base, anterior: a.base, at: "2026-10-25T21:30:00.000Z" });
    const delta = b.resumo.delta as { secoes: number; viradas_governador: string[]; diferenca_pp_antes: number | null };
    expect(delta.secoes).toBe(b.base.st - a.base.st);
    expect(delta.secoes).toBeGreaterThan(0);
    expect(delta.diferenca_pp_antes).toBe(a.base.diferenca_pp);
    expect(delta.viradas_governador.some(v => v.startsWith("AC:"))).toBe(true);
    expect(b.resumo.modo).toBe("muita");
    const janela = b.resumo.desde_o_boletim_anterior as { para_quem: { votos: number }[]; votos_validos_que_chegaram: number };
    expect(janela.para_quem.reduce((s, c) => s + c.votos, 0)).toBe(janela.votos_validos_que_chegaram);
    const par = b.resumo.totalizacao_paralela as { rotulo_obrigatorio: string };
    expect(par.rotulo_obrigatorio).toBe("soma dos BUs recebidos, não projeção");
    expect(JSON.stringify(b.resumo)).not.toContain("—");

    // anterior com mais de 30 min não vale como base do delta
    const c = await coletarDados({ base, anterior: { ...a.base, at: "2026-10-25T20:00:00.000Z" }, at: "2026-10-25T21:30:00.000Z" });
    expect(c.resumo.delta).toBeNull();
  });
});
