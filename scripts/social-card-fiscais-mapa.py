"""Card social do mapa de fiscais em tela cheia (docs/fiscais_mapa.html).

Os números saem de docs/assets/fiscais_mapa/dados.json; sem o arquivo, o card cai num
texto neutro, sem número.
"""

import json


def _int(x):
    return f"{x:,}".replace(",", ".")


def card(root):
    caminho = root / "docs/assets/fiscais_mapa/dados.json"
    stats = [("CEP", "zona ou município: o mapa centra onde você está")]
    if caminho.exists():
        d = json.loads(caminho.read_text(encoding="utf-8"))
        atencao = d["resumo"].get("atencao", {})
        fortes = int(atencao.get("3", 0)) + int(atencao.get("2", 0))
        stats = [
            (
                _int(d["resumo"].get("secoes_originais", len(d["secoes"]))),
                "seções pelos critérios históricos do boletim",
            ),
            (
                _int(fortes),
                "seções com sinais combinados ou arquivo a conferir no log",
            ),
            (
                "Resultado por seção",
                "votaram, Flávio × Lula e o número da seção no mapa",
            ),
        ]
    return {
        "slug": "fiscais_mapa",
        "eyebrow": "Mapa de fiscais · 2º turno, 25 de outubro",
        "title": "Mapa de fiscais.",
        "title_em": "Onde vale a pena estar.",
        "lede": (
            "Prédio por prédio: critérios do boletim, sinais do log da urna em cinco "
            "famílias e o resultado de cada seção. Mapa, lista e CSV. "
            "<b>Atipicidade não é irregularidade.</b>"
        ),
        "stats": stats,
        "foot": "boletins e logs oficiais (TSE) · critérios históricos preservados · brasil.arvor.co",
        "accent": "amber",
    }
