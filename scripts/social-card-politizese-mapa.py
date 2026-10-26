"""Card social do mapa do Brasil do Politize-se (todos os locais de votação).

Os números saem de docs/assets/politize_se_mapa/indice.json; sem o arquivo, o card cai
num texto neutro, sem número.
"""

import json


def _int(x):
    return f"{int(x):,}".replace(",", ".")


def card(root):
    caminho = root / "docs/assets/politize_se_mapa/indice.json"
    stats = [
        ("7", "camadas de cor: 2º turno, mudança, comparecimento e sinais"),
        ("1", "toque leva à seção no Politize-se"),
    ]
    if caminho.exists():
        idx = json.loads(caminho.read_text(encoding="utf-8"))
        r = idx["resumo"]
        stats = [
            (_int(r["locais"]), "locais de votação, do Oiapoque ao exterior"),
            (
                str(len(idx["camadas"])),
                "camadas: 2º turno, mudança, comparecimento, sinais",
            ),
            (_int(r["secoes"]), "seções, cada uma aberta no Politize-se"),
        ]
    return {
        "slug": "politizese_mapa",
        "eyebrow": "Politize-se · o mapa do Brasil",
        "title": "Todos os locais de votação",
        "title_em": "num mapa só.",
        "lede": (
            "Cada ponto é um prédio de votação, colorido pelo resultado do 2º turno, pela "
            "mudança contra o 1º, pelo comparecimento ou pelos sinais. Toque e veja as "
            "seções lado a lado. <b>Sinal pede explicação, não prova irregularidade.</b>"
        ),
        "stats": stats,
        "foot": "boletins de urna por seção (TSE) · brasil.arvor.co/politizese_mapa.html",
        "accent": "blue",
    }
