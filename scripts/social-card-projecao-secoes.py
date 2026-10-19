"""Card da projeção territorial, sempre lido do payload corrente."""

import json


def card(root):
    data = json.loads((root / "docs/assets/projecao_secoes_2t_2026.json").read_text())
    pct = data["nacional"]["combinado"]["flavio_validos"]
    return {
        "slug": "projecao_secoes_2t_2026",
        "eyebrow": "Laboratório eleitoral · segundo turno · 19/10/2026",
        "title": "A urna encontra",
        "title_em": "as pesquisas.",
        "lede": "Projeção por seção com apuração, histórico e pesquisas. <b>A complexidade precisa vencer o teste temporal.</b>",
        "stats": [
            (f"{pct:.2f}%".replace(".", ","), "Flávio · combinação experimental"),
            (f"{100-pct:.2f}%".replace(".", ","), "Lula · votos válidos"),
            ("6", "métodos comparados em 2018 → 2022"),
        ],
        "foot": "Brasil sem exterior · hipóteses explícitas · sem probabilidade de vitória validada",
        "accent": "lime",
        "logo": True,
    }
