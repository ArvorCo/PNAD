#!/usr/bin/env python3
"""
Find duplicated code cells in a Jupyter notebook.

Usage:
  python scripts/find-duplicate-cells.py notebooks/PNADC_exploration.ipynb [--mode normalized|raw] [--min-lines N]

- mode:
    raw        : compares exact cell source (default)
    normalized : trims whitespace, drops empty lines, normalizes indentation
                 to better catch near-identical cells
- min-lines: minimum number of non-empty lines in a cell to consider (default: 1)

Outputs groups of duplicated cells (same signature) with their indices and a short snippet.
"""

import argparse
import hashlib
import json
from pathlib import Path


def parse_cells_fallback(path: Path):
    code_cells = []  # list of tuples (nb_index, [source_lines])
    nb_index = -1
    in_code_cell = False
    in_source = False
    current_lines = []

    def flush_current(nb_idx):
        nonlocal current_lines
        if in_code_cell:
            code_cells.append((nb_idx, current_lines[:]))
        current_lines = []

    with path.open('r', encoding='utf-8') as f:
        for raw in f:
            line = raw.rstrip('\n')
            if '"cell_type"' in line and '"cell_type":' in line:
                nb_index += 1
                in_code_cell = '"code"' in line
                in_source = False
                current_lines = []
                continue

            if not in_code_cell:
                continue

            if '"source"' in line and '[]' in line:
                # empty source
                code_cells.append((nb_index, []))
                in_source = False
                current_lines = []
                continue

            if '"source"' in line and '[' in line:
                in_source = True
                current_lines = []
                continue

            if in_source:
                stripped = line.strip()
                if stripped.startswith(']'):
                    in_source = False
                    code_cells.append((nb_index, current_lines[:]))
                    current_lines = []
                    continue
                # try to parse a JSON string line
                try:
                    # remove trailing comma if present
                    s = stripped
                    if s.endswith(','):
                        s = s[:-1]
                    # only attempt if it begins and ends with quotes
                    if s.startswith('"') and s.endswith('"'):
                        text = json.loads(s)
                        current_lines.append(text)
                except Exception:
                    # fallback: keep raw content
                    current_lines.append(raw)

    return code_cells


def normalize_lines(lines):
    # Remove trailing newlines from each line and strip whitespace
    norm = []
    for line in lines:
        s = line.rstrip("\n").strip()
        if s == "":
            continue
        norm.append(s)
    return norm


def signature(lines, mode: str):
    if mode == "normalized":
        lines = normalize_lines(lines)
    else:
        # raw: use as-is
        lines = [l.rstrip("\n") for l in lines]

    joined = "\n".join(lines)
    sha = hashlib.sha256(joined.encode("utf-8")).hexdigest()
    return sha, lines


def analyze(path: Path, mode: str, min_lines: int):
    try:
        txt = Path(path).read_text(encoding="utf-8")
        try:
            nb = json.loads(txt)
        except json.JSONDecodeError:
            class LooseJSONDecoder(json.JSONDecoder):
                def __init__(self, *args, **kwargs):
                    kwargs["strict"] = False
                    super().__init__(*args, **kwargs)
            nb = json.loads(txt, cls=LooseJSONDecoder)
        code_cells = []
        for idx, cell in enumerate(nb.get("cells", [])):
            if cell.get("cell_type") != "code":
                continue
            src = cell.get("source", [])
            code_cells.append((idx, src))
    except Exception:
        # fallback line-oriented parser for slightly malformed notebooks
        code_cells = parse_cells_fallback(Path(path))

    sig_map = {}
    for code_idx, (nb_idx, src) in enumerate(code_cells):
        sha, norm_lines = signature(src, mode)
        # enforce min_lines threshold on the normalized/selected lines
        effective_lines = [l for l in norm_lines if l.strip()]
        if len(effective_lines) < min_lines:
            continue
        entry = sig_map.setdefault(sha, {"cells": [], "snippet": effective_lines[:3]})
        entry["cells"].append({"nb_index": nb_idx, "code_index": code_idx, "lines": len(effective_lines)})

    # Only keep signatures with duplicates
    duplicates = {k: v for k, v in sig_map.items() if len(v["cells"]) > 1}
    return duplicates, len(code_cells)


def main():
    ap = argparse.ArgumentParser(description="Find duplicated code cells in a notebook")
    ap.add_argument("notebook", type=Path)
    ap.add_argument("--mode", choices=["raw", "normalized"], default="raw")
    ap.add_argument("--min-lines", type=int, default=1)
    args = ap.parse_args()

    duplicates, total_code_cells = analyze(args.notebook, args.mode, args.min_lines)

    print(f"Notebook: {args.notebook}")
    print(f"Total code cells: {total_code_cells}")
    print(f"Mode: {args.mode}; Min lines: {args.min_lines}")
    print()

    if not duplicates:
        print("No duplicate code cells found with current settings.")
        return

    print(f"Duplicate groups: {len(duplicates)}\n")
    for i, (sha, info) in enumerate(sorted(duplicates.items(), key=lambda kv: (-len(kv[1]["cells"]), kv[0])) , start=1):
        cells = info["cells"]
        snippet = info["snippet"]
        print(f"Group {i}: occurrences={len(cells)} sha256={sha[:12]}")
        for c in cells:
            print(f"  - nb_index={c['nb_index']} code_index={c['code_index']} lines={c['lines']}")
        if snippet:
            print("  Snippet:")
            for ln in snippet:
                print(f"    {ln}")
        print()


if __name__ == "__main__":
    main()
