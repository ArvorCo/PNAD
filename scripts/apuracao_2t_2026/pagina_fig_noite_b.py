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


def fig_projecao(J: dict) -> str:
    pts = J["pontos"]
    proj = pontos_proj(J)
    final = J["observado_final"]["p_f_entre_os_dois"]
    obs = [p for p in pts if p["pst"] >= 0.3]
    vivo = [
        v
        for v in tabela_linhas(J["serie_ao_vivo"])
        if v["p_f_proj"] is not None and v["min"] >= 120
    ]
    vals = (
        [p["p_f_observado"] for p in obs]
        + [p["faixa90"][0] for p in proj]
        + [p["faixa90"][1] for p in proj]
    )
    lo = min(44.0, min(vals) - 0.5)
    hi = max(51.5, max(vals) + 0.5)
    H, ml, mr, mt, mb = 440, 70, 40, 26, 50
    m0, m1 = 120, max(330, pts[-1]["min"])
    x = escala(m0, m1, ml, W - mr)
    y = escala(lo, hi, H - mb, mt)
    out = [
        svg_abre(
            W,
            H,
            "Projeção da casa contra o observado, noite do 2º turno",
            "Parte de Flávio entre os dois: projeção com faixa de 90%, contagem observada e resultado final.",
        )
    ]
    for tk in ticks(lo, hi, 6):
        out.append(ln(ml, y(tk), W - mr, y(tk), GRADE, 1))
        out.append(
            t(ml - 8, y(tk) + 4, f"{num(tk, 0)}%", 12.5, MUTED, "end", mono=True)
        )
    m = m0
    while m <= m1:
        out.append(ln(x(m), mt, x(m), H - mb, GRADE, 1))
        out.append(t(x(m), H - mb + 20, hhmm(m), 12.5, MUTED, "middle", mono=True))
        m += 30
    # faixa de 90%
    if proj:
        topo = " ".join(f"{x(p['min']):.1f},{y(p['faixa90'][1]):.1f}" for p in proj)
        base = " ".join(
            f"{x(p['min']):.1f},{y(p['faixa90'][0]):.1f}" for p in reversed(proj)
        )
        out.append(
            f'<polygon points="{topo} {base}" fill="{FAIXA_COR}" opacity="0.85"/>'
        )
    out.append(ln(ml, y(50), W - mr, y(50), INK, 1.2))
    out.append(t(ml + 6, y(50) - 6, "50%", 12.5, INK, weight="700", extra=HALO))
    out.append(
        ln(ml, y(final), W - mr, y(final), "#0b6650", 1.6, ' stroke-dasharray="6 4"')
    )
    out.append(
        t(
            W - mr - 4,
            y(final) + 18,
            f"final {pct(final)}",
            13,
            "#0b6650",
            "end",
            "700",
            extra=HALO,
        )
    )
    pl = " ".join(f"{x(p['min']):.1f},{y(p['p_f_observado']):.1f}" for p in obs)
    out.append(
        f'<polyline points="{pl}" fill="none" stroke="{MUTED}" stroke-width="2.2"/>'
    )
    if vivo:
        pv = " ".join(f"{x(v['min']):.1f},{y(v['p_f_proj']):.1f}" for v in vivo)
        out.append(
            f'<polyline points="{pv}" fill="none" stroke="{AO_VIVO}" stroke-width="1.6" stroke-dasharray="2 3"/>'
        )
    pp_ = " ".join(f"{x(p['min']):.1f},{y(p['p_f_projetado']):.1f}" for p in proj)
    out.append(
        f'<polyline points="{pp_}" fill="none" stroke="{FLAVIO}" stroke-width="2.8"/>'
    )
    p0 = J.get("primeiro_ponto_com_projecao")
    if p0:
        out.append(
            f'<circle cx="{x(p0["min"]):.1f}" cy="{y(p0["p_f_projetado"]):.1f}" r="5" fill="{FLAVIO}"/>'
        )
        out.append(
            t(
                x(p0["min"]) + 8,
                y(p0["p_f_projetado"]) + 20,
                f"{p0['hhmm']}: {pct(p0['p_f_projetado'])} com {num(p0['pst'], 2)}% das seções",
                13,
                FLAVIO,
                weight="700",
                extra=HALO,
            )
        )
    tips = Tips()
    for p in pts:
        if p["pst"] < 0.3:
            continue
        xa = x(p["min"] - 2.5)
        linhas = [
            ("Observado", pct(p["p_f_observado"])),
            ("Seções", f"{num(p['pst'], 2)}%"),
        ]
        if p.get("p_f_projetado") is not None:
            linhas.insert(0, ("Projetado", pct(p["p_f_projetado"])))
            linhas.insert(
                1,
                (
                    "Faixa de 90%",
                    f"{num(p['faixa90'][0], 2)} a {num(p['faixa90'][1], 2)}",
                ),
            )
            linhas.append(("Erro contra o final", pp(p["p_f_projetado"] - final)))
        else:
            linhas.append(("Sem projeção", p.get("motivo_sem_projecao") or ""))
        k = tips.add(ficha(p["hhmm"], "Flávio entre os dois", linhas))
        out.append(hit(area(xa, mt, x(p["min"] + 2.5) - xa, H - mb - mt), k))
    out.append("</svg>")
    leg = legenda_html(
        [
            ("Projeção relida", FLAVIO),
            ("Faixa de 90%", FAIXA_COR),
            ("Contagem observada", MUTED),
            ("Exibida ao vivo", AO_VIVO),
            ("Resultado final", "#0b6650"),
        ]
    )
    legenda = (
        f"Parte de Flávio entre os dois. Linha azul: projeção da casa relida a cada 5 minutos sobre o banco; "
        f"faixa: 90%; cinza: o que já estava contado; pontilhado dourado: a série que o telão exibiu ao vivo. "
        f"A projeção abaixo de 50% em todos os {J['pontos_com_projecao']} pontos significa Lula à frente. "
        "Projeção estatística a partir do que já foi totalizado; não é resultado nem previsão de vitória. Fonte: projecao_noite.json."
    )
    return figura_html(
        "projecao_noite_2t", "".join(out), legenda, tips, apos=leg, minw=760
    )
