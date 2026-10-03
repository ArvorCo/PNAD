"""Texto dinâmico do card da predição do Senado; a renderização segue o manifesto único."""

import json


def _num(x):
    return f"{x:.1f}".replace(".", ",")


def card(root):
    path = root / "docs/assets/predicao_senado.json"
    stats = [("81", "assentos no Senado de 2027")]
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        por_campo = data["senado_2027"].get("por_campo", {})
        grupos = (
            ("direita e centro-direita", ("direita", "centro-direita")),
            ("centro", ("centro",)),
            ("esquerda e centro-esquerda", ("centro-esquerda", "esquerda")),
        )
        stats = [
            (
                _num(sum(por_campo.get(k, {}).get("esperado", 0) for k in ks)),
                f"assentos esperados: {nome}",
            )
            for nome, ks in grupos
        ]
    return {
        "slug": "predicao_senado",
        "eyebrow": "Predição experimental · Senado de 2027",
        "title": "Quem senta no",
        "title_em": "Senado em 2027.",
        "lede": "Dois nomes por estado, hemiciclo de 81 assentos e a <b>probabilidade de eleição</b> de cada candidatura, com a fonte de cada pesquisa.",
        "stats": stats,
        "foot": "predição condicional a pesquisas registradas · incerteza explícita",
        "accent": "blue",
    }
