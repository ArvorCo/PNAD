"""Autoria, corte temporal, score sem cancelamento e projeção realmente pré-urna."""

import hashlib
import json
import subprocess
from copy import deepcopy

import pytest
from bs4 import BeautifulSoup
from reponderacao_vista.avaliacao_1t import (
    EVIDENCE,
    FROZEN,
    ROOT,
    evaluate,
    metrics,
    ranking,
    urna,
)
from reponderacao_vista.historico_urna import comparison_html


def test_official_valids_take_precedence_without_renormalizing():
    row = evaluate("Quaest")
    assert row["leituras"]["validos_instituto"]["valores"]["flavio"] == 45
    assert row["leituras"]["conversao_arvor"]["valores"]["flavio"] == pytest.approx(
        100 * 38 / 87
    )
    assert row["score_arvor_pp"] == row["leituras"]["validos_instituto"]["eam_fl_pp"]
    df = evaluate("Datafolha")["leituras"]["validos_instituto"]["valores"]
    assert df["flavio"] == 42
    assert (
        sum(df.values()) == 98
    )  # Preserve the source discrepancy, never repair it silently.
    assert sum(EVIDENCE["ondas"]["poderdata_2026-10-02"]["validos"].values()) == 101


def test_score_does_not_reward_cancellation_or_pair_normalization():
    actual = urna("validos")
    row = metrics({k: v + 3 for k, v in actual.items()})
    assert row["eam_fl_pp"] == pytest.approx(3)
    assert row["erro_vantagem_fl_pp"] == pytest.approx(0)
    assert sum(actual.values()) < 93
    assert sum(urna("total").values()) < sum(actual.values())


def test_missing_official_forecast_has_no_score_or_rank():
    for name in (
        "Palver",
        "Vox Brasil",
        "Indexa/Broadcast",
        "Meio/Ideia",
        "Alfa",
    ):
        assert evaluate(name)["score_arvor_pp"] is None
    p = evaluate("Palver")
    assert p["evidencia"]["status"] == "nao_publica_declarado"
    assert "conversao_arvor" in p["leituras"]
    assert "arvor_pre_urna" in p["leituras"]
    assert "validos_instituto" not in p["leituras"]
    assert evaluate("Veritá")["id"] == "verita_2026-09-25"


def test_rank_uses_absolute_error_and_missing_values_are_last():
    names = ["Nexus", "Quaest", "Gerp", "AtlasIntel", "Palver", "Veritá"]
    rows = ranking(names)
    assert [r["instituto"] for r in rows] == [
        "Gerp",
        "Veritá",
        "Quaest",
        "AtlasIntel",
        "Nexus",
        "Palver",
    ]
    assert [r["posicao"] for r in rows] == [1, 2, 3, 4, 5, None]
    assert evaluate("Gerp")["nota_documental"] is not None


def test_evidence_hashes_match_and_transcriptions_remain_unchanged():
    before = deepcopy(EVIDENCE)
    for row in EVIDENCE["ondas"].values():
        source = row["fonte"]
        assert (
            hashlib.sha256((ROOT / source["arquivo"]).read_bytes()).hexdigest()
            == source["sha256"]
        )
        assert source["pagina"] and source["url"]
        evaluate(row["instituto"])
    assert before == EVIDENCE


def test_frozen_projection_matches_pre_election_git_object():
    raw = subprocess.check_output(
        ["git", "show", f'{FROZEN["commit"]}:{FROZEN["arquivo_original"]}'], cwd=ROOT
    )
    assert hashlib.sha256(raw).hexdigest() == FROZEN["sha256_original"]
    original = json.loads(raw)["ballots"]["1t"]["scenarios"]
    assert FROZEN["cenario_padrao"] == "central"
    for pid, row in FROZEN["ondas"].items():
        assert row["divulgacao"] < "2026-10-04"
        original_row = next(p for p in original["central"]["polls"] if p["id"] == pid)
        assert row["modelo"] == original_row["modelo"]
        for key, vector in row["cenarios"].items():
            assert vector == next(
                p["modelo"] for p in original[key]["polls"] if p["id"] == pid
            )
        assert (
            evaluate(row["instituto"])["leituras"]["arvor_pre_urna"]["valores"]
            == row["modelo"]
        )
    assert "arvor_pre_urna" not in evaluate("AtlasIntel")["leituras"]


def test_visible_authorship_sources_and_generated_card_order():
    for name in ("Quaest", "Palver", "Datafolha"):
        text = BeautifulSoup(comparison_html(name), "html.parser").get_text()
        assert "Conversão dos totais · Arvor" in text
        assert "PNAD + presença · Arvor pré-urna" in text
        assert "Δ PNAD" in text
    page = BeautifulSoup(
        (ROOT / "docs/reponderacao_pnad.html").read_text(), "html.parser"
    )
    panels = page.select("#institutos-2t .history-panel")
    names = [p["data-instituto"] for p in panels]
    assert names == [r["instituto"] for r in ranking(names)]
    assert len(page.select("#score-arvor [data-score-house]")) == len(panels)
    assert page.select_one(
        '#score-arvor a[href="reponderacao_pnad_1o_turno_2026.html#comparar-metodos"]'
    )
    export = json.loads(
        (ROOT / "docs/assets/reponderacao_score_arvor.json").read_text()
    )
    assert [r["instituto"] for r in export["institutos"]] == names
    assert sum(r["posicao"] is not None for r in export["institutos"]) == 10
