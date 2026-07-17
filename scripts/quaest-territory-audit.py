#!/usr/bin/env python3
"""Audit Quaest census-sector annexes and compare June with July 2026.

The PDF is the evidence source. The IBGE API used by Panorama supplies a
current population lookup for each selected 2022 census sector. No vote is
imputed from neighborhood demographics: the annex contains locations, not
respondent-level answers or weights.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import re
import time
import unicodedata
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

try:
    from pypdf import PdfReader
except ModuleNotFoundError:  # pragma: no cover - parser unit tests need no PDF stack
    PdfReader = None


ROOT = Path(__file__).resolve().parents[1]
JUNE_PDF = ROOT / "data/pesquisas/quaest/2026-06/Quaest_Bairros_062026.pdf"
JULY_PDF = ROOT / "data/pesquisas/quaest/2026-07/Quaest_Bairros_072026.pdf"
JUNE_CSV = ROOT / "data/pesquisas/quaest/2026-06/quaest_bairros_0626.csv"
JULY_CSV = ROOT / "data/pesquisas/quaest/2026-07/quaest_bairros_0726.csv"
OUTPUT = ROOT / "docs/assets/quaest_0726_territory.json"
IBGE_REFERENCE = (
    ROOT
    / "data/originals/censo_2022_setores_censitarios"
    / "quaest_sector_reference_2026-07-16.json"
)

POPULATION_API = (
    "https://servicodados.ibge.gov.br/api/v2/censos/demografico/2022/"
    "agregados/setores-censitarios/?l={municipality}&n=setor&v=pop"
)
MESH_API = (
    "https://servicodados.ibge.gov.br/api/v2/censos/demografico/2022/"
    "malhas/setores-censitarios/municipios/{municipality}"
    "?intrarregiao=setor&formato=application/json"
)

ROW_RE = re.compile(
    r"^(?P<municipality>.+?) \((?P<uf>[A-Z]{2})\) "
    r"(?P<neighborhood>.+?) (?P<sector_code>\d{15}) "
    r"(?P<interviews>\d+)$"
)

UF_CODES = {
    "RO": "11",
    "AC": "12",
    "AM": "13",
    "RR": "14",
    "PA": "15",
    "AP": "16",
    "TO": "17",
    "MA": "21",
    "PI": "22",
    "CE": "23",
    "RN": "24",
    "PB": "25",
    "PE": "26",
    "AL": "27",
    "SE": "28",
    "BA": "29",
    "MG": "31",
    "ES": "32",
    "RJ": "33",
    "SP": "35",
    "PR": "41",
    "SC": "42",
    "RS": "43",
    "MS": "50",
    "MT": "51",
    "GO": "52",
    "DF": "53",
}

REGIONS = {
    "Norte": {"RO", "AC", "AM", "RR", "PA", "AP", "TO"},
    "Nordeste": {"MA", "PI", "CE", "RN", "PB", "PE", "AL", "SE", "BA"},
    "Sudeste": {"MG", "ES", "RJ", "SP"},
    "Sul": {"PR", "SC", "RS"},
    "Centro-Oeste": {"MS", "MT", "GO", "DF"},
}

CAPITAL_CODES = {
    "1200401",
    "2704302",
    "1600303",
    "1302603",
    "2927408",
    "2304400",
    "5300108",
    "3205309",
    "5208707",
    "2111300",
    "5103403",
    "5002704",
    "3106200",
    "1501402",
    "2507507",
    "4106902",
    "2611606",
    "2211001",
    "3304557",
    "2408102",
    "4314902",
    "1100205",
    "1400100",
    "4205407",
    "3550308",
    "2800308",
    "1721000",
}


@dataclass(frozen=True)
class Location:
    round: str
    registry: str
    municipality: str
    uf: str
    municipality_code: str
    neighborhood: str
    sector_code: str
    interviews: int
    region: str


def normalize(value: str) -> str:
    value = "".join(
        char
        for char in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(char)
    )
    return " ".join(value.casefold().split())


def region_for(uf: str) -> str:
    return next(name for name, states in REGIONS.items() if uf in states)


def parse_rows(text: str, round_name: str, registry: str) -> list[Location]:
    rows = []
    for line in text.splitlines():
        match = ROW_RE.match(line.strip())
        if not match:
            continue
        item = match.groupdict()
        sector = item["sector_code"]
        uf = item["uf"]
        if sector[:2] != UF_CODES[uf]:
            raise ValueError(f"UF incompatible with sector code: {line}")
        rows.append(
            Location(
                round=round_name,
                registry=registry,
                municipality=item["municipality"],
                uf=uf,
                municipality_code=sector[:7],
                neighborhood=item["neighborhood"],
                sector_code=sector,
                interviews=int(item["interviews"]),
                region=region_for(uf),
            )
        )
    return rows


def parse_pdf(path: Path, round_name: str, registry: str) -> list[Location]:
    if PdfReader is None:  # pragma: no cover - environment guidance
        raise SystemExit(
            "Dependência ausente: instale o extra de auditoria com "
            "`python3 -m pip install -e '.[audit]'`."
        )
    reader = PdfReader(path)
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    rows = parse_rows(text, round_name, registry)
    if len(rows) != 334 or sum(row.interviews for row in rows) != 2004:
        raise ValueError(
            f"Unexpected annex totals for {path}: "
            f"{len(rows)} sectors, {sum(row.interviews for row in rows)} interviews"
        )
    if len({row.sector_code for row in rows}) != len(rows):
        raise ValueError(f"Duplicate sector in {path}")
    names_by_code: dict[str, set[tuple[str, str]]] = defaultdict(set)
    for row in rows:
        names_by_code[row.municipality_code].add((row.municipality, row.uf))
    conflicts = {code: names for code, names in names_by_code.items() if len(names) > 1}
    if conflicts:
        raise ValueError(f"Municipality code/name conflicts: {conflicts}")
    return rows


def http_json(url: str, attempts: int = 3) -> dict:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Arvor-PNAD/0.4 census-sector audit"},
    )
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                payload = response.read()
                if (
                    response.headers.get("Content-Encoding") == "gzip"
                    or payload[:2] == b"\x1f\x8b"
                ):
                    payload = gzip.decompress(payload)
                return json.loads(payload)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            if attempt + 1 == attempts:
                raise
            time.sleep(0.5 * (2**attempt))
    raise AssertionError("unreachable")


def mesh_codes(payload: dict) -> set[str]:
    codes = set()
    for object_value in payload.get("objects", {}).values():
        for geometry in object_value.get("geometries", []):
            code = geometry.get("properties", {}).get("codarea")
            if code:
                codes.add(str(code))
    return codes


def fetch_ibge_reference(rows: list[Location]) -> dict:
    selected: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        selected[row.municipality_code].add(row.sector_code)

    populations: dict[str, dict] = {}
    errors: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=12) as executor:
        jobs = {
            executor.submit(
                http_json, POPULATION_API.format(municipality=municipality)
            ): municipality
            for municipality in selected
        }
        for job in as_completed(jobs):
            municipality = jobs[job]
            try:
                populations[municipality] = job.result()
            except Exception as error:  # pragma: no cover - network failure
                errors[municipality] = f"{type(error).__name__}: {error}"

    missing_by_municipality = {
        municipality: codes - set(map(str, populations.get(municipality, {})))
        for municipality, codes in selected.items()
    }
    missing_by_municipality = {
        municipality: codes
        for municipality, codes in missing_by_municipality.items()
        if codes and municipality in populations
    }
    resolved_mesh: dict[str, set[str]] = {}
    with ThreadPoolExecutor(max_workers=6) as executor:
        jobs = {
            executor.submit(
                http_json, MESH_API.format(municipality=municipality)
            ): municipality
            for municipality in missing_by_municipality
        }
        for job in as_completed(jobs):
            municipality = jobs[job]
            try:
                resolved_mesh[municipality] = mesh_codes(job.result())
            except Exception as error:  # pragma: no cover - network failure
                errors[municipality] = f"{type(error).__name__}: {error}"

    sectors = {}
    for row in rows:
        code = row.sector_code
        if code in sectors:
            continue
        population_map = populations.get(row.municipality_code)
        population = population_map.get(code) if population_map else None
        exists = population is not None
        validation = "population_api"
        if population_map is None:
            validation = "api_error"
        elif population is None:
            mesh = resolved_mesh.get(row.municipality_code)
            if mesh is None:
                validation = "mesh_unavailable"
            elif code in mesh:
                exists = True
                validation = "mesh_only_no_resident_aggregate"
            else:
                validation = "absent_from_current_mesh"
        sectors[code] = {
            "municipality_code": row.municipality_code,
            "exists": exists,
            "population_2022": population,
            "validation": validation,
        }
    return {
        "retrieved": date.today().isoformat(),
        "population_api": POPULATION_API,
        "mesh_api": MESH_API,
        "source_context": (
            "IBGE Panorama Censo 2022 service; population aggregate may omit "
            "sectors without residents, resolved against the current mesh endpoint"
        ),
        "municipalities_requested": len(selected),
        "errors": errors,
        "sectors": sectors,
    }


def load_or_refresh_reference(rows: list[Location], path: Path, refresh: bool) -> dict:
    if path.exists() and not refresh:
        return json.loads(path.read_text(encoding="utf-8"))
    reference = fetch_ibge_reference(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(reference, ensure_ascii=False, indent=2) + "\n")
    return reference


def round_summary(rows: list[Location], reference: dict) -> dict:
    by_municipality: dict[str, list[Location]] = defaultdict(list)
    for row in rows:
        by_municipality[row.municipality_code].append(row)
    populations = [
        reference["sectors"].get(row.sector_code, {}).get("population_2022")
        for row in rows
    ]
    populations = sorted(value for value in populations if isinstance(value, int))
    top_municipalities = []
    for code, items in sorted(
        by_municipality.items(),
        key=lambda pair: (-len(pair[1]), pair[1][0].municipality),
    )[:15]:
        top_municipalities.append(
            {
                "municipality_code": code,
                "municipality": items[0].municipality,
                "uf": items[0].uf,
                "sectors": len(items),
                "interviews": sum(item.interviews for item in items),
            }
        )
    return {
        "sectors": len(rows),
        "interviews": sum(row.interviews for row in rows),
        "municipalities": len(by_municipality),
        "municipality_neighborhood_pairs": len(
            {(row.municipality_code, normalize(row.neighborhood)) for row in rows}
        ),
        "interviews_per_sector": dict(Counter(row.interviews for row in rows)),
        "regions": dict(Counter(row.region for row in rows)),
        "states": dict(Counter(row.uf for row in rows)),
        "capitals": sum(code in CAPITAL_CODES for code in by_municipality),
        "top_municipalities": top_municipalities,
        "selected_sector_population": {
            "available": len(populations),
            "minimum": min(populations) if populations else None,
            "median": populations[len(populations) // 2] if populations else None,
            "maximum": max(populations) if populations else None,
            "below_50": sum(value < 50 for value in populations),
            "below_100": sum(value < 100 for value in populations),
        },
    }


def capital_rows(rows: list[Location]) -> list[dict]:
    grouped: dict[str, list[Location]] = defaultdict(list)
    for row in rows:
        if row.municipality_code in CAPITAL_CODES:
            grouped[row.municipality_code].append(row)
    result = []
    for code, items in grouped.items():
        result.append(
            {
                "municipality_code": code,
                "municipality": items[0].municipality,
                "uf": items[0].uf,
                "sectors": len(items),
                "interviews": sum(item.interviews for item in items),
                "neighborhoods": [item.neighborhood for item in items],
            }
        )
    return sorted(result, key=lambda item: (-item["sectors"], item["municipality"]))


def compare_rounds(june: list[Location], july: list[Location]) -> dict:
    june_by_sector = {row.sector_code: row for row in june}
    july_by_sector = {row.sector_code: row for row in july}
    june_municipalities = {row.municipality_code for row in june}
    july_municipalities = {row.municipality_code for row in july}

    def neighborhood_key(row: Location) -> tuple[str, str]:
        return row.municipality_code, normalize(row.neighborhood)

    june_neighborhoods: dict[tuple[str, str], list[Location]] = defaultdict(list)
    july_neighborhoods: dict[tuple[str, str], list[Location]] = defaultdict(list)
    for row in june:
        june_neighborhoods[neighborhood_key(row)].append(row)
    for row in july:
        july_neighborhoods[neighborhood_key(row)].append(row)

    common_sectors = sorted(set(june_by_sector) & set(july_by_sector))
    common_neighborhoods = sorted(set(june_neighborhoods) & set(july_neighborhoods))
    neighborhood_details = []
    for key in common_neighborhoods:
        old = june_neighborhoods[key]
        new = july_neighborhoods[key]
        neighborhood_details.append(
            {
                "municipality": new[0].municipality,
                "uf": new[0].uf,
                "neighborhood_june": old[0].neighborhood,
                "neighborhood_july": new[0].neighborhood,
                "june_sectors": [row.sector_code for row in old],
                "july_sectors": [row.sector_code for row in new],
                "same_exact_sector": bool(
                    {row.sector_code for row in old} & {row.sector_code for row in new}
                ),
            }
        )

    union_municipalities = june_municipalities | july_municipalities
    union_sectors = set(june_by_sector) | set(july_by_sector)
    return {
        "common_municipalities": len(june_municipalities & july_municipalities),
        "municipality_jaccard_pct": round(
            100
            * len(june_municipalities & july_municipalities)
            / len(union_municipalities),
            2,
        ),
        "common_municipality_codes": sorted(june_municipalities & july_municipalities),
        "common_exact_sectors": len(common_sectors),
        "sector_jaccard_pct": round(100 * len(common_sectors) / len(union_sectors), 3),
        "common_sector_details": [
            asdict(july_by_sector[code]) for code in common_sectors
        ],
        "common_municipality_neighborhoods": len(common_neighborhoods),
        "common_neighborhood_details": neighborhood_details,
        "same_neighborhood_but_different_sector": sum(
            not item["same_exact_sector"] for item in neighborhood_details
        ),
    }


def write_csv(path: Path, rows: list[Location], reference: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [*asdict(rows[0]).keys(), "ibge_population_2022", "validation"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            values = asdict(row)
            official = reference["sectors"].get(row.sector_code, {})
            values.update(
                {
                    "ibge_population_2022": official.get("population_2022"),
                    "validation": official.get("validation", "not_in_reference"),
                }
            )
            writer.writerow(values)


def build_payload(june: list[Location], july: list[Location], reference: dict) -> dict:
    statuses = Counter(
        item.get("validation", "unknown") for item in reference["sectors"].values()
    )
    july_population = []
    for row in july:
        population = (
            reference["sectors"].get(row.sector_code, {}).get("population_2022")
        )
        if isinstance(population, int):
            july_population.append((population, row))
    smallest = [
        {
            **asdict(row),
            "population_2022": population,
            "interviews_as_pct_of_population": (
                round(100 * row.interviews / population, 2) if population else None
            ),
        }
        for population, row in sorted(july_population, key=lambda item: item[0])[:12]
    ]
    return {
        "metadata": {
            "june_registry": "BR-07661/2026",
            "july_registry": "BR-07181/2026",
            "sampling_unit": "IBGE 2022 census sector",
            "comparison_key": "15-digit sector geocode",
            "warning": (
                "The annex has no vote by sector or respondent weights; locations alone "
                "cannot explain candidate shares or support ecological inference."
            ),
        },
        "rounds": {
            "june": round_summary(june, reference),
            "july": round_summary(july, reference),
        },
        "comparison": compare_rounds(june, july),
        "capitals": {"june": capital_rows(june), "july": capital_rows(july)},
        "ibge_validation": {
            "retrieved": reference["retrieved"],
            "statuses": dict(statuses),
            "errors": reference.get("errors", {}),
            "smallest_july_sectors": smallest,
            "reference_file": str(IBGE_REFERENCE.relative_to(ROOT)),
        },
        "design": {
            "clusters": 334,
            "interviews_per_cluster": 6,
            "intraclass_correlation_scenarios": [
                {"rho": rho, "cluster_deff": round(1 + 5 * rho, 2)}
                for rho in (0.05, 0.10, 0.20)
            ],
            "interpretation": (
                "Every listed sector contributes exactly six interviews. The uniform "
                "take makes the cluster component of design effect material; the actual "
                "survey deff still requires microdata, PSU identifiers and final weights."
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--june", type=Path, default=JUNE_PDF)
    parser.add_argument("--july", type=Path, default=JULY_PDF)
    parser.add_argument("--june-csv", type=Path, default=JUNE_CSV)
    parser.add_argument("--july-csv", type=Path, default=JULY_CSV)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--ibge-reference", type=Path, default=IBGE_REFERENCE)
    parser.add_argument("--refresh-ibge", action="store_true")
    args = parser.parse_args()

    june = parse_pdf(args.june, "junho/2026", "BR-07661/2026")
    july = parse_pdf(args.july, "julho/2026", "BR-07181/2026")
    reference = load_or_refresh_reference(
        [*june, *july], args.ibge_reference, args.refresh_ibge
    )
    payload = build_payload(june, july, reference)
    write_csv(args.june_csv, june, reference)
    write_csv(args.july_csv, july, reference)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(
        json.dumps(
            {
                "output": str(args.output),
                "common_municipalities": payload["comparison"]["common_municipalities"],
                "common_exact_sectors": payload["comparison"]["common_exact_sectors"],
                "common_neighborhoods": payload["comparison"][
                    "common_municipality_neighborhoods"
                ],
                "ibge_statuses": payload["ibge_validation"]["statuses"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
