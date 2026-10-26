"""Figuras do capítulo "Seis governadores" do dossiê do 2º turno.

- ``fig_placar``: os dois nomes de cada UF, barra de 100% dos válidos com a cor do campo
  e a marca do 1º turno;
- ``fig_noite``: a vantagem da candidatura vencedora em cada versão do arquivo de UF,
  com as trocas de liderança marcadas;
- ``fig_vao``: candidatura ao governo contra o finalista presidencial do mesmo lado.

Números de ``governadores.json``; cor por campo (``pagina_fig_base.cor_campo``).
"""

from __future__ import annotations

from apuracao_2026.pagina_comum import INK, MUTED, inteiro, num, tabela
from apuracao_2026.pagina_fig_base import (
    GRADE,
    HALO,
    Tips,
    area,
    campo_nome,
    cor_campo,
    escala,
    ficha,
    figura_html,
    hit,
    legenda_html,
    ln,
    nome_bonito,
    r,
    sobre,
    svg_abre,
    t,
)


def ordenados(G: dict) -> list[dict]:
    return sorted(G["ufs"], key=lambda u: u.get("margem_pp") or 0)


def par(u: dict) -> tuple[dict, dict]:
    c = sorted(u["candidatos"], key=lambda c: -(c.get("votos") or 0))
    return c[0], c[1]


def nome(c: dict) -> str:
    return nome_bonito(c.get("nome_urna") or "")


def fig_placar(G: dict) -> str:
    ufs = ordenados(G)
    w, esq, dir_ = 1000, 90, 30
    topo, passo = 34, 78
    h = topo + passo * len(ufs) + 10
    x = escala(0, 100, esq, w - dir_)
    out = [
        svg_abre(
            w,
            h,
            "Governadores no 2º turno: placar por UF",
            "Uma barra de 100% dos válidos por UF, vencedor à esquerda; cor pelo campo político; "
            "tracejado na parte do vencedor entre os dois no 1º turno.",
        )
    ]
    out.append(ln(x(50), topo - 10, x(50), h - 8, INK, 1, ' stroke-dasharray="2 3"'))
    out.append(t(x(50), topo - 14, "50%", 12, MUTED, "middle", mono=True))
    tips = Tips()
    for i, u in enumerate(ufs):
        a, b = par(u)
        y = topo + i * passo
        pa = a.get("pct") or 0
        ca, cb = cor_campo(a.get("campo")), cor_campo(b.get("campo"))
        partes = [
            t(esq - 12, y + 30, u["uf"], 18, INK, "end", "700"),
            r(x(0), y + 10, x(pa) - x(0), 34, ca),
            r(x(pa), y + 10, x(100) - x(pa), 34, cb),
            t(
                x(0) + 8,
                y + 32,
                f"{nome(a)} {num(pa, 2)}%",
                14,
                sobre(ca),
                weight="600",
            ),
            t(
                x(100) - 8,
                y + 32,
                f"{num(b.get('pct'), 2)}% {nome(b)}",
                14,
                sobre(cb),
                "end",
                "600",
            ),
            t(
                x(0),
                y + 62,
                f"{a.get('partido')} ({campo_nome(a.get('campo')).lower()}) × {b.get('partido')} "
                f"({campo_nome(b.get('campo')).lower()}); diferença de {inteiro(u.get('margem_votos'))} "
                f"votos, {num(u.get('margem_pp'), 2)} pp",
                12.5,
                MUTED,
            ),
        ]
        if a.get("t1_pct") is not None and b.get("t1_pct"):
            p1 = 100 * a["t1_pct"] / (a["t1_pct"] + b["t1_pct"])
            partes.append(
                f'<line x1="{x(p1):.1f}" y1="{y + 6}" x2="{x(p1):.1f}" y2="{y + 48}" stroke="#ffffff" stroke-width="2.6"/>'
                f'<line x1="{x(p1):.1f}" y1="{y + 6}" x2="{x(p1):.1f}" y2="{y + 48}" stroke="{INK}" '
                'stroke-width="1.3" stroke-dasharray="3 2"/>'
            )
        kk = tips.add(
            ficha(
                f"{u.get('nome')}",
                f"{inteiro(u.get('secoes'))} seções, {num(u.get('pst'), 2)}% totalizadas",
                [
                    (nome(a), f"{num(pa, 2)}% ({inteiro(a.get('votos'))})"),
                    (nome(b), f"{num(b.get('pct'), 2)}% ({inteiro(b.get('votos'))})"),
                    (f"{nome(a)} no 1º turno", f"{num(a.get('t1_pct'), 2)}%"),
                    (f"{nome(b)} no 1º turno", f"{num(b.get('t1_pct'), 2)}%"),
                    ("trocas de liderança na noite", inteiro(u.get("n_viradas"))),
                    ("arquivo completo às", (u.get("fechou_brt") or "s/d")[-8:-3]),
                ],
            )
        )
        out.append(hit("".join(partes) + area(0, y, w, passo), kk, foco=True))
    out.append("</svg>")
    campos = []
    for u in ufs:
        for c in u["candidatos"]:
            k = c.get("campo")
            if k not in [z for z, _ in campos]:
                campos.append((k, cor_campo(k)))
    leg = legenda_html(
        [(campo_nome(k), cor) for k, cor in campos],
        "Campo político (classificação editorial da casa)",
    )
    legenda = (
        "Percentuais dos válidos de governador. O tracejado marca a parte do vencedor entre os dois "
        "finalistas no 1º turno. Fonte: governadores.json."
    )
    return figura_html(
        "gov_placar", "".join(out), legenda, tips, modo="scroll", minw=760, apos=leg
    )


def _serie_margem(u: dict) -> list[tuple[float, float, float]]:
    """(minuto, pst, vantagem do vencedor final em pp) por versão."""
    a, b = par(u)
    out = []
    for m, pst, pcts in u.get("serie") or []:
        va, vb = pcts.get(a["sqcand"]), pcts.get(b["sqcand"])
        if va is None or vb is None:
            continue
        out.append((m, pst, va - vb))
    return out


def _tracado(s: list, x, y, cor: str) -> str:
    """Linha por versão; intervalo de mais de 30 min sem versão vira pontilhado cinza."""
    out, trecho = [], []
    for k, (m, _, v) in enumerate(s):
        if trecho and m - s[k - 1][0] > 30:
            m0, _, v0 = s[k - 1]
            out.append(
                f'<line x1="{x(m0):.1f}" y1="{y(v0):.1f}" x2="{x(m):.1f}" y2="{y(v):.1f}" '
                f'stroke="{MUTED}" stroke-width="1.2" stroke-dasharray="2 3"/>'
            )
            out.append(_poli(trecho, cor))
            trecho = []
        trecho.append((x(m), y(v)))
    out.append(_poli(trecho, cor))
    return "".join(out)


def _poli(pts: list, cor: str) -> str:
    if len(pts) == 1:
        px, py = pts[0]
        return f'<circle cx="{px:.1f}" cy="{py:.1f}" r="2.5" fill="{cor}"/>'
    d = " ".join(f"{px:.1f},{py:.1f}" for px, py in pts)
    return f'<polyline points="{d}" fill="none" stroke="{cor}" stroke-width="2"/>'


def fig_noite(G: dict) -> str:
    ufs = sorted(G["ufs"], key=lambda u: u["uf"])
    cols, pw, ph = 3, 340, 200
    gap_x, gap_y, topo = 26, 54, 20
    rows = (len(ufs) + cols - 1) // cols
    w = cols * pw + (cols - 1) * gap_x + 20
    h = topo + rows * (ph + gap_y) + 10
    out = [
        svg_abre(
            w,
            h,
            "A noite dos governadores: vantagem do vencedor em cada versão",
            "Seis painéis, um por UF: vantagem em pontos percentuais da candidatura que venceu, em cada "
            "versão do arquivo de UF, pela hora de Brasília; pontos nas trocas de liderança.",
        )
    ]
    tmin = 0.0
    tmax = max((s[0] for u in ufs for s in _serie_margem(u)), default=300.0)
    tmax = max(tmax, 300.0)
    tips = Tips()
    for k, u in enumerate(ufs):
        cx = 10 + (k % cols) * (pw + gap_x)
        cy = topo + (k // cols) * (ph + gap_y)
        s = _serie_margem(u)
        a, _ = par(u)
        if not s:
            continue
        lim = max(5.0, max(abs(v) for _, _, v in s) * 1.1)
        x = escala(tmin, tmax, cx + 34, cx + pw - 6)
        y = escala(-lim, lim, cy + ph - 22, cy + 26)
        partes = [
            t(cx, cy + 14, f"{u['uf']}: {nome(a)}", 14, INK, weight="700"),
            ln(cx + 34, y(0), cx + pw - 6, y(0), INK, 1),
        ]
        for m in (0, 120, 240):
            if m <= tmax:
                partes.append(ln(x(m), cy + 26, x(m), cy + ph - 22, GRADE, 1))
                partes.append(
                    t(
                        x(m),
                        cy + ph - 6,
                        f"{17 + m // 60:02d}h",
                        11,
                        MUTED,
                        "middle",
                        mono=True,
                    )
                )
        partes.append(
            t(cx + 30, y(lim) + 10, f"+{num(lim, 0)}", 11, MUTED, "end", mono=True)
        )
        partes.append(
            t(cx + 30, y(-lim), f"−{num(lim, 0)}", 11, MUTED, "end", mono=True)
        )
        cor = cor_campo(a.get("campo"))
        partes.append(_tracado(s, x, y, cor))
        for vi in u.get("viradas") or []:
            partes.append(
                f'<circle cx="{x(vi["min"]):.1f}" cy="{y(0):.1f}" r="4" fill="#ffffff" stroke="{INK}" stroke-width="1.6"/>'
            )
        mf, _, vf = s[-1]
        partes.append(
            t(
                x(mf) - 2,
                y(vf) - 6,
                f"{num(vf, 1)} pp",
                12,
                INK,
                "end",
                "600",
                extra=HALO,
            )
        )
        vir = u.get("viradas") or []
        kk = tips.add(
            ficha(
                u.get("nome") or u["uf"],
                f"{len(s)} versões do arquivo de UF",
                [
                    ("vencedor", nome(a)),
                    ("vantagem final", f"{num(vf, 2)} pp"),
                    ("trocas de liderança", inteiro(len(vir))),
                ]
                + [
                    (
                        f"troca às {v.get('gerado_brt', '')[-8:-3]}",
                        f"{num(v.get('pst'), 2)}% das seções, {inteiro(v.get('margem_votos'))} votos",
                    )
                    for v in vir
                ],
            )
        )
        out.append(hit("".join(partes) + area(cx, cy, pw, ph), kk, foco=True))
    out.append("</svg>")
    legenda = (
        "Eixo vertical: vantagem da candidatura que venceu sobre a outra, em pp dos válidos; acima de "
        "zero, ela liderava. Círculos: trocas de liderança entre versões genuínas consecutivas; "
        "pontilhado cinza: mais de 30 min sem versão nova (a pausa da totalização). "
        "Fonte: governadores.json (serie, viradas)."
    )
    return figura_html(
        "gov_noite", "".join(out), legenda, tips, modo="scroll", minw=760
    )


def fig_vao(G: dict) -> str:
    ufs = sorted(G["ufs"], key=lambda u: -(par(u)[0].get("vao_pp") or 0))
    w, esq, dir_ = 900, 300, 60
    topo, passo = 40, 40
    h = topo + passo * len(ufs) + 40
    lim = max(abs(par(u)[0].get("vao_pp") or 0) for u in ufs) or 1
    lim = max(5.0, lim * 1.15)
    x = escala(-lim, lim, esq, w - dir_)
    out = [
        svg_abre(
            w,
            h,
            "Vão entre o governador eleito e o presidenciável do mesmo lado",
            "Barras divergentes por UF: percentual da candidatura vencedora ao governo menos o do "
            "finalista presidencial do mesmo lado na mesma UF.",
        )
    ]
    out.append(ln(x(0), topo - 14, x(0), h - 30, INK, 1.2))
    out.append(t(x(0) + 6, topo - 18, "governo acima do presidente →", 12, MUTED))
    out.append(t(x(0) - 6, topo - 18, "← abaixo", 12, MUTED, "end"))
    tips = Tips()
    for i, u in enumerate(ufs):
        a, _ = par(u)
        v = a.get("vao_pp") or 0
        y = topo + i * passo
        quem = "Flávio" if a.get("finalista_comparado") == "flavio" else "Lula"
        cor = cor_campo(a.get("campo"))
        partes = [
            t(esq - 10, y + 18, f"{u['uf']}: {nome(a)} × {quem}", 13, INK, "end"),
            r(min(x(0), x(v)), y + 6, abs(x(v) - x(0)), 20, cor),
            t(
                (x(v) if v >= 0 else x(0)) + 6,
                y + 21,
                f"{'+' if v > 0 else '−' if v < 0 else ''}{num(abs(v), 2)} pp",
                13,
                INK,
                mono=True,
            ),
        ]
        kk = tips.add(
            ficha(
                f"{u['uf']}: {nome(a)}",
                a.get("comparacao") or "",
                [
                    ("governo", f"{num(a.get('pct'), 2)}%"),
                    (
                        f"{quem} na UF",
                        f"{num(a.get('pct_presidencial_mesmo_lado'), 2)}%",
                    ),
                    ("vão", f"{num(v, 2)} pp"),
                    ("vão em votos", inteiro(a.get("vao_votos"))),
                ],
                a.get("evidencia") or "",
            )
        )
        out.append(hit("".join(partes) + area(0, y, w, passo), kk, foco=True))
    out.append("</svg>")
    legenda = (
        f"{(G.get('rotulo_vao') or '').capitalize()}. O lado de cada candidatura segue a coligação registrada ou a "
        "exceção de campo declarada pela casa (ficha ao tocar). Fonte: governadores.json."
    )
    return figura_html("gov_vao", "".join(out), legenda, tips, modo="scroll", minw=700)


def tabela_1t(G: dict) -> str:
    linhas = []
    for u in sorted(G["ufs"], key=lambda u: u["uf"]):
        a, b = par(u)
        ter = u.get("t1_terceiro") or {}
        linhas.append(
            [
                u["uf"],
                f"{nome(a)} {num(a.get('t1_pct'), 2)}% → {num(a.get('pct'), 2)}%",
                f"{nome(b)} {num(b.get('t1_pct'), 2)}% → {num(b.get('pct'), 2)}%",
                f"{nome_bonito(ter.get('nome') or '')} ({ter.get('partido') or ''}, "
                f"{campo_nome(ter.get('campo')).lower()}) {num(ter.get('pct'), 2)}%",
                f"{'+' if (u.get('brancos_nulos_gov_menos_pres_pp') or 0) > 0 else ''}"
                f"{num(u.get('brancos_nulos_gov_menos_pres_pp'), 2)} pp",
            ]
        )
    return tabela(
        [
            "UF",
            "vencedor, 1º → 2º turno",
            "derrotado, 1º → 2º turno",
            "terceiro colocado no 1º turno",
            "brancos e nulos: governo menos presidente",
        ],
        linhas,
        "Comparação com o 1º turno (percentuais dos válidos de cada turno).",
    )
