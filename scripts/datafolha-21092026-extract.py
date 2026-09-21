#!/usr/bin/env python3
"""Extract every native-text cross-tab of Datafolha BR-04029/2026."""

from __future__ import annotations

import json
import re
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "data/pesquisas/datafolha/2026-09-17"
COLUMNS = {
    1: [
        "Total",
        "Masculino",
        "Feminino",
        "16-24",
        "25-34",
        "35-44",
        "45-59",
        "60+",
        "Fundamental",
        "Medio",
        "Superior",
    ],
    2: [
        "Total",
        "Ate 2 SM",
        "2 a 5 SM",
        "Mais de 5 SM",
        "PEA",
        "Nao PEA",
        "Branca",
        "Preta",
        "Parda",
        "Catolica",
        "Evangelica",
    ],
    3: [
        "Total",
        "Sudeste",
        "Sul",
        "Nordeste",
        "Centro-Oeste/Norte",
        "Regiao metropolitana",
        "Interior",
        "PT",
        "PL",
        "Outro partido",
        "Nao tem",
    ],
}
PAGES = {
    "espontanea": [32, 33],
    "estimulada_b": [34, 35, 36],
    "validos_b": [37, 38],
    "rejeicao": [39, 40, 41],
    "turno2_flavio": [42],
    "turno2_caiado": [43],
    "turno2_zema": [44],
    "turno2_renan": [45],
    "turno2_cury": [46],
    "definicao": [47],
    "motivacao": [48],
    "avaliacao": [49],
    "aprovacao": [50],
}
NUMBER = re.compile(r"^\d+$")
DASHES = {"–", "—", "-"}


def block(body: str, index: int, page: int) -> dict:
    tokens = [x.strip() for x in body.splitlines() if x.strip()]
    end_header = {1: "rior", 2: "Evangélica", 3: "Não tem"}[index]
    tokens = tokens[tokens.index(end_header) + 1 :]
    width = len(COLUMNS[index])
    rows = {}
    while tokens:
        name = []
        while tokens and not NUMBER.fullmatch(tokens[0]) and tokens[0] not in DASHES:
            name.append(tokens.pop(0))
        label = " ".join(name)
        if not label or len(tokens) < width:
            raise ValueError(f"Incomplete row p{page}: {label}")
        cells = tokens[:width]
        tokens = tokens[width:]
        if not all(NUMBER.fullmatch(v) or v in DASHES for v in cells):
            raise ValueError(f"Invalid numeric width p{page}: {label}: {cells}")
        values = [None if v in DASHES else int(v) for v in cells]
        row = dict(zip(COLUMNS[index], values, strict=True))
        if label == "Base ponderada":
            if any(v is None or v < 1 for v in values):
                raise ValueError("Missing base")
            return {
                "pdf_page": page,
                "annex_page": page - 25,
                "columns": COLUMNS[index],
                "rows": rows,
                "base": row,
            }
        if label in rows:
            raise ValueError(f"Duplicate row {label}")
        if any(v is not None and not 0 <= v <= 100 for v in values):
            raise ValueError(label)
        rows[label] = row
    raise ValueError(f"Missing base p{page}")


def extract(pdf: Path) -> dict:
    tables = {}
    with fitz.open(pdf) as doc:
        for key, pages in PAGES.items():
            blocks = {}
            for page in pages:
                parts = re.split(
                    r"Bloco ([123]) de 3,[^\n]*\n", doc[page - 1].get_text()
                )
                for i in range(1, len(parts), 2):
                    n = int(parts[i])
                    blocks[f"bloco{n}"] = block(parts[i + 1], n, page)
            if set(blocks) != {"bloco1", "bloco2", "bloco3"}:
                raise ValueError(key)
            labels = [list(b["rows"]) for b in blocks.values()]
            if any(x != labels[0] for x in labels):
                raise ValueError(f"Row order differs: {key}")
            tables[key] = {"blocks": blocks}
    return tables


def main():
    tables = extract(FOLDER / "relatorio.pdf")
    out = {
        "fonte": {
            "registro": "BR-04029/2026",
            "pdf": "relatorio.pdf",
            "paginas": 50,
            "metodo": "Extração automática do texto nativo, incluindo todas as células e bases das 13 tabelas.",
        },
        "tabelas": tables,
    }
    for path in [
        FOLDER / "cruzamentos.json",
        ROOT / "docs/assets/datafolha_21092026_cruzamentos.json",
    ]:
        path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
    print(
        {
            key: {b: len(v["rows"]) for b, v in t["blocks"].items()}
            for key, t in tables.items()
        }
    )


if __name__ == "__main__":
    main()
