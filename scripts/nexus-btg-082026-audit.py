#!/usr/bin/env python3
"""Rebuild the quantitative evidence for the BTG/Nexus 3 Aug. 2026 dossier."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from statistics import NormalDist

import numpy as np
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/pesquisas/nexus_btg"
OUTPUT = ROOT / "docs/assets/nexus_btg_082026_1_data.json"
PNAD_DB = ROOT / "data/outputs/brasil.sqlite"
TSE_DB = ROOT / "data/outputs/tse_eleitorado_perfil.sqlite"
EDUCATION_BENCHMARK = ROOT / "data/outputs/atlas_260626/pnad_education_benchmarks.json"
TABLE = "base_anual_visita1_labeled_npv"

UF_BY_PREFIX = {
    11: "RO",
    12: "AC",
    13: "AM",
    14: "RR",
    15: "PA",
    16: "AP",
    17: "TO",
    21: "MA",
    22: "PI",
    23: "CE",
    24: "RN",
    25: "PB",
    26: "PE",
    27: "AL",
    28: "SE",
    29: "BA",
    31: "MG",
    32: "ES",
    33: "RJ",
    35: "SP",
    41: "PR",
    42: "SC",
    43: "RS",
    50: "MS",
    51: "MT",
    52: "GO",
    53: "DF",
}
REGION_BY_UF = {
    **{uf: "Norte" for uf in "RO AC AM RR PA AP TO".split()},
    **{uf: "Nordeste" for uf in "MA PI CE RN PB PE AL SE BA".split()},
    **{uf: "Sudeste" for uf in "MG ES RJ SP".split()},
    **{uf: "Sul" for uf in "PR SC RS".split()},
    **{uf: "Centro-Oeste" for uf in "MS MT GO DF".split()},
}

DATES = [
    "30 mar.",
    "27 abr.",
    "25 mai.",
    "15 jun.",
    "29 jun.",
    "13 jul.",
    "27 jul.",
    "3 ago.",
]
SERIES = {
    "dates": DATES,
    "first": {
        "Lula": [41, 41, 40, 42, 42, 40, 42, 41],
        "Flávio": [38, 36, 35, 33, 34, 34, 33, 37],
    },
    "runoff": {
        "Lula": [46, 46, 47, 49, 47, 47, 47, 46],
        "Flávio": [46, 45, 43, 43, 44, 44, 43, 45],
    },
    "spontaneous": {
        "Lula": [32, 33, 36, 36, 38, 35, 36, 36],
        "Flávio": [26, 26, 26, 27, 27, 24, 27, 28],
    },
}

TOPLINES = {
    "july": {
        "first": [42, 33, 6, 5, 3, 2, 1, 0, 6, 2],
        "runoff": [47, 43, 9, 1],
        "labels": [
            "Lula",
            "Flávio",
            "Caiado",
            "Renan",
            "Zema",
            "Cury",
            "Daciolo",
            "Samara",
            "B/N",
            "NS",
        ],
    },
    "august": {
        "first": [41, 37, 5, 4, 3, 1, 1, 1, 4, 3],
        "runoff": [46, 45, 8, 2],
        "labels": [
            "Lula",
            "Flávio",
            "Caiado",
            "Renan",
            "Zema",
            "Cury",
            "Daciolo",
            "Samara",
            "B/N",
            "NS",
        ],
    },
}

PROFILES = {
    "july": {
        "sex": [53, 47],
        "age": [12, 30, 34, 24],
        "education": [36, 41, 23],
        "income": [23, 17, 40, 20],
        "region": [16, 28, 42, 14],
    },
    "august": {
        "sex": [53, 47],
        "age": [12, 30, 34, 24],
        "education": [36, 41, 23],
        "income": [22, 18, 40, 21],
        "region": [16, 28, 42, 14],
    },
}

# Cell order: candidates, then blank/null and undecided. Values are published rounded percentages.
# July first round has one column per candidate (Samara Martins padded with 0, she enters only
# in August); August first round aggregates the tail into "Outros". Transcribed from the
# published tables: July pp. 28-29 and 57-58, August pp. 28-29 and 52-53.
CROSSTABS = {
    "july": {
        "first": {
            "income": [
                [58, 24, 3, 2, 1, 0, 0, 0, 8, 3],
                [47, 30, 7, 3, 1, 1, 0, 0, 8, 2],
                [36, 38, 6, 6, 4, 2, 2, 0, 5, 2],
                [34, 37, 7, 8, 7, 3, 0, 0, 3, 0],
            ],
            "religion": [
                [49, 27, 7, 4, 3, 1, 1, 0, 6, 2],
                [28, 50, 4, 6, 3, 3, 0, 0, 4, 1],
                [35, 32, 6, 6, 5, 2, 3, 0, 8, 2],
                [50, 26, 3, 7, 3, 2, 0, 0, 8, 2],
            ],
            "labour": [
                [31, 39, 6, 7, 4, 3, 1, 0, 6, 2],
                [44, 32, 5, 5, 4, 2, 0, 0, 6, 1],
                [41, 30, 5, 4, 1, 1, 0, 0, 15, 2],
                [55, 27, 5, 2, 2, 1, 0, 0, 5, 2],
            ],
        },
        "runoff": {
            "income": [[62, 28, 8, 2], [53, 39, 8, 0], [42, 48, 9, 1], [39, 51, 10, 0]],
            "religion": [
                [55, 36, 8, 1],
                [30, 62, 8, 0],
                [40, 44, 14, 2],
                [57, 31, 10, 1],
            ],
            "labour": [
                [37, 52, 10, 1],
                [48, 41, 10, 0],
                [47, 34, 17, 2],
                [59, 34, 5, 2],
            ],
        },
    },
    "august": {
        "first": {
            "sex": [[48, 29, 4, 1, 2, 6, 6, 4], [34, 45, 5, 7, 4, 1, 2, 2]],
            "age": [
                [50, 21, 2, 15, 2, 4, 1, 5],
                [33, 43, 4, 4, 2, 6, 5, 2],
                [40, 41, 3, 1, 4, 3, 5, 2],
                [50, 31, 8, 1, 3, 1, 4, 3],
            ],
            "education": [
                [44, 39, 5, 1, 2, 3, 3, 4],
                [40, 37, 4, 5, 3, 4, 5, 2],
                [39, 34, 5, 6, 5, 5, 3, 2],
            ],
            "income": [
                [54, 26, 3, 1, 2, 6, 6, 3],
                [37, 44, 3, 1, 1, 3, 5, 5],
                [38, 39, 6, 5, 3, 3, 3, 2],
                [39, 38, 5, 7, 4, 3, 2, 2],
            ],
            "region": [
                [40, 34, 10, 3, 3, 5, 2, 3],
                [48, 34, 4, 5, 1, 3, 3, 2],
                [42, 35, 3, 3, 5, 4, 4, 4],
                [27, 51, 5, 4, 2, 3, 6, 1],
            ],
            "religion": [
                [46, 34, 5, 3, 3, 3, 4, 3],
                [28, 50, 5, 4, 3, 4, 3, 3],
                [46, 30, 3, 3, 5, 6, 4, 2],
                [52, 23, 3, 8, 1, 4, 5, 3],
            ],
            "labour": [
                [35, 42, 4, 5, 4, 4, 4, 2],
                [42, 37, 4, 4, 1, 4, 4, 3],
                [42, 30, 2, 3, 3, 10, 6, 4],
                [48, 31, 6, 2, 2, 2, 4, 4],
            ],
        },
        "runoff": {
            "sex": [[54, 37, 7, 3], [37, 53, 9, 1]],
            "age": [[56, 31, 10, 3], [39, 51, 9, 1], [43, 48, 7, 2], [53, 38, 6, 3]],
            "education": [[47, 43, 6, 3], [44, 45, 9, 2], [46, 45, 8, 1]],
            "income": [[58, 32, 6, 4], [43, 49, 7, 1], [42, 47, 10, 2], [43, 50, 7, 1]],
            "region": [[44, 48, 6, 2], [52, 39, 7, 1], [47, 42, 8, 3], [32, 57, 9, 1]],
            "religion": [
                [51, 41, 7, 1],
                [31, 59, 8, 2],
                [48, 40, 10, 1],
                [60, 29, 8, 3],
            ],
            "labour": [[39, 50, 9, 1], [47, 44, 8, 2], [51, 40, 5, 3], [52, 39, 6, 3]],
        },
    },
}

# Margins the institute does NOT declare as quota or weighting target, published on
# July p. 117 and August p. 113. Order: religion = católicos, evangélicos, outras, sem religião;
# labour = PEA formal, PEA informal, desocupados, fora da força de trabalho.
UNCONTROLLED_PROFILES = {
    "july": {"religion": [53, 25, 9, 12], "labour": [42, 17, 5, 35]},
    "august": {"religion": [48, 30, 9, 12], "labour": [43, 17, 5, 35]},
}
RELIGION_LABELS = ["Católicos", "Evangélicos", "Outras religiões", "Sem religião"]
LABOUR_LABELS = ["PEA formal", "PEA informal", "Desocupados", "Não PEA"]

# Realized interviews per wave, from the report cover pages (p. 4 in both waves).
INTERVIEWS = {"july": 2004, "august": 2002}

# Age bands used in the report profile (16-24, 25-40, 41-59, 60+) do not match the five bands
# filed in the TSE sample plan (16-24, 25-34, 35-44, 45-59, 60+). The TSE micro-bands are
# five-year groups, so 25-40 and 41-59 need one linear split inside "40 a 44 anos".
TSE_AGE_BANDS = {
    "16-24": ["16 anos", "17 anos", "18 anos", "19 anos", "20 anos", "21 a 24 anos"],
    "25-40": ["25 a 29 anos", "30 a 34 anos", "35 a 39 anos"],
    "41-59": ["45 a 49 anos", "50 a 54 anos", "55 a 59 anos"],
    "60+": [
        "60 a 64 anos",
        "65 a 69 anos",
        "70 a 74 anos",
        "75 a 79 anos",
        "80 a 84 anos",
        "85 a 89 anos",
        "90 a 94 anos",
        "95 a 99 anos",
        "100 anos ou mais",
    ],
}
TSE_AGE_SPLIT = (
    "40 a 44 anos",
    0.2,
)  # share of the 40-44 group that is exactly 40 years old

# Age quota filed in the TSE registration for the 8th wave (BR-02874/2026).
FILED_AGE_QUOTA = {"16-24": 12, "25-34": 19, "35-44": 20, "45-59": 26, "60+": 24}
FILED_TSE_MICRO = {
    "16-24": TSE_AGE_BANDS["16-24"],
    "25-34": ["25 a 29 anos", "30 a 34 anos"],
    "35-44": ["35 a 39 anos", "40 a 44 anos"],
    "45-59": TSE_AGE_BANDS["41-59"],
    "60+": TSE_AGE_BANDS["60+"],
}

# The 27 state capitals, to separate capital / interior inside the municipality filing.
CAPITALS = {
    "1100205",
    "1200401",
    "1302603",
    "1400100",
    "1501402",
    "1600303",
    "1721000",
    "2111300",
    "2211001",
    "2304400",
    "2408102",
    "2507507",
    "2611606",
    "2704302",
    "2800308",
    "2927408",
    "3106200",
    "3205309",
    "3304557",
    "3550308",
    "4106902",
    "4205407",
    "4314902",
    "5002704",
    "5103403",
    "5208707",
    "5300108",
}

# Published series, with the base each one is computed on. The cluster series are read on the
# share of the sample that the report itself assigns to the cluster in the last wave.
SERIES_DISPERSION = {
    "1º turno, Lula": (SERIES["first"]["Lula"], 1.0),
    "1º turno, Flávio": (SERIES["first"]["Flávio"], 1.0),
    "2º turno, Lula": (SERIES["runoff"]["Lula"], 1.0),
    "2º turno, Flávio": (SERIES["runoff"]["Flávio"], 1.0),
    "Aprovação do governo": ([45, 46, 47, 48, 48, 47, 47, 47], 1.0),
    "Comparecimento declarado": ([95, 93, 95, 94, 93, 96, 95, 96], 1.0),
    "Bolsonarista convicto vota Flávio": ([68, 70, 68, 71, 68, 68, 68, 69], 0.29),
    "Lulista convicto vota Lula": ([79, 81, 79, 84, 83, 86, 83, 79], 0.25),
    "Lula como alternativa vota Lula": ([54, 48, 49, 47, 61, 50, 43, 38], 0.05),
    "Bolsonaro como alternativa vota Flávio": ([50, 45, 35, 36, 42, 38, 40, 38], 0.06),
}

SECOND_CHOICE_JULY = {
    "Lula": [13, 7, 11, 5, 6, 3, 44, 11],
    "Flávio": [25, 28, 8, 0, 5, 6, 19, 7],
    "Renan": [21, 21, 0, 20, 7, 12, 16, 2],
    "Caiado": [0, 19, 6, 29, 8, 2, 11, 3],
    "Zema": [32, 0, 2, 33, 6, 5, 10, 5],
}

TRANSFER_SOURCES = [
    "Lula",
    "Flávio",
    "Caiado",
    "Renan",
    "Zema",
    "Cury",
    "Daciolo",
    "Samara",
    "B/N",
    "NS",
]
TRANSFER_ROWS = np.array([41, 37, 5, 4, 3, 1, 1, 1, 4, 3], dtype=float)
TRANSFER_COLS = np.array([46, 45, 8, 2], dtype=float)
TRANSFER_PRIOR = np.array(
    [
        [98, 0.4, 0.3, 0.3],
        [0.5, 98, 0.3, 0.2],
        [17, 52, 30, 0.5],
        [15, 40, 44, 1],
        [12, 57, 27, 4],
        [43, 40, 17, 0.5],
        [35, 31, 11, 22],
        [33, 25, 33, 8],
        [15, 15, 67, 3],
        [18, 18, 22, 42],
    ],
    dtype=float,
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def documents() -> list[dict]:
    result = []
    for wave in ("rodada7_2026-07-27", "rodada8_2026-08-03"):
        for path in sorted((SOURCE / wave).glob("*.pdf")):
            result.append(
                {
                    "wave": wave,
                    "file": path.name,
                    "bytes": path.stat().st_size,
                    "sha256": sha256(path),
                }
            )
    return result


def parse_cities(path: Path) -> dict[str, tuple[str, int]]:
    text = "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
    rows: dict[str, tuple[str, int]] = {}
    pattern = re.compile(r"(?m)^\s*(.+?)\s+(\d{7})\s+(\d+)\s*$")
    for match in pattern.finditer(text):
        name, code, interviews = match.groups()
        rows[code] = (re.sub(r"\s+", " ", name).strip(), int(interviews))
    return rows


def territory() -> dict:
    waves = {}
    city_sets = {}
    for key, folder in (
        ("july", "rodada7_2026-07-27"),
        ("august", "rodada8_2026-08-03"),
    ):
        cities = parse_cities(SOURCE / folder / "municipios.pdf")
        city_sets[key] = set(cities)
        regions, top = Counter(), []
        for code, (name, n) in cities.items():
            uf = UF_BY_PREFIX.get(int(code[:2]))
            regions[REGION_BY_UF.get(uf, "Indefinida")] += n
            top.append({"code": code, "city": name, "uf": uf, "n": n})
        total = sum(n for _, n in cities.values())
        singletons = sum(1 for _, n in cities.values() if n == 1)
        waves[key] = {
            "cities": len(cities),
            "interviews": total,
            "singletons": singletons,
            "singleton_city_pct": round(100 * singletons / len(cities), 2),
            "singleton_interview_pct": round(100 * singletons / total, 2),
            "raw_region_pct": {
                region: round(100 * n / total, 2) for region, n in regions.items()
            },
            "top": sorted(top, key=lambda item: item["n"], reverse=True)[:12],
        }
    intersection = city_sets["july"] & city_sets["august"]
    union = city_sets["july"] | city_sets["august"]
    return {
        **waves,
        "overlap": len(intersection),
        "entered": len(city_sets["august"] - city_sets["july"]),
        "left": len(city_sets["july"] - city_sets["august"]),
        "retention_pct": round(100 * len(intersection) / len(city_sets["august"]), 2),
        "jaccard_pct": round(100 * len(intersection) / len(union), 2),
    }


def replicate_ci(theta: float, values: list[float], level: float = 0.95) -> dict:
    variance = sum((value - theta) ** 2 for value in values) / (len(values) - 1)
    moe = NormalDist().inv_cdf(0.5 + level / 2) * math.sqrt(variance)
    return {
        "pct": round(theta, 4),
        "moe": round(moe, 4),
        "low": round(theta - moe, 4),
        "high": round(theta + moe, 4),
    }


def pnad_distribution(column: str, classifier) -> dict:
    base = "V1032__peso_com_calibracao"
    reps = [f"V1032{i:03d}__peso_replicado_{i}" for i in range(1, 201)]
    sums = defaultdict(float)
    rep_sums = {label: [0.0] * len(reps) for label in classifier(None, labels=True)}
    rep_totals = [0.0] * len(reps)
    total = 0.0
    columns = ",".join([column, base, *reps])
    query = f'SELECT {columns} FROM "{TABLE}" WHERE V2009__idade_na_data_de_referencia >= 16 AND {column} IS NOT NULL'
    with sqlite3.connect(PNAD_DB) as connection:
        for row in connection.execute(query):
            label = classifier(row[0])
            if label is None:
                continue
            weight = float(row[1] or 0)
            total += weight
            sums[label] += weight
            for i, value in enumerate(row[2:]):
                rep = float(value or 0)
                rep_totals[i] += rep
                rep_sums[label][i] += rep
    result = {}
    for label in classifier(None, labels=True):
        estimate = 100 * sums[label] / total
        values = [
            100 * value / denominator
            for value, denominator in zip(rep_sums[label], rep_totals)
            if denominator
        ]
        result[label] = replicate_ci(estimate, values)
    return {"distribution": result, "weighted_people": round(total), "replicates": 200}


def income_classifier(value=None, labels=False):
    names = ["Até 1 SM", "1-2 SM", "2-5 SM", "5+ SM"]
    if labels:
        return names
    if value in (None, ""):
        return None
    value = float(value)
    return (
        names[0]
        if value <= 1
        else names[1] if value <= 2 else names[2] if value <= 5 else names[3]
    )


def education_classifier(value=None, labels=False):
    names = ["Fundamental", "Médio", "Superior"]
    if labels:
        return names
    if value in (None, ""):
        return None
    value = int(value)
    return names[0] if value <= 3 else names[1] if value <= 5 else names[2]


def education_benchmark() -> dict:
    payload = json.loads(EDUCATION_BENCHMARK.read_text(encoding="utf-8"))
    values = payload["atlas_3way_comparable"]
    return {
        "distribution": {
            "Fundamental": {"pct": values["Fundamental"]},
            "Médio": {"pct": values["Medio"]},
            "Superior": {"pct": values["Superior"]},
        },
        "source": payload["source"],
        "universe": payload["universe"],
    }


def tse_age_bands() -> dict:
    """Electorate by age on the report's own bands and on the bands filed at the TSE.

    The report profiles ages as 16-24 / 25-40 / 41-59 / 60+, while the registered sample plan
    uses 16-24 / 25-34 / 35-44 / 45-59 / 60+. Comparing one against the other is a category
    error, so both are rebuilt here from the same TSE micro-bands.
    """
    query = (
        "SELECT category, qt_eleitores FROM summary "
        "WHERE dimension='idade_raw' AND universe='Brasil sem exterior'"
    )
    with sqlite3.connect(TSE_DB) as connection:
        micro = dict(connection.execute(query))
    split_band, split_share = TSE_AGE_SPLIT
    report = {
        name: sum(micro[key] for key in keys) for name, keys in TSE_AGE_BANDS.items()
    }
    report["25-40"] += micro[split_band] * split_share
    report["41-59"] += micro[split_band] * (1 - split_share)
    filed = {
        name: sum(micro[key] for key in keys) for name, keys in FILED_TSE_MICRO.items()
    }
    total = sum(report.values())
    return {
        "report_bands": {
            name: round(100 * value / total, 3) for name, value in report.items()
        },
        "filed_bands": {
            name: round(100 * value / total, 3) for name, value in filed.items()
        },
        "filed_quota": FILED_AGE_QUOTA,
        "filed_quota_sum": sum(FILED_AGE_QUOTA.values()),
        "electors_16_plus": round(total),
        "split_note": (
            f"'{split_band}' foi repartida linearmente: {split_share:.0%} em 25-40 e o "
            "restante em 41-59, porque o TSE só publica faixas quinquenais."
        ),
    }


def official_targets(pnad_income: dict, pnad_education: dict, ages: dict) -> dict:
    with sqlite3.connect(TSE_DB) as connection:
        rows = connection.execute(
            "SELECT dimension, category, tse_pct FROM atlas_comparison"
        ).fetchall()
        metadata = dict(connection.execute("SELECT key, value FROM metadata"))
    by_dim = defaultdict(dict)
    for dimension, category, value in rows:
        by_dim[dimension][category] = value
    regions = by_dim["regiao"]
    report_ages = ages["report_bands"]
    return {
        "sex": [
            by_dim["genero_atlas_binario"]["Mulher"],
            by_dim["genero_atlas_binario"]["Homem"],
        ],
        "age": [
            report_ages["16-24"],
            report_ages["25-40"],
            report_ages["41-59"],
            report_ages["60+"],
        ],
        "education": [item["pct"] for item in pnad_education["distribution"].values()],
        "income": [item["pct"] for item in pnad_income["distribution"].values()],
        "region": [
            regions["Norte"] + regions["Centro-Oeste"],
            regions["Nordeste"],
            regions["Sudeste"],
            regions["Sul"],
        ],
        "tse_metadata": metadata,
    }


def normalize_rows(cells) -> np.ndarray:
    matrix = np.asarray(cells, dtype=float)
    return matrix / matrix.sum(axis=1, keepdims=True) * 100


def reweight(cells, profile, target, published) -> dict:
    matrix = normalize_rows(cells)
    profile = np.asarray(profile, dtype=float)
    profile = profile / profile.sum()
    target = np.asarray(target, dtype=float)
    target = target / target.sum()
    reproduced = profile @ matrix
    direct = target @ matrix
    anchored = np.asarray(published, dtype=float) + direct - reproduced
    return {
        "reproduced": [round(x, 3) for x in reproduced],
        "direct": [round(x, 3) for x in direct],
        "anchored": [round(x, 3) for x in anchored],
        "gap": round(float(anchored[0] - anchored[1]), 3),
    }


def rounding_sensitivity(
    cells, profile, target, published, seed=826, draws=10000
) -> dict:
    rng = np.random.default_rng(seed)
    gaps = []
    matrix = np.asarray(cells, dtype=float)
    for _ in range(draws):
        jittered = np.clip(matrix + rng.uniform(-0.5, 0.5, matrix.shape), 0, None)
        gaps.append(reweight(jittered, profile, target, published)["gap"])
    low, high = np.quantile(gaps, [0.025, 0.975])
    return {
        "draws": draws,
        "p2_5": round(float(low), 3),
        "p97_5": round(float(high), 3),
        "median": round(float(np.median(gaps)), 3),
    }


def all_reweighting(targets: dict) -> dict:
    output = {}
    for wave in ("july", "august"):
        output[wave] = {}
        for ballot in ("first", "runoff"):
            output[wave][ballot] = {}
            for dimension, cells in CROSSTABS[wave][ballot].items():
                if dimension not in targets:
                    continue
                published = TOPLINES[wave][ballot]
                if ballot == "first" and len(cells[0]) == 8:
                    published = [*published[:5], sum(published[5:8]), *published[8:]]
                output[wave][ballot][dimension] = reweight(
                    cells, PROFILES[wave][dimension], targets[dimension], published
                )
        income = output[wave]["runoff"]["income"]
        income["rounding"] = rounding_sensitivity(
            CROSSTABS[wave]["runoff"]["income"],
            PROFILES[wave]["income"],
            targets["income"],
            TOPLINES[wave]["runoff"],
        )
    return output


def ipf_transfer() -> dict:
    matrix = TRANSFER_PRIOR / TRANSFER_PRIOR.sum(axis=1, keepdims=True)
    rows = TRANSFER_ROWS * TRANSFER_COLS.sum() / TRANSFER_ROWS.sum()
    matrix *= rows[:, None]
    for _ in range(10000):
        matrix *= (TRANSFER_COLS / matrix.sum(axis=0))[None, :]
        matrix *= (rows / matrix.sum(axis=1))[:, None]
        if max(abs(matrix.sum(axis=0) - TRANSFER_COLS)) < 1e-10:
            break
    lula_gain = TRANSFER_COLS[0] - rows[0]
    flavio_gain = TRANSFER_COLS[1] - rows[1]
    return {
        "sources": TRANSFER_SOURCES,
        "destinations": ["Lula", "Flávio", "B/N", "NS"],
        "matrix": [[round(float(x), 3) for x in row] for row in matrix],
        "row_targets_scaled": [round(float(x), 3) for x in rows],
        "column_targets": TRANSFER_COLS.tolist(),
        "consolidation": {
            "Lula": round(float(lula_gain), 3),
            "Flávio": round(float(flavio_gain), 3),
            "ratio_flavio_lula": round(float(flavio_gain / lula_gain), 3),
        },
        "prior_note": "Prior ideológica explícita; as margens publicadas fecham por IPF. Os elos não foram medidos.",
    }


def duel(cells, profile) -> tuple[float, float]:
    """Lula and Flávio shares implied by a category profile over a published crosstab."""
    matrix = normalize_rows(cells)
    weights = np.asarray(profile, dtype=float)
    weights = weights / weights.sum()
    estimate = weights @ matrix
    return float(estimate[0]), float(estimate[1])


def decompose_shift(dimension: str, labels: list[str]) -> dict:
    """Split the July to August move into composition and behaviour, on one uncontrolled margin.

    Composition = July response rates read on August's profile. Behaviour = August response
    rates read on July's profile. Both are descriptive: nothing here identifies individual
    voters, and the institute's own weighting is joint and unpublished.
    """
    output = {"labels": labels}
    for ballot in ("first", "runoff"):
        july_cells = CROSSTABS["july"][ballot][dimension]
        august_cells = CROSSTABS["august"][ballot][dimension]
        july_profile = (
            UNCONTROLLED_PROFILES["july"].get(dimension) or PROFILES["july"][dimension]
        )
        august_profile = (
            UNCONTROLLED_PROFILES["august"].get(dimension)
            or PROFILES["august"][dimension]
        )
        base = duel(july_cells, july_profile)
        final = duel(august_cells, august_profile)
        composition = duel(july_cells, august_profile)
        behaviour = duel(august_cells, july_profile)
        entry = {
            "july_profile": july_profile,
            "august_profile": august_profile,
            "july_published": TOPLINES["july"][ballot][:2],
            "august_published": TOPLINES["august"][ballot][:2],
            "july_reproduced": [round(x, 2) for x in base],
            "august_reproduced": [round(x, 2) for x in final],
            "counterfactual_august_on_july_profile": [round(x, 2) for x in behaviour],
        }
        for index, who in enumerate(("Lula", "Flávio")):
            entry[who] = {
                "total": round(final[index] - base[index], 2),
                "composition": round(composition[index] - base[index], 2),
                "behaviour": round(behaviour[index] - base[index], 2),
            }
        entry["gap_published_july"] = (
            TOPLINES["july"][ballot][0] - TOPLINES["july"][ballot][1]
        )
        entry["gap_published_august"] = (
            TOPLINES["august"][ballot][0] - TOPLINES["august"][ballot][1]
        )
        entry["gap_august_on_july_profile"] = round(behaviour[0] - behaviour[1], 2)
        output[ballot] = entry
    return output


def profile_shift_test(dimension: str, labels: list[str]) -> list[dict]:
    """How far each uncontrolled margin moved between the waves, in sampling units.

    The z score assumes simple random sampling, which understates variance, so it is the most
    favourable assumption for the institute: `deff_to_erase` is the design effect that would be
    needed to turn each move into noise at 95%.
    """
    july = UNCONTROLLED_PROFILES["july"][dimension]
    august = UNCONTROLLED_PROFILES["august"][dimension]
    n_july, n_august = INTERVIEWS["july"], INTERVIEWS["august"]
    critical = NormalDist().inv_cdf(0.975)
    rows = []
    for label, before, after in zip(labels, july, august):
        p1, p2 = before / 100, after / 100
        error = math.sqrt(p1 * (1 - p1) / n_july + p2 * (1 - p2) / n_august)
        z = (p2 - p1) / error if error else 0.0
        rows.append(
            {
                "category": label,
                "july_pct": before,
                "august_pct": after,
                "change_pp": after - before,
                "se_srs_pp": round(100 * error, 3),
                "z_srs": round(z, 3),
                "p_two_sided": round(2 * (1 - NormalDist().cdf(abs(z))), 5),
                "deff_to_erase": round((abs(z) / critical) ** 2, 2) if z else 0.0,
            }
        )
    return rows


def uncontrolled_margins() -> dict:
    """Every margin the institute controls is frozen between the waves; these are the ones free."""
    controlled = {
        key: [PROFILES["july"][key], PROFILES["august"][key]]
        for key in ("sex", "age", "education", "region")
    }
    return {
        "controlled_frozen": {
            key: value[0] == value[1] for key, value in controlled.items()
        },
        "controlled_values": controlled,
        "declared_quota_report": [
            "sexo",
            "idade",
            "escolaridade",
            "tipo de telefonia",
            "DDD",
        ],
        "declared_quota_tse": [
            "região",
            "tipo de telefonia",
            "sexo",
            "idade",
            "escolaridade",
        ],
        "declared_weighting_extra_tse": ["dentro e fora da força de trabalho", "renda"],
        "religion": decompose_shift("religion", RELIGION_LABELS),
        "religion_shift_test": profile_shift_test("religion", RELIGION_LABELS),
        "labour_shift_test": profile_shift_test("labour", LABOUR_LABELS),
        "labour": decompose_shift("labour", LABOUR_LABELS),
        "income": decompose_shift("income", ["Até 1 SM", "1-2 SM", "2-5 SM", "5+ SM"]),
        "warning": (
            "Decomposição descritiva sobre percentuais publicados. A ponderação do "
            "instituto é conjunta e não publicada; nada aqui mede voto individual."
        ),
    }


def labour_benchmark() -> dict:
    """PNAD labour-force composition of the 16+ population, against the published sample profile."""
    query = f"""
        SELECT VD4001__condicao_em_relacao_forca_d_trab, VD4002__condicao_de_ocupacao,
               VD4009__posicao_na_ocupacao_trab_princ, V4032__contribuinte_de_instit_d_previd,
               V1032__peso_com_calibracao
        FROM "{TABLE}" WHERE V2009__idade_na_data_de_referencia >= 16
    """
    formal_positions = {1, 3, 5, 7}
    own_account = {8, 9}
    totals = defaultdict(float)
    grand = 0.0
    with sqlite3.connect(PNAD_DB) as connection:
        for in_force, occupied, position, social_security, weight in connection.execute(
            query
        ):
            weight = float(weight or 0)
            grand += weight
            if in_force != 1:
                group = LABOUR_LABELS[3]
            elif occupied == 2:
                group = LABOUR_LABELS[2]
            elif position in formal_positions or (
                position in own_account and social_security == 1
            ):
                group = LABOUR_LABELS[0]
            else:
                group = LABOUR_LABELS[1]
            totals[group] += weight
    distribution = {
        label: round(100 * totals[label] / grand, 2) for label in LABOUR_LABELS
    }
    published = dict(zip(LABOUR_LABELS, UNCONTROLLED_PROFILES["august"]["labour"]))
    return {
        "labels": LABOUR_LABELS,
        "pnad_distribution": distribution,
        "published_profile_august": published,
        "published_profile_july": dict(
            zip(LABOUR_LABELS, UNCONTROLLED_PROFILES["july"]["labour"])
        ),
        "gap_pp": {
            label: round(published[label] - distribution[label], 2)
            for label in LABOUR_LABELS
        },
        "ratio": {
            label: round(published[label] / distribution[label], 3)
            for label in LABOUR_LABELS
        },
        "weighted_people": round(grand),
        "universe": "Pessoas de 16 anos ou mais, PNAD Contínua anual 2025, 1ª visita",
        "formality_rule": (
            "Formal = carteira assinada, estatutário ou militar; conta própria e "
            "empregador contam como formais quando contribuem para a previdência."
        ),
    }


def field_geography() -> dict:
    """Realized field geography from the municipality filing, against the TSE electorate."""
    with sqlite3.connect(TSE_DB) as connection:
        query = (
            "SELECT category, pct_total FROM summary "
            "WHERE dimension='uf' AND universe='Brasil sem exterior'"
        )
        tse_uf = dict(connection.execute(query))
    tse_region = defaultdict(float)
    for uf, share in tse_uf.items():
        tse_region[REGION_BY_UF[uf]] += share
    waves = {}
    for key, folder in (
        ("july", "rodada7_2026-07-27"),
        ("august", "rodada8_2026-08-03"),
    ):
        cities = parse_cities(SOURCE / folder / "municipios.pdf")
        counts, region_counts = Counter(), Counter()
        capital = 0
        for code, (_, interviews) in cities.items():
            uf = UF_BY_PREFIX[int(code[:2])]
            counts[uf] += interviews
            region_counts[REGION_BY_UF[uf]] += interviews
            if code in CAPITALS:
                capital += interviews
        total = sum(counts.values())
        chi2 = sum(
            (counts[uf] - tse_uf[uf] * total / 100) ** 2 / (tse_uf[uf] * total / 100)
            for uf in tse_uf
        )
        deff = (
            sum(
                (tse_uf[uf] * total / 100) ** 2 / counts[uf]
                for uf in tse_uf
                if counts[uf]
            )
            / total
        )
        srs = 100 * NormalDist().inv_cdf(0.975) * math.sqrt(0.25 / total)
        waves[key] = {
            "interviews": total,
            "matches_report_n": total == INTERVIEWS[key],
            "uf_ratio_to_tse": {
                uf: round((100 * counts[uf] / total) / tse_uf[uf], 3) for uf in tse_uf
            },
            "uf_interviews": dict(counts),
            "region_field_pct": {
                name: round(100 * value / total, 2)
                for name, value in region_counts.items()
            },
            "region_field_pct_report_bands": {
                "Norte/Centro-Oeste": round(
                    100
                    * (region_counts["Norte"] + region_counts["Centro-Oeste"])
                    / total,
                    2,
                ),
                "Nordeste": round(100 * region_counts["Nordeste"] / total, 2),
                "Sudeste": round(100 * region_counts["Sudeste"] / total, 2),
                "Sul": round(100 * region_counts["Sul"] / total, 2),
            },
            "region_published_pct": dict(
                zip(
                    ["Norte/Centro-Oeste", "Nordeste", "Sudeste", "Sul"],
                    PROFILES[key]["region"],
                )
            ),
            "northeast_field_pct": round(100 * region_counts["Nordeste"] / total, 2),
            "capital_field_pct": round(100 * capital / total, 2),
            "chi2_vs_tse": round(chi2, 1),
            "chi2_df": len(tse_uf) - 1,
            "p_vs_tse": round(1 - chi2_cdf(chi2, len(tse_uf) - 1), 6),
            "deff_uf_calibration": round(deff, 3),
            "effective_n": round(total / deff),
            "moe_srs_pp": round(srs, 2),
            "moe_with_uf_calibration_pp": round(srs * math.sqrt(deff), 2),
            "moe_published_pp": 2,
        }
    july, august = waves["july"], waves["august"]
    expected = {
        uf: july["uf_interviews"][uf] * august["interviews"] / july["interviews"]
        for uf in july["uf_interviews"]
    }
    allocation_chi2 = sum(
        (august["uf_interviews"].get(uf, 0) - value) ** 2 / value
        for uf, value in expected.items()
        if value
    )
    waves["p_august_vs_july_allocation"] = round(
        1 - chi2_cdf(allocation_chi2, len(expected) - 1), 6
    )
    waves["chi2_august_vs_july_allocation"] = round(
        sum(
            (august["uf_interviews"].get(uf, 0) - value) ** 2 / value
            for uf, value in expected.items()
            if value
        ),
        1,
    )
    waves["capital_published_pct"] = {"july": 25, "august": 27}
    waves["note"] = (
        "A distribuição por município é a contagem bruta de entrevistas filhada ao "
        "TSE; o perfil publicado no relatório já é ponderado. A diferença entre as "
        "duas é o efeito da ponderação geográfica."
    )
    return waves


def chi2_cdf(value: float, degrees: int) -> float:
    """Chi-square CDF for even/odd small degrees of freedom, via the regularised gamma series."""
    shape, argument = degrees / 2, value / 2
    if argument <= 0:
        return 0.0
    term = 1.0 / shape
    total = term
    for step in range(1, 400):
        term *= argument / (shape + step)
        total += term
        if term < total * 1e-14:
            break
    return min(
        1.0,
        total * math.exp(-argument + shape * math.log(argument) - math.lgamma(shape)),
    )


def series_dispersion(n: int = 2002) -> dict:
    """Compare the wave-to-wave swing of each published series with pure sampling noise."""
    rows = []
    for name, (values, base) in SERIES_DISPERSION.items():
        size = n * base
        mean = sum(values) / len(values)
        observed = math.sqrt(
            sum((value - mean) ** 2 for value in values) / (len(values) - 1)
        )
        expected = 100 * math.sqrt((mean / 100) * (1 - mean / 100) / size)
        degrees = len(values) - 1
        chi2 = degrees * (observed / expected) ** 2
        rows.append(
            {
                "series": name,
                "base_share": base,
                "implied_n": round(size),
                "mean": round(mean, 2),
                "sd_observed": round(observed, 2),
                "sd_srs_expected": round(expected, 2),
                "ratio": round(observed / expected, 2),
                "implied_deff": round((observed / expected) ** 2, 2),
                "chi2": round(chi2, 2),
                "chi2_df": degrees,
                "p_smoother_than_srs": round(chi2_cdf(chi2, degrees), 4),
                "p_noisier_than_srs": round(1 - chi2_cdf(chi2, degrees), 4),
                "moe_srs_pp": round(
                    100
                    * NormalDist().inv_cdf(0.975)
                    * math.sqrt((mean / 100) * (1 - mean / 100) / size),
                    2,
                ),
            }
        )
    return {
        "waves": len(DATES),
        "rows": sorted(rows, key=lambda item: item["ratio"]),
        "published_moe_pp": 2,
        "note": (
            "Razão acima de 1 indica série que oscila mais do que a amostragem explicaria; "
            "abaixo de 1, série mais lisa do que o acaso. O relatório publica margem de erro "
            "por perfil (p. 114), mas nenhuma para os clusters de polarização."
        ),
    }


def document_trail() -> dict:
    """Dates on the face of the filed documents, and what they precede."""
    try:
        import fitz
    except ImportError:  # pragma: no cover - optional dependency
        return {"available": False}
    trail = []
    for wave, folder in (
        ("july", "rodada7_2026-07-27"),
        ("august", "rodada8_2026-08-03"),
    ):
        for path in sorted((SOURCE / folder).glob("*.pdf")):
            with fitz.open(path) as document:
                meta = document.metadata or {}
                pages = document.page_count
            trail.append(
                {
                    "wave": wave,
                    "file": path.name,
                    "pages": pages,
                    "creator": meta.get("creator", ""),
                    "producer": meta.get("producer", ""),
                    "author": meta.get("author", ""),
                    "created": meta.get("creationDate", ""),
                    "modified": meta.get("modDate", ""),
                }
            )
    return {
        "available": True,
        "files": trail,
        "field": {
            "july": ["24/07/2026", "26/07/2026"],
            "august": ["31/07/2026", "02/08/2026"],
        },
        "release": {"july": "27/07/2026", "august": "03/08/2026"},
        "registration_august": {"id": "BR-02874/2026", "registered": "28/07/2026"},
        "registration_july": {"id": "BR-01489/2026"},
        "statistician_signature": {
            "july": "2026-07-21T18:18:52-03:00",
            "august": "2026-07-28T15:30:18-03:00",
        },
        "invoice_august": {
            "number": 310,
            "issued": "2026-05-05",
            "due": "2026-06-05",
            "value_brl": 164888.89,
            "net_brl": 154748.22,
            "buyer": "BANCO BTG PACTUAL S.A.",
            "description_date": "1 de agosto de 2026",
            "provider_contact_domain": "fsb.com.br",
        },
        "declared_value_brl": {"july": 164888.89, "august": 164888.89},
        "declared_interviews": {"july": 2000, "august": 2000},
        "realized_interviews": INTERVIEWS,
    }


def questionnaire_shift() -> dict:
    """What the instrument gained and lost between the two waves."""
    return {
        "stimulated_ballot_names": {"july": 7, "august": 12},
        "stimulated_added": [
            "Samara Martins",
            "Rui Costa Pimenta",
            "Hertz Dias",
            "Heró Bezerra",
            "Edmilson Costa",
        ],
        "rejection_battery_names": {"july": 7, "august": 5},
        "rejection_removed": ["Augusto Cury", "Cabo Daciolo"],
        "removed_questions": [
            "P5, segunda opção de voto no 1º turno",
            "P9A/P9B, motivação do voto no 2º turno (melhor candidato ou derrotar o adversário)",
            "P16, voto ideal, voto disponível ou voto útil",
            "P17, contra quem o eleitor está votando",
            "P18 a P20, bloco do tarifaço (conhecimento, natureza da decisão e quem está certo)",
        ],
        "added_questions": [
            "P10 e P11, área de maior destaque positivo e negativo do governo",
            "P13, sete itens de vida comparando 2026 com 2022",
            "P14 e P15, responsabilidade do governo Lula pela melhora e pela piora de cada item",
            "P16, prioridade esperada do candidato de 2º turno",
        ],
        "questions_before_polarisation_scale": {"july": 24, "august": 23},
        "polarisation_scale_position": {"july": "P25 de 25", "august": "P24 de 24"},
        "report_disclaimer_added_in_august": (
            "A sequência de perguntas apresentadas neste relatório difere da ordem original das "
            "perguntas no instrumento de coleta registrado no TSE."
        ),
        "note": (
            "A mesma onda que ampliou a lista de voto de 7 para 12 nomes reduziu a bateria de "
            "rejeição de 7 para 5: Cury e Daciolo passaram a poder receber voto sem poder "
            "receber rejeição."
        ),
    }


def difference_moe(p1: float, p2: float, n: int, level=0.95) -> float:
    z = NormalDist().inv_cdf(0.5 + level / 2)
    variance = (p1 + p2 - (p1 - p2) ** 2) / n
    return round(100 * z * math.sqrt(variance), 3)


def women_profiles() -> dict:
    """Descriptive PNAD household archetypes, never political targeting segments."""
    query = f"""
        WITH hh AS (
          SELECT dom_id,
                 MAX(CASE WHEN V2009__idade_na_data_de_referencia < 18 THEN 1 ELSE 0 END) AS minor,
                 MAX(CASE WHEN V2005__condicao_no_domicilio IN (2,3) THEN 1 ELSE 0 END) AS spouse
          FROM "{TABLE}" GROUP BY dom_id
        )
        SELECT p.V1032__peso_com_calibracao, p.V2009__idade_na_data_de_referencia,
               p.V2005__condicao_no_domicilio, p.VD5001__rend_efetivo_domiciliar_mw,
               p.UF__unidade_da_federacao, p.Capital__municipio_da_capital,
               p.VD4002__condicao_de_ocupacao, p.V5002A__recebeu_bolsa_familia,
               hh.minor, hh.spouse
        FROM "{TABLE}" p JOIN hh USING (dom_id)
        WHERE p.V2007__sexo = 2 AND p.V2009__idade_na_data_de_referencia >= 16
    """
    archetypes = defaultdict(lambda: defaultdict(float))
    totals = defaultdict(float)
    with sqlite3.connect(PNAD_DB) as connection:
        for (
            weight,
            age,
            position,
            income,
            uf_code,
            capital,
            occupied,
            bolsa,
            minor,
            spouse,
        ) in connection.execute(query):
            weight = float(weight or 0)
            position = int(position or 0)
            if position == 1 and minor and not spouse:
                group = "Responsável sem cônjuge, com menor"
            elif position in (1, 2, 3) and minor and spouse:
                group = "Casal com menor"
            elif position in (1, 2, 3) and spouse:
                group = "Casal sem menor"
            elif position == 1:
                group = "Responsável sem cônjuge, sem menor"
            else:
                group = "Filha ou outra posição"
            totals[group] += weight
            values = {
                "age_mean": float(age) * weight,
                "occupied": (occupied == 1) * weight,
                "bolsa_familia": (bolsa == 1) * weight,
                "capital": (capital not in (None, 0, "")) * weight,
                "northeast": (int(uf_code or 0) in range(21, 30)) * weight,
            }
            if income not in (None, ""):
                values["income_mean_sm"] = float(income) * weight
                values["income_weight"] = weight
            for key, value in values.items():
                archetypes[group][key] += value
    grand = sum(totals.values())
    result = []
    for group, total in sorted(totals.items(), key=lambda item: item[1], reverse=True):
        row = {"group": group, "population_pct": round(100 * total / grand, 2)}
        for key, value in archetypes[group].items():
            if key == "income_weight":
                continue
            if key == "income_mean_sm":
                row[key] = round(value / archetypes[group]["income_weight"], 2)
            else:
                row[key] = round(
                    value / total if key.endswith("_mean") else 100 * value / total, 2
                )
        result.append(row)
    return {
        "universe": "Mulheres de 16 anos ou mais, PNAD Contínua anual 2025, 1ª visita",
        "warning": "Arquétipos domiciliares descritivos. PNAD não mede voto, religião, persuasibilidade ou intenção eleitoral.",
        "groups": result,
    }


def build() -> dict:
    income = pnad_distribution("VD5001__rend_efetivo_domiciliar_mw", income_classifier)
    education = education_benchmark()
    ages = tse_age_bands()
    targets = official_targets(income, education, ages)
    reweighted = all_reweighting(targets)
    geography = field_geography()
    deff = geography["august"]["deff_uf_calibration"]
    return {
        "generated_at": "2026-08-03",
        "documents": documents(),
        "series": SERIES,
        "toplines": TOPLINES,
        "profiles": PROFILES,
        "territory": territory(),
        "benchmarks": {
            "pnad_income_2025": income,
            "pnad_education_2025": education,
            "pnad_labour_2025": labour_benchmark(),
            "tse_age_bands": ages,
            "targets": targets,
        },
        "reweighting": reweighted,
        "transfer": ipf_transfer(),
        "second_choice_july": SECOND_CHOICE_JULY,
        "uncontrolled": uncontrolled_margins(),
        "field_geography": geography,
        "series_dispersion": series_dispersion(),
        "documents_trail": document_trail(),
        "questionnaire": questionnaire_shift(),
        "uncertainty": {
            "first_gap": 4,
            "first_gap_moe_srs": difference_moe(0.41, 0.37, 2002),
            "runoff_gap": 1,
            "runoff_gap_moe_srs": difference_moe(0.46, 0.45, 2002),
            "first_gap_moe_deff": round(
                difference_moe(0.41, 0.37, 2002) * math.sqrt(deff), 3
            ),
            "runoff_gap_moe_deff": round(
                difference_moe(0.46, 0.45, 2002) * math.sqrt(deff), 3
            ),
            "deff_uf_calibration": deff,
            "warning": "Aproximação sob amostra aleatória simples. O desenho CATI, ponderação e efeito de desenho não publicados podem ampliar a incerteza.",
        },
        "women_pnad": women_profiles(),
        "sources": {
            "august": "https://www.nexus.fsb.com.br/estudos-divulgados/pesquisa-btg-nexus-de-intencao-de-votos-para-presidente-do-brasil-3-de-agosto-de-2026/",
            "july": "https://www.nexus.fsb.com.br/estudos-divulgados/pesquisa-btg-nexus-de-intencao-de-votos-para-presidente-do-brasil-27-de-julho-de-2026/",
            "ibge_pnad": "https://www.ibge.gov.br/estatisticas/sociais/trabalho/17270-pnad-continua.html",
            "tse_open": "https://dadosabertos.tse.jus.br/dataset/eleitorado-atual",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    payload = build()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {"output": str(args.output), "bytes": args.output.stat().st_size},
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
