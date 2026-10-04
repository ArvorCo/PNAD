"""Página do Senado gerada da fixture: fichas, barras, números e ausência de travessão."""

import copy
import importlib.util
import json
import re
from pathlib import Path

import pytest
from senado_2026.pagina.comum import pct

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/predicao_senado_exemplo.json"
MALHA = ROOT / "data/originals/ibge_malhas/br_uf/br_uf_minima.geojson"


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
    if not MALHA.exists():
        pytest.skip("Malha do IBGE ausente neste ambiente; o mapa não é renderizado")
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


@pytest.fixture(scope="module")
def html_sem_alertas(data):
    if not MALHA.exists():
        pytest.skip("Malha do IBGE ausente neste ambiente; o mapa não é renderizado")
    limpo = copy.deepcopy(data)
    for e in limpo["estados"].values():
        e.pop("alertas", None)
        e.pop("cenarios", None)
    limpo["senado_2027"].pop("cenarios", None)
    mod = _build_module()
    return mod.render(limpo, mod.TEMPLATE.read_text(encoding="utf-8"))


def test_alerta_cenario_chip_e_aviso(html, data):
    alerta = data["estados"]["PR"]["alertas"][0]
    cenario = data["estados"]["PR"]["cenarios"][0]
    ficha = re.search(
        r'<details class="sn-ficha" id="estado-PR".*?</details>', html, re.DOTALL
    ).group(0)
    corpo = ficha.split('<div class="sn-ficha-corpo">')[1]
    assert corpo.startswith('<div class="sn-alerta"')
    assert alerta["titulo"] in ficha
    assert "03/10/2026 20:17" in ficha
    assert "E se os votos forem anulados?" in ficha
    assert cenario["rotulo"] in ficha
    assert cenario["hipotese"] in ficha
    assert "hipótese explícita" in ficha
    assert pct(cenario["p_dupla_mais_provavel"]) in ficha
    assert html.count('<span class="sn-marca">registro indeferido</span>') >= 3
    assert 'class="sn-atualizacao"' in html
    assert "Atualização de 03/10, noite" in html
    assert 'href="#estado-PR"' in html
    assert "Registro indeferido e votos nulos." in html
    assert "Matérias arquivadas sobre os alertas" in html
    assert alerta["fontes"][0]["sha256"] in html


def test_sem_alertas_nada_aparece(html_sem_alertas):
    for marca in (
        "sn-alerta",
        "sn-marca",
        "sn-atualizacao",
        "sn-cenario",
        "E se os votos forem anulados?",
        "Registro indeferido e votos nulos.",
        "Matérias arquivadas",
    ):
        assert marca not in html_sem_alertas
    assert "—" not in html_sem_alertas
