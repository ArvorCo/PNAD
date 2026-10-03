"""Central nova: recência com tendência encolhida e indecisos por disponibilidade.

Confere os dois motores (Python e navegador), o recentramento do Monte Carlo,
o choque da projeção, o ponto de partida dos cenários de consolidação e os
blocos de texto da página."""

import json
import math
import re
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest
from predicao_2026 import motor, simulador

ROOT = Path(__file__).resolve().parents[1]

JS = ROOT / "docs/assets/predicao_2026.js"
PAGE = ROOT / "docs/predicao_2026_1T_presidente.html"
FIELDS = ("lula", "flavio", "outros", "comparecimento", "abstencao", "branco_nulo")


@pytest.fixture(scope="module")
def data():
    return json.loads(
        (ROOT / "docs/assets/predicao_2026_1T_presidente.json").read_text()
    )


def node(script, payload):
    exe = shutil.which("node")
    if not exe:
        pytest.skip("Node necessário para verificar o motor do navegador")
    run = subprocess.run(
        [exe, "-e", script, str(JS)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(run.stdout)


def test_central_is_sloped_anchor_with_availability(data):
    params = data["central"]["parametros"]
    assert motor.DEFAULTS["base"] == "central_inclinacao"
    assert params["base"] == "central_inclinacao"
    assert params["indecisos_flavio"] == data["rejeicao"]["indecisos_flavio"]
    assert data["configuracao"]["central"] == params
    fresh = motor.scenario(data["estados"], params)["brasil"]
    for k in (*FIELDS, "margem_flavio_lula"):
        assert data["central"]["brasil"][k] == pytest.approx(fresh[k])
    first = next(iter(data["sensibilidades"]))
    assert first.startswith("Central: recência com tendência")
    assert data["sensibilidades"][first]["brasil"] == data["central"]["brasil"]
    old = data["sensibilidades"]["Recência sem tendência (central anterior)"]
    assert old["parametros"]["base"] == "inclusivo"
    assert old["parametros"]["indecisos_flavio"] is None


def test_browser_central_matches_python_and_is_detected(data):
    script = """const fs=require('fs'),engine=require(process.argv[1]),S=engine.Simulador;
    const x=JSON.parse(fs.readFileSync(0,'utf8'));const C=S.configure(x.central);
    const prop={...C,indecisos_flavio:null},code=S.encode(prop);
    process.stdout.write(JSON.stringify({r:engine.scenario(x.states,C),central:S.isCentral(C),
      empty:S.encode({}),code,back:S.decode(code).indecisos_flavio,base:S.decode('').base,
      sentence:S.describe(prop),old:S.describe({base:'inclusivo'})}));"""
    params = data["central"]["parametros"]
    out = node(script, {"states": data["estados"], "central": params})
    py = motor.scenario(data["estados"], params)
    for left, right in [
        (py["brasil"], out["r"]["brasil"]),
        *zip(py["ufs"], out["r"]["ufs"], strict=True),
    ]:
        for k in FIELDS:
            assert left[k] == pytest.approx(right[k], abs=1e-6, rel=1e-12)
    assert out["central"] is True and out["empty"] == ""
    # Proporcional difere da central nova e vira "if:p" no link.
    assert out["code"] == "if:p" and out["back"] is None
    assert out["base"] == "central_inclinacao"
    assert out["sentence"] == ["indecisos que escolhem proporcionais às candidaturas"]
    assert "sem tendência" in out["old"][0]


def test_bootstrap_is_recentred_for_every_anchor_on_central_houses(data):
    n = data["nacional"]
    for base in ("central_inclinacao", "dinamico", "tendencia", "tendencia_corte"):
        polls, kind, shift = motor.bootstrap_design(n, base)
        assert polls is n["selecionadas"] and kind == "previsao_vetor"
        np.testing.assert_allclose(
            shift, np.subtract(n["alvos"][base], n["alvos"]["inclusivo"])
        )
    _, _, zero = motor.bootstrap_design(n, "inclusivo")
    assert not np.any(zero)
    for base, kind in (
        ("pnad", "pnad_vetor"),
        ("publicado", "publicado_vetor"),
        ("todas", "publicado_vetor"),
        ("sem_recencia", "previsao_vetor"),
    ):
        assert motor.bootstrap_design(n, base)[1:] == (kind, None)


def test_projection_shock_is_added_in_quadrature(data):
    n = data["nacional"]
    unc = data["configuracao"]["incerteza"]["projecao_inclinacao"]
    assert set(unc["aplica_em"]) == {"central_inclinacao", "tendencia"}
    sloped = n["tendencia"]["central_com_inclinacao"]
    sd = n["incerteza_projecao_pp"]["central_inclinacao"]
    assert sd == pytest.approx(
        sloped["horizonte_dias"] * sloped["dp_inclinacao_margem_pp_dia"]
    )
    assert 0 < sd < 2
    mc = data["incerteza"]
    assert mc["base"] == "central_inclinacao"
    assert mc["indecisos_flavio"] == data["central"]["parametros"]["indecisos_flavio"]
    assert mc["erro_comum_total_sd_pp"] == pytest.approx(math.hypot(2, sd))
    assert unc["erro_comum_total_sd_pp"] == pytest.approx(mc["erro_comum_total_sd_pp"])
    assert motor.projection_sd(n, "inclusivo") == 0
    assert motor.projection_sd(n, "dinamico") == 0
    script = """const fs=require('fs'),engine=require(process.argv[1]);
    const x=JSON.parse(fs.readFileSync(0,'utf8'));
    (async()=>{const out={};for(const base of ['central_inclinacao','tendencia','inclusivo'])
      out[base]=await engine.simulate(x,{...x.central.parametros,base},()=>{},()=>false,100);
    process.stdout.write(JSON.stringify(out));})();"""
    out = node(script, data)
    for base, result in out.items():
        extra = n["incerteza_projecao_pp"].get(base, 0)
        assert result["erro_comum_total_sd_pp"] == pytest.approx(math.hypot(2, extra))


def test_python_and_browser_uncertainty_center_on_the_new_central(data):
    params = data["central"]["parametros"]
    central = data["central"]["brasil"]["percentuais"]
    py = motor.simulate(data["estados"], data["nacional"], params, runs=400, seed=7)
    script = """const fs=require('fs'),engine=require(process.argv[1]);
    const x=JSON.parse(fs.readFileSync(0,'utf8'));
    (async()=>{const r=await engine.simulate(x,x.central.parametros,()=>{},()=>false,400);
    process.stdout.write(JSON.stringify(r));})();"""
    js = node(script, data)
    for i, k in enumerate(("lula", "flavio")):
        assert py["candidatos"][k]["percentual"]["p50"] == pytest.approx(
            central[k], abs=0.3
        )
        assert js["intervalos"][k][1] == pytest.approx(central[k], abs=0.3), i
    # O destino dos indecisos entra na simulação Python, como no navegador.
    to_flavio = motor.simulate(
        data["estados"],
        data["nacional"],
        {**params, "indecisos_flavio": 1.0},
        runs=200,
        seed=7,
    )
    to_lula = motor.simulate(
        data["estados"],
        data["nacional"],
        {**params, "indecisos_flavio": 0.0},
        runs=200,
        seed=7,
    )
    assert to_flavio["margem"]["p50"] > to_lula["margem"]["p50"]
    with pytest.raises(ValueError, match="não reproduz"):
        motor.simulate(data["estados"], data["nacional"], {"voto_flavio": 0.5})


def test_consolidation_starts_from_the_anchor_without_trend(data):
    cons = data["consolidacao"]
    sloped = data["nacional"]["tendencia"]["central_com_inclinacao"]
    assert cons["ancora"] == "inclusivo" == sloped["ancora_de_partida"]
    assert cons["data_efetiva_ancora"] == sloped["data_efetiva_central"]
    assert cons["horizonte_dias"] == pytest.approx(sloped["horizonte_dias"])
    cmp_ = cons["comparacao_central"]
    assert abs(cmp_["diferenca_pp"]) < 0.5
    assert "encolhe" in cmp_["nota"] and "não encolhe" in cmp_["nota"]
    ready = {p["id"]: p for p in simulador.presets(data)}
    for i in ("consolidacao_28", "consolidacao_14", "disponibilidade_28"):
        assert ready[i]["parametros"]["base"] == "inclusivo"
        assert "recência sem tendência" in ready[i]["frase"]
    for label in (
        "Consolidação na proporção medida, 28 dias",
        "Consolidação 28 dias, divisão por disponibilidade",
    ):
        assert data["sensibilidades"][label]["parametros"]["base"] == "inclusivo"


def test_page_shows_the_new_central_blocks(data):
    html = PAGE.read_text()
    assert "—" not in html
    assert (
        '<option value="central_inclinacao" selected>Central: recência com '
        "tendência de 28 dias encolhida</option>" in html
    )
    assert "Recência sem tendência (central até 03/10 à tarde)" in html
    value = str(data["central"]["parametros"]["indecisos_flavio"])
    assert re.search(rf'<option value="{re.escape(value)}" selected>', html)
    for phrase in (
        "validada por origem móvel contra pesquisas, não contra a urna",
        "<strong>Correção de tendência.</strong>",
        "extrapolação encolhida de uma tendência medida nas pesquisas, não medição da urna",
        "A troca da central na véspera",
        "<strong>reprovou</strong>",
        "<strong>aprovada</strong>",
        "não é identificável",
        "destino central dos indecisos",
        "partem da média por recência sem tendência",
    ):
        assert phrase in html, phrase
    gap = data["central"]["brasil"]["margem_flavio_lula"]
    shown = f"{abs(gap):.2f}".replace(".", ",")
    assert f"a central fica em F−L −{shown}" in html or gap >= 0
