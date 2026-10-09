#!/usr/bin/env python3
"""Soma os dois turnos presidenciais dos ZIPs TSE locais, sem extrair os CSVs."""

import csv
import hashlib
import io
import json
import zipfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "analysis/reponderacao/comparecimento/tse_2018_2022.json"
FIELDS = ("QT_APTOS", "QT_COMPARECIMENTO", "QT_ABSTENCOES")


def aggregate(rows):
    totals = defaultdict(lambda: defaultdict(int))
    seen, dates = set(), set()
    for row in rows:
        if row["CD_CARGO"] != "1" or row["NR_TURNO"] not in ("1", "2"):
            continue
        ident = tuple(
            row[k] for k in ("NR_TURNO", "SG_UF", "CD_MUNICIPIO", "NR_ZONA", "NR_SECAO")
        )
        if ident in seen:
            raise ValueError(f"Seção presidencial repetida: {ident}")
        seen.add(ident)
        dates.add(row["DT_GERACAO"])
        counts = {k: int(row[k]) for k in FIELDS}
        if any(v < 0 for v in counts.values()):
            raise ValueError("Contagem negativa")
        residual = (
            counts["QT_APTOS"] - counts["QT_COMPARECIMENTO"] - counts["QT_ABSTENCOES"]
        )
        # Em 2018 a situação de instalação pode vir #NULO#. Aptos com
        # comparecimento e ausência ambos zero ficam como resíduo documental.
        if residual and not (
            residual > 0 and counts["QT_COMPARECIMENTO"] == counts["QT_ABSTENCOES"] == 0
        ):
            raise ValueError(f"Seção não fecha: {ident}")
        scopes = ["Brasil e exterior"] + (["Brasil"] if row["SG_UF"] != "ZZ" else [])
        for scope in scopes:
            d = totals[(row["NR_TURNO"], scope)]
            for key, value in counts.items():
                d[key] += value
            d["secoes"] += 1
    return sorted(dates), [
        {"turno": int(t), "scope": s, **d} for (t, s), d in totals.items()
    ]


def extract(year):
    path = ROOT / f"data/raw/tse_resultados/detalhe_votacao_secao_{year}.zip"
    member = f"detalhe_votacao_secao_{year}_BR.csv"
    with zipfile.ZipFile(path) as archive, archive.open(member) as binary:
        dates, totals = aggregate(
            csv.DictReader(io.TextIOWrapper(binary, encoding="latin1"), delimiter=";")
        )
    return {
        "year": year,
        "source": {
            "url": f"https://cdn.tse.jus.br/estatistica/sead/odsele/detalhe_votacao_secao/detalhe_votacao_secao_{year}.zip",
            "path": str(path.relative_to(ROOT)),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "member": member,
            "generated_dates": dates,
        },
        "rounds": totals,
    }


def main():
    OUTPUT.write_text(
        json.dumps([extract(y) for y in (2018, 2022)], ensure_ascii=False, indent=2)
        + "\n"
    )
    print(f"Escrito {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
