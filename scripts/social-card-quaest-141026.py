"""Card da leitura preliminar; valores derivados da auditoria corrente."""

import json


def card(root):
    data = json.loads((root / "docs/assets/quaest_14102026_data.json").read_text())
    pub = data["pesquisa"]["publicado"]["2t"]
    income = data["identificacao_renda"]
    gap = f'{income["gap_ajustado_pp"]:.2f}'.replace(".", ",")
    return {
        "slug": "quaest_14102026",
        "eyebrow": "Quaest · 14/10/2026 · dossiê preliminar",
        "title": "Dois pontos no placar.",
        "title_em": "Menos de um sob a PNAD.",
        "lede": "<b>Voto, renda e segmentos em gráficos.</b> Série de 12 ondas e explorador de cinco perguntas. A sensibilidade PNAD usa as cotas planejadas como hipótese de pesos finais.",
        "stats": [
            (
                f'{pub["flavio"]} × {pub["lula"]}',
                "Flávio × Lula / total de entrevistados",
            ),
            (
                f"{gap} pp",
                "diferença F−L na sensibilidade condicional",
            ),
            ("130", "recortes em cinco perguntas do painel G1"),
        ],
        "foot": "Cruzamentos atuais conferidos · cotas registradas como hipótese de pesos",
        "accent": "blue",
    }
