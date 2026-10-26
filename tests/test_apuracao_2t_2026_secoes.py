"""Contratos da análise por seção do 2º turno (pula sem os JSONs gerados)."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from apuracao_2t_2026 import secoes_fonte, secoes_linhas, secoes_sinais, secoes_voto

DADOS = Path(__file__).resolve().parents[1] / "analysis/apuracao_2t_2026/dados"
ARQS = ["secoes.json", "secoes_voto.json", "secoes_ranking.json"]


def _carregar(nome):
    arq = DADOS / nome
    if not arq.exists():
        pytest.skip(f"{nome} ausente: rode scripts/apuracao-2t-2026-secoes.py")
    return json.loads(arq.read_text(encoding="utf-8"))


def test_hhmm():
    assert secoes_sinais.hhmm(0.6) == "17:00"
    assert secoes_sinais.hhmm(121.0) == "19:01"
    assert secoes_sinais.hhmm(-540) == "08:00"
    assert secoes_sinais.hhmm(float("nan")) is None


def test_escolher_fonte():
    assert secoes_fonte.escolher_fonte("auto", 100, 1000) == "amostra"
    assert secoes_fonte.escolher_fonte("auto", 950, 1000) == "completo"
    assert secoes_fonte.escolher_fonte("completo", 0, 1000) == "completo"


def test_fuso_municipal_corrige_uma_hora():
    df = pd.DataFrame(
        {
            "uf": ["AM", "AM", "AM", "SP"],
            "mun": ["02020", "02020", "02003", "71072"],
            "abert_min": [-600.0, -599.0, -540.0, -538.0],
        }
    )
    corr = secoes_fonte.correcao_fuso_municipal(df)
    assert list(corr) == [60.0, 60.0, 0.0, 0.0]


def test_minutos_local_pelo_fuso_da_uf():
    s = pd.Series(["2026-10-25 15:01:00", "2026-10-25 17:01:00"])
    uf = pd.Series(["AC", "SP"])
    assert list(secoes_fonte.minutos_local(s, uf)) == [1.0, 1.0]


def test_comparar_exige_n_minimo():
    x = pd.DataFrame(
        {
            "uf": ["SP"] * 6,
            "mun": ["1"] * 6,
            "fl": [10, 10, 10, 20, 20, 20],
            "lu": [10, 10, 10, 10, 10, 10],
            "comp": [25] * 6,
            "delta_fatia_pp": [0.0] * 6,
            "fl1": [10] * 6,
            "lu1": [10] * 6,
        }
    )
    m = pd.Series([True, True, True, False, False, False])
    out = secoes_voto.comparar(x, m)
    assert out["n_sinal_comparavel"] == 3
    assert "dif_fatia_flavio_vs_vizinhas_pp" not in out


def test_rotulo_e_fonte_em_todo_json():
    for nome in ARQS:
        d = _carregar(nome)
        assert d["rotulo"] == secoes_sinais.ROTULO
        assert d["fonte"] in ("amostra", "completo")
        assert "—" not in json.dumps(d, ensure_ascii=False)


def test_secoes_coerentes():
    s = _carregar("secoes.json")
    if not secoes_linhas.disponivel(s):
        pytest.skip("linhas por seção fora do git ausentes")
    bloco = secoes_linhas.bloco(s)
    cols = bloco["colunas"]
    linhas = bloco["linhas"]
    assert len(linhas) == s["totais"]["secoes"]
    i = {c: cols.index(c) for c in cols}
    sinais = ["sinal_delta", "sinal_sem_bio", "sinal_ano_nasc", "sinal_salto_bio"]
    sinais += ["sinal_tardia", "sinal_papel"]
    api = ["sinal_delta", "sinal_sem_bio", "sinal_tardia", "sinal_papel"]
    for li in linhas[:2000]:
        assert li[i["escore"]] == sum(bool(li[i[c]]) for c in sinais)
        assert li[i["escore_api"]] == sum(bool(li[i[c]]) for c in api)
        if li[i["delta_pp"]] is not None:
            assert li[i["sinal_delta"]] == (li[i["delta_pp"]] >= 5)
    b = s["agregados"]["brasil"]
    assert b["n"] == s["totais"]["secoes"]
    assert sum(b["escore"].values()) == b["n"]
    assert sum(u["n"] for u in s["agregados"]["por_uf"]) == b["n"]


def test_voto_respeita_n_minimo():
    v = _carregar("secoes_voto.json")
    for x in v["sinais"]:
        if "dif_fatia_flavio_vs_vizinhas_pp" in x:
            assert x["n_sinal_comparavel"] >= secoes_voto.N_MIN
        if "did_fatia_flavio_pp" in x:
            assert x["n_did"] >= secoes_voto.N_MIN
    assert len(v["tabela_2x2x2"]) == 4
    for c in v["tabela_2x2x2"]:
        assert c["n"] == c["n_flavio_sobe"] + c["n_flavio_nao_sobe"]
        if c["n"] < secoes_voto.N_MIN:
            assert "delta_fatia_flavio_pp" not in c


def test_ranking():
    r = _carregar("secoes_ranking.json")
    rs = r["secoes"]
    assert 0 < len(rs) <= 100
    chave = [(-x["escore"], -x["magnitude"]) for x in rs]
    assert chave == sorted(chave)
    for x in rs:
        assert x["explicacao_provavel"]
        assert x["escore"] >= 1
        assert set(x["sinais"]) <= set(secoes_sinais.SINAIS)


def test_percentuais_com_duas_casas():
    s = _carregar("secoes.json")
    for u in s["agregados"]["por_uf"]:
        for v in u["delta_comp"].values():
            if isinstance(v, float):
                assert np.isclose(v, round(v, 2))


def test_linhas_fora_do_json(tmp_path):
    p = secoes_linhas.gravar(["a", "b"], [[1, 2], [3, None]], tmp_path / "x.json.gz")
    S = {"secoes": p}
    assert p["n_linhas"] == 2 and "linhas" not in p
    assert secoes_linhas.bloco(S)["linhas"] == [[1, 2], [3, None]]
    (tmp_path / "x.json.gz").unlink()
    assert not secoes_linhas.disponivel(S)
    with pytest.raises(secoes_linhas.LinhasAusentes):
        secoes_linhas.bloco(S)


def test_ponteiro_no_json_leve():
    s = _carregar("secoes.json")
    p = s["secoes"]
    assert "linhas" not in p
    assert p["n_linhas"] == s["totais"]["secoes"]
    assert len(p["sha256"]) == 64
