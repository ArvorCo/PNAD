"""O sitemap publica toda página indexável de docs/ e nada além dela."""

import datetime as dt
import importlib.util
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "sitemap_build", ROOT / "scripts/sitemap-build.py"
)
assert spec is not None and spec.loader is not None
sitemap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sitemap)

NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def test_exclui_template_noindex_e_fontes_de_card():
    urls = {url for url, _ in sitemap.entradas()}
    assert f"{sitemap.SITE}/" in urls
    assert f"{sitemap.SITE}/social.html" not in urls
    assert not any(".template.html" in u for u in urls)
    assert not any("/assets/" in u for u in urls)
    assert all(u.startswith(sitemap.SITE + "/") for u in urls)


def test_xml_valido_com_lastmod_iso():
    itens = [("https://brasil.arvor.co/a&b.html", dt.date(2026, 10, 7))]
    raiz = ET.fromstring(sitemap.sitemap_xml(itens))
    assert raiz.findtext("sm:url/sm:loc", namespaces=NS) == (
        "https://brasil.arvor.co/a&b.html"
    )
    assert raiz.findtext("sm:url/sm:lastmod", namespaces=NS) == "2026-10-07"


def test_arquivos_publicados_estao_atualizados():
    assert sitemap.main(["--check"]) == 0


def test_robots_aponta_para_o_sitemap():
    texto = sitemap.robots_txt()
    assert "Sitemap: https://brasil.arvor.co/sitemap.xml" in texto
    assert "Disallow: /social.html" in texto
