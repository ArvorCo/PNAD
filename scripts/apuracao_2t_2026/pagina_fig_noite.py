"""Figuras do capítulo 02 (a noite minuto a minuto) do dossiê do 2º turno.

Relógio: minutos após 17:00 de Brasília de 25/10/2026 pela hora de geração do
arquivo (`linha_do_tempo.relogio`). A votação terminou às 19:00 (minuto 120)
depois da prorrogação. A parada sai de `linha_do_tempo.pausas`, nunca de horário
digitado; as marcas externas (STF, aviso do TSE, TRE-SP) vêm do noticiário e
levam o veículo na ficha.
"""

from __future__ import annotations

from apuracao_2026.pagina_comum import NOME_UF, inteiro, num
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
    r,
    svg_abre,
    t,
    tabela_linhas,
    ticks,
)
from apuracao_2026.pagina_fig_mapas import mapa_ufs

GOLD = "#7d5b00"
VERDE = "#0b6650"
HACHURA = (
    '<defs><pattern id="hach2t" width="7" height="7" patternUnits="userSpaceOnUse" '
    'patternTransform="rotate(45)"><rect width="7" height="7" fill="#efe6cf"/>'
    '<rect width="2.4" height="7" fill="#c9b27a"/></pattern></defs>'
)
FIM_VOTACAO = 120


def teto(v: float) -> float:
    """Menor marca redonda de `ticks` que cobre `v` (o eixo nunca corta a série)."""
    tk = ticks(0, v, 5)
    passo = tk[1] - tk[0] if len(tk) > 1 else max(v, 1)
    return tk[-1] if tk[-1] >= v else tk[-1] + passo


def hhmm(m: float) -> str:
    """Minuto após 17:00 vira 'HH:MM' de Brasília."""
    tot = round(17 * 60 + m)
    return f"{(tot // 60) % 24:02d}:{tot % 60:02d}"


def minuto_de(s: str | None) -> float | None:
    """'2026-10-25 19:01:56' vira minutos após 17:00 de 25/10."""
    if not s:
        return None
    data, _, h = s.strip().partition(" ")
    hh, mm, *ss = (int(x) for x in h.split(":"))
    dia = int(data[-2:]) - 25
    return dia * 1440 + (hh - 17) * 60 + mm + (ss[0] / 60 if ss else 0)


def serie(L: dict) -> list[dict]:
    """Versões nacionais da noite (do minuto 0 em diante) com seções totalizadas."""
    return [
        v
        for v in tabela_linhas(L["nacional"]["serie"])
        if v["min"] >= 0 and (v["st"] or 0) > 0
    ]


def parada(L: dict) -> dict:
    return L["pausas"]["maior_lacuna_nacional"]


def marcas_externas(N: dict | None) -> list[dict]:
    """Marcas do noticiário (minuto, rótulo, veículo, URL) escolhidas pela URL."""
    if not N:
        return []
    regras = [
        ("stf-prorroga-votacao", "STF: Zanin prorroga até 19h"),
        ("tse-avisou-secoes", "TSE avisa as seções"),
        ("so-recebeu-decisao", "TRE-SP recebe a decisão"),
    ]
    out = []
    for chave, rotulo in regras:
        for it in N.get("itens", []):
            hora_ok = (
                chave == "so-recebeu-decisao" or it.get("quando", "")[11:13] >= "17"
            )
            if chave in it.get("url", "") and hora_ok:
                q = it.get("quando", "")
                m = None
                if "T" in q:
                    hm = q.split("T")[1][:5]
                    m = (int(hm[:2]) - 17) * 60 + int(hm[3:5])
                if chave == "so-recebeu-decisao":
                    m = 77  # 18:17 é a hora citada pelo presidente do TRE-SP na matéria
                if m is not None:
                    out.append(
                        {
                            "min": m,
                            "rotulo": rotulo,
                            "veiculo": it.get("veiculo", ""),
                            "url": it.get("url", ""),
                        }
                    )
                break
    return out


def _eixo_tempo(x, y0: float, y1: float, m0: int, m1: int, passo: int = 30) -> str:
    out = []
    m = m0
    while m <= m1:
        xx = x(m)
        out.append(ln(xx, y0, xx, y1, GRADE, 1))
        out.append(t(xx, y1 + 20, hhmm(m), 12.5, MUTED, "middle", mono=True))
        m += passo
    return "".join(out)


def _faixa_parada(x, P: dict, y0: float, y1: float) -> str:
    a, b = P["de_min"], P["ate_min"]
    return r(x(a), y0, x(b) - x(a), y1 - y0, "url(#hach2t)", ' opacity="0.85"') + t(
        (x(a) + x(b)) / 2,
        y0 + 18,
        f"parada {num(P['minutos'], 1)} min",
        13,
        INK,
        "middle",
        "700",
        extra=HALO,
    )


def _marcas(x, marcas: list[dict], y0: float, y1: float) -> str:
    out = []
    for i, mk in enumerate(marcas):
        xx = x(mk["min"])
        out.append(ln(xx, y0, xx, y1, GOLD, 1.4, ' stroke-dasharray="3 3"'))
        out.append(
            t(
                xx + 4,
                y0 + 40 + 17 * i,
                mk["rotulo"],
                12,
                GOLD,
                weight="700",
                extra=HALO,
            )
        )
    return "".join(out)


# ------------------------------------------------------------------ acumulado


def fig_acumulado(L: dict, N: dict | None) -> str:
    vs = serie(L)
    P = parada(L)
    H, ml, mr, mt, mb = 460, 78, 40, 26, 50
    m0, m1 = 0, max(330, round(vs[-1]["min"] / 30 + 0.5) * 30)
    x = escala(m0, m1, ml, W - mr)
    vmax = max(max(v["flavio"], v["lula"]) for v in vs) / 1e6
    ymax = teto(vmax * 1.04)
    y = escala(0, ymax, H - mb, mt)
    out = [
        svg_abre(
            W,
            H,
            "Votos acumulados por candidato na noite do 2º turno",
            "Linhas de Lula e Flávio pelo arquivo nacional, com a parada de 17:07 a 19:01 hachurada.",
        ),
        HACHURA,
    ]
    for tk in ticks(0, ymax, 5):
        out.append(ln(ml, y(tk), W - mr, y(tk), GRADE, 1))
        out.append(
            t(ml - 8, y(tk) + 4, f"{num(tk, 0)} mi", 12.5, MUTED, "end", mono=True)
        )
    out.append(_eixo_tempo(x, mt, H - mb, m0, m1))
    out.append(_faixa_parada(x, P, mt, H - mb))
    xf = x(FIM_VOTACAO)
    out.append(ln(xf, mt, xf, H - mb, INK, 1.6))
    out.append(
        t(
            xf + 4,
            H - mb - 8,
            "19:00, fim da votação",
            12,
            INK,
            weight="700",
            extra=HALO,
        )
    )
    out.append(_marcas(x, marcas_externas(N), mt, H - mb))
    tips, linhas = Tips(), []
    for cand, cor in (("lula", LULA), ("flavio", FLAVIO)):
        pts = " ".join(f"{x(v['min']):.1f},{y(v[cand] / 1e6):.1f}" for v in vs)
        out.append(
            f'<polyline points="{pts}" fill="none" stroke="{cor}" stroke-width="2.6"/>'
        )
    ult = vs[-1]
    out.append(
        t(
            x(ult["min"]) - 6,
            y(ult["lula"] / 1e6) - 10,
            f"Lula {num(ult['lula'] / 1e6, 2)} mi",
            14,
            LULA,
            "end",
            "700",
            extra=HALO,
        )
    )
    out.append(
        t(
            x(ult["min"]) - 6,
            y(ult["flavio"] / 1e6) + 22,
            f"Flávio {num(ult['flavio'] / 1e6, 2)} mi",
            14,
            FLAVIO,
            "end",
            "700",
            extra=HALO,
        )
    )
    for i, v in enumerate(vs):
        prox = vs[i + 1]["min"] if i + 1 < len(vs) else v["min"] + 1
        ant = vs[i - 1]["min"] if i else v["min"] - 1
        xa, xb = x((ant + v["min"]) / 2), x((v["min"] + prox) / 2)
        linhas.append(
            [
                f"Versão de {v['gerado_brt'][11:19]}",
                f"{num(v['pst'], 2)}% das seções",
                f"{inteiro(v['lula'])} ({pct(v['pct_lula'])})",
                f"{inteiro(v['flavio'])} ({pct(v['pct_flavio'])})",
                f"{inteiro(v['lote_st'])} seções",
            ]
        )
        out.append(hit(area(xa, mt, xb - xa, H - mb - mt), f"r{i}"))
    tips.tabela(["Versão", "Seções", "Lula", "Flávio", "Lote"], linhas, sub=1)
    out.append("</svg>")
    leg = legenda_html(
        [
            ("Lula", LULA),
            ("Flávio Bolsonaro", FLAVIO),
            (
                "Parada do arquivo nacional",
                "repeating-linear-gradient(45deg,#c9b27a 0 2px,#efe6cf 2px 6px)",
            ),
            ("Marca do noticiário", GOLD),
        ]
    )
    legenda = (
        f"Votos de cada candidato pelo arquivo nacional, {inteiro(len(vs))} versões geradas pelo TSE desde 17:00. "
        f"Entre {P['de_brt'][11:19]} e {P['ate_brt'][11:19]} o arquivo nacional não teve versão nova. "
        "As marcas tracejadas vêm do noticiário (veículo e link no texto), não do banco. Fonte: linha_do_tempo.json."
    )
    return figura_html("acumulado_2t", "".join(out), legenda, tips, apos=leg, minw=760)


# ------------------------------------------------------------------ fatia


def trechos_flavio_frente(vs: list[dict]) -> list[tuple[dict, dict]]:
    out, ini, ant = [], None, None
    for v in vs:
        frente = (v["pct_flavio"] or 0) > 50
        if frente and ini is None:
            ini = v
        if not frente and ini is not None:
            out.append((ini, ant))
            ini = None
        ant = v
    if ini is not None:
        out.append((ini, ant))
    return out


def fig_fatia(L: dict) -> str:
    vs = [v for v in serie(L) if v["pct_flavio"] is not None]
    H, ml, mr, mt, mb = 400, 70, 40, 26, 50
    m0 = 0
    m1 = max(330, round(vs[-1]["min"] / 30 + 0.5) * 30)
    x = escala(m0, m1, ml, W - mr)
    lo = min(40.0, min(v["pct_flavio"] for v in vs) - 1)
    hi = max(52.0, max(v["pct_flavio"] for v in vs) + 1)
    y = escala(lo, hi, H - mb, mt)
    out = [
        svg_abre(
            W,
            H,
            "Fatia de Flávio entre os dois na noite",
            "Parte de Flávio nos votos válidos, versão a versão, com a linha de 50%.",
        ),
        HACHURA,
    ]
    for tk in ticks(lo, hi, 6):
        out.append(ln(ml, y(tk), W - mr, y(tk), GRADE, 1))
        out.append(
            t(ml - 8, y(tk) + 4, f"{num(tk, 0)}%", 12.5, MUTED, "end", mono=True)
        )
    out.append(_eixo_tempo(x, mt, H - mb, m0, m1))
    out.append(_faixa_parada(x, parada(L), mt, H - mb))
    out.append(ln(ml, y(50), W - mr, y(50), INK, 1.4))
    out.append(t(W - mr - 4, y(50) - 6, "50%", 12.5, INK, "end", "700", extra=HALO))
    for a, b in trechos_flavio_frente(vs):
        xa, xb = x(a["min"]), x(b["min"])
        out.append(r(xa, mt, max(xb - xa, 2), H - mb - mt, "#dbe5f3", ' opacity="0.9"'))
    pts = " ".join(f"{x(v['min']):.1f},{y(v['pct_flavio']):.1f}" for v in vs)
    out.append(
        f'<polyline points="{pts}" fill="none" stroke="{FLAVIO}" stroke-width="2.4"/>'
    )
    tips, linhas = Tips(), []
    for i, v in enumerate(vs):
        prox = vs[i + 1]["min"] if i + 1 < len(vs) else v["min"] + 1
        ant = vs[i - 1]["min"] if i else v["min"] - 1
        xa, xb = x((ant + v["min"]) / 2), x((v["min"] + prox) / 2)
        linhas.append(
            [
                v["gerado_brt"][11:19],
                f"{num(v['pst'], 2)}% das seções",
                pct(v["pct_flavio"]),
                pct(v["pct_lula"]),
            ]
        )
        out.append(hit(area(xa, mt, xb - xa, H - mb - mt), f"r{i}"))
    tips.tabela(["Versão", "Seções", "Flávio", "Lula"], linhas, sub=1)
    out.append("</svg>")
    frente = trechos_flavio_frente(vs)
    txt = ""
    if frente:
        mx = max(v["pct_flavio"] for v in vs if v["min"] >= FIM_VOTACAO)
        txt = (
            f" Faixa azul: versões em que Flávio tinha mais da metade dos válidos "
            f"(de {frente[0][0]['gerado_brt'][11:16]} a {frente[-1][1]['gerado_brt'][11:16]}; máximo de {pct(mx)} depois das 19:00)."
        )
    legenda = (
        "Parte de Flávio Bolsonaro nos votos válidos em cada versão do arquivo nacional."
        + txt
        + " A fatia mostra quem já tinha sido contado, não a direção do resultado. Fonte: linha_do_tempo.json."
    )
    return figura_html("fatia_2t", "".join(out), legenda, tips, minw=760)


# ------------------------------------------------------------------ lotes


def fig_lotes(L: dict) -> str:
    vs = [v for v in serie(L) if (v["lote_st"] or 0) > 0]
    H, ml, mr, mt, mb = 360, 78, 40, 26, 50
    m0 = 0
    m1 = max(330, round(vs[-1]["min"] / 30 + 0.5) * 30)
    x = escala(m0, m1, ml, W - mr)
    vmax = max(v["lote_st"] for v in vs)
    ymax = teto(vmax)
    y = escala(0, ymax, H - mb, mt)
    out = [
        svg_abre(
            W,
            H,
            "Seções por versão do arquivo nacional",
            "Barras com as seções que cada versão acrescentou, coloridas por quem levou mais no lote.",
        ),
        HACHURA,
    ]
    for tk in ticks(0, ymax, 5):
        out.append(ln(ml, y(tk), W - mr, y(tk), GRADE, 1))
        out.append(t(ml - 8, y(tk) + 4, inteiro(tk), 12.5, MUTED, "end", mono=True))
    out.append(_eixo_tempo(x, mt, H - mb, m0, m1))
    out.append(_faixa_parada(x, parada(L), mt, H - mb))
    tips, linhas = Tips(), []
    larg = max(2.0, (x(1.2) - x(0)))
    for i, v in enumerate(vs):
        cor = FLAVIO if (v["lote_pct_flavio"] or 0) > 50 else LULA
        xx = x(v["min"]) - larg / 2
        hh = y(0) - y(v["lote_st"])
        linhas.append(
            [
                v["gerado_brt"][11:19],
                f"{num(v['minutos_desde_anterior'] or 0, 1)} min depois da anterior",
                inteiro(v["lote_st"]),
                pct(v["lote_pct_flavio"]),
                f"{num(v['pst'], 2)}%",
            ]
        )
        out.append(
            hit(
                r(xx, y(v["lote_st"]), larg, max(hh, 1), cor)
                + area(xx - 2, mt, larg + 4, H - mb - mt),
                f"r{i}",
            )
        )
    tips.tabela(
        ["Versão", "Intervalo", "Seções no lote", "Flávio no lote", "Total"],
        linhas,
        sub=1,
    )
    out.append("</svg>")
    maior = max(vs, key=lambda v: v["lote_st"])
    leg = legenda_html(
        [
            ("Lote com mais votos de Lula", LULA),
            ("Lote com mais votos de Flávio", FLAVIO),
        ]
    )
    legenda = (
        f"Seções acrescentadas por versão do arquivo nacional. O maior lote, às {maior['gerado_brt'][11:19]}, "
        f"trouxe {inteiro(maior['lote_st'])} seções. A cor diz quem levou mais votos dentro do lote, "
        "o que reflete a geografia de quem chegou naquela hora. Fonte: linha_do_tempo.json."
    )
    return figura_html("lotes_2t", "".join(out), legenda, tips, apos=leg, minw=760)


# ------------------------------------------------------------------ régua 1T × 2T


def curva_1t(L1: dict | None) -> list[tuple[float, float]]:
    """(minutos após 17:00 de 04/10, % de seções) do arquivo nacional do 1º turno."""
    if not L1:
        return []
    out = []
    for v in tabela_linhas(L1["nacional"]["versoes"]):
        g = v.get("gerado_brt") or ""
        if not g.startswith("2026-10-0") or (v.get("st") or 0) <= 0:
            continue
        data, _, h = g.partition(" ")
        hh, mm, ss = (int(z) for z in h.split(":"))
        m = (int(data[-2:]) - 4) * 1440 + (hh - 17) * 60 + mm + ss / 60
        if m <= 600:
            out.append((m, v["pst"]))
    return sorted(out)


def fig_regua(L: dict, L1: dict | None) -> str:
    vs = serie(L)
    c2 = [(v["min"] - FIM_VOTACAO, v["pst"]) for v in vs]
    c1 = curva_1t(L1)
    H, ml, mr, mt, mb = 400, 70, 40, 26, 56
    m0, m1 = -120, 330
    x = escala(m0, m1, ml, W - mr)
    y = escala(0, 100, H - mb, mt)
    out = [
        svg_abre(
            W,
            H,
            "Régua do 1º turno contra o 2º turno",
            "Porcentagem de seções totalizadas pelo tempo depois do fim da votação, 1º e 2º turno.",
        )
    ]
    for tk in range(0, 101, 20):
        out.append(ln(ml, y(tk), W - mr, y(tk), GRADE, 1))
        out.append(t(ml - 8, y(tk) + 4, f"{tk}%", 12.5, MUTED, "end", mono=True))
    m = m0
    while m <= m1:
        out.append(ln(x(m), mt, x(m), H - mb, GRADE, 1))
        rot = (
            "fim"
            if m == 0
            else (
                f"+{m // 60}h"
                if m > 0 and m % 60 == 0
                else (f"−{-m // 60}h" if m % 60 == 0 else "")
            )
        )
        if rot:
            out.append(t(x(m), H - mb + 20, rot, 12.5, MUTED, "middle", mono=True))
        m += 30
    out.append(
        t(
            (ml + W - mr) / 2,
            H - 8,
            "tempo desde o fim da votação (17:00 no 1º turno, 19:00 no 2º)",
            12.5,
            MUTED,
            "middle",
        )
    )
    out.append(ln(x(0), mt, x(0), H - mb, INK, 1.4))
    tips = Tips()
    for curva, cor, w in ((c1, "#8a8f86", 2.2), (c2, VERDE, 2.8)):
        if not curva:
            continue
        pts = " ".join(f"{x(a):.1f},{y(b):.1f}" for a, b in curva if m0 <= a <= m1)
        out.append(
            f'<polyline points="{pts}" fill="none" stroke="{cor}" stroke-width="{w}"/>'
        )
    for alvo in (50, 90, 99):
        lin = []
        for curva, nome in ((c1, "1º turno"), (c2, "2º turno")):
            p = next((a for a, b in curva if b >= alvo), None)
            lin.append((nome, "s/d" if p is None else sinal_min(p)))
        k = tips.add(
            ficha(f"{alvo}% das seções", "minutos desde o fim da votação", lin)
        )
        out.append(
            hit(
                area(ml, y(alvo) - 6, W - ml - mr, 12)
                + ln(
                    ml,
                    y(alvo),
                    W - mr,
                    y(alvo),
                    "#c9c2b0",
                    0.8,
                    ' stroke-dasharray="2 4"',
                ),
                k,
            )
        )
    out.append("</svg>")
    leg = legenda_html([("2º turno", VERDE), ("1º turno", "#8a8f86")])
    p50_2 = next((a for a, b in c2 if b >= 50), None)
    p50_1 = next((a for a, b in c1 if b >= 50), None)
    comp = ""
    if p50_1 is not None and p50_2 is not None:
        comp = f" Metade das seções chegou {sinal_min(p50_2)} do fim da votação no 2º turno, contra {sinal_min(p50_1)} no 1º."
    legenda = (
        "Mesma régua para as duas noites: o zero é o fim da votação (17:00 em 04/10, 19:00 em 25/10, depois da prorrogação)."
        + comp
        + " A parte à esquerda do zero no 2º turno são as seções totalizadas antes da parada das 17:07. "
        "Fontes: linha_do_tempo.json do 2º turno e analysis/apuracao_2026/dados/linha_do_tempo.json."
    )
    return figura_html("regua_1t_2t", "".join(out), legenda, tips, apos=leg, minw=760)


def sinal_min(m: float) -> str:
    """Minutos relativos ao fim da votação em texto: '1h27 depois', '5 min antes'."""
    m = round(m)
    if m < 0:
        return f"{-m} min antes"
    h, mm = divmod(m, 60)
    return (f"{h}h{mm:02d}" if h else f"{mm} min") + " depois"


# ------------------------------------------------------------------ mapa do fechamento

CORES_FECHA = ["#c5dccf", "#7fb19e", "#2f7a66", "#0d3f35", "#061f1a"]
CORTES_FECHA = [255, 270, 285, 300]  # 21:15, 21:30, 21:45, 22:00
ROT_FECHA = [
    "antes de 21:15",
    "21:15 a 21:30",
    "21:30 a 21:45",
    "21:45 a 22:00",
    "depois de 22:00",
]


def fig_mapa_fechou(L: dict) -> str:
    tips, fill, chaves = Tips(), {}, {}
    abertas = []
    for c in L["conclusao_ufs"]:
        uf = c["uf"]
        if uf == "ZZ":
            continue
        m = c.get("fechou_min")
        if m is None:
            fill[uf] = "#ece6d4"
            abertas.append(uf)
            linhas = [("Situação", "ainda com seção por totalizar na rodada")]
        else:
            fill[uf] = CORES_FECHA[sum(m >= q for q in CORTES_FECHA)]
            linhas = [
                ("Arquivo a 100%", c["fechou_brt"][11:19]),
                (
                    "Depois do fim da votação",
                    f"{num(c['fechou_min_apos_fim_votacao'], 0)} min",
                ),
            ]
        if c.get("t1_p100_hhmm"):
            linhas.append(("1º turno a 100%", c["t1_p100_hhmm"]))
        if (
            c.get("atraso_vs_1t_descontada_prorrogacao_min") is not None
            and m is not None
        ):
            v = c["atraso_vs_1t_descontada_prorrogacao_min"]
            linhas.append(
                (
                    "Contra o 1º turno, descontados 120 min",
                    f"{'+' if v > 0 else '−'}{num(abs(v), 0)} min",
                )
            )
        chaves[uf] = tips.add(
            ficha(f"{NOME_UF.get(uf, uf)} ({uf})", "hora em que a UF fechou", linhas)
        )
    svg = mapa_ufs(
        fill,
        chaves,
        "Hora em que cada UF chegou a 100% das seções",
        "Mapa por UF com a hora de Brasília da primeira versão completa.",
    )
    itens = [(ROT_FECHA[i], CORES_FECHA[i]) for i in range(5)] + (
        [("ainda aberta na rodada", "#ece6d4")] if abertas else []
    )
    leg = legenda_html(itens, "Hora de Brasília da primeira versão completa")
    fechadas = sorted(
        (
            c
            for c in L["conclusao_ufs"]
            if c.get("fechou_min") is not None and c["uf"] != "ZZ"
        ),
        key=lambda c: c["fechou_min"],
    )
    txt = ""
    if fechadas:
        txt = (
            f"{fechadas[0]['uf']} fechou primeiro, às {fechadas[0]['fechou_brt'][11:16]}; "
            f"{fechadas[-1]['uf']} por último{' entre as completas' if abertas else ''}, às {fechadas[-1]['fechou_brt'][11:16]}. "
        )
    if abertas:
        txt += (
            f"Ainda com seção por totalizar na rodada: {', '.join(sorted(abertas))}. "
        )
    return figura_html(
        "mapa_fechou_2t",
        svg,
        txt + "Fonte: linha_do_tempo.json, conclusao_ufs.",
        tips,
        modo="fit",
        apos=leg,
    )
