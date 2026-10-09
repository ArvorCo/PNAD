"""Mesmo denominador oficial, mesmas ondas da apuração e corte pré-eleitoral."""

import copy
import importlib
import json
from pathlib import Path

import pytest
from bs4 import BeautifulSoup
from reponderacao_vista.urna_dados import AUDIT, ELECTION, URNA, build, comparison

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "docs/assets/reponderacao_pnad.json").read_text())
NEXUS = json.loads((ROOT / "docs/assets/nexus_btg_28092026_data.json").read_text())
MODEL = importlib.import_module("reponderacao-validos")


def test_urna_uses_all_official_valid_votes_including_minor_candidates():
    result = build()
    votes = result["urna"]["votos"]
    assert sum(votes.values()) == result["urna"]["validos_votos"] == 119300788
    for k, count in votes.items():
        assert URNA[k] == pytest.approx(100 * count / 119300788, abs=0.000001)
    assert URNA["lula"] + URNA["flavio"] < 100
    assert result["urna"]["secoes"] == result["urna"]["secoes_total"]


def test_compact_final_audit_preserves_all_houses_and_exclusions():
    result = build()
    assert len(result["pesquisas"]) == 13
    assert len({p["instituto"] for p in result["pesquisas"]}) == 13
    assert sum(p["reponderado"] is not None for p in result["pesquisas"]) == 10
    assert all(
        "2026-09-25" <= p["campo"]["fim"] <= ELECTION for p in result["pesquisas"]
    )
    assert all(p["divulgacao"] <= ELECTION for p in result["pesquisas"])
    assert result["efeito_pareado"] == AUDIT["efeito_reponderacao"]["ultimas_ondas"]


@pytest.mark.parametrize(
    "row",
    [p for p in AUDIT["pesquisas"] if p["ultima_onda_da_casa"] and p["reponderado"]],
    ids=lambda p: p["id"],
)
def test_wave_comparison_agrees_with_full_apuracao_report(row):
    poll = next(p for p in DATA["pesquisas"] if p["id"] == row["id"])
    comp = comparison(poll)
    assert comp is not None
    for mode, source_mode in (("publicado", "publicado"), ("pnad", "reponderado")):
        assert comp[mode]["validos"] == pytest.approx(
            row[source_mode]["validos"], abs=0.000001
        )
        assert comp[mode]["diferenca_lula_menos_flavio"]["erro"] == pytest.approx(
            row[source_mode]["diferenca_lula_menos_flavio"]["erro"], abs=0.000002
        )


def test_partial_income_adjustment_is_disclosed_and_not_imputed_as_zero():
    poll = next(p for p in DATA["pesquisas"] if p["id"] == "mda_2026-10-02")
    comp = comparison(poll)
    assert set(comp["sem_cruzamento"]) == {"caiado", "cury", "renan_santos", "zema"}
    assert comp["pnad"]["validos"]["cury"] > 0
    with pytest.raises(ValueError, match="Candidatos positivos sem cruzamento"):
        MODEL.prepare(poll, "1t")


def test_first_round_projection_cannot_consume_post_election_waves():
    data = copy.deepcopy(DATA)
    base = MODEL.build(data, NEXUS)
    new = copy.deepcopy(
        next(p for p in data["pesquisas"] if p["id"] == "datafolha_2026-10-03")
    )
    new.update(id="datafolha_apos_eleicao", divulgacao="2026-10-08")
    new["campo"]["fim"] = "2026-10-07"
    new["turnos"] = {"1t": new["turnos"]["1t"]}
    new["publicado"] = {"1t": new["publicado"]["1t"]}
    data["pesquisas"].append(new)
    result = MODEL.build(data, NEXUS)
    assert result["ballots"]["1t"] == base["ballots"]["1t"]
    assert result["ballots"]["1t"]["reference"] == ELECTION
    assert result["ballots"]["2t"]["reference"] == DATA["referencia"]
    assert "urna" not in result["ballots"]["2t"]
    assert comparison(new) is None


def test_projection_error_uses_same_partition_and_signed_gap_in_every_scenario():
    block = MODEL.build(DATA, NEXUS)["ballots"]["1t"]
    assert sum(block["urna"].values()) == pytest.approx(100)
    assert block["urna"]["demais"] == pytest.approx(
        100 - sum(URNA[k] for k in block["urna"] if k != "demais")
    )
    for scenario in block["scenarios"].values():
        for mode, vector in scenario["aggregate"].items():
            assert sum(vector.values()) == pytest.approx(100)
            assert scenario["erros"][mode]["diferenca_lula_flavio_pp"] == pytest.approx(
                (vector["lula"] - vector["flavio"]) - (URNA["lula"] - URNA["flavio"])
            )


def test_institutes_have_separate_turns_and_first_round_tables_link_full_audit():
    current = BeautifulSoup(
        (ROOT / "docs/reponderacao_pnad.html").read_text(), "html.parser"
    )
    archive = BeautifulSoup(
        (ROOT / "docs/reponderacao_pnad_1o_turno_2026.html").read_text(), "html.parser"
    )
    for turn in ("1t", "2t"):
        soup = archive if turn == "1t" else current
        group = soup.select_one(f"#institutos-{turn}")
        assert group is not None
        assert all(
            panel["data-turno"] == turn for panel in group.select("article.panel")
        )
    assert archive.select_one('#projecao-validos [data-ballot="1t"] .vf-error')
    assert not current.select_one('#projecao-validos [data-ballot="2t"] .vf-error')
    assert archive.select_one(
        '#pesquisa-mda_2026-10-02 .poll-urna a[href="apuracao_1o_turno_2026.html#pesquisas"]'
    )
    assert not current.select_one("#pesquisa-datafolha_2026-10-08 .poll-urna")
