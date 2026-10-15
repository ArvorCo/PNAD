"""Card social do mapa de fiscais em tela cheia (docs/fiscais_mapa.html).

Os números saem de docs/assets/fiscais_mapa/dados.json; sem o arquivo, o card cai num
texto neutro, sem número.
"""

import json
from collections import Counter


def _int(x):
    return f"{x:,}".replace(",", ".")


def card(root):
    caminho = root / "docs/assets/fiscais_mapa/dados.json"
    stats = [("CEP", "zona ou município: o mapa centra onde você está")]
    if caminho.exists():
        d = json.loads(caminho.read_text(encoding="utf-8"))
        i = d["colunas"].index("nivel")
        n = Counter(ln[i] for ln in d["linhas"])
        stats = [
            (
                _int(len(d["linhas"])),
                "seções sinalizadas no 1º turno, no mapa e em lista",
            ),
            (_int(n["alta"] + n["media"]), "em prioridade alta ou média"),
            ("1 a 50 km", "de raio em linha reta, com exportação em CSV"),
        ]
    return {
        "slug": "fiscais_mapa",
        "eyebrow": "Mapa de fiscais · 2º turno, 25 de outubro",
        "title": "Onde colocar fiscal",
        "title_em": "perto de você.",
        "lede": (
            "Busque por CEP, zona eleitoral ou município e veja as seções sinalizadas pelo "
            "capítulo 13 do dossiê da apuração, com a ficha de cada local e o que conferir. "
            "<b>Atipicidade não é irregularidade: é prioridade de fiscalização.</b>"
        ),
        "stats": stats,
        "foot": "boletins de urna por seção (TSE) · capítulo 13 do dossiê da apuração · seja fiscal em fiscaisdopl.com.br",
        "accent": "amber",
    }
