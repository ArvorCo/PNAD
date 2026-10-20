"""Gráficos próprios do relatório de clima, no mesmo traço do laudo irmão.

O texto do gráfico usa as classes `tx` e `tm` da folha de estilo; a cor vai só nas marcas.
Todo gráfico tem tabela equivalente no capítulo.
"""

from __future__ import annotations

from mudancas_secoes_2t.pagina import figuras as fg
from mudancas_secoes_2t.pagina.figuras import (
    LINHA,
    PAINEL,
    TINTA,
    W,
    _abrir,
    _escala,
    _legenda,
    _rotulo_multilinha,
    _txt,
)

barras_h = fg.barras_h
pontos_ic = fg.pontos_ic
floresta_log = fg.floresta_log
reset_ids = fg.reset_ids


def pontos_series(
    titulo: str,
    desc: str,
    linhas: list[dict],
    series: list[tuple[str, str]],
    eixo: tuple[float, float],
    ticks: list[float],
    fmt,
    lw: int = 210,
    zero: float | None = 0.0,
    unidade: str = "",
) -> str:
    """linhas: [{rotulo, pontos: [{v, lo, hi, txt} | None]}], uma marca por série.

    Marca sem intervalo (lo ou hi ausentes) sai vazada e leva o aviso `sem IC`.
    """
    leg, n_leg = _legenda(series, 18)
    topo, passo = 14 + 20 * n_leg + (18 if unidade else 0), 22
    bloco = passo * len(series) + 16
    x0, x1 = lw + 14, W - 170
    altura = topo + bloco * len(linhas) + 30
    partes = []
    if unidade:
        partes.append(_txt(x0, topo - 6, unidade, "tm"))
    for t in ticks:
        x = _escala(t, eixo[0], eixo[1], x0, x1)
        partes.append(
            f'<line x1="{x:.1f}" y1="{topo}" x2="{x:.1f}" y2="{altura - 28}" stroke="{LINHA}"/>'
        )
        partes.append(_txt(x, altura - 10, fmt(t), "tm", "middle"))
    if zero is not None:
        xz = _escala(zero, eixo[0], eixo[1], x0, x1)
        partes.append(
            f'<line x1="{xz:.1f}" y1="{topo}" x2="{xz:.1f}" y2="{altura - 28}" '
            f'stroke="{TINTA}" stroke-width="1.6"/>'
        )
    for i, r in enumerate(linhas):
        y = topo + bloco * i
        partes.append(
            _rotulo_multilinha(lw, y + 8 + passo * len(series) / 2, r["rotulo"], 26)
        )
        for j, p in enumerate(r["pontos"]):
            if p is None:
                continue
            yc = y + 12 + passo * j
            cor = series[j][1]
            xv = _escala(min(max(p["v"], eixo[0]), eixo[1]), *eixo, x0, x1)
            tem_ic = p.get("lo") is not None and p.get("hi") is not None
            if tem_ic:
                xl = _escala(max(p["lo"], eixo[0]), *eixo, x0, x1)
                xh = _escala(min(p["hi"], eixo[1]), *eixo, x0, x1)
                partes.append(
                    f'<line x1="{xl:.1f}" y1="{yc}" x2="{xh:.1f}" y2="{yc}" stroke="{cor}" stroke-width="3"/>'
                    f'<line x1="{xl:.1f}" y1="{yc - 5}" x2="{xl:.1f}" y2="{yc + 5}" stroke="{cor}" stroke-width="2"/>'
                    f'<line x1="{xh:.1f}" y1="{yc - 5}" x2="{xh:.1f}" y2="{yc + 5}" stroke="{cor}" stroke-width="2"/>'
                )
                partes.append(
                    f'<circle cx="{xv:.1f}" cy="{yc}" r="5.5" fill="{cor}" stroke="{PAINEL}" stroke-width="2"/>'
                )
            else:
                partes.append(
                    f'<circle cx="{xv:.1f}" cy="{yc}" r="5.5" fill="{PAINEL}" stroke="{cor}" stroke-width="2.4"/>'
                )
            partes.append(f'<circle cx="{x1 + 16}" cy="{yc}" r="5" fill="{cor}"/>')
            sufixo = ""
            partes.append(_txt(x1 + 28, yc + 4, p["txt"] + sufixo, "tx"))
        partes.append(
            f'<line x1="8" y1="{y + bloco - 5}" x2="{W - 8}" y2="{y + bloco - 5}" '
            f'stroke="{LINHA}" stroke-dasharray="2 4"/>'
        )
    cab, _ = _abrir(altura, titulo, desc)
    return cab + leg + "".join(partes) + "</svg>"


def pontos_referencia(
    titulo: str,
    desc: str,
    linhas: list[dict],
    eixo: tuple[float, float],
    ticks: list[float],
    referencia: float,
    rotulo_ref: str,
    fmt,
    lw: int = 270,
) -> str:
    """linhas: [{rotulo, v, cor, txt}]; um ponto por linha e uma linha de referência."""
    topo, alt = 34, 34
    x0, x1 = lw + 14, W - 200
    altura = topo + alt * len(linhas) + 34
    partes = []
    for t in ticks:
        x = _escala(t, *eixo, x0, x1)
        partes.append(
            f'<line x1="{x:.1f}" y1="{topo - 6}" x2="{x:.1f}" y2="{altura - 28}" stroke="{LINHA}"/>'
        )
        partes.append(_txt(x, altura - 10, fmt(t), "tm", "middle"))
    xr = _escala(referencia, *eixo, x0, x1)
    partes.append(
        f'<line x1="{xr:.1f}" y1="{topo - 6}" x2="{xr:.1f}" y2="{altura - 28}" '
        f'stroke="{TINTA}" stroke-width="1.6" stroke-dasharray="5 4"/>'
    )
    partes.append(_txt(xr, topo - 14, rotulo_ref, "tm", "middle"))
    for i, r in enumerate(linhas):
        yc = topo + alt * i + alt / 2
        partes.append(_rotulo_multilinha(lw, yc, r["rotulo"], 34))
        xv = _escala(r["v"], *eixo, x0, x1)
        partes.append(
            f'<line x1="{xr:.1f}" y1="{yc}" x2="{xv:.1f}" y2="{yc}" stroke="{r["cor"]}" stroke-width="3"/>'
            f'<circle cx="{xv:.1f}" cy="{yc}" r="7" fill="{r["cor"]}" stroke="{PAINEL}" stroke-width="2"/>'
        )
        partes.append(_txt(x1 + 22, yc + 4, r["txt"], "tx"))
    cab, _ = _abrir(altura, titulo, desc)
    return cab + "".join(partes) + "</svg>"


def dispersao_uf(
    titulo: str,
    desc: str,
    pontos: list[dict],
    eixo_x: tuple[float, float],
    eixo_y: tuple[float, float],
    rot_x: str,
    rot_y: str,
    fmt_x,
    fmt_y,
    ticks_x: list[float],
    ticks_y: list[float],
) -> str:
    """pontos: [{uf, x, y, cor, rotulo (bool)}]; só os marcados levam sigla."""
    altura, esq, dir_, topo, base = 360.0, 62.0, W - 28, 20.0, 360.0 - 56
    partes = []
    for t in ticks_x:
        x = _escala(t, *eixo_x, esq, dir_)
        partes.append(
            f'<line x1="{x:.1f}" y1="{topo}" x2="{x:.1f}" y2="{base}" stroke="{LINHA}"/>'
        )
        partes.append(_txt(x, base + 18, fmt_x(t), "tm", "middle"))
    for t in ticks_y:
        y = base - (base - topo) * (t - eixo_y[0]) / (eixo_y[1] - eixo_y[0])
        partes.append(
            f'<line x1="{esq}" y1="{y:.1f}" x2="{dir_}" y2="{y:.1f}" stroke="{LINHA}"/>'
        )
        partes.append(_txt(esq - 8, y + 4, fmt_y(t), "tm", "end"))
    partes.append(_txt((esq + dir_) / 2, base + 40, rot_x, "tm", "middle"))
    partes.append(_txt(esq, 12, rot_y, "tm"))
    partes.append(
        f'<line x1="{esq}" y1="{base}" x2="{dir_}" y2="{base}" stroke="{TINTA}"/>'
        f'<line x1="{esq}" y1="{topo}" x2="{esq}" y2="{base}" stroke="{TINTA}"/>'
    )
    for p in pontos:
        x = _escala(p["x"], *eixo_x, esq, dir_)
        y = base - (base - topo) * (p["y"] - eixo_y[0]) / (eixo_y[1] - eixo_y[0])
        partes.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="{p["cor"]}" stroke="{PAINEL}" '
            f'stroke-width="1.6"><title>{p["uf"]}</title></circle>'
        )
        if p.get("rotulo"):
            partes.append(_txt(x + 9, y - 7, p["uf"], "tx"))
    cab, _ = _abrir(altura, titulo, desc)
    return cab + "".join(partes) + "</svg>"
