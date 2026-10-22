"""Onda atual, bases ausentes e válidos oficiais separados do cenário."""

import importlib
from copy import deepcopy

import pytest
from bs4 import BeautifulSoup
from reponderacao_vista.historico_2t import history
from reponderacao_vista.historico_painel import panel
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


def test_history_keeps_official_valids_and_identifies_preview():
    rows = [p for p in history() if p["id"] == "datafolha_2026-10-22"]
    assert len(rows) == 1
    row = rows[0]
    assert row["pnad"] is not None
    assert row["renda"]["perfil_tipo"] == "hipotese_onda_anterior"
    projected = project(row)
    assert projected["modos"]["pnad"] is not None
    assert projected["evidencia"]["tipo"] == "neutro"
    assert projected["modos"]["placar"]["validos"]["flavio"] == pytest.approx(
        100 * 47 / 93
    )
    assert row["publicado_validos"]["2t"] == {"flavio": 50, "lula": 50}


def test_transcription_reproducible_and_sources_intact(assert_json_close):
    poll = MODULE.previa()
    stored = MODULE.COMMON.read(
        MODULE.ROOT / "analysis/reponderacao/pesquisas/datafolha_2026-10-22.json"
    )
    assert_json_close(poll, stored)
    assert len(MODULE.COMMON.archive("datafolha_102026_22")) == 5
    plan = (MODULE.FOLDER / "registro-plano-amostral.txt").read_text()
    assert "2520" in plan and "Plano amostral" in plan


def test_preview_borrows_only_income_profile_and_coverage():
    poll = MODULE.previa()
    old = MODULE.COMMON.read(
        MODULE.ROOT / "analysis/reponderacao/pesquisas/datafolha_2026-10-14.json"
    )
    assert poll["renda"]["bases_referencia"] == [1172, 918, 335]
    assert poll["renda"]["amostra_pct"] == old["renda"]["amostra_pct"]
    assert poll["renda"]["parcela_ajustada_pct"] == pytest.approx(100 * 2425 / 2520)
    assert "bases" not in poll["renda"]
    assert (
        poll["cruzamentos"]["2t"]["linhas"]
        == MODULE.datafolha()["cruzamentos_documentais"]["linhas"]
    )
    assert poll["cruzamentos"]["2t"]["linhas"] != old["cruzamentos"]["2t"]["linhas"]


def test_preview_is_explicit_in_total_and_valid_charts():
    rows = [p for p in history() if p["instituto"] == "Datafolha"]
    rendered = BeautifulSoup(panel("Datafolha", rows), "html.parser")
    for mode in ("total", "validos"):
        view = rendered.select_one(f'[data-history-view="{mode}"]')
        assert "PRÉVIA PNAD" in view.get_text()
        assert "Prévia F" in view.select_one("svg").get_text()
        assert "Prévia L" in view.select_one("svg").get_text()
    assert "96,23%" in rendered.select_one(".history-preview").get_text()
    assert "48,72 × 44,53" in rendered.get_text()


def test_preview_delta_limits_adjustment_and_preserves_old_snapshot():
    row = next(p for p in history() if p["id"] == "datafolha_2026-10-22")
    assert row["pnad"]["flavio"] == pytest.approx(48.897, abs=0.001)
    assert row["pnad"]["lula"] == pytest.approx(44.216, abs=0.001)
    for key, published, cells in (
        ("flavio", 47, [39, 54, 54]),
        ("lula", 46, [54, 39, 40]),
    ):
        direct = sum(
            v * w / 100 for v, w in zip(cells, [35.187, 39.259, 25.554], strict=True)
        )
        reconstructed = (
            sum(v * n for v, n in zip(cells, [1172, 918, 335], strict=True)) / 2425
        )
        assert row["pnad"][key] == pytest.approx(
            published + 2425 / 2520 * (direct - reconstructed), abs=0.001
        )
    old = MODULE.COMMON.read(
        MODULE.ROOT / "docs/assets/reponderacao_cenarios/5098fa9fd1762b7a.json"
    )
    selected = next(p for p in old["projection"]["selected"] if p["id"] == row["id"])
    assert not selected["income_available"]
    current = MODULE.COMMON.read(
        MODULE.ROOT / "docs/assets/reponderacao_simulador.json"
    )
    selected = next(
        p for p in current["projection"]["selected"] if p["id"] == row["id"]
    )
    assert selected["income_available"]
    assert row["id"] in {p["id"] for p in current["polls"]}
