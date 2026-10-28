"""Card do relatório geográfico, derivado da base publicada."""

import json


def card(root):
    path = root / "analysis/analise_realidade_eleicao/dados.json"
    if not path.exists():
        return {
            "slug": "analise_realidade_eleicao",
            "eyebrow": "Geografia eleitoral · 2026",
            "title": "A geografia do voto.",
            "title_em": "E o que pede explicação.",
            "lede": "Renda, desenvolvimento, segurança e uma trilha de auditoria.",
            "stats": [],
            "foot": "Brasil · Arvor Intelligence",
            "accent": "red",
        }
    d = json.loads(path.read_text())
    return {
        "slug": "analise_realidade_eleicao",
        "eyebrow": "Geografia e auditoria · 2º turno de 2026",
        "title": "A geografia do voto.",
        "title_em": "E o que pede explicação.",
        "lede": "Renda, progresso social, violência e mudanças entre os turnos. <b>Do padrão territorial à conferência dos boletins.</b>",
        "stats": [
            (f"{len(d['municipios']):,}".replace(",", "."), "municípios no mapa"),
            (str(len(d["zonas"])), "zonas nas capitais"),
            (str(len(d["cortes"]["10"])), "municípios com Flávio abaixo de 10%"),
        ],
        "foot": "dados, hipóteses e evidência documental em camadas separadas",
        "accent": "red",
    }
