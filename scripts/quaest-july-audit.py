#!/usr/bin/env python3
"""Rebuild the evidence ledger for the July 2026 Genial/Quaest audit.

The generator keeps measurements and provenance in JSON. Editorial judgments
stay in the HTML report. Run with the bundled workspace Python because PDF
extraction requires ``pypdf``.
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

try:
    from pypdf import PdfReader
except ModuleNotFoundError as error:  # pragma: no cover - environment guidance
    raise SystemExit(
        "Dependência ausente: instale o extra de auditoria com "
        "`python3 -m pip install -e '.[audit]'`."
    ) from error

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/pesquisas/quaest/2026-07"
JUNE_SOURCE = ROOT / "data/pesquisas/quaest/2026-06"
OUTPUT = ROOT / "docs/assets/quaest_0726_data.json"
TERRITORY_OUTPUT = ROOT / "docs/assets/quaest_0726_territory.json"
PNAD_DB = ROOT / "data/outputs/brasil.sqlite"
TSE_DB = ROOT / "data/outputs/tse_eleitorado_perfil.sqlite"

REPORT = "Quaest_072026.pdf"
QUESTIONNAIRE = "Quaest_Questionario_072026.pdf"
JUNE_QUESTIONNAIRE = "questionario_quaest.pdf"

QUAEST_TARGETS = {
    "sex": {"Mulher": 53.0, "Homem": 47.0},
    "age": {"16-34": 32.0, "35-59": 45.0, "60+": 23.0},
    "region": {
        "Norte": 9.0,
        "Centro-Oeste": 8.0,
        "Nordeste": 27.0,
        "Sudeste": 41.0,
        "Sul": 15.0,
    },
    "income": {"Até 2 SM": 31.0, "2-5 SM": 42.0, "5+ SM": 27.0},
}

VOTE_SERIES = {
    "first_round": {
        "dates": ["jun/26", "jul/26"],
        "Lula": [39, 40],
        "Flávio Bolsonaro": [29, 28],
        "gap": [10, 12],
    },
    "runoff": {
        "dates": ["jun/26", "jul/26"],
        "Lula": [44, 45],
        "Flávio Bolsonaro": [38, 37],
        "gap": [6, 8],
    },
    "spontaneous": {
        "dates": ["jun/26", "jul/26"],
        "Lula": [23, 26],
        "Flávio Bolsonaro": [17, 14],
        "gap": [6, 12],
        "indecisos": [56, 54],
    },
    "runoff_july": [
        {"opponent": "Flávio Bolsonaro", "lula": 45, "opponent_pct": 37, "gap": 8},
        {"opponent": "Ronaldo Caiado", "lula": 45, "opponent_pct": 36, "gap": 9},
        {"opponent": "Romeu Zema", "lula": 45, "opponent_pct": 35, "gap": 10},
        {"opponent": "Renan Santos", "lula": 45, "opponent_pct": 33, "gap": 12},
    ],
    "candidate_image": {
        "Lula": {
            "june_could_vote": 45,
            "july_could_vote": 47,
            "june_reject": 53,
            "july_reject": 50,
        },
        "Flávio Bolsonaro": {
            "june_could_vote": 39,
            "july_could_vote": 38,
            "june_reject": 56,
            "july_reject": 57,
        },
    },
    "government": {
        "approval": {"june": 47, "july": 48},
        "disapproval": {"june": 48, "july": 47},
        "positive": {"june": 34, "july": 36},
        "negative": {"june": 38, "july": 36},
    },
}

# Manual page-by-page reconciliation between the registered 101-item instrument
# and the 121-page public deck. A question is "published" only when a topline or
# crosstab for that numbered item appears in the deck.
PUBLISHED_QUESTIONS = {
    2,
    3,
    4,
    6,
    8,
    *range(9, 21),
    21,
    22,
    *range(23, 27),
    27,
    28,
    31,
    32,
    40,
    41,
    43,
    *range(46, 57),
    *range(66, 77),
    78,
    79,
    *range(84, 87),
    89,
    90,
    91,
    *range(95, 100),
}

UNPUBLISHED_GROUPS = [
    {
        "name": "Operacionais e perfil",
        "questions": [1, 5, 7],
        "note": "Elegibilidade, ocupação e consentimento para gravação.",
    },
    {
        "name": "Diagnóstico eleitoral",
        "questions": [29, 30],
        "note": "Melhor resultado para o Brasil e expectativa de vencedor.",
    },
    {
        "name": "Engajamento eleitoral",
        "questions": list(range(33, 40)),
        "note": "Sete ações de interesse e participação na eleição.",
    },
    {
        "name": "País e MEI",
        "questions": [42, 44, 45],
        "note": "Direção do país e duas perguntas sobre política para MEIs.",
    },
    {
        "name": "EUA, tarifas e voto",
        "questions": list(range(57, 66)),
        "note": "Nove itens sobre EUA, tarifaço, Lula, Flávio e efeito no voto.",
    },
    {
        "name": "Michelle, mulheres e Paulo Figueiredo",
        "questions": [77, 80, 81, 82, 83],
        "note": "O deck corta justamente voto, gênero e o bloco Paulo Figueiredo.",
    },
    {
        "name": "Economia doméstica",
        "questions": [87, 88],
        "note": "Renda versus preços e situação econômica da família.",
    },
    {
        "name": "Ideologia e voto passado",
        "questions": [92, 93, 94, 100, 101],
        "note": "Esquerda/centro/direita, afetos partidários e recordação de voto.",
    },
]

FINANCIAL_HALF_YEARS = {
    2019: {"june": -7_832_564.34, "december": 8_018_759.38},
    2022: {"june": -12_711_549.01, "december": 20_552_824.55},
    2023: {"june": -2_590_908.16, "december": -8_619_305.37},
    2024: {"june": -197_605.87, "december": 15_847_497.86},
    2025: {"june": -7_764_921.74, "december": 6_719_750.03},
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def pdf_text(path: Path) -> str:
    return "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)


def file_manifest(source: Path) -> list[dict]:
    result = []
    for path in sorted(source.iterdir()):
        if path.is_file() and path.name != "README.md":
            result.append(
                {
                    "name": path.name,
                    "bytes": path.stat().st_size,
                    "sha256": sha256(path),
                }
            )
    return result


def _count_template_residue(july: str) -> dict:
    """Count unresolved CAPI template placeholders semantically.

    pypdf extraction breaks the trailing ``AQUI`` token onto the next line in
    several slots, so a naive contiguous ``count`` undercounts. Collapse all
    runs of whitespace to a single space before matching so that a placeholder
    split across a line break still registers as one occurrence.
    """
    collapsed = re.sub(r"\s+", " ", july.upper())
    item = collapsed.count("TRAZER ITEM AQUI")
    opcao = collapsed.count("TRAZER OPÇÃO AQUI")
    return {
        "trazer_item_aqui": item,
        "trazer_opcao_aqui": opcao,
        "total": item + opcao,
    }


def questionnaire_diagnostics() -> dict:
    july = pdf_text(SOURCE / QUESTIONNAIRE)
    june = pdf_text(JUNE_SOURCE / JUNE_QUESTIONNAIRE)
    numbered = sorted(
        {
            int(value)
            for value in re.findall(r"(?m)^\s*(\d{1,3})\.\s", july)
            if int(value) <= 101
        }
    )
    return {
        "pages": len(PdfReader(SOURCE / QUESTIONNAIRE).pages),
        "numbered_range": [min(numbered), max(numbered)],
        "expected_question_count": 101,
        "cover_project": "OP093/25 – GENIAL INVESTIMENTOS",
        "cover_month": "JUNHO/2026",
        "pdf_metadata_title": PdfReader(SOURCE / QUESTIONNAIRE).metadata.title,
        "template_residue": _count_template_residue(july),
        "typos": {"sm_ja_sabia": july.upper().count("SM, JÁ SABIA")},
        "privacy": {
            "opening_promise": "respostas não são associadas ao seu nome",
            "july_closing_request": ["nome", "telefone", "email", "CPF", "Instagram"],
            "july_printed_fields": ["nome", "telefone", "email"],
            "june_closing_request": ["nome", "telefone", "email"],
            "cpf_added_in_july": "CPF" in july and "CPF" not in june,
        },
    }


def publication_coverage() -> dict:
    all_questions = set(range(1, 102))
    unpublished = sorted(all_questions - PUBLISHED_QUESTIONS)
    grouped = sorted(
        question for group in UNPUBLISHED_GROUPS for question in group["questions"]
    )
    if unpublished != grouped:
        raise ValueError("unpublished question grouping is inconsistent")
    return {
        "total_numbered_questions": 101,
        "published": len(PUBLISHED_QUESTIONS),
        "unpublished": len(unpublished),
        "published_pct": round(100 * len(PUBLISHED_QUESTIONS) / 101, 1),
        "published_ids": sorted(PUBLISHED_QUESTIONS),
        "unpublished_ids": unpublished,
        "groups": UNPUBLISHED_GROUPS,
        "method": "manual reconciliation of numbered questionnaire items against public deck pages",
    }


def summary_pct(connection: sqlite3.Connection, dimension: str) -> dict[str, float]:
    sql = "SELECT category, pct_total FROM summary WHERE dimension = ?"
    return {row[0]: float(row[1]) for row in connection.execute(sql, (dimension,))}


def tse_benchmarks() -> dict:
    with sqlite3.connect(TSE_DB) as connection:
        metadata = dict(connection.execute("SELECT key, value FROM metadata"))
        sex_raw = summary_pct(connection, "genero_atlas_binario")
        age_raw = summary_pct(connection, "idade_atlas")
        region_raw = summary_pct(connection, "regiao")
    official = {
        "sex": {"Mulher": sex_raw["Mulher"], "Homem": sex_raw["Homem"]},
        "age": {
            "16-34": age_raw["16-24"] + age_raw["25-34"],
            "35-59": age_raw["35-44"] + age_raw["45-59"],
            "60+": age_raw["60-100"],
        },
        "region": {name: region_raw[name] for name in QUAEST_TARGETS["region"]},
    }

    def compare(dimension: str) -> list[dict]:
        return [
            {
                "category": category,
                "quaest": target,
                "official": round(official[dimension][category], 3),
                "delta": round(target - official[dimension][category], 3),
            }
            for category, target in QUAEST_TARGETS[dimension].items()
        ]

    return {
        "generated": f"{metadata['dt_geracao']} {metadata['hh_geracao']}",
        "competence": "junho de 2026",
        "source": metadata["source_name"],
        "source_url": metadata["source_url"],
        "universe": "eleitorado residente no Brasil; exterior excluído",
        "resident_electors": int(metadata["total_eleitores_brasil_sem_exterior"]),
        "sex": compare("sex"),
        "age": compare("age"),
        "region": compare("region"),
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
    replicate_weights = [
        f"V1032{index:03d}__peso_replicado_{index}" for index in range(1, 201)
    ]
    columns = ",".join([base_weight, *replicate_weights])
    query = f"""
        SELECT VD5001__rend_efetivo_domiciliar_mw, {columns}
        FROM {table}
        WHERE V2009__idade_na_data_de_referencia >= 16
          AND TRIM(VD5001__rend_efetivo_domiciliar_mw) <> ''
          AND {base_weight} IS NOT NULL
    """
    labels = ["Até 2 SM", "2-5 SM", "5+ SM"]
    base = [0.0] * 3
    rep_bands = [[0.0] * 3 for _ in replicate_weights]
    rep_totals = [0.0] * len(replicate_weights)
    total = 0.0
    persons = 0
    with sqlite3.connect(PNAD_DB) as connection:
        for row in connection.execute(query):
            income, base_value, *rep_values = row
            income = float(income)
            band = 0 if income <= 2 else 1 if income <= 5 else 2
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
            100 * rep_bands[index][band] / rep_totals[index] for index in range(200)
        ]
        item = replicate_ci(estimate, replicate_estimates)
        target = QUAEST_TARGETS["income"][label]
        item.update(
            {"category": label, "quaest": target, "delta": round(target - estimate, 3)}
        )
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
        "bands": results,
    }


def margin_scenarios(n: int = 2004, lula: float = 0.45, flavio: float = 0.37) -> dict:
    z_score = NormalDist().inv_cdf(0.975)
    individual = z_score * math.sqrt(0.25 / n)
    difference_variance = (lula + flavio - (lula - flavio) ** 2) / n
    gap = 100 * (lula - flavio)
    scenarios = []
    for design_effect in (1.0, 1.5, 2.0):
        margin = z_score * math.sqrt(difference_variance * design_effect)
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
        "observed_gap": round(gap, 1),
        "scenarios": scenarios,
        "warning": "scenario analysis, not a substitute for the unpublished survey-specific covariance and design effect",
    }


def financials() -> dict:
    annual = []
    for year, halves in FINANCIAL_HALF_YEARS.items():
        annual.append(
            {
                "year": year,
                "first_half_million": round(halves["june"] / 1_000_000, 3),
                "second_half_million": round(halves["december"] / 1_000_000, 3),
                "annual_million": round(sum(halves.values()) / 1_000_000, 3),
            }
        )
    return {
        "entity": "Banco Genial S.A.",
        "entity_id_bcb": "45246410",
        "scope": "individual institution and the Genial financial conglomerate report the same net-income values for these dates",
        "unit": "R$ milhões nominais",
        "annual": annual,
        "q1_2026_million": -47.721,
        "source": "Banco Central do Brasil, IF.data, Demonstração de Resultado",
        "source_url": "https://www3.bcb.gov.br/ifdata/index.html",
        "calculation": "annual net income = June half-year result + December half-year result; March 2026 is Q1",
        "retrieved": "2026-07-15",
        "caveat": "These figures describe the poll-paying bank, not every company, fund or shareholder in the wider Genial brand ecosystem.",
    }


def territory_diagnostics() -> dict:
    if not TERRITORY_OUTPUT.exists():
        raise FileNotFoundError(
            "Territorial audit missing. Run "
            "`python3 scripts/quaest-territory-audit.py` first."
        )
    return json.loads(TERRITORY_OUTPUT.read_text(encoding="utf-8"))


def build_payload() -> dict:
    report_text = pdf_text(SOURCE / REPORT)
    if "O que dá mais medo" not in report_text:
        raise ValueError("unexpected July report text")
    return {
        "metadata": {
            "registry": "BR-07181/2026",
            "field": "10–13/07/2026",
            "release": "15/07/2026",
            "sample": 2004,
            "mode": "presencial domiciliar",
            "sponsor": "Banco Genial S.A.",
            "cost_brl": 433255.92,
            "institute": "Quaest Pesquisa e Consultoria Ltda.",
            "statistician": "Margarida Maria de Mendonça — CONRE 6731",
        },
        "manifest": file_manifest(SOURCE),
        "questionnaire": questionnaire_diagnostics(),
        "publication_coverage": publication_coverage(),
        "benchmarks": {"tse": tse_benchmarks(), "pnad_income": pnad_income()},
        "vote": VOTE_SERIES,
        "margin": margin_scenarios(),
        "territory": territory_diagnostics(),
        "financials": financials(),
        "limits": [
            "No respondent-level microdata or final weights were published.",
            "The territorial annex has no respondent outcomes, inclusion probabilities or final weights by sector.",
            "Causal influence from the June public discussion cannot be inferred from temporal sequence alone.",
            "Mention of a service provider or fund in an investigation does not establish criminal responsibility.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    payload = build_payload()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(
        json.dumps(
            {
                "output": str(args.output),
                "unpublished": payload["publication_coverage"]["unpublished"],
                "template_residue": payload["questionnaire"]["template_residue"][
                    "total"
                ],
                "bank_q1_2026_million": payload["financials"]["q1_2026_million"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
