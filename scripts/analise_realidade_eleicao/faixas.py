"""Partição municipal exata, sem lacunas, sobreposição ou arredondamento."""

LIMITES = (0, 25, 50, 75, 100, 125, 150, 200)  # Percentuais multiplicados por 2.
ROTULOS = (
    "Menos de 12,5%",
    "12,5 a <25%",
    "25 a <37,5%",
    "37,5 a <50%",
    "50 a <62,5%",
    "62,5 a <75%",
    "75 a 100%",
)


def pertence(m, indice):
    if not m["completo"] or m["validos"] <= 0:
        return False
    voto = 200 * m["flavio"]
    inferior = LIMITES[indice] * m["validos"]
    superior = LIMITES[indice + 1] * m["validos"]
    return inferior <= voto and (
        voto <= superior if indice == len(ROTULOS) - 1 else voto < superior
    )


def faixas(rows):
    return [
        {
            "id": str(i),
            "rotulo": rotulo,
            "min_pct": LIMITES[i] / 2,
            "max_pct": LIMITES[i + 1] / 2,
            "inclui_maximo": i == len(ROTULOS) - 1,
            "municipios": [m["ibge"] for m in rows if pertence(m, i)],
        }
        for i, rotulo in enumerate(ROTULOS)
    ]
