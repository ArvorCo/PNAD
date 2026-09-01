#!/usr/bin/env python3
"""Injeta as figuras SVG geradas nos marcadores do dossiê BTG/Nexus 03/08/2026.

Cada gerador de figuras grava um dicionário {id: svg} em docs/assets/figuras/.
Este script junta todos e substitui o conteúdo entre <!--FIG:id--> e
<!--/FIG:id--> no HTML, mantendo o restante da página editável à mão.

    python3 scripts/nexus-btg-082026-figuras.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from svgkit import inject  # noqa: E402

FIGURES = ROOT / "docs/assets/figuras"
TARGETS = [
    ROOT / "docs/nexus_btg_082026_1.html",
]


def load_all() -> dict[str, str]:
    figures: dict[str, str] = {}
    for path in sorted(FIGURES.glob("*.json")):
        figures.update(json.loads(path.read_text(encoding="utf-8")))
    return figures


def main() -> None:
    figures = load_all()
    report = {"figuras_disponiveis": len(figures), "arquivos": {}}
    for target in TARGETS:
        text = target.read_text(encoding="utf-8")
        wanted = {name for name in figures if f"<!--FIG:{name}-->" in text}
        missing = {
            marker.split("<!--FIG:")[1].split("-->")[0]
            for marker in text.split()
            if marker.startswith("<!--FIG:")
        } - set(figures)
        count = inject(target, {name: figures[name] for name in wanted})
        report["arquivos"][target.name] = {
            "injetadas": count,
            "sem_figura": sorted(missing),
        }
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
