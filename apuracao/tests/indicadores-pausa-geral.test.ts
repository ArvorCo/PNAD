// Volta de pausa geral nos indicadores do 2º turno: idade, UF parada e velocidade medidas pela
// publicação (gerado_em), não pelo carimbo de totalização, e previsão de 100% limitada.
// Caso real do 1º turno: silêncio de 19:32 a 20:02 e versões publicadas às 20:02 com totalização
// de durante a pausa; às 20:04 as 27 UFs apareciam paradas e a previsão caía em 25/10.
import { describe, expect, test } from "bun:test";
import { ETA_MAX_MS, VEL_MIN_ETA_SPM, ritmo } from "../src/server/indicadores/agregados.ts";
import type { LinhaTempo, LinhaUf, Versao } from "../src/server/indicadores/linha-tempo.ts";
import { montarUfs } from "../src/server/indicadores/ufs.ts";
import { T0_2T_MS } from "../src/turno2/comum.ts";

const m = (min: number): number => T0_2T_MS + min * 60_000;

function versao(id: number, st: number, ts: number, o: { cap: number; pub: number; inst?: number }): Versao {
  return {
    id, cap: o.cap, inst: o.inst ?? o.pub, pub: o.pub, ger: o.pub, ts, st, snt: ts - st, te: ts * 300, est: st * 300,
    comparecimento: st * 240, abstencao: st * 60, tv: st * 240, vv: st * 220, vb: st * 10, vn: st * 10, votos: new Map([[13, st * 110], [22, st * 110]]),
  };
}

/** UFs publicando a cada minuto até `ate`; `voltam` republicam a cada minuto de `volta` a `fim`, com totalização `totPausa`. */
function cenario(ufs: readonly string[], ate: number, voltam: readonly string[], volta: number, fim: number, totPausa: number): LinhaTempo {
  const mapa = new Map<string, LinhaUf>();
  let id = 1;
  for (const uf of ufs) {
    const versoes: Versao[] = [];
    for (let i = 1; i <= ate; i += 1) versoes.push(versao(id++, i * 10, 1000, { cap: m(i) + 20_000, pub: m(i) }));
    if (voltam.includes(uf)) {
      for (let i = volta; i <= fim; i += 1) {
        const st = (ate + 1 + i - volta) * 10;
        versoes.push(versao(id++, st, 1000, { cap: m(i) + 20_000, pub: m(i), inst: i === volta ? m(totPausa) : m(i) }));
      }
    }
    mapa.set(uf, { uf, arquivo_id: mapa.size + 1, versoes });
  }
  return { ele: 6258, cargo: 1, ufs: mapa };
}

const ufsDe = (lt: LinhaTempo, agora: number) =>
  montarUfs({ lt, rel: { agoraMs: agora, t0Ms: T0_2T_MS }, regua: null, ab: [], muns: [], limiarMin: 10 }).ufs.filter((u) => lt.ufs.has(u.uf));

describe("volta de pausa geral", () => {
  // quatro UFs publicam até 17:30; silêncio de 30 min; SP e RJ voltam às 18:00 com totalização das 17:45
  const lt = cenario(["SP", "RJ", "MG", "BA"], 30, ["SP", "RJ"], 60, 75, 45);

  test("dois minutos depois da volta nenhuma UF está parada, e a idade é a da publicação", () => {
    const u = ufsDe(lt, m(62) + 30_000);
    expect(u.filter((x) => x.parada).map((x) => x.uf)).toEqual([]);
    // SP: publicada às 18:02 (contagem nova a cada minuto), não às 17:45 da totalização da volta
    expect(u.find((x) => x.uf === "SP")?.idade_s).toBe(30);
    // MG ainda não voltou: idade conta desde a última publicação (17:30)
    expect(u.find((x) => x.uf === "MG")?.idade_s).toBe(32.5 * 60);
  });

  test("UF que não volta em 10 min depois da retomada geral fica parada", () => {
    const u = ufsDe(lt, m(71));
    expect(u.filter((x) => x.parada).map((x) => x.uf).sort()).toEqual(["BA", "MG"]);
  });

  test("velocidade pela publicação: a volta não zera o ritmo nem joga a previsão para semanas adiante", () => {
    const linhas = [...lt.ufs.values()];
    const r = ritmo(linhas, m(62) + 30_000);
    // SP e RJ: de 300 (17:30) a 330 (18:02) cada, 60 seções em 10 min
    expect(r.vel_10min_spm).toBe(6);
    expect(r.eta_100_iso).not.toBeNull();
    const eta = Date.parse(r.eta_100_iso ?? "");
    expect(eta - (m(62) + 30_000)).toBeLessThanOrEqual(ETA_MAX_MS);
  });
});

describe("previsão de 100%", () => {
  const umaUf = (pontos: [number, number][], ts: number): LinhaUf => ({
    uf: "SP", arquivo_id: 1, versoes: pontos.map(([min, st], i) => versao(i + 1, st, ts, { cap: m(min) + 10_000, pub: m(min) })),
  });

  test("além de 8 h à frente vira null", () => {
    // 10 seções em 10 min e 10.000 faltando: 1.000 min (16,7 h)
    const r = ritmo([umaUf([[0, 0], [5, 5], [10, 10]], 10_010)], m(10) + 30_000);
    expect(r.vel_10min_spm).toBe(1);
    expect(r.eta_100_iso).toBeNull();
  });

  test(`abaixo de ${VEL_MIN_ETA_SPM} seção por minuto não há previsão`, () => {
    const r = ritmo([umaUf([[0, 0], [10, 2]], 10)], m(10) + 30_000);
    expect(r.vel_10min_spm).toBe(0.2);
    expect(r.eta_100_iso).toBeNull();
  });

  test("ritmo normal mantém a previsão", () => {
    const r = ritmo([umaUf([[0, 0], [10, 100]], 200)], m(10) + 30_000);
    expect(r.vel_10min_spm).toBe(10);
    expect(r.eta_100_iso).toBe(new Date(m(10) + 30_000 + 10 * 60_000).toISOString());
  });
});
