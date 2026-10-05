"""Build do dossiê da apuração: capítulos, travessão, figuras e capítulo pendente."""

import importlib.util
import re
import shutil
from pathlib import Path

import pytest
from apuracao_2026 import pagina_comum as C
from apuracao_2026.pagina_view import capitulos

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "apuracao_build", ROOT / "scripts/apuracao-2026-build.py"
)
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)

IDS = [c.ident for c in capitulos()]


@pytest.fixture(scope="module")
def pagina(tmp_path_factory):
    saida = tmp_path_factory.mktemp("pagina") / "apuracao.html"
    _, estado = build.construir(C.DADOS, saida)
    return saida.read_text(encoding="utf-8"), estado


def test_quinze_capitulos_com_id(pagina):
    html, estado = pagina
    assert len(IDS) == 15
    for ident in IDS:
        assert f'id="{ident}"' in html
        assert f'href="#{ident}"' in html
    assert set(estado) == set(IDS)


def test_sem_travessao(pagina):
    assert "—" not in pagina[0]


def test_metatags_og(pagina):
    html = pagina[0]
    assert f"https://brasil.arvor.co/img/og/{C.SLUG}.png" in html
    assert '<meta property="og:image:width" content="1200">' in html
    assert '<meta property="og:image:height" content="630">' in html


def test_sem_marcas_de_estouro_lateral(pagina):
    html = pagina[0]
    assert "100vw" not in html
    assert not re.search(r'<svg[^>]*\bwidth="\d{4,}"', html)
    # figura larga rola dentro do próprio quadro, nunca a página
    assert ".chart-scroll{overflow-x:auto}" in html
    assert "figure img{display:block;max-width:100%" in html


def test_figuras_nao_vazias(pagina):
    html = pagina[0]
    svgs = re.findall(r"<svg\b.*?</svg>", html, flags=re.DOTALL)
    assert len(svgs) >= 20
    for svg in svgs:
        assert "<title>" in svg
        assert re.search(r"<(path|rect|circle|line)\b", svg)
        vb = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg)
        assert vb and float(vb.group(1)) > 0 and float(vb.group(2)) > 0


def test_tabelas_marcam_colunas_numericas(pagina):
    assert 'class="num"' in pagina[0]


def test_json_ausente_vira_pendente(tmp_path):
    for nome in ("presidente.json", "noticias_noite.json"):
        origem = C.DADOS / nome
        if origem.exists():
            shutil.copy(origem, tmp_path / nome)
    saida = tmp_path / "pendente.html"
    _, estado = build.construir(tmp_path, saida)
    html = saida.read_text(encoding="utf-8")
    assert '<section class="pendente" id="camara">' in html
    assert "capítulo em preparação: <code>camara.json</code>" in html
    assert estado["camara"] is False
    for ident in IDS:
        assert f'id="{ident}"' in html


def test_chave_ausente_vira_pendente_sem_excecao(tmp_path):
    (tmp_path / "camara.json").write_text('{"vagas_total": 513}', encoding="utf-8")
    d = C.Dados(pasta=tmp_path)
    cap = next(c for c in capitulos() if c.ident == "camara")
    html, ok = C.montar(cap, d)
    assert not ok
    assert 'class="pendente"' in html
    assert "chave ausente" in html
    assert any("camara" in a for a in d.avisos)


def test_formato_brasileiro():
    assert C.num(47.0278, 2) == "47,03"
    assert C.inteiro(2224965) == "2.224.965"
    assert C.sinal(-3.27, 2) == "−3,27"
    assert C.milhoes(2224965) == "2,22 milhões"


H3_SECOES = [
    "Da zona para a seção",
    "Seções acima de 90%",
    "Quatro grupos de seções",
    "Modelo de urna",
    "O que mais a seção mostra",
    "O que a seção prova e o que não prova",
]


def _capitulo_anomalias(html: str) -> str:
    ini = html.index('<section id="anomalias"')
    return html[ini : html.index("</section>", ini)]


def test_capitulo_12_ganha_parte_por_secao(tmp_path):
    for origem in C.DADOS.glob("*.json"):
        shutil.copy(origem, tmp_path / origem.name)
    if not (tmp_path / "secoes.json").exists():
        shutil.copy(
            ROOT / "tests/fixtures/apuracao_2026/secoes_fixture.json",
            tmp_path / "secoes.json",
        )
    saida = tmp_path / "secoes.html"
    _, estado = build.construir(tmp_path, saida)
    cap = _capitulo_anomalias(saida.read_text(encoding="utf-8"))
    assert estado["anomalias"] is True
    for h3 in H3_SECOES:
        assert f"<h3>{h3}</h3>" in cap, h3
    assert 'id="fig-clusters_secoes"' in cap and 'id="fig-modelo_urna_zona"' in cap
    assert "—" not in cap and "fraude" not in cap.split("Da zona para a seção")[1]


def test_capitulo_12_sem_secoes_mantem_a_zona(tmp_path):
    for origem in C.DADOS.glob("*.json"):
        if origem.name != "secoes.json":
            shutil.copy(origem, tmp_path / origem.name)
    saida = tmp_path / "sem_secoes.html"
    _, estado = build.construir(tmp_path, saida)
    cap = _capitulo_anomalias(saida.read_text(encoding="utf-8"))
    assert estado["anomalias"] is True
    assert "Da zona para a seção" not in cap and 'id="fig-mapa_anomalias"' in cap
