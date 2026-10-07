#!/usr/bin/env python3
"""Gera docs/sitemap.xml e docs/robots.txt para brasil.arvor.co.

Entram só as páginas HTML de primeiro nível em docs/ rastreadas pelo git,
porque é isso que o GitHub Pages publica. Ficam de fora os templates
(``*.template.html``), as páginas marcadas com ``noindex`` e as fontes dos
cards sociais em ``docs/assets/og``. O ``lastmod`` é a data do último commit
que tocou o arquivo; arquivo sem commit usa a data de hoje.

Uso: ``python3 scripts/sitemap-build.py`` (``--check`` só compara, sem gravar).
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SITE = "https://brasil.arvor.co"
NOINDEX = re.compile(r'<meta[^>]+name="robots"[^>]+noindex', re.IGNORECASE)
HEAD_BYTES = 16_384


def paginas_rastreadas(docs: Path = DOCS) -> list[Path]:
    """HTML de primeiro nível em docs/ que o git rastreia, em ordem estável."""
    saida = subprocess.run(
        ["git", "ls-files", "--", "*.html"],
        cwd=docs,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return sorted(docs / linha for linha in saida.splitlines() if "/" not in linha)


def indexavel(pagina: Path) -> bool:
    if pagina.name.endswith(".template.html"):
        return False
    with pagina.open("rb") as fh:
        cabeca = fh.read(HEAD_BYTES).decode("utf-8", errors="replace")
    return not NOINDEX.search(cabeca)


def ultimo_commit(pagina: Path, hoje: dt.date | None = None) -> dt.date:
    saida = subprocess.run(
        ["git", "log", "-1", "--format=%cs", "--", pagina.name],
        cwd=pagina.parent,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    if saida:
        return dt.date.fromisoformat(saida)
    return hoje or dt.date.today()


def url_publica(pagina: Path) -> str:
    if pagina.name == "index.html":
        return f"{SITE}/"
    return f"{SITE}/{pagina.name}"


def entradas(docs: Path = DOCS) -> list[tuple[str, dt.date]]:
    return [
        (url_publica(p), ultimo_commit(p))
        for p in paginas_rastreadas(docs)
        if indexavel(p)
    ]


def sitemap_xml(itens: list[tuple[str, dt.date]]) -> str:
    linhas = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for url, data in itens:
        linhas.append(
            f"  <url><loc>{escape(url)}</loc><lastmod>{data.isoformat()}</lastmod></url>"
        )
    linhas.append("</urlset>")
    return "\n".join(linhas) + "\n"


def robots_txt() -> str:
    return (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /social.html\n"
        "Disallow: /assets/og/\n"
        f"Sitemap: {SITE}/sitemap.xml\n"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Gera docs/sitemap.xml e docs/robots.txt para brasil.arvor.co."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="não grava; sai com 1 se os arquivos publicados estão desatualizados",
    )
    args = parser.parse_args(argv)

    itens = entradas()
    alvos = {
        DOCS / "sitemap.xml": sitemap_xml(itens),
        DOCS / "robots.txt": robots_txt(),
    }
    desatualizados = [
        caminho
        for caminho, conteudo in alvos.items()
        if not caminho.exists() or caminho.read_text(encoding="utf-8") != conteudo
    ]
    if args.check:
        for caminho in desatualizados:
            print(f"desatualizado: {caminho.relative_to(ROOT)}")
        return 1 if desatualizados else 0
    for caminho, conteudo in alvos.items():
        caminho.write_text(conteudo, encoding="utf-8")
    print(f"{len(itens)} URLs em docs/sitemap.xml; robots.txt gravado")
    return 0


if __name__ == "__main__":
    sys.exit(main())
