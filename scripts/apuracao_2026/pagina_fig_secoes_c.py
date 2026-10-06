"""Figuras do capítulo 12 no nível da seção eleitoral, parte 3: `clusters_secoes`.

Dispersão da amostra de seções nos dois primeiros componentes principais, com a
cor do grupo da mistura gaussiana (ou da região), os centros rotulados, as 200
seções menos prováveis com contorno e a elipse do grupo mais atípico pelo centro
e pela covariância de todas as seções dele (`pca.elipses`, dois desvios). Ao
lado, o painel dos grupos, com a barra do eleitorado de cada um (Lula, Flávio,
terceiros, brancos, nulos e abstenção) e a caixa "O que não deu certo", com os
números da versão de 15 partes; abaixo, a tabela das 20 amostras do grupo mais
atípico. Tudo sai de `secoes.json`.
"""

from __future__ import annotations

import math
from html import escape

from .pagina_comum import CINZA, FLAVIO, LULA, OUTROS, inteiro, num, tabela
from .pagina_fig_base import (
    COR_REGIAO,
    GRADE,
    INK,
    LIMA,
    MUTED,
    REGIOES,
    Tips,
    botoes,
    chip,
    escala,
    figura_html,
    legenda_html,
    ln,
    nome_bonito,
    registra,
    svg_abre,
    t,
    ticks,
)
from .pagina_fig_secoes import (
    CLUSTER_COR,
    grupos_extenso,
    nota_cobertura,
    regiao_da_uf,
    rotulo_cluster,
    secoes,
)

CINZA_ELIPSE = "#5f6773"
PARTES_BARRA = [  # (chave no centro, nome, cor)
    ("lula", "Lula", LULA),
    ("flavio", "Flávio", FLAVIO),
    ("terceiros", "terceiros (fora do modelo)", OUTROS),
    ("brancos", "brancos", "#d9d2bf"),
    ("nulos", "nulos", CINZA),
    ("abstencao", "abstenção", "#c9a43a"),
]
ESTILO_PAINEL = (
    "<style>#fig-clusters_secoes .cl-barra{display:flex;height:12px;margin:5px 0 3px;"
    "border:1px solid var(--line)}"
    "#fig-clusters_secoes .cl-barra>span{display:block;height:100%}"
    "#fig-clusters_secoes .cl-leg{list-style:none;display:flex;flex-wrap:wrap;gap:2px 12px;"
    "padding:0;margin:0 0 10px;font:12.5px/1.5 var(--sans)}"
    "#fig-clusters_secoes .cl-leg li{margin:0;padding:0;border:0;font:inherit}"
    "#fig-clusters_secoes .cl-leg i{display:inline-block;width:10px;height:10px;"
    "margin-right:5px;vertical-align:-1px;border:1px solid #9a9c94}"
    "#fig-clusters_secoes .cl-falha{margin:6px 0 0;padding:10px 12px;"
    "border-left:4px solid var(--gold);background:#efe8d4;font:13.5px/1.5 var(--sans)}"
    "#fig-clusters_secoes .cl-falha h4{margin:0 0 4px}"
    "#fig-clusters_secoes .cl-falha p{margin:0 0 6px;font:inherit}</style>"
)


def elipse_cov(
    mx: float, my: float, sxx: float, syy: float, sxy: float
) -> tuple[float, float, float, float, float]:
    """Centro, semieixos (2 desvios) e ângulo em graus a partir da covariância."""
    tr, det = sxx + syy, sxx * syy - sxy * sxy
    disc = math.sqrt(max(tr * tr / 4 - det, 0))
    l1, l2 = tr / 2 + disc, max(tr / 2 - disc, 0)
    ang = (
        math.degrees(math.atan2(l1 - sxx, sxy))
        if sxy
        else (0.0 if sxx >= syy else 90.0)
    )
    return mx, my, 2 * math.sqrt(l1), 2 * math.sqrt(l2), ang


def _elipse(
    pts: list[tuple[float, float]],
) -> tuple[float, float, float, float, float] | None:
    """Centro, semieixos (2 desvios) e ângulo em graus da nuvem de pontos."""
    if len(pts) < 3:
        return None
    n = len(pts)
    mx = sum(p[0] for p in pts) / n
    my = sum(p[1] for p in pts) / n
    sxx = sum((p[0] - mx) ** 2 for p in pts) / n
    syy = sum((p[1] - my) ** 2 for p in pts) / n
    sxy = sum((p[0] - mx) * (p[1] - my) for p in pts) / n
    return elipse_cov(mx, my, sxx, syy, sxy)


def topo_elipse(
    cx: float, cy: float, rx: float, ry: float, ang: float
) -> tuple[float, float]:
    """Ponto mais alto da borda da elipse girada (coordenadas de tela)."""
    a = math.radians(ang)
    h = math.hypot(rx * math.sin(a), ry * math.cos(a))
    if h == 0:
        return cx, cy
    return cx + math.sin(a) * math.cos(a) * (ry * ry - rx * rx) / h, cy - h


def _elipse_grupo(P: dict, k: int, X, Y, pontos: list[dict]):
    """Elipse do grupo pelo centro e pela covariância de todas as seções dele,
    projetadas no plano (`pca.elipses`); sem esse campo, pela amostra da figura."""
    e = next((e for e in P.get("elipses") or [] if e["cluster"] == k), None)
    if e is None:
        return _elipse(
            [
                (X(p["x"]), Y(p["y"]))
                for p in pontos
                if p["cluster"] == k and not p.get("top200")
            ]
        )
    ax = X(1.0) - X(0.0)
    ay = Y(0.0) - Y(1.0)
    (cxx, cxy), (_, cyy) = e["cov"]
    return elipse_cov(
        X(e["x"]), Y(e["y"]), ax * ax * cxx, ay * ay * cyy, -ax * ay * cxy
    )


def _larg_chip(texto: str, size: float = 13) -> float:
    """Largura da caixa de `chip` (mesma conta de `pagina_fig_base.chip`)."""
    return 0.53 * size * len(texto) + 12


def _colide(
    a: tuple[float, float, float, float], b: tuple[float, float, float, float]
) -> bool:
    return not (
        a[0] + a[2] + 4 <= b[0]
        or b[0] + b[2] + 4 <= a[0]
        or a[1] + a[3] + 3 <= b[1]
        or b[1] + b[3] + 3 <= a[1]
    )


def _casa_menos_provaveis(C: dict, pontos: list[dict]) -> dict[int, dict]:
    """Índice do ponto top200 para o registro de `menos_provaveis`, quando dá para casar."""
    mp = C.get("menos_provaveis") or []
    top = [i for i, p in enumerate(pontos) if p.get("top200")]
    out: dict[int, dict] = {}
    if mp and "x" in mp[0] and "y" in mp[0]:
        pos = {(round(m["x"], 3), round(m["y"], 3)): m for m in mp}
        for i in top:
            m = pos.get((round(pontos[i]["x"], 3), round(pontos[i]["y"], 3)))
            if m:
                out[i] = m
        return out
    for i, m in zip(top, mp, strict=False):
        p = pontos[i]
        if p.get("uf") == m.get("uf") and p.get("cluster") == m.get("cluster"):
            out[i] = m
    return out


def centro_eleitorado(c: dict) -> dict:
    """Centro do grupo em % do eleitorado, com os terceiros (o que falta)."""
    out = dict(c.get("centro_pct_eleitorado") or {})
    if c.get("terceiros_pct_eleitorado") is not None:
        out["terceiros"] = c["terceiros_pct_eleitorado"]
    return out


def barra_eleitorado(c: dict) -> str:
    """Barra de 100% do eleitorado do grupo, em segmentos `display:block`."""
    ce = centro_eleitorado(c)
    segs = "".join(
        f'<span title="{escape(nome)} {num(ce[k], 1)}%" '
        f'style="flex:{ce[k]:.3f} 1 0;background:{cor}"></span>'
        for k, nome, cor in PARTES_BARRA
        if ce.get(k)
    )
    return f'<div class="cl-barra" role="img" aria-label="Eleitorado do grupo">{segs}</div>'


def caixa_falha(C: dict, nomes: dict) -> str:
    """'O que não deu certo': as duas tentativas em log-razão, em números do JSON."""
    var = C.get("variantes") or {}
    q, c5 = var.get("quinze_partes"), var.get("cinco_partes_clr")
    if not q and not c5:
        return ""
    paras = []
    if q:
        nuv = [
            s
            for s in (q.get("nuvens") or {}).get("separacao") or []
            if (s.get("acerto_balanceado_pct") or 0) >= 90
        ]
        frase_nuv = (
            " As nuvens da projeção eram seções com e sem voto em "
            + " e em ".join(escape(nomes.get(s["feature"], s["feature"])) for s in nuv)
            + "."
            if nuv
            else ""
        )
        paras.append(
            f"<p><b>1. {len(q.get('features') or [])} partes em log-razão.</b> "
            f"{num(q['zeros_substituidos_pct'], 1)}% das células eram zero, e o degrau de 0,0001 para um voto separou "
            f"as seções por quem tinha ou não voto em candidatura nanica. V de Cramér com a região: "
            f"{num(q['cramer_v_regiao'], 2)}.{frase_nuv}</p>"
        )
    if c5:
        med = c5.get("mediana_votos_por_secao") or {}
        art = [g for g in c5.get("grupos") or [] if g.get("artefato")]
        quais = ", ".join(escape(g["artefato"]) for g in art)
        conv = c5.get("convergencia") or {}
        paras.append(
            "<p><b>2. Cinco partes em log-razão.</b> Com mediana de "
            f"{num(med.get('brancos') or 0, 0)} brancos e {num(med.get('nulos') or 0, 0)} nulos por seção, o log "
            f"deu a eles o mesmo peso de Lula e Flávio: {grupos_extenso(len(art))} dos cinco grupos foram "
            f"artefatos ({quais}). V de Cramér: {num(c5['cramer_v_regiao'], 2)}; "
            f"{conv.get('no_maximo', 's/d')} de {conv.get('total', 's/d')} partidas no máximo.</p>"
        )
    paras.append(
        "<p><b>3. Proporções do eleitorado, sem log</b>, a versão publicada: "
        f"V de Cramér {num(C['cramer_v_regiao'], 2)}.{_ainda(C)}</p>"
    )
    return (
        '<div class="cl-falha"><h4>O que não deu certo</h4>' + "".join(paras) + "</div>"
    )


def _ainda(C: dict) -> str:
    """Quais grupos do modelo publicado ainda são artefato da contagem inteira."""
    art = [c for c in C["componentes"] if c.get("artefato")]
    if not art:
        return " Nenhum grupo é artefato da contagem."
    itens = [f"o {c['id'] + 1} ({escape(c['artefato'])})" for c in art]
    lista_ = ", ".join(itens[:-1]) + " e " + itens[-1] if len(itens) > 1 else itens[0]
    quantos = (
        "um grupo ainda é artefato"
        if len(art) == 1
        else f"{grupos_extenso(len(art))} grupos ainda são artefatos"
    )
    return f" Ainda assim, {quantos} da contagem inteira: {lista_}."


def _painel_clusters(S: dict) -> str:
    C = S["clusters"]
    nomes = {c["chave"]: c["nome"] for c in S.get("candidatos") or []}
    ma = C["mais_anomalo"]["id"]
    itens = []
    for c in C["componentes"]:
        cv = c["centro_pct_validos"]
        ce = centro_eleitorado(c)
        ufs = ", ".join(
            f"{u['uf']} {num(u['pct_do_cluster'], 1)}%" for u in c["ufs_top"][:3]
        )
        reg = c["regioes"][0] if c.get("regioes") else None
        marca = ' <em class="cl-anom">mais atípico</em>' if c["id"] == ma else ""
        eleit = ", ".join(
            f"{nome.split(' (')[0]} {num(ce[k], 1)}%"
            for k, nome, _ in PARTES_BARRA
            if ce.get(k) is not None
        )
        itens.append(
            f'<li><span class="sw" style="background:{CLUSTER_COR[c["id"] % len(CLUSTER_COR)]}"></span>'
            f"<b>Grupo {c['id'] + 1}: {escape(c['rotulo'])}</b>{marca}"
            f"<span>{inteiro(c['secoes'])} seções ({num(c['pct_secoes'], 1)}%)</span>"
            + barra_eleitorado(c)
            + f"<span>Eleitorado: {escape(eleit)}</span>"
            f"<span>Válidos: Lula {num(cv['lula'], 1)}%, Flávio {num(cv['flavio'], 1)}%, outros {num(cv['outros'], 1)}%</span>"
            f"<span>UFs: {escape(ufs)}</span>"
            + (
                f"<span>Região dominante: {escape(reg['regiao'])} ({num(reg['pct_do_cluster'], 1)}%)</span>"
                if reg
                else ""
            )
            + "</li>"
        )
    leg = "".join(
        f'<li><i style="background:{cor}"></i>{escape(nome)}</li>'
        for _, nome, cor in PARTES_BARRA
    )
    return (
        f'<div class="cl-painel">{ESTILO_PAINEL}<h4>Os {grupos_extenso(C["k"])} grupos</h4>'
        f'<ul class="cl-leg" aria-label="Partes da barra do eleitorado">{leg}</ul>'
        f'<ol>{"".join(itens)}</ol>{caixa_falha(C, nomes)}</div>'
    )


def _tabela_anomalo(S: dict) -> str:
    C = S["clusters"]
    am = C["mais_anomalo"]["amostras"]
    linhas = [
        [
            escape(a["uf"]),
            escape(nome_bonito(a["municipio"])),
            str(a["zona"]),
            str(a["secao"]),
            escape(nome_bonito(a.get("local") or "")),
            num(a.get("lula_pct"), 1),
            num(a.get("flavio_pct"), 1),
            inteiro(a.get("aptos")),
            inteiro(a.get("comparecimento")),
            escape(a.get("modelo_urna") or "s/d"),
            escape(a.get("explicacao") or ""),
        ]
        for a in am
    ]
    return tabela(
        [
            "UF",
            "Município",
            "Zona",
            "Seção",
            "Local",
            "Lula %",
            "Flávio %",
            "Aptos",
            "Votantes",
            "Modelo",
            "Explicação (regra declarada)",
        ],
        linhas,
        f"Amostras do grupo mais atípico ({escape(rotulo_cluster(S, C['mais_anomalo']['id']))}): "
        f"{escape(C['mais_anomalo'].get('criterio', '').rstrip('.'))}. Percentuais dos válidos.",
    )


@registra("clusters_secoes")
def clusters_secoes(d, **_op) -> str:
    S = secoes(d)
    C = S["clusters"]
    P = C["pca"]
    cols = P["colunas"]
    pontos = [dict(zip(cols, p, strict=False)) for p in P["pontos"]]
    if not pontos:
        raise ValueError("clusters.pca.pontos vazio")
    w, h = 780, 620
    x0, x1, y0, y1 = 70, 760, 24, 560
    xs = [p["x"] for p in pontos]
    ys = [p["y"] for p in pontos]
    pad_x = (max(xs) - min(xs)) * 0.04 or 1
    pad_y = (max(ys) - min(ys)) * 0.04 or 1
    lox, hix = min(xs) - pad_x, max(xs) + pad_x
    loy, hiy = min(ys) - pad_y, max(ys) + pad_y
    X = escala(lox, hix, x0, x1)
    Y = escala(loy, hiy, y1, y0)
    ve = P.get("variancia_explicada") or [None, None]
    ve_txt = ["s/d" if v is None else num(100 * v, 1) for v in ve[:2]]
    out = [
        svg_abre(
            w,
            h,
            f"{grupos_extenso(C['k']).capitalize()} grupos de seções na projeção em dois componentes principais",
            "Cada ponto é uma seção da amostra; cor pelo grupo da mistura gaussiana; as 200 seções menos prováveis "
            "têm contorno preto; a elipse cinza tracejada marca o grupo mais atípico (centro e covariância, dois desvios).",
            ' data-near="1"',
        )
    ]
    for v in ticks(lox, hix, 6):
        out.append(ln(X(v), y0, X(v), y1, GRADE, 0.8))
        out.append(t(X(v), y1 + 20, num(v, 1), 13, MUTED, "middle", mono=True))
    for v in ticks(loy, hiy, 6):
        out.append(ln(x0, Y(v), x1, Y(v), GRADE, 0.8))
        out.append(t(x0 - 8, Y(v) + 5, num(v, 1), 13, MUTED, "end", mono=True))
    out.append(
        t(
            (x0 + x1) / 2,
            h - 22,
            f"Componente principal 1 ({ve_txt[0]}% da variância)",
            14,
            INK,
            "middle",
            "600",
        )
    )
    yy = (y0 + y1) / 2
    out.append(
        t(
            20,
            yy,
            f"Componente 2 ({ve_txt[1]}%)",
            14,
            INK,
            "middle",
            "600",
            extra=f' transform="rotate(-90 20 {yy:.0f})"',
        )
    )
    ma = C["mais_anomalo"]["id"]
    el = _elipse_grupo(P, ma, X, Y, pontos)
    elipse_svg = ""
    if el:
        cx, cy, rx, ry, ang = el
        # por cima dos pontos, em cinza tracejado e quase sem preenchimento: não se
        # confunde com nenhuma das cores de grupo
        elipse_svg = (
            f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{max(ry, 6):.1f}" '
            f'transform="rotate({ang:.1f} {cx:.1f} {cy:.1f})" fill="{CINZA_ELIPSE}" '
            f'fill-opacity="0.06" stroke="{CINZA_ELIPSE}" stroke-width="2.2" '
            'stroke-dasharray="7 5" pointer-events="none"/>'
        )
    grupos: dict[tuple[int, str], list[str]] = {}
    casados = _casa_menos_provaveis(C, pontos)
    linhas, xy, top = [], [], []
    for i, p in enumerate(pontos):
        x, y = X(p["x"]), Y(p["y"])
        k = int(p["cluster"])
        reg = regiao_da_uf(p.get("uf"))
        if p.get("top200"):
            top.append((x, y, k, reg))
            raio = 4.5
        else:
            grupos.setdefault((k, reg), []).append(f"M{x:.0f} {y:.0f}h0")
            raio = 2
        linha = [f"Grupo {k + 1} · {p.get('uf') or 's/d'}"]
        if p.get("top200"):
            m = casados.get(i)
            linha.append("entre as 200 menos prováveis")
            if m:
                linha += [
                    nome_bonito(m["municipio"]),
                    f"{m['zona']} · {m['secao']}",
                    nome_bonito(m.get("local") or ""),
                    f"{num(m.get('lula_pct'), 1)} · {num(m.get('flavio_pct'), 1)}",
                    m.get("explicacao") or "",
                    num(m.get("loglik"), 1),
                ]
        linhas.append(linha)
        xy.append([round(x), round(y), raio])
    for (k, reg), segs in sorted(grupos.items()):
        out.append(
            f'<path d="{"".join(segs)}" stroke="{CLUSTER_COR[k % len(CLUSTER_COR)]}" data-as="regiao>{COR_REGIAO.get(reg, MUTED)}" '
            'stroke-width="4" stroke-linecap="round" stroke-opacity="0.5" fill="none"/>'
        )
    for x, y, k, reg in top:
        out.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="{CLUSTER_COR[k % len(CLUSTER_COR)]}" '
            f'data-af="regiao>{COR_REGIAO.get(reg, MUTED)}" stroke="{INK}" stroke-width="1.3"/>'
        )
    out.append(elipse_svg)
    caixas: list[tuple[float, float, float, float]] = []
    if el:
        ecx, ecy, erx, ery, eang = el
        rot_el = f"Grupo {ma + 1}, o mais atípico"
        larg_el = _larg_chip(rot_el)
        # sobre a borda, no ponto mais alto da elipse; preso ao quadro do gráfico
        bx_el, by_el = topo_elipse(ecx, ecy, erx, max(ery, 6), eang)
        y_el = min(max(by_el + 5, y0 + 17), y1 - 6)
        x_el = min(max(bx_el - larg_el / 2, x0 + 4), x1 - larg_el - 4)
        caixas.append((x_el, y_el - 15, larg_el, 21))
        rot_el_svg = f'<g pointer-events="none">{chip(x_el, y_el, rot_el, 13)}</g>'
    else:
        rot_el_svg = ""
    guias, cruzes, chips = [], [], []
    # a cruz de cada centro também é obstáculo: nenhum rótulo cobre o centro de outro grupo
    caixas += [(X(c["x"]) - 8, Y(c["y"]) - 8, 16, 16) for c in P["centros"]]
    for c in sorted(P["centros"], key=lambda c: Y(c["y"])):
        cx, cy = X(c["x"]), Y(c["y"])
        k = int(c["cluster"])
        texto = f"Grupo {k + 1}"
        larg = _larg_chip(texto)
        bx = cx - 12 - larg if cx > x1 - 120 else cx + 12
        by = cy - 12
        passo = -26
        while any(_colide((bx, by - 15, larg, 21), cx_) for cx_ in caixas):
            by += passo
            if by - 15 < y0:
                by, passo = cy + 30, 26
        caixas.append((bx, by - 15, larg, 21))
        guia = (
            ln(cx, cy, bx + (larg if bx < cx else 0), by - 4, INK, 0.8)
            if abs(by - (cy - 12)) > 1
            else ""
        )
        guias.append(guia)
        cruzes.append(
            ln(cx - 8, cy, cx + 8, cy, INK, 3) + ln(cx, cy - 8, cx, cy + 8, INK, 3)
        )
        chips.append(chip(bx, by, texto, 13))
    # guias por baixo de todos os rótulos: nenhuma linha atravessa o rótulo de outro grupo
    out.append(
        f'<g pointer-events="none">{"".join(guias)}{"".join(cruzes)}{"".join(chips)}</g>'
    )
    out.append(rot_el_svg)
    out.append(
        f'<circle class="near-halo" cx="0" cy="0" r="8" fill="none" stroke="{LIMA}" stroke-width="3" display="none"/>'
    )
    out.append("</svg>")
    tips = Tips()
    tips.tabela(
        [
            "Seção",
            "Marca",
            "Município",
            "Zona · seção",
            "Local",
            "Lula · Flávio, % dos válidos",
            "Explicação",
            "Log-verossimilhança",
        ],
        linhas,
        xy=xy,
        nota="rótulo de cada grupo no painel ao lado",
    )
    ctl = botoes(
        [("cluster", "Cor pelo grupo"), ("regiao", "Cor pela região")], "cluster", "Cor"
    )
    leg_cl = (
        '<div data-alt-show="cluster">'
        + legenda_html(
            [
                (rotulo_cluster(S, c["id"]), CLUSTER_COR[c["id"] % len(CLUSTER_COR)])
                for c in C["componentes"]
            ],
            "Grupo da mistura gaussiana",
        )
        + "</div>"
    )
    regs = [*REGIOES, "Exterior"]
    leg_rg = (
        '<div data-alt-show="regiao" hidden>'
        + legenda_html([(rg, COR_REGIAO[rg]) for rg in regs], "Região da seção")
        + "</div>"
    )
    aj = C["ajuste"]
    dg = aj.get("diagnostico_convergencia") or {}
    busca = (
        f"{dg['sementes']} sementes, {len(dg.get('inits') or [])} inicializações e {aj.get('n_init')} partidas internas cada"
        if dg
        else f"{aj.get('n_init')} inicializações"
    )
    legenda = (
        f"Projeção das {inteiro(P.get('n_pontos', len(pontos)))} seções da amostra: "
        f"{escape(P.get('base') or 'dois primeiros componentes principais')}. Partes: {escape(C['base'])}. "
        f"Mistura gaussiana com k = {C['k']}, covariância completa, {busca}. Contorno preto: as 200 "
        "seções menos prováveis sob o modelo. Elipse cinza tracejada: centro e covariância do grupo mais atípico, a dois desvios. O botão troca a cor do grupo pela região, para ver se grupo é geografia. "
        f"{nota_cobertura(S)} Fonte: secoes.json."
    )
    apos = _painel_clusters(S) + leg_cl + leg_rg + _tabela_anomalo(S)
    return figura_html(
        "clusters_secoes",
        "".join(out),
        legenda,
        tips,
        controles=ctl,
        minw=640,
        dim=False,
        apos=apos,
    )


__all__ = ["CINZA_ELIPSE", "elipse_cov", "topo_elipse"]
