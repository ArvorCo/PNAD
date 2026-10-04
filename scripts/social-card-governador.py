"""Texto dinâmico do card da predição de governador; a renderização segue o manifesto único."""

import json


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
            (
                f"{dec.get('esperado', 0):.0f}",
                "estados devem decidir o governo já no 1º turno",
            ),
            (f"{seg.get('esperado', 0):.0f}", "estados devem ir ao 2º turno, em 25/10"),
            (str(apertadas), "estados em que ninguém sabe quem ganha"),
        ]
    return {
        "slug": "predicao_governador",
        "eyebrow": "Predição experimental · Governadores de 2026",
        "title": "Quem governa",
        "title_em": "os 27 estados.",
        "lede": "Quem deve ganhar em cada estado, se a eleição acaba amanhã ou vai ao 2º turno, e <b>os placares de 2º turno medidos</b> pelos institutos. Uma frase por estado, em português corrente.",
        "stats": stats,
        "foot": "predição condicional a pesquisas registradas · incerteza explícita",
        "accent": "blue",
    }
