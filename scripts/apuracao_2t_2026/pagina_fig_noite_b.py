"""Figuras dos capítulos 01 (resultado) e 03 (projeção da casa) do dossiê do 2º turno.

O mapa por UF reaproveita `apuracao_2026.pagina_fig_mapas.mapa_ufs` e a paleta de
margem do 1º turno; a projeção lê `projecao_noite.json` (série relida com `at=`)
e, separada, a série exibida ao vivo (`serie_ao_vivo`).
"""

from __future__ import annotations

from apuracao_2026.pagina_comum import inteiro, num
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
    pct,
    pp,
    r,
    svg_abre,
    t,
    tabela_linhas,
    ticks,
)
from apuracao_2026.pagina_fig_mapas import (
    AZUIS,
    FAIXAS,
    ROT_FAIXA,
    VERMELHOS,
    faixa,
    mapa_ufs,
)

from .pagina_fig_noite import hhmm

FAIXA_COR = "#c9d8ef"
AO_VIVO = "#7d5b00"


# ------------------------------------------------------------------ 01 mapa


def fig_mapa_vencedor(P: dict) -> str:
    tips, fill, chaves = Tips(), {}, {}
    n_f = n_l = 0
    for u in P["ufs"]:
        uf = u["uf"]
        if uf == "ZZ":
            continue
        m = u["pct_flavio"] - u["pct_lula"]
        lider = "flavio" if m > 0 else "lula"
        n_f += lider == "flavio"
        n_l += lider == "lula"
        fill[uf] = (AZUIS if lider == "flavio" else VERMELHOS)[faixa(abs(m), FAIXAS)]
        chaves[uf] = tips.add(
            ficha(
                f"{u['nome']} ({uf})",
                "Flávio vence" if lider == "flavio" else "Lula vence",
                [
                    ("Lula", f"{pct(u['pct_lula'])} · {inteiro(u['lula'])}"),
                    ("Flávio", f"{pct(u['pct_flavio'])} · {inteiro(u['flavio'])}"),
                    (
                        "Margem",
                        f"{pp(abs(m))} · {inteiro(abs(u['margem_lula_votos']))} votos",
                    ),
                    ("Abstenção", pct(u["pct_abstencao"])),
                    (
                        "Seções",
                        f"{inteiro(u['secoes'])} de {inteiro(u['secoes_total'])}",
                    ),
                ],
            )
        )
    itens = [(f"Lula, {ROT_FAIXA[i]}", VERMELHOS[i]) for i in range(4)]
    itens += [(f"Flávio, {ROT_FAIXA[i]}", AZUIS[i]) for i in range(4)]
    svg = mapa_ufs(
        fill,
        chaves,
        "Vencedor por UF, presidente, 2º turno de 2026",
        f"Lula vence em {n_l} UFs e Flávio em {n_f}; tom pela margem nos válidos.",
    )
    legenda = (
        f"Lula venceu em {n_l} UFs e Flávio Bolsonaro em {n_f}. Tom pela margem nos válidos. "
        "Fonte: arquivos de UF do TSE, versão vigente (presidente.json)."
    )
    return figura_html(
        "mapa_vencedor_2t",
        svg,
        legenda,
        tips,
        modo="fit",
        apos=legenda_html(itens, "Margem nos válidos"),
    )


# ------------------------------------------------------------------ 01 barras


def fig_barras(P: dict) -> str:
    linhas = [("Brasil", P["nacional"])]
    nomes = {
        "N": "Norte",
        "NE": "Nordeste",
        "CO": "Centro-Oeste",
        "SE": "Sudeste",
        "S": "Sul",
    }
    for rg in P["regioes"]:
        if rg["sigla"] in nomes:
            linhas.append((nomes[rg["sigla"]], rg))
    linhas.append(("Exterior", P["exterior"]))
    ml, mr, mt, lh = 150, 30, 34, 50
    H = mt + lh * len(linhas) + 30
    x = escala(0, 100, ml, W - mr)
    out = [
        svg_abre(
            W,
            H,
            "Lula e Flávio no Brasil, nas regiões e no exterior",
            "Barras de 100% com a parte de cada um nos válidos.",
        )
    ]
    tips = Tips()
    out.append(ln(x(50), mt - 10, x(50), H - 24, INK, 1.2, ' stroke-dasharray="4 3"'))
    out.append(t(x(50), mt - 14, "50%", 12, INK, "middle", "700"))
    for i, (nome, o) in enumerate(linhas):
        yy = mt + i * lh
        wl = x(o["pct_lula"]) - ml
        peso = "800" if nome == "Brasil" else "600"
        out.append(t(ml - 12, yy + 24, nome, 15, INK, "end", peso))
        barra = r(ml, yy + 6, wl, 28, LULA) + r(
            ml + wl, yy + 6, W - mr - ml - wl, 28, FLAVIO
        )
        barra += t(ml + 8, yy + 25, pct(o["pct_lula"]), 14, "#ffffff", weight="700")
        barra += t(
            W - mr - 8, yy + 25, pct(o["pct_flavio"]), 14, "#ffffff", "end", "700"
        )
        k = tips.add(
            ficha(
                nome,
                "votos válidos",
                [
                    ("Lula", f"{inteiro(o['lula'])} ({pct(o['pct_lula'])})"),
                    ("Flávio", f"{inteiro(o['flavio'])} ({pct(o['pct_flavio'])})"),
                    ("Diferença", f"{inteiro(abs(o['margem_lula_votos']))} votos"),
                    ("Abstenção", pct(o["pct_abstencao"])),
                ],
            )
        )
        out.append(hit(barra + area(ml, yy + 4, W - mr - ml, 32), k, foco=True))
    out.append("</svg>")
    leg = legenda_html([("Lula", LULA), ("Flávio Bolsonaro", FLAVIO)])
    return figura_html(
        "barras_regioes_2t",
        "".join(out),
        "Parte de cada candidato nos votos válidos. Fonte: presidente.json (nacional, regiões e exterior).",
        tips,
        apos=leg,
        minw=640,
    )


# ------------------------------------------------------------------ 03 projeção


def pontos_proj(J: dict) -> list[dict]:
    return [p for p in J["pontos"] if p.get("p_f_projetado") is not None]


def faixa_candidato(faixa: list[float], candidato: str) -> tuple[float, float]:
    """Complemento de uma faixa entre os dois: inverte também os extremos."""
    lo, hi = faixa
    return (lo, hi) if candidato == "flavio" else (100 - hi, 100 - lo)


def fig_projecao(J: dict) -> str:
    pts = J["pontos"]
    proj = pontos_proj(J)
    final = J["observado_final"]["p_f_entre_os_dois"]
    obs = [p for p in pts if p["pst"] >= 0.3]
    vivo = [
        v
        for v in tabela_linhas(J["serie_ao_vivo"])
        if v["p_f_proj"] is not None and 120 <= v["min"] <= max(330, pts[-1]["min"])
    ]
    vals = [p["p_f_observado"] for p in obs]
    vals += [v for p in proj for v in p["faixa90"]]
    vals += [v["p_f_proj"] for v in vivo]
    vals += [100 - v for v in vals]
    lo, hi = min(44, min(vals) - 1), max(56, max(vals) + 1)
    H, ml, mr, panel = 640, 70, 40, 290
    m0, m1 = 120, max(330, pts[-1]["min"])
    x = escala(m0, m1, ml, W - mr)
    out = [
        svg_abre(
            W,
            H,
            "Projeção da casa: Flávio e Lula na noite do 2º turno",
            "Dois painéis na mesma escala: projeção relida com faixa de 90%, contagem observada, série ao vivo e resultado final.",
        )
    ]
    tips = Tips()
    for i, (cand, nome, cor) in enumerate(
        (("flavio", "Flávio", FLAVIO), ("lula", "Lula", LULA))
    ):
        mt, bottom = 42 + i * panel, 270 + i * panel
        y = escala(lo, hi, bottom, mt)

        def valor(v, candidato=cand):
            return v if candidato == "flavio" else 100 - v

        out.append(t(ml, mt - 15, nome, 19, cor, weight="700"))
        for tk in ticks(lo, hi, 5):
            out.append(ln(ml, y(tk), W - mr, y(tk), GRADE, 1))
            out.append(
                t(ml - 8, y(tk) + 4, f"{num(tk, 0)}%", 12, MUTED, "end", mono=True)
            )
        for m in range(m0, int(m1) + 1, 30):
            out.append(ln(x(m), mt, x(m), bottom, GRADE, 1))
            out.append(t(x(m), bottom + 19, hhmm(m), 12, MUTED, "middle", mono=True))
        if proj:
            topo = " ".join(
                f"{x(p['min']):.1f},{y(faixa_candidato(p['faixa90'], cand)[1]):.1f}"
                for p in proj
            )
            base = " ".join(
                f"{x(p['min']):.1f},{y(faixa_candidato(p['faixa90'], cand)[0]):.1f}"
                for p in reversed(proj)
            )
            out.append(f'<polygon points="{topo} {base}" fill="{cor}" opacity="0.15"/>')
        out.append(ln(ml, y(50), W - mr, y(50), INK, 1))
        out.append(
            ln(
                ml,
                y(valor(final)),
                W - mr,
                y(valor(final)),
                cor,
                1.2,
                ' stroke-dasharray="8 5"',
            )
        )
        for series, field, color, width, dash in (
            (obs, "p_f_observado", MUTED, 1.8, ""),
            (vivo, "p_f_proj", AO_VIVO, 1.8, ' stroke-dasharray="2 4"'),
            (proj, "p_f_projetado", cor, 2.8, ""),
        ):
            pl = " ".join(f"{x(p['min']):.1f},{y(valor(p[field])):.1f}" for p in series)
            out.append(
                f'<polyline points="{pl}" fill="none" stroke="{color}" stroke-width="{width}"{dash}/>'
            )
        p0 = J.get("primeiro_ponto_com_projecao")
        if p0:
            out.append(
                f'<circle cx="{x(p0["min"]):.1f}" cy="{y(valor(p0["p_f_projetado"])):.1f}" r="4" fill="{cor}"/>'
            )
            out.append(
                t(
                    x(p0["min"]) + 8,
                    y(valor(p0["p_f_projetado"])) + (20 if i == 0 else -14),
                    f"{pct(valor(p0['p_f_projetado']))} com {num(p0['pst'], 2)}% das seções",
                    12,
                    cor,
                    weight="700",
                    extra=HALO,
                )
            )
        out.append(
            t(W - mr, mt - 15, f"Final: {pct(valor(final))}", 14, cor, "end", "700")
        )
        for p in obs:
            linhas = [
                ("Observado", pct(valor(p["p_f_observado"]))),
                ("Seções", pct(p["pst"])),
            ]
            if p.get("p_f_projetado") is not None:
                a, b = faixa_candidato(p["faixa90"], cand)
                linhas += [
                    ("Projetado", pct(valor(p["p_f_projetado"]))),
                    ("Faixa de 90%", f"{num(a, 2)} a {num(b, 2)}%"),
                    (
                        "Erro contra o final",
                        pp(valor(p["p_f_projetado"]) - valor(final)),
                    ),
                ]
            k = tips.add(ficha(p["hhmm"], f"{nome} entre os dois", linhas))
            out.append(
                hit(
                    area(
                        x(p["min"] - 2.5),
                        mt,
                        x(p["min"] + 2.5) - x(p["min"] - 2.5),
                        bottom - mt,
                    ),
                    k,
                )
            )
    out.append("</svg>")
    leg = legenda_html(
        [
            ("Flávio: projeção relida", FLAVIO),
            ("Lula: projeção relida", LULA),
            ("Contagem observada", MUTED),
            ("Exibida ao vivo (pontilhada)", AO_VIVO),
        ]
    )
    legenda = (
        "Mesma escala nos dois painéis. Linha colorida: projeção relida; área: faixa de 90%; "
        "cinza: contagem; dourado pontilhado: projeção exibida ao vivo, no mesmo intervalo de tempo; tracejado: resultado final. "
        "As participações somam 100%; a faixa de Lula é [100 − limite superior de Flávio, 100 − limite inferior]. "
        "A faixa descreve a projeção, não uma probabilidade de vitória. Fonte: projecao_noite.json."
    )
    return figura_html(
        "projecao_noite_2t", "".join(out), legenda, tips, apos=leg, minw=680
    )
