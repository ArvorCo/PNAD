"""Logs no relógio do eleitor, independentes do agrupamento de BUs."""

import json

import pytest
from apuracao_2t_2026.encerramento_dados import CORTES, SAIDA, faixa
from apuracao_2t_2026.encerramento_figura import pct
from apuracao_2t_2026.encerramento_logs import (
    contar_textos,
    elegibilidade,
    integrar,
)


def evento(hora, urna="00000001", dia="25/10/2026", id="A"):
    return f"{dia} {hora}\tINFO\t{urna}\tVOTA\tO voto do eleitor foi computado\t{id}\n"


def test_releitura_deduplica_filtra_urna_e_dia_sem_truncar_segundos():
    texto = (
        evento("15:00:00")
        + evento("15:00:01")
        + evento("15:01:00")
        + evento("15:01:01")
        + evento("15:00:00", dia="04/10/2026")
        + evento("15:00:00", urna="00000002")
    )
    hs = contar_textos([("a", texto), ("b", texto)], {"00000001"}, 2)
    assert hs == {61200: 1, 61201: 1, 61260: 1, 61261: 1}
    bins = [0] * (len(CORTES) + 1)
    for s, n in hs.items():
        bins[faixa(s)] += n
    assert bins[:3] == [1, 2, 1]
    assert contar_textos(
        [("a", evento("00:00:01", dia="26/10/2026"))], {"00000001"}, 0
    ) == {86401: 1}
    # Mesmo segundo não implica duplicidade: linhas distintas contam separadamente.
    assert contar_textos(
        [("a", evento("17:00:00", id="A") + evento("17:00:00", id="B"))],
        {"00000001"},
        0,
    ) == {61200: 2}


def metricas():
    return {
        "bu": {"pleito": 3221, "fase": 2},
        "tempos_validos": True,
        "computados_por_hora_confiavel": True,
        "contagem_confere": True,
        "contagens": {"computados": 20},
        "primeiro_computo_s": 30000,
        "ultimo_computo_s": 61200,
    }


def test_cobertura_exige_hash_relogio_contagem_e_dia():
    r = metricas()
    assert elegibilidade("ok", r, "a", "a", 20, 0) is None
    assert elegibilidade(None, {}, None, "a", 20, 0) == "sem_log_utilizavel"
    assert elegibilidade("ok", r, "a", "b", 20, 0) == "hash_divergente"
    assert elegibilidade("ok", r, "a", None, 20, 0) == "sem_hash_no_catalogo"
    assert elegibilidade("ok", r, "a", "a", 21, 0) == "contagem"
    assert (
        elegibilidade("ok", dict(r, tempos_validos=False), "a", "a", 20, 0) == "relogio"
    )
    assert (
        elegibilidade("ok", dict(r, ultimo_computo_s=86400), "a", "a", 20, 0)
        == "fora_dia"
    )


def test_logs_nao_herdam_o_grupo_de_encerramento():
    d = {
        "total": {"secoes": 2, "comparecimento": 100},
        "linhas": [{"secoes": 0}, {"secoes": 2}],
    }
    logs = {
        "secoes": 2,
        "comparecimento_total": 100,
        "computados": 90,
        "intervalos": [80, 10],
    }
    integrar(d, logs)
    assert d["linhas"][0]["logs_computados_intervalo"] == 80
    assert d["linhas"][0]["secoes"] == 0
    assert d["linhas"][1]["logs_computados_acumulados_pct"] == 100
    with pytest.raises(ValueError):
        integrar(d, dict(logs, secoes=3))


def test_publicacao_recompoe_logs_sem_imputar_excluidos():
    d = json.loads((SAIDA / "dados.json").read_text())
    logs = d["logs"]
    assert logs["secoes"] == d["total"]["secoes"]
    assert logs["cobertas"] + sum(logs["exclusoes"].values()) == logs["secoes"]
    assert (
        logs["computados"] + logs["comparecimento_excluido"]
        == d["total"]["comparecimento"]
    )
    assert (
        sum(r["logs_computados_intervalo"] for r in d["linhas"]) == logs["computados"]
    )
    assert d["linhas"][-1]["logs_computados_acumulados_pct"] == 100
    assert (
        d["linhas"][0]["secoes"] == 0
        and d["linhas"][0]["logs_computados_intervalo"] > 0
    )
    assert len(logs["extrato_sha256"]) == 64
    assert len(logs["ufs"]) == 27


def test_porcentagem_nao_antecipa_completude_por_arredondamento():
    assert pct(99.99999, 3) == ">99,999%"
    assert pct(100, 3) == "100,000%"
    assert pct(99.97, 3) == "99,970%"
