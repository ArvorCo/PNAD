"""Figuras do catálogo do dossiê da apuração: presença, contrato HTML e fichas."""

import importlib.util
import json
import re
from pathlib import Path

import pytest
from apuracao_2026 import pagina_comum as C
from apuracao_2026.pagina_figuras import FIGURAS
from apuracao_2026.pagina_interativo import interativo_html

ROOT = Path(__file__).resolve().parents[1]
CATALOGO = ROOT / "analysis/apuracao_2026/CATALOGO_FIGURAS.md"
NOMES = re.findall(
    r"^\| `([a-z0-9_]+)` \|", CATALOGO.read_text(encoding="utf-8"), re.MULTILINE
)

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
    assert len(NOMES) == 35
    assert set(NOMES) <= set(FIGURAS)


@pytest.mark.parametrize("nome", NOMES)
def test_contrato_da_figura(html, nome):
    h = html[nome]
    assert h.startswith(f'<figure class="reveal fig-i" id="fig-{nome}"')
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
    assert "—" not in pagina
    for nome in NOMES:
        assert f'id="fig-{nome}"' in pagina, nome
