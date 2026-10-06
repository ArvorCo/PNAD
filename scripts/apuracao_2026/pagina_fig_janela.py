"""Figura `janela_parada_uf`: o que continuou chegando pelos arquivos de UF enquanto o
arquivo nacional estava parado (19:00 a 20:15 de 04/10), minuto a minuto, empilhado
por candidato ou por região, com as versões do nacional marcadas e a conferência
de que o nacional reproduz a soma das UFs. Dados: `noite_regioes.json`
(`minutos`, `painel_nacional`)."""

from __future__ import annotations

import math

from .pagina_comum import inteiro, num
from .pagina_fig_base import (
    COR_REGIAO,
    FLAVIO,
    INK,
    LULA,
    MUTED,
    OUTROS,
    Tips,
    W,
    area,
    botoes,
    dado,
    escala,
    figura_html,
    hit,
    legenda,
    ln,
    minutos,
    r,
    registra,
    svg_abre,
    t,
    tabela_linhas,
)
from .pagina_fig_noite import GOLD, eixo_x_horas, eixo_y

INI, FIM = 19 * 60, 20 * 60 + 15
REGIOES = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul", "Exterior"]


def _por_minuto(N: dict) -> dict[str, dict]:
    """hora -> {flavio, lula, outros, st, regioes: {regiao: vv}} só dentro da janela."""
    out: dict[str, dict] = {}
    for x in tabela_linhas(N["minutos"]):
        m = minutos(x["hora_brt"])
        if not INI <= m <= FIM:
            continue
        g = out.setdefault(
            x["hora_brt"],
            {
                "m": m,
                "flavio": 0,
                "lula": 0,
                "outros": 0,
                "st": 0,
                "vv": 0,
                "regioes": {},
            },
        )
        dvv, df, dl = x["d_vv"] or 0, x["d_flavio"] or 0, x["d_lula"] or 0
        g["flavio"] += df
        g["lula"] += dl
        g["outros"] += dvv - df - dl
        g["vv"] += dvv
        g["st"] += x["d_st"] or 0
        g["regioes"][x["regiao"]] = dvv
    return out


def _nacionais(N: dict) -> list[dict]:
    return [p for p in N["painel_nacional"] if INI <= minutos(p["gerado_brt"]) <= FIM]


@registra("janela_parada_uf")
def janela_parada_uf(d, **_op) -> str:
    N = dado(d, "noite_regioes")
    por = _por_minuto(N)
    nac = _nacionais(N)
    esq, topo, base, dir_ = 80, 56, 380, W - 40
    h = base + 60
    X = escala(INI, FIM, esq, dir_)
    vmax = max((g["vv"] for g in por.values()), default=1) / 1e6
    teto = max(0.5, math.ceil(vmax * 2) / 2)
    Y = escala(0, teto, base, topo)
    out = [
        svg_abre(
            W,
            h,
            "O que chegava pelos arquivos de UF enquanto o nacional estava parado",
            "Barras por minuto: votos válidos acrescentados pelos 28 arquivos de UF, empilhados por candidato ou por região; marcas: versões do arquivo nacional.",
        ),
        eixo_y(
            Y,
            [float(v) for v in range(0, int(teto) + 1, 2)]
            + ([teto] if teto % 2 else []),
            esq,
            dir_,
            lambda v: f"{num(v, 0)} mi",
        ),
    ]
    larg = (X(INI + 1) - X(INI)) * 0.8
    gc, gr = [], []
    for _hora, g in sorted(por.items()):
        x = X(g["m"]) - larg / 2
        y = base
        for parte, cor in (
            (g["flavio"], FLAVIO),
            (g["lula"], LULA),
            (g["outros"], OUTROS),
        ):
            alt = base - Y(max(parte, 0) / 1e6)
            y -= alt
            gc.append(r(x, y, larg, alt, cor))
        y = base
        for reg in REGIOES:
            alt = base - Y(max(g["regioes"].get(reg, 0), 0) / 1e6)
            y -= alt
            gr.append(r(x, y, larg, alt, COR_REGIAO.get(reg, MUTED)))
    out.append(f'<g data-alt-show="candidato">{"".join(gc)}</g>')
    out.append(f'<g data-alt-show="regiao" display="none">{"".join(gr)}</g>')
    # versões do arquivo nacional dentro da janela
    for p in nac:
        m = minutos(p["gerado_brt"])
        if m < INI:
            continue
        x = X(m)
        delimita = p["gerado_brt"][11:19] in ("19:14:08", "20:04:39")
        out.append(
            ln(
                x,
                topo - 6,
                x,
                base,
                GOLD,
                2.2 if delimita else 1,
                ' stroke-dasharray="5 4"',
            )
        )
        if delimita:
            anchor = "start" if m < (INI + FIM) / 2 else "end"
            out.append(
                t(
                    x + (5 if anchor == "start" else -5),
                    topo + 6,
                    f"nacional {p['gerado_brt'][11:19]}: {inteiro(p['st'])} seções",
                    13,
                    GOLD,
                    anchor,
                    "700",
                )
            )
    out.append(ln(esq, base, dir_, base, INK, 1.2))
    out.append(eixo_x_horas(X, INI, FIM, base, passo=15))
    out.append(
        '<g data-alt-show="candidato">'
        + legenda([("Flávio", FLAVIO), ("Lula", LULA), ("Terceiros", OUTROS)], esq, 22)
        + '</g><g data-alt-show="regiao" display="none">'
        + legenda([(reg, COR_REGIAO.get(reg, MUTED)) for reg in REGIOES], esq, 22)
        + "</g>"
    )
    tips = Tips()
    linhas = []
    for i, (hora, g) in enumerate(sorted(por.items())):
        linhas.append(
            [
                hora[11:16],
                inteiro(g["st"]),
                inteiro(g["vv"]),
                f"{num(100 * g['flavio'] / g['vv'], 1)}%" if g["vv"] else "s/d",
                f"{num(100 * g['lula'] / g['vv'], 1)}%" if g["vv"] else "s/d",
                ", ".join(
                    f"{reg} {num(100 * g['regioes'].get(reg, 0) / g['vv'], 0)}%"
                    for reg in REGIOES
                    if g["vv"] and g["regioes"].get(reg, 0) > 0
                ),
            ]
        )
        out.append(hit(area(X(g["m"]) - larg / 2, topo, larg, base - topo), f"r{i}"))
    tips.tabela(
        [
            "Minuto",
            "Seções pelas UFs",
            "Válidos pelas UFs",
            "Flávio no minuto",
            "Lula no minuto",
            "Regiões",
        ],
        linhas,
        sub=1,
    )
    out.append("</svg>")
    # conferência: o nacional reproduz a soma das UFs?
    conf = [
        '<div class="table-scroll"><table class="compacta"><thead><tr><th>Versão do nacional</th><th class="num">Seções</th>'
        '<th>Soma das UFs alcançou</th><th class="num">Seções na soma</th><th class="num">Resíduo Flávio</th>'
        '<th class="num">Resíduo Lula</th><th class="num">UFs à frente antes da próxima</th></tr></thead><tbody>'
    ]
    for p in nac:
        conf.append(
            f"<tr><td>{p['gerado_brt'][11:19]}</td><td class=\"num\">{inteiro(p['st'])}</td>"
            f"<td>{(p['soma_ufs_alcancou_brt'] or 's/d')[11:19]}</td><td class=\"num\">{inteiro(p['soma_ufs_st'] or 0)}</td>"
            f"<td class=\"num\">{num(p['residuo_pp_flavio'] or 0, 3)} pp</td><td class=\"num\">{num(p['residuo_pp_lula'] or 0, 3)} pp</td>"
            f"<td class=\"num\">{inteiro(p['soma_ufs_a_frente_antes_da_proxima'] or 0)}</td></tr>"
        )
    conf.append("</tbody></table></div>")
    total_vv = sum(g["vv"] for g in por.values())
    total_st = sum(g["st"] for g in por.values())
    p1 = next((p for p in nac if p["gerado_brt"].endswith("19:14:08")), None)
    p2 = next((p for p in nac if p["gerado_brt"].endswith("20:04:39")), None)
    bate = ""
    if p1 and p2:
        bate = (
            f" A versão de 19:14:08 reproduz a soma das UFs de {p1['soma_ufs_alcancou_brt'][11:19]} com resíduo de "
            f"{num(abs(p1['residuo_pp_flavio']), 3)} pp em Flávio; a de 20:04:39, a soma de {p2['soma_ufs_alcancou_brt'][11:19]}, "
            f"com resíduo de {num(abs(p2['residuo_pp_flavio']), 3)} pp. O nacional bate com a soma das UFs; o que muda é a idade do retrato."
        )
    legenda_ = (
        f"Entre 19:00 e 20:15 os arquivos de UF acrescentaram {inteiro(total_st)} seções e {inteiro(total_vv)} válidos, "
        "minuto a minuto, enquanto o arquivo nacional ficou nas duas versões marcadas (as marcas finas são as versões seguintes). "
        "Os minutos vazios entre 19:32 e 20:02 são a pausa geral: nenhum arquivo de UF foi gerado nesse intervalo. "
        "O pico de 19:26 é SP e MG entrando de uma vez, porque o coletor lê os arquivos desses estados a cada 2 ou 3 minutos. "
        "Botão: empilhar por candidato ou por região."
        + bate
        + " Fonte: noite_regioes.json, soma dos 28 arquivos de UF do TSE."
    )
    ctl = botoes(
        [("candidato", "Por candidato"), ("regiao", "Por região")],
        "candidato",
        "Empilhar",
    )
    return figura_html(
        "janela_parada_uf",
        "".join(out),
        legenda_,
        tips,
        controles=ctl,
        minw=820,
        apos="".join(conf),
    )
