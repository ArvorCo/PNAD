"""Card social do aplicativo Politize sua vizinhança.

Os números saem de docs/assets/politize/dados/indice.json; sem o arquivo, o card
cai num texto neutro, sem número.
"""

import json


def _num(x, casas=1):
    return f"{x:,.{casas}f}".replace(",", " ").replace(".", ",").replace(" ", ".")


def _ler(root):
    caminho = root / "docs/assets/politize/dados/indice.json"
    if not caminho.exists():
        return None
    return json.loads(caminho.read_text(encoding="utf-8"))


def card(root):
    idx = _ler(root)
    stats = [("CEP", "ou bairro: o boletim do seu local de votação")]
    lede = (
        "Digite UF, zona e seção do título de eleitor e receba o boletim da sua "
        "vizinhança: quanto voto Flávio e Lula tiveram no 1º turno, com quem "
        "conversar e sobre o quê. "
        "<b>Leitura agregada por seção, do TSE. O voto é secreto.</b>"
    )
    if idx:
        n_locais = sum(uf["n_locais"] for uf in idx["ufs"])
        nac = idx["nacional"]
        stats = [
            (
                f"{_num(n_locais / 1000, 0)} mil",
                "locais de votação com boletim próprio",
            ),
            (f"{_num(nac['abst_a'])}%", "do eleitorado ficou em casa no 1º turno"),
            (
                f"{_num(nac['terceira_v'])}%",
                "dos válidos foram para a terceira via",
            ),
        ]
    return {
        "slug": "politizesuavizinhanca",
        "eyebrow": "Politize sua vizinhança · 2º turno de 2026",
        "title": "Onde ainda dá para conversar",
        "title_em": "na sua rua.",
        "lede": lede,
        "stats": stats,
        "foot": "boletins de urna por seção (TSE) · perfil do eleitorado · PNAD 2025 · não é previsão",
        "accent": "lime",
    }
