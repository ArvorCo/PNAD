"""Texto dinâmico do card do dossiê da apuração do 1º turno de 2026."""

import json


def _num(x, casas=2):
    return f"{x:,.{casas}f}".replace(",", " ").replace(".", ",").replace(" ", ".")


def card(root):
    dados = root / "analysis/apuracao_2026/dados"
    stats = [
        ("100%", "das seções apuradas"),
        ("3", "paradas do arquivo nacional"),
        ("15", "capítulos"),
    ]
    lede = "O resultado, a noite minuto a minuto e a falha do TSE, com três camadas de fonte."
    pres = dados / "presidente.json"
    if pres.exists():
        n = json.loads(pres.read_text(encoding="utf-8"))["nacional"]
        stats = [
            (
                f"{_num(n['pct']['flavio'])} × {_num(n['pct']['lula'])}",
                "Flávio × Lula, % dos válidos",
            ),
            (
                f"{_num(n['diferenca_votos'] / 1e6)} mi",
                "votos de diferença, 100% das seções",
            ),
        ]
        lt = dados / "linha_do_tempo.json"
        if lt.exists():
            lacunas = (
                json.loads(lt.read_text(encoding="utf-8"))
                .get("pausa_geral", {})
                .get("lacunas", [])
            )
            if lacunas:
                stats.append(
                    (
                        f"{round(lacunas[0]['minutos'])} min",
                        "sem nenhum arquivo de resultado gerado",
                    )
                )
        lede = (
            "O resultado com 100% das seções, a noite minuto a minuto e a falha do TSE. "
            "<b>O que o banco prova, o que o tribunal disse e o que falta explicar.</b>"
        )
    return {
        "slug": "apuracao_1o_turno_2026",
        "eyebrow": "Dossiê da apuração · 1º turno de 2026",
        "title": "Flávio na frente.",
        "title_em": "E o TSE parado no pico.",
        "lede": lede,
        "stats": stats,
        "foot": "dados do TSE lidos e guardados versão a versão · fonte de cada número na página",
        "accent": "blue",
    }
