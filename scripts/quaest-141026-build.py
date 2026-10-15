#!/usr/bin/env python3
"""Gera o dossiê preliminar da Quaest de 14/10 a partir do acervo conferido."""

import argparse
from pathlib import Path

from quaest_141026.audit import ROOT, SLUG, write
from quaest_141026.g1 import write as write_g1
from quaest_141026.history import write_sources
from quaest_141026.integra.data import write as write_integra
from quaest_141026.integra.provenance import update_poll
from quaest_141026.panel import ingest, integrate
from quaest_141026.view import render

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--import-panel",
        type=Path,
        help="Importa o HTML com gráficos salvo pelo usuário, sem acesso remoto.",
    )
    parser.add_argument(
        "--render-history-sources",
        action="store_true",
        help="Regenera as quatro páginas de evidência histórica a partir dos PDFs locais.",
    )
    args = parser.parse_args()
    if args.import_panel:
        integrate(ingest(args.import_panel))
    if args.render_history_sources:
        write_sources()
    update_poll()
    write_integra()
    write_g1()
    data = write()
    output = ROOT / "docs" / (SLUG + ".html")
    output.write_text(render(data), encoding="utf-8")
    print(output)
