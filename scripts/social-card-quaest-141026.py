"""Card da íntegra auditada; valores derivados da auditoria corrente."""

import json


def card(root):
    data = json.loads((root / "docs/assets/quaest_14102026_data.json").read_text())
    pub = data["pesquisa"]["publicado"]["2t"]
    income = data["identificacao_renda"]
    gap = f'{income["gap_ajustado_pp"]:.2f}'.replace(".", ",")
    return {
        "slug": "quaest_14102026",
        "eyebrow": "Quaest · 14/10/2026 · íntegra auditada",
        "title": "Voto declarado.",
        "title_em": "Presença sem modelo publicado.",
        "lede": "<b>152 páginas, 23 temas.</b> Transferências, memória do voto, renda, propostas e interesse. Os 9% misturam brancos, nulos e quem não vai votar.",
        "stats": [
            (
                f'{pub["flavio"]} × {pub["lula"]}',
                "Flávio × Lula / total de entrevistados",
            ),
            (
                f"{gap} pp",
                "diferença F−L na sensibilidade condicional",
            ),
            ("23", "temas com análise e páginas originais"),
        ],
        "foot": "Íntegra arquivada · transferências e eleitor provável sob auditoria",
        "accent": "blue",
    }
