"""Fronteiras temporais, fusos e propagação de faltantes na previsão horária."""

import json
from copy import deepcopy

import pytest
from clima_1t import horaria, previsao
from clima_1t.pagina.util import PREVISAO_JSON


@pytest.fixture
def resposta():
    return {
        "hourly": {
            "time": [f"2026-10-25T{h:02d}:00" for h in range(24)],
            "precipitation": list(range(24)),
            "precipitation_probability": [80] * 24,
            "wind_gusts_10m": [30] * 24,
        }
    }


def test_janela_soma_nove_intervalos_sem_pegar_antes_ou_depois(resposta):
    cel = previsao._celula(resposta)
    assert cel["chuva_mm"] == sum(range(9, 18))
    periodos = cel["periodos"]
    assert periodos["manha"]["chuva_mm"] == 9 + 10 + 11 + 12
    assert periodos["almoco"]["chuva_mm"] == 13 + 14
    assert periodos["transicao"]["chuva_mm"] == 15
    assert periodos["tarde"]["chuva_mm"] == 16 + 17
    assert (
        sum(p["chuva_mm"] for k, p in periodos.items() if k != "votacao")
        == cel["chuva_mm"]
    )
    assert cel["prob_pct"] == 80  # não soma probabilidades
    assert cel["horas"][0]["inicio_brasilia"].endswith("08:00:00-03:00")
    for h in [0, 8, 18, 23]:
        resposta["hourly"]["precipitation"][h] = 9999
    assert previsao._celula(resposta)["chuva_mm"] == cel["chuva_mm"]


@pytest.mark.parametrize("campo", list(horaria.VARIAVEIS.values()))
def test_falta_uma_hora_invalida_somente_janelas_afetadas(resposta, campo):
    resposta["hourly"][campo][13] = None
    cel = previsao._celula(resposta)
    assert cel["risco"] == "sem_dado"
    assert not cel["periodos"]["almoco"]["completa"]
    assert cel["periodos"]["manha"]["completa"]
    assert cel["periodos"]["tarde"]["completa"]


def test_resposta_de_outro_dia_nao_entra_na_janela(resposta):
    resposta["hourly"]["time"] = [
        t.replace("25T", "26T") for t in resposta["hourly"]["time"]
    ]
    assert previsao._celula(resposta)["risco"] == "sem_dado"


@pytest.mark.parametrize(
    "uf,nome,utc,janela",
    [
        ("AC", "Rio Branco", -5, "06h–15h"),
        ("AM", "São Paulo de Olivença", -5, "06h–15h"),
        ("AM", "Manaus", -4, "07h–16h"),
        ("MS", "Campo Grande", -4, "07h–16h"),
        ("PE", "Fernando de Noronha", -2, "09h–18h"),
        ("PE", "Recife", -3, "08h–17h"),
    ],
)
def test_conversao_de_fusos(uf, nome, utc, janela):
    assert horaria.fuso_local(uf, nome) == utc
    assert horaria.janela_local(8, 17, utc) == janela


def test_resumo_ponderado_nao_soma_probabilidade_nem_imputa_faltantes(resposta):
    a = previsao._celula(resposta)
    b = deepcopy(a)
    b["periodos"]["votacao"]["chuva_mm"] = 0
    indice = {
        "celulas": {
            "a": [["SP", "1", "A", 1, 100]],
            "b": [["SP", "2", "B", 1, 300]],
            "c": [["SP", "3", "C", 1, 100]],
        }
    }
    r = horaria.resumir({"a": a, "b": b}, indice)["votacao"]["grupos"]["SP"]
    assert r["eleitores"] == 500
    assert r["cobertos"] == 400
    assert r["chuva_media_mm"] == a["chuva_mm"] / 4
    assert r["cadastro_chuva_1mm_pct"] == 20


def test_publicacao_horaria_conserva_particao_e_cobertura():
    d = json.loads(PREVISAO_JSON.read_text())
    assert d["versao"] == 2
    assert d["coleta"]["completa"]
    for c in d["celulas"].values():
        assert len(c["horas"]) == 9
        assert c["chuva_mm"] == pytest.approx(
            sum(
                c["periodos"][k]["chuva_mm"] for k in horaria.PERIODOS if k != "votacao"
            )
        )
        assert c["chuva_mm"] <= c["diario"]["chuva_mm"] + 0.05
    r = d["resumo_periodos"]
    assert (
        r["votacao"]["grupos"]["BR"]["cobertos"]
        == r["votacao"]["grupos"]["BR"]["eleitores"]
    )
