#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import pnadc_cli  # type: ignore


def _legacy_commands() -> set[str]:
    parser = pnadc_cli.build_parser()
    sub_actions = [a for a in parser._actions if isinstance(a, argparse._SubParsersAction)]
    if not sub_actions:
        return set()
    return set(sub_actions[0].choices.keys())


LEGACY_COMMANDS = _legacy_commands()

IBGE_MICRODADOS_BASE = (
    "https://ftp.ibge.gov.br/Trabalho_e_Rendimento/"
    "Pesquisa_Nacional_por_Amostra_de_Domicilios_continua/Trimestral/Microdados/"
)
PNADC_ZIP_RE = re.compile(r"^PNADC_(0[1-4])(\d{4})(?:_(\d{8}))?\.zip$", re.IGNORECASE)
RANGE_RE = re.compile(r"^\s*([0-9]+(?:[.,][0-9]+)?)\s*-\s*([0-9]+(?:[.,][0-9]+)?)\s*$")
PLUS_RE = re.compile(r"^\s*([0-9]+(?:[.,][0-9]+)?)\s*\+\s*$")
BCB_SALARIO_MINIMO_SERIE = 1619
BCB_SALARIO_MINIMO_URL = (
    f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{BCB_SALARIO_MINIMO_SERIE}/dados?formato=json&dataInicial=01/01/1994"
)
UF_TO_MACRO = {
    "11": "Norte",
    "12": "Norte",
    "13": "Norte",
    "14": "Norte",
    "15": "Norte",
    "16": "Norte",
    "17": "Norte",
    "21": "Nordeste",
    "22": "Nordeste",
    "23": "Nordeste",
    "24": "Nordeste",
    "25": "Nordeste",
    "26": "Nordeste",
    "27": "Nordeste",
    "28": "Nordeste",
    "29": "Nordeste",
    "31": "Sudeste",
    "32": "Sudeste",
    "33": "Sudeste",
    "35": "Sudeste",
    "41": "Sul",
    "42": "Sul",
    "43": "Sul",
    "50": "Centro-Oeste",
    "51": "Centro-Oeste",
    "52": "Centro-Oeste",
    "53": "Centro-Oeste",
}
MACRO_REGION_ORDER = ["Norte", "Nordeste", "Sudeste", "Sul", "Centro-Oeste", "Desconhecida"]


def _print(msg: str, quiet: bool = False) -> None:
    if not quiet:
        print(msg)


def _download(url: str, destination: Path, *, force: bool = False, quiet: bool = False) -> Path:
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and not force:
        raise FileExistsError(f"Destination already exists: {destination}")

    _print(f"Downloading {url} -> {destination}", quiet=quiet)
    req = Request(url, headers={"User-Agent": "pnad-cli/1.0"})
    with urlopen(req, timeout=120) as resp, destination.open("wb") as fh:
        while True:
            chunk = resp.read(1024 * 1024)
            if not chunk:
                break
            fh.write(chunk)

    _print(f"Saved {destination}", quiet=quiet)
    return destination


def _read_json(path: Path) -> object:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def _json_dump(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)


def _fetch_text(url: str, *, timeout: int = 120) -> str:
    req = Request(url, headers={"User-Agent": "pnad-cli/1.0"})
    with urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _fetch_json(url: str, *, timeout: int = 120) -> object:
    req = Request(url, headers={"User-Agent": "pnad-cli/1.0"})
    with urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def _extract_relative_hrefs(html: str) -> List[str]:
    hrefs = re.findall(r'href="([^"]+)"', html, flags=re.IGNORECASE)
    rel: List[str] = []
    for href in hrefs:
        h = href.strip()
        if not h or h.startswith("?") or h.startswith("/") or ":" in h:
            continue
        rel.append(h)
    return rel


def _list_hrefs(url: str) -> List[str]:
    html = _fetch_text(url)
    return _extract_relative_hrefs(html)


def _parse_pnadc_zip_name(name: str) -> Optional[Dict[str, object]]:
    m = PNADC_ZIP_RE.match(name)
    if not m:
        return None
    quarter = int(m.group(1))
    year = int(m.group(2))
    revision = m.group(3) or ""
    return {"name": name, "quarter": quarter, "year": year, "revision": revision}


def _group_latest_by_quarter(file_names: Sequence[str]) -> Dict[int, Dict[str, object]]:
    latest: Dict[int, Dict[str, object]] = {}
    for name in file_names:
        parsed = _parse_pnadc_zip_name(name)
        if parsed is None:
            continue
        q = int(parsed["quarter"])
        prev = latest.get(q)
        if prev is None:
            latest[q] = parsed
            continue
        if str(parsed["revision"]) > str(prev["revision"]):
            latest[q] = parsed
    return latest


def _latest_local_raw(raw_dir: Path) -> Optional[Path]:
    best_key: tuple[int, int] | None = None
    best_path: Optional[Path] = None
    if not raw_dir.exists():
        return None
    for path in raw_dir.glob("PNADC_*.txt"):
        m = re.match(r"^PNADC_(0[1-4])(\d{4})\.txt$", path.name, flags=re.IGNORECASE)
        if not m:
            continue
        key = (int(m.group(2)), int(m.group(1)))
        if best_key is None or key > best_key:
            best_key = key
            best_path = path
    return best_path


def _head_meta(url: str, *, timeout: int = 120) -> Dict[str, str]:
    req = Request(url, method="HEAD", headers={"User-Agent": "pnad-cli/1.0"})
    with urlopen(req, timeout=timeout) as resp:
        return {
            "etag": (resp.headers.get("ETag") or "").strip(),
            "last_modified": (resp.headers.get("Last-Modified") or "").strip(),
            "content_length": (resp.headers.get("Content-Length") or "").strip(),
            "content_type": (resp.headers.get("Content-Type") or "").strip(),
        }


def _download_if_changed(
    url: str,
    destination: Path,
    *,
    previous_meta: Optional[Dict[str, str]] = None,
    force: bool = False,
    quiet: bool = False,
) -> Dict[str, object]:
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)

    known_etag = (previous_meta or {}).get("etag", "")
    known_last_modified = (previous_meta or {}).get("last_modified", "")
    remote_meta = _head_meta(url)

    if (
        not force
        and destination.exists()
        and (
            (known_etag and known_etag == remote_meta.get("etag", ""))
            or (
                not known_etag
                and known_last_modified
                and known_last_modified == remote_meta.get("last_modified", "")
            )
        )
    ):
        return {"status": "not_modified", "path": str(destination), "meta": remote_meta}

    headers = {"User-Agent": "pnad-cli/1.0"}
    if not force and known_etag:
        headers["If-None-Match"] = known_etag
    elif not force and known_last_modified:
        headers["If-Modified-Since"] = known_last_modified

    req = Request(url, headers=headers)
    tmp = destination.with_name(destination.name + ".tmp")
    try:
        _print(f"Downloading {url} -> {destination}", quiet=quiet)
        with urlopen(req, timeout=120) as resp, tmp.open("wb") as fh:
            while True:
                chunk = resp.read(1024 * 1024)
                if not chunk:
                    break
                fh.write(chunk)
        tmp.replace(destination)
        _print(f"Saved {destination}", quiet=quiet)
        return {"status": "downloaded", "path": str(destination), "meta": remote_meta}
    except HTTPError as exc:
        if exc.code == 304:
            if tmp.exists():
                tmp.unlink()
            return {"status": "not_modified", "path": str(destination), "meta": remote_meta}
        if tmp.exists():
            tmp.unlink()
        raise
    except Exception:
        if tmp.exists():
            tmp.unlink()
        raise


def _extract_single_txt(zip_path: Path, output_dir: Path, *, quiet: bool = False) -> Optional[Path]:
    with zipfile.ZipFile(zip_path) as zf:
        members = [n for n in zf.namelist() if n.lower().endswith(".txt")]
        if not members:
            return None
        member = members[0]
        target = output_dir / Path(member).name
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_name(target.name + ".tmp")
        _print(f"Extracting {zip_path.name}:{member} -> {target}", quiet=quiet)
        with zf.open(member, "r") as src, tmp.open("wb") as dst:
            shutil.copyfileobj(src, dst, length=1024 * 1024)
        tmp.replace(target)
        return target


def _quarter_to_month(q: int) -> int:
    return {1: 3, 2: 6, 3: 9, 4: 12}.get(q, 12)


def _parse_float(value: str | None) -> Optional[float]:
    if value is None:
        return None
    s = str(value).strip().replace(",", ".")
    if not s:
        return None
    try:
        return float(s)
    except Exception:
        return None


def _parse_ranges(spec: str) -> List[Dict[str, object]]:
    out: List[Dict[str, object]] = []
    for token in [p.strip() for p in spec.split(";") if p.strip()]:
        m_plus = PLUS_RE.match(token)
        if m_plus:
            lo = float(m_plus.group(1).replace(",", "."))
            out.append({"label": token, "min": lo, "max": None})
            continue
        m_rng = RANGE_RE.match(token)
        if not m_rng:
            raise ValueError(f"invalid range token: {token}")
        lo = float(m_rng.group(1).replace(",", "."))
        hi = float(m_rng.group(2).replace(",", "."))
        if hi <= lo:
            raise ValueError(f"range upper bound must be greater than lower bound: {token}")
        out.append({"label": token, "min": lo, "max": hi})
    if not out:
        raise ValueError("empty range specification")
    prev_min: Optional[float] = None
    for item in out:
        cur = float(item["min"])
        if prev_min is not None and cur < prev_min:
            raise ValueError("ranges must be ordered by lower bound")
        prev_min = cur
    return out


def _classify_range(value: float, ranges: Sequence[Dict[str, object]]) -> str:
    for item in ranges:
        lo = float(item["min"])
        hi = item["max"]
        if value < lo:
            continue
        if hi is None or value < float(hi):
            return str(item["label"])
    if value < float(ranges[0]["min"]):
        return str(ranges[0]["label"])
    return str(ranges[-1]["label"])


def _find_col(headers: Sequence[str], prefix: str, fallback: str) -> Optional[str]:
    c = next((h for h in headers if h.startswith(prefix)), None)
    if c:
        return c
    if fallback in headers:
        return fallback
    return None


def _detect_income_col(headers: Sequence[str], requested: Optional[str]) -> str:
    if requested:
        if requested not in headers:
            raise ValueError(f"income column not found: {requested}")
        return requested
    c = next((h for h in headers if h.startswith("VD4020")), None)
    if c:
        return c
    c = next((h for h in headers if h.startswith("VD4019")), None)
    if c:
        return c
    raise ValueError("could not auto-detect income column; use --income-col")


def _detect_weight_col(headers: Sequence[str], requested: Optional[str]) -> Optional[str]:
    if requested:
        if requested not in headers:
            raise ValueError(f"weight column not found: {requested}")
        return requested

    def base(name: str) -> str:
        return name.split("__", 1)[0]

    # Prefer calibrated weight (V1028), fallback to non-calibrated (V1027).
    for target in ("V1028", "V1027"):
        for h in headers:
            if base(h) == target:
                return h
    return None


def _read_salario_minimo_csv(path: Path) -> Dict[str, float]:
    out: Dict[str, float] = {}
    with Path(path).open("r", encoding="utf-8", errors="replace", newline="") as fh:
        r = csv.DictReader(fh)
        cols = {c.lower(): c for c in (r.fieldnames or [])}
        date_col = cols.get("date")
        value_col = cols.get("value")
        if not date_col or not value_col:
            raise ValueError("salario minimo csv must contain headers: date,value")
        for row in r:
            ym = str(row.get(date_col, "")).strip()
            val = _parse_float(str(row.get(value_col, "")))
            if ym and val is not None:
                out[ym] = float(val)
    if not out:
        raise ValueError(f"empty salario minimo series: {path}")
    return out


def _latest_target_month(ipca_index: Dict[str, float]) -> str:
    return sorted(ipca_index.keys())[-1]


def _norm_text(value: str) -> str:
    return value.strip().lower()


def _uf_code_norm(uf_value: str) -> str:
    s = uf_value.strip()
    if s.isdigit():
        return s.zfill(2)
    return s


def _macro_region_from_uf(uf_value: str) -> str:
    return UF_TO_MACRO.get(_uf_code_norm(uf_value), "Desconhecida")


def _series_value_at_or_before(series: Dict[str, float], target: str) -> Tuple[str, float]:
    if target in series:
        return target, float(series[target])
    candidates = [k for k in series.keys() if k <= target]
    if not candidates:
        raise ValueError(f"no series value available at or before {target}")
    best = max(candidates)
    return best, float(series[best])


def _resolve_pipeline_target_and_min_wage(
    *,
    target_arg: str,
    min_wage_arg: Optional[float],
    ipca_csv: Path,
    salario_minimo_csv: Path,
) -> Tuple[str, float, str]:
    try:
        from npv_deflators import read_ipca_csv  # type: ignore
    except Exception as exc:
        raise ValueError(f"could not import deflator helper: {exc}") from exc

    ipca_index = read_ipca_csv(Path(ipca_csv))
    if not ipca_index:
        raise ValueError(f"empty IPCA series: {ipca_csv}")

    target = target_arg.strip() if target_arg else _latest_target_month(ipca_index)
    if min_wage_arg is not None:
        return target, float(min_wage_arg), target

    sm_series = _read_salario_minimo_csv(Path(salario_minimo_csv))
    month_used, min_wage = _series_value_at_or_before(sm_series, target)
    return target, float(min_wage), month_used


def _supports_color(no_color: bool = False) -> bool:
    if no_color:
        return False
    if not sys.stdout.isatty():
        return False
    return os.environ.get("TERM", "").lower() not in ("", "dumb")


def _colorize(text: str, code: object, enabled: bool) -> str:
    if not enabled:
        return text
    if isinstance(code, int):
        return f"\033[{code}m{text}\033[0m"
    return f"\033[{str(code)}m{text}\033[0m"


def _bar(pct: float, width: int = 28, char: str = "█") -> str:
    n = max(0, min(width, int(round(width * max(0.0, min(100.0, pct)) / 100.0))))
    return char * n + " " * (width - n)


def _spark(value: float, width: int = 16) -> str:
    blocks = "▁▂▃▄▅▆▇█"
    pct = max(0.0, min(100.0, value))
    idx = int(round((len(blocks) - 1) * pct / 100.0))
    return blocks[idx] * width


def _panel(title: str, lines: Sequence[str], *, color: object, use_color: bool, width: int = 92) -> None:
    t = f" {title} "
    print(_colorize("┏" + t + "━" * max(0, width - len(t) - 2) + "┓", color, use_color))
    for ln in lines:
        txt = (ln[: width - 4] + "..") if len(ln) > width - 2 else ln
        print(_colorize("┃", color, use_color) + txt.ljust(width - 2) + _colorize("┃", color, use_color))
    print(_colorize("┗" + "━" * (width - 2) + "┛", color, use_color))


def _fmt_num(value: float) -> str:
    return f"{value:,.0f}".replace(",", ".")


def _fmt_brl(value: float) -> str:
    s = f"{float(value):,.2f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def _ranges_money_from_specs(
    range_specs: Sequence[Dict[str, object]],
    sm_value: float,
) -> List[Dict[str, object]]:
    out: List[Dict[str, object]] = []
    for spec in range_specs:
        label = str(spec.get("label", ""))
        lo_sm = float(spec.get("min", 0.0) or 0.0)
        hi_raw = spec.get("max")
        lo_brl = lo_sm * float(sm_value)
        hi_brl: Optional[float]
        money_label: str
        if hi_raw is None:
            hi_brl = None
            money_label = f">= {_fmt_brl(lo_brl)}"
        else:
            hi_sm = float(hi_raw)
            hi_brl = hi_sm * float(sm_value)
            money_label = f"{_fmt_brl(lo_brl)} a {_fmt_brl(hi_brl)}"
        out.append(
            {
                "range": label,
                "min_sm": lo_sm,
                "max_sm": None if hi_raw is None else float(hi_raw),
                "min_brl": round(lo_brl, 2),
                "max_brl": None if hi_brl is None else round(hi_brl, 2),
                "money_label": money_label,
            }
        )
    return out


def _mini_pie(bands: Sequence[Dict[str, object]], colors: Sequence[object], use_color: bool, slices: int = 24) -> str:
    if not bands:
        return ""
    pcts = [max(0.0, float(b.get("households_pct", 0.0) or 0.0)) for b in bands]
    raw = [p * slices / 100.0 for p in pcts]
    alloc = [int(x) for x in raw]
    remaining = max(0, slices - sum(alloc))
    frac_idx = sorted(range(len(raw)), key=lambda i: raw[i] - alloc[i], reverse=True)
    for i in frac_idx[:remaining]:
        alloc[i] += 1

    parts: List[str] = []
    for i, n in enumerate(alloc):
        if n <= 0:
            continue
        seg = "●" * n
        parts.append(_colorize(seg, colors[i % len(colors)], use_color))
    return "".join(parts)


def _stacked_mix_bar(
    bands: Sequence[Dict[str, object]],
    *,
    pct_key: str,
    width: int,
    colors: Sequence[object],
    use_color: bool,
) -> str:
    if not bands or width <= 0:
        return ""
    pcts = [max(0.0, float((b or {}).get(pct_key, 0.0) or 0.0)) for b in bands]
    raw = [p * width / 100.0 for p in pcts]
    alloc = [int(x) for x in raw]
    remaining = max(0, width - sum(alloc))
    frac_idx = sorted(range(len(raw)), key=lambda i: raw[i] - alloc[i], reverse=True)
    for i in frac_idx[:remaining]:
        alloc[i] += 1

    parts: List[str] = []
    for i, n in enumerate(alloc):
        if n <= 0:
            continue
        seg = "█" * n
        parts.append(_colorize(seg, colors[i % len(colors)], use_color))
    used = sum(alloc)
    if used < width:
        parts.append(_colorize("░" * (width - used), "38;5;238", use_color))
    return "".join(parts)


def _band_pct(row: Dict[str, object], range_label: str, *, pct_key: str = "persons_pct") -> float:
    bands = row.get("bands", [])
    if not isinstance(bands, list):
        return 0.0
    for band in bands:
        if not isinstance(band, dict):
            continue
        if str(band.get("range", "")) == str(range_label):
            return float(band.get(pct_key, 0.0) or 0.0)
    return 0.0


def _brazil_flag_strip(use_color: bool, width: int = 64) -> str:
    width = max(24, int(width))
    if not use_color:
        return "[BR] " + "=" * (width - 5)

    # Patriotic high-contrast strip with dominant green and accents:
    # green (base) -> yellow -> blue -> white.
    sizes = [int(width * 0.56), int(width * 0.21), int(width * 0.13)]
    sizes.append(max(0, width - sum(sizes)))
    palette = ["1;38;5;46", "1;38;5;226", "1;38;5;21", "1;38;5;15"]
    out: List[str] = []
    for i, n in enumerate(sizes):
        if n > 0:
            out.append(_colorize("█" * n, palette[i], use_color))
    return "".join(out)


def _print_two_columns(
    left: Sequence[str],
    right: Sequence[str],
    *,
    width: int = 58,
    gap: int = 3,
) -> None:
    n = max(len(left), len(right))
    spacer = " " * gap
    for i in range(n):
        l = left[i] if i < len(left) else ""
        r = right[i] if i < len(right) else ""
        print(f"{l:<{width}}{spacer}{r}")


def _brazil_band_colors(n: int) -> List[object]:
    # Brasil-inspired socioeconomic palette from poorer to richer:
    # green -> yellow -> blue -> white.
    base = [
        "1;38;5;46",  # vivid green
        "1;38;5;226",  # vivid yellow
        "1;38;5;21",  # vivid blue
        "1;38;5;15",  # bright white
    ]
    if n <= len(base):
        return base[:n]
    out = []
    for i in range(n):
        out.append(base[i % len(base)])
    return out


def _brazil_band_gradients(n: int) -> List[List[int]]:
    base = [
        [22, 28, 34, 40, 46],  # green ramp
        [178, 184, 190, 220, 226],  # yellow ramp
        [17, 19, 21, 27, 33],  # blue ramp
        [248, 250, 252, 254, 15],  # white ramp
    ]
    return [base[i % len(base)] for i in range(n)]


def _gradient_bar(pct: float, *, width: int, palette: Sequence[int], use_color: bool) -> str:
    p = max(0.0, min(100.0, pct))
    n = max(0, min(width, int(round(width * p / 100.0))))
    if n <= 0:
        return _colorize("░" * width, "38;5;238", use_color)
    parts: List[str] = []
    for i in range(n):
        level = int((i * len(palette)) / max(1, n))
        level = min(level, len(palette) - 1)
        parts.append(_colorize("█", f"1;38;5;{palette[level]}", use_color))
    if n < width:
        parts.append(_colorize("░" * (width - n), "38;5;238", use_color))
    return "".join(parts)


def _badge(text: str, *, fg: int, bg: int, use_color: bool) -> str:
    return _colorize(f" {text} ", f"1;38;5;{fg};48;5;{bg}", use_color)


def _print_renda_pretty(payload: Dict[str, object], *, no_color: bool = False) -> None:
    colors = _brazil_band_colors(len(payload.get("ranges", []) or []))
    gradients = _brazil_band_gradients(len(payload.get("ranges", []) or []))
    use_color = _supports_color(no_color=no_color)

    title = (
        f"Renda Por Faixa De Salario Minimo | alvo {payload.get('target')} | "
        f"{payload.get('weighting_mode')}"
    )
    print(_colorize(title, 1, use_color))
    print(f"Entrada: {payload.get('input')}")
    print(f"Renda: {payload.get('income_col')} | Peso: {payload.get('weight_col') or 'N/A'}")
    print(f"Faixas: {'; '.join(payload.get('ranges', []))}")
    sm_ref = payload.get("sm_reference_value")
    if sm_ref is not None:
        print(f"SM referencia: {_fmt_brl(float(sm_ref))}")
    ranges_money = payload.get("ranges_money")
    if isinstance(ranges_money, list) and ranges_money:
        money_legend = []
        for item in ranges_money:
            if not isinstance(item, dict):
                continue
            money_legend.append(f"{item.get('range')}={item.get('money_label')}")
        if money_legend:
            print("Faixas em R$: " + " | ".join(money_legend))
    print()

    groups = payload.get("groups", [])
    if not isinstance(groups, list):
        return
    for g in groups:
        if not isinstance(g, dict):
            continue
        label = str(g.get("label", g.get("group", "")))
        hh_total = float(g.get("households_total", 0.0) or 0.0)
        pp_total = float(g.get("persons_total", 0.0) or 0.0)
        hh_sample = int(g.get("households_sample", 0) or 0)
        pp_sample = int(g.get("persons_sample", 0) or 0)
        print(_colorize(f"{label}", 1, use_color))
        print(
            f"  Domicilios: {_fmt_num(hh_total)} (amostra={hh_sample}) | "
            f"Pessoas: {_fmt_num(pp_total)} (amostra={pp_sample})"
        )
        avg_sm = float(g.get("avg_household_sm", 0.0) or 0.0)
        print(f"  Media renda domiciliar (SM): {avg_sm:.3f}")
        print("  Faixa      Dom%     Dom(barra)                    Pes%     Pes(barra)")

        bands = g.get("bands", [])
        if not isinstance(bands, list):
            continue
        for i, b in enumerate(bands):
            if not isinstance(b, dict):
                continue
            rng = str(b.get("range", ""))
            hp = float(b.get("households_pct", 0.0) or 0.0)
            pp = float(b.get("persons_pct", 0.0) or 0.0)
            hbar = _gradient_bar(hp, width=28, palette=gradients[i % len(gradients)], use_color=use_color)
            pbar = _gradient_bar(pp, width=28, palette=gradients[i % len(gradients)], use_color=use_color)
            c = colors[i % len(colors)]
            print(
                "  "
                + _badge(f"{rng:<8}", fg=16, bg=gradients[i % len(gradients)][-1], use_color=use_color)
                + f" {hp:6.2f}%  "
                + hbar
                + f"  {pp:6.2f}%  "
                + pbar
            )
        pie = _mini_pie([b for b in bands if isinstance(b, dict)], colors, use_color)
        if pie:
            print(f"  Pizza domicílios: {pie}")
        print()


def _safe_div(num: float, den: float) -> float:
    if den == 0:
        return 0.0
    return float(num) / float(den)


def _weighted_median(pairs: Sequence[Tuple[float, float]]) -> float:
    data = [(x, w) for (x, w) in pairs if w > 0]
    if not data:
        return 0.0
    data.sort(key=lambda t: t[0])
    total = sum(w for _, w in data)
    cutoff = total * 0.5
    acc = 0.0
    for x, w in data:
        acc += w
        if acc >= cutoff:
            return float(x)
    return float(data[-1][0])


def _weighted_gini(pairs: Sequence[Tuple[float, float]]) -> float:
    data = [(max(0.0, x), w) for (x, w) in pairs if w > 0]
    if not data:
        return 0.0
    data.sort(key=lambda t: t[0])
    total_w = sum(w for _, w in data)
    total_xw = sum(x * w for x, w in data)
    if total_w <= 0 or total_xw <= 0:
        return 0.0

    cum_w = 0.0
    cum_xw = 0.0
    area = 0.0
    for x, w in data:
        prev_w = cum_w
        prev_xw = cum_xw
        cum_w += w
        cum_xw += x * w
        area += (prev_xw + cum_xw) * (cum_w - prev_w) * 0.5
    gini = 1.0 - 2.0 * area / (total_w * total_xw)
    return max(0.0, min(1.0, gini))


def _age_band(age_value: str) -> str:
    age = _parse_float(age_value)
    if age is None:
        return "sem_idade"
    a = int(age)
    if a <= 13:
        return "00-13"
    if a <= 24:
        return "14-24"
    if a <= 39:
        return "25-39"
    if a <= 59:
        return "40-59"
    return "60+"


def _counter_to_sorted_rows(counter: Dict[str, float], total: float) -> List[Dict[str, object]]:
    rows = []
    for k, v in counter.items():
        rows.append({"label": k, "value": float(v), "pct": round(100.0 * _safe_div(v, total), 4)})
    rows.sort(key=lambda r: r["value"], reverse=True)
    return rows


def _build_dashboard_payload(args: argparse.Namespace) -> Dict[str, object]:
    try:
        from npv_deflators import build_deflators, read_ipca_csv  # type: ignore
    except Exception as exc:
        raise ValueError(f"could not import deflator helpers: {exc}") from exc

    ranges = _parse_ranges(args.ranges)
    input_path = Path(args.input)
    ipca_csv = Path(args.ipca_csv)
    sm_csv = Path(args.salario_minimo_csv)
    if not input_path.exists():
        raise ValueError(f"input file not found: {input_path}")
    ipca_index = read_ipca_csv(ipca_csv)
    target = args.target.strip() if args.target else _latest_target_month(ipca_index)
    factor_map = build_deflators(ipca_index, target)
    sm_series = _read_salario_minimo_csv(sm_csv)
    sm_target_month, sm_target_nominal = _series_value_at_or_before(sm_series, target)

    uf_filter: set[str] = set()
    if args.state:
        uf_filter = {_norm_text(x) for x in args.state.split(",") if x.strip()}

    sampled_rows = 0
    skipped_missing_period = 0
    skipped_missing_sm = 0
    skipped_missing_factor = 0
    skipped_missing_weight = 0
    skipped_invalid_weight = 0
    inconsistent_household_weight = 0
    selected_income_col = ""
    selected_weight_col: Optional[str] = None
    households: Dict[str, Dict[str, object]] = {}
    dimension_labels: Dict[str, str] = {}
    dim_keys: List[str] = []

    with input_path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fh:
        r = csv.DictReader(fh)
        headers = r.fieldnames or []
        if not headers:
            raise ValueError("input has no header")

        dom_col = _find_col(headers, "dom_id", "dom_id")
        year_col = _find_col(headers, "Ano__", "Ano")
        qtr_col = _find_col(headers, "Trimestre__", "Trimestre")
        uf_col = _find_col(headers, "UF__", "UF")
        uf_label_col = _find_col(headers, "UF_label", "UF_label")
        cap_col = _find_col(headers, "Capital__", "Capital")
        cap_label_col = _find_col(headers, "Capital_label", "Capital_label")

        sex_col = "V2007_label" if "V2007_label" in headers else _find_col(headers, "V2007__", "V2007")
        race_col = "V2010_label" if "V2010_label" in headers else _find_col(headers, "V2010__", "V2010")
        edu_col = "V3009A_label" if "V3009A_label" in headers else _find_col(headers, "V3009A__", "V3009A")
        age_col = _find_col(headers, "V2009__", "V2009")

        relationship_col = "V2005_label" if "V2005_label" in headers else _find_col(headers, "V2005__", "V2005")
        occupation_status_col = (
            "VD4009_label" if "VD4009_label" in headers else _find_col(headers, "VD4009__", "VD4009")
        )
        labor_type_col = "VD4005_label" if "VD4005_label" in headers else _find_col(headers, "VD4005__", "VD4005")
        position_col = "V4010_label" if "V4010_label" in headers else _find_col(headers, "V4010__", "V4010")
        rm_label_col = "RM_RIDE_label" if "RM_RIDE_label" in headers else None
        rm_col = _find_col(headers, "RM_RIDE__", "RM_RIDE")

        income_col = _detect_income_col(headers, args.income_col)
        selected_income_col = income_col
        selected_weight_col = None if args.unweighted else _detect_weight_col(headers, args.weight_col)

        if not dom_col or not year_col or not qtr_col or not uf_col:
            raise ValueError("input must contain dom_id, Ano, Trimestre and UF")
        if not args.unweighted and not selected_weight_col:
            raise ValueError(
                "weight column not found. Re-run pipeline including V1028 "
                "or pass --weight-col / use --unweighted for diagnostics."
            )

        dim_keys = ["sex", "race", "education", "age", "capital", "macro_region"]
        dimension_labels = {
            "sex": "Sexo",
            "race": "Raca/Cor",
            "education": "Escolaridade",
            "age": "Faixa etaria",
            "capital": "Capital x Interior",
            "macro_region": "Macro-regiao",
        }
        if relationship_col:
            dim_keys.append("relationship")
            dimension_labels["relationship"] = "Relacao no domicilio"
        if occupation_status_col:
            dim_keys.append("occupation_status")
            dimension_labels["occupation_status"] = "Condicao ocupacional"
        if labor_type_col:
            dim_keys.append("labor_type")
            dimension_labels["labor_type"] = "Tipo de trabalho"
        if position_col:
            dim_keys.append("occupation_position")
            dimension_labels["occupation_position"] = "Posicao ocupacao"
        if rm_label_col or rm_col:
            dim_keys.append("metro_region")
            dimension_labels["metro_region"] = "RM/RIDE"

        for row in r:
            sampled_rows += 1
            dom = str(row.get(dom_col, "")).strip()
            if not dom:
                continue

            y_raw = str(row.get(year_col, "")).strip()
            q_raw = str(row.get(qtr_col, "")).strip()
            try:
                year = int(y_raw)
                quarter = int(q_raw)
                month = _quarter_to_month(quarter)
            except Exception:
                skipped_missing_period += 1
                continue
            ym = f"{year}-{month:02d}"

            factor = factor_map.get(ym)
            if factor is None:
                skipped_missing_factor += 1
                continue
            sm_nominal = sm_series.get(ym)
            if sm_nominal is None:
                skipped_missing_sm += 1
                continue

            uf_code_raw = str(row.get(uf_col, "")).strip()
            uf_code = _uf_code_norm(uf_code_raw)
            uf_label = str(row.get(uf_label_col, "")).strip() if uf_label_col else ""
            if uf_filter and _norm_text(uf_code) not in uf_filter and _norm_text(uf_label) not in uf_filter:
                continue

            row_weight = 1.0
            if selected_weight_col:
                rw = row.get(selected_weight_col, "")
                if rw in (None, ""):
                    skipped_missing_weight += 1
                    continue
                parsed_w = _parse_float(rw)
                if parsed_w is None or parsed_w <= 0:
                    skipped_invalid_weight += 1
                    continue
                row_weight = float(parsed_w)

            income_nominal = _parse_float(row.get(income_col, ""))
            if income_nominal is None:
                income_nominal = 0.0

            sex = str(row.get(sex_col, "")).strip() if sex_col else ""
            race = str(row.get(race_col, "")).strip() if race_col else ""
            edu = str(row.get(edu_col, "")).strip() if edu_col else ""
            age_band = _age_band(str(row.get(age_col, ""))) if age_col else "sem_idade"

            cap = str(row.get(cap_label_col, "")).strip() if cap_label_col else ""
            if not cap and cap_col:
                raw_cap = str(row.get(cap_col, "")).strip()
                cap = "Capital" if raw_cap in ("1", "01") else ("Nao capital" if raw_cap in ("2", "02") else raw_cap)

            relationship = str(row.get(relationship_col, "")).strip() if relationship_col else ""
            occupation_status = str(row.get(occupation_status_col, "")).strip() if occupation_status_col else ""
            labor_type = str(row.get(labor_type_col, "")).strip() if labor_type_col else ""
            occupation_position = str(row.get(position_col, "")).strip() if position_col else ""
            if rm_label_col:
                metro_region = str(row.get(rm_label_col, "")).strip()
            elif rm_col:
                metro_region = str(row.get(rm_col, "")).strip()
            else:
                metro_region = ""
            macro_region = _macro_region_from_uf(uf_code)

            st = households.get(dom)
            if st is None:
                st = {
                    "dom_id": dom,
                    "uf_code": uf_code,
                    "uf_label": uf_label or uf_code,
                    "macro_region": macro_region,
                    "persons_n": 0,
                    "persons_weight": 0.0,
                    "household_weight": row_weight,
                    "income_nominal": 0.0,
                    "income_target": 0.0,
                    "sm_period": float(sm_nominal),
                    "ym": ym,
                    "dim_counts": {k: defaultdict(float) for k in dim_keys},
                }
                households[dom] = st

            st["persons_n"] = int(st["persons_n"]) + 1
            st["persons_weight"] = float(st["persons_weight"]) + row_weight
            st["income_nominal"] = float(st["income_nominal"]) + float(income_nominal)
            st["income_target"] = float(st["income_target"]) + float(income_nominal) * float(factor)
            hw = float(st.get("household_weight") or row_weight)
            if abs(hw - row_weight) > 1e-6:
                inconsistent_household_weight += 1

            sw = row_weight if not args.unweighted else 1.0
            row_dims = {
                "sex": sex or "sem_info",
                "race": race or "sem_info",
                "education": edu or "sem_info",
                "age": age_band or "sem_info",
                "capital": cap or "N/A",
                "macro_region": macro_region,
            }
            if "relationship" in dim_keys:
                row_dims["relationship"] = relationship or "sem_info"
            if "occupation_status" in dim_keys:
                row_dims["occupation_status"] = occupation_status or "sem_info"
            if "labor_type" in dim_keys:
                row_dims["labor_type"] = labor_type or "sem_info"
            if "occupation_position" in dim_keys:
                row_dims["occupation_position"] = occupation_position or "sem_info"
            if "metro_region" in dim_keys:
                row_dims["metro_region"] = metro_region or "sem_info"

            dim_counts = st["dim_counts"]
            for dim, value in row_dims.items():
                dim_counts[dim][str(value)] += sw

    modes = ["periodo", "alvo"] if args.sm_mode == "both" else [args.sm_mode]
    modes_out: Dict[str, object] = {}
    for mode in modes:
        national = {
            "households_total": 0.0,
            "persons_total": 0.0,
            "households_sample": 0,
            "persons_sample": 0,
            "sum_ratio": 0.0,
            "bands": {str(item["label"]): {"households": 0.0, "persons": 0.0} for item in ranges},
        }
        uf_stats: Dict[str, Dict[str, object]] = {}
        macro_stats: Dict[str, Dict[str, object]] = {}
        demo = {k: defaultdict(float) for k in dim_keys}
        cross = {k: defaultdict(lambda: defaultdict(float)) for k in dim_keys}
        ratio_pairs: List[Tuple[float, float]] = []
        sm_ref_weighted_sum = 0.0
        sm_ref_weight_total = 0.0
        sm_ref_min: Optional[float] = None
        sm_ref_max: Optional[float] = None

        def ensure_group(container: Dict[str, Dict[str, object]], key: str, label: str) -> Dict[str, object]:
            g = container.get(key)
            if g is None:
                g = {
                    "group": key,
                    "label": label,
                    "households_total": 0.0,
                    "persons_total": 0.0,
                    "households_sample": 0,
                    "persons_sample": 0,
                    "sum_ratio": 0.0,
                    "bands": {str(item["label"]): {"households": 0.0, "persons": 0.0} for item in ranges},
                }
                container[key] = g
            return g

        for h in households.values():
            if mode == "periodo":
                ratio = _safe_div(float(h["income_nominal"]), float(h["sm_period"]))
            else:
                ratio = _safe_div(float(h["income_target"]), float(sm_target_nominal))
            band = _classify_range(ratio if ratio > 0 else 0.0, ranges)

            hh_w = 1.0 if args.unweighted else float(h["household_weight"])
            pp_w = float(h["persons_n"]) if args.unweighted else float(h["persons_weight"])
            uf_code = str(h["uf_code"])
            uf_label = str(h["uf_label"])
            macro = str(h.get("macro_region", "Desconhecida") or "Desconhecida")
            sm_ref_value = float(sm_target_nominal) if mode == "alvo" else float(h.get("sm_period") or 0.0)
            if sm_ref_value > 0:
                sm_ref_weighted_sum += sm_ref_value * hh_w
                sm_ref_weight_total += hh_w
                sm_ref_min = sm_ref_value if sm_ref_min is None else min(sm_ref_min, sm_ref_value)
                sm_ref_max = sm_ref_value if sm_ref_max is None else max(sm_ref_max, sm_ref_value)

            national["households_total"] += hh_w
            national["persons_total"] += pp_w
            national["households_sample"] += 1
            national["persons_sample"] += int(h["persons_n"])
            national["sum_ratio"] += ratio * hh_w
            national["bands"][band]["households"] += hh_w
            national["bands"][band]["persons"] += pp_w
            ratio_pairs.append((ratio, hh_w))

            u = ensure_group(uf_stats, uf_code, uf_label)
            u["households_total"] += hh_w
            u["persons_total"] += pp_w
            u["households_sample"] += 1
            u["persons_sample"] += int(h["persons_n"])
            u["sum_ratio"] += ratio * hh_w
            u["bands"][band]["households"] += hh_w
            u["bands"][band]["persons"] += pp_w

            m = ensure_group(macro_stats, macro, macro)
            m["households_total"] += hh_w
            m["persons_total"] += pp_w
            m["households_sample"] += 1
            m["persons_sample"] += int(h["persons_n"])
            m["sum_ratio"] += ratio * hh_w
            m["bands"][band]["households"] += hh_w
            m["bands"][band]["persons"] += pp_w

            dim_counts = h.get("dim_counts", {})
            for dim in dim_keys:
                src = dim_counts.get(dim, {})
                for lbl, val in src.items():
                    demo[dim][str(lbl)] += float(val)
                    cross[dim][str(lbl)][band] += float(val)

        def finalize_group(g: Dict[str, object]) -> Dict[str, object]:
            hh_total = float(g["households_total"])
            pp_total = float(g["persons_total"])
            bands_rows = []
            for item in ranges:
                lbl = str(item["label"])
                b = g["bands"][lbl]
                bh = float(b["households"])
                bp = float(b["persons"])
                bands_rows.append(
                    {
                        "range": lbl,
                        "households": bh,
                        "households_pct": round(100.0 * _safe_div(bh, hh_total), 4),
                        "persons": bp,
                        "persons_pct": round(100.0 * _safe_div(bp, pp_total), 4),
                    }
                )
            avg_sm = _safe_div(float(g["sum_ratio"]), hh_total)
            return {
                "group": g["group"],
                "label": g["label"],
                "households_total": hh_total,
                "persons_total": pp_total,
                "households_sample": int(g["households_sample"]),
                "persons_sample": int(g["persons_sample"]),
                "avg_household_sm": round(avg_sm, 6),
                "bands": bands_rows,
            }

        national_out = finalize_group({"group": "BR", "label": "Brasil", **national})
        national_out["median_household_sm"] = round(_weighted_median(ratio_pairs), 6)
        national_out["gini_household_sm"] = round(_weighted_gini(ratio_pairs), 6)

        uf_rows = [finalize_group(v) for v in uf_stats.values()]
        if args.uf_order == "alfabetica":
            uf_rows.sort(key=lambda r: str(r["label"]).lower())
        elif args.uf_order == "codigo":
            uf_rows.sort(key=lambda r: str(r["group"]))
        elif args.uf_order == "renda_asc":
            uf_rows.sort(key=lambda r: float(r["avg_household_sm"]))
        else:
            uf_rows.sort(key=lambda r: float(r["avg_household_sm"]), reverse=True)

        top10_income = uf_rows[:10]
        bottom10_income = sorted(uf_rows, key=lambda r: float(r["avg_household_sm"]))[:10]
        top10_population = sorted(uf_rows, key=lambda r: float(r["persons_total"]), reverse=True)[:10]
        low_label = str(ranges[0]["label"]) if ranges else ""
        high_label = str(ranges[-1]["label"]) if ranges else ""
        top10_low_income = (
            sorted(uf_rows, key=lambda r: _band_pct(r, low_label), reverse=True)[:10] if low_label else []
        )
        top10_high_income = (
            sorted(uf_rows, key=lambda r: _band_pct(r, high_label), reverse=True)[:10] if high_label else []
        )

        macro_rows = [finalize_group(v) for v in macro_stats.values()]
        macro_rows.sort(
            key=lambda r: MACRO_REGION_ORDER.index(str(r["group"]))
            if str(r["group"]) in MACRO_REGION_ORDER
            else 999
        )

        persons_total = float(national_out["persons_total"])
        demographics_out = {k: _counter_to_sorted_rows(v, persons_total) for k, v in demo.items()}

        def cross_rows(src: Dict[str, Dict[str, float]]) -> List[Dict[str, object]]:
            rows = []
            for k, v in src.items():
                total = sum(v.values())
                row = {"label": k, "total": total, "bands": {}}
                for item in ranges:
                    lbl = str(item["label"])
                    x = float(v.get(lbl, 0.0))
                    row["bands"][lbl] = {
                        "value": x,
                        "pct_within_label": round(100.0 * _safe_div(x, total), 4),
                    }
                rows.append(row)
            rows.sort(key=lambda r: float(r["total"]), reverse=True)
            return rows

        cross_out = {f"{k}_by_band": cross_rows(v) for k, v in cross.items()}
        sm_reference_value = _safe_div(sm_ref_weighted_sum, sm_ref_weight_total)
        if sm_reference_value <= 0:
            sm_reference_value = float(sm_target_nominal)
        ranges_money = _ranges_money_from_specs(ranges, sm_reference_value)
        range_money_map = {str(x.get("range", "")): str(x.get("money_label", "")) for x in ranges_money}
        insights = {
            "national_low_income_band": low_label,
            "national_high_income_band": high_label,
            "national_low_income_money": range_money_map.get(low_label, ""),
            "national_high_income_money": range_money_map.get(high_label, ""),
            "national_low_income_pct": round(_band_pct(national_out, low_label), 4) if low_label else 0.0,
            "national_high_income_pct": round(_band_pct(national_out, high_label), 4) if high_label else 0.0,
            "richest_uf_by_avg_sm": top10_income[0]["label"] if top10_income else "",
            "poorest_uf_by_avg_sm": bottom10_income[0]["label"] if bottom10_income else "",
            "highest_low_income_uf": top10_low_income[0]["label"] if top10_low_income else "",
            "highest_high_income_uf": top10_high_income[0]["label"] if top10_high_income else "",
        }

        modes_out[mode] = {
            "national": national_out,
            "uf": uf_rows,
            "macro_regions": macro_rows,
            "top5_uf": top10_income[:5],
            "bottom5_uf": bottom10_income[:5],
            "top10_uf_income": top10_income,
            "bottom10_uf_income": bottom10_income,
            "top10_uf_population": top10_population,
            "top10_uf_low_income": top10_low_income,
            "top10_uf_high_income": top10_high_income,
            "sm_reference_value": round(float(sm_reference_value), 2),
            "sm_reference_month": sm_target_month if mode == "alvo" else "periodo_medio",
            "sm_reference_min": None if sm_ref_min is None else round(float(sm_ref_min), 2),
            "sm_reference_max": None if sm_ref_max is None else round(float(sm_ref_max), 2),
            "ranges_money": ranges_money,
            "insights": insights,
            "demographics": demographics_out,
            "dimensions": dim_keys,
            "cross": cross_out,
        }

    return {
        "input": str(input_path),
        "target": target,
        "sm_target_month": sm_target_month,
        "sm_target_value": sm_target_nominal,
        "sm_mode": args.sm_mode,
        "uf_order": args.uf_order,
        "ranges": [str(x["label"]) for x in ranges],
        "range_specs": [
            {
                "label": str(x["label"]),
                "min": float(x["min"]),
                "max": None if x["max"] is None else float(x["max"]),
            }
            for x in ranges
        ],
        "income_col": selected_income_col,
        "weight_col": None if args.unweighted else selected_weight_col,
        "weighting_mode": "unweighted" if args.unweighted else "weighted",
        "dimension_labels": dimension_labels,
        "modes": modes_out,
        "metadata": {
            "rows_read": sampled_rows,
            "households": len(households),
            "states_covered": len({str(h["uf_code"]) for h in households.values()}),
            "dimensions": dim_keys,
            "skipped_missing_period": skipped_missing_period,
            "skipped_missing_factor": skipped_missing_factor,
            "skipped_missing_sm": skipped_missing_sm,
            "skipped_missing_weight": skipped_missing_weight,
            "skipped_invalid_weight": skipped_invalid_weight,
            "inconsistent_household_weight_rows": inconsistent_household_weight,
            "ipca_csv": str(ipca_csv),
            "salario_minimo_csv": str(sm_csv),
        },
    }


def _print_dashboard_mode(
    payload: Dict[str, object], mode: str, *, no_color: bool = False, section: str = "all"
) -> None:
    use_color = _supports_color(no_color=no_color)
    colors = _brazil_band_colors(len(payload.get("ranges", []) or []))
    gradients = _brazil_band_gradients(len(payload.get("ranges", []) or []))
    mode_data = payload["modes"][mode]
    nat = mode_data["national"]
    show = lambda key: section in ("all", key)

    if show("overview"):
        sm_ref = float(mode_data.get("sm_reference_value", payload.get("sm_target_value") or 0.0) or 0.0)
        sm_ref_month = str(mode_data.get("sm_reference_month", "") or "")
        sm_ref_min = mode_data.get("sm_reference_min")
        sm_ref_max = mode_data.get("sm_reference_max")
        if sm_ref_min is not None and sm_ref_max is not None and float(sm_ref_min) != float(sm_ref_max):
            sm_ref_txt = (
                f"{_fmt_brl(sm_ref)} (ref media, intervalo: {_fmt_brl(float(sm_ref_min))}..{_fmt_brl(float(sm_ref_max))})"
            )
        else:
            sm_ref_txt = _fmt_brl(sm_ref)
        overview_lines = [
            f"Modo de comparacao: {mode.upper()}",
            f"Domicilios: {_fmt_num(float(nat['households_total']))} | Pessoas: {_fmt_num(float(nat['persons_total']))}",
            (
                f"Media SM: {float(nat['avg_household_sm']):.3f} | "
                f"Mediana SM: {float(nat['median_household_sm']):.3f} | Gini(SM): {float(nat['gini_household_sm']):.3f}"
            ),
            f"SM referencia ({sm_ref_month}): {sm_ref_txt}",
        ]
        _panel("Visao Brasil", overview_lines, color="1;38;5;45", use_color=use_color)
        print(_colorize(" Distribuicao nacional por faixa", 1, use_color))
        for b in nat["bands"]:
            hp = float(b["households_pct"])
            pp = float(b["persons_pct"])
            gi = payload["ranges"].index(b["range"]) % len(gradients)
            print(
                "  "
                + _badge(f"{b['range']:<8}", fg=16, bg=gradients[gi][-1], use_color=use_color)
                + f" dom={hp:6.2f}% {_gradient_bar(hp, width=24, palette=gradients[gi], use_color=use_color)}"
                + f"  pes={pp:6.2f}% {_gradient_bar(pp, width=10, palette=gradients[gi], use_color=use_color)}"
            )
        pie = _mini_pie(nat["bands"], colors=colors, use_color=use_color, slices=30)
        if pie:
            print(f"  Pizza domicílios: {pie}")
        mix = _stacked_mix_bar(
            nat["bands"],
            pct_key="persons_pct",
            width=40,
            colors=colors,
            use_color=use_color,
        )
        if mix:
            print(f"  Mix pessoas: {mix}")
        if payload.get("ranges"):
            legend = []
            socio = ["mais pobre", "media baixa", "media alta", "mais rica"]
            ranges_money = mode_data.get("ranges_money", [])
            money_map: Dict[str, str] = {}
            if isinstance(ranges_money, list):
                for item in ranges_money:
                    if not isinstance(item, dict):
                        continue
                    money_map[str(item.get("range", ""))] = str(item.get("money_label", ""))
            for i, rng in enumerate(payload["ranges"]):
                label = socio[i] if i < len(socio) else f"faixa {i + 1}"
                cash = money_map.get(str(rng), "")
                if cash:
                    legend.append(_colorize(f"{rng}={label} ({cash})", colors[i % len(colors)], use_color))
                else:
                    legend.append(_colorize(f"{rng}={label}", colors[i % len(colors)], use_color))
            print("  Legenda BR: " + " | ".join(legend))
        print()

    if show("ranking"):
        print(_colorize(" Ranking horizontal de UFs", "1;38;5;51", use_color))
        left = [_colorize("  Top 10 UFs por renda (SM domiciliar)", "1;38;5;46", use_color)]
        right = [_colorize("  Top 10 UFs por populacao estimada", "1;38;5;33", use_color)]
        pop_total = float(nat["persons_total"]) or 1.0
        for i, u in enumerate(mode_data.get("top10_uf_income", []), start=1):
            val = float(u["avg_household_sm"])
            heat = _gradient_bar(min(val * 16, 100), width=8, palette=[22, 28, 34, 40, 46], use_color=use_color)
            left.append(f"  {i:>2}. {u['label']:<18} {val:6.3f} SM {heat}")
        for i, u in enumerate(mode_data.get("top10_uf_population", []), start=1):
            ppl = float(u["persons_total"])
            share = 100.0 * _safe_div(ppl, pop_total)
            heat = _gradient_bar(min(share * 4, 100), width=8, palette=[17, 19, 21, 27, 33], use_color=use_color)
            right.append(f"  {i:>2}. {u['label']:<18} {share:5.2f}% {heat}")
        _print_two_columns(left, right, width=58, gap=3)
        print("")
        print(_colorize("  Bottom 10 UFs por renda (SM)", "1;38;5;196", use_color))
        for i, u in enumerate(mode_data.get("bottom10_uf_income", []), start=1):
            val = float(u["avg_household_sm"])
            heat = _gradient_bar(min(val * 16, 100), width=10, palette=[52, 88, 124, 160, 196], use_color=use_color)
            print(f"   {i:>2}. {u['label']:<18} {val:6.3f} SM {heat}")
        print()

    if show("macro"):
        print(_colorize(" Macro-regioes do Brasil", "1;38;5;39", use_color))
        for mr in mode_data.get("macro_regions", []):
            ppl = float(mr["persons_total"])
            share = 100.0 * _safe_div(ppl, float(nat["persons_total"]) or 1.0)
            avg = float(mr["avg_household_sm"])
            mix = _stacked_mix_bar(
                mr["bands"],
                pct_key="persons_pct",
                width=20,
                colors=colors,
                use_color=use_color,
            )
            pbar = _gradient_bar(share, width=12, palette=[17, 19, 21, 27, 33], use_color=use_color)
            print(f"  {mr['label']:<12} pop={share:5.2f}% {pbar}  media={avg:5.2f} SM  mix={mix}")
        print("")

    if show("population"):
        print(_colorize(" Top 10 UFs por populacao com mix de faixas", "1;38;5;33", use_color))
        for i, u in enumerate(mode_data.get("top10_uf_population", []), start=1):
            ppl = float(u["persons_total"])
            share = 100.0 * _safe_div(ppl, float(nat["persons_total"]) or 1.0)
            mix = _stacked_mix_bar(
                u["bands"],
                pct_key="persons_pct",
                width=24,
                colors=colors,
                use_color=use_color,
            )
            print(f"  {i:>2}. {u['label']:<18} pop={share:5.2f}%  mix={mix}")
        print()

    if show("demography"):
        print(_colorize(" Demografia compacta (multiplos recortes)", 33, use_color))
        demo = mode_data.get("demographics", {})
        dim_labels = payload.get("dimension_labels", {})
        dim_order = mode_data.get("dimensions", [])
        for dim in dim_order:
            rows = demo.get(dim, [])
            if not rows:
                continue
            top = rows[:4]
            parts = [f"{str(x['label'])[:18]} {float(x['pct']):4.1f}%" for x in top]
            label = dim_labels.get(dim, dim)
            print(f"  {label:<22} " + " | ".join(parts))
        print("")

    if show("cross"):
        print(_colorize(" Cruzamentos principais x faixas de SM", 34, use_color))
        cross = mode_data.get("cross", {})
        dim_labels = payload.get("dimension_labels", {})
        chosen_dims = ["sex", "race", "education", "age", "capital", "macro_region"]
        for dim in chosen_dims:
            key = f"{dim}_by_band"
            rows = cross.get(key, [])
            if not rows:
                continue
            print(_colorize(f"  {dim_labels.get(dim, dim)}", "1;38;5;117", use_color))
            for row in rows[:3]:
                parts = []
                for b in payload["ranges"]:
                    pct = float(row["bands"][b]["pct_within_label"])
                    bi = payload["ranges"].index(b) % len(gradients)
                    parts.append(
                        f"{b}:{pct:4.1f}% {_gradient_bar(pct, width=3, palette=gradients[bi], use_color=use_color)}"
                    )
                print(f"   - {str(row['label'])[:18]:<18} {' | '.join(parts)}")
            print("")

    if show("insights"):
        ins = mode_data.get("insights", {})
        if isinstance(ins, dict):
            print(_colorize(" Termometro socioeconomico", "1;38;5;229", use_color))
            low_label = str(ins.get("national_low_income_band", "") or "")
            high_label = str(ins.get("national_high_income_band", "") or "")
            low_money = str(ins.get("national_low_income_money", "") or "")
            high_money = str(ins.get("national_high_income_money", "") or "")
            low_pct = float(ins.get("national_low_income_pct", 0.0) or 0.0)
            high_pct = float(ins.get("national_high_income_pct", 0.0) or 0.0)
            print(
                "  "
                + _badge(f"{low_label or 'baixa':<8}", fg=16, bg=46, use_color=use_color)
                + f" {low_pct:6.2f}% das pessoas"
                + "  |  "
                + _badge(f"{high_label or 'alta':<8}", fg=16, bg=15, use_color=use_color)
                + f" {high_pct:6.2f}% das pessoas"
            )
            if low_money or high_money:
                print(f"  Equivalencia em R$: baixa={low_money or 'N/A'} | alta={high_money or 'N/A'}")
            print(
                f"  Renda media mais alta: {ins.get('richest_uf_by_avg_sm', 'N/A')} | "
                f"mais baixa: {ins.get('poorest_uf_by_avg_sm', 'N/A')}"
            )
            print(
                f"  Maior concentracao na faixa {low_label}: {ins.get('highest_low_income_uf', 'N/A')} | "
                f"na faixa {high_label}: {ins.get('highest_high_income_uf', 'N/A')}"
            )
            left = [_colorize(f"  Top 10 UFs na faixa {low_label}", "1;38;5;46", use_color)]
            right = [_colorize(f"  Top 10 UFs na faixa {high_label}", "1;38;5;15", use_color)]
            for i, u in enumerate(mode_data.get("top10_uf_low_income", []), start=1):
                pct = _band_pct(u, low_label)
                bar = _gradient_bar(pct, width=8, palette=[22, 28, 34, 40, 46], use_color=use_color)
                left.append(f"  {i:>2}. {u['label']:<18} {pct:5.2f}% {bar}")
            for i, u in enumerate(mode_data.get("top10_uf_high_income", []), start=1):
                pct = _band_pct(u, high_label)
                bar = _gradient_bar(pct, width=8, palette=[248, 250, 252, 254, 15], use_color=use_color)
                right.append(f"  {i:>2}. {u['label']:<18} {pct:5.2f}% {bar}")
            _print_two_columns(left, right, width=58, gap=3)
            print("")

    if show("meta"):
        md = payload.get("metadata", {})
        if isinstance(md, dict):
            print(_colorize(" Metadados de cobertura e qualidade", "1;38;5;250", use_color))
            print(
                f"  rows={md.get('rows_read')} | households={md.get('households')} | "
                f"ufs={md.get('states_covered')} | dims={len(md.get('dimensions', []))}"
            )
            print(
                f"  skips(period={md.get('skipped_missing_period')}, factor={md.get('skipped_missing_factor')}, "
                f"sm={md.get('skipped_missing_sm')}, w_missing={md.get('skipped_missing_weight')}, "
                f"w_invalid={md.get('skipped_invalid_weight')})"
            )
        print()


def _print_dashboard_pretty(payload: Dict[str, object], *, no_color: bool = False) -> None:
    use_color = _supports_color(no_color=no_color)
    title_style = "1;38;5;46"
    print(_brazil_flag_strip(use_color))
    header = [
        _colorize("PNAD DASHBOARD ECONOMICO", title_style, use_color),
        f"Entrada: {payload.get('input')}",
        f"Target: {payload.get('target')} | SM alvo: {payload.get('sm_target_value')} (mes {payload.get('sm_target_month')})",
        f"Peso: {payload.get('weighting_mode')} ({payload.get('weight_col') or 'N/A'}) | Renda: {payload.get('income_col')}",
    ]
    md = payload.get("metadata", {})
    if isinstance(md, dict):
        header.append(
            f"Cobertura: {md.get('states_covered')} UFs | {md.get('households')} domicilios | linhas lidas={md.get('rows_read')}"
        )
        dims = md.get("dimensions", [])
        if isinstance(dims, list):
            header.append(f"Recortes ativos: {', '.join(str(x) for x in dims)}")
    _panel("Panorama Geral", header, color="1;38;5;46", use_color=use_color)
    print("")

    for mode in payload.get("modes", {}).keys():
        _print_dashboard_mode(payload, mode, no_color=no_color)


def _run_dashboard_interactive(payload: Dict[str, object], *, no_color: bool = False) -> None:
    modes = list(payload.get("modes", {}).keys())
    if not modes:
        return
    idx = 0
    section = "all"
    while True:
        mode = modes[idx]
        print("\n" + "=" * 90)
        _print_dashboard_mode(payload, mode, no_color=no_color, section=section)
        print(
            "[n] proximo modo | [p] modo anterior | [1] overview | [2] ranking | "
            "[3] macro | [4] population | [5] demography | [6] cross | [7] meta | [8] insights | [a] all | [q] sair"
        )
        try:
            ans = input("> ").strip().lower()
        except EOFError:
            return
        if ans in ("q", "quit", "exit"):
            return
        if ans in ("n", "next"):
            idx = (idx + 1) % len(modes)
            continue
        if ans in ("p", "prev", "anterior"):
            idx = (idx - 1) % len(modes)
            continue
        if ans in ("a", "all", "dashboard"):
            section = "all"
            continue
        if ans == "1":
            section = "overview"
            continue
        if ans == "2":
            section = "ranking"
            continue
        if ans == "3":
            section = "macro"
            continue
        if ans == "4":
            section = "population"
            continue
        if ans == "5":
            section = "demography"
            continue
        if ans == "6":
            section = "cross"
            continue
        if ans == "7":
            section = "meta"
            continue
        if ans == "8":
            section = "insights"
            continue


def cmd_dashboard(args: argparse.Namespace) -> int:
    try:
        payload = _build_dashboard_payload(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if args.interactive:
        _run_dashboard_interactive(payload, no_color=args.no_color)
    else:
        _print_dashboard_pretty(payload, no_color=args.no_color)
    return 0


def cmd_ibge_sync(args: argparse.Namespace) -> int:
    base_url = args.base_url.rstrip("/") + "/"
    raw_dir = Path(args.raw_dir)
    docs_dir = Path(args.docs_dir)
    manifest_path = Path(args.manifest)
    manifest = _read_json(manifest_path)
    if not isinstance(manifest, dict):
        manifest = {}
    files_meta = manifest.get("files", {})
    if not isinstance(files_meta, dict):
        files_meta = {}
    sync_events: List[Dict[str, object]] = []

    def sync_one(url: str, destination: Path) -> Dict[str, object]:
        prev = files_meta.get(url, {}) if isinstance(files_meta.get(url, {}), dict) else {}
        result = _download_if_changed(url, destination, previous_meta=prev, force=args.force, quiet=args.quiet)
        files_meta[url] = {
            "path": str(destination),
            "etag": str(result.get("meta", {}).get("etag", "")),
            "last_modified": str(result.get("meta", {}).get("last_modified", "")),
            "content_length": str(result.get("meta", {}).get("content_length", "")),
        }
        event = {
            "url": url,
            "path": str(destination),
            "status": result.get("status", "unknown"),
        }
        sync_events.append(event)
        return event

    selected_year: Optional[int] = None
    selected_raw_files: List[str] = []
    extracted_txt: List[str] = []

    try:
        root_hrefs = _list_hrefs(base_url)
    except Exception as exc:
        print(f"ERROR: could not list IBGE base URL: {exc}", file=sys.stderr)
        return 2

    if not args.no_docs:
        top_docs = [
            h
            for h in root_hrefs
            if h != "Documentacao/" and not h.endswith("/") and not h.lower().endswith(".zip")
        ]
        for name in sorted(top_docs):
            sync_one(base_url + name, docs_dir / name)

        doc_hrefs = _list_hrefs(base_url + "Documentacao/")
        doc_files = [h for h in doc_hrefs if not h.endswith("/")]
        for name in sorted(doc_files):
            sync_one(base_url + "Documentacao/" + name, docs_dir / name)

        if not args.no_extract and (docs_dir / "Dicionario_e_input_20221031.zip").exists():
            with zipfile.ZipFile(docs_dir / "Dicionario_e_input_20221031.zip") as zf:
                for member in zf.namelist():
                    if member.endswith("/"):
                        continue
                    target = docs_dir / Path(member).name
                    tmp = target.with_name(target.name + ".tmp")
                    with zf.open(member, "r") as src, tmp.open("wb") as dst:
                        shutil.copyfileobj(src, dst, length=1024 * 1024)
                    tmp.replace(target)

        # Refresh monthly nominal minimum wage series (BCB SGS 1619).
        # This feeds income-by-minimum-wage analytics in `renda-por-faixa-sm`.
        mw_rows = _fetch_json(BCB_SALARIO_MINIMO_URL)
        if not isinstance(mw_rows, list):
            raise ValueError("unexpected response while fetching salario minimo series")
        mw_out = docs_dir / "salario_minimo.csv"
        with mw_out.open("w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["date", "value"])
            for row in mw_rows:
                if not isinstance(row, dict):
                    continue
                d = str(row.get("data", "")).strip()
                v = str(row.get("valor", "")).strip()
                if not d or not v:
                    continue
                try:
                    dd, mm, yyyy = d.split("/")
                except ValueError:
                    continue
                ym = f"{yyyy}-{mm}"
                fv = _parse_float(v)
                if fv is None:
                    continue
                w.writerow([ym, f"{float(fv):.2f}"])
        sync_events.append(
            {
                "url": BCB_SALARIO_MINIMO_URL,
                "path": str(mw_out),
                "status": "downloaded",
            }
        )

    if not args.no_raw:
        years = sorted(
            int(h.rstrip("/")) for h in root_hrefs if re.match(r"^\d{4}/$", h) and h.rstrip("/").isdigit()
        )
        if not years:
            print("ERROR: no year folders found in IBGE Microdados index", file=sys.stderr)
            return 2
        selected_year = int(args.year) if args.year else years[-1]
        if selected_year not in years:
            print(f"ERROR: year {selected_year} not available on IBGE index", file=sys.stderr)
            return 2

        year_url = f"{base_url}{selected_year}/?C=N;O=D"
        year_hrefs = _list_hrefs(year_url)
        zip_names = sorted({h for h in year_hrefs if PNADC_ZIP_RE.match(h)})
        latest_by_quarter = _group_latest_by_quarter(zip_names)
        if not latest_by_quarter:
            print(f"ERROR: no PNADC zip files found for year {selected_year}", file=sys.stderr)
            return 2

        if args.quarter:
            q = int(args.quarter)
            pick = latest_by_quarter.get(q)
            if not pick:
                print(f"ERROR: no file for quarter {q} in year {selected_year}", file=sys.stderr)
                return 2
            to_download = [str(pick["name"])]
        elif args.all_in_year:
            to_download = [str(latest_by_quarter[q]["name"]) for q in sorted(latest_by_quarter)]
        else:
            latest_q = max(latest_by_quarter)
            to_download = [str(latest_by_quarter[latest_q]["name"])]

        for file_name in to_download:
            selected_raw_files.append(file_name)
            zip_url = f"{base_url}{selected_year}/{file_name}"
            zip_dest = raw_dir / file_name
            sync_event = sync_one(zip_url, zip_dest)
            if not args.no_extract and zip_dest.exists():
                txt_path = _extract_single_txt(zip_dest, raw_dir, quiet=args.quiet)
                if txt_path:
                    extracted_txt.append(str(txt_path))
                    sync_events.append(
                        {
                            "url": zip_url,
                            "path": str(txt_path),
                            "status": "extracted" if sync_event["status"] == "downloaded" else "present",
                        }
                    )

    manifest = {
        "updated_at_utc": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "base_url": base_url,
        "files": files_meta,
    }
    _json_dump(manifest_path, manifest)

    payload = {
        "base_url": base_url,
        "year": selected_year,
        "raw_files": selected_raw_files,
        "raw_txt": extracted_txt,
        "docs_dir": str(docs_dir),
        "raw_dir": str(raw_dir),
        "manifest": str(manifest_path),
        "events": sync_events,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_download_pnadc(args: argparse.Namespace) -> int:
    if not args.url:
        print("ERROR: --url is required for download-pnadc", file=sys.stderr)
        return 2

    filename = args.filename
    if not filename:
        parsed = urlparse(args.url)
        filename = Path(parsed.path).name
        if not filename:
            print("ERROR: could not infer filename from URL; use --filename", file=sys.stderr)
            return 2

    dest = Path(args.dest_dir) / filename
    try:
        out = _download(args.url, dest, force=args.force, quiet=args.quiet)
    except FileExistsError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"downloaded": str(out)}, ensure_ascii=False))
    return 0


def cmd_download_news(args: argparse.Namespace) -> int:
    req = Request(args.url, headers={"User-Agent": "pnad-cli/1.0"})
    with urlopen(req, timeout=120) as resp:
        xml_text = resp.read().decode("utf-8", errors="replace")

    root = ET.fromstring(xml_text)
    items = []
    query = args.query.lower().strip()

    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        desc = (item.findtext("description") or "").strip()
        blob = f"{title}\n{desc}".lower()
        if query and query not in blob:
            continue
        items.append({"title": title, "link": link, "pub_date": pub_date})
        if args.limit and len(items) >= args.limit:
            break

    out_path = Path(args.out)
    _json_dump(out_path, {"source": args.url, "query": args.query, "items": items})
    print(json.dumps({"news_file": str(out_path), "items": len(items)}, ensure_ascii=False))
    return 0


def cmd_renda_por_faixa_sm(args: argparse.Namespace) -> int:
    try:
        ranges = _parse_ranges(args.ranges)
    except Exception as exc:
        print(f"ERROR: invalid --ranges: {exc}", file=sys.stderr)
        return 2

    try:
        from npv_deflators import build_deflators, read_ipca_csv  # type: ignore
    except Exception as exc:
        print(f"ERROR: could not import deflator helpers: {exc}", file=sys.stderr)
        return 2

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: input file not found: {input_path}", file=sys.stderr)
        return 2

    try:
        ipca_index = read_ipca_csv(Path(args.ipca_csv))
    except Exception as exc:
        print(f"ERROR: failed to read ipca csv: {exc}", file=sys.stderr)
        return 2

    target = args.target.strip() if args.target else _latest_target_month(ipca_index)
    try:
        factor_map = build_deflators(ipca_index, target)
    except Exception as exc:
        print(f"ERROR: failed to build deflators: {exc}", file=sys.stderr)
        return 2

    try:
        sal_min = _read_salario_minimo_csv(Path(args.salario_minimo_csv))
    except Exception as exc:
        print(f"ERROR: failed to read salario minimo csv: {exc}", file=sys.stderr)
        return 2

    uf_filter: set[str] = set()
    if args.state:
        uf_filter = {_norm_text(x) for x in args.state.split(",") if x.strip()}

    sampled_rows = 0
    skipped_missing_period = 0
    skipped_missing_sm = 0
    skipped_missing_factor = 0
    skipped_missing_weight = 0
    skipped_invalid_weight = 0
    inconsistent_household_weight = 0

    households: Dict[str, Dict[str, object]] = {}
    selected_income_col = ""
    selected_weight_col: Optional[str] = None

    try:
        with input_path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fh:
            r = csv.DictReader(fh)
            headers = r.fieldnames or []
            if not headers:
                raise ValueError("input has no header")

            dom_col = _find_col(headers, "dom_id", "dom_id")
            year_col = _find_col(headers, "Ano__", "Ano")
            qtr_col = _find_col(headers, "Trimestre__", "Trimestre")
            uf_col = _find_col(headers, "UF__", "UF")
            uf_label_col = _find_col(headers, "UF_label", "UF_label")
            income_col = _detect_income_col(headers, args.income_col)
            selected_income_col = income_col
            selected_weight_col = None if args.unweighted else _detect_weight_col(headers, args.weight_col)

            if not dom_col:
                raise ValueError("input must contain dom_id (run fwf-extract with dom_id)")
            if not year_col or not qtr_col:
                raise ValueError("input must contain Ano and Trimestre columns")
            if not uf_col:
                raise ValueError("input must contain UF column")
            if not args.unweighted and not selected_weight_col:
                raise ValueError(
                    "weight column not found. Re-run pipeline including V1028 "
                    "or pass --weight-col / use --unweighted for diagnostics."
                )

            for row in r:
                sampled_rows += 1
                dom = str(row.get(dom_col, "")).strip()
                if not dom:
                    continue

                y_raw = str(row.get(year_col, "")).strip()
                q_raw = str(row.get(qtr_col, "")).strip()
                try:
                    year = int(y_raw)
                    quarter = int(q_raw)
                    month = _quarter_to_month(quarter)
                except Exception:
                    skipped_missing_period += 1
                    continue
                ym = f"{year}-{month:02d}"

                factor = factor_map.get(ym)
                if factor is None:
                    skipped_missing_factor += 1
                    continue

                sm_nominal = sal_min.get(ym)
                if sm_nominal is None:
                    skipped_missing_sm += 1
                    continue

                uf_code = str(row.get(uf_col, "")).strip()
                uf_label = str(row.get(uf_label_col, "")).strip() if uf_label_col else ""
                if uf_filter:
                    if _norm_text(uf_code) not in uf_filter and _norm_text(uf_label) not in uf_filter:
                        continue

                row_weight = 1.0
                if selected_weight_col:
                    raw_w = row.get(selected_weight_col, "")
                    if raw_w in (None, ""):
                        skipped_missing_weight += 1
                        continue
                    row_weight_parsed = _parse_float(raw_w)
                    if row_weight_parsed is None:
                        skipped_invalid_weight += 1
                        continue
                    if row_weight_parsed <= 0:
                        skipped_invalid_weight += 1
                        continue
                    row_weight = float(row_weight_parsed)

                income_nominal = _parse_float(row.get(income_col, ""))
                if income_nominal is None:
                    income_nominal = 0.0

                st = households.get(dom)
                if st is None:
                    st = {
                        "dom_id": dom,
                        "uf_code": uf_code,
                        "uf_label": uf_label,
                        "persons": 0,
                        "income_target": 0.0,
                        "sm_target": float(sm_nominal) * float(factor),
                        "household_weight": row_weight,
                        "persons_weight": 0.0,
                        "ym": ym,
                    }
                    households[dom] = st

                st["persons"] = int(st["persons"]) + 1
                st["income_target"] = float(st["income_target"]) + float(income_nominal) * float(factor)
                st["persons_weight"] = float(st["persons_weight"]) + row_weight
                hw = float(st.get("household_weight") or row_weight)
                if abs(hw - row_weight) > 1e-6:
                    inconsistent_household_weight += 1
                    st["household_weight"] = hw

    except Exception as exc:
        print(f"ERROR: failed while reading input: {exc}", file=sys.stderr)
        return 2

    group_mode = args.group_by
    by_group: Dict[str, Dict[str, object]] = {}
    for h in households.values():
        uf_code = str(h.get("uf_code", "")).strip()
        uf_label = str(h.get("uf_label", "")).strip()
        if group_mode == "uf":
            gkey = uf_code or "UF?"
            gname = uf_label or uf_code or "UF?"
        else:
            gkey = "BR"
            gname = "Brasil"

        g = by_group.get(gkey)
        if g is None:
            g = {
                "group": gkey,
                "label": gname,
                "households_total": 0.0,
                "persons_total": 0.0,
                "households_sample": 0,
                "persons_sample": 0,
                "sum_ratio_household_weighted": 0.0,
                "bands": {str(item["label"]): {"households": 0, "persons": 0} for item in ranges},
            }
            by_group[gkey] = g

        sm_target = float(h.get("sm_target") or 0.0)
        if sm_target <= 0:
            continue
        income_target = float(h.get("income_target") or 0.0)
        ratio_sm = income_target / sm_target
        band = _classify_range(ratio_sm, ranges)
        persons = int(h.get("persons") or 0)
        persons_weight = float(h.get("persons_weight") or 0.0)
        household_weight = float(h.get("household_weight") or 1.0)

        g["households_sample"] = int(g["households_sample"]) + 1
        g["persons_sample"] = int(g["persons_sample"]) + persons

        if args.unweighted:
            hh_inc = 1.0
            pp_inc = float(persons)
        else:
            hh_inc = household_weight
            pp_inc = persons_weight

        g["households_total"] = float(g["households_total"]) + hh_inc
        g["persons_total"] = float(g["persons_total"]) + pp_inc
        g["sum_ratio_household_weighted"] = float(g["sum_ratio_household_weighted"]) + (ratio_sm * hh_inc)
        gband = g["bands"][band]
        gband["households"] = float(gband["households"]) + hh_inc
        gband["persons"] = float(gband["persons"]) + pp_inc

    if group_mode == "uf":
        order = args.uf_order
        if order == "alfabetica":
            group_keys = sorted(by_group.keys(), key=lambda k: str(by_group[k].get("label", "")).lower())
        elif order == "codigo":
            group_keys = sorted(by_group.keys())
        elif order == "renda_asc":
            group_keys = sorted(
                by_group.keys(),
                key=lambda k: (
                    float(by_group[k].get("sum_ratio_household_weighted", 0.0) or 0.0)
                    / max(float(by_group[k].get("households_total", 0.0) or 0.0), 1e-12)
                ),
            )
        else:
            group_keys = sorted(
                by_group.keys(),
                key=lambda k: (
                    float(by_group[k].get("sum_ratio_household_weighted", 0.0) or 0.0)
                    / max(float(by_group[k].get("households_total", 0.0) or 0.0), 1e-12)
                ),
                reverse=True,
            )
    else:
        group_keys = sorted(by_group.keys())

    groups_out: List[Dict[str, object]] = []
    for gkey in group_keys:
        g = by_group[gkey]
        htot = float(g["households_total"]) or 0.0
        ptot = float(g["persons_total"]) or 0.0
        avg_household_sm = (
            float(g["sum_ratio_household_weighted"]) / htot if htot else 0.0
        )
        bands_out = []
        for item in ranges:
            label = str(item["label"])
            b = g["bands"][label]
            bh = float(b["households"])
            bp = float(b["persons"])
            bands_out.append(
                {
                    "range": label,
                    "households": bh,
                    "households_pct": round((100.0 * bh / htot), 4) if htot else 0.0,
                    "persons": bp,
                    "persons_pct": round((100.0 * bp / ptot), 4) if ptot else 0.0,
                }
            )
        groups_out.append(
            {
                "group": g["group"],
                "label": g["label"],
                "households_total": htot,
                "persons_total": ptot,
                "households_sample": int(g["households_sample"]),
                "persons_sample": int(g["persons_sample"]),
                "avg_household_sm": round(avg_household_sm, 6),
                "bands": bands_out,
            }
        )

    sm_ref_weighted_sum = 0.0
    sm_ref_weight_total = 0.0
    sm_ref_min: Optional[float] = None
    sm_ref_max: Optional[float] = None
    for h in households.values():
        sm_target = float(h.get("sm_target") or 0.0)
        if sm_target <= 0:
            continue
        hh_w = 1.0 if args.unweighted else float(h.get("household_weight") or 1.0)
        sm_ref_weighted_sum += sm_target * hh_w
        sm_ref_weight_total += hh_w
        sm_ref_min = sm_target if sm_ref_min is None else min(sm_ref_min, sm_target)
        sm_ref_max = sm_target if sm_ref_max is None else max(sm_ref_max, sm_target)
    sm_reference_value = _safe_div(sm_ref_weighted_sum, sm_ref_weight_total)
    ranges_money = _ranges_money_from_specs(ranges, sm_reference_value if sm_reference_value > 0 else 0.0)

    payload = {
        "input": str(input_path),
        "income_col": selected_income_col or (args.income_col or "auto(VD4020->VD4019)"),
        "weight_col": selected_weight_col if not args.unweighted else None,
        "weighting_mode": "unweighted" if args.unweighted else "weighted",
        "target": target,
        "sm_reference_value": round(float(sm_reference_value), 2),
        "sm_reference_mode": "periodo_deflacionado",
        "sm_reference_min": None if sm_ref_min is None else round(float(sm_ref_min), 2),
        "sm_reference_max": None if sm_ref_max is None else round(float(sm_ref_max), 2),
        "group_by": group_mode,
        "uf_order": args.uf_order if group_mode == "uf" else None,
        "ranges": [str(x["label"]) for x in ranges],
        "range_specs": [
            {
                "label": str(x["label"]),
                "min": float(x["min"]),
                "max": None if x["max"] is None else float(x["max"]),
            }
            for x in ranges
        ],
        "ranges_money": ranges_money,
        "groups": groups_out,
        "metadata": {
            "rows_read": sampled_rows,
            "households": len(households),
            "skipped_missing_period": skipped_missing_period,
            "skipped_missing_factor": skipped_missing_factor,
            "skipped_missing_sm": skipped_missing_sm,
            "skipped_missing_weight": skipped_missing_weight,
            "skipped_invalid_weight": skipped_invalid_weight,
            "inconsistent_household_weight_rows": inconsistent_household_weight,
            "ipca_csv": str(args.ipca_csv),
            "salario_minimo_csv": str(args.salario_minimo_csv),
            "method_income": "sum of individual income by dom_id",
            "method_ratio": "household_income_deflated / salario_minimo_deflated",
            "weights": "weighted by V1028/V1027 unless --unweighted",
        },
    }

    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        _print_renda_pretty(payload, no_color=args.no_color)
    return 0


def _is_int(value: str) -> bool:
    s = value.strip()
    if not s:
        return False
    if s.startswith(("+", "-")):
        s = s[1:]
    return s.isdigit()


def _is_float(value: str) -> bool:
    s = value.strip().replace(",", ".")
    if not s:
        return False
    try:
        float(s)
        return True
    except Exception:
        return False


def _infer_column_types(csv_path: Path, sample_rows: int = 5000) -> Dict[str, str]:
    with csv_path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fh:
        reader = csv.DictReader(fh)
        columns = reader.fieldnames or []
        states: Dict[str, str] = {c: "INTEGER" for c in columns}
        nonempty: Dict[str, int] = {c: 0 for c in columns}

        for i, row in enumerate(reader):
            if i >= sample_rows:
                break
            for col in columns:
                raw = str(row.get(col, "")).strip()
                if raw == "":
                    continue
                nonempty[col] += 1
                if states[col] == "TEXT":
                    continue
                if states[col] == "INTEGER":
                    if _is_int(raw):
                        continue
                    if _is_float(raw):
                        states[col] = "REAL"
                    else:
                        states[col] = "TEXT"
                    continue
                if states[col] == "REAL":
                    if not _is_float(raw):
                        states[col] = "TEXT"

        for col in columns:
            if nonempty[col] == 0:
                states[col] = "TEXT"

        return states


def _quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def build_sqlite_from_csv(
    csv_path: Path,
    db_path: Path,
    *,
    table: str,
    if_exists: str = "replace",
    chunk_size: int = 5000,
    index_columns: Optional[Sequence[str]] = None,
) -> Dict[str, object]:
    csv_path = Path(csv_path)
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    inferred = _infer_column_types(csv_path)
    columns = list(inferred.keys())
    if not columns:
        raise ValueError("CSV has no columns")

    qtable = _quote_ident(table)
    col_defs = ", ".join(f"{_quote_ident(c)} {inferred[c]}" for c in columns)
    col_names = ", ".join(_quote_ident(c) for c in columns)
    placeholders = ", ".join(["?"] * len(columns))
    insert_sql = f"INSERT INTO {qtable} ({col_names}) VALUES ({placeholders})"

    with sqlite3.connect(db_path) as conn:
        if if_exists == "replace":
            conn.execute(f"DROP TABLE IF EXISTS {qtable}")
        elif if_exists == "fail":
            exists = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                (table,),
            ).fetchone()
            if exists:
                raise ValueError(f"Table already exists: {table}")

        conn.execute(f"CREATE TABLE IF NOT EXISTS {qtable} ({col_defs})")

        with csv_path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fh:
            reader = csv.DictReader(fh)
            batch: List[tuple] = []
            total = 0
            for row in reader:
                batch.append(tuple(row.get(c, "") for c in columns))
                if len(batch) >= chunk_size:
                    conn.executemany(insert_sql, batch)
                    total += len(batch)
                    batch = []
            if batch:
                conn.executemany(insert_sql, batch)
                total += len(batch)

        for col in index_columns or ():
            if col not in columns:
                continue
            idx_name = f"idx_{table}_{col}".replace(" ", "_")
            conn.execute(
                f"CREATE INDEX IF NOT EXISTS {_quote_ident(idx_name)} "
                f"ON {qtable} ({_quote_ident(col)})"
            )
        conn.commit()

    return {
        "db": str(db_path),
        "table": table,
        "rows": total,
        "columns": len(columns),
    }


def cmd_sqlite_build(args: argparse.Namespace) -> int:
    try:
        result = build_sqlite_from_csv(
            Path(args.input),
            Path(args.db),
            table=args.table,
            if_exists=args.if_exists,
            chunk_size=args.chunk_size,
            index_columns=[c.strip() for c in args.indexes.split(",") if c.strip()],
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result, ensure_ascii=False))
    return 0


def _run_capture_stdout(cmd: Sequence[str], out_file: Path, quiet: bool = False) -> None:
    out_file.parent.mkdir(parents=True, exist_ok=True)
    _print("$ " + " ".join(cmd), quiet=quiet)
    with out_file.open("w", encoding="utf-8", newline="") as fh:
        subprocess.run(cmd, check=True, stdout=fh)


def _run_cmd(cmd: Sequence[str], quiet: bool = False) -> None:
    _print("$ " + " ".join(cmd), quiet=quiet)
    subprocess.run(cmd, check=True)


def cmd_pipeline_run(args: argparse.Namespace) -> int:
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.download_url:
        fallback_name = "PNADC_download.txt"
        if str(args.raw).strip().lower() != "latest":
            fallback_name = Path(args.raw).name
        filename = args.filename or Path(urlparse(args.download_url).path).name or fallback_name
        raw_path: Optional[Path] = out_dir / filename
    elif str(args.raw).strip().lower() == "latest":
        latest = _latest_local_raw(Path(args.raw_dir))
        if latest is None:
            print(
                f"ERROR: no local raw PNADC file found under {args.raw_dir}. "
                "Run `pnad ibge-sync` first or pass --raw PATH.",
                file=sys.stderr,
            )
            return 2
        raw_path = latest
    else:
        raw_path = Path(args.raw)

    if args.download_url:
        assert raw_path is not None
        raw_path = out_dir / filename
        try:
            _download(args.download_url, raw_path, force=args.force_download, quiet=args.quiet)
        except Exception as exc:
            print(f"ERROR: download failed: {exc}", file=sys.stderr)
            return 2

    if raw_path is None or not raw_path.exists():
        print(f"ERROR: raw file not found: {raw_path}", file=sys.stderr)
        return 2

    try:
        rc = pnadc_cli.cmd_emit_codes(argparse.Namespace(out=out_dir))
        if rc != 0:
            return rc

        base_csv = out_dir / "base.csv"
        labeled_csv = out_dir / "base_labeled.csv"
        npv_csv = out_dir / "base_labeled_npv.csv"
        ipca_csv = Path(args.ipca_csv)

        fwf_cmd = [
            sys.executable,
            str(SCRIPT_DIR / "pnadc_cli.py"),
            "fwf-extract",
            str(args.layout),
            str(raw_path),
            "--header",
            "--name-style",
            args.name_style,
        ]
        if args.keep:
            fwf_cmd.extend(["--keep", args.keep])
        _run_capture_stdout(fwf_cmd, base_csv, quiet=args.quiet)

        join_cmd = [
            sys.executable,
            str(SCRIPT_DIR / "pnadc_cli.py"),
            "join-codes",
            str(base_csv),
            "--codes-dir",
            str(out_dir),
        ]
        _run_capture_stdout(join_cmd, labeled_csv, quiet=args.quiet)

        if not args.skip_ipca_fetch or not ipca_csv.exists():
            _run_cmd(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "fetch_ipca.py"),
                    "--out",
                    str(ipca_csv),
                ],
                quiet=args.quiet,
            )

        try:
            target_for_npv, min_wage_for_npv, min_wage_month_used = _resolve_pipeline_target_and_min_wage(
                target_arg=args.target,
                min_wage_arg=args.min_wage,
                ipca_csv=ipca_csv,
                salario_minimo_csv=Path(args.salario_minimo_csv),
            )
        except Exception as exc:
            print(f"ERROR: failed to resolve target/minimum wage: {exc}", file=sys.stderr)
            return 2
        _print(
            f"Using NPV target={target_for_npv} and min_wage={min_wage_for_npv:.2f} "
            f"(source month: {min_wage_month_used})",
            quiet=args.quiet,
        )

        _run_cmd(
            [
                sys.executable,
                str(SCRIPT_DIR / "npv_deflators.py"),
                "apply",
                "--in",
                str(labeled_csv),
                "--out",
                str(npv_csv),
                "--ipca-csv",
                str(ipca_csv),
                "--target",
                target_for_npv,
                "--min-wage",
                str(min_wage_for_npv),
            ],
            quiet=args.quiet,
        )

        sqlite_info = None
        if args.sqlite:
            sqlite_info = build_sqlite_from_csv(
                npv_csv,
                Path(args.sqlite),
                table=args.table,
                if_exists=args.if_exists,
                chunk_size=args.chunk_size,
                index_columns=[c.strip() for c in args.indexes.split(",") if c.strip()],
            )

        manifest = {
            "raw": str(raw_path),
            "base_csv": str(base_csv),
            "base_labeled_csv": str(labeled_csv),
            "base_labeled_npv_csv": str(npv_csv),
            "ipca_csv": str(ipca_csv),
            "target": target_for_npv,
            "min_wage": min_wage_for_npv,
            "min_wage_source_month": min_wage_month_used,
            "salario_minimo_csv": str(args.salario_minimo_csv),
            "sqlite": sqlite_info,
        }
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
        return 0
    except subprocess.CalledProcessError as exc:
        print(f"ERROR: pipeline command failed with exit code {exc.returncode}", file=sys.stderr)
        return int(exc.returncode or 1)
    except Exception as exc:
        print(f"ERROR: pipeline failed: {exc}", file=sys.stderr)
        return 2


def cmd_help_legacy(args: argparse.Namespace) -> int:
    parser = pnadc_cli.build_parser()
    parser.print_help()
    return 0


def build_parser() -> argparse.ArgumentParser:
    description = (
        "PNAD automation CLI. Use this tool to download inputs, refresh IPCA, rerun the pipeline, "
        "and rebuild SQLite outputs."
    )
    epilog = """Examples:
  pnad --help
  pnad help-legacy
  pnad ibge-sync
  pnad ibge-sync --year 2025 --quarter 3
  pnad download-pnadc --url https://host/PNADC_022025.txt --dest-dir data/raw
  pnad download-news --query PNAD --out data/news_pnad.json
  pnad renda-por-faixa-sm --input data/outputs/base_labeled.csv --group-by uf --ranges "0-2;2-5;5-10;10+"
  pnad dashboard --input data/outputs/base_labeled.csv --sm-mode both
  pnad renda-por-faixa-sm --input data/outputs/base_labeled.csv --format json
  pnad pipeline-run --raw latest --layout data/originals/input_PNADC_trimestral.sas --sqlite data/outputs/pnad.sqlite
  pnad sqlite-build --input data/outputs/base_labeled_npv.csv --db data/outputs/pnad.sqlite --table base_labeled_npv

Legacy commands still work directly:
  pnad inspect data/outputs/base_labeled.csv
  pnad fwf-extract data/originals/input_PNADC_trimestral.sas data/raw/PNADC_032025.txt --header > data/outputs/base.csv
"""

    p = argparse.ArgumentParser(
        prog="pnad",
        description=description,
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    sub = p.add_subparsers(dest="cmd")

    ph = sub.add_parser("help-legacy", help="Show --help for legacy data-processing commands")
    ph.set_defaults(func=cmd_help_legacy)

    pdl = sub.add_parser("download-pnadc", help="Download a PNADC raw file to a local directory")
    pdl.add_argument("--url", help="Source URL for the PNADC file")
    pdl.add_argument("--filename", help="Optional target filename (default from URL path)")
    pdl.add_argument("--dest-dir", default="data/raw", help="Target directory (default: data/raw)")
    pdl.add_argument("--force", action="store_true", help="Overwrite destination if it already exists")
    pdl.add_argument("--quiet", action="store_true", help="Reduce command output")
    pdl.set_defaults(func=cmd_download_pnadc)

    pnews = sub.add_parser("download-news", help="Download and filter RSS news entries into JSON")
    pnews.add_argument("--url", default="https://www.ibge.gov.br/rss.xml", help="RSS feed URL")
    pnews.add_argument("--query", default="PNAD", help="Case-insensitive keyword filter")
    pnews.add_argument("--limit", type=int, default=30, help="Maximum number of entries")
    pnews.add_argument("--out", default="data/news_pnad.json", help="Output JSON file")
    pnews.set_defaults(func=cmd_download_news)

    prf = sub.add_parser(
        "renda-por-faixa-sm",
        help="Estimate household income distribution by minimum-wage ranges (Brazil or UF)",
    )
    prf.add_argument("--input", default="data/outputs/base_labeled.csv", help="Input labeled CSV with dom_id")
    prf.add_argument("--ipca-csv", default="data/outputs/ipca.csv", help="IPCA CSV file path")
    prf.add_argument(
        "--salario-minimo-csv",
        default="data/originals/salario_minimo.csv",
        help="Monthly nominal minimum wage CSV (date,value)",
    )
    prf.add_argument("--target", default="", help="Target month YYYY-MM (default: latest in IPCA series)")
    prf.add_argument(
        "--ranges",
        default="0-2;2-5;5-10;10+",
        help='Band specification. Example: "0-2;2-5;5-10;10+"',
    )
    prf.add_argument(
        "--group-by",
        choices=["pais", "uf"],
        default="pais",
        help="Aggregate output for Brazil total or by state (UF)",
    )
    prf.add_argument(
        "--uf-order",
        choices=["renda_desc", "renda_asc", "alfabetica", "codigo"],
        default="renda_desc",
        help="Order for UF output: richest->poorest (default), poorest->richest, alphabetic, or UF code",
    )
    prf.add_argument("--state", default="", help="Optional UF filter (code or label), comma-separated")
    prf.add_argument(
        "--income-col",
        default=None,
        help="Income column name. Default auto: VD4020 then VD4019",
    )
    prf.add_argument(
        "--weight-col",
        default=None,
        help="Weight column name. Default auto: V1028 then V1027",
    )
    prf.add_argument(
        "--unweighted",
        action="store_true",
        help="Diagnostic mode without sample weights (not for official estimates)",
    )
    prf.add_argument("--format", choices=["pretty", "json"], default="pretty", help="Output format")
    prf.add_argument("--no-color", action="store_true", help="Disable ANSI colors in pretty output")
    prf.set_defaults(func=cmd_renda_por_faixa_sm)

    pdash = sub.add_parser(
        "dashboard",
        help="Terminal dashboard with national/state economic stats, distributions and cross-tabs",
    )
    pdash.add_argument("--input", default="data/outputs/base_labeled.csv", help="Input labeled CSV with dom_id")
    pdash.add_argument("--ipca-csv", default="data/outputs/ipca.csv", help="IPCA CSV file path")
    pdash.add_argument(
        "--salario-minimo-csv",
        default="data/originals/salario_minimo.csv",
        help="Monthly nominal minimum wage CSV (date,value)",
    )
    pdash.add_argument("--target", default="", help="Target month YYYY-MM (default: latest in IPCA series)")
    pdash.add_argument(
        "--sm-mode",
        choices=["both", "periodo", "alvo"],
        default="alvo",
        help="Compare ratios using period SM, target SM, or both (default: alvo)",
    )
    pdash.add_argument(
        "--ranges",
        default="0-2;2-5;5-10;10+",
        help='Band specification. Example: "0-2;2-5;5-10;10+"',
    )
    pdash.add_argument(
        "--uf-order",
        choices=["renda_desc", "renda_asc", "alfabetica", "codigo"],
        default="renda_desc",
        help="Order for UF rankings",
    )
    pdash.add_argument("--state", default="", help="Optional UF filter (code or label), comma-separated")
    pdash.add_argument(
        "--income-col",
        default=None,
        help="Income column name. Default auto: VD4020 then VD4019",
    )
    pdash.add_argument(
        "--weight-col",
        default=None,
        help="Weight column name. Default auto: V1028 then V1027",
    )
    pdash.add_argument(
        "--unweighted",
        action="store_true",
        help="Diagnostic mode without sample weights (not for official estimates)",
    )
    pdash.add_argument("--interactive", action="store_true", help="Interactive navigation in terminal")
    pdash.add_argument("--format", choices=["pretty", "json"], default="pretty", help="Output format")
    pdash.add_argument("--no-color", action="store_true", help="Disable ANSI colors in pretty output")
    pdash.set_defaults(func=cmd_dashboard)

    psync = sub.add_parser("ibge-sync", help="Sync PNADC microdados and documentation from IBGE")
    psync.add_argument("--base-url", default=IBGE_MICRODADOS_BASE, help="IBGE microdados base URL")
    psync.add_argument("--raw-dir", default="data/raw", help="Where to store downloaded PNADC zip/txt files")
    psync.add_argument("--docs-dir", default="data/originals", help="Where to store IBGE documentation files")
    psync.add_argument("--manifest", default="data/originals/ibge_sync_manifest.json", help="Sync metadata file")
    psync.add_argument("--year", type=int, help="Optional year folder (default: latest year available)")
    psync.add_argument("--quarter", type=int, choices=[1, 2, 3, 4], help="Quarter (1-4) inside selected year")
    psync.add_argument("--all-in-year", action="store_true", help="Download latest revision for all quarters in year")
    psync.add_argument("--no-docs", action="store_true", help="Skip documentation sync")
    psync.add_argument("--no-raw", action="store_true", help="Skip PNADC microdados sync")
    psync.add_argument("--no-extract", action="store_true", help="Do not extract zip files after download")
    psync.add_argument("--force", action="store_true", help="Force re-download even when remote is unchanged")
    psync.add_argument("--quiet", action="store_true", help="Reduce command output")
    psync.set_defaults(func=cmd_ibge_sync)

    psq = sub.add_parser("sqlite-build", help="Build or refresh a SQLite table from a CSV file")
    psq.add_argument("--input", required=True, help="Input CSV path")
    psq.add_argument("--db", required=True, help="SQLite DB path")
    psq.add_argument("--table", default="base_labeled_npv", help="Target table name")
    psq.add_argument("--if-exists", choices=["replace", "append", "fail"], default="replace")
    psq.add_argument("--chunk-size", type=int, default=5000, help="Insert batch size")
    psq.add_argument(
        "--indexes",
        default="dom_id,UF__unidade_da_federao,Ano__ano_de_referncia,Trimestre__trimestre_de_referncia",
        help="Comma-separated columns to index when present",
    )
    psq.set_defaults(func=cmd_sqlite_build)

    pr = sub.add_parser("pipeline-run", help="Run the full PNADC refresh pipeline")
    pr.add_argument("--raw", default="latest", help="Local raw PNADC file path or 'latest'")
    pr.add_argument("--raw-dir", default="data/raw", help="Directory used when --raw latest")
    pr.add_argument("--download-url", help="If set, download raw file before processing")
    pr.add_argument("--filename", help="Filename to use when --download-url is set")
    pr.add_argument("--force-download", action="store_true", help="Overwrite downloaded raw file")
    pr.add_argument("--layout", default="data/originals/input_PNADC_trimestral.sas", help="SAS layout file")
    pr.add_argument("--out-dir", default="data/outputs", help="Output directory")
    pr.add_argument("--ipca-csv", default="data/outputs/ipca.csv", help="IPCA CSV file path")
    pr.add_argument(
        "--salario-minimo-csv",
        default="data/originals/salario_minimo.csv",
        help="Monthly nominal minimum wage CSV (date,value) for automatic --min-wage",
    )
    pr.add_argument("--skip-ipca-fetch", action="store_true", help="Reuse existing --ipca-csv if present")
    pr.add_argument("--target", default="", help="NPV target month YYYY-MM (default: latest in IPCA series)")
    pr.add_argument(
        "--min-wage",
        type=float,
        default=None,
        help="Minimum wage for *_mw columns (default: auto from --salario-minimo-csv at target month)",
    )
    pr.add_argument("--name-style", choices=["name", "label", "both"], default="both")
    pr.add_argument("--keep", help="Optional comma-separated keep list for fwf-extract")
    pr.add_argument("--sqlite", default="data/outputs/pnad.sqlite", help="SQLite output file (empty to disable)")
    pr.add_argument("--table", default="base_labeled_npv", help="SQLite table name")
    pr.add_argument("--if-exists", choices=["replace", "append", "fail"], default="replace")
    pr.add_argument("--chunk-size", type=int, default=5000, help="SQLite insert batch size")
    pr.add_argument(
        "--indexes",
        default="dom_id,UF__unidade_da_federao,Ano__ano_de_referncia,Trimestre__trimestre_de_referncia",
        help="Comma-separated columns to index when present",
    )
    pr.add_argument("--quiet", action="store_true", help="Reduce command output")
    pr.set_defaults(func=cmd_pipeline_run)

    return p


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(argv) if argv is not None else sys.argv[1:]

    # Keep existing workflow intact: legacy subcommands can be invoked directly.
    if argv and argv[0] in LEGACY_COMMANDS:
        return int(pnadc_cli.main(argv) or 0)

    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.cmd:
        parser.print_help()
        return 0

    return int(args.func(args) or 0)


if __name__ == "__main__":
    raise SystemExit(main())
