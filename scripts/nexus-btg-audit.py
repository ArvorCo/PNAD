#!/usr/bin/env python3
"""Rebuild the quantitative evidence used by the BTG/Nexus July 2026 audit.

The script intentionally separates measured facts (PDFs, TSE and PNAD) from the
editorial interpretation in the HTML report. Run it with the bundled workspace
Python because PDF extraction requires ``pypdf``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sqlite3
from pathlib import Path
from statistics import NormalDist

import numpy as np
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "data/pesquisas/nexus_btg/rodada6"
DEFAULT_OUTPUT = ROOT / "docs/assets/nexus_btg_0726_data.json"
PNAD_DB = ROOT / "data/outputs/brasil.sqlite"
TSE_DB = ROOT / "data/outputs/tse_eleitorado_perfil.sqlite"

CITY_PDFS = [
    ("27 abr.", "NexusBTG_Bairros_042026.pdf", "BR-01075/2026"),
    ("25 mai.", "NexusBTG_Bairros_052026.pdf", "BR-04193/2026"),
    ("15 jun.", "NexusBTG_Bairros_062026_2.pdf", "BR-06645/2026"),
    ("29 jun.", "NexusBTG_Bairros_062026.pdf", "BR-08521/2026"),
    ("13 jul.", "NexusBTG_Bairros_072026.pdf", "BR-07981/2026"),
]

# IBGE 2-digit UF prefix (first two digits of the 7-digit municipality code).
UF_BY_CODE_PREFIX = {
    11: "RO", 12: "AC", 13: "AM", 14: "RR", 15: "PA", 16: "AP", 17: "TO",
    21: "MA", 22: "PI", 23: "CE", 24: "RN", 25: "PB", 26: "PE", 27: "AL", 28: "SE", 29: "BA",
    31: "MG", 32: "ES", 33: "RJ", 35: "SP",
    41: "PR", 42: "SC", 43: "RS",
    50: "MS", 51: "MT", 52: "GO", 53: "DF",
}
REGION_BY_UF = {
    "RO": "Norte", "AC": "Norte", "AM": "Norte", "RR": "Norte", "PA": "Norte", "AP": "Norte", "TO": "Norte",
    "MA": "Nordeste", "PI": "Nordeste", "CE": "Nordeste", "RN": "Nordeste", "PB": "Nordeste",
    "PE": "Nordeste", "AL": "Nordeste", "SE": "Nordeste", "BA": "Nordeste",
    "MG": "Sudeste", "ES": "Sudeste", "RJ": "Sudeste", "SP": "Sudeste",
    "PR": "Sul", "SC": "Sul", "RS": "Sul",
    "MS": "Centro-Oeste", "MT": "Centro-Oeste", "GO": "Centro-Oeste", "DF": "Centro-Oeste",
}
# Regional macro-strata declared as the project weighting target (relatório p.4/p.109).
REGION_DESIGN_TARGET = {"Norte": 8, "Centro-Oeste": 8, "Nordeste": 27, "Sudeste": 43, "Sul": 15}
REGION_ORDER = ["Norte", "Centro-Oeste", "Nordeste", "Sudeste", "Sul"]

SERIES = {
    "dates": ["30 mar.", "27 abr.", "25 mai.", "15 jun.", "29 jun.", "13 jul."],
    "first_round": {
        "Lula": [41, 41, 40, 42, 42, 40],
        "Flávio Bolsonaro": [38, 36, 35, 33, 34, 34],
        "gap": [3, 5, 5, 9, 8, 6],
    },
    "runoff": {
        "Lula": [46, 46, 47, 49, 47, 47],
        "Flávio Bolsonaro": [46, 45, 43, 43, 44, 44],
        "gap": [0, 1, 4, 6, 3, 3],
    },
    "spontaneous": {
        "Lula": [32, 33, 36, 36, 38, 35],
        "Flávio Bolsonaro": [26, 26, 26, 27, 27, 24],
        "Ninguém/branco/nulo": [10, 10, 9, 9, 9, 11],
        "NS/NR": [30, 29, 26, 24, 20, 22],
    },
}

NEXUS_TARGETS = {
    "sex": {"Mulher": 52.0, "Homem": 48.0},
    "age": {"16-24": 17.0, "25-34": 20.0, "35-44": 20.0, "45-59": 24.0, "60+": 20.0},
    "region": {"Norte": 8.0, "Centro-Oeste": 8.0, "Nordeste": 27.0, "Sudeste": 43.0, "Sul": 15.0},
    "education": {"Fundamental": 36.0, "Médio": 41.0, "Superior": 23.0},
    "income_july": {"Até 1 SM": 20.0, "1-2 SM": 20.0, "2-5 SM": 40.0, "5+ SM": 20.0},
}

INCOME_SERIES = {
    "27 abr.": [24, 17, 40, 20],
    "25 mai.": [25, 15, 40, 20],
    "15 jun.": [22, 18, 40, 20],
    "29 jun.": [22, 18, 40, 21],
    "13 jul.": [20, 20, 40, 20],
}

# ---------------------------------------------------------------------------
# Runoff reweighting ("a mesma pesquisa com a régua oficial")
# ---------------------------------------------------------------------------
# Published Lula x Flávio runoff crosstabs (relatório p.49–50). Every cell is
# ordered as VOTE_LABELS. ``profile`` is the published sample profile (p.109),
# i.e. the Nexus weighting embedded in the cells. We reweight these estimates
# to the official universe rulers (TSE electorate, PNAD income/schooling).
VOTE_LABELS = ["Lula", "Flávio", "Nenhum/Branco/Nulo", "NS/NR"]
RUNOFF_TOPLINE = {"Lula": 47.0, "Flávio": 44.0, "Nenhum/Branco/Nulo": 8.0, "NS/NR": 1.0}
RUNOFF_QUESTION = (
    "Pensando em um possível segundo turno... em quem você votaria para "
    "Presidente da República se tivesse que escolher entre Lula e Flávio "
    "Bolsonaro? (ESTIMULADA E ÚNICA) — relatório p.49–50"
)
# region uses the 4-way grouping printed in the runoff crosstab (Norte+CO juntos)
REGION_RUNOFF_GROUP = {
    "Norte/Centro-Oeste": ("Norte", "Centro-Oeste"),
    "Nordeste": ("Nordeste",),
    "Sudeste": ("Sudeste",),
    "Sul": ("Sul",),
}
RUNOFF_CROSSTABS = {
    "sexo": {
        "page": 49,
        "profile": {"Feminino": 52.0, "Masculino": 48.0},
        "cells": {"Feminino": [53, 37, 8, 1], "Masculino": [40, 51, 8, 1]},
    },
    "idade": {
        "page": 49,
        "profile": {"16-24": 17.0, "25-40": 32.0, "41-59": 31.0, "60+": 20.0},
        "cells": {
            "16-24": [43, 46, 11, 0],
            "25-40": [42, 48, 9, 2],
            "41-59": [49, 43, 7, 1],
            "60+": [55, 37, 8, 0],
        },
    },
    "escolaridade": {
        "page": 49,
        "profile": {"Fundamental": 36.0, "Médio": 41.0, "Superior": 23.0},
        "cells": {
            "Fundamental": [55, 38, 6, 2],
            "Médio": [41, 51, 8, 1],
            "Superior": [46, 41, 12, 1],
        },
    },
    "renda": {
        "page": 50,
        "profile": {"Até 1 SM": 20.0, "1-2 SM": 20.0, "2-5 SM": 40.0, "5+ SM": 20.0},
        "cells": {
            "Até 1 SM": [60, 33, 5, 2],
            "1-2 SM": [49, 42, 8, 1],
            "2-5 SM": [41, 49, 9, 1],
            "5+ SM": [44, 45, 11, 0],
        },
    },
    "regiao": {
        "page": 50,
        "profile": {
            "Norte/Centro-Oeste": 16.0,
            "Nordeste": 26.0,
            "Sudeste": 43.0,
            "Sul": 15.0,
        },
        "cells": {
            "Norte/Centro-Oeste": [42, 50, 5, 4],
            "Nordeste": [59, 35, 5, 1],
            "Sudeste": [46, 42, 12, 1],
            "Sul": [34, 58, 8, 0],
        },
    },
}
REWEIGHT_DIMS = ["sexo", "idade", "escolaridade", "renda", "regiao"]
# Extra published crosstab kept for the coherence check only: there is no
# official universe ruler for religion (Census religion is stale/out of scope),
# so it is not reweighted — only validated against the 47×44 topline.
RUNOFF_EXTRA_CROSSTABS = {
    "religiao": {
        "page": 49,
        "profile": {
            "Católicos": 50.0,
            "Evangélicos": 27.0,
            "Outras religiões": 10.0,
            "Sem religião": 13.0,
        },
        "cells": {
            "Católicos": [51, 42, 7, 1],
            "Evangélicos": [36, 55, 8, 1],
            "Outras religiões": [48, 41, 10, 1],
            "Sem religião": [55, 32, 13, 0],
        },
    },
}
REWEIGHT_SCENARIOS = [
    ("b", "sexo", "reponderado por sexo (TSE)"),
    ("c", "idade", "reponderado por idade (TSE)"),
    ("d", "renda", "reponderado por renda familiar (PNAD)"),
    ("e", "escolaridade", "reponderado por escolaridade (PNAD)"),
    ("f", "regiao", "reponderado por região (TSE)"),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def pdf_text(path: Path) -> str:
    return "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)


def parse_cities(path: Path) -> dict[str, tuple[str, int]]:
    """Return municipality code -> (label as printed, interview count)."""
    rows: dict[str, tuple[str, int]] = {}
    pattern = re.compile(r"^(.+?)\s+(\d{7})\s+(\d+)\s*$")
    for raw_line in pdf_text(path).splitlines():
        match = pattern.match(raw_line.strip())
        if match:
            label, code, count = match.groups()
            rows[code] = (label.strip(), int(count))
    return rows


def city_audit(source: Path) -> tuple[list[dict], list[dict]]:
    waves = []
    sets: list[set[str]] = []
    for date, filename, registration in CITY_PDFS:
        cities = parse_cities(source / filename)
        counts = [count for _, count in cities.values()]
        sample = sum(counts)
        top = sorted(cities.items(), key=lambda item: item[1][1], reverse=True)[:10]
        sets.append(set(cities))
        waves.append(
            {
                "date": date,
                "registration": registration,
                "municipalities": len(cities),
                "interviews": sample,
                "singleton_municipalities": sum(count == 1 for count in counts),
                "singleton_city_pct": round(100 * sum(count == 1 for count in counts) / len(cities), 1),
                "singleton_interview_pct": round(100 * sum(count == 1 for count in counts) / sample, 1),
                "top10_interviews": sum(item[1][1] for item in top),
                "top10_pct": round(100 * sum(item[1][1] for item in top) / sample, 1),
                "largest_city_count": top[0][1][1],
            }
        )

    overlaps = []
    for index in range(1, len(sets)):
        previous, current = sets[index - 1], sets[index]
        intersection = previous & current
        union = previous | current
        overlaps.append(
            {
                "from": waves[index - 1]["date"],
                "to": waves[index]["date"],
                "intersection": len(intersection),
                "jaccard": round(len(intersection) / len(union), 3),
                "current_retained_pct": round(100 * len(intersection) / len(current), 1),
                "entered": len(current - previous),
                "left": len(previous - current),
            }
        )
    return waves, overlaps


def uf_distribution(source: Path, filename: str = "NexusBTG_Bairros_072026.pdf", wave: str = "13 jul.") -> dict:
    """Aggregate the current wave's municipality file by UF and compare it with the
    TSE electorate share per UF, exposing the intra-region distortion that regional
    weighting (5 macro-strata) cannot correct."""
    cities = parse_cities(source / filename)
    by_uf: dict[str, int] = {}
    total = 0
    for code, (_, count) in cities.items():
        uf = UF_BY_CODE_PREFIX.get(int(code) // 100000)
        if uf is None:
            continue
        by_uf[uf] = by_uf.get(uf, 0) + count
        total += count

    with sqlite3.connect(TSE_DB) as connection:
        tse_uf = summary_pct(connection, "uf")
        tse_region = summary_pct(connection, "regiao")

    chi_square = 0.0
    uf_rows: list[dict] = []
    for uf, observed in by_uf.items():
        electorate_pct = tse_uf.get(uf, 0.0)
        expected_n = electorate_pct / 100 * total
        sample_pct = 100 * observed / total
        if expected_n > 0:
            chi_square += (observed - expected_n) ** 2 / expected_n
        uf_rows.append(
            {
                "uf": uf,
                "region": REGION_BY_UF[uf],
                "interviews": observed,
                "sample_pct": round(sample_pct, 2),
                "electorate_pct": round(electorate_pct, 2),
                "delta": round(sample_pct - electorate_pct, 2),
                "expected_pps": round(expected_n, 1),
            }
        )
    uf_rows.sort(key=lambda row: row["interviews"], reverse=True)

    by_region: dict[str, int] = {}
    for uf, observed in by_uf.items():
        by_region[REGION_BY_UF[uf]] = by_region.get(REGION_BY_UF[uf], 0) + observed
    region_rows = [
        {
            "region": region,
            "interviews": by_region.get(region, 0),
            "sample_pct": round(100 * by_region.get(region, 0) / total, 2),
            "electorate_pct": round(tse_region.get(region, 0.0), 2),
            "design_pct": REGION_DESIGN_TARGET[region],
            "delta": round(100 * by_region.get(region, 0) / total - tse_region.get(region, 0.0), 2),
        }
        for region in REGION_ORDER
    ]

    return {
        "wave": wave,
        "source_file": filename,
        "interviews": total,
        "uf_count": len(by_uf),
        "chi_square": round(chi_square, 1),
        "df": len(by_uf) - 1,
        "critical_alpha_001": 54,
        "weighting_strata": "região (5 macrorregiões), sexo, idade, escolaridade, telefonia",
        "note": "A ponderação declarada corrige 5 macrorregiões, nunca as 27 UFs; distorções intra-região não são corrigidas.",
        "uf": uf_rows,
        "region": region_rows,
    }


def summary_pct(connection: sqlite3.Connection, dimension: str) -> dict[str, float]:
    query = "SELECT category, pct_total FROM summary WHERE dimension = ?"
    return {row[0]: float(row[1]) for row in connection.execute(query, (dimension,))}


def tse_benchmarks() -> dict:
    with sqlite3.connect(TSE_DB) as connection:
        metadata = dict(connection.execute("SELECT key, value FROM metadata"))
        sex_raw = summary_pct(connection, "genero_atlas_binario")
        age_raw = summary_pct(connection, "idade_atlas")
        region_raw = summary_pct(connection, "regiao")

    sex = {"Mulher": sex_raw["Mulher"], "Homem": sex_raw["Homem"]}
    age = {
        "16-24": age_raw["16-24"],
        "25-34": age_raw["25-34"],
        "35-44": age_raw["35-44"],
        "45-59": age_raw["45-59"],
        "60+": age_raw["60-100"],
    }
    region = {key: region_raw[key] for key in ("Norte", "Centro-Oeste", "Nordeste", "Sudeste", "Sul")}

    def compare(targets: dict[str, float], official: dict[str, float]) -> list[dict]:
        return [
            {
                "category": key,
                "nexus": round(value, 3),
                "official": round(official[key], 3),
                "delta": round(value - official[key], 3),
            }
            for key, value in targets.items()
        ]

    return {
        "generated": f"{metadata['dt_geracao']} {metadata['hh_geracao']}",
        "competence": "junho de 2026",
        "source": metadata["source_name"],
        "source_url": metadata["source_url"],
        "universe": "eleitorado residente no Brasil; SG_UF=ZZ (exterior) excluída",
        "resident_electors": int(metadata["total_eleitores_brasil_sem_exterior"]),
        "sex": compare(NEXUS_TARGETS["sex"], sex),
        "age": compare(NEXUS_TARGETS["age"], age),
        "region": compare(NEXUS_TARGETS["region"], region),
    }


def replicate_ci(theta: float, values: list[float], level: float = 0.95) -> dict:
    variance = sum((value - theta) ** 2 for value in values) / (len(values) - 1)
    standard_error = math.sqrt(variance)
    z_score = NormalDist().inv_cdf(0.5 + level / 2)
    margin = z_score * standard_error
    return {
        "estimate": round(theta, 3),
        "se": round(standard_error, 3),
        "moe": round(margin, 3),
        "low": round(theta - margin, 3),
        "high": round(theta + margin, 3),
    }


def pnad_income() -> dict:
    table = "base_anual_visita1_labeled_npv"
    base_weight = "V1032__peso_com_calibracao"
    replicate_weights = [f"V1032{index:03d}__peso_replicado_{index}" for index in range(1, 201)]
    columns = ",".join([base_weight, *replicate_weights])
    query = f"""
        SELECT VD5001__rend_efetivo_domiciliar_mw, {columns}
        FROM {table}
        WHERE V2009__idade_na_data_de_referencia >= 16
          AND TRIM(VD5001__rend_efetivo_domiciliar_mw) <> ''
          AND {base_weight} IS NOT NULL
    """
    labels = ["Até 1 SM", "1-2 SM", "2-5 SM", "5+ SM"]
    base = [0.0] * 4
    rep_bands = [[0.0] * 4 for _ in replicate_weights]
    rep_totals = [0.0] * len(replicate_weights)
    total = 0.0
    persons = 0

    with sqlite3.connect(PNAD_DB) as connection:
        for row in connection.execute(query):
            income, base_value, *rep_values = row
            income = float(income)
            band = 0 if income <= 1 else 1 if income <= 2 else 2 if income <= 5 else 3
            weight = float(base_value or 0)
            base[band] += weight
            total += weight
            for index, value in enumerate(rep_values):
                rep_weight = float(value or 0)
                rep_bands[index][band] += rep_weight
                rep_totals[index] += rep_weight
            persons += 1

    results = []
    for band, label in enumerate(labels):
        estimate = 100 * base[band] / total
        replicate_estimates = [
            100 * rep_bands[index][band] / rep_totals[index]
            for index in range(len(replicate_weights))
        ]
        item = replicate_ci(estimate, replicate_estimates)
        nexus = NEXUS_TARGETS["income_july"][label]
        item.update({"category": label, "nexus": nexus, "delta": round(nexus - estimate, 3)})
        results.append(item)

    return {
        "source": "PNAD Contínua anual, 1ª visita, 2024",
        "universe": "pessoas de 16 anos ou mais com renda efetiva domiciliar válida",
        "income_target": "abril de 2026",
        "minimum_wage": 1621,
        "persons": persons,
        "weighted_people": round(total),
        "weight": "V1032",
        "replicates": 200,
        "variance": "1/(R-1) × Σ(θr-θ)²",
        "bands": results,
    }


def margin_scenarios(n: int = 2003, lula: float = 0.47, flavio: float = 0.44) -> dict:
    z_score = NormalDist().inv_cdf(0.975)
    individual = z_score * math.sqrt(0.25 / n)
    difference_variance = (lula + flavio - (lula - flavio) ** 2) / n
    scenarios = []
    for design_effect in (1.0, 1.5, 2.0):
        margin = z_score * math.sqrt(difference_variance * design_effect)
        gap = 100 * (lula - flavio)
        scenarios.append(
            {
                "deff": design_effect,
                "difference_moe": round(100 * margin, 2),
                "gap_low": round(gap - 100 * margin, 2),
                "gap_high": round(gap + 100 * margin, 2),
                "effective_n": round(n / design_effect),
            }
        )
    return {
        "n": n,
        "published_individual_moe": 2.0,
        "srs_worst_case_moe": round(100 * individual, 2),
        "observed_gap": round(100 * (lula - flavio), 1),
        "scenarios": scenarios,
    }


def financials() -> dict:
    values = {2019: 3.833, 2022: 8.3065, 2023: 10.4191, 2024: 12.3, 2025: 16.7}

    def cagr(start: int, end: int) -> float:
        return 100 * ((values[end] / values[start]) ** (1 / (end - start)) - 1)

    return {
        "unit": "R$ bilhões nominais; lucro líquido ajustado",
        "values": [{"year": year, "profit": value} for year, value in values.items()],
        "bolsonaro_selected_cagr_2019_2022": round(cagr(2019, 2022), 1),
        "lula_cagr_2022_2025": round(cagr(2022, 2025), 1),
        "lula_total_2023_2025": round(sum(values[year] for year in (2023, 2024, 2025)), 1),
        "q1_2026": {"profit": 4.8, "growth_yoy_pct": 42.3},
    }


def file_manifest(source: Path) -> list[dict]:
    output = []
    for path in sorted(source.iterdir()):
        if path.is_file() and path.suffix.lower() in {".pdf", ".html"}:
            output.append(
                {
                    "name": path.name,
                    "bytes": path.stat().st_size,
                    "sha256": sha256(path),
                }
            )
    return output


def _normalize(vector: np.ndarray) -> np.ndarray:
    total = vector.sum()
    return vector / total if total else vector


def _cell_matrix(dimension: str) -> np.ndarray:
    cells = RUNOFF_CROSSTABS[dimension]["cells"]
    return np.array([cells[cat] for cat in cells], dtype=float)


def _margin_topline(cells: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """Weighted vote vector (4-dim, ×100) with each published row renormalized.

    Renormalizing each crosstab row to sum to 1 removes the ±1 pp published
    rounding (rows print as 99–101) before applying the weights.
    """
    rows = cells / cells.sum(axis=1, keepdims=True)
    weights = _normalize(weights)
    return (weights[:, None] * rows).sum(axis=0) * 100.0


def _single_reweight_delta(dimension: str, cells: np.ndarray, ruler: dict) -> np.ndarray:
    """Reweight effect = topline(official ruler) − topline(published profile).

    Anchoring on the same cells cancels the per-margin rounding offset, so the
    delta isolates the pure effect of swapping the Nexus ruler for the official
    one. The scenario score is then RUNOFF_TOPLINE + delta.
    """
    categories = list(RUNOFF_CROSSTABS[dimension]["cells"])
    profile = np.array(
        [RUNOFF_CROSSTABS[dimension]["profile"][cat] for cat in categories], dtype=float
    )
    official = np.array([ruler[cat] for cat in categories], dtype=float)
    return _margin_topline(cells, official) - _margin_topline(cells, profile)


def _combined_reweight_delta(
    matrices: dict[str, np.ndarray],
    nexus: dict[str, np.ndarray],
    official: dict[str, np.ndarray],
    iterations: int = 60,
) -> np.ndarray:
    """Combined (raking/IPF) reweight effect over all five margins at once.

    We do not have Nexus microdata, only one-way vote crosstabs, so we build a
    synthetic joint by independence of the published Nexus margins (the seed)
    and rake a (demographic-cell × vote) array so it reproduces every published
    dim×vote table. That yields a conditional vote p(voto|célula) whose only
    modelling assumption is "no interaction beyond the fitted margins" (the
    minimum-information / main-effects hypothesis). We then swap the Nexus
    demographic weights for the official ones (which, under independence, is the
    product of the official margins) and read off the new vote. The delta is
    anchored the same way as the single-margin scenarios.
    """
    seed = nexus[REWEIGHT_DIMS[0]]
    for dimension in REWEIGHT_DIMS[1:]:
        seed = np.multiply.outer(seed, nexus[dimension])
    published = np.array(list(RUNOFF_TOPLINE.values())) / 100.0
    joint = seed[..., None] * published
    votes = {
        dimension: matrices[dimension] / matrices[dimension].sum(axis=1, keepdims=True)
        for dimension in REWEIGHT_DIMS
    }
    other_axes = tuple(range(len(REWEIGHT_DIMS) - 1))
    for _ in range(iterations):
        row = joint.sum(axis=-1)
        joint *= np.divide(seed, row, out=np.ones_like(row), where=row > 0)[..., None]
        for axis, dimension in enumerate(REWEIGHT_DIMS):
            for index in range(len(nexus[dimension])):
                target = nexus[dimension][index] * votes[dimension][index]
                selector: list[int | slice] = [slice(None)] * (len(REWEIGHT_DIMS) + 1)
                selector[axis] = index
                block = joint[tuple(selector)]
                current = block.sum(axis=other_axes)
                scale = np.divide(
                    target, current, out=np.ones_like(current), where=current > 0
                )
                joint[tuple(selector)] = block * scale
    cell_mass = joint.sum(axis=-1)
    conditional = joint / np.where(cell_mass > 0, cell_mass, 1.0)[..., None]
    top_nexus = (seed[..., None] * conditional).sum(axis=tuple(other_axes) + (len(REWEIGHT_DIMS) - 1,))
    off_seed = official[REWEIGHT_DIMS[0]]
    for dimension in REWEIGHT_DIMS[1:]:
        off_seed = np.multiply.outer(off_seed, official[dimension])
    axes = tuple(range(len(REWEIGHT_DIMS)))
    top_official = (off_seed[..., None] * conditional).sum(axis=axes)
    return (top_official - top_nexus) * 100.0


def _tse_reweight_rulers() -> dict:
    """Official electorate rulers (TSE jun/2026) mapped onto the report bands."""
    with sqlite3.connect(TSE_DB) as connection:
        sex = summary_pct(connection, "genero_atlas_binario")
        raw_age = summary_pct(connection, "idade_raw")
        region = summary_pct(connection, "regiao")

    # Report age bands (16-24 / 25-40 / 41-59 / 60+) from the TSE 5-year bands.
    # The 40–44 bucket straddles the 40/41 cut: split uniformly (age 40 → 25-40,
    # ages 41–44 → 41-59). Documented approximation; 40 is 1/5 of that bucket.
    def band(*keys: str) -> float:
        return sum(raw_age[key] for key in keys)

    b1624 = band("16 anos", "17 anos", "18 anos", "19 anos", "20 anos", "21 a 24 anos")
    b2540 = band("25 a 29 anos", "30 a 34 anos", "35 a 39 anos") + 0.2 * raw_age["40 a 44 anos"]
    b4159 = 0.8 * raw_age["40 a 44 anos"] + band("45 a 49 anos", "50 a 54 anos", "55 a 59 anos")
    b60 = band(
        "60 a 64 anos", "65 a 69 anos", "70 a 74 anos", "75 a 79 anos", "80 a 84 anos",
        "85 a 89 anos", "90 a 94 anos", "95 a 99 anos", "100 anos ou mais",
    )
    total = b1624 + b2540 + b4159 + b60
    age = {
        "16-24": b1624 / total * 100,
        "25-40": b2540 / total * 100,
        "41-59": b4159 / total * 100,
        "60+": b60 / total * 100,
    }
    region_group = {
        label: sum(region[uf] for uf in ufs)
        for label, ufs in REGION_RUNOFF_GROUP.items()
    }
    return {
        "sexo": {
            "target": {"Feminino": sex["Mulher"], "Masculino": sex["Homem"]},
            "source": "TSE jun/2026 — genero_atlas_binario",
        },
        "idade": {
            "target": age,
            "source": "TSE jun/2026 — idade_raw reagrupada nas faixas do relatório",
            "note": "40–44 anos dividido uniformemente (40 → 25-40; 41–44 → 41-59).",
        },
        "regiao": {
            "target": region_group,
            "source": "TSE jun/2026 — regiao (Norte+Centro-Oeste agrupados como no relatório)",
        },
    }


def reweight_scenarios(
    income_bands: list[dict],
    education_3way: dict,
    replicates: int = 10000,
    seed: int = 20260713,
) -> dict:
    """Recompute the runoff Lula×Flávio score under the official universe rulers.

    This is a sensitivity analysis on PUBLISHED, already-weighted cells — not a
    reweighting of microdata. See ``notes`` for the three structural caveats.
    """
    tse = _tse_reweight_rulers()
    income = {item["category"]: item["estimate"] for item in income_bands}
    rulers = {
        "sexo": tse["sexo"],
        "idade": tse["idade"],
        "regiao": tse["regiao"],
        "escolaridade": {
            "target": {
                "Fundamental": education_3way["Fundamental"],
                "Médio": education_3way["Medio"],
                "Superior": education_3way["Superior"],
            },
            "source": "PNAD — escolaridade 3 vias comparável (Fundamental/Médio/Superior)",
        },
        "renda": {
            "target": {
                "Até 1 SM": income["Até 1 SM"],
                "1-2 SM": income["1-2 SM"],
                "2-5 SM": income["2-5 SM"],
                "5+ SM": income["5+ SM"],
            },
            "source": "PNAD — renda efetiva domiciliar em SM (16+)",
        },
    }

    matrices = {dim: _cell_matrix(dim) for dim in REWEIGHT_DIMS}
    nexus = {
        dim: _normalize(
            np.array(list(RUNOFF_CROSSTABS[dim]["profile"].values()), dtype=float)
        )
        for dim in REWEIGHT_DIMS
    }
    official = {
        dim: _normalize(
            np.array(
                [rulers[dim]["target"][cat] for cat in RUNOFF_CROSSTABS[dim]["cells"]],
                dtype=float,
            )
        )
        for dim in REWEIGHT_DIMS
    }
    base = np.array(list(RUNOFF_TOPLINE.values()), dtype=float)

    # Step 1 — validation: profile-weighted reproduction of the 47×44 topline.
    validation = []
    for dim in REWEIGHT_DIMS:
        profile = np.array(
            list(RUNOFF_CROSSTABS[dim]["profile"].values()), dtype=float
        )
        topline = _margin_topline(matrices[dim], profile)
        validation.append(
            {
                "margin": dim,
                "page": RUNOFF_CROSSTABS[dim]["page"],
                "lula": round(topline[0], 2),
                "flavio": round(topline[1], 2),
                "delta_lula": round(topline[0] - base[0], 2),
                "delta_flavio": round(topline[1] - base[1], 2),
                "within_0_5": bool(
                    abs(topline[0] - base[0]) <= 0.5 and abs(topline[1] - base[1]) <= 0.5
                ),
            }
        )

    def score(delta: np.ndarray) -> tuple[float, float, float, float]:
        lula, flavio = base[0] + delta[0], base[1] + delta[1]
        two_way = 100 * lula / (lula + flavio)
        return lula, flavio, lula - flavio, two_way

    def point_delta(scenario_dim: str | None) -> np.ndarray:
        if scenario_dim is None:  # combined
            return _combined_reweight_delta(matrices, nexus, official)
        return _single_reweight_delta(
            scenario_dim, matrices[scenario_dim], rulers[scenario_dim]["target"]
        )

    plan = [("a", None, "baseline publicado")]
    plan += [(key, dim, label) for key, dim, label in REWEIGHT_SCENARIOS]
    plan += [("g", "__combined__", "combinado — raking/IPF sobre as 5 margens")]

    # Monte Carlo: propagate the ±0.5 pp cell rounding through every scenario.
    generator = np.random.default_rng(seed)
    samples = {key: np.zeros((replicates, 4)) for key, *_ in plan}
    for replica in range(replicates):
        perturbed = {
            dim: np.clip(
                matrices[dim] + generator.uniform(-0.5, 0.5, matrices[dim].shape),
                0.0,
                None,
            )
            for dim in REWEIGHT_DIMS
        }
        for key, dim, _ in plan:
            if dim is None:
                delta = np.zeros(4)
            elif dim == "__combined__":
                delta = _combined_reweight_delta(perturbed, nexus, official)
            else:
                delta = _single_reweight_delta(
                    dim, perturbed[dim], rulers[dim]["target"]
                )
            samples[key][replica] = base + delta

    scenarios = []
    for key, dim, label in plan:
        delta = (
            np.zeros(4)
            if dim is None
            else point_delta(None if dim == "__combined__" else dim)
        )
        lula, flavio, gap, two_way = score(delta)
        draws = samples[key]
        gap_draws = draws[:, 0] - draws[:, 1]
        scenarios.append(
            {
                "id": key,
                "label": label,
                "ruler": (
                    None
                    if dim in (None, "__combined__")
                    else rulers[dim]["source"]
                ),
                "lula": round(lula, 2),
                "flavio": round(flavio, 2),
                "gap": round(gap, 2),
                "two_way_lula": round(two_way, 1),
                "delta_lula": round(delta[0], 2),
                "delta_flavio": round(delta[1], 2),
                "delta_gap": round(delta[0] - delta[1], 2),
                "ci95": {
                    "lula": [
                        round(float(np.percentile(draws[:, 0], 2.5)), 2),
                        round(float(np.percentile(draws[:, 0], 97.5)), 2),
                    ],
                    "flavio": [
                        round(float(np.percentile(draws[:, 1], 2.5)), 2),
                        round(float(np.percentile(draws[:, 1], 97.5)), 2),
                    ],
                    "gap": [
                        round(float(np.percentile(gap_draws, 2.5)), 2),
                        round(float(np.percentile(gap_draws, 97.5)), 2),
                    ],
                },
            }
        )

    def crosstab_block(table: dict) -> dict:
        return {
            "page": table["page"],
            "vote_labels": VOTE_LABELS,
            "categories": [
                {
                    "category": cat,
                    "cells": table["cells"][cat],
                    "profile_pct": table["profile"][cat],
                }
                for cat in table["cells"]
            ],
        }

    crosstabs = {dim: crosstab_block(RUNOFF_CROSSTABS[dim]) for dim in REWEIGHT_DIMS}

    extras = []
    for dim, table in RUNOFF_EXTRA_CROSSTABS.items():
        cells = np.array([table["cells"][c] for c in table["cells"]], dtype=float)
        weights = np.array(list(table["profile"].values()), dtype=float)
        topline = _margin_topline(cells, weights)
        extras.append(
            {
                "margin": dim,
                "reweighted": False,
                "reason": "sem régua oficial de universo (não reponderado; só validação)",
                "crosstab": crosstab_block(table),
                "reproduction": {
                    "lula": round(topline[0], 2),
                    "flavio": round(topline[1], 2),
                    "delta_lula": round(topline[0] - base[0], 2),
                    "delta_flavio": round(topline[1] - base[1], 2),
                    "within_0_5": bool(
                        abs(topline[0] - base[0]) <= 0.5
                        and abs(topline[1] - base[1]) <= 0.5
                    ),
                },
            }
        )
    ruler_block = {
        dim: {
            "source": rulers[dim]["source"],
            "target": {k: round(v, 3) for k, v in rulers[dim]["target"].items()},
            **({"note": tse["idade"]["note"]} if dim == "idade" else {}),
        }
        for dim in REWEIGHT_DIMS
    }

    return {
        "question": RUNOFF_QUESTION,
        "published_topline": {**RUNOFF_TOPLINE, "gap": 3.0, "page": "49–50"},
        "method": (
            "Reponderação de estimativas publicadas (não de microdados). "
            "Cenários b–f: recálculo fechado da média das células sob a régua "
            "oficial de cada margem, ancorado como 47×44 + Δ (a diferença cancela "
            "o arredondamento por margem). Cenário g: raking/IPF sobre um conjunto "
            "sintético construído por independência das margens Nexus, reproduzindo "
            "todas as tabelas dim×voto publicadas (erro máx. de reprodução ~0,5 pp)."
        ),
        "crosstabs": crosstabs,
        "extras": {
            "note": (
                "Cruzamentos extraídos como extras (passo 1). 'religião' valida a "
                "coerência mas não é reponderado (sem régua oficial de universo). "
                "'Bolsa Família' (p.46–47) é série histórica em gráfico, sem "
                "participação populacional publicada e sem régua oficial limpa — "
                "não reponderado."
            ),
            "crosstabs": extras,
        },
        "rulers": ruler_block,
        "validation": {
            "reference": {"lula": 47.0, "flavio": 44.0},
            "profile_weights_page": 109,
            "by_margin": validation,
            "note": (
                "Cada margem reproduz o topline 47×44 dentro de ±0,5 pp com os "
                "pesos do perfil publicado (p.109) — confirma um único esquema de "
                "ponderação coerente, sem células editadas à mão."
            ),
        },
        "scenarios": scenarios,
        "monte_carlo": {
            "replicates": replicates,
            "perturbation": "U(−0.5, +0.5) pp independente por célula publicada",
            "seed": seed,
            "reads": "IC de 95% = percentis 2,5/97,5 das réplicas",
        },
        "notes": [
            "Limitação estrutural 1: as células já embutem a ponderação Nexus; "
            "isto reponde estimativas, não microdados. É análise de sensibilidade, "
            "não 'o número correto'.",
            "Limitação estrutural 2: as células são arredondadas ao inteiro (±0,5 "
            "pp). A propagação (Monte Carlo) mostra que o EFEITO da reponderação é "
            "robusto ao arredondamento (o Δ depende da diferença de pesos sobre as "
            "mesmas células, e o ruído quase se cancela).",
            "Limitação estrutural 3: o combinado assume independência das margens "
            "no conjunto sintético e ausência de interações além das margens "
            "ajustadas; a reprodução das tabelas publicadas fica dentro de ~0,5 pp.",
            "A incerteza dominante continua sendo a margem amostral da própria "
            "pesquisa (±2 pp), que engloba todos os cenários: reponderar para a "
            "régua oficial NÃO vira o placar — o 47×44 permanece estatisticamente "
            "compatível com Lula à frente por ~2,6 a 3 pp.",
        ],
    }


def build_payload(source: Path) -> dict:
    cities, overlaps = city_audit(source)
    education_path = ROOT / "data/outputs/atlas_260626/pnad_education_benchmarks.json"
    education = json.loads(education_path.read_text(encoding="utf-8"))
    income = pnad_income()
    return {
        "audit": {
            "report_date": "2026-07-15",
            "registration": "BR-07981/2026",
            "field": "10–12/07/2026",
            "release": "13/07/2026",
            "n": 2003,
            "mode": "CATI/RDD telefônico",
            "contractor": "Banco BTG Pactual S.A.",
            "cost_brl": 164888.89,
        },
        "files": file_manifest(source),
        "series": SERIES,
        "income_series": INCOME_SERIES,
        "cities": cities,
        "city_overlaps": overlaps,
        "uf_distribution": uf_distribution(source),
        "tse": tse_benchmarks(),
        "pnad_income": income,
        "pnad_education": education,
        "reweight": reweight_scenarios(
            income_bands=income["bands"],
            education_3way=education["atlas_3way_comparable"],
        ),
        "margin": margin_scenarios(),
        "btg": financials(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    payload = build_payload(args.source.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.output} ({len(payload['files'])} source files)")


if __name__ == "__main__":
    main()
