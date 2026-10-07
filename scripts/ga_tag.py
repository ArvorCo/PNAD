"""Tag do Google Analytics (gtag.js) de brasil.arvor.co.

Uma fonte só para a tag: toda página navegável em `docs/` a carrega logo depois
do `<meta charset>`. Os geradores chamam `injetar()` no HTML pronto; o CLI
(`python3 scripts/ga_tag.py`) passa por `docs/*.html` e `docs/*.template.html`
e acrescenta a tag onde falta, sem duplicar. `tests/test_ga_tag.py` falha no CI
se qualquer página publicada ficar sem ela.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

GA_ID = "G-ZPYEE8P9YC"

GA_TAG = (
    "<!-- Google tag (gtag.js) -->"
    f'<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>'
    "<script>window.dataLayer=window.dataLayer||[];"
    "function gtag(){dataLayer.push(arguments);}gtag('js',new Date());"
    f"gtag('config','{GA_ID}');</script>"
)

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

_CHARSET = re.compile(r'<meta\s+charset="?utf-8"?\s*/?>', re.IGNORECASE)
_HEAD = re.compile(r"<head[^>]*>", re.IGNORECASE)


def injetar(html: str) -> str:
    """Devolve o HTML com a tag uma vez só, logo após o charset (ou o <head>)."""
    if GA_ID in html:
        return html
    for padrao in (_CHARSET, _HEAD):
        alvo = padrao.search(html)
        if alvo:
            fim = alvo.end()
            quebra = "\n" if html[fim : fim + 1] == "\n" else ""
            return html[:fim] + quebra + GA_TAG + html[fim:]
    raise ValueError("HTML sem <head>: não há onde pôr a tag do Google Analytics")


def paginas(docs: Path = DOCS) -> list[Path]:
    """Páginas navegáveis e templates: `docs/*.html`, sem os cards de `assets/og`."""
    return sorted(docs.glob("*.html"))


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    conferir = "--check" in args
    faltam: list[Path] = []
    for pagina in paginas():
        texto = pagina.read_text(encoding="utf-8")
        if GA_ID in texto:
            continue
        faltam.append(pagina)
        if not conferir:
            pagina.write_text(injetar(texto), encoding="utf-8")
    verbo = "sem tag" if conferir else "tag acrescentada"
    for pagina in faltam:
        print(f"{verbo}: {pagina.relative_to(ROOT)}")
    print(f"{len(faltam)} de {len(paginas())} páginas {verbo}")
    return 1 if (conferir and faltam) else 0


if __name__ == "__main__":
    raise SystemExit(main())
