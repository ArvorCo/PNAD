"""Rejeição como régua de destino: transcrições, conta, motor e página."""

import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from predicao_2026 import motor, rejeicao, simulador  # noqa: E402

JS = ROOT / "docs/assets/predicao_2026.js"
PAGE = ROOT / "docs/predicao_2026_1T_presidente.html"
DASH = "\u2014"
DISP_IDS = ("disponibilidade_28", "disponibilidade_14")


@pytest.fixture(scope="module")
def data():
    return json.loads(
        (ROOT / "docs/assets/predicao_2026_1T_presidente.json").read_text()
    )


@pytest.fixture(scope="module")
def doc():
    return json.loads(rejeicao.SOURCE.read_text())


def test_transcriptions_have_hash_pages_and_renders(doc):
    seen = set()
    for c in doc["casas"]:
        assert c["instituto"] not in seen
        seen.add(c["instituto"])
        pdf = ROOT / c["pdf"]
        assert hashlib.sha256(pdf.read_bytes()).hexdigest() == c["sha256"]
        if not c["publica"]:
            # Ausência só se afirma depois de varrer o documento inteiro.
            assert c["paginas_varridas"] and c["nota"].startswith("Não publica")
            continue
        assert c["pagina_principal"] in c["paginas"]
        assert 0 < c["lula"] < 100 and 0 < c["flavio"] < 100
        assert c["tipo_pergunta"] in (
            "cartao_multipla",
            "grade_por_candidato",
            "escala_de_potencial",
        )
        if c["comparavel"]:
            assert "jeito nenhum" in c["enunciado"]
        else:
            assert c["motivo_controle"]
        for png in c.get("renderizacao", []):
            assert (ROOT / png).is_file()
        for seg in c.get("segmentos", []):
            assert 0 <= seg["lula"] <= 100 and 0 <= seg["flavio"] <= 100
    matrix = doc["matriz_nexus"]
    assert (
        hashlib.sha256((ROOT / matrix["pdf"]).read_bytes()).hexdigest()
        == matrix["sha256"]
    )
    for row in matrix["linhas"].values():
        assert 98 <= sum(row.values()) <= 101
    text = json.dumps(doc, ensure_ascii=False)
    assert DASH not in text


def test_availability_bounds_and_symmetry():
    assert rejeicao.availability_share(0.45, 0.45) == pytest.approx(0.5)
    assert rejeicao.availability_share(1.0, 0.3) == pytest.approx(1.0)
    assert rejeicao.availability_share(0.3, 1.0) == pytest.approx(0.0)
    for rl in (0.0, 0.2, 0.5, 0.9):
        for rf in (0.0, 0.3, 0.6, 0.95):
            s = rejeicao.availability_share(rl, rf)
            assert 0 <= s <= 1
            assert rejeicao.availability_share(rf, rl) == pytest.approx(1 - s)
    with pytest.raises(ValueError):
        rejeicao.availability_share(1.0, 1.0)
    with pytest.raises(ValueError):
        rejeicao.availability_share(-0.1, 0.5)


def test_delta_standard_error_matches_simulation():
    import numpy as np

    rng = np.random.default_rng(7)
    rl, rf, n = 0.48, 0.47, 2000
    var_l, var_f, cov = rejeicao.sampling(rl, rf, n, deff=1.0)
    chol = np.linalg.cholesky(np.array([[var_l, cov], [cov, var_f]]))
    z = rng.standard_normal((200000, 2))
    draws = np.array([rl, rf]) + np.einsum("ij,nj->ni", chol, z)
    shares = (1 - draws[:, 1]) / (2 - draws.sum(axis=1))
    se = rejeicao.share_se(rl, rf, var_l, var_f, cov)
    assert shares.std() == pytest.approx(se, rel=0.02)
    # Fréchet inferior é o caso conservador: covariância zero dá erro menor.
    assert rejeicao.share_se(rl, rf, var_l, var_f, 0.0) < se


def test_published_block(data):
    rej = data["rejeicao"]
    media = rej["media"]
    assert 0 <= media["parte_flavio"] <= 1
    lo, hi = media["ic95"]
    assert lo < media["parte_flavio"] < hi
    assert rej["indecisos_flavio"] == round(media["parte_flavio"], 4)
    rows = {r["instituto"]: r for r in rej["casas"]}
    inside = [r for r in rej["casas"] if r["na_media"]]
    assert sorted(media["casas"]) == sorted(r["instituto"] for r in inside)
    assert all(r["tipo_pergunta"] != "escala_de_potencial" for r in inside)
    assert not rows["MDA"]["na_media"] and not rows["PoderData"]["na_media"]
    assert sum(media["pesos"].values()) == pytest.approx(1)
    lula = sum(media["pesos"][r["instituto"]] * r["lula"] for r in inside)
    assert media["lula"] == pytest.approx(lula)
    assert {r["instituto"] for r in rej["nao_publicam"]} >= {"AtlasIntel"}
    assert rej["terceira_via_indecisos"]["publicado"] is False
    for key in ("serie_28", "serie_14", "nexus_p84", "datafolha_segunda_opcao"):
        assert key in rej["comparacao"]
    nexus = rej["comparacao"]["nexus_p84"]["parte_flavio_entre_finalistas"]
    assert nexus == pytest.approx(588 / 950)


def test_availability_lambda_uses_same_migration(data):
    cons, rej = data["consolidacao"], data["rejeicao"]
    for key in ("28", "14"):
        measured = cons["projecao"][key]
        available = rej["consolidacao_disponibilidade"][key]
        assert available["migracao_total_pp"] == pytest.approx(
            measured["migracao_total_pp"]
        )
        assert available["parte_flavio_usada"] == pytest.approx(
            rej["media"]["parte_flavio"]
        )
        assert available["migracao_pp"]["flavio"] == pytest.approx(
            available["migracao_total_pp"] * rej["media"]["parte_flavio"]
        )
        assert all(0 <= v <= 1 for v in available["lambda"].values())


def test_resolve_keeps_engine_numeric(data):
    rej = data["rejeicao"]
    resolved = rejeicao.resolve({"indecisos_flavio": "disponibilidade"}, rej)
    assert resolved["indecisos_flavio"] == rej["indecisos_flavio"]
    assert rejeicao.resolve({"indecisos_flavio": 0.6}, rej) == {"indecisos_flavio": 0.6}
    assert motor.DEFAULTS["indecisos_flavio"] is None
    # A central resolve a disponibilidade para número no build.
    assert data["central"]["parametros"]["indecisos_flavio"] == rej["indecisos_flavio"]
    sens = data["sensibilidades"][
        "Recência sem tendência, indecisos por disponibilidade"
    ]
    assert sens["parametros"]["indecisos_flavio"] == rej["indecisos_flavio"]
    prop = data["sensibilidades"]["Indecisos proporcionais às candidaturas"]
    assert prop["parametros"]["indecisos_flavio"] is None


def test_presets_carry_availability_lambda(data):
    ready = simulador.presets(data)
    ids = [p["id"] for p in ready]
    assert ids[:3] == ["central", "consolidacao_28", "consolidacao_14"]
    assert ids[3:5] == list(DISP_IDS)
    for preset, key in zip(ready[3:5], ("28", "14"), strict=True):
        lam = data["rejeicao"]["consolidacao_disponibilidade"][key][
            "lambda_arredondado"
        ]
        assert preset["parametros"] == {
            "base": "inclusivo",
            "voto_flavio": lam["flavio"],
            "voto_lula": lam["lula"],
        }
        assert "disponibilidade" in preset["nome"]
        assert DASH not in preset["nome"] + preset["frase"] + preset["nota"]


def test_availability_destination_parity_python_js(data):
    exe = shutil.which("node")
    if not exe:
        pytest.skip("Node necessário para verificar a paridade com o navegador")
    rej = data["rejeicao"]
    presets = {p["id"]: p for p in simulador.presets(data)}
    cases = [
        rejeicao.resolve({"indecisos_flavio": "disponibilidade"}, rej),
        rejeicao.resolve(
            {"indecisos_flavio": "disponibilidade", "indecisos_validos": 0.5}, rej
        ),
        *(presets[i]["parametros"] for i in DISP_IDS),
    ]
    script = """const fs=require('fs'),engine=require(process.argv[1]),S=engine.Simulador;
    const x=JSON.parse(fs.readFileSync(0,'utf8'));
    process.stdout.write(JSON.stringify(x.cases.map(p=>({r:engine.scenario(x.states,p),
      back:S.decode(S.encode(p)).indecisos_flavio}))));"""
    out = json.loads(
        subprocess.run(
            [exe, "-e", script, str(JS)],
            input=json.dumps({"states": data["estados"], "cases": cases}),
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    )
    for params, js in zip(cases, out, strict=True):
        py = motor.scenario(data["estados"], params)
        for left, right in [
            (py["brasil"], js["r"]["brasil"]),
            *zip(py["ufs"], js["r"]["ufs"], strict=True),
        ]:
            for k in ("lula", "flavio", "outros", "comparecimento", "branco_nulo"):
                assert left[k] == pytest.approx(right[k], abs=1e-6, rel=1e-12)
        # O link do cenário devolve o mesmo destino numérico.
        expected = params.get("indecisos_flavio")
        assert js["back"] == (
            None if expected is None else pytest.approx(expected, abs=1e-12)
        )


def test_page_has_resolved_rejection_block(data):
    html = PAGE.read_text()
    assert DASH not in html
    match = re.search(
        r'<div class="sim-consolidacao" id="rejeicao">.*?</div>', html, re.DOTALL
    )
    assert match is not None
    block = match.group(0)
    assert "{{" not in block
    assert "nunca retira voto já contado" in block
    share = data["rejeicao"]["media"]["parte_flavio"]
    assert f"{100 * share:.1f}".replace(".", ",") + "%" in block
    value = str(data["rejeicao"]["indecisos_flavio"])
    assert (
        f'<option value="{value}" selected>Por disponibilidade: 1 − rejeição medida'
        in html
    )
    for i in DISP_IDS:
        assert f'data-preset="{i}"' in html
    assert 'id="help-disponibilidade"' in html


def test_block_rejects_empty_window(data, tmp_path, doc):
    empty = {**doc, "casas": [c for c in doc["casas"] if not c["publica"]]}
    path = tmp_path / "rej.json"
    path.write_text(json.dumps(empty))
    with pytest.raises(ValueError):
        rejeicao.block(data["consolidacao"], date(2026, 10, 3), source=path)
