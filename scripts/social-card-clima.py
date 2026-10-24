"""Card do relatório de clima, bateria e abstenção no 1º turno; números lidos do JSON."""

import json


def _n(x):
    return f"{round(x):,}".replace(",", ".")


def _d(x, casas=2):
    return f"{x:.{casas}f}".replace(".", ",")


def card(root):
    d = json.loads(
        (root / "analysis/clima_1t_2026/clima.json").read_text(encoding="utf-8")
    )
    faixas = d["bateria_x_chuva"]["por_exposicao"]["chuva_votacao"]["faixas"]
    forte = next(f for f in faixas["bateria_votacao"] if f["faixa"] == "forte")
    b = d["abstencao_x_chuva"]["binario"]["chuva_votacao"]
    mun = next(iter(b["dentro_do_municipio"]["grupos"].values()))["abst_vs_ref_pp"]
    r = forte["razao_vs_ref"]
    return {
        "slug": "clima_abstencao_1t_2026",
        "eyebrow": "Segundo turno · 25/10/2026 · clima e abstenção",
        "title": "Chuva no domingo.",
        "title_em": "Mapa, presença e limites.",
        "lede": (
            f"<b>{_n(d['cobertura']['urnas_amostra'])} urnas cruzadas com a chuva de 4 de outubro.</b> "
            "Previsão do tempo e mapa da abstenção. O estudo não identificou um aumento de faltas por chuva dentro do município."
        ),
        "stats": [
            (
                f"{_d(r['valor'])}×",
                f"bateria na chuva forte, IC 95% de {_d(r['ic95'][0])} a {_d(r['ic95'][1])}",
            ),
            (
                f"+{_d(mun['valor'])} pp",
                f"abstenção dentro do município, IC 95% de {_d(mun['ic95'][0])} a {_d(mun['ic95'][1])}",
            ),
            (
                "27 UFs",
                "abstenção observada no 1º turno, sem exterior",
            ),
        ],
        "foot": "ERA5 · Open-Meteo, boletins e logs do TSE · correlação não é causa",
        "accent": "blue",
    }
