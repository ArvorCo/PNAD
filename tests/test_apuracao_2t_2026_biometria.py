"""Bloco "Como o eleitor foi habilitado": identidades e esquema de biometria.json."""

import json
from pathlib import Path

import pytest
from apuracao_2t_2026 import biometria_analise as A
from apuracao_2t_2026 import pagina_cap_secoes as CS

ARQ = (
    Path(__file__).resolve().parents[1]
    / "analysis/apuracao_2t_2026/dados/biometria.json"
)


@pytest.fixture(scope="module")
def B():
    if not ARQ.exists():
        pytest.skip(
            "biometria.json ausente: rode scripts/apuracao-2t-2026-biometria.py"
        )
    return json.loads(ARQ.read_text(encoding="utf-8"))


def test_identidade_nacional(B):
    for turno in ("1t", "2t"):
        t = B["totais"][turno]
        assert t["identidade_fecha"] and t["secoes_identidade_falha"] == 0
        assert t["biometria"] + t["ano_nascimento"] + t["sem_cadastro"] == (
            t["comparecimento_com_categoria"]
        )
        assert t["comparecimento_total"] == (
            t["comparecimento_com_categoria"]
            + t["exterior_comparecimento_sem_categoria"]
            + t["sistema_apuracao_comparecimento_brasil"]
        )
        assert (
            abs(
                t["biometria_pct"]
                + t["ano_nascimento_pct"]
                + t["sem_cadastro_pct"]
                - 100
            )
            < 0.05
        )


def test_exterior_pelo_log(B):
    for turno in ("1t", "2t"):
        ex = B["exterior_log"][turno]
        if ex is None:
            continue
        assert (
            ex["sem_biometria"]
            == B["totais"][turno]["exterior_comparecimento_sem_categoria"]
        )
        assert ex["biometrica"] == 0
    assert B["exterior_log"]["fonte"] == "log"


def test_ufs_somam_o_pais(B):
    for turno in ("1t", "2t"):
        for cat in ("biometria", "ano_nascimento", "sem_cadastro"):
            assert (
                sum(u[f"{cat}_{turno}"] for u in B["por_uf"]) == B["totais"][turno][cat]
            )
    assert len(B["por_uf"]) == 27


def test_histograma_e_municipios(B):
    for turno in ("1t", "2t"):
        h = B["histograma_ano_nascimento"]["turnos"][turno]
        assert sum(h["contagem"]) == h["n"] == B["totais"][turno]["secoes"]
    M = B["municipios"]
    v = [m["ano_nascimento_pct_2t"] for m in M["maior_ano_nascimento"]]
    assert v == sorted(v, reverse=True) and len(v) == A.REGRAS["ranking_n"]
    assert all(
        m["aptos_2t"] >= A.REGRAS["municipio_aptos_min"]
        for m in M["maior_ano_nascimento"]
    )


def test_voto_com_n(B):
    for v in B["voto"]:
        if "did_fatia_flavio_pp" in v:
            assert v["n_did"] >= A.REGRAS["n_min"]


def test_bloco_renderiza(B):
    h = CS.habilitacao(B)
    assert "—" not in h and "fraude" not in h.lower()
    assert "não prova irregularidade" in h
    for f in ("categorias", "ufs", "mapa_uf", "mapa_mun", "histograma", "modelos"):
        assert f'id="fig-bio_{f}"' in h
    assert CS.habilitacao(None) == ""
