"""Card social do aplicativo Politize-se (1º × 2º turno por seção).

Os números saem de docs/assets/politize_se/dados/indice.json; sem o arquivo, o card
cai num texto neutro, sem número.
"""

import json


def _int(x):
    return f"{int(x):,}".replace(",", ".")


def _ler(root):
    caminho = root / "docs/assets/politize_se/dados/indice.json"
    if not caminho.exists():
        return None
    return json.loads(caminho.read_text(encoding="utf-8"))


def card(root):
    idx = _ler(root)
    stats = [
        ("2", "turnos lado a lado, seção por seção"),
        ("6", "sinais com a explicação provável ao lado"),
    ]
    if idx:
        nac = idx["cobertura"]["nacional"]
        n_locais = sum(x[7] or 0 for x in idx["municipios"]["linhas"])
        stats = [
            (_int(nac["secoes"]), "seções, cada uma com o 1º e o 2º turno"),
            (_int(n_locais), "locais de votação comparados ao município"),
            ("6", "sinais que pedem explicação, com a explicação provável"),
        ]
    return {
        "slug": "politizese",
        "eyebrow": "Politize-se · eleições de 2026",
        "title": "O que aconteceu",
        "title_em": "na sua seção.",
        "lede": (
            "Digite UF, zona e seção e veja o 1º e o 2º turno lado a lado: votos, "
            "comparecimento, biometria, horário do último voto, a urna e os sinais. "
            "<b>Atipicidade pede explicação, não prova irregularidade. O voto é secreto.</b>"
        ),
        "stats": stats,
        "foot": "boletins de urna por seção (TSE) · leitura agregada · brasil.arvor.co/politizese.html",
        "accent": "blue",
    }
