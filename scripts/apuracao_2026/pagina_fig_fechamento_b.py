"""Figuras do fechamento das seções (capítulo 12), parte 2: encerramento e voto.

- `fechamento_voto_lula`: a % de Lula e de Flávio por faixa de encerramento em
  três réguas (bruta, dentro da zona, dentro da zona com tamanho e tipo), a
  inclinação por hora de atraso e o Spearman por UF;
- `fechamento_voto_zona`: seção tardia contra as demais da mesma zona em voto,
  comparecimento, fila e identificação, com intervalo de 95%.

Lê `fechamento.json`; nenhum número vem digitado.
"""

from __future__ import annotations

from html import escape

from .pagina_comum import inteiro, num, sinal
from .pagina_fig_base import (
    FLAVIO,
    GRADE,
    INK,
    LULA,
    MUTED,
    PAPER,
    Tips,
    area,
    botoes,
    escala,
    ficha,
    figura_html,
    hit,
    legenda_html,
    ln,
    pct,
    pp,
    r,
    registra,
    svg_abre,
    t,
)
from .pagina_fig_fechamento import (
    FUNDO,
    OURO,
    REGIOES,
    VAZIO,
    fech,
    nota_cobertura,
)

# ------------------------------------------------------------------ 3 voto de Lula por hora

MODELOS = [
    ("bruta", "bruta", MUTED, "losango"),
    ("zona", "dentro da zona", INK, "ponto"),
    ("zona_controles", "zona, tamanho e tipo", OURO, "quadrado"),
]


def _marca(forma: str, x: float, y: float, cor: str) -> str:
    if forma == "losango":
        return (
            f'<rect x="{x - 5:.1f}" y="{y - 5:.1f}" width="10" height="10" fill="{PAPER}" stroke="{cor}" '
            f'stroke-width="2" transform="rotate(45 {x:.1f} {y:.1f})"/>'
        )
    if forma == "quadrado":
        return f'<rect x="{x - 5:.1f}" y="{y - 5:.1f}" width="10" height="10" fill="{cor}" stroke="{PAPER}"/>'
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5.5" fill="{cor}" stroke="{PAPER}"/>'


def _painel_bruta(L: dict, grupo: str, px: float, py: float, tips: Tips) -> str:
    linhas_ = [x for x in L["bruta"] if x["grupo"] == grupo]
    x0, x1 = px + 150, px + 420
    X = escala(0, 100, x0, x1)
    out = []
    for v in (0, 25, 50, 75, 100):
        out.append(ln(X(v), py, X(v), py + 34 * len(linhas_), GRADE, 0.8))
        out.append(
            t(
                X(v),
                py + 34 * len(linhas_) + 18,
                f"{v}%",
                13,
                MUTED,
                "middle",
                mono=True,
            )
        )
    for i, x in enumerate(linhas_):
        y = py + 17 + 34 * i
        out.append(t(px, y + 5, x["faixa"], 14, INK))
        if not x["secoes"]:
            out.append(t(x0, y + 5, VAZIO, 13, MUTED))
            continue
        k = tips.add(
            ficha(
                f"{grupo}: encerramento {x['faixa']}",
                "% dos válidos de presidente, soma das seções",
                [
                    ("Seções", inteiro(x["secoes"])),
                    ("Votantes", inteiro(x["votantes"])),
                    ("Lula", pct(x["lula_pct"], 1)),
                    ("Flávio", pct(x["flavio_pct"], 1)),
                ],
            )
        )
        xl, xf = X(x["lula_pct"] or 0), X(x["flavio_pct"] or 0)
        g = ln(min(xl, xf), y, max(xl, xf), y, "#b9b29f", 3)
        g += f'<circle cx="{xl:.1f}" cy="{y:.1f}" r="6" fill="{LULA}"/>'
        g += f'<circle cx="{xf:.1f}" cy="{y:.1f}" r="6" fill="{FLAVIO}"/>'
        out.append(hit(g + area(px, y - 16, 520, 32), k))
        out.append(
            t(
                px + 520,
                y + 5,
                f"{inteiro(x['secoes'])} seções",
                13,
                MUTED,
                "end",
                mono=True,
            )
        )
    return "".join(out)


def _coef(L: dict, bloco: str, mid: str, cand: str, nome: str) -> dict:
    m = next((z for z in L[bloco] if z["id"] == mid), {})
    return ((m.get(cand) or {}).get("coeficientes") or {}).get(nome) or {}


def _coluna_coef(
    L: dict,
    bloco: str,
    cand: str,
    nomes: list[str],
    px: float,
    py: float,
    larg: float,
    tips: Tips,
    passo: float = 52,
) -> str:
    """Coeficientes dentro da zona (com e sem controles) com IC; a bruta vai em texto."""
    controlados = MODELOS[1:]
    vals = [0.0]
    for n in nomes:
        for mid, _rot, _cor, _f in controlados:
            c = _coef(L, bloco, mid, cand, n)
            vals += [
                v
                for v in [c.get("estimativa"), *(c.get("ic95") or [])]
                if v is not None
            ]
    lo, hi = min(vals), max(vals)
    pad = (hi - lo) * 0.12 or 1
    X = escala(lo - pad, hi + pad, px + 4, px + larg - 4)
    yb = py + passo * len(nomes)
    nome_c = "Lula" if cand == "lula" else "Flávio"
    out = [
        r(px, py - 4, larg, yb - py + 8, FUNDO),
        ln(X(0), py - 4, X(0), yb + 4, INK, 1.4),
        t(
            px + larg / 2,
            py - 14,
            nome_c,
            14,
            LULA if cand == "lula" else FLAVIO,
            "middle",
            "700",
        ),
        t(
            px + 2,
            yb + 20,
            pp(lo - pad, 1).replace(" pp", ""),
            13,
            MUTED,
            "start",
            mono=True,
        ),
        t(
            px + larg - 2,
            yb + 20,
            pp(hi + pad, 1).replace(" pp", ""),
            13,
            MUTED,
            "end",
            mono=True,
        ),
    ]
    for i, n in enumerate(nomes):
        yc = py + passo * i + 16
        for j, (mid, rot, cor, forma) in enumerate(controlados):
            c = _coef(L, bloco, mid, cand, n)
            e, ic = c.get("estimativa"), c.get("ic95") or [None, None]
            if e is None:
                continue
            y = yc + 12 * j
            g = ""
            if ic[0] is not None and ic[1] is not None:
                g += ln(X(ic[0]), y, X(ic[1]), y, cor, 2.4)
            g += _marca(forma, X(e), y, cor)
            k = tips.add(
                ficha(
                    f"{nome_c}: {n.replace('horas_atraso', 'por hora de atraso')}",
                    rot,
                    [
                        ("Estimativa", pp(e, 2)),
                        ("Intervalo de 95%", f"{pp(ic[0], 2)} a {pp(ic[1], 2)}"),
                        ("Erro-padrão (bootstrap)", num(c.get("ep"), 2)),
                        (
                            "Bruta, sem controle",
                            pp(_coef(L, bloco, "bruta", cand, n).get("estimativa"), 2),
                        ),
                    ],
                    "pontos percentuais dos válidos; bootstrap de zonas"
                    + ("" if bloco == "inclinacao" else f"; contra {L['referencia']}"),
                )
            )
            out.append(hit(g + area(px, y - 6, larg, 12), k))
        b = _coef(L, bloco, "bruta", cand, n).get("estimativa")
        esquerda = X(0) > px + larg / 2
        out.append(
            t(
                px + 6 if esquerda else px + larg - 6,
                yc + 34,
                f"bruta {pp(b, 1)}",
                13,
                MUTED,
                "start" if esquerda else "end",
                mono=True,
            )
        )
    return "".join(out)


def _painel_spearman(L: dict, px: float, py: float, larg: float, tips: Tips) -> str:
    lista = L.get("spearman_uf") or []
    out = [
        t(px, py, "4. Spearman seção a seção dentro da UF", 15, INK, weight="700"),
        t(
            px,
            py + 18,
            "hora de encerramento contra % de Lula, sem controle",
            13,
            MUTED,
        ),
    ]
    if not lista:
        return "".join(out) + t(px + larg / 2, py + 80, VAZIO, 14, MUTED, "middle")
    vals = [x["rho_lula"] for x in lista if x["rho_lula"] is not None] + [0.0]
    lo, hi = min(min(vals), -0.05), max(max(vals), 0.05)
    X = escala(lo, hi, px + 44, px + larg - 70)
    y = py + 34
    passo = 17
    out.append(ln(X(0), y - 4, X(0), y + passo * len(lista), INK, 1.2))
    for x in lista:
        v = x["rho_lula"]
        k = tips.add(
            ficha(
                x["uf"],
                x["regiao"],
                [
                    ("Seções", inteiro(x["secoes"])),
                    ("Encerradas às 18h ou depois", inteiro(x["secoes_depois_1800"])),
                    ("Spearman com Lula", num(v, 3)),
                    ("Spearman com Flávio", num(x["rho_flavio"], 3)),
                ],
                "correlação de postos, sem controle de zona",
            )
        )
        out.append(t(px + 30, y + 11, x["uf"], 13, INK, "end", mono=True))
        barra = ""
        if v is not None:
            a, b = sorted((X(0), X(v)))
            barra = r(a, y + 2, b - a, 11, LULA)
        out.append(hit(barra + area(px, y, larg, passo), k))
        out.append(t(px + larg, y + 11, sinal(v, 2), 13, INK, "end", mono=True))
        y += passo
    return "".join(out)


@registra("fechamento_voto_lula")
def fechamento_voto_lula(d, **_op) -> str:
    F = fech(d)
    L = F["lula_hora"]
    tips = Tips()
    grupos = ["Brasil"] + [
        rg for rg in REGIOES if any(x["grupo"] == rg for x in L["bruta"])
    ]
    n_faixas = len(L["faixas"])
    topo = 70
    alt_a = 34 * n_faixas + 40
    nomes_f = [x["rotulo"] for x in L["faixas"] if x["rotulo"] != L["referencia"]]
    nomes_f = [
        n
        for n in nomes_f
        if any(
            n in (m.get("lula") or {}).get("coeficientes", {}) for m in L["por_faixa"]
        )
    ]
    topo_b = topo + alt_a + 70
    n_uf = len(L.get("spearman_uf") or [])
    h = max(topo_b + 40 * 1 + 120, topo_b + 17 * n_uf + 60) + 20
    out = [
        svg_abre(
            1100,
            h,
            "Encerramento tardio e voto em Lula, em três réguas",
            "Bruta: % dos válidos de Lula e de Flávio por faixa de hora de encerramento. Dentro da zona: diferença "
            "contra as seções que encerraram de 17:00 a 17:30, com e sem controle de tamanho e tipo de local. "
            "Inclinação: pontos por hora de atraso. Spearman por UF.",
        ),
        t(
            20,
            24,
            "1. Bruta: % dos válidos por faixa de encerramento",
            15,
            INK,
            weight="700",
        ),
        t(
            20,
            44,
            "Lula (vermelho) e Flávio (azul), soma das seções da faixa",
            13,
            MUTED,
        ),
    ]
    for gi, g in enumerate(grupos):
        vis = "" if gi == 0 else ' display="none"'
        out.append(
            f'<g data-alt-show="{escape(g)}"{vis}>{_painel_bruta(L, g, 20, topo, tips)}</g>'
        )
    out.append(
        t(580, 24, "2. Dentro da zona, contra 17:00 a 17:30", 15, INK, weight="700")
    )
    out.append(t(580, 44, "pontos dos válidos; traço: intervalo de 95%", 13, MUTED))
    py = topo + 20
    for i, n in enumerate(nomes_f):
        out.append(t(580, py + 52 * i + 27, n, 14, INK))
    out.append(_coluna_coef(L, "por_faixa", "lula", nomes_f, 712, py, 178, tips))
    out.append(_coluna_coef(L, "por_faixa", "flavio", nomes_f, 908, py, 178, tips))
    out.append(
        t(
            20,
            topo_b - 24,
            "3. Inclinação: pontos por hora de atraso",
            15,
            INK,
            weight="700",
        )
    )
    sob = L.get("sobrevive_pct") or {}
    out.append(
        t(
            20,
            topo_b - 4,
            f"sobra {num(sob.get('lula_inclinacao'), 0)}% da bruta para Lula e "
            f"{num(sob.get('flavio_inclinacao'), 0)}% para Flávio",
            13,
            MUTED,
        )
    )
    out.append(t(20, topo_b + 66, "por hora", 14, INK))
    out.append(
        _coluna_coef(
            L, "inclinacao", "lula", ["horas_atraso"], 130, topo_b + 40, 190, tips, 60
        )
    )
    out.append(
        _coluna_coef(
            L, "inclinacao", "flavio", ["horas_atraso"], 340, topo_b + 40, 190, tips, 60
        )
    )
    out.append(_painel_spearman(L, 580, topo_b - 24, 500, tips))
    out.append("</svg>")
    ctl = botoes([(g, g) for g in grupos], "Brasil", "Painel 1, régua bruta")
    leg = legenda_html(
        [(f"{rot}", cor) for _m, rot, cor, _f in MODELOS[1:]],
        "Painéis 2 e 3: ponto = dentro da zona; quadrado = zona, tamanho e tipo; a régua bruta vai escrita",
    )
    legenda = (
        "A correlação bruta é esperada: seção grande, rural e indígena fecha tarde e vota em Lula. O número que "
        f"interessa é o que sobrevive ao controle por zona, tamanho e tipo de local: sobra "
        f"{num(sob.get('lula_inclinacao'), 0)}% da inclinação bruta. Correlação dentro da zona não identifica "
        f"mecanismo. Regressão ponderada pelos votantes, efeito fixo de zona, intervalo por bootstrap de "
        f"{inteiro(F['voto']['bootstrap'])} reamostras de zonas; {inteiro(L['secoes'])} seções em "
        f"{inteiro(L['zonas'])} zonas. {nota_cobertura(F)} Fonte: fechamento.json."
    )
    return figura_html(
        "fechamento_voto_lula",
        "".join(out),
        legenda,
        tips,
        controles=ctl,
        minw=900,
        apos=leg,
    )


# ------------------------------------------------------------------ 4 seção tardia contra a zona

ESTIMADORES = [
    "tarde18_zona",
    "tarde18_zona_tamanho",
    "tarde19_zona",
    "recebimento_decil_2026",
    "recebimento_decil_2022",
]
CURTO = {
    "tarde18_zona": "encerrou 18h+, mesma zona",
    "tarde18_zona_tamanho": "18h+, mesma zona e tamanho",
    "tarde19_zona": "encerrou 19h+, mesma zona",
    "recebimento_decil_2026": "chegou no último décimo, 2026",
    "recebimento_decil_2022": "chegou no último décimo, 2022",
}
PAINEIS = [
    [
        ("lula_pp", "Lula", LULA),
        ("flavio_pp", "Flávio", FLAVIO),
        ("comparecimento_pp", "Comparecimento", INK),
    ],
    [
        ("votantes_secao", "Votantes por seção", INK),
        ("votantes_hora", "Votantes por hora", INK),
        ("ano_nascimento_pp", "Hab. por ano de nascimento", OURO),
        ("sem_biometria_pp", "Sem biometria", MUTED),
    ],
]
UNIDADE = {
    "lula_pp": "pontos dos válidos",
    "flavio_pp": "pontos dos válidos",
    "comparecimento_pp": "pontos dos aptos",
    "votantes_secao": "votantes",
    "votantes_hora": "votantes por hora",
    "ano_nascimento_pp": "pontos dos votantes",
    "sem_biometria_pp": "pontos dos votantes",
}


def _painel_metrica(
    ests: dict,
    chave: str,
    nome: str,
    cor: str,
    px: float,
    py: float,
    larg: float,
    tips: Tips,
) -> str:
    vals = [0.0]
    for e in ests.values():
        m = (e or {}).get(chave) or {}
        vals += [
            v
            for v in [m.get("estimativa"), m.get("bruto"), *(m.get("ic95") or [])]
            if v is not None
        ]
    lim = max(abs(v) for v in vals) * 1.12 or 1
    X = escala(-lim, lim, px + 6, px + larg - 6)
    yb = py + 34 * len(ESTIMADORES)
    out = [
        r(px, py - 4, larg, yb - py + 8, FUNDO),
        ln(X(0), py - 4, X(0), yb + 4, INK, 1.4),
        t(
            px + larg / 2,
            py - 30,
            nome,
            14,
            cor if cor != MUTED else INK,
            "middle",
            "700",
        ),
        t(px + larg / 2, py - 13, UNIDADE[chave], 13, MUTED, "middle"),
    ]
    for v, anc in ((-lim / 1.12, "start"), (lim / 1.12, "end")):
        vv = float(f"{v:.2g}")
        out.append(
            t(
                px + 2 if anc == "start" else px + larg - 2,
                yb + 20,
                pp(vv, 1).replace(" pp", ""),
                13,
                MUTED,
                anc,
                mono=True,
            )
        )
    for i, ident in enumerate(ESTIMADORES):
        y = py + 17 + 34 * i
        e = ests.get(ident) or {}
        m = e.get(chave) or {}
        if not m:
            out.append(r(px + larg / 2 - 34, y - 10, 68, 20, PAPER))
            out.append(t(px + larg / 2, y + 5, "sem dado", 13, MUTED, "middle"))
            continue
        est, ic, b = m.get("estimativa"), m.get("ic95") or [None, None], m.get("bruto")
        g = ""
        if ic[0] is not None and ic[1] is not None:
            g += ln(X(ic[0]), y, X(ic[1]), y, cor, 3)
        if b is not None:
            g += _marca("losango", X(b), y, cor)
        if est is not None:
            g += f'<circle cx="{X(est):.1f}" cy="{y:.1f}" r="5.5" fill="{cor}" stroke="{PAPER}"/>'
        k = tips.add(
            ficha(
                f"{nome}: {CURTO[ident]}",
                "seção tardia menos as demais",
                [
                    ("Estimativa", num(est, 2)),
                    ("Intervalo de 95%", f"{num(ic[0], 2)} a {num(ic[1], 2)}"),
                    ("Sem controle", num(b, 2)),
                    ("Unidades comparadas", inteiro(e.get("unidades"))),
                    (
                        "Seções tardias · demais",
                        f"{inteiro(e.get('secoes_b'))} · {inteiro(e.get('secoes_a'))}",
                    ),
                ],
                UNIDADE[chave],
            )
        )
        out.append(hit(g + area(px, y - 16, larg, 32), k))
    return "".join(out)


@registra("fechamento_voto_zona")
def fechamento_voto_zona(d, **_op) -> str:
    F = fech(d)
    ests = {e["id"]: e.get("resultado") for e in F["voto"]["estimadores"]}
    tips = Tips()
    lx, larg, gap = 250, 196, 14
    alt = 34 * len(ESTIMADORES) + 90
    h = 2 * alt + 20
    out = [
        svg_abre(
            1100,
            h,
            "A seção que fecha tarde contra as demais da mesma zona",
            "Para cinco definições de seção tardia, a diferença contra as demais seções da mesma zona em voto, "
            "comparecimento, votantes por seção e por hora e forma de habilitação, com intervalo de 95%.",
        )
    ]
    for li, painel in enumerate(PAINEIS):
        py = 60 + li * alt
        for i, ident in enumerate(ESTIMADORES):
            out.append(t(lx - 12, py + 17 + 34 * i + 5, CURTO[ident], 13, INK, "end"))
        for j, (chave, nome, cor) in enumerate(painel):
            out.append(
                _painel_metrica(
                    ests, chave, nome, cor, lx + j * (larg + gap), py, larg, tips
                )
            )
    out.append("</svg>")
    leg = legenda_html(
        [
            ("estimativa dentro da unidade (ponto) e intervalo de 95% (traço)", INK),
            ("diferença sem controle (losango vazado)", PAPER),
        ]
    )
    z = ests.get("tarde18_zona") or {}
    legenda = (
        "Diferença = seções tardias menos as demais da mesma zona (ou da mesma zona e faixa de eleitorado apto), "
        "pelo estimador do modelo de urna: percentual agregado de cada grupo dentro da unidade, média ponderada "
        f"pelos votantes, intervalo por bootstrap de {inteiro(F['voto']['bootstrap'])} reamostras de unidades. "
        f"{inteiro(z.get('unidades'))} zonas com seções dos dois grupos na primeira linha. Em 2022 não há hora de "
        f"encerramento nem habilitação no arquivo do TSE. {nota_cobertura(F)} Fonte: fechamento.json."
    )
    return figura_html(
        "fechamento_voto_zona", "".join(out), legenda, tips, minw=900, apos=leg
    )
