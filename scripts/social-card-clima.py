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
    alto = d["previsao_25_10"]["pais"]["eleitores"]["alto"]
    r = forte["razao_vs_ref"]
    return {
        "slug": "clima_abstencao_1t_2026",
        "eyebrow": "Relatório · clima e urna · 1º turno de 2026",
        "title": "Chuva derruba a urna para a bateria.",
        "title_em": "Não derruba o eleitor.",
        "lede": (
            f"<b>{_n(d['cobertura']['urnas_amostra'])} urnas cruzadas com a chuva de 4 de outubro.</b> "
            "A bateria sobe onde choveu forte; a abstenção, dentro do município, não."
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
                f"{_d(alto / 1e6, 1)} mi",
                "eleitores em risco alto de chuva para 25/10",
            ),
        ],
        "foot": "ERA5 · Open-Meteo, boletins e logs do TSE · correlação não é causa",
        "accent": "blue",
    }
