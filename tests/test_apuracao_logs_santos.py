"""Regressão do original relatado pelo leitor; acervo pesado é opcional no CI."""

import hashlib
from pathlib import Path

import pytest
from apuracao_logs.parser import analisar
from apuracao_logs.processamento import reconciliar

ORIGINAL = (
    Path(__file__).resolve().parents[1]
    / "data/originals/tse_logs_2026/casos/sp-273-214/o03220sp7071802730214-log.jez"
)


@pytest.mark.skipif(not ORIGINAL.exists(), reason="original oficial no acervo local")
def test_santos_inspecoes_nao_sao_reinicializacao_e_processo_inclui_mesario():
    raw = ORIGINAL.read_bytes()
    assert (
        hashlib.sha256(raw).hexdigest()
        == "4873b29f6fba577ab83c6360e6a4efe4b2986f3e206d3447b1388549ad704d1a"
    )
    bu = {
        "mun": "70718",
        "zona": 273,
        "secao": 214,
        "comparecimento": 275,
        "hab_biometria": 215,
        "hab_ano_nascimento": 32,
        "comp_sem_biometria": 28,
        "modelo_urna": "UE2015",
        "fase": 2,
        "pleito": 3220,
    }
    r = reconciliar(analisar(raw, bu), bu)
    assert r["contagem_confere"] and r["biometria_confere"]
    c, p = r["contagens"], r["processo_observado"]
    assert (
        c.get("erros", 0)
        == c["reinicios_durante_votacao"]
        == c.get("reinicios_sistema_em_votacao", 0)
        == 0
    )
    assert c["retomadas_inatividade"] == 9 and c["habilitacoes_canceladas"] == 1
    assert r["inspecoes"]["n"] == 7 and r["inspecoes"]["max"] == 41
    assert p["processo"]["n"] == 275 and p["processo"]["p50"] == 73
    assert p["cadencia"]["p50"] == 97 and p["rajada10_s"] == 74
    assert p["por_tipo"]["biometrica"]["p50"] == 70
    assert p["por_tipo"]["biografica"]["p50"] == 122
    assert p["por_tipo"]["sem_biometria"]["p50"] == 74
