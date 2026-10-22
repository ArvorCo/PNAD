"""Onda atual, bases ausentes e válidos oficiais separados do cenário."""

import importlib
from copy import deepcopy

import pytest
from reponderacao_vista.historico_2t import history
from reponderacao_vista.historico_projecao import project

MODULE = importlib.import_module("datafolha-221026-renda")


def test_current_wave_uses_its_own_date_and_official_valids():
    poll = MODULE.datafolha()
    assert poll["publicado"]["2t"] == {
        "flavio": 47,
        "lula": 46,
        "branco_nulo": 5,
        "indecisos": 2,
    }
    assert poll["publicado_validos"]["2t"] == {"flavio": 50, "lula": 50}
    assert poll["n"] == 2520
    assert poll["registro_tse"] == "BR-09709/2026"
    assert poll["campo"] == {"inicio": "2026-10-20", "fim": "2026-10-22"}
    assert poll["cruzamentos_documentais"]["linhas"] == [
        [39, 54, 5, 2],
        [54, 39, 6, 1],
        [54, 40, 5, 1],
    ]


def test_registration_targets_cannot_become_observed_income():
    poll = MODULE.datafolha()
    assert poll["ignorar"] and not poll["cruzamentos"]
    assert "renda" not in poll
    assert poll["cruzamentos_documentais"]["bases"] == [None] * 3
    assert not poll["registro_conferido"]["usado_como_perfil"]
    assert not poll["registro_conferido"]["integra_anexada"]
    assert (
        "Relatório completo com o resultado da pesquisa não foi fornecido"
        in (MODULE.FOLDER / "registro-tse.txt").read_text()
    )


def test_missing_current_date_raises_instead_of_reusing_previous_wave():
    raw = MODULE.COMMON.read(MODULE.FOLDER / "g1_estimulada.json")["resultado"][
        "cenarios"
    ][0]
    chart = deepcopy(raw)
    for option in chart["data"]:
        option["values"] = [
            v for v in option["values"] if not v["date"].startswith(MODULE.DAY)
        ]
    with pytest.raises(ValueError, match="Onda atual ausente"):
        MODULE.current(chart)


def test_history_keeps_official_valids_and_does_not_fabricate_pnad():
    rows = [p for p in history() if p["id"] == "datafolha_2026-10-22"]
    assert len(rows) == 1
    row = rows[0]
    assert row["pnad"] is None
    projected = project(row)
    assert projected["modos"]["pnad"] is None
    assert projected["evidencia"]["tipo"] == "neutro"
    assert projected["modos"]["placar"]["validos"]["flavio"] == pytest.approx(
        100 * 47 / 93
    )
    assert row["publicado_validos"]["2t"] == {"flavio": 50, "lula": 50}


def test_transcription_reproducible_and_sources_intact(assert_json_close):
    poll = MODULE.datafolha()
    stored = MODULE.COMMON.read(
        MODULE.ROOT / "analysis/reponderacao/pesquisas/datafolha_2026-10-22.json"
    )
    assert_json_close(poll, stored)
    assert len(MODULE.COMMON.archive("datafolha_102026_22")) == 5
    plan = (MODULE.FOLDER / "registro-plano-amostral.txt").read_text()
    assert "2520" in plan and "Plano amostral" in plan
