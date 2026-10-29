"""Fronteiras de segundos, fusos municipais e conservação dos agregados."""

import json

import pytest
from apuracao_2t_2026.encerramento_dados import (
    AM_ACRE,
    CAMPOS,
    CORTES,
    SAIDA,
    deslocamento,
    faixa,
    resumir,
    segundo_brt,
)


@pytest.mark.parametrize(
    ("s", "esperado"),
    [
        (61200, 0),
        (61201, 1),
        (61260, 1),
        (61261, 2),
        (61320, 2),
        (61321, 3),
        (68400, 19),
        (68401, 20),
    ],
)
def test_limites_sem_arredondamento(s, esperado):
    assert faixa(s) == esperado


@pytest.mark.parametrize(
    ("uf", "mun", "local"),
    [
        ("SP", "71072", "17:02:00"),
        ("AC", "01392", "15:02:00"),
        ("AM", "02550", "16:02:00"),
        ("AM", "98477", "15:02:00"),
        ("PE", "30015", "18:02:00"),
        ("MS", "90514", "16:02:00"),
    ],
)
def test_fusos_mesmo_instante(uf, mun, local):
    assert segundo_brt(f"2026-10-25 {local}", uf, mun) == 61320


def test_exterior_e_datas_invalidas():
    assert segundo_brt("2026-10-25 17:02:00", "ZZ", "00001") is None
    assert segundo_brt("2026-10-24 17:02:00", "SP", "71072") is None
    assert segundo_brt("inválido", "SP", "71072") is None
    assert segundo_brt(None, "SP", "71072") is None
    assert len(AM_ACRE) == 11
    assert all(deslocamento("AM", mun) == 2 for mun in AM_ACRE)


def test_intervalos_e_acumulado_nao_confundem_votos():
    base = {
        "uf": "SP",
        "mun": "71072",
        "zona": 1,
        "pleito": 3221,
        "id_confere": 1,
        "abertura": "2026-10-25 08:00:01",
        "aptos": 100,
        "comparecimento": 80,
        "brancos": 2,
        "nulos": 3,
    }
    d = resumir(
        [
            dict(base, secao=1, encerramento="2026-10-25 17:02:00", flavio=40, lula=35),
            dict(base, secao=2, encerramento="2026-10-25 17:02:01", flavio=30, lula=45),
        ]
    )
    assert d["linhas"][2]["flavio"] == 40
    assert d["linhas"][3]["flavio"] == 30
    assert d["linhas"][3]["acumulado"]["flavio"] == 70
    assert d["linhas"][2]["encerradas_pct"] == 50
    assert d["linhas"][3]["encerradas_pct"] == 100
    assert d["residuo_comparecimento_menos_votos"] == 0


def test_publicado_conserva_particoes():
    d = json.loads((SAIDA / "dados.json").read_text())
    assert d["catalogo_principais_brasil"] == d["total"]["secoes"] == 497897
    assert d["conferencia_abertura"] == {"municipios": 5571, "divergencias": []}
    assert d["residuo_comparecimento_menos_votos"] == 0
    assert d["linhas"][0]["secoes"] == 0
    assert d["linhas"][2]["encerradas_acumuladas"] == 281948
    assert d["linhas"][10]["encerradas_acumuladas"] == 484541
    assert d["linhas"][-1]["secoes"] == 6336
    for k in CAMPOS:
        assert sum(r[k] for r in d["linhas"]) == d["total"][k]
    for r in d["linhas"]:
        assert r["flavio"] + r["lula"] == r["validos"]
        assert r["encerradas_acumuladas"] + r["restantes"] == d["total"]["secoes"]
        assert sum(u["secoes"] for u in r["ufs"]) == r["secoes"]
        if r["corte_s"] in CORTES:
            assert (
                sum(
                    s["secoes"]
                    for s in d["segundos"]
                    if s["segundo_brt"] <= r["corte_s"]
                )
                == r["encerradas_acumuladas"]
            )
