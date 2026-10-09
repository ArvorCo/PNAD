"""Cobertura, inclinação binária, sorteios congelados e paridade das centrais."""

import hashlib
import importlib
import json
import shutil
import subprocess
from copy import deepcopy
from datetime import date
from pathlib import Path

import numpy as np
import pytest
from bs4 import BeautifulSoup
from predicao_2026 import base, motor

ROOT = Path(__file__).resolve().parents[1]
M = importlib.import_module("reponderacao-simulador")
P = importlib.import_module("reponderacao-projecao")
DATA = json.loads((ROOT / "docs/assets/reponderacao_simulador.json").read_text())
RAW = json.loads((ROOT / "docs/assets/reponderacao_pnad.json").read_text())


def source(house, day, flavio, *, income=False):
    values = {"flavio": flavio, "lula": 93 - flavio, "indecisos": 2, "branco_nulo": 5}
    return {
        "id": f"{house}_{day}",
        "instituto": house,
        "n": 2000,
        "campo": {"inicio": day, "fim": day},
        "divulgacao": day,
        "publicado": {"2t": values},
        "turnos": (
            {"2t": {"cenarios": {"pessoas16_efetivo": {"ajustado": values}}}}
            if income
            else {}
        ),
    }


def test_inclusive_projection_uses_latest_post_first_round_and_never_imputes_income():
    projection = DATA["projection"]
    selected = projection["selected"]
    assert {p["instituto"] for p in selected} == {
        "Datafolha",
        "PoderData",
        "Vox Brasil",
    }
    assert all(p["campo"]["inicio"] > "2026-10-04" for p in selected)
    assert sum(p["weight"] for p in selected) == pytest.approx(1)
    assert projection["half_life_days"] == 3
    vox = next(p for p in selected if p["instituto"] == "Vox Brasil")
    assert not vox["income_available"]
    assert vox["pnad"] == vox["published"]
    assert any(p["id"] == "atlas_2026-10-08" for p in projection["excluded"])
    assert not projection["trend"]["pnad"]["available"]
    assert projection["trend"]["pnad"]["dp_margem_projecao_pp"] == 0
    # Zero inclinação significa média dos vetores completos por recência.
    expected = np.average(
        [p["previsao_vetor"] for p in selected],
        axis=0,
        weights=[p["weight"] for p in selected],
    )
    assert projection["trend"]["pnad"]["vetor"] == pytest.approx(expected)


def test_mean_preserves_published_snapshot_for_all_controls():
    old = json.loads(
        (ROOT / "docs/assets/reponderacao_cenarios/010e789ca6361ba3.json").read_text()
    )
    for params in (
        {},
        {"modo": "publicado"},
        {"idade": "idosos60", "presenca_relativa": -20, "branco_nulo_pp": 15},
        {"comparecimento": 95, "indecisos_flavio": 75, "vies_pp": 10},
    ):
        left, right = M.evaluate(DATA, params), M.evaluate(old, params)
        for key in ("flavio", "lula", "validos", "branco_nulo", "abstencao"):
            assert left[key] == right[key]
    assert DATA["central"]["flavio"] == pytest.approx(55.32369660392367)
    assert DATA["central_projection"]["flavio"] == pytest.approx(53.90182661768348)


def test_projection_does_not_learn_trend_from_house_level_differences():
    rows = [source(f"casa{i}", f"2026-10-{5+i:02}", 30 + i * 10) for i in range(3)]
    out = P.build({"referencia": "2026-10-09", "pesquisas": rows}, M.preferences)
    assert not out["trend"]["pnad"]["available"]
    assert all(
        v == 0
        for v in out["trend"]["pnad"]["inclinacoes_encolhidas_validos_pp_dia"].values()
    )


def test_binary_within_house_trend_activates_and_projects_to_runoff_date():
    rows = [
        source(house, f"2026-10-{day:02}", 40 + day + shift)
        for house, shift in (("a", 0), ("b", 5))
        for day in (5, 6, 7, 8)
    ]
    out = P.build({"referencia": "2026-10-09", "pesquisas": rows}, M.preferences)
    fitted = out["trend"]["pnad"]
    assert fitted["available"]
    assert len(out["selected"]) == 2
    assert fitted["horizonte_dias"] == 17
    assert fitted["inclinacoes_encolhidas_validos_pp_dia"]["flavio"] > 0
    assert fitted["inclinacoes_encolhidas_validos_pp_dia"]["outros"] == 0
    assert sum(out["anchors"]["pnad"].values()) == pytest.approx(100)
    assert out["anchors"]["pnad"]["flavio"] > 50.5
    assert (
        base.sloped_central(out["selected"], [], date(2026, 10, 9))["horizonte_dias"]
        == 0
    )


def test_latest_incomplete_house_is_not_replaced_with_older_complete_wave():
    old = source("a", "2026-10-06", 49)
    incomplete = source("a", "2026-10-08", 50)
    del incomplete["publicado"]["2t"]["lula"]
    future = source("b", "2026-10-10", 10)
    rows = [old, incomplete, source("b", "2026-10-07", 50), future]
    out = P.build({"referencia": "2026-10-09", "pesquisas": rows}, M.preferences)
    assert [p["instituto"] for p in out["selected"]] == ["b"]
    assert out["selected"][0]["id"] == "b_2026-10-07"
    assert any(p["id"] == incomplete["id"] for p in out["excluded"])


@pytest.mark.parametrize(
    "params",
    [
        {},
        {"modo": "publicado", "comparecimento": 95, "presenca_relativa": 30},
        {
            "idade": "idosos60",
            "indecisos_flavio": 75,
            "indecisos_validos": 30,
            "branco_nulo_pp": 8,
            "nulo_diferencial_pp": 20,
            "vies_pp": -7,
        },
    ],
)
def test_projection_python_browser_parity_simulations_and_shared_links(params):
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node ausente")
    params = {"centro": "projecao", **params}
    script = """const fs=require('fs'),m=require('./docs/assets/reponderacao_simulador_motor.js');
const {data,p}=JSON.parse(fs.readFileSync(0,'utf8'));
process.stdout.write(JSON.stringify({result:m.evaluate(data,p),mc:m.simulate(data,p),decoded:m.decode(data,m.encode(data,p))}));"""
    actual = json.loads(
        subprocess.check_output(
            [node, "-e", script],
            input=json.dumps({"data": DATA, "p": params}),
            text=True,
            cwd=ROOT,
        )
    )
    expected = M.evaluate(DATA, params)
    assert actual["decoded"] == expected["parametros"]
    for k in ("flavio", "lula", "validos", "branco_nulo", "abstencao"):
        assert actual["result"][k] == pytest.approx(expected[k], abs=1e-10)
    assert sum(expected["por_100_eleitores"].values()) == pytest.approx(100)
    mc = M.simulate(DATA, params)
    assert actual["mc"]["runs"] == mc["runs"] == 2000
    assert actual["mc"]["share_flavio_ahead"] == mc["share_flavio_ahead"]
    for k in ("flavio", "lula", "gap"):
        assert actual["mc"][k] == pytest.approx(mc[k], abs=1e-10)
    for k, values in mc["totals"].items():
        assert actual["mc"]["totals"][k] == pytest.approx(values, abs=1e-6)
    assert all(
        sum(draw) == pytest.approx(100, abs=3e-8)
        for draw in DATA["projection"]["mc"]["draws"]["pnad"]
    )


def test_snapshot_encoding_and_sources_are_exact_reproducible_and_compact():
    assert json.loads(P.encode(DATA)) == DATA
    assert len(P.encode(DATA).splitlines()) < 1000
    for path, digest in DATA["projection"]["shared_sources"].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest
    assert (
        DATA["projection"]["adapter_sha256"]
        == hashlib.sha256(Path(P.__file__).read_bytes()).hexdigest()
    )
    assert DATA["projection"]["uncertainty"] == M.simulate(DATA)
    assert (
        P.build(RAW, M.preferences)["mc"]["draws"] == DATA["projection"]["mc"]["draws"]
    )


def test_invalid_central_or_projection_in_an_old_snapshot_fails_explicitly():
    invalid = [{"centro": "inventada"}, {"centro": None}, {"centro": ""}, {"centro": 0}]
    for p in invalid:
        with pytest.raises(ValueError):
            M.evaluate(DATA, p)
    node = shutil.which("node")
    if node:
        script = """const fs=require('fs'),m=require('./docs/assets/reponderacao_simulador_motor.js');
const {data,cases}=JSON.parse(fs.readFileSync(0,'utf8'));
process.stdout.write(JSON.stringify(cases.map(p=>{try{m.evaluate(data,p);return false;}catch{return true;}})));"""
        failures = json.loads(
            subprocess.check_output(
                [node, "-e", script],
                input=json.dumps({"data": DATA, "cases": invalid}),
                text=True,
                cwd=ROOT,
            )
        )
        assert all(failures)
    old = deepcopy(DATA)
    del old["projection"]
    with pytest.raises(ValueError, match="não disponível"):
        M.evaluate(old, {"centro": "projecao"})


def test_state_update_is_documented_by_field_date_and_never_added_as_national_house():
    s = DATA["projection"]["states"]
    assert s["covered_ufs"] == ["DF"]
    assert s["covered_electorate"] == 2_258_320
    assert s["electorate"] == DATA["electorate"]["total"]
    assert s["coverage_pct"] == pytest.approx(1.4308653402587033)
    row = s["selected"][0]
    assert row["campo"] == {"inicio": "2026-10-06", "fim": "2026-10-07"}
    assert row["divulgacao"] == "2026-10-09" and row["n"] == 910
    assert row["publicado"] == {
        "flavio": 49,
        "lula": 43,
        "branco_nulo": 6,
        "indecisos": 2,
    }
    assert row["validos_publicados"] == {"flavio": 54, "lula": 46}
    assert row["validos_normalizados"]["flavio"] == pytest.approx(100 * 49 / 92)
    assert not row["income_available"]
    assert row["id"] not in [p["id"] for p in DATA["projection"]["selected"]]
    source_text = (ROOT / row["source"]["arquivo"]).read_text()
    assert "49%" in source_text and "43%" in source_text
    assert row["registro_tse"] in source_text and "quarta-feira (7)" in source_text


def test_explanations_work_without_javascript_and_distinguish_validation():
    page = BeautifulSoup(
        (ROOT / "docs/reponderacao_pnad.html").read_text(), "html.parser"
    )
    cards = page.select(".rs-central-card")
    assert len(cards) == 2
    assert [c.select_one("button")["data-rs-central"] for c in cards] == [
        "media",
        "projecao",
    ]
    assert "55,3% × 44,7%" in cards[0].get_text()
    assert "53,9% × 46,1%" in cards[1].get_text()
    assert all(c.select_one("details > summary").has_attr("aria-label") for c in cards)
    assert (
        "machine learning supervisionado" in cards[1].select_one("details").get_text()
    )
    assert "insuficiente" in page.select_one("#modelo-projecao").get_text()
    assert (
        "não é chance de vitória medida"
        in page.select_one("#rs-uncertainty").get_text().lower()
    )


def test_extracting_shared_monte_carlo_kernel_preserves_first_round_draws():
    # Conferência contra o motor realmente publicado antes desta adaptação.
    original = subprocess.check_output(
        ["git", "show", "b57157e2:scripts/predicao_2026/motor.py"], cwd=ROOT, text=True
    )
    previous = dict(motor.__dict__)
    exec(compile(original, "motor_publicado_1t.py", "exec"), previous)
    old = json.loads(
        (ROOT / "docs/assets/predicao_2026_1T_presidente.json").read_text()
    )
    params = old["central"]["parametros"]
    expected = previous["simulate"](
        old["estados"], old["nacional"], params, runs=100, seed=42
    )
    actual = motor.simulate(old["estados"], old["nacional"], params, runs=100, seed=42)
    assert actual == expected
