import { describe, expect, test } from "bun:test";
import { abrirEscrita } from "../src/db/abrir.ts";
import { Escritor } from "../src/db/escrita.ts";
import type { ItemLote, LinhaFetch, LinhaSnapshot } from "../src/db/escrita.ts";
import { comprimir, gunzipTexto, itensDeAb, itensDeCm, itensDeEleC, itensDeU, sha256Hex } from "../src/db/itens.ts";
import {
  abAtual, arquivoPorChave, atual, blobDoSnapshot, candidatosDoSnapshot, maxSnapshotId, partidosDoSnapshot,
  serieDoArquivo, todosArquivos, ultimoSnapshotPorChave,
} from "../src/db/leitura.ts";
import { normalizarAb, normalizarCm, normalizarEleC, normalizarU } from "../src/parse/normalizar.ts";
import { chave, keyAb, keyU, registroDeArquivos, urlDe } from "../src/tse/urls.ts";
import type { ArquivoRegistro, FileKey } from "../src/types.ts";
import { bytes, lerAb, lerCm, lerEleC, lerU } from "./helpers.ts";

const reg = (k: FileKey, tier: 0 | 1 | 2 | 3 | 4): ArquivoRegistro => ({ ...k, chave: chave(k), url: urlDe(k), tier, sonda: false });

function fetchOk(arquivo: number | { ref: string }, sha: string, em: string): LinhaFetch {
  return {
    arquivo_id: arquivo, iniciado_em: em, duracao_ms: 42, motivo: "periodico", condicional: 1, http_status: 200,
    classe: "ok", etag: '"abc"', last_modified: null, servidor_date: null, cache_hdr: "max-age=57", age: 3, bytes: 1000,
    body_sha256: sha, mudou: 0, erro: null,
  };
}

/** Itens de um snapshot completo de -u, como o processador do coletor fará. */
function loteU(arquivoId: number, arquivo: string, em: string, opts: { regressivo?: 0 | 1; tf?: string } = {}): ItemLote[] {
  const corpo = bytes(arquivo);
  const sha = sha256Hex(corpo) + (opts.tf ?? "") + (opts.regressivo ?? "");
  const p = lerU(arquivo);
  const n = normalizarU(opts.tf ? { ...p, tf: opts.tf } : p, { uf: "sp", politicaCandidatos: "sempre", primeiro: true });
  const { gz, bytes: tamanho } = comprimir(corpo);
  const snap: LinhaSnapshot = {
    ...n.snapshotMeta, arquivo_id: arquivoId, fetch_id: { ref: "f" }, sha256: sha, capturado_em: em,
    regressivo: opts.regressivo ?? 0, anterior_id: null,
  };
  return [
    { k: "fetch", ref: "f", row: fetchOk(arquivoId, sha, em) },
    { k: "blob", sha256: sha, bytes: tamanho, gz, criado_em: em },
    { k: "snapshot", ref: "s", row: snap },
    ...itensDeU(n, { ref: "s" }),
    { k: "evento", row: { em, tipo: "teste", snapshot_id: { ref: "s" }, arquivo_id: arquivoId, detalhe: { ok: true } } },
  ];
}

describe("Escritor e leitura", () => {
  const db = abrirEscrita(":memory:");
  const w = new Escritor(db);
  const kVer = keyU(619, 13, "mu", "sp", "71072");
  const kPres = keyU(6257, 1, "br");
  const kAb = keyAb(6257, "sp");

  test("configuração e registro", () => {
    const r = w.gravarLote([
      ...itensDeEleC(normalizarEleC(lerEleC("ele-c.json"))),
      ...itensDeCm(normalizarCm(lerCm("mun-e006257-cm.json"))),
      ...[...registroDeArquivos(new Map([[6257, lerCm("mun-e006257-cm.json")]]))].map((row): ItemLote => ({ k: "arquivo", row })),
      { k: "arquivo", ref: "ver", row: reg(kVer, 2) },
      { k: "meta", chave: "teste", valor: "1" },
    ]);
    expect(r.ids.get("ver")).toBeGreaterThan(0);
    expect(db.query<{ n: number }, []>("SELECT COUNT(*) AS n FROM municipio").get()?.n).toBe(5757);
    expect(db.query<{ n: number }, []>("SELECT COUNT(*) AS n FROM cargo").get()?.n).toBe(7);
    const total = todosArquivos(db).length;
    // reinserir o registro é idempotente e devolve o mesmo id
    const r2 = w.gravarLote([{ k: "arquivo", ref: "ver", row: reg(kVer, 2) }]);
    expect(r2.ids.get("ver")).toBe(r.ids.get("ver") ?? -1);
    expect(todosArquivos(db).length).toBe(total);
  });

  test("snapshot completo de vereador 2024 lido de volta", () => {
    const arq = arquivoPorChave(db, chave(kVer));
    if (!arq) throw new Error("arquivo");
    const r = w.gravarLote(loteU(arq.id, "2024/sp71072-c0013-e000619-u.json", "2026-10-04T20:00:01.000Z", { tf: "n" }));
    const sid = r.ids.get("s") ?? -1;
    const snap = ultimoSnapshotPorChave(db, chave(kVer));
    expect(snap?.snapshot_id).toBe(sid);
    expect(snap?.vagas).toBe(55);
    expect(snap?.tv).toBe(6773587);
    expect(snap?.tf).toBe(0);
    const cands = candidatosDoSnapshot(db, sid);
    expect(cands.length).toBe(979);
    expect(cands.filter((c) => c.eleito === 1).length).toBe(55);
    expect(cands[0]?.vap).toBeGreaterThanOrEqual(cands[1]?.vap ?? 0);
    expect(cands.find((c) => c.sqcand === 250002052100)?.sigla).toBe("REDE");
    const partidos = partidosDoSnapshot(db, sid);
    expect(partidos.find((p) => p.partido_n === 18)?.tvtl).toBe(1721);
    const fetchRow = db.query<{ snapshot_id: number; mudou: number }, []>("SELECT snapshot_id, mudou FROM fetch").get();
    expect(fetchRow).toEqual({ snapshot_id: sid, mudou: 1 });
    const blob = blobDoSnapshot(db, sid);
    if (!blob) throw new Error("blob");
    expect(JSON.parse(gunzipTexto(blob)).carg[0].nv).toBe("55");
    const ev = db.query<{ detalhe: string; snapshot_id: number }, []>("SELECT detalhe, snapshot_id FROM evento").get();
    expect(ev).toEqual({ detalhe: '{"ok":true}', snapshot_id: sid });
  });

  test("segundo snapshot final, regressivo ignorado, séries e views", () => {
    const arq = arquivoPorChave(db, chave(kVer));
    if (!arq) throw new Error("arquivo");
    const final = w.gravarLote(loteU(arq.id, "2024/sp71072-c0013-e000619-u.json", "2026-10-04T21:00:00.000Z")).ids.get("s");
    w.gravarLote(loteU(arq.id, "2024/sp71072-c0013-e000619-u.json", "2026-10-04T21:01:00.000Z", { regressivo: 1 }));
    expect(maxSnapshotId(db)).toBe((final ?? 0) + 1);
    expect(ultimoSnapshotPorChave(db, chave(kVer))?.snapshot_id).toBe(final ?? -1);
    expect(ultimoSnapshotPorChave(db, chave(kVer), "2026-10-04T20:30:00.000Z")?.tf).toBe(0);
    expect(serieDoArquivo(db, arq.id).length).toBe(2);
    const v = atual(db, { eleicao: 619, nivel: "mu", uf: "sp" });
    expect(v.length).toBe(1);
    expect(v[0]?.snapshot_id).toBe(final ?? -1);
    expect(v[0]?.tf).toBe(1);
    const delta = db.query<{ d_tv: number | null; intervalo_geracao_s: number | null }, [number]>(
      "SELECT d_tv, intervalo_geracao_s FROM v_snapshot_delta WHERE arquivo_id = ? AND regressivo = 0 ORDER BY snapshot_id",
    ).all(arq.id);
    expect(delta.map((d) => d.d_tv)).toEqual([null, 0]);
    const vcd = db.query<{ n: number }, []>("SELECT COUNT(*) AS n FROM v_voto_candidato_delta WHERE d_vap = 0").get();
    expect(vcd?.n).toBe(979);
    const fim = db.query<{ arquivo_id: number }, []>("SELECT arquivo_id FROM v_municipio_fim").all();
    expect(fim.map((f) => f.arquivo_id)).toEqual([arq.id]);
  });

  test("estado do arquivo sobrescrito inteiro", () => {
    const arq = arquivoPorChave(db, chave(kPres));
    if (!arq) throw new Error("arquivo");
    w.gravarLote([
      {
        k: "arquivo_estado", id: arq.id, row: {
          ativo: 1, etag: '"e1"', last_modified: null, sha256: "x", idg: 1079360, gerado_em: "2026-10-03T17:47:37.000Z",
          ultimo_snapshot_id: null, ultimo_fetch_em: "2026-10-03T18:00:00.000Z", ultimo_status: "ok", n_fetch: 3,
          n_mudancas: 1, erros_seguidos: 0, backoff_ate: null, final_agendado: 0,
        },
      },
    ]);
    expect(arquivoPorChave(db, chave(kPres))).toMatchObject({ etag: '"e1"', n_fetch: 3, idg: 1079360, ultimo_status: "ok" });
  });

  test("-ab: só mudanças gravadas, v_ab_atual reconstrói o estado", () => {
    const arq = arquivoPorChave(db, chave(kAb));
    if (!arq) throw new Error("arquivo");
    const p = lerAb("sp-e006257-ab.json");
    const n1 = normalizarAb(p, new Map());
    const gravarAb = (n: ReturnType<typeof normalizarAb>, sha: string, em: string): void => {
      const { gz, bytes: b } = comprimir(new TextEncoder().encode(sha));
      w.gravarLote([
        { k: "blob", sha256: sha, bytes: b, gz, criado_em: em },
        { k: "snapshot", ref: "s", row: { ...n.snapshotMeta, arquivo_id: arq.id, fetch_id: null, sha256: sha, capturado_em: em, regressivo: 0, anterior_id: null } },
        ...itensDeAb(n, { ref: "s" }),
      ]);
    };
    gravarAb(n1, "ab1", "2026-10-04T20:00:00.000Z");
    const p2 = structuredClone(p);
    const a = p2.abr.find((x) => x.cdabr === "71072");
    if (!a?.s) throw new Error("71072");
    a.s.st = "500";
    const n2 = normalizarAb(p2, n1.fingerprints);
    expect(n2.entradas.length).toBe(1);
    gravarAb(n2, "ab2", "2026-10-04T20:01:00.000Z");
    const estado = abAtual(db, 6257, "sp");
    expect(estado.length).toBe(646);
    expect(estado.find((e) => e.cdabr === "71072")?.st).toBe(500);
    expect(estado.find((e) => e.cdabr === "61000")?.st).toBe(0);
  });

  test("ref inexistente aborta o lote inteiro", () => {
    const antes = maxSnapshotId(db);
    expect(() => w.gravarLote([{ k: "totais", snapshot: { ref: "nada" }, row: normalizarU(lerU("br-c0001-e006257-u.json"), { uf: null, politicaCandidatos: "sempre", primeiro: true }).totais }])).toThrow();
    expect(maxSnapshotId(db)).toBe(antes);
  });
});
