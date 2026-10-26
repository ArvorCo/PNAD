"""Figuras do capítulo "Grupos" do dossiê do 2º turno, parte 1.

- ``fig_bic``: BIC e ICL por k na amostra estratificada, com k* marcado e a regra;
- ``fig_kmeans``: silhueta do k-means por k nos dois enquadramentos (contraste);
- ``fig_grupos``: painel dos grupos, barras do eleitorado no 1º e no 2º turno lado a
  lado e os centros em diferenças;
- ``fig_regiao``: composição regional de cada grupo (como ``clusters_regiao`` do 1T).

Tudo sai de ``anomalia_ml.json``; nenhum número vem digitado.
"""

from __future__ import annotations

from html import escape

from apuracao_2026.pagina_comum import CINZA, FLAVIO, LULA, OUTROS, inteiro, num, tabela
from apuracao_2026.pagina_fig_base import (
    COR_REGIAO,
    GRADE,
    INK,
    LIMA,
    MUTED,
    PAPER,
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
    r,
    sobre,
    svg_abre,
    t,
    ticks,
)
from apuracao_2026.pagina_fig_secoes import larg_texto

from . import pagina_fig_anomalia_base as B

ICL_COR = "#6b4a92"
BIC_COR = INK
PARTES = [  # (chave, nome, cor)
    ("lula", "Lula", LULA),
    ("flavio", "Flávio", FLAVIO),
    ("terceiros", "outras candidaturas (só no 1º turno)", OUTROS),
    ("brancos", "brancos", "#d9d2bf"),
    ("nulos", "nulos", CINZA),
    ("abstencao", "abstenção", "#c9a43a"),
]
COR_PARTE = {k: c for k, _, c in PARTES}
NOME_PARTE = {k: n.split(" (")[0] for k, n, _ in PARTES}
ESTILO = (
    "<style>#fig-an_grupos .an-g{margin:0 0 16px;padding:0 0 12px;border-bottom:1px solid var(--line)}"
    "#fig-an_grupos .an-g h4{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin:0 0 4px;"
    "font:700 15px/1.4 var(--sans)}"
    "#fig-an_grupos .an-g h4 span{font:400 13px/1.4 var(--sans);color:var(--muted)}"
    "#fig-an_grupos .an-g h4 .sw{display:inline-block;width:12px;height:12px;border:1px solid #9a9c94;flex:none}"
    "#fig-an_grupos .an-g em.cl-anom{font:700 12px/1.4 var(--sans);color:#fff;background:var(--ink);"
    "padding:1px 7px;border-radius:3px;font-style:normal}"
    "#fig-an_grupos .an-t{display:grid;grid-template-columns:32px 1fr;gap:6px;align-items:center;margin:4px 0}"
    "#fig-an_grupos .an-t b{font:700 12px/1 var(--mono);color:var(--muted)}"
    "#fig-an_grupos .an-barra{display:flex;height:18px;border:1px solid var(--line)}"
    "#fig-an_grupos .an-barra>span{display:block;height:100%}"
    "#fig-an_grupos .an-d{margin:6px 0 0;font:13px/1.5 var(--sans)}"
    "#fig-an_grupos .an-leg{list-style:none;display:flex;flex-wrap:wrap;gap:2px 12px;padding:0;margin:0 0 12px;"
    "font:12.5px/1.5 var(--sans)}"
    "#fig-an_grupos .an-leg li{margin:0}"
    "#fig-an_grupos .an-leg i{display:inline-block;width:10px;height:10px;margin-right:5px;vertical-align:-1px;"
    "border:1px solid #9a9c94}</style>"
)


# ------------------------------------------------------------------ BIC e ICL


def fig_bic(A: dict) -> str:
    linhas = sorted(A["bic"], key=lambda x: x["k"])
    if not linhas:
        raise KeyError("bic")
    k_est = B.k_de(A)
    ks = [x["k"] for x in linhas]
    bics = [float(x["bic"]) for x in linhas]
    icls = [float(B.g(x, "icl", padrao=x["bic"])) for x in linhas]
    w, h = 1100, 420
    x0, x1, y0, y1 = 120, 1060, 30, 350
    lo = min(bics + icls)
    hi = max(bics + icls)
    pad = (hi - lo) * 0.08 or 1
    X = escala(min(ks) - 0.5, max(ks) + 0.5, x0, x1)
    Y = escala(lo - pad, hi + pad, y1, y0)
    out = [
        svg_abre(
            w,
            h,
            "BIC e ICL por número de grupos",
            "Duas curvas por k, de 2 a 10, na amostra estratificada por UF; o k escolhido pela regra "
            "declarada aparece marcado. Quanto menor, melhor.",
        )
    ]
    for v in ticks(lo - pad, hi + pad, 5):
        out.append(ln(x0, Y(v), x1, Y(v), GRADE, 0.8))
        out.append(
            t(x0 - 8, Y(v) + 4, f"{v / 1e6:.2f} mi", 12, MUTED, "end", mono=True)
        )
    for k in ks:
        out.append(t(X(k), y1 + 22, str(k), 13, INK, "middle", mono=True))
    out.append(t((x0 + x1) / 2, h - 14, "número de grupos (k)", 13, MUTED, "middle"))
    out.append(
        t(16, (y0 + y1) / 2, "critério (menor é melhor)", 13, MUTED, "middle",
          extra=f' transform="rotate(-90 16 {(y0 + y1) / 2:.0f})"')
    )  # fmt: skip
    kx = X(k_est)
    out.append(
        f'<rect x="{kx - 18:.1f}" y="{y0:.1f}" width="36" height="{y1 - y0:.1f}" fill="{LIMA}" fill-opacity="0.22"/>'
    )
    for serie, cor, dash in (
        (bics, BIC_COR, ""),
        (icls, ICL_COR, ' stroke-dasharray="6 4"'),
    ):
        pts = " ".join(f"{X(k):.1f},{Y(v):.1f}" for k, v in zip(ks, serie, strict=True))
        out.append(
            f'<polyline points="{pts}" fill="none" stroke="{cor}" stroke-width="2.4"{dash}/>'
        )
    tips = Tips()
    for x, bic, icl in zip(linhas, bics, icls, strict=True):
        k = x["k"]
        ch = tips.add(
            ficha(
                f"k = {k}",
                "amostra estratificada por UF",
                [
                    ("BIC", inteiro(bic)),
                    ("ICL", inteiro(icl)),
                    ("Log-verossimilhança média", num(B.g(x, "loglik_media"), 4)),
                    ("Iterações", inteiro(B.g(x, "iteracoes"))),
                    ("Convergiu", "sim" if B.g(x, "convergiu") else "não"),
                ],
                "k escolhido" if k == k_est else "",
            )
        )
        corpo = (
            area(X(k) - 22, y0, 44, y1 - y0)
            + f'<circle cx="{X(k):.1f}" cy="{Y(bic):.1f}" r="5" fill="{BIC_COR}" stroke="{PAPER}" stroke-width="1.5"/>'
            + f'<circle cx="{X(k):.1f}" cy="{Y(icl):.1f}" r="5" fill="{ICL_COR}" stroke="{PAPER}" stroke-width="1.5"/>'
        )
        out.append(hit(corpo, ch, foco=True))
    out.append(chip(kx, y0 + 18, f"k* = {k_est}", 13, "middle"))
    out.append("</svg>")
    leg = legenda_html(
        [
            ("BIC", BIC_COR),
            ("ICL (BIC mais a entropia das responsabilidades)", ICL_COR),
        ],
        "Curvas",
    )
    regra = escape(str(B.g(A, "regra", padrao="")))
    legenda = (
        f"BIC e ICL para k de {min(ks)} a {max(ks)}. Regra: {regra} "
        f"Candidatos: joelho do BIC em k = {B.g(A, 'k_joelho_bic', padrao='s/d')}, mínimo do ICL em "
        f"k = {B.g(A, 'k_min_icl', padrao='s/d')}; escolhido k = {k_est}. Fonte: anomalia_ml.json."
    )
    return figura_html(
        "an_bic", "".join(out), legenda, tips, minw=640, apos=leg, dim=False
    )


def tabela_bic(A: dict) -> str:
    k_est = B.k_de(A)
    linhas = []
    for x in sorted(A["bic"], key=lambda x: x["k"]):
        marca = " <b>(escolhido)</b>" if x["k"] == k_est else ""
        pm, pt = B.g(x, "partidas_no_maximo"), B.g(x, "partidas")
        linhas.append(
            [
                f"{x['k']}{marca}",
                inteiro(x["bic"]),
                inteiro(B.g(x, "icl")),
                num(B.g(x, "loglik_media"), 4).replace("-", "−"),
                inteiro(B.g(x, "iteracoes")),
                "sim" if B.g(x, "convergiu") else "não",
                f"{inteiro(pm)} de {inteiro(pt)}" if pt else "s/d",
            ]
        )
    return tabela(
        [
            "k",
            "BIC",
            "ICL",
            "log-verossimilhança média",
            "iterações",
            "convergiu",
            "partidas no máximo",
        ],
        linhas,
        "Critérios por número de grupos na amostra estratificada; menor é melhor. A última coluna conta quantas "
        "partidas chegaram ao mesmo máximo da melhor.",
    )


# ------------------------------------------------------------------ k-means


def fig_kmeans(A: dict) -> str:
    K = A.get("kmeans") or {}
    series = [
        ("niveis", "nove níveis", INK, ""),
        (
            "niveis_e_deltas",
            "cinco níveis do 1º turno e quatro diferenças",
            ICL_COR,
            ' stroke-dasharray="6 4"',
        ),
    ]
    dados = {ch: sorted(K.get(ch) or [], key=lambda x: x["k"]) for ch, *_ in series}
    if not any(dados.values()):
        raise KeyError("kmeans")
    ks = sorted({x["k"] for v in dados.values() for x in v})
    sil = [
        float(x["silhueta"])
        for v in dados.values()
        for x in v
        if x.get("silhueta") is not None
    ]
    lo, hi = min([*sil, 0.0]), max([*sil, 0.1])
    pad = (hi - lo) * 0.1 or 0.05
    w, h = 1100, 400
    x0, x1, y0, y1 = 90, 1060, 30, 330
    X = escala(min(ks) - 0.5, max(ks) + 0.5, x0, x1)
    Y = escala(lo - pad, hi + pad, y1, y0)
    k_est = B.k_de(A)
    out = [
        svg_abre(
            w,
            h,
            "Silhueta média do k-means por número de grupos, em dois enquadramentos",
            "Contraste com a mistura: o k-means não é invariante à troca de níveis por diferenças, "
            "então roda nos dois; silhueta numa amostra de 20.000 seções.",
        )
    ]
    for v in ticks(lo - pad, hi + pad, 5):
        out.append(ln(x0, Y(v), x1, Y(v), GRADE, 0.8))
        out.append(t(x0 - 8, Y(v) + 4, num(v, 2), 12, MUTED, "end", mono=True))
    for k in ks:
        out.append(t(X(k), y1 + 22, str(k), 13, INK, "middle", mono=True))
    out.append(t((x0 + x1) / 2, h - 14, "número de grupos (k)", 13, MUTED, "middle"))
    out.append(
        t(16, (y0 + y1) / 2, "silhueta média", 13, MUTED, "middle",
          extra=f' transform="rotate(-90 16 {(y0 + y1) / 2:.0f})"')
    )  # fmt: skip
    kx = X(k_est)
    out.append(
        f'<rect x="{kx - 18:.1f}" y="{y0:.1f}" width="36" height="{y1 - y0:.1f}" fill="{LIMA}" fill-opacity="0.22"/>'
    )
    tips = Tips()
    for ch, nome, cor_s, dash in series:
        v = [x for x in dados[ch] if x.get("silhueta") is not None]
        if not v:
            continue
        pts = " ".join(f"{X(x['k']):.1f},{Y(float(x['silhueta'])):.1f}" for x in v)
        out.append(
            f'<polyline points="{pts}" fill="none" stroke="{cor_s}" stroke-width="2.4"{dash}/>'
        )
        for x in v:
            k = x["k"]
            chave = tips.add(
                ficha(
                    f"k = {k}: {nome}",
                    "k-means, 10 partidas",
                    [
                        ("Silhueta média", num(x["silhueta"], 3)),
                        ("Inércia", inteiro(B.g(x, "inercia"))),
                        ("Iterações", inteiro(B.g(x, "iteracoes"))),
                        ("Convergiu", "sim" if B.g(x, "convergiu") else "não"),
                    ],
                )
            )
            out.append(
                hit(
                    area(X(k) - 10, Y(float(x["silhueta"])) - 10, 20, 20)
                    + f'<circle cx="{X(k):.1f}" cy="{Y(float(x["silhueta"])):.1f}" r="5" fill="{cor_s}" '
                    f'stroke="{PAPER}" stroke-width="1.5"/>',
                    chave,
                    foco=True,
                )
            )
    out.append(chip(kx, y0 + 18, f"k* = {k_est}", 13, "middle"))
    out.append("</svg>")
    ari = K.get("ari_com_mistura_k_estrela") or {}
    leg = legenda_html([(n, c) for _, n, c, _ in series], "Enquadramento")
    legenda = (
        f"Silhueta média do k-means por k nos dois enquadramentos; faixa verde em k = {k_est}. Índice de Rand "
        f"ajustado entre a partição do k-means com k = {k_est} e a da mistura: {num(ari.get('niveis'), 2)} nos "
        f"níveis e {num(ari.get('niveis_e_deltas'), 2)} em níveis e diferenças. A mistura é o modelo principal; "
        "o k-means é contraste. Fonte: anomalia_ml.json."
    )
    return figura_html(
        "an_kmeans", "".join(out), legenda, tips, minw=640, apos=leg, dim=False
    )


# ------------------------------------------------------------------ painel dos grupos


def _barra_svg(
    partes: list[tuple[str, float]],
    x0: float,
    y: float,
    larg: float,
    alt: float,
    tips: Tips,
    titulo: str,
) -> str:
    out, cx = [], x0
    for nome, v in partes:
        if v <= 0:
            continue
        lw = larg * v / 100
        cor_p = COR_PARTE[nome]
        ch = tips.add(
            ficha(titulo, NOME_PARTE[nome], [("Parte do eleitorado", B.pct_txt(v, 1))])
        )
        out.append(
            hit(r(cx, y, lw, alt, cor_p, f' stroke="{PAPER}" stroke-width="0.8"'), ch)
        )
        rot = f"{num(v, 0)}"
        if lw >= larg_texto(rot, 11) + 8 and nome != "brancos":
            out.append(
                t(
                    cx + lw / 2,
                    y + alt / 2 + 4,
                    rot,
                    11,
                    sobre(cor_p),
                    "middle",
                    extra=' pointer-events="none"',
                )
            )
        cx += lw
    return "".join(out)


def _barra_html(partes: list[tuple[str, float]]) -> str:
    segs = "".join(
        f'<span title="{escape(NOME_PARTE[n])} {num(v, 1)}%" style="flex:{v:.3f} 1 0;background:{COR_PARTE[n]}"></span>'
        for n, v in partes
        if v > 0
    )
    return f'<div class="an-barra" role="img" aria-label="Eleitorado do grupo">{segs}</div>'


def _frase_deltas(c: dict) -> str:
    dl = B.deltas(c)
    partes = [
        f"{B.DELTA_NOME[k]} {B.pp_txt(dl[k], 1)}"
        for k in ("comp", "lula", "flavio", "brancos", "nulos")
        if k in dl
    ]
    t3 = B.terceira_1t(c)
    if t3 is not None:
        partes.append(
            f"outras candidaturas no 1º turno {B.pct_txt(t3, 1)} do eleitorado"
        )
    return "; ".join(partes)


def fig_grupos(A: dict) -> str:
    cs = B.componentes(A)
    ma = B.id_atipico(A)
    w = 1100
    bloco = 92
    h = 36 + bloco * len(cs) + 10
    xr, larg = 300, 520
    xd = xr + larg + 18
    out = [
        svg_abre(
            w,
            h,
            f"Os {B.extenso(len(cs))} grupos de seções: eleitorado no 1º e no 2º turno",
            "Para cada grupo, duas barras de 100% do eleitorado (1º e 2º turno) com Lula, Flávio, outras "
            "candidaturas, brancos, nulos e abstenção, e o centro em diferenças à direita.",
        ),
        t(20, 24, "Grupo", 13, MUTED, weight="600"),
        t(
            xr,
            24,
            "Eleitorado do grupo, 1º turno (acima) e 2º turno (abaixo)",
            13,
            MUTED,
            weight="600",
        ),
        t(xd, 24, "2º turno menos 1º, pp do eleitorado", 13, MUTED, weight="600"),
    ]
    tips = Tips()
    estreito = [ESTILO]
    y = 40
    for c in cs:
        k = c["id"]
        cor_g = B.cor(k)
        rot = B.rotulo_grupo(A, k, curto=True)
        out.append(r(20, y + 4, 13, 13, cor_g, f' stroke="{INK}" stroke-width="0.6"'))
        out.append(t(40, y + 15, rot, 14, INK, weight="700"))
        if k == ma:
            out.append(chip(40, y + 36, "mais atípico", 11))
        out.append(
            t(
                40,
                y + (58 if k == ma else 36),
                f"{inteiro(c['secoes'])} seções ({num(c['pct_secoes'], 1)}%)",
                12,
                MUTED,
            )
        )
        p1, p2 = B.partes_turno(c, 1), B.partes_turno(c, 2)
        out.append(t(xr - 8, y + 20, "1º", 11, MUTED, "end", mono=True))
        out.append(_barra_svg(p1, xr, y + 6, larg, 22, tips, f"{rot}, 1º turno"))
        out.append(t(xr - 8, y + 50, "2º", 11, MUTED, "end", mono=True))
        out.append(_barra_svg(p2, xr, y + 36, larg, 22, tips, f"{rot}, 2º turno"))
        dl = B.deltas(c)
        yy = y + 14
        for kk in ("comp", "lula", "flavio", "brancos", "nulos"):
            if kk in dl:
                out.append(
                    t(
                        xd,
                        yy,
                        f"{B.DELTA_NOME[kk]} {B.pp_txt(dl[kk], 1)}",
                        12,
                        INK,
                        mono=True,
                    )
                )
                yy += 14
        rotulo = escape(c.get("rotulo") or "")
        estreito.append(
            f'<div class="an-g"><h4><i class="sw" style="background:{cor_g}"></i>{escape(rot)}'
            + (' <em class="cl-anom">mais atípico</em>' if k == ma else "")
            + f"<span>{inteiro(c['secoes'])} seções ({num(c['pct_secoes'], 1)}%)</span></h4>"
            + (f'<p class="an-d">{rotulo}</p>' if rotulo else "")
            + f'<div class="an-t"><b>1º</b>{_barra_html(p1)}</div>'
            + f'<div class="an-t"><b>2º</b>{_barra_html(p2)}</div>'
            + f'<p class="an-d">2º menos 1º: {escape(_frase_deltas(c))}.</p></div>'
        )
        y += bloco
    out.append("</svg>")
    corpo = f'<div class="fig-larga">{"".join(out)}</div><div class="fig-estreita">{"".join(estreito)}</div>'
    leg = legenda_html(
        [(n, c) for _, n, c in PARTES],
        "Partes da barra (% do eleitorado apto do turno)",
    )
    painel = _painel(A)
    legenda = (
        f"Centros dos {B.extenso(len(cs))} grupos da mistura gaussiana, em frações do eleitorado apto de cada "
        "turno. Abstenção fecha a barra em 100%. Os números à direita são o mesmo centro em diferenças "
        "(2º turno menos 1º), a parametrização equivalente que o leitor entende. Fonte: anomalia_ml.json."
    )
    return figura_html(
        "an_grupos", corpo, legenda, tips, modo="full", apos=leg + painel, dim=False
    )


def _painel(A: dict) -> str:
    """Lista dos grupos com rótulo, UFs e região dominante (como o painel do 1T)."""
    ma = B.id_atipico(A)
    itens = []
    for c in B.componentes(A):
        ufs = ", ".join(
            f"{u['uf']} {num(u['pct_do_cluster'], 1)}%"
            for u in (c.get("ufs_top") or [])[:3]
        )
        reg = (c.get("regioes") or [None])[0]
        marca = ' <em class="cl-anom">mais atípico</em>' if c["id"] == ma else ""
        itens.append(
            f'<li><span class="sw" style="background:{B.cor(c["id"])}"></span>'
            f"<b>{escape(B.rotulo_grupo(A, c['id']))}</b>{marca}"
            f"<span>{inteiro(c['secoes'])} seções ({num(c['pct_secoes'], 1)}%), {inteiro(c.get('aptos_medio'))} aptos por seção</span>"
            f"<span>Comparecimento: {B.pct_txt(B.g(c, 'comp1_pct'))} no 1º turno, {B.pct_txt(B.g(c, 'comp2_pct'))} no 2º</span>"
            f"<span>Fatia de Flávio entre os dois: {B.pct_txt(B.g(c, 'fatia_f1'))} no 1º, {B.pct_txt(B.g(c, 'fatia_f2'))} no 2º</span>"
            + (f"<span>UFs: {escape(ufs)}</span>" if ufs else "")
            + (
                f"<span>Região dominante: {escape(reg['regiao'])} ({num(reg['pct_do_cluster'], 1)}%)</span>"
                if reg
                else ""
            )
            + "</li>"
        )
    return f'<div class="cl-painel"><h4>Os {B.extenso(len(itens))} grupos, um a um</h4><ol>{"".join(itens)}</ol></div>'


# ------------------------------------------------------------------ composição regional


ESTILO_REGIAO = (
    "<style>#fig-an_regiao .clr-g{margin:0 0 18px}"
    "#fig-an_regiao .clr-g h4{display:flex;align-items:center;gap:8px;margin:0 0 6px;font:700 15px/1.4 var(--sans)}"
    "#fig-an_regiao .clr-g h4 span{font:400 13px/1.4 var(--sans);color:var(--muted)}"
    "#fig-an_regiao .clr-g .sw{display:inline-block;width:12px;height:12px;border:1px solid #9a9c94;flex:none}"
    "#fig-an_regiao .clr-barra{display:flex;height:26px;border:1px solid var(--line)}"
    "#fig-an_regiao .clr-barra>span{display:block;height:100%}"
    "#fig-an_regiao .clr-g ul{list-style:none;display:flex;flex-wrap:wrap;gap:2px 14px;padding:0;margin:6px 0 0;"
    "font:13px/1.5 var(--sans)}"
    "#fig-an_regiao .clr-g li{margin:0}"
    "#fig-an_regiao .clr-g li i{display:inline-block;width:10px;height:10px;margin-right:5px;vertical-align:-1px}</style>"
)


def fig_regiao(A: dict) -> str:
    linhas = A.get("cluster_regiao") or []
    if not linhas:
        raise KeyError("cluster_regiao")
    ids = sorted({int(x["cluster"]) for x in linhas})
    regs = [*REGIOES, "Exterior"]
    nomes = {k: B.rotulo_grupo(A, k, curto=True) for k in ids}
    n_sec = {c["id"]: c["secoes"] for c in A["componentes"]}
    w = 1100
    h = 40 + 52 * len(ids) + 20
    xs, tam = 20, 14
    x0 = xs + 20 + max(larg_texto(n, tam, True) for n in nomes.values()) + 24
    x1 = 1080
    out = [
        svg_abre(
            w,
            h,
            "Composição regional de cada grupo de seções",
            "Uma barra por grupo da mistura gaussiana, dividida pela região das seções que o compõem.",
        ),
        t(xs, 26, "Grupo", 13, MUTED, weight="600"),
        t(x0, 26, "Parte das seções do grupo, por região", 13, MUTED, weight="600"),
    ]
    tips = Tips()
    estreito = [ESTILO_REGIAO]
    y = 40
    for k in ids:
        cor_g = B.cor(k)
        out.append(r(xs, y + 16, 13, 13, cor_g, f' stroke="{INK}" stroke-width="0.6"'))
        out.append(t(xs + 20, y + 28, nomes[k], tam, INK, weight="700"))
        cx = float(x0)
        partes = sorted(
            (x for x in linhas if int(x["cluster"]) == k),
            key=lambda x: regs.index(x["regiao"]) if x["regiao"] in regs else 9,
        )
        segs, itens = [], []
        for x in partes:
            larg = (x1 - x0) * (x["pct_do_cluster"] or 0) / 100
            cor_r = COR_REGIAO.get(x["regiao"], MUTED)
            chave = tips.add(
                ficha(
                    f"{nomes[k]}: {x['regiao']}",
                    "",
                    [
                        ("Seções", inteiro(x["secoes"])),
                        ("Parte do grupo", B.pct_txt(x["pct_do_cluster"], 1)),
                        (
                            "Parte das seções da região",
                            B.pct_txt(B.g(x, "pct_da_regiao"), 1),
                        ),
                    ],
                    B.rotulo_grupo(A, k),
                )
            )
            out.append(
                hit(
                    r(
                        cx,
                        y + 6,
                        larg,
                        34,
                        cor_r,
                        f' stroke="{PAPER}" stroke-width="1"',
                    ),
                    chave,
                )
            )
            rot = f"{x['regiao']} {num(x['pct_do_cluster'], 0)}%"
            if larg >= larg_texto(rot, 13, True) + 12:
                out.append(
                    t(
                        cx + 6,
                        y + 28,
                        rot,
                        13,
                        sobre(cor_r),
                        weight="600",
                        extra=' pointer-events="none"',
                    )
                )
            segs.append(
                f'<span class="hit" data-k="{chave}" style="flex:{x["pct_do_cluster"] or 0:.2f} 1 0;background:{cor_r}"></span>'
            )
            itens.append(f'<li><i style="background:{cor_r}"></i>{escape(rot)}</li>')
            cx += larg
        estreito.append(
            f'<div class="clr-g"><h4><i class="sw" style="background:{cor_g}"></i>{escape(nomes[k])}'
            f"<span>{inteiro(n_sec.get(k))} seções</span></h4>"
            f'<div class="clr-barra">{"".join(segs)}</div><ul>{"".join(itens)}</ul></div>'
        )
        y += 52
    out.append("</svg>")
    corpo = f'<div class="fig-larga">{"".join(out)}</div><div class="fig-estreita">{"".join(estreito)}</div>'
    presentes = [rg for rg in regs if any(x["regiao"] == rg for x in linhas)]
    leg = legenda_html(
        [(rg, COR_REGIAO[rg]) for rg in presentes], "Região (cor da barra)"
    ) + legenda_html(
        [(B.rotulo_grupo(A, k), B.cor(k)) for k in ids],
        "Grupos (a cor do quadrado é a da projeção)",
    )
    legenda = (
        f"Cada barra soma 100% das seções do grupo. V de Cramér entre grupo e região: {num(A.get('cramer_v_regiao'), 2)}; "
        f"entre grupo e UF: {num(A.get('cramer_v_uf'), 2)}. Exterior fora do modelo. Fonte: anomalia_ml.json."
    )
    return figura_html("an_regiao", corpo, legenda, tips, minw=640, apos=leg)


__all__ = [
    "COR_PARTE",
    "PARTES",
    "fig_bic",
    "fig_grupos",
    "fig_kmeans",
    "fig_regiao",
    "tabela_bic",
]
