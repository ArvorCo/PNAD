"""Efeitos complementares entre dois finalistas, com intervalos espelhados."""

from __future__ import annotations

from textwrap import wrap

from apuracao_2026.pagina_comum import inteiro
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
    legenda_html,
    ln,
    pp,
    svg_abre,
    t,
    ticks,
)


def espelhar(valor, intervalo=None):
    """Em percentuais entre dois, a diferença troca de sinal e os extremos de ordem."""
    return -valor, None if intervalo is None else (-intervalo[1], -intervalo[0])


def efeitos(ident, itens, titulo, legenda, intervalo_rotulo="IC de 95%"):
    """Cada item tem nome, valor de Flávio, intervalo opcional, n e ficha extra."""
    tips = Tips()
    w, esq, fim, topo, passo = 1100, 440, 935, 75, 72
    h = topo + passo * len(itens) + 55
    limites = [abs(i["valor"]) for i in itens]
    limites += [abs(v) for i in itens for v in (i.get("intervalo") or [])]
    lim = max([0.1, *limites]) * 1.15
    x = escala(-lim, lim, esq, fim)
    out = [
        svg_abre(
            w,
            h,
            titulo,
            "Para cada grupo, estimativas de Flávio em azul e Lula em vermelho; os efeitos e seus intervalos são complementares, não dois testes independentes.",
        )
    ]
    for v in ticks(-lim, lim, 5):
        out += [
            ln(x(v), topo - 20, x(v), h - 45, GRADE, 1),
            t(
                x(v),
                h - 24,
                pp(v, 2).removesuffix(" pp"),
                11.5,
                MUTED,
                "middle",
                mono=True,
            ),
        ]
    out += [
        ln(x(0), topo - 20, x(0), h - 45, INK, 1.3),
        t(esq, 25, "← menor participação", 12, MUTED),
        t(fim, 25, "maior participação →", 12, MUTED, "end"),
        t(960, 25, "estimativa, pp", 12, MUTED),
    ]
    for idx, item in enumerate(itens):
        cy = topo + idx * passo
        label = item["nome"] + (
            f" · n = {inteiro(item['n'])}" if item.get("n") is not None else ""
        )
        for j, linha in enumerate(wrap(label, width=54)):
            out.append(t(esq - 22, cy - 6 + 15 * j, linha, 12.5, INK, "end"))
        f, ic = item["valor"], item.get("intervalo")
        for candidato, cor, valor, intervalo, dy in (
            ("Flávio", FLAVIO, f, ic, -11),
            ("Lula", LULA, *espelhar(f, ic), 11),
        ):
            y = cy + dy
            partes = []
            campos = [("Candidato", candidato), ("Estimativa", pp(valor, 3))]
            if intervalo is not None:
                lo, hi = intervalo
                partes += [
                    ln(x(lo), y, x(hi), y, cor, 2),
                    ln(x(lo), y - 4, x(lo), y + 4, cor, 1.5),
                    ln(x(hi), y - 4, x(hi), y + 4, cor, 1.5),
                ]
                campos.append((intervalo_rotulo, f"{pp(lo,3)} a {pp(hi,3)}"))
            bruto = item.get("bruto")
            if bruto is not None:
                campos.append(
                    (
                        "Contra vizinhas, 2º turno sem ajuste",
                        pp(bruto if candidato == "Flávio" else -bruto, 3),
                    )
                )
            campos.extend(item.get("ficha", []))
            partes += [
                f'<circle class="effect-point" data-candidato="{candidato}" data-valor="{valor}" cx="{x(valor):.2f}" cy="{y}" r="4.5" fill="{cor}"/>',
                t(960, y + 4, pp(valor, 2), 12.5, cor, mono=True),
            ]
            k = tips.add(ficha(item["nome"], candidato, campos))
            out.append(hit("".join(partes) + area(esq, y - 10, w - esq, 20), k))
    out.append("</svg>")
    nota = (
        " Valores em pontos percentuais entre os dois finalistas. Lula = −Flávio; "
        "o intervalo [a, b] vira [−b, −a]. São duas leituras do mesmo contraste, não evidências independentes."
    )
    return figura_html(
        ident,
        "".join(out),
        legenda + nota,
        tips,
        modo="scroll",
        minw=900,
        apos=legenda_html([("Flávio", FLAVIO), ("Lula", LULA)]),
    )
