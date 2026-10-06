"""Figuras dos cards 1 a 8 da super thread: placar, noite, falha, arquitetura,
regiões, exterior, Câmara e Senado. SVG 1000 × 600, dados dos JSONs."""

from __future__ import annotations

import math

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
    REGIOES5,
    ROT_CAMPO,
    WHITE,
    W,
    area,
    caminho,
    circ,
    dado,
    etiqueta,
    hachura,
    legenda,
    ln,
    mi_curto,
    nome_proprio,
    num,
    pct,
    r,
    sinal,
    svg,
    t,
    tabela,
)
from .thread_valores import capitais_interior


def _min(h: str) -> float:
    """'2026-10-04 18:10' ou '18:10:33' em minutos depois das 17h do dia 4."""
    dia = 1440 if h.startswith("2026-10-05") else 0
    hh = h.split(" ")[-1]
    p = [int(x) for x in hh.split(":")]
    return dia + (p[0] - 17) * 60 + p[1] + (p[2] / 60 if len(p) > 2 else 0)


def _eixo_horas(x0, x1, m0, m1, y, passo=60, size=16):
    out = []
    m = math.ceil(m0 / passo) * passo
    while m <= m1:
        x = x0 + (x1 - x0) * (m - m0) / (m1 - m0)
        total = 17 * 60 + int(m)
        hh, mm = total // 60 % 24, total % 60
        rot = f"{hh:02d}h" if mm == 0 else f"{hh:02d}h{mm:02d}"
        out.append(ln(x, y, x, y + 6, MUTED, 1))
        out.append(t(x, y + 26, rot, size, MUTED, 500, "middle", MONO))
        m += passo
    return "".join(out)


# ------------------------------------------------------------------ 1 placar


def fig_placar() -> str:
    n = dado("presidente")["nacional"]
    linhas = [
        ("Flávio Bolsonaro", "flavio", FLAVIO),
        ("Lula", "lula", LULA),
        ("Augusto Cury", "cury", OUTROS),
        ("Renan Santos", "renan", OUTROS),
        ("Ronaldo Caiado", "caiado", OUTROS),
        (f"Outros {len(n['candidaturas']) - 5}", "outros", CINZA),
    ]
    out = []
    x0, x1 = 230, 900
    escala = (x1 - x0) / 50
    for g in (10, 20, 30, 40, 50):
        x = x0 + g * escala
        out.append(ln(x, 8, x, 330, GRID, 1, "3 5"))
        out.append(t(x, 352, f"{g}%", 15, MUTED, 500, "middle", MONO))
    for i, (nome, k, cor) in enumerate(linhas):
        grande = i < 2
        y = 6 + i * 52 + (0 if grande else 14)
        v = n["pct"][k]
        if grande:
            out.append(t(x0 - 14, y + 24, nome, 22, INK, 700, "end"))
            out.append(
                t(
                    x0 - 14,
                    y + 44,
                    num(n["votos"][k]) + " votos",
                    14,
                    MUTED,
                    500,
                    "end",
                    MONO,
                )
            )
            out.append(r(x0, y + 4, v * escala, 44, cor, 3))
            out.append(
                t(x0 + v * escala - 12, y + 36, pct(v), 26, WHITE, 800, "end", MONO)
            )
        else:
            out.append(t(x0 - 14, y + 25, nome, 18, INK, 500, "end"))
            out.append(r(x0, y + 8, v * escala, 24, cor, 3))
            out.append(
                t(x0 + v * escala + 10, y + 27, pct(v), 18, INK, 700, "start", MONO)
            )
    ufs = [u for u in dado("presidente")["ufs"] if u["uf"] != "ZZ"]
    ufs.sort(key=lambda u: u["pct"]["flavio"] - u["pct"]["lula"], reverse=True)
    passo = W / 27
    out.append(
        t(
            0,
            400,
            "Margem em cada UF, da maior de Flávio à maior de Lula",
            17,
            MUTED,
            600,
        )
    )
    base = 490
    for i, u in enumerate(ufs):
        x = i * passo
        m = u["pct"]["flavio"] - u["pct"]["lula"]
        cor = FLAVIO if m > 0 else LULA
        alt = 8 + min(abs(m), 50) * 1.3
        out.append(r(x + 2, base - alt if m > 0 else base, passo - 4, alt, cor, 2))
        out.append(
            t(
                x + passo / 2,
                base + (20 if m > 0 else -8),
                u["uf"],
                13,
                INK,
                700,
                "middle",
                MONO,
            )
        )
    nf = sum(1 for u in ufs if u["pct"]["flavio"] > u["pct"]["lula"])
    out.append(t(0, 590, f"Flávio venceu em {nf} UFs", 19, FLAVIO, 700))
    out.append(t(W, 590, f"Lula, em {27 - nf}", 19, LULA, 700, "end"))
    return svg("".join(out), "Placar do 1º turno e vencedor por UF")


# ------------------------------------------------------------------ 2 noite


def fig_noite() -> str:
    nr = dado("noite_regioes")
    linhas = tabela(nr["nacional_por_minuto"])
    m0, m1 = _min("2026-10-04 17:20"), _min("2026-10-04 23:00")
    x0, x1, y0, y1 = 70, 960, 40, 470
    vmax = 12

    def sx(m):
        return x0 + (x1 - x0) * (m - m0) / (m1 - m0)

    def sy(v):
        return y1 - (y1 - y0) * v / vmax

    out = [hachura("hp-noite", "#c9c1ad", PAPER)]
    for v in (0, 2, 4, 6, 8, 10, 12):
        out.append(ln(x0, sy(v), x1, sy(v), GRID, 1, None if v == 0 else "3 5"))
        out.append(t(x0 - 10, sy(v) + 6, f"{v}", 16, MUTED, 500, "end", MONO))
    out.append(
        t(
            x0 - 10,
            y0 - 16,
            "Flávio menos Lula, pontos dos válidos apurados",
            16,
            MUTED,
            600,
            "start",
        )
    )
    for p in dado("linha_do_tempo")["travamentos"]["nacional"]:
        if p["pst_ate"] >= 99.5:
            continue
        a, b = sx(_min(p["de_brt"])), sx(_min(p["ate_brt"]))
        out.append(r(a, y0, b - a, y1 - y0, PAPER2))
    pg = dado("linha_do_tempo")["pausa_geral"]["lacunas"][0]
    a, b = sx(_min(pg["de_brt"])), sx(_min(pg["ate_brt"]))
    out.append(r(a, y0, b - a, y1 - y0, "url(#hp-noite)"))
    pts, pts_peso = [], []
    inicio_peso = _min("2026-10-04 17:45")
    for x in linhas:
        m = _min(x["hora_brt"])
        if m < m0 or m > m1 or x["dif_pp"] is None:
            continue
        pts.append((sx(m), sy(x["dif_pp"])))
        if x["dif_pp_peso_final"] is not None and m >= inicio_peso:
            pts_peso.append((sx(m), sy(x["dif_pp_peso_final"])))
    out.append(area(pts, sy(0), FLAVIO, 0.12))
    out.append(caminho(pts_peso, GOLD, 3, ' stroke-dasharray="8 6"'))
    out.append(caminho(pts, FLAVIO, 4.5))
    dec = nr["decomposicao"]
    px, py = sx(_min(dec["pico_brt"])), sy(dec["pico_pp"])
    out.append(circ(px, py, 9, FLAVIO, f' stroke="{PAPER}" stroke-width="3"'))
    out.append(
        etiqueta(
            px + 16,
            py + 6,
            f"{num(dec['pico_pp'], 1)} pontos às {dec['pico_brt'][-5:]}",
            20,
            FLAVIO,
        )
    )
    fx, fy = pts[-1]
    out.append(circ(fx, fy, 8, FLAVIO, f' stroke="{PAPER}" stroke-width="3"'))
    out.append(
        etiqueta(
            fx - 4,
            fy - 18,
            f"{num(dec['final_pp'], 1)} no fim",
            20,
            FLAVIO,
            anchor="end",
        )
    )
    out.append(
        etiqueta(
            sx(_min("2026-10-04 20:40")),
            sy(1.0),
            f"{num(dec['entre_regioes_pct_da_queda'], 1)}% da queda é ordem de chegada",
            18,
            GOLD,
            anchor="middle",
        )
    )
    out.append(_eixo_horas(x0, x1, m0, m1, y1, 60))
    out.append(
        legenda(
            [
                ("Vantagem apurada", FLAVIO),
                ("Com cada região no peso final", GOLD),
                ("Paradas do arquivo nacional", "#d9d1bd"),
            ],
            x0,
            562,
            16,
        )
    )
    return svg("".join(out), "A vantagem de Flávio ao longo da noite")


# ------------------------------------------------------------------ 3 falha


def fig_falha() -> str:
    arq = dado("arquitetura")
    rec = tabela(arq["recebimento_2026"])
    m0, m1 = 30, 240
    x0, x1, y0, y1 = 70, 930, 50, 470

    def sx(m):
        return x0 + (x1 - x0) * (m - m0) / (m1 - m0)

    vmax = 7000

    def sy(v):
        return y1 - (y1 - y0) * v / vmax

    out = [hachura("hp-falha", "#c9c1ad", PAPER)]
    for v in (0, 2000, 4000, 6000):
        out.append(ln(x0, sy(v), x1, sy(v), GRID, 1, None if v == 0 else "3 5"))
        out.append(t(x0 - 10, sy(v) + 6, num(v), 15, MUTED, 500, "end", MONO))
    out.append(
        t(
            x0 - 10,
            y0 - 22,
            "Boletins carimbados como recebidos pelo TSE, por minuto",
            16,
            MUTED,
            600,
        )
    )
    tr = [
        p
        for p in dado("linha_do_tempo")["travamentos"]["nacional"]
        if p["pst_ate"] < 99.5
    ]
    for i, p in enumerate(tr, 1):
        a, b = sx(_min(p["de_brt"])), sx(_min(p["ate_brt"]))
        out.append(r(a, y0, b - a, y1 - y0, PAPER2))
        out.append(t((a + b) / 2, y0 + 20, f"parada {i}", 15, INK, 700, "middle"))
    pg = dado("linha_do_tempo")["pausa_geral"]["lacunas"][0]
    a, b = sx(_min(pg["de_brt"])), sx(_min(pg["ate_brt"]))
    out.append(r(a, y0 + 30, b - a, y1 - y0 - 30, "url(#hp-falha)"))
    largura = (x1 - x0) / (m1 - m0)
    des = arq["recebimento_2026"]["desaceleracao"]
    d0, d1 = _min(des["janela"][0]), _min(des["janela"][1])
    for x in rec:
        m = _min(x["minuto"])
        if m < m0 or m > m1:
            continue
        cor = GOLD if d0 <= m <= d1 else OUTROS
        v = x["secoes_extrapoladas"]
        out.append(r(sx(m), sy(v), largura * 0.82, y1 - sy(v), cor))
    vers = [
        x for x in tabela(dado("linha_do_tempo")["nacional"]["versoes"]) if x["st"] > 0
    ]
    pts, ultimo = [], None
    for x in vers:
        m = _min(x["gerado_brt"])
        if m > m1:
            break
        yy = y1 - (y1 - y0) * x["pst"] / 100
        if ultimo is not None:
            pts.append((sx(m), ultimo))
        pts.append((sx(m), yy))
        ultimo = yy
    if pts:
        pts.append((sx(m1), pts[-1][1]))
    out.append(caminho(pts, INK, 3))
    for v in (25, 50, 75, 100):
        yy = y1 - (y1 - y0) * v / 100
        out.append(t(x1 + 10, yy + 6, f"{v}%", 15, INK, 600, "start", MONO))
    out.append(
        etiqueta(
            sx((d0 + d1) / 2),
            sy(2600),
            f"{num(100 * des['razao'], 0)}% do ritmo",
            18,
            GOLD,
            anchor="middle",
        )
    )
    out.append(
        etiqueta(
            (a + b) / 2,
            sy(1200),
            f"{num(pg['minutos'], 0)} min",
            20,
            INK,
            anchor="middle",
            weight=800,
        )
    )
    out.append(
        etiqueta((a + b) / 2, sy(1200) + 26, "sem arquivo", 16, INK, anchor="middle")
    )
    out.append(_eixo_horas(x0, x1, m0, m1, y1, 30, 15))
    out.append(
        legenda(
            [
                ("Recebidos por minuto", OUTROS),
                ("Desaceleração", GOLD),
                ("Seções no arquivo nacional (eixo da direita)", INK),
            ],
            x0,
            562,
            16,
        )
    )
    return svg("".join(out), "Recebimento de boletins e paradas do arquivo nacional")


# ------------------------------------------------------------------ 4 arquitetura


def _caixa(x, y, w, h, titulo, sub, cor, tracejada=False):
    borda = f' stroke="{cor}" stroke-width="2.5"' + (
        ' stroke-dasharray="7 5"' if tracejada else ""
    )
    out = [r(x, y, w, h, WHITE, 8, borda)]
    out.append(t(x + w / 2, y + 34, titulo, 19, cor, 700, "middle"))
    for i, s in enumerate(sub):
        out.append(t(x + w / 2, y + 60 + i * 22, s, 15, INK, 500, "middle"))
    return "".join(out)


def _seta(x1, y, x2, cor=MUTED):
    return ln(x1, y, x2 - 10, y, cor, 2.5) + (
        f'<path d="M{x2 - 12:.1f},{y - 7:.1f} L{x2:.1f},{y:.1f} L{x2 - 12:.1f},{y + 7:.1f} Z" fill="{cor}"/>'
    )


def fig_arquitetura() -> str:
    a = dado("arquitetura")
    vol = a["volume"]
    out = [t(0, 22, "Como os documentos de 2020 descrevem a totalização", 18, INK, 700)]
    w, h, y = 178, 118, 42
    xs = [0, 205, 410, 615, 820]
    cx = [
        ("Urna", ["boletim assinado", "por seção"], INK, False),
        ("Transmissão", ["Transportador", "e RecArquivos"], INK, False),
        ("Banco central", ["Oracle em", "Exadata (2020)"], LULA, True),
        ("Totalização", ["recalcula", "totais"], LULA, True),
        ("Divulgação", ["arquivos por", "cargo e nível"], LULA, True),
    ]
    for x, (tt, sub, cor, tr) in zip(xs, cx, strict=True):
        out.append(_caixa(x, y, w, h, tt, sub, cor, tr))
    for i in range(4):
        out.append(_seta(xs[i] + w, y + h / 2, xs[i + 1]))
    out.append(
        t(
            410,
            186,
            "tracejado: onde a hipótese do autor põe o engasgo, sem documento de 2026",
            15,
            LULA,
            600,
        )
    )
    y2 = 232
    out.append(
        t(
            0,
            y2 - 14,
            "O desenho proporcional ao volume (juízo editorial)",
            18,
            INK,
            700,
        )
    )
    cx2 = [
        ("Boletim", ["chega uma vez", "por seção"], OUTROS),
        ("Log de eventos", ["só acréscimo,", "partição por UF"], OUTROS),
        ("Consumidores", ["idempotentes", "por seção"], OUTROS),
        ("Totais", ["incrementais", "sem recálculo"], OUTROS),
        ("Publicação", ["fotografia", "assinada, assíncrona"], OUTROS),
    ]
    for x, (tt, sub, cor) in zip(xs, cx2, strict=True):
        out.append(_caixa(x, y2, w, h, tt, sub, cor))
    for i in range(4):
        out.append(_seta(xs[i] + w, y2 + h / 2, xs[i + 1], OUTROS))
    nums = [
        (num(vol["pico_secoes_por_segundo"], 0), "seções por segundo no pico"),
        (num(vol["pico_linhas_por_minuto"]), "linhas de voto por minuto no pico"),
        (f"{num(vol['bu_total_mb'] / 1024, 1)} GB", "todos os boletins do país"),
        (num(vol["secoes_represadas"]), "seções presas na parada longa"),
    ]
    y3 = 420
    for i, (v, rot) in enumerate(nums):
        x = i * 252
        out.append(r(x, y3, 236, 150, PAPER2, 8))
        out.append(t(x + 118, y3 + 62, v, 36, FLAVIO, 800, "middle", MONO))
        palavras = rot.split(" ")
        meio = len(palavras) // 2
        out.append(
            t(x + 118, y3 + 98, " ".join(palavras[:meio]), 16, INK, 500, "middle")
        )
        out.append(
            t(x + 118, y3 + 120, " ".join(palavras[meio:]), 16, INK, 500, "middle")
        )
    return svg("".join(out), "Arquitetura documentada e desenho proposto")


# ------------------------------------------------------------------ 5 regiões


def fig_regioes() -> str:
    ci = capitais_interior()
    out = []
    xz, esc = 600, 42
    for v in (-8, -6, -4, -2, 0, 2, 4, 6):
        x = xz + v * esc
        out.append(
            ln(
                x,
                34,
                x,
                528,
                INK if not v else GRID,
                1.5 if not v else 1,
                None if not v else "3 5",
            )
        )
        out.append(t(x, 552, sinal(v, 0) if v else "0", 15, MUTED, 500, "middle", MONO))
    out.append(t(xz - 14, 22, "Lula contra Lula de 2022", 17, LULA, 700, "end"))
    out.append(t(xz + 14, 22, "Flávio contra Bolsonaro de 2022", 17, FLAVIO, 700))
    y = 44
    for reg in REGIOES5:
        out.append(t(0, y + 46, reg, 21, INK, 700))
        for g in ("capitais", "interior"):
            d = ci[reg][g]
            out.append(t(150, y + 26, g, 15, MUTED, 600))
            for k, (v, cor) in enumerate(
                ((d["swing_flavio"], FLAVIO), (d["swing_lula"], LULA))
            ):
                yy = y + 6 + k * 21
                x_ini = xz if v >= 0 else xz + v * esc
                out.append(r(x_ini, yy, abs(v) * esc, 17, cor, 2))
                if v >= 0:
                    out.append(
                        t(
                            xz + v * esc + 7,
                            yy + 15,
                            sinal(v),
                            14,
                            cor,
                            700,
                            "start",
                            MONO,
                        )
                    )
                else:
                    out.append(
                        t(
                            xz + v * esc - 7,
                            yy + 15,
                            sinal(v),
                            14,
                            cor,
                            700,
                            "end",
                            MONO,
                        )
                    )
            y += 46
        y += 6
    out.append(
        t(
            0,
            590,
            "Pontos dos válidos, 1º turno de 2026 contra o 1º turno de 2022",
            16,
            MUTED,
            500,
        )
    )
    return svg("".join(out), "Variação por região, capitais e interior")


# ------------------------------------------------------------------ 6 exterior


def fig_exterior() -> str:
    e = dado("exterior")
    conts = sorted(e["continentes"], key=lambda c: -c["validos"])
    out = []
    x0 = 300
    esc = 6.2
    out.append(t(0, 22, "Votos válidos por continente", 17, MUTED, 600))
    y = 50
    for c in conts:
        out.append(t(x0 - 14, y + 22, c["continente"], 19, INK, 600, "end"))
        out.append(
            t(
                x0 - 14,
                y + 44,
                f"{num(c['validos'])} válidos",
                14,
                MUTED,
                500,
                "end",
                MONO,
            )
        )
        f, lu = c["pct"]["flavio"], c["pct"]["lula"]
        out.append(r(x0, y + 4, f * esc, 20, FLAVIO, 2))
        out.append(r(x0, y + 28, lu * esc, 20, LULA, 2))
        out.append(
            t(x0 + f * esc + 8, y + 20, pct(f, 1), 15, FLAVIO, 700, "start", MONO)
        )
        out.append(
            t(x0 + lu * esc + 8, y + 44, pct(lu, 1), 15, LULA, 700, "start", MONO)
        )
        y += 64
    zz = next(u for u in dado("presidente")["ufs"] if u["uf"] == "ZZ")
    c22 = zz["r2022"]["t1"]["pct_comparecimento"]
    c26 = e["total"]["pct_comparecimento"]
    bx = 760
    out.append(r(bx, 40, 240, 250, PAPER2, 8))
    out.append(t(bx + 120, 74, "Comparecimento", 18, INK, 700, "middle"))
    for i, (ano, v) in enumerate((("2022", c22), ("2026", c26))):
        hh = v * 2.6
        xx = bx + 50 + i * 90
        out.append(r(xx, 270 - hh, 50, hh, CINZA if i == 0 else GOLD_FILL, 3))
        out.append(t(xx + 25, 262 - hh, pct(v, 1), 16, INK, 700, "middle", MONO))
        out.append(t(xx + 25, 288, ano, 15, MUTED, 600, "middle", MONO))
    pt = next(p for p in e["paises"] if p["pais"] == "PT")
    out.append(r(bx, 310, 240, 150, PAPER2, 8))
    out.append(t(bx + 120, 344, "Portugal", 18, INK, 700, "middle"))
    out.append(
        t(
            bx + 120,
            394,
            sinal(pt["swing_flavio_vs_bolsonaro_1t_pp"]),
            40,
            FLAVIO,
            800,
            "middle",
            MONO,
        )
    )
    out.append(t(bx + 120, 426, "pontos de Flávio sobre", 15, INK, 500, "middle"))
    out.append(t(bx + 120, 446, "Bolsonaro, mesmas cidades", 15, INK, 500, "middle"))
    out.append(legenda([("Flávio", FLAVIO), ("Lula", LULA)], 0, 590, 17))
    return svg("".join(out), "Exterior por continente")


# ------------------------------------------------------------------ hemiciclo


def hemiciclo(contagem: list[tuple[str, int]], cx, cy, r0, r1, linhas, raio_ponto):
    total = sum(n for _, n in contagem)
    raios = [r0 + (r1 - r0) * i / max(linhas - 1, 1) for i in range(linhas)]
    soma = sum(raios)
    por_linha = [round(total * rr / soma) for rr in raios]
    por_linha[-1] += total - sum(por_linha)
    lugares = []
    for rr, n in zip(raios, por_linha, strict=True):
        for k in range(n):
            ang = math.pi * (1 - (k + 0.5) / n)
            lugares.append((ang, rr))
    lugares.sort(key=lambda a: (-a[0], a[1]))
    cores = [c for c, n in contagem for _ in range(n)]
    out = []
    for (ang, rr), cor in zip(lugares, cores, strict=True):
        out.append(
            circ(cx + rr * math.cos(ang), cy - rr * math.sin(ang), raio_ponto, cor)
        )
    return "".join(out)


def fig_camara() -> str:
    c = dado("camara")
    cp = dado("comparacao_2022")["camara"]
    cont = [(CAMPO[k], c["por_campo"][k]) for k in CAMPOS]
    out = [hemiciclo(cont, 330, 330, 120, 310, 12, 7.2)]
    bd = c["blocos"]["direita + centro-direita"]
    out.append(t(330, 300, num(bd), 64, FLAVIO, 800, "middle", MONO))
    out.append(t(330, 330, "direita e centro-direita", 17, INK, 600, "middle"))
    out.append(
        t(
            330,
            380,
            f"maioria absoluta {c['vagas_total'] // 2 + 1} · três quintos {math.ceil(c['vagas_total'] * 3 / 5)}",
            16,
            MUTED,
            600,
            "middle",
        )
    )
    x0 = 700
    out.append(t(x0, 40, "Cadeiras 2026 e variação sobre 2022", 17, MUTED, 600))
    for i, k in enumerate(reversed(CAMPOS)):
        y = 80 + i * 72
        out.append(r(x0, y, 26, 26, CAMPO[k], 4))
        out.append(t(x0 + 40, y + 21, ROT_CAMPO[k], 20, INK, 600))
        out.append(
            t(
                x0 + 40,
                y + 50,
                num(c["por_campo"][k]),
                26,
                CAMPO[k] if k != "centro" else INK,
                800,
                "start",
                MONO,
            )
        )
        dlt = cp["delta_campo"][k]
        out.append(
            t(
                x0 + 120,
                y + 50,
                sinal(dlt, 0),
                20,
                FLAVIO if dlt > 0 else LULA,
                700,
                "start",
                MONO,
            )
        )
    out.append(
        t(
            0,
            440,
            f"PL {num(c['por_partido']['PL'])} · PT {num(c['por_partido']['PT'])} · União {num(c['por_partido']['UNIÃO'])} · PSD {num(c['por_partido']['PSD'])}",
            19,
            INK,
            600,
        )
    )
    out.append(
        t(
            0,
            480,
            f"Votos para a Câmara: direita {pct(c['votos_por_campo_pct']['direita'], 1)}, esquerda {pct(c['votos_por_campo_pct']['esquerda'], 1)}",
            17,
            MUTED,
            500,
        )
    )
    out.append(
        t(
            0,
            590,
            f"Alocação provisória em {', '.join(c['ufs_provisorias'])}, reproduzida nome a nome nas UFs que o TSE fechou",
            15,
            MUTED,
            500,
        )
    )
    return svg("".join(out), "Câmara dos Deputados eleita, por campo")


def fig_senado() -> str:
    s = dado("senado")["senado_2027"]
    sx = dado("senado_x_flavio")
    cont = [(CAMPO[k], s["por_campo"][k]) for k in CAMPOS]
    out = [hemiciclo(cont, 226, 250, 118, 205, 4, 10.5)]
    out.append(
        t(
            226,
            238,
            num(s["por_bloco"]["direita + centro-direita"]),
            60,
            FLAVIO,
            800,
            "middle",
            MONO,
        )
    )
    out.append(
        t(
            226,
            290,
            f"de {s['total']} cadeiras no Senado de 2027",
            17,
            INK,
            600,
            "middle",
        )
    )
    out.append(t(226, 316, "são de direita ou centro-direita", 17, INK, 600, "middle"))
    out.append(
        t(
            226,
            360,
            f"três quintos: {math.ceil(s['total'] * 3 / 5)}",
            17,
            MUTED,
            600,
            "middle",
        )
    )
    out.append(
        t(
            226,
            400,
            f"PL {s['por_partido']['PL']} · PT {s['por_partido']['PT']} · MDB {s['por_partido']['MDB']}",
            18,
            INK,
            600,
            "middle",
        )
    )
    acima = sorted(
        (u for u in sx["ufs"] if u["melhor"]["vao_votantes_pp"] > 0),
        key=lambda u: -u["melhor"]["vao_votantes_pp"],
    )
    x0, esc = 640, 14
    out.append(
        t(
            450,
            30,
            "Candidatura do bloco que alcançou mais eleitores que Flávio",
            16,
            MUTED,
            600,
        )
    )
    out.append(t(450, 52, "pontos dos votantes de cada cargo", 15, MUTED, 500))
    for i, u in enumerate(acima[:10]):
        y = 76 + i * 50
        m = u["melhor"]
        out.append(t(x0 - 12, y + 16, nome_proprio(m["nome"]), 16, INK, 600, "end"))
        out.append(
            t(
                x0 - 12,
                y + 36,
                f"{u['uf']} · {m['partido']}",
                13,
                MUTED,
                500,
                "end",
                MONO,
            )
        )
        v = m["vao_votantes_pp"]
        cor = CAMPO.get(m["campo"], FLAVIO)
        out.append(r(x0, y + 8, v * esc, 26, cor, 3))
        out.append(
            t(x0 + v * esc + 8, y + 28, sinal(v, 1), 16, INK, 700, "start", MONO)
        )
    out.append(
        legenda(
            [
                (ROT_CAMPO[k], CAMPO[k])
                for k in ("esquerda", "centro", "centro-direita", "direita")
            ],
            0,
            590,
            15,
        )
    )
    return svg("".join(out), "Senado de 2027 e os nomes que passaram Flávio")


__all__ = [
    "fig_arquitetura",
    "fig_camara",
    "fig_exterior",
    "fig_falha",
    "fig_noite",
    "fig_placar",
    "fig_regioes",
    "fig_senado",
    "hemiciclo",
    "mi_curto",
]
