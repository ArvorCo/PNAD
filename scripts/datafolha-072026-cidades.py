#!/usr/bin/env python3
"""Concentração territorial das ondas nacionais do Datafolha (maio-julho/2026).

Lê o CSV já extraído dos anexos de bairros (``datafolha-072026-audit.py``) e
responde às perguntas que o relatório publicado não responde:

* quantos municípios se repetem em todas as ondas;
* que fração das entrevistas de julho está em municípios herdados de maio;
* quantas unidades da federação ficam de fora do desenho "nacional";
* qual o tamanho do conglomerado por ponto de fluxo — insumo do efeito de
  desenho, já que o Datafolha publica margem, mas não publica deff.

Uso:
  python3 scripts/datafolha-072026-cidades.py
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "outputs" / "datafolha_bairros_072026_compare.csv"
DEFAULT_OUTPUT = ROOT / "docs" / "assets" / "datafolha_072026_territorio.json"

UF_BRASIL = {
    "AC",
    "AL",
    "AP",
    "AM",
    "BA",
    "CE",
    "DF",
    "ES",
    "GO",
    "MA",
    "MT",
    "MS",
    "MG",
    "PA",
    "PB",
    "PR",
    "PE",
    "PI",
    "RJ",
    "RN",
    "RS",
    "RO",
    "RR",
    "SC",
    "SP",
    "SE",
    "TO",
}
WAVES = ("2026-05", "2026-06", "2026-07")
LATEST = "2026-07"


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def city_key(row: dict[str, str]) -> str:
    return row["municipality_code"]


def build_report(rows: list[dict[str, str]]) -> dict[str, Any]:
    by_wave: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_wave[row["wave"]].append(row)

    names: dict[str, str] = {}
    cities: dict[str, set[str]] = {}
    for wave in WAVES:
        cities[wave] = {city_key(row) for row in by_wave[wave]}
        for row in by_wave[wave]:
            names[city_key(row)] = f'{row["municipality"]}/{row["uf"]}'

    persistent = cities[WAVES[0]] & cities[WAVES[1]] & cities[WAVES[2]]
    latest = by_wave[LATEST]
    total_interviews = sum(int(row["interviews"]) for row in latest)
    inherited = sum(
        int(row["interviews"]) for row in latest if city_key(row) in persistent
    )

    interviews_by_city: Counter[str] = Counter()
    for row in latest:
        interviews_by_city[city_key(row)] += int(row["interviews"])
    top = interviews_by_city.most_common(12)

    ufs_present = {row["uf"] for row in latest}
    cluster_sizes = Counter(int(row["interviews"]) for row in latest)

    churn = {
        "june_to_july_out": sorted(
            names[code] for code in cities["2026-06"] - cities["2026-07"]
        ),
        "june_to_july_in": sorted(
            names[code] for code in cities["2026-07"] - cities["2026-06"]
        ),
        "may_to_june_out": sorted(
            names[code] for code in cities["2026-05"] - cities["2026-06"]
        ),
    }

    return {
        "source_csv": str(DEFAULT_INPUT.relative_to(ROOT)),
        "waves": {
            wave: {
                "points": len(by_wave[wave]),
                "cities": len(cities[wave]),
                "interviews": sum(int(row["interviews"]) for row in by_wave[wave]),
            }
            for wave in WAVES
        },
        "persistent_cities": {
            "count": len(persistent),
            "share_of_july_cities_pct": round(
                100 * len(persistent) / len(cities[LATEST]), 1
            ),
            "july_interviews_inside": inherited,
            "share_of_july_interviews_pct": round(
                100 * inherited / total_interviews, 1
            ),
        },
        "city_churn": churn,
        "concentration": {
            "top_cities": [
                {
                    "city": names[code],
                    "interviews": count,
                    "share_pct": round(100 * count / total_interviews, 1),
                }
                for code, count in top
            ],
            "top_11_share_pct": round(
                100 * sum(count for _, count in top[:11]) / total_interviews, 1
            ),
        },
        "federal_coverage": {
            "ufs_present": len(ufs_present),
            "ufs_absent": sorted(UF_BRASIL - ufs_present),
            "absent_in_every_wave": sorted(UF_BRASIL - {row["uf"] for row in rows}),
        },
        "cluster_profile": {
            "interviews_per_point": dict(sorted(cluster_sizes.items())),
            "modal_cluster_size": cluster_sizes.most_common(1)[0][0],
            "note": (
                "Conglomerado de tamanho fixo: quase todo setor entrega "
                "exatamente 6 entrevistas. É o insumo direto do efeito de "
                "desenho que o relatório não publica."
            ),
        },
        "limitations": [
            "Repetição de município é repetição documental de unidade primária, "
            "não repetição do mesmo entrevistado.",
            "Amostra-mestra fixa é prática legítima e reduz a variância da "
            "variação entre ondas; o problema auditável é a ausência de "
            "probabilidades de seleção, estratos e efeito de desenho.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    report = build_report(load_rows(args.input))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    persistent: dict[str, Any] = report["persistent_cities"]
    coverage: dict[str, Any] = report["federal_coverage"]
    churn: dict[str, Any] = report["city_churn"]
    absent = ", ".join(coverage["absent_in_every_wave"]) or "nenhuma"
    print(
        f'{persistent["count"]} municípios nas três ondas; '
        f'{persistent["share_of_july_interviews_pct"]}% das entrevistas de '
        f"julho estão neles."
    )
    print(f'UFs cobertas: {coverage["ufs_present"]}; ausentes sempre: {absent}.')
    print(
        f'Trocas junho->julho: saiu {churn["june_to_july_out"]}, '
        f'entrou {churn["june_to_july_in"]}.'
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
