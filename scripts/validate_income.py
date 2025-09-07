#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Iterable, Optional


def _to_float(x: str) -> Optional[float]:
    if x is None:
        return None
    s = str(x).strip().replace(",", ".")
    if s == "":
        return None
    try:
        return float(s)
    except Exception:
        return None


def _read_rows(path: Path) -> Iterable[dict]:
    with Path(path).open("r", encoding="utf-8-sig", errors="replace", newline="") as fh:
        r = csv.DictReader(fh)
        for row in r:
            yield row


def cmd_vd4020_components(args: argparse.Namespace) -> int:
    target = args.target
    comps = [c.strip() for c in args.components.split(",") if c.strip()]
    tol = float(args.tol)

    total = 0
    available = 0
    within = 0
    abs_errors: list[float] = []

    for row in _read_rows(args.inp):
        total += 1
        t = _to_float(row.get(target, ""))
        # require target and at least one component present
        vals = [_to_float(row.get(c, "")) for c in comps]
        present_vals = [v for v in vals if v is not None]
        if t is None or not present_vals:
            continue
        s = sum(present_vals)
        available += 1
        err = abs(s - t)
        abs_errors.append(err)
        if err <= tol:
            within += 1

        if args.limit and available >= args.limit:
            break

    out = {
        "rows_total": total,
        "rows_with_target_and_any_component": available,
        "matches_within_tol": within,
        "match_rate": (within / available) if available else None,
        "tol": tol,
        "mean_abs_error": (sum(abs_errors) / len(abs_errors)) if abs_errors else None,
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


def cmd_vd4020_vs_principal(args: argparse.Namespace) -> int:
    target = args.target
    principal = args.principal
    tol = float(args.tol)
    sec_money = args.secondary_money

    total = 0
    comparable = 0
    geq = 0
    equal_when_no_secondary = 0
    cnt_when_no_secondary = 0

    for row in _read_rows(args.inp):
        total += 1
        t = _to_float(row.get(target, ""))
        p = _to_float(row.get(principal, ""))
        if t is None or p is None:
            continue
        comparable += 1
        if t + tol >= p:
            geq += 1
        if sec_money:
            sm = _to_float(row.get(sec_money, ""))
            if sm is None:
                cnt_when_no_secondary += 1
                if abs((t - p)) <= tol:
                    equal_when_no_secondary += 1
        if args.limit and comparable >= args.limit:
            break

    out = {
        "rows_total": total,
        "rows_comparable": comparable,
        "vd4020_ge_principal_rate": (geq / comparable) if comparable else None,
        "rows_without_secondary_money": cnt_when_no_secondary,
        "equal_when_no_secondary_rate": (equal_when_no_secondary / cnt_when_no_secondary) if cnt_when_no_secondary else None,
        "tol": tol,
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Validate PNADC income consistency (e.g., VD4020 vs components)")
    sub = p.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("vd4020-components", help="Check VD4020 approx equals sum of component columns")
    p1.add_argument("--in", dest="inp", required=True, type=Path, help="Input CSV (e.g., base_labeled.csv)")
    p1.add_argument("--target", required=True, help="Target column (e.g., VD4020__rendim_efetivo_qq_trabalho)")
    p1.add_argument("--components", required=True, help="Comma-separated component columns to sum")
    p1.add_argument("--tol", default=1.0, help="Absolute tolerance for equality (BRL)")
    p1.add_argument("--limit", type=int, default=0, help="Optional row limit for speed")
    p1.set_defaults(func=cmd_vd4020_components)

    p2 = sub.add_parser("vd4020-vs-principal", help="Check VD4020 >= VD4017 and equality when no secondary income")
    p2.add_argument("--in", dest="inp", required=True, type=Path)
    p2.add_argument("--target", required=True)
    p2.add_argument("--principal", required=True, help="Principal job effective income column (e.g., VD4017__...)")
    p2.add_argument("--secondary-money", default=None, help="Secondary job effective money column (e.g., V405912__...)")
    p2.add_argument("--tol", default=1.0, help="Absolute tolerance (BRL)")
    p2.add_argument("--limit", type=int, default=0)
    p2.set_defaults(func=cmd_vd4020_vs_principal)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

