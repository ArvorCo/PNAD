"""Seleção por onda, massas conservadas e comparação com a cédula correta."""

import hashlib
from copy import deepcopy

import pytest
from bs4 import BeautifulSoup
from reponderacao_vista.context import ROOT
from reponderacao_vista.historico_2t import history
from reponderacao_vista.historico_2t_chart import chart, segments
from reponderacao_vista.historico_projecao import evidence, project, projected_row
from reponderacao_vista.historico_urna import OFF, latest_comparison, reference, urna


@pytest.fixture(scope="module")
def polls():
    return {p["id"]: p for p in history()}


def test_atlas_crossing_field_connects_to_next_post_election_wave(polls):
    rows = [p for p in polls.values() if p["instituto"] == "AtlasIntel"]
    post = segments(rows, "placar")[-1]
    assert [p["id"] for p in post] == ["atlas_2026-10-08", "atlas_2026-10-18"]
    assert post[0]["fase"] == "Campo atravessa o 1º turno"
    assert len(segments(rows, "placar")) == 2
    assert len(segments(rows, "pnad")[-1]) == 2


def test_proportional_undecideds_conserve_mass_without_changing_valid_share(polls):
    poll = deepcopy(polls["ipespe_2026-10-15"])
    result = project(poll)["modos"]["placar"]
    assert result["validos"]["flavio"] == pytest.approx(
        100 * 48 * 0.92 / (48 * 0.92 + 46 * 0.88)
    )
    assert sum(result["transferidos"].values()) == pytest.approx(3 * 0.60)
    poll["placar"]["indecisos"] = 0
    assert project(poll)["modos"]["placar"]["validos"] == pytest.approx(
        result["validos"]
    )


def test_proxy_rates_are_conditioned_on_candidate_and_income_margin(polls):
    poll = polls["nexus_2026-10-18"]
    model = project(poll)
    e = model["evidencia"]
    for mode, weights in (("placar", e["perfil"]), ("pnad", e["pnad"])):
        v = e["voto_renda"]["flavio"]
        expected = sum(
            w * vote * q
            for w, vote, q in zip(weights, v, e["presenca_renda"], strict=True)
        ) / sum(w * vote for w, vote in zip(weights, v, strict=True))
        assert model["modos"][mode]["taxas"]["flavio"] == pytest.approx(expected)
    assert model["modos"]["placar"]["taxas"] != model["modos"]["pnad"]["taxas"]


def test_no_transport_between_waves_and_combined_nonchoice_is_not_split(polls):
    before = deepcopy(polls)
    old = project(polls["verita_2026-10-16"])
    assert old["evidencia"]["tipo"] == "neutro"
    assert old["modos"]["placar"]["taxas"]["flavio"] == 1
    atlas = project(polls["atlas_2026-10-18"])
    assert atlas["modos"]["placar"]["indecisos"] is None
    assert atlas["modos"]["placar"]["transferidos"] is None
    assert polls == before


def test_valid_only_is_preserved_and_missing_income_remains_missing(polls):
    source = polls["verita_2026-10-02"]
    converted = projected_row(source)
    assert converted["placar"] == source["placar"]
    assert converted["base_original"] == "validos"
    assert converted["pnad"] is None
    assert converted["projecao"]["modos"]["placar"]["indecisos"] is None
    assert projected_row(polls["indexa_2026-10-21"])["pnad"] is None


def test_all_projections_are_finite_conserved_and_documented(polls):
    for poll in polls.values():
        result = project(poll)
        assert result["evidencia"]["regra"]
        for key, mode in result["modos"].items():
            if mode is None:
                assert poll[key] is None
                continue
            assert sum(mode["validos"].values()) == pytest.approx(100, abs=0.01)
            assert all(0 <= v <= 100 for v in mode["validos"].values())
            assert all(0 <= v <= 1 for v in mode["taxas"].values())


def test_transcribed_sources_match_hash_and_each_own_wave(polls):
    for pid, e in evidence()["ondas"].items():
        ref = e["fonte"]
        assert (
            hashlib.sha256((ROOT / ref["arquivo"]).read_bytes()).hexdigest()
            == ref["sha256"]
        )
        assert polls[pid]["fonte_historico"]["sha256"] == ref["sha256"]
        assert polls[pid]["campo"]["inicio"] > "2026-10-04"


def test_urna_keeps_all_candidates_and_correct_total_denominator():
    assert sum(reference(True).values()) < 93
    assert urna("validos")["flavio"] == pytest.approx(
        100 * OFF["votos"]["flavio"] / OFF["validos"]
    )
    assert urna("total")["flavio"] == pytest.approx(
        100 * OFF["votos"]["flavio"] / (OFF["validos"] + OFF["brancos"] + OFF["nulos"])
    )
    poll = latest_comparison("AtlasIntel")
    assert poll["id"] == "atlas_2026-10-02"
    assert poll["publicado"]["validos"]["flavio"] != pytest.approx(
        100
        * poll["publicado"]["total"]["flavio"]
        / sum(poll["publicado"]["total"][c] for c in ("flavio", "lula"))
    )
    # The 05/10 runoff release remains ineligible; the official catalogue now
    # supplies a distinct first-round consolidation published on 01/10.
    assert latest_comparison("Veritá")["id"] == "verita_2026-09-25"


def test_generated_controls_cover_every_wave_with_distinct_tooltips(polls):
    soup = BeautifulSoup(
        (ROOT / "docs/reponderacao_pnad.html").read_text(), "html.parser"
    )
    root = soup.select_one("#institutos-2t")
    assert root.select_one('#history-valids-all[type="checkbox"]')
    for card in root.select(".history-panel"):
        assert card.select_one('[data-history-toggle][type="checkbox"]')
        original = card.select_one('[data-history-view="total"]')
        projected = card.select_one('[data-history-view="validos"][hidden]')
        assert {
            r["data-history-id"] for r in original.select("tr[data-history-id]")
        } == {r["data-history-id"] for r in projected.select("tr[data-history-id]")}
        for target in projected.select("g.hit[data-k]"):
            assert target["data-k"].endswith("|validos")
    assert soup.select_one('script[src^="assets/reponderacao_historico.js"]')
    assert soup.select_one('link[href^="assets/reponderacao_historico.css"]')
    assert "não um modelo validado" in root.get_text()
    atlas = [p for p in polls.values() if p["instituto"] == "AtlasIntel"]
    assert "Urna 1ºT" in BeautifulSoup(chart(atlas), "html.parser").get_text()
