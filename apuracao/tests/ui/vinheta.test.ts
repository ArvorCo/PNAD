import { describe, expect, test } from "bun:test";
import { ehComando } from "../../src/ui/control/broadcast.ts";

describe("comando vinheta", () => {
  test("é aceito pelo canal com e sem valor", () => {
    expect(ehComando({ tipo: "vinheta" })).toBe(true);
    expect(ehComando({ tipo: "vinheta", valor: false })).toBe(true);
    expect(ehComando({ tipo: "vinhetas" })).toBe(false);
  });
});
