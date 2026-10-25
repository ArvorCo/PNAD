// Boletim falado do 2º turno: relógio, roteiro (guardas e enxugar), estado combinado e gerador.
import { describe, expect, test } from "bun:test";
import { existsSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import type { SaidaDados } from "../src/boletim/dados.ts";
import { gravarJson, lerIndice, listar } from "../src/boletim/estado.ts";
import type { Controle, Indice, ItemIndice } from "../src/boletim/estado.ts";
import { GeradorBoletim } from "../src/boletim/gerador.ts";
import type { Dependencias } from "../src/boletim/gerador.ts";
import { idLivre, inicioDoRelogio, proximoCiclo } from "../src/boletim/relogio.ts";
import { contarPalavras, escreverRoteiro, guardar, montarPrompt, TAMANHOS } from "../src/boletim/roteiro.ts";

const T1710 = Date.parse("2026-10-25T20:10:00.000Z");

describe("relógio", () => {
  test("17:10 de Brasília no dia de hoje e ISO completo", () => {
    expect(inicioDoRelogio(undefined, new Date("2026-10-25T16:00:00Z"))).toBe(T1710);
    expect(inicioDoRelogio("17:10", new Date("2026-10-25T23:30:00Z"))).toBe(T1710);
    expect(inicioDoRelogio("2026-10-25T17:00:00-03:00", new Date())).toBe(Date.parse("2026-10-25T20:00:00Z"));
    expect(() => inicioDoRelogio("amanhã", new Date())).toThrow();
  });
  test("ciclos alinhados aos múltiplos do intervalo", () => {
    expect(proximoCiclo(T1710, 600, T1710 - 3600_000)).toBe(T1710);
    expect(proximoCiclo(T1710, 600, T1710)).toBe(T1710);
    expect(proximoCiclo(T1710, 600, T1710 + 1)).toBe(T1710 + 600_000);
    expect(proximoCiclo(T1710, 600, T1710 + 4 * 60_000)).toBe(T1710 + 600_000);
    expect(proximoCiclo(T1710, 600, T1710 + 600_000)).toBe(T1710 + 600_000);
  });
  test("id livre com sufixo", () => {
    const usados = new Set(["1720", "1720-2"]);
    expect(idLivre("1730", x => usados.has(x))).toBe("1730");
    expect(idLivre("1720", x => usados.has(x))).toBe("1720-3");
  });
});

describe("roteiro", () => {
  test("conta palavras faladas, sem as tags", () => {
    expect(contarPalavras("[calm] Dezessete e vinte. [pause] O TSE totalizou, ... dez por cento.")).toBe(9);
  });
  test("guardas: travessão, palavra proibida e markdown", () => {
    const g = guardar("## Título\n**Placar** \u2014 Flávio na frente.\n\nNão há fraude nenhuma. O quadro se mantém.");
    expect(g.texto).not.toContain("\u2014");
    expect(g.texto.toLowerCase()).not.toContain("fraude");
    expect(g.texto).toContain("O quadro se mantém.");
    expect(g.texto).not.toContain("#");
    expect(g.texto).not.toContain("**");
    expect(g.avisos.length).toBe(2);
  });
  test("enxuga acima do teto e mantém o longo se o enxuto vier curto", async () => {
    const longo = Array.from({ length: 700 }, () => "palavra").join(" ");
    const curto = Array.from({ length: 540 }, () => "palavra").join(" ");
    const r = await escreverRoteiro("p", "muita", async p => (p === "p" ? longo : curto));
    expect(r.enxugado).toBe(true);
    expect(r.palavras_bruto).toBe(700);
    expect(r.palavras).toBe(540);
    const r2 = await escreverRoteiro("p", "muita", async p => (p === "p" ? longo : "curto demais"));
    expect(r2.enxugado).toBe(false);
    expect(r2.palavras).toBe(700);
  });
  test("tenta de novo uma vez quando o claude falha", async () => {
    let n = 0;
    const r = await escreverRoteiro("p", "abertura", async () => {
      n += 1;
      if (n === 1) throw new Error("falhou");
      return Array.from({ length: 180 }, () => "palavra").join(" ");
    });
    expect(n).toBe(2);
    expect(r.palavras).toBe(180);
  });
  test("prompt traz guia, tamanho do modo, regras e o anterior", () => {
    const p = montarPrompt({ hora_brt: "17:20", modo: "pouca" }, "{\"x\":1}", "Boletim antigo.");
    expect(p).toContain("boletim das 17:20");
    expect(p).toContain(`${TAMANHOS.pouca.min} a ${TAMANHOS.pouca.max} palavras`);
    expect(p).toContain("soma dos BUs recebidos, não projeção");
    expect(p).toContain("intervalo sem versão nova publicada");
    expect(p).toContain("Boletim antigo.");
    expect(p).toContain("Roteiro ElevenLabs dos boletins");
    expect(p).not.toContain("\u2014");
  });
});

const item = (id: string, estado: ItemIndice["estado"], criado: string): ItemIndice => ({
  id, hora: `${id.slice(0, 2)}:${id.slice(2, 4)}`, estado, etapa: null, origem: "relogio", criado_em: criado, atualizado_em: criado,
  modo: "muita", palavras: 500, duracao_s: 200, resumo: null, erro: null,
});

describe("estado combinado", () => {
  test("descartado > no ar > gerando/erro > tocado > pronto, mais recente primeiro", () => {
    const ind: Indice = { atualizado_em: "", itens: [item("1710", "pronto", "a"), item("1720", "pronto", "b"), item("1730", "erro", "c"), item("1740", "pronto", "d"), item("1750", "gerando", "e")] };
    const c: Controle = { atualizado_em: "", no_ar: { id: "1740", desde: "x", duracao_s: 200 }, tocados: { "1710": "t" }, descartados: { "1720": "t" } };
    const l = listar(ind, c);
    expect(l.map(i => [i.id, i.estado])).toEqual([["1750", "gerando"], ["1740", "no_ar"], ["1730", "erro"], ["1710", "tocado"]]);
    expect(listar(ind, c, true).find(i => i.id === "1720")?.estado).toBe("descartado");
  });
});

function saidaFalsa(modo: SaidaDados["resumo"]["modo"], st: number): SaidaDados {
  return {
    resumo: { hora_brt: "17:20", agora_iso: "2026-10-25T20:20:00.000Z", relogio_min: 20, modo, motivos_modo: [] },
    base: { at: "2026-10-25T20:20:00.000Z", st, ts: 100, pst: st, vv: 10, votos: { a: 5, b: 5 }, diferenca_pp: 0, diferenca_votos: 0, lideres_uf: {}, ufs_fechadas: [], pausa_nacional: false, pausas_nacionais_n: 0, ufs_em_pausa: [], divergentes: 0, lideres_gov: {} },
    linha: `17:20 · ${st}% das seções`,
  };
}

function deps(dir: string, agora: { t: number }, sobre: Partial<Dependencias> = {}): Dependencias & { prompts: string[]; anteriores: (number | null)[] } {
  const prompts: string[] = [];
  const anteriores: (number | null)[] = [];
  return {
    prompts,
    anteriores,
    dados: async o => {
      anteriores.push(o.anterior?.st ?? null);
      return saidaFalsa("muita", 10 + anteriores.length);
    },
    roteiro: async p => {
      prompts.push(p);
      return { texto: "[calm] Texto do boletim.", palavras: 3, palavras_bruto: 3, enxugado: false, avisos: [], ms_roteiro: 1, ms_enxugar: 0 };
    },
    audio: async txt => {
      const mp3 = txt.replace(/\.txt$/, ".mp3");
      writeFileSync(mp3, new Uint8Array(2000));
      return { mp3, duracao_s: 12.5, log: "ok", ms: 1 };
    },
    agora: () => agora.t,
    log: () => undefined,
    ...sobre,
  };
}

describe("gerador", () => {
  test("geração completa grava os arquivos, usa a base do anterior e nunca roda duas ao mesmo tempo", async () => {
    const dir = mkdtempSync(join(tmpdir(), "bol-"));
    const agora = { t: T1710 + 5_000 };
    const d = deps(dir, agora);
    const g = new GeradorBoletim({ dir, api: "http://x", relogioLigado: true, intervaloS: 600, inicioMs: T1710 }, d);
    const p1 = g.gerar("manual", T1710);
    expect(await g.gerar("manual", T1710)).toBeNull();
    expect(await p1).toBe("1710");
    for (const ext of ["dados.json", "txt", "mp3", "meta.json", "prompt.txt"]) expect(existsSync(join(dir, `1710.${ext}`))).toBe(true);
    const ind = lerIndice(dir);
    expect(ind.itens[0]?.estado).toBe("pronto");
    expect(ind.itens[0]?.duracao_s).toBe(12.5);
    const meta = JSON.parse(readFileSync(join(dir, "1710.meta.json"), "utf8")) as { tempos: Record<string, number> };
    expect(Object.keys(meta.tempos)).toEqual(expect.arrayContaining(["dados_ms", "roteiro_ms", "audio_ms", "total_ms"]));
    // segunda geração no mesmo minuto: id com sufixo, base e texto do anterior no prompt
    expect(await g.gerar("manual", T1710)).toBe("1710-2");
    expect(d.anteriores).toEqual([null, 11]);
    expect(d.prompts[1]).toContain("Texto do boletim.");
  });

  test("relógio: gera no ciclo, pula ciclo ocupado e não gera com o relógio desligado", async () => {
    const dir = mkdtempSync(join(tmpdir(), "bol-"));
    const agora = { t: T1710 - 60_000 };
    let liberar: () => void = () => undefined;
    const trava = new Promise<void>(r => {
      liberar = r;
    });
    const d = deps(dir, agora, {
      roteiro: async () => {
        await trava;
        return { texto: "Texto.", palavras: 1, palavras_bruto: 1, enxugado: false, avisos: [], ms_roteiro: 1, ms_enxugar: 0 };
      },
    });
    const g = new GeradorBoletim({ dir, api: "http://x", relogioLigado: true, intervaloS: 600, inicioMs: T1710 }, d);
    g.tick();
    expect(g.ocupado).toBe(false);
    agora.t = T1710 + 500;
    g.tick();
    expect(g.ocupado).toBe(true);
    agora.t = T1710 + 600_500;
    g.tick(); // ciclo de 17:20 cai com 17:10 ainda gerando: pulado
    liberar();
    await Bun.sleep(20);
    expect(g.ocupado).toBe(false);
    expect(lerIndice(dir).itens.map(i => i.id)).toEqual(["1710"]);
    const g2 = new GeradorBoletim({ dir: mkdtempSync(join(tmpdir(), "bol-")), api: "http://x", relogioLigado: false, intervaloS: 600, inicioMs: T1710 }, deps(dir, agora));
    g2.tick();
    expect(g2.ocupado).toBe(false);
  });

  test("pedido manual pelo arquivo e erro vira estado erro; geração interrompida vira erro na partida", async () => {
    const dir = mkdtempSync(join(tmpdir(), "bol-"));
    const agora = { t: T1710 - 3600_000 };
    const d = deps(dir, agora, { audio: async () => Promise.reject(new Error("sem crédito")) });
    const g = new GeradorBoletim({ dir, api: "http://x", relogioLigado: true, intervaloS: 600, inicioMs: T1710 }, d);
    gravarJson(join(dir, "pedido.json"), { em: "agora" });
    g.tick();
    expect(existsSync(join(dir, "pedido.json"))).toBe(false);
    await Bun.sleep(20);
    const it = lerIndice(dir).itens[0];
    expect(it?.estado).toBe("erro");
    expect(it?.erro).toContain("sem crédito");
    gravarJson(join(dir, "indice.json"), { atualizado_em: "", itens: [{ ...item("1600", "gerando", "z") }] });
    new GeradorBoletim({ dir, api: "http://x", relogioLigado: false, intervaloS: 600, inicioMs: T1710 }, d);
    expect(lerIndice(dir).itens[0]?.estado).toBe("erro");
  });
});
