"""Clima, bateria e abstenção no 1º turno de 2026: motor, previsão e saídas."""

from __future__ import annotations

import gzip
import json
import re
from pathlib import Path

import numpy as np
import pytest
from clima_1t import coleta, grade, previsao, saidas, variaveis
from clima_1t import estatistica as es

ROOT = Path(__file__).resolve().parents[1]
MAPA = ROOT / "docs/assets/fiscais_mapa/clima"
PREVISAO = MAPA / "previsao.json"
DADOS = ROOT / "docs/assets/clima_1t/dados.json"
CSV = ROOT / "docs/assets/clima_1t/locais.csv.gz"
TRAVESSAO = chr(0x2014)
COLUNAS_CONTRATO = [
    "local_id",
    "cel",
    "chuva_04_10_mm",
    "chuva_votacao_mm",
    "hora_pico_chuva",
    "rajada_04_10_kmh",
    "rajada_votacao_kmh",
    "faixa_chuva",
    "faixa_rajada",
    "urnas",
    "urnas_bateria",
    "urnas_bateria_votacao",
    "abst_pct",
    "abst22_pct",
    "dif_abst_pp",
]


# --- faixas ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("mm", "faixa"),
    [
        (0.0, "seca"),
        (0.04, "seca"),
        (0.1, "fraca"),
        (5.0, "fraca"),
        (5.1, "moderada"),
        (20.0, "moderada"),
        (20.1, "forte"),
        (50.0, "forte"),
        (50.1, "muito_forte"),
        (None, None),
        (float("nan"), None),
    ],
)
def test_faixa_chuva(mm, faixa):
    assert variaveis.faixa_chuva(mm) == faixa


@pytest.mark.parametrize(
    ("kmh", "faixa"),
    [
        (0.0, "ate_40"),
        (40.0, "ate_40"),
        (40.1, "40_60"),
        (60.0, "40_60"),
        (60.1, "60_80"),
        (80.0, "60_80"),
        (80.1, "acima_80"),
        (None, None),
    ],
)
def test_faixa_rajada(kmh, faixa):
    assert variaveis.faixa_rajada(kmh) == faixa


def test_faixas_tem_rotulo():
    assert set(variaveis.ROTULO_CHUVA) == set(variaveis.FAIXAS_CHUVA)
    assert set(variaveis.ROTULO_RAJADA) == set(variaveis.FAIXAS_RAJADA)


# --- chave da célula ------------------------------------------------------------------


def test_chave_sao_paulo():
    assert grade.chave(-23.55, -46.63, 0.25) == "-23.75,-46.75"
    assert grade.chave(-23.55, -46.63, 0.5) == "-24.0,-47.0"
    assert grade.indice(-23.55, -46.63, 0.25) == (-95, -187)
    assert grade.centro("-23.75,-46.75", 0.25) == (-23.625, -46.625)
    assert grade.centro("-24.0,-47.0", 0.5) == (-23.75, -46.75)


@pytest.mark.parametrize(
    ("lat", "lon", "passo", "chave"),
    [
        (-23.5, -46.5, 0.5, "-23.5,-46.5"),  # canto exato fica na própria célula
        (-23.5, -46.5, 0.25, "-23.50,-46.50"),
        (2.8, -60.7, 0.5, "2.5,-61.0"),  # hemisfério norte
        (0.1, -50.1, 0.5, "0.0,-50.5"),  # sem "-0.0"
        (-0.1, -50.1, 0.5, "-0.5,-50.5"),
        (-3.73, -38.52, 0.25, "-3.75,-38.75"),
    ],
)
def test_chave_casos(lat, lon, passo, chave):
    assert grade.chave(lat, lon, passo) == chave


def test_chave_previsao_tem_uma_casa():
    assert re.fullmatch(r"-?\d+\.\d,-?\d+\.\d", grade.chave(-9.97, -67.81, 0.5))


def test_territorio():
    assert grade.no_territorio(-23.5, -46.6)
    assert not grade.no_territorio(48.27, 17.47)
    assert not grade.no_territorio(None, -46.6)
    assert not grade.no_territorio(float("nan"), -46.6)


def test_local_id():
    assert grade.local_id("AC", "01074", 4, 2291) == "AC-01074-4-2291"


# --- regra de risco -------------------------------------------------------------------


@pytest.mark.parametrize(
    ("chuva", "prob", "rajada", "nivel"),
    [
        (30.0, 0, 0, "alto"),
        (0, 0, 70.0, "alto"),
        (15.0, 80, 0, "alto"),
        (14.9, 80, 0, "medio"),
        (15.0, 79, 0, "medio"),
        (10.0, 0, 0, "medio"),
        (0, 0, 50.0, "medio"),
        (0, 60, 0, "medio"),
        (9.9, 59, 49.9, "baixo"),
        (0, None, None, "baixo"),
        (None, None, None, "sem_dado"),
        (None, 90, None, "medio"),
    ],
)
def test_regra_de_risco(chuva, prob, rajada, nivel):
    assert previsao.risco(chuva, prob, rajada) == nivel


def test_celula_da_previsao_usa_o_dia_alvo():
    datas = [f"2026-10-{d}" for d in range(19, 27)]
    chuva = [0.0] * 8
    chuva[datas.index("2026-10-25")] = 31.0
    resp = {
        "daily": {
            "time": datas,
            "precipitation_sum": chuva,
            "precipitation_probability_max": [10] * 8,
            "wind_gusts_10m_max": [20.0] * 8,
            "weather_code": [3] * 8,
        }
    }
    cel = previsao._celula(resp)
    assert cel["risco"] == "sem_dado"  # o total diário não substitui horas ausentes
    assert cel["chuva_mm"] is None
    assert cel["diario"]["chuva_mm"] == 31.0
    assert len(cel["serie"]) == 8
    assert set(cel["serie"][0]) == {"data", "chuva_mm", "prob_pct", "rajada_kmh"}
    resp["daily"]["time"] = [f"2026-10-{d}" for d in range(10, 18)]
    assert previsao._celula(resp)["risco"] == "sem_dado"


# --- horas de votação e fuso ----------------------------------------------------------


def _serie(**chuva):
    s = [0.0] * 24
    for h, v in chuva.items():
        s[int(h[1:])] = v
    return s


def test_soma_da_janela_de_votacao_usa_horas_de_brasilia():
    # hora H soma de H-1 a H; janela 7h às 18h de Brasília = horas 8 a 18
    s = _serie(h7=5.0, h8=1.0, h12=2.0, h18=3.0, h19=7.0)
    assert variaveis.soma_janela(s, *variaveis.JANELA_BRASILIA) == 6.0
    assert variaveis.soma_janela(s, *variaveis.JANELA_ESTRITA) == 2.0
    assert variaveis.maximo_janela(s, *variaveis.JANELA_BRASILIA) == 3.0
    assert variaveis.soma_janela([None] * 24, 7, 18) is None


def test_janela_local_por_fuso():
    # votação unificada às 8h de Brasília: no Acre (fuso 2) a janela local é 5h às 16h
    assert variaveis.janela_local(0) == (7, 18)
    assert variaveis.janela_local(1) == (6, 17)
    assert variaveis.janela_local(2) == (5, 16)
    assert variaveis.janela_local(-1) == (8, 19)


def test_pico_em_hora_local():
    s = _serie(h10=1.0, h15=4.0, h16=4.0)
    pico = variaveis.pico_brasilia(s, *variaveis.JANELA_BRASILIA)
    assert pico == 14  # intervalo das 14h às 15h de Brasília; empate fica no primeiro
    assert variaveis.hora_local(pico, 0) == 14
    assert variaveis.hora_local(pico, 1) == 13
    assert variaveis.hora_local(pico, 2) == 12
    assert variaveis.hora_local(pico, -1) == 15
    assert variaveis.pico_brasilia([0.0] * 24, 7, 18) is None
    assert variaveis.hora_local(None, 2) is None


def test_clima_por_celula():
    horas = [0.0] * 24
    horas[9], horas[13] = 2.0, 6.0
    rajadas = [10.0] * 24
    rajadas[17] = 65.0
    doc = {
        "dias": ["2026-10-02", "2026-10-03", "2026-10-04", "2026-10-05"],
        "horas_04_10": [f"{h:02d}" for h in range(24)],
        "formato": {
            "diarias": coleta.DIARIAS,
            "horarias": coleta.HORARIAS,
        },
        "celulas": {
            "-23.75,-46.75": [
                [-23.65, -46.61, 768.0],
                [
                    [0.0, 3.0, 25.0, 60.0],
                    [0, 2, 5, 9],
                    [30.0, 31.0, 70.0, 40.0],
                    [20, 21, 22, 23],
                ],
                [horas, rajadas],
            ]
        },
    }
    df = variaveis.clima_por_celula(doc)
    r = df.loc["-23.75,-46.75"].to_dict()
    assert r["chuva_04_10_mm"] == 25.0
    assert r["chuva_03_10_mm"] == 3.0
    assert r["chuva_02a05_max_mm"] == 60.0
    assert r["chuva_votacao_mm"] == 8.0
    assert r["rajada_votacao_kmh"] == 65.0
    assert r["pico_brasilia"] == 12
    assert r["faixa_chuva"] == "forte"
    assert r["faixa_chuva_votacao"] == "moderada"
    assert r["faixa_rajada"] == "60_80"


# --- estatística ----------------------------------------------------------------------


def test_bootstrap_de_celulas_soma_e_ponto():
    boot = es.BootCelulas(n_celulas=5, reps=30, seed=1, bloco=7)
    blocos = list(boot.blocos())
    w = np.concatenate(blocos)
    assert w.shape == (30, 5)
    assert np.all(w.sum(axis=1) == 5)
    cel = np.array([0, 0, 1, 2, 3, 4, 4])
    grupo = np.array([0, 1, 0, 1, 0, 1, -1])
    val = np.column_stack([np.arange(7, dtype=float), np.ones(7)])
    ponto, reps = es.aplicar(boot, cel, grupo, val, 2, lambda s: s[..., 0])
    assert ponto.tolist() == [0 + 2 + 4, 1 + 3 + 5]
    assert reps.shape == (30, 2)


def test_diferenca_dentro_do_estrato():
    # dois estratos, grupos ref (0) e 1; taxa e peso por (réplica, estrato, grupo)
    taxa = np.array([[[0.20, 0.25], [0.10, 0.10]]])
    peso = np.array([[[100.0, 300.0], [50.0, 100.0]]])
    d = es.dif_dentro(taxa, peso, 0)
    assert d[0, 0] == 0.0
    assert d[0, 1] == pytest.approx((0.05 * 300 + 0.0 * 100) / 400)
    masc = np.array([[True, True], [True, False]])
    assert es.dif_dentro(taxa, peso, 0, masc)[0, 1] == pytest.approx(0.05)


def test_ic_sem_menos_zero():
    r = es.ic(-0.00001, np.array([-0.001, 0.0, 0.001] * 10), 100.0, 2)
    assert str(r["valor"]) == "0.0"


# --- cliente da Open-Meteo ------------------------------------------------------------


class _Falso:
    def __init__(self, respostas):
        self.respostas = list(respostas)
        self.pedidos = []
        self.chamadas = 0

    def get(self, base, params, locais=1):
        self.pedidos.append(params)
        r = self.respostas.pop(0)
        if isinstance(r, Exception):
            raise r
        return r

    def avisar(self, texto):
        self.ultimo_aviso = texto


def test_lotes_em_ordem_e_parada_na_cota_do_dia():
    cel = {"a": (-10.0, -50.0), "b": (-11.0, -51.0), "c": (-12.0, -52.0)}
    respostas = [
        [
            {"latitude": -10.02, "longitude": -50.01},
            {"latitude": -11.0, "longitude": -51.0},
        ],
        coleta.CotaDiariaEsgotada("Daily API request limit exceeded"),
    ]
    gravadas = {}
    falso = _Falso(respostas)
    estado = coleta.baixar_lotes(
        falso,
        "http://x",
        {},
        cel,
        2,
        lambda c, it, url, pos: gravadas.setdefault(c, pos),
    )
    assert gravadas == {"a": 0, "b": 1}
    assert estado["baixadas"] == 2
    assert "cota diária" in estado["parada"]
    assert falso.pedidos[0]["latitude"] == "-10,-11"


def test_lote_recusa_resposta_fora_do_ponto():
    cel = {"a": (-10.0, -50.0)}
    falso = _Falso([[{"latitude": 5.0, "longitude": -50.0}]])
    with pytest.raises(RuntimeError):
        coleta.baixar_lotes(falso, "http://x", {}, cel, 1, lambda *a: None)


def test_lote_pula_o_que_ja_foi_baixado():
    cel = {"a": (-10.0, -50.0), "b": (-11.0, -51.0)}
    falso = _Falso([[{"latitude": -11.0, "longitude": -51.0}]])
    estado = coleta.baixar_lotes(
        falso, "http://x", {}, cel, 5, lambda *a: None, pular=["a"]
    )
    assert estado["baixadas"] == 1
    assert falso.pedidos[0]["latitude"] == "-11"


# --- saídas ---------------------------------------------------------------------------


def _uf_jsons():
    return sorted(
        p
        for p in MAPA.glob("*.json")
        if p.name not in ("previsao.json", "observado_2t.json")
    )


@pytest.mark.skipif(not MAPA.exists(), reason="saídas do mapa ainda não geradas")
def test_esquema_dos_arquivos_do_mapa():
    arquivos = _uf_jsons()
    assert len(arquivos) == 27
    for arq in arquivos:
        d = json.loads(arq.read_text(encoding="utf-8"))
        assert {"gerado_em", "fonte", "celula_graus", "colunas", "linhas"} <= set(d)
        assert d["celula_graus"] == 0.25
        assert d["colunas"][: len(COLUNAS_CONTRATO)] == COLUNAS_CONTRATO
        n = len(d["colunas"])
        ic = d["colunas"].index("cel")
        il = d["colunas"].index("local_id")
        ifx = d["colunas"].index("faixa_chuva")
        ich = d["colunas"].index("chuva_04_10_mm")
        for linha in d["linhas"]:
            assert len(linha) == n
            assert linha[il].startswith(arq.stem + "-")
            if linha[ic] is not None:
                assert re.fullmatch(r"-?\d+\.\d\d,-?\d+\.\d\d", linha[ic])
            if linha[ich] is not None:
                assert linha[ic] is not None
                assert linha[ifx] == variaveis.faixa_chuva(linha[ich])


@pytest.mark.skipif(not PREVISAO.exists(), reason="previsão ainda não gerada")
def test_esquema_da_previsao():
    d = json.loads(PREVISAO.read_text(encoding="utf-8"))
    assert {
        "gerado_em",
        "alvo",
        "fonte",
        "celula_graus",
        "regra_risco",
        "dias",
        "celulas",
        "resumo",
    } <= set(d)
    assert d["alvo"] == "2026-10-25"
    assert d["celula_graus"] == 0.5
    assert {"por_uf", "cidades_risco_alto"} <= set(d["resumo"])
    assert len(d["resumo"]["cidades_risco_alto"]) <= 30
    for chave, cel in d["celulas"].items():
        assert re.fullmatch(r"-?\d+\.\d,-?\d+\.\d", chave)
        assert {
            "chuva_mm",
            "prob_pct",
            "rajada_kmh",
            "codigo_wmo",
            "risco",
            "serie",
        } <= set(cel)
        assert cel["risco"] == previsao.risco(
            cel["chuva_mm"], cel["prob_pct"], cel["rajada_kmh"]
        )
        for s in cel["serie"]:
            assert set(s) == {"data", "chuva_mm", "prob_pct", "rajada_kmh"}


@pytest.mark.skipif(not DADOS.exists(), reason="payload ainda não gerado")
def test_esquema_do_payload():
    d = json.loads(DADOS.read_text(encoding="utf-8"))
    for chave in (
        "bateria_x_chuva",
        "abstencao_x_chuva",
        "abstencao_x_bateria",
        "cadeia_completa",
        "locais_curiosos",
        "mapa_resumo",
        "previsao_25_10",
        "limites",
        "controles",
        "fontes",
    ):
        assert chave in d
    for lista in d["locais_curiosos"].values():
        for item in lista.get("itens", []):
            assert (
                item["mapa"]
                == f"fiscais_mapa.html#uf={item['uf']}&l={item['local_id']}"
            )
        assert len(lista.get("itens", [])) <= 30
    assert "_interno" not in d


@pytest.mark.skipif(not CSV.exists(), reason="CSV ainda não gerado")
def test_csv_dos_locais():
    with gzip.open(CSV, "rt", encoding="utf-8") as f:
        cabecalho = f.readline().strip().split(",")
    assert cabecalho == saidas.COLUNAS_CSV


def test_sem_travessao_nos_json_publicos():
    arquivos = [*_uf_jsons(), PREVISAO, DADOS]
    existentes = [a for a in arquivos if a.exists()]
    for arq in existentes:
        assert TRAVESSAO not in arq.read_text(encoding="utf-8"), arq.name
    for mod in ("texto", "analises", "curiosos", "previsao", "saidas", "variaveis"):
        fonte = (ROOT / "scripts/clima_1t" / f"{mod}.py").read_text(encoding="utf-8")
        assert TRAVESSAO not in fonte, mod


def test_sem_a_palavra_proibida_nos_textos():
    proibida = "fr" + "aude"
    for mod in ("texto", "texto_md", "analises", "curiosos", "previsao", "saidas"):
        fonte = (ROOT / "scripts/clima_1t" / f"{mod}.py").read_text(encoding="utf-8")
        assert proibida not in fonte.lower(), mod


def test_modulos_abaixo_de_mil_linhas():
    for arq in (ROOT / "scripts/clima_1t").glob("*.py"):
        assert len(arq.read_text(encoding="utf-8").splitlines()) < 1000, arq.name
