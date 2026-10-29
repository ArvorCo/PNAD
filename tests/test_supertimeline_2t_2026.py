"""Conservação do quadro anterior e três relógios sem dupla contagem."""

import csv
import json
from itertools import pairwise

import pytest
from apuracao_2t_2026.encerramento_dados import CAMPOS, CORTES, SAIDA
from apuracao_2t_2026.supertimeline_dados import cortes, instante, rotulo


@pytest.fixture(scope="module")
def dados():
    return json.loads((SAIDA / "supertimeline.json").read_text())


def test_fusos_e_virada_nao_perdem_data():
    assert instante("2026-10-25T23:30:00", 1) == 88200
    assert rotulo(88200) == "26/10 00:30:00"
    assert cortes(88200)[-1] == 90000
    assert cortes(84100)[-1] == 86400
    assert cortes(86400)[-1] == 86400
    with pytest.raises(ValueError):
        instante("2026-10-25T20:00:00-03:00")


def test_cortes_preservam_segundos_e_detalhe_publicado():
    cs = cortes(84100)
    assert cs[:10] == [h * 3600 - 1 for h in range(8, 18)]
    assert cs[10:30] == CORTES
    assert all(a < b for a, b in pairwise(cs))
    assert cs[30:] == [h * 3600 for h in range(20, 25)]


def test_todos_os_dados_anteriores_permanecem(dados):
    antigo = json.loads((SAIDA / "dados.json").read_text())
    assert dados["total"] == antigo["total"]
    assert dados["extrato_bu_legado_sha256"] == antigo["extrato_ordenado_sha256"]
    assert dados["logs_cobertura"] == antigo["logs"]
    assert dados["apos19_subtotal"] == antigo["linhas"][-1]
    for old, row in zip(antigo["linhas"][:-1], dados["linhas"][10:30], strict=True):
        for key in (
            *CAMPOS,
            "parcela_secoes_pct",
            "encerradas_acumuladas",
            "encerradas_pct",
            "restantes",
            "restantes_pct",
            "comparecimento_pct",
            "flavio_pct",
            "lula_pct",
            "ufs",
        ):
            assert row["fecho"][key] == old[key], (row["data_hora"], key)
        assert row["logs"]["acumulado"] == old["logs_computados_acumulados"]
        assert row["logs"]["acumulado_pct"] == old["logs_computados_acumulados_pct"]
    assert dados["linhas"][10]["logs"]["intervalo"] == 280
    assert (
        sum(r["logs"]["intervalo"] for r in dados["linhas"][:11])
        == antigo["linhas"][0]["logs_computados_intervalo"]
    )


def test_tres_trilhas_recompoem_sem_somar_subtotal(dados):
    for trilha in ("fecho", "recebido"):
        for campo in CAMPOS:
            assert (
                sum(r[trilha][campo] for r in dados["linhas"]) == dados["total"][campo]
            )
        acumulado = 0
        for r in dados["linhas"]:
            acumulado += r[trilha]["secoes"]
            assert r[trilha]["encerradas_acumuladas"] == acumulado
            assert r[trilha]["restantes"] + acumulado == dados["total"]["secoes"]
        assert dados["linhas"][-1][trilha]["encerradas_pct"] == 100
    assert (
        sum(r["logs"]["intervalo"] for r in dados["linhas"])
        == dados["logs_cobertura"]["computados"]
    )
    assert sum(dados["logs_dia"]["horas"]) == dados["logs_cobertura"]["computados"]
    assert (
        dados["logs_dia"]["extrato_sha256"] == dados["logs_cobertura"]["extrato_sha256"]
    )


def test_recebimentos_inconsistentes_nao_sao_apagados(dados):
    assert sum(r["recebido"]["cronologia_divergente"] for r in dados["linhas"]) == 16
    primeira = dados["linhas"][9]
    assert primeira["recebido"]["secoes"] == 1 and primeira["fecho"]["secoes"] == 0
    assert primeira["recebido"]["cronologia_divergente"] == 1
    assert dados["trilhas"]["recebido"]["ultimo_s"] == 84100
    assert dados["linhas"][-1]["data_hora"] == "26/10 00:00:00"
    assert dados["linhas"][-1]["recebido"]["secoes"] == 2


def test_cada_trilha_e_distribuicao_segundo_recompoe(dados):
    for nome, trilha in dados["trilhas"].items():
        eventos = iter(trilha["segundos"])
        e = next(eventos, None)
        for r in dados["linhas"]:
            contagem = 0
            while e and e[0] <= r["fim_inclusivo_s"]:
                contagem += e[1]
                e = next(eventos, None)
            assert contagem == r[nome]["secoes"]
        assert e is None


def test_csv_uma_linha_por_faixa_nao_duplica_logs(dados):
    with (SAIDA / "supertimeline.csv").open() as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == len(dados["linhas"])
    assert (
        sum(int(r["logs_intervalo"]) for r in rows)
        == dados["logs_cobertura"]["computados"]
    )
    for k in ("fecho", "recebido"):
        assert sum(int(r[f"{k}_secoes"]) for r in rows) == dados["total"]["secoes"]
