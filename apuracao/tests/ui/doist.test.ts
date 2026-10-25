// Telão do 2º turno: normalizadores das rotas /api/2t/*, escalas, seleções de destaque, playlist,
// atalhos, mock determinístico e as funções puras das telas novas.
import { describe, expect, test } from "bun:test";
import { CATEGORIAS, contarPorCategoria, maisRecentes } from "../../src/ui/data/categorias.ts";
import {
  dadosDe,
  normalizarAbstencao,
  normalizarEstaduais,
  normalizarEvolucao,
  normalizarParalela,
  normalizarPausas,
  normalizarRegioes,
  normalizarSecoes,
  normalizarUfs,
  pedidoDaRota,
  textoSemFonte,
} from "../../src/ui/data/doist.ts";
import type { UfLinha } from "../../src/ui/data/doist.ts";
import { normalizarAnomalias } from "../../src/ui/data/api.ts";
import { contraste, NAO_INICIADO, PAPEL } from "../../src/ui/data/cores.ts";
import { lerParamsMock } from "../../src/ui/data/mock-hash.ts";
import { criarMock } from "../../src/ui/data/mock.ts";
import { emPausaNacionalMin, GOVERNADORES_2T, PAUSAS_NACIONAL, shiftMin } from "../../src/ui/data/mock2t.ts";
import { eventoAfeta, intervaloDe, mesmoConteudo } from "../../src/ui/dados.ts";
import { destinoDaTecla2T, destinoDaUf, destinoDoDigito, subirNivel, TECLA_TELA_2T } from "../../src/ui/control/navegacao.ts";
import { expandirPlaylist, PLAYLIST_2T, PLAYLIST_PADRAO, playlistDoTurno } from "../../src/ui/control/rotation.ts";
import { criarIndice } from "../../src/ui/control/search.ts";
import { AMOSTRA_CONFIG } from "../../src/ui/data/amostra.ts";
import {
  COR_ABSTENCAO_CAIU,
  COR_ABSTENCAO_SUBIU,
  atrasoDaCelula,
  corDivergente,
  dominioDuelo,
  estadualMaisApertado,
  evolucaoSvg,
  fundoDoDelta,
  faixasDePausa,
  fatiasConferencia,
  fechamPorUltimo,
  fechamentoPrevisto,
  fimDoEixo,
  hhmmDeMin,
  idadeCurta,
  minDeHhmm,
  municipiosAbertos,
  passoDoEixo,
  pontosDoDuelo,
  regiaoMaisLenta,
  rotuloAtraso,
  rotuloPp,
  ticksDeHora,
  topAtraso,
  ufsMaisLentas,
} from "../../src/ui/views/doist-util.ts";
import { IDS_2T, TELAS_2T } from "../../src/ui/views/meta-2t.ts";
import { ultimoDuelo } from "../../src/ui/views/evolucao.ts";
import { unidadesDeAbstencao } from "../../src/ui/views/abstencao.ts";
import { pctPlacar } from "../../src/ui/views/paralela.ts";
import { escalaLag, ufsDeMaiorLag } from "../../src/ui/views/secoes.ts";
import { minutosDasVersoes } from "../../src/ui/views/pausas.ts";
import { coresDoPar } from "../../src/ui/views/gov2t.ts";
import { normalizarCampos } from "../../src/ui/data/cores.ts";
import type { EventoSse, Lotes, State } from "../../src/ui/state/types.ts";
import { ehSegundoTurno, ROTULO_PRES_2T, ROTULOS, TITULOS, tituloDaTela } from "../../src/ui/views/index.ts";

const MIN = 60_000;
const T0 = Date.parse("2026-10-25T20:00:00.000Z");

function ufLinha(parcial: Partial<UfLinha> & { uf: string }): UfLinha {
  return {
    nome: parcial.uf,
    regiao: "SE",
    ts: 1000,
    st: 500,
    snt: 500,
    pst: 50,
    te: 100_000,
    comparecimento: 0,
    abstencao: 0,
    pa: 0,
    munnr: 0,
    munpt: 0,
    munf: 0,
    votos: {},
    lider: null,
    margem_pp: 0,
    ultima_versao_em: null,
    idade_s: 10,
    vel_10min_spm: 5,
    eta_100_iso: null,
    parada: false,
    ref_1t: null,
    pendentes_maiores: [],
    ...parcial,
  };
}

const ref = (atraso: number | null, p100 = 150) => ({ pst_mesmo_relogio: 60, atraso_min: atraso, p50_min: 60, p90_min: 110, p99_min: 140, p100_min: p100, pa_final: 21 });

describe("normalizadores das rotas /api/2t/*", () => {
  test("pendente, erro e corpo vazio viram a resposta certa, nunca exceção", () => {
    for (const n of [normalizarRegioes, normalizarUfs, normalizarAbstencao, normalizarEstaduais, normalizarEvolucao, normalizarPausas, normalizarSecoes, normalizarParalela]) {
      expect(n({ pendente: true, rota: "x" })).toEqual({ situacao: "pendente" });
      expect(n({ erro: "banco fechado" })).toEqual({ situacao: "erro", mensagem: "banco fechado" });
      expect(n(null).situacao).toBe("erro");
      expect(n("texto").situacao).toBe("erro");
      expect(n({}).situacao).toBe("erro");
    }
  });

  test("regiões: campos ausentes viram zero e a régua do 1º turno pode faltar", () => {
    const r = normalizarRegioes({
      at: "2026-10-25T21:00:00Z",
      min: 60,
      turno: 2,
      referencia_1t: false,
      brasil: { sigla: "BR", pst: 12.5, ts: 100, st: 12, votos: { "1": { vap: 10, pvapn: 55 } } },
      regioes: [{ sigla: "N", nome: "Norte", ts: 10, st: 5, ref_1t: null, lider: "1" }],
    });
    expect(r.situacao).toBe("ok");
    if (r.situacao !== "ok") return;
    expect(r.dados.referencia_1t).toBe(false);
    expect(r.dados.brasil.snt).toBe(88);
    expect(r.dados.regioes[0]?.ref_1t).toBeNull();
    expect(r.dados.regioes[0]?.snt).toBe(5);
    expect(r.dados.brasil.votos["1"]).toEqual({ vap: 10, pvapn: 55 });
    expect(r.dados.regioes[0]?.vel_10min_spm).toBe(0);
  });

  test("UFs: sigla em caixa alta, pendentes e ref_1t opcional", () => {
    const r = normalizarUfs({
      at: "x",
      min: 1,
      ufs: [{ uf: "sp", pst: 3, pendentes_maiores: [{ cd: "71072", nm: "São Paulo", te: 9, pst: 40 }], ref_1t: { pst_mesmo_relogio: 5, atraso_min: null } }],
    });
    expect(dadosDe({ ufs: r }, "ufs")?.ufs[0]?.uf).toBe("SP");
    expect(dadosDe({ ufs: r }, "ufs")?.ufs[0]?.pendentes_maiores[0]?.nm).toBe("São Paulo");
    expect(dadosDe({ ufs: r }, "ufs")?.ufs[0]?.ref_1t?.atraso_min).toBeNull();
    expect(dadosDe({ ufs: r }, "ufs")?.limiar_parada_min).toBe(10);
  });

  test("abstenção: a chave vem de sigla ou de uf e o Δ nulo é preservado", () => {
    const r = normalizarAbstencao({
      brasil: { sigla: "BR", delta_pp: null, pa_2t: 20 },
      regioes: [{ sigla: "NE", nome: "Nordeste", delta_pp: 1.2 }],
      ufs: [{ uf: "ba", nome: "Bahia", delta_pp: -0.4, pa_corrente: 21, pa_final_1t: 22 }],
      destaques: { subiu: [{ uf: "pe", cd: "1", nm: "X", te: 30000, pa_2t: 25, pa_1t: 18, delta_pp: 7, fechou_min: 90 }] },
    });
    if (r.situacao !== "ok") throw new Error("esperava ok");
    expect(r.dados.brasil.chave).toBe("BR");
    expect(r.dados.brasil.delta_pp).toBeNull();
    expect(r.dados.regioes[0]?.chave).toBe("NE");
    expect(r.dados.ufs[0]?.chave).toBe("BA");
    expect(r.dados.destaques.subiu[0]?.uf).toBe("PE");
    expect(r.dados.destaques.caiu).toEqual([]);
  });

  test("evolução: ordena os candidatos pelo número de urna e troca as colunas a e b junto", () => {
    const r = normalizarEvolucao({
      at: "x",
      passo_s: 300,
      candidatos: [
        { sqcand: "F", n: "22", nome_urna: "Flávio" },
        { sqcand: "L", n: "13", nome_urna: "Lula" },
      ],
      series: { br: [[10, 5, 60, 40, 100], [0, 0, null, null, 0]] },
      referencia_1t: { br: [[10, 6], [0, 0]] },
    });
    if (r.situacao !== "ok") throw new Error("esperava ok");
    expect(r.dados.candidatos.map(c => c.n)).toEqual(["13", "22"]);
    const pts = r.dados.series.BR ?? [];
    expect(pts[0]).toEqual({ min: 0, pst: 0, a: null, b: null, st: 0 });
    // coluna a era o 22 (60) e vira b; o 13 (40) vira a
    expect(pts[1]).toEqual({ min: 10, pst: 5, a: 40, b: 60, st: 100 });
    expect(r.dados.referencia_1t?.BR).toEqual([[0, 0], [10, 6]]);
  });

  test("evolução sem referência do 1º turno", () => {
    const r = normalizarEvolucao({ at: "x", candidatos: [], series: {}, referencia_1t: null });
    expect(r.situacao === "ok" && r.dados.referencia_1t).toBeNull();
  });

  test("pausas e seções: blocos opcionais não quebram", () => {
    const p = normalizarPausas({ at: "x", min: 100, nacional: { st: 5, ts: 10, em_pausa: true, pausa_atual: { desde: "2026-10-25T20:30:00Z", minutos: 12 }, historico: [{ de: "a", ate: "b", minutos: 8 }] }, ufs: [{ uf: "ma", em_pausa: true }] });
    if (p.situacao !== "ok") throw new Error("esperava ok");
    expect(p.dados.nacional.pausa_atual?.minutos).toBe(12);
    expect(p.dados.referencia_1t.pausa_geral).toBeNull();
    expect(p.dados.ufs[0]?.uf).toBe("MA");
    const s = normalizarSecoes({ at: "x", min: 1, brasil: { alvo: 10, recebidas: 4, lag_encerr_recebimento_min: { p50: 2 } }, por_uf: [{ uf: "ac", alvo: 5, recebidas: 1 }] });
    if (s.situacao !== "ok") throw new Error("esperava ok");
    expect(s.dados.brasil.lag_recebimento_totalizacao_min).toBeNull();
    expect(s.dados.brasil.lag_encerr_recebimento_min).toEqual({ p50: 2, p90: null, p99: null });
    expect(s.dados.por_uf[0]?.ref_1t).toBeNull();
  });

  test("paralela: erro puro vira erro; erro junto dos números vira aviso dentro dos dados", () => {
    expect(normalizarParalela({ erro: "supabase fora" })).toEqual({ situacao: "erro", mensagem: "supabase fora" });
    const r = normalizarParalela({ at: "x", erro: "leitura falhou", recebidos: { bus: 7 }, conferencia: { iguais: 5, divergentes: 1 }, placar_bus: { presidente: { votos: { "13": 3 } }, governador: { ac: { votos: { "11": 1 }, secoes: 2 } } } });
    if (r.situacao !== "ok") throw new Error("esperava ok");
    expect(r.dados.erro).toBe("leitura falhou");
    expect(r.dados.recebidos.bus).toBe(7);
    expect(r.dados.placar_bus.governador.AC?.secoes).toBe(2);
    expect(r.dados.divergencias).toEqual([]);
  });

  test("pedido da evolução: nível e passo de 5 minutos; as demais rotas sem parâmetros", () => {
    expect(pedidoDaRota("evolucao-regiao")).toEqual({ caminho: "/api/2t/evolucao", params: { nivel: "regiao", passo: 300 } });
    expect(pedidoDaRota("evolucao-uf").params.nivel).toBe("uf");
    expect(pedidoDaRota("paralela")).toEqual({ caminho: "/api/2t/paralela", params: {} });
  });

  test("texto de fonte indisponível", () => {
    expect(textoSemFonte({}, "ufs")).toBe("aguardando a fonte");
    expect(textoSemFonte({ ufs: { situacao: "pendente" } }, "ufs")).toContain("fonte indisponível");
    expect(textoSemFonte({ ufs: { situacao: "erro", mensagem: "HTTP 500" } }, "ufs")).toBe("fonte indisponível: HTTP 500");
    expect(dadosDe({ ufs: { situacao: "pendente" } }, "ufs")).toBeNull();
  });

  test("anomalias aceitam as quatro categorias novas e o detalhe em texto", () => {
    const a = normalizarAnomalias([
      { categoria: "pausa", tipo: "pausa_nacional_inicio", at: "x", texto: "t", severidade: "warn", detalhe: '{"minutos": 6}' },
      { categoria: "divergencia", tipo: "divergencia_paralela", at: "y", texto: "d", detalhe: { campos: ["nulos"] } },
      { categoria: "abstencao", tipo: "abstencao_atipica_mun", at: "z", texto: "a" },
      { categoria: "paralela", tipo: "paralela_conferida", at: "w", texto: "p", detalhe: "não é json" },
      { categoria: "outro", tipo: "erro_interno", at: "q", texto: "fora do ar" },
    ]);
    expect(a.map(x => x.tipo)).toEqual(["pausa", "divergencia", "abstencao", "paralela"]);
    expect(a[0]?.detalhe).toEqual({ minutos: 6 });
    expect(a[1]?.detalhe).toEqual({ campos: ["nulos"] });
    expect(a[3]?.detalhe).toBeUndefined();
  });
});

describe("categorias de alerta", () => {
  test("contagem inclui as categorias zeradas e a ordem é de atenção", () => {
    const c = contarPorCategoria([{ tipo: "pausa" }, { tipo: "pausa" }, { tipo: "virada" }]);
    expect(c.pausa).toBe(2);
    expect(c.divergencia).toBe(0);
    expect(Object.keys(c)).toEqual([...CATEGORIAS]);
    expect(CATEGORIAS[0]).toBe("divergencia");
  });

  test("as mais recentes: instante decrescente e empate pela severidade", () => {
    const l = [
      { at: "2026-10-25T21:00:00Z", severidade: "info" as const, id: 1 },
      { at: "2026-10-25T22:00:00Z", severidade: "info" as const, id: 2 },
      { at: "2026-10-25T22:00:00Z", severidade: "error" as const, id: 3 },
      { at: "2026-10-25T20:00:00Z", severidade: "warn" as const, id: 4 },
    ];
    expect(maisRecentes(l, 3).map(x => x.id)).toEqual([3, 2, 1]);
    expect(maisRecentes(l, 12)).toHaveLength(4);
  });
});

describe("escala divergente da abstenção", () => {
  test("zero é papel, ±5 é cor cheia, acima disso satura e sem Δ é cinza", () => {
    expect(corDivergente(0)).toBe(PAPEL);
    expect(corDivergente(5)).toBe(COR_ABSTENCAO_SUBIU);
    expect(corDivergente(-5)).toBe(COR_ABSTENCAO_CAIU);
    expect(corDivergente(12)).toBe(COR_ABSTENCAO_SUBIU);
    expect(corDivergente(-30)).toBe(COR_ABSTENCAO_CAIU);
    expect(corDivergente(null)).toBe(NAO_INICIADO);
    expect(corDivergente(undefined)).toBe(NAO_INICIADO);
    expect(corDivergente(Number.NaN)).toBe(NAO_INICIADO);
    expect(corDivergente(2.5)).not.toBe(corDivergente(5));
    expect(corDivergente(2.5)).not.toBe(PAPEL);
  });

  test("o fundo da etiqueta do Δ é sempre claro o bastante para texto escuro (4,5:1)", () => {
    for (const d of [-9, -5, -2.5, -0.4, 0, 0.4, 2.5, 5, 9]) expect(contraste(fundoDoDelta(d), "#192e2b")).toBeGreaterThan(4.5);
    expect(fundoDoDelta(null)).toBe(NAO_INICIADO);
    expect(contraste(NAO_INICIADO, "#192e2b")).toBeGreaterThan(4.5);
  });

  test("unidades do mapa vêm dos blocos por UF", () => {
    const u = unidadesDeAbstencao([{ chave: "SP", nome: "São Paulo", n_mun: 1, n_mun_fechados: 0, te_fechado: 0, pct_te_fechado: 12, comparecimento: 0, abstencao: 0, pa_2t: null, pa_1t_mesmos: null, delta_pp: null, pa_corrente: null, pa_final_1t: null }]);
    expect(u).toEqual([{ cd: "SP", nm: "São Paulo", pst: 12, tf: false }]);
  });
});

describe("seleção de destaques", () => {
  test("região mais lenta: o exterior só entra se for a única", () => {
    const base = { sigla: "", nome: "", ufs: [], ts: 10, st: 1, snt: 9, pst: 0, te: 0, est: 0, comparecimento: 0, abstencao: 0, pa: 0, votos: {}, vv: 0, vb: 0, vn: 0, tv: 0, lider: null, margem_pp: 0, vel_10min_spm: 0, eta_100_iso: null, ref_1t: null, atualizado_em: null };
    const r = (sigla: string, pst: number, ts = 10) => ({ ...base, sigla, pst, ts });
    expect(regiaoMaisLenta([r("N", 50), r("NE", 40), r("ZZ", 10)])?.sigla).toBe("NE");
    expect(regiaoMaisLenta([r("ZZ", 10)])?.sigla).toBe("ZZ");
    expect(regiaoMaisLenta([r("N", 50, 0)])).toBeNull();
    // nada totalizado ainda: não há região mais lenta
    expect(regiaoMaisLenta([{ ...r("N", 0), st: 0 }, { ...r("NE", 0), st: 0 }])).toBeNull();
    expect(regiaoMaisLenta([])).toBeNull();
  });

  test("UFs mais lentas: menor pst, depois mais seções, depois a sigla", () => {
    const l = ufsMaisLentas([ufLinha({ uf: "B", pst: 10, ts: 5 }), ufLinha({ uf: "A", pst: 10, ts: 5 }), ufLinha({ uf: "C", pst: 10, ts: 50 }), ufLinha({ uf: "D", pst: 1 })]);
    expect(l.map(u => u.uf)).toEqual(["D", "C", "A", "B"]);
  });

  test("top atraso: só com régua e já iniciadas, maior atraso primeiro", () => {
    const l = topAtraso(
      [
        ufLinha({ uf: "A", ref_1t: ref(5) }),
        ufLinha({ uf: "B", ref_1t: ref(30) }),
        ufLinha({ uf: "C", ref_1t: null }),
        ufLinha({ uf: "D", ref_1t: ref(null) }),
        ufLinha({ uf: "E", ref_1t: ref(40), st: 0 }),
        ufLinha({ uf: "F", ref_1t: ref(-8) }),
      ],
      3,
    );
    expect(l.map(u => u.uf)).toEqual(["B", "A", "F"]);
    expect(topAtraso([], 8)).toEqual([]);
  });

  test("previsão de fechamento: ETA do servidor, senão p100 do 1T mais o atraso, senão nada", () => {
    const eta = new Date(T0 + 190 * MIN).toISOString();
    expect(fechamentoPrevisto(ufLinha({ uf: "A", eta_100_iso: eta }), T0)).toBe(190);
    expect(fechamentoPrevisto(ufLinha({ uf: "B", ref_1t: ref(20, 150) }), T0)).toBe(170);
    expect(fechamentoPrevisto(ufLinha({ uf: "C" }), T0)).toBeNull();
    expect(fechamentoPrevisto(ufLinha({ uf: "D", pst: 100, ref_1t: ref(20) }), T0)).toBeNull();
    const ult = fechamPorUltimo([ufLinha({ uf: "A", ref_1t: ref(0, 100) }), ufLinha({ uf: "B", ref_1t: ref(30, 150) }), ufLinha({ uf: "C" })], T0, 2);
    expect(ult.map(x => x.u.uf)).toEqual(["B", "A"]);
  });

  test("maiores municípios abertos do país: junta as UFs e ordena pelo eleitorado", () => {
    const m = municipiosAbertos(
      [
        ufLinha({ uf: "SP", pendentes_maiores: [{ cd: "1", nm: "São Paulo", te: 9000, pst: 60 }, { cd: "2", nm: "Campinas", te: 800, pst: 70 }] }),
        ufLinha({ uf: "RJ", pendentes_maiores: [{ cd: "3", nm: "Rio", te: 5000, pst: 50 }] }),
      ],
      2,
    );
    expect(m.map(x => `${x.nm}/${x.uf}`)).toEqual(["São Paulo/SP", "Rio/RJ"]);
  });

  test("estadual mais apertado ignora quem ainda não tem voto", () => {
    const cand = (vap: number) => [{ sqcand: "1", n: "13", nome_urna: "A", partido: "PT", vap, pvapn: 50, campo: "esquerda" }];
    const e = (uf: string, margem: number, vap: number) => ({
      uf, nome: uf, ts: 1, st: 1, pst: 1, te: 1, comparecimento: 0, abstencao: 0, pa: 0, munnr: 0, munpt: 0, munf: 0,
      cand: cand(vap), lider: null, margem_pp: margem, viradas: [], ultima_versao_em: null, idade_s: null, ref_1t: null, pa_final_1t: null,
    });
    expect(estadualMaisApertado([e("AC", 20, 5), e("AM", -2, 5), e("DF", 0.1, 0)])?.uf).toBe("AM");
    expect(estadualMaisApertado([e("DF", 0, 0)])).toBeNull();
  });
});

describe("textos curtos", () => {
  test("atraso e pontos percentuais", () => {
    expect(rotuloAtraso(12.4)).toBe("+12 min");
    expect(rotuloAtraso(-3.6)).toBe("−4 min");
    expect(rotuloAtraso(0.4)).toBe("no ritmo");
    expect(rotuloAtraso(null)).toBe("sem régua");
    expect(rotuloPp(1.26)).toBe("+1,3 pp");
    expect(rotuloPp(-0.44)).toBe("−0,4 pp");
    expect(rotuloPp(0.02)).toBe("0,0 pp");
    expect(rotuloPp(null)).toBe("sem dado");
    expect(atrasoDaCelula(false, 12)).toBe("sem régua do 1º turno");
    expect(atrasoDaCelula(true, null)).toBe("aguardando");
    expect(atrasoDaCelula(true, 12)).toBe("+12 min");
  });

  test("idade da versão e relógio da apuração", () => {
    expect(idadeCurta(24)).toBe("24 s");
    expect(idadeCurta(180)).toBe("3 min");
    expect(idadeCurta(3900)).toBe("1 h 05 min");
    expect(idadeCurta(null)).toBe("sem dado");
    expect(hhmmDeMin(0)).toBe("17:00");
    expect(hhmmDeMin(152)).toBe("19:32");
    expect(hhmmDeMin(400)).toBe("23:40");
    expect(hhmmDeMin(480)).toBe("01:00");
    expect(minDeHhmm("19:32")).toBe(152);
    expect(minDeHhmm("00:30")).toBe(450);
    expect(minDeHhmm("lixo")).toBeNull();
    expect(minDeHhmm(null)).toBeNull();
  });
});

describe("linha do tempo das pausas", () => {
  test("faixas do histórico e da pausa em curso, ordenadas, sem faixa invertida", () => {
    const f = faixasDePausa(
      [
        { de: new Date(T0 + 118 * MIN).toISOString(), ate: new Date(T0 + 131 * MIN).toISOString(), minutos: 13, st_antes: 1, st_depois: 2 },
        { de: new Date(T0 + 50 * MIN).toISOString(), ate: new Date(T0 + 40 * MIN).toISOString(), minutos: 0, st_antes: null, st_depois: null },
        { de: new Date(T0 + 38 * MIN).toISOString(), ate: new Date(T0 + 46.5 * MIN).toISOString(), minutos: 0, st_antes: null, st_depois: null },
      ],
      { desde: new Date(T0 + 205 * MIN).toISOString(), minutos: 7 },
      T0,
    );
    expect(f.map(x => [x.de, x.ate])).toEqual([[38, 46.5], [118, 131], [205, 212]]);
    expect(f[0]?.minutos).toBe(8.5);
  });

  test("fim do eixo cobre o agora com folga e a grade vai de hora em hora", () => {
    expect(fimDoEixo(0)).toBe(180);
    expect(fimDoEixo(169)).toBe(180);
    expect(fimDoEixo(171)).toBe(240);
    expect(fimDoEixo(400)).toBe(420);
    expect(fimDoEixo(24_920)).toBe(1440);
    expect(ticksDeHora(180).map(t => t.texto)).toEqual(["17:00", "18:00", "19:00", "20:00"]);
    expect(ticksDeHora(240, 120).map(t => t.v)).toEqual([0, 120, 240]);
    expect(passoDoEixo(480)).toBe(60);
    expect(passoDoEixo(540)).toBe(120);
    expect(passoDoEixo(1440)).toBe(180);
    for (const fim of [180, 420, 600, 1440]) expect(ticksDeHora(fim).length).toBeLessThanOrEqual(10);
  });

  test("minutos das versões a partir dos lotes, sem as de antes das 17:00", () => {
    const lotes = { abr: "br", candidatos: [], lotes: [-5, 3, 1].map(m => ({ at: new Date(T0 + m * MIN).toISOString() })) } as unknown as Lotes;
    expect(minutosDasVersoes(lotes, T0)).toEqual([1, 3]);
    expect(minutosDasVersoes(undefined, T0)).toEqual([]);
  });
});

describe("evolução", () => {
  const pt = (min: number, pst: number, a: number | null, b: number | null) => ({ min, pst, a, b, st: 0 });

  test("domínio do duelo: o preferido de 30 a 70 quando cabe, senão ajustado de 5 em 5", () => {
    expect(dominioDuelo([pt(1, 5, 45, 55)])).toEqual([30, 70]);
    expect(dominioDuelo([pt(1, 5, 72, 28)])).toEqual([25, 75]);
    expect(dominioDuelo([])).toEqual([30, 70]);
  });

  test("ignora leituras com poucas seções e pontos sem votos", () => {
    const v = pontosDoDuelo([pt(1, 1, 90, 10), pt(2, 5, null, null), pt(3, 5, 50, 50)]);
    expect(v.map(p => p.min)).toEqual([3]);
    expect(ultimoDuelo([pt(1, 5, 40, 60), pt(2, 0, null, null)])?.min).toBe(1);
    expect(ultimoDuelo([])).toBeNull();
  });

  test("o SVG leva as duas linhas, a curva do 2T, a do 1T pontilhada e nunca NaN", () => {
    const svg = evolucaoSvg({
      largura: 400,
      altura: 300,
      pontos: [pt(0, 0, null, null), pt(20, 10, 48, 52), pt(40, 30, 50, 50)],
      ref: [[0, 0], [20, 14], [40, 36]],
      corA: "#b02f21",
      corB: "#1457aa",
      minAgora: 40,
      fim: 180,
      fonte: 22,
      margem: { t: 10, r: 10, b: 30, l: 40 },
    });
    expect(svg.startsWith("<svg")).toBe(true);
    expect(svg).toContain('class="ev-linha"');
    expect(svg).toContain('class="ev-pst1"');
    expect(svg).toContain('class="ev-pst2"');
    expect(svg).toContain('stroke="#b02f21"');
    expect(svg).not.toContain("NaN");
    expect(svg).not.toContain("undefined");
  });

  test("sem referência do 1T não desenha a curva pontilhada", () => {
    const svg = evolucaoSvg({ largura: 400, altura: 300, pontos: [pt(20, 10, 48, 52)], ref: null, corA: "#000", corB: "#111", minAgora: 20, fim: 180, fonte: 22, margem: { t: 10, r: 10, b: 30, l: 40 } });
    expect(svg).not.toContain("ev-pst1");
  });
});

describe("paralela e seções", () => {
  test("fatias da conferência somam 100 e zeram sem BUs", () => {
    const f = fatiasConferencia({ iguais: 90, divergentes: 1, tse_ainda_nao_publicou: 5, fora_do_oficial: 2, erro: 0, pendentes: 2 });
    expect(f.reduce((s, x) => s + x.pct, 0)).toBeCloseTo(100, 6);
    expect(f[0]?.chave).toBe("iguais");
    expect(fatiasConferencia({ iguais: 0, divergentes: 0, tse_ainda_nao_publicou: 0, fora_do_oficial: 0, erro: 0, pendentes: 0 }).every(x => x.pct === 0)).toBe(true);
  });

  test("placar dos BUs em % dos dois lados, nulo sem voto", () => {
    expect(pctPlacar({ "13": 30, "22": 70 }, "13", "22")).toEqual({ a: 30, b: 70, total: 100 });
    expect(pctPlacar({ "13": 0 }, "13", "22")).toBeNull();
    expect(pctPlacar({ "99": 5 }, "13", "22")).toBeNull();
  });

  test("lag por UF: as de maior p90 primeiro; escala cobre o p90 e a marca do 1T", () => {
    const l = (uf: string, p90: number | null, recebidas = 3, r90: number | null = null) => ({
      uf, alvo: 10, recebidas, encerramento_p50_hhmm: null, encerramento_p90_hhmm: null, tarde_apos_1730_pct: null,
      lag_encerr_recebimento_min: { p50: 1, p90, p99: null }, lag_encerr_emissao_min: { p50: null, p90: null, p99: null },
      lag_recebimento_totalizacao_min: null, ref_1t: r90 === null ? null : { lag_p50: 1, lag_p90: r90, enc_p90_hhmm: null },
    });
    const top = ufsDeMaiorLag([l("A", 5), l("B", 12), l("C", null), l("D", 9, 0)], 2);
    expect(top.map(x => x.uf)).toEqual(["B", "A"]);
    expect(escalaLag([l("A", 5)])).toBeCloseTo(5.25, 6);
    expect(escalaLag([l("A", 5, 3, 20)])).toBeCloseTo(21, 6);
    expect(escalaLag([])).toBeGreaterThan(0);
  });

  test("cores do par de governadores: campo de cada um e o segundo escurece se forem do mesmo campo", () => {
    const campos = normalizarCampos(null);
    const c = (campo: string) => ({ sqcand: "1", n: "1", nome_urna: "X", partido: "P", vap: 0, pvapn: 0, campo });
    const [a, b] = coresDoPar([c("esquerda"), c("direita")], campos);
    expect(a).not.toBe(b);
    const [x, y] = coresDoPar([c("direita"), c("direita")], campos);
    expect(x).not.toBe(y);
  });
});

describe("playlist, atalhos e navegação do 2º turno", () => {
  test("playlist do 2º turno vem do contrato e a do 1º não muda", () => {
    expect(playlistDoTurno(2, null, null)).toBe(PLAYLIST_2T);
    expect(playlistDoTurno(2, { itens: [{ v: "pres" }] }, null)).toBe(PLAYLIST_2T);
    expect(playlistDoTurno(1, null, { itens: [{ v: "regioes" }] })).toBe(PLAYLIST_PADRAO);
    expect(playlistDoTurno(2, null, { itens: [{ v: "alertas", dwell: 9 }] }).itens).toEqual([{ v: "alertas", dwell: 9 }]);
    expect(PLAYLIST_2T.itens.map(i => i.v)).toEqual(["pres", "regioes", "ufs", "evolucao", "gov-2t", "abstencao", "atraso", "pausas", "paralela", "alertas", "pres-uf"]);
    expect(PLAYLIST_2T.itens[0]?.dwell).toBe(25);
    const ultimo = PLAYLIST_2T.itens[PLAYLIST_2T.itens.length - 1];
    expect(ultimo).toMatchObject({ v: "pres-uf", uf: "$destaque", max: 3 });
  });

  test("a playlist do 2º turno expande no máximo 3 destaques e usa só telas registradas", () => {
    const estado = { ufs: AMOSTRA_CONFIG.ufs.map(u => ({ uf: u.uf, pst: 50 })) } as never;
    const e = expandirPlaylist(PLAYLIST_2T, estado, AMOSTRA_CONFIG, null);
    expect(e.filter(x => x.v === "pres-uf")).toHaveLength(3);
    expect(e.length).toBe(PLAYLIST_2T.itens.length - 1 + 3);
    const validas = new Set(["pres", "pres-uf", ...TELAS_2T.map(t => t.id)]);
    expect(e.every(x => validas.has(x.v))).toBe(true);
    expect(e[0]?.dwellMs).toBe(25_000);
  });

  test("Shift + letra abre as dez telas, sem repetir letra nem tela", () => {
    const letras = Object.keys(TECLA_TELA_2T);
    expect(new Set(letras).size).toBe(letras.length);
    expect(new Set(Object.values(TECLA_TELA_2T)).size).toBe(letras.length);
    expect(Object.values(TECLA_TELA_2T).sort()).toEqual([...IDS_2T].sort());
    expect(destinoDaTecla2T("G")).toMatchObject({ v: "gov-2t", uf: null });
    expect(destinoDaTecla2T("p")?.v).toBe("pausas");
    expect(destinoDaTecla2T("z")).toBeNull();
  });

  test("a tecla 3 e o Backspace seguem o turno; a tecla de UF desce de gov-2t para gov-uf", () => {
    expect(destinoDoDigito("3", null)?.v).toBe("gov");
    expect(destinoDoDigito("3", null, 2)?.v).toBe("regioes");
    expect(destinoDoDigito("6", null, 2)?.v).toBe("gov-2t");
    expect(destinoDoDigito("7", null, 2)?.v).toBe("exterior");
    expect(destinoDoDigito("9", null, 2)?.v).toBe("atraso");
    expect(destinoDoDigito("0", null, 2)?.v).toBe("pausas");
    expect(destinoDoDigito("0", null, 2)?.v).toBe("mov");
    expect(destinoDaUf("gov-2t", "sp")).toMatchObject({ v: "gov-uf", uf: "SP" });
    expect(destinoDaUf("pausas", "sp").v).toBe("pres-uf");
    expect(subirNivel({ v: "gov-uf", uf: "AC", mun: null, zonas: false, zona: null }, 2)?.v).toBe("gov-2t");
    expect(subirNivel({ v: "gov-uf", uf: "AC", mun: null, zonas: false, zona: null })?.v).toBe("gov");
  });

  test("a busca (/) encontra as telas novas pelo nome e por sinônimos", () => {
    const i = criarIndice();
    i.adicionarConfig(AMOSTRA_CONFIG);
    i.adicionarTelas(TELAS_2T.map(t => ({ id: t.id, rotulo: t.titulo, atalho: t.atalho, busca: t.busca })));
    expect(i.buscar("pausas")[0]).toMatchObject({ tipo: "tela", v: "pausas" });
    expect(i.buscar("paralela")[0]).toMatchObject({ tipo: "tela", v: "paralela" });
    expect(i.buscar("lerdo")[0]).toMatchObject({ tipo: "tela", v: "atraso" });
    expect(i.buscar("cadeia")[0]).toMatchObject({ tipo: "tela", v: "secoes" });
    expect(i.buscar("alertas")[0]?.tipo).toBe("tela");
  });
});

describe("títulos do 2º turno", () => {
  const estado = (turno: number): State => ({ config: { turno, eleicoes: { federal: 6258, estadual: 6260 }, ufs: [], municipios: {} }, estado: null }) as unknown as State;

  test("o duelo se chama Presidente, 2º turno só no 2º turno", () => {
    expect(ROTULO_PRES_2T).toBe("Presidente, 2º turno");
    expect(tituloDaTela("pres", estado(2), null)).toBe("Presidente, 2º turno");
    expect(tituloDaTela("pres", estado(1), null)).toBe("Presidente, Brasil");
    expect(ehSegundoTurno(estado(2))).toBe(true);
    expect(ehSegundoTurno({ config: null, estado: { turno: 2 } } as unknown as State)).toBe(true);
    expect(ehSegundoTurno({ config: null, estado: null } as unknown as State)).toBe(false);
  });

  test("cada tela nova tem título e rótulo sem travessão, e o título da faixa não leva a UF", () => {
    for (const t of TELAS_2T) {
      expect(TITULOS[t.id]).toBe(t.titulo);
      expect(ROTULOS[t.id]).toBe(t.rotulo);
      expect(`${t.titulo}${t.rotulo}${t.atalho}`).not.toContain("—");
      expect(tituloDaTela(t.id, estado(2), "SP")).toBe(t.titulo);
    }
  });
});

describe("carregador e eventos das rotas do 2º turno", () => {
  const ev = (e: Partial<EventoSse>): EventoSse => ({ kind: "resultado", ele: 6258, cargo: 1, abr: "br", snapshot_id: 1, at: "", ...e });
  test("resultado, -ab e anomalia invalidam as rotas /api/2t; o batimento não", () => {
    const n = { tipo: "doist", rota: "ufs" } as const;
    expect(eventoAfeta(ev({}), n)).toBe(true);
    expect(eventoAfeta(ev({ kind: "ab", cargo: 0 }), n)).toBe(true);
    expect(eventoAfeta(ev({ kind: "anomalia" }), n)).toBe(true);
    expect(eventoAfeta(ev({ kind: "estado" }), n)).toBe(false);
    expect(eventoAfeta(ev({ kind: "anomalia" }), { tipo: "estado" })).toBe(false);
  });

  test("o estado só troca quando o conteúdo muda", () => {
    expect(mesmoConteudo({ a: [1, 2] }, { a: [1, 2] })).toBe(true);
    expect(mesmoConteudo({ a: [1, 2] }, { a: [1, 3] })).toBe(false);
    expect(mesmoConteudo(undefined, { a: 1 })).toBe(false);
    expect(mesmoConteudo(null, null)).toBe(true);
    const circular: Record<string, unknown> = {};
    circular.eu = circular;
    expect(mesmoConteudo(circular, { eu: 1 })).toBe(false);
  });

  test("rotas do 2º turno esperam 4 s entre buscas; as demais, 1 s", () => {
    expect(intervaloDe({ tipo: "doist", rota: "pausas" })).toBe(4000);
    expect(intervaloDe({ tipo: "estado" })).toBe(1000);
  });
});

describe("parâmetros do ensaio no hash", () => {
  test("padrão é o 2º turno sem falhas", () => {
    expect(lerParamsMock("#mock=1")).toEqual({ turno: 2, inicioMin: null, falhas: {}, sem1t: false, congelar: false });
    expect(lerParamsMock("mock=1&turno=1").turno).toBe(1);
  });

  test("t0, falhas por rota e modo, evolução nas duas rotas e sem1t", () => {
    const p = lerParamsMock("#mock=1&t0=150&falha=paralela,ufs:pendente,evolucao:erro,paralela:fonte,lixo,secoes:xyz&sem1t=1");
    expect(p.inicioMin).toBe(150);
    expect(p.sem1t).toBe(true);
    expect(p.falhas).toEqual({ paralela: "fonte", ufs: "pendente", "evolucao-regiao": "erro", "evolucao-uf": "erro", secoes: "erro" });
    expect(lerParamsMock("t0=abc").inicioMin).toBeNull();
    expect(lerParamsMock("sem1t=0").sem1t).toBe(false);
    expect(lerParamsMock("congelar=1").congelar).toBe(true);
    expect(lerParamsMock("congelar=0").congelar).toBe(false);
  });
});

describe("mock do 2º turno", () => {
  const mockEm = (min: number, opcoes: Parameters<typeof criarMock>[0] extends infer O ? Partial<O> : never = {}) =>
    criarMock({ speed: 1, turno: 2, inicioMin: min, agoraReal: () => 0, ...opcoes });

  test("config de 2º turno, duelo de duas candidaturas e governador só nas seis UFs", async () => {
    const m = mockEm(60);
    const c = await m.config();
    expect(c.turno).toBe(2);
    expect(c.eleicoes).toEqual({ federal: 6258, estadual: 6260 });
    const r = await m.resultado({ ele: 6258, cargo: 1, abr: "br" });
    expect(r.cand.map(x => x.n).sort()).toEqual(["13", "22"]);
    expect(r.cand.reduce((s, x) => s + x.pvapn, 0)).toBeCloseTo(100, 5);
    const g = await m.resultado({ ele: 6260, cargo: 3, abr: "ac" });
    expect(g.cand).toHaveLength(2);
    await expect(m.resultado({ ele: 6260, cargo: 3, abr: "sp" })).rejects.toThrow();
    await expect(m.resultado({ ele: 6260, cargo: 3, abr: "br" })).rejects.toThrow();
    const mapa = await m.mapa({ ele: 6260, cargo: 3, nivel: "uf", pai: "br" });
    expect(mapa.unidades.map(u => u.cd.toUpperCase()).sort()).toEqual(Object.keys(GOVERNADORES_2T).sort());
  });

  test("relógio congelado devolve exatamente a mesma resposta a cada leitura", async () => {
    let real = 0;
    const m = criarMock({ speed: 60, turno: 2, inicioMin: 90, congelar: true, agoraReal: () => real });
    const a = await m.doisT("ufs");
    real = 5_000;
    expect(await m.doisT("ufs")).toEqual(a);
    expect(mesmoConteudo(await m.anomalias(), await m.anomalias())).toBe(true);
  });

  test("é determinístico", async () => {
    const a = await mockEm(90).doisT("regioes");
    const b = await mockEm(90).doisT("regioes");
    expect(a).toEqual(b);
    const u1 = await mockEm(90).doisT("ufs");
    const u2 = await mockEm(90).doisT("ufs");
    expect(u1).toEqual(u2);
  });

  test("regiões: seis agregados que somam o Brasil, com a régua do 1º turno", async () => {
    const r = await mockEm(100).doisT("regioes");
    if (r.situacao !== "ok") throw new Error("esperava ok");
    expect(r.dados.regioes.map(x => x.sigla)).toEqual(["N", "NE", "CO", "SE", "S", "ZZ"]);
    expect(r.dados.regioes.reduce((s, x) => s + x.st, 0)).toBe(r.dados.brasil.st);
    expect(r.dados.regioes.reduce((s, x) => s + x.ts, 0)).toBe(r.dados.brasil.ts);
    expect(r.dados.referencia_1t).toBe(true);
    expect(r.dados.brasil.ref_1t).not.toBeNull();
    const nacional = r.dados.brasil;
    const soma = Object.values(nacional.votos).reduce((s, v) => s + v.pvapn, 0);
    expect(soma).toBeCloseTo(100, 4);
  });

  test("UFs: 27 mais o exterior, das mais lentas e com paradas nas janelas de pausa", async () => {
    const r = await mockEm(85).doisT("ufs");
    if (r.situacao !== "ok") throw new Error("esperava ok");
    expect(r.dados.ufs).toHaveLength(28);
    const psts = r.dados.ufs.map(u => u.pst);
    expect([...psts].sort((a, b) => a - b)).toEqual(psts);
    expect(r.dados.ufs.find(u => u.uf === "MA")?.parada).toBe(true);
    expect(r.dados.ufs.find(u => u.uf === "SP")?.parada).toBe(false);
    expect(r.dados.ufs.find(u => u.uf === "PA")?.ref_1t?.atraso_min).toBe(32);
    const cedo = await mockEm(30).doisT("ufs");
    if (cedo.situacao !== "ok") throw new Error("esperava ok");
    expect(cedo.dados.ufs.some(u => u.parada)).toBe(false);
  });

  test("sem a régua do 1º turno nada vem com ref_1t e as telas ainda recebem dados", async () => {
    const m = mockEm(100, { sem1t: true });
    const [rg, uf, ab, ev, se, es] = await Promise.all([m.doisT("regioes"), m.doisT("ufs"), m.doisT("abstencao"), m.doisT("evolucao-regiao"), m.doisT("secoes"), m.doisT("estaduais")]);
    if (rg.situacao !== "ok" || uf.situacao !== "ok" || ab.situacao !== "ok" || ev.situacao !== "ok" || se.situacao !== "ok" || es.situacao !== "ok") throw new Error("esperava ok");
    expect(rg.dados.referencia_1t).toBe(false);
    expect(rg.dados.regioes.every(r => r.ref_1t === null)).toBe(true);
    expect(uf.dados.ufs.every(u => u.ref_1t === null)).toBe(true);
    expect(ab.dados.brasil.delta_pp).toBeNull();
    expect(ab.dados.destaques.subiu).toEqual([]);
    expect(ev.dados.referencia_1t).toBeNull();
    expect(se.dados.brasil.ref_1t).toBeNull();
    expect(es.dados.ufs.every(u => u.ref_1t === null)).toBe(true);
  });

  test("falhas simuladas: erro, pendente e erro dentro dos dados da paralela", async () => {
    const m = mockEm(100, { falhas: { paralela: "erro", ufs: "pendente", secoes: "fonte" } });
    expect(await m.doisT("paralela")).toEqual({ situacao: "erro", mensagem: "falha simulada no ensaio" });
    expect(await m.doisT("ufs")).toEqual({ situacao: "pendente" });
    expect((await m.doisT("regioes")).situacao).toBe("ok");
    const f = mockEm(100, { falhas: { paralela: "fonte" } });
    const r = await f.doisT("paralela");
    expect(r.situacao === "ok" && r.dados.erro).toBeTruthy();
  });

  test("estaduais: seis duelos na ordem AC AM DF ES RN TO", async () => {
    const r = await mockEm(120).doisT("estaduais");
    if (r.situacao !== "ok") throw new Error("esperava ok");
    expect(r.dados.ufs.map(u => u.uf)).toEqual(["AC", "AM", "DF", "ES", "RN", "TO"]);
    expect(r.dados.ufs.every(u => u.cand.length === 2)).toBe(true);
  });

  test("evolução: candidatos em ordem de urna, séries do Brasil e das regiões e do 1º turno", async () => {
    const r = await mockEm(90).doisT("evolucao-regiao");
    if (r.situacao !== "ok") throw new Error("esperava ok");
    expect(r.dados.candidatos.map(c => c.n)).toEqual(["13", "22"]);
    expect(Object.keys(r.dados.series).sort()).toEqual(["BR", "CO", "N", "NE", "S", "SE", "ZZ"]);
    const br = r.dados.series.BR ?? [];
    expect(br.length).toBeGreaterThan(10);
    expect(br[br.length - 1]?.pst).toBeGreaterThan(20);
    const comVoto = br.filter(p => p.a !== null && p.b !== null);
    expect(comVoto.length).toBeGreaterThan(5);
    for (const p of comVoto) expect((p.a ?? 0) + (p.b ?? 0)).toBeCloseTo(100, 1);
    expect(r.dados.referencia_1t?.BR?.length).toBe(br.length);
    const uf = await mockEm(90).doisT("evolucao-uf");
    expect(uf.situacao === "ok" && Object.keys(uf.dados.series)).toHaveLength(29);
  });

  test("pausas: janelas do cronograma, histórico e pausa em curso", async () => {
    const dentro = await mockEm(42).doisT("pausas");
    if (dentro.situacao !== "ok") throw new Error("esperava ok");
    expect(dentro.dados.nacional.pausa_atual?.minutos).toBeCloseTo(4, 1);
    expect(dentro.dados.nacional.historico).toHaveLength(0);
    const depois = await mockEm(140).doisT("pausas");
    if (depois.situacao !== "ok") throw new Error("esperava ok");
    expect(depois.dados.nacional.historico).toHaveLength(2);
    expect(depois.dados.nacional.pausa_atual).toBeNull();
    expect(depois.dados.referencia_1t.pausa_geral).toEqual({ de: "19:32", ate: "20:02", minutos: 29.6 });
    expect(emPausaNacionalMin(40)).toBe(true);
    expect(emPausaNacionalMin(50)).toBe(false);
    expect(PAUSAS_NACIONAL.every(([d, a]) => a > d)).toBe(true);
  });

  test("lotes do arquivo nacional não ganham versão durante a pausa", async () => {
    const m = mockEm(60);
    const l = await m.lotes({ ele: 6258, cargo: 1, abr: "br" });
    const minutos = l.lotes.map(x => (Date.parse(x.capturado_em) - Date.parse("2026-10-25T20:00:00Z")) / MIN);
    expect(minutos.some(x => x > 38.5 && x < 46)).toBe(false);
    expect(minutos.some(x => x > 20 && x < 38)).toBe(true);
  });

  test("paralela cresce com o tempo e traz uma divergência depois dos 95 minutos", async () => {
    const cedo = await mockEm(70).doisT("paralela");
    const tarde = await mockEm(130).doisT("paralela");
    if (cedo.situacao !== "ok" || tarde.situacao !== "ok") throw new Error("esperava ok");
    expect(tarde.dados.recebidos.bus).toBeGreaterThan(cedo.dados.recebidos.bus);
    expect(tarde.dados.conferencia.divergentes).toBe(1);
    expect(tarde.dados.divergencias).toHaveLength(1);
    expect(cedo.dados.conferencia.divergentes).toBe(0);
    const antes = await mockEm(30).doisT("paralela");
    expect(antes.situacao === "ok" && antes.dados.recebidos.bus).toBe(0);
  });

  test("seções: cadeia completa, tardias só depois de 18:00 e a totalização do município", async () => {
    const r = await mockEm(200).doisT("secoes");
    if (r.situacao !== "ok") throw new Error("esperava ok");
    expect(r.dados.totais.alvo).toBeGreaterThan(0);
    expect(r.dados.totais.recebidas + r.dados.totais.pendentes).toBe(r.dados.totais.alvo);
    expect(r.dados.brasil.lag_recebimento_totalizacao_min?.p50).not.toBeNull();
    expect(r.dados.tardias.every(t => t.encerramento_hhmm >= "18:00")).toBe(true);
    expect(r.dados.ultimas.length).toBeLessThanOrEqual(20);
  });

  test("abstenção: base em municípios fechados e destaques com |Δ| de 3 pontos ou mais", async () => {
    const r = await mockEm(200).doisT("abstencao");
    if (r.situacao !== "ok") throw new Error("esperava ok");
    expect(r.dados.base).toBe("municipios_fechados");
    expect(r.dados.regioes).toHaveLength(5);
    expect(r.dados.ufs).toHaveLength(27);
    for (const m of r.dados.destaques.subiu) expect(m.delta_pp).toBeGreaterThanOrEqual(3);
    for (const m of r.dados.destaques.caiu) expect(m.delta_pp).toBeLessThanOrEqual(-3);
    const antes = await mockEm(2).doisT("abstencao");
    expect(antes.situacao === "ok" && antes.dados.brasil.pa_2t).toBeNull();
  });

  test("anomalias do 2º turno trazem as categorias novas, sem travessão no texto", async () => {
    const a = await mockEm(260).anomalias();
    const tipos = new Set(a.map(x => x.tipo));
    for (const t of ["pausa", "atraso", "abstencao", "paralela", "divergencia"] as const) expect(tipos.has(t)).toBe(true);
    expect(a.every(x => !x.texto.includes("—"))).toBe(true);
    expect(a.find(x => x.tipo === "divergencia")?.severidade).toBe("error");
    expect(a.map(x => x.at)).toEqual([...a.map(x => x.at)].sort().reverse());
  });

  test("1º turno: o mock antigo segue com 12 candidaturas e as rotas novas ficam pendentes", async () => {
    const m = criarMock({ speed: 1, inicioMin: 100 });
    expect((await m.config()).turno).toBe(1);
    expect((await m.resultado({ ele: 6257, cargo: 1, abr: "br" })).cand).toHaveLength(12);
    expect(await m.doisT("regioes")).toEqual({ situacao: "pendente" });
  });

  test("o deslocamento do 1º turno por UF é fixo", () => {
    expect(shiftMin("PA")).toBe(32);
    expect(shiftMin("SP")).toBe(shiftMin("SP"));
    expect(Math.abs(shiftMin("RJ"))).toBeLessThan(40);
  });
});
