"""Figuras do capítulo "O que entrou cedo e o que entrou tarde" (2º turno de 2026).

Fonte: ``cedo_tarde.json`` (decis de municípios e de zonas, transição de ordem
entre turnos, últimos 50) e, quando existe, ``linha_do_tempo.json``
(``conclusao_ufs``: minuto em que cada UF fechou nos dois turnos).
"""

from __future__ import annotations

from apuracao_2026.pagina_comum import inteiro, num
from apuracao_2026.pagina_fig_base import (
    FLAVIO,
    GRADE,
    HALO,
    INK,
    LINE,
    LULA,
    MUTED,
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
    rot_hora,
    sobre,
    svg_abre,
    t,
    ticks,
)
from apuracao_2026.pagina_mapas import mapa_uf

from .pagina_fig_turnos_util import faixa, nome_uf

T1 = "#8a7a3a"
HORAS = ["#ece6d4", "#c5dccf", "#7fb19e", "#2f7a66", "#0d3f35"]
CORTES_HORA: list[float] = [21 * 60 + 15, 21 * 60 + 30, 21 * 60 + 45, 22 * 60]
ROT_HORA = [
    "até 21:15",
    "21:15 a 21:30",
    "21:30 a 21:45",
    "21:45 a 22:00",
    "depois de 22:00",
]


def _painel_decis(decis: list[dict], ident: str, mostra: bool, tips: Tips) -> str:
    """Os dois candidatos, dois turnos e mudanças com escalas compartilhadas."""
    h, x0, x1 = 600, 80, 980
    ya0, ya1, yb0, yb1 = 70, 315, 390, 525
    niveis = [
        v
        for dd in decis
        for k in ("h2h_flavio", "t1_h2h_flavio")
        for v in (dd[k], 100 - dd[k])
    ]
    lo, hi = min(niveis) - 1.5, max(niveis) + 1.5
    fy = escala(lo, hi, ya1, ya0)
    lim = max(1, max(abs(dd["swing_h2h_flavio_pp"]) for dd in decis) * 1.35)
    fs = escala(-lim, lim, yb1, yb0)
    passo = (x1 - x0) / len(decis)
    fx = [x0 + passo * (i + 0.5) for i in range(len(decis))]
    out = [
        f'<g data-alt-show="{ident}"{"" if mostra else " display=none"}>',
        t(x0, 30, "Participação entre os dois finalistas, %", 14, INK, weight="700"),
    ]
    for v in ticks(lo, hi, 5):
        out += [
            ln(x0, fy(v), x1, fy(v), GRADE, 1),
            t(x0 - 8, fy(v) + 4, num(v, 0), 12, MUTED, "end", mono=True),
        ]
    out.append(ln(x0, fy(50), x1, fy(50), INK, 1.2, ' stroke-dasharray="5 4"'))
    for candidato, cor in (("Flávio", FLAVIO), ("Lula", LULA)):
        for chave, tr in (
            ("t1_h2h_flavio", ' stroke-dasharray="7 5" stroke-opacity="0.65"'),
            ("h2h_flavio", ""),
        ):
            vals = [
                dd[chave] if candidato == "Flávio" else 100 - dd[chave] for dd in decis
            ]
            pts = " ".join(f"{fx[i]:.1f},{fy(v):.1f}" for i, v in enumerate(vals))
            out.append(
                f'<polyline data-candidato="{candidato}" points="{pts}" fill="none" stroke="{cor}" stroke-width="2.4"{tr}/>'
            )
            if chave == "h2h_flavio":
                for i, v in enumerate(vals):
                    out += [
                        f'<circle cx="{fx[i]:.1f}" cy="{fy(v):.1f}" r="4" fill="{cor}"/>',
                        t(
                            fx[i],
                            fy(v)
                            + (
                                -12
                                if v > 50 or (v == 50 and candidato == "Lula")
                                else 20
                            ),
                            num(v, 1),
                            12,
                            cor,
                            "middle",
                            "700",
                            mono=True,
                            extra=HALO,
                        ),
                    ]
    out.append(
        t(
            x0,
            yb0 - 28,
            "Mudança contra o 1º turno nos mesmos lugares, pontos",
            14,
            INK,
            weight="700",
        )
    )
    for v in ticks(-lim, lim, 4):
        out += [
            ln(x0, fs(v), x1, fs(v), GRADE, 1),
            t(
                x0 - 8,
                fs(v) + 4,
                pp(v, 1).removesuffix(" pp"),
                11,
                MUTED,
                "end",
                mono=True,
            ),
        ]
    out.append(ln(x0, fs(0), x1, fs(0), INK, 1.2))
    for i, dd in enumerate(decis):
        cx = fx[i]
        partes = []
        for _candidato, cor, valor, dx in (
            ("Flávio", FLAVIO, dd["swing_h2h_flavio_pp"], -passo * 0.17),
            ("Lula", LULA, -dd["swing_h2h_flavio_pp"], passo * 0.17),
        ):
            partes += [
                r(
                    cx + dx - passo * 0.13,
                    min(fs(0), fs(valor)),
                    passo * 0.26,
                    abs(fs(valor) - fs(0)),
                    cor,
                ),
                t(
                    cx + dx,
                    fs(valor) + (-6 if valor >= 0 else 15),
                    pp(valor, 1).removesuffix(" pp"),
                    11,
                    cor,
                    "middle",
                    mono=True,
                ),
            ]
        partes += [
            t(cx, h - 34, f"{dd['decil']}º", 13, INK, "middle", "700"),
            t(
                cx,
                h - 16,
                f"{dd['fechou_hhmm_de']}–{dd['fechou_hhmm_ate']}",
                10.5,
                MUTED,
                "middle",
                mono=True,
            ),
            area(cx - passo / 2, ya0 - 10, passo, h - ya0),
        ]
        linhas = [
            ("Fechou entre", f"{dd['fechou_hhmm_de']} e {dd['fechou_hhmm_ate']}"),
            ("Unidades", inteiro(dd["n"])),
            ("Eleitores", inteiro(dd["aptos"])),
        ]
        for candidato in ("Flávio", "Lula"):
            v1, v2 = dd["t1_h2h_flavio"], dd["h2h_flavio"]
            if candidato == "Lula":
                v1, v2 = 100 - v1, 100 - v2
            linhas += [
                (f"{candidato}, 1º turno entre os dois", pct(v1)),
                (f"{candidato}, 2º turno", pct(v2)),
            ]
        k = tips.add(ficha(f"{dd['decil']}º decil", "1 = fechou mais cedo", linhas))
        out.append(hit("".join(partes), k))
    out.append("</g>")
    return "".join(out)


def fig_decis(C: dict) -> str:
    tips = Tips()
    w, h = 1000, 600
    corpo = _painel_decis(C["decis_2t"], "mun", True, tips)
    zonas = (C.get("zonas") or {}).get("decis") or []
    controles = ""
    if zonas:
        corpo += _painel_decis(zonas, "zona", False, tips)
        controles = botoes(
            [("mun", "Municípios"), ("zona", "Zonas eleitorais")],
            "mun",
            "Unidade",
            "tab",
        )
    svg = (
        svg_abre(
            w,
            h,
            "Lula e Flávio por decil de fechamento, 2º e 1º turno",
            "Dez grupos de mesmo número de municípios pelo minuto em que fecharam; participação dos dois candidatos "
            "no 2º turno, no 1º turno nos mesmos lugares e a mudança entre os dois.",
        )
        + corpo
        + "</svg>"
    )

    def faixas(decis: list[dict], unidade: str) -> str:
        nv = [dd["h2h_flavio"] for dd in decis]
        sw = [dd["swing_h2h_flavio_pp"] for dd in decis]
        return f"{unidade}, Flávio: nível de {num(min(nv), 2)}% a {num(max(nv), 2)}%, mudança de {pp(max(sw))} a {pp(min(sw))}"

    leg = legenda_html(
        [
            ("Flávio", FLAVIO),
            ("Lula", LULA),
        ],
    )
    partes = [faixas(C["decis_2t"], "Municípios")]
    if zonas:
        partes.append(faixas(zonas, "zonas eleitorais"))
    legenda = (
        "Linha contínua: 2º turno; tracejada: 1º turno nos mesmos lugares, só entre os finalistas. Lula = 100 − Flávio, e a mudança troca de sinal. O nível sobe e desce de um decil a outro, e o 1º turno nos mesmos lugares desenha a mesma serra; a mudança "
        f"varia bem menos que o nível. {'; '.join(partes)}. Fonte: cedo_tarde.json (decis_2t e zonas.decis)."
    )
    return figura_html(
        "ct_decis",
        svg,
        legenda,
        tips,
        controles=controles,
        modo="scroll",
        minw=760,
        apos=leg,
    )


def fig_transicao(C: dict) -> str:
    tr = C["transicao_decil_1t_para_2t"]["matriz"]
    tips = Tips()
    n = len(tr)
    cel = 46
    x0, y0 = 150, 70
    w, h = x0 + cel * n + 30, y0 + cel * n + 50
    out = [
        svg_abre(
            w,
            h,
            "Decil de fechamento no 1º turno contra o 2º turno",
            "Número de municípios em cada par de decis; diagonal = mesma posição na fila nos dois turnos.",
        )
    ]
    out.append(t(x0, 28, "decil no 2º turno →", 13, INK, weight="700"))
    out.append(t(18, y0 - 12, "decil no 1º turno ↓", 13, INK, weight="700"))
    vmax = max(max(lin) for lin in tr) or 1
    pal = ["#f3efe3", "#d7e3dc", "#a9c9ba", "#6fa38e", "#2f7a66", "#0d3f35"]
    for j in range(n):
        out.append(
            t(x0 + cel * (j + 0.5), y0 - 10, str(j + 1), 12.5, INK, "middle", mono=True)
        )
    for i, lin in enumerate(tr):
        out.append(
            t(
                x0 - 10,
                y0 + cel * (i + 0.5) + 4,
                str(i + 1),
                12.5,
                INK,
                "end",
                mono=True,
            )
        )
        tot = sum(lin) or 1
        for j, v in enumerate(lin):
            cor = pal[min(len(pal) - 1, int(5.999 * v / vmax))]
            x, y = x0 + cel * j, y0 + cel * i
            partes = r(x, y, cel - 2, cel - 2, cor) + t(
                x + cel / 2 - 1,
                y + cel / 2 + 4,
                str(v),
                12,
                sobre(cor),
                "middle",
                mono=True,
            )
            k = tips.add(
                ficha(
                    f"1º turno: {i + 1}º decil, 2º turno: {j + 1}º decil",
                    "",
                    [("Municípios", inteiro(v)), ("Da linha", pct(100 * v / tot, 1))],
                )
            )
            out.append(hit(partes + area(x, y, cel, cel), k))
    out.append("</svg>")
    legenda = (
        f"Correlação de postos entre a ordem de fechamento do 1º e do 2º turno: {num(C['spearman_ordem_1t_x_2t'], 2)}; "
        f"entre tamanho do município e minuto de fechamento no 2º turno: {num(C['spearman_tamanho_x_fechamento_2t'], 2)}. "
        "A fila se repete em parte: quem foi tarde no 1º turno tende a ir tarde de novo. Fonte: cedo_tarde.json."
    )
    return figura_html("ct_transicao", "".join(out), legenda, tips, modo="fit")


def _ufs_fechamento(L: dict | None) -> list[dict]:
    if not L:
        return []
    return [u for u in L.get("conclusao_ufs", []) if u.get("uf") != "ZZ"]


def fig_ufs_vs_1t(L: dict | None) -> str:
    """Minuto em que cada UF fechou: 1º turno contra 2º turno descontados 120 min."""
    ufs = _ufs_fechamento(L)
    if not ufs:
        return ""
    ufs = sorted(ufs, key=lambda u: (u["fechou_min"] is None, u["fechou_min"] or 0))
    tips = Tips()
    passo = 22
    x0, x1, topo = 70, 960, 60
    h = topo + passo * len(ufs) + 50
    vals = [u["t1_p100_min"] for u in ufs] + [
        u["fechou_min"] - 120 for u in ufs if u["fechou_min"] is not None
    ]
    vals += [u["fechou_min"] for u in ufs if u["fechou_min"] is not None]
    lo, hi = 0, max(vals) * 1.04
    fx = escala(lo, hi, x0, x1)
    out = [
        svg_abre(
            1000,
            h,
            "Minuto em que cada UF fechou, 1º turno contra 2º turno",
            "Ponto dourado: 1º turno. Ponto azul: 2º turno descontados os 120 minutos da prorrogação informada pelo noticiário. "
            "Contorno azul: 2º turno no relógio.",
        )
    ]
    for v in range(0, int(hi) + 1, 60):
        x = fx(v)
        out.append(ln(x, topo - 10, x, h - 36, GRADE, 1))
        out.append(t(x, h - 18, rot_hora(17 * 60 + v), 12, MUTED, "middle", mono=True))
    out.append(
        t(
            x0,
            24,
            "horário de Brasília em que a última seção da UF entrou",
            13,
            INK,
            weight="700",
        )
    )
    for i, u in enumerate(ufs):
        y = topo + i * passo
        partes = [t(x0 - 10, y + 5, u["uf"], 12.5, INK, "end", "700")]
        x1t = fx(u["t1_p100_min"])
        if u["fechou_min"] is None:
            partes.append(f'<circle cx="{x1t:.1f}" cy="{y:.1f}" r="5" fill="{T1}"/>')
            partes.append(
                t(
                    x1t - 10,
                    y + 4,
                    "2º turno ainda incompleto na rodada",
                    11.5,
                    MUTED,
                    "end",
                )
            )
        else:
            xd = fx(u["fechou_min"] - 120)
            xr = fx(u["fechou_min"])
            partes.append(ln(min(xd, x1t), y, max(xd, x1t), y, LINE, 3))
            partes.append(
                f'<circle cx="{xr:.1f}" cy="{y:.1f}" r="4.5" fill="none" stroke="{FLAVIO}" stroke-width="1.6"/>'
            )
            partes.append(f'<circle cx="{x1t:.1f}" cy="{y:.1f}" r="5" fill="{T1}"/>')
            partes.append(f'<circle cx="{xd:.1f}" cy="{y:.1f}" r="5" fill="{FLAVIO}"/>')
        partes.append(area(0, y - passo / 2, 1000, passo))
        linhas = [("1º turno, 100%", u.get("t1_p100_hhmm", "s/d"))]
        if u["fechou_min"] is not None:
            linhas += [
                ("2º turno, 100%", (u.get("fechou_brt") or "")[11:16]),
                ("Atraso contra o 1º turno", f"{num(u['atraso_vs_1t_min'], 1)} min"),
                (
                    "Descontada a prorrogação",
                    f"{num(u['atraso_vs_1t_descontada_prorrogacao_min'], 1)} min",
                ),
            ]
        k = tips.add(ficha(nome_uf(u["uf"]), "", linhas))
        out.append(hit("".join(partes), k))
    out.append("</svg>")
    leg = legenda_html(
        [
            ("1º turno", T1),
            ("2º turno menos 120 min", FLAVIO),
            ("2º turno no relógio", "#ffffff"),
        ]
    )
    legenda = (
        "Sem descontar nada, várias UFs fecharam mais tarde que no 1º turno; descontados os 120 minutos da "
        "prorrogação (horário do noticiário, não do banco), todas as UFs"
        + (" completas" if any(u["fechou_min"] is None for u in ufs) else "")
        + " fecharam antes. Fonte: linha_do_tempo.json (conclusao_ufs)."
    )
    return figura_html(
        "ct_ufs_vs_1t", "".join(out), legenda, tips, modo="scroll", minw=760, apos=leg
    )


def fig_mapa_hora(L: dict | None) -> str:
    ufs = {u["uf"]: u for u in _ufs_fechamento(L)}
    if not ufs:
        return ""

    def minuto(u):
        return None if not u or u["fechou_min"] is None else 17 * 60 + u["fechou_min"]

    def cor(uf, u):
        m = minuto(u)
        return "#d8d4c8" if m is None else HORAS[faixa(m, CORTES_HORA)]

    def tit(uf, u):
        m = minuto(u)
        quando = (
            "ainda incompleta na rodada" if m is None else f"completa às {rot_hora(m)}"
        )
        return f"{nome_uf(uf)}: {quando}"

    svg = mapa_uf(
        ufs,
        cor,
        lambda uf, u: uf,
        tit,
        "Hora em que cada UF completou o 2º turno",
        "Mapa do Brasil por UF com a hora de Brasília em que a última seção do estado entrou.",
        escuro=lambda uf, u: (m := minuto(u)) is not None
        and faixa(m, CORTES_HORA) >= 3,
    )
    leg = legenda_html(
        [*zip(ROT_HORA, HORAS, strict=True)]
        + (
            [("incompleta na rodada", "#d8d4c8")]
            if any(minuto(u) is None for u in ufs.values())
            else []
        ),
        "Hora de Brasília",
    )
    legenda = "Hora da primeira versão do arquivo de presidente da UF com todas as seções. Fonte: linha_do_tempo.json."
    return figura_html("ct_mapa_hora", svg, legenda, Tips(), modo="fit", apos=leg)
