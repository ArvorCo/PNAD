#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional
from urllib.request import urlopen, Request


BCB_SERIES_INDEX = 433  # IPCA (variação mensal, %) – mensal


def _fetch_bcb(series: int, last: Optional[int] = None) -> list[dict]:
    base = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{series}/dados"
    if last:
        url = f"{base}/ultimos/{int(last)}?formato=json"
    else:
        url = f"{base}?formato=json"
    req = Request(url, headers={"User-Agent": "pnad-npv/1.0"})
    with urlopen(req, timeout=60) as resp:
        data = resp.read().decode("utf-8")
    items = json.loads(data)
    # items like {"data":"07/2025","valor":"123.45"} or sometimes dd/mm/yyyy
    return items


def _norm_date_br(s: str) -> tuple[int, int]:
    # Accept "mm/yyyy" or "dd/mm/yyyy"
    s = s.strip()
    parts = s.split("/")
    if len(parts) == 2:
        m, y = int(parts[0]), int(parts[1])
        return y, m
    if len(parts) == 3:
        _, m, y = int(parts[0]), int(parts[1]), int(parts[2])
        return y, m
    raise ValueError(f"invalid BCB date: {s}")


def emit_csv(items: Iterable[dict], out: Path) -> Path:
    out = Path(out)
    # Parse and sort
    parsed = []
    for it in items:
        y, m = _norm_date_br(str(it.get("data", "")))
        sval = str(it.get("valor", "")).replace(",", ".").strip()
        if not sval:
            continue
        try:
            f = float(sval)
        except Exception:
            continue
        parsed.append((f"{y}-{m:02d}", f))
    parsed.sort(key=lambda x: x[0])

    # Heuristic: if typical magnitude < 20, treat as monthly percent and build an index via compounding
    last_vals = [v for _, v in parsed[-120:]] or [v for _, v in parsed]
    is_percent = False
    if last_vals:
        mid = sorted(last_vals)[len(last_vals)//2]
        is_percent = abs(mid) < 20.0

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "index"])  # index base cancels in ratios
        if is_percent:
            idx = 100.0
            for d, v in parsed:
                idx *= (1.0 + (v / 100.0))
                w.writerow([d, f"{idx:.6f}"])
        else:
            for d, v in parsed:
                w.writerow([d, f"{v:.6f}"])
    return out


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Fetch monthly IPCA index and write CSV (date,index)")
    p.add_argument("--out", required=True, type=Path, help="Output CSV path, e.g., data/ipca.csv")
    p.add_argument("--source", default="bcb", choices=["bcb"], help="Data source (default: bcb)")
    p.add_argument("--last", type=int, default=None, help="Fetch only last N observations (optional)")
    args = p.parse_args(argv)

    if args.source == "bcb":
        items = _fetch_bcb(BCB_SERIES_INDEX, last=args.last)
        out = emit_csv(items, args.out)
        print(out)
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
