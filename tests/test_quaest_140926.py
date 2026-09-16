"""Contratos analíticos do dossiê: medição, hipótese, fonte e cenário."""

import csv
import importlib.util
import json
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "docs/assets/quaest_140926_data.json").read_text())


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_transfer_keeps_measured_rows_and_structural_zeros():
    s = DATA["transfer"]
    assert s["matrix"][0] == [36, 0, 0, 0]
    assert s["matrix"][1] == [0, 31, 0, 0]
    assert s["matrix"][2] == pytest.approx([1.75, 2.87, 0.49, 1.89])
    assert s["matrix"][5] == pytest.approx([0.38, 0.32, 0, 0.30])
    assert s["kinds"].count("medido") == 4
    for row, total in zip(s["matrix"], s["shares"], strict=True):
        assert sum(row) == pytest.approx(total)
    for j, total in enumerate(s["targets"]):
        assert sum(row[j] for row in s["matrix"]) == pytest.approx(total)


def test_prior_changes_only_the_unmeasured_allocation():
    audit = load("quaest-140926-audit")
    a = audit.transfer()
    b = audit.transfer([[100, 1, 1, 1], [1, 100, 1, 1]])
    assert a["matrix"][:6] == b["matrix"][:6]
    assert a["matrix"][6] != b["matrix"][6]
    assert a["residual_targets"] == pytest.approx([0.35, 3.97, 4.19, 8.49])
    assert a["consolidation"] == b["consolidation"]
    assert a["consolidation"]["ratio"] == 2.75


def test_income_reading_is_independently_checked():
    r = DATA["reweight"]["turnos"]
    assert r["2t"]["recomposto"]["lula"] == 40.11
    assert r["2t"]["recomposto"]["flavio"] == 41.93
    assert DATA["proofs"]["2t"]["sex_recomposed"] == pytest.approx([39.59, 42.23])
    assert DATA["proofs"]["1t"]["sex_recomposed"] == pytest.approx([36.06, 30.88])
    a = r["1t"]["cenarios"]["pessoas16_efetivo"]["ajustado"]
    assert a["lula"] == pytest.approx(36.531)
    assert a["flavio"] == pytest.approx(30.440)
    assert [sum(row) for row in DATA["tables"]["FIRST_INCOME"]] == [101, 101, 100]


def test_historical_scenario_is_not_silently_overwritten():
    old = json.loads(
        (ROOT / "analysis/reponderacao/pesquisas/quaest_2026-09-06.json").read_text()
    )
    assert old["publicado"]["1t"]["indecisos"] == 9  # lista com Marçal
    assert DATA["tables"]["FIRST_HISTORY"][1] == [36, 29, 8, 9, 10, 8]  # sem Marçal
    assert DATA["tables"]["FIRST_HISTORY"][2] == [36, 31, 7, 9, 10, 7]


def test_question_ledger_distinguishes_external_disclosure():
    rows = DATA["questions"]
    assert [r["question"] for r in rows] == list(range(1, 67))
    assert sum(r["report_page"] is not None for r in rows) == 38
    assert rows[22]["report_page"] == 16
    assert "Lista compatível" in rows[22]["status"]
    assert rows[49]["external"] == "g1-stf"
    assert rows[49]["report_page"] is None
    assert rows[42]["external"] == "g1-reformas"
    assert rows[64]["report_page"] is None
    assert rows[36]["questionnaire_page"] == 12
    assert rows[64]["questionnaire_page"] == 18
    assert "cen1t_pres1" in rows[23]["registered_block"]


def test_territorial_comparison_uses_exact_sector_codes():
    with (ROOT / "docs/assets/quaest_140926_territorio.csv").open() as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 668
    a, b = [[r for r in rows if r["round"] == wave] for wave in ["07/09", "14/09"]]
    for wave in [a, b]:
        assert sum(int(r["interviews"]) for r in wave) == 2004
        assert len({r["sector_code"] for r in wave}) == 334
        assert len({r["municipality_code"] for r in wave}) == 120
        assert all(len(r["sector_code"]) == 15 for r in wave)
    assert len({r["sector_code"] for r in a} & {r["sector_code"] for r in b}) == 4
    assert (
        len({r["municipality_code"] for r in a} & {r["municipality_code"] for r in b})
        == 26
    )


def test_uncertainty_and_conditional_denominator():
    assert DATA["derived"]["difference_margin_2t_aas"] == pytest.approx(
        3.96377, abs=0.00001
    )
    assert DATA["derived"]["open_vote_approx"] == pytest.approx(32.41)
    assert (
        DATA["derived"]["flavio_definite_new"] < DATA["derived"]["flavio_definite_old"]
    )


def test_static_report_local_links_and_sources():
    path = ROOT / "docs/quaest_14092026.html"
    source = path.read_text()
    soup = BeautifulSoup(source, "html.parser")
    ids = [tag["id"] for tag in soup.select("[id]")]
    assert len(ids) == len(set(ids))
    assert len(soup.select("main section")) == 20
    assert len(soup.select("svg")) == 3
    assert "—" not in source
    assert "Não há fita de Lula ou Flávio" in soup.get_text()
    assert "não foi aplicada a cada fita" in soup.get_text()
    for tag in soup.select("[href], [src]"):
        url = tag.get("href", tag.get("src"))
        if url.startswith(("https:", "http:", "data:")):
            continue
        local, _, anchor = url.partition("#")
        if local:
            assert (path.parent / local).exists(), url
        elif anchor:
            assert anchor in ids, url


def test_legacy_partial_import_cannot_overwrite_full_source(tmp_path, capsys):
    mod = load("quaest-140926-g1")
    mod.ROOT = tmp_path
    target = tmp_path / "analysis/reponderacao/pesquisas/quaest_2026-09-13.json"
    target.parent.mkdir(parents=True)
    target.write_text('{"fonte":{"tipo":"relatorio"}}')
    before = target.read_bytes()
    mod.main()
    assert target.read_bytes() == before
    assert "Fonte integral já disponível" in capsys.readouterr().out
