"""Cards das três páginas do agregador, com números do build corrente."""

import json


def cards(root):
    assets = root / "docs/assets"
    data = json.loads((assets / "reponderacao_simulador.json").read_text())
    history = json.loads((root / "analysis/reponderacao/log.json").read_text())
    central = data["central"]

    def fmt(number):
        return f"{number:.1f}".replace(".", ",")

    return [
        {
            "slug": "reponderacao_pnad",
            "eyebrow": "Arvor · 2º turno · votos válidos",
            "title": "O voto conta.",
            "title_em": "A presença decide.",
            "lede": "<b>A central da casa, com hipóteses abertas.</b> Simule presença relativa, abstenção, brancos/nulos e indecisos. Compartilhe o link ou a imagem do seu cenário.",
            "stats": [
                (fmt(central["flavio"]) + "%", "Flávio / válidos"),
                (fmt(central["lula"]) + "%", "Lula / válidos"),
                (str(len(data["polls"])), "casas com campo após o 1º turno"),
            ],
            "foot": f"{data['reference']} · central condicional · presença relativa F +5%",
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
