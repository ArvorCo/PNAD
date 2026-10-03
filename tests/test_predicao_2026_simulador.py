"""Simulador do leitor: cenários prontos, link compartilhável e contrato do evento."""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from predicao_2026 import base, motor, simulador  # noqa: E402

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
        pytest.skip("Node necessário para verificar o simulador do navegador")
    run = subprocess.run(
        [exe, "-e", script, str(JS)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(run.stdout)


def test_presets_only_use_engine_parameters(data):
    ready = simulador.presets(data)
    ids = [p["id"] for p in ready]
    assert len(ids) == len(set(ids))
    assert ready[0]["id"] == "central"
    assert ready[0]["parametros"] == {}
    for preset in ready:
        assert set(preset["parametros"]) <= set(motor.DEFAULTS)
        assert preset["nome"] and preset["frase"]
        for region in preset["parametros"].get("regioes", {}):
            assert region in base.REGIONS
        for key, value in preset["parametros"].items():
            if key in simulador.RANGES:
                _, lo, hi, _, suffix = simulador.RANGES[key]
                shown = 100 * value if suffix == "%" else value
                assert lo <= shown <= hi, key
        text = preset["nome"] + preset["frase"]
        assert "—" not in text
        assert "previsão" not in text.lower()


def test_presets_match_between_python_and_browser(data):
    script = """const fs=require('fs'),engine=require(process.argv[1]);
    const x=JSON.parse(fs.readFileSync(0,'utf8'));
    const C=engine.Simulador.configure(x.central);
    process.stdout.write(JSON.stringify(x.presets.map(p=>engine.scenario(x.states,{...C,...p.parametros}))));"""
    presets = [dict(p) for p in simulador.presets(data)]
    c = data["central"]["parametros"]
    browser = node(
        script, {"states": data["estados"], "presets": presets, "central": c}
    )
    central = motor.scenario(data["estados"], c)["brasil"]
    for preset, js in zip(presets, browser, strict=True):
        python = motor.scenario(data["estados"], {**c, **preset["parametros"]})
        for left, right in [
            (python["brasil"], js["brasil"]),
            *zip(python["ufs"], js["ufs"], strict=True),
        ]:
            for k in FIELDS:
                assert left[k] == pytest.approx(right[k], abs=1e-6, rel=1e-12)
        b = python["brasil"]
        assert b["eleitorado"] == pytest.approx(
            b["validos"] + b["branco_nulo"] + b["abstencao"], abs=1e-6
        )
        if preset["parametros"]:
            assert b != central, preset["id"]


def test_presets_move_in_the_declared_direction(data):
    central = motor.scenario(data["estados"])["brasil"]["margem_flavio_lula"]

    def gap(preset_id):
        preset = next(p for p in simulador.PRESETS if p["id"] == preset_id)
        return motor.scenario(data["estados"], preset["parametros"])["brasil"][
            "margem_flavio_lula"
        ]

    assert gap("util_direita") > central > gap("util_esquerda")
    assert gap("erro_flavio") > central > gap("erro_lula")
    assert gap("diferencial_flavio") > central > gap("diferencial_lula")


CODEC_CASES = [
    {},
    {"voto_flavio": 0.5},
    {"voto_flavio": 0.29, "voto_lula": 0.07, "vies_pp": -2.75},
    {"base": "pnad", "comparecimento_modelo": "secoes", "secoes_abstencao_pp": -4.5},
    {"indecisos_validos": 0, "indecisos_flavio": 0.6, "branco_nulo_pp": 1.25},
    {"eleitor_provavel": False, "exterior": False, "diferencial_pp": 3},
    {
        "comparecimento_pp": -2,
        "regioes": {
            "Nordeste": {"comparecimento_pp": -5},
            "Sul": {"comparecimento_pp": 2},
        },
        "ufs": {
            "SP": {"comparecimento_pp": 2, "voto_flavio": 0.5},
            "SE": {"diferencial_pp": -1.5, "voto_lula": 0},
            "ZZ": {"comparecimento_pp": -10},
        },
    },
]


def test_url_fragment_round_trip_and_central_detection():
    script = """const fs=require('fs'),S=require(process.argv[1]).Simulador;
    const x=JSON.parse(fs.readFileSync(0,'utf8'));
    process.stdout.write(JSON.stringify(x.map(p=>{const code=S.encode(p),back=S.decode(code);
      return {code,again:S.encode(back),back,central:S.isCentral(p),sentence:S.describe(p)};})));"""
    out = node(script, CODEC_CASES)
    assert out[0]["code"] == ""
    assert out[0]["central"] is True
    assert out[1]["code"] == "vf:50"
    for case, row in zip(CODEC_CASES, out, strict=True):
        assert row["code"] == row["again"]
        assert row["central"] is (case == {})
        assert "—" not in row["code"] + " ".join(row["sentence"])
        for k, v in case.items():
            if k in ("regioes", "ufs"):
                continue
            if isinstance(v, (bool, str)):
                assert row["back"][k] == v
            else:
                assert row["back"][k] == pytest.approx(v)
        for region, value in case.get("regioes", {}).items():
            assert row["back"]["regioes"][region] == value
        for uf, value in case.get("ufs", {}).items():
            assert row["back"]["ufs"][uf] == pytest.approx(value)
    regional = out[-1]["code"]
    assert "rNE:-5" in regional and "rS:2" in regional
    assert "SE:df-1.5,vl0" in regional, "UF Sergipe não pode virar a região Sudeste"
    assert "rSE" not in regional


def test_decoder_ignores_garbage_and_clamps_fractions():
    script = """const fs=require('fs'),S=require(process.argv[1]).Simulador;
    const x=JSON.parse(fs.readFileSync(0,'utf8'));
    process.stdout.write(JSON.stringify(x.map(t=>S.decode(t))));"""
    out = node(
        script,
        [
            "vf:900;vl:-3;a:<script>;zz:1;cp:abc;rXX:4;sp:cp2;SP:cp;SP:xx9",
            "iv:;if:40;ep:0",
        ],
    )
    first, second = out
    assert first["voto_flavio"] == 1
    assert first["voto_lula"] == 0
    assert first["base"] == "central_inclinacao"
    assert first["comparecimento_pp"] == 0
    assert first["regioes"] == {}
    assert first["ufs"] == {}
    assert second["indecisos_validos"] == 1
    assert second["indecisos_flavio"] == pytest.approx(0.4)
    assert second["eleitor_provavel"] is False


def test_sentence_reports_change_against_central(data):
    script = """const fs=require('fs'),engine=require(process.argv[1]),S=engine.Simulador;
    const x=JSON.parse(fs.readFileSync(0,'utf8'));
    const c=engine.scenario(x.states,{}).brasil;
    process.stdout.write(JSON.stringify(x.cases.map(p=>S.sentence(p,c,engine.scenario(x.states,p).brasil))));"""
    cases = [
        {},
        {"voto_flavio": 0.5, "regioes": {"Nordeste": {"comparecimento_pp": -5}}},
    ]
    central, edited = node(script, {"states": data["estados"], "cases": cases})
    assert central.startswith("Sem hipóteses do leitor")
    assert edited.startswith(
        "Com Flávio antecipando 50% da reserva e comparecimento 5 pp menor no Nordeste"
    )
    # The central sign moves with new polls; the sentence must carry it explicitly.
    assert re.search(r"passa de [−+]\d+,\d{2} para [−+]\d+,\d{2} pp", edited)
    assert "—" not in central + edited


def test_page_embeds_presets_and_event_contract(data):
    html = PAGE.read_text()
    js = JS.read_text()
    assert 'id="sim-presets-data"' in html
    assert html.count("data-preset=") == len(simulador.presets(data))
    assert 'new CustomEvent("predicao:cenario"' in js
    assert "result:lastResult,params:lastParams,central:" in js
    assert "—" not in js


def browser_page(viewport):
    sync = pytest.importorskip("playwright.sync_api")
    manager = sync.sync_playwright().start()
    try:
        browser = manager.chromium.launch()
    except Exception as error:  # navegador ausente no CI
        manager.stop()
        pytest.skip(f"Chromium indisponível: {error}")
    page = browser.new_page(viewport=viewport)
    page.add_init_script(
        "window.__eventos=[];document.addEventListener('predicao:cenario',"
        "e=>window.__eventos.push({central:e.detail.central,params:e.detail.params,"
        "gap:e.detail.result.brasil.margem_flavio_lula}));"
    )
    return manager, browser, page


def test_browser_dispatches_event_restores_link_and_has_no_lateral_scroll():
    manager, browser, page = browser_page({"width": 1280, "height": 900})
    try:
        page.goto(PAGE.as_uri())
        page.wait_for_function("window.__eventos.length>=1")
        events = page.evaluate("window.__eventos")
        assert len(events) == 1 and events[0]["central"] is True
        page.click('[data-preset="util_direita"]')
        last = page.evaluate("window.__eventos.at(-1)")
        assert last["central"] is False
        assert last["params"]["voto_flavio"] == pytest.approx(0.5)
        assert page.evaluate("location.hash") == "#sim=vf:50"
        assert (
            page.get_attribute('[data-preset="util_direita"]', "aria-pressed") == "true"
        )
        page.click("#sim-reset")
        assert page.evaluate("window.__eventos.at(-1).central") is True
        assert page.evaluate("location.hash") == ""

        page.goto(PAGE.as_uri() + "#sim=vf:50;rNE:-5;SP:cp2")
        page.wait_for_function("window.__eventos.length>=1")
        assert page.input_value("#param-voto_flavio") == "50"
        assert page.input_value('input[data-region="Nordeste"]') == "-5"
        assert "SP" in page.inner_text("#uf-edits")
        page.wait_for_function("window.scrollY>500")
        detail = page.evaluate("window.__eventos.at(-1)")
        assert detail["central"] is False
        assert detail["params"]["ufs"]["SP"]["comparecimento_pp"] == 2

        page.set_viewport_size({"width": 390, "height": 844})
        page.reload()
        page.wait_for_function("window.__eventos.length>=1")
        page.evaluate(
            "document.querySelectorAll('#simulador details').forEach(d=>d.open=true)"
        )
        page.click("[data-view=uf]")
        page.evaluate("document.querySelectorAll('.help-toggle').forEach(b=>b.click())")
        width = page.evaluate(
            "[document.documentElement.scrollWidth, window.innerWidth]"
        )
        assert width[0] <= width[1], width
    finally:
        browser.close()
        manager.stop()
