"""Figuras dos capítulos 6 a 9: Câmara, Senado, assembleias e o vão estadual.

Campo é classificação editorial da casa (`apuracao/public/campos.json`); tucano
é centro-esquerda. Os assentos vão da esquerda para a direita na ordem dos campos,
e as linhas de referência contam a partir da direita: na Câmara, maioria absoluta
(257) e três quintos (308); no Senado, maioria (41), três quintos (49) e dois
terços (54).
"""

from __future__ import annotations

import math

from senado_2026.pagina import hemiciclo as HEMI81

from .pagina_comum import NOME_UF, inteiro, num
from .pagina_fig_base import (
    CAMPOS,
    COR_PARTIDO,
    GRADE,
    INK,
    MUTED,
    PAPER,
    Tips,
    W,
    area,
    botoes,
    campo_nome,
    cor_campo,
    dado,
    escala,
    ficha,
    figura_html,
    hit,
    legenda,
    ln,
    nome_bonito,
    pct,
    pp,
    r,
    registra,
    sobre,
    svg_abre,
    t,
    ticks,
)

CINZA_2022 = "#c9c3b3"


def _ci(campo: str | None) -> int:
    return CAMPOS.index(campo) if campo in CAMPOS else 2


def cor_partido(p: str, campo: str | None) -> str:
    return COR_PARTIDO.get(p, cor_campo(campo))


def posicoes(
    n: int, cx: float, cy: float, r1: float, r0: float, fileiras: int
) -> list[tuple[float, float, float]]:
    """Assentos de um hemiciclo, ordenados da esquerda para a direita: (ângulo, x, y)."""
    raios = [r0 + (r1 - r0) * i / (fileiras - 1) for i in range(fileiras)]
    soma = sum(raios)
    qtd = [round(n * rr / soma) for rr in raios]
    qtd[-1] += n - sum(qtd)
    out = []
    for rr, q in zip(raios, qtd, strict=True):
        for k in range(q):
            ang = math.pi * (1 - k / max(q - 1, 1))
            out.append((ang, rr, cx + rr * math.cos(ang), cy - rr * math.sin(ang)))
    out.sort(key=lambda s: (-round(s[0], 6), s[1]))
    return [(a, x, y) for a, _, x, y in out]


def linha_limiar(
    seats: list[tuple[float, float, float]],
    k_direita: int,
    cx: float,
    cy: float,
    r0: float,
    r1: float,
    rotulo: str,
    lado: str = "end",
) -> str:
    """Linha radial depois do k-ésimo assento contado da direita."""
    n = len(seats)
    a = (seats[n - k_direita][0] + seats[n - k_direita - 1][0]) / 2
    x1, y1 = cx + (r0 - 16) * math.cos(a), cy - (r0 - 16) * math.sin(a)
    x2, y2 = cx + (r1 + 22) * math.cos(a), cy - (r1 + 22) * math.sin(a)
    tx, ty = cx + (r1 + 30) * math.cos(a), cy - (r1 + 30) * math.sin(a)
    return ln(x1, y1, x2, y2, INK, 1.6, ' stroke-dasharray="5 4"') + t(
        tx, ty, rotulo, 13, INK, lado, "700"
    )


# ------------------------------------------------------------------ Câmara


@registra("hemiciclo_camara")
def hemiciclo_camara(d, **_op) -> str:
    C = dado(d, "camara")
    deps = []
    for u in C["ufs"]:
        for e in u["eleitos"]:
            deps.append(dict(e, uf=u["uf"], fonte=u["fonte"]))
    tam = {}
    for e in deps:
        tam[e["partido"]] = tam.get(e["partido"], 0) + 1
    deps.sort(
        key=lambda e: (_ci(e["campo"]), -tam[e["partido"]], e["partido"], -e["votos"])
    )
    n = len(deps)
    cx, cy, r1, r0 = W / 2, 560, 520, 190
    seats = posicoes(n, cx, cy, r1, r0, 12)
    raio = 8.6
    h = cy + 120
    out = [
        svg_abre(
            W,
            h,
            f"Câmara dos Deputados eleita em 2026: {n} cadeiras por campo",
            "Cada círculo é um deputado eleito; linhas tracejadas marcam a maioria absoluta (257) e três quintos (308) contados a partir da direita.",
        )
    ]
    linhas = []
    for i, (e, (_, x, y)) in enumerate(zip(deps, seats, strict=True)):
        cor = cor_campo(e["campo"])
        cp = cor_partido(e["partido"], e["campo"])
        out.append(
            f'<circle class="hit" data-k="r{i}" cx="{x:.1f}" cy="{y:.1f}" r="{raio}" fill="{cor}" '
            f'data-af="partido>{cp}" stroke="{PAPER}" stroke-width="1"/>'
        )
        linhas.append(
            [
                nome_bonito(e["nome"]),
                f"{e['partido']} · {campo_nome(e['campo'])}",
                NOME_UF[e["uf"]],
                f"{inteiro(e['votos'])} ({num(e['pct'], 2)}% na UF)",
                e.get("st")
                or ("eleito" if e["fonte"] == "tse" else "eleito, alocação provisória"),
            ]
        )
    out.append(linha_limiar(seats, 257, cx, cy, r0, r1, "257 maioria", "end"))
    out.append(linha_limiar(seats, 308, cx, cy, r0, r1, "308 três quintos", "end"))
    b = C["blocos"]
    out.append(
        t(
            cx,
            cy - 92,
            str(n),
            54,
            INK,
            "middle",
            "500",
            extra=' font-family="Fraunces, Georgia, serif"',
        )
    )
    out.append(t(cx, cy - 64, "deputados", 15, MUTED, "middle"))
    out.append(
        t(
            cx,
            cy - 30,
            f"direita + centro-direita: {b['direita + centro-direita']}",
            15,
            INK,
            "middle",
            "700",
        )
    )
    out.append(
        t(
            cx,
            cy - 8,
            f"centro: {b['centro']} · esquerda + centro-esquerda: {b['esquerda + centro-esquerda']}",
            14,
            INK,
            "middle",
        )
    )
    leg_campo = [(f"{campo_nome(c)} {C['por_campo'][c]}", cor_campo(c)) for c in CAMPOS]
    partidos = sorted(C["por_partido"].items(), key=lambda kv: -kv[1])
    campo_de = {e["partido"]: e["campo"] for e in deps}
    leg_part = [(f"{p} {q}", cor_partido(p, campo_de.get(p))) for p, q in partidos[:14]]
    out.append(f'<g data-alt-show="campo">{legenda(leg_campo, 40, h - 40)}</g>')
    out.append(
        f'<g data-alt-show="partido" display="none">{legenda(leg_part[:7], 40, h - 52)}{legenda(leg_part[7:], 40, h - 26)}</g>'
    )
    out.append("</svg>")
    tips = Tips()
    tips.tabela(["Deputado", "Partido", "UF", "Votos", "Situação"], linhas, sub=1)
    ctl = botoes([("campo", "Por campo"), ("partido", "Por partido")], "campo", "Cor")
    prov = ", ".join(C["ufs_provisorias"])
    legenda_ = (
        f"As {n} cadeiras, da esquerda para a direita por campo e partido. O bloco direita e centro-direita soma "
        f"{b['direita + centro-direita']}: passa da maioria absoluta (257) e fica abaixo dos três quintos (308) de emenda "
        f"constitucional. Em {prov} a distribuição é provisória, pelo quociente. Fonte: camara.json."
    )
    return figura_html(
        "hemiciclo_camara",
        "".join(out),
        legenda_,
        tips,
        controles=ctl,
        minw=720,
        dim=False,
    )


@registra("camara_partidos")
def camara_partidos(d, **_op) -> str:
    C = dado(d, "comparacao_2022")["camara"]
    partidos = sorted(C["partidos"], key=lambda p: -p["cadeiras_2026"])[:14]
    esq, topo, passo = 170, 60, 40
    h = topo + passo * len(partidos) + 40
    vmax = (
        math.ceil(
            max(max(p["cadeiras_2026"], p["cadeiras_2022"]) for p in partidos) / 20
        )
        * 20
    )
    X = escala(0, vmax, esq, W - 170)
    out = [
        svg_abre(
            W,
            h,
            "As 14 maiores bancadas: cadeiras eleitas em 2022 e em 2026",
            "Barra clara 2022, barra na cor do partido 2026, com a variação à direita.",
        ),
        legenda([("eleitos em 2022", CINZA_2022), ("eleitos em 2026", INK)], esq, 24),
    ]
    for v in ticks(0, vmax, 6):
        out.append(ln(X(v), topo - 6, X(v), h - 34, GRADE))
        out.append(t(X(v), h - 14, num(v, 0), 13, MUTED, "middle", mono=True))
    tips = Tips()
    for i, p in enumerate(partidos):
        y = topo + i * passo
        cor = cor_partido(p["partido"], p["campo"])
        delta = p["delta_cadeiras"]
        corpo = (
            t(esq - 12, y + 22, p["partido"], 14, INK, "end", "700")
            + r(esq, y + 4, X(p["cadeiras_2022"]) - esq, 13, CINZA_2022)
            + r(esq, y + 18, X(p["cadeiras_2026"]) - esq, 15, cor)
            + t(
                X(max(p["cadeiras_2026"], p["cadeiras_2022"])) + 8,
                y + 24,
                f"{p['cadeiras_2026']} ({'+' if delta > 0 else '−' if delta < 0 else ''}{abs(delta)})",
                14,
                INK,
                mono=True,
            )
        )
        k = tips.add(
            ficha(
                p["partido"],
                campo_nome(p["campo"]),
                [
                    (
                        "Cadeiras 2022 → 2026",
                        f"{p['cadeiras_2022']} → {p['cadeiras_2026']}",
                    ),
                    (
                        "Variação",
                        f"{'+' if delta > 0 else '−' if delta < 0 else ''}{abs(delta)}",
                    ),
                    (
                        "Votos 2022",
                        f"{inteiro(p['votos_2022'])} ({num(p['pct_votos_2022'], 1)}%)",
                    ),
                    (
                        "Votos 2026",
                        f"{inteiro(p['votos_2026'])} ({num(p['pct_votos_2026'], 1)}%)",
                    ),
                ],
                "2022 com a sigla de 2026 (fusões e incorporações)",
            )
        )
        out.append(hit(area(0, y, W, passo) + corpo, k, foco=True))
    out.append("</svg>")
    legenda_ = (
        "Bancadas eleitas, 2022 contra 2026. Siglas de 2022 levadas às de 2026 pela tabela de sucessores "
        "(PSL e DEM no União, PSC no Podemos, PTB e Patriota no PRD). Fonte: comparacao_2022.json."
    )
    return figura_html("camara_partidos", "".join(out), legenda_, tips, minw=760)


def _barra_campos(
    y: float,
    esq: float,
    larg: float,
    valores: dict,
    alt: float,
    fmt,
    tips: Tips,
    titulo: str,
    absolutos: dict | None = None,
) -> str:
    out, x = [], esq
    tot = sum(valores.get(c, 0) for c in CAMPOS) or 1
    for c in CAMPOS:
        v = valores.get(c, 0)
        w = larg * v / tot
        if w <= 0:
            continue
        cor = cor_campo(c)
        corpo = r(x, y, w, alt, cor, f' stroke="{PAPER}" stroke-width="1"')
        if w > 44:
            corpo += t(
                x + w / 2,
                y + alt / 2 + 5,
                fmt(v),
                13,
                sobre(cor),
                "middle",
                "700",
                mono=True,
            )
        linhas = [("Parcela", pct(100 * v / tot, 1))]
        if absolutos:
            linhas.insert(0, ("Total", inteiro(absolutos.get(c, 0))))
        k = tips.add(ficha(campo_nome(c), titulo, linhas))
        out.append(hit(corpo, k))
        x += w
    return "".join(out)


def _pct1(v: float) -> str:
    return f"{num(v, 1)}%"


@registra("votos_x_cadeiras")
def votos_x_cadeiras(d, **_op) -> str:
    C = dado(d, "comparacao_2022")["camara"]
    esq, topo, passo, larg = 190, 70, 56, W - 190 - 60
    linhas_ = [
        (
            "Votos, 2022",
            {c: C["votos_por_campo_2022"][c]["pct"] for c in CAMPOS},
            {c: C["votos_por_campo_2022"][c]["votos"] for c in CAMPOS},
        ),
        ("Cadeiras, 2022", C["por_campo_2022"], C["por_campo_2022"]),
        (
            "Votos, 2026",
            {c: C["votos_por_campo_2026"][c]["pct"] for c in CAMPOS},
            {c: C["votos_por_campo_2026"][c]["votos"] for c in CAMPOS},
        ),
        ("Cadeiras, 2026", C["por_campo_2026"], C["por_campo_2026"]),
    ]
    h = topo + passo * len(linhas_) + 40
    out = [
        svg_abre(
            W,
            h,
            "Votos e cadeiras por campo na Câmara, 2022 e 2026",
            "Barras 100%: parcela dos votos de partido e parcela das cadeiras; linhas a 257 e 308 cadeiras contadas da direita.",
        ),
        legenda([(campo_nome(c), cor_campo(c)) for c in CAMPOS], esq, 24),
    ]
    tips = Tips()
    for i, (rot, vals, abs_) in enumerate(linhas_):
        y = topo + i * passo
        out.append(
            t(
                esq - 12,
                y + 25,
                rot,
                14,
                INK,
                "end",
                "700" if "Cadeiras" in rot else None,
            )
        )
        cad = "Cadeiras" in rot
        out.append(
            _barra_campos(
                y, esq, larg, vals, 36, inteiro if cad else _pct1, tips, rot, abs_
            )
        )
    for k_, rot, yy, anc in (
        (257, "maioria: 257", h - 14, "start"),
        (308, "três quintos: 308", h - 14, "end"),
    ):
        x = esq + larg * (1 - k_ / 513)
        out.append(
            ln(
                x,
                topo - 12,
                x,
                topo + passo * len(linhas_) - 14,
                INK,
                1.6,
                ' stroke-dasharray="5 4"',
            )
        )
        out.append(t(x + (6 if anc == "start" else -6), yy, rot, 13, INK, anc, "700"))
    out.append("</svg>")
    b26 = C["por_bloco_2026"]
    legenda_ = (
        f"Em 2026 a direita teve {num(C['votos_por_campo_2026']['direita']['pct'], 1)}% dos votos de partido e "
        f"{C['por_campo_2026']['direita']} cadeiras. O bloco direita e centro-direita tem {b26['direita + centro-direita']} "
        "cadeiras: as linhas mostram onde ficam 257 e 308 contadas a partir da direita. Fonte: comparacao_2022.json."
    )
    return figura_html(
        "votos_x_cadeiras", "".join(out), legenda_, tips, minw=760, dim=False
    )


@registra("camara_por_uf")
def camara_por_uf(d, **_op) -> str:
    C = dado(d, "camara")
    ufs = sorted(
        C["ufs"],
        key=lambda u: -(
            u["por_campo"].get("direita", 0) + u["por_campo"].get("centro-direita", 0)
        )
        / u["vagas"],
    )
    esq, topo, passo, larg = 210, 60, 30, W - 210 - 150
    h = topo + passo * len(ufs) + 40
    out = [
        svg_abre(
            W,
            h,
            "Câmara por UF: cadeiras de cada campo",
            "Barras 100% por UF, ordenadas pela parcela da direita e centro-direita; à direita, número de vagas.",
        ),
        legenda([(campo_nome(c), cor_campo(c)) for c in CAMPOS], esq, 24),
        t(esq + larg + 16, topo - 10, "vagas", 13, MUTED),
    ]
    tips = Tips()
    for i, u in enumerate(ufs):
        y = topo + i * passo
        x = esq
        corpo = [t(esq - 12, y + 19, NOME_UF[u["uf"]], 14, INK, "end")]
        for c in CAMPOS:
            v = u["por_campo"].get(c, 0)
            w = larg * v / u["vagas"]
            if w <= 0:
                continue
            cor = cor_campo(c)
            corpo.append(
                r(x, y + 2, w, passo - 6, cor, f' stroke="{PAPER}" stroke-width="1"')
            )
            if w > 22:
                corpo.append(
                    t(
                        x + w / 2,
                        y + passo / 2 + 4,
                        str(v),
                        13,
                        sobre(cor),
                        "middle",
                        "700",
                        mono=True,
                    )
                )
            x += w
        prov = u["fonte"] != "tse"
        corpo.append(
            t(
                esq + larg + 16,
                y + 19,
                f"{u['vagas']}{' *' if prov else ''}",
                14,
                INK,
                mono=True,
            )
        )
        partidos = sorted(u["por_partido"].items(), key=lambda kv: -kv[1])
        k = tips.add(
            ficha(
                f"{NOME_UF[u['uf']]} ({u['uf']})",
                f"{u['vagas']} vagas · {'provisória' if prov else 'TSE'}",
                [
                    (campo_nome(c), str(u["por_campo"].get(c, 0)))
                    for c in CAMPOS
                    if u["por_campo"].get(c)
                ]
                + [("Partidos", ", ".join(f"{p} {q}" for p, q in partidos[:6]))],
            )
        )
        out.append(hit(area(0, y, W, passo) + "".join(corpo), k))
    out.append(
        ln(
            esq + larg / 2,
            topo - 4,
            esq + larg / 2,
            topo + passo * len(ufs),
            INK,
            1,
            ' stroke-dasharray="3 3"',
        )
    )
    out.append("</svg>")
    legenda_ = (
        "Cadeiras por campo em cada UF, ordenadas pela parcela da direita e centro-direita; a linha marca metade das vagas. "
        f"Asterisco: distribuição provisória pelo quociente ({', '.join(C['ufs_provisorias'])}). Fonte: camara.json."
    )
    return figura_html("camara_por_uf", "".join(out), legenda_, tips, minw=760)


# ------------------------------------------------------------------ Senado


def _senadores(lista: list[dict], ano: str, contorno: bool) -> list[dict]:
    return [dict(s, ano=ano, contorno=contorno) for s in lista]


@registra("hemiciclo_senado")
def hemiciclo_senado(d, **_op) -> str:
    S = dado(d, "senado")
    CS = dado(d, "comparacao_2022")["senado"]
    comp = {
        "2027": _senadores(CS["classe_2022"], "2022", True)
        + _senadores(S["eleitos_2026"], "2026", False),
        "2023": _senadores(CS["classe_2022"], "2022", True)
        + _senadores(CS["classe_2018"], "2018", False),
    }
    pos = HEMI81.posicoes()
    w0, h0 = HEMI81.W, HEMI81.H
    w, h = w0, h0 + 96
    cx, cy = HEMI81.CX, HEMI81.CY
    angs = [(math.atan2(cy - y, x - cx), x, y) for x, y in pos]
    out = [
        svg_abre(
            w,
            h,
            "Senado: composição de 2027 e de 2023 por campo",
            "81 assentos; contorno para os eleitos em 2022, cheio para os eleitos na eleição seguinte; linhas a 41, 49 e 54.",
        )
    ]
    tips = Tips()
    rr = HEMI81.RAIO_ASSENTO
    for ano, lista in comp.items():
        lista.sort(key=lambda s: (_ci(s["campo"]), not s["contorno"], s["partido"]))
        g = []
        for s, (x, y) in zip(lista, pos, strict=True):
            cor = cor_campo(s["campo"])
            attrs = (
                f'fill="#fffdf8" stroke="{cor}" stroke-width="3.2"'
                if s["contorno"]
                else f'fill="{cor}" stroke="{cor}" stroke-width="1"'
            )
            k = tips.add(
                ficha(
                    nome_bonito(s["nome"]),
                    f"{s['partido']} · {s['uf']}",
                    [
                        ("Campo", campo_nome(s["campo"])),
                        ("Eleito em", s["ano"]),
                        ("Votos", inteiro(s.get("votos"))),
                        (
                            "Mandato até",
                            (
                                "2031"
                                if s["ano"] == "2022"
                                else "2035" if s["ano"] == "2026" else "2027"
                            ),
                        ),
                    ],
                )
            )
            g.append(hit(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rr}" {attrs}/>', k))
        mostra = "" if ano == "2027" else ' display="none"'
        cont = {c: sum(1 for s in lista if s["campo"] == c) for c in CAMPOS}
        bloco = cont["direita"] + cont["centro-direita"]
        g.append(
            t(
                cx,
                cy - 42,
                f"direita + centro-direita: {bloco}",
                14,
                INK,
                "middle",
                "700",
            )
        )
        g.append(t(cx, cy - 20, f"de 81 em {ano}", 14, MUTED, "middle"))
        leg = [(f"{campo_nome(c)} {cont[c]}", cor_campo(c)) for c in CAMPOS]
        g.append(legenda(leg[:3], 20, h - 50, 13) + legenda(leg[3:], 20, h - 26, 13))
        out.append(f'<g data-alt-show="{ano}"{mostra}>{"".join(g)}</g>')
    angs_ord = sorted(angs, key=lambda a: -a[0])
    n = len(angs_ord)
    for k_, rot in ((41, "41"), (49, "49: 3/5"), (54, "54: 2/3")):
        a = (angs_ord[n - k_][0] + angs_ord[n - k_ - 1][0]) / 2
        r_in, r_out = HEMI81.RAIOS[0] - 18, HEMI81.RAIOS[-1] + 24
        out.append(
            ln(
                cx + r_in * math.cos(a),
                cy - r_in * math.sin(a),
                cx + r_out * math.cos(a),
                cy - r_out * math.sin(a),
                INK,
                1.5,
                ' stroke-dasharray="4 3"',
            )
        )
        out.append(
            t(
                cx + (r_out + 6) * math.cos(a),
                cy - (r_out + 6) * math.sin(a),
                rot,
                13,
                INK,
                "start",
                "700",
            )
        )
    out.append(t(w - 20, h - 26, "contorno: eleito em 2022", 13, MUTED, "end"))
    out.append("</svg>")
    ctl = botoes(
        [("2027", "Senado de 2027"), ("2023", "Senado de 2023")], "2027", "Composição"
    )
    s27 = S["senado_2027"]
    legenda_ = (
        f"Senado de 2027: {s27['por_bloco']['direita + centro-direita']} assentos de direita e centro-direita, acima dos 49 "
        "de três quintos. Assento com contorno: eleito em 2022 (eleito da urna, não o titular atual). Linhas contadas a "
        "partir da direita. Fonte: senado.json e comparacao_2022.json."
    )
    return figura_html(
        "hemiciclo_senado",
        "".join(out),
        legenda_,
        tips,
        controles=ctl,
        modo="fit",
        dim=False,
    )


@registra("senado_segundas_vagas")
def senado_segundas_vagas(d, **_op) -> str:
    S = dado(d, "senado")
    seg = {e["uf"]: e for e in S["eleitos_2026"] if e["vaga"] == 2}
    disp = sorted(S["disputas"], key=lambda x: x["margem_2a_vaga_pp"])
    esq, topo, passo = 70, 50, 30
    h = topo + passo * len(disp) + 40
    vmax = math.ceil(max(x["margem_2a_vaga_pp"] for x in disp) / 2) * 2
    X = escala(0, vmax, esq, W - 470)
    out = [
        svg_abre(
            W,
            h,
            "Senado: distância entre o 2º eleito e o 3º colocado, por UF",
            "Barras em pontos percentuais dos votos, da disputa mais apertada para a mais folgada; cor do campo do 2º eleito.",
        ),
        t(X(vmax) + 16, 30, "2º eleito × 3º colocado", 13, MUTED),
    ]
    for v in ticks(0, vmax, 6):
        out.append(ln(X(v), topo - 6, X(v), h - 34, GRADE))
        out.append(t(X(v), h - 14, f"{num(v, 0)} pp", 13, MUTED, "middle", mono=True))
    tips = Tips()
    for i, x in enumerate(disp):
        y = topo + i * passo
        e = seg.get(x["uf"], {})
        te = x["terceiro"]
        cor = cor_campo(e.get("campo"))
        corpo = (
            t(esq - 12, y + 19, x["uf"], 14, INK, "end", "700")
            + r(esq, y + 5, max(X(x["margem_2a_vaga_pp"]) - esq, 2), passo - 10, cor)
            + t(
                X(x["margem_2a_vaga_pp"]) + 8,
                y + 19,
                num(x["margem_2a_vaga_pp"], 2),
                13,
                INK,
                mono=True,
            )
            + t(
                X(vmax) + 16,
                y + 19,
                f"{nome_bonito(e.get('nome', '?'))} × {nome_bonito(te['nome'])}",
                13,
                INK,
            )
        )
        k = tips.add(
            ficha(
                f"{NOME_UF[x['uf']]} ({x['uf']})",
                "fonte TSE" if x["fonte"] == "tse" else "provisória",
                [
                    (
                        "2º eleito",
                        f"{nome_bonito(e.get('nome', '?'))} ({e.get('partido', '?')}) {pct(e.get('pct'))}",
                    ),
                    (
                        "3º colocado",
                        f"{nome_bonito(te['nome'])} ({te['partido']}) {pct(te['pct'])}",
                    ),
                    (
                        "Distância",
                        f"{pp(x['margem_2a_vaga_pp'])} · {inteiro(x['margem_2a_vaga_votos'])} votos",
                    ),
                    (
                        "Campo do 2º · do 3º",
                        f"{campo_nome(e.get('campo'))} · {campo_nome(te['campo'])}",
                    ),
                ],
            )
        )
        out.append(hit(area(0, y, W, passo) + corpo, k))
    out.append(
        legenda([(campo_nome(c), cor_campo(c)) for c in CAMPOS], esq + 140, 24, 13)
    )
    out.append("</svg>")
    a = disp[0]
    legenda_ = (
        f"A segunda vaga mais apertada foi em {NOME_UF[a['uf']]}: {num(a['margem_2a_vaga_pp'], 2)} ponto, "
        f"{inteiro(a['margem_2a_vaga_votos'])} votos. Cor: campo do 2º eleito. Fonte: senado.json."
    )
    return figura_html("senado_segundas_vagas", "".join(out), legenda_, tips, minw=820)


# ------------------------------------------------------------------ assembleias


@registra("assembleias_campo")
def assembleias_campo(d, **_op) -> str:
    A = dado(d, "comparacao_2022")["assembleias"]
    casas = A["casas"]
    esq, topo, larg = 150, 60, W - 150 - 120
    bar, gap = 22, 20
    h = topo + len(casas) * (2 * bar + 6 + gap) + 30
    out = [
        svg_abre(
            W,
            h,
            "Assembleias legislativas: cadeiras por campo, 2022 e 2026",
            "Duas barras 100% por casa, 2022 em cima e 2026 embaixo; linha a metade das cadeiras.",
        ),
        legenda([(campo_nome(c), cor_campo(c)) for c in CAMPOS], esq, 24),
    ]
    tips = Tips()
    y = topo
    for c in casas:
        out.append(t(esq - 12, y + bar + 8, NOME_UF[c["uf"]], 14, INK, "end", "700"))
        for j, ano in enumerate(("2022", "2026")):
            yy = y + j * (bar + 6)
            vals = c[f"por_campo_{ano}"]
            out.append(t(esq + larg + 12, yy + 16, ano, 13, MUTED, mono=True))
            out.append(
                _barra_campos(
                    yy, esq, larg, vals, bar, inteiro, tips, f"{c['uf']}, {ano}", vals
                )
            )
        b22, b26 = c["por_bloco_2022"], c["por_bloco_2026"]
        x = esq + larg / 2
        out.append(ln(x, y - 3, x, y + 2 * bar + 9, INK, 1, ' stroke-dasharray="3 3"'))
        out.append(
            f'<g><title>{NOME_UF[c["uf"]]}: direita e centro-direita {b22["direita + centro-direita"]} em 2022, '
            f'{b26["direita + centro-direita"]} em 2026, de {c["vagas"]}</title></g>'
        )
        y += 2 * bar + 6 + gap
    out.append("</svg>")
    o = A["onze_casas"]
    legenda_ = (
        f"Onze casas, {o['vagas']} cadeiras. Direita: {o['por_campo_2022']['direita']} em 2022, {o['por_campo_2026']['direita']} "
        f"em 2026; centro-direita: {o['por_campo_2022']['centro-direita']} e {o['por_campo_2026']['centro-direita']}. "
        "A linha tracejada marca metade das cadeiras. Fonte: comparacao_2022.json."
    )
    return figura_html("assembleias_campo", "".join(out), legenda_, tips, minw=760)


# ------------------------------------------------------------------ vão estadual


@registra("vao_estadual")
def vao_estadual(d, **_op) -> str:
    G = dado(d, "governadores")
    V = G["vao_estadual"]
    lista = sorted(V["lista"], key=lambda x: -x["vao_pp"])
    try:
        aliados = {
            a["uf"]: a for a in dado(d, "estrategia_2t")["governadores"]["aliados"]
        }
    except KeyError:
        aliados = {}
    esq, topo, passo = 430, 60, 28
    base = topo + passo * len(lista)
    h = base + 92
    vmax = math.ceil(max(abs(x["vao_pp"]) for x in lista) / 10) * 10
    X = escala(-vmax, vmax, esq, W - 60)
    x0 = X(0)
    hachura = (
        '<defs><pattern id="vao-sem-apoio" width="7" height="7" patternUnits="userSpaceOnUse" '
        'patternTransform="rotate(45)"><rect width="7" height="7" fill="#efe9d8"/>'
        f'<rect width="3" height="7" fill="{cor_campo("centro")}"/></pattern></defs>'
    )
    out = [
        svg_abre(
            W,
            h,
            "Vão estadual: governador menos o finalista presidencial do lado dele",
            "Barras em pontos dos válidos; positivo, a candidatura ao governo teve parcela maior que o finalista "
            "comparado na mesma UF. Centro contra o finalista que a coligação apoiou; hachura, sem apoio declarado.",
        ),
        hachura,
        t(x0 + 8, 30, "governador à frente →", 13, MUTED),
        t(x0 - 8, 30, "← presidenciável à frente", 13, MUTED, "end"),
    ]
    for v in ticks(-vmax, vmax, 8):
        out.append(ln(X(v), topo - 6, X(v), base, GRADE))
        out.append(
            t(
                X(v),
                base + 20,
                f"{'+' if v > 0 else '−' if v < 0 else ''}{num(abs(v), 0)}",
                13,
                MUTED,
                "middle",
                mono=True,
            )
        )
    out.append(ln(x0, topo - 6, x0, base, INK, 1.4))
    tips = Tips()
    for i, x in enumerate(lista):
        y = topo + i * passo
        uf = x["uf"].upper()
        v = x["vao_pp"]
        sem_apoio = x.get("comparacao") == "sem apoio declarado"
        cor = "url(#vao-sem-apoio)" if sem_apoio else cor_campo(x["campo"])
        xa, xb = sorted((x0, X(v)))
        contra = "Flávio" if x.get("finalista", "flavio") == "flavio" else "Lula"
        rot = f"{uf} · {nome_bonito(x['governador'])} ({x['partido']}) × {contra}"
        extra = f' stroke="{cor_campo("centro")}" stroke-width="1"' if sem_apoio else ""
        corpo = (
            t(esq - 12, y + 19, rot, 13.5, INK, "end")
            + r(xa, y + 5, xb - xa, passo - 10, cor, extra)
            + t(
                X(v) + (6 if v >= 0 else -6),
                y + 19,
                pp(v, 1)[:-3],
                13,
                INK,
                "start" if v >= 0 else "end",
                mono=True,
            )
        )
        linhas = [
            ("Governador", f"{pct(x['pct_governador'])}"),
            ("Flávio", pct(x.get("pct_flavio"))),
            ("Lula", pct(x.get("pct_lula"))),
            ("Contra Flávio", pp(x.get("vao_flavio_pp"))),
            ("Contra Lula", pp(x.get("vao_lula_pp"))),
            ("Comparado com", f"{contra} ({x.get('comparacao', 'mesmo bloco')})"),
            ("Campo", campo_nome(x["campo"])),
        ]
        al = aliados.get(uf)
        if al and nome_bonito(al["governador"]) == nome_bonito(x["governador"]):
            linhas.append(
                (
                    "Em votos",
                    f"{inteiro(al['governador_votos'])} × {inteiro(al['flavio_votos'])}",
                )
            )
        k = tips.add(
            ficha(
                f"{NOME_UF[uf]}: {nome_bonito(x['governador'])}",
                "teto endereçável, não transferência",
                linhas,
                (
                    x.get("evidencia", "")
                    if x.get("evidencia") != "regra do bloco"
                    else ""
                ),
            )
        )
        out.append(hit(area(0, y, W, passo) + corpo, k))
    out.append(
        legenda([(campo_nome(c), cor_campo(c)) for c in CAMPOS], esq, base + 52, 13)
        + r(
            esq,
            base + 67,
            13,
            13,
            "url(#vao-sem-apoio)",
            f' stroke="{cor_campo("centro")}"',
        )
        + t(esq + 18, base + 78, "centro sem apoio declarado, comparado com Flávio", 13)
    )
    out.append("</svg>")
    centro = V.get("centro", [])
    contra_lula = [c["uf"] for c in centro if c["comparado_com"] == "LULA"]
    contra_fl = [c["uf"] for c in centro if c["comparacao"] == "coligação com o PL"]
    sem = [c["uf"] for c in centro if c["comparacao"] == "sem apoio declarado"]
    legenda_ = (
        f"Parcela da candidatura ao governo (eleita ou no 2º turno, {V.get('n_ufs', 27)} UFs) menos a do finalista "
        "presidencial do lado dela, na mesma UF e na mesma urna. Direita e centro-direita contra Flávio; esquerda e "
        "centro-esquerda contra Lula. Centro contra o finalista que a coligação registrada no TSE apoiou: Lula em "
        f"{', '.join(contra_lula)}; Flávio em {', '.join(contra_fl)}. Sem PT nem PL na coligação e sem alinhamento "
        f"declarado ({', '.join(sem)}): comparado com Flávio, em hachura. A ficha traz as duas diferenças. "
        f"Cor: campo do governador. {G['rotulo_obrigatorio_vao'].capitalize()}. Fonte: governadores.json."
    )
    return figura_html("vao_estadual", "".join(out), legenda_, tips, minw=860)
