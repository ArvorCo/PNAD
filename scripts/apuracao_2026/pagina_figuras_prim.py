"""Primitivas SVG do dossiê da apuração (barras, linhas, hemiciclo, cascata, dispersão).

Cada função devolve um ``<svg>`` completo com ``<title>`` e ``aria-label``. O
viewBox é desenhado na largura em que a figura aparece, para que o tamanho de
fonte declarado seja o que o leitor enxerga. Texto pequeno usa só tinta, cinza
da casa ou as cores de Lula e Flávio, que passam em contraste sobre o papel.
"""

from __future__ import annotations

import math
from html import escape

from .pagina_comum import CINZA, FLAVIO, INK, LINE, LULA, MUTED, PAPER, num

FONTE = "Archivo, Helvetica, Arial, sans-serif"
MONO = "IBM Plex Mono, ui-monospace, monospace"
ESCURAS = {LULA, FLAVIO, INK, "#0f7f5f", "#3d8a74"}


def abre(w: float, h: float, titulo: str, desc: str, cls: str = "fig") -> str:
    return (
        f'<svg class="{cls}" viewBox="0 0 {w:.0f} {h:.0f}" role="img" '
        f'aria-label="{escape(desc)}" xmlns="http://www.w3.org/2000/svg">'
        f"<title>{escape(titulo)}</title>"
    )


def txt(
    x: float,
    y: float,
    s: str,
    size: float = 13,
    fill: str = INK,
    anchor: str = "start",
    weight: str | None = None,
    family: str = FONTE,
    extra: str = "",
) -> str:
    peso = f' font-weight="{weight}"' if weight else ""
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" '
        f'font-family="{family}" text-anchor="{anchor}"{peso}{extra}>{escape(str(s))}</text>'
    )


def rect(x, y, w, h, fill, extra: str = "") -> str:
    return (
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(w, 0):.1f}" '
        f'height="{max(h, 0):.1f}" fill="{fill}"{extra}/>'
    )


def linha(x1, y1, x2, y2, stroke=LINE, w: float = 1, extra: str = "") -> str:
    return (
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
        f'stroke="{stroke}" stroke-width="{w}"{extra}/>'
    )


def cor_texto_sobre(fundo: str) -> str:
    return "#ffffff" if fundo in ESCURAS else INK


def legenda_linha(itens: list[tuple[str, str]], x: float, y: float) -> str:
    """Legenda horizontal: quadrado de cor e nome."""
    out, cx = [], x
    for nome, cor in itens:
        out.append(rect(cx, y - 10, 12, 12, cor))
        out.append(txt(cx + 17, y, nome, 13, INK))
        cx += 30 + 7.4 * len(nome)
    return "".join(out)


# ------------------------------------------------------------------ barras


def barras_h(
    itens: list[dict],
    titulo: str,
    desc: str,
    largura: float = 760,
    rotulo_w: float = 190,
    max_v: float | None = None,
    passo: float = 34,
) -> str:
    """Barras horizontais. Item: rotulo, valor, cor, texto (opcional)."""
    topo = 12
    h = topo + passo * len(itens) + 10
    vmax = max_v or max((i["valor"] for i in itens), default=1) or 1
    area = largura - rotulo_w - 120
    out = [abre(largura, h, titulo, desc)]
    for k, it in enumerate(itens):
        y = topo + k * passo
        w = area * max(it["valor"], 0) / vmax
        out.append(txt(rotulo_w - 10, y + passo / 2 + 4, it["rotulo"], 14, INK, "end"))
        out.append(rect(rotulo_w, y + 7, w, passo - 14, it["cor"]))
        texto = it.get("texto", num(it["valor"], 2))
        out.append(
            txt(rotulo_w + w + 8, y + passo / 2 + 5, texto, 14, INK, family=MONO)
        )
    out.append("</svg>")
    return "".join(out)


def divergentes(
    linhas: list[tuple[str, list[float | None]]],
    series: list[tuple[str, str]],
    titulo: str,
    desc: str,
    largura: float = 820,
    rotulo_w: float = 150,
    unidade: str = " pp",
    casas: int = 1,
    limite: float | None = None,
) -> str:
    """Barras divergentes de um zero central; uma ou mais séries por linha."""
    ns = len(series)
    barra = 11 if ns > 1 else 16
    passo = ns * barra + 12
    topo = 44
    h = topo + passo * len(linhas) + 34
    valores = [abs(v) for _, vs in linhas for v in vs if v is not None]
    vmax = limite or (max(valores, default=1) * 1.08) or 1
    x0 = rotulo_w + (largura - rotulo_w - 20) / 2
    meia = (largura - rotulo_w - 150) / 2
    out = [abre(largura, h, titulo, desc)]
    out.append(legenda_linha(series, rotulo_w, 18))
    # grade
    passo_tick = _passo_bonito(vmax)
    t = -math.floor(vmax / passo_tick) * passo_tick
    while t <= vmax + 1e-9:
        x = x0 + meia * t / vmax
        out.append(linha(x, topo - 6, x, h - 30, LINE, 1))
        out.append(
            txt(
                x,
                h - 12,
                num(t, 0 if passo_tick >= 1 else 1),
                12,
                MUTED,
                "middle",
                family=MONO,
            )
        )
        t += passo_tick
    out.append(linha(x0, topo - 6, x0, h - 30, INK, 1.4))
    for k, (rot, vs) in enumerate(linhas):
        y = topo + k * passo
        out.append(txt(rotulo_w - 10, y + passo / 2 + 3, rot, 13.5, INK, "end"))
        for j, v in enumerate(vs):
            if v is None:
                continue
            yy = y + 6 + j * barra
            w = meia * abs(v) / vmax
            x = x0 if v >= 0 else x0 - w
            out.append(rect(x, yy, w, barra - 2, series[j][1]))
            tx = x0 + w + 5 if v >= 0 else x0 - w - 5
            out.append(
                txt(
                    tx,
                    yy + barra - 3,
                    _fmt(v, casas, unidade),
                    11.5,
                    INK,
                    "start" if v >= 0 else "end",
                    family=MONO,
                )
            )
    out.append("</svg>")
    return "".join(out)


def _fmt(v: float, casas: int, unidade: str) -> str:
    s = num(abs(v), casas)
    return ("+" if v > 0 else "−" if v < 0 else "") + s + unidade


def _passo_bonito(vmax: float) -> float:
    alvo = vmax / 4
    base = 10 ** math.floor(math.log10(alvo)) if alvo > 0 else 1
    for m in (1, 2, 2.5, 5, 10):
        if base * m >= alvo:
            return base * m
    return base * 10


def empilhadas(
    linhas: list[tuple[str, list[tuple[float, str, str]], str]],
    titulo: str,
    desc: str,
    largura: float = 820,
    rotulo_w: float = 120,
    direita_w: float = 120,
    marcas: list[tuple[float, str]] | None = None,
) -> str:
    """Barras 100% empilhadas. Linha: rótulo, [(valor, cor, nome)], texto à direita."""
    passo = 40
    topo = 46
    h = topo + passo * len(linhas) + (30 if marcas else 12)
    area = largura - rotulo_w - direita_w
    out = [abre(largura, h, titulo, desc)]
    vistos: dict[str, str] = {}
    for _, segs, _ in linhas:
        for _, cor, nome in segs:
            vistos.setdefault(nome, cor)
    out.append(legenda_linha(list(vistos.items()), rotulo_w, 18))
    for k, (rot, segs, direita) in enumerate(linhas):
        y = topo + k * passo
        total = sum(v for v, _, _ in segs) or 1
        x = rotulo_w
        out.append(txt(rotulo_w - 10, y + 21, rot, 14, INK, "end", "600"))
        for v, cor, nome in segs:
            w = area * v / total
            out.append(
                rect(
                    x, y + 4, w, passo - 12, cor, f' stroke="{PAPER}" stroke-width="1"'
                ).replace("/>", f"><title>{escape(nome)}: {num(v, 0)}</title></rect>")
            )
            if w >= 24 and v:
                out.append(
                    txt(
                        x + w / 2,
                        y + 22,
                        num(v, 0),
                        12.5,
                        cor_texto_sobre(cor),
                        "middle",
                        "600",
                        MONO,
                    )
                )
            x += w
        out.append(txt(rotulo_w + area + 10, y + 21, direita, 13, INK, family=MONO))
    if marcas:
        for frac, nome in marcas:
            x = rotulo_w + area * frac
            out.append(
                linha(x, topo - 4, x, h - 22, INK, 1.2, ' stroke-dasharray="4 3"')
            )
            out.append(txt(x, h - 6, nome, 12, INK, "middle"))
    out.append("</svg>")
    return "".join(out)


# ------------------------------------------------------------------ linhas


def grafico_linhas(
    series: list[tuple[str, str, list[tuple[float, float]]]],
    xlim: tuple[float, float],
    ylim: tuple[float, float],
    xticks: list[tuple[float, str]],
    yticks: list[tuple[float, str]],
    titulo: str,
    desc: str,
    largura: float = 900,
    altura: float = 380,
    sombras: list[tuple[float, float, str]] | None = None,
    rotulo_fim: bool = True,
    degraus: bool = False,
    margem_dir: float = 150,
) -> str:
    """Linhas no tempo, com faixas sombreadas (paradas, janelas)."""
    esq, topo, base = 70, 24, 40
    w = largura - esq - margem_dir
    hh = altura - topo - base

    def X(v):
        return esq + w * (v - xlim[0]) / (xlim[1] - xlim[0])

    def Y(v):
        return topo + hh * (1 - (v - ylim[0]) / (ylim[1] - ylim[0]))

    out = [abre(largura, altura, titulo, desc)]
    for a, b, rot in sombras or []:
        out.append(rect(X(a), topo, X(b) - X(a), hh, "#e2d6b8", ' opacity="0.9"'))
        rot_s = rot if X(b) - X(a) >= 6.5 * len(rot) else rot.split()[-1]
        out.append(txt((X(a) + X(b)) / 2, topo + 14, rot_s, 11.5, INK, "middle", "600"))
    for v, rot in yticks:
        out.append(linha(esq, Y(v), esq + w, Y(v), LINE, 1))
        out.append(txt(esq - 8, Y(v) + 4, rot, 12, MUTED, "end", family=MONO))
    for v, rot in xticks:
        out.append(linha(X(v), topo + hh, X(v), topo + hh + 5, MUTED, 1))
        out.append(txt(X(v), topo + hh + 20, rot, 12, MUTED, "middle", family=MONO))
    out.append(linha(esq, topo + hh, esq + w, topo + hh, INK, 1.2))
    finais = []
    for nome, cor, pts in series:
        if not pts:
            continue
        cam = []
        prev = None
        for x, y in pts:
            if degraus and prev is not None:
                cam.append(f"L{X(x):.1f},{Y(prev):.1f}")
            cam.append(("M" if not cam else "L") + f"{X(x):.1f},{Y(y):.1f}")
            prev = y
        out.append(
            f'<path d="{"".join(cam)}" fill="none" stroke="{cor}" stroke-width="2.4" '
            'stroke-linejoin="round"/>'
        )
        finais.append([Y(pts[-1][1]), nome, cor, X(pts[-1][0])])
    if rotulo_fim:
        finais.sort()
        for i in range(1, len(finais)):
            if finais[i][0] - finais[i - 1][0] < 16:
                finais[i][0] = finais[i - 1][0] + 16
        for y, nome, cor, x in finais:
            out.append(
                txt(
                    x + 8,
                    y + 4,
                    nome,
                    13,
                    cor if cor in (LULA, FLAVIO) else INK,
                    weight="600",
                )
            )
    out.append("</svg>")
    return "".join(out)


def barras_tempo(
    barras: list[tuple[float, list[tuple[float, str]]]],
    xlim: tuple[float, float],
    xticks: list[tuple[float, str]],
    yticks: list[tuple[float, str]],
    ymax: float,
    titulo: str,
    desc: str,
    largura: float = 900,
    altura: float = 330,
    sombras: list[tuple[float, float, str]] | None = None,
    legenda: list[tuple[str, str]] | None = None,
) -> str:
    """Barras finas no tempo, empilhadas (o que cada atualização trouxe)."""
    esq, topo, base, dirm = 70, 34, 40, 30
    w = largura - esq - dirm
    hh = altura - topo - base

    def X(v):
        return esq + w * (v - xlim[0]) / (xlim[1] - xlim[0])

    out = [abre(largura, altura, titulo, desc)]
    if legenda:
        out.append(legenda_linha(legenda, esq, 16))
    for a, b, rot in sombras or []:
        out.append(rect(X(a), topo, X(b) - X(a), hh, "#e2d6b8", ' opacity="0.9"'))
        rot_s = rot if X(b) - X(a) >= 6.5 * len(rot) else rot.split()[-1]
        out.append(txt((X(a) + X(b)) / 2, topo + 14, rot_s, 11.5, INK, "middle", "600"))
    for v, rot in yticks:
        y = topo + hh * (1 - v / ymax)
        out.append(linha(esq, y, esq + w, y, LINE, 1))
        out.append(txt(esq - 8, y + 4, rot, 12, MUTED, "end", family=MONO))
    for v, rot in xticks:
        out.append(txt(X(v), topo + hh + 20, rot, 12, MUTED, "middle", family=MONO))
    for t, segs in barras:
        x = X(t)
        y = topo + hh
        for v, cor in segs:
            alt = hh * v / ymax
            y -= alt
            out.append(rect(x - 1.1, y, 2.2, alt, cor))
    out.append(linha(esq, topo + hh, esq + w, topo + hh, INK, 1.2))
    out.append("</svg>")
    return "".join(out)


# ------------------------------------------------------------------ hemiciclo


def hemiciclo(
    blocos: list[tuple[str, int, str]],
    titulo: str,
    desc: str,
    largura: float = 760,
    fileiras: int | None = None,
) -> str:
    """Hemiciclo genérico. Bloco: (cor, assentos, rótulo), da esquerda para a direita."""
    n = sum(q for _, q, _ in blocos)
    fileiras = fileiras or max(3, round(math.sqrt(n / 4.5)))
    cx, cy = largura / 2, largura / 2 - 6
    r1 = largura / 2 - 14
    r0 = r1 * 0.38
    raios = [r0 + (r1 - r0) * i / (fileiras - 1) for i in range(fileiras)]
    soma = sum(raios)
    qtd = [round(n * r / soma) for r in raios]
    qtd[-1] += n - sum(qtd)
    assentos = []
    for r, q in zip(raios, qtd, strict=True):
        for k in range(q):
            ang = math.pi * (1 - k / max(q - 1, 1))
            assentos.append((-ang, r, cx + r * math.cos(ang), cy - r * math.sin(ang)))
    assentos.sort(key=lambda s: (round(s[0], 6), s[1]))
    raio_assento = min(
        (r1 - r0) / (fileiras - 1) * 0.42, math.pi * r0 / max(qtd[0], 1) * 0.42
    )
    h = cy + 14
    out = [abre(largura, h, titulo, desc)]
    i = 0
    for cor, q, rot in blocos:
        grupo = []
        for _ in range(q):
            _, _, x, y = assentos[i]
            i += 1
            grupo.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{raio_assento:.1f}" fill="{cor}"/>'
            )
        out.append(f"<g><title>{escape(rot)}: {q}</title>{''.join(grupo)}</g>")
    out.append(
        txt(cx, cy - 8, str(n), 44, INK, "middle", "500", "Fraunces, Georgia, serif")
    )
    out.append(txt(cx, cy + 10, "assentos", 13, MUTED, "middle"))
    out.append("</svg>")
    return "".join(out)


# ------------------------------------------------------------------ cascata


def cascata(
    passos: list[tuple[str, float, str]],
    titulo: str,
    desc: str,
    largura: float = 820,
    altura: float = 340,
    unidade: str = " pp",
) -> str:
    """Cascata. Passo: (rótulo, valor, tipo) com tipo 'total' ou 'delta'."""
    esq, topo, base = 60, 30, 70
    w = largura - esq - 20
    hh = altura - topo - base
    nivel, pontos = 0.0, []
    for rot, v, tipo in passos:
        if tipo == "total":
            pontos.append((rot, 0.0, v, tipo, v))
            nivel = v
        else:
            pontos.append((rot, nivel, nivel + v, tipo, v))
            nivel += v
    vals = [a for _, a, _, _, _ in pontos] + [b for _, _, b, _, _ in pontos]
    vmin, vmax = min(0.0, *vals), max(0.0, *vals)
    pad = (vmax - vmin) * 0.12 or 1

    def Y(v):
        return topo + hh * (1 - (v - (vmin - pad)) / ((vmax + pad) - (vmin - pad)))

    out = [abre(largura, altura, titulo, desc)]
    out.append(linha(esq, Y(0), largura - 20, Y(0), INK, 1.2))
    out.append(txt(esq - 6, Y(0) + 4, "0", 12, MUTED, "end", family=MONO))
    col = w / len(pontos)
    for k, (rot, a, b, tipo, v) in enumerate(pontos):
        x = esq + k * col + col * 0.18
        bw = col * 0.64
        y1, y2 = sorted((Y(a), Y(b)))
        cor = INK if tipo == "total" else (FLAVIO if v < 0 else LULA)
        out.append(rect(x, y1, bw, max(y2 - y1, 1.5), cor))
        out.append(
            txt(x + bw / 2, y1 - 7, _fmt(v, 2, unidade), 13, INK, "middle", "600", MONO)
        )
        for j, parte in enumerate(_quebra(rot, 18)):
            out.append(
                txt(x + bw / 2, altura - base + 22 + 15 * j, parte, 12.5, INK, "middle")
            )
        if k + 1 < len(pontos):
            out.append(
                linha(x + bw, Y(b), x + col, Y(b), MUTED, 1, ' stroke-dasharray="3 3"')
            )
    out.append("</svg>")
    return "".join(out)


def _quebra(s: str, n: int) -> list[str]:
    palavras, linhas_, atual = s.split(), [], ""
    for pw in palavras:
        if len(atual) + len(pw) + 1 > n and atual:
            linhas_.append(atual)
            atual = pw
        else:
            atual = f"{atual} {pw}".strip()
    if atual:
        linhas_.append(atual)
    return linhas_[:3]


# ------------------------------------------------------------------ dispersão


def dispersao(
    grupos: list[tuple[str, str, list[tuple[float, float]]]],
    xlim: tuple[float, float],
    ylim: tuple[float, float],
    passo: float,
    rotulo_x: str,
    rotulo_y: str,
    titulo: str,
    desc: str,
    largura: float = 760,
    altura: float = 560,
    diagonal: bool = True,
    raio: float = 2.4,
    destaques: list[tuple[float, float, str]] | None = None,
    fmt_x=None,
    passo_y: float | None = None,
) -> str:
    """Nuvem de pontos leve: cada grupo vira um só <path> de traços de comprimento zero."""
    esq, topo, base, dirm = 64, 34, 52, 20
    w = largura - esq - dirm
    hh = altura - topo - base

    def X(v):
        return esq + w * (v - xlim[0]) / (xlim[1] - xlim[0])

    def Y(v):
        return topo + hh * (1 - (v - ylim[0]) / (ylim[1] - ylim[0]))

    out = [abre(largura, altura, titulo, desc)]
    out.append(legenda_linha([(n, c) for n, c, _ in grupos], esq, 16))
    t = xlim[0]
    while t <= xlim[1] + 1e-9:
        out.append(linha(X(t), topo, X(t), topo + hh, LINE, 1))
        rot_x = fmt_x(t) if fmt_x else num(t, 0)
        out.append(txt(X(t), topo + hh + 18, rot_x, 12, MUTED, "middle", family=MONO))
        t += passo
    t = ylim[0]
    passo_y = passo_y or passo
    while t <= ylim[1] + 1e-9:
        out.append(linha(esq, Y(t), esq + w, Y(t), LINE, 1))
        out.append(txt(esq - 8, Y(t) + 4, num(t, 0), 12, MUTED, "end", family=MONO))
        t += passo_y
    if diagonal:
        a = max(xlim[0], ylim[0])
        b = min(xlim[1], ylim[1])
        out.append(linha(X(a), Y(a), X(b), Y(b), INK, 1.2, ' stroke-dasharray="5 4"'))
    for _, cor, pts in grupos:
        d = "".join(
            f"M{X(x):.1f} {Y(y):.1f}h0"
            for x, y in pts
            if xlim[0] <= x <= xlim[1] and ylim[0] <= y <= ylim[1]
        )
        out.append(
            f'<path d="{d}" stroke="{cor}" stroke-width="{2 * raio}" '
            'stroke-linecap="round" opacity="0.55" fill="none"/>'
        )
    for x, y, rot in destaques or []:
        out.append(
            f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="4.5" fill="none" stroke="{INK}" stroke-width="1.5"/>'
        )
        out.append(txt(X(x) + 7, Y(y) - 6, rot, 12, INK, weight="600"))
    out.append(txt(esq + w / 2, altura - 10, rotulo_x, 13, INK, "middle"))
    out.append(
        txt(
            16,
            topo + hh / 2,
            rotulo_y,
            13,
            INK,
            "middle",
            extra=f' transform="rotate(-90 16 {topo + hh / 2:.1f})"',
        )
    )
    out.append("</svg>")
    return "".join(out)


# ------------------------------------------------------------------ pesquisas


def pontos_setas(
    linhas_: list[tuple[str, float, float | None]],
    titulo: str,
    desc: str,
    largura: float = 820,
    rotulo_w: float = 190,
) -> str:
    """Erro de cada pesquisa na diferença L−F: ponto publicado, seta até o reponderado."""
    passo, topo = 26, 52
    h = topo + passo * len(linhas_) + 40
    vals = [abs(v) for _, a, b in linhas_ for v in (a, b) if v is not None]
    vmax = max(vals, default=1) * 1.1
    x0 = rotulo_w + (largura - rotulo_w - 30) / 2
    meia = (largura - rotulo_w - 60) / 2

    def X(v):
        return x0 + meia * v / vmax

    out = [abre(largura, h, titulo, desc)]
    out.append(
        '<defs><marker id="seta-rep" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        f'<path d="M0,0L10,5L0,10z" fill="{INK}"/></marker></defs>'
    )
    out.append(
        legenda_linha(
            [("Publicado", INK), ("Reponderado por renda", CINZA)], rotulo_w, 16
        )
    )
    out.append(txt(x0 - 8, 40, "superestimou Flávio", 12, FLAVIO, "end", "600"))
    out.append(txt(x0 + 8, 40, "superestimou Lula", 12, LULA, weight="600"))
    passo_tick = _passo_bonito(vmax)
    t = -math.floor(vmax / passo_tick) * passo_tick
    while t <= vmax + 1e-9:
        out.append(linha(X(t), topo - 4, X(t), h - 30, LINE, 1))
        out.append(txt(X(t), h - 12, num(t, 0), 12, MUTED, "middle", family=MONO))
        t += passo_tick
    out.append(linha(x0, topo - 4, x0, h - 30, INK, 1.6))
    out.append(txt(x0, h - 26, "urna", 11.5, INK, "middle", "700"))
    for k, (rot, a, b) in enumerate(linhas_):
        y = topo + k * passo + passo / 2
        out.append(txt(rotulo_w - 10, y + 4, rot, 13, INK, "end"))
        if b is not None and abs(X(b) - X(a)) > 6:
            out.append(
                f'<line x1="{X(a):.1f}" y1="{y:.1f}" x2="{X(b):.1f}" y2="{y:.1f}" '
                f'stroke="{INK}" stroke-width="1.4" marker-end="url(#seta-rep)"/>'
            )
        if b is not None:
            out.append(f'<circle cx="{X(b):.1f}" cy="{y:.1f}" r="4.5" fill="{CINZA}"/>')
        out.append(f'<circle cx="{X(a):.1f}" cy="{y:.1f}" r="5.5" fill="{INK}"/>')
    out.append("</svg>")
    return "".join(out)
