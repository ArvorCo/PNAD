"""Figuras do capítulo `pesquisas` (2º turno): casas contra a urna e erro por casa.

Desenho em Python sobre `apuracao_2026.pagina_fig_base` (ficha, escalas, figura
adiada). A urna é sempre a linha de referência. Diferença Flávio menos Lula (F−L)
nos válidos; positivo quer dizer Flávio à frente.
"""

from __future__ import annotations

import math

from apuracao_2026.pagina_fig_base import (
    FLAVIO,
    GRADE,
    HALO,
    INK,
    LULA,
    MUTED,
    Tips,
    W,
    area,
    escala,
    ficha,
    figura_html,
    hit,
    legenda_html,
    ln,
    pp,
    r,
    svg_abre,
    t,
    ticks,
)

from .pagina_comum import inteiro, num

CINZA_REP = "#8d8f88"
GOLD = "#7d5b00"
MARGEM = "#cdc5ae"
AZUL_CLARO = "#9db7dd"


def _sn(v: float, casas: int = 1) -> str:
    return pp(v, casas)[:-3]


def _dm(iso: str) -> str:
    return f"{iso[8:10]}/{iso[5:7]}"


def _ordenadas(PV: dict) -> list[dict]:
    por_id = {x["id"]: x for x in PV["pesquisas"]}
    return [por_id[i] for i in PV["ranking"] if i in por_id]


# ------------------------------------------------------------------ casas × urna


def fig_casas(PV: dict) -> str:
    casas = _ordenadas(PV)
    urna = PV["urna"]["brasil"]["validos"]
    u = urna["flavio"] - urna["lula"]
    c = PV["centrais"]
    ms = PV["resumo"]["media_simples_validos"]
    centrais = [
        (f"Média simples das {len(casas)} casas", ms["flavio"] - ms["lula"], None),
        (
            "Âncora da Projeção, publicada",
            c["ancora_projecao_published"]["pesquisa_f_menos_l"],
            c["ancora_projecao_published"],
        ),
        (
            "Âncora com PNAD",
            c["ancora_projecao_pnad"]["pesquisa_f_menos_l"],
            c["ancora_projecao_pnad"],
        ),
        (
            "Projeção Arvor",
            c["projecao_arvor"]["pesquisa_f_menos_l"],
            c["projecao_arvor"],
        ),
        ("Média Arvor", c["media_arvor"]["pesquisa_f_menos_l"], c["media_arvor"]),
    ]
    vals = [u]
    for x in casas:
        a = x["erro_validos_do_total"]["pesquisa_f_menos_l"]
        m = x["margem_95_diferenca_aas_pp"]
        vals += [a - m, a + m]
        if x.get("erro_reponderado"):
            vals.append(x["erro_reponderado"]["pesquisa_f_menos_l"])
    vals += [v for _, v, _ in centrais]
    lo = math.floor(min(vals) / 2) * 2
    hi = math.ceil(max(vals) / 2) * 2
    esq, topo, passo = 240, 92, 28
    n = len(casas) + len(centrais)
    base = topo + passo * n + 26
    h = base + 56
    X = escala(lo, hi, esq, W - 70)
    tips = Tips()
    out = [
        svg_abre(
            W,
            h,
            "Último campo das casas contra a urna do 2º turno",
            "Cada linha é a última onda de uma casa: ponto escuro o publicado, anel os válidos oficiais, "
            "seta até o ponto cinza o reponderado por renda; a linha vermelha é a urna.",
        ),
        '<defs><marker id="p2-seta" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
        f'markerHeight="7" orient="auto-start-reverse"><path d="M0,0L10,5L0,10z" fill="{INK}"/>'
        "</marker></defs>",
    ]
    for v in ticks(lo, hi, 10):
        out.append(ln(X(v), topo - 8, X(v), base, GRADE))
        out.append(t(X(v), base + 20, _sn(v, 0), 13, MUTED, "middle", mono=True))
    out.append(
        t(
            W - 70,
            base + 42,
            "diferença Flávio menos Lula, em pontos dos válidos",
            13,
            MUTED,
            "end",
        )
    )
    out.append(ln(X(0), topo - 14, X(0), base, MUTED, 1.2, ' stroke-dasharray="4 4"'))
    out.append(t(X(0), topo - 20, "empate", 13, MUTED, "middle"))
    out.append(ln(X(u), topo - 30, X(u), base, LULA, 2.6))
    out.append(t(X(u), topo - 36, f"urna {_sn(u, 2)}", 14, LULA, "middle", "700"))
    out.append(t(X(u) - 10, 24, "← Lula à frente", 13, LULA, "end", "700"))
    out.append(t(X(0) + 10, 24, "Flávio à frente →", 13, FLAVIO, weight="700"))
    for i, x in enumerate(casas):
        y = topo + i * passo + passo / 2
        a = x["erro_validos_do_total"]["pesquisa_f_menos_l"]
        m = x["margem_95_diferenca_aas_pp"]
        of = x.get("erro_validos_oficiais")
        rp = x.get("erro_reponderado")
        g = [ln(X(a - m), y, X(a + m), y, MARGEM, 5, ' stroke-linecap="round"')]
        xr = X(rp["pesquisa_f_menos_l"]) if rp else None
        if xr is not None and abs(xr - X(a)) > 8:
            g.append(
                f'<line x1="{X(a):.1f}" y1="{y:.1f}" x2="{xr:.1f}" y2="{y:.1f}" stroke="{INK}" '
                'stroke-width="1.3" marker-end="url(#p2-seta)"/>'
            )
        if xr is not None:
            g.append(f'<circle cx="{xr:.1f}" cy="{y:.1f}" r="5" fill="{CINZA_REP}"/>')
        if of:
            g.append(
                f'<circle cx="{X(of["pesquisa_f_menos_l"]):.1f}" cy="{y:.1f}" r="8" fill="none" '
                f'stroke="{GOLD}" stroke-width="1.8"/>'
            )
        g.append(f'<circle cx="{X(a):.1f}" cy="{y:.1f}" r="6" fill="{INK}"/>')
        xd = max(X(a + m), xr or 0) + 10
        g.append(t(xd, y + 5, _sn(a), 12.5, INK, mono=True, extra=HALO))
        linhas = [
            (
                "Publicado F × L",
                f"{num(x['publicado_total']['flavio'], 1)} × {num(x['publicado_total']['lula'], 1)}",
            ),
            ("F−L nos válidos", pp(a)),
            ("Afastamento da urna", pp(x["erro_validos_do_total"]["erro_f_menos_l"])),
            (
                "Válidos oficiais, F−L",
                pp(of["pesquisa_f_menos_l"]) if of else "não divulgados",
            ),
            ("Reponderado, F−L", pp(rp["pesquisa_f_menos_l"]) if rp else "sem PNAD"),
            ("Campo", f"{_dm(x['campo']['inicio'])} a {_dm(x['campo']['fim'])}"),
            (
                "Entrevistas · modo",
                f"{inteiro(x['n'])} · {x['modo'].replace('_', ' ')}",
            ),
            ("Margem 95% da diferença", f"±{num(m, 2)}"),
        ]
        k = tips.add(ficha(x["instituto"], x.get("registro_tse") or "", linhas))
        rot = t(esq - 12, y + 5, x["instituto"], 13.5, INK, "end")
        out.append(
            hit(area(10, y - passo / 2, W - 20, passo) + rot + "".join(g), k, foco=True)
        )
    ysep = topo + len(casas) * passo + 4
    out.append(ln(10, ysep, W - 20, ysep, INK, 1))
    for j, (nome, v, bloco) in enumerate(centrais):
        y = topo + (len(casas) + j) * passo + passo / 2 + 8
        xv = X(v)
        g = [
            f'<path d="M{xv:.1f} {y - 8:.1f}l8 8l-8 8l-8-8z" fill="{GOLD}"/>',
            t(xv + 14, y + 5, _sn(v), 12.5, INK, mono=True, extra=HALO),
        ]
        erro = v - u
        linhas = [("F−L", pp(v)), ("Afastamento da urna", pp(erro))]
        if bloco and "validos" in bloco:
            linhas.insert(
                0,
                (
                    "Flávio · Lula",
                    f"{num(bloco['validos']['flavio'], 2)} · {num(bloco['validos']['lula'], 2)}",
                ),
            )
        k = tips.add(ficha(nome, "central" if bloco else "média", linhas))
        rot = t(esq - 12, y + 5, nome, 13.5, INK, "end", "700")
        out.append(
            hit(area(10, y - passo / 2, W - 20, passo) + rot + "".join(g), k, foco=True)
        )
    out.append("</svg>")
    leg = legenda_html(
        [
            ("publicado (válidos pela regra da casa)", INK),
            ("válidos oficiais da casa (anel)", GOLD),
            ("reponderado por renda", CINZA_REP),
            ("margem de 95% da diferença", MARGEM),
            ("centrais (losango)", GOLD),
            ("urna", LULA),
        ]
    )
    res = PV["resumo"]
    legenda = (
        f"Última onda de cada casa, campo encerrado a partir de 19/10. {res['flavio_a_frente_nos_validos']} de "
        f"{res['n_casas']} punham Flávio à frente; a urna deu Lula {_sn(-u, 2)}. A seta vai do publicado ao "
        "reponderado pela PNAD. Fonte: pesquisas_vs_urna.json."
    )
    return figura_html(
        "p2t_casas_urna",
        "".join(out),
        legenda,
        tips,
        minw=860,
        dim=False,
        apos=leg,
        foco=(X(u) - 40, X(hi) - 10, X(u)),
    )


# ------------------------------------------------------------------ erro por casa


def fig_erro(PV: dict) -> str:
    casas = sorted(
        _ordenadas(PV), key=lambda x: -x["erro_validos_do_total"]["erro_f_menos_l"]
    )
    res = PV["resumo"]
    media = res["publicado_validos_do_total"]["media"]
    vmax = max(
        max(
            x["erro_validos_do_total"]["erro_f_menos_l"],
            x["margem_95_diferenca_aas_pp"],
        )
        for x in casas
    )
    vmax = math.ceil(vmax + 0.5)
    esq, topo, passo = 220, 60, 26
    base = topo + passo * len(casas) + 8
    h = base + 52
    X = escala(0, vmax, esq, W - 80)
    tips = Tips()
    out = [
        svg_abre(
            W,
            h,
            "Afastamento de cada casa em relação à urna, diferença Flávio menos Lula",
            "Barras do afastamento em relação à urna, da maior para a menor; traço vertical em cada linha é a "
            "margem de 95% da diferença; barra escura quando o afastamento passa da margem.",
        )
    ]
    for v in ticks(0, vmax, 8):
        out.append(ln(X(v), topo - 6, X(v), base, GRADE))
        out.append(t(X(v), base + 20, _sn(v, 0), 13, MUTED, "middle", mono=True))
    out.append(
        t(
            W - 80,
            base + 42,
            "afastamento em pontos dos válidos (F−L)",
            13,
            MUTED,
            "end",
        )
    )
    for i, x in enumerate(casas):
        y = topo + i * passo
        e = x["erro_validos_do_total"]["erro_f_menos_l"]
        m = x["margem_95_diferenca_aas_pp"]
        fora = x["erro_fora_da_margem_aas"]
        cor = FLAVIO if fora else AZUL_CLARO
        g = [
            r(X(0), y + 4, X(e) - X(0), passo - 8, cor),
            ln(X(m), y + 1, X(m), y + passo - 1, INK, 2.2),
            t(X(max(e, m)) + 12, y + passo / 2 + 5, _sn(e, 2), 12.5, INK, mono=True),
        ]
        k = tips.add(
            ficha(
                x["instituto"],
                x["modo"].replace("_", " "),
                [
                    ("Afastamento F−L", pp(e)),
                    ("Margem 95% da diferença", f"±{num(m, 2)}"),
                    ("Fora da margem", "sim" if fora else "não"),
                    ("Acertou o vencedor", "sim" if x["acertou_vencedor"] else "não"),
                ],
            )
        )
        rot = t(esq - 10, y + passo / 2 + 5, x["instituto"], 13.5, INK, "end")
        out.append(hit(area(10, y, W - 20, passo) + rot + "".join(g), k, foco=True))
    out.append(
        ln(X(media), topo - 14, X(media), base, GOLD, 1.8, ' stroke-dasharray="6 4"')
    )
    out.append(
        t(
            X(media),
            topo - 20,
            f"afastamento comum {_sn(media, 2)}",
            13.5,
            GOLD,
            "middle",
            "700",
        )
    )
    out.append("</svg>")
    leg = legenda_html(
        [
            ("afastamento fora da margem de 95%", FLAVIO),
            ("afastamento dentro da margem", AZUL_CLARO),
            ("margem da diferença (traço)", INK),
            ("afastamento comum das casas", GOLD),
        ]
    )
    legenda = (
        f"{res['fora_da_margem_aas']} de {res['n_casas']} afastamentos passam da margem de 95% da diferença "
        "sob amostragem simples, que é piso e não intervalo da casa. Fonte: pesquisas_vs_urna.json."
    )
    return figura_html(
        "p2t_erro_casas", "".join(out), legenda, tips, minw=760, dim=False, apos=leg
    )
