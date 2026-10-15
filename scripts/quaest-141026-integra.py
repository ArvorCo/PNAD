#!/usr/bin/env python3
"""Arquiva/renderiza a íntegra local e publica transcrições e contas auditáveis."""

import argparse

from quaest_141026.integra.archive import render_pages
from quaest_141026.integra.data import write

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--render-pages",
        action="store_true",
        help="Regenera PDF público e 152 páginas WebP a partir da cópia arquivada.",
    )
    args = parser.parse_args()
    if args.render_pages:
        render_pages()
    data = write()
    print(f'{len(data["temas"])} temas; {len(data["catalogo"])} páginas catalogadas')
