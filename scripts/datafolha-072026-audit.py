#!/usr/bin/env python3
"""Auditoria reproduzível da rodada Datafolha nacional de julho de 2026.

Lê os anexos territoriais de maio, junho e julho, calcula sobreposição de
setores/municípios, verifica duplicidades e emite os números usados no laudo.
Os toplines e as bases de julho são transcrições auditáveis do relatório
Datafolha; os benchmarks do eleitorado vêm do JSON produzido pelo pipeline TSE.

Uso:
  python3 scripts/datafolha-072026-audit.py

Dependência:
  pdfplumber (disponível no runtime Python do workspace do Codex).
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
ORIGINALS = ROOT / "data" / "originals"
OUTPUTS = ROOT / "data" / "outputs"
ANALYSIS = ROOT / "analysis" / "datafolha_072026"

ROUNDS = {
    "2026-05": ORIGINALS / "datafolha_052026" / "BairrosDatafolha052026.pdf",
    "2026-06": ORIGINALS / "datafolha_062026" / "bairrosdatafolha062026.pdf",
    "2026-07": ORIGINALS / "datafolha_072026" / "BairrosDatafolha072026.pdf",
}

JULY_DIR = ORIGINALS / "datafolha_072026"
TSE_BENCHMARK = OUTPUTS / "tse_eleitorado_perfil_benchmark.json"
OUT_JSON = ANALYSIS / "audit.json"
OUT_CSV = OUTPUTS / "datafolha_bairros_072026_compare.csv"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clean(value: object) -> str:
    return " ".join(str(value or "").replace("\n", " ").split())


def extract_locations(path: Path, wave: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with pdfplumber.open(path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            for table in page.extract_tables():
                for cells in table:
                    if len(cells) < 6:
                        continue
                    region, uf, city, neighborhood, sector, interviews = map(
                        clean, cells[:6]
                    )
                    # Em algumas linhas longas de junho, o PDF corta a palavra
                    # do bairro no limite da coluna e empurra seu sufixo, junto
                    # com o geocódigo, para a célula do setor.
                    joined_location = clean(f"{neighborhood} {sector}")
                    digits = "".join(
                        ch if ch.isdigit() else " " for ch in joined_location
                    )
                    candidates = [part for part in digits.split() if len(part) == 15]
                    if not candidates:
                        continue
                    sector = candidates[-1]
                    neighborhood = clean(joined_location.rsplit(sector, 1)[0])
                    if not interviews.isdigit():
                        continue
                    rows.append(
                        {
                            "wave": wave,
                            "page": page_number,
                            "region": region,
                            "uf": uf,
                            "municipality": city,
                            "municipality_code": sector[:7],
                            "neighborhood": neighborhood,
                            "sector": sector,
                            "interviews": int(interviews),
                        }
                    )
    if not rows:
        raise RuntimeError(f"Nenhuma linha territorial extraída de {path}")
    return rows


def overlap(current: set[str], previous: set[str]) -> dict[str, object]:
    repeated = current & previous
    return {
        "repeated": len(repeated),
        "current_total": len(current),
        "previous_total": len(previous),
        "share_of_current_pct": round(100 * len(repeated) / len(current), 1),
    }


def difference_margin(p_a: float, p_b: float, n: int, z: float = 1.96) -> float:
    """Margem da diferença em pontos percentuais sob amostragem aleatória simples."""
    variance = ((p_a + p_b) - (p_a - p_b) ** 2) / n
    return 100 * z * math.sqrt(variance)


def deff_to_include_zero(gap_pp: float, srs_margin_pp: float) -> float:
    return (gap_pp / srs_margin_pp) ** 2


def segment_diagnostics(
    segments: dict[str, dict[str, dict[str, float | int]]],
) -> dict[str, object]:
    """Calcula incerteza AAS e contribuição aritmética de cada recorte."""
    diagnostics: dict[str, object] = {}
    for dimension, groups in segments.items():
        base_total = sum(int(group.get("base", 0)) for group in groups.values())
        dimension_groups: dict[str, object] = {}
        for name, group in groups.items():
            if "base" not in group:
                dimension_groups[name] = {
                    "status": "unavailable_without_published_base"
                }
                continue
            lula = float(group["lula"]) / 100
            flavio = float(group["flavio"]) / 100
            base = int(group["base"])
            gap = float(group["flavio"]) - float(group["lula"])
            margin = difference_margin(lula, flavio, base)
            dimension_groups[name] = {
                "flavio_minus_lula_pp": round(gap, 2),
                "srs_margin_of_difference_pp": round(margin, 2),
                "srs_95ci_flavio_minus_lula_pp": [
                    round(gap - margin, 2),
                    round(gap + margin, 2),
                ],
                "deff_threshold_to_include_zero": round(
                    deff_to_include_zero(abs(gap), margin), 2
                ),
                "arithmetic_contribution_pp": round(gap * base / base_total, 2),
            }
        diagnostics[dimension] = {
            "published_base_total": base_total,
            "groups": dimension_groups,
        }
    return diagnostics


def load_tse() -> dict[str, object]:
    source = json.loads(TSE_BENCHMARK.read_text(encoding="utf-8"))
    # O arquivo do projeto já separa Brasil sem exterior. Aceita pequenas
    # mudanças de chave para manter o script útil em rebuilds futuros.
    for key in (
        "poll_universe_brazil_excluding_exterior",
        "brasil_sem_exterior",
        "excluding_exterior",
        "brazil_excluding_exterior",
    ):
        if key in source:
            return source[key]
    return source


def main() -> None:
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    ANALYSIS.mkdir(parents=True, exist_ok=True)

    locations = {wave: extract_locations(path, wave) for wave, path in ROUNDS.items()}
    sectors = {
        wave: {str(row["sector"]) for row in rows} for wave, rows in locations.items()
    }
    municipalities = {
        wave: {str(row["municipality_code"]) for row in rows}
        for wave, rows in locations.items()
    }
    neighborhoods = {
        wave: {
            f'{row["municipality_code"]}|{str(row["neighborhood"]).upper()}'
            for row in rows
        }
        for wave, rows in locations.items()
    }

    july_sector_counts = Counter(str(row["sector"]) for row in locations["2026-07"])
    duplicate_sectors = []
    for sector, count in july_sector_counts.items():
        if count <= 1:
            continue
        duplicate_sectors.append(
            {
                "sector": sector,
                "occurrences": count,
                "rows": [
                    row for row in locations["2026-07"] if row["sector"] == sector
                ],
            }
        )

    second_round_margin = difference_margin(0.48, 0.43, 2004)
    first_round_margin = difference_margin(0.40, 0.32, 2004)
    tse = load_tse()

    original_manifest = []
    for path in sorted(JULY_DIR.glob("*.pdf")):
        original_manifest.append(
            {
                "file": path.name,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )

    output = {
        "generated_from": {
            "territory_pdfs": {
                wave: str(path.relative_to(ROOT)) for wave, path in ROUNDS.items()
            },
            "tse_benchmark": str(TSE_BENCHMARK.relative_to(ROOT)),
        },
        "national_poll": {
            "registration": "BR-01166/2026",
            "sample": 2004,
            "municipalities_reported": 139,
            "field_report": "2026-07-22/2026-07-23",
            "field_registry": "2026-07-22/2026-07-24",
            "registered_cost_brl": 307541.60,
            "invoice_cost_brl": 307641.60,
            "cost_difference_brl": 100.00,
            "cost_difference_pct": round(100 * 100 / 307541.60, 4),
            "registered_cost_per_interview_brl": round(307541.60 / 2004, 2),
            "invoice_cost_per_interview_brl": round(307641.60 / 2004, 2),
            "toplines": {
                "first_round": {"lula": 40, "flavio": 32, "gap_pp": 8},
                "second_round": {
                    "lula": 48,
                    "flavio": 43,
                    "gap_pp": 5,
                    "srs_margin_of_difference_pp": round(second_round_margin, 2),
                    "srs_95ci_gap_pp": [
                        round(5 - second_round_margin, 2),
                        round(5 + second_round_margin, 2),
                    ],
                    "deff_threshold_to_include_zero": round(
                        deff_to_include_zero(5, second_round_margin), 2
                    ),
                },
                "first_round_gap_srs": {
                    "margin_of_difference_pp": round(first_round_margin, 2),
                    "deff_threshold_to_include_zero": round(
                        deff_to_include_zero(8, first_round_margin), 2
                    ),
                },
            },
            "second_round_segments": {
                "gender": {
                    "men": {"lula": 45, "flavio": 46, "base": 959},
                    "women": {"lula": 50, "flavio": 40, "base": 1045},
                },
                "age": {
                    "16-24": {"lula": 46, "flavio": 41, "base": 251},
                    "25-34": {"lula": 47, "flavio": 44, "base": 369},
                    "35-44": {"lula": 38, "flavio": 53, "base": 393},
                    "45-59": {"lula": 50, "flavio": 39, "base": 508},
                    "60+": {"lula": 55, "flavio": 37, "base": 483},
                },
                "education": {
                    "fundamental": {"lula": 59, "flavio": 34, "base": 594},
                    "secondary": {"lula": 45, "flavio": 45, "base": 900},
                    "higher": {"lula": 39, "flavio": 48, "base": 509},
                },
                "income_minimum_wages": {
                    "up_to_2": {"lula": 56, "flavio": 36, "base": 1002},
                    "2_to_5": {"lula": 39, "flavio": 50, "base": 678},
                    "5_to_10": {"lula": 38, "flavio": 51, "base": 194},
                    "over_10": {"lula": 45, "flavio": 51, "base": 51},
                },
                "region": {
                    "southeast": {"lula": 44, "flavio": 46, "base": 840},
                    "south": {"lula": 36, "flavio": 52, "base": 294},
                    "northeast": {"lula": 62, "flavio": 29, "base": 552},
                    "center_west_north": {"lula": 42, "flavio": 49, "base": 317},
                },
                "religion": {
                    "catholic": {"lula": 54, "flavio": 37},
                    "evangelical": {"lula": 31, "flavio": 60},
                },
            },
        },
        "territory": {
            "rounds": {
                wave: {
                    "rows": len(rows),
                    "unique_sectors": len(sectors[wave]),
                    "unique_municipalities": len(municipalities[wave]),
                    "interviews": sum(int(row["interviews"]) for row in rows),
                }
                for wave, rows in locations.items()
            },
            "may_to_june": {
                "sectors": overlap(sectors["2026-06"], sectors["2026-05"]),
                "municipalities": overlap(
                    municipalities["2026-06"], municipalities["2026-05"]
                ),
            },
            "june_to_july": {
                "sectors": overlap(sectors["2026-07"], sectors["2026-06"]),
                "municipalities": overlap(
                    municipalities["2026-07"], municipalities["2026-06"]
                ),
                "neighborhood_labels": overlap(
                    neighborhoods["2026-07"], neighborhoods["2026-06"]
                ),
            },
            "may_to_july": {
                "sectors": overlap(sectors["2026-07"], sectors["2026-05"]),
                "municipalities": overlap(
                    municipalities["2026-07"], municipalities["2026-05"]
                ),
            },
            "all_three": {
                "sectors": len(
                    sectors["2026-05"] & sectors["2026-06"] & sectors["2026-07"]
                ),
                "municipalities": len(
                    municipalities["2026-05"]
                    & municipalities["2026-06"]
                    & municipalities["2026-07"]
                ),
            },
            "duplicate_sectors_july": duplicate_sectors,
        },
        "tse_benchmark": tse,
        "original_manifest": original_manifest,
        "limitations": [
            "A margem calculada para a diferença pressupõe amostragem aleatória simples; o desenho real usa estratos, pontos de fluxo, cotas e ponderação.",
            "Sem pesos individuais, conglomerados e microdados, não é possível calcular o efeito de desenho real nem reestimar o resultado.",
            "Sobreposição territorial identifica repetição documental de setor, não repetição do mesmo entrevistado.",
        ],
    }

    segments = output["national_poll"]["second_round_segments"]
    output["national_poll"]["second_round_segment_diagnostics"] = segment_diagnostics(
        segments
    )
    target_subgroup_n = math.ceil(1.96**2 * 0.25 * 1.5 / 0.05**2)
    share_5_to_10_sm = 194 / 2004
    output["national_poll"]["policy_diagnostic_sample_planning"] = {
        "assumed_deff": 1.5,
        "target_margin_single_proportion_pp": 5,
        "required_subgroup_n": target_subgroup_n,
        "observed_share_5_to_10_sm": round(share_5_to_10_sm, 4),
        "estimated_national_n_for_5_to_10_sm_target": math.ceil(
            target_subgroup_n / share_5_to_10_sm
        ),
    }

    OUT_JSON.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    with OUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "wave",
            "page",
            "region",
            "uf",
            "municipality",
            "municipality_code",
            "neighborhood",
            "sector",
            "interviews",
            "sector_in_may",
            "sector_in_june",
            "sector_in_july",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for wave in ROUNDS:
            for row in locations[wave]:
                sector = str(row["sector"])
                writer.writerow(
                    {
                        **row,
                        "sector_in_may": int(sector in sectors["2026-05"]),
                        "sector_in_june": int(sector in sectors["2026-06"]),
                        "sector_in_july": int(sector in sectors["2026-07"]),
                    }
                )

    print(f"OK: {OUT_JSON.relative_to(ROOT)}")
    print(f"OK: {OUT_CSV.relative_to(ROOT)}")
    print(
        "Julho: "
        f'{output["territory"]["rounds"]["2026-07"]["unique_sectors"]} setores únicos; '
        f'{output["territory"]["june_to_july"]["sectors"]["repeated"]} repetidos desde junho.'
    )


if __name__ == "__main__":
    main()
