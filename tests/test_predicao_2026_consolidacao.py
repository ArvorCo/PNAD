"""Consolidação medida: regressão com efeito de casa, λ e cenários prontos."""

import json
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from predicao_2026 import consolidacao, motor, simulador  # noqa: E402

JS = ROOT / "docs/assets/predicao_2026.js"
PAGE = ROOT / "docs/predicao_2026_1T_presidente.html"
CONS_IDS = ("consolidacao_28", "consolidacao_14")


@pytest.fixture(scope="module")
def data():
    return json.loads(
        (ROOT / "docs/assets/predicao_2026_1T_presidente.json").read_text()
    )


def synthetic(slopes, levels, ages, noise=0.0, seed=1):
    """Ondas com nível próprio por casa e tendência comum, nos válidos."""
    rng = np.random.default_rng(seed)
    polls = []
    for j, (house, level) in enumerate(levels.items()):
        for i, a in enumerate(ages):
            age = float(a + 0.5 * j)  # casas em datas diferentes
            share = np.array(level) - np.array(slopes) * age
            share[:2] += rng.normal(0, noise, 2)
            share[2] = 100 - share[:2].sum()
            polls.append(
                {
                    "id": f"{house}_{i}",
                    "instituto": house,
                    "idade_campo_dias": age,
                    "n": 1000 + 500 * i,
                    "publicado_vetor": [*(0.9 * share / 100), 0.04, 0.06],
                }
            )
    return polls


SLOPES = (0.13, 0.19, -0.32)
LEVELS = {
    "A": (45.0, 40.0, 15.0),
    "B": (42.0, 44.0, 14.0),
    "C": (47.0, 39.0, 14.0),
    "D": (44.0, 42.0, 14.0),
}


def test_regression_recovers_known_slopes_with_house_effects():
    polls = synthetic(SLOPES, LEVELS, ages=(2, 9, 16, 24))
    fit = consolidacao.regression(polls, 28)
    for k, expected in zip(consolidacao.KEYS, SLOPES, strict=True):
        assert fit["inclinacao_pp_dia"][k] == pytest.approx(expected, abs=1e-9)
    assert sum(fit["inclinacao_pp_dia"].values()) == pytest.approx(0, abs=1e-9)
    assert fit["divisao"]["flavio"] == pytest.approx(0.19 / 0.32, abs=1e-9)
    assert fit["n_casas"] == 4 and fit["n_ondas"] == 16


def test_house_levels_alone_do_not_create_a_trend():
    # Sem efeito fixo, casas diferentes em datas diferentes simulariam tendência.
    polls = synthetic((0, 0, 0), LEVELS, ages=(3, 20))
    for p in polls:
        if p["instituto"] in ("B", "D"):
            p["idade_campo_dias"] += 5
    fit = consolidacao.regression(polls, 28)
    for v in fit["inclinacao_pp_dia"].values():
        assert v == pytest.approx(0, abs=1e-9)
    assert fit["divisao"]["derrete"] is False


def test_noisy_recovery_and_delta_standard_error():
    polls = synthetic(SLOPES, LEVELS, ages=(1, 4, 8, 12, 17, 22, 27), noise=0.8)
    fit = consolidacao.regression(polls, 28)
    for k, expected in zip(consolidacao.KEYS, SLOPES, strict=True):
        se = fit["erro_padrao_pp_dia"][k]
        assert se > 0
        assert abs(fit["inclinacao_pp_dia"][k] - expected) < 4 * se
    assert 0 < fit["divisao"]["erro_padrao"] < 0.5


def test_window_requires_repeated_waves():
    polls = synthetic(SLOPES, {"A": LEVELS["A"]}, ages=(2,))
    with pytest.raises(ValueError):
        consolidacao.regression(polls, 28)


@pytest.mark.parametrize("horizon", [0, 1, 5.7, 40, 400])
def test_lambda_is_bounded_and_cap_is_recorded(horizon):
    fit = consolidacao.regression(synthetic(SLOPES, LEVELS, ages=(2, 9, 16)), 28)
    proj = consolidacao.projection(fit, horizon, [0.05, 0.08])
    for k in ("lula", "flavio"):
        assert 0 <= proj["lambda"][k] <= 1
        need = proj["migracao_pp"][k] / 100
        assert proj["teto_atingido"][k] is (need > (0.05, 0.08)[k == "flavio"])
    if horizon == 400:
        assert proj["teto_atingido"] == {"lula": True, "flavio": True}
        assert proj["lambda"] == {"lula": 1.0, "flavio": 1.0}


def test_published_block_is_consistent(data):
    cons = data["consolidacao"]
    assert "não medição da urna" in cons["nota"]
    sel = data["nacional"]["selecionadas"]
    age = sum(p["idade_campo_dias"] * p["participacao_central_pct"] for p in sel)
    age /= sum(p["participacao_central_pct"] for p in sel)
    assert cons["idade_efetiva_ancora_dias"] == pytest.approx(age)
    days = (
        date.fromisoformat(data["eleicao"]) - date.fromisoformat(data["referencia"])
    ).days
    assert cons["horizonte_dias"] == pytest.approx(days + age)
    reserve = consolidacao.national_reserve(data["estados"])
    for key in ("28", "14"):
        fit, proj = cons["janelas"][key], cons["projecao"][key]
        assert fit["janela_dias"] == int(key)
        assert len(fit["pesos"]) == fit["n_ondas"]
        assert all(0 < w <= 2000 for w in fit["pesos"].values())
        for k, r in zip(("lula", "flavio"), reserve, strict=True):
            lam = proj["lambda"][k]
            assert 0 <= lam <= 1
            if not proj["teto_atingido"][k]:
                assert lam * r * 100 == pytest.approx(proj["migracao_pp"][k])
    sens = data["sensibilidades"]["Consolidação na proporção medida, 28 dias"]
    assert cons["ancora"] == "inclusivo"
    params = {
        **data["central"]["parametros"],
        "base": "inclusivo",
        "voto_lula": cons["projecao"]["28"]["lambda_arredondado"]["lula"],
        "voto_flavio": cons["projecao"]["28"]["lambda_arredondado"]["flavio"],
    }
    fresh = motor.scenario(data["estados"], params)["brasil"]
    for k in ("lula", "flavio", "outros", "margem_flavio_lula"):
        assert sens["brasil"][k] == pytest.approx(fresh[k])


def test_presets_follow_central_and_carry_measured_lambda(data):
    ready = simulador.presets(data)
    assert [p["id"] for p in ready[:3]] == ["central", *CONS_IDS]
    for preset, key in zip(ready[1:3], ("28", "14"), strict=True):
        lam = data["consolidacao"]["projecao"][key]["lambda_arredondado"]
        assert preset["parametros"] == {
            "base": "inclusivo",
            "voto_flavio": lam["flavio"],
            "voto_lula": lam["lula"],
        }
        assert all(
            round(v, 2) == v for k, v in preset["parametros"].items() if k != "base"
        )
        assert "recência sem tendência" in preset["frase"]
        assert preset["destaque"] is True
        assert "Divisão medida" in preset["nota"]
        assert "—" not in preset["nome"] + preset["frase"] + preset["nota"]


def test_presets_are_identical_and_equivalent_in_python_and_js(data):
    exe = shutil.which("node")
    if not exe:
        pytest.skip("Node necessário para verificar o simulador do navegador")
    html = PAGE.read_text()
    match = re.search(
        r'<script type="application/json" id="sim-presets-data">(.*?)</script>',
        html,
        re.DOTALL,
    )
    assert match is not None
    embedded = json.loads(match.group(1))
    python = {p["id"]: p for p in simulador.presets(data)}
    for p in embedded:
        assert p["parametros"] == python[p["id"]]["parametros"]
    chosen = [p for p in embedded if p["id"] in CONS_IDS]
    assert len(chosen) == 2
    script = """const fs=require('fs'),engine=require(process.argv[1]),S=engine.Simulador;
    const x=JSON.parse(fs.readFileSync(0,'utf8'));const C=S.configure(x.central);const c=engine.scenario(x.states,C).brasil;
    process.stdout.write(JSON.stringify(x.presets.map(p=>{const r=engine.scenario(x.states,{...C,...p.parametros});
      return {r,sentence:S.sentence(p.parametros,c,r.brasil,p.nota)};})));"""
    out = json.loads(
        subprocess.run(
            [exe, "-e", script, str(JS)],
            input=json.dumps(
                {
                    "states": data["estados"],
                    "presets": chosen,
                    "central": data["central"]["parametros"],
                }
            ),
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    )
    for preset, js in zip(chosen, out, strict=True):
        py = motor.scenario(
            data["estados"], {**data["central"]["parametros"], **preset["parametros"]}
        )
        for left, right in [
            (py["brasil"], js["r"]["brasil"]),
            *zip(py["ufs"], js["r"]["ufs"], strict=True),
        ]:
            for k in ("lula", "flavio", "outros", "comparecimento", "branco_nulo"):
                assert left[k] == pytest.approx(right[k], abs=1e-6, rel=1e-12)
        assert js["sentence"].endswith(preset["nota"])
        assert "Divisão medida nas pesquisas" in js["sentence"]


def test_page_has_resolved_consolidation_block(data):
    html = PAGE.read_text()
    match = re.search(r'<div class="sim-consolidacao".*?</div>', html, re.DOTALL)
    assert match is not None
    block = match.group(0)
    assert "{{" not in block and "—" not in html
    for phrase in (
        "tendência medida nas pesquisas",
        "extrapolação linear",
        "não medição da urna",
        "Lula também sobe",
        "metade",
    ):
        assert phrase in block.lower() or phrase in block
    slope = data["consolidacao"]["janelas"]["28"]["inclinacao_pp_dia"]["terceira_via"]
    shown = f"{abs(slope):.2f}".replace(".", ",")
    assert f"−{shown} ponto por dia" in block
    assert html.index(block) < html.index('id="simulador-app"')
    assert 'class="preset featured"' in html
    assert 'id="help-consolidacao"' in html
