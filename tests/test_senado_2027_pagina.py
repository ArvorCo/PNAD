"""Página O Senado de 2027 diante do STF: view, texto e build com o JSON real."""

import importlib.util
import json
import re
import sys
import types
from pathlib import Path

import pytest
from senado_2027.pagina import texto, view

ROOT = Path(__file__).resolve().parents[1]
JSON = ROOT / "docs/assets/senado_2027.json"
TEMPLATE = ROOT / "docs/senado_2027.template.html"
FIGURAS = (
    "dispersao_k_c",
    "hemiciclo_c",
    "distribuicao_votos",
    "tipos_de_caso",
    "curva_k",
    "dispersao_relatorios",
    "teste_pec8",
    "pivos",
    "placar_cenarios",
)
VALORES = {
    "DATE",
    "N_SENADORES",
    "N_COM_CASO",
    "K_MEDIA",
    "K_MEDIANA",
    "ESPERADO_PEC_FLAVIO",
    "ESPERADO_IMP_FLAVIO",
    "ESPERADO_PEC_LULA",
    "ESPERADO_IMP_LULA",
    "P49_FLAVIO",
    "P54_FLAVIO",
    "P49_LULA",
    "P54_LULA",
    "N_ALTA",
    "N_MEDIA",
    "N_BAIXA",
    "N_PIVOS",
    "PIVOS_NOMES",
    "N_PEC8_PRESENTES",
    "N_PEC8_SIM",
    "N_PEC8_NAO",
    "N_PEC8_AUSENTES",
}


@pytest.fixture(scope="module")
def data():
    if not JSON.exists():
        pytest.skip("docs/assets/senado_2027.json ausente; rode o motor")
    return json.loads(JSON.read_text(encoding="utf-8"))


def _garantir_figuras():
    """Usa figuras.py quando existe; senão, um stub que devolve <figure> vazia."""
    try:
        importlib.import_module("senado_2027.pagina.figuras")
    except ImportError:
        stub = types.ModuleType("senado_2027.pagina.figuras")
        for nome in FIGURAS:
            setattr(
                stub,
                nome,
                lambda *_a, _n=nome, **_k: f'<figure class="sn27-fig" data-stub="{_n}">'
                "</figure>",
            )
        sys.modules["senado_2027.pagina.figuras"] = stub
        sys.modules["senado_2027.pagina"].figuras = stub


@pytest.fixture(scope="module")
def html(data):
    _garantir_figuras()
    spec = importlib.util.spec_from_file_location(
        "senado_2027_build", ROOT / "scripts/senado-2027-build.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.render(data, TEMPLATE.read_text(encoding="utf-8"))


def test_placeholders_trocados_sem_travessao(html):
    assert "{{" not in html
    assert "—" not in html


def test_81_fichas(html, data):
    n = len(data["elenco"])
    assert n == 81
    assert len(re.findall(r'<details class="sn27-ficha" id="ficha-', html)) == n


def test_ranking_tem_81_linhas(data):
    r = view.ranking(data)
    assert "data-sortable" in r and "sn27-ranking" in r
    corpo = r.split("<tbody>")[1].split("</tbody>")[0]
    assert corpo.count("<tr>") == 81
    assert 'class="num"' in r


def test_ficha_com_caso_tem_defesa(data):
    f = view.fichas(data)
    pedacos = f.split('<details class="sn27-ficha"')[1:]
    assert len(pedacos) == 81
    for pedaco in pedacos:
        if 'class="sn27-caso"' in pedaco:
            assert "Defesa" in pedaco
            assert pedaco.count('class="sn27-caso"') == pedaco.count("<b>Defesa.</b>")


def test_nenhum_span_com_width(html):
    assert not re.search(r'<span[^>]*style="[^"]*width', html)


def test_recomendacoes_rotuladas(data):
    r = view.recomendacoes(data)
    assert "juízo editorial" in r
    assert 'class="contraprova"' in r
    assert 'class="hyp"' in r and "iffail" in r


def test_values_nomes(data):
    v = texto.values(data)
    assert set(v) == VALORES
    assert all(isinstance(x, str) and x for x in v.values())
    assert re.fullmatch(r"\d{2}/\d{2}/\d{4}", v["DATE"])
    assert v["N_SENADORES"] == "81"
    assert v["P54_FLAVIO"].endswith("%")


def test_chances_simetrico():
    assert texto.chances(91) == "9 chances em 10"
    assert texto.chances(19) == "1 chance em 4"
    assert texto.chances(1) == "quase nenhuma chance"
    assert texto.chances(50) == "cara ou coroa"


def test_hero_tres_cartoes(data):
    h = view.hero(data)
    assert h.count('<article class="sn27-hero-card') == 3
    assert "sn27-hero-card-lula" in h
    assert "quórum de 49" in h and "quórum de 54" in h
