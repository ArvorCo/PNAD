#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime
import json
import math
import os
import re
import shutil
import ssl
import sqlite3
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
import zipfile
from collections import defaultdict
from pathlib import Path
from statistics import NormalDist
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus, urlparse
from urllib.request import Request, urlopen

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
IBGE_ANUAL_VISITA5_BASE = (
    "https://ftp.ibge.gov.br/Trabalho_e_Rendimento/"
    "Pesquisa_Nacional_por_Amostra_de_Domicilios_continua/Anual/Microdados/Visita/Visita_5/"
)
IBGE_CENSO_2022_BASE = "https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/"
IBGE_CENSO_RENDA_RESP_FOLDER = "Agregados_por_Setores_Censitarios_Rendimento_do_Responsavel/"
TSE_CKAN_BASE = "https://dadosabertos.tse.jus.br"
TSE_DEFAULT_QUERY = "perfil eleitorado"
TOOL_USER_AGENT = "brasil-cli/1.0"
PNADC_ZIP_RE = re.compile(r"^PNADC_(0[1-4])(\d{4})(?:_(\d{8}))?\.zip$", re.IGNORECASE)
PNADC_ANUAL_VISITA5_ZIP_RE = re.compile(r"^PNADC_(\d{4})_visita5(?:_(\d{8}))?\.zip$", re.IGNORECASE)
PNADC_ANUAL_VISITA5_TXT_RE = re.compile(r"^PNADC_(\d{4})_visita5(?:_(\d{8}))?\.txt$", re.IGNORECASE)
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
REPLICATE_WEIGHT_BASE_RE = re.compile(r"^V1028(\d{3})$")


def _print(msg: str, quiet: bool = False) -> None:
    if not quiet:
        print(msg)


def _urlopen_retry_ssl(req: Request, *, timeout: int = 120):
    """Fallback to unverified SSL context when local trust store is broken."""
    try:
        return urlopen(req, timeout=timeout)
    except URLError as exc:
        reason = getattr(exc, "reason", None)
        if isinstance(reason, ssl.SSLCertVerificationError):
            ctx = ssl._create_unverified_context()
            return urlopen(req, timeout=timeout, context=ctx)
        raise


def _download(url: str, destination: Path, *, force: bool = False, quiet: bool = False) -> Path:
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and not force:
        raise FileExistsError(f"Destination already exists: {destination}")

    _print(f"Downloading {url} -> {destination}", quiet=quiet)
    req = Request(url, headers={"User-Agent": TOOL_USER_AGENT})
    with _urlopen_retry_ssl(req, timeout=120) as resp, destination.open("wb") as fh:
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
    req = Request(url, headers={"User-Agent": TOOL_USER_AGENT})
    with _urlopen_retry_ssl(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _fetch_json(url: str, *, timeout: int = 120) -> object:
    req = Request(url, headers={"User-Agent": TOOL_USER_AGENT})
    with _urlopen_retry_ssl(req, timeout=timeout) as resp:
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


def _parse_pnadc_anual_visita5_zip_name(name: str) -> Optional[Dict[str, object]]:
    m = PNADC_ANUAL_VISITA5_ZIP_RE.match(name)
    if not m:
        return None
    year = int(m.group(1))
    revision = m.group(2) or ""
    return {"name": name, "year": year, "revision": revision}


def _parse_pnadc_anual_visita5_txt_name(name: str) -> Optional[Dict[str, object]]:
    m = PNADC_ANUAL_VISITA5_TXT_RE.match(name)
    if not m:
        return None
    year = int(m.group(1))
    revision = m.group(2) or ""
    return {"name": name, "year": year, "revision": revision}


def _group_latest_anual_by_year(file_names: Sequence[str]) -> Dict[int, Dict[str, object]]:
    latest: Dict[int, Dict[str, object]] = {}
    for name in file_names:
        parsed = _parse_pnadc_anual_visita5_zip_name(name)
        if parsed is None:
            continue
        y = int(parsed["year"])
        prev = latest.get(y)
        if prev is None:
            latest[y] = parsed
            continue
        if str(parsed["revision"]) > str(prev["revision"]):
            latest[y] = parsed
    return latest


def _extract_zip_all(zip_path: Path, out_dir: Path, *, quiet: bool = False) -> List[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    extracted: List[Path] = []
    with zipfile.ZipFile(zip_path) as zf:
        members = [m for m in zf.namelist() if not m.endswith("/")]
        for member in members:
            target = out_dir / Path(member).name
            tmp = target.with_name(target.name + ".tmp")
            _print(f"Extracting {zip_path.name}:{member} -> {target}", quiet=quiet)
            with zf.open(member, "r") as src, tmp.open("wb") as dst:
                shutil.copyfileobj(src, dst, length=1024 * 1024)
            tmp.replace(target)
            extracted.append(target)
    return extracted


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


def _latest_local_raw_anual(raw_dir: Path) -> Optional[Path]:
    best_key: tuple[int, str] | None = None
    best_path: Optional[Path] = None
    if not raw_dir.exists():
        return None
    for path in raw_dir.glob("*.txt"):
        parsed = _parse_pnadc_anual_visita5_txt_name(path.name)
        if parsed is None:
            continue
        key = (int(parsed["year"]), str(parsed["revision"]))
        if best_key is None or key > best_key:
            best_key = key
            best_path = path
    return best_path


def _head_meta(url: str, *, timeout: int = 120) -> Dict[str, str]:
    req = Request(url, method="HEAD", headers={"User-Agent": TOOL_USER_AGENT})
    with _urlopen_retry_ssl(req, timeout=timeout) as resp:
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

    headers = {"User-Agent": TOOL_USER_AGENT}
    if not force and known_etag:
        headers["If-None-Match"] = known_etag
    elif not force and known_last_modified:
        headers["If-Modified-Since"] = known_last_modified

    req = Request(url, headers=headers)
    tmp = destination.with_name(destination.name + ".tmp")
    try:
        _print(f"Downloading {url} -> {destination}", quiet=quiet)
        with _urlopen_retry_ssl(req, timeout=120) as resp, tmp.open("wb") as fh:
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


def _extract_year_tokens(text: str) -> List[int]:
    years = []
    for y in re.findall(r"(?<!\d)(20\d{2})(?!\d)", text):
        try:
            years.append(int(y))
        except Exception:
            continue
    return years


def _fetch_tse_resources(api_base: str, query: str, *, rows: int = 50) -> List[Dict[str, object]]:
    base = api_base.rstrip("/")
    url = f"{base}/api/3/action/package_search?q={quote_plus(query)}&rows={int(rows)}"
    payload = _fetch_json(url)
    if not isinstance(payload, dict) or not payload.get("success"):
        return []
    result = payload.get("result")
    if not isinstance(result, dict):
        return []
    packages = result.get("results")
    if not isinstance(packages, list):
        return []

    out: List[Dict[str, object]] = []
    seen_urls: set[str] = set()
    for pkg in packages:
        if not isinstance(pkg, dict):
            continue
        pkg_name = str(pkg.get("name", "") or "")
        pkg_title = str(pkg.get("title", "") or "")
        resources = pkg.get("resources")
        if not isinstance(resources, list):
            continue
        for res in resources:
            if not isinstance(res, dict):
                continue
            res_url = str(res.get("url", "") or "").strip()
            if not res_url or res_url in seen_urls:
                continue
            res_url_l = res_url.lower()
            if not res_url_l.endswith(".zip"):
                continue

            # Focus on elector profile datasets useful for election calibration.
            if "perfil_eleitor" not in res_url_l and "perfil_rae" not in res_url_l:
                continue
            if "secao" in res_url_l:
                continue

            res_name = str(res.get("name", "") or "")
            text_blob = f"{res_name} {res_url} {pkg_name} {pkg_title}"
            years = _extract_year_tokens(text_blob)
            year = max(years) if years else None

            kind = "other"
            if "perfil_eleitorado" in res_url_l:
                kind = "perfil_eleitorado"
            elif "perfil_rae" in res_url_l:
                kind = "perfil_rae"
            elif "perfil_eleitor" in res_url_l:
                kind = "perfil_eleitor"

            item = {
                "package_name": pkg_name,
                "package_title": pkg_title,
                "resource_id": str(res.get("id", "") or ""),
                "resource_name": res_name,
                "url": res_url,
                "format": str(res.get("format", "") or ""),
                "year": year,
                "kind": kind,
            }
            out.append(item)
            seen_urls.add(res_url)

    out.sort(key=lambda x: (str(x.get("kind", "")), int(x.get("year") or 0), str(x.get("resource_name", ""))))
    return out


def _select_tse_resources(
    resources: Sequence[Dict[str, object]], *, year: Optional[int], all_years: bool
) -> List[Dict[str, object]]:
    filtered = [dict(r) for r in resources]
    if year is not None:
        filtered = [r for r in filtered if int(r.get("year") or -1) == int(year)]
    if not filtered:
        return []

    # Keep latest by kind/year unless caller asks for all years.
    latest_by_key: Dict[Tuple[str, int], Dict[str, object]] = {}
    for r in filtered:
        kind = str(r.get("kind", "other"))
        y = int(r.get("year") or 0)
        key = (kind, y)
        prev = latest_by_key.get(key)
        if prev is None:
            latest_by_key[key] = r
            continue
        # tie-breaker by lexical resource name/url (usually carries revision tokens)
        prev_key = f"{prev.get('resource_name','')}|{prev.get('url','')}"
        cur_key = f"{r.get('resource_name','')}|{r.get('url','')}"
        if cur_key > prev_key:
            latest_by_key[key] = r

    by_key = sorted(latest_by_key.values(), key=lambda r: (str(r.get("kind", "")), int(r.get("year") or 0)))
    if all_years or year is not None:
        return by_key

    latest_by_kind: Dict[str, Dict[str, object]] = {}
    for r in by_key:
        kind = str(r.get("kind", "other"))
        prev = latest_by_kind.get(kind)
        if prev is None or int(r.get("year") or 0) > int(prev.get("year") or 0):
            latest_by_kind[kind] = r
    return sorted(latest_by_kind.values(), key=lambda r: str(r.get("kind", "")))


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
    # Anual: renda domiciliar total (VD5001)
    c = next((h for h in headers if h.startswith("VD5001")), None)
    if c:
        return c
    # Trimestral: renda do trabalho (VD4020 ou VD4019)
    c = next((h for h in headers if h.startswith("VD4020")), None)
    if c:
        return c
    c = next((h for h in headers if h.startswith("VD4019")), None)
    if c:
        return c
    raise ValueError("could not auto-detect income column; use --income-col")


INCOME_SOURCE_COLS = {
    "bpc_loas": "V5001A2",
    "bolsa_familia": "V5002A2",
    "outros_sociais": "V5003A2",
    "aposentadoria_pensao": "V5004A2",
    "seguro_desemprego": "V5005A2",
    "pensao_doacao": "V5006A2",
    "aluguel": "V5007A2",
    "outros_capital": "V5008A2",
}

INCOME_SOURCE_LABELS = {
    "bpc_loas": "BPC-LOAS",
    "bolsa_familia": "Bolsa Familia",
    "outros_sociais": "Outros programas sociais",
    "aposentadoria_pensao": "Aposentadoria/pensao",
    "seguro_desemprego": "Seguro-desemprego",
    "pensao_doacao": "Pensao/doacoes",
    "aluguel": "Aluguel/arrendamento",
    "outros_capital": "Outros de capital",
    "trabalho": "Renda do trabalho",
}

INCOME_CATEGORIES = {
    "trabalho": [],
    "beneficios_sociais": ["bpc_loas", "bolsa_familia", "outros_sociais"],
    "previdencia": ["aposentadoria_pensao"],
    "seguro": ["seguro_desemprego"],
    "transferencias_privadas": ["pensao_doacao"],
    "capital": ["aluguel", "outros_capital"],
}

INCOME_CATEGORY_LABELS = {
    "trabalho": "Trabalho",
    "beneficios_sociais": "Beneficios sociais",
    "previdencia": "Previdencia",
    "seguro": "Seguro",
    "transferencias_privadas": "Transferencias privadas",
    "capital": "Capital",
}

INCOME_CATEGORY_ORDER = [
    "trabalho",
    "beneficios_sociais",
    "previdencia",
    "seguro",
    "transferencias_privadas",
    "capital",
]


def _detect_income_source_cols(headers: Sequence[str]) -> Dict[str, str]:
    found: Dict[str, str] = {}
    for key, prefix in INCOME_SOURCE_COLS.items():
        col = next((h for h in headers if h.startswith(prefix)), None)
        if col:
            found[key] = col
    return found


def _detect_pnad_mode(headers: Sequence[str]) -> str:
    if any(h.startswith("VD5001") for h in headers):
        return "anual"
    if any(h.startswith("VD4020") or h.startswith("VD4019") for h in headers):
        return "trimestral"
    raise ValueError("could not auto-detect mode: expected VD5001 or VD4019/VD4020 columns")


def _calculate_income_composition(
    row: Dict[str, str],
    total_income_col: str,
    source_cols: Dict[str, str],
) -> Dict[str, float]:
    total = _parse_float(row.get(total_income_col, "")) or 0.0
    if total <= 0:
        return {}

    sources: Dict[str, float] = {}
    non_work_total = 0.0
    for key, col in source_cols.items():
        val = _parse_float(row.get(col, "")) or 0.0
        if val < 0:
            val = 0.0
        sources[key] = float(val)
        non_work_total += float(val)
    sources["trabalho"] = max(0.0, float(total) - non_work_total)

    return {k: _safe_div(float(v), float(total)) for k, v in sources.items()}


def _calculate_household_income_sources(
    row: Dict[str, str],
    total_income_col: str,
    source_cols: Dict[str, str],
) -> Dict[str, float]:
    total = _parse_float(row.get(total_income_col, "")) or 0.0
    if total < 0:
        total = 0.0

    out: Dict[str, float] = {"total": float(total)}
    non_work_total = 0.0
    for key, col in source_cols.items():
        val = _parse_float(row.get(col, "")) or 0.0
        if val < 0:
            val = 0.0
        out[key] = float(val)
        non_work_total += float(val)
    out["trabalho"] = max(0.0, float(total) - non_work_total)
    return out


def _aggregate_income_by_category(sources: Dict[str, float]) -> Dict[str, float]:
    categories: Dict[str, float] = {k: 0.0 for k in INCOME_CATEGORY_ORDER}
    categories["trabalho"] = float(sources.get("trabalho", 0.0) or 0.0)
    for cat in INCOME_CATEGORY_ORDER:
        if cat == "trabalho":
            continue
        categories[cat] = sum(float(sources.get(k, 0.0) or 0.0) for k in INCOME_CATEGORIES.get(cat, []))
    return categories


def _calculate_dependency_score(benefits_pct: float, previdencia_pct: float, work_pct: float) -> float:
    _ = work_pct
    return float(benefits_pct) + float(previdencia_pct)


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


def _detect_replicate_weight_cols(headers: Sequence[str], *, base_prefix: str = "V1028") -> List[str]:
    pairs: List[Tuple[int, str]] = []
    for h in headers:
        base = h.split("__", 1)[0]
        m = re.fullmatch(rf"{re.escape(base_prefix)}(\d{{3}})", base)
        if not m:
            continue
        pairs.append((int(m.group(1)), h))
    pairs.sort(key=lambda t: t[0])
    return [h for _, h in pairs]


def _normalize_ci_level(raw: float) -> float:
    level = float(raw)
    if level <= 0.0 or level >= 1.0:
        raise ValueError("ci level must be between 0 and 1 (exclusive)")
    return level


def _ci_from_replicates(
    theta: float,
    replicate_thetas: Sequence[float],
    *,
    ci_level: float,
    clamp: Optional[Tuple[float, float]] = None,
) -> Optional[Dict[str, float]]:
    vals = [float(x) for x in replicate_thetas if math.isfinite(float(x))]
    r = len(vals)
    if r < 2:
        return None
    var = sum((x - theta) ** 2 for x in vals) / float(r - 1)
    if var < 0:
        var = 0.0
    se = math.sqrt(var)
    z = NormalDist().inv_cdf(0.5 + ci_level / 2.0)
    moe = z * se
    low = theta - moe
    high = theta + moe
    if clamp is not None:
        lo, hi = clamp
        low = max(lo, low)
        high = min(hi, high)
    return {
        "replicates": int(r),
        "se": float(se),
        "moe": float(moe),
        "ci_low": float(low),
        "ci_high": float(high),
    }


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


def _is_missing_label(value: str) -> bool:
    t = _norm_text(value)
    return t in ("", "sem_info", "n/a", "na", "nan", "none", "null")


def _capital_bucket(cap_label: str, cap_code: str) -> str:
    # Prefer coded value when available.
    c = cap_code.strip()
    if c in ("1", "01"):
        return "Capital"
    if c in ("2", "02"):
        return "Nao capital/Interior"

    t = _norm_text(cap_label)
    if _is_missing_label(cap_label):
        return "Nao capital/Interior"
    if "nao capital" in t or "não capital" in t or "interior" in t:
        return "Nao capital/Interior"
    if "capital" in t or "municipio de" in t or "município de" in t:
        return "Capital"
    return "Capital"


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
    sampling = payload.get("sampling", {})
    if isinstance(sampling, dict):
        print(
            f"Amostral: ci={sampling.get('ci_enabled')} "
            f"(nivel={sampling.get('ci_level')}, reps={sampling.get('replicate_weight_columns_detected')})"
        )
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
        avg_moe = g.get("avg_household_sm_moe")
        avg_ci_low = g.get("avg_household_sm_ci_low")
        avg_ci_high = g.get("avg_household_sm_ci_high")
        if avg_moe is not None and avg_ci_low is not None and avg_ci_high is not None:
            print(
                "  Media renda domiciliar (SM): "
                f"{avg_sm:.3f} ± {float(avg_moe):.3f} "
                f"(IC {float(payload.get('sampling', {}).get('ci_level', 0.95) or 0.95):.0%}: "
                f"{float(avg_ci_low):.3f}..{float(avg_ci_high):.3f})"
            )
        else:
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
            hp_moe = b.get("households_pct_moe")
            pp_moe = b.get("persons_pct_moe")
            hbar = _gradient_bar(hp, width=28, palette=gradients[i % len(gradients)], use_color=use_color)
            pbar = _gradient_bar(pp, width=28, palette=gradients[i % len(gradients)], use_color=use_color)
            c = colors[i % len(colors)]
            hp_txt = f"{hp:6.2f}%"
            pp_txt = f"{pp:6.2f}%"
            if hp_moe is not None:
                hp_txt = f"{hp:6.2f}%±{float(hp_moe):4.2f}"
            if pp_moe is not None:
                pp_txt = f"{pp:6.2f}%±{float(pp_moe):4.2f}"
            print(
                "  "
                + _badge(f"{rng:<8}", fg=16, bg=gradients[i % len(gradients)][-1], use_color=use_color)
                + f" {hp_txt:<14} "
                + hbar
                + f"  {pp_txt:<14} "
                + pbar
            )
        pie = _mini_pie([b for b in bands if isinstance(b, dict)], colors, use_color)
        if pie:
            print(f"  Distribuição domicílios: {pie}")
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


def _age_label_sort_key(label: str) -> Tuple[int, str]:
    s = str(label).strip()
    if s == "sem_idade":
        return (9999, s)
    m = re.match(r"^(\d+)\s*-\s*(\d+)$", s)
    if m:
        return (int(m.group(1)), s)
    m = re.match(r"^(\d+)\s*\+$", s)
    if m:
        return (int(m.group(1)), s)
    return (9000, s.lower())


def _sex_bucket(value: str) -> str:
    t = _norm_text(value)
    if t in ("1", "homem", "masculino"):
        return "M"
    if t in ("2", "mulher", "feminino"):
        return "F"
    if "homem" in t or "masc" in t:
        return "M"
    if "mulher" in t or "fem" in t:
        return "F"
    return "O"


def _shorten_text(value: str, max_len: int) -> str:
    s = re.sub(r"\s+", " ", str(value).strip())
    if len(s) <= max_len:
        return s
    if max_len <= 3:
        return s[:max_len]
    return s[: max_len - 3].rstrip() + "..."


def _compact_dim_label(dim: str, label: str, *, max_len: int = 34) -> str:
    s = re.sub(r"\s+", " ", str(label).strip())
    if _is_missing_label(s):
        return "Sem informacao"

    if dim == "education":
        replacements = [
            (r"^Regular do ensino m[ée]dio", "Ensino medio (regular)"),
            (r"^Regular do ensino fundamental", "Ensino fundamental (regular)"),
            (r"^Superior\s*-\s*", "Superior "),
            (r"^Especializa[çc][aã]o de n[íi]vel superior", "Especializacao"),
            (r"^Mestrado", "Mestrado"),
            (r"^Doutorado", "Doutorado"),
            (r"^Antigo prim[áa]rio", "Primario (antigo)"),
            (r"^EJA ou supletivo do 2[ºo] grau", "EJA/supletivo 2o grau"),
            (r"^EJA ou supletivo do 1[ºo] grau", "EJA/supletivo 1o grau"),
            (r"\s+ou equivalente", ""),
        ]
        for pat, rep in replacements:
            s = re.sub(pat, rep, s, flags=re.IGNORECASE)
    elif dim == "occupation_status":
        replacements = [
            (r"Empregado no setor privado", "Empregado setor privado"),
            (r"Trabalhador dom[ée]stico", "Trab. domestico"),
            (r"Militar e servidor estatut[áa]rio", "Militar/servidor"),
        ]
        for pat, rep in replacements:
            s = re.sub(pat, rep, s, flags=re.IGNORECASE)
    elif dim == "occupation_position":
        replacements = [
            (r"^Grande grupo ", "GG "),
            (r"^Nao se aplica \(fora da ocupacao\)$", "Nao se aplica (fora ocupacao)"),
        ]
        for pat, rep in replacements:
            s = re.sub(pat, rep, s, flags=re.IGNORECASE)
    elif dim == "metro_region":
        s = s.replace("Região Metropolitana", "RM")
        s = s.replace("Regiao Metropolitana", "RM")
        s = s.replace("Região Integrada de Desenvolvimento", "RIDE")
        s = s.replace("Regiao Integrada de Desenvolvimento", "RIDE")

    return _shorten_text(s, max_len)


def _labor_type_bucket(raw_value: str, label_value: str) -> str:
    raw = raw_value.strip()
    label = label_value.strip()
    if label:
        if "desalent" in _norm_text(label):
            return "Desalentado(a)"
        return label
    if raw in ("1", "01"):
        return "Desalentado(a)"
    return "Nao desalentado/ou nao se aplica"


def _occupation_status_bucket(raw_value: str, label_value: str) -> str:
    label = label_value.strip()
    raw = raw_value.strip()
    if label:
        return label
    if raw:
        return f"VD4009 codigo {raw}"
    return "Nao se aplica (fora da ocupacao)"


def _occupation_position_bucket(raw_value: str, label_value: str) -> str:
    label = label_value.strip()
    raw = raw_value.strip()
    if label:
        return label
    if raw:
        digits = re.sub(r"\D", "", raw)
        if digits:
            group = digits[0]
            groups = {
                "0": "Grande grupo 0: Forcas armadas",
                "1": "Grande grupo 1: Dirigentes e gerentes",
                "2": "Grande grupo 2: Profissionais das ciencias/intelectuais",
                "3": "Grande grupo 3: Tecnicos de nivel medio",
                "4": "Grande grupo 4: Apoio administrativo",
                "5": "Grande grupo 5: Servicos e vendedores",
                "6": "Grande grupo 6: Agropecuaria/florestal/pesca",
                "7": "Grande grupo 7: Industria/construcao/artesaos",
                "8": "Grande grupo 8: Operadores de maquinas",
                "9": "Grande grupo 9: Ocupacoes elementares",
            }
            return groups.get(group, f"Grande grupo {group}")
        return f"CBO {raw}"
    return "Nao se aplica (fora da ocupacao)"


def _metro_region_bucket(raw_value: str, label_value: str) -> str:
    label = label_value.strip()
    raw = raw_value.strip()
    if label:
        return label
    if raw:
        return f"RM/RIDE codigo {raw}"
    return "Fora de RM/RIDE"


def _counter_to_sorted_rows(counter: Dict[str, float], total: float) -> List[Dict[str, object]]:
    rows = []
    for k, v in counter.items():
        rows.append({"label": k, "value": float(v), "pct": round(100.0 * _safe_div(v, total), 4)})
    rows.sort(key=lambda r: r["value"], reverse=True)
    return rows


def _build_dashboard_payload(args: argparse.Namespace) -> Dict[str, object]:
    try:
        from npv_deflators import build_deflators  # type: ignore
        from npv_deflators import read_ipca_csv
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
    ci_level = _normalize_ci_level(args.ci_level)
    use_ci = (not args.unweighted) and (not args.no_ci)
    replicate_weight_cols: List[str] = []
    replicate_count = 0
    households: Dict[str, Dict[str, object]] = {}
    dimension_labels: Dict[str, str] = {}
    dim_keys: List[str] = []
    
    # Dashboard v2.0: Initialize variables that need to persist outside with block
    pnad_mode = "trimestral"
    income_source_cols: Dict[str, str] = {}
    is_anual_mode = False
    do_breakdown = False
    do_source_detail = False
    do_dependency_ranking = False
    do_composition_by_band = False

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

        relationship_label_col = "V2005_label" if "V2005_label" in headers else None
        relationship_raw_col = _find_col(headers, "V2005__", "V2005")
        occupation_status_label_col = "VD4009_label" if "VD4009_label" in headers else None
        occupation_status_raw_col = _find_col(headers, "VD4009__", "VD4009")
        labor_type_label_col = "VD4005_label" if "VD4005_label" in headers else None
        labor_type_raw_col = _find_col(headers, "VD4005__", "VD4005")
        position_label_col = "V4010_label" if "V4010_label" in headers else None
        position_raw_col = _find_col(headers, "V4010__", "V4010")
        rm_label_col = "RM_RIDE_label" if "RM_RIDE_label" in headers else None
        rm_col = _find_col(headers, "RM_RIDE__", "RM_RIDE")

        income_col = _detect_income_col(headers, args.income_col)
        selected_income_col = income_col
        selected_weight_col = None if args.unweighted else _detect_weight_col(headers, args.weight_col)
        if use_ci:
            replicate_weight_cols = _detect_replicate_weight_cols(headers, base_prefix="V1028")
            replicate_count = len(replicate_weight_cols)

        # Dashboard v2.0: Detect PNAD mode and set up income composition analysis
        pnad_mode_arg = str(getattr(args, "mode", "auto") or "auto").strip().lower()
        if pnad_mode_arg in ("", "auto", "comparativo"):
            pnad_mode = _detect_pnad_mode(headers)
        else:
            pnad_mode = pnad_mode_arg

        has_anual_cols = any(h.startswith("VD5001") for h in headers)
        has_tri_cols = any(h.startswith("VD4020") or h.startswith("VD4019") for h in headers)
        if pnad_mode == "anual" and not has_anual_cols:
            raise ValueError("modo anual solicitado, mas coluna VD5001 nao foi encontrada")
        if pnad_mode == "trimestral" and not has_tri_cols:
            raise ValueError("modo trimestral solicitado, mas colunas VD4019/VD4020 nao foram encontradas")

        is_anual_mode = pnad_mode == "anual"
        if is_anual_mode:
            income_source_cols = _detect_income_source_cols(headers)
        
        # Set breakdown flags based on args and mode
        do_breakdown = getattr(args, "breakdown", False) and is_anual_mode
        do_source_detail = getattr(args, "source_detail", False) and is_anual_mode
        do_dependency_ranking = getattr(args, "dependency_ranking", False) and is_anual_mode
        do_composition_by_band = getattr(args, "composition_by_band", False) and is_anual_mode

        if not dom_col or not year_col or not qtr_col or not uf_col:
            raise ValueError("input must contain dom_id, Ano, Trimestre and UF")
        if not args.unweighted and not selected_weight_col:
            raise ValueError(
                "weight column not found. Re-run pipeline including V1028 "
                "or pass --weight-col / use --unweighted for diagnostics."
            )
        if use_ci and replicate_count < 2:
            use_ci = False

        dim_keys = ["sex", "race", "education", "age", "capital", "macro_region"]
        dimension_labels = {
            "sex": "Sexo",
            "race": "Raca/Cor",
            "education": "Escolaridade",
            "age": "Faixa etaria",
            "capital": "Capital x Interior",
            "macro_region": "Macro-regiao",
        }
        if relationship_label_col or relationship_raw_col:
            dim_keys.append("relationship")
            dimension_labels["relationship"] = "Relacao no domicilio"
        if occupation_status_label_col or occupation_status_raw_col:
            dim_keys.append("occupation_status")
            dimension_labels["occupation_status"] = "Condicao ocupacional"
        if labor_type_label_col or labor_type_raw_col:
            dim_keys.append("labor_type")
            dimension_labels["labor_type"] = "Desalento (VD4005)"
        if position_label_col or position_raw_col:
            dim_keys.append("occupation_position")
            dimension_labels["occupation_position"] = "Grande grupo ocupacional"
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

            cap_label_raw = str(row.get(cap_label_col, "")).strip() if cap_label_col else ""
            cap_code_raw = str(row.get(cap_col, "")).strip() if cap_col else ""
            cap = _capital_bucket(cap_label_raw, cap_code_raw)

            relationship_label = str(row.get(relationship_label_col, "")).strip() if relationship_label_col else ""
            relationship_raw = str(row.get(relationship_raw_col, "")).strip() if relationship_raw_col else ""
            relationship = relationship_label or relationship_raw or "Sem informacao"

            occupation_status_label = (
                str(row.get(occupation_status_label_col, "")).strip() if occupation_status_label_col else ""
            )
            occupation_status_raw = (
                str(row.get(occupation_status_raw_col, "")).strip() if occupation_status_raw_col else ""
            )
            occupation_status = _occupation_status_bucket(occupation_status_raw, occupation_status_label)

            labor_type_label = str(row.get(labor_type_label_col, "")).strip() if labor_type_label_col else ""
            labor_type_raw = str(row.get(labor_type_raw_col, "")).strip() if labor_type_raw_col else ""
            labor_type = _labor_type_bucket(labor_type_raw, labor_type_label)

            occupation_position_label = str(row.get(position_label_col, "")).strip() if position_label_col else ""
            occupation_position_raw = str(row.get(position_raw_col, "")).strip() if position_raw_col else ""
            occupation_position = _occupation_position_bucket(occupation_position_raw, occupation_position_label)

            metro_region_label = str(row.get(rm_label_col, "")).strip() if rm_label_col else ""
            metro_region_raw = str(row.get(rm_col, "")).strip() if rm_col else ""
            metro_region = _metro_region_bucket(metro_region_raw, metro_region_label)
            macro_region = _macro_region_from_uf(uf_code)

            st = households.get(dom)
            if st is None:
                rep_household_weights: List[float] = []
                if use_ci:
                    for rep_col in replicate_weight_cols:
                        rep_raw = row.get(rep_col, "")
                        rep_val = _parse_float(rep_raw)
                        rep_household_weights.append(float(rep_val) if rep_val is not None and rep_val > 0 else 0.0)

                income_sources_nominal_init: Dict[str, float] = {}
                income_sources_target_init: Dict[str, float] = {}
                if is_anual_mode:
                    src_keys = list(income_source_cols.keys()) + ["trabalho", "total"]
                    income_sources_nominal_init = {k: 0.0 for k in src_keys}
                    income_sources_target_init = {k: 0.0 for k in src_keys}

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
                    "age_sex_counts": defaultdict(lambda: defaultdict(float)),
                    "rep_household_weights": rep_household_weights,
                    "income_sources_nominal": income_sources_nominal_init,
                    "income_sources_target": income_sources_target_init,
                }
                households[dom] = st

            st["persons_n"] = int(st["persons_n"]) + 1
            st["persons_weight"] = float(st["persons_weight"]) + row_weight
            hw = float(st.get("household_weight") or row_weight)
            if abs(hw - row_weight) > 1e-6:
                inconsistent_household_weight += 1

            if is_anual_mode:
                row_sources = _calculate_household_income_sources(row, income_col, income_source_cols)
                row_sources_target = {k: float(v) * float(factor) for k, v in row_sources.items()}
                st["income_nominal"] = max(float(st["income_nominal"]), float(row_sources.get("total", 0.0) or 0.0))
                st["income_target"] = max(float(st["income_target"]), float(row_sources_target.get("total", 0.0) or 0.0))
                src_nominal = st.get("income_sources_nominal", {})
                src_target = st.get("income_sources_target", {})
                if isinstance(src_nominal, dict) and isinstance(src_target, dict):
                    for src_key, src_val in row_sources.items():
                        src_nominal[src_key] = max(float(src_nominal.get(src_key, 0.0) or 0.0), float(src_val))
                        src_target[src_key] = max(
                            float(src_target.get(src_key, 0.0) or 0.0),
                            float(row_sources_target.get(src_key, 0.0) or 0.0),
                        )
            else:
                st["income_nominal"] = float(st["income_nominal"]) + float(income_nominal)
                st["income_target"] = float(st["income_target"]) + float(income_nominal) * float(factor)

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
                row_dims["relationship"] = relationship
            if "occupation_status" in dim_keys:
                row_dims["occupation_status"] = occupation_status
            if "labor_type" in dim_keys:
                row_dims["labor_type"] = labor_type
            if "occupation_position" in dim_keys:
                row_dims["occupation_position"] = occupation_position
            if "metro_region" in dim_keys:
                row_dims["metro_region"] = metro_region

            dim_counts = st["dim_counts"]
            for dim, value in row_dims.items():
                dim_counts[dim][str(value)] += sw
            age_sex_counts = st["age_sex_counts"]
            age_sex_counts[str(age_band or "sem_idade")][_sex_bucket(sex)] += sw

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
            "rep_households_total": [0.0] * replicate_count if use_ci else [],
            "rep_persons_total": [0.0] * replicate_count if use_ci else [],
            "rep_sum_ratio": [0.0] * replicate_count if use_ci else [],
            "rep_bands": (
                {
                    str(item["label"]): {
                        "households": [0.0] * replicate_count,
                        "persons": [0.0] * replicate_count,
                    }
                    for item in ranges
                }
                if use_ci
                else {}
            ),
        }
        uf_stats: Dict[str, Dict[str, object]] = {}
        macro_stats: Dict[str, Dict[str, object]] = {}
        demo = {k: defaultdict(float) for k in dim_keys}
        cross = {k: defaultdict(lambda: defaultdict(float)) for k in dim_keys}
        age_sex = defaultdict(lambda: defaultdict(float))
        ratio_pairs: List[Tuple[float, float]] = []
        sm_ref_weighted_sum = 0.0
        sm_ref_weight_total = 0.0
        sm_ref_min: Optional[float] = None
        sm_ref_max: Optional[float] = None

        def ensure_group(container: Dict[str, Dict[str, object]], key: str, label: str) -> Dict[str, object]:
            g = container.get(key)
            if g is None:
                rep_households_total = [0.0] * replicate_count if use_ci else []
                rep_persons_total = [0.0] * replicate_count if use_ci else []
                rep_sum_ratio = [0.0] * replicate_count if use_ci else []
                rep_bands = (
                    {
                        str(item["label"]): {
                            "households": [0.0] * replicate_count,
                            "persons": [0.0] * replicate_count,
                        }
                        for item in ranges
                    }
                    if use_ci
                    else {}
                )
                g = {
                    "group": key,
                    "label": label,
                    "households_total": 0.0,
                    "persons_total": 0.0,
                    "households_sample": 0,
                    "persons_sample": 0,
                    "sum_ratio": 0.0,
                    "bands": {str(item["label"]): {"households": 0.0, "persons": 0.0} for item in ranges},
                    "rep_households_total": rep_households_total,
                    "rep_persons_total": rep_persons_total,
                    "rep_sum_ratio": rep_sum_ratio,
                    "rep_bands": rep_bands,
                }
                container[key] = g
            return g

        def add_replicate_stats(
            g_obj: Dict[str, object],
            *,
            ratio_value: float,
            band_label: str,
            persons_n: int,
            rep_weights: Sequence[float],
        ) -> None:
            if not use_ci or len(rep_weights) != replicate_count:
                return
            rep_households_total = g_obj["rep_households_total"]
            rep_persons_total = g_obj["rep_persons_total"]
            rep_sum_ratio = g_obj["rep_sum_ratio"]
            rep_band = g_obj["rep_bands"][band_label]
            rep_band_households = rep_band["households"]
            rep_band_persons = rep_band["persons"]
            for j, rep_hh_w in enumerate(rep_weights):
                wj = float(rep_hh_w)
                if wj <= 0:
                    continue
                rep_pp_w = float(persons_n) * wj
                rep_households_total[j] += wj
                rep_persons_total[j] += rep_pp_w
                rep_sum_ratio[j] += ratio_value * wj
                rep_band_households[j] += wj
                rep_band_persons[j] += rep_pp_w

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
            rep_weights = h.get("rep_household_weights", [])
            if isinstance(rep_weights, list):
                add_replicate_stats(
                    national,
                    ratio_value=ratio,
                    band_label=band,
                    persons_n=int(h["persons_n"]),
                    rep_weights=rep_weights,
                )
                add_replicate_stats(
                    u,
                    ratio_value=ratio,
                    band_label=band,
                    persons_n=int(h["persons_n"]),
                    rep_weights=rep_weights,
                )
                add_replicate_stats(
                    m,
                    ratio_value=ratio,
                    band_label=band,
                    persons_n=int(h["persons_n"]),
                    rep_weights=rep_weights,
                )

            dim_counts = h.get("dim_counts", {})
            for dim in dim_keys:
                src = dim_counts.get(dim, {})
                for lbl, val in src.items():
                    demo[dim][str(lbl)] += float(val)
                    cross[dim][str(lbl)][band] += float(val)
            age_sex_counts = h.get("age_sex_counts", {})
            if isinstance(age_sex_counts, dict):
                for age_lbl, sx_map in age_sex_counts.items():
                    if not isinstance(sx_map, dict):
                        continue
                    for sx, val in sx_map.items():
                        age_sex[str(age_lbl)][str(sx)] += float(val)

        def finalize_group(g: Dict[str, object]) -> Dict[str, object]:
            hh_total = float(g["households_total"])
            pp_total = float(g["persons_total"])
            avg_sm = _safe_div(float(g["sum_ratio"]), hh_total)
            rep_households_total = g.get("rep_households_total", [])
            rep_persons_total = g.get("rep_persons_total", [])
            rep_sum_ratio = g.get("rep_sum_ratio", [])
            avg_sm_ci: Optional[Dict[str, float]] = None
            if use_ci and isinstance(rep_households_total, list) and isinstance(rep_sum_ratio, list):
                avg_reps = [
                    _safe_div(float(rep_sum_ratio[j]), float(rep_households_total[j]))
                    if float(rep_households_total[j]) > 0
                    else 0.0
                    for j in range(replicate_count)
                ]
                avg_sm_ci = _ci_from_replicates(float(avg_sm), avg_reps, ci_level=ci_level)

            bands_rows = []
            for item in ranges:
                lbl = str(item["label"])
                b = g["bands"][lbl]
                bh = float(b["households"])
                bp = float(b["persons"])
                hp = round(100.0 * _safe_div(bh, hh_total), 4)
                pp = round(100.0 * _safe_div(bp, pp_total), 4)
                row_out: Dict[str, object] = {
                    "range": lbl,
                    "households": bh,
                    "households_pct": hp,
                    "persons": bp,
                    "persons_pct": pp,
                }
                if use_ci:
                    rep_band = g.get("rep_bands", {}).get(lbl, {})
                    rep_bh = rep_band.get("households", []) if isinstance(rep_band, dict) else []
                    rep_bp = rep_band.get("persons", []) if isinstance(rep_band, dict) else []
                    if (
                        isinstance(rep_households_total, list)
                        and isinstance(rep_persons_total, list)
                        and isinstance(rep_bh, list)
                        and isinstance(rep_bp, list)
                        and len(rep_households_total) == replicate_count
                        and len(rep_persons_total) == replicate_count
                        and len(rep_bh) == replicate_count
                        and len(rep_bp) == replicate_count
                    ):
                        hh_rep = [
                            100.0 * _safe_div(float(rep_bh[j]), float(rep_households_total[j]))
                            if float(rep_households_total[j]) > 0
                            else 0.0
                            for j in range(replicate_count)
                        ]
                        pp_rep = [
                            100.0 * _safe_div(float(rep_bp[j]), float(rep_persons_total[j]))
                            if float(rep_persons_total[j]) > 0
                            else 0.0
                            for j in range(replicate_count)
                        ]
                        hh_ci = _ci_from_replicates(float(hp), hh_rep, ci_level=ci_level, clamp=(0.0, 100.0))
                        pp_ci = _ci_from_replicates(float(pp), pp_rep, ci_level=ci_level, clamp=(0.0, 100.0))
                        if hh_ci:
                            row_out.update(
                                {
                                    "households_pct_se": round(float(hh_ci["se"]), 6),
                                    "households_pct_moe": round(float(hh_ci["moe"]), 6),
                                    "households_pct_ci_low": round(float(hh_ci["ci_low"]), 6),
                                    "households_pct_ci_high": round(float(hh_ci["ci_high"]), 6),
                                }
                            )
                        if pp_ci:
                            row_out.update(
                                {
                                    "persons_pct_se": round(float(pp_ci["se"]), 6),
                                    "persons_pct_moe": round(float(pp_ci["moe"]), 6),
                                    "persons_pct_ci_low": round(float(pp_ci["ci_low"]), 6),
                                    "persons_pct_ci_high": round(float(pp_ci["ci_high"]), 6),
                                }
                            )
                bands_rows.append(row_out)

            out_row: Dict[str, object] = {
                "group": g["group"],
                "label": g["label"],
                "households_total": hh_total,
                "persons_total": pp_total,
                "households_sample": int(g["households_sample"]),
                "persons_sample": int(g["persons_sample"]),
                "avg_household_sm": round(avg_sm, 6),
                "bands": bands_rows,
            }
            if avg_sm_ci:
                out_row.update(
                    {
                        "avg_household_sm_se": round(float(avg_sm_ci["se"]), 6),
                        "avg_household_sm_moe": round(float(avg_sm_ci["moe"]), 6),
                        "avg_household_sm_ci_low": round(float(avg_sm_ci["ci_low"]), 6),
                        "avg_household_sm_ci_high": round(float(avg_sm_ci["ci_high"]), 6),
                    }
                )
            return out_row

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
        demographics_out: Dict[str, List[Dict[str, object]]] = {}
        for k, v in demo.items():
            rows = _counter_to_sorted_rows(v, persons_total)
            if k == "age":
                rows.sort(key=lambda r: _age_label_sort_key(str(r.get("label", ""))))
            demographics_out[k] = rows

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
        age_pyramid_rows: List[Dict[str, object]] = []
        for age_lbl in sorted(age_sex.keys(), key=_age_label_sort_key):
            sx_map = age_sex[age_lbl]
            female = float(sx_map.get("F", 0.0))
            male = float(sx_map.get("M", 0.0))
            other = float(sx_map.get("O", 0.0))
            total_age = female + male + other
            age_pyramid_rows.append(
                {
                    "age": age_lbl,
                    "female": female,
                    "male": male,
                    "other": other,
                    "total": total_age,
                    "female_pct": round(100.0 * _safe_div(female, persons_total), 4),
                    "male_pct": round(100.0 * _safe_div(male, persons_total), 4),
                    "other_pct": round(100.0 * _safe_div(other, persons_total), 4),
                    "female_within_age_pct": round(100.0 * _safe_div(female, total_age), 4),
                    "male_within_age_pct": round(100.0 * _safe_div(male, total_age), 4),
                    "other_within_age_pct": round(100.0 * _safe_div(other, total_age), 4),
                }
            )
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
            "age_pyramid": age_pyramid_rows,
            "dimensions": dim_keys,
            "cross": cross_out,
            "sampling": {
                "ci_enabled": bool(use_ci),
                "ci_level": ci_level,
                "variance_method": "bootstrap_replicates_mse",
                "variance_formula": "var=(1/(R-1))*sum((theta_r-theta)^2)",
                "replicate_weight_base": "V1028",
                "replicate_weight_count": int(replicate_count),
                "replicate_weight_columns_detected": int(len(replicate_weight_cols)),
                "person_weight_assumption": "persons_weight_rep=persons_in_dom*household_rep_weight",
            },
        }

    income_composition_payload: Dict[str, object] = {
        "income_composition_national": {},
        "income_sources_detail": {},
        "uf_dependency_ranking": [],
        "composition_by_band": {},
    }
    total_income_mean = 0.0
    total_income_median = 0.0

    if is_anual_mode:
        summary_mode = "alvo" if "alvo" in modes_out else (next(iter(modes_out.keys())) if modes_out else "alvo")
        use_target_values = summary_mode == "alvo"
        active_income_key = "income_target" if use_target_values else "income_nominal"
        active_sources_key = "income_sources_target" if use_target_values else "income_sources_nominal"

        annual_source_keys = list(INCOME_SOURCE_COLS.keys()) + ["trabalho"]
        source_totals = {k: 0.0 for k in annual_source_keys}
        source_recipients = {k: 0.0 for k in INCOME_SOURCE_COLS.keys()}
        national_total_income = 0.0
        national_total_weight = 0.0
        income_pairs: List[Tuple[float, float]] = []

        uf_income_composition: Dict[str, Dict[str, object]] = {}
        band_income_composition: Dict[str, Dict[str, object]] = {
            str(item["label"]): {
                "households": 0.0,
                "total_income": 0.0,
                "sources": {k: 0.0 for k in annual_source_keys},
            }
            for item in ranges
        }

        for h in households.values():
            hh_w = 1.0 if args.unweighted else float(h.get("household_weight", 1.0) or 1.0)
            if hh_w <= 0:
                continue
            hh_income = float(h.get(active_income_key, 0.0) or 0.0)
            if hh_income < 0:
                hh_income = 0.0
            uf_code = str(h.get("uf_code", "") or "")
            uf_label = str(h.get("uf_label", "") or uf_code)
            raw_sources = h.get(active_sources_key, {})
            if not isinstance(raw_sources, dict):
                raw_sources = {}

            source_amounts: Dict[str, float] = {}
            non_work_total = 0.0
            for src_key in INCOME_SOURCE_COLS.keys():
                val = float(raw_sources.get(src_key, 0.0) or 0.0)
                if val < 0:
                    val = 0.0
                source_amounts[src_key] = val
                non_work_total += val
            trabalho_val = float(raw_sources.get("trabalho", max(0.0, hh_income - non_work_total)) or 0.0)
            if trabalho_val < 0:
                trabalho_val = 0.0
            source_amounts["trabalho"] = trabalho_val

            national_total_income += hh_income * hh_w
            national_total_weight += hh_w
            income_pairs.append((hh_income, hh_w))
            for src_key in annual_source_keys:
                source_totals[src_key] += float(source_amounts.get(src_key, 0.0) or 0.0) * hh_w
            for src_key in INCOME_SOURCE_COLS.keys():
                if float(source_amounts.get(src_key, 0.0) or 0.0) > 0:
                    source_recipients[src_key] += hh_w

            if uf_code:
                if uf_code not in uf_income_composition:
                    uf_income_composition[uf_code] = {
                        "uf_code": uf_code,
                        "uf_label": uf_label,
                        "households": 0.0,
                        "total_income": 0.0,
                        "sources": {k: 0.0 for k in annual_source_keys},
                    }
                uf_data = uf_income_composition[uf_code]
                uf_data["households"] = float(uf_data["households"]) + hh_w
                uf_data["total_income"] = float(uf_data["total_income"]) + hh_income * hh_w
                uf_sources = uf_data.get("sources", {})
                if isinstance(uf_sources, dict):
                    for src_key in annual_source_keys:
                        uf_sources[src_key] = float(uf_sources.get(src_key, 0.0) or 0.0) + float(
                            source_amounts.get(src_key, 0.0) or 0.0
                        ) * hh_w

            sm_ref = float(sm_target_nominal) if use_target_values else float(h.get("sm_period", 0.0) or 0.0)
            if sm_ref > 0:
                ratio = _safe_div(hh_income, sm_ref)
                band = _classify_range(max(0.0, ratio), ranges)
                band_data = band_income_composition.get(band)
                if isinstance(band_data, dict):
                    band_data["households"] = float(band_data.get("households", 0.0) or 0.0) + hh_w
                    band_data["total_income"] = float(band_data.get("total_income", 0.0) or 0.0) + hh_income * hh_w
                    band_sources = band_data.get("sources", {})
                    if isinstance(band_sources, dict):
                        for src_key in annual_source_keys:
                            band_sources[src_key] = float(band_sources.get(src_key, 0.0) or 0.0) + float(
                                source_amounts.get(src_key, 0.0) or 0.0
                            ) * hh_w

        total_income_mean = _safe_div(national_total_income, national_total_weight)
        total_income_median = _weighted_median(income_pairs)
        income_composition_national: Dict[str, object] = {}
        income_sources_detail: Dict[str, object] = {}

        if national_total_income > 0 and national_total_weight > 0:
            for src_key in INCOME_SOURCE_COLS.keys():
                src_total = float(source_totals.get(src_key, 0.0) or 0.0)
                income_sources_detail[src_key] = {
                    "label": INCOME_SOURCE_LABELS.get(src_key, src_key),
                    "mean": round(_safe_div(src_total, national_total_weight), 2),
                    "pct": round(100.0 * _safe_div(src_total, national_total_income), 2),
                    "recipients_pct": round(100.0 * _safe_div(source_recipients.get(src_key, 0.0), national_total_weight), 2),
                }

            for cat in INCOME_CATEGORY_ORDER:
                if cat == "trabalho":
                    cat_total = float(source_totals.get("trabalho", 0.0) or 0.0)
                else:
                    cat_total = sum(float(source_totals.get(src, 0.0) or 0.0) for src in INCOME_CATEGORIES.get(cat, []))
                income_composition_national[cat] = {
                    "label": INCOME_CATEGORY_LABELS.get(cat, cat),
                    "mean": round(_safe_div(cat_total, national_total_weight), 2),
                    "pct": round(100.0 * _safe_div(cat_total, national_total_income), 2),
                }

        uf_dependency_ranking: List[Dict[str, object]] = []
        for uf_code, uf_data in uf_income_composition.items():
            total_inc = float(uf_data.get("total_income", 0.0) or 0.0)
            hh_count = float(uf_data.get("households", 0.0) or 0.0)
            uf_sources = uf_data.get("sources", {})
            if total_inc <= 0 or hh_count <= 0 or not isinstance(uf_sources, dict):
                continue
            work_total = float(uf_sources.get("trabalho", 0.0) or 0.0)
            benefits_total = sum(float(uf_sources.get(k, 0.0) or 0.0) for k in INCOME_CATEGORIES["beneficios_sociais"])
            previdencia_total = float(uf_sources.get("aposentadoria_pensao", 0.0) or 0.0)
            work_pct = 100.0 * _safe_div(work_total, total_inc)
            benefits_pct = 100.0 * _safe_div(benefits_total, total_inc)
            previdencia_pct = 100.0 * _safe_div(previdencia_total, total_inc)
            dependency_score = _calculate_dependency_score(benefits_pct, previdencia_pct, work_pct)
            uf_dependency_ranking.append(
                {
                    "uf_code": uf_code,
                    "uf_label": str(uf_data.get("uf_label", uf_code) or uf_code),
                    "income_mean": round(_safe_div(total_inc, hh_count), 2),
                    "work_pct": round(work_pct, 2),
                    "benefits_pct": round(benefits_pct, 2),
                    "previdencia_pct": round(previdencia_pct, 2),
                    "dependency_score": round(dependency_score, 2),
                }
            )
        uf_dependency_ranking.sort(key=lambda x: float(x.get("dependency_score", 0.0)), reverse=True)

        composition_by_band: Dict[str, object] = {}
        total_households_in_bands = sum(float(x.get("households", 0.0) or 0.0) for x in band_income_composition.values())
        for item in ranges:
            band_label = str(item["label"])
            band_data = band_income_composition.get(band_label, {})
            band_hh = float(band_data.get("households", 0.0) or 0.0) if isinstance(band_data, dict) else 0.0
            band_income = float(band_data.get("total_income", 0.0) or 0.0) if isinstance(band_data, dict) else 0.0
            band_sources = band_data.get("sources", {}) if isinstance(band_data, dict) else {}
            composition: Dict[str, float] = {}
            for cat in INCOME_CATEGORY_ORDER:
                if cat == "trabalho":
                    cat_total = float(band_sources.get("trabalho", 0.0) or 0.0) if isinstance(band_sources, dict) else 0.0
                else:
                    cat_total = (
                        sum(float(band_sources.get(src, 0.0) or 0.0) for src in INCOME_CATEGORIES.get(cat, []))
                        if isinstance(band_sources, dict)
                        else 0.0
                    )
                composition[cat] = round(100.0 * _safe_div(cat_total, band_income), 2) if band_income > 0 else 0.0
            composition_by_band[band_label] = {
                "households_pct": round(100.0 * _safe_div(band_hh, total_households_in_bands), 2)
                if total_households_in_bands > 0
                else 0.0,
                "income_mean": round(_safe_div(band_income, band_hh), 2) if band_hh > 0 else 0.0,
                "composition": composition,
            }

        income_composition_payload = {
            "income_composition_national": income_composition_national,
            "income_sources_detail": income_sources_detail,
            "uf_dependency_ranking": uf_dependency_ranking,
            "composition_by_band": composition_by_band,
        }
    
    return {
        "input": str(input_path),
        "target": target,
        "sm_target_month": sm_target_month,
        "sm_target_value": sm_target_nominal,
        "sm_mode": args.sm_mode,
        "uf_order": args.uf_order,
        "mode": pnad_mode,
        "dashboard_mode": pnad_mode,
        "pnad_mode": pnad_mode,
        "options": {
            "breakdown": bool(getattr(args, "breakdown", False)),
            "source_detail": bool(getattr(args, "source_detail", False)),
            "dependency_ranking": bool(getattr(args, "dependency_ranking", False)),
            "composition_by_band": bool(getattr(args, "composition_by_band", False)),
        },
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
        "sampling": {
            "ci_requested": bool((not args.unweighted) and (not args.no_ci)),
            "ci_effective": bool(use_ci),
            "ci_level": ci_level,
            "variance_method": "bootstrap_replicates_mse",
            "variance_formula": "var=(1/(R-1))*sum((theta_r-theta)^2)",
            "replicate_weight_base": "V1028",
            "replicate_weight_count": int(replicate_count),
            "replicate_weight_columns_detected": int(len(replicate_weight_cols)),
            "person_weight_assumption": "persons_weight_rep=persons_in_dom*household_rep_weight",
        },
        "dimension_labels": dimension_labels,
        "modes": modes_out,
        "total_households": int(len(households)),
        "total_income_mean": round(float(total_income_mean), 2) if is_anual_mode else None,
        "total_income_median": round(float(total_income_median), 2) if is_anual_mode else None,
        **income_composition_payload,
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
            "ci_requested": bool((not args.unweighted) and (not args.no_ci)),
            "ci_effective": bool(use_ci),
            "ci_level": ci_level,
            "replicate_weights_found": int(len(replicate_weight_cols)),
            "pnad_mode": pnad_mode,
            "income_source_cols_detected": list(income_source_cols.keys()) if income_source_cols else [],
        },
    }


def _print_dashboard_mode(
    payload: Dict[str, object], mode: str, *, no_color: bool = False, section: str = "all"
) -> None:
    use_color = _supports_color(no_color=no_color)
    term_cols = shutil.get_terminal_size((120, 24)).columns
    colors = _brazil_band_colors(len(payload.get("ranges", []) or []))
    gradients = _brazil_band_gradients(len(payload.get("ranges", []) or []))
    mode_data = payload["modes"][mode]
    nat = mode_data["national"]
    dashboard_mode = str(payload.get("dashboard_mode", payload.get("pnad_mode", "trimestral")) or "trimestral")
    is_anual_mode = dashboard_mode == "anual"
    income_composition_national = payload.get("income_composition_national", {})
    income_sources_detail = payload.get("income_sources_detail", {})
    uf_dependency_ranking = payload.get("uf_dependency_ranking", [])
    composition_by_band = payload.get("composition_by_band", {})
    show = lambda key: section in ("all", key)
    uf_name_width = 18
    max_uf_label_len = 0
    for key in (
        "top10_uf_income",
        "bottom10_uf_income",
        "top10_uf_population",
        "top10_uf_low_income",
        "top10_uf_high_income",
    ):
        rows = mode_data.get(key, [])
        if not isinstance(rows, list):
            continue
        for row in rows:
            if isinstance(row, dict):
                max_uf_label_len = max(max_uf_label_len, len(str(row.get("label", "")).strip()))
    if max_uf_label_len > 0:
        uf_name_width = max(18, min(26, max_uf_label_len + 1))

    if show("overview"):
        sm_ref = float(mode_data.get("sm_reference_value", payload.get("sm_target_value") or 0.0) or 0.0)
        sm_ref_month = str(mode_data.get("sm_reference_month", "") or "")
        sm_ref_min = mode_data.get("sm_reference_min")
        sm_ref_max = mode_data.get("sm_reference_max")
        ci_level = float(mode_data.get("sampling", {}).get("ci_level", payload.get("sampling", {}).get("ci_level", 0.95)))
        avg_sm = float(nat.get("avg_household_sm", 0.0) or 0.0)
        avg_sm_moe = nat.get("avg_household_sm_moe")
        if avg_sm_moe is not None:
            avg_sm_txt = f"{avg_sm:.3f} ± {float(avg_sm_moe):.3f} (IC {ci_level:.0%})"
        else:
            avg_sm_txt = f"{avg_sm:.3f}"
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
                f"Media SM: {avg_sm_txt} | "
                f"Mediana SM: {float(nat['median_household_sm']):.3f} | Gini(SM): {float(nat['gini_household_sm']):.3f}"
            ),
            f"SM referencia ({sm_ref_month}): {sm_ref_txt}",
        ]
        _panel("Visao Brasil", overview_lines, color="1;38;5;45", use_color=use_color)
        print(_colorize(" Distribuicao nacional por faixa", 1, use_color))
        for b in nat["bands"]:
            hp = float(b["households_pct"])
            pp = float(b["persons_pct"])
            hp_moe = b.get("households_pct_moe")
            pp_moe = b.get("persons_pct_moe")
            hp_txt = f"{hp:6.2f}%"
            pp_txt = f"{pp:6.2f}%"
            if hp_moe is not None:
                hp_txt = f"{hp:6.2f}%±{float(hp_moe):4.2f}"
            if pp_moe is not None:
                pp_txt = f"{pp:6.2f}%±{float(pp_moe):4.2f}"
            gi = payload["ranges"].index(b["range"]) % len(gradients)
            print(
                "  "
                + _badge(f"{b['range']:<8}", fg=16, bg=gradients[gi][-1], use_color=use_color)
                + f" dom={hp_txt:<14} {_gradient_bar(hp, width=20, palette=gradients[gi], use_color=use_color)}"
                + f"  pes={pp_txt:<14} {_gradient_bar(pp, width=8, palette=gradients[gi], use_color=use_color)}"
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
        if is_anual_mode and isinstance(income_composition_national, dict) and income_composition_national:
            print(_colorize(" Composicao nacional de renda (PNAD anual)", "1;38;5;214", use_color))
            for cat in INCOME_CATEGORY_ORDER:
                data = income_composition_national.get(cat, {})
                if not isinstance(data, dict):
                    continue
                pct = float(data.get("pct", 0.0) or 0.0)
                mean = float(data.get("mean", 0.0) or 0.0)
                label = str(data.get("label", INCOME_CATEGORY_LABELS.get(cat, cat)))
                bar = _gradient_bar(pct, width=22, palette=[22, 28, 34, 40, 46], use_color=use_color)
                print(f"  - {label:<24} {_fmt_brl(mean):>12}  {pct:6.2f}% {bar}")
            if isinstance(income_sources_detail, dict) and income_sources_detail:
                print(_colorize("  Fontes detalhadas (V500xA2)", "1;38;5;221", use_color))
                for src_key in INCOME_SOURCE_COLS.keys():
                    item = income_sources_detail.get(src_key, {})
                    if not isinstance(item, dict):
                        continue
                    src_mean = float(item.get("mean", 0.0) or 0.0)
                    src_pct = float(item.get("pct", 0.0) or 0.0)
                    rec_pct = float(item.get("recipients_pct", 0.0) or 0.0)
                    src_label = str(item.get("label", INCOME_SOURCE_LABELS.get(src_key, src_key)))
                    print(f"    · {src_label:<28} {_fmt_brl(src_mean):>12}  {src_pct:6.2f}%  recip={rec_pct:6.2f}%")
        print()

    if show("ranking"):
        print(_colorize(" Ranking horizontal de UFs", "1;38;5;51", use_color))
        left = [_colorize("  Top 10 UFs por renda (SM domiciliar)", "1;38;5;46", use_color)]
        right = [_colorize("  Top 10 UFs por populacao estimada", "1;38;5;33", use_color)]
        pop_total = float(nat["persons_total"]) or 1.0
        for i, u in enumerate(mode_data.get("top10_uf_income", []), start=1):
            val = float(u["avg_household_sm"])
            moe = u.get("avg_household_sm_moe")
            heat = _gradient_bar(min(val * 16, 100), width=8, palette=[22, 28, 34, 40, 46], use_color=use_color)
            val_txt = f"{val:6.3f} SM"
            if moe is not None:
                val_txt = f"{val:6.3f}±{float(moe):4.3f} SM"
            left.append(f"  {i:>2}. {u['label']:<{uf_name_width}} {val_txt:<17} {heat}")
        for i, u in enumerate(mode_data.get("top10_uf_population", []), start=1):
            ppl = float(u["persons_total"])
            share = 100.0 * _safe_div(ppl, pop_total)
            heat = _gradient_bar(min(share * 4, 100), width=8, palette=[17, 19, 21, 27, 33], use_color=use_color)
            right.append(f"  {i:>2}. {u['label']:<{uf_name_width}} {share:5.2f}% {heat}")
        _print_two_columns(left, right, width=58, gap=3)
        print("")
        print(_colorize("  Bottom 10 UFs por renda (SM)", "1;38;5;196", use_color))
        for i, u in enumerate(mode_data.get("bottom10_uf_income", []), start=1):
            val = float(u["avg_household_sm"])
            moe = u.get("avg_household_sm_moe")
            heat = _gradient_bar(min(val * 16, 100), width=10, palette=[52, 88, 124, 160, 196], use_color=use_color)
            val_txt = f"{val:6.3f} SM"
            if moe is not None:
                val_txt = f"{val:6.3f}±{float(moe):4.3f} SM"
            print(f"   {i:>2}. {u['label']:<{uf_name_width}} {val_txt:<17} {heat}")
        if is_anual_mode and isinstance(uf_dependency_ranking, list) and uf_dependency_ranking:
            print("")
            print(_colorize("  Ranking de dependencia por UF (beneficios + previdencia)", "1;38;5;220", use_color))
            print(
                "   # "
                + f"{'UF':<{uf_name_width}} {'dep%':>7} {'trab%':>7} {'benef%':>8} {'prev%':>7} {'media':>12}"
            )
            for i, row in enumerate(uf_dependency_ranking[:10], start=1):
                if not isinstance(row, dict):
                    continue
                dep = float(row.get("dependency_score", 0.0) or 0.0)
                work = float(row.get("work_pct", 0.0) or 0.0)
                ben = float(row.get("benefits_pct", 0.0) or 0.0)
                prev = float(row.get("previdencia_pct", 0.0) or 0.0)
                inc = float(row.get("income_mean", 0.0) or 0.0)
                dep_bar = _gradient_bar(dep, width=8, palette=[52, 88, 124, 160, 196], use_color=use_color)
                print(
                    f"  {i:>2}. {str(row.get('uf_label', '')):<{uf_name_width}} "
                    f"{dep:6.2f}% {work:6.2f}% {ben:7.2f}% {prev:6.2f}% {_fmt_brl(inc):>12} {dep_bar}"
                )
        print()

    if show("macro"):
        print(_colorize(" Macro-regioes do Brasil", "1;38;5;39", use_color))
        macro_list = mode_data.get("macro_regions", [])
        macro_map: Dict[str, Dict[str, object]] = {}
        if isinstance(macro_list, list):
            for mr in macro_list:
                if isinstance(mr, dict):
                    macro_map[str(mr.get("group", ""))] = mr

        for macro_name in [m for m in MACRO_REGION_ORDER if m != "Desconhecida"]:
            mr = macro_map.get(macro_name)
            if not isinstance(mr, dict):
                mr = {
                    "group": macro_name,
                    "label": macro_name,
                    "persons_total": 0.0,
                    "avg_household_sm": 0.0,
                    "bands": [],
                }
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
            print(f"  {i:>2}. {u['label']:<{uf_name_width}} pop={share:5.2f}%  mix={mix}")
        print()

    if show("demography"):
        print(_colorize(" Demografia detalhada (recortes com barras)", 33, use_color))
        demo = mode_data.get("demographics", {})
        dim_labels = payload.get("dimension_labels", {})
        dim_order = mode_data.get("dimensions", [])
        demog_bar_width = 16
        demog_label_cap = max(28, min(64, term_cols - 18 - demog_bar_width))
        for dim in dim_order:
            rows = demo.get(dim, [])
            if not rows:
                continue
            label = dim_labels.get(dim, dim)
            print(_colorize(f"  {label}", "1;38;5;117", use_color))

            if dim == "macro_region":
                by_label = {str(x.get("label", "")): float(x.get("pct", 0.0) or 0.0) for x in rows if isinstance(x, dict)}
                show_rows = [{"label": rg, "pct": by_label.get(rg, 0.0)} for rg in MACRO_REGION_ORDER if rg != "Desconhecida"]
                unknown_pct = 0.0
                known_labels = {x["label"] for x in show_rows}
                for k, v in by_label.items():
                    if k not in known_labels:
                        unknown_pct += float(v)
                if unknown_pct > 0:
                    show_rows.append({"label": "Desconhecida", "pct": unknown_pct})
                hidden_pct = 0.0
            elif dim == "age":
                known_rows = []
                missing_pct = 0.0
                for x in rows:
                    lbl = str(x.get("label", ""))
                    pct = float(x.get("pct", 0.0) or 0.0)
                    if _is_missing_label(lbl):
                        missing_pct += pct
                    else:
                        known_rows.append({"label": lbl, "pct": pct})
                known_rows.sort(key=lambda r: _age_label_sort_key(str(r.get("label", ""))))
                show_rows = known_rows
                hidden_pct = 0.0
                if missing_pct > 0:
                    show_rows.append({"label": "Sem idade", "pct": missing_pct})
            else:
                known_rows = []
                missing_pct = 0.0
                for x in rows:
                    lbl = str(x.get("label", ""))
                    pct = float(x.get("pct", 0.0) or 0.0)
                    if _is_missing_label(lbl):
                        missing_pct += pct
                    else:
                        known_rows.append({"label": lbl, "pct": pct})
                show_rows = known_rows[:6]
                shown_known_pct = sum(float(x["pct"]) for x in show_rows)
                hidden_pct = max(0.0, 100.0 - shown_known_pct - missing_pct)
                if missing_pct > 0:
                    show_rows.append({"label": "Sem informacao", "pct": missing_pct})

            labels_out = [
                _compact_dim_label(dim, str(row.get("label", "")), max_len=demog_label_cap)
                for row in show_rows
            ]
            demog_label_width = min(
                demog_label_cap,
                max(20, max((len(x) for x in labels_out), default=20)),
            )

            for row, lbl in zip(show_rows, labels_out):
                pct = float(row.get("pct", 0.0) or 0.0)
                bar = _gradient_bar(
                    pct,
                    width=demog_bar_width,
                    palette=[22, 28, 34, 40, 46],
                    use_color=use_color,
                )
                print(f"   - {lbl:<{demog_label_width}} {pct:5.1f}% {bar}")

            if hidden_pct > 0.05:
                other_bar = _gradient_bar(
                    hidden_pct,
                    width=demog_bar_width,
                    palette=[239, 242, 245, 248, 251],
                    use_color=use_color,
                )
                print(f"   - {'Outros':<{demog_label_width}} {hidden_pct:5.1f}% {other_bar}")
            print("")
        print("")

    if show("pyramid"):
        print(_colorize(" Piramide etaria (sexo x idade)", "1;38;5;45", use_color))
        pyramid = mode_data.get("age_pyramid", [])
        if not isinstance(pyramid, list) or not pyramid:
            print("  Sem dados suficientes para piramide etaria.\n")
        else:
            max_pct = 0.0
            for row in pyramid:
                if not isinstance(row, dict):
                    continue
                max_pct = max(max_pct, float(row.get("female_pct", 0.0) or 0.0), float(row.get("male_pct", 0.0) or 0.0))
            max_pct = max(max_pct, 1.0)
            width = 16
            print(
                "  "
                + _colorize("Mulher".rjust(width), "1;38;5;226", use_color)
                + " "
                + "Idade".center(8)
                + " "
                + _colorize("Homem".ljust(width), "1;38;5;21", use_color)
                + "   %F/%M"
            )
            print("  " + "─" * (width * 2 + 19))
            other_total_pct = 0.0
            for row in pyramid:
                if not isinstance(row, dict):
                    continue
                age_lbl = str(row.get("age", ""))
                female_pct = float(row.get("female_pct", 0.0) or 0.0)
                male_pct = float(row.get("male_pct", 0.0) or 0.0)
                other_total_pct += float(row.get("other_pct", 0.0) or 0.0)

                f_len = int(round(width * female_pct / max_pct))
                m_len = int(round(width * male_pct / max_pct))
                f_len = max(0, min(width, f_len))
                m_len = max(0, min(width, m_len))

                left = " " * (width - f_len) + _colorize("█" * f_len, "1;38;5;226", use_color)
                right = _colorize("█" * m_len, "1;38;5;21", use_color) + " " * (width - m_len)
                print(f"  {left} {age_lbl:^8} {right}  {female_pct:4.1f}%/{male_pct:4.1f}%")
            if other_total_pct > 0.01:
                print(f"  Outros/sem info de sexo: {other_total_pct:.2f}%")
            print("")

    if show("cross"):
        print(_colorize(" Cruzamentos principais x faixas de SM", 34, use_color))
        cross = mode_data.get("cross", {})
        dim_labels = payload.get("dimension_labels", {})
        chosen_dims = ["sex", "race", "education", "age", "capital", "macro_region"]
        max_label_len_by_dim = {
            "education": 28,
            "occupation_status": 28,
        }
        for dim in chosen_dims:
            key = f"{dim}_by_band"
            rows = cross.get(key, [])
            if not rows:
                continue
            print(_colorize(f"  {dim_labels.get(dim, dim)}", "1;38;5;117", use_color))
            if dim == "age":
                rows_iter = sorted(
                    [r for r in rows if isinstance(r, dict)],
                    key=lambda r: _age_label_sort_key(str(r.get("label", ""))),
                )
            elif dim == "macro_region":
                row_list = [r for r in rows if isinstance(r, dict)]
                by_label = {str(r.get("label", "")): r for r in row_list}

                def _zero_cross_row(label: str) -> Dict[str, object]:
                    return {
                        "label": label,
                        "total": 0.0,
                        "bands": {
                            str(b): {"value": 0.0, "pct_within_label": 0.0}
                            for b in payload["ranges"]
                        },
                    }

                rows_iter = []
                used_labels = set()
                for rg in [x for x in MACRO_REGION_ORDER if x != "Desconhecida"]:
                    row = by_label.get(rg) or _zero_cross_row(rg)
                    rows_iter.append(row)
                    used_labels.add(rg)

                for r in row_list:
                    lbl = str(r.get("label", ""))
                    if lbl in used_labels:
                        continue
                    rows_iter.append(r)
            elif dim == "education":
                rows_iter = [r for r in rows if isinstance(r, dict)][:8]
            else:
                rows_iter = [r for r in rows if isinstance(r, dict)][:4]

            for row in rows_iter:
                parts = []
                for b in payload["ranges"]:
                    pct = float(row["bands"][b]["pct_within_label"])
                    bi = payload["ranges"].index(b) % len(gradients)
                    parts.append(
                        f"{b}:{pct:4.1f}% {_gradient_bar(pct, width=3, palette=gradients[bi], use_color=use_color)}"
                    )
                lbl = _compact_dim_label(dim, str(row.get("label", "")), max_len=max_label_len_by_dim.get(dim, 28))
                print(f"   - {lbl:<28} {' | '.join(parts)}")
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
                left.append(f"  {i:>2}. {u['label']:<{uf_name_width}} {pct:5.2f}% {bar}")
            for i, u in enumerate(mode_data.get("top10_uf_high_income", []), start=1):
                pct = _band_pct(u, high_label)
                bar = _gradient_bar(pct, width=8, palette=[248, 250, 252, 254, 15], use_color=use_color)
                right.append(f"  {i:>2}. {u['label']:<{uf_name_width}} {pct:5.2f}% {bar}")
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
            samp = payload.get("sampling", {})
            if isinstance(samp, dict):
                print(
                    f"  amostral(ci_effective={samp.get('ci_effective')}, "
                    f"ci_level={samp.get('ci_level')}, reps={samp.get('replicate_weight_columns_detected')})"
                )
        print()


def _print_income_composition_pretty(payload: Dict[str, object], *, no_color: bool = False) -> None:
    """Print income composition analysis for anual mode (Dashboard v2.0)"""
    use_color = _supports_color(no_color=no_color)
    
    # National income composition
    national_comp = payload.get("income_composition_national", {})
    if national_comp:
        print(_colorize("\n╔══════════════════════════════════════════════════════════════════════════════╗", "1;38;5;214", use_color))
        print(_colorize("║                    COMPOSIÇÃO DE RENDA NACIONAL (PNAD ANUAL)                 ║", "1;38;5;214", use_color))
        print(_colorize("╚══════════════════════════════════════════════════════════════════════════════╝", "1;38;5;214", use_color))
        print("")
        
        # Colors for income categories
        cat_colors = {
            "trabalho": "1;38;5;46",  # Green for work
            "beneficios_sociais": "1;38;5;196",  # Red for social benefits
            "previdencia": "1;38;5;208",  # Orange for pensions
            "seguro": "1;38;5;226",  # Yellow for insurance
            "transferencias_privadas": "1;38;5;39",  # Blue for private transfers
            "capital": "1;38;5;15",  # White for capital
        }
        
        for cat in ["trabalho", "beneficios_sociais", "previdencia", "seguro", "transferencias_privadas", "capital"]:
            data = national_comp.get(cat, {})
            if not data:
                continue
            label = str(data.get("label", cat))
            mean = float(data.get("mean", 0.0) or 0.0)
            pct = float(data.get("pct", 0.0) or 0.0)
            bar_width = 40
            bar_fill = int(round(bar_width * pct / 100.0))
            bar_fill = max(0, min(bar_width, bar_fill))
            bar = "█" * bar_fill + "░" * (bar_width - bar_fill)
            color = cat_colors.get(cat, "1;38;5;250")
            print(f"  {_colorize(label.ljust(22), color, use_color)} {_colorize(bar, color, use_color)} {pct:5.1f}% (R$ {mean:,.2f})")
        print("")
    
    # Income sources detail
    sources_detail = payload.get("income_sources_detail", {})
    if sources_detail:
        print(_colorize(" Detalhamento por Fonte de Renda:", "1;38;5;117", use_color))
        for src_key in ["trabalho", "bpc_loas", "bolsa_familia", "outros_sociais", "aposentadoria_pensao", 
                        "seguro_desemprego", "pensao_doacao", "aluguel", "outros_capital"]:
            data = sources_detail.get(src_key, {})
            if not data:
                continue
            label = str(data.get("label", src_key))
            mean = float(data.get("mean", 0.0) or 0.0)
            pct = float(data.get("pct", 0.0) or 0.0)
            recipients_pct = data.get("recipients_pct")
            recipients_txt = f" ({recipients_pct:.1f}% recebem)" if recipients_pct is not None else ""
            bar_width = 30
            bar_fill = int(round(bar_width * pct / 100.0))
            bar_fill = max(0, min(bar_width, bar_fill))
            bar = "▓" * bar_fill + "░" * (bar_width - bar_fill)
            print(f"    {label.ljust(24)} {bar} {pct:5.2f}% R$ {mean:,.2f}{recipients_txt}")
        print("")
    
    # UF dependency ranking
    uf_ranking = payload.get("uf_dependency_ranking", [])
    if uf_ranking:
        print(_colorize("\n╔══════════════════════════════════════════════════════════════════════════════╗", "1;38;5;196", use_color))
        print(_colorize("║             RANKING DE DEPENDÊNCIA POR UF (% não-trabalho)                   ║", "1;38;5;196", use_color))
        print(_colorize("╚══════════════════════════════════════════════════════════════════════════════╝", "1;38;5;196", use_color))
        print("")
        print(_colorize("  UF                  Renda Média   %Trabalho  %Benefícios  %Previd.  Score Dep.", "1;38;5;250", use_color))
        print("  " + "─" * 76)
        
        for i, uf in enumerate(uf_ranking[:15]):  # Show top 15
            uf_label = str(uf.get("uf_label", "")).ljust(18)
            income_mean = float(uf.get("income_mean", 0.0) or 0.0)
            work_pct = float(uf.get("work_pct", 0.0) or 0.0)
            benefits_pct = float(uf.get("benefits_pct", 0.0) or 0.0)
            previdencia_pct = float(uf.get("previdencia_pct", 0.0) or 0.0)
            dep_score = float(uf.get("dependency_score", 0.0) or 0.0)
            
            # Color based on dependency score (higher = more red)
            if dep_score > 50:
                row_color = "1;38;5;196"  # Red
            elif dep_score > 40:
                row_color = "1;38;5;208"  # Orange
            elif dep_score > 30:
                row_color = "1;38;5;226"  # Yellow
            else:
                row_color = "1;38;5;46"  # Green
            
            rank = f"{i+1:2}."
            print(f"  {_colorize(rank, row_color, use_color)} {uf_label} R$ {income_mean:>8,.2f}    {work_pct:5.1f}%      {benefits_pct:5.1f}%     {previdencia_pct:5.1f}%   {_colorize(f'{dep_score:5.1f}', row_color, use_color)}")
        
        if len(uf_ranking) > 15:
            print(f"  ... e mais {len(uf_ranking) - 15} UFs")
        print("")
    
    # Composition by income band
    band_comp = payload.get("composition_by_band", {})
    if band_comp:
        print(_colorize("\n╔══════════════════════════════════════════════════════════════════════════════╗", "1;38;5;33", use_color))
        print(_colorize("║              COMPOSIÇÃO DE RENDA POR FAIXA DE SALÁRIO MÍNIMO                 ║", "1;38;5;33", use_color))
        print(_colorize("╚══════════════════════════════════════════════════════════════════════════════╝", "1;38;5;33", use_color))
        print("")
        print(_colorize("  Faixa SM     %Dom.    Renda Média   %Trab.  %Benef.  %Prev.  %Seg.  %Transf. %Cap.", "1;38;5;250", use_color))
        print("  " + "─" * 80)
        
        for band_label, data in band_comp.items():
            if not isinstance(data, dict):
                continue
            hh_pct = float(data.get("households_pct", 0.0) or 0.0)
            income_mean = float(data.get("income_mean", 0.0) or 0.0)
            comp = data.get("composition", {})
            
            work = float(comp.get("trabalho", 0.0) or 0.0)
            benefits = float(comp.get("beneficios_sociais", 0.0) or 0.0)
            prev = float(comp.get("previdencia", 0.0) or 0.0)
            seg = float(comp.get("seguro", 0.0) or 0.0)
            transf = float(comp.get("transferencias_privadas", 0.0) or 0.0)
            cap = float(comp.get("capital", 0.0) or 0.0)
            
            # Highlight low work percentage (poverty trap indicator)
            if work < 50:
                work_color = "1;38;5;196"
            elif work < 70:
                work_color = "1;38;5;226"
            else:
                work_color = "1;38;5;46"
            
            print(f"  {band_label.ljust(10)} {hh_pct:6.1f}%  R$ {income_mean:>9,.2f}   {_colorize(f'{work:5.1f}%', work_color, use_color)}  {benefits:5.1f}%  {prev:5.1f}%  {seg:4.1f}%   {transf:5.1f}%  {cap:4.1f}%")
        
        print("")
        print(_colorize("  💡 Hipótese validada: nas faixas mais baixas, maior % vem de benefícios/previdência", "1;38;5;226", use_color))
        print("")


def _print_dashboard_pretty(payload: Dict[str, object], *, no_color: bool = False) -> None:
    use_color = _supports_color(no_color=no_color)
    title_style = "1;38;5;46"
    pnad_mode = payload.get("pnad_mode", "trimestral")
    mode_label = "ANUAL (Visita 5)" if pnad_mode == "anual" else "TRIMESTRAL"
    
    print(_brazil_flag_strip(use_color))
    header = [
        _colorize(f"PNAD DASHBOARD ECONOMICO - {mode_label}", title_style, use_color),
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
        # Show income source columns detected for anual mode
        src_cols = md.get("income_source_cols_detected", [])
        if src_cols:
            header.append(f"Fontes de renda detectadas: {len(src_cols)} colunas V50xxA2")
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
            "[3] macro | [4] population | [5] demography | [6] pyramid | [7] cross | [8] meta | [9] insights | [a] all | [q] sair"
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
            section = "pyramid"
            continue
        if ans == "7":
            section = "cross"
            continue
        if ans == "8":
            section = "meta"
            continue
        if ans == "9":
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
    scope_errors: List[Dict[str, str]] = []

    def record_scope_error(scope: str, exc: Exception) -> None:
        msg = str(exc)
        scope_errors.append({"scope": scope, "error": msg})
        print(f"WARN: {scope} sync failed: {msg}", file=sys.stderr)

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

    with_anual = bool(args.with_anual or args.full)
    with_censo = bool(args.with_censo or args.full)
    with_tse = bool(args.with_tse or args.full)

    # ---------------- Trimestral PNADC (existing behavior) ----------------
    root_hrefs: List[str] = []
    needs_trimestral_index = (not args.no_docs) or (not args.no_raw)
    if needs_trimestral_index:
        try:
            root_hrefs = _list_hrefs(base_url)
        except Exception as exc:
            print(f"ERROR: could not list IBGE base URL: {exc}", file=sys.stderr)
            return 2

    if not args.no_docs:
        try:
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
                _extract_zip_all(docs_dir / "Dicionario_e_input_20221031.zip", docs_dir, quiet=args.quiet)

            # Refresh monthly nominal minimum wage series (BCB SGS 1619).
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
                        _dd, mm, yyyy = d.split("/")
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
        except Exception as exc:
            record_scope_error("trimestral_docs", exc)

    if not args.no_raw:
        try:
            years = sorted(
                int(h.rstrip("/")) for h in root_hrefs if re.match(r"^\d{4}/$", h) and h.rstrip("/").isdigit()
            )
            if not years:
                raise ValueError("no year folders found in IBGE Microdados index")
            selected_year = int(args.year) if args.year else years[-1]
            if selected_year not in years:
                raise ValueError(f"year {selected_year} not available on IBGE index")

            year_url = f"{base_url}{selected_year}/?C=N;O=D"
            year_hrefs = _list_hrefs(year_url)
            zip_names = sorted({h for h in year_hrefs if PNADC_ZIP_RE.match(h)})
            latest_by_quarter = _group_latest_by_quarter(zip_names)
            if not latest_by_quarter:
                raise ValueError(f"no PNADC zip files found for year {selected_year}")

            if args.quarter:
                q = int(args.quarter)
                pick = latest_by_quarter.get(q)
                if not pick:
                    raise ValueError(f"no file for quarter {q} in year {selected_year}")
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
        except Exception as exc:
            record_scope_error("trimestral_raw", exc)

    # ---------------- PNADC Anual (Visita 5) ----------------
    anual_payload: Dict[str, object] = {
        "enabled": with_anual,
        "base_url": args.anual_base_url,
        "raw_dir": args.anual_raw_dir,
        "docs_dir": args.anual_docs_dir,
        "year": None,
        "raw_files": [],
        "raw_txt": [],
        "docs_files": [],
    }

    if with_anual:
        anual_base = args.anual_base_url.rstrip("/") + "/"
        anual_raw_dir = Path(args.anual_raw_dir)
        anual_docs_dir = Path(args.anual_docs_dir)
        anual_selected_year: Optional[int] = None

        try:
            if not args.no_anual_docs:
                doc_hrefs = _list_hrefs(anual_base + "Documentacao/")
                doc_files = sorted([h for h in doc_hrefs if not h.endswith("/")])
                for name in doc_files:
                    sync_one(anual_base + "Documentacao/" + name, anual_docs_dir / name)
                anual_payload["docs_files"] = doc_files

            if not args.no_anual_raw:
                data_hrefs = _list_hrefs(anual_base + "Dados/")
                zip_names = sorted([h for h in data_hrefs if PNADC_ANUAL_VISITA5_ZIP_RE.match(h)])
                latest_by_year = _group_latest_anual_by_year(zip_names)
                years = sorted(latest_by_year.keys())
                if not years:
                    raise ValueError("no PNADC Anual Visita 5 zip files found")

                if args.anual_year:
                    y = int(args.anual_year)
                    if y not in latest_by_year:
                        raise ValueError(f"no PNADC Anual Visita 5 file for year {y}")
                    selected_years = [y]
                elif args.anual_all_years:
                    selected_years = years
                else:
                    selected_years = [years[-1]]

                anual_selected_year = selected_years[-1]
                anual_files: List[str] = []
                anual_txt: List[str] = []
                for y in selected_years:
                    file_name = str(latest_by_year[y]["name"])
                    anual_files.append(file_name)
                    zip_url = f"{anual_base}Dados/{file_name}"
                    zip_dest = anual_raw_dir / file_name
                    ev = sync_one(zip_url, zip_dest)
                    if not args.no_extract and zip_dest.exists():
                        txt_path = _extract_single_txt(zip_dest, anual_raw_dir, quiet=args.quiet)
                        if txt_path:
                            anual_txt.append(str(txt_path))
                            sync_events.append(
                                {
                                    "url": zip_url,
                                    "path": str(txt_path),
                                    "status": "extracted" if ev["status"] == "downloaded" else "present",
                                }
                            )

                anual_payload["year"] = anual_selected_year
                anual_payload["raw_files"] = anual_files
                anual_payload["raw_txt"] = anual_txt
        except Exception as exc:
            record_scope_error("anual_visita5", exc)

    # ---------------- Censo 2022 agregados de renda do responsavel ----------------
    censo_payload: Dict[str, object] = {
        "enabled": with_censo,
        "base_url": args.censo_base_url,
        "folder": args.censo_folder,
        "dir": args.censo_dir,
        "files": [],
        "extracted": [],
    }

    if with_censo:
        censo_base = args.censo_base_url.rstrip("/") + "/"
        censo_folder = args.censo_folder.strip("/") + "/"
        censo_dir = Path(args.censo_dir)
        try:
            hrefs = _list_hrefs(censo_base + censo_folder)
            files = sorted([h for h in hrefs if not h.endswith("/")])
            extracted_files: List[str] = []
            for name in files:
                url = censo_base + censo_folder + name
                dest = censo_dir / name
                ev = sync_one(url, dest)
                if not args.no_extract and str(name).lower().endswith(".zip") and dest.exists():
                    out = _extract_zip_all(dest, censo_dir, quiet=args.quiet)
                    extracted_files.extend(str(x) for x in out)
                    sync_events.append(
                        {
                            "url": url,
                            "path": str(dest),
                            "status": "extracted" if ev["status"] == "downloaded" else "present",
                        }
                    )
            censo_payload["files"] = files
            censo_payload["extracted"] = extracted_files
        except Exception as exc:
            record_scope_error("censo_renda_responsavel", exc)

    # ---------------- TSE dados abertos (perfil do eleitorado) ----------------
    tse_payload: Dict[str, object] = {
        "enabled": with_tse,
        "api_base": args.tse_api_base,
        "query": args.tse_query,
        "dir": args.tse_dir,
        "resources_found": 0,
        "resources_selected": [],
        "extracted": [],
    }

    if with_tse:
        tse_dir = Path(args.tse_dir)
        try:
            resources = _fetch_tse_resources(args.tse_api_base, args.tse_query, rows=int(args.tse_rows))
            selected = _select_tse_resources(resources, year=args.tse_year, all_years=bool(args.tse_all_years))
            tse_payload["resources_found"] = len(resources)
            tse_payload["resources_selected"] = selected

            extracted_files: List[str] = []
            for item in selected:
                url = str(item.get("url", "") or "")
                if not url:
                    continue
                name = Path(urlparse(url).path).name or f"tse_{item.get('kind','dataset')}_{item.get('year','')}.zip"
                dest = tse_dir / name
                ev = sync_one(url, dest)
                if not args.no_extract and dest.exists() and name.lower().endswith(".zip"):
                    out = _extract_zip_all(dest, tse_dir, quiet=args.quiet)
                    extracted_files.extend(str(x) for x in out)
                    sync_events.append(
                        {
                            "url": url,
                            "path": str(dest),
                            "status": "extracted" if ev["status"] == "downloaded" else "present",
                        }
                    )
            tse_payload["extracted"] = extracted_files
        except Exception as exc:
            record_scope_error("tse_eleitorado", exc)

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
        "scopes": {
            "trimestral": {
                "enabled": (not args.no_docs) or (not args.no_raw),
                "docs_enabled": not args.no_docs,
                "raw_enabled": not args.no_raw,
            },
            "anual_visita5": anual_payload,
            "censo_renda_responsavel": censo_payload,
            "tse_eleitorado": tse_payload,
        },
        "errors": scope_errors,
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
    req = Request(args.url, headers={"User-Agent": TOOL_USER_AGENT})
    with _urlopen_retry_ssl(req, timeout=120) as resp:
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
        from npv_deflators import build_deflators  # type: ignore
        from npv_deflators import read_ipca_csv
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
        ci_level = _normalize_ci_level(args.ci_level)
    except Exception as exc:
        print(f"ERROR: invalid --ci-level: {exc}", file=sys.stderr)
        return 2
    use_ci = (not args.unweighted) and (not args.no_ci)
    replicate_weight_cols: List[str] = []
    replicate_count = 0

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
            if use_ci:
                replicate_weight_cols = _detect_replicate_weight_cols(headers, base_prefix="V1028")
                replicate_count = len(replicate_weight_cols)

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
            if use_ci and replicate_count < 2:
                use_ci = False

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
                    rep_household_weights: List[float] = []
                    if use_ci:
                        for rep_col in replicate_weight_cols:
                            rep_raw = row.get(rep_col, "")
                            rep_val = _parse_float(rep_raw)
                            rep_household_weights.append(float(rep_val) if rep_val is not None and rep_val > 0 else 0.0)
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
                        "rep_household_weights": rep_household_weights,
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
            rep_households_total = [0.0] * replicate_count if use_ci else []
            rep_persons_total = [0.0] * replicate_count if use_ci else []
            rep_sum_ratio = [0.0] * replicate_count if use_ci else []
            rep_bands = (
                {
                    str(item["label"]): {
                        "households": [0.0] * replicate_count,
                        "persons": [0.0] * replicate_count,
                    }
                    for item in ranges
                }
                if use_ci
                else {}
            )
            g = {
                "group": gkey,
                "label": gname,
                "households_total": 0.0,
                "persons_total": 0.0,
                "households_sample": 0,
                "persons_sample": 0,
                "sum_ratio_household_weighted": 0.0,
                "bands": {str(item["label"]): {"households": 0, "persons": 0} for item in ranges},
                "rep_households_total": rep_households_total,
                "rep_persons_total": rep_persons_total,
                "rep_sum_ratio_household_weighted": rep_sum_ratio,
                "rep_bands": rep_bands,
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

        if use_ci:
            rep_weights = h.get("rep_household_weights")
            if isinstance(rep_weights, list) and len(rep_weights) == replicate_count:
                rep_households_total = g["rep_households_total"]
                rep_persons_total = g["rep_persons_total"]
                rep_sum_ratio = g["rep_sum_ratio_household_weighted"]
                rep_band = g["rep_bands"][band]
                rep_band_households = rep_band["households"]
                rep_band_persons = rep_band["persons"]
                for j, rep_hh_w in enumerate(rep_weights):
                    wj = float(rep_hh_w)
                    if wj <= 0:
                        continue
                    rep_pp_w = float(persons) * wj
                    rep_households_total[j] += wj
                    rep_persons_total[j] += rep_pp_w
                    rep_sum_ratio[j] += ratio_sm * wj
                    rep_band_households[j] += wj
                    rep_band_persons[j] += rep_pp_w

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
        avg_household_sm = float(g["sum_ratio_household_weighted"]) / htot if htot else 0.0

        rep_households_total = g.get("rep_households_total", [])
        rep_persons_total = g.get("rep_persons_total", [])
        rep_sum_ratio = g.get("rep_sum_ratio_household_weighted", [])

        avg_sm_ci: Optional[Dict[str, float]] = None
        if use_ci and isinstance(rep_households_total, list) and isinstance(rep_sum_ratio, list):
            avg_reps = [
                _safe_div(float(rep_sum_ratio[j]), float(rep_households_total[j]))
                if float(rep_households_total[j]) > 0
                else 0.0
                for j in range(replicate_count)
            ]
            avg_sm_ci = _ci_from_replicates(avg_household_sm, avg_reps, ci_level=ci_level)

        bands_out = []
        for item in ranges:
            label = str(item["label"])
            b = g["bands"][label]
            bh = float(b["households"])
            bp = float(b["persons"])
            hp = round((100.0 * bh / htot), 4) if htot else 0.0
            pp = round((100.0 * bp / ptot), 4) if ptot else 0.0
            row_out: Dict[str, object] = {
                "range": label,
                "households": bh,
                "households_pct": hp,
                "persons": bp,
                "persons_pct": pp,
            }
            if use_ci:
                rep_band = g.get("rep_bands", {}).get(label, {})
                rep_bh = rep_band.get("households", []) if isinstance(rep_band, dict) else []
                rep_bp = rep_band.get("persons", []) if isinstance(rep_band, dict) else []
                if (
                    isinstance(rep_households_total, list)
                    and isinstance(rep_persons_total, list)
                    and isinstance(rep_bh, list)
                    and isinstance(rep_bp, list)
                    and len(rep_households_total) == replicate_count
                    and len(rep_persons_total) == replicate_count
                    and len(rep_bh) == replicate_count
                    and len(rep_bp) == replicate_count
                ):
                    hh_rep = [
                        100.0 * _safe_div(float(rep_bh[j]), float(rep_households_total[j]))
                        if float(rep_households_total[j]) > 0
                        else 0.0
                        for j in range(replicate_count)
                    ]
                    pp_rep = [
                        100.0 * _safe_div(float(rep_bp[j]), float(rep_persons_total[j]))
                        if float(rep_persons_total[j]) > 0
                        else 0.0
                        for j in range(replicate_count)
                    ]
                    hh_ci = _ci_from_replicates(float(hp), hh_rep, ci_level=ci_level, clamp=(0.0, 100.0))
                    pp_ci = _ci_from_replicates(float(pp), pp_rep, ci_level=ci_level, clamp=(0.0, 100.0))
                    if hh_ci:
                        row_out.update(
                            {
                                "households_pct_se": round(float(hh_ci["se"]), 6),
                                "households_pct_moe": round(float(hh_ci["moe"]), 6),
                                "households_pct_ci_low": round(float(hh_ci["ci_low"]), 6),
                                "households_pct_ci_high": round(float(hh_ci["ci_high"]), 6),
                            }
                        )
                    if pp_ci:
                        row_out.update(
                            {
                                "persons_pct_se": round(float(pp_ci["se"]), 6),
                                "persons_pct_moe": round(float(pp_ci["moe"]), 6),
                                "persons_pct_ci_low": round(float(pp_ci["ci_low"]), 6),
                                "persons_pct_ci_high": round(float(pp_ci["ci_high"]), 6),
                            }
                        )
            bands_out.append(row_out)

        group_out: Dict[str, object] = {
            "group": g["group"],
            "label": g["label"],
            "households_total": htot,
            "persons_total": ptot,
            "households_sample": int(g["households_sample"]),
            "persons_sample": int(g["persons_sample"]),
            "avg_household_sm": round(avg_household_sm, 6),
            "bands": bands_out,
        }
        if avg_sm_ci:
            group_out.update(
                {
                    "avg_household_sm_se": round(float(avg_sm_ci["se"]), 6),
                    "avg_household_sm_moe": round(float(avg_sm_ci["moe"]), 6),
                    "avg_household_sm_ci_low": round(float(avg_sm_ci["ci_low"]), 6),
                    "avg_household_sm_ci_high": round(float(avg_sm_ci["ci_high"]), 6),
                }
            )
        groups_out.append(group_out)

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
        "sampling": {
            "ci_enabled": bool(use_ci),
            "ci_level": ci_level,
            "variance_method": "bootstrap_replicates_mse",
            "variance_formula": "var=(1/(R-1))*sum((theta_r-theta)^2)",
            "replicate_weight_base": "V1028",
            "replicate_weight_count": int(replicate_count),
            "replicate_weight_columns_detected": int(len(replicate_weight_cols)),
            "person_weight_assumption": "persons_weight_rep=persons_in_dom*household_rep_weight",
        },
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
            "ci_requested": bool((not args.unweighted) and (not args.no_ci)),
            "ci_effective": bool(use_ci),
            "ci_level": ci_level,
            "replicate_weights_found": int(len(replicate_weight_cols)),
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


def _strip_sql_comments(sql: str) -> str:
    no_block = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    lines = []
    for ln in no_block.splitlines():
        if "--" in ln:
            ln = ln.split("--", 1)[0]
        lines.append(ln)
    return "\n".join(lines)


def _is_read_only_sql(sql: str) -> bool:
    cleaned = _strip_sql_comments(sql).strip()
    if not cleaned:
        return False

    forbidden = re.compile(
        r"\b(?:INSERT|UPDATE|DELETE|REPLACE|DROP|ALTER|CREATE|ATTACH|DETACH|VACUUM|REINDEX|ANALYZE|"
        r"BEGIN|COMMIT|ROLLBACK|SAVEPOINT|RELEASE)\b",
        flags=re.IGNORECASE,
    )
    if forbidden.search(cleaned):
        return False

    statements = [s.strip() for s in cleaned.split(";") if s.strip()]
    if not statements:
        return False
    for stmt in statements:
        m = re.match(r"^([A-Za-z_]+)", stmt)
        if not m:
            return False
        head = m.group(1).upper()
        if head not in {"SELECT", "WITH", "PRAGMA", "EXPLAIN"}:
            return False
    return True


def _read_query_sql(args: argparse.Namespace) -> str:
    sql_cli = str(args.sql or "").strip()
    sql_file = str(args.sql_file or "").strip()
    if sql_cli and sql_file:
        raise ValueError("use either --sql or --sql-file, not both")
    if sql_file:
        path = Path(sql_file)
        if not path.exists():
            raise ValueError(f"sql file not found: {path}")
        return path.read_text(encoding="utf-8")
    if sql_cli:
        return sql_cli
    if not sys.stdin.isatty():
        return sys.stdin.read()
    raise ValueError("missing SQL. Use --sql, --sql-file, or pipe SQL via stdin")


def _cell_text(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, float):
        return f"{value:.10g}"
    return str(value)


def _truncate_cell(value: str, width: int) -> str:
    if width <= 1:
        return value[:width]
    if len(value) <= width:
        return value
    return value[: width - 1] + "…"


def _format_table(rows: Sequence[Dict[str, object]], columns: Sequence[str], *, max_col_width: int = 48) -> str:
    cols = [str(c) for c in columns]
    if not cols:
        return "(sem colunas)"

    widths = [len(c) for c in cols]
    matrix: List[List[str]] = []
    for row in rows:
        row_cells: List[str] = []
        for i, c in enumerate(cols):
            txt = _cell_text(row.get(c))
            row_cells.append(txt)
            widths[i] = min(max(widths[i], len(txt)), max_col_width)
        matrix.append(row_cells)

    widths = [max(1, min(w, max_col_width)) for w in widths]
    sep = "+-" + "-+-".join("-" * w for w in widths) + "-+"
    header = "| " + " | ".join(cols[i].ljust(widths[i]) for i in range(len(cols))) + " |"
    out = [sep, header, sep]
    for row_cells in matrix:
        out.append(
            "| "
            + " | ".join(_truncate_cell(row_cells[i], widths[i]).ljust(widths[i]) for i in range(len(cols)))
            + " |"
        )
    out.append(sep)
    return "\n".join(out)


def cmd_query(args: argparse.Namespace) -> int:
    try:
        sql = _read_query_sql(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"ERROR: sqlite db not found: {db_path}", file=sys.stderr)
        return 2

    if not args.allow_write and not _is_read_only_sql(sql):
        print(
            "ERROR: only read-only SQL is allowed by default. "
            "Use SELECT/WITH/PRAGMA/EXPLAIN or pass --allow-write explicitly.",
            file=sys.stderr,
        )
        return 2

    started = time.perf_counter()
    conn: Optional[sqlite3.Connection] = None
    replicate_cols_detected = 0
    try:
        if args.allow_write:
            conn = sqlite3.connect(db_path, timeout=float(args.timeout))
        else:
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=float(args.timeout))
        conn.row_factory = sqlite3.Row
        with conn:
            cur = conn.cursor()
            cur.execute(sql)
            columns = [str(d[0]) for d in (cur.description or [])]
            rows: List[Dict[str, object]] = []
            truncated = False
            if columns:
                limit = max(1, int(args.max_rows))
                fetched = cur.fetchmany(limit + 1)
                if len(fetched) > limit:
                    truncated = True
                    fetched = fetched[:limit]
                rows = [{k: row[k] for k in columns} for row in fetched]
            else:
                if args.allow_write:
                    conn.commit()
            try:
                meta = conn.cursor()
                exists = meta.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='base_labeled_npv'"
                ).fetchone()
                if exists:
                    info = meta.execute("PRAGMA table_info(base_labeled_npv)").fetchall()
                    for col in info:
                        name = str(col[1])
                        base = name.split("__", 1)[0]
                        if REPLICATE_WEIGHT_BASE_RE.match(base):
                            replicate_cols_detected += 1
            except Exception:
                pass
    except Exception as exc:
        print(f"ERROR: query failed: {exc}", file=sys.stderr)
        return 2
    finally:
        try:
            if conn is not None:
                conn.close()
        except Exception:
            pass

    elapsed_ms = round((time.perf_counter() - started) * 1000.0, 3)
    payload = {
        "db": str(db_path),
        "sql": sql.strip(),
        "columns": columns,
        "rows": rows,
        "row_count": len(rows),
        "truncated": truncated,
        "max_rows": int(args.max_rows),
        "elapsed_ms": elapsed_ms,
        "read_only": (not args.allow_write),
        "sampling": {
            "variance_method": "bootstrap_replicates_mse",
            "variance_formula": "var=(1/(R-1))*sum((theta_r-theta)^2)",
            "replicate_weight_base": "V1028",
            "replicate_weight_columns_detected": int(replicate_cols_detected),
            "note": (
                "brasil query does not infer CI automatically for arbitrary SQL. "
                "Use replicate estimates in SQL or dedicated commands (renda-por-faixa-sm/dashboard)."
            ),
        },
    }

    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    # Pretty table for humans in terminal.
    print(_colorize("BRASIL QUERY", "1;38;5;45", _supports_color(no_color=args.no_color)))
    print(f"DB: {db_path}")
    print(f"Rows: {payload['row_count']} | Cols: {len(columns)} | Elapsed: {elapsed_ms} ms")
    if columns:
        table = _format_table(rows, columns, max_col_width=int(args.max_col_width))
        print(table)
    else:
        print("(Query executada sem retorno tabular)")
    if truncated:
        print(f"[truncated] showing first {args.max_rows} rows")
    return 0


def _run_capture_stdout(cmd: Sequence[str], out_file: Path, quiet: bool = False) -> None:
    out_file.parent.mkdir(parents=True, exist_ok=True)
    _print("$ " + " ".join(cmd), quiet=quiet)
    with out_file.open("w", encoding="utf-8", newline="") as fh:
        subprocess.run(cmd, check=True, stdout=fh)


def _run_cmd(cmd: Sequence[str], quiet: bool = False) -> None:
    _print("$ " + " ".join(cmd), quiet=quiet)
    subprocess.run(cmd, check=True)


def _resolve_pipeline_raw_path(
    args: argparse.Namespace,
    out_dir: Path,
    *,
    latest_resolver=_latest_local_raw,
) -> Tuple[Optional[Path], Optional[int]]:
    if args.download_url:
        fallback_name = "PNADC_download.txt"
        if str(args.raw).strip().lower() != "latest":
            fallback_name = Path(args.raw).name
        filename = args.filename or Path(urlparse(args.download_url).path).name or fallback_name
        raw_path: Optional[Path] = out_dir / filename
    elif str(args.raw).strip().lower() == "latest":
        latest = latest_resolver(Path(args.raw_dir))
        if latest is None:
            print(
                f"ERROR: no local raw PNADC file found under {args.raw_dir}. "
                "Run `brasil ibge-sync` first (or `brasil ibge-sync --full`) or pass --raw PATH.",
                file=sys.stderr,
            )
            return None, 2
        raw_path = latest
    else:
        raw_path = Path(args.raw)

    if args.download_url:
        assert raw_path is not None
        try:
            _download(args.download_url, raw_path, force=args.force_download, quiet=args.quiet)
        except Exception as exc:
            print(f"ERROR: download failed: {exc}", file=sys.stderr)
            return None, 2

    if raw_path is None or not raw_path.exists():
        print(f"ERROR: raw file not found: {raw_path}", file=sys.stderr)
        return None, 2
    return raw_path, None


def _run_pipeline_core(
    args: argparse.Namespace,
    *,
    base_name: str,
    default_keep: Optional[str] = None,
    latest_resolver=_latest_local_raw,
) -> int:
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.sync_full:
        sync_cmd = [sys.executable, str(SCRIPT_DIR / "pnad.py"), "ibge-sync", "--full"]
        if args.quiet:
            sync_cmd.append("--quiet")
        _run_cmd(sync_cmd, quiet=args.quiet)

    raw_path, raw_error = _resolve_pipeline_raw_path(args, out_dir, latest_resolver=latest_resolver)
    if raw_error is not None:
        return raw_error

    try:
        rc = pnadc_cli.cmd_emit_codes(argparse.Namespace(out=out_dir))
        if rc != 0:
            return rc

        base_csv = out_dir / f"{base_name}.csv"
        labeled_csv = out_dir / f"{base_name}_labeled.csv"
        npv_csv = out_dir / f"{base_name}_labeled_npv.csv"
        ipca_csv = Path(args.ipca_csv)
        keep_value = args.keep if args.keep else default_keep

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
        if keep_value:
            fwf_cmd.extend(["--keep", keep_value])
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


def cmd_pipeline_run(args: argparse.Namespace) -> int:
    return _run_pipeline_core(args, base_name="base", latest_resolver=_latest_local_raw)


def cmd_pipeline_run_anual(args: argparse.Namespace) -> int:
    return _run_pipeline_core(
        args,
        base_name="base_anual",
        default_keep=pnadc_cli.DEFAULT_KEEP_ANUAL,
        latest_resolver=_latest_local_raw_anual,
    )


def cmd_help_legacy(args: argparse.Namespace) -> int:
    parser = pnadc_cli.build_parser()
    parser.print_help()
    return 0


def build_parser(prog_name: str = "brasil") -> argparse.ArgumentParser:
    description = (
        "Brasil data CLI. Download official datasets (PNADC/Censo/TSE), refresh IPCA, run pipelines, "
        "and query analytics outputs."
    )
    epilog = """Examples:
  brasil --help
  brasil help-legacy
  brasil ibge-sync
  brasil ibge-sync --full
  brasil ibge-sync --year 2025 --quarter 3
  brasil download-pnadc --url https://host/PNADC_022025.txt --dest-dir data/raw
  brasil download-news --query PNAD --out data/news_pnad.json
  brasil renda-por-faixa-sm --input data/outputs/base_labeled.csv --group-by uf --ranges "0-2;2-5;5-10;10+"
  brasil dashboard --input data/outputs/base_labeled.csv --sm-mode both
  brasil query --db data/outputs/brasil.sqlite --sql "SELECT UF__unidade_da_federacao, AVG(VD4020__rendim_efetivo_qq_trabalho) AS renda_media FROM base_labeled_npv GROUP BY 1 ORDER BY 2 DESC LIMIT 10"
  brasil pipeline-run --sync-full --raw latest --layout data/originals/input_PNADC_trimestral.sas --sqlite data/outputs/brasil.sqlite
  brasil pipeline-run-anual --raw data/raw/pnadc_anual_visita5/PNADC_2024_visita5.txt

Legacy commands still work directly:
  brasil inspect data/outputs/base_labeled.csv
  brasil fwf-extract data/originals/input_PNADC_trimestral.sas data/raw/PNADC_032025.txt --header > data/outputs/base.csv
"""

    p = argparse.ArgumentParser(
        prog=prog_name,
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
        help="Income column name. Default auto: VD5001, then VD4020, then VD4019",
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
    prf.add_argument(
        "--no-ci",
        action="store_true",
        help="Disable confidence intervals/margin of error from replicate weights",
    )
    prf.add_argument(
        "--ci-level",
        type=float,
        default=0.95,
        help="Confidence level for interval estimation (default: 0.95)",
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
        help="Income column name. Default auto: VD5001, then VD4020, then VD4019",
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
    pdash.add_argument(
        "--no-ci",
        action="store_true",
        help="Disable confidence intervals/margin of error from replicate weights",
    )
    pdash.add_argument(
        "--ci-level",
        type=float,
        default=0.95,
        help="Confidence level for interval estimation (default: 0.95)",
    )
    pdash.add_argument("--interactive", action="store_true", help="Interactive navigation in terminal")
    pdash.add_argument("--format", choices=["pretty", "json"], default="pretty", help="Output format")
    pdash.add_argument("--no-color", action="store_true", help="Disable ANSI colors in pretty output")
    # Dashboard v2.0: Annual income composition arguments
    pdash.add_argument(
        "--mode",
        choices=["trimestral", "anual", "comparativo", "auto"],
        default="auto",
        help="Analysis mode. 'auto' detects based on columns (VD5001=anual, VD4019/VD4020=trimestral)",
    )
    pdash.add_argument(
        "--breakdown",
        action="store_true",
        help="Show income composition by source (anual mode only)",
    )
    pdash.add_argument(
        "--source-detail",
        action="store_true",
        help="Show each income source V50xxA2 separately (not aggregated by category)",
    )
    pdash.add_argument(
        "--dependency-ranking",
        action="store_true",
        help="Rank UFs by %% of income from benefits vs work (shows dependency score)",
    )
    pdash.add_argument(
        "--composition-by-band",
        action="store_true",
        help="Show income composition within each salary band",
    )
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

    psync.add_argument("--full", action="store_true", help="Enable all election scopes (PNADC anual + Censo renda + TSE)")

    psync.add_argument("--with-anual", action="store_true", help="Sync PNADC Anual (Visita 5)")
    psync.add_argument("--anual-base-url", default=IBGE_ANUAL_VISITA5_BASE, help="PNADC Anual Visita 5 base URL")
    psync.add_argument("--anual-raw-dir", default="data/raw/pnadc_anual_visita5", help="Directory for PNADC anual zip/txt files")
    psync.add_argument("--anual-docs-dir", default="data/originals/pnadc_anual_visita5", help="Directory for PNADC anual docs")
    psync.add_argument("--anual-year", type=int, help="Specific year for PNADC anual")
    psync.add_argument("--anual-all-years", action="store_true", help="Download latest revision for all annual years")
    psync.add_argument("--no-anual-raw", action="store_true", help="Skip PNADC anual microdados sync")
    psync.add_argument("--no-anual-docs", action="store_true", help="Skip PNADC anual documentation sync")

    psync.add_argument("--with-censo", action="store_true", help="Sync Censo 2022 renda do responsavel aggregates")
    psync.add_argument("--censo-base-url", default=IBGE_CENSO_2022_BASE, help="Censo 2022 base URL")
    psync.add_argument("--censo-folder", default=IBGE_CENSO_RENDA_RESP_FOLDER, help="Folder under Censo base with files to sync")
    psync.add_argument("--censo-dir", default="data/originals/censo_2022_renda_responsavel", help="Directory for Censo aggregated files")

    psync.add_argument("--with-tse", action="store_true", help="Sync TSE eleitorado resources from dados abertos")
    psync.add_argument("--tse-api-base", default=TSE_CKAN_BASE, help="TSE CKAN API base URL")
    psync.add_argument("--tse-query", default=TSE_DEFAULT_QUERY, help="Search query for TSE datasets")
    psync.add_argument("--tse-rows", type=int, default=50, help="Max packages to scan in TSE CKAN search")
    psync.add_argument("--tse-year", type=int, help="Filter TSE resources by year")
    psync.add_argument("--tse-all-years", action="store_true", help="Keep one resource per year/kind instead of only latest")
    psync.add_argument("--tse-dir", default="data/raw/tse_eleitorado", help="Directory for TSE downloaded resources")
    psync.set_defaults(func=cmd_ibge_sync)

    psq = sub.add_parser("sqlite-build", help="Build or refresh a SQLite table from a CSV file")
    psq.add_argument("--input", required=True, help="Input CSV path")
    psq.add_argument("--db", required=True, help="SQLite DB path")
    psq.add_argument("--table", default="base_labeled_npv", help="Target table name")
    psq.add_argument("--if-exists", choices=["replace", "append", "fail"], default="replace")
    psq.add_argument("--chunk-size", type=int, default=5000, help="Insert batch size")
    psq.add_argument(
        "--indexes",
        default=(
            "dom_id,"
            "UF__unidade_da_federacao,UF__unidade_da_federao,"
            "Ano__ano_de_referencia,Ano__ano_de_referncia,"
            "Trimestre__trimestre_de_referencia,Trimestre__trimestre_de_referncia"
        ),
        help="Comma-separated columns to index when present",
    )
    psq.set_defaults(func=cmd_sqlite_build)

    pq = sub.add_parser(
        "query",
        help="Run SQL against Brasil SQLite (JSON default, table format optional)",
    )
    pq.add_argument("--db", default="data/outputs/brasil.sqlite", help="SQLite DB path")
    pq.add_argument("--sql", default="", help="SQL string (read-only by default)")
    pq.add_argument("--sql-file", default="", help="Path to a .sql file")
    pq.add_argument(
        "--format",
        choices=["json", "table"],
        default="json",
        help="Output format (default: json, ideal for LLMs)",
    )
    pq.add_argument("--max-rows", type=int, default=200, help="Maximum returned rows before truncation")
    pq.add_argument("--max-col-width", type=int, default=48, help="Max column width in table mode")
    pq.add_argument("--timeout", type=float, default=30.0, help="SQLite timeout in seconds")
    pq.add_argument(
        "--allow-write",
        action="store_true",
        help="Allow write statements (off by default for safe LLM workflows)",
    )
    pq.add_argument("--no-color", action="store_true", help="Disable ANSI colors in table mode")
    pq.set_defaults(func=cmd_query)

    def _add_pipeline_args(
        parser: argparse.ArgumentParser,
        *,
        default_raw_dir: str,
        default_layout: str,
        default_table: str,
    ) -> None:
        parser.add_argument("--raw", default="latest", help="Local raw PNADC file path or 'latest'")
        parser.add_argument(
            "--sync-full",
            action="store_true",
            help="Run `ibge-sync --full` before pipeline execution (PNADC trimestral/anual + Censo + TSE)",
        )
        parser.add_argument("--raw-dir", default=default_raw_dir, help="Directory used when --raw latest")
        parser.add_argument("--download-url", help="If set, download raw file before processing")
        parser.add_argument("--filename", help="Filename to use when --download-url is set")
        parser.add_argument("--force-download", action="store_true", help="Overwrite downloaded raw file")
        parser.add_argument("--layout", default=default_layout, help="SAS/TXT layout file")
        parser.add_argument("--out-dir", default="data/outputs", help="Output directory")
        parser.add_argument("--ipca-csv", default="data/outputs/ipca.csv", help="IPCA CSV file path")
        parser.add_argument(
            "--salario-minimo-csv",
            default="data/originals/salario_minimo.csv",
            help="Monthly nominal minimum wage CSV (date,value) for automatic --min-wage",
        )
        parser.add_argument("--skip-ipca-fetch", action="store_true", help="Reuse existing --ipca-csv if present")
        parser.add_argument("--target", default="", help="NPV target month YYYY-MM (default: latest in IPCA series)")
        parser.add_argument(
            "--min-wage",
            type=float,
            default=None,
            help="Minimum wage for *_mw columns (default: auto from --salario-minimo-csv at target month)",
        )
        parser.add_argument("--name-style", choices=["name", "label", "both"], default="both")
        parser.add_argument("--keep", help="Optional comma-separated keep list for fwf-extract")
        parser.add_argument("--sqlite", default="data/outputs/brasil.sqlite", help="SQLite output file (empty to disable)")
        parser.add_argument("--table", default=default_table, help="SQLite table name")
        parser.add_argument("--if-exists", choices=["replace", "append", "fail"], default="replace")
        parser.add_argument("--chunk-size", type=int, default=5000, help="SQLite insert batch size")
        parser.add_argument(
            "--indexes",
            default=(
                "dom_id,"
                "UF__unidade_da_federacao,UF__unidade_da_federao,"
                "Ano__ano_de_referencia,Ano__ano_de_referncia,"
                "Trimestre__trimestre_de_referencia,Trimestre__trimestre_de_referncia"
            ),
            help="Comma-separated columns to index when present",
        )
        parser.add_argument("--quiet", action="store_true", help="Reduce command output")

    pr = sub.add_parser("pipeline-run", help="Run the full PNADC trimestral refresh pipeline")
    _add_pipeline_args(
        pr,
        default_raw_dir="data/raw",
        default_layout="data/originals/input_PNADC_trimestral.sas",
        default_table="base_labeled_npv",
    )
    pr.set_defaults(func=cmd_pipeline_run)

    pra = sub.add_parser("pipeline-run-anual", help="Run the full PNADC anual visita 5 refresh pipeline")
    _add_pipeline_args(
        pra,
        default_raw_dir="data/raw/pnadc_anual_visita5",
        default_layout="data/originals/pnadc_anual_visita5/input_PNADC_2024_visita5.txt",
        default_table="base_anual_labeled_npv",
    )
    pra.set_defaults(func=cmd_pipeline_run_anual)

    return p


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(argv) if argv is not None else sys.argv[1:]

    invoked_name = Path(sys.argv[0]).stem.lower()
    prog_name = invoked_name if invoked_name in {"pnad", "brasil"} else "brasil"

    # Accept accidental explicit prefix: `python scripts/pnad.py brasil ...`
    if argv and argv[0] in {"pnad", "brasil"}:
        argv = argv[1:]

    # Keep existing workflow intact: legacy subcommands can be invoked directly.
    if argv and argv[0] in LEGACY_COMMANDS:
        return int(pnadc_cli.main(argv) or 0)

    parser = build_parser(prog_name=prog_name)
    args = parser.parse_args(argv)

    if not args.cmd:
        parser.print_help()
        return 0

    return int(args.func(args) or 0)


if __name__ == "__main__":
    raise SystemExit(main())
