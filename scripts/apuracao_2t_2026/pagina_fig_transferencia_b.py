"""Dispersão parcial e barras por UF da regressão ecológica (capítulo "De onde veio o voto").

Fonte: ``transferencia.json`` (``regressao.dispersao`` e ``regressao.por_uf``). A
dispersão é a regressão parcial de Frisch-Waugh: x e y de cada município depois
de descontar o efeito fixo de UF, a terceira via, o branco/nulo do 1º turno e a
variação do eleitorado, e a reta pela origem tem exatamente a inclinação da
regressão principal.
"""

from __future__ import annotations

from apuracao_2026.pagina_comum import NOME_UF, inteiro, num
from apuracao_2026.pagina_fig_base import (
    COR_REGIAO,
    GRADE,
    INK,
    LULA,
    MUTED,
    REGIOES,
    Tips,
    area,
    chip,
    escala,
    ficha,
    figura_html,
    hit,
    legenda_html,
    ln,
    nome_bonito,
    r,
    svg_abre,
    t,
    ticks,
)

TAMANHOS = ((20_000, 2.6), (200_000, 4.4), (10**12, 7.0))


def _nome_uf(uf: str) -> str:
    return str(NOME_UF.get(uf) or uf)


def _linhas(bloco: dict) -> list[dict]:
    cols = bloco["colunas"]
    return [dict(zip(cols, x, strict=True)) for x in bloco["linhas"]]


def fig_dispersao(T: dict) -> str:
    disp = T["regressao"]["dispersao"]
    pts = _linhas(disp)
    b = disp["b_lula"]
    (xa, xb), (ya, yb) = disp["janela_x_pp"], disp["janela_y_pp"]
    xa, xb = min(xa, -1.0), max(xb, 1.0)
    ya, yb = min(ya, -1.0), max(yb, 1.0)
    w, h = 760, 560
    X0, X1, Y0, Y1 = 70, 730, 30, 500
    fx = escala(xa, xb, X0, X1)
    fy = escala(ya, yb, Y1, Y0)
    out = [
        svg_abre(
            w,
            h,
            "Variação do comparecimento contra variação dos votos de Lula, por município",
            "Cada ponto é um município, depois de descontar a UF, a terceira via e o branco e nulo do 1º turno. "
            f"A reta tem a inclinação da regressão: {num(b, 2)} voto de Lula por eleitor a mais.",
        )
    ]
    for v in ticks(xa, xb, 6):
        out.append(ln(fx(v), Y0, fx(v), Y1, GRADE, 1))
        out.append(t(fx(v), Y1 + 20, num(v, 0), 12, MUTED, "middle", mono=True))
    for v in ticks(ya, yb, 6):
        out.append(ln(X0, fy(v), X1, fy(v), GRADE, 1))
        out.append(t(X0 - 8, fy(v) + 4, num(v, 0), 12, MUTED, "end", mono=True))
    out.append(ln(fx(0), Y0, fx(0), Y1, INK, 1))
    out.append(ln(X0, fy(0), X1, fy(0), INK, 1))
    fora = 0
    grupos: dict[tuple[str, float], list[str]] = {}
    for p in pts:
        x, y = p["x_pp"], p["y_lula_pp"]
        if not (xa <= x <= xb and ya <= y <= yb):
            fora += 1
            continue
        tam = next(s for lim, s in TAMANHOS if p["eleitores"] < lim)
        grupos.setdefault((p["regiao"], tam), []).append(f"M{fx(x):.1f} {fy(y):.1f}h0")
    for tam in sorted({k[1] for k in grupos}):
        for reg in REGIOES:
            seg = grupos.get((reg, tam))
            if seg:
                out.append(
                    f'<path d="{"".join(seg)}" stroke="{COR_REGIAO[reg]}" stroke-width="{tam}" '
                    'stroke-linecap="round" stroke-opacity="0.5" fill="none"/>'
                )
    # Reta da regressão (pela origem) e referência de metade.
    for incl, cor, larg, tracejo in (
        (0.5, MUTED, 1.2, ' stroke-dasharray="5 4"'),
        (b, LULA, 2.6, ""),
    ):
        xs = [max(xa, ya / incl), min(xb, yb / incl)]
        out.append(
            ln(
                fx(xs[0]),
                fy(incl * xs[0]),
                fx(xs[1]),
                fy(incl * xs[1]),
                cor,
                larg,
                tracejo,
            )
        )
    xr = min(xb, yb / b) * 0.92
    out.append(
        chip(
            fx(xr) - 250,
            fy(b * xr) - 4,
            f"inclinação {num(b, 2)}: Lula por eleitor a mais",
            12,
        )
    )
    xm = min(xb, yb / 0.5) * 0.98
    out.append(t(fx(xm), fy(0.5 * xm) + 18, "metade", 12, MUTED, "end"))
    tips = Tips()
    caps = sorted((p for p in pts if p["capital"]), key=lambda p: -p["eleitores"])
    for p in caps:
        x, y = p["x_pp"], p["y_lula_pp"]
        if not (xa <= x <= xb and ya <= y <= yb):
            continue
        cx, cy = fx(x), fy(y)
        k = tips.add(
            ficha(
                f"{nome_bonito(p['nome'])} ({p['uf']})",
                "capital",
                [
                    ("Variação do comparecimento (parcial)", f"{num(x, 2)} pp"),
                    ("Variação de Lula (parcial)", f"{num(p['y_lula_pp'], 2)} pp"),
                    ("Variação de Flávio (parcial)", f"{num(p['y_flavio_pp'], 2)} pp"),
                    ("Eleitores", inteiro(p["eleitores"])),
                ],
                "Valores depois de descontar UF, terceira via e branco e nulo do 1º turno.",
            )
        )
        out.append(
            hit(
                f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="5.5" fill="none" stroke="{INK}" stroke-width="1.5"/>'
                + area(cx - 7, cy - 7, 14, 14),
                k,
            )
        )
    out.append(
        t(
            (X0 + X1) / 2,
            h - 22,
            "Variação do comparecimento, 2º menos 1º turno (pontos do eleitorado, parcial)",
            13,
            INK,
            "middle",
        )
    )
    out.append(
        t(
            18,
            (Y0 + Y1) / 2,
            "Variação dos votos de Lula (pontos, parcial)",
            13,
            INK,
            "middle",
            extra=f' transform="rotate(-90 18 {(Y0 + Y1) / 2:.0f})"',
        )
    )
    out.append("</svg>")
    leg = legenda_html(
        [(rg, COR_REGIAO[rg]) for rg in REGIOES] + [("capital (círculo)", "#ffffff")],
        "Região",
    )
    legenda = (
        f"{inteiro(len(pts))} municípios; {inteiro(fora)} ficam fora da janela (0,5% em cada ponta) e não aparecem. "
        f"Ponto maior, município maior. A reta vermelha passa pela origem com inclinação {num(b, 2)}, a da regressão principal "
        f"(Flávio: {num(disp['b_flavio'], 2)}); a tracejada marca metade. Fonte: transferencia.json (regressao.dispersao)."
    )
    return figura_html(
        "tr_dispersao", "".join(out), legenda, tips, modo="scroll", minw=620, apos=leg
    )


def fig_barras_uf(T: dict) -> str:
    reg = T["regressao"]
    nac = 100 * reg["principal"]["coef"]["L"]["delta_comparecimento"]["b"]
    ufs = [u for u in reg["por_uf"] if "L" in u]
    sem = [u["uf"] for u in reg["por_uf"] if "L" not in u]
    ufs.sort(key=lambda u: -u["L"]["b"])
    lo = min(-10.0, min(100 * u["L"]["ic95"][0] for u in ufs))
    hi = max(110.0, max(100 * u["L"]["ic95"][1] for u in ufs))
    lo, hi = 10 * (lo // 10), 10 * (-(-hi // 10))
    linha = 23
    topo = 66
    w = 760
    h = topo + linha * len(ufs) + 46
    X0, X1 = 200, 735
    fx = escala(lo, hi, X0, X1)
    out = [
        svg_abre(
            w,
            h,
            "De cada 100 eleitores a mais, quantos foram para Lula, por UF",
            "Regressão dentro de cada UF, entre os seus municípios, com intervalo de 95%. Linha vermelha: o Brasil com efeito fixo de UF.",
        )
    ]
    for v in ticks(lo, hi, 8):
        out.append(ln(fx(v), topo - 8, fx(v), h - 40, GRADE, 1))
        out.append(t(fx(v), h - 22, num(v, 0), 12, MUTED, "middle", mono=True))
    for ref, rot in ((0, "0"), (50, "metade"), (100, "todos")):
        out.append(
            ln(
                fx(ref),
                topo - 8,
                fx(ref),
                h - 40,
                MUTED,
                1.2,
                ' stroke-dasharray="4 3"',
            )
        )
        if rot != "0":
            out.append(t(fx(ref) + 4, topo - 14, rot, 12, MUTED))
    out.append(ln(fx(nac), topo - 8, fx(nac), h - 40, LULA, 2))
    out.append(
        t(
            fx(nac) + 4,
            topo - 34,
            f"Brasil, efeito fixo de UF: {num(nac, 1)}",
            12,
            LULA,
            weight="700",
        )
    )
    tips = Tips()
    for i, u in enumerate(ufs):
        y = topo + i * linha
        b = 100 * u["L"]["b"]
        a0, a1 = (100 * v for v in u["L"]["ic95"])
        xb0, xb1 = sorted((fx(0), fx(b)))
        k = tips.add(
            ficha(
                _nome_uf(u["uf"]),
                f"{inteiro(u['n'])} municípios",
                [
                    ("Lula por 100 eleitores a mais", num(b, 1)),
                    ("Intervalo de 95%", f"{num(a0, 1)} a {num(a1, 1)}"),
                    ("Flávio por 100", num(100 * u["F"]["b"], 1)),
                    ("Branco e nulo por 100", num(100 * u["BN"]["b"], 1)),
                    (
                        "Variação líquida do comparecimento",
                        inteiro(u["delta_comparecimento"]),
                    ),
                ],
                "Abaixo de 0 ou acima de 100 não é transferência possível: é sinal de que a regressão mede o contexto do município, não o eleitor.",
            )
        )
        corpo = (
            r(xb0, y + 4, xb1 - xb0, linha - 9, LULA, ' fill-opacity="0.78"')
            + ln(fx(a0), y + linha / 2 - 0.5, fx(a1), y + linha / 2 - 0.5, INK, 1.4)
            + ln(fx(a0), y + 6, fx(a0), y + linha - 7, INK, 1.4)
            + ln(fx(a1), y + 6, fx(a1), y + linha - 7, INK, 1.4)
            + area(X0 - 190, y, X1 - X0 + 190, linha)
        )
        out.append(hit(corpo, k))
        out.append(
            t(
                X0 - 10,
                y + linha / 2 + 4,
                f"{_nome_uf(u['uf'])} ({u['n']})",
                13,
                INK,
                "end",
            )
        )
    out.append(
        t(
            (X0 + X1) / 2,
            h - 4,
            "Votos de Lula por 100 eleitores a mais",
            13,
            INK,
            "middle",
        )
    )
    out.append("</svg>")
    legenda = (
        f"Barra: estimativa; traço: intervalo de 95% (erro robusto). Entre parênteses, número de municípios. "
        f"{', '.join(sem)} fica de fora (um município só). UFs pequenas têm intervalo largo, e estimativa fora de 0 a 100 "
        "denuncia o limite ecológico, não um eleitor. Fonte: transferencia.json (regressao.por_uf)."
    )
    return figura_html("tr_ufs", "".join(out), legenda, tips, modo="scroll", minw=620)
