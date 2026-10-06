"""Figuras dos capítulos 10 e 11: pesquisas contra a urna e voto útil.

Erro é pesquisa menos urna, em pontos dos votos válidos; na diferença Lula menos
Flávio, positivo quer dizer que a pesquisa superestimou Lula. A urna é sempre a
linha de referência; o erro comum de 2022 entra tracejado.
"""

from __future__ import annotations

import math

from .pagina_comum import NOME_UF, inteiro, num
from .pagina_fig_base import (
    COR_CAND,
    FLAVIO,
    GRADE,
    HALO,
    INK,
    LULA,
    MUTED,
    NOME_CAND,
    OUTROS,
    OUTROS_TXT,
    PAPER,
    Tips,
    W,
    area,
    botoes,
    dado,
    escala,
    ficha,
    figura_html,
    hit,
    legenda,
    ln,
    nome_bonito,
    pct,
    posiciona_siglas,
    pp,
    r,
    registra,
    svg_abre,
    t,
    ticks,
)

CINZA_REP = "#8d8f88"
GOLD = "#7d5b00"


def _sn(v: float, casas: int = 1) -> str:
    return pp(v, casas)[:-3]


# ------------------------------------------------------------------ erro por instituto


@registra("pesquisas_erro")
def pesquisas_erro(d, **_op) -> str:
    P = dado(d, "pesquisas_vs_urna")
    ids = P["medias"]["ultimas_ondas_publicado"]["ondas"]
    por_id = {p["id"]: p for p in P["pesquisas"]}
    ondas = [por_id[i] for i in ids if i in por_id]
    ondas.sort(key=lambda p: p["publicado"]["diferenca_lula_menos_flavio"]["erro"])
    ag_pub, ag_rep = (
        P["medias"]["agregador_publicado"],
        P["medias"]["agregador_reponderado"],
    )
    pc = P["previsao_casa"]["central"]
    central = {
        "diferenca_lula_menos_flavio": {"erro": pc["erro_diferenca_lula_menos_flavio"]},
        "erro_blocos_pp": pc["erro_pp"],
    }
    modos = {
        "dif": (
            "Diferença Lula − Flávio",
            lambda b: b["diferenca_lula_menos_flavio"]["erro"],
        ),
        "flavio": (
            "Flávio",
            lambda b: (
                b["erro_blocos_pp"]["flavio"]
                if "erro_blocos_pp" in b
                else b["erro_pp"]["flavio"]
            ),
        ),
        "lula": (
            "Lula",
            lambda b: (
                b["erro_blocos_pp"]["lula"]
                if "erro_blocos_pp" in b
                else b["erro_pp"]["lula"]
            ),
        ),
    }
    esq, topo, passo = 250, 100, 30
    extra = 3
    h = topo + passo * (len(ondas) + extra) + 24 + 50
    vmax = 0.0
    for p in ondas:
        for _, f in modos.values():
            vmax = max(vmax, abs(f(p["publicado"])))
            if p.get("reponderado"):
                vmax = max(vmax, abs(f(p["reponderado"])))
    # o eixo cobre também a margem de 95% da diferença, até 14 pontos; o que
    # passar disso leva a ponta de seta de corte
    marg = max(
        abs(p["publicado"]["diferenca_lula_menos_flavio"]["erro"])
        + p["margem_95_diferenca_aas_pp"]
        for p in ondas
    )
    vmax = min(max(math.ceil((vmax + 1) / 2) * 2, math.ceil(marg / 2) * 2), 14)
    X = escala(-vmax, vmax, esq, W - 60)
    x0 = X(0)
    base = topo + passo * (len(ondas) + extra) + 24
    out = [
        svg_abre(
            W,
            h,
            "Erro das pesquisas finais contra a urna, publicado e reponderado por renda",
            "Ponto escuro: pesquisa publicada; ponto cinza: reponderada pela PNAD; zero é a urna.",
        ),
        '<defs><marker id="pe-seta" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
        f'orient="auto-start-reverse"><path d="M0,0L10,5L0,10z" fill="{INK}"/></marker></defs>',
        legenda([("publicado", INK), ("reponderado por renda", CINZA_REP)], esq, 22),
        t(esq + 430, 22, "traço: margem de 95% da diferença", 13, MUTED),
    ]
    for v in ticks(-vmax, vmax, 8):
        out.append(ln(X(v), topo - 8, X(v), base, GRADE))
        out.append(t(X(v), base + 20, _sn(v, 0), 13, MUTED, "middle", mono=True))
    out.append(
        t(W - 60, base + 40, "erro em pontos percentuais dos válidos", 13, MUTED, "end")
    )
    out.append(ln(x0, topo - 14, x0, base, INK, 2))
    out.append(t(x0, topo - 20, "urna", 14, INK, "middle", "700"))
    ref = P["referencia_2022"]["erro_comum_diferenca_lula_menos_bolsonaro"]
    media = P["resumo_ultimas_ondas"]["publicado"]["media"]
    g_ref = [
        ln(X(ref), topo - 6, X(ref), base, GOLD, 1.6, ' stroke-dasharray="6 4"'),
        t(
            X(ref) + 6,
            base - 6,
            f"erro comum de 2022: {_sn(ref, 2)}",
            13,
            GOLD,
            weight="700",
        ),
        ln(X(media), topo - 6, X(media), base, INK, 1, ' stroke-dasharray="2 3"'),
        t(
            X(media) - 6,
            base - 6,
            f"média 2026: {_sn(media, 2)}",
            13,
            INK,
            "end",
            "700",
        ),
    ]
    out.append(f'<g data-alt-show="dif">{"".join(g_ref)}</g>')
    out.append(t(x0 - 10, 56, "← superestimou Flávio", 13, FLAVIO, "end", "700"))
    out.append(t(x0 + 10, 56, "superestimou Lula →", 13, LULA, weight="700"))
    tips = Tips()
    linhas_ = [
        (
            p["instituto"],
            p["campo"]["fim"][8:10] + "/" + p["campo"]["fim"][5:7],
            p["publicado"],
            p.get("reponderado"),
            p,
        )
        for p in ondas
    ]
    linhas_.append(("Agregador Arvor, 7 dias", "04/10", ag_pub, ag_rep, None))
    linhas_.append(("Central da casa", "04/10", central, None, None))
    for i, (nome, data, pub, rep, onda) in enumerate(linhas_):
        y = topo + i * passo + passo / 2 + (14 if i >= len(ondas) else 0)
        if i == len(ondas):
            out.append(
                ln(esq - 230, y - passo / 2 - 7, W - 60, y - passo / 2 - 7, INK, 1)
            )
        grupos = []
        for modo, (_rot, f) in modos.items():
            a = f(pub)
            b = f(rep) if rep else None
            g = []
            if modo == "dif" and onda:
                m = onda["margem_95_diferenca_aas_pp"]
                lo_, hi_ = max(a - m, -vmax), min(a + m, vmax)
                g.append(
                    ln(X(lo_), y, X(hi_), y, "#c9c1ab", 5, ' stroke-linecap="round"')
                )
                for corte, lado in ((a + m > vmax, 1), (a - m < -vmax, -1)):
                    if corte:
                        xc = X(lado * vmax)
                        g.append(
                            f'<path d="M{xc:.1f} {y - 7:.1f}l{8 * lado} 7l{-8 * lado} 7z" fill="{MUTED}"/>'
                        )
            if b is not None and abs(X(b) - X(a)) > 7:
                g.append(
                    f'<line x1="{X(a):.1f}" y1="{y:.1f}" x2="{X(b):.1f}" y2="{y:.1f}" stroke="{INK}" stroke-width="1.4" marker-end="url(#pe-seta)"/>'
                )
            if b is not None:
                g.append(
                    f'<circle cx="{X(b):.1f}" cy="{y:.1f}" r="5.5" fill="{CINZA_REP}"/>'
                )
            g.append(f'<circle cx="{X(a):.1f}" cy="{y:.1f}" r="6.5" fill="{INK}"/>')
            g.append(
                t(
                    max(X(a), X(b) if b is not None else X(a)) + 12,
                    y + 5,
                    _sn(a),
                    13,
                    INK,
                    mono=True,
                    extra=HALO,
                )
            )
            mostra = "" if modo == "dif" else ' display="none"'
            grupos.append(f'<g data-alt-show="{modo}"{mostra}>{"".join(g)}</g>')
        dif_p = pub["diferenca_lula_menos_flavio"]
        linhas = [
            ("Erro na diferença L − F", pp(dif_p["erro"])),
            (
                "Flávio · Lula (erro)",
                f"{pp(modos['flavio'][1](pub), 1)} · {pp(modos['lula'][1](pub), 1)}",
            ),
        ]
        if rep:
            linhas.append(
                (
                    "Reponderado, diferença",
                    pp(rep["diferenca_lula_menos_flavio"]["erro"]),
                )
            )
        if onda:
            linhas += [
                (
                    "Campo",
                    f"{onda['campo']['inicio'][8:10]}/{onda['campo']['inicio'][5:7]} a {data}",
                ),
                ("Entrevistas · modo", f"{inteiro(onda['n'])} · {onda['modo']}"),
                (
                    "Margem 95% da diferença",
                    f"±{num(onda['margem_95_diferenca_aas_pp'], 1)} pp",
                ),
                (
                    "Fora da margem",
                    "sim" if onda["erro_diferenca_fora_da_margem_aas"] else "não",
                ),
            ]
        k = tips.add(ficha(nome, onda["registro_tse"] if onda else "média", linhas))
        rotulo = t(
            esq - 12,
            y + 5,
            f"{nome} · {data}",
            14,
            INK,
            "end",
            "700" if not onda else None,
        )
        out.append(
            hit(
                area(esq - 240, y - passo / 2, W - 60 - esq + 240, passo)
                + rotulo
                + "".join(grupos),
                k,
                foco=True,
            )
        )
    out.append("</svg>")
    ctl = botoes(
        [("dif", "Diferença L − F"), ("flavio", "Flávio"), ("lula", "Lula")],
        "dif",
        "Erro em",
    )
    res = P["resumo_ultimas_ondas"]["publicado"]
    legenda_ = (
        f"Última onda de cada casa, campo encerrado entre 25/09 e 03/10. {res['positivos']} de {res['n']} superestimaram Lula "
        f"na diferença; erro médio {pp(res['media'])} (2022: {pp(ref)}). A seta vai do publicado ao reponderado por renda. "
        "Proximidade da urna numa eleição não é prova de método. Fonte: pesquisas_vs_urna.json."
    )
    f_dif = modos["dif"][1]
    xs = [X(f_dif(b)) for _, _, pub, rep, _ in linhas_ for b in (pub, rep) if b]
    return figura_html(
        "pesquisas_erro",
        "".join(out),
        legenda_,
        tips,
        controles=ctl,
        minw=860,
        dim=False,
        foco=(min([*xs, x0]) - 14, max(xs) + 60, x0),
    )


# ------------------------------------------------------------------ série do agregador


def _validos(serie: dict, i: int) -> tuple[float, float, float] | None:
    vals = [
        serie[k][i]
        for k in ("flavio", "lula", "outros_centro_direita", "outros_esquerda_nanicos")
    ]
    if any(v is None for v in vals):
        return None
    tot = sum(vals) or 1
    f, lu = 100 * vals[0] / tot, 100 * vals[1] / tot
    return f, lu, 100 - f - lu


@registra("pesquisas_serie")
def pesquisas_serie(d, **_op) -> str:
    A = dado(d, "agregador")["agregador"]
    P = dado(d, "presidente")["nacional"]
    datas = A["serie"]["datas"]
    s1 = A["serie"]["1t"]
    ini = next(i for i, x in enumerate(datas) if x >= "2026-08-01")
    idx = list(range(ini, len(datas)))
    n = len(idx) + 2
    esq, topo, base, dir_ = 70, 50, 420, W - 190
    h = base + 54
    X = escala(0, n - 1, esq, dir_)
    Y = escala(0, 55, base, topo)
    out = [
        svg_abre(
            W,
            h,
            "Agregador Arvor de 1º turno contra a urna",
            "Média móvel de 7 dias em parcela dos válidos, publicada e reponderada por renda; os pontos à direita são a urna.",
        )
    ]
    for v in ticks(0, 55, 6):
        out.append(ln(esq, Y(v), dir_, Y(v), GRADE))
        out.append(t(esq - 8, Y(v) + 5, f"{num(v, 0)}%", 13, MUTED, "end", mono=True))
    for j, i in enumerate(idx):
        if datas[i].endswith("-01") or datas[i].endswith("-15"):
            out.append(ln(X(j), base, X(j), base + 6, MUTED))
            out.append(
                t(
                    X(j),
                    base + 22,
                    f"{datas[i][8:10]}/{datas[i][5:7]}",
                    13,
                    MUTED,
                    "middle",
                    mono=True,
                )
            )
    out.append(ln(esq, base, dir_, base, INK, 1.2))
    xu = X(n - 1)
    out.append(ln(xu, topo - 10, xu, base, INK, 1, ' stroke-dasharray="3 3"'))
    out.append(t(xu, topo - 16, "urna 04/10", 13, INK, "middle", "700"))
    urna = (P["pct"]["flavio"], P["pct"]["lula"], P["pct"]["terceiros"])
    cores = (FLAVIO, LULA, OUTROS)
    nomes = ("Flávio", "Lula", "Terceiros")
    for qual in ("publicado", "ajustado"):
        g = []
        serie = s1[qual]
        for c in range(3):
            segs, atual = [], []
            for j, i in enumerate(idx):
                v = _validos(serie, i)
                if v is None:
                    if atual:
                        segs.append(atual)
                    atual = []
                    continue
                atual.append(f"{X(j):.1f},{Y(v[c]):.1f}")
            if atual:
                segs.append(atual)
            for sg in segs:
                g.append(
                    f'<polyline points="{" ".join(sg)}" fill="none" stroke="{cores[c]}" stroke-width="2.6" stroke-linejoin="round"/>'
                )
        ult = next(
            (_validos(serie, i) for i in reversed(idx) if _validos(serie, i)), None
        )
        if ult:
            for c in range(3):
                xa, ya = X(len(idx) - 1), Y(ult[c])
                g.append(
                    ln(xa, ya, xu, Y(urna[c]), cores[c], 1.4, ' stroke-dasharray="4 4"')
                )
        mostra = "" if qual == "publicado" else ' display="none"'
        out.append(f'<g data-alt-show="{qual}"{mostra}>{"".join(g)}</g>')
    finais = sorted([[Y(urna[c]), c] for c in range(3)])
    for i in range(1, 3):
        finais[i][0] = max(finais[i][0], finais[i - 1][0] + 20)
    for y, c in finais:
        out.append(
            f'<circle cx="{xu:.1f}" cy="{Y(urna[c]):.1f}" r="7" fill="{cores[c]}" stroke="#ffffff" stroke-width="2"/>'
        )
        out.append(
            t(
                xu + 14,
                y + 5,
                f"{nomes[c]} {num(urna[c], 2)}%",
                14,
                OUTROS_TXT if c == 2 else cores[c],
                weight="700",
            )
        )
    tips = Tips()
    linhas = []
    for j, i in enumerate(idx):
        p = _validos(s1["publicado"], i)
        a = _validos(s1["ajustado"], i)
        if p is None:
            linhas.append(
                [
                    f"{datas[i][8:10]}/{datas[i][5:7]}",
                    "sem pesquisa na janela",
                    "",
                    "",
                    "",
                ]
            )
        else:
            linhas.append(
                [
                    f"{datas[i][8:10]}/{datas[i][5:7]}",
                    "publicado · reponderado",
                    f"{num(p[0], 1)} · {num(a[0], 1) if a else 's/d'}",
                    f"{num(p[1], 1)} · {num(a[1], 1) if a else 's/d'}",
                    f"{num(p[2], 1)} · {num(a[2], 1) if a else 's/d'}",
                ]
            )
        cruz = ln(
            X(j), topo, X(j), base, INK, 1, ' class="hit-cross" stroke-dasharray="3 3"'
        )
        out.append(
            hit(
                area(X(j) - (X(1) - X(0)) / 2, topo, X(1) - X(0), base - topo) + cruz,
                f"r{len(linhas) - 1}",
            )
        )
    linhas.append(
        [
            "Urna, 04/10",
            "100% das seções",
            num(urna[0], 2),
            num(urna[1], 2),
            num(urna[2], 2),
        ]
    )
    out.append(hit(area(xu - 14, topo, 28, base - topo), f"r{len(linhas) - 1}"))
    tips.tabela(
        ["Dia", "", "Flávio", "Lula", "Terceiros"],
        linhas,
        sub=1,
        nota="% dos válidos; média de 7 dias pela divulgação",
    )
    out.append("</svg>")
    ctl = botoes(
        [("publicado", "Publicado"), ("ajustado", "Reponderado por renda")],
        "publicado",
        "Série",
    )
    legenda_ = (
        "Média móvel de 7 dias do agregador da casa, em parcela dos válidos (candidaturas renormalizadas para 100). "
        "O tracejado liga a última média à urna. Fonte: docs/assets/reponderacao_pnad.json e presidente.json."
    )
    return figura_html(
        "pesquisas_serie",
        "".join(out),
        legenda_,
        tips,
        controles=ctl,
        minw=860,
        dim=False,
    )


# ------------------------------------------------------------------ central por UF


@registra("central_casa_ufs")
def central_casa_ufs(d, **_op) -> str:
    P = dado(d, "pesquisas_vs_urna")
    linhas_ = sorted(
        P["previsao_casa"]["ufs"]["linhas"],
        key=lambda x: x["erro_diferenca_lula_menos_flavio"],
    )
    esq, topo, passo = 200, 60, 28
    base = topo + passo * len(linhas_)
    h = base + 54
    vmax = (
        math.ceil(max(abs(x["erro_diferenca_lula_menos_flavio"]) for x in linhas_) / 2)
        * 2
    )
    X = escala(-vmax, vmax, esq, W - 160)
    x0 = X(0)
    out = [
        svg_abre(
            W,
            h,
            "Erro da central da casa por UF, na diferença Lula menos Flávio",
            "Barras em pontos dos válidos; positivo superestimou Lula. Marca nas UFs em que o líder previsto errou.",
        ),
        t(x0 - 10, 30, "← superestimou Flávio", 13, FLAVIO, "end", "700"),
        t(x0 + 10, 30, "superestimou Lula →", 13, LULA, weight="700"),
    ]
    for v in ticks(-vmax, vmax, 8):
        out.append(ln(X(v), topo - 6, X(v), base, GRADE))
        out.append(t(X(v), base + 20, _sn(v, 0), 13, MUTED, "middle", mono=True))
    out.append(ln(x0, topo - 6, x0, base, INK, 1.6))
    out.append(
        t(
            W - 160,
            base + 44,
            "erro em pontos percentuais dos válidos",
            13,
            MUTED,
            "end",
        )
    )
    tips = Tips()
    for i, x in enumerate(linhas_):
        y = topo + i * passo
        v = x["erro_diferenca_lula_menos_flavio"]
        xa, xb = sorted((x0, X(v)))
        corpo = (
            t(esq - 12, y + 19, NOME_UF[x["uf"]], 14, INK, "end")
            + r(xa, y + 5, xb - xa, passo - 10, LULA if v > 0 else FLAVIO)
            + t(
                X(v) + (6 if v >= 0 else -6),
                y + 19,
                _sn(v),
                13,
                INK,
                "start" if v >= 0 else "end",
                mono=True,
            )
        )
        if not x["acertou_lider"]:
            # encostado na barra: depois do número se ela cresce para a direita,
            # do outro lado do zero se cresce para a esquerda
            xm = X(v) + 6 + 7.9 * len(_sn(v)) + 8 if v >= 0 else x0 + 8
            corpo += t(xm, y + 19, "líder errado", 13, "#b02f21", weight="700")
        pv, e = x["validos"], x["erro_pp"]
        k = tips.add(
            ficha(
                f"{NOME_UF[x['uf']]} ({x['uf']})",
                x["regiao"],
                [
                    (
                        "Flávio previsto · urna",
                        f"{pct(pv['flavio'], 1)} · {pct(pv['flavio'] - e['flavio'], 1)}",
                    ),
                    (
                        "Lula previsto · urna",
                        f"{pct(pv['lula'], 1)} · {pct(pv['lula'] - e['lula'], 1)}",
                    ),
                    (
                        "Terceira via prevista · urna",
                        f"{pct(pv['terceira_via'], 1)} · {pct(pv['terceira_via'] - e['terceira_via'], 1)}",
                    ),
                    ("Erro na diferença", pp(v)),
                    (
                        "Líder previsto · urna",
                        f"{NOME_CAND[x['lider_previsto']]} · {NOME_CAND[x['lider_urna']]}",
                    ),
                ],
            )
        )
        out.append(hit(area(0, y, W, passo) + corpo, k))
    out.append("</svg>")
    c = P["previsao_casa"]["central"]
    legenda_ = (
        f"Previsão central da casa (04/10) contra a urna, por UF. No país o erro na diferença foi {pp(c['erro_diferenca_lula_menos_flavio'])}. "
        "Fonte: pesquisas_vs_urna.json (previsao_casa.ufs)."
    )
    xs = [X(x["erro_diferenca_lula_menos_flavio"]) for x in linhas_]
    return figura_html(
        "central_casa_ufs",
        "".join(out),
        legenda_,
        tips,
        minw=820,
        foco=(min([*xs, x0]) - 50, max([*xs, x0]) + 60, x0),
    )


# ------------------------------------------------------------------ Senado: calibração


@registra("senado_brier")
def senado_brier(d, **_op) -> str:
    P = dado(d, "pesquisas_vs_urna")["senado"]
    pts = []
    for x in P["linhas"]:
        for e in x["eleitos"]:
            pts.append((x["uf"], e, True, x["cobertura"]))
        ne = x.get("nao_eleito_mais_provavel")
        if ne:
            pts.append((x["uf"], ne, False, x["cobertura"]))
    esq, topo = 260, 60
    faixa_h = 150
    h = topo + 2 * faixa_h + 70
    X = escala(0, 1, esq, W - 50)
    out = [
        svg_abre(
            W,
            h,
            "Senado: probabilidade prevista de cada candidatura e o resultado",
            "Em cima, os 54 eleitos; embaixo, o não eleito mais provável de cada UF; posição pela probabilidade prevista.",
        )
    ]
    for v in ticks(0, 1, 5):
        out.append(ln(X(v), topo - 6, X(v), topo + 2 * faixa_h, GRADE))
        out.append(
            t(
                X(v),
                topo + 2 * faixa_h + 22,
                f"{num(100 * v, 0)}%",
                13,
                MUTED,
                "middle",
                mono=True,
            )
        )
    out.append(
        t(
            (esq + W - 50) / 2,
            h - 12,
            "probabilidade de eleição prevista pela casa em 04/10",
            14,
            INK,
            "middle",
            "600",
        )
    )
    tips = Tips()
    for faixa, (rot, eleito) in enumerate(
        (("Eleitos (54)", True), ("Não eleito mais provável", False))
    ):
        y0 = topo + faixa * faixa_h
        out.append(
            r(
                esq,
                y0 + 4,
                W - 50 - esq,
                faixa_h - 8,
                "#ebe4d4" if eleito else "#f0ebdf",
            )
        )
        out.append(t(esq - 14, y0 + faixa_h / 2 + 5, rot, 14, INK, "end", "700"))
        pilhas: dict[int, int] = {}
        for uf, e, el, cob in sorted(
            (p for p in pts if p[2] == eleito), key=lambda p: p[1]["p_eleito"]
        ):
            b = round(e["p_eleito"] * 40)
            n = pilhas.get(b, 0)
            pilhas[b] = n + 1
            x = X(e["p_eleito"])
            y = y0 + faixa_h - 18 - n * 15
            cor = INK if el else "#b02f21"
            preench = cor if cob == "recente" else "#ffffff"
            k = tips.add(
                ficha(
                    nome_bonito(e["nome"]),
                    f"{e.get('partido', '')} · {uf}",
                    [
                        ("Probabilidade prevista", pct(100 * e["p_eleito"], 1)),
                        ("Votos na urna", pct(e["pct"], 2)),
                        ("Resultado", "eleito" if el else "não eleito"),
                        (
                            "Pesquisas na UF",
                            "recentes" if cob == "recente" else "antigas",
                        ),
                    ],
                )
            )
            out.append(
                hit(
                    f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6.5" fill="{preench}" stroke="{cor}" stroke-width="2"/>',
                    k,
                )
            )
    res = P["resumo"]
    out.append(
        t(
            esq,
            30,
            f"Brier {num(res['brier'], 3)} · média sem incerteza {num(res['brier_media_sem_incerteza'], 3)} · "
            f"chute uniforme {num(res['brier_uniforme_2_sobre_k'], 3)} (menor é melhor)",
            14,
            INK,
            weight="600",
        )
    )
    out.append("</svg>")
    legenda_ = (
        f"Os dois mais prováveis de cada UF levaram {res['acertos_top2']} das {res['vagas']} vagas "
        f"({num(res['acertos_top2_esperados'], 1)} esperadas). Círculo vazado: UF só com pesquisas antigas. "
        "Fonte: pesquisas_vs_urna.json (senado)."
    )
    return figura_html(
        "senado_brier", "".join(out), legenda_, tips, minw=820, dim=False
    )


# ------------------------------------------------------------------ voto útil


@registra("voto_util_cascata")
def voto_util_cascata(d, **_op) -> str:
    V = dado(d, "voto_util")
    tc = V["terceiros_por_candidato"]["publicado"]
    total = V["terceira_via"]["media_publicado_todas"]
    urna = V["terceira_via"]["urna_validos"]
    ordem = sorted(tc["queda_pp"].items(), key=lambda kv: -kv[1])
    passos = [("Terceiros nas pesquisas finais", total, "total", None)]
    passos += [(NOME_CAND.get(c, nome_bonito(c)), -v, "delta", c) for c, v in ordem]
    passos.append(("Terceiros na urna", urna, "total", None))
    esq, topo, base = 70, 50, 360
    h = base + 90
    Y = escala(0, math.ceil(total / 2) * 2, base, topo)
    col = (W - 260 - esq) / len(passos)
    out = [
        svg_abre(
            W,
            h,
            "Voto útil: da terceira via nas pesquisas à terceira via na urna",
            "Cascata em pontos dos válidos: média das pesquisas finais, queda de cada candidatura e o resultado.",
        )
    ]
    for v in ticks(0, math.ceil(total / 2) * 2, 6):
        out.append(ln(esq, Y(v), W - 260, Y(v), GRADE))
        out.append(t(esq - 8, Y(v) + 5, f"{num(v, 0)}%", 13, MUTED, "end", mono=True))
    tips = Tips()
    nivel = 0.0
    for i, (rot, v, tipo, chave) in enumerate(passos):
        x = esq + i * col + col * 0.16
        bw = col * 0.68
        if tipo == "total":
            a, b = 0.0, v
            nivel = v
            cor = INK
        else:
            a, b = nivel + v, nivel
            nivel += v
            cor = COR_CAND.get(chave, "#8fb8aa")
        ya, yb = Y(max(a, b)), Y(min(a, b))
        corpo = r(x, ya, bw, max(yb - ya, 2), cor)
        corpo += t(
            x + bw / 2,
            ya - 8,
            num(v, 2) if tipo == "total" else _sn(v, 2),
            14,
            INK,
            "middle",
            "700",
            mono=True,
        )
        palavras = rot.split()
        corpo += t(x + bw / 2, base + 22, " ".join(palavras[:2]), 13, INK, "middle")
        if len(palavras) > 2:
            corpo += t(x + bw / 2, base + 40, " ".join(palavras[2:]), 13, INK, "middle")
        if i + 1 < len(passos):
            corpo += ln(
                x + bw, Y(nivel), x + col, Y(nivel), MUTED, 1, ' stroke-dasharray="3 3"'
            )
        if tipo == "total":
            k = tips.add(ficha(rot, "% dos válidos", [("Parcela", pct(v, 2))]))
        else:
            media = tc["media_validos"].get(chave)
            na_urna = V["terceiros_por_candidato"]["urna_validos"].get(chave)
            k = tips.add(
                ficha(
                    rot,
                    "queda das pesquisas à urna",
                    [
                        ("Média das pesquisas finais", pct(media)),
                        ("Urna", pct(na_urna)),
                        ("Queda", pp(v)),
                        ("Queda relativa", pct(100 * tc["queda_relativa"][chave], 0)),
                        (
                            "Fatia da queda total",
                            pct(100 * tc["fatia_da_queda"][chave], 0),
                        ),
                    ],
                )
            )
        out.append(
            hit(area(esq + i * col, topo, col, base - topo + 46) + corpo, k, foco=True)
        )
    out.append(ln(esq, base, W - 260, base, INK, 1.2))
    rn = V["reserva_nacional"]
    xn = W - 240
    out.append(t(xn, topo + 10, "Para onde foi", 15, INK, weight="700"))
    out.append(
        t(
            xn,
            topo + 38,
            f"Flávio {_sn(rn['ganho_medio_validos_flavio_pp'], 2)} sobre",
            14,
            FLAVIO,
            weight="700",
        )
    )
    out.append(t(xn, topo + 58, "as pesquisas", 14, FLAVIO, weight="700"))
    out.append(
        t(
            xn,
            topo + 88,
            f"Lula {_sn(rn['ganho_medio_validos_lula_pp'], 2)}",
            14,
            LULA,
            weight="700",
        )
    )
    dec = V["decomposicao"]["agregados"]["ultimas_ondas_publicado"][
        "nexus_renormalizada"
    ]
    out.append(
        t(
            xn,
            topo + 124,
            f"consolidação explica {num(dec['explicado_diferenca_pp'], 2)}",
            13,
            INK,
        )
    )
    out.append(
        t(
            xn,
            topo + 144,
            f"dos {num(dec['erro_diferenca_lula_menos_flavio_pp'], 2)} pp de erro",
            13,
            INK,
        )
    )
    out.append(
        t(
            xn,
            topo + 164,
            f"({pct(100 * dec['fracao_explicada_diferenca'], 0)}, matriz Nexus)",
            13,
            MUTED,
        )
    )
    out.append("</svg>")
    legenda_ = (
        f"Média das {tc['n_ondas']} ondas finais publicadas contra a urna, em parcela dos válidos. A terceira via caiu "
        f"{num(total - urna, 2)} pontos. Estimativa sob hipóteses declaradas, não medição do eleitor individual. Fonte: voto_util.json."
    )
    return figura_html("voto_util_cascata", "".join(out), legenda_, tips, minw=860)


@registra("reserva_vs_urna")
def reserva_vs_urna(d, **_op) -> str:
    V = dado(d, "voto_util")
    ufs = [
        u
        for u in V["reserva_ufs"]
        if u.get("reserva_flavio_pp_media_casas") is not None
    ]
    esq, topo, lado_w, lado_h = 90, 40, 760, 520
    h = topo + lado_h + 70
    xs = [u["reserva_flavio_pp_media_casas"] for u in ufs]
    ys = [u["ganho_flavio_sobre_pesquisa_pp"] for u in ufs]
    xmax = math.ceil(max(xs) / 2) * 2
    ylo, yhi = math.floor(min([*ys, 0]) / 2) * 2, math.ceil(max([*ys, xmax]) / 2) * 2
    X = escala(0, xmax, esq, esq + lado_w)
    Y = escala(ylo, yhi, topo + lado_h, topo)
    out = [
        svg_abre(
            W,
            h,
            "Reserva de 2º turno medida contra o ganho revelado na urna, por UF",
            "Eixo horizontal: reserva de Flávio nas pesquisas estaduais; vertical: quanto Flávio fez acima das pesquisas.",
        )
    ]
    for v in ticks(0, xmax, 6):
        out.append(ln(X(v), topo, X(v), topo + lado_h, GRADE))
        out.append(
            t(X(v), topo + lado_h + 22, num(v, 0), 13, MUTED, "middle", mono=True)
        )
    for v in ticks(ylo, yhi, 6):
        out.append(ln(esq, Y(v), esq + lado_w, Y(v), GRADE))
        out.append(t(esq - 8, Y(v) + 5, _sn(v, 0), 13, MUTED, "end", mono=True))
    out.append(ln(X(0), Y(0), X(xmax), Y(0), INK, 1.2))
    lim = min(xmax, yhi)
    out.append(ln(X(0), Y(0), X(lim), Y(lim), INK, 1.4, ' stroke-dasharray="6 4"'))
    out.append(
        t(X(lim) - 6, Y(lim) + 18, "toda a reserva revelada", 13, INK, "end", "700")
    )
    out.append(
        t(
            esq + lado_w / 2,
            h - 16,
            "reserva de 2º turno de Flávio nas pesquisas estaduais (pontos)",
            14,
            INK,
            "middle",
            "600",
        )
    )
    yy = topo + lado_h / 2
    out.append(
        t(
            24,
            yy,
            "Flávio na urna menos nas pesquisas (pp)",
            14,
            INK,
            "middle",
            "600",
            extra=f' transform="rotate(-90 24 {yy:.0f})"',
        )
    )
    tips = Tips()
    pos = [
        (
            X(u["reserva_flavio_pp_media_casas"]),
            Y(u["ganho_flavio_sobre_pesquisa_pp"]),
            u["uf"],
        )
        for u in ufs
    ]
    siglas = posiciona_siglas(
        pos, (esq + 2, topo + 2, esq + lado_w - 2, topo + lado_h - 2)
    )
    # pontos primeiro, rótulos por cima: nenhuma sigla fica sob outro ponto
    for x, y, _ in pos:
        out.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="{FLAVIO}" fill-opacity="0.8" '
            'stroke="#ffffff" stroke-width="1.5" pointer-events="none"/>'
        )
    for u, (x, y, _), (sx, sy, sw, sh, fio) in zip(ufs, pos, siglas, strict=True):
        casas = ", ".join(c["casa"] for c in u.get("casas", []))
        k = tips.add(
            ficha(
                f"{NOME_UF[u['uf']]} ({u['uf']})",
                "estimada" if u.get("estimado") else casas,
                [
                    (
                        "Reserva medida",
                        f"{num(u['reserva_flavio_pp_media_casas'], 2)} pp",
                    ),
                    ("Revelada na urna", pp(u["ganho_flavio_sobre_pesquisa_pp"])),
                    ("Fração revelada (λ)", num(u["lambda_flavio_media_casas"], 2)),
                    ("Lula sobre as pesquisas", pp(u["ganho_lula_sobre_pesquisa_pp"])),
                    ("Eleitores na reserva", inteiro(u["reserva_flavio_eleitores"])),
                ],
            )
        )
        ligacao = ""
        if fio:
            nx = min(max(x, sx), sx + sw)
            ny = min(max(y, sy), sy + sh)
            ligacao = ln(x, y, nx, ny, INK, 0.8)
        out.append(
            hit(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="9" fill="transparent"/>'
                + ligacao
                + r(
                    sx,
                    sy,
                    sw,
                    sh,
                    PAPER,
                    f' rx="2" stroke="{MUTED}" stroke-width="0.5"',
                )
                + t(sx + 3, sy + sh - 4, u["uf"], 13, INK, weight="700"),
                k,
            )
        )
    lam = V["reserva_nacional"]["lambda_flavio"]
    xn = esq + lado_w + 30
    out.append(t(xn, topo + 20, "No país", 15, INK, weight="700"))
    out.append(t(xn, topo + 46, f"λ mediano {num(lam['mediana'], 2)}:", 14, INK))
    out.append(t(xn, topo + 66, f"{pct(100 * lam['mediana'], 0)} da reserva", 14, INK))
    out.append(t(xn, topo + 86, "de Flávio apareceu", 14, INK))
    out.append(t(xn, topo + 106, "já no 1º turno", 14, INK))
    out.append("</svg>")
    legenda_ = (
        "Reserva = Flávio no 2º turno menos Flávio no 1º turno na mesma pesquisa estadual (média das casas). "
        "Pontos acima da diagonal: Flávio passou das pesquisas por mais que a reserva medida, o que inclui erro de pesquisa. "
        "Fonte: voto_util.json (reserva_ufs)."
    )
    return figura_html("reserva_vs_urna", "".join(out), legenda_, tips, minw=860)
