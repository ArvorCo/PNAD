"""Extrai todas as tabelas do anexo Datafolha e matrizes nativas da Nexus."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]
PDFS = {
    "datafolha": ROOT / "data/originals/datafolha_102026_13/relatorio.pdf",
    "nexus": ROOT / "data/originals/nexus_102026_13/relatorio.pdf",
}
HASHES = {
    "datafolha": "9b95078c8f04e961b48719c166a303b354c4366eb59b633642ef0fc0de7aafcb",
    "nexus": "122e3f2052c72c3da04f6bd556cf592f2c341cdda90b462632a6a63dbda1c6a7",
}
GROUPS = [
    [
        "total",
        "homens",
        "mulheres",
        "16–24",
        "25–34",
        "35–44",
        "45–59",
        "60+",
        "fundamental",
        "médio",
        "superior",
    ],
    [
        "total",
        "até 2 SM",
        "2–5 SM",
        ">5 SM",
        "PEA",
        "não PEA",
        "branca",
        "preta",
        "parda",
        "católica",
        "evangélica",
    ],
    [
        "total",
        "Sudeste",
        "Sul",
        "Nordeste",
        "CO/Norte",
        "metropolitana",
        "interior",
        "PT",
        "PL",
        "outro partido",
        "sem partido",
    ],
]
DF_QUESTIONS = {
    25: ("espontanea", "Intenção espontânea", "total da amostra"),
    26: ("voto", "Intenção estimulada", "total da amostra"),
    27: ("validos", "Votos válidos", "quem declarou uma candidatura"),
    28: ("rejeicao_combinada", "Rejeição combinada", "total da amostra"),
    29: ("potencial_flavio", "Potencial e rejeição de Flávio", "total da amostra"),
    30: ("potencial_lula", "Potencial e rejeição de Lula", "total da amostra"),
    31: ("decisao", "Decisão do voto", "quem declarou candidatura ou branco/nulo"),
    32: ("motivacao", "Motivação do voto", "quem declarou uma candidatura"),
    33: ("avaliacao", "Avaliação do governo", "total da amostra"),
    34: ("aprovacao", "Aprovação ao trabalho de Lula", "total da amostra"),
}
ROW = re.compile(
    r"^\s*(.*?)\s{2,}((?:(?:\d+|[–-])\s+){10}(?:\d+|[–-]))\s*$", re.MULTILINE
)


def verified_document(house):
    path = PDFS[house]
    if hashlib.sha256(path.read_bytes()).hexdigest() != HASHES[house]:
        raise ValueError(f"Fonte alterada: {path}")
    return fitz.open(path)


def datafolha():
    tables = {}
    with verified_document("datafolha") as doc:
        for page, (key, title, universe) in DF_QUESTIONS.items():
            text = doc[page - 1].get_text(sort=True)
            blocks, current = [], []
            for label, tokens in ROW.findall(text):
                values = [int(v) if v.isdigit() else None for v in tokens.split()]
                if label == "Base ponderada":
                    blocks.append({"rows": current, "bases": values})
                    current = []
                else:
                    if label == "É, na sua opinião, o melhor candidato a":
                        label += " presidente"
                    current.append({"label": label, "values": values})
            if len(blocks) != 3 or current:
                raise ValueError(f"Página {page}: blocos incompletos")
            segments = {}
            for columns, block in zip(GROUPS, blocks, strict=True):
                for i, name in enumerate(columns):
                    row = {
                        "base_ponderada": block["bases"][i],
                        "responses": {
                            r["label"]: r["values"][i] for r in block["rows"]
                        },
                    }
                    if name in segments and segments[name] != row:
                        raise ValueError(f"Totais divergentes na página {page}")
                    segments[name] = row
            tables[key] = {
                "page": page,
                "annex_page": page - 18,
                "title": title,
                "universe": universe,
                "segments": segments,
                "dash": "Traço preservado como null; não é convertido silenciosamente em zero.",
            }
    return tables


def nexus_matrix(page, expected_columns=None):
    """Linhas das tabelas por perfil, com rótulos e ordem originais."""
    with verified_document("nexus") as doc:
        text = doc[page - 1].get_text(sort=True)
    rows = []
    for line in text.splitlines():
        values = re.findall(r"(\d+)%", line)
        if not values:
            continue
        first = re.search(r"\d+%", line).start()
        label = line[:first].strip()
        if not label or not re.search(r"[a-zA-ZÀ-ÿ]", label):
            continue
        if expected_columns and len(values) != expected_columns:
            raise ValueError(f"Página {page}: linha {label}, {values}")
        rows.append({"label": label, "values": list(map(int, values))})
    return {"page": page, "rows": rows}


def nexus_catalog():
    catalog = []
    with verified_document("nexus") as doc:
        for i, page in enumerate(doc):
            text = page.get_text(sort=True)
            if "Pergunta:" not in text:
                continue
            question = text.split("Pergunta:", 1)[1]
            question = re.sub(r"<\d+>\s*$", "", question).strip()
            catalog.append(
                {"page": i + 1, "question_original": re.sub(r"\s+", " ", question)}
            )
    return catalog
