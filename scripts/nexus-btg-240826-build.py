#!/usr/bin/env python3
"""Inject generated SVG evidence into the 24 Aug. BTG/Nexus dossier."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from svgkit import inject  # noqa: E402

FIGURES = ROOT / "docs/assets/figuras/nexus_btg_240826.json"
TARGET = ROOT / "docs/nexus_btg_240826.html"


def main() -> None:
    figures = json.loads(FIGURES.read_text(encoding="utf-8"))
    count = inject(TARGET, figures)
    print(
        json.dumps(
            {"target": str(TARGET), "figures_injected": count}, ensure_ascii=False
        )
    )


if __name__ == "__main__":
    main()
