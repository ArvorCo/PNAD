"""Figuras dos cards 9 a 16 da super thread: assembleias, governadores, pesquisas,
voto útil, anomalias, seções de 90%, grupos e modelo de urna."""

from __future__ import annotations

import math

import voto_util_mapa as VM

from .secoes_clusters_leitura import extenso
from .thread_base import (
    CAMPO,
    CAMPOS,
    CINZA,
    FLAVIO,
    GOLD,
    GOLD_FILL,
    GRID,
    INK,
    LULA,
    MONO,
    MUTED,
    OUTROS,
    PAPER,
    PAPER2,
    ROT_CAMPO,
    WHITE,
    H,
    W,
    circ,
    dado,
    etiqueta,
    legenda,
    ln,
    nome_proprio,
    num,
    pct,
    r,
    sinal,
    svg,
    t,
)

# ------------------------------------------------------------------ 9 assembleias


def fig_assembleias() -> str:
    a = dado("assembleias")
    cp = {c["uf"]: c for c in dado("comparacao_2022")["assembleias"]["casas"]}
    x0, x1 = 120, 860
    out = [
        t(
            x0,
            22,
            "Cadeiras por campo, 2026; o traço marca direita e centro-direita em 2022",
            16,
            MUTED,
            600,
        )
    ]
    y = 40
    for c in a["casas"]:
        tot = c["vagas"]
        xx = x0
        out.append(t(x0 - 14, y + 26, c["uf"], 20, INK, 700, "end", MONO))
        for k in CAMPOS:
            w = (x1 - x0) * c["por_campo"][k] / tot
            out.append(r(xx, y + 8, w, 26, CAMPO[k]))
            xx += w
        d22 = cp[c["uf"]]["por_bloco_2022"]["direita + centro-direita"]
        xm = x1 - (x1 - x0) * d22 / tot
        out.append(ln(xm, y + 2, xm, y + 40, INK, 3))
        bd = c["blocos"]["direita + centro-direita"]
        out.append(t(x1 + 12, y + 28, f"{bd} de {tot}", 17, INK, 700, "start", MONO))
        y += 46
    meio = (x0 + x1) / 2
    out.append(ln(meio, 34, meio, y + 4, MUTED, 1.5, "4 4"))
    out.append(t(meio, y + 24, "metade da casa", 14, MUTED, 600, "middle"))
    out.append(legenda([(ROT_CAMPO[k], CAMPO[k]) for k in CAMPOS], 0, 590, 15))
    return svg("".join(out), "Assembleias dos onze maiores colégios")


# ------------------------------------------------------------------ 10 governadores


def fig_governadores() -> str:
    lista = [x for x in dado("governadores")["vao_estadual"]["lista"] if x["principal"]]
    lista.sort(key=lambda x: -x["vao_pp"])
    n = len(lista)
    passo = (W - 48) / n
    yz, esc = 290, 7.6
    out = [
        t(
            0,
            22,
            "Governador menos o presidenciável do mesmo lado, pontos dos válidos",
            16,
            MUTED,
            600,
        )
    ]
    for v in (-20, -10, 10, 20, 30):
        y = yz - v * esc
        out.append(ln(0, y, W, y, GRID, 1, "3 5"))
        out.append(t(W, y - 4, sinal(v, 0), 13, MUTED, 500, "end", MONO))
    out.append(ln(0, yz, W, yz, INK, 1.5))
    for i, x in enumerate(lista):
        v = x["vao_pp"]
        cx = i * passo
        cor = CAMPO[x["campo"]]
        hh = abs(v) * esc
        out.append(r(cx + 3, yz - hh if v > 0 else yz, passo - 6, hh, cor, 2))
        uf = x["uf"].upper()
        if v >= 0:
            out.append(t(cx + passo / 2, yz + 20, uf, 13, INK, 700, "middle", MONO))
            out.append(
                t(cx + passo / 2, yz - hh - 6, _int(v), 13, INK, 700, "middle", MONO)
            )
        else:
            out.append(t(cx + passo / 2, yz - 8, uf, 13, INK, 700, "middle", MONO))
            out.append(
                t(cx + passo / 2, yz + hh + 16, _int(v), 13, INK, 700, "middle", MONO)
            )
    out.append(
        t(
            0,
            520,
            "Direita e centro-direita contra Flávio; esquerda contra Lula; centro e PB contra o finalista da coligação.",
            15,
            MUTED,
            500,
        )
    )
    out.append(t(0, 545, "Teto endereçável, nunca transferência certa.", 15, INK, 700))
    out.append(legenda([(ROT_CAMPO[k], CAMPO[k]) for k in CAMPOS], 0, 590, 15))
    return svg("".join(out), "Vão estadual nas 27 UFs")


# ------------------------------------------------------------------ 11 pesquisas


def fig_pesquisas() -> str:
    p = dado("pesquisas_vs_urna")
    ondas = {o["id"]: o for o in p["pesquisas"]}
    ids = p["medias"]["ultimas_ondas_publicado"]["ondas"]
    linhas = []
    for i in ids:
        o = ondas[i]
        pub = o["publicado"]["diferenca_lula_menos_flavio"]["erro"]
        rep = (
            (o.get("reponderado") or {})
            .get("diferenca_lula_menos_flavio", {})
            .get("erro")
        )
        linhas.append((o["instituto"], pub, rep))
    linhas.sort(key=lambda x: x[1])
    central = p["previsao_casa"]["central"]["erro_diferenca_lula_menos_flavio"]
    comum = p["medias"]["ultimas_ondas_publicado"]["diferenca_lula_menos_flavio"][
        "erro"
    ]
    x0, x1 = 230, 960
    vmin, vmax = -4, 9

    def sx(v):
        return x0 + (x1 - x0) * (v - vmin) / (vmax - vmin)

    out = [
        t(
            0,
            20,
            "Erro na diferença Lula menos Flávio, pontos; positivo = Lula superestimado",
            16,
            MUTED,
            600,
        )
    ]
    y_fim = 40 + (len(linhas) + 1) * 34
    for v in range(vmin, vmax + 1, 2):
        out.append(
            ln(
                sx(v),
                34,
                sx(v),
                y_fim,
                GRID if v else INK,
                1.5 if not v else 1,
                None if not v else "3 5",
            )
        )
        out.append(
            t(
                sx(v),
                y_fim + 22,
                sinal(v, 0) if v else "urna",
                15,
                MUTED,
                600,
                "middle",
                MONO,
            )
        )
    out.append(ln(sx(comum), 34, sx(comum), y_fim, GOLD, 3, "6 4"))
    out.append(
        etiqueta(sx(comum), 48, f"erro comum {sinal(comum)}", 15, GOLD, anchor="middle")
    )
    y = 64
    for nome, pub, rep in linhas:
        out.append(t(x0 - 14, y + 6, nome, 16, INK, 600, "end"))
        if rep is not None:
            out.append(ln(sx(pub), y, sx(rep), y, OUTROS, 3))
            out.append(
                circ(sx(rep), y, 7, WHITE, f' stroke="{OUTROS}" stroke-width="3"')
            )
        out.append(circ(sx(pub), y, 8, LULA))
        y += 34
    out.append(r(0, y - 16, W, 32, PAPER2, 4))
    out.append(t(x0 - 14, y + 6, "Central da casa", 16, FLAVIO, 800, "end"))
    out.append(circ(sx(central), y, 9, FLAVIO))
    out.append(
        t(sx(central) + 16, y + 6, sinal(central), 15, FLAVIO, 700, "start", MONO)
    )
    out.append(
        legenda(
            [
                ("Publicado", LULA),
                ("Reponderado pela renda da PNAD", OUTROS),
                ("Central da casa", FLAVIO),
            ],
            0,
            590,
            15,
        )
    )
    return svg("".join(out), "Pesquisas contra a urna")


# ------------------------------------------------------------------ 12 voto útil


def fig_voto_util() -> str:
    vu = dado("voto_util")["terceiros_por_candidato"]
    pub, urna = vu["publicado"]["media_validos"], vu["urna_validos"]
    out = []

    def painel(x0, chaves, vmin, vmax, titulo):
        y0, y1 = 70, 470
        xa, xb = x0 + 150, x0 + 390

        def sy(v):
            return y1 - (y1 - y0) * (v - vmin) / (vmax - vmin)

        o = [t(x0 + 270, 30, titulo, 17, INK, 700, "middle")]
        o.append(t(xa, y1 + 34, "pesquisas", 15, MUTED, 600, "middle"))
        o.append(t(xb, y1 + 34, "urna", 15, MUTED, 600, "middle"))
        o.append(ln(xa, y0 - 10, xa, y1, GRID, 1.5))
        o.append(ln(xb, y0 - 10, xb, y1, GRID, 1.5))
        usados_a, usados_b = [], []
        for k, nome, cor in chaves:
            a, b = pub[k], urna[k]
            o.append(ln(xa, sy(a), xb, sy(b), cor, 4))
            o.append(circ(xa, sy(a), 7, cor))
            o.append(circ(xb, sy(b), 7, cor))
            ya, yb = sy(a) + 6, sy(b) + 6
            while any(abs(ya - u) < 20 for u in usados_a):
                ya += 20
            while any(abs(yb - u) < 20 for u in usados_b):
                yb += 20
            usados_a.append(ya)
            usados_b.append(yb)
            o.append(
                t(xa - 14, ya, f"{nome} {num(a, 1)}", 15, _texto(cor), 700, "end", MONO)
            )
            o.append(t(xb + 14, yb, num(b, 1), 15, _texto(cor), 700, "start", MONO))
        return "".join(o)

    out.append(
        painel(
            -20,
            [("flavio", "Flávio", FLAVIO), ("lula", "Lula", LULA)],
            42,
            48,
            "Finalistas, % dos válidos",
        )
    )
    out.append(
        painel(
            470,
            [
                ("renan_santos", "Renan", OUTROS),
                ("cury", "Cury", "#3d8a74"),
                ("caiado", "Caiado", GOLD),
                ("zema", "Zema", CINZA),
            ],
            0,
            4,
            "Terceira via, % dos válidos",
        )
    )
    out.append(
        t(
            0,
            560,
            f"Média das últimas ondas de {dado('pesquisas_vs_urna')['medias']['ultimas_ondas_publicado']['n_ondas']} casas contra a urna. Quanto a terceira via perdeu explica parte do erro, não todo.",
            15,
            MUTED,
            500,
        )
    )
    return svg("".join(out), "Voto útil: pesquisas contra urna")


# ------------------------------------------------------------------ 13 anomalias


def fig_anomalias() -> str:
    a = dado("anomalias")
    topo = a["topo"][:50]
    w, h = 620, 600
    geo = VM.paths(w, h, 8)
    proj, _ = VM._proj(w, h, 8)
    out = []
    for g in geo.values():
        out.append(
            f'<path d="{g["d"]}" fill="{PAPER2}" stroke="#c9c1ad" stroke-width="1"/>'
        )
    hip = 0
    for x in topo:
        if x["lat"] is None:
            continue
        px, py = proj(x["lon"], x["lat"])
        local = any("efeito político local" in e for e in x["explicacao_provavel"])
        hip += local
        cor = GOLD_FILL if local else OUTROS
        out.append(
            circ(
                px, py, 9, cor, f' stroke="{INK}" stroke-width="1.2" fill-opacity="0.9"'
            )
        )
    bx = 650
    out.append(t(bx, 60, f"As {len(topo)} zonas mais atípicas", 20, INK, 700))
    out.append(t(bx, 86, f"entre {num(a['resumo']['n_zonas'])}", 17, MUTED, 600))
    out.append(circ(bx + 12, 140, 11, OUTROS, f' stroke="{INK}" stroke-width="1.2"'))
    out.append(t(bx + 34, 147, f"{len(topo) - hip} com explicação comum", 18, INK, 600))
    out.append(circ(bx + 12, 186, 11, GOLD_FILL, f' stroke="{INK}" stroke-width="1.2"'))
    out.append(t(bx + 34, 193, f"{hip} hipóteses de política local", 18, INK, 600))
    out.append(t(bx, 250, "Explicações comuns:", 17, INK, 700))
    regras = a["resumo"]["topo_por_regra"]
    yy = 278
    for k in (
        "zona pequena",
        "voto concentrado em terceira via",
        "eleitorado cresceu",
        "padrão regional",
    ):
        out.append(t(bx, yy, f"{k}: {regras.get(k, 0)}", 16, INK, 500))
        yy += 26
    out.append(r(bx, 410, 340, 150, PAPER2, 8))
    out.append(
        t(
            bx + 170,
            476,
            "Nenhuma",
            46,
            FLAVIO,
            800,
            "middle",
            "Fraunces, Georgia, serif",
        )
    )
    out.append(t(bx + 170, 512, "aponta para fraude", 18, INK, 700, "middle"))
    out.append(
        t(bx + 170, 536, "nos dados de urna e de 2022", 15, MUTED, 600, "middle")
    )
    return svg("".join(out), "Mapa das 50 zonas mais atípicas")


# ------------------------------------------------------------------ 14 seções 90%


def fig_secoes90() -> str:
    e = dado("secoes")["extremos"]
    hist = e["histograma"]
    hist["bins_pct"]
    lula, fla = hist["lula"], hist["flavio"]
    x0, x1, ym = 70, 960, 300
    esc = 210 / math.sqrt(max(max(lula), max(fla)))
    n = len(lula)
    largura = (x1 - x0) / n
    out = [r(x0 + (x1 - x0) * 0.9, 30, (x1 - x0) * 0.1, 540, PAPER2)]
    for i in range(n):
        x = x0 + i * largura
        hl, hf = math.sqrt(lula[i]) * esc, math.sqrt(fla[i]) * esc
        out.append(r(x + 1, ym - hl, largura - 2, hl, LULA))
        out.append(r(x + 1, ym, largura - 2, hf, FLAVIO))
    for p in (0, 25, 50, 75, 90, 100):
        x = x0 + (x1 - x0) * p / 100
        out.append(
            t(x, ym + 6 if False else 590, f"{p}%", 15, MUTED, 600, "middle", MONO)
        )
        out.append(ln(x, 560, x, 568, MUTED, 1))
    out.append(ln(x0, ym, x1, ym, INK, 1.5))
    res = {(x["candidato"], x["limiar"]): x for x in e["resumo"]}
    out.append(t(x0, 40, "Seções por faixa da parcela de Lula", 17, LULA, 700))
    out.append(t(x0, 560, "Seções por faixa da parcela de Flávio", 17, FLAVIO, 700))
    xr = x0 + (x1 - x0) * 0.9 - 10
    out.append(
        etiqueta(
            xr,
            64,
            f"{num(res[('lula', 90)]['secoes'])} seções de Lula a 90% ou mais",
            17,
            LULA,
            anchor="end",
        )
    )
    out.append(
        etiqueta(
            xr,
            470,
            f"{num(res[('flavio', 90)]['secoes'])} de Flávio",
            17,
            FLAVIO,
            anchor="end",
        )
    )
    c22 = e["comparacao_2022"]["lula"]
    out.append(
        etiqueta(
            xr,
            96,
            f"{num(c22['tambem_90_em_2022_1t'])} de {num(c22['secoes_90_2026_casadas'])} já davam 90% a Lula em 2022",
            17,
            INK,
            anchor="end",
        )
    )
    return svg("".join(out), "Distribuição das seções pela parcela de cada finalista")


# ------------------------------------------------------------------ 15 grupos

PARTES_GRUPO = [  # (chave do centro, nome, cor da barra, cor do texto dentro)
    ("lula", "Lula", LULA, WHITE),
    ("flavio", "Flávio", FLAVIO, WHITE),
    ("terceiros", "terceiros, fora do modelo", OUTROS, WHITE),
    ("brancos", "brancos", GRID, INK),
    ("nulos", "nulos", CINZA, WHITE),
    ("abstencao", "abstenção", GOLD_FILL, INK),
]


def _curto(artefato: str) -> str:
    """'sem voto branco' → 'sem branco'; 'mesmo número de brancos e de nulos' →
    'brancos = nulos'."""
    if artefato.startswith("mesmo número de "):
        a, b = artefato.removeprefix("mesmo número de ").split(" e de ", 1)
        return f"{a} = {b}"
    return artefato.replace("sem voto ", "sem ")


def fig_grupos() -> str:
    """Cinco grupos da mistura de cinco partes: o eleitorado de cada um em barra de
    100%, com tamanho e região; no rodapé, a versão de 15 partes que não deu certo."""
    c = dado("secoes")["clusters"]
    comp = c["componentes"]
    q = (c.get("variantes") or {}).get("quinze_partes") or {}
    x0, x1, y0 = 250, 990, 50
    passo = min(84, int((H - y0 - 130) / max(1, len(comp))))
    out = [
        t(
            0,
            24,
            "Eleitorado de cada grupo de seções, em % dos aptos (média das seções do grupo)",
            16,
            MUTED,
            600,
        )
    ]
    for i, g in enumerate(comp):
        y = y0 + i * passo
        reg = (g.get("regioes") or [{}])[0]
        out.append(t(0, y + 22, f"Grupo {i + 1}", 20, INK, 700))
        out.append(
            t(
                0,
                y + 43,
                f"{num(g['secoes'])} seções · {reg.get('regiao', '')} "
                f"{num(reg.get('pct_do_cluster') or 0)}%",
                14,
                MUTED,
                600,
            )
        )
        if g.get("artefato"):
            out.append(
                t(0, y + 63, f"artefato: {_curto(g['artefato'])}", 14, GOLD, 700)
            )
        ce = dict(g["centro_pct_eleitorado"])
        ce["terceiros"] = g.get("terceiros_pct_eleitorado") or 0.0
        total = sum(ce.get(k) or 0.0 for k, *_ in PARTES_GRUPO) or 1.0
        xx = float(x0)
        for k, _, cor, cor_txt in PARTES_GRUPO:
            w = (x1 - x0) * (ce.get(k) or 0.0) / total
            out.append(r(xx, y + 8, w, 44, cor))
            rot = num(ce.get(k) or 0.0)
            if w >= 0.62 * 18 * len(rot) + 12:
                out.append(t(xx + w / 2, y + 37, rot, 18, cor_txt, 700, "middle", MONO))
            xx += w
    y = y0 + len(comp) * passo + 14
    out.append(legenda([(n, cor) for _, n, cor, _ in PARTES_GRUPO[:3]], 0, y + 4, 15))
    out.append(legenda([(n, cor) for _, n, cor, _ in PARTES_GRUPO[3:]], 0, y + 30, 15))
    out.append(
        t(
            0,
            y + 66,
            f"Antes: 15 partes, {num(q.get('zeros_substituidos_pct') or 0, 1)}% das células em zero, "
            f"V de Cramér com a região {num(q.get('cramer_v_regiao') or 0, 2)}: grupos de zeros.",
            15,
            MUTED,
            600,
        )
    )
    n_art = sum(1 for g in comp if g.get("artefato"))
    out.append(
        t(
            0,
            y + 90,
            f"Agora: cinco partes, {num(c['zeros_substituidos_pct'], 1)}% das células em zero, "
            f"V de Cramér {num(c['cramer_v_regiao'], 2)}; "
            f"{extenso(n_art)} dos {extenso(len(comp))} grupos ainda são artefatos da contagem.",
            15,
            INK,
            700,
        )
    )
    return svg(
        "".join(out), "Eleitorado dos cinco grupos de seções da mistura gaussiana"
    )


def _texto(cor: str) -> str:
    """Variante escura para texto pequeno sobre o papel."""
    return {OUTROS: "#0b6650", "#3d8a74": "#2c6b5a"}.get(cor, cor)


def _int(v: float) -> str:
    k = round(v)
    return num(k, 0) if k >= 0 else "−" + num(-k, 0)


# ------------------------------------------------------------------ 16 urna


def fig_urna() -> str:
    it = dado("secoes")["urna"]["reguas"]["itens"]
    x0, x1 = 430, 975
    vmin, vmax = -1.5, 1.5

    def sx(v):
        return x0 + (x1 - x0) * (v - vmin) / (vmax - vmin)

    out = [
        t(
            0,
            24,
            "Urna mais nova contra a mais velha: efeito em Flávio, pontos, IC 95%",
            16,
            MUTED,
            600,
        )
    ]
    out.append(r(sx(-1), 50, sx(1) - sx(-1), 430, PAPER2))
    out.append(t(sx(0), 72, "faixa de um ponto", 15, MUTED, 600, "middle"))
    for v in (-1.5, -1, -0.5, 0, 0.5, 1, 1.5):
        out.append(
            ln(
                sx(v),
                84,
                sx(v),
                470,
                INK if v == 0 else GRID,
                1.5 if v == 0 else 1,
                None if v == 0 else "3 5",
            )
        )
        out.append(
            t(sx(v), 500, sinal(v, 1) if v else "0", 15, MUTED, 600, "middle", MONO)
        )
    y = 130
    for x in it:
        est, (lo, hi) = x["estimativa"], x["ic95"]
        cor = FLAVIO if est > 0 else LULA
        out.append(
            t(
                x0 - 16,
                y + 2,
                x["regua"][:1].upper() + x["regua"][1:],
                17,
                INK,
                700,
                "end",
            )
        )
        out.append(
            t(
                x0 - 16,
                y + 24,
                f"{num(x['unidades'])} {x['unidade']}",
                14,
                MUTED,
                600,
                "end",
                MONO,
            )
        )
        out.append(ln(sx(lo), y, sx(hi), y, cor, 5))
        out.append(circ(sx(est), y, 10, cor, f' stroke="{PAPER}" stroke-width="3"'))
        out.append(t(sx(est), y - 18, sinal(est), 16, cor, 700, "middle", MONO))
        y += 90
    out.append(
        t(
            0,
            560,
            "Quatro réguas, todas abaixo de um ponto, e o sinal muda com o controle: alocação, não máquina.",
            16,
            INK,
            600,
        )
    )
    return svg("".join(out), "Modelo de urna pelas quatro réguas")


__all__ = [
    "fig_anomalias",
    "fig_assembleias",
    "fig_governadores",
    "fig_grupos",
    "fig_pesquisas",
    "fig_secoes90",
    "fig_urna",
    "fig_voto_util",
    "nome_proprio",
    "pct",
]
