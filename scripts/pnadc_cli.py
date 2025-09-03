#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

# Reuse delimiter/header detection from existing helper
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from parse_pnadc import sniff_delimiter  # type: ignore
from layout_sas import parse_layout, fields_index, extract_line  # type: ignore
import unicodedata
import re


# ---------- Safe filter expression (row-aware) ----------
import ast


class RowExpr(ast.NodeTransformer):
    """Transform a limited Python expression into lookups against a row dict.

    Allowed: Names (become row.get('name')), literals, comparisons, bool ops,
    unary ops, arithmetic ops (+-*/% //), and membership 'in' with literals.
    """

    ALLOWED_NODES = (
        ast.Expression,
        ast.BoolOp,
        ast.BinOp,
        ast.UnaryOp,
        ast.Compare,
        ast.Name,
        ast.Load,
        ast.Constant,
        ast.List,
        ast.Tuple,
        ast.Dict,
        ast.Set,
        ast.Call,
        # operator tokens treated as nodes in AST
        ast.And,
        ast.Or,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.Mod,
        ast.FloorDiv,
        ast.UAdd,
        ast.USub,
        ast.Eq,
        ast.NotEq,
        ast.Lt,
        ast.LtE,
        ast.Gt,
        ast.GtE,
        ast.In,
        ast.NotIn,
        ast.Is,
        ast.IsNot,
    )

    ALLOWED_OPS = (
        ast.And,
        ast.Or,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.Mod,
        ast.FloorDiv,
        ast.USub,
        ast.UAdd,
    )

    ALLOWED_CMPS = (
        ast.Eq,
        ast.NotEq,
        ast.Lt,
        ast.LtE,
        ast.Gt,
        ast.GtE,
        ast.In,
        ast.NotIn,
        ast.Is,
        ast.IsNot,
    )

    def __init__(self, colnames: Sequence[str]):
        self.colnames = set(colnames)
        self.allowed_func_names = {"int", "float", "str", "len"}

    def visit_Name(self, node: ast.Name):
        # Keep allowed builtins (int/float/str/len) as names
        if node.id in self.allowed_func_names:
            return node
        # Replace other names with row.get('name')
        return ast.Call(
            func=ast.Attribute(value=ast.Name(id="row", ctx=ast.Load()), attr="get", ctx=ast.Load()),
            args=[ast.Constant(node.id)],
            keywords=[],
        )

    def generic_visit(self, node):
        if not isinstance(node, self.ALLOWED_NODES):
            raise ValueError(f"Disallowed node in expression: {type(node).__name__}")
        return super().generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp):
        if not isinstance(node.op, self.ALLOWED_OPS):
            raise ValueError("Operator not allowed")
        return self.generic_visit(node)

    def visit_UnaryOp(self, node: ast.UnaryOp):
        if not isinstance(node.op, self.ALLOWED_OPS):
            raise ValueError("Operator not allowed")
        return self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare):
        for op in node.ops:
            if not isinstance(op, self.ALLOWED_CMPS):
                raise ValueError("Comparator not allowed")
        return self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        # Allow calls to a small set of safe builtins only
        if not isinstance(node.func, ast.Name) or node.func.id not in self.allowed_func_names:
            raise ValueError("Only int/float/str/len calls are allowed")
        return self.generic_visit(node)


def compile_row_expr(expr: str, columns: Sequence[str]):
    tree = ast.parse(expr, mode="eval")
    transformer = RowExpr(columns)
    tree = transformer.visit(tree)
    ast.fix_missing_locations(tree)
    code = compile(tree, filename="<row-expr>", mode="eval")
    return code


def eval_row_expr(code, row: Dict[str, str]) -> bool:
    # Only expose row and builtins needed for casting
    env = {"row": row, "__builtins__": {"int": int, "float": float, "len": len, "str": str}}
    return bool(eval(code, env, {}))


# ---------- CSV streaming helpers ----------


def open_reader(path: Path, delimiter: Optional[str] = None, has_header: Optional[bool] = None):
    path = Path(path)
    with path.open("r", encoding="utf-8-sig", errors="replace") as fh:
        head = fh.read(8192)
    delim, hdr = sniff_delimiter(head)
    delimiter = delimiter or delim
    has_header = hdr if has_header is None else has_header

    fh = path.open("r", encoding="utf-8-sig", errors="replace", newline="")
    if has_header:
        reader = csv.DictReader(fh, delimiter=delimiter)
        return fh, reader, reader.fieldnames or []
    else:
        # derive number of columns from first line
        fh.seek(0)
        r0 = csv.reader(fh, delimiter=delimiter)
        first = next(r0)
        ncols = len(first)
        fh.seek(0)
        fieldnames = [f"col_{i+1}" for i in range(ncols)]
        reader = csv.DictReader(fh, delimiter=delimiter, fieldnames=fieldnames)
        return fh, reader, fieldnames


# ---------- Commands ----------


def cmd_inspect(args: argparse.Namespace) -> int:
    path = Path(args.input)
    with path.open("r", encoding="utf-8-sig", errors="replace") as fh:
        head = fh.read(8192)
    delim, hdr = sniff_delimiter(head)
    fh, reader, cols = open_reader(path, delim, hdr)
    with fh:
        n = 0
        for _ in reader:
            n += 1
            if args.limit and n >= args.limit:
                break
    out = {
        "path": str(path),
        "delimiter": delim,
        "has_header": bool(hdr),
        "columns": cols,
        "preview_rows_counted": n,
        "size_bytes": path.stat().st_size,
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


def iter_rows(path: Path, delimiter=None, has_header=None) -> Tuple[Iterable[Dict[str, str]], List[str]]:
    fh, reader, cols = open_reader(path, delimiter, has_header)
    def gen():
        nonlocal fh
        with fh:
            for row in reader:
                yield row
    return gen(), cols


def cmd_head(args: argparse.Namespace) -> int:
    rows, cols = iter_rows(Path(args.input))
    w = csv.writer(sys.stdout)
    if args.header:
        w.writerow(cols)
    for i, r in enumerate(rows):
        if i >= args.n:
            break
        w.writerow([r.get(c, "") for c in cols])
    return 0


def cmd_select(args: argparse.Namespace) -> int:
    cols_req = [c.strip() for c in args.columns.split(",")]
    rows, cols = iter_rows(Path(args.input))
    missing = [c for c in cols_req if c not in cols]
    if missing:
        print(f"ERROR: missing columns: {missing}", file=sys.stderr)
        return 2
    w = csv.writer(sys.stdout)
    if args.header:
        w.writerow(cols_req)
    for r in rows:
        w.writerow([r.get(c, "") for c in cols_req])
    return 0


def cmd_filter(args: argparse.Namespace) -> int:
    rows, cols = iter_rows(Path(args.input))
    code = compile_row_expr(args.where, cols)
    out_cols = cols if args.columns is None else [c.strip() for c in args.columns.split(",")]
    if args.columns is not None:
        missing = [c for c in out_cols if c not in cols]
        if missing:
            print(f"ERROR: missing columns: {missing}", file=sys.stderr)
            return 2
    w = csv.writer(sys.stdout)
    if args.header:
        w.writerow(out_cols)
    cnt = 0
    for r in rows:
        try:
            if eval_row_expr(code, r):
                w.writerow([r.get(c, "") for c in out_cols])
                cnt += 1
        except Exception as e:
            if args.strict:
                raise
            # Skip rows that error during evaluation (e.g., bad types)
            continue
    return 0


def cmd_sample(args: argparse.Namespace) -> int:
    # Reservoir sampling (Vitter's Algorithm R)
    import random

    rows, cols = iter_rows(Path(args.input))
    k = args.n
    reservoir: List[Dict[str, str]] = []
    for i, r in enumerate(rows):
        if i < k:
            reservoir.append(r)
        else:
            j = random.randint(0, i)
            if j < k:
                reservoir[j] = r
    w = csv.writer(sys.stdout)
    if args.header:
        w.writerow(cols)
    for r in reservoir:
        w.writerow([r.get(c, "") for c in cols])
    return 0


@dataclass
class AggSpec:
    name: str  # output column name
    func: str  # one of: count,sum,mean,min,max
    column: Optional[str]  # None for count


def parse_agg(spec: str) -> AggSpec:
    # Format examples: count(), sum(renda), mean(idade) -> out names default to func_column
    spec = spec.strip()
    if not spec.endswith(")") or "(" not in spec:
        raise ValueError(f"Invalid agg spec: {spec}")
    func, inner = spec.split("(", 1)
    func = func.strip().lower()
    col = inner[:-1].strip()  # drop )
    column = col if col else None
    name = f"{func}{'_' + column if column else ''}"
    if func not in {"count", "sum", "mean", "min", "max"}:
        raise ValueError(f"Unsupported agg func: {func}")
    return AggSpec(name=name, func=func, column=column)


def cmd_agg(args: argparse.Namespace) -> int:
    rows, cols = iter_rows(Path(args.input))
    keys = [c.strip() for c in args.by.split(",")]
    for k in keys:
        if k not in cols:
            print(f"ERROR: missing group key: {k}", file=sys.stderr)
            return 2
    aggs = [parse_agg(s) for s in args.agg]
    for a in aggs:
        if a.column and a.column not in cols:
            print(f"ERROR: missing agg column: {a.column}", file=sys.stderr)
            return 2

    # Accumulators: dict[key_tuple] -> dict of agg state
    state: Dict[Tuple[str, ...], Dict[str, object]] = {}

    def to_float(x: str) -> Optional[float]:
        if x is None or x == "":
            return None
        try:
            return float(str(x).replace(",", "."))
        except Exception:
            return None

    for r in rows:
        gk = tuple(r.get(k, "") for k in keys)
        st = state.get(gk)
        if st is None:
            st = {"count": 0}
            for a in aggs:
                if a.func in {"sum", "mean", "min", "max"}:
                    st[f"sum_{a.name}"] = 0.0
                    st[f"cnt_{a.name}"] = 0
                    st[f"min_{a.name}"] = math.inf
                    st[f"max_{a.name}"] = -math.inf
            state[gk] = st
        st["count"] = st.get("count", 0) + 1
        for a in aggs:
            if a.func == "count":
                # overall count already tracked
                continue
            val = to_float(r.get(a.column or "", ""))
            if val is None:
                continue
            st[f"sum_{a.name}"] += val
            st[f"cnt_{a.name}"] += 1
            if val < st[f"min_{a.name}"]:
                st[f"min_{a.name}"] = val
            if val > st[f"max_{a.name}"]:
                st[f"max_{a.name}"] = val

    # Emit results
    out_cols = list(keys)
    for a in aggs:
        if a.func == "count":
            out_cols.append("count")
        elif a.func == "sum":
            out_cols.append(a.name)
        elif a.func == "mean":
            out_cols.append(a.name)
        elif a.func == "min":
            out_cols.append(a.name)
        elif a.func == "max":
            out_cols.append(a.name)

    w = csv.writer(sys.stdout)
    if args.header:
        w.writerow(out_cols)
    for gk, st in state.items():
        row = list(gk)
        for a in aggs:
            if a.func == "count":
                row.append(st.get("count", 0))
            elif a.func == "sum":
                row.append(round(st.get(f"sum_{a.name}", 0.0), 6))
            elif a.func == "mean":
                s = st.get(f"sum_{a.name}", 0.0)
                c = st.get(f"cnt_{a.name}", 0)
                row.append(round((s / c) if c else 0.0, 6))
            elif a.func == "min":
                m = st.get(f"min_{a.name}", math.inf)
                row.append(None if m is math.inf else round(m, 6))
            elif a.func == "max":
                m = st.get(f"max_{a.name}", -math.inf)
                row.append(None if m is -math.inf else round(m, 6))
        w.writerow(row)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="pnadc", description="Stream PNADC files and query them via CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("inspect", help="Detect delimiter, header and preview columns")
    pi.add_argument("input", type=Path)
    pi.add_argument("--limit", type=int, default=10000, help="Max rows to scan for preview count")
    pi.set_defaults(func=cmd_inspect)

    ph = sub.add_parser("head", help="Print first N rows to CSV")
    ph.add_argument("input", type=Path)
    ph.add_argument("-n", type=int, default=10)
    ph.add_argument("--header", action="store_true")
    ph.set_defaults(func=cmd_head)

    ps = sub.add_parser("select", help="Select columns")
    ps.add_argument("input", type=Path)
    ps.add_argument("columns", help="Comma-separated column names")
    ps.add_argument("--header", action="store_true")
    ps.set_defaults(func=cmd_select)

    pf = sub.add_parser("filter", help="Filter rows by expression (e.g., renda>1000 and sexo=='M')")
    pf.add_argument("input", type=Path)
    pf.add_argument("--where", required=True)
    pf.add_argument("--columns", help="Comma-separated columns to output (default: all)")
    pf.add_argument("--header", action="store_true")
    pf.add_argument("--strict", action="store_true", help="Error on bad rows (default: skip)")
    pf.set_defaults(func=cmd_filter)

    psm = sub.add_parser("sample", help="Reservoir sample N rows")
    psm.add_argument("input", type=Path)
    psm.add_argument("-n", type=int, default=1000)
    psm.add_argument("--header", action="store_true")
    psm.set_defaults(func=cmd_sample)

    pagg = sub.add_parser("agg", help="Group and aggregate")
    pagg.add_argument("input", type=Path)
    pagg.add_argument("--by", required=True, help="Comma-separated group keys")
    pagg.add_argument("--agg", required=True, nargs="+", help="Aggregations, e.g., count() sum(renda) mean(idade)")
    pagg.add_argument("--header", action="store_true")
    pagg.set_defaults(func=cmd_agg)

    # Layout utilities (SAS INPUT for fixed-width files)
    pl = sub.add_parser("layout", help="Parse SAS layout and print CSV of fields")
    pl.add_argument("layout", type=Path, help="Path to input_*.sas layout file")
    pl.set_defaults(func=lambda args: _cmd_layout(args))

    pfx = sub.add_parser(
        "fwf-extract",
        help="Extract selected fields from a fixed-width file using a SAS layout",
    )
    pfx.add_argument("layout", type=Path, help="Path to input_*.sas layout file")
    pfx.add_argument("input", type=Path, help="Fixed-width data file path")
    pfx.add_argument(
        "--keep",
        required=False,
        help="Comma-separated field names to extract (default: UF,Capital,V4050,V40501,V405011,V405012,V40502,V405021,V405022,V40503,V405031,V4051,V40511,V405111,V405112,V40512,V405121,V405122,V4056,V4056C,V4057,V4058,V40581,V405811,V405812,V40582,V405821,V405822,V40583,V405831,V40584,V4059,V40591,V405911,V405912,V40592)",
    )
    pfx.add_argument("--header", action="store_true")
    pfx.add_argument(
        "--name-style",
        choices=["name", "label", "both"],
        default="both",
        help="How to name columns: SAS name, label slug, or 'name__label' (default)",
    )
    pfx.set_defaults(func=cmd_fwf_extract)

    pschema = sub.add_parser("fwf-schema", help="Emit schema CSV: name,label,slug,start,width,kind")
    pschema.add_argument("layout", type=Path)
    pschema.set_defaults(func=cmd_fwf_schema)

    pdict = sub.add_parser(
        "dict-extract",
        help="Extract code tables (UF, Capital, RM_RIDE) from Excel dictionary into CSVs",
    )
    pdict.add_argument("excel", type=Path, help="Path to dicionario .xls")
    pdict.add_argument("--out", type=Path, default=Path("data"))
    pdict.add_argument("--vars", default="UF,Capital,RM_RIDE", help="Comma-separated variable names to extract")
    pdict.set_defaults(func=cmd_dict_extract)

    pcodes = sub.add_parser("emit-codes", help="Emit static code tables (V2005,V2010,V3001,V3003A,V3009A)")
    pcodes.add_argument("--out", type=Path, default=Path("data"))
    pcodes.set_defaults(func=cmd_emit_codes)

    pjoin = sub.add_parser("join-codes", help="Join code tables to extracted CSV to add *_label columns")
    pjoin.add_argument("input", type=Path, help="CSV produced by fwf-extract")
    pjoin.add_argument("--codes-dir", type=Path, default=Path("data"), help="Directory with *_codes.csv from dict-extract/emit-codes")
    pjoin.add_argument("--header", action="store_true", help="Ensure header is written (if input has none)")
    pjoin.set_defaults(func=cmd_join_codes)

    phh = sub.add_parser(
        "household-agg",
        help="Aggregate persons to household level using dom_id and sum of income columns",
    )
    phh.add_argument("input", type=Path, help="CSV from fwf-extract containing dom_id and income cols")
    phh.add_argument(
        "--income-cols",
        default="V405012,V405022,V405112,V405122",
        help="Comma-separated numeric columns to sum for household income",
    )
    phh.add_argument(
        "--keep-cols",
        default="Ano,Trimestre,UF,Capital,RM_RIDE",
        help="Comma-separated grouping columns to carry (first non-empty per household)",
    )
    phh.set_defaults(func=cmd_household_agg)

    return p


def main(argv: Optional[List[str]] = None) -> int:
    p = build_parser()
    args = p.parse_args(argv)
    return int(args.func(args) or 0)


# ---------------- layout helpers -----------------


def _cmd_layout(args: argparse.Namespace) -> int:
    fields = parse_layout(args.layout)
    import csv, sys

    w = csv.writer(sys.stdout)
    w.writerow(["name", "start", "width", "kind"])
    for f in fields:
        w.writerow([f.name, f.start + 1, f.width, f.kind])
    return 0


DEFAULT_KEEP = (
    "Ano,Trimestre,UF,Capital,RM_RIDE,UPA,V1008,V1014,"
    "V2007,V2005,V2009,V2010,V3001,V3003A,V3009A,"
    "V2008,V20081,V20082,VD2003,"
    "VD4011,VD4014,VD4015,VD4016,VD4017,VD4018,VD4019,VD4020,"
    "V4010,VD4009,VD4008,VD4007,VD4005,VD4004A,VD4003,"
    "VD3005,VD3004,VD2002,VD2004,VD2006,"
    "V4050,V40501,V405011,V405012,"
    "V40502,V405021,V405022,"
    "V40503,V405031,"
    "V4051,V40511,V405111,V405112,"
    "V40512,V405121,V405122,"
    "V4056C,V4057,V4062C,VD4023,VD4030,VD4031,VD4032,VD4033,VD4034,VD4035,VD4036,VD4037,"
    "V4058,V40581,V405811,V405812,"
    "V40582,V405821,V405822,"
    "V40583,V405831,V40584,"
    "V4059,V40591,V405911,V405912,"
    "V40592"
)


def _compose_birthdate(day: str, month: str, year: str) -> str:
    d = (day or "").strip()
    m = (month or "").strip()
    y = (year or "").strip()
    if not (y and m and d):
        return ""
    # normalize
    y = y.zfill(4)
    m = m.zfill(2)
    d = d.zfill(2)
    try:
        # rudimentary validation
        mi = int(m)
        di = int(d)
        yi = int(y)
        if yi < 1900 or mi < 1 or mi > 12 or di < 1 or di > 31:
            return f"{y}-{m}-{d}"
    except Exception:
        return f"{y}-{m}-{d}"
    return f"{y}-{m}-{d}"


def cmd_fwf_extract(args: argparse.Namespace) -> int:
    fields = parse_layout(args.layout)
    idx = fields_index(fields)
    keep = [s.strip() for s in (args.keep or DEFAULT_KEEP).split(",") if s.strip()]
    missing = [k for k in keep if k not in idx]
    if missing:
        print(f"WARN: missing fields in layout: {missing}", file=sys.stderr)
    # Compose selection honoring priority order, then ascending names for the rest
    selected_all = [idx[k] for k in keep if k in idx]
    priority = [
        "Ano","Trimestre","UF","Capital","RM_RIDE","UPA","V1008","V1014",
        "V2007","V2005","V2009","V2010","V3001","V3003A","V3009A",
        "V2008","V20081","V20082","VD2003",
    ]
    priority_set = set(priority)
    pri = [f for f in selected_all if f.name in priority]
    rest = [f for f in selected_all if f.name not in priority_set]
    rest_sorted = sorted(rest, key=lambda f: f.name)
    selected = pri + rest_sorted
    # Stream lines and write CSV
    import csv

    w = csv.writer(sys.stdout)
    # Determine derived birthdate availability
    has_birth = all(k in idx for k in ("V2008", "V20081", "V20082"))
    # Determine household id availability
    has_dom = all(k in idx for k in ("Ano", "Trimestre", "UPA", "V1008"))
    # Write header
    if args.header:
        if args.name_style == "name":
            hdr = [f.name for f in selected]
        elif args.name_style == "label":
            hdr = [f.slug or f.name for f in selected]
        else:  # both
            hdr = [f"{f.name}__{(f.slug or f.name)}" for f in selected]
        if has_birth:
            hdr.append("data_nascimento")
        if has_dom:
            hdr.append("dom_id")
        w.writerow(hdr)
    input_path = _resolve_data_path(args.input)
    with input_path.open("r", encoding="latin-1", errors="replace") as fh:
        for line in fh:
            # Year filter: only >= 2015 if Ano exists
            if "Ano" in idx:
                year = extract_line(line, [idx["Ano"]])[0].strip()
                try:
                    if int(year) < 2015:
                        continue
                except Exception:
                    pass
            row = extract_line(line, selected)
            if has_birth:
                d = extract_line(line, [idx["V2008"]])[0]
                m = extract_line(line, [idx["V20081"]])[0]
                y = extract_line(line, [idx["V20082"]])[0]
                row.append(_compose_birthdate(d, m, y))
            if has_dom:
                ano = extract_line(line, [idx["Ano"]])[0].strip()
                tri = extract_line(line, [idx["Trimestre"]])[0].strip()
                upa = extract_line(line, [idx["UPA"]])[0].strip()
                v1008 = extract_line(line, [idx["V1008"]])[0].strip()
                dom_id = f"{ano}{tri}-{upa}-{v1008}"
                row.append(dom_id)
            w.writerow(row)
    return 0


def _write_code_csv(out_dir: Path, name: str, mapping: dict):
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{name}_codes.csv"
    import csv

    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["code", "label"])
        for k, v in mapping.items():
            w.writerow([k, v])
    return path


def cmd_emit_codes(args: argparse.Namespace) -> int:
    # V2005 - parentesco com responsável
    v2005 = {
        "01": "Pessoa responsável pelo domicílio",
        "02": "Cônjuge ou companheiro(a) de sexo diferente",
        "03": "Cônjuge ou companheiro(a) do mesmo sexo",
        "04": "Filho(a) do responsável e do cônjuge",
        "05": "Filho(a) somente do responsável",
        "06": "Enteado(a)",
        "07": "Genro ou nora",
        "08": "Pai, mãe, padrasto ou madrasta",
        "09": "Sogro(a)",
        "10": "Neto(a)",
        "11": "Bisneto(a)",
        "12": "Irmão ou irmã",
        "13": "Avô ou avó",
        "14": "Outro parente",
        "15": "Agregado(a) - Não parente que não compartilha despesas",
        "16": "Convivente - Não parente que compartilha despesas",
        "17": "Pensionista",
        "18": "Empregado(a) doméstico(a)",
        "19": "Parente do(a) empregado(a) doméstico(a)",
    }
    # include non-zero-padded keys
    v2005.update({k.lstrip("0"): v for k, v in list(v2005.items())})

    # V2010 - cor/raça
    v2010 = {
        "1": "Branca",
        "2": "Preta",
        "3": "Amarela",
        "4": "Parda",
        "5": "Indígena",
        "9": "Ignorado",
        "09": "Ignorado",
    }

    # V3001 - Frequenta escola
    v3001 = {"1": "Sim", "2": "Não", "01": "Sim", "02": "Não"}

    # V3003A - Curso que frequenta
    v3003a = {
        "01": "Creche",
        "02": "Pré-escola",
        "03": "Alfabetização de jovens e adultos",
        "04": "Regular do ensino fundamental",
        "05": "EJA do ensino fundamental",
        "06": "Regular do ensino médio",
        "07": "EJA do ensino médio",
        "08": "Superior - graduação",
        "09": "Especialização de nível superior",
        "10": "Mestrado",
        "11": "Doutorado",
    }
    v3003a.update({k.lstrip("0"): v for k, v in list(v3003a.items())})

    # V3009A - Curso mais elevado concluído
    v3009a = {
        "01": "Creche",
        "02": "Pré-escola",
        "03": "Classe de alfabetização - CA",
        "04": "Alfabetização de jovens e adultos",
        "05": "Antigo primário (elementar)",
        "06": "Antigo ginásio (médio 1º ciclo)",
        "07": "Regular do ensino fundamental ou do 1º grau",
        "08": "EJA ou supletivo do 1º grau",
        "09": "Antigo científico, clássico, etc. (médio 2º ciclo)",
        "10": "Regular do ensino médio ou do 2º grau",
        "11": "EJA ou supletivo do 2º grau",
        "12": "Superior - graduação",
        "13": "Especialização de nível superior",
        "14": "Mestrado",
        "15": "Doutorado",
    }
    v3009a.update({k.lstrip("0"): v for k, v in list(v3009a.items())})

    # V2007 - sexo
    v2007 = {"1": "Homem", "2": "Mulher"}

    # VD4011 - Grandes grupos ocupacionais
    vd4011 = {
        "01": "Diretores e gerentes",
        "02": "Profissionais das ciências e intelectuais",
        "03": "Técnicos e profissionais de nível médio",
        "04": "Trabalhadores de apoio administrativo",
        "05": "Trabalhadores dos serviços, vendedores dos comércios e mercados",
        "06": "Trabalhadores qualificados da agropecuária, florestais, da caça e da pesca",
        "07": "Trabalhadores qualificados, operários e artesãos da construção, das artes mecânicas e outros ofícios",
        "08": "Operadores de instalações e máquinas e montadores",
        "09": "Ocupações elementares",
        "10": "Membros das forças armadas, policiais e bombeiros militares",
        "11": "Ocupações maldefinidas",
    }
    vd4011.update({k.lstrip("0"): v for k, v in list(vd4011.items())})

    # V4010 - Seção de atividade agregada
    v4010 = {
        "01": "Agricultura, pecuária, produção florestal, pesca e aquicultura",
        "02": "Indústria geral",
        "03": "Construção",
        "04": "Comércio, reparação de veículos automotores e motocicletas",
        "05": "Transporte, armazenagem e correio",
        "06": "Alojamento e alimentação",
        "07": "Informação, comunicação e atividades financeiras, imobiliárias, profissionais e administrativas",
        "08": "Administração pública, defesa e seguridade social",
        "09": "Educação, saúde humana e serviços sociais",
        "10": "Outros Serviços",
        "11": "Serviços domésticos",
        "12": "Atividades mal definidas",
    }
    v4010.update({k.lstrip("0"): v for k, v in list(v4010.items())})

    # VD4009 - Posição na ocupação (detalhe)
    vd4009 = {
        "01": "Empregado no setor privado com carteira de trabalho assinada",
        "02": "Empregado no setor privado sem carteira de trabalho assinada",
        "03": "Trabalhador doméstico com carteira de trabalho assinada",
        "04": "Trabalhador doméstico sem carteira de trabalho assinada",
        "05": "Empregado no setor público com carteira de trabalho assinada",
        "06": "Empregado no setor público sem carteira de trabalho assinada",
        "07": "Militar e servidor estatutário",
        "08": "Empregador",
        "09": "Conta-própria",
        "10": "Trabalhador familiar auxiliar",
    }
    vd4009.update({k.lstrip("0"): v for k, v in list(vd4009.items())})

    # VD4008 - Posição na ocupação (agregada)
    vd4008 = {
        "1": "Empregado no setor privado",
        "2": "Trabalhador doméstico",
        "3": "Empregado no setor público (inclusive servidor estatutário e militar)",
        "4": "Empregador",
        "5": "Conta-própria",
        "6": "Trabalhador familiar auxiliar",
        "01": "Empregado no setor privado",
        "02": "Trabalhador doméstico",
        "03": "Empregado no setor público (inclusive servidor estatutário e militar)",
        "04": "Empregador",
        "05": "Conta-própria",
        "06": "Trabalhador familiar auxiliar",
    }

    # VD4007 - Posição na ocupação (agregada 4 categorias)
    vd4007 = {
        "1": "Empregado (inclusive trabalhador doméstico)",
        "2": "Empregador",
        "3": "Conta própria",
        "4": "Trabalhador familiar auxiliar",
        "01": "Empregado (inclusive trabalhador doméstico)",
        "02": "Empregador",
        "03": "Conta própria",
        "04": "Trabalhador familiar auxiliar",
    }

    # VD4005 - Pessoas desalentadas
    vd4005 = {"1": "Pessoas desalentadas", "01": "Pessoas desalentadas"}

    # VD4004A - Pessoas subocupadas
    vd4004a = {"1": "Pessoas subocupadas", "01": "Pessoas subocupadas"}

    # VD4003 - Força de trabalho potencial
    vd4003 = {
        "1": "Pessoas fora da força de trabalho e na força de trabalho potencial",
        "2": "Pessoas fora da força de trabalho e fora da força de trabalho potencial",
        "01": "Pessoas fora da força de trabalho e na força de trabalho potencial",
        "02": "Pessoas fora da força de trabalho e fora da força de trabalho potencial",
    }

    # VD3005 - anos de estudo
    vd3005 = {
        "00": "Sem instrução e menos de 1 ano de estudo",
        **{f"{i:02d}": f"{i} anos de estudo" for i in range(1, 16)},
        "16": "16 anos ou mais de estudo",
    }
    vd3005.update({k.lstrip("0"): v for k, v in list(vd3005.items())})

    # VD3004 - nível de instrução
    vd3004 = {
        "1": "Sem instrução e menos de 1 ano de estudo",
        "2": "Fundamental incompleto ou equivalente",
        "3": "Fundamental completo ou equivalente",
        "4": "Médio incompleto ou equivalente",
        "5": "Médio completo ou equivalente",
        "6": "Superior incompleto ou equivalente",
        "7": "Superior completo",
        "01": "Sem instrução e menos de 1 ano de estudo",
        "02": "Fundamental incompleto ou equivalente",
        "03": "Fundamental completo ou equivalente",
        "04": "Médio incompleto ou equivalente",
        "05": "Médio completo ou equivalente",
        "06": "Superior incompleto ou equivalente",
        "07": "Superior completo",
    }

    # VD2002 - parentesco (agregado)
    vd2002 = {
        "01": "Pessoa responsável",
        "02": "Cônjuge ou companheiro(a)",
        "03": "Filho(a)",
        "04": "Enteado(a)",
        "05": "Genro ou nora",
        "06": "Pai, mãe, padrasto ou madrasta",
        "07": "Sogro(a)",
        "08": "Neto(a)",
        "09": "Bisneto(a)",
        "10": "Irmão ou irmã",
        "11": "Avô ou avó",
        "12": "Outro parente",
        "13": "Agregado(a)",
        "14": "Convivente",
        "15": "Pensionista",
        "16": "Empregado(a) doméstico(a)",
        "17": "Parente do(a) empregado(a) doméstico(a)",
    }
    vd2002.update({k.lstrip("0"): v for k, v in list(vd2002.items())})

    # VD2004 - tipo de arranjo
    vd2004 = {
        "1": "Unipessoal",
        "2": "Nuclear",
        "3": "Estendida",
        "4": "Composta",
        "01": "Unipessoal",
        "02": "Nuclear",
        "03": "Estendida",
        "04": "Composta",
    }

    # VD2006 - grupos etários
    vd2006 = {
        "01": "0 a 4 anos",
        "02": "5 a 9 anos",
        "03": "10 a 13 anos",
        "04": "14 a 19 anos",
        "05": "20 a 24 anos",
        "06": "25 a 29 anos",
        "07": "30 a 34 anos",
        "08": "35 a 39 anos",
        "09": "40 a 44 anos",
        "10": "45 a 49 anos",
        "11": "50 a 54 anos",
        "12": "55 a 59 anos",
        "13": "60 a 64 anos",
        "14": "65 a 69 anos",
        "15": "70 a 74 anos",
        "16": "75 a 79 anos",
        "17": "80 anos ou mais",
    }
    vd2006.update({k.lstrip("0"): v for k, v in list(vd2006.items())})

    # UF codes (2-digit strings)
    uf = {
        "11": "Rondônia",
        "12": "Acre",
        "13": "Amazonas",
        "14": "Roraima",
        "15": "Pará",
        "16": "Amapá",
        "17": "Tocantins",
        "21": "Maranhão",
        "22": "Piauí",
        "23": "Ceará",
        "24": "Rio Grande do Norte",
        "25": "Paraíba",
        "26": "Pernambuco",
        "27": "Alagoas",
        "28": "Sergipe",
        "29": "Bahia",
        "31": "Minas Gerais",
        "32": "Espírito Santo",
        "33": "Rio de Janeiro",
        "35": "São Paulo",
        "41": "Paraná",
        "42": "Santa Catarina",
        "43": "Rio Grande do Sul",
        "50": "Mato Grosso do Sul",
        "51": "Mato Grosso",
        "52": "Goiás",
        "53": "Distrito Federal",
    }

    # Capital codes (2-digit strings)
    capital = {
        "11": "Município de Porto Velho (RO)",
        "12": "Município de Rio Branco (AC)",
        "13": "Município de Manaus (AM)",
        "14": "Município de Boa Vista (RR)",
        "15": "Município de Belém (PA)",
        "16": "Município de Macapá (AP)",
        "17": "Município de Palmas (TO)",
        "21": "Município de São Luís (MA)",
        "22": "Município de Teresina (PI)",
        "23": "Município de Fortaleza (CE)",
        "24": "Município de Natal (RN)",
        "25": "Município de João Pessoa (PB)",
        "26": "Município de Recife (PE)",
        "27": "Município de Maceió (AL)",
        "28": "Município de Aracaju (SE)",
        "29": "Município de Salvador (BA)",
        "31": "Município de Belo Horizonte (MG)",
        "32": "Município de Vitória (ES)",
        "33": "Município de Rio de Janeiro (RJ)",
        "35": "Município de São Paulo (SP)",
        "41": "Município de Curitiba (PR)",
        "42": "Município de Florianópolis (SC)",
        "43": "Município de Porto Alegre (RS)",
        "50": "Município de Campo Grande (MS)",
        "51": "Município de Cuiabá (MT)",
        "52": "Município de Goiânia (GO)",
        "53": "Município de Brasília (DF)",
    }

    # RM_RIDE codes (2-digit strings)
    rm_ride = {
        "13": "Região Metropolitana de Manaus (AM)",
        "15": "Região Metropolitana de Belém (PA)",
        "16": "Região Metropolitana de Macapá (AP)",
        "21": "Região Metropolitana de Grande São Luís (MA)",
        "22": "Região Administrativa Integrada de Desenvolvimento da Grande Teresina (PI)",
        "23": "Região Metropolitana de Fortaleza (CE)",
        "24": "Região Metropolitana de Natal (RN)",
        "25": "Região Metropolitana de João Pessoa (PB)",
        "26": "Região Metropolitana de Recife (PE)",
        "27": "Região Metropolitana de Maceió (AL)",
        "28": "Região Metropolitana de Aracaju (SE)",
        "29": "Região Metropolitana de Salvador (BA)",
        "31": "Região Metropolitana de Belo Horizonte (MG)",
        "32": "Região Metropolitana de Grande Vitória (ES)",
        "33": "Região Metropolitana de Rio de Janeiro (RJ)",
        "35": "Região Metropolitana de São Paulo (SP)",
        "41": "Região Metropolitana de Curitiba (PR)",
        "42": "Região Metropolitana de Florianópolis (SC)",
        "43": "Região Metropolitana de Porto Alegre (RS)",
        "51": "Região Metropolitana de Vale do Rio Cuiabá (MT)",
        "52": "Região Metropolitana de Goiânia (GO)",
    }

    out = args.out
    print(json.dumps({"out": str(out)}, ensure_ascii=False))
    _write_code_csv(out, "v2005", v2005)
    _write_code_csv(out, "v2007", v2007)
    _write_code_csv(out, "v2010", v2010)
    _write_code_csv(out, "v3001", v3001)
    _write_code_csv(out, "v3003a", v3003a)
    _write_code_csv(out, "v3009a", v3009a)
    # VD4036/VD4037 - hours categories
    v403x_hours = {
        "1": "Até 14 horas",
        "2": "15 a 39 horas",
        "3": "40 a 44 horas",
        "4": "45 a 48 horas",
        "5": "49 horas ou mais",
        "01": "Até 14 horas",
        "02": "15 a 39 horas",
        "03": "40 a 44 horas",
        "04": "45 a 48 horas",
        "05": "49 horas ou mais",
    }

    # VD4030 - reasons for not seeking work (6 categories)
    vd4030 = {
        "1": "Afazeres domésticos/filhos/outros parentes",
        "2": "Estava estudando",
        "3": "Problema de saúde/gravidez",
        "4": "Muito jovem/idoso para trabalhar",
        "5": "Não queria trabalhar",
        "6": "Outro motivo",
        "01": "Afazeres domésticos/filhos/outros parentes",
        "02": "Estava estudando",
        "03": "Problema de saúde/gravidez",
        "04": "Muito jovem/idoso para trabalhar",
        "05": "Não queria trabalhar",
        "06": "Outro motivo",
    }

    # VD4023 - reasons for not working (6 categories)
    vd4023 = {
        "1": "Afazeres domésticos/filhos/dependentes",
        "2": "Estava estudando",
        "3": "Incapacidade física/mental/doença permanente",
        "4": "Muito jovem/idoso para trabalhar",
        "5": "Não queria trabalhar",
        "6": "Outro motivo",
        "01": "Afazeres domésticos/filhos/dependentes",
        "02": "Estava estudando",
        "03": "Incapacidade física/mental/doença permanente",
        "04": "Muito jovem/idoso para trabalhar",
        "05": "Não queria trabalhar",
        "06": "Outro motivo",
    }

    _write_code_csv(out, "uf", uf)
    _write_code_csv(out, "capital", capital)
    _write_code_csv(out, "rm_ride", rm_ride)
    _write_code_csv(out, "vd4036", v403x_hours)
    _write_code_csv(out, "vd4037", v403x_hours)
    _write_code_csv(out, "vd4030", vd4030)
    _write_code_csv(out, "vd4023", vd4023)
    _write_code_csv(out, "vd4011", vd4011)
    _write_code_csv(out, "v4010", v4010)
    _write_code_csv(out, "vd4009", vd4009)
    _write_code_csv(out, "vd4008", vd4008)
    _write_code_csv(out, "vd4007", vd4007)
    _write_code_csv(out, "vd4005", vd4005)
    _write_code_csv(out, "vd4004a", vd4004a)
    _write_code_csv(out, "vd4003", vd4003)
    _write_code_csv(out, "vd3005", vd3005)
    _write_code_csv(out, "vd3004", vd3004)
    _write_code_csv(out, "vd2002", vd2002)
    _write_code_csv(out, "vd2004", vd2004)
    _write_code_csv(out, "vd2006", vd2006)
    return 0


def cmd_join_codes(args: argparse.Namespace) -> int:
    import csv

    codes_dir = args.codes_dir
    # Load mapping CSVs if present
    def load_map(name):
        path = codes_dir / f"{name}_codes.csv"
        if not path.exists():
            return None
        mp = {}
        with path.open("r", encoding="utf-8") as fh:
            r = csv.DictReader(fh)
            for row in r:
                c = str(row.get("code", ""))
                mp[c] = row.get("label", "")
        # augment with non-zero-padded keys
        for k, v in list(mp.items()):
            mp[k.lstrip("0")] = v
        return mp

    maps = {
        "UF": load_map("uf"),
        "Capital": load_map("capital"),
        "RM_RIDE": load_map("rm_ride"),
        "V2005": load_map("v2005"),
        "V2007": load_map("v2007"),
        "V2010": load_map("v2010"),
        "V3001": load_map("v3001"),
        "V3003A": load_map("v3003a"),
        "V3009A": load_map("v3009a"),
        "VD4036": load_map("vd4036"),
        "VD4037": load_map("vd4037"),
        "VD4030": load_map("vd4030"),
        "VD4023": load_map("vd4023"),
        "VD4011": load_map("vd4011"),
        "V4010": load_map("v4010"),
        "VD4009": load_map("vd4009"),
        "VD4008": load_map("vd4008"),
        "VD4007": load_map("vd4007"),
        "VD4005": load_map("vd4005"),
        "VD4004A": load_map("vd4004a"),
        "VD4003": load_map("vd4003"),
        "VD3005": load_map("vd3005"),
        "VD3004": load_map("vd3004"),
        "VD2002": load_map("vd2002"),
        "VD2004": load_map("vd2004"),
        "VD2006": load_map("vd2006"),
    }

    inp = args.input
    with inp.open("r", encoding="utf-8", errors="replace", newline="") as rf:
        r = csv.DictReader(rf)
        base_to_full = {}
        for c in r.fieldnames or []:
            base = c.split("__", 1)[0]
            base_to_full[base] = c
        # Determine label columns to add
        add_cols = []
        for base, mp in maps.items():
            if base in base_to_full and mp:
                add_cols.append(f"{base}_label")
        fieldnames = list(r.fieldnames or []) + add_cols
        w = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
        w.writeheader()
        for row in r:
            for base, mp in maps.items():
                if not mp or base not in base_to_full:
                    continue
                code = row.get(base_to_full[base], "")
                label = mp.get(str(code), mp.get(str(code).lstrip("0"), ""))
                row[f"{base}_label"] = label
            w.writerow(row)
    return 0


def cmd_household_agg(args: argparse.Namespace) -> int:
    import csv

    inp = args.input
    income_cols = [c.strip() for c in args.income_cols.split(",") if c.strip()]
    carry_cols = [c.strip() for c in args.keep_cols.split(",") if c.strip()]

    def to_float(x: str) -> float:
        try:
            return float(str(x).replace(",", ".")) if x not in (None, "") else 0.0
        except Exception:
            return 0.0

    households = {}
    with inp.open("r", encoding="utf-8", errors="replace", newline="") as rf:
        r = csv.DictReader(rf)
        if "dom_id" not in (r.fieldnames or []):
            print("ERROR: input must contain 'dom_id' (use fwf-extract)", file=sys.stderr)
            return 2
        for row in r:
            dom = row.get("dom_id", "")
            if not dom:
                # skip if cannot identify household
                continue
            st = households.get(dom)
            if st is None:
                st = {"dom_id": dom, "household_persons": 0, "household_income": 0.0}
                for c in carry_cols:
                    st[c] = ""
                households[dom] = st
            st["household_persons"] += 1
            inc = sum(to_float(row.get(c, "")) for c in income_cols)
            st["household_income"] += inc
            # carry first non-empty values
            for c in carry_cols:
                if not st[c]:
                    st[c] = row.get(c, "")

    # Emit CSV
    out_cols = ["dom_id"] + carry_cols + ["household_persons", "household_income"]
    w = csv.DictWriter(sys.stdout, fieldnames=out_cols)
    w.writeheader()
    for st in households.values():
        st_out = st.copy()
        st_out["household_income"] = round(float(st_out["household_income"]), 2)
        w.writerow(st_out)
    return 0


def _slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^A-Za-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text.lower()


def cmd_dict_extract(args: argparse.Namespace) -> int:
    import pandas as pd
    xl_path = Path(args.excel).expanduser()
    out_dir = args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        xls = pd.read_excel(xl_path, sheet_name=None, engine="xlrd")
    except Exception:
        # Fallback: let pandas choose engine
        xls = pd.read_excel(xl_path, sheet_name=None)

    # Normalize column names for each sheet
    def norm_cols(df):
        df = df.copy()
        df.columns = [_slugify(str(c)) for c in df.columns]
        return df

    sheets = {name: norm_cols(df) for name, df in xls.items()}

    # Helpers to pick code/label columns heuristically
    code_candidates = {"codigo", "cod", "valor", "categoria", "code", "id"}
    label_candidates = {"descricao", "descrição", "label", "nome", "description", "titulo", "titulo_categoria", "desc"}

    def pick_cols(df):
        cols = list(df.columns)
        code = next((c for c in cols if c in code_candidates), None)
        label = next((c for c in cols if c in label_candidates), None)
        if code and label:
            return code, label
        # fallback: two first columns
        if len(cols) >= 2:
            return cols[0], cols[1]
        return None, None

    targets = [v.strip() for v in str(args.vars).split(",") if v.strip()]
    sheet_names = list(sheets.keys())

    for var in targets:
        var_slug = _slugify(var)
        # choose sheet by best match on name contains var
        candidates = [name for name in sheet_names if var_slug in _slugify(name)]
        chosen_name = candidates[0] if candidates else None
        if not chosen_name:
            # try any sheet that contains a column matching the var name
            for name, df in sheets.items():
                if var_slug in " ".join(df.columns):
                    chosen_name = name
                    break
        if not chosen_name:
            print(f"ERROR: could not find sheet for '{var}'. Available sheets: {sheet_names}", file=sys.stderr)
            continue
        df = sheets[chosen_name]
        code_col, label_col = pick_cols(df)
        if code_col is None or label_col is None:
            print(f"ERROR: could not infer code/label columns for '{var}' from sheet '{chosen_name}'", file=sys.stderr)
            continue
        out = df[[code_col, label_col]].dropna().drop_duplicates()
        out.columns = ["code", "label"]
        out_path = out_dir / (f"{var_slug}_codes.csv")
        out.to_csv(out_path, index=False)
        print(json.dumps({"var": var, "sheet": chosen_name, "rows": int(len(out)), "out": str(out_path)}, ensure_ascii=False))
    return 0


def cmd_fwf_schema(args: argparse.Namespace) -> int:
    import csv

    fields = parse_layout(args.layout)
    w = csv.writer(sys.stdout)
    w.writerow(["name", "label", "slug", "start", "width", "kind"])
    for f in fields:
        w.writerow([f.name, f.label or "", f.slug or "", f.start + 1, f.width, f.kind])
    return 0


def _resolve_data_path(p) -> Path:
    """Resolve '@data/...' to the repository '@data' directory; else pass-through.

    Examples:
      '@data/PNADC_012025.txt' -> PROJECT_ROOT / '@data' / 'PNADC_012025.txt'
    """
    p = str(p)
    if p.startswith("@data/"):
        rel = p.split("/", 1)[1]
        return PROJECT_ROOT / "@data" / rel
    if p == "@data":
        return PROJECT_ROOT / "@data"
    return Path(p).expanduser()


if __name__ == "__main__":
    raise SystemExit(main())
