"""Protege a projeção, ausência de cobertura e contagem territorial sem duplicação."""

import hashlib
import json
import math

import numpy as np
import pytest
from analise_realidade_eleicao.territorio import (
    FONTE,
    OUTPUT,
    classificar,
    mercator,
    pixel,
    somar,
)


def test_pixel_usa_mercator_e_nao_latitude_linear():
    bounds = [[60, -10], [0, 10]]
    meio_lat = math.degrees(2 * math.atan(math.exp(mercator(60) / 2)) - math.pi / 2)
    x, y = pixel(meio_lat, 0, bounds, 100, 100)
    assert x == 50 and y in (49, 50)
    assert pixel(30, 0, bounds, 100, 100)[1] > 55


def test_limites_da_imagem_nao_inventam_classe():
    bounds = [[1, 0], [0, 1]]
    for lat, lon in ((2, 0.5), (0.5, 2), (0, 0.5), (0.5, 1)):
        assert pixel(lat, lon, bounds, 4, 4) is None
    assert pixel(1, 0, bounds, 4, 4) == (0, 0)
    layer = {
        "bounds": bounds,
        "ids": np.array([[0, 2], [3, 4]]),
        "distancias": np.ones((2, 2)),
    }
    assert classificar(layer, 2, 2) == (None, None)
    assert classificar(layer, 0.75, 0.25)[0] == "Sem marcação"
    assert classificar(layer, 0.75, 0.75)[0] == "CV"
    assert classificar(layer, 0.25, 0.25)[0] == "Milícia"


def test_agregacao_usa_votos_e_preserva_grupo_vazio():
    r = somar(
        [
            {"flavio": 90, "lula": 10, "secoes": 1},
            {"flavio": 0, "lula": 10, "secoes": 1},
        ]
    )
    assert r["pct_lula"] == pytest.approx(100 * 20 / 110)
    assert somar([])["pct_lula"] is None


def test_fonte_e_derivados_tem_hashes_conferiveis():
    meta = json.loads((FONTE / "geni_mapa_2024.fonte.json").read_text())
    assert (
        hashlib.sha256((FONTE / "geni_mapa_2024_widget.json").read_bytes()).hexdigest()
        == meta["sha256_widget"]
    )
    assert (
        hashlib.sha256((FONTE / "geni_mapa_leaflet.js").read_bytes()).hexdigest()
        == meta["sha256_renderer"]
    )
    for layer in meta["camadas"]:
        assert (
            hashlib.sha256(
                (FONTE / f'geni_2024_{layer["nome"]}.png').read_bytes()
            ).hexdigest()
            == layer["sha256"]
        )


def test_particao_reconcilia_e_sensibilidade_e_monotona():
    d = json.loads((OUTPUT / "territorio.json").read_text())
    assert len({r["local_id"] for r in d["locais"]}) == len(d["locais"])
    assert all(r["coord_fonte"] == "cadastro" for r in d["locais"])
    for camada in ("controle", "influencia"):
        base = [r for r in d["resumo"] if r["camada"] == camada and r["margem_m"] == 0]
        for field in ("locais", "secoes", "lula", "flavio", "validos"):
            assert sum(r[field] for r in base) == d["total_janela"][field]
        for group in ("ADA", "CV", "Milícia", "TCP"):
            cases = sorted(
                [
                    r
                    for r in d["resumo"]
                    if r["camada"] == camada and r["grupo"] == group
                ],
                key=lambda r: r["margem_m"],
            )
            assert [r["locais"] for r in cases] == sorted(
                [r["locais"] for r in cases], reverse=True
            )
            municipal = [
                r
                for r in d["recortes"]
                if r["camada"] == camada
                and r["nivel"] == "municipio"
                and r["grupo"] == group
            ]
            for field in ("locais", "lula", "flavio"):
                assert sum(r[field] for r in municipal) == cases[0][field]
