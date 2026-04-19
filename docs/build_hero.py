#!/usr/bin/env python3
"""Generate docs/assets/hero.png — a static Brazil choropleth for the README.

Uses matplotlib + the br-uf.geojson shipped in docs/geo.
Output: docs/assets/hero.png (1600×900 @ 2x dpi).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.collections import PatchCollection
from matplotlib.path import Path as MplPath

ROOT = Path(__file__).resolve().parent.parent
DOCS = Path(__file__).resolve().parent
GEO = DOCS / "geo" / "br-uf.geojson"
OUT = DOCS / "assets" / "hero.png"

# Brazilian flag palette — amber → green gradient
PALETTE = [
    (0.00, "#8a5400"),
    (0.18, "#c47800"),
    (0.35, "#e8a700"),
    (0.55, "#ffdf00"),
    (0.75, "#009c3b"),
    (1.00, "#00673a"),
]
CMAP = LinearSegmentedColormap.from_list("brasil", PALETTE)

PAPER = "#f6f3ee"
INK = "#0a1a12"
RULE = "#1a1a1a"


def _geojson_to_patches(geo: dict, values: dict) -> tuple[list, list]:
    patches: list = []
    vals: list = []
    for f in geo["features"]:
        name = f["properties"]["name"]
        v = values.get(name)
        if v is None:
            continue
        coords = f["geometry"]["coordinates"]
        polygons = coords if f["geometry"]["type"] == "MultiPolygon" else [coords]
        for polygon in polygons:
            ring = polygon[0]
            verts = [(p[0], p[1]) for p in ring]
            codes = (
                [MplPath.MOVETO]
                + [MplPath.LINETO] * (len(verts) - 2)
                + [MplPath.CLOSEPOLY]
            )
            path = MplPath(verts, codes)
            patches.append(mpatches.PathPatch(path))
            vals.append(v)
    return patches, vals


def main() -> int:
    if not GEO.exists():
        print(f"ERROR: missing {GEO}", file=sys.stderr)
        return 2

    # Run pnad dashboard anual and parse values per UF.
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "pnad.py"),
            "dashboard",
            "--input",
            str(ROOT / "data" / "outputs" / "base_anual_labeled_npv.csv"),
            "--format",
            "json",
            "--mode",
            "anual",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    ufs = payload["modes"]["alvo"]["uf"]
    values = {u["label"]: u["avg_household_sm"] for u in ufs}

    geo = json.loads(GEO.read_text(encoding="utf-8"))
    patches, vals = _geojson_to_patches(geo, values)
    vmin = min(vals)
    vmax = max(vals)

    fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAPER)
    ax.set_facecolor(PAPER)

    pc = PatchCollection(patches, cmap=CMAP, edgecolor="white", linewidth=0.7)
    pc.set_array([(v - vmin) / (vmax - vmin) if vmax > vmin else 0.5 for v in vals])
    ax.add_collection(pc)

    # Frame the map to Brazil's bounding box.
    ax.set_xlim(-75, -32)
    ax.set_ylim(-35, 6)
    ax.set_aspect("equal")
    ax.axis("off")

    # Masthead text
    fig.text(
        0.05,
        0.92,
        "O   B R A S I L   Q U E   O S   N Ú M E R O S   R E V E L A M",
        fontsize=11,
        color=INK,
        family="serif",
        weight="bold",
    )
    fig.text(
        0.05,
        0.86,
        "renda domiciliar média por UF",
        fontsize=22,
        color=INK,
        family="serif",
        style="italic",
    )
    fig.text(
        0.05,
        0.82,
        "em múltiplos do salário mínimo · PNADC anual, visita 5 · IBGE",
        fontsize=11,
        color="#6b6762",
        family="sans-serif",
    )

    # Data extremes annotations
    max_uf = max(values, key=values.get)
    min_uf = min(values, key=values.get)
    fig.text(
        0.70,
        0.20,
        f"mais rica · {max_uf}\n{values[max_uf]:.2f} SM",
        fontsize=10,
        color="#00673a",
        family="sans-serif",
        weight="bold",
    )
    fig.text(
        0.70,
        0.13,
        f"mais pobre · {min_uf}\n{values[min_uf]:.2f} SM",
        fontsize=10,
        color="#8a5400",
        family="sans-serif",
        weight="bold",
    )

    # Thin red rule, bottom-left
    fig.lines.append(
        plt.Line2D(
            [0.05, 0.12],
            [0.05, 0.05],
            color="#009c3b",
            linewidth=2,
            transform=fig.transFigure,
        )
    )
    fig.text(
        0.05,
        0.02,
        "A R V O R   ·   L E O N A R D O   D I A S",
        fontsize=8,
        color="#6b6762",
        family="sans-serif",
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=144, bbox_inches="tight", facecolor=PAPER)
    print(f"[hero] wrote {OUT} ({OUT.stat().st_size / 1024:.1f} KB)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
