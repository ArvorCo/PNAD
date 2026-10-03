"""Texto dinâmico do card preditivo; a renderização segue o manifesto único."""

import json


def card(root):
    path = root / "docs/assets/predicao_2026_1T_presidente.json"
    stats = [("27 UFs", "mais o eleitorado no exterior")]
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        p = data["central"]["brasil"]["percentuais"]
        stats = [
            (f"{p[k]:.1f}%".replace(".", ","), label)
            for k, label in (
                ("lula", "Lula, cenário central"),
                ("flavio", "Flávio, cenário central"),
            )
        ]
        stats.append(("27 + ZZ", "UFs e exterior · incerteza explícita"))
    return {
        "slug": "predicao_2026_1T_presidente",
        "eyebrow": "Previsão experimental · presidencial de 2026",
        "title": "Da intenção de voto",
        "title_em": "à urna.",
        "lede": "Pesquisas estaduais e nacionais, PNAD e comparecimento do TSE. Um modelo territorial com <b>simulador de voto útil e abstenção</b>.",
        "stats": stats,
        "foot": "cenário central condicional · probabilidades não calibradas historicamente",
        "accent": "lime",
    }
