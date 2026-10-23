#!/usr/bin/env python3
"""Gera o dossiê atual; não modifica centrais nem snapshots."""

from datafolha_221026.audit import ROOT, write
from datafolha_221026.view import render

if __name__ == "__main__":
    data = write()
    path = ROOT / "docs/datafolha_22102026.html"
    path.write_text(render(data), encoding="utf-8")
    print(path)
