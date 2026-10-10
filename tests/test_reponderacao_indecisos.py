"""Divisão global, denominadores, limites, versões antigas e paridade."""

import importlib
import json
import shutil
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

M = importlib.import_module("reponderacao-simulador")
ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "docs/assets/reponderacao_simulador.json").read_text())


def simple(masses):
    data = deepcopy(DATA)
    data["defaults"].update(modo="publicado", presenca_relativa=0, comparecimento=80)
    data["electorate"]["total"] = 100_000_000
    data["polls"] = [
        {
            "id": str(i),
            "instituto": str(i),
            "divulgacao": "2026-10-09",
            "published": m,
            "pnad": m,
        }
        for i, m in enumerate(masses)
    ]
    return data


def test_one_point_of_undecided_has_known_half_point_effect_and_absolute_size():
    data = simple([{"flavio": 49.5, "lula": 49.5, "indecisos": 1, "branco_nulo": 0}])
    central = M.undecided(data)
    all_f = M.undecided(data, {"indecisos_flavio": 100})
    assert central["survey_pct"] == pytest.approx(1)
    assert central["present_total"] == pytest.approx(800_000)
    assert central["to_flavio"] == central["to_lula"] == pytest.approx(400_000)
    assert all_f["to_flavio"] == pytest.approx(800_000)
    assert all_f["impact_flavio_pp"] == pytest.approx(0.5)
    assert all_f["impact_flavio_votes"] == pytest.approx(400_000)
    assert M.evaluate(data, {"indecisos_flavio": 100})[
        "diferenca_flavio_lula"
    ] == pytest.approx(1)


def test_global_proportion_is_applied_to_every_house_before_other_outflows():
    data = simple(
        [
            {"flavio": 60, "lula": 30, "indecisos": 10, "branco_nulo": 0},
            {"flavio": 20, "lula": 50, "indecisos": 20, "branco_nulo": 10},
        ]
    )
    share = (60 / 90 + 20 / 70) / 2
    effective = M.allocation_parameters(data, M.parameters(data))
    assert effective["indecisos_flavio"] == pytest.approx(100 * share)
    result = M.evaluate(data)
    assert result["polls"][0]["flavio"] == pytest.approx(100 * (48 + 8 * share) / 80)
    assert result["polls"][1]["flavio"] == pytest.approx(100 * (16 + 16 * share) / 72)
    extra = M.undecided(data, {"vies_pp": 8, "nulo_diferencial_pp": 10})
    assert extra["chosen_flavio_pct"] == pytest.approx(100 * share)


@pytest.mark.parametrize("centre", ["media", "projecao"])
@pytest.mark.parametrize("conversion", [0, 35, 100])
def test_partial_conversion_conserves_the_pool_and_electorate(centre, conversion):
    params = {
        "centro": centre,
        "indecisos_flavio": 27.4,
        "indecisos_validos": conversion,
    }
    u = M.undecided(DATA, params)
    assert u["to_flavio"] + u["to_lula"] + u["to_invalid"] == pytest.approx(
        u["present_total"]
    )
    assert u["to_flavio"] == pytest.approx(
        u["present_total"] * conversion / 100 * 0.274
    )
    result = M.evaluate(DATA, params)
    assert sum(result["por_100_eleitores"].values()) == pytest.approx(100)
    assert result["abstencao"] == 100 - DATA["defaults"]["comparecimento"]
    if conversion == 0:
        assert u["impact_flavio_pp"] == pytest.approx(0)
        assert u["to_flavio"] == u["to_lula"] == 0


def test_zero_pool_is_finite_and_split_has_no_effect():
    data = simple([{"flavio": 60, "lula": 40, "indecisos": 0, "branco_nulo": 0}])
    u = M.undecided(data, {"indecisos_flavio": 100})
    assert u["present_total"] == u["impact_flavio_pp"] == 0
    assert u["proportional_flavio_pct"] == pytest.approx(60)


def test_monte_carlo_uses_the_scenario_anchor_proportion_in_every_draw():
    p = M.parameters(DATA, {"centro": "projecao"})
    explicit = M.allocation_parameters(DATA, p)
    assert explicit["indecisos_flavio"] != p["indecisos_flavio"]
    assert M.simulate(DATA, p) == M.simulate(DATA, explicit)


def test_archived_data_retains_old_per_house_rule_and_matches_frozen_engine():
    old = json.loads(
        (ROOT / "docs/assets/reponderacao_cenarios/c593ba54c460637c.json").read_text()
    )
    assert "undecided_policy" not in old
    assert M.evaluate(old)["flavio"] == pytest.approx(
        old["central"]["flavio"], abs=1e-9, rel=0
    )
    node = shutil.which("node")
    if not node:
        pytest.skip("Node ausente")
    script = """const fs=require('fs'),d=JSON.parse(fs.readFileSync(0,'utf8'));
const old=require('./docs/assets/reponderacao_cenarios/motor-'+d.engine+'.js');
process.stdout.write(JSON.stringify(['media','projecao'].map(centro=>old.evaluate(d,{centro}))));"""
    frozen = json.loads(
        subprocess.check_output(
            [node, "-e", script], input=json.dumps(old), text=True, cwd=ROOT
        )
    )
    for centre, expected in zip(["media", "projecao"], frozen, strict=True):
        actual = M.evaluate(old, {"centro": centre})
        for key in ["flavio", "lula", "validos", "branco_nulo", "abstencao"]:
            assert actual[key] == pytest.approx(expected[key], abs=1e-9, rel=0)


def test_diagnostics_python_browser_parity_across_both_centres():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node ausente")
    cases = [
        {"centro": c, "indecisos_flavio": share, "indecisos_validos": conversion}
        for c in ["media", "projecao"]
        for share in [None, 0, 47.3, 100]
        for conversion in [0, 30, 100]
    ]
    script = """const fs=require('fs'),m=require('./docs/assets/reponderacao_simulador_motor.js');
const {data,cases}=JSON.parse(fs.readFileSync(0,'utf8'));
process.stdout.write(JSON.stringify(cases.map(p=>m.undecided(data,p))));"""
    results = json.loads(
        subprocess.check_output(
            [node, "-e", script],
            input=json.dumps({"data": DATA, "cases": cases}),
            text=True,
            cwd=ROOT,
        )
    )
    for case, actual in zip(cases, results, strict=True):
        expected = M.undecided(DATA, case)
        for key, value in expected.items():
            assert actual[key] == (
                pytest.approx(value, abs=1e-6, rel=0)
                if isinstance(value, (int, float))
                else value
            )


def test_transfer_controls_are_prominent_and_evidence_keeps_source_coverage():
    page = BeautifulSoup(
        (ROOT / "docs/reponderacao_pnad.html").read_text(), "html.parser"
    )
    for key in ["indecisos_validos", "indecisos_flavio"]:
        control = page.select_one(f"#rs-{key}")
        assert not control.find_parent("details", class_="rs-advanced")
        assert control["type"] == "range"
    evidence = page.select_one("#indecisos-fontes").get_text()
    assert "Vox Brasil" in evidence and "9,7%" in evidence
    assert (
        "não migração medida" in page.select_one("#transferencia-indecisos").get_text()
    )
