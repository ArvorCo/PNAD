"""Mapa interativo da seção #territorio: HTML estático completo e JS válido."""

import json
import re
import shutil
import subprocess
import sys
from html import unescape
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from predicao_2026 import mapa  # noqa: E402

PAGE = ROOT / "docs/predicao_2026_1T_presidente.html"
TEMPLATE = ROOT / "docs/predicao_2026_1T_presidente.template.html"
JS = ROOT / "docs/assets/predicao_2026_mapa.js"
CSS = ROOT / "docs/assets/predicao_2026_mapa.css"
UFS = set(mapa.UF_NOMES) - {"ZZ"}


@pytest.fixture(scope="module")
def page():
    return PAGE.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def data():
    return json.loads(
        (ROOT / "docs/assets/predicao_2026_1T_presidente.json").read_text()
    )


def test_template_has_single_map_block_and_assets():
    text = TEMPLATE.read_text(encoding="utf-8")
    head = text.split("</head>")[0]
    assert text.count("{{MAP}}") == 1
    assert 'class="map-layout"' not in text
    assert 'href="assets/predicao_2026_mapa.css"' in head
    assert 'src="assets/predicao_2026_mapa.js" defer' in head


def test_page_has_27_accessible_states(page):
    links = re.findall(r'<a class="mx-uf" href="#estado-(\w\w)" data-uf="(\w\w)"', page)
    assert len(links) == 27
    assert {a for a, b in links if a == b} == UFS
    paths = re.findall(r'<path id="mx-path-(\w\w)" data-uf="(\w\w)"', page)
    assert {a for a, b in paths if a == b} == UFS
    for uf in UFS:
        assert f'id="estado-{uf}"' in page
    assert len(re.findall(r'<a class="mx-uf"[^>]*aria-label="[^"]+"', page)) == 27


def test_controls_panel_legend_and_exterior_are_static(page):
    block = page.split('id="mapa-explorador"')[1].split('id="mapa-2022"')[0]
    for key in (
        "margem",
        "lula",
        "flavio",
        "outros",
        "comparecimento",
        "abstencao",
        "eleitorado",
        "swing_flavio",
        "swing_lula",
        "ondas",
        "prior",
    ):
        assert f'data-metric="{key}"' in block
    assert (
        'id="mx-controls" role="toolbar" aria-label="Métrica do mapa" hidden' in block
    )
    assert 'id="mx-scenario" hidden' in block and 'id="mx-back"' in block
    assert 'id="mx-panel"' in block and 'id="mx-tip"' in block
    assert 'id="mx-zz" href="#estado-ZZ"' in block
    assert "não indica liderança estatisticamente identificada" in block
    assert "linear-gradient(90deg" in block
    assert 'id="mx-desc"' in block and 'aria-describedby="mx-desc"' in block


def test_static_values_match_central(page, data):
    rows = {r["uf"]: r for r in data["central"]["ufs"]}
    margins = {
        uf: 100 * (r["flavio"] - r["lula"]) / (r["lula"] + r["flavio"] + r["outros"])
        for uf, r in rows.items()
    }
    domain = mapa.nice_domain(v for uf, v in margins.items() if uf != "ZZ")
    for uf in UFS:
        m = re.search(
            rf'aria-label="([^"]+)"><path id="mx-path-{uf}" data-uf="{uf}" d="[^"]+" fill="(#[0-9a-f]{{6}})"',
            page,
        )
        assert m, uf
        label, fill = unescape(m.group(1)), m.group(2)
        assert fill == mapa.diverging(margins[uf], domain)
        assert mapa._signed(margins[uf]) + " pp" in label
        lula = (
            100
            * rows[uf]["lula"]
            / (rows[uf]["lula"] + rows[uf]["flavio"] + rows[uf]["outros"])
        )
        assert f"Lula {mapa._fmt(lula)}%" in label


def test_diverging_scale_is_centered_and_monotone():
    assert mapa.diverging(0, 20) == mapa.mix(mapa.NEUTRAL, mapa.NEUTRAL, 0)
    assert mapa.diverging(20, 20) == mapa.FLAVIO
    assert mapa.diverging(-40, 20) == mapa.LULA
    assert mapa.mix("#000000", "#ffffff", 0.5) not in ("#000000", "#ffffff")


def test_embedded_2022_matches_tse(page):
    raw = page.split('<script type="application/json" id="mapa-2022">')[1]
    extra = json.loads(raw.split("</script>")[0])
    tse = json.loads((ROOT / "analysis/voto_util/tse_2022_uf.json").read_text())
    assert set(extra["passado"]) >= UFS
    for u in tse["ufs"]:
        t = u["t1"]
        assert extra["passado"][u["uf"]]["bolsonaro"] == pytest.approx(
            100 * t["bolsonaro"] / t["validos"], abs=1e-3
        )


def test_assets_are_valid_and_free_of_em_dash():
    for path in (JS, CSS, ROOT / "scripts/predicao_2026/mapa.py"):
        assert "—" not in path.read_text(encoding="utf-8"), path
    node = shutil.which("node")
    if not node:
        pytest.skip("node indisponível")
    subprocess.run([node, "--check", str(JS)], check=True)
    subprocess.run(
        [node, "--check", str(ROOT / "docs/assets/predicao_2026.js")], check=True
    )
    js = JS.read_text(encoding="utf-8")
    assert 'addEventListener("predicao:cenario"' in js
    assert "prediction-data" in js and "removeChild" not in js
