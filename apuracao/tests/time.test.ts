import { describe, expect, test } from "bun:test";
import { dgHgToUtcIso, isoDiffMs, nowIso } from "../src/tse/time.ts";

describe("dgHgToUtcIso", () => {
  test("Brasília fixo -03:00", () => {
    expect(dgHgToUtcIso("04/10/2026", "17:00:00")).toBe("2026-10-04T20:00:00.000Z");
    expect(dgHgToUtcIso("03/10/2026", "15:36:16")).toBe("2026-10-03T18:36:16.000Z");
  });
  test("23:59:59 cruza para o dia seguinte em UTC", () => {
    expect(dgHgToUtcIso("04/10/2026", "23:59:59")).toBe("2026-10-05T02:59:59.000Z");
    expect(dgHgToUtcIso("31/12/2026", "22:00:00")).toBe("2027-01-01T01:00:00.000Z");
  });
  test("vazio ou inválido vira null", () => {
    expect(dgHgToUtcIso("", "")).toBeNull();
    expect(dgHgToUtcIso(undefined, "17:00:00")).toBeNull();
    expect(dgHgToUtcIso("2026-10-04", "17:00:00")).toBeNull();
    expect(dgHgToUtcIso("04/10/2026", "17:00")).toBeNull();
  });
});

describe("isoDiffMs e nowIso", () => {
  test("diferença em ms", () => {
    expect(isoDiffMs("2026-10-04T20:00:05.000Z", "2026-10-04T20:00:00.000Z")).toBe(5000);
    expect(isoDiffMs(null, "2026-10-04T20:00:00.000Z")).toBeNull();
    expect(isoDiffMs("lixo", "2026-10-04T20:00:00.000Z")).toBeNull();
  });
  test("nowIso é ISO UTC com ms", () => {
    expect(nowIso()).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/);
  });
});
