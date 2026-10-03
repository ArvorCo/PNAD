"""Página do Senado gerada da fixture: fichas, barras, números e ausência de travessão."""

import importlib.util
import json
import re
from pathlib import Path

import pytest
from senado_2026.pagina.comum import pct

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/predicao_senado_exemplo.json"


def _build_module():
    spec = importlib.util.spec_from_file_location(
        "senado_2026_build", ROOT / "scripts/senado-2026-build.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def data():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def html(data):
    mod = _build_module()
    return mod.render(data, mod.TEMPLATE.read_text(encoding="utf-8"))


def test_27_fichas(html):
    assert len(re.findall(r'<details class="sn-ficha"', html)) == 27


def test_sem_travessao(html):
    assert "—" not in html


def test_barras_sao_div(html):
    barras = re.findall(r'<[a-z]+ class="sn-bar[ -][^"]*"', html)
    assert barras
    assert all(b.startswith("<div") for b in barras)
    assert not re.search(r"<span[^>]*style=\"[^\"]*width:", html)


def test_p_eleito_formatado(html, data):
    for e in data["estados"].values():
        for c in e["probabilidades"][:2]:
            assert pct(c["p_eleito"]) in html


def test_sem_pesquisa_sem_nomes(html, data):
    sem = [e for e in data["estados"].values() if e["cobertura"] == "sem_pesquisa"]
    assert sem
    for e in sem:
        assert e["eleitos_provaveis"] == []
        ficha = re.search(
            rf'<details class="sn-ficha" id="estado-{e["uf"]}".*?</details>',
            html,
            re.DOTALL,
        ).group(0)
        assert "Exemplo" not in ficha
        assert "sem pesquisa" in ficha


def test_hemiciclo_81_assentos(html):
    primeiro = html.split('id="hemiciclo-campo"')[1].split("</svg>")[0]
    assert primeiro.count("<circle") == 81


def test_json_ausente_falha_com_mensagem(tmp_path):
    mod = _build_module()
    with pytest.raises(SystemExit) as exc:
        mod.carregar(tmp_path / "nao_existe.json")
    assert "Falta" in str(exc.value)
