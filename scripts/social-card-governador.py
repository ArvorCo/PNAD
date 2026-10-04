"""Texto dinâmico do card da predição de governador; a renderização segue o manifesto único."""

import json


def _num(x):
    return f"{x:.1f}".replace(".", ",")


def card(root):
    path = root / "docs/assets/predicao_governador.json"
    stats = [("27", "estados")]
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        n = data["nacional"]
        dec = n.get("decididos_1t") or {}
        seg = n.get("segundo_turno") or {}
        apertadas = len((n.get("por_classe") or {}).get("apertada") or [])
        stats = [
            (_num(dec.get("esperado", 0)), "estados decididos no 1º turno (esperado)"),
            (_num(seg.get("esperado", 0)), "estados com 2º turno em 25/10"),
            (str(apertadas), "corridas apertadas: favorita com menos de 70%"),
        ]
    return {
        "slug": "predicao_governador",
        "eyebrow": "Predição experimental · Governadores de 2026",
        "title": "Quem governa",
        "title_em": "os 27 estados.",
        "lede": "Chance de eleição por estado, decisão no 1º turno ou 2º turno, e os <b>pares de 2º turno com o placar medido</b> pelos institutos, com a fonte de cada pesquisa.",
        "stats": stats,
        "foot": "predição condicional a pesquisas registradas · incerteza explícita",
        "accent": "blue",
    }
