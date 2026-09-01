#!/usr/bin/env python3
"""Reproduce the Quaest/Globo 14 August 2026 dossier calculations.

The public report is image-only. Tables transcribed below carry their report
page beside the values. Internal controls recompose the national topline from
the political-positioning crosstab and close every derived arithmetic identity.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import re
import sys
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
ROUND = ROOT / "data/pesquisas/quaest/2026-08-14"
PREVIOUS = ROOT / "data/pesquisas/quaest/2026-08"
OUTPUT = ROOT / "docs/assets/quaest_globo_140826_data.json"
TERRITORY_OUTPUT = ROOT / "docs/assets/quaest_globo_140826_territory.json"
TERRITORY_CSV = ROUND / "quaest_bairros_140826.csv"
IBGE_REFERENCE = (
    ROOT
    / "data/originals/censo_2022_setores_censitarios"
    / "quaest_sector_reference_2026-08-14.json"
)

FILES = [
    "relatorio.pdf",
    "registro-tse.pdf",
    "questionario.pdf",
    "anexo-territorial.pdf",
    "declaracao.pdf",
    *[f"nota-fiscal-{number}.pdf" for number in range(1, 7)],
]

FIRST_ROUND = {
    "page": 16,
    "values": {
        "Lula": 38,
        "Flávio Bolsonaro": 31,
        "Renan Santos": 4,
        "Ronaldo Caiado": 4,
        "Augusto Cury": 2,
        "Romeu Zema": 2,
        "Samara Martins": 1,
        "Clariana Barão": 0,
        "Edmilson Costa": 0,
        "Hertz Dias": 0,
        "Leonardo Avalanche": 0,
        "Rui Costa Pimenta": 0,
        "Wilson Grassi": 0,
        "Indeciso": 10,
        "Branco, nulo ou não vota": 8,
    },
}

RUNOFFS = {
    "page": [30, 40, 50, 60],
    "values": {
        "Flávio Bolsonaro": {"Lula": 43, "challenger": 40, "blank": 13, "undecided": 4},
        "Ronaldo Caiado": {"Lula": 44, "challenger": 37, "blank": 14, "undecided": 5},
        "Renan Santos": {"Lula": 44, "challenger": 36, "blank": 16, "undecided": 4},
        "Romeu Zema": {"Lula": 45, "challenger": 34, "blank": 16, "undecided": 5},
    },
}

POSITIONING = {
    "page": 24,
    "shares": {
        "Lulista": 19,
        "Esquerda não lulista": 14,
        "Independente": 32,
        "Direita não bolsonarista": 21,
        "Bolsonarista": 12,
        "Não sabe": 2,
    },
    "first_round": {
        "Lulista": {
            "Lula": 91,
            "Flávio": 1,
            "Renan": 0,
            "Caiado": 0,
            "Cury": 0,
            "Zema": 1,
            "Samara": 1,
            "Outros": 1,
            "Indeciso": 3,
            "Branco": 2,
        },
        "Esquerda não lulista": {
            "Lula": 81,
            "Flávio": 2,
            "Renan": 1,
            "Caiado": 0,
            "Cury": 2,
            "Zema": 1,
            "Samara": 1,
            "Outros": 0,
            "Indeciso": 7,
            "Branco": 5,
        },
        "Independente": {
            "Lula": 23,
            "Flávio": 16,
            "Renan": 8,
            "Caiado": 6,
            "Cury": 4,
            "Zema": 3,
            "Samara": 1,
            "Outros": 1,
            "Indeciso": 20,
            "Branco": 18,
        },
        "Direita não bolsonarista": {
            "Lula": 5,
            "Flávio": 70,
            "Renan": 5,
            "Caiado": 6,
            "Cury": 2,
            "Zema": 3,
            "Samara": 0,
            "Outros": 0,
            "Indeciso": 6,
            "Branco": 3,
        },
        "Bolsonarista": {
            "Lula": 3,
            "Flávio": 90,
            "Renan": 1,
            "Caiado": 2,
            "Cury": 0,
            "Zema": 0,
            "Samara": 0,
            "Outros": 0,
            "Indeciso": 2,
            "Branco": 2,
        },
    },
}

SEGMENTS = {
    "page": 31,
    "runoff": {
        "Nordeste": [61, 26],
        "Até 2 SM": [58, 27],
        "Preta": [52, 30],
        "Fundamental": [52, 31],
        "Católica": [50, 36],
        "60 anos ou mais": [48, 35],
        "Mulheres": [44, 35],
        "Parda": [44, 37],
        "Centro-Oeste/Norte": [42, 41],
        "16 a 34 anos": [41, 41],
        "35 a 59 anos": [42, 42],
        "Homens": [41, 45],
        "2 a 5 SM": [38, 43],
        "Branca": [38, 45],
        "Sudeste": [36, 44],
        "Médio": [36, 45],
        "Superior": [36, 47],
        "Mais de 5 SM": [34, 48],
        "Evangélica": [28, 53],
        "Sul": [27, 54],
    },
}

APPROVAL = {
    "pages": [111, 112, 113, 114, 115, 116, 117, 118, 119],
    "national": {"approve": 46, "disapprove": 48, "unknown": 6},
    "disapproval": {
        "Nordeste": 31,
        "Sudeste": 54,
        "Sul": 59,
        "Centro-Oeste/Norte": 48,
        "Mulheres": 45,
        "Homens": 51,
        "16 a 34 anos": 47,
        "35 a 59 anos": 50,
        "60 anos ou mais": 38,
        "Fundamental": 38,
        "Médio": 52,
        "Superior": 57,
        "Até 2 SM": 35,
        "2 a 5 SM": 51,
        "Mais de 5 SM": 57,
        "Católica": 42,
        "Evangélica": 60,
        "Branca": 43,
        "Parda": 43,
        "Preta": 40,
        "Independente": 48,
        "Direita não bolsonarista": 88,
        "Bolsonarista": 94,
    },
}

CHANNELS = {
    "pages": [161, 162, 163, 164, 165, 166, 167],
    "national": {
        "Redes sociais": 35,
        "TV": 34,
        "Sites": 10,
        "Amigos/família": 6,
        "Rádio": 3,
        "WhatsApp": 3,
        "Impresso": 2,
        "Chat com IA": 1,
        "Não se informa": 5,
        "Não sabe": 1,
    },
    "segments": {
        "Mulheres": [31, 38],
        "Homens": [38, 29],
        "16 a 34 anos": [56, 15],
        "35 a 59 anos": [30, 39],
        "60 anos ou mais": [16, 52],
        "Fundamental": [23, 43],
        "Médio": [42, 29],
        "Superior": [45, 23],
        "Até 2 SM": [30, 39],
        "2 a 5 SM": [35, 33],
        "Mais de 5 SM": [36, 28],
        "Lulista": [21, 47],
        "Esquerda não lulista": [33, 32],
        "Independente": [33, 32],
        "Direita não bolsonarista": [48, 25],
        "Bolsonarista": [39, 31],
    },
}

SAMPLE_SHARES = {
    "region": {"Nordeste": 27, "Sudeste": 42, "Sul": 14, "Centro-Oeste/Norte": 17},
    "sex": {"Mulheres": 53, "Homens": 47},
    "age": {"16 a 34 anos": 31, "35 a 59 anos": 45, "60 anos ou mais": 24},
    "education": {"Fundamental": 41, "Médio": 40, "Superior": 19},
    "income": {"Até 2 SM": 31, "2 a 5 SM": 42, "Mais de 5 SM": 27},
}

OTHER_FINDINGS = {
    "vote_certainty_page": 28,
    "vote_certainty": {
        "Lula": 77,
        "Flávio Bolsonaro": 70,
        "Renan Santos": 57,
        "Ronaldo Caiado": 55,
        "Romeu Zema": 23,
    },
    "potential_rejection_page": 71,
    "potential_rejection": {
        "Lula": [45, 52],
        "Flávio Bolsonaro": [41, 54],
        "Ronaldo Caiado": [22, 35],
        "Romeu Zema": [19, 34],
        "Renan Santos": [14, 21],
    },
    "fear_page": 81,
    "fear": {
        "Família Bolsonaro": 45,
        "Mais Lula": 41,
        "Ambos": 6,
        "Nenhum": 3,
        "Não sabe": 5,
    },
    "expected_winner_page": 91,
    "expected_winner": {
        "Lula": 56,
        "Flávio Bolsonaro": 27,
        "Renan Santos": 1,
        "Romeu Zema": 1,
        "Ronaldo Caiado": 1,
        "Não sabe": 14,
    },
    "direction_page": 131,
    "direction": {"Errada": 53, "Certa": 38, "Não sabe": 9},
    "economy_past_page": 141,
    "economy_past": {"Piorou": 49, "Ficou igual": 30, "Melhorou": 19, "Não sabe": 2},
    "food_page": 145,
    "food": {"Subiu": 68, "Ficou igual": 22, "Caiu": 8, "Não sabe": 2},
    "economy_future_page": 149,
    "economy_future": {"Melhorar": 42, "Ficar igual": 24, "Piorar": 28, "Não sabe": 6},
    "concerns_page": 154,
    "concerns": {
        "Violência": 33,
        "Economia": 15,
        "Saúde": 14,
        "Corrupção": 14,
        "Questões sociais": 12,
        "Educação": 7,
        "Outros": 5,
    },
    "ideology_page": 169,
    "ideology": {"Esquerda": 23, "Centro": 20, "Direita": 40, "Não sabe": 17},
    "morals_page": 178,
    "morals": {"Progressista": 28, "Nenhum": 18, "Conservador": 54},
}

TRANSFER_SOURCES = {
    "Lula": 38,
    "Flávio": 31,
    "Renan": 4,
    "Caiado": 4,
    "Augusto Cury": 2,
    "Zema": 2,
    "Samara": 1,
    "Indeciso 1º": 10,
    "Branco 1º": 8,
}
TRANSFER_TARGETS = {"Lula": 43, "Flávio": 40, "Branco 2º": 13, "Indeciso 2º": 4}
TRANSFER_PRIOR = {
    "Lula": [0.995, 0.0, 0.0, 0.005],
    "Flávio": [0.0, 0.995, 0.0, 0.005],
    "Renan": [0.06, 0.58, 0.34, 0.02],
    "Caiado": [0.12, 0.50, 0.36, 0.02],
    "Augusto Cury": [0.25, 0.60, 0.12, 0.03],
    "Zema": [0.08, 0.55, 0.35, 0.02],
    "Samara": [0.98, 0.0, 0.01, 0.01],
    "Indeciso 1º": [0.18, 0.18, 0.34, 0.30],
    "Branco 1º": [0.10, 0.15, 0.72, 0.03],
}

PUBLISHED_QUESTIONS = [2, 3, 4, 6, *range(8, 36), 38, 39, 44, 45, 46, 48, 49, 50, 51]
WITHHELD_SUBSTANTIVE = {
    36: "importância da eleição",
    37: "emoções provocadas pela eleição",
    40: "influência partidária na decisão",
    41: "possibilidade de interferência estrangeira",
    42: "ideologia de presidentes estrangeiros que ajudaria",
    43: "aprovação do uso de IA em campanhas",
    47: "principal sonho",
    52: "voto recordado no segundo turno de 2022",
    53: "comparecimento declarado em 2024",
}


def pdf_text(path: Path) -> str:
    return "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pages(path: Path) -> int:
    return len(PdfReader(path).pages)


def round_values(values: dict[str, float], digits: int = 3) -> dict[str, float]:
    return {key: round(value, digits) for key, value in values.items()}


def weighted(values: dict[str, float], shares: dict[str, float]) -> float:
    assert set(values) == set(shares)
    assert math.isclose(sum(shares.values()), 100)
    return sum(values[key] * shares[key] for key in shares) / 100


def multinomial_difference_moe(a: float, b: float, n: int = 2004) -> float:
    pa, pb = a / 100, b / 100
    se = math.sqrt((pa + pb - (pa - pb) ** 2) / n)
    return 1.96 * 100 * se


def ipf() -> list[list[float]]:
    rows = list(TRANSFER_SOURCES)
    matrix = [
        [TRANSFER_SOURCES[row] * value for value in TRANSFER_PRIOR[row]] for row in rows
    ]
    for _ in range(10_000):
        for i, target in enumerate(TRANSFER_SOURCES.values()):
            factor = target / sum(matrix[i])
            matrix[i] = [value * factor for value in matrix[i]]
        for j, target in enumerate(TRANSFER_TARGETS.values()):
            current = sum(matrix[i][j] for i in range(len(rows)))
            factor = target / current
            for i in range(len(rows)):
                matrix[i][j] *= factor
        row_error = max(
            abs(sum(matrix[i]) - target)
            for i, target in enumerate(TRANSFER_SOURCES.values())
        )
        col_error = max(
            abs(sum(matrix[i][j] for i in range(len(rows))) - target)
            for j, target in enumerate(TRANSFER_TARGETS.values())
        )
        if max(row_error, col_error) < 1e-11:
            break
    else:
        raise RuntimeError("IPF did not converge")
    return matrix


def transfer_payload() -> dict:
    rows = list(TRANSFER_SOURCES)
    columns = list(TRANSFER_TARGETS)
    matrix = ipf()
    cells = {
        row: round_values(dict(zip(columns, matrix[index])), 3)
        for index, row in enumerate(rows)
    }
    lula_gain = TRANSFER_TARGETS["Lula"] - cells["Lula"]["Lula"]
    flavio_gain = TRANSFER_TARGETS["Flávio"] - cells["Flávio"]["Flávio"]
    return {
        "method": "IPF/RAS with explicit ideological prior and structural zeros",
        "published_matrix_found": False,
        "measured_origin_rows": 0,
        "estimated_origin_rows": len(rows),
        "sources": TRANSFER_SOURCES,
        "targets": TRANSFER_TARGETS,
        "prior": {
            key: dict(zip(columns, values)) for key, values in TRANSFER_PRIOR.items()
        },
        "matrix": cells,
        "outside_base_gain": {
            "Lula": round(lula_gain, 3),
            "Flávio": round(flavio_gain, 3),
            "Flávio_to_Lula_ratio": round(flavio_gain / lula_gain, 3),
        },
        "warning": "All ribbons are estimates. Aggregate consolidation is constrained by published margins; candidate-level splits depend on the prior.",
    }


def positioning_control() -> dict:
    shares = POSITIONING["shares"]
    known_share = 100 - shares["Não sabe"]
    recomposed = {}
    for candidate in ("Lula", "Flávio"):
        key = "Flávio" if candidate == "Flávio" else candidate
        recomposed[candidate] = sum(
            shares[bloc] * POSITIONING["first_round"][bloc][key] / 100
            for bloc in POSITIONING["first_round"]
        )
    return {
        "known_position_share": known_share,
        "recomposed": round_values(recomposed),
        "published": {"Lula": 38, "Flávio": 31},
        "residual_context": "The crosstab excludes the 2% without a declared political position and uses rounded cells.",
    }


def conversion_gaps() -> dict:
    runoff = {name: values[1] for name, values in SEGMENTS["runoff"].items()}
    gaps = {
        segment: APPROVAL["disapproval"][segment] - flavio
        for segment, flavio in runoff.items()
    }
    partition_results = {}
    for partition, shares in SAMPLE_SHARES.items():
        disapproval = weighted(
            {segment: APPROVAL["disapproval"][segment] for segment in shares},
            shares,
        )
        flavio = weighted({segment: runoff[segment] for segment in shares}, shares)
        partition_results[partition] = {
            "disapproval": round(disapproval, 2),
            "Flávio_runoff": round(flavio, 2),
            "addressable_ceiling_gap": round(disapproval - flavio, 2),
        }
    return {
        "segment_gaps": gaps,
        "closed_partitions": partition_results,
        "label": "addressable ceiling, not forecast",
    }


def invoice_payload() -> dict:
    paths = [ROUND / f"nota-fiscal-{number}.pdf" for number in range(1, 7)]
    texts = [pdf_text(path) for path in paths]
    normalized = [re.sub(r"\s+", " ", text).upper() for text in texts]
    required = ["409.646,00", "314.628,00", "570.108,00", "7 PESQUISAS"]
    for path, text in zip(paths, normalized):
        missing = [value for value in required if value not in text]
        if missing:
            raise ValueError(f"Invoice transcription failed for {path}: {missing}")
    invoice_numbers = [455, 456, 479, 480, 481, 482]
    recipients = ["Globo Comunicação e Participações", "Editora Globo"] * 3
    installments = [1, 1, 2, 2, 3, 3]
    dates = [
        "2026-07-22",
        "2026-07-22",
        "2026-08-04",
        "2026-08-04",
        "2026-08-04",
        "2026-08-04",
    ]
    entries = [
        {
            "file": path.name,
            "nfs_e": number,
            "recipient": recipient,
            "installment": installment,
            "issued": issued,
            "amount_brl": 409_646,
        }
        for path, number, recipient, installment, issued in zip(
            paths, invoice_numbers, recipients, installments, dates
        )
    ]
    regular = 314_628
    seventh = 570_108
    previous = 433_255.92
    total = sum(item["amount_brl"] for item in entries)
    assert total == 6 * regular + seventh == 3 * 819_292
    return {
        "entries": entries,
        "contract": {
            "polls": 7,
            "regular_polls": 6,
            "regular_poll_brl": regular,
            "seventh_poll_brl": seventh,
            "installments": 3,
            "installment_brl": 819_292,
            "total_brl": total,
            "due_dates": ["2026-07-25", "2026-08-25", "2026-09-25"],
        },
        "current_vs_genial_previous": {
            "current_brl": regular,
            "previous_brl": previous,
            "difference_brl": round(regular - previous, 2),
            "difference_pct": round(100 * (regular / previous - 1), 2),
            "current_cost_per_interview_brl": round(regular / 2004, 2),
            "previous_cost_per_interview_brl": round(previous / 2004, 2),
            "seventh_premium_pct": round(100 * (seventh / regular - 1), 2),
        },
        "interpretation": "The six invoices are paired 50% shares of three contract installments, not six separate payments for this single round.",
    }


def instrument_payload() -> dict:
    published = sorted(set(PUBLISHED_QUESTIONS))
    assert len(published) == 41
    all_questions = set(range(1, 54))
    withheld = sorted(all_questions - set(published))
    assert withheld == [1, 5, 7, 36, 37, 40, 41, 42, 43, 47, 52, 53]
    return {
        "current": {
            "numbered_questions": 53,
            "questionnaire_pages": pages(ROUND / "questionario.pdf"),
            "promised_minutes": 10,
            "report_pages": pages(ROUND / "relatorio.pdf"),
            "published_questions": published,
            "published_count": len(published),
            "published_pct": round(100 * len(published) / 53, 1),
            "withheld": withheld,
            "withheld_substantive": WITHHELD_SUBSTANTIVE,
        },
        "previous": {
            "numbered_questions": 109,
            "questionnaire_pages": pages(PREVIOUS / "questionario.pdf"),
            "promised_minutes": 20,
            "report_pages": pages(PREVIOUS / "relatorio.pdf"),
            "published_count": 58,
            "published_pct": round(100 * 58 / 109, 1),
        },
        "change": {
            "questions": -56,
            "questions_pct": round(100 * (53 / 109 - 1), 1),
            "questionnaire_pages": -16,
            "questionnaire_pages_pct": round(100 * (23 / 39 - 1), 1),
            "promised_minutes_pct": -50,
            "report_pages": 83,
            "report_pages_pct": round(100 * (197 / 114 - 1), 1),
            "publication_coverage_pp": round(100 * 41 / 53 - 100 * 58 / 109, 1),
        },
    }


def uncertainty_payload() -> dict:
    first_moe = multinomial_difference_moe(38, 31)
    runoff_moe = multinomial_difference_moe(43, 40)
    first_lead = 7
    return {
        "assumption": "simple random sample approximation; actual weights, PSU covariance and design effect are unpublished",
        "first_round": {
            "lead": first_lead,
            "difference_moe_95": round(first_moe, 2),
            "difference_interval_95": [
                round(first_lead - first_moe, 2),
                round(first_lead + first_moe, 2),
            ],
            "deff_to_include_zero": round((first_lead / first_moe) ** 2, 2),
            "rho_with_six_per_sector": round(
                (((first_lead / first_moe) ** 2) - 1) / 5, 3
            ),
        },
        "runoff": {
            "lead": 3,
            "difference_moe_95": round(runoff_moe, 2),
            "difference_interval_95": [
                round(3 - runoff_moe, 2),
                round(3 + runoff_moe, 2),
            ],
            "statistically_clear_under_srs": False,
        },
        "wave_change": "The 39 to 38 Lula and 30 to 31 Flávio first-round movement is within sampling noise under an SRS approximation.",
    }


def load_territory_module():
    script = ROOT / "scripts/quaest-territory-audit.py"
    spec = importlib.util.spec_from_file_location(
        "quaest_territory_audit_aug14", script
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def territory_payload(refresh: bool) -> dict:
    module = load_territory_module()
    previous = module.parse_pdf(
        PREVIOUS / "anexo-territorial.pdf", "05/08/2026", "BR-06591/2026"
    )
    current = module.parse_pdf(
        ROUND / "anexo-territorial.pdf", "14/08/2026", "BR-06773/2026"
    )
    reference = module.load_or_refresh_reference(
        [*previous, *current], IBGE_REFERENCE, refresh
    )
    module.write_csv(TERRITORY_CSV, current, reference)
    comparison = module.compare_rounds(previous, current)
    rounds = {
        "previous": module.round_summary(previous, reference),
        "current": module.round_summary(current, reference),
    }
    for summary in rounds.values():
        summary["capital_sectors"] = sum(
            1
            for row in (previous if summary is rounds["previous"] else current)
            if row.municipality_code in module.CAPITAL_CODES
        )
    statuses = {}
    for item in reference["sectors"].values():
        status = item.get("validation", "unknown")
        statuses[status] = statuses.get(status, 0) + 1
    result = {
        "metadata": {
            "comparison": "05/08/2026 vs 14/08/2026",
            "unit": "15-digit IBGE 2022 census-sector geocode",
            "warning": "Locations contain no vote or final weight; they cannot explain candidate shares.",
        },
        "rounds": rounds,
        "comparison": comparison,
        "ibge_validation": {
            "retrieved": reference["retrieved"],
            "statuses": statuses,
            "errors": reference.get("errors", {}),
            "reference_file": str(IBGE_REFERENCE.relative_to(ROOT)),
        },
        "design": {
            "sectors": 334,
            "interviews_per_sector": 6,
            "region_allocation_identical": rounds["previous"]["regions"]
            == rounds["current"]["regions"],
            "capital_interviews_identical": 510,
        },
    }
    TERRITORY_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    TERRITORY_OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return result


def source_manifest() -> dict:
    result = {}
    for name in FILES:
        path = ROUND / name
        if not path.exists():
            raise FileNotFoundError(path)
        result[name] = {
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
            "pages": pages(path),
        }
    return result


def validate_transcriptions() -> None:
    if sum(FIRST_ROUND["values"].values()) != 100:
        raise ValueError("First-round transcription does not close to 100")
    for challenger, values in RUNOFFS["values"].items():
        if sum(values.values()) != 100:
            raise ValueError(f"Runoff transcription does not close for {challenger}")
    for bloc, values in POSITIONING["first_round"].items():
        if sum(values.values()) != 100:
            raise ValueError(f"Positioning row does not close for {bloc}")
    for name, shares in SAMPLE_SHARES.items():
        if sum(shares.values()) != 100:
            raise ValueError(f"Sample partition does not close for {name}")


def build_payload(refresh_ibge: bool) -> dict:
    validate_transcriptions()
    territory = territory_payload(refresh_ibge)
    segment_margins = {
        segment: flavio - lula for segment, (lula, flavio) in SEGMENTS["runoff"].items()
    }
    return {
        "metadata": {
            "registry": "BR-06773/2026",
            "registered": "2026-08-08",
            "published": "2026-08-14",
            "field": ["2026-08-10", "2026-08-13"],
            "interviews": 2004,
            "mode": "in-person household interview",
            "municipalities": 120,
            "census_sectors": 334,
            "interviews_per_sector": 6,
            "contractors": [
                "Globo Comunicação e Participações S/A",
                "Editora Globo S/A",
            ],
            "sources": source_manifest(),
        },
        "instrument": instrument_payload(),
        "invoices": invoice_payload(),
        "first_round": FIRST_ROUND,
        "runoffs": RUNOFFS,
        "positioning": POSITIONING,
        "positioning_control": positioning_control(),
        "segments": {**SEGMENTS, "Flávio_margin": segment_margins},
        "approval": APPROVAL,
        "conversion_gap": conversion_gaps(),
        "channels": CHANNELS,
        "other_findings": OTHER_FINDINGS,
        "uncertainty": uncertainty_payload(),
        "transfer": transfer_payload(),
        "territory_summary": {
            "rounds": territory["rounds"],
            "comparison": territory["comparison"],
            "ibge_validation": territory["ibge_validation"],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--refresh-ibge", action="store_true")
    args = parser.parse_args()
    payload = build_payload(args.refresh_ibge)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    summary = {
        "output": str(args.output.relative_to(ROOT)),
        "territory_output": str(TERRITORY_OUTPUT.relative_to(ROOT)),
        "first_round": [38, 31],
        "runoff": [43, 40],
        "runoff_srs_interval": payload["uncertainty"]["runoff"][
            "difference_interval_95"
        ],
        "addressable_gap_region": payload["conversion_gap"]["closed_partitions"][
            "region"
        ]["addressable_ceiling_gap"],
        "transfer_ratio": payload["transfer"]["outside_base_gain"][
            "Flávio_to_Lula_ratio"
        ],
        "common_municipalities": payload["territory_summary"]["comparison"][
            "common_municipalities"
        ],
        "common_exact_sectors": payload["territory_summary"]["comparison"][
            "common_exact_sectors"
        ],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
