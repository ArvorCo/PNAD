"""Conservação, denominadores, cronologia e reprodução Python/navegador."""

import hashlib
import importlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
M = importlib.import_module("reponderacao-simulador")
DATA = json.loads((ROOT / "docs/assets/reponderacao_simulador.json").read_text())


@pytest.mark.parametrize(
    "params",
    [
        {},
        {"presenca_relativa": -30},
        {"presenca_relativa": 30, "comparecimento": 95},
        {"branco_nulo_pp": -10},
        {"branco_nulo_pp": 20, "nulo_diferencial_pp": 20},
        {"indecisos_validos": 0},
        {"indecisos_flavio": 100},
        {"indecisos_flavio": 0, "nulo_diferencial_pp": -20, "vies_pp": -10},
        {"idade": "idosos60"},
        {"idade": "idosos80", "comparecimento": 40},
        {"modo": "publicado", "presenca_relativa": 0},
    ],
)
def test_physical_mass_conservation_under_stress(params):
    result = M.evaluate(DATA, params)
    assert result["flavio"] + result["lula"] == pytest.approx(100)
    assert sum(result["por_100_eleitores"].values()) == pytest.approx(100)
    assert result["validos"] + result["branco_nulo"] == pytest.approx(
        result["comparecimento"]
    )
    for poll in result["polls"]:
        assert poll["validos"] + poll["branco_nulo"] + poll[
            "abstencao"
        ] == pytest.approx(100)
        assert all(0 <= q <= 1 for q in poll["taxas"].values())
    assert all(v >= 0 for v in result["por_100_eleitores"].values())


def test_relative_presence_and_asymmetric_invalid_votes_have_correct_sign():
    low = M.evaluate(DATA, {"presenca_relativa": -5})
    high = M.evaluate(DATA, {"presenca_relativa": 10})
    central = M.evaluate(DATA)
    assert low["flavio"] < central["flavio"] < high["flavio"]
    assert M.evaluate(DATA, {"nulo_diferencial_pp": 5})["flavio"] < central["flavio"]
    assert M.evaluate(DATA, {"nulo_diferencial_pp": -5})["flavio"] > central["flavio"]
    assert central["diferenca_flavio_lula"] == pytest.approx(
        central["flavio"] - central["lula"]
    )


def test_uniform_nonchoice_changes_volume_not_valid_shares():
    central = M.evaluate(DATA)
    for params in (
        {"comparecimento": 60},
        {"branco_nulo_pp": 3},
        {"indecisos_validos": 0},
    ):
        result = M.evaluate(DATA, params)
        assert result["flavio"] == pytest.approx(central["flavio"])
        assert result["validos"] != pytest.approx(central["validos"])


def test_only_post_first_round_fields_enter_central_and_no_vox_imputation():
    assert all(p["campo"]["inicio"] > "2026-10-04" for p in DATA["polls"])
    assert {p["instituto"] for p in DATA["polls"]} == {"Datafolha", "PoderData"}
    assert any(p["id"] == "vox_brasil_2026-10-07" for p in DATA["excluded"])
    forecast = json.loads((ROOT / "docs/assets/reponderacao_validos.json").read_text())
    previous = forecast["ballots"]["2t"]["scenarios"]["flavio105"]["aggregate"][
        "modelo"
    ]
    assert DATA["central"]["flavio"] == pytest.approx(previous["flavio"])


@pytest.mark.parametrize(
    "params",
    [
        {"presenca_relativa": 31},
        {"comparecimento": float("nan")},
        {"indecisos_flavio": -1},
        {"modo": "inventado"},
    ],
)
def test_invalid_inputs_fail_explicitly(params):
    with pytest.raises(ValueError):
        M.evaluate(DATA, params)


def test_javascript_parity_and_link_roundtrip_with_all_controls():
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node ausente")
    cases = [
        {},
        {"presenca_relativa": -30, "comparecimento": 95},
        {
            "idade": "idosos60",
            "indecisos_validos": 50,
            "indecisos_flavio": 37.5,
            "branco_nulo_pp": -10,
            "nulo_diferencial_pp": -15,
            "vies_pp": 7,
        },
        {"modo": "publicado", "presenca_relativa": 0},
    ]
    script = """
const fs=require('fs'),m=require('./docs/assets/reponderacao_simulador_motor.js');
const {data,cases}=JSON.parse(fs.readFileSync(0,'utf8'));
process.stdout.write(JSON.stringify(cases.map(p=>({result:m.evaluate(data,p),decoded:m.decode(data,m.encode(data,p)),threshold:m.breakEven(data,p)}))));
"""
    output = subprocess.check_output(
        [node, "-e", script],
        input=json.dumps({"data": DATA, "cases": cases}),
        text=True,
        cwd=ROOT,
    )
    for params, actual in zip(cases, json.loads(output), strict=True):
        expected = M.evaluate(DATA, params)
        for k in (
            "flavio",
            "lula",
            "validos",
            "branco_nulo",
            "abstencao",
            "diferenca_flavio_lula",
        ):
            assert actual["result"][k] == pytest.approx(expected[k], abs=1e-10)
        assert actual["decoded"] == expected["parametros"]
        if actual["threshold"] is not None:
            assert M.evaluate(
                DATA, {**params, "presenca_relativa": actual["threshold"]}
            )["diferenca_flavio_lula"] == pytest.approx(0, abs=1e-7)


def test_public_routes_preserve_first_round_and_log_separately():
    page = BeautifulSoup(
        (ROOT / "docs/reponderacao_pnad.html").read_text(), "html.parser"
    )
    archive = BeautifulSoup(
        (ROOT / "docs/reponderacao_pnad_1o_turno_2026.html").read_text(), "html.parser"
    )
    log = BeautifulSoup(
        (ROOT / "docs/reponderacao_pnad_log.html").read_text(), "html.parser"
    )
    assert page.select_one("main > section")["id"] == "simulador"
    assert not page.select(
        '#primeiro-turno, #atualizacao, [data-ballot="1t"], [data-turno="1t"]'
    )
    assert all(
        card["data-research-turns"] == "2t" for card in page.select("article.poll")
    )
    assert archive.select_one("#primeiro-turno") and archive.select_one(
        "#institutos-1t"
    )
    assert log.select_one("#atualizacao") and log.select_one("#ondas")
    assert "83,89" in page.select_one("#vox-renda").get_text()
    assert DATA["defaults"]["presenca_relativa"] == 5
    snapshot = ROOT / f"docs/assets/reponderacao_cenarios/{DATA['version']}.json"
    assert json.loads(snapshot.read_text()) == DATA


def test_vox_evidence_distinguishes_registered_targets_and_unknown_income_concept():
    raw = json.loads(
        (
            ROOT / "analysis/reponderacao/pesquisas/vox_brasil_2026-10-07.json"
        ).read_text()
    )
    assert raw["ignorar"] and raw["cruzamentos"] == {}
    assert raw["fonte"]["total_paginas"] == 16
    audit = raw["fonte"]["auditoria_registro"]
    assert audit["alvos_renda_pct"] == [83.89, 12.42, 2.79, 0.9]
    assert audit["pergunta_renda"]["conceito"] == "não definido no instrumento"
    assert sum(
        raw["comparecimento_publicado"][k]
        for k in raw["comparecimento_publicado"]
        if k != "pagina"
    ) == pytest.approx(100)


def test_shared_version_preserves_its_calculation_engine():
    engine = ROOT / f"docs/assets/reponderacao_cenarios/motor-{DATA['engine']}.js"
    assert hashlib.sha256(engine.read_bytes()).hexdigest()[:16] == DATA["engine"]
    assert (
        engine.read_bytes()
        == (ROOT / "docs/assets/reponderacao_simulador_motor.js").read_bytes()
    )


def test_diary_is_idempotent_and_distinguishes_addition_from_revision(tmp_path):
    module = importlib.import_module("reponderacao-diario")
    manifest = tmp_path / "log.json"
    manifest.write_text(json.dumps({"waves": [], "changes": []}))
    folder = tmp_path / "polls"
    folder.mkdir()
    poll = folder / "wave.json"
    poll.write_text(json.dumps({"id": "wave", "n": 1000}))
    reference = {"gerado_em": "2026-10-09T12:00:00"}
    history = module.update(reference, manifest, folder)
    assert history["waves"] == [{"id": "wave", "added": "2026-10-09", "commit": None}]
    assert len(history["changes"]) == 1
    before = manifest.read_bytes()
    module.update(reference, manifest, folder)
    assert manifest.read_bytes() == before
    poll.write_text(json.dumps({"id": "wave", "n": 2000}))
    history = module.update({"gerado_em": "2026-10-10T12:00:00"}, manifest, folder)
    assert history["waves"][0]["added"] == "2026-10-09"
    assert len(history["changes"]) == 2
    assert (
        history["changes"][-1]["hashes_before"]["wave"]
        != history["changes"][-1]["hashes_after"]["wave"]
    )
