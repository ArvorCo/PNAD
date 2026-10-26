"""Pesquisas do 2º turno contra a urna: aritmética e contratos dos JSON gravados."""

import json
from pathlib import Path

import pytest
from apuracao_2t_2026 import pesquisas_nacionais as N
from apuracao_2t_2026 import pesquisas_territorio as T

DADOS = Path(__file__).resolve().parents[1] / "analysis/apuracao_2t_2026/dados"
URNA = {"flavio": 48.0, "lula": 52.0}


def test_erro_sinal_f_menos_l():
    e = N.erro({"flavio": 51.0, "lula": 49.0}, URNA)
    assert e["erro_f_menos_l"] == pytest.approx(6.0)
    assert e["erro_lula_menos_flavio"] == pytest.approx(-6.0)
    assert e["erro_flavio"] == pytest.approx(3.0)


def test_modo_coleta():
    assert N.modo("presencial domiciliar") == "presencial"
    assert N.modo("recrutamento digital aleatório") == "online"
    assert N.modo("telefônico automatizado IVR/URA") == "telefone"
    assert N.modo("seleção por cotas") == "nao_informado"


def test_ultima_por_casa_respeita_corte():
    ondas = [
        {
            "id": "a1",
            "instituto": "A",
            "campo": {"fim": "2026-10-18"},
            "divulgacao": "",
        },
        {
            "id": "a2",
            "instituto": "A",
            "campo": {"fim": "2026-10-22"},
            "divulgacao": "",
        },
        {
            "id": "a3",
            "instituto": "A",
            "campo": {"fim": "2026-10-24"},
            "divulgacao": "",
        },
        {
            "id": "b1",
            "instituto": "B",
            "campo": {"fim": "2026-10-16"},
            "divulgacao": "",
        },
    ]
    assert [x["id"] for x in N.ultima_por_casa(ondas)] == ["a3"]


def test_multiplicador_necessario_zera_na_urna():
    assert N.multiplicador_necessario(URNA, URNA) == pytest.approx(0.0)
    assert N.multiplicador_necessario({"flavio": 50, "lula": 50}, URNA) < 0


def test_avaliar_metodo_vies_e_vencedor():
    urna = {
        "ufs": {
            "SP": {"votos": {"flavio": 55, "lula": 45}},
            "BA": {"votos": {"flavio": 30, "lula": 70}},
        }
    }
    pred = {"SP": (58.0, 42.0), "BA": (33.0, 67.0)}
    m = T.avaliar_metodo("x", "x", pred, urna)
    assert m["acertou_vencedor"] == 2
    assert m["vies_flavio_pp_ponderado"] == pytest.approx(3.0)
    assert m["rmse_sem_vies_pp"] == pytest.approx(0.0, abs=1e-9)


def _ler(nome):
    caminho = DADOS / nome
    if not caminho.exists():
        pytest.skip(f"{nome} ausente; rode scripts/apuracao-2t-2026-pesquisas.py")
    return json.loads(caminho.read_text(encoding="utf-8"))


def test_pesquisas_vs_urna_contrato():
    d = _ler("pesquisas_vs_urna.json")
    r = d["resumo"]
    assert r["n_casas"] == len(d["pesquisas"]) == len(d["ranking"])
    assert len({x["instituto"] for x in d["pesquisas"]}) == r["n_casas"]
    assert all(x["campo"]["fim"] >= "2026-10-19" for x in d["pesquisas"])
    assert (
        r["flavio_a_frente_nos_validos"]
        + r["lula_a_frente_nos_validos"]
        + r["empates_nos_validos"]
        == r["n_casas"]
    )
    urna = d["urna"]["brasil"]["validos"]
    assert urna["flavio"] + urna["lula"] == pytest.approx(100.0)
    cb = d["hipoteses"]["contabilidade_entre_turnos"]["brasil"]
    assert cb["residuo_identidade"] == 0
    for x in d["pesquisas"]:
        e = x["erro_validos_do_total"]
        assert e["erro_f_menos_l"] == pytest.approx(
            e["pesquisa_f_menos_l"] - e["urna_f_menos_l"], abs=1e-5
        )


def test_projecao_e_estaduais_contrato():
    p = _ler("projecao_pre_urna.json")
    for m in p["metodos"].values():
        assert m["n_ufs"] == 27
        assert 0 <= m["acertou_vencedor"] <= 27
    e = _ler("pesquisas_estaduais.json")
    assert e["acertaram_vencedor"] <= len(e["pesquisas"])


def test_memorando_sem_travessao_e_com_entrada_do_autor():
    caminho = DADOS / "pesquisas.md"
    if not caminho.exists():
        pytest.skip("pesquisas.md ausente")
    texto = caminho.read_text(encoding="utf-8")
    assert chr(0x2014) not in texto
    assert "ENTRADA DO AUTOR" in texto
    assert "não saberemos" in texto
    assert "fraude" not in texto.lower()


def test_hipotese_autor_contrato():
    a = _ler("hipotese_autor.json")
    assert a["reproducao_tweet"]["flavio_validos_pct"] == pytest.approx(48.3, abs=0.05)
    alvo = a["urna"]["flavio_validos_pct"]
    for c in a["cenarios"]:
        assert c["placar"]["branco_nulo_pct_comparecimento"] == pytest.approx(
            a["urna"]["branco_nulo_pct_comparecimento"], abs=1e-3
        )
    if a["presenca_necessaria_a"] is not None:
        c = next(x for x in a["cenarios"] if x["nome"] == "a_presenca_necessaria")
        assert c["placar"]["flavio_validos_pct"] == pytest.approx(alvo, abs=1e-3)
