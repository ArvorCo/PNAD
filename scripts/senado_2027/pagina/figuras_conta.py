"""Figuras da conta do Senado de 2027: distribuição de votos, pivôs e placar dos cenários."""

from __future__ import annotations

import math

from .figuras_base import (
    CHAVE_SIM,
    GOLD,
    INK,
    LIMIAR,
    MUTED,
    NEUTRO,
    RED,
    ROTULO_ALVO,
    ROTULO_CENARIO,
    TEAL,
    TEAL_CLARO,
    esc,
    figura,
    fmt,
    ocupantes,
    pct,
    sigla,
    sim,
    svg,
    txt,
)

# 3. Distribuição simulada dos votos


def _painel_hist(
    s: dict,
    titulo: str,
    quorum: int,
    x: float,
    y: float,
    w: float,
    h: float,
    xmin: int,
    ident: str,
) -> str:
    hist = s["histograma"]
    xmax = 81
    n_bins = xmax - xmin + 1
    bw = w / n_bins
    topo = max(hist[xmin:]) or 1
    base_y = y + h

    def bx(v: float) -> float:
        return x + (v - xmin) * bw

    out = [txt(x, y - 46, titulo, 17, "start", 700)]
    total = sum(hist)
    for v in range(xmin, xmax + 1):
        cnt = hist[v]
        if not cnt:
            continue
        hh = h * cnt / topo
        cor = TEAL if v >= quorum else NEUTRO
        out.append(
            f'<rect x="{bx(v) + 0.4:.1f}" y="{base_y - hh:.1f}" width="{bw - 0.8:.1f}" '
            f'height="{hh:.1f}" fill="{cor}"><title>{v} votos: '
            f"{pct(100 * cnt / total, 1)} dos sorteios</title></rect>"
        )
    out.append(
        f'<line x1="{x}" x2="{x + w}" y1="{base_y}" y2="{base_y}" stroke="{INK}" '
        'stroke-width="1"/>'
    )
    for v in [*range(10 * math.ceil(xmin / 10), 71, 10), 81]:
        out.append(txt(bx(v) + bw / 2, base_y + 18, str(v), 14, "middle", cor=MUTED))
    out.append(txt(x + w / 2, base_y + 40, "votos sim", 14, "middle", cor=MUTED))
    # limiares
    for lim, anchor, dx in ((49, "end", -4), (54, "start", 4)):
        lx = bx(lim)
        out.append(
            f'<line class="sn27-limiar" data-limiar="{lim}" x1="{lx:.1f}" '
            f'x2="{lx:.1f}" y1="{y - 22}" y2="{base_y}" stroke="{INK}" '
            'stroke-width="2" stroke-dasharray="4 3"/>'
        )
        out.append(txt(lx + dx, y - 26, str(lim), 15, anchor, 700))
    # média
    mx = bx(s["media"]) + bw / 2
    out.append(
        f'<line x1="{mx:.1f}" x2="{mx:.1f}" y1="{y + 4}" y2="{base_y}" '
        f'stroke="{GOLD}" stroke-width="2.4"/>'
    )
    # p5 a p95
    p5x, p95x = bx(s["p5"]) + bw / 2, bx(s["p95"]) + bw / 2
    yb = base_y + 56
    out.append(
        f'<line x1="{p5x:.1f}" x2="{p95x:.1f}" y1="{yb}" y2="{yb}" stroke="{INK}" '
        'stroke-width="2"/>'
        f'<line x1="{p5x:.1f}" x2="{p5x:.1f}" y1="{yb - 6}" y2="{yb + 6}" '
        f'stroke="{INK}" stroke-width="2"/>'
        f'<line x1="{p95x:.1f}" x2="{p95x:.1f}" y1="{yb - 6}" y2="{yb + 6}" '
        f'stroke="{INK}" stroke-width="2"/>'
    )
    out.append(
        txt(
            (p5x + p95x) / 2,
            yb + 22,
            f"9 em 10 sorteios: {s['p5']} a {s['p95']}",
            14,
            "middle",
        )
    )
    # caixa de probabilidades no canto mais vazio (o lado esquerdo)
    tx = x + 4
    out.append(txt(tx, y + 8, f"média {fmt(s['media'], 1)}", 15, "start", 700, GOLD))
    out.append(txt(tx, y + 30, f"≥ 49: {pct(s['P49'])}", 15, "start", 700))
    out.append(txt(tx, y + 50, f"≥ 54: {pct(s['P54'])}", 15, "start", 700))
    return f'<g class="sn27-hist" data-alvo="{ident}">' + "".join(out) + "</g>"


def distribuicao_votos(data: dict, cenario: str = "flavio") -> str:
    base = sim(data, cenario)
    pec, imp = base["pec"], base["imp"]
    primeiro = min(
        next(i for i, v in enumerate(pec["histograma"]) if v),
        next(i for i, v in enumerate(imp["histograma"]) if v),
    )
    xmin = max(0, 10 * (primeiro // 10))
    tit_pec = "PEC que limite o STF (quórum 49)"
    tit_imp = "Impeachment de Moraes (quórum 54)"
    largo = _painel_hist(
        pec, tit_pec, 49, 30, 80, 420, 250, xmin, "pec"
    ) + _painel_hist(imp, tit_imp, 54, 510, 80, 420, 250, xmin, "imp")
    estreito = _painel_hist(pec, tit_pec, 49, 14, 80, 352, 220, xmin, "pec") + (
        '<g transform="translate(0 410)">'
        + _painel_hist(imp, tit_imp, 54, 14, 80, 352, 220, xmin, "imp")
        + "</g>"
    )
    rotulo = (
        f"Distribuição de 20.000 sorteios, {ROTULO_CENARIO[cenario]}. PEC: média "
        f"{fmt(pec['media'], 1)} votos, 49 ou mais em {pct(pec['P49'])}. "
        f"Impeachment: média {fmt(imp['media'], 1)}, 54 ou mais em {pct(imp['P54'])}."
    )
    estilo = (
        "<style>.sn27-fig svg.sn27-dist-estreito{display:none}"
        "@media (max-width:719px){.sn27-fig svg.sn27-dist-largo{display:none}"
        ".sn27-fig svg.sn27-dist-estreito{display:block}}</style>"
    )
    conteudo = (
        estilo
        + svg(960, 420, rotulo, largo, "sn27-dist-largo")
        + svg(380, 820, rotulo, estreito, "sn27-dist-estreito")
    )
    n = data["simulacao"]["parametros"]["sorteios"]
    legenda = (
        f"Em {fmt(n)} sorteios do {ROTULO_CENARIO[cenario]}, a PEC reúne em média "
        f"{fmt(pec['media'], 1)} votos e chega a 49 em {pct(pec['P49'])} deles; o "
        f"impeachment reúne {fmt(imp['media'], 1)} e chega a 54 em {pct(imp['P54'])}. "
        "Barras verdes: sorteios que alcançam o quórum da conta. Linha dourada: média. "
        "O traço embaixo cobre 9 em 10 sorteios. Os sorteios não são independentes: "
        "um choque comum por bloco e outro nacional fazem os senadores errarem juntos."
    )
    return figura("sn27-fig-dist", conteudo, legenda, f"distribuicao-{cenario}")


# 8. Pivôs


def pivos(data: dict, cenario: str = "flavio", alvo: str = "C_imp") -> str:
    lista = sorted(
        sim(data, cenario)["pivos"][CHAVE_SIM[alvo]],
        key=lambda p: (-p["sobe_pp"], -p["decisivo_pp"]),
    )
    por_slug = {p["slug"]: p for p in ocupantes(data, cenario)}
    lim = LIMIAR[alvo]
    s = sim(data, cenario)[CHAVE_SIM[alvo]]
    p_ref = s[f"P{lim}"]
    W = 960.0
    passo = 28.0
    topo = 84.0
    H = topo + passo * len(lista) + 20
    centro = 700.0
    maximo = max(max(p["sobe_pp"], p["cai_pp"]) for p in lista) or 1
    escala = 180.0 / maximo
    corpo = [
        txt(20, 28, f"Chance de {lim} votos hoje: {pct(p_ref, 1)}", 17, "start", 700),
        txt(centro - 8, 62, "cai se vota não", 14, "end", cor=MUTED),
        txt(centro + 8, 62, "sobe se vota sim", 14, "start", cor=MUTED),
        txt(20, 62, "senador", 14, cor=MUTED),
        txt(300, 62, "partido-UF", 14, cor=MUTED),
        txt(450, 62, "C", 14, "end", cor=MUTED),
    ]
    for i, pv in enumerate(lista):
        y = topo + i * passo
        pessoa = por_slug.get(pv["slug"])
        sig = sigla(pessoa) if pessoa else pv["uf"]
        if i % 2 == 0:
            corpo.append(
                f'<rect x="10" y="{y - 4:.1f}" width="{W - 20}" height="{passo:.0f}" '
                'fill="#ece8dc"/>'
            )
        corpo.append(txt(20, y + 15, pv["nome"], 14, "start", 700))
        corpo.append(txt(300, y + 15, sig, 13, cor=MUTED))
        corpo.append(txt(450, y + 15, fmt(pv["C"]), 14, "end"))
        wc = pv["cai_pp"] * escala
        ws = pv["sobe_pp"] * escala
        corpo.append(
            f'<rect x="{centro - wc:.1f}" y="{y + 2:.1f}" width="{wc:.1f}" height="16" '
            f'fill="{RED}"><title>{esc(pv["nome"])} votando não: a chance cai '
            f"{fmt(pv['cai_pp'], 1)} pontos</title></rect>"
        )
        corpo.append(
            f'<rect x="{centro:.1f}" y="{y + 2:.1f}" width="{ws:.1f}" height="16" '
            f'fill="{TEAL}"><title>{esc(pv["nome"])} votando sim: a chance sobe '
            f"{fmt(pv['sobe_pp'], 1)} pontos</title></rect>"
        )
        corpo.append(
            txt(centro - wc - 6, y + 15, f"−{fmt(pv['cai_pp'], 1)}", 13, "end")
        )
        corpo.append(
            txt(centro + ws + 6, y + 15, f"+{fmt(pv['sobe_pp'], 1)}", 13, "start")
        )
    corpo.append(
        f'<line x1="{centro}" x2="{centro}" y1="{topo - 8}" y2="{H - 14}" '
        f'stroke="{INK}" stroke-width="1.4"/>'
    )
    p1 = lista[0]
    rotulo = (
        f"Gráfico tornado de {len(lista)} pivôs da conta de {lim} votos, "
        f"{ROTULO_CENARIO[cenario]}: quanto a chance sobe se cada um vota sim e "
        "quanto cai se vota não."
    )
    legenda = (
        f"Os {len(lista)} senadores cujo voto mais move a chance de {lim} votos no "
        f"{ROTULO_ALVO[alvo]}, {ROTULO_CENARIO[cenario]}, que hoje é de "
        f"{pct(p_ref, 1)}. Se {p1['nome']} vota sim com certeza, a chance sobe "
        f"{fmt(p1['sobe_pp'], 1)} pontos; se vota não, cai {fmt(p1['cai_pp'], 1)}. "
        "Pivô é quem tem C no meio da régua: os votos certos dos dois lados não "
        "movem a conta."
    )
    return figura(
        "sn27-fig-wide sn27-fig-pivos",
        svg(W, H, rotulo, "".join(corpo), "sn27-svg-pivos"),
        legenda,
        f"pivos-{CHAVE_SIM[alvo]}-{cenario}",
    )


# 9. Placar dos cenários


def placar_cenarios(data: dict) -> str:
    W = 960.0
    linhas = [
        ("flavio", "C_pec", "PEC", "governo Flávio"),
        ("flavio", "C_imp", "Impeachment", "governo Flávio"),
        ("lula", "C_pec", "PEC", "governo Lula"),
        ("lula", "C_imp", "Impeachment", "governo Lula"),
    ]
    passo = 104.0
    H = 30 + passo * len(linhas)
    x0, x1 = 330.0, 920.0

    def bx(v: float) -> float:
        return x0 + (x1 - x0) * v / 81

    corpo = [
        "<defs>"
        '<pattern id="sn27-hachura-placar" width="7" height="7" '
        'patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
        f'<rect width="7" height="7" fill="{TEAL_CLARO}"/>'
        f'<line x1="0" y1="0" x2="0" y2="7" stroke="{INK}" stroke-width="2"/>'
        "</pattern></defs>"
    ]
    frases = []
    for i, (cen, alvo, nome, rot_cen) in enumerate(linhas):
        s = sim(data, cen)[CHAVE_SIM[alvo]]
        lim = LIMIAR[alvo]
        p = s[f"P{lim}"]
        y = 30 + i * passo
        corpo.append(txt(20, y + 34, fmt(s["media"], 1), 48, "start", 600))
        corpo.append(txt(180, y + 18, nome, 17, "start", 700))
        corpo.append(txt(180, y + 40, rot_cen, 14, cor=MUTED))
        corpo.append(txt(180, y + 62, f"≥ {lim}: {pct(p)}", 15, "start", 700))
        ty = y + 14
        corpo.append(
            f'<rect x="{x0}" y="{ty}" width="{x1 - x0}" height="30" fill="#e4e1d3"/>'
        )
        corpo.append(
            f'<rect x="{x0}" y="{ty + 8}" width="{bx(s["media"]) - x0:.1f}" '
            f'height="14" fill="{TEAL}"><title>{nome}, {rot_cen}: '
            f"{fmt(s['media'], 1)} votos esperados</title></rect>"
        )
        corpo.append(
            f'<rect x="{bx(s["p5"]):.1f}" y="{ty}" '
            f'width="{bx(s["p95"]) - bx(s["p5"]):.1f}" height="30" '
            f'fill="url(#sn27-hachura-placar)" fill-opacity="0.55" stroke="{INK}" '
            f'stroke-width="1"><title>9 em 10 sorteios entre {s["p5"]} e {s["p95"]} '
            "votos</title></rect>"
        )
        lx = bx(lim)
        corpo.append(
            f'<line class="sn27-limiar" data-limiar="{lim}" x1="{lx:.1f}" '
            f'x2="{lx:.1f}" y1="{ty - 8}" y2="{ty + 38}" stroke="{INK}" '
            'stroke-width="3"/>'
        )
        corpo.append(txt(lx, ty - 12, f"quórum {lim}", 13, "middle", 700))
        corpo.append(txt(x0, ty + 54, "0", 13, "middle", cor=MUTED))
        corpo.append(txt(x1, ty + 54, "81", 13, "middle", cor=MUTED))
        corpo.append(
            txt(
                (bx(s["p5"]) + bx(s["p95"])) / 2,
                ty + 54,
                f"{s['p5']} a {s['p95']}",
                13,
                "middle",
                cor=MUTED,
            )
        )
        frases.append(
            f"{nome} no {rot_cen}: {fmt(s['media'], 1)} votos, {lim} ou mais em "
            f"{pct(p)} dos sorteios"
        )
    rotulo = "Placar esperado: " + "; ".join(frases) + "."
    imp_max = max(sim(data, c)["imp"]["media"] for c in ("flavio", "lula"))
    pec_min = min(sim(data, c)["pec"]["media"] for c in ("flavio", "lula"))
    leitura = []
    if pec_min >= 49:
        leitura.append("a PEC passa do quórum na média dos dois governos")
    if imp_max < 54:
        leitura.append(
            "o impeachment fica abaixo de 54 na média mesmo no cenário mais favorável"
        )
    legenda = (
        "Número grande: votos esperados de 81. Barra verde até o valor esperado; "
        "caixa hachurada: 9 em 10 sorteios; traço preto: o quórum. "
        + "; ".join(frases)
        + "."
        + (" Na leitura: " + ", e ".join(leitura) + "." if leitura else "")
    )
    return figura(
        "sn27-fig-wide sn27-fig-placar",
        svg(W, H, rotulo, "".join(corpo), "sn27-svg-placar"),
        legenda,
        "placar-cenarios",
    )
