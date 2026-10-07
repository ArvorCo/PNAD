"""Figuras SVG da página do Senado de 2027 sobre o JSON real do motor."""

import json
import re
from pathlib import Path

import pytest
from senado_2027.pagina import figuras

ROOT = Path(__file__).resolve().parents[1]
JSON = ROOT / "docs/assets/senado_2027.json"


@pytest.fixture(scope="module")
def data():
    if not JSON.exists():
        pytest.skip("docs/assets/senado_2027.json ainda não foi gerado")
    return json.loads(JSON.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def todas(data):
    return figuras.todas(data)


def test_toda_figura_tem_forma_da_casa(todas):
    assert len(todas) >= 9
    for nome, html in todas.items():
        assert html.startswith('<figure class="sn27-fig'), nome
        assert "<svg" in html, nome
        assert "<figcaption>" in html, nome
        assert 'role="img"' in html, nome
        assert re.search(r'aria-label="[^"]{20,}"', html), nome
        assert chr(0x2014) not in html, nome
        assert "viewBox=" in html, nome


def test_funcoes_publicas_pelo_nome(data):
    nomes = [
        "dispersao_k_c",
        "hemiciclo_c",
        "distribuicao_votos",
        "tipos_de_caso",
        "curva_k",
        "dispersao_relatorios",
        "teste_pec8",
        "pivos",
        "placar_cenarios",
    ]
    for nome in nomes:
        html = getattr(figuras, nome)(data)
        assert "<figure" in html and "<svg" in html


def test_hemiciclo_tem_81_assentos(data):
    for alvo in ("C_imp", "C_pec"):
        for cenario in ("flavio", "lula"):
            html = figuras.hemiciclo_c(data, alvo=alvo, cenario=cenario)
            assert html.count('class="sn27-assento"') == 81
            assert 'data-limiar="49"' in html and 'data-limiar="54"' in html


def test_dispersao_tem_81_pontos(data):
    for cenario in ("flavio", "lula"):
        html = figuras.dispersao_k_c(data, cenario)
        assert html.count('class="sn27-ponto"') == 81


def test_histograma_marca_49_e_54(data):
    html = figuras.distribuicao_votos(data, "flavio")
    assert 'data-limiar="49"' in html
    assert 'data-limiar="54"' in html
    assert "sn27-dist-largo" in html and "sn27-dist-estreito" in html


def test_pec8_um_ponto_por_senador(data):
    html = figuras.teste_pec8(data)
    assert html.count('class="sn27-pec8"') == len(data["teste_pec8"]["senadores"])


def test_rotulos_da_dispersao_nao_se_sobrepoem(data):
    pts = [(100.0, 100.0, 6.0, "Fulano de Tal"), (102.0, 101.0, 6.0, "Beltrana")]
    rot = figuras.resolver_rotulos(pts, [], (0, 0, 400, 300), 13)
    a, b = rot[0]["caixa"], rot[1]["caixa"]
    assert figuras._sobrepoe(a, b) == 0
