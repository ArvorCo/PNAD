"""Figura do bloco "O registro digital do voto": nulos por origem nas seis UFs.

``logs_rdv_nulos``: para cada UF, duas barras de 100% (nulos de governador e nulos de
presidente), com a parte que é o número do outro cargo digitado no campo errado.
Fonte: ``logs.json`` (chave ``rdv``).
"""

from __future__ import annotations

from apuracao_2026.pagina_comum import CINZA, FLAVIO, INK, LULA, MUTED, inteiro, num
from apuracao_2026.pagina_fig_base import (
    Tips,
    area,
    escala,
    ficha,
    figura_html,
    hit,
    legenda_html,
    ln,
    r,
    svg_abre,
    t,
)

COR_13 = LULA
COR_22 = FLAVIO
COR_GOV = "#0c7a72"


def fig_rdv_nulos(R: dict) -> str:
    ufs = R["ufs"]
    w, esq = 1000, 250
    topo, passo, alt = 30, 76, 24
    h = topo + passo * len(ufs) + 30
    x = escala(0, 100, esq, w - 70)
    out = [
        svg_abre(
            w,
            h,
            "Nulos de governador e de presidente por origem, seis UFs",
            "Para cada UF, uma barra dos nulos de governador (parte com 13, parte com 22, resto) e uma dos "
            "nulos de presidente (parte com número de candidato a governador, resto), em porcentagem.",
        )
    ]
    tips = Tips()
    for i, u in enumerate(ufs):
        y = topo + i * passo
        ng = u["nulos_governador"] or 1
        a13, a22 = 100 * u["governador_com_13"] / ng, 100 * u["governador_com_22"] / ng
        pg = u["presidente_com_governador_pct"] or 0
        comp = (
            f" · {', '.join(u['numero_compartilhado'])} é válido nos dois"
            if u["numero_compartilhado"]
            else ""
        )
        partes = [
            t(esq - 12, y + 18, f"{u['uf']} · nulos de governador", 13, INK, "end"),
            r(esq, y + 4, x(a13) - esq, alt, COR_13),
            r(x(a13), y + 4, x(a13 + a22) - x(a13), alt, COR_22),
            r(x(a13 + a22), y + 4, x(100) - x(a13 + a22), alt, CINZA),
            t(x(100) + 8, y + 20, f"{num(a13 + a22, 1)}%", 13, INK, mono=True),
            t(
                esq - 12,
                y + 18 + alt + 8,
                f"nulos de presidente{comp}",
                12,
                MUTED,
                "end",
            ),
            r(esq, y + 8 + alt, x(pg) - esq, alt - 6, COR_GOV),
            r(x(pg), y + 8 + alt, x(100) - x(pg), alt - 6, CINZA),
            t(x(100) + 8, y + 22 + alt, f"{num(pg, 1)}%", 13, INK, mono=True),
        ]
        k = tips.add(
            ficha(
                u["uf"],
                f"{inteiro(u['secoes'])} seções",
                [
                    ("nulos de governador", inteiro(u["nulos_governador"])),
                    ("13 no campo do governador", inteiro(u["governador_com_13"])),
                    ("22 no campo do governador", inteiro(u["governador_com_22"])),
                    ("nulos de presidente", inteiro(u["nulos_presidente"])),
                    (
                        "número de governador no presidente",
                        inteiro(u["presidente_com_governador"]),
                    ),
                ],
                (
                    "Piso onde um candidato a governador tem o número de um finalista."
                    if u["numero_compartilhado"]
                    else ""
                ),
            )
        )
        out.append(hit("".join(partes) + area(0, y, w, passo), k, foco=True))
    out.append(ln(esq, topo, esq, h - 20, MUTED, 1))
    out.append("</svg>")
    leg = legenda_html(
        [
            ("13 digitado no governador", COR_13),
            ("22 digitado no governador", COR_22),
            ("número de candidato a governador digitado no presidente", COR_GOV),
            ("outros nulos", CINZA),
        ]
    )
    s = R["seis_ufs"]
    legenda = (
        f"Parcela dos nulos de cada cargo que é o número do outro cargo. Nas seis UFs, "
        f"{num(s['governador_com_numero_de_presidente_pct'], 1)}% dos nulos de governador e "
        f"{num(s['presidente_com_numero_de_governador_pct'], 1)}% dos de presidente. Fonte: rdv.json "
        "(troca_de_campo), via logs.json."
    )
    return figura_html(
        "logs_rdv_nulos", "".join(out), legenda, tips, minw=760, apos=leg
    )
