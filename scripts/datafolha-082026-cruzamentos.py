#!/usr/bin/env python3
"""Extracao integral do anexo de tabelas cruzadas do Datafolha BR-04496/2026.

O relatorio completo publicado no PesqEle traz, das paginas 24 a 51 do PDF,
um anexo de 29 paginas com catorze tabelas cruzadas por onze recortes. A
divulgacao usa uma fracao delas. Este modulo le o PDF, reconstroi cada tabela
com a pagina de origem ao lado e valida a leitura recompondo o placar
publicado a partir de cruzamentos independentes.

Nao ha numero digitado a mao aqui: tudo vem do texto do proprio PDF.

Uso:
  python3 scripts/datafolha-082026-cruzamentos.py

Saida:
  analysis/datafolha_082026/cruzamentos.json
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
REPORT = (
    ROOT / "data" / "originals" / "datafolha_082026" / "DatafolhaRelatorio082026.pdf"
)
OUT = ROOT / "analysis" / "datafolha_082026" / "cruzamentos.json"

NUMBER = re.compile(r"^-?\d+$")
DASHES = {"–", "—", "-"}

BLOCK1 = [
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
]
BLOCK2 = [
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
]
BLOCK3 = [
    "Total",
    "Sudeste",
    "Sul",
    "Nordeste",
    "Centro-Oeste/Norte",
    "Regiao metropolitana",
    "Interior",
    "Bolsonaristas",
    "Nao alinhados",
    "Petistas",
    "PT",
    "PL",
    "Outro partido",
    "Sem partido",
]

CANDIDATES_A = [
    "Lula (PT)",
    "Flavio Bolsonaro (PL)",
    "Ronaldo Caiado (PSD)",
    "Renan Santos (MISSAO)",
    "Zema (NOVO)",
    "Pablo Marcal (PRTB)",
    "Augusto Cury (AVANTE)",
    "Samara (UP)",
    "Rui Costa Pimenta (PCO)",
    "Wilson Grassi (DEMOCRATA)",
    "Edmilson Costa (PCB)",
    "Hertz Dias (PSTU)",
    "Clariana Barao (DC)",
]
CANDIDATES_B = [
    "Lula (PT)",
    "Flavio Bolsonaro (PL)",
    "Ronaldo Caiado (PSD)",
    "Renan Santos (MISSAO)",
    "Zema (NOVO)",
    "Augusto Cury (AVANTE)",
    "Samara (UP)",
    "Rui Costa Pimenta (PCO)",
    "Edmilson Costa (PCB)",
    "Wilson Grassi (DEMOCRATA)",
    "Clariana Barao (DC)",
    "Hertz Dias (PSTU)",
]
NON_VOTE = ["Branco/nulo/nenhum", "Indecisos"]

REJECTION_ROWS = [
    "Flavio Bolsonaro (PL)",
    "Lula (PT)",
    "Pablo Marcal (PRTB)",
    "Zema (NOVO)",
    "Renan Santos (MISSAO)",
    "Ronaldo Caiado (PSD)",
    "Rui Costa Pimenta (PCO)",
    "Samara (UP)",
    "Edmilson Costa (PCB)",
    "Clariana Barao (DC)",
    "Wilson Grassi (DEMOCRATA)",
    "Hertz Dias (PSTU)",
    "Augusto Cury (AVANTE)",
    "Nao rejeita nenhum",
    "Rejeita todos",
    "Nao sabe",
]

SPONTANEOUS_ROWS = [
    "Lula (PT)",
    "Flavio Bolsonaro (PL)",
    "Jair Bolsonaro (PL)",
    "Ronaldo Caiado (PSD)",
    "Renan Santos (MISSAO)",
    "Zema (NOVO)",
    "Pablo Marcal (PRTB)",
    "Outras respostas",
    "Branco/nulo/nenhum",
    "Indecisos",
]

TABLES = {
    "espontanea": {
        "title": "Intencao de voto espontanea",
        "pages": {"bloco1": 29, "bloco2": 29, "bloco3": 30},
        "rows": SPONTANEOUS_ROWS,
        "annex_pages": {"bloco1": 7, "bloco2": 7, "bloco3": 8},
    },
    "estimulada_a": {
        "title": "Intencao de voto estimulada, situacao A (com Marcal)",
        "pages": {"bloco1": 31, "bloco2": 32, "bloco3": 33},
        "rows": CANDIDATES_A + NON_VOTE,
        "annex_pages": {"bloco1": 9, "bloco2": 10, "bloco3": 11},
    },
    "validos_a": {
        "title": "Votos validos, situacao A",
        "pages": {"bloco1": 34, "bloco2": 35, "bloco3": 35},
        "rows": CANDIDATES_A,
        "annex_pages": {"bloco1": 12, "bloco2": 13, "bloco3": 13},
    },
    "estimulada_b": {
        "title": "Intencao de voto estimulada, situacao B (sem Marcal)",
        "pages": {"bloco1": 36, "bloco2": 37, "bloco3": 38},
        "rows": CANDIDATES_B + NON_VOTE,
        "annex_pages": {"bloco1": 14, "bloco2": 15, "bloco3": 16},
    },
    "validos_b": {
        "title": "Votos validos, situacao B",
        "pages": {"bloco1": 39, "bloco2": 40, "bloco3": 40},
        "rows": CANDIDATES_B,
        "annex_pages": {"bloco1": 17, "bloco2": 18, "bloco3": 18},
    },
    "rejeicao": {
        "title": "Rejeicao a candidatos",
        "pages": {"bloco1": 41, "bloco2": 42, "bloco3": 43},
        "rows": REJECTION_ROWS,
        "annex_pages": {"bloco1": 19, "bloco2": 20, "bloco3": 21},
    },
    "turno2_flavio": {
        "title": "Segundo turno, situacao A: Lula x Flavio Bolsonaro",
        "pages": {"bloco1": 44, "bloco2": 44, "bloco3": 44},
        "rows": ["Lula (PT)", "Flavio Bolsonaro (PL)", *NON_VOTE],
        "annex_pages": {"bloco1": 22, "bloco2": 22, "bloco3": 22},
    },
    "turno2_caiado": {
        "title": "Segundo turno, situacao B: Lula x Ronaldo Caiado",
        "pages": {"bloco1": 45, "bloco2": 45, "bloco3": 45},
        "rows": ["Lula (PT)", "Ronaldo Caiado (PSD)", *NON_VOTE],
        "annex_pages": {"bloco1": 23, "bloco2": 23, "bloco3": 23},
    },
    "turno2_zema": {
        "title": "Segundo turno, situacao C: Lula x Zema",
        "pages": {"bloco1": 46, "bloco2": 46, "bloco3": 46},
        "rows": ["Lula (PT)", "Zema (NOVO)", *NON_VOTE],
        "annex_pages": {"bloco1": 24, "bloco2": 24, "bloco3": 24},
    },
    "turno2_renan": {
        "title": "Segundo turno, situacao D: Lula x Renan Santos",
        "pages": {"bloco1": 47, "bloco2": 47, "bloco3": 47},
        "rows": ["Lula (PT)", "Renan Santos (MISSAO)", *NON_VOTE],
        "annex_pages": {"bloco1": 25, "bloco2": 25, "bloco3": 25},
    },
    "definicao": {
        "title": "Grau de definicao do voto",
        "pages": {"bloco1": 48, "bloco2": 48, "bloco3": 48},
        "rows": ["Totalmente decidido", "Pode mudar", "Nao sabe"],
        "annex_pages": {"bloco1": 26, "bloco2": 26, "bloco3": 26},
    },
    "motivacao": {
        "title": "Motivacao do voto",
        "pages": {"bloco1": 49, "bloco2": 49, "bloco3": 49},
        "rows": [
            "Melhores propostas",
            "Evitar outro candidato",
            "Outras respostas",
            "Nao sabe",
        ],
        "annex_pages": {"bloco1": 27, "bloco2": 27, "bloco3": 27},
    },
    "avaliacao": {
        "title": "Avaliacao do governo Lula",
        "pages": {"bloco1": 50, "bloco2": 50, "bloco3": 50},
        "rows": ["Otimo/bom", "Regular", "Ruim/pessimo", "Nao sabe"],
        "annex_pages": {"bloco1": 28, "bloco2": 28, "bloco3": 28},
    },
    "aprovacao": {
        "title": "Aprovacao do trabalho de Lula",
        "pages": {"bloco1": 51, "bloco2": 51, "bloco3": 51},
        "rows": ["Aprova", "Desaprova", "Nao sabe"],
        "annex_pages": {"bloco1": 29, "bloco2": 29, "bloco3": 29},
    },
}


def numeric_runs(document: fitz.Document, page_number: int) -> list[list[int | None]]:
    """Sequencias consecutivas de celulas numericas de uma pagina do anexo."""
    runs: list[list[int | None]] = []
    current: list[int | None] = []
    for raw in document[page_number - 1].get_text().split("\n"):
        token = raw.strip()
        if not token:
            continue
        if NUMBER.match(token):
            current.append(int(token))
        elif token in DASHES:
            current.append(None)
        elif current:
            runs.append(current)
            current = []
    if current:
        runs.append(current)
    return runs


def page_blocks(
    document: fitz.Document, page_number: int
) -> list[list[list[int | None]]]:
    """Agrupa as sequencias de uma pagina em blocos terminados por base ponderada."""
    blocks: list[list[list[int | None]]] = []
    current: list[list[int | None]] = []
    for run in numeric_runs(document, page_number):
        if len(run) not in (len(BLOCK1), len(BLOCK3)):
            continue
        current.append(run)
        present = [value for value in run if value is not None]
        if present and max(present) > 200:
            blocks.append(current)
            current = []
    return blocks


def build(document: fitz.Document) -> dict[str, object]:
    columns = {"bloco1": BLOCK1, "bloco2": BLOCK2, "bloco3": BLOCK3}
    cache: dict[int, list[list[list[int | None]]]] = {}
    tables: dict[str, object] = {}

    for key, spec in TABLES.items():
        table: dict[str, object] = {
            "title": spec["title"],
            "blocks": {},
        }
        used: dict[int, int] = {}
        for block_name in ("bloco1", "bloco2", "bloco3"):
            page = spec["pages"][block_name]
            if page not in cache:
                cache[page] = page_blocks(document, page)
            index = used.get(page, 0)
            used[page] = index + 1
            block = cache[page][index]
            names = columns[block_name]
            if len(block) != len(spec["rows"]) + 1:
                raise RuntimeError(
                    f"{key}/{block_name}: {len(block)} linhas lidas, "
                    f"{len(spec['rows']) + 1} esperadas na pagina {page}"
                )
            for run in block:
                if len(run) != len(names):
                    raise RuntimeError(
                        f"{key}/{block_name}: largura {len(run)} != {len(names)}"
                    )
            values = {
                label: dict(zip(names, run, strict=False))
                for label, run in zip(spec["rows"], block[:-1], strict=False)
            }
            table["blocks"][block_name] = {
                "pdf_page": page,
                "annex_page": spec["annex_pages"][block_name],
                "columns": names,
                "rows": values,
                "base": dict(zip(names, block[-1], strict=False)),
            }
        tables[key] = table
    return tables


def flatten(
    table: dict[str, object],
) -> tuple[dict[str, dict[str, int]], dict[str, int]]:
    """Une os tres blocos em um unico dicionario recorte -> linha -> valor."""
    merged: dict[str, dict[str, int]] = {}
    bases: dict[str, int] = {}
    for block in table["blocks"].values():
        for label, row in block["rows"].items():
            for column, value in row.items():
                merged.setdefault(column, {})[label] = value
        for column, value in block["base"].items():
            bases[column] = value
    return merged, bases


def recompose(
    table: dict[str, object], groups: list[str], row: str
) -> dict[str, float]:
    """Recompoe o total publicado a partir de um cruzamento independente."""
    merged, bases = flatten(table)
    weight = sum(bases[group] for group in groups)
    total = sum((merged[group][row] or 0) * bases[group] for group in groups)
    return {
        "recomposto_pct": round(total / weight, 2),
        "publicado_pct": merged["Total"][row],
        "base_do_cruzamento": weight,
        "base_total": bases["Total"],
        "residuo_de_base": bases["Total"] - weight,
    }


def main() -> None:
    document = fitz.open(REPORT)
    tables = build(document)

    identity = ["Bolsonaristas", "Nao alinhados", "Petistas"]
    region = ["Sudeste", "Sul", "Nordeste", "Centro-Oeste/Norte"]
    proofs = {
        "turno2_flavio_por_identidade_lula": recompose(
            tables["turno2_flavio"], identity, "Lula (PT)"
        ),
        "turno2_flavio_por_identidade_flavio": recompose(
            tables["turno2_flavio"], identity, "Flavio Bolsonaro (PL)"
        ),
        "turno2_flavio_por_regiao_lula": recompose(
            tables["turno2_flavio"], region, "Lula (PT)"
        ),
        "turno2_flavio_por_regiao_flavio": recompose(
            tables["turno2_flavio"], region, "Flavio Bolsonaro (PL)"
        ),
        "estimulada_b_por_identidade_lula": recompose(
            tables["estimulada_b"], identity, "Lula (PT)"
        ),
        "estimulada_b_por_identidade_flavio": recompose(
            tables["estimulada_b"], identity, "Flavio Bolsonaro (PL)"
        ),
        "aprovacao_por_regiao_desaprova": recompose(
            tables["aprovacao"], region, "Desaprova"
        ),
    }

    payload = {
        "fonte": {
            "arquivo": REPORT.name,
            "registro": "BR-04496/2026",
            "anexo": "Relatorio de tabelas cruzadas, 29 paginas, paginas 24 a 51 do PDF",
            "extracao": "texto nativo do PDF, sem digitacao manual",
        },
        "prova_de_leitura": proofs,
        "tabelas": tables,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(f"tabelas extraidas: {len(tables)}")
    for name, proof in proofs.items():
        print(
            f"  {name}: recomposto {proof['recomposto_pct']} "
            f"vs publicado {proof['publicado_pct']} "
            f"(residuo de base {proof['residuo_de_base']})"
        )


if __name__ == "__main__":
    main()
