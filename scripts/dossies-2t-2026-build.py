#!/usr/bin/env python3
"""Gera os dois dossiês sem modificar o agregador ou suas versões publicadas."""

from dossies_2t_2026.audit import ROOT, write
from dossies_2t_2026.datafolha_view import render as datafolha
from dossies_2t_2026.nexus_view import render as nexus

if __name__ == "__main__":
    data = write()
    for house, renderer in [("nexus", nexus), ("datafolha", datafolha)]:
        path = ROOT / "docs" / (data[house]["slug"] + ".html")
        path.write_text(renderer(data[house]))
        print(path)
