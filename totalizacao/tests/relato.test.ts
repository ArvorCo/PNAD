import { describe, expect, test } from "bun:test";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { hashIp, ipCliente, normalizarContato, resumirUA, TIPOS_RELATO, validarRelato } from "../src/relato/validar.ts";

const BASE = { turno: 2, uf: "SP", zona: 1, secao: 123, tipo: "fila_longa", texto: "Fila de duas horas.", presenciou: true };

function motivo(corpo: unknown): string | null {
  const r = validarRelato(corpo);
  return r.ok ? null : r.motivo;
}

describe("validarRelato", () => {
  test("aceita o mínimo e normaliza", () => {
    const r = validarRelato({ ...BASE, uf: "sp", zona: "1", secao: "0123", texto: "  linha\r\noutra  " });
    expect(r.ok).toBe(true);
    if (!r.ok) return;
    expect(r.relato).toEqual({
      turno: 2, uf: "SP", zona: 1, secao: 123, local_id: null, tipo: "fila_longa", texto: "linha\noutra",
      hora_aproximada: null, presenciou: true, contato: null, versao: null,
    });
  });

  test("campos opcionais", () => {
    const r = validarRelato({ ...BASE, local_id: "SP-71072-1-1015", hora_aproximada: "16:45", contato: "Pessoa@Exemplo.com.br", versao: "2026-10-26.1" });
    expect(r.ok && r.relato.local_id).toBe("SP-71072-1-1015");
    expect(r.ok && r.relato.hora_aproximada).toBe("16:45");
    expect(r.ok && r.relato.contato).toBe("pessoa@exemplo.com.br");
  });

  test("recusa o que foge do esquema", () => {
    expect(motivo(null)).toBe("corpo invalido");
    expect(motivo([])).toBe("corpo invalido");
    expect(motivo({ ...BASE, turno: 3 })).toBe("turno invalido");
    expect(motivo({ ...BASE, uf: "XX" })).toBe("UF invalida");
    expect(motivo({ ...BASE, zona: 0 })).toBe("zona ou secao invalida");
    expect(motivo({ ...BASE, secao: 10000 })).toBe("zona ou secao invalida");
    expect(motivo({ ...BASE, secao: 1.5 })).toBe("zona ou secao invalida");
    expect(motivo({ ...BASE, tipo: "fraude" })).toBe("tipo invalido");
    expect(motivo({ ...BASE, tipo: "toString" })).toBe("tipo invalido");
    expect(motivo({ ...BASE, texto: "   " })).toBe("texto obrigatorio");
    expect(motivo({ ...BASE, texto: undefined })).toBe("texto obrigatorio");
    expect(motivo({ ...BASE, texto: "a".repeat(1001) })).toBe("texto acima de 1000 caracteres");
    expect(motivo({ ...BASE, texto: "oi\u0000" })).toBe("texto com caracteres de controle");
    expect(motivo({ ...BASE, texto: "oi‮" })).toBe("texto com caracteres de controle");
    expect(motivo({ ...BASE, hora_aproximada: "25:00" })).toBe("hora invalida");
    expect(motivo({ ...BASE, hora_aproximada: "9:30" })).toBe("hora invalida");
    expect(motivo({ ...BASE, presenciou: "sim" })).toBe("presenciou invalido");
    expect(motivo({ ...BASE, local_id: "RJ-1-1-1" })).toBe("local invalido");
    expect(motivo({ ...BASE, local_id: "SP-1-1-<b>" })).toBe("local invalido");
    expect(motivo({ ...BASE, contato: "não sei" })).toBe("contato invalido");
  });

  test("texto de 1.000 caracteres com acento passa (conta caractere, não byte)", () => {
    expect(motivo({ ...BASE, texto: "é".repeat(1000) })).toBeNull();
  });
});

describe("normalizarContato", () => {
  test("telefone e e-mail", () => {
    expect(normalizarContato("(11) 98765-4321")).toBe("+5511987654321");
    expect(normalizarContato("+55 11 98765-4321")).toBe("+5511987654321");
    expect(normalizarContato("")).toBeNull();
    expect(normalizarContato(undefined)).toBeNull();
    expect(normalizarContato("123")).toBeUndefined();
    expect(normalizarContato("a@b")).toBeUndefined();
    expect(normalizarContato(42)).toBeUndefined();
  });
});

describe("resumirUA e IP", () => {
  test("resume sem versão", () => {
    expect(resumirUA("Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/130.0 Mobile Safari/537.36")).toBe("android/chrome");
    expect(resumirUA("Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit Version/18.0 Mobile Safari/604.1")).toBe("ios/safari");
    expect(resumirUA("curl/8.7.1")).toBe("outro/script");
    expect(resumirUA(null)).toBeNull();
  });
  test("primeiro IP do x-forwarded-for", () => {
    const h = new Headers({ "x-forwarded-for": "203.0.113.7, 10.0.0.1" });
    expect(ipCliente(h)).toBe("203.0.113.7");
    expect(ipCliente(new Headers())).toBe("0.0.0.0");
  });
  test("hash do IP depende do sal e do dia", async () => {
    const a = await hashIp("sal", "2026-10-26", "203.0.113.7");
    expect(a).toMatch(/^[0-9a-f]{64}$/);
    expect(await hashIp("sal", "2026-10-27", "203.0.113.7")).not.toBe(a);
    expect(await hashIp("outro", "2026-10-26", "203.0.113.7")).not.toBe(a);
  });
});

test("tipos iguais na migração 0005", () => {
  const sql = readFileSync(join(import.meta.dir, "../supabase/migrations/0005_relatos_secao.sql"), "utf8");
  const bloco = /create type relato_tipo as enum \(([^)]*)\)/.exec(sql)?.[1] ?? "";
  expect([...bloco.matchAll(/'([a-z_]+)'/g)].map((m) => m[1])).toEqual([...TIPOS_RELATO]);
});
