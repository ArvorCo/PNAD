"""Seções sem votos: os dois lados na mesma escala, por UF e tipo de local."""

from apuracao_2026.pagina_comum import NOME_UF, inteiro
from apuracao_2026.pagina_fig_base import (
    FLAVIO,
    GRADE,
    INK,
    LULA,
    MUTED,
    Tips,
    area,
    escala,
    ficha,
    figura_html,
    hit,
    larga_estreita,
    ln,
    r,
    svg_abre,
    t,
)

SERIES = [
    ("zero_direita_2022_2t", "Bolsonaro 2022", "#6586b2"),
    ("zero_direita_2026_2t", "Flávio 2026", FLAVIO),
    ("zero_lula_2022_2t", "Lula 2022", "#c47769"),
    ("zero_lula_2026_2t", "Lula 2026", LULA),
]


def _svg(z, tips, larga):
    w = 1100 if larga else 380
    x0, x1 = (300, 1025) if larga else (55, 335)
    f = 13 if larga else 12
    out = []
    y = 28
    out.append(
        t(8, y, "Seções sem voto em cada candidato · 2º turno", 15, INK, weight="700")
    )
    y += 28
    for j, (_, nome, cor) in enumerate(SERIES):
        xx = 8 + (j if larga else j % 2) * 180
        yy = y + (0 if larga else j // 2) * 24
        out += [r(xx, yy - 10, 10, 10, cor), t(xx + 17, yy, nome, f, INK)]
    y += 32 if larga else 56
    rows = sorted(
        [u for u in z["por_uf"] if any(u[k] for k, _, _ in SERIES)],
        key=lambda u: (-u["zero_direita_2026_2t"], u["uf"]),
    )
    maximo = max([1, *[u[k] for u in rows for k, _, _ in SERIES]])
    fx = escala(0, maximo, x0, x1)
    for u in rows:
        nome = NOME_UF.get(u["uf"], u["uf"])
        out.append(t(x0 - 10, y + 28, nome if larga else u["uf"], f, INK, "end"))
        partes = []
        campos = []
        for j, (k, candidato, cor) in enumerate(SERIES):
            v, yy = u[k], y + j * 14
            partes += [
                r(x0, yy, fx(v) - x0, 9, cor),
                t(fx(v) + 5, yy + 9, inteiro(v), f, cor, mono=True),
            ]
            ano = 2022 if "2022" in k else 2026
            campos.append(
                (candidato, f"{inteiro(v)} de {inteiro(u[f'secoes_{ano}_2t'])} seções")
            )
        kk = tips.add(ficha(nome, "Seções com zero voto no candidato", campos))
        out.append(hit("".join(partes) + area(0, y - 2, w, 58), kk))
        y += 66
    out.append(ln(x0, y - 4, x1, y - 4, GRADE, 1))
    out.append(
        t(
            x1,
            y + 14,
            "número de seções; escala comum aos dois candidatos",
            f,
            MUTED,
            "end",
        )
    )
    y += 60
    out.append(
        t(8, y, "Tipo de local · 2026, ambos os candidatos", 15, INK, weight="700")
    )
    y += 30
    tipos = [
        {p["tipo"]: p for p in z["tipo_local"][f"2026_2t_{lado}"]}
        for lado in ("direita", "lula")
    ]
    mx = max([1, *[p["secoes"] for ts in tipos for p in ts.values()]])
    fx = escala(0, mx, x0 if larga else 8, x1)
    for tipo, rec in tipos[0].items():
        if larga:
            out.append(t(x0 - 10, y + 17, rec["nome"], f, INK, "end"))
        else:
            out.append(t(8, y + 12, rec["nome"], f, INK))
            y += 22
        partes = []
        campos = []
        for j, (ts, nome, cor) in enumerate(
            zip(tipos, ("Flávio", "Lula"), (FLAVIO, LULA), strict=True)
        ):
            v = ts[tipo]["secoes"]
            yy = y + j * 16
            partes += [
                r(fx(0), yy, fx(v) - fx(0), 11, cor),
                t(fx(v) + 5, yy + 10, inteiro(v), f, cor, mono=True),
            ]
            campos.append((f"Sem voto em {nome}", inteiro(v)))
        kk = tips.add(ficha(rec["nome"], "2026, tipo pelo nome do prédio", campos))
        out.append(hit("".join(partes) + area(0, y - 2, w, 38), kk))
        y += 44
    return (
        svg_abre(
            w,
            y + 10,
            "Seções sem votos nos dois candidatos",
            "Contagens por UF em 2022 e 2026 e por tipo de local em 2026, em escalas compartilhadas.",
        )
        + "".join(out)
        + "</svg>"
    )


def fig_zeros(z):
    tips = Tips()
    corpo = larga_estreita(_svg(z, tips, True), _svg(z, tips, False))
    return figura_html(
        "an_zeros",
        corpo,
        "Brasil sem exterior. Por UF: zero voto em Bolsonaro/Flávio e em Lula nos segundos turnos de 2022 e 2026. "
        "Só UFs com ao menos um caso em qualquer lado/ano. Por tipo do local: 2026, classificação pelo nome do prédio; "
        "sem descrição suficiente fica em outro local. Os universos de seções de cada ano estão nas fichas e na tabela de recortes. "
        "Seções sem voto não são automaticamente irregulares. Fonte: zeros.json.",
        tips,
        modo="full",
    )
