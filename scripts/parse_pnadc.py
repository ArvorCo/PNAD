#!/usr/bin/env python3
"""
Lightweight PNADC file helper.

Functions:
- sniff_delimiter: detect delimiter from a sample.
- summarize_file: stream rows to produce a summary JSON-friendly dict.
- write_sample_csv: write a small sample CSV to inspect data quickly.

CLI:
  python scripts/parse_pnadc.py <input> -o out/ --sample-rows 100
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Optional, Tuple


COMMON_DELIMS = [",", ";", "\t", "|"]


def sniff_delimiter(sample_text: str, candidates: list[str] = None) -> Tuple[str, bool]:
    """Return (delimiter, has_header) guessed from sample text.

    Falls back to semicolon/comma/tab/pipe frequency if csv.Sniffer fails.
    """
    candidates = candidates or COMMON_DELIMS
    sample = sample_text.strip().splitlines()
    sample = [ln for ln in sample if ln.strip()][:10]  # up to 10 non-empty lines
    joined = "\n".join(sample)

    # Try csv.Sniffer first
    try:
        dialect = csv.Sniffer().sniff(joined, delimiters="".join(candidates))
        has_header = csv.Sniffer().has_header(joined)
        return dialect.delimiter, bool(has_header)
    except Exception:
        pass

    # Fallback: pick highest consistent delimiter count on first line
    scores = {}
    if not sample:
        return ",", False
    first = sample[0]
    for d in candidates:
        scores[d] = first.count(d)
    delimiter = max(scores, key=scores.get)

    # Heuristic header detection: any non-numeric tokens suggests header
    tokens = [t.strip() for t in first.split(delimiter)]
    def is_num(x: str) -> bool:
        try:
            float(x.replace(",", "."))
            return True
        except Exception:
            return False
    non_numeric = any((t and not is_num(t)) for t in tokens)
    return delimiter, bool(non_numeric)


def summarize_file(path: Path, delimiter: Optional[str] = None, has_header: Optional[bool] = None) -> dict:
    """Stream through file to collect a minimal summary.

    Returns dict with: path, delimiter, has_header, rows, columns, size_bytes.
    """
    path = Path(path)
    size_bytes = path.stat().st_size
    # Prepare delimiter/header if not provided
    if delimiter is None or has_header is None:
        with path.open("r", encoding="utf-8-sig", errors="replace") as fh:
            head = fh.read(8192)
        delim, hdr = sniff_delimiter(head)
        delimiter = delimiter or delim
        has_header = has_header if has_header is not None else hdr

    rows = 0
    columns = None
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fh:
        reader = csv.reader(fh, delimiter=delimiter)
        for i, rec in enumerate(reader):
            if i == 0:
                columns = len(rec)
                if has_header:
                    # do not count header as data row
                    continue
            rows += 1

    return {
        "path": str(path),
        "delimiter": delimiter,
        "has_header": bool(has_header),
        "rows": rows,
        "columns": columns,
        "size_bytes": size_bytes,
    }


def write_sample_csv(path: Path, out_dir: Path, delimiter: Optional[str] = None, has_header: Optional[bool] = None, sample_rows: int = 100) -> Path:
    """Write a small CSV sample to out_dir/sample.csv and return its path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "sample.csv"

    # Determine delimiter/header if needed
    if delimiter is None or has_header is None:
        with Path(path).open("r", encoding="utf-8-sig", errors="replace") as fh:
            head = fh.read(8192)
        delim, hdr = sniff_delimiter(head)
        delimiter = delimiter or delim
        has_header = has_header if has_header is not None else hdr

    # Stream and write sample
    written = 0
    header_written = False
    with Path(path).open("r", encoding="utf-8-sig", errors="replace", newline="") as rf, out_path.open("w", encoding="utf-8", newline="") as wf:
        r = csv.reader(rf, delimiter=delimiter)
        w = csv.writer(wf)
        for i, rec in enumerate(r):
            if i == 0 and has_header:
                w.writerow(rec)
                header_written = True
                continue
            if not header_written and i == 0:
                # Synthesize headers if none
                w.writerow([f"col_{j+1}" for j in range(len(rec))])
                header_written = True
            w.writerow(rec)
            written += 1
            if written >= sample_rows:
                break
    return out_path


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="PNADC helper: summarize and sample data files")
    p.add_argument("input", type=Path, help="Path to PNADC data file (txt/csv)")
    p.add_argument("-o", "--out", type=Path, default=Path("out"), help="Output directory (default: out/)")
    p.add_argument("--sample-rows", type=int, default=100, help="Number of rows to include in sample.csv")
    args = p.parse_args(argv)

    summary = summarize_file(args.input)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    write_sample_csv(args.input, args.out, sample_rows=args.sample_rows)
    print(json.dumps({"ok": True, "out": str(args.out)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

