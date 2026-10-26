"""Figuras do capítulo "Seção por seção": horário, transmissão e comparecimento.

Três desenhos, todos em SVG gerado aqui, com os dados embutidos na página:
- ``encerramento_1t_2t``: horário de encerramento do BU nas mesmas seções, 1º e 2º turno;
- ``emissao_recebimento_uf``: por UF, encerramento do BU, emissão e recebimento;
- ``comparecimento_1t_2t``: mapa de calor do comparecimento de cada seção nos dois turnos.

Na fonte ``amostra`` as distribuições são ponderadas pelas seções de cada UF
(``pagina_fig_secoes_base.pesos``); na fonte ``completo``, contagem simples.
"""

from __future__ import annotations

import math

from apuracao_2026.pagina_comum import CINZA, GOLD, INK, LINE, MUTED, num
from apuracao_2026.pagina_fig_base import (
    GRADE,
    HALO,
    Tips,
    area,
    escala,
    ficha,
    figura_html,
    hit,
    legenda_html,
    ln,
    r,
    svg_abre,
    t,
)

from .pagina_fig_secoes_base import (
    eh_amostra,
    hhmm,
    linhas,
    min_de,
    peso_linha,
    pesos,
)

TEAL = "#0c7a72"
COR_2T = INK
COR_1T = CINZA

# Faixas do horário de encerramento do BU, em minutos inteiros depois das 17:00
# (17:00 = 0, o minuto em que a votação terminava pela regra). "Depois das 19:00"
# segue a regra de secoes.json: minuto inteiro 19:01 ou mais.
FAIXAS_ENC = [
    (None, 0, "até 17:00"),
    (1, 4, "17:01 a 17:04"),
    (5, 9, "17:05 a 17:09"),
    (10, 14, "17:10 a 17:14"),
    (15, 29, "17:15 a 17:29"),
    (30, 60, "17:30 a 18:00"),
    (61, 120, "18:01 a 19:00"),
    (121, None, "depois das 19:00"),
]


def _faixa(m: float) -> int:
    v = math.floor(m)
    for i, (lo, hi, _) in enumerate(FAIXAS_ENC):
        if (lo is None or v >= lo) and (hi is None or v <= hi):
            return i
    return len(FAIXAS_ENC) - 1


def distribuicao_encerramento(S: dict, P: dict | None) -> dict:
    """Parcela das seções (ponderada na amostra) em cada faixa, nos dois turnos."""
    w = pesos(S, P)
    soma = {"2t": [0.0] * len(FAIXAS_ENC), "1t": [0.0] * len(FAIXAS_ENC)}
    for x in linhas(S):
        p = peso_linha(x, w)
        if not p:
            continue
        if x.get("enc_min") is not None:
            soma["2t"][_faixa(x["enc_min"])] += p
        if x.get("enc1_min") is not None:
            soma["1t"][_faixa(x["enc1_min"])] += p
    out = {}
    for k, v in soma.items():
        tot = sum(v) or 1.0
        out[k] = [100 * a / tot for a in v]
    return out


def fig_encerramento(S: dict, P: dict | None) -> str:
    dist = distribuicao_encerramento(S, P)
    w, esq, dir_ = 760, 150, 96
    linha_h, topo = 50, 46
    h = topo + linha_h * len(FAIXAS_ENC) + 20
    vmax = max(max(dist["1t"]), max(dist["2t"]), 1)
    x = escala(0, vmax, esq, w - dir_)
    out = [
        svg_abre(
            w,
            h,
            "Horário de encerramento do BU nas mesmas seções, 1º e 2º turno",
            "Barras horizontais por faixa de horário de encerramento do BU; cinza é o 1º turno, tinta é o 2º.",
        )
    ]
    out.append(t(esq, 22, "parcela das seções em cada faixa", 13, MUTED))
    tips = Tips()
    for i, (_, _, rot) in enumerate(FAIXAS_ENC):
        y0 = topo + i * linha_h
        out.append(t(esq - 10, y0 + 24, rot, 14, INK, "end"))
        partes = []
        for j, (k, cor) in enumerate((("1t", COR_1T), ("2t", COR_2T))):
            v = dist[k][i]
            yb = y0 + 6 + j * 19
            partes.append(r(esq, yb, x(v) - esq, 16, cor))
            partes.append(t(x(v) + 6, yb + 13, f"{num(v, 2)}%", 13, INK, mono=True))
        kk = tips.add(
            ficha(
                rot,
                "encerramento do BU da seção",
                [
                    ("1º turno", f"{num(dist['1t'][i], 2)}%"),
                    ("2º turno", f"{num(dist['2t'][i], 2)}%"),
                ],
            )
        )
        out.append(hit("".join(partes) + area(0, y0, w, linha_h), kk, foco=True))
    out.append(ln(esq, topo - 4, esq, h - 18, MUTED, 1))
    out.append("</svg>")
    pond = (
        "ponderado pelas seções de cada UF"
        if eh_amostra(S) and pesos(S, P)
        else "contagem simples"
    )
    legenda = (
        f"Último voto de cada seção, hora de Brasília, nas mesmas seções nos dois turnos ({pond}). "
        "No 1º turno a fila andava com seis cargos; no 2º, com um ou dois. "
        "Fonte: secoes.json (enc_min, enc1_min)."
    )
    leg = legenda_html([("1º turno", COR_1T), ("2º turno", COR_2T)])
    return figura_html(
        "secoes_encerramento",
        "".join(out),
        legenda,
        tips,
        modo="scroll",
        minw=600,
        apos=leg,
    )


# ------------------------------------------------------------------ transmissão por UF


def _pausa_geral(L: dict | None) -> tuple[float, float] | None:
    if not L:
        return None
    for p in (L.get("pausas") or {}).get("tabela_do_coletor", []):
        if p.get("nivel") == "geral" and p.get("de_min") is not None:
            return p["de_min"], p["ate_min"]
    return None


def fig_emissao_recebimento(S: dict, L: dict | None = None) -> str:
    ufs = [
        u
        for u in S["prorrogacao"]["por_uf"]
        if min_de(u.get("recebimento_p50")) is not None
    ]
    ufs.sort(key=lambda u: min_de(u["recebimento_p50"]))
    br = S["prorrogacao"]["brasil"]
    w, esq, dir_ = 1100, 70, 30
    topo, passo = 70, 26
    h = topo + passo * (len(ufs) + 1) + 46
    fim = max(min_de(u["recebimento_p50"]) for u in ufs)
    fim = 30 * math.ceil((fim + 10) / 30)
    x = escala(-10, fim, esq, w - dir_)
    out = [
        svg_abre(
            w,
            h,
            "Último voto, emissão do BU e recebimento pelo TSE, por UF",
            "Uma linha por UF: ponto do encerramento do BU (mediana), emissão do BU, primeiro recebimento e "
            "faixa do recebimento entre o 10º percentil e a mediana.",
        )
    ]
    pausa = _pausa_geral(L)
    if pausa:
        a, b = pausa
        out.append(r(x(a), topo - 30, x(b) - x(a), h - topo - 16, "#efe7d2"))
        out.append(
            t(
                (x(a) + x(b)) / 2,
                topo - 38,
                f"arquivo nacional parado de {hhmm(a)} a {hhmm(b)}",
                13,
                MUTED,
                "middle",
            )
        )
    for m in range(0, int(fim) + 1, 30):
        out.append(ln(x(m), topo - 24, x(m), h - 40, GRADE, 1))
        out.append(t(x(m), h - 22, hhmm(m), 13, MUTED, "middle", mono=True))
    for m, rot in ((0, "17:00"), (120, "19:00")):
        out.append(
            ln(x(m), topo - 24, x(m), h - 40, MUTED, 1.4, ' stroke-dasharray="4 3"')
        )
        out.append(t(x(m) + 4, topo - 14, rot, 12, INK, weight="600", extra=HALO))
    tips = Tips()
    linhas_uf = [("Brasil", br)] + [(u["uf"], u) for u in ufs]
    for i, (rot, u) in enumerate(linhas_uf):
        y = topo + i * passo + 10
        enc = min_de(u.get("encerramento_p50"))
        emi = min_de(u.get("emissao_p50"))
        pri = min_de(u.get("recebimento_primeiro"))
        p10 = min_de(u.get("recebimento_p10"))
        p50 = min_de(u.get("recebimento_p50"))
        partes = [t(esq - 10, y + 5, rot, 13, INK, "end", "700" if i == 0 else None)]
        if enc is not None and p50 is not None:
            partes.append(ln(x(enc), y, x(p50), y, LINE, 2))
        if p10 is not None and p50 is not None:
            partes.append(
                r(x(p10), y - 6, max(x(p50) - x(p10), 2), 12, TEAL, ' rx="2"')
            )
        if enc is not None:
            partes.append(f'<circle cx="{x(enc):.1f}" cy="{y}" r="5" fill="{INK}"/>')
        if emi is not None:
            partes.append(
                f'<rect x="{x(emi) - 4:.1f}" y="{y - 4}" width="8" height="8" fill="{GOLD}" '
                f'transform="rotate(45 {x(emi):.1f} {y})"/>'
            )
        if pri is not None:
            partes.append(
                f'<rect x="{x(pri) - 5:.1f}" y="{y - 5}" width="10" height="10" fill="#ffffff" '
                f'stroke="{TEAL}" stroke-width="2"/>'
            )
        kk = tips.add(
            ficha(
                rot,
                f"{u.get('n')} seções na base",
                [
                    ("encerramento do BU, mediana", u.get("encerramento_p50") or "s/d"),
                    ("BU emitido, mediana", u.get("emissao_p50") or "s/d"),
                    ("1º recebimento", u.get("recebimento_primeiro") or "s/d"),
                    ("recebimento, mediana", u.get("recebimento_p50") or "s/d"),
                    (
                        "recebidos antes das 19:00",
                        f"{num(u.get('pct_recebido_antes_1900'), 2)}%",
                    ),
                    (
                        "encerramento → recebimento",
                        f"{num(u.get('lag_encerramento_recebimento_p50_min'), 0)} min",
                    ),
                ],
            )
        )
        out.append(
            hit("".join(partes) + area(0, y - passo / 2, w, passo), kk, foco=True)
        )
    out.append("</svg>")
    leg = legenda_html(
        [
            ("encerramento do BU (mediana)", INK),
            ("BU emitido (mediana)", GOLD),
            ("primeiro BU recebido", "#ffffff; border:2px solid " + TEAL),
            ("recebimento: 10º percentil à mediana", TEAL),
        ]
    )
    nota_base = (
        " O primeiro recebimento é o da base lida: na amostra, é o primeiro entre as seções "
        "sorteadas da UF, não o primeiro da UF."
        if eh_amostra(S)
        else ""
    )
    legenda = (
        "Hora de Brasília. O encerramento do BU (último cômputo registrado) e a emissão colam no "
        f"17:00; o recebimento pelo TSE só deslancha depois das 19:00.{nota_base} Fonte: secoes.json "
        "(prorrogacao.por_uf) e linha_do_tempo.json (pausa geral do arquivo nacional)."
    )
    return figura_html(
        "secoes_emissao_recebimento",
        "".join(out),
        legenda,
        tips,
        modo="scroll",
        minw=820,
        apos=leg,
    )


# ------------------------------------------------------------------ comparecimento


def grade_comparecimento(
    S: dict, P: dict | None, lo: float = 50, hi: float = 100, passo: float = 2
) -> tuple[dict, float]:
    """Soma dos pesos por célula (taxa 1T, taxa 2T), e o total."""
    w = pesos(S, P)
    cel: dict[tuple[int, int], float] = {}
    tot = 0.0
    nb = int((hi - lo) / passo)
    for x in linhas(S):
        p = peso_linha(x, w)
        a, b = x.get("taxa1"), x.get("taxa2")
        if not p or a is None or b is None:
            continue
        i = min(max(int((a - lo) // passo), 0), nb - 1)
        j = min(max(int((b - lo) // passo), 0), nb - 1)
        cel[(i, j)] = cel.get((i, j), 0.0) + p
        tot += p
    return cel, tot


AZUL_SEQ = ["#e9e4d8", "#c9d6e3", "#95b0cc", "#5f86b0", "#2f5d8f", "#173e66"]


def fig_comparecimento(S: dict, P: dict | None) -> str:
    lo, hi, passo = 50.0, 100.0, 2.0
    cel, _ = grade_comparecimento(S, P, lo, hi, passo)
    w = h = 620
    m = 64
    x = escala(lo, hi, m, w - 20)
    y = escala(lo, hi, h - m, 20)
    tam = x(lo + passo) - x(lo)
    out = [
        svg_abre(
            w,
            h,
            "Comparecimento de cada seção no 1º e no 2º turno",
            "Mapa de calor: cada célula conta as seções com o comparecimento do 1º turno no eixo "
            "horizontal e o do 2º no vertical. Acima da diagonal, a seção subiu.",
        )
    ]
    vmax = max(cel.values(), default=1) or 1
    for (i, j), v in sorted(cel.items()):
        k = min(
            int(len(AZUL_SEQ) * math.log1p(v) / math.log1p(vmax)), len(AZUL_SEQ) - 1
        )
        k = max(k, 1)
        out.append(r(x(lo + i * passo), y(lo + (j + 1) * passo), tam, tam, AZUL_SEQ[k]))
    out.append(ln(x(lo), y(lo), x(hi), y(hi), INK, 1.2))
    out.append(
        ln(
            x(lo),
            y(lo + 5),
            x(hi - 5),
            y(hi),
            "#b02f21",
            1.2,
            ' stroke-dasharray="5 4"',
        )
    )
    for v in range(int(lo), int(hi) + 1, 10):
        out.append(t(x(v), h - m + 20, f"{v}%", 12, MUTED, "middle", mono=True))
        out.append(t(m - 8, y(v) + 4, f"{v}%", 12, MUTED, "end", mono=True))
    out.append(t((m + w) / 2, h - 18, "comparecimento no 1º turno", 13, INK, "middle"))
    out.append(
        t(
            18,
            h / 2,
            "comparecimento no 2º turno",
            13,
            INK,
            "middle",
            extra=f' transform="rotate(-90 18 {h / 2})"',
        )
    )
    out.append(t(x(hi - 1), y(hi - 1) + 30, "mesma taxa", 12, INK, "end", extra=HALO))
    out.append(t(x(lo + 8), y(lo + 17), "5 pp acima", 12, "#b02f21", extra=HALO))
    out.append("</svg>")
    leg = legenda_html(
        [
            ("poucas seções", AZUL_SEQ[1]),
            ("muitas", AZUL_SEQ[3]),
            ("concentração máxima", AZUL_SEQ[5]),
        ],
        "Cor da célula (escala logarítmica)",
    )
    pond = (
        "ponderadas pelas seções de cada UF"
        if eh_amostra(S) and pesos(S, P)
        else "contadas"
    )
    legenda = (
        f"Células de 2 pp; seções {pond}, comparecimento abaixo de 50% somado à primeira célula. "
        "A nuvem fica colada na diagonal e um pouco acima dela: a alta é geral e pequena. "
        "Fonte: secoes.json (taxa1, taxa2)."
    )
    return figura_html(
        "secoes_comparecimento",
        "".join(out),
        legenda,
        Tips(),
        modo="fit",
        apos=leg,
    )
