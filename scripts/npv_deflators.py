#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple


def _to_float(x: str) -> Optional[float]:
    if x is None:
        return None
    s = str(x).strip().replace(",", ".")
    if not s:
        return None
    try:
        return float(s)
    except Exception:
        return None


def read_ipca_csv(path: Path) -> Dict[str, float]:
    """Read a simple CSV of monthly IPCA index levels into a map.

    Accepted headers:
      - date,index              (date as YYYY-MM)
      - year,month,index        (year=int, month=int)

    Returns: { 'YYYY-MM': index_level }
    """
    path = Path(path)
    with path.open("r", encoding="utf-8") as fh:
        r = csv.DictReader(fh)
        cols = [c.strip().lower() for c in (r.fieldnames or [])]
        date_based = ("date" in cols and "index" in cols)
        ymb_based = all(c in cols for c in ("year", "month", "index"))
        if not (date_based or ymb_based):
            raise ValueError("ipca csv must have columns (date,index) or (year,month,index)")
        out: Dict[str, float] = {}
        for row in r:
            if date_based:
                key = str(row.get("date", "")).strip()
            else:
                y = str(row.get("year", "")).strip()
                m = str(row.get("month", "")).strip()
                if m and len(m) == 1:
                    m = "0" + m
                key = f"{y}-{m}"
            idx = _to_float(row.get("index", ""))
            if key and idx is not None:
                out[key] = idx
        return out


def build_deflators(index: Dict[str, float], target: str) -> Dict[str, float]:
    """Compute deflator factors to convert values from t to target month.

    Factor = index[target] / index[t]. If either is missing, t not included.
    """
    if target not in index:
        raise ValueError(f"target {target} missing from index data")
    target_idx = index[target]
    out: Dict[str, float] = {}
    for ym, val in index.items():
        if val and val != 0:
            out[ym] = float(target_idx) / float(val)
    return out


def _detect_year_quarter_columns(headers: Iterable[str]) -> Tuple[Optional[str], Optional[str]]:
    # Prefer canonical names with labels attached
    year_col = next((c for c in headers if c.startswith("Ano__")), None)
    quarter_col = next((c for c in headers if c.startswith("Trimestre__")), None)
    # Fallback to raw names
    if year_col is None:
        year_col = "Ano" if "Ano" in headers else None
    if quarter_col is None:
        quarter_col = "Trimestre" if "Trimestre" in headers else None
    return year_col, quarter_col


def _quarter_to_month(q: int) -> int:
    # Use last month of quarter as reference
    return {1: 3, 2: 6, 3: 9, 4: 12}.get(q, 12)


def apply_deflator_to_csv(
    in_path: Path,
    out_path: Path,
    factor_map: Dict[str, float],
    columns: Iterable[str],
    *,
    date_col: Optional[str] = None,
    year_col: Optional[str] = None,
    quarter_col: Optional[str] = None,
    target_label: str = "jul2025",
    min_wage: float = 1518.0,
) -> None:
    """Stream input CSV, apply deflator to given columns, write augmented CSV.

    - If date_col is provided (YYYY-MM), use it.
    - Else derive YYYY-MM from (year_col, quarter_col) using last month of quarter.
    - Adds two columns per input column: {col}_{target_label} and {col}_mw.
    """
    in_path = Path(in_path)
    out_path = Path(out_path)
    with in_path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fh_in, \
         out_path.open("w", encoding="utf-8", newline="") as fh_out:
        r = csv.DictReader(fh_in)
        headers = r.fieldnames or []

        if date_col is None:
            # Try detect year/quarter if not provided
            if year_col is None or quarter_col is None:
                ycol, qcol = _detect_year_quarter_columns(headers)
                year_col = year_col or ycol
                quarter_col = quarter_col or qcol
        # Validate
        if date_col is None and (not year_col or not quarter_col):
            raise ValueError("Could not determine date column nor (year,quarter) columns")

        cols = list(columns)
        missing = [c for c in cols if c not in headers]
        if missing:
            raise ValueError(f"Missing input columns: {missing}")

        # Prepare output header
        out_headers = headers[:]
        for c in cols:
            out_headers.append(f"{c}_{target_label}")
            out_headers.append(f"{c}_mw")
        w = csv.DictWriter(fh_out, fieldnames=out_headers)
        w.writeheader()

        for row in r:
            if date_col:
                ym = str(row.get(date_col, "")).strip()
            else:
                y = str(row.get(year_col or "", "")).strip()
                q = row.get(quarter_col or "", "")
                try:
                    q = int(str(q).strip())
                except Exception:
                    q = None
                m = _quarter_to_month(q or 4)
                ym = f"{y}-{m:02d}"

            factor = factor_map.get(ym)
            for c in cols:
                src = _to_float(row.get(c, ""))
                if src is None or factor is None:
                    row[f"{c}_{target_label}"] = ""
                    row[f"{c}_mw"] = ""
                else:
                    adj = float(src) * float(factor)
                    row[f"{c}_{target_label}"] = f"{adj:.2f}"
                    row[f"{c}_mw"] = f"{adj / float(min_wage):.6f}"
            w.writerow(row)


def _auto_income_columns(headers: Iterable[str]) -> Tuple[Optional[str], Optional[str]]:
    # Try find VD4019 and VD4020 variants (with or without label suffix)
    vd4019 = next((h for h in headers if h.startswith("VD4019")), None)
    vd4020 = next((h for h in headers if h.startswith("VD4020")), None)
    return vd4019, vd4020


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="NPV helpers for PNADC: build deflators and apply to income columns")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_defl = sub.add_parser("emit-factors", help="Emit monthly deflator factors to a target month")
    p_defl.add_argument("--ipca-csv", required=True, type=Path, help="CSV with monthly IPCA index levels")
    p_defl.add_argument("--target", default="2025-07", help="Target month YYYY-MM (default: 2025-07)")
    p_defl.add_argument("--out", required=True, type=Path, help="Output CSV path for deflators")

    p_apply = sub.add_parser("apply", help="Apply deflators to income columns, add *_jul2025 and *_mw columns")
    p_apply.add_argument("--in", dest="inp", required=True, type=Path, help="Input CSV path")
    p_apply.add_argument("--out", dest="out", required=True, type=Path, help="Output CSV path")
    p_apply.add_argument("--ipca-csv", required=True, type=Path, help="CSV with monthly IPCA index levels")
    p_apply.add_argument("--target", default="2025-07", help="Target month YYYY-MM (default: 2025-07)")
    p_apply.add_argument("--min-wage", dest="min_wage", default=1518.0, type=float, help="Current minimum wage in BRL")
    p_apply.add_argument("--columns", default=None, help="Comma-separated columns to deflate; default auto-detect VD4019/VD4020")
    p_apply.add_argument("--date-col", default=None, help="Column with YYYY-MM; else derive from Ano/Trimestre")
    p_apply.add_argument("--year-col", default=None, help="Year column name (auto-detect if omitted)")
    p_apply.add_argument("--quarter-col", default=None, help="Quarter column name (auto-detect if omitted)")

    args = p.parse_args(argv)

    if args.cmd == "emit-factors":
        ipca = read_ipca_csv(args.ipca_csv)
        factors = build_deflators(ipca, args.target)
        with args.out.open("w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["date", "factor_to_target"])
            for ym, f in sorted(factors.items()):
                w.writerow([ym, f"{f:.12f}"])
        return 0

    if args.cmd == "apply":
        ipca = read_ipca_csv(args.ipca_csv)
        factors = build_deflators(ipca, args.target)
        # Determine columns
        if args.columns:
            cols = [c.strip() for c in args.columns.split(",") if c.strip()]
        else:
            # attempt to auto-detect from header
            with args.inp.open("r", encoding="utf-8-sig", errors="replace") as fh:
                r = csv.reader(fh)
                headers = next(r)
            c1, c2 = _auto_income_columns(headers)
            cols = [c for c in (c1, c2) if c]
            if not cols:
                print("ERROR: could not auto-detect income columns (VD4019/VD4020); use --columns", file=sys.stderr)
                return 2
        apply_deflator_to_csv(
            args.inp,
            args.out,
            factors,
            cols,
            date_col=args.date_col,
            year_col=args.year_col,
            quarter_col=args.quarter_col,
            target_label=args.target.replace("-", "").lower(),
            min_wage=float(args.min_wage),
        )
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())

