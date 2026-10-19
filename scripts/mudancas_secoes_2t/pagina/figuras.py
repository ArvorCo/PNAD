"""Gráficos em SVG desenhados em Python, com os dados dentro do próprio HTML.

Texto de gráfico usa só tinta e cinza da casa sobre o painel claro; cor de série vai nas
marcas, nunca em texto pequeno. Cada figura leva título, descrição e a tabela equivalente
fica no capítulo, então o gráfico nunca é a única forma de ler o número.
"""

from __future__ import annotations

import math

from .util import CORES, esc, inteiro

W = 760
TINTA, CINZA, LINHA, PAINEL = (
    CORES["tinta"],
    CORES["cinza"],
    CORES["linha"],
    CORES["painel"],
)
_ids = {"n": 0}


def _abrir(altura: float, titulo: str, desc: str) -> tuple[str, str]:
    _ids["n"] += 1
    base = f"fig{_ids['n']}"
    cab = (
        f'<svg viewBox="0 0 {W} {altura:.0f}" role="img" aria-labelledby="{base}t {base}d" '
        f'xmlns="http://www.w3.org/2000/svg"><title id="{base}t">{esc(titulo)}</title>'
        f'<desc id="{base}d">{esc(desc)}</desc>'
    )
    return cab, base


def reset_ids() -> None:
    _ids["n"] = 0


def _txt(x, y, s, cls="tx", anchor="start", extra="") -> str:
    return f'<text x="{x:.1f}" y="{y:.1f}" class="{cls}" text-anchor="{anchor}"{extra}>{esc(s)}</text>'


def _linhas_rotulo(rotulo: str, n: int) -> list[str]:
    palavras, linhas, atual = rotulo.split(), [], ""
    for p in palavras:
        if atual and len(atual) + 1 + len(p) > n:
            linhas.append(atual)
            atual = p
        else:
            atual = (atual + " " + p).strip()
    if atual:
        linhas.append(atual)
    return linhas[:3]


def _rotulo_multilinha(x, yc, rotulo, n=30, cls="tx") -> str:
    ls = _linhas_rotulo(rotulo, n)
    y0 = yc - (len(ls) - 1) * 7.5 + 4
    return "".join(_txt(x, y0 + i * 15, s, cls, "end") for i, s in enumerate(ls))


def _legenda(itens: list[tuple[str, str]], y: float, x0: float = 12) -> tuple[str, int]:
    """Legenda que quebra de linha; devolve o SVG e o número de linhas usadas."""
    out, x, linha = [], x0, 0
    for rot, cor in itens:
        larg = 17 + 7.6 * len(rot) + 22
        if x > x0 and x + larg > W - 12:
            x, linha = x0, linha + 1
        yy = y + linha * 20
        out.append(f'<rect x="{x}" y="{yy - 10}" width="12" height="12" fill="{cor}"/>')
        out.append(_txt(x + 17, yy, rot, "tm"))
        x += larg
    return "".join(out), linha + 1


def barras_h(
    titulo: str,
    desc: str,
    linhas: list[dict],
    legenda: list[tuple[str, str]] | None = None,
    fmt=inteiro,
    lw: int = 250,
    rotulo_n: int = 34,
    maximo: float | None = None,
) -> str:
    """linhas: [{rotulo, barras: [{v, cor, txt?}]}]; barras do mesmo grupo ficam coladas."""
    altura_barra, gap = 15, 18
    leg, n_leg = _legenda(legenda, 18) if legenda else ("", 0)
    topo = 14 + 20 * n_leg if legenda else 12
    x0, x1 = lw + 14, W - 92
    mx = maximo or max(b["v"] for r in linhas for b in r["barras"]) * 1.0
    mx = mx or 1
    y = topo
    partes = []
    for r in linhas:
        n = len(r["barras"])
        bloco = n * (altura_barra + 3) - 3
        h = max(bloco, 32 if len(_linhas_rotulo(r["rotulo"], rotulo_n)) > 2 else 20)
        yc = y + h / 2
        partes.append(_rotulo_multilinha(lw, yc, r["rotulo"], rotulo_n))
        yb = y + (h - bloco) / 2
        for b in r["barras"]:
            w = max((x1 - x0) * b["v"] / mx, 1.5 if b["v"] else 0)
            partes.append(
                f'<rect x="{x0}" y="{yb:.1f}" width="{w:.1f}" height="{altura_barra}" fill="{b["cor"]}"/>'
            )
            partes.append(_txt(x0 + w + 6, yb + 12, b.get("txt") or fmt(b["v"]), "tx"))
            yb += altura_barra + 3
        y += h + gap
    cab, _ = _abrir(y + 6, titulo, desc)
    base = f'<line x1="{x0}" y1="{topo - 6}" x2="{x0}" y2="{y - gap + 6}" stroke="{TINTA}" stroke-width="1"/>'
    return cab + leg + base + "".join(partes) + "</svg>"


def empilhado(
    titulo: str,
    desc: str,
    linhas: list[dict],
    cores: dict[str, str],
    nomes: dict[str, str],
    lw: int = 60,
) -> str:
    """linhas: [{rotulo, segs: {chave: valor}}]; barra empilhada com o total no fim."""
    leg, n_leg = _legenda([(nomes[k], cores[k]) for k in cores], 18)
    topo, alt, gap = 14 + 20 * n_leg, 16, 6
    x0, x1 = lw + 14, W - 80
    mx = max(sum(r["segs"].values()) for r in linhas) or 1
    partes, y = [], topo
    for r in linhas:
        partes.append(_txt(lw, y + 12, r["rotulo"], "tx", "end"))
        x = x0
        for k in cores:
            v = r["segs"].get(k, 0)
            if not v:
                continue
            w = (x1 - x0) * v / mx
            partes.append(
                f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{alt}" fill="{cores[k]}"><title>{esc(nomes[k])}: {inteiro(v)}</title></rect>'
            )
            x += w
        partes.append(_txt(x + 6, y + 12, inteiro(sum(r["segs"].values())), "tx"))
        y += alt + gap
    cab, _ = _abrir(y + 8, titulo, desc)
    eixo = f'<line x1="{x0}" y1="{topo - 4}" x2="{x0}" y2="{y}" stroke="{TINTA}"/>'
    return cab + leg + eixo + "".join(partes) + "</svg>"


def histograma(
    titulo: str, desc: str, faixas: list[tuple[str, float, str]], unidade: str
) -> str:
    """faixas: [(rótulo, valor, cor)]; barras verticais com o valor em cima."""
    altura = 300
    base_y, topo = altura - 52, 62
    n = len(faixas)
    margem = 20
    larg = (W - 2 * margem) / n
    mx = max(v for _, v, _ in faixas) or 1
    partes = []
    for i, (rot, v, cor) in enumerate(faixas):
        h = (base_y - topo) * v / mx
        x = margem + i * larg + larg * 0.14
        w = larg * 0.72
        partes.append(
            f'<rect x="{x:.1f}" y="{base_y - h:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{cor}"/>'
        )
        partes.append(_txt(x + w / 2, base_y - h - 7, inteiro(v), "tx", "middle"))
        for j, s in enumerate(_linhas_rotulo(rot, 11)):
            partes.append(_txt(x + w / 2, base_y + 18 + j * 15, s, "tm", "middle"))
    cab, _ = _abrir(altura, titulo, desc)
    eixo = f'<line x1="{margem}" y1="{base_y}" x2="{W - margem}" y2="{base_y}" stroke="{TINTA}"/>'
    cap = _txt(margem, 18, unidade, "tm")
    return cab + cap + eixo + "".join(partes) + "</svg>"


def _escala(v, lo, hi, x0, x1):
    return x0 + (x1 - x0) * (v - lo) / (hi - lo)


def pontos_ic(
    titulo: str,
    desc: str,
    linhas: list[dict],
    eixo: tuple[float, float],
    ticks: list[float],
    fmt,
    lw: int = 250,
    zero: float | None = None,
    rotulo_n: int = 34,
    unidade: str = "",
) -> str:
    """linhas: [{rotulo, v, lo, hi, cor, txt}]; ponto com intervalo e valor à direita."""
    topo, alt = 30, 30
    x0, x1 = lw + 14, W - 150
    partes = []
    for t in ticks:
        x = _escala(t, eixo[0], eixo[1], x0, x1)
        partes.append(
            f'<line x1="{x:.1f}" y1="{topo - 8}" x2="{x:.1f}" y2="{topo + alt * len(linhas)}" stroke="{LINHA}"/>'
        )
        partes.append(_txt(x, topo + alt * len(linhas) + 16, fmt(t), "tm", "middle"))
    if zero is not None:
        xz = _escala(zero, eixo[0], eixo[1], x0, x1)
        partes.append(
            f'<line x1="{xz:.1f}" y1="{topo - 8}" x2="{xz:.1f}" y2="{topo + alt * len(linhas)}" stroke="{TINTA}" stroke-width="1.6"/>'
        )
    for i, r in enumerate(linhas):
        yc = topo + alt * i + alt / 2
        partes.append(_rotulo_multilinha(lw, yc, r["rotulo"], rotulo_n))
        lo = max(r["lo"], eixo[0])
        hi = min(r["hi"], eixo[1])
        xl, xh = _escala(lo, *eixo, x0, x1), _escala(hi, *eixo, x0, x1)
        partes.append(
            f'<line x1="{xl:.1f}" y1="{yc}" x2="{xh:.1f}" y2="{yc}" stroke="{r["cor"]}" stroke-width="3"/>'
            f'<line x1="{xl:.1f}" y1="{yc - 6}" x2="{xl:.1f}" y2="{yc + 6}" stroke="{r["cor"]}" stroke-width="2"/>'
            f'<line x1="{xh:.1f}" y1="{yc - 6}" x2="{xh:.1f}" y2="{yc + 6}" stroke="{r["cor"]}" stroke-width="2"/>'
        )
        xv = _escala(min(max(r["v"], eixo[0]), eixo[1]), *eixo, x0, x1)
        partes.append(
            f'<circle cx="{xv:.1f}" cy="{yc}" r="6" fill="{r["cor"]}" stroke="{PAINEL}" stroke-width="2"/>'
        )
        partes.append(_txt(x1 + 14, yc + 4, r["txt"], "tx"))
    altura = topo + alt * len(linhas) + 34
    cab, _ = _abrir(altura, titulo, desc)
    cap = _txt(x0, 16, unidade, "tm") if unidade else ""
    return cab + cap + "".join(partes) + "</svg>"


def floresta_log(
    titulo: str,
    desc: str,
    linhas: list[dict],
    series: list[tuple[str, str]],
    fmt,
    lw: int = 210,
) -> str:
    """linhas: [{rotulo, pontos: [{v, lo, hi}]}]; eixo logarítmico, linha de referência em 1."""
    lo_eixo, hi_eixo = 0.4, 80.0
    ticks = [0.5, 1, 2, 5, 10, 20, 50]
    leg, n_leg = _legenda(series, 18)
    topo, bloco = 14 + 20 * n_leg, 24 * len(series) + 14
    x0, x1 = lw + 14, W - 120

    def px(v):
        v = min(max(v, lo_eixo), hi_eixo)
        return x0 + (x1 - x0) * (math.log(v) - math.log(lo_eixo)) / (
            math.log(hi_eixo) - math.log(lo_eixo)
        )

    altura_total = topo + bloco * len(linhas) + 26
    partes = []
    for t in ticks:
        partes.append(
            f'<line x1="{px(t):.1f}" y1="{topo - 8}" x2="{px(t):.1f}" y2="{altura_total - 26}" stroke="{LINHA}"/>'
        )
        partes.append(
            _txt(
                px(t),
                altura_total - 8,
                f"{t:g}".replace(".", ",") + "×",
                "tm",
                "middle",
            )
        )
    partes.append(
        f'<line x1="{px(1):.1f}" y1="{topo - 8}" x2="{px(1):.1f}" y2="{altura_total - 26}" stroke="{TINTA}" stroke-width="1.8"/>'
    )
    for i, r in enumerate(linhas):
        y = topo + bloco * i
        partes.append(_rotulo_multilinha(lw, y + 12 * len(series), r["rotulo"], 28))
        for j, p in enumerate(r["pontos"]):
            yc = y + 12 + 24 * j
            cor = series[j][1]
            partes.append(
                f'<line x1="{px(p["lo"]):.1f}" y1="{yc}" x2="{px(p["hi"]):.1f}" y2="{yc}" stroke="{cor}" stroke-width="3"/>'
                f'<circle cx="{px(p["v"]):.1f}" cy="{yc}" r="5.5" fill="{cor}" stroke="{PAINEL}" stroke-width="2"/>'
            )
            partes.append(f'<circle cx="{x1 + 16}" cy="{yc}" r="5" fill="{cor}"/>')
            partes.append(_txt(x1 + 28, yc + 4, fmt(p["v"]) + "×", "tx"))
        partes.append(
            f'<line x1="8" y1="{y + bloco - 5}" x2="{W - 8}" y2="{y + bloco - 5}" stroke="{LINHA}" stroke-dasharray="2 4"/>'
        )
    cab, _ = _abrir(altura_total, titulo, desc)
    return cab + leg + "".join(partes) + "</svg>"


def divergente(
    titulo: str,
    desc: str,
    linhas: list[dict],
    legenda: list[tuple[str, str]],
    fmt,
    lw: int = 190,
) -> str:
    """linhas: [{rotulo, barras: [{v (com sinal), cor}]}]; zero ao centro, perda à esquerda."""
    leg, n_leg = _legenda(legenda, 18)
    topo, alt, gap = 40 + 20 * n_leg, 15, 22
    x0, x1 = lw + 30, W - 30
    mx = max(abs(b["v"]) for r in linhas for b in r["barras"]) or 1
    xz = (x0 + x1) / 2
    meia = (x1 - x0) / 2 - 62
    y, partes = topo, []
    for r in linhas:
        n = len(r["barras"])
        bloco = n * (alt + 3) - 3
        partes.append(_rotulo_multilinha(lw, y + bloco / 2, r["rotulo"], 26))
        yb = y
        for b in r["barras"]:
            w = meia * abs(b["v"]) / mx
            x = xz - w if b["v"] < 0 else xz
            partes.append(
                f'<rect x="{x:.1f}" y="{yb}" width="{max(w, 1.5):.1f}" height="{alt}" fill="{b["cor"]}"/>'
            )
            if b["v"] < 0:
                partes.append(_txt(x - 6, yb + 12, fmt(b["v"]), "tx", "end"))
            else:
                partes.append(_txt(x + w + 6, yb + 12, fmt(b["v"]), "tx"))
            yb += alt + 3
        y += bloco + gap
    cab, _ = _abrir(y + 4, titulo, desc)
    eixo = f'<line x1="{xz}" y1="{topo - 8}" x2="{xz}" y2="{y - gap + 6}" stroke="{TINTA}" stroke-width="1.6"/>'
    rot = _txt(xz - 8, topo - 14, "perde voto", "tm", "end") + _txt(
        xz + 8, topo - 14, "recupera voto", "tm"
    )
    return cab + leg + rot + eixo + "".join(partes) + "</svg>"
