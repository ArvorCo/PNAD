#!/usr/bin/env python3
"""Reponderação da renda da AtlasIntel 07/2026 contra a PNADC 2024 e 2025.

A Atlas registra no TSE que a cota de nível econômico vem da ``PNADC 2024`` e
usa faixas em reais **nominais** (até R$ 2.000, R$ 2.000–3.000, R$ 3.000–5.000,
R$ 5.000–10.000, acima de R$ 10.000). Duas coisas decorrem disso e o relatório
não trata nenhuma:

1. faixa nominal envelhece. O mesmo domicílio de 2024, com o mesmo poder de
   compra, aparece uma faixa acima quando a renda é expressa a preços de 2026;
2. a PNADC anual **2025** (visita 1) foi divulgada em maio de 2026, antes do
   campo desta pesquisa (22–27/07/2026). Usar a de 2024 é escolha, não
   limitação.

O script mede as duas coisas separadamente, para que a crítica não dependa da
comparação entre visitas diferentes do painel:

* ``pnadc_2024_v5_nominal``   — a régua equivalente à declarada pela Atlas;
* ``pnadc_2024_v5_target``    — a MESMA pesquisa, a preços do mês-alvo. Isola o
  efeito puro da faixa nominal envelhecida, sem trocar de safra;
* ``pnadc_2025_v1_nominal``   — a safra que a Atlas poderia ter usado;
* ``pnadc_2025_v1_target``    — a safra nova, a preços do mês-alvo.

Depois reponderá o cenário 1 de 1º turno (cruzamento por renda, p.20 e p.21 do
relatório) por cada distribuição. É pós-estratificação em **uma** margem, com o
voto dentro da faixa mantido fixo: análise de sensibilidade, não estimativa
corrigida — a ponderação da Atlas é conjunta e não é pública.

Uso:
  python3 scripts/atlas-072026-renda.py
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "data" / "outputs"
DEFAULT_OUTPUT = ROOT / "docs" / "assets" / "atlas_072026_renda.json"

AGE_COL = "V2009__idade_na_data_de_referencia"
WEIGHT_COL = "V1032__peso_com_calibracao"
INCOME_COL = "VD5007__rend_habitual_domiciliar"
MIN_AGE = 16
# Cortes usados apenas para checar se a conclusão depende do universo escolhido.
AGE_CUTS = (0, 16, 18, 25)

# Alvo de deflação: último mês disponível na série IPCA do repositório.
TARGET_MONTH = "202604"

VINTAGES = {
    "pnadc_2024_v5": {
        "file": OUTPUTS / "base_anual_labeled_npv.csv",
        "label": "PNADC anual 2024 · visita 5",
        "deflated_col": f"{INCOME_COL}_202603",
        "deflated_from": "202603",
    },
    "pnadc_2025_v1": {
        "file": OUTPUTS / "base_anual_visita1_labeled_npv.csv",
        "label": "PNADC anual 2025 · visita 1",
        "deflated_col": f"{INCOME_COL}_202604",
        "deflated_from": "202604",
    },
}

BAND_CEILINGS = (2000.0, 3000.0, 5000.0, 10000.0)
BAND_LABELS = (
    "até R$ 2.000",
    "R$ 2.000–3.000",
    "R$ 3.000–5.000",
    "R$ 5.000–10.000",
    "acima de R$ 10.000",
)

# Registro TSE BR-08602/2026 e perfil publicado no relatório.
ATLAS_QUOTA = [22.4, 17.1, 23.1, 23.9, 13.5]
ATLAS_SAMPLE = [22.1, 17.9, 23.2, 23.4, 13.3]

# Cenário 1 de 1º turno por faixa de renda familiar (relatório, p.20 e p.21).
VOTE_BY_BAND = {
    "Lula": [53.5, 37.1, 35.8, 47.8, 52.8],
    "Flávio Bolsonaro": [35.3, 40.9, 41.4, 33.4, 24.1],
    "Renan Santos": [3.4, 7.2, 10.6, 8.5, 9.3],
    "Ronaldo Caiado": [0.6, 5.3, 2.7, 3.0, 5.3],
    "Romeu Zema": [1.4, 1.3, 3.7, 2.9, 5.4],
    "Samara Martins": [1.9, 3.5, 2.0, 1.8, 1.3],
    "Augusto Cury": [3.7, 1.6, 0.7, 1.0, 0.6],
    "Cabo Daciolo": [0.0, 0.0, 0.1, 0.0, 0.1],
    "Hertz Dias": [0.0, 0.1, 0.1, 0.0, 0.3],
    "Rui Costa Pimenta": [0.0, 0.0, 0.0, 0.0, 0.1],
    "Edmilson Costa": [0.0, 0.0, 0.2, 0.0, 0.0],
    "Voto branco/nulo": [0.1, 1.4, 0.6, 0.7, 0.3],
    "Não sei": [0.0, 1.8, 2.1, 0.6, 0.4],
}

# Faixa colada no teto de R$ 3.000, usada para demonstrar o mecanismo:
# dois salários mínimos de 2024 valem R$ 2.824 e de 2025 valem R$ 3.036.
PILEUP_RANGE = (2700.0, 3000.0)
MIN_WAGE = {"2024": 1412.0, "2025": 1518.0, "2026": 1621.0}


def band_of(value: float) -> int:
    for index, ceiling in enumerate(BAND_CEILINGS):
        if value < ceiling:
            return index
    return len(BAND_CEILINGS)


def ipca_factor(from_month: str, to_month: str) -> float:
    """Return the multiplicative factor between two months of the IPCA series."""
    if from_month == to_month:
        return 1.0
    series: dict[str, float] = {}
    with (OUTPUTS / "ipca.csv").open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            series[row["date"].replace("-", "")] = float(row["index"])
    return series[to_month] / series[from_month]


def scan(path: Path, columns: dict[str, float]) -> dict[str, Any]:
    """Stream one PNADC file and accumulate weighted band shares per column."""
    totals = {name: 0.0 for name in columns}
    bands = {name: [0.0] * 5 for name in columns}
    pileup = 0.0
    pileup_total = 0.0

    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        index = {name: header.index(name) for name in columns}
        age_at = header.index(AGE_COL)
        weight_at = header.index(WEIGHT_COL)
        nominal_at = header.index(INCOME_COL)

        for row in reader:
            try:
                weight = float(row[weight_at])
                age = int(row[age_at])
            except ValueError:
                continue
            if weight <= 0 or age < MIN_AGE:
                continue

            nominal = row[nominal_at].strip()
            if nominal:
                value = float(nominal)
                pileup_total += weight
                if PILEUP_RANGE[0] <= value < PILEUP_RANGE[1]:
                    pileup += weight

            for name, scale in columns.items():
                raw = row[index[name]].strip()
                if not raw:
                    continue
                try:
                    income = float(raw) * scale
                except ValueError:
                    continue
                totals[name] += weight
                bands[name][band_of(income)] += weight

    return {
        "shares": {
            name: [round(100 * cell / totals[name], 1) for cell in bands[name]]
            for name in columns
            if totals[name]
        },
        "universe_millions": round(max(totals.values()) / 1e6, 1),
        "pileup_pct_of_adults": round(100 * pileup / pileup_total, 1),
    }


def scan_age_cuts(path: Path, column: str, scale: float) -> dict[str, list[float]]:
    """Repeat the band count under several minimum-age cuts, in one pass."""
    totals = {cut: 0.0 for cut in AGE_CUTS}
    bands = {cut: [0.0] * 5 for cut in AGE_CUTS}

    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        income_at = header.index(column)
        age_at = header.index(AGE_COL)
        weight_at = header.index(WEIGHT_COL)

        for row in reader:
            try:
                weight = float(row[weight_at])
                age = int(row[age_at])
            except ValueError:
                continue
            raw = row[income_at].strip()
            if weight <= 0 or not raw:
                continue
            try:
                index = band_of(float(raw) * scale)
            except ValueError:
                continue
            for cut in AGE_CUTS:
                if age >= cut:
                    totals[cut] += weight
                    bands[cut][index] += weight

    return {
        str(cut): [round(100 * cell / totals[cut], 1) for cell in bands[cut]]
        for cut in AGE_CUTS
        if totals[cut]
    }


def reweight(distribution: list[float]) -> dict[str, float]:
    """Post-stratify the first-round scenario on the income margin alone."""
    total = sum(distribution)
    weights = [share / total for share in distribution]
    return {
        name: round(sum(a * b for a, b in zip(cells, weights)), 2)
        for name, cells in VOTE_BY_BAND.items()
    }


def build() -> dict[str, Any]:
    distributions: dict[str, list[float]] = {}
    diagnostics: dict[str, Any] = {}

    for key, spec in VINTAGES.items():
        path = spec["file"]
        if not path.exists():
            print(f"aviso: {path} ausente; safra {key} ignorada", file=sys.stderr)
            continue
        factor = ipca_factor(str(spec["deflated_from"]), TARGET_MONTH)
        result = scan(
            path,
            {INCOME_COL: 1.0, str(spec["deflated_col"]): factor},
        )
        distributions[f"{key}_nominal"] = result["shares"][INCOME_COL]
        distributions[f"{key}_target"] = result["shares"][str(spec["deflated_col"])]
        diagnostics[key] = {
            "label": spec["label"],
            "source": str(path.relative_to(ROOT)),
            "universe_millions": result["universe_millions"],
            "rebase_factor_to_target": round(factor, 6),
            "adults_between_2700_and_3000_pct": result["pileup_pct_of_adults"],
        }

    sensitivity: dict[str, Any] = {}
    latest = VINTAGES["pnadc_2025_v1"]
    if latest["file"].exists():
        shares_by_cut = scan_age_cuts(
            latest["file"],
            str(latest["deflated_col"]),
            ipca_factor(str(latest["deflated_from"]), TARGET_MONTH),
        )
        sensitivity = {
            "note": (
                "PNADC 2025 a preços do mês-alvo, variando só o corte de idade. "
                "A distância Lula–Flávio cresce em todos os cortes; o universo "
                "escolhido (16+) é o mais conservador entre os elegíveis a voto."
            ),
            "by_minimum_age": {
                cut: {
                    "shares": shares,
                    "first_round": reweight(shares),
                    "lula_minus_flavio": round(
                        reweight(shares)["Lula"] - reweight(shares)["Flávio Bolsonaro"],
                        2,
                    ),
                }
                for cut, shares in shares_by_cut.items()
            },
        }

    scenarios = {
        "atlas_quota_tse": ATLAS_QUOTA,
        "atlas_amostra_publicada": ATLAS_SAMPLE,
        **distributions,
    }
    toplines = {name: reweight(shares) for name, shares in scenarios.items()}
    baseline = toplines["atlas_amostra_publicada"]
    deltas = {
        name: {
            candidate: round(value - baseline[candidate], 2)
            for candidate, value in line.items()
        }
        for name, line in toplines.items()
    }
    gaps = {
        name: round(line["Lula"] - line["Flávio Bolsonaro"], 2)
        for name, line in toplines.items()
    }

    return {
        "poll": {
            "registration": "BR-08602/2026",
            "field": "2026-07-22/2026-07-27",
            "declared_source": "PNADC 2024 para escolaridade e nível econômico",
            "declared_bands": list(BAND_LABELS),
        },
        "method": {
            "variable": INCOME_COL,
            "universe": f"pessoas de {MIN_AGE} anos ou mais, peso {WEIGHT_COL}",
            "target_month": TARGET_MONTH,
            "minimum_wage": MIN_WAGE,
            "two_minimum_wages": {
                year: round(2 * value) for year, value in MIN_WAGE.items()
            },
            "note": (
                "Reponderação em uma única margem, com o voto dentro da faixa "
                "mantido fixo. É análise de sensibilidade, não estimativa "
                "corrigida: a ponderação da Atlas é conjunta e não é pública."
            ),
        },
        "diagnostics": diagnostics,
        "age_cut_sensitivity": sensitivity,
        "distributions": scenarios,
        "reweighted_first_round": toplines,
        "delta_vs_published": deltas,
        "lula_minus_flavio": gaps,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    audit = build()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print("distribuição da renda familiar (pessoas 16+), em %:")
    for name, shares in audit["distributions"].items():
        print(f"  {name:<28} {shares}")
    cuts = audit["age_cut_sensitivity"].get("by_minimum_age", {})
    if cuts:
        print("\nsensibilidade ao corte de idade (PNADC 2025 a preços do alvo):")
        for cut, row in cuts.items():
            label = "todas as idades" if cut == "0" else f"{cut} anos ou mais"
            print(
                f'  {label:<18} {row["shares"]} · '
                f'gap {row["lula_minus_flavio"]:.2f}'
            )
    print("\n1º turno reponderado só pela margem de renda:")
    for name, line in audit["reweighted_first_round"].items():
        gap = audit["lula_minus_flavio"][name]
        print(
            f'  {name:<28} Lula {line["Lula"]:5.2f} · '
            f'Flávio {line["Flávio Bolsonaro"]:5.2f} · '
            f'Renan {line["Renan Santos"]:4.2f} · gap {gap:5.2f}'
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
