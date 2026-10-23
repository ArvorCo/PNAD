"""Tabelas nativas, verificadas por hash e com denominadores preservados."""

import hashlib

import pymupdf
from dossies_2t_2026.extract import GROUPS, ROOT, ROW

PDF = ROOT / "data/originals/datafolha_102026_22_integra/relatorio.pdf"
SHA256 = "c548241d08d526ce1ceecc87e64cd1ba989634130ba165b9660fbab4219321d4"
QUESTIONS = {
    26: ("espontanea", "Intenção espontânea", "Total da amostra"),
    27: ("voto", "Intenção estimulada", "Total da amostra"),
    28: ("validos", "Votos válidos", "Quem declarou uma candidatura"),
    29: ("decisao", "Decisão do voto", "Quem declarou candidatura ou branco/nulo"),
    30: ("potencial_flavio", "Certeza e rejeição de Flávio", "Total da amostra"),
    31: ("potencial_lula", "Certeza e rejeição de Lula", "Total da amostra"),
    32: ("rejeicao", "Rejeição combinada", "Total da amostra"),
    33: ("motivacao", "Motivação do voto", "Quem declarou uma candidatura"),
    34: ("avaliacao", "Avaliação do governo", "Total da amostra"),
    35: ("aprovacao", "Aprovação ao trabalho de Lula", "Total da amostra"),
    36: ("expectativa", "Expectativa de vencedor", "Total da amostra"),
}


def tables():
    if hashlib.sha256(PDF.read_bytes()).hexdigest() != SHA256:
        raise ValueError("Íntegra Datafolha alterada")
    output = {}
    with pymupdf.open(PDF) as doc:
        for page, (key, title, universe) in QUESTIONS.items():
            blocks, rows = [], []
            for label, tokens in ROW.findall(doc[page - 1].get_text(sort=True)):
                values = [int(v) if v.isdigit() else None for v in tokens.split()]
                if label == "Base ponderada":
                    blocks.append((rows, values))
                    rows = []
                else:
                    if label == "É, na sua opinião, o melhor candidato a":
                        label += " presidente"
                    rows.append((label, values))
            if len(blocks) != 3 or rows:
                raise ValueError(f"Página {page}: tabela incompleta")
            segments = {}
            for names, (rows, bases) in zip(GROUPS, blocks, strict=True):
                for i, name in enumerate(names):
                    cell = {
                        "base_ponderada": bases[i],
                        "responses": {label: values[i] for label, values in rows},
                    }
                    if name in segments and segments[name] != cell:
                        raise ValueError(f"Totais divergentes na página {page}")
                    segments[name] = cell
            output[key] = {
                "page": page,
                "annex_page": page - 19,
                "title": title,
                "universe": universe,
                "segments": segments,
                "dash": "Traços preservados como null; zero é percentual arredondado.",
            }
    return output
