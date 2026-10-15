"""Card da leitura preliminar; valores derivados da auditoria corrente."""

import json


def card(root):
    data = json.loads((root / "docs/assets/quaest_14102026_data.json").read_text())
    pub = data["pesquisa"]["publicado"]["2t"]
    delta = data["decomposicao"]["variacoes_total_pp"]
    return {
        "slug": "quaest_14102026",
        "eyebrow": "Quaest · 14/10/2026 · dossiê preliminar",
        "title": "Duas escolhas crescem.",
        "title_em": "A distância permanece.",
        "lede": "<b>O mesmo duelo antes e depois da urna.</b> A não escolha cai, a diferença fica em dois pontos. Por renda, os movimentos são opostos. Sensibilidade PNAD com cotas atuais.",
        "stats": [
            (
                f'{pub["flavio"]} × {pub["lula"]}',
                "Flávio × Lula / total de entrevistados",
            ),
            (
                f'{delta["flavio"]:+d} / {delta["lula"]:+d}',
                "variação de cada candidato desde 03/10",
            ),
            ("10–13/10", "campo domiciliar, incluindo o feriadão"),
        ],
        "foot": "Cruzamentos atuais conferidos · cotas registradas como hipótese de pesos",
        "accent": "blue",
    }
