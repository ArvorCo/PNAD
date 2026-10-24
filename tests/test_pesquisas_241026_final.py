"""Dois universos Quaest, renda Atlas e integração sem dupla seleção."""

import gzip
import hashlib
import importlib
import json
import shutil
import subprocess
from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest
from reponderacao_vista.historico_2t import history
from reponderacao_vista.historico_2t_chart import segments
from reponderacao_vista.historico_projecao import projected_row

ROOT = Path(__file__).resolve().parents[1]
ROUND = importlib.import_module("pesquisas-241026-final-renda")
SIM = importlib.import_module("reponderacao-simulador")
PROJECTION = importlib.import_module("reponderacao-projecao")
LIKELY = importlib.import_module("reponderacao-likely")
DATA = json.loads((ROOT / "docs/assets/reponderacao_simulador.json").read_text())


@pytest.mark.parametrize("name", ["quaest", "atlas"])
def test_sources_transcriptions_and_hashes(name, assert_json_close):
    poll = getattr(ROUND, name)()
    assert_json_close(
        poll,
        json.loads(
            (
                ROOT / "analysis/reponderacao/pesquisas" / (poll["id"] + ".json")
            ).read_text()
        ),
    )
    refs = json.loads(
        (ROOT / f"data/originals/{name}_102026_24/fonte.json").read_text()
    )
    for entry in refs["arquivos"]:
        assert (
            hashlib.sha256((ROOT / entry["arquivo"]).read_bytes()).hexdigest()
            == entry["sha256"]
        )
    if name == "atlas":
        assert sum(poll["renda"]["amostra_pct"]) == pytest.approx(100)
        assert "indecisos" not in poll["publicado"]["2t"]
        for control in poll["controles"]["2t"].values():
            assert control["residuo_max_abs"] < 0.7
    else:
        article = gzip.decompress(
            (ROOT / "data/originals/quaest_102026_24/divulgacao.html.gz").read_bytes()
        ).decode()
        assert "likely voter" in article and "3.702" in article
        assert "Access Denied" not in article
        assert poll["ignorar"] and "renda" not in poll
        assert poll["publicado"]["2t"] == {
            "flavio": 46,
            "lula": 45,
            "branco_nulo": 8,
            "indecisos": 1,
        }
        assert poll["eleitor_provavel_oficial"]["validos"] == {"flavio": 51, "lula": 49}


def test_one_wave_one_house_no_borrowed_income_or_trend():
    selected = DATA["projection"]["selected"]
    assert len(selected) == len({p["instituto"] for p in selected})
    assert sum(p["weight"] for p in selected) == pytest.approx(1)
    quaest = next(p for p in selected if p["instituto"] == "Quaest")
    assert quaest["id"] == "quaest_2026-10-24" and not quaest["income_available"]
    assert "Quaest" not in {p["instituto"] for p in DATA["polls"]}
    assert (
        next(p for p in DATA["polls"] if p["instituto"] == "AtlasIntel")["id"]
        == "atlas_2026-10-23"
    )
    assert DATA["projection"]["official"]["weight"] == quaest["weight"]
    raw = json.loads((ROOT / "docs/assets/reponderacao_pnad.json").read_text())
    reduced = {
        **raw,
        **{
            key: [p for p in raw[key] if p["instituto"] != "Quaest"]
            for key in ("pesquisas", "nao_reponderaveis")
        },
    }
    fitted = PROJECTION.build(reduced, SIM.preferences)
    for kind in ("published", "pnad"):
        assert DATA["projection"]["anchors"][kind] == pytest.approx(
            fitted["anchors"][kind]
        )


@pytest.mark.parametrize(
    "extra",
    [
        {},
        {"modo": "publicado", "presenca_relativa": -30, "comparecimento": 95},
        {
            "modo": "modelo",
            "presenca_relativa": 30,
            "idade": "idosos80",
            "indecisos_flavio": 0,
            "indecisos_validos": 0,
        },
        {
            "modo": "pnad",
            "indecisos_flavio": 100,
            "branco_nulo_pp": 20,
            "comparecimento": 40,
        },
    ],
)
def test_official_share_is_immune_to_presence_income_and_undecided_controls(extra):
    data = deepcopy(DATA)
    data["projection"]["official"]["weight"] = 1
    result = SIM.evaluate(data, {"centro": "projecao", **extra})
    assert result["flavio"] == pytest.approx(51)
    assert result["lula"] == pytest.approx(49)
    assert sum(result["por_100_eleitores"].values()) == pytest.approx(100)
    u = SIM.undecided(data, {"centro": "projecao", **extra})
    assert u["present_total"] == u["to_flavio"] == u["to_lula"] == 0


def test_mixture_is_recency_weighted_and_preserves_nonchoice():
    ordinary = deepcopy(DATA)
    official = ordinary["projection"].pop("official")
    baseline = SIM.evaluate(ordinary, {"centro": "projecao"})
    actual = SIM.evaluate(DATA, {"centro": "projecao"})
    assert actual["flavio"] == pytest.approx(
        (1 - official["weight"]) * baseline["flavio"] + official["weight"] * 51
    )
    assert actual["validos"] == pytest.approx(baseline["validos"])
    assert actual["branco_nulo"] == pytest.approx(baseline["branco_nulo"])
    assert SIM.undecided(DATA, {"centro": "projecao"})["survey_pct"] == pytest.approx(
        (1 - official["weight"])
        * SIM.undecided(ordinary, {"centro": "projecao"})["survey_pct"]
    )


def test_bootstrap_uses_shared_common_error_and_joint_house_weights():
    selected = [
        {"n": 2000, "weight": 0.5, "publicado_vetor": [0.49, 0.51, 0, 0, 0]},
        {"n": 2000, "weight": 0.5, "official_valids": {"flavio": 51, "lula": 49}},
    ]
    regular, official = LIKELY.draws(
        selected,
        "publicado_vetor",
        {"vetor": [0.49, 0.51, 0, 0, 0], "dp_margem_projecao_pp": 0},
        20000,
        123,
    )
    official = np.asarray(official)
    assert 0.48 < official[:, 0].mean() < 0.52
    assert np.corrcoef(regular[:, 1], official[:, 1])[0, 1] > 0.2
    assert np.allclose(regular.sum(axis=1), 1)
    assert (official[:, 0] > 0).all() and (official[:, 0] < 1).all()


def test_documentary_graph_does_not_join_different_universes():
    rows = [p for p in history() if p["instituto"] == "Quaest"]
    latest = rows[-1]
    assert latest["placar"]["flavio"] == 46
    projected = [projected_row(p) for p in rows]
    assert projected[-1]["placar"] == {"flavio": 51, "lula": 49}
    assert projected[-1]["pnad"] is None
    assert len(segments(projected, "placar")[-1]) == 1
    assert len(segments(rows, "placar")[-1]) > 1
    assert projected[-1]["projecao"]["modos"]["placar"]["delta_presenca_pp"] is None


def test_undecided_python_browser_parity():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node ausente")
    p = {"centro": "projecao", "indecisos_flavio": 75, "indecisos_validos": 30}
    code = "const fs=require('fs'),m=require('./docs/assets/reponderacao_simulador_motor.js');const {data,p}=JSON.parse(fs.readFileSync(0,'utf8'));process.stdout.write(JSON.stringify(m.undecided(data,p)));"
    actual = json.loads(
        subprocess.check_output(
            [node, "-e", code],
            input=json.dumps({"data": DATA, "p": p}),
            text=True,
            cwd=ROOT,
        )
    )
    expected = SIM.undecided(DATA, p)
    for key, value in expected.items():
        assert actual[key] == (
            pytest.approx(value, abs=1e-6) if isinstance(value, (float, int)) else value
        )
