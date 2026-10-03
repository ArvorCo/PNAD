"""Conservação, temporalidade, calibração e paridade do forecast com o browser."""

import copy
import json
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from predicao_2026 import base, motor, recencia, tse  # noqa: E402


@pytest.fixture(scope="module")
def data():
    return json.loads(
        (ROOT / "docs/assets/predicao_2026_1T_presidente.json").read_text()
    )


def closed(result):
    for row in [result["brasil"], *result["regioes"].values(), *result["ufs"]]:
        valid = sum(row[k] for k in base.GROUPS[:3])
        assert row["eleitorado"] == pytest.approx(
            valid + row["branco_nulo"] + row["abstencao"], abs=1e-6
        )
        assert row["comparecimento"] == pytest.approx(
            valid + row["branco_nulo"], abs=1e-6
        )
        assert sum(row["demais"].values()) == pytest.approx(row["outros"], abs=1e-6)
        assert (
            min(row[k] for k in (*base.GROUPS[:3], "branco_nulo", "abstencao")) >= -1e-7
        )


CASES = [
    {},
    {"voto_lula": 1, "voto_flavio": 1},
    {"comparecimento_pp": -100},
    {"comparecimento_pp": 100},
    {"branco_nulo_pp": 100},
    {"branco_nulo_pp": -100},
    {"diferencial_pp": 35},
    {"diferencial_pp": -35},
    {"indecisos_validos": 0},
    {"indecisos_validos": 0.5, "indecisos_flavio": 0.6},
    {"vies_pp": 100},
    {"vies_pp": -100},
    {"exterior": False},
    {"eleitor_provavel": False},
    {"base": "publicado"},
    {"base": "todas"},
    {"base": "casas"},
    {"base": "pnad"},
    {"base": "sem_recencia"},
    {"comparecimento_modelo": "secoes", "secoes_abstencao_pp": 15},
    {
        "regioes": {"Nordeste": {"comparecimento_pp": -15}},
        "ufs": {
            "SP": {
                "comparecimento_pp": 20,
                "diferencial_pp": 20,
                "voto_flavio": 1,
                "voto_lula": 0,
            }
        },
    },
]


@pytest.mark.parametrize("params", CASES)
def test_conservation_under_scenarios(data, params):
    closed(motor.scenario(data["estados"], params))


def test_attendance_differential_preserves_total(data):
    a = motor.scenario(data["estados"])["brasil"]
    b = motor.scenario(data["estados"], {"diferencial_pp": 35})["brasil"]
    assert a["comparecimento"] == pytest.approx(b["comparecimento"], abs=1e-6)
    assert b["flavio"] > a["flavio"]
    assert b["lula"] < a["lula"]


def test_useful_vote_is_bounded_and_local(data):
    states = copy.deepcopy(data["estados"])
    s = next(x for x in states if x["uf"] == "SP")
    s["reserva"] = [100, 100]
    result = motor.scenario(states, {"ufs": {"SP": {"voto_flavio": 1, "voto_lula": 1}}})
    closed(result)
    row = next(x for x in result["ufs"] if x["uf"] == "SP")
    assert row["outros"] < 1e-6
    central = motor.scenario(states)
    for old, new in zip(central["ufs"], result["ufs"], strict=True):
        if new["uf"] != "SP":
            assert old == new


def test_raking_matches_weighted_national_margins():
    seed = [[0.8, 0.1, 0.1], [0.1, 0.2, 0.7], [0.2, 0.5, 0.3]]
    weights = [100, 300, 600]
    target = [0.31, 0.46, 0.23]
    q, _ = motor.rake(seed, weights, target)
    np.testing.assert_allclose(base.normalize(weights) @ q, target, atol=1e-10)
    np.testing.assert_allclose(q.sum(axis=1), 1, atol=1e-12)
    assert (q > 0).all()


def test_latest_prevents_future_leakage_and_duplicate_house():
    def p(ident, house, release, field):
        return {
            "id": ident,
            "instituto": house,
            "divulgacao": release,
            "campo": {"inicio": field, "fim": field},
        }

    rows = [
        p("old", "A", "2026-09-29", "2026-09-28"),
        p("new", "A", "2026-10-02", "2026-10-01"),
        p("old-republished", "A", "2026-10-03", "2026-09-28"),
        p("future", "B", "2026-10-04", "2026-10-02"),
        p("future-field", "C", "2026-10-03", "2026-10-04"),
        p("stale", "D", "2026-09-26", "2026-09-26"),
        p("unknown", "E", None, "2026-10-01"),
    ]
    assert [x["id"] for x in base.latest(rows, date(2026, 10, 3))] == ["new"]


def test_recency_uses_field_midpoint_and_halves_weight():
    field = {"inicio": "2026-09-29", "fim": "2026-10-01"}
    assert recencia.age(field, date(2026, 10, 3)) == 3
    assert recencia.decay(9, 3) / recencia.decay(3, 3) == pytest.approx(0.25)
    assert recencia.decay(14, 7) == pytest.approx(0.25)
    for invalid in (0, -1, np.inf, np.nan):
        with pytest.raises(ValueError):
            recencia.decay(0, invalid)


def test_inclusive_central_weights_and_vox(data):
    n = data["nacional"]
    selected = n["selecionadas"]
    expected = recencia.mean(selected, "previsao_vetor")
    np.testing.assert_allclose(expected, n["alvos"]["inclusivo"], atol=1e-12)
    assert sum(p["participacao_central_pct"] for p in selected) == pytest.approx(100)
    vox = [p for p in selected if "Vox" in p["instituto"]]
    assert len(vox) == 1
    assert vox[0]["registro"] == "BR-00148/2026"
    assert vox[0]["pnad_vetor"] is None
    assert vox[0]["previsao_vetor"] == vox[0]["publicado_vetor"]
    assert vox[0]["participacao_central_pct"] > 0
    for p in selected:
        assert p["peso_recencia"] == pytest.approx(
            recencia.decay(p["idade_campo_dias"], n["meia_vida_dias"])
        )
    np.testing.assert_allclose(
        np.mean([p["previsao_vetor"] for p in selected], axis=0),
        n["alvos"]["sem_recencia"],
        atol=1e-12,
    )


def test_weighted_bootstrap_retains_recency_in_expectation():
    polls = [{"peso_recencia": 1}, {"peso_recencia": 0.25}]
    w = recencia.weights(polls)
    draws = np.random.default_rng(19).dirichlet(2 * w, 20000)
    np.testing.assert_allclose(draws.mean(axis=0), w, atol=0.01)


def test_recent_state_sources_replace_old_waves_and_have_primary_proof(data):
    polls = [p for s in data["estados"] for p in s["pesquisas"]]
    new = [
        p for p in polls if p["arquivo"].startswith("analysis/predicao_2026/estaduais/")
    ]
    assert len(new) == data["qualidade"]["n_estaduais_novas_integradas"] == 34
    datafolha = sorted(p["uf"] for p in new if p["instituto"] == "Datafolha")
    assert datafolha == ["DF", "MG", "PE", "RJ", "SP"]
    assert len({(p["instituto"], p["uf"]) for p in polls}) == len(polls)
    quaest = [p for p in new if p["instituto"] == "Quaest"]
    assert len(quaest) == 25
    assert all(p["campo"]["fim"] >= "2026-09-21" for p in quaest)
    for p in new:
        assert len(p["sha256_relatorio"]) == 64
        assert p["fonte"].startswith("https://")
        assert p["sha256"] == tse.sha(ROOT / p["arquivo"])
        raw = base.read(ROOT / p["arquivo"])
        if p["instituto"] == "Quaest":
            assert raw["pres_2t"]["pagina"] > 0
            assert raw["comparecimento_compacto"]["pagina_voto"] > 0


def test_recent_turnout_crossbreaks_expose_missingness_and_bounds(data):
    assert data["qualidade"]["n_ufs_cruzamento_comparecimento"] == 25
    for s in data["estados"]:
        signal = s["sinal_comparecimento"]
        if not signal:
            continue
        poll = next(p for p in s["pesquisas"] if p["instituto"] == "Quaest")
        assert signal["fonte_sha256"] == poll["sha256_relatorio"]
        assert signal["cobertura_pct"] + signal["habito_nao_declarado_pct"] == 100
        lo, hi = np.array(signal["recomposicao_envelope_arredondamento_pct"])
        observed = 100 * np.array(poll["vetor"][:2])
        assert (observed + 0.5 >= lo).all() and (observed - 0.5 <= hi).all()
        assert (np.array(signal["fatores"]) > 0).all()


def test_rounding_envelope_admits_rounding_but_rejects_wrong_crossbreak():
    path = ROOT / "analysis/predicao_2026/estaduais/quaest_RO_20260923.json"
    raw = base.read(path)
    signal = base.compact_turnout(raw)
    assert signal["recomposicao_residuo_lula_flavio_pp"][1] == pytest.approx(-1.21)
    raw["comparecimento_compacto"]["sempre_vota"][1] -= 12
    raw["comparecimento_compacto"]["sempre_vota"][2] += 12
    with pytest.raises(ValueError, match="incompatível com placar"):
        base.compact_turnout(raw)


def test_rounding_envelope_for_complete_identical_groups():
    lo, hi = base.rounded_crossbreak_bounds(
        [80, 5, 10, 3, 2, 0], [40, 35, 15, 5, 5], [40, 35, 15, 5, 5]
    )
    assert lo[0] <= 39.5 and hi[0] >= 40.5
    assert hi[0] - lo[0] < 1.6
    assert lo[1] <= 34.5 and hi[1] >= 35.5


def test_rounding_negative_requires_adjusted_source():
    values = {
        "lula": 43,
        "flavio": 42,
        "renan": 10,
        "indecisos": 2,
        "branco_nulo": 3,
        "other": -0.15,
    }
    with pytest.raises(ValueError):
        base.grouped(values)
    vector, audit = base.grouped(values, adjusted=True)
    assert vector.sum() == pytest.approx(1)
    assert audit["negativos_truncados_pp"] == 0.15
    with pytest.raises(ValueError):
        base.normalize([1, np.nan])


def test_section_key_normalizes_municipality_zeros():
    a = {"SG_UF": "SP", "CD_MUNICIPIO": "00123", "NR_ZONA": "01", "NR_SECAO": "0007"}
    b = {**a, "CD_MUNICIPIO": "123", "NR_ZONA": "1", "NR_SECAO": "7"}
    assert tse.key(a) == tse.key(b)
    assert tse.age_lower("70 a 74 anos") == 70
    assert tse.age_lower("Inválida") is None


def test_public_package_has_coverage_and_no_future_input(data):
    cutoff = data["referencia"]
    assert {s["uf"] for s in data["estados"]} == set(base.UF_REGION)
    assert len(data["central"]["ufs"]) == 28
    assert all(
        not any(check["diferencas"]) for check in data["tse_metadata"]["validacao_2022"]
    )
    assert data["qualidade"]["demografia_uf_sem_imputacao_secao"]
    for poll in data["nacional"]["pesquisas"]:
        assert poll["divulgacao"] <= cutoff
        assert poll["campo"]["fim"] <= cutoff
    for state in data["estados"]:
        for poll in state["pesquisas"]:
            assert poll["campo"]["fim"] <= cutoff
            assert poll["divulgacao"] is None or poll["divulgacao"] <= cutoff
            assert len(poll["sha256"]) == 64
    domestic = [s for s in data["estados"] if s["uf"] != "ZZ"]
    for name, target in data["nacional"]["alvos"].items():
        actual = np.average(
            [s["bases"][name] for s in domestic],
            axis=0,
            weights=[s["eleitorado"] for s in domestic],
        )
        np.testing.assert_allclose(actual, target, atol=1e-10)
    closed(data["central"])


def test_uncertainty_reproducible_and_common_error_matters(data):
    args = (data["estados"], data["nacional"])
    a = motor.simulate(*args, runs=700, seed=22)
    assert a == motor.simulate(*args, runs=700, seed=22)
    zero = motor.simulate(*args, runs=700, seed=22, common_sd_pp=0)
    assert (
        a["margem"]["p95"] - a["margem"]["p05"]
        > zero["margem"]["p95"] - zero["margem"]["p05"]
    )
    assert sum(a["distribuicao_margem"]) == 700
    assert all(
        0 <= a[k] <= 1
        for k in ("p_flavio_a_frente_de_lula", "p_lula_maioria", "p_flavio_maioria")
    )


def test_browser_engine_matches_python(data):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node necessário para verificar a paridade com o navegador")
    js = """const fs=require('fs'), engine=require(process.argv[1]);
    const x=JSON.parse(fs.readFileSync(0,'utf8'));
    process.stdout.write(JSON.stringify(x.cases.map(p=>engine.scenario(x.states,p))));"""
    run = subprocess.run(
        [node, "-e", js, str(ROOT / "docs/assets/predicao_2026.js")],
        input=json.dumps({"states": data["estados"], "cases": CASES}),
        capture_output=True,
        text=True,
        check=True,
    )
    results = json.loads(run.stdout)
    for params, browser in zip(CASES, results, strict=True):
        python = motor.scenario(data["estados"], params)
        for left, right in [
            (python["brasil"], browser["brasil"]),
            *zip(python["ufs"], browser["ufs"], strict=True),
        ]:
            for k in (
                "lula",
                "flavio",
                "outros",
                "comparecimento",
                "abstencao",
                "branco_nulo",
            ):
                assert left[k] == pytest.approx(right[k], abs=1e-6, rel=1e-12)
        closed(browser)


def test_browser_uncertainty_accepts_every_temporal_anchor(data):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node necessário para verificar a simulação no navegador")
    script = """const fs=require('fs'), engine=require(process.argv[1]);
    const x=JSON.parse(fs.readFileSync(0,'utf8'));
    (async()=>{const out={};for(const base of Object.keys(x.nacional.alvos).concat('casas'))
      out[base]=await engine.simulate(x,{base},()=>{},()=>false,100);
    process.stdout.write(JSON.stringify(out));})();"""
    run = subprocess.run(
        [node, "-e", script, str(ROOT / "docs/assets/predicao_2026.js")],
        input=json.dumps(data),
        capture_output=True,
        text=True,
        check=True,
    )
    for result in json.loads(run.stdout).values():
        assert result["runs"] == 100
        assert -100 <= result["margem"][0] <= result["margem"][1] <= 100
        for interval in result["intervalos"].values():
            assert 0 <= interval[0] <= interval[1] <= interval[2] <= 100


def test_page_static_fallback_and_documented_limits():
    html = (ROOT / "docs/predicao_2026_1T_presidente.html").read_text()
    assert "{{" not in html
    assert "—" not in html
    assert 'id="prediction-data"' in html
    assert "probabilidades não calibradas" in html
    assert "não valida os coeficientes de renda, voto útil ou preferência" in html
    assert "predicao_2026-responsive.css" in html
    assert "<noscript>" in html


def test_pre_election_cli_rejects_post_election():
    run = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/predicao-2026-build.py"),
            "--hoje",
            "2026-10-05",
            "--skip-card",
        ],
        text=True,
        capture_output=True,
    )
    assert run.returncode == 2
    assert "Corte pós-eleição" in run.stderr


def test_tse_registry_cannot_leak_into_an_earlier_cutoff(monkeypatch):
    builder = base.module("predicao-2026-build")
    monkeypatch.setattr(
        builder,
        "read",
        lambda _: {
            "locais_metadata": {"DT_GERACAO": "02/10/2026"},
            "perfil_metadata": {"DT_GERACAO": "14/07/2026"},
        },
    )
    with pytest.raises(ValueError, match="Cadastro TSE posterior ao corte"):
        builder.build(date(2026, 10, 1))


def test_futura_eve_wave_replaces_september_29_in_central(data):
    selected = data["nacional"]["selecionadas"]
    futura = [p for p in selected if p["instituto"] == "Futura"]
    assert [p["id"] for p in futura] == ["futura_2026-10-03"]
    assert futura[0]["registro"] == "BR-02431/2026"
    assert futura[0]["pnad_vetor"] is None
    assert futura[0]["previsao_vetor"] == futura[0]["publicado_vetor"]
    assert futura[0]["opcoes_publicadas"]["flavio"] == 42.5
    assert futura[0]["opcoes_publicadas"]["lula"] == 40.5
    assert futura[0]["participacao_central_pct"] > 0
