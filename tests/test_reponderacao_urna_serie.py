"""Corte temporal, média pareada em válidos e urna fora da curva histórica."""

import copy
import csv
import json
from datetime import date
from pathlib import Path

import pytest
from bs4 import BeautifulSoup
from reponderacao_vista.urna_dados import AUDIT
from reponderacao_vista.urna_serie import KEYS, MODES, WINDOW, blocks, build

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "docs/assets/reponderacao_pnad.json").read_text())


@pytest.fixture(scope="module")
def history():
    return build(DATA)


def test_same_latest_ten_income_houses_as_apuracao_audit(history):
    final = history["final"]
    audit = [
        p for p in AUDIT["pesquisas"] if p["ultima_onda_da_casa"] and p["reponderado"]
    ]
    assert final["n_institutos"] == len(audit) == 10
    assert set(final["ondas"]) == {p["id"] for p in audit}
    for mode, audit_mode in (("publicado", "publicado"), ("pnad", "reponderado")):
        for key in ("flavio", "lula"):
            expected = sum(p[audit_mode]["validos"][key] for p in audit) / len(audit)
            assert final[mode][key] == pytest.approx(expected, abs=0.000002)


def test_full_candidate_denominator_and_signed_difference(history):
    assert history["urna"]["validos_votos"] == 119300788
    assert sum(history["urna"]["validos"].values()) == pytest.approx(100)
    assert history["urna"]["validos"]["flavio"] == pytest.approx(
        47.027772, abs=0.000001
    )
    assert history["urna"]["validos"]["demais"] > 7
    for row in history["serie"]:
        for mode in MODES:
            if row[mode] is not None:
                assert sum(row[mode].values()) == pytest.approx(100)
    for mode in MODES:
        for key in KEYS:
            assert history["final"]["urna_menos_media_pp"][mode][key] == pytest.approx(
                history["urna"]["validos"][key] - history["final"][mode][key]
            )


def test_normalize_each_poll_before_equal_house_mean():
    data = copy.deepcopy(DATA)
    source = next(p for p in data["pesquisas"] if p["id"] == "datafolha_2026-10-03")
    rows = []
    for ident, institute, release, vector in (
        ("a1", "A", "2026-09-27", {"flavio": 90, "lula": 10}),
        ("a2", "A", "2026-10-03", {"flavio": 40, "lula": 40, "indecisos": 20}),
        ("b", "B", "2026-10-01", {"flavio": 20, "lula": 40, "indecisos": 40}),
        ("old", "C", "2026-09-26", {"flavio": 99, "lula": 1}),
    ):
        row = copy.deepcopy(source)
        row.update(id=ident, instituto=institute, divulgacao=release)
        row["campo"]["fim"] = release
        row["publicado"]["1t"] = vector
        row["turnos"]["1t"]["cenarios"][data["benchmark"]["cenario_principal"]][
            "ajustado"
        ] = vector
        rows.append(row)
    data["pesquisas"] = rows
    result = build(data)
    assert result["final"]["ondas"] == ["a2", "b"]
    assert result["final"]["publicado"]["flavio"] == pytest.approx((50 + 100 / 3) / 2)
    edge = next(p for p in result["serie"] if p["data"] == "2026-10-02")
    assert "a1" in edge["ondas"]
    assert "old" not in result["final"]["ondas"]


def test_absent_windows_remain_null_and_urna_never_enters_series(history):
    assert any(row["publicado"] is None for row in history["serie"])
    assert history["corte_pesquisas"] == "2026-10-03"
    assert all(row["data"] < history["eleicao"] for row in history["serie"])
    for row in history["serie"]:
        eligible = [
            p
            for p in DATA["pesquisas"]
            if "1t" in p["turnos"]
            and p["campo"]["fim"] <= "2026-10-04"
            and not p.get("substituida")
            and not p.get("primeiro_turno_com_marcal")
        ]
        selected = WINDOW.select(eligible, date.fromisoformat(row["data"]))
        assert row["ondas"] == [p["id"] for p in selected]
        assert row["n_institutos"] == len(selected)


@pytest.mark.parametrize(
    "change", ["release", "field", "replaced", "marcal", "undated"]
)
def test_invalid_or_post_election_waves_do_not_change_history(history, change):
    data = copy.deepcopy(DATA)
    new = copy.deepcopy(
        next(p for p in data["pesquisas"] if p["id"] == "datafolha_2026-10-03")
    )
    new.update(id="invalid_wave", instituto="Invalid house")
    if change == "release":
        new["divulgacao"] = "2026-10-05"
    elif change == "field":
        new["campo"]["fim"] = "2026-10-05"
    elif change == "replaced":
        new["substituida"] = True
    elif change == "marcal":
        new["primeiro_turno_com_marcal"] = True
    else:
        new["divulgacao"] = None
    data["pesquisas"].append(new)
    result = build(data)
    assert result["serie"] == history["serie"]
    assert result["final"] == history["final"]
    assert "invalid_wave" in result["excluidas"]


def test_partial_income_crossings_and_negative_residuals_are_disclosed(history):
    mda = next(p for p in history["final"]["pesquisas"] if p["id"] == "mda_2026-10-02")
    assert set(mda["sem_cruzamento"]) == {"cury", "renan_santos", "caiado", "zema"}
    vector, audit = blocks({"flavio": 45, "lula": 40, "outros": -1, "indecisos": 16})
    assert sum(vector.values()) == pytest.approx(100)
    assert audit["negativos_truncados_pp"] == 1


def test_published_exports_match_build_and_urna_is_separate(history):
    assert (
        json.loads((ROOT / "docs/assets/reponderacao_urna_serie_1t.json").read_text())
        == history
    )
    with (ROOT / "docs/assets/reponderacao_urna_serie_1t.csv").open() as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == len(history["serie"]) + 1
    assert rows[-1]["tipo"] == "urna"
    assert rows[-1]["data"] == history["eleicao"]
    assert rows[-1]["ondas"] == ""
    assert (
        float(rows[-2]["pnad_flavio_validos_pct"]) == history["final"]["pnad"]["flavio"]
    )


def test_chart_is_visible_before_projection_only_in_first_round_archive():
    archive = BeautifulSoup(
        (ROOT / "docs/reponderacao_pnad_1o_turno_2026.html").read_text(), "html.parser"
    )
    section = archive.select_one("#agregador-urna")
    assert section and section.find_parent("details") is None
    sections = [p.get("id") for p in archive.select("main > section")]
    assert sections.index("agregador-urna") < sections.index("projecao-validos")
    assert len(section.select("[data-urna-candidato]")) == 2
    assert len(section.select(".us-candidate")) == 3
    assert len(section.select(".us-comparison")) == 6
    assert archive.select_one('.toc a[href="#agregador-urna"]')
    assert archive.select_one("#primeiro-turno-chart")
    current = BeautifulSoup(
        (ROOT / "docs/reponderacao_pnad.html").read_text(), "html.parser"
    )
    assert current.select_one("#agregador-urna") is None
