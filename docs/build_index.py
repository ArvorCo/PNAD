#!/usr/bin/env python3
"""Generate docs/index.html from PNADC data.

Runs `pnad dashboard --format json` twice (trimestral + anual), merges the
payloads, and substitutes them into docs/index.template.html.

Usage:
    python docs/build_index.py
    python docs/build_index.py --tri-input data/outputs/base_labeled_npv.csv \
                               --ann-input data/outputs/base_anual_labeled_npv.csv

The resulting docs/index.html is a self-contained static page suitable for
GitHub Pages (main:/docs).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path
from string import Template

ROOT = Path(__file__).resolve().parent.parent
DOCS = Path(__file__).resolve().parent
TEMPLATE = DOCS / "index.template.html"
OUTPUT = DOCS / "index.html"
GEOJSON = DOCS / "geo" / "br-uf.geojson"


def run_dashboard(input_csv: Path, *, mode: str, extra: list[str]) -> dict:
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "pnad.py"),
        "dashboard",
        "--input",
        str(input_csv),
        "--format",
        "json",
        "--mode",
        mode,
        *extra,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--tri-input",
        default=str(ROOT / "data" / "outputs" / "base_labeled_npv.csv"),
        help="Trimestral labeled NPV CSV",
    )
    p.add_argument(
        "--ann-input",
        default=str(ROOT / "data" / "outputs" / "base_anual_labeled_npv.csv"),
        help="Anual labeled NPV CSV",
    )
    p.add_argument(
        "--output",
        default=str(OUTPUT),
        help="Output HTML path (default: docs/index.html)",
    )
    args = p.parse_args()

    tri_csv = Path(args.tri_input)
    ann_csv = Path(args.ann_input)

    if not TEMPLATE.exists():
        print(f"ERROR: template missing: {TEMPLATE}", file=sys.stderr)
        return 2
    if not GEOJSON.exists():
        print(f"ERROR: geojson missing: {GEOJSON}", file=sys.stderr)
        return 2

    print(f"[build] trimestral: {tri_csv}", file=sys.stderr)
    tri = run_dashboard(tri_csv, mode="trimestral", extra=[])

    print(f"[build] anual: {ann_csv}", file=sys.stderr)
    ann = run_dashboard(
        ann_csv,
        mode="anual",
        extra=["--composition-by-band", "--dependency-ranking", "--source-detail"],
    )

    geo = json.loads(GEOJSON.read_text(encoding="utf-8"))

    payload = {
        "trimestral": tri,
        "anual": ann,
        "geojson": geo,
        "built_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "vintage_tri": tri.get("target", ""),
        "vintage_ann": ann.get("target", ""),
    }

    tpl = Template(TEMPLATE.read_text(encoding="utf-8"))
    html = tpl.safe_substitute(
        PAYLOAD=json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        BUILT_AT=payload["built_at"],
        VINTAGE_TRI=payload["vintage_tri"],
        VINTAGE_ANN=payload["vintage_ann"],
    )

    out = Path(args.output)
    out.write_text(html, encoding="utf-8")
    kb = out.stat().st_size / 1024
    print(f"[build] wrote {out} ({kb:.1f} KB)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
