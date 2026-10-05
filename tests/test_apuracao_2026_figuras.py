"""Figuras do catálogo do dossiê da apuração: presença, contrato HTML e fichas."""

import importlib.util
import json
import re
from pathlib import Path

import pytest
from apuracao_2026 import pagina_comum as C
from apuracao_2026.pagina_fig_base import ADIAR_ACIMA, Tips, figura_html
from apuracao_2026.pagina_figuras import FIGURAS
from apuracao_2026.pagina_interativo import interativo_html

ROOT = Path(__file__).resolve().parents[1]
CATALOGO = ROOT / "analysis/apuracao_2026/CATALOGO_FIGURAS.md"
FIXTURE_SECOES = ROOT / "tests/fixtures/apuracao_2026/secoes_fixture.json"
SECOES = [
    "secoes_90",
    "secoes_excesso",
    "secoes_tamanho_tipo",
    "clusters_secoes",
    "clusters_regiao",
    "modelo_urna_uf",
    "modelo_urna_zona",
    "secoes_outras",
]
NOMES = re.findall(
    r"^\| `([a-z0-9_]+)` \|", CATALOGO.read_text(encoding="utf-8"), re.MULTILINE
)

ABERTURA = r'^<figure class="reveal fig-i( fig-adiada)?" id="fig-{nome}"'

spec = importlib.util.spec_from_file_location(
    "apuracao_build_fig", ROOT / "scripts/apuracao-2026-build.py"
)
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


@pytest.fixture(scope="module")
def dados():
    d = C.Dados()
    tudo = {f.stem: d.get(f.name) for f in sorted(C.DADOS.glob("*.json"))}
    agregador = ROOT / "docs/assets/reponderacao_pnad.json"
    tudo["agregador"] = json.loads(agregador.read_text(encoding="utf-8"))
    if not tudo.get("secoes"):
        tudo["secoes"] = json.loads(FIXTURE_SECOES.read_text(encoding="utf-8"))
    return tudo


@pytest.fixture(scope="module")
def html(dados):
    return {nome: FIGURAS[nome](dados) for nome in NOMES}


def _tips(h: str) -> dict:
    m = re.search(
        r'<script type="application/json" class="tips">(.*?)</script>', h, re.DOTALL
    )
    assert m, "sem bloco de fichas"
    return json.loads(m.group(1).replace("<\\/", "</"))


def test_catalogo_inteiro_registrado():
    assert len(NOMES) >= 43
    assert len(NOMES) == len(set(NOMES))
    assert set(SECOES) <= set(NOMES)
    assert set(NOMES) <= set(FIGURAS)


@pytest.mark.parametrize("nome", NOMES)
def test_contrato_da_figura(html, nome):
    h = html[nome]
    assert re.match(ABERTURA.format(nome=nome), h)
    assert "pendente" not in h[:80]
    assert h.count("<svg") == 1
    assert "<title>" in h and "<desc>" in h
    assert "<figcaption>" in h
    assert "—" not in h
    _tips(h)


@pytest.mark.parametrize("nome", NOMES)
def test_toda_chave_tem_ficha(html, nome):
    h = html[nome]
    tips = _tips(h)
    linhas = tips.get("_rows", {}).get("linhas", [])
    chaves = re.findall(r'data-k="([^"]+)"', h)
    assert chaves or 'data-near="1"' in h
    for k in chaves:
        if k.startswith("r") and k[1:].isdigit():
            assert int(k[1:]) < len(linhas), k
        else:
            assert k in tips, k
    rows = tips.get("_rows")
    if rows and "xy" in rows:
        assert len(rows["xy"]) == len(rows["linhas"])


ADIADAS_ESPERADAS = (
    "terceira_via_mapa",
    "reguas_divergencia_mapa",
    "nulo_2022_municipios",
    "senado_carregadores_mapa",
)


def _corpo_adiado(h: str) -> str:
    m = re.search(r'<noscript class="fig-src">(.*?)</noscript>', h, re.DOTALL)
    assert m, "figura adiada sem noscript"
    return m.group(1)


@pytest.mark.parametrize("nome", ADIADAS_ESPERADAS)
def test_figura_pesada_sai_adiada(html, nome):
    h = html[nome]
    assert h.startswith(f'<figure class="reveal fig-i fig-adiada" id="fig-{nome}"')
    assert " data-adiada>" in h[:200]
    assert h.count("<noscript") == 1 and h.count("</noscript>") == 1
    corpo = _corpo_adiado(h)
    assert len(corpo.encode("utf-8")) >= ADIAR_ACIMA
    assert "<svg" in corpo and 'class="tips"' in corpo
    # a espera vem antes do bloco cru, com a razão do viewBox; a legenda fica fora
    assert re.search(r'<div class="fig-espera" style="--ar:\d+/\d+"', h)
    assert h.index('class="fig-espera"') < h.index("<noscript")
    assert h.index("</noscript>") < h.index("<figcaption>")


def test_figura_leve_nao_e_adiada(html):
    h = html["placar_candidatos"]
    assert "noscript" not in h and "data-adiada" not in h
    assert len(h.encode("utf-8")) < ADIAR_ACIMA


def test_figura_html_adia_por_tamanho_ou_por_pedido():
    svg = '<svg class="fig" viewBox="0 0 1100 550"><title>t</title><desc>d</desc><rect/></svg>'
    tips = Tips()
    tips.add("<p>ficha</p>")
    leve = figura_html("x", svg, "legenda", tips)
    assert "noscript" not in leve
    forcada = figura_html("x", svg, "legenda", tips, adiar=True)
    assert '<noscript class="fig-src">' in forcada and "--ar:1100/550" in forcada
    assert (
        _corpo_adiado(forcada)
        == leve[
            len('<figure class="reveal fig-i" id="fig-x" data-fig="x" data-dim>') :
        ].split("<figcaption>")[0]
    )
    pesada = figura_html("x", svg + " " * ADIAR_ACIMA, "legenda", tips)
    assert "data-adiada" in pesada
    with pytest.raises(ValueError):
        figura_html("x", svg, "legenda", tips, apos="</noscript>", adiar=True)


def test_dado_ausente_vira_pendente():
    h = FIGURAS["placar_candidatos"]({})
    assert 'class="pendente"' in h and "presidente.json" in h


def test_texto_minimo_13px(html):
    for nome, h in html.items():
        tamanhos = [float(x) for x in re.findall(r'<text[^>]*font-size="([0-9.]+)"', h)]
        assert min(tamanhos, default=13) >= 13, nome


def test_camada_interativa_uma_vez(tmp_path):
    bloco = interativo_html()
    assert bloco.startswith("<style>") and "<script>" in bloco
    saida = tmp_path / "apuracao.html"
    build.construir(C.DADOS, saida)
    pagina = saida.read_text(encoding="utf-8")
    assert pagina.count("function monta(fig)") == 1
    assert pagina.count("function materializa(fig)") == 1
    assert "rootMargin:'1000px 0px 1000px 0px'" in pagina
    assert pagina.count('<figure class="reveal fig-i fig-adiada"') == pagina.count(
        '<noscript class="fig-src">'
    )
    assert pagina.count('<noscript class="fig-src">') >= len(ADIADAS_ESPERADAS)
    assert "—" not in pagina
    tem_secoes = (C.DADOS / "secoes.json").exists()
    for nome in NOMES:
        if nome in SECOES and not tem_secoes:
            continue
        assert f'id="fig-{nome}"' in pagina, nome


# ------------------------------------------------------------------ capítulo 12 por seção


def _fixture() -> dict:
    return json.loads(FIXTURE_SECOES.read_text(encoding="utf-8"))


@pytest.mark.parametrize("nome", SECOES)
def test_secoes_sobre_a_fixture(nome):
    h = FIGURAS[nome]({"secoes": _fixture()})
    assert re.match(ABERTURA.format(nome=nome), h)
    assert h.count("<svg") == 1 and "<title>" in h
    assert "—" not in h
    _tips(h)
    assert "Cobertura parcial: 7 UFs completas" in h
    assert (
        re.search(r'id="[^"]*(chart|map|scatter|legend|readout)"[^>]*>\s*<', h) is None
    )


@pytest.mark.parametrize("nome", SECOES)
def test_secoes_cobertura_completa(nome):
    S = _fixture()
    S["cobertura"]["parcial"] = False
    h = FIGURAS[nome]({"secoes": S})
    assert "Cobertura completa" in h and "parcial" not in h.split("<figcaption>")[1]


def test_secoes_listas_vazias_dizem_que_nao_ha():
    S = _fixture()
    for k in ("tipo_arquivo", "tipo_urna", "cargas"):
        S["outras"][k] = []
    S["outras"]["recebimento"]["por_hora"] = []
    S["outras"]["horarios"]["histograma_encerramento"] = []
    h = FIGURAS["secoes_outras"]({"secoes": S})
    assert h.count("nenhuma seção nesta condição") == 5
    S["urna"]["dentro_local"]["pares"] = []
    h = FIGURAS["modelo_urna_zona"]({"secoes": S})
    assert "nenhuma seção nesta condição" in h


def test_secoes_mapa_agrupa_acima_de_seis_mil():
    S = _fixture()
    base = S["extremos"]["mapa"]["pontos"][0]
    S["extremos"]["mapa"]["pontos"] = [
        [base[0] + (i % 80) * 0.01, base[1] + (i // 80) * 0.01, 1, 0, 2]
        for i in range(6100)
    ]
    h = FIGURAS["secoes_90"]({"secoes": S})
    assert "células de 0,25 grau" in h
    assert len(_tips(h)["_rows"]["linhas"]) < 100


def test_secoes_ausente_vira_pendente():
    h = FIGURAS["secoes_90"]({})
    assert 'class="pendente"' in h and "secoes" in h


def test_clusters_alterna_por_regiao():
    h = FIGURAS["clusters_secoes"]({"secoes": _fixture()})
    assert 'data-as="regiao>' in h and 'data-af="regiao>' in h
    assert 'data-alt="regiao"' in h
    assert h.count("<tr>") >= 21  # cabeçalho e as 20 amostras do grupo mais atípico
