// Exportador da página pública: rota que falha reaproveita o arquivo da pasta `--anterior` (o
// worktree de publicação, último retrato publicado), nunca o que estiver na própria saída (na main
// local, um retrato antigo restaurado pelo git), e entra em `pendentes`.
import { afterAll, describe, expect, test } from "bun:test";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const RAIZ = resolve(import.meta.dir, "..");
const dirs: string[] = [];
afterAll(() => {
  for (const d of dirs) rmSync(d, { recursive: true, force: true });
});

function pasta(): string {
  const d = mkdtempSync(join(tmpdir(), "exportar-"));
  dirs.push(d);
  return d;
}

async function exportar(saida: string, anterior: string, falhar: (caminho: string) => boolean): Promise<Record<string, unknown>> {
  const srv = Bun.serve({
    port: 0,
    fetch(req) {
      const u = new URL(req.url);
      if (falhar(u.pathname)) return new Response("erro", { status: 500 });
      return Response.json({ rota: u.pathname, turno: 2, at: new Date().toISOString() });
    },
  });
  try {
    const p = Bun.spawn(["bun", "run", "scripts/exportar-publico.ts", "--saida", saida, "--anterior", anterior, "--base", `http://127.0.0.1:${srv.port}`], {
      cwd: RAIZ, stdout: "pipe", stderr: "pipe",
    });
    expect(await p.exited).toBe(0);
  } finally {
    await srv.stop(true);
  }
  return JSON.parse(readFileSync(join(saida, "manifest.json"), "utf8")) as Record<string, unknown>;
}

describe("exportar-publico --anterior", () => {
  test("rota com erro: vale o último publicado, não o retrato velho da saída; sem anterior, pendente", async () => {
    const saida = pasta();
    const anterior = pasta();
    mkdirSync(saida, { recursive: true });
    writeFileSync(join(saida, "ufs.json"), JSON.stringify({ retrato: "13:27, velho" }));
    writeFileSync(join(anterior, "ufs.json"), JSON.stringify({ retrato: "último publicado" }));
    const m = await exportar(saida, anterior, (c) => c === "/api/2t/ufs" || c === "/api/2t/pausas");
    expect(m.pendentes).toEqual(["ufs", "pausas"]);
    expect(JSON.parse(readFileSync(join(saida, "ufs.json"), "utf8"))).toEqual({ retrato: "último publicado" });
    expect(JSON.parse(readFileSync(join(saida, "pausas.json"), "utf8"))).toEqual({ pendente: true });
    expect(JSON.parse(readFileSync(join(saida, "regioes.json"), "utf8"))).toMatchObject({ rota: "/api/2t/regioes" });
  });

  test("tudo respondendo: nenhuma pendência", async () => {
    const saida = pasta();
    const m = await exportar(saida, saida, () => false);
    expect(m.pendentes).toEqual([]);
    expect(m.turno).toBe(2);
  });
});
