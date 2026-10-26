"""Chuva de 25/10 por célula: interpolação das estações, fotos do CEMADEN e arquivo público."""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest
from clima_2t import estacoes, observado

ROOT = Path(__file__).resolve().parents[1]
PUBLICO = ROOT / "docs/assets/fiscais_mapa/clima/observado_2t.json"


def _est(lat, lon, dia=None, vot=None, rede="cemaden"):
    return {"rede": rede, "lat": lat, "lon": lon, "dia_mm": dia, "votacao_mm": vot}


def test_interpolacao_inverso_do_quadrado():
    centro = (-23.625, -46.625)
    perto = _est(-23.625, -46.6, dia=40.0)
    longe = _est(-23.625, -46.4, dia=10.0)
    r = observado.interpolar(centro, [perto, longe], "dia_mm")
    d1 = observado.km(*centro, perto["lat"], perto["lon"])
    d2 = observado.km(*centro, longe["lat"], longe["lon"])
    esperado = (40 / d1**2 + 10 / d2**2) / (1 / d1**2 + 1 / d2**2)
    assert r["n"] == 2
    assert r["mm"] == pytest.approx(round(esperado, 1))
    assert r["dmin"] == pytest.approx(round(d1, 1))
    assert r["rede"] == "cemaden"


def test_raio_de_50_km_e_campo_ausente():
    centro = (-10.125, -50.125)
    fora = _est(-10.125, -49.6, dia=30.0)  # cerca de 57 km
    sem_campo = _est(-10.13, -50.13, dia=None, vot=5.0)
    assert observado.km(*centro, fora["lat"], fora["lon"]) > 50
    assert observado.interpolar(centro, [fora, sem_campo], "dia_mm") is None
    assert observado.interpolar(centro, [sem_campo], "votacao_mm")["mm"] == 5.0


def test_redes_misturadas_viram_ambos():
    centro = (0.125, -51.125)
    lista = [_est(0.13, -51.12, dia=1.0), _est(0.12, -51.13, dia=3.0, rede="inmet")]
    assert observado.interpolar(centro, lista, "dia_mm")["rede"] == "ambos"


def test_traco_da_tabela_do_cemaden_e_zero():
    assert observado._num("-") == 0.0
    assert observado._num(12.5) == 12.5
    assert observado._num(None) is None
    assert observado._num(float("nan")) is None


def test_janela_do_modelo_usa_horas_8_a_18():
    m = {"horas": [f"{h:02d}" for h in range(24)], "chuva": [1.0] * 24}
    assert observado._janela_modelo(m, "chuva", sum) == 11.0
    m["chuva"][12] = None
    assert observado._janela_modelo(m, "chuva", sum) is None


def test_horas_pedidas_ao_cemaden_alcancam_a_votacao():
    from datetime import datetime, timezone

    agora = datetime(2026, 10, 26, 16, tzinfo=timezone.utc)
    h = estacoes.horas_pedidas(agora)
    assert agora.timestamp() - h * 3600 <= estacoes.INICIO_UTC.timestamp()
    with pytest.raises(RuntimeError):
        estacoes.horas_pedidas(datetime(2026, 10, 30, tzinfo=timezone.utc))


@pytest.mark.skipif(not PUBLICO.exists(), reason="observado_2t.json ainda não gerado")
def test_arquivo_publico():
    d = json.loads(PUBLICO.read_text(encoding="utf-8"))
    assert d["celula_graus"] == 0.25
    assert d["gerado_em"]
    cols = d["colunas"]
    i_f = cols.index("fonte")
    fontes = {v[i_f] for v in d["celulas"].values()}
    assert fontes <= {"cemaden", "inmet", "ambos", "ifs_provisorio", "era5", None}
    for k, v in d["celulas"].items():
        a, b = (float(x) for x in k.split(","))
        assert math.isclose(a * 4, round(a * 4)) and math.isclose(b * 4, round(b * 4))
        r = dict(zip(cols, v, strict=True))
        if r["fonte"] in ("cemaden", "inmet", "ambos"):
            assert r["n_estacoes"] >= 1 and 0 <= r["distancia_min_km"] <= 50
        if r["chuva_forte_dia"] is not None:
            assert r["chuva_forte_dia"] == int(r["chuva_dia_mm"] >= 20)
    assert chr(0x2014) not in PUBLICO.read_text(encoding="utf-8")
