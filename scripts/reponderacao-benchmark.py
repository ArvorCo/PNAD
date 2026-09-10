#!/usr/bin/env python3
"""Histograma de renda domiciliar da PNADC anual, a régua do agregador Arvor.

Lê uma única vez o microdado anual (visita 1 de 2025, já deflacionado pelo
pipeline ``npv_deflators.py``) e grava um histograma ponderado, em caixas de
R$ 10, do rendimento domiciliar para quatro universos:

* ``pessoas16_efetivo``: pessoas de 16 anos ou mais, VD5001 (rendimento efetivo
  domiciliar). É o universo declarado pelos institutos no registro do TSE e a
  régua principal do agregador.
* ``pessoas16_habitual``: mesmo universo, VD5007 (rendimento habitual), usado
  como variante de robustez.
* ``domicilios_efetivo`` e ``domicilios_habitual``: uma linha por domicílio
  (pessoa responsável, V2005 = 01), com o peso calibrado dessa pessoa.

Com o histograma gravado, qualquer corte de faixa em reais (o cartão de renda
de cada instituto) vira uma soma de caixas, sem reler 1,5 GB por pesquisa.
Uso: ``python3 scripts/reponderacao-benchmark.py`` (grava
``analysis/reponderacao/pnad_2025v1_histograma.json``).
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "outputs" / "base_anual_visita1_labeled_npv.csv"
DEFAULT_OUTPUT = ROOT / "analysis" / "reponderacao" / "pnad_2025v1_histograma.json"

PRICE_MONTH = "202604"
AGE_COL = "V2009__idade_na_data_de_referencia"
WEIGHT_COL = "V1032__peso_com_calibracao"
ROLE_COL = "V2005__condicao_no_domicilio"
EFETIVO_COL = f"VD5001__rend_efetivo_domiciliar_{PRICE_MONTH}"
HABITUAL_COL = f"VD5007__rend_habitual_domiciliar_{PRICE_MONTH}"
MIN_AGE = 16
BIN = 10.0
CEILING = 100_000.0
BINS = int(CEILING / BIN)

SERIES = {
    "pessoas16_efetivo": (EFETIVO_COL, False),
    "pessoas16_habitual": (HABITUAL_COL, False),
    "domicilios_efetivo": (EFETIVO_COL, True),
    "domicilios_habitual": (HABITUAL_COL, True),
}


def bin_index(value: float) -> int:
    if value >= CEILING:
        return BINS
    return int(value // BIN)


def scan(path: Path) -> dict[str, Any]:
    """Uma passagem pelo arquivo, acumulando os quatro histogramas."""
    hist = {name: [0.0] * (BINS + 1) for name in SERIES}
    missing = dict.fromkeys(SERIES, 0.0)
    rows = 0
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        at = {name: header.index(name) for name in (AGE_COL, WEIGHT_COL, ROLE_COL)}
        cols = {name: header.index(spec[0]) for name, spec in SERIES.items()}
        for row in reader:
            rows += 1
            try:
                weight = float(row[at[WEIGHT_COL]])
                age = int(row[at[AGE_COL]])
            except ValueError:
                continue
            if weight <= 0 or age < MIN_AGE:
                continue
            is_head = row[at[ROLE_COL]].strip().lstrip("0") == "1"
            for name, (_, households) in SERIES.items():
                if households and not is_head:
                    continue
                raw = row[cols[name]].strip()
                if not raw:
                    missing[name] += weight
                    continue
                hist[name][bin_index(float(raw))] += weight
    return {
        "source": str(path.relative_to(ROOT)),
        "rows_read": rows,
        "benchmark": "PNADC anual 2025, visita 1",
        "price_month": PRICE_MONTH,
        "weight": WEIGHT_COL,
        "min_age": MIN_AGE,
        "bin_width_brl": BIN,
        "ceiling_brl": CEILING,
        "series": {
            name: {
                "column": SERIES[name][0],
                "universe": (
                    "domicílios (pessoa responsável, V2005 = 01)"
                    if SERIES[name][1]
                    else f"pessoas de {MIN_AGE} anos ou mais"
                ),
                "total_weight": sum(hist[name]),
                "missing_weight": missing[name],
                "counts": [round(cell, 3) for cell in hist[name]],
            }
            for name in SERIES
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Histograma de renda da PNADC para o agregador."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    if not args.input.exists():
        print(f"arquivo não encontrado: {args.input}", file=sys.stderr)
        return 1
    data = scan(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    for name, series in data["series"].items():
        millions = series["total_weight"] / 1e6
        print(
            f"{name:22s} {millions:8.1f} mi  faltantes {series['missing_weight'] / 1e6:5.1f} mi"
        )
    print(f"gravado em {args.output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
