"""Cards das três páginas do agregador, com números do build corrente."""

import json


def cards(root):
    assets = root / "docs/assets"
    data = json.loads((assets / "reponderacao_simulador.json").read_text())
    history = json.loads((root / "analysis/reponderacao/log.json").read_text())
    central = data["central"]
    projection = data["central_projection"]
    relative = f"+{data['defaults']['presenca_relativa']:.1f}%".replace(".", ",")

    def fmt(number):
        return f"{number:.1f}".replace(".", ",")

    return [
        {
            "slug": "reponderacao_pnad",
            "eyebrow": "Arvor · 2º turno · votos válidos",
            "title": "O voto conta.",
            "title_em": "A presença decide.",
            "lede": "<b>Duas centrais, hipóteses abertas.</b> Compare a média com a projeção por recência e Monte Carlo. Simule presença relativa e brancos/nulos; compartilhe seu cenário.",
            "stats": [
                (
                    fmt(central["flavio"]) + " × " + fmt(central["lula"]),
                    "Média / Flávio × Lula / válidos",
                ),
                (
                    fmt(projection["flavio"]) + " × " + fmt(projection["lula"]),
                    "Projeção / Flávio × Lula / válidos",
                ),
                (relative, "ajuste relativo F / hipótese do 1º turno"),
            ],
            "foot": f"{data['reference']} · central condicional · ajuste relativo F {relative}",
            "accent": "blue",
        },
        {
            "slug": "reponderacao_pnad_1o_turno_2026",
            "eyebrow": "Arvor · arquivo do 1º turno de 2026",
            "title": "A conta de ontem.",
            "title_em": "A urna de hoje.",
            "lede": "<b>As hipóteses contra o resultado oficial.</b> Séries, candidaturas, ondas e erros preservados: como cada pesquisa foi publicada e o que a troca da margem de renda mudou.",
            "stats": [
                ("04/10", "referência fechada"),
                ("100%", "das seções apuradas"),
                ("3", "modos de projeção"),
            ],
            "foot": "arquivo do primeiro turno · sem reescrever o passado",
            "accent": "amber",
        },
        {
            "slug": "reponderacao_pnad_log",
            "eyebrow": "Arvor · diário do agregador",
            "title": "O que mudou.",
            "title_em": "Quando e por quê.",
            "lede": "<b>As datas, as fontes e o caminho de cada alteração.</b> Incorporações, revisões e atualizações documentais preservadas, com links para as fichas dos dois turnos.",
            "stats": [
                (str(len(history["waves"])), "ondas no acervo"),
                (str(len(history["documentary_history"])), "atualizações anteriores"),
                ("2", "turnos documentados"),
            ],
            "foot": "campo, divulgação e incorporação têm datas distintas",
            "accent": "lime",
        },
    ]
