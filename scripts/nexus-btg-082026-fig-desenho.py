#!/usr/bin/env python3
"""Figuras do desenho amostral, do rastro documental e do modelo Nexus.

Capítulo C do dossiê da 8ª rodada BTG/Nexus, 3 de agosto de 2026. Todo número
desenhado aqui sai de docs/assets/nexus_btg_082026_1_data.json ou é aritmética
explícita sobre esse arquivo. Rode sem argumento:

    python3 scripts/nexus-btg-082026-fig-desenho.py
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from svgkit import (
    AMBER,
    CORAL,
    FULL,
    GRAY,
    INK,
    LIME,
    LINE,
    MONO,
    MUTED,
    NAVY,
    PAPER,
    SKY,
    WHITE,
    Canvas,
    br,
    write_fragments,
)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs/assets/nexus_btg_082026_1_data.json"
OUTPUT = ROOT / "docs/assets/figuras/nexus_082026_desenho.json"

# Valor crítico da qui-quadrado com 26 graus de liberdade a 5%, tabela padrão.
CHI2_CRIT_26 = 38.9
# Fundo escuro do dossiê e os dois tons de apoio usados sobre ele.
DARK_PANEL = "#122a41"
DARK_LINE = "#27435f"
DARK_DIM = "#2c4260"


def _halo(canvas: Canvas, x, y, width, height) -> None:
    """Fundo sólido atrás de rótulo que cruza grade, curva ou trama."""
    canvas.rect(x, y, width, height, WHITE, opacity=0.93)


def _moe(base: float) -> float:
    """Margem de erro máxima, p = 50%, 95% de confiança, amostra simples."""
    return 1.96 * 0.5 / math.sqrt(base) * 100


# --------------------------------------------------------------------------
# 1. Alocação por UF contra o eleitorado do TSE
# --------------------------------------------------------------------------


def fig_uf_alocacao(data: dict) -> str:
    geo = data["field_geography"]
    aug, jul = geo["august"], geo["july"]
    ratio_aug = aug["uf_ratio_to_tse"]
    ratio_jul = jul["uf_ratio_to_tse"]
    entrevistas = aug["uf_interviews"]
    ordem = sorted(ratio_aug, key=lambda uf: ratio_aug[uf], reverse=True)

    top, row_h = 112, 33
    bottom = top + 14 * row_h
    height = bottom + 78
    canvas = Canvas(
        FULL,
        height,
        aria=(
            "Barras divergentes da razão entre a fatia de entrevistas por UF e a "
            "fatia do eleitorado no TSE na onda de agosto de 2026, com a razão de "
            "julho marcada em losango"
        ),
    )

    dom0, dom1 = -1.62, 1.42
    axis_x, axis_w = 146, 396
    panels = (24, 618)

    def pos(px: float, valor: float) -> float:
        desvio = min(max(math.log2(valor), dom0), dom1)
        return px + axis_x + (desvio - dom0) / (dom1 - dom0) * axis_w

    canvas.text(
        24,
        26,
        "Entrevistas por UF divididas pelo peso da UF no eleitorado do TSE",
        size=17,
        weight=800,
    )
    canvas.text(
        24,
        48,
        "1,0 é a paridade. Contagem bruta do campo, antes da ponderação do instituto.",
        size=14,
        fill=MUTED,
    )
    canvas.rect(24, 62, 15, 15, NAVY, rx=2)
    canvas.text(46, 75, "acima do eleitorado", size=14)
    canvas.rect(206, 62, 15, 15, AMBER, rx=2)
    canvas.text(228, 75, "abaixo do eleitorado", size=14)
    canvas.path(
        "M 400 69.5 L 407 62.5 L 414 69.5 L 407 76.5 Z",
        fill=WHITE,
        stroke=MUTED,
        stroke_width=2,
    )
    canvas.text(422, 75, "razão da onda de julho", size=14)

    canvas.rect(700, 8, 460, 82, PAPER, rx=6, stroke=LINE)
    canvas.text(
        716,
        36,
        f"χ² = {br(aug['chi2_vs_tse'])} contra o eleitorado do TSE",
        size=17,
        weight=800,
    )
    canvas.label(
        716,
        58,
        f"{aug['chi2_df']} g.l. · crítico a 5% = {br(CHI2_CRIT_26)} · "
        f"p = {br(aug['p_vs_tse'], 4)}",
        size=13,
    )
    canvas.text(
        716,
        79,
        f"Em julho o mesmo teste dava {br(jul['chi2_vs_tse'])}: caiu, ainda não bate.",
        size=13,
        fill=MUTED,
    )

    for px in panels:
        canvas.label(px + 70, 104, "entrev.", size=13, anchor="end")
        canvas.label(px + 134, 104, "razão", size=13, anchor="end")
        for tick in (0.5, 0.7, 1.0, 1.5, 2.0):
            x = pos(px, tick)
            paridade = tick == 1.0
            canvas.line(
                x,
                top - 4,
                x,
                bottom,
                stroke=INK if paridade else LINE,
                width=1.6 if paridade else 1,
            )
            canvas.label(
                x,
                104,
                br(tick, 1),
                size=13,
                anchor="middle",
                fill=INK if paridade else MUTED,
            )

    for coluna, ufs in ((0, ordem[:14]), (1, ordem[14:])):
        px = panels[coluna]
        parity_x = pos(px, 1.0)
        for i, uf in enumerate(ufs):
            valor = ratio_aug[uf]
            y0 = top + i * row_h
            cy = y0 + 16.5
            destaque = uf in ("DF", "MA")
            if destaque:
                canvas.rect(px - 8, y0, 554, row_h, PAPER, rx=4)
            cor = NAVY if valor >= 1 else AMBER
            x_bar = pos(px, valor)
            canvas.rect(
                min(parity_x, x_bar), y0 + 8, abs(x_bar - parity_x), 17, cor, rx=2
            )
            canvas.text(px, cy + 6, uf, size=17, weight=800)
            canvas.label(px + 70, cy + 5, br(entrevistas[uf], 0), size=14, anchor="end")
            canvas.text(
                px + 134,
                cy + 6,
                br(valor, 2),
                size=16,
                family=MONO,
                weight=700,
                fill=cor,
                anchor="end",
            )
            xj = pos(px, ratio_jul[uf])
            canvas.path(
                f"M {xj:.1f} {cy - 7:.1f} L {xj + 7:.1f} {cy:.1f} "
                f"L {xj:.1f} {cy + 7:.1f} L {xj - 7:.1f} {cy:.1f} Z",
                fill=WHITE,
                stroke=MUTED,
                stroke_width=2,
            )
            if destaque:
                texto = f"com paridade seriam {br(round(entrevistas[uf] / valor), 0)}"
                largura = len(texto) * 7.4
                if valor >= 1:
                    _halo(canvas, parity_x - largura - 20, cy - 11, largura + 14, 22)
                    canvas.text(
                        parity_x - 14, cy + 5, texto, size=14, fill=MUTED, anchor="end"
                    )
                else:
                    _halo(canvas, parity_x + 8, cy - 11, largura + 14, 22)
                    canvas.text(parity_x + 14, cy + 5, texto, size=14, fill=MUTED)

    canvas.line(24, bottom + 16, 1156, bottom + 16, stroke=LINE)
    canvas.text(
        24,
        bottom + 44,
        "Os losangos marcam julho: a alocação muda de uma onda para a outra.",
        size=15,
        weight=700,
    )
    canvas.text(
        24,
        bottom + 66,
        f"No Acre a razão caiu de {br(ratio_jul['AC'], 2)} para "
        f"{br(ratio_aug['AC'], 2)}; no Maranhão subiu de {br(ratio_jul['MA'], 2)} "
        f"para {br(ratio_aug['MA'], 2)} e ainda é a menor do país.",
        size=15,
        fill=MUTED,
    )
    return canvas.render()


# --------------------------------------------------------------------------
# 2. As camadas da margem de erro
# --------------------------------------------------------------------------


def fig_margem_camadas(data: dict) -> str:
    aug = data["field_geography"]["august"]
    disp = data["series_dispersion"]
    extra = data["uncontrolled"]["declared_weighting_extra_tse"]

    canvas = Canvas(
        FULL,
        418,
        aria=(
            "Camadas cumulativas da margem de erro nacional e faixa do efeito de "
            "desenho implícito nas séries da rodada"
        ),
    )
    trama = canvas.hatch("mc-hatch", SKY, 0.20)
    canvas.define(
        '<linearGradient id="mc-fade" x1="0" y1="0" x2="1" y2="0">'
        '<stop offset="0.8" stop-color="#ffffff"/>'
        '<stop offset="1" stop-color="#000000"/></linearGradient>'
        '<mask id="mc-mask"><rect x="40" y="220" width="860" height="60" '
        'fill="url(#mc-fade)"/></mask>'
    )

    canvas.text(
        40,
        26,
        "Margem de erro nacional, em pontos percentuais, a 95% de confiança",
        size=17,
        weight=800,
        fill=PAPER,
    )
    canvas.text(
        1140,
        26,
        "sólido = publicado · trama = calculado por nós",
        size=14,
        fill=GRAY,
        anchor="end",
    )
    x0, escala = 40, 313.33
    publicada = float(aug["moe_published_pp"])
    linhas = (
        (54, publicada, "Publicada na capa do relatório", False),
        (
            110,
            aug["moe_srs_pp"],
            f"Piso aritmético: n = {br(aug['interviews'], 0)} sob amostra "
            "aleatória simples",
            True,
        ),
        (
            166,
            aug["moe_with_uf_calibration_pp"],
            "Com a calibração geográfica medida por nós, efeito de desenho "
            f"{br(aug['deff_uf_calibration'], 3)}",
            True,
        ),
    )
    guia_x = x0 + publicada * escala
    canvas.line(
        guia_x,
        54,
        guia_x,
        262,
        stroke=SKY,
        width=1.2,
        stroke_dasharray="5 5",
        opacity=0.6,
    )
    for y0, valor, rotulo, estimado in linhas:
        canvas.text(x0, y0, rotulo, size=15, fill=PAPER)
        largura = valor * escala
        canvas.rect(
            x0,
            y0 + 12,
            largura,
            26,
            trama if estimado else SKY,
            rx=3,
            stroke=SKY,
            stroke_width=1.5 if estimado else 0,
        )
        canvas.text(
            x0 + largura + 14,
            y0 + 32,
            "±" + br(valor, 2),
            size=19,
            weight=800,
            fill=PAPER if estimado else SKY,
        )
        canvas.text(
            x0 + largura + (92 if estimado else 82),
            y0 + 32,
            (
                br(valor - publicada, 2) + " acima da capa"
                if estimado
                else "o número que o relatório imprime"
            ),
            size=14,
            fill=GRAY,
        )

    canvas.text(
        x0,
        222,
        "Com as demais camadas declaradas (sexo, idade, escolaridade, telefonia, "
        f"DDD, {extra[0]} e {extra[1]})",
        size=15,
        fill=PAPER,
    )
    canvas.rect(
        x0,
        234,
        860,
        26,
        trama,
        rx=3,
        stroke=SKY,
        stroke_width=1.5,
        mask="url(#mc-mask)",
    )
    canvas.path("M 906 234 L 936 247 L 906 260 Z", fill=SKY, opacity=0.5)
    canvas.text(950, 254, "maior, e não publicada", size=15, fill=LIME, weight=700)

    canvas.line(40, 282, 1140, 282, stroke=DARK_LINE)
    canvas.text(
        40,
        308,
        f"As {disp['waves']} ondas não oscilam como uma amostra de "
        f"{br(aug['interviews'], 0)}",
        size=17,
        weight=800,
        fill=PAPER,
    )
    canvas.text(
        40,
        330,
        "Cada ponto é uma série da rodada, com o efeito de desenho implícito na "
        "própria oscilação ao longo das ondas.",
        size=14,
        fill=GRAY,
    )

    series = sorted(disp["rows"], key=lambda r: r["implied_deff"])
    menor, maior = series[0], series[-1]
    dx0, dscale = 60, 158.33
    canvas.line(dx0, 376, dx0 + 6 * dscale, 376, stroke=DARK_LINE, width=2)
    vistos: dict[float, int] = {}
    for row in series:
        deff = row["implied_deff"]
        vistos[deff] = vistos.get(deff, 0) + 1
        dy = 376 if vistos[deff] == 1 else 376 - 15
        extremo = row in (menor, maior)
        canvas.circle(
            dx0 + deff * dscale,
            dy,
            9 if extremo else 6,
            LIME if extremo else SKY,
            stroke=NAVY,
            stroke_width=2,
        )
    x_um = dx0 + dscale
    canvas.line(x_um, 356, x_um, 396, stroke=PAPER, width=1.4, stroke_dasharray="4 4")
    canvas.text(
        x_um + 10, 352, "1,0 é o que a margem publicada supõe", size=14, fill=PAPER
    )
    for row in (menor, maior):
        canvas.text(
            dx0 + row["implied_deff"] * dscale,
            352,
            br(row["implied_deff"], 2),
            size=15,
            weight=800,
            fill=LIME,
            anchor="middle",
            family=MONO,
        )
    canvas.text(100, 406, f"{menor['series']}: a mais lisa", size=14, fill=GRAY)
    canvas.text(
        1010,
        406,
        f"{maior['series']}: a mais ruidosa",
        size=14,
        fill=GRAY,
        anchor="end",
    )
    return canvas.render()


# --------------------------------------------------------------------------
# 3. Rotação municipal entre julho e agosto
# --------------------------------------------------------------------------


def fig_territorio_rotacao(data: dict) -> str:
    ter = data["territory"]
    jul, aug = ter["july"], ter["august"]
    saiu, entrou, comum = ter["left"], ter["entered"], ter["overlap"]

    canvas = Canvas(
        FULL,
        408,
        aria=(
            "Rotação dos municípios entre julho e agosto de 2026, com o núcleo "
            "comum alinhado, e a fatia de municípios com uma única entrevista"
        ),
    )
    x0, largura_total = 50, 1080
    k = largura_total / (saiu + comum + entrou)
    x_comum = x0 + saiu * k
    x_fim_comum = x_comum + comum * k

    canvas.text(
        x0,
        30,
        "Metade da lista de municípios trocou de uma onda para a outra",
        size=17,
        weight=800,
        fill=PAPER,
    )
    for guia in (x_comum, x_fim_comum):
        canvas.line(
            guia, 86, guia, 260, stroke=DARK_LINE, width=1.4, stroke_dasharray="5 5"
        )

    canvas.rect(x0, 90, saiu * k, 52, DARK_DIM, rx=4)
    canvas.rect(x_comum, 90, comum * k, 52, SKY, rx=4)
    canvas.rect(x_comum, 200, comum * k, 52, SKY, rx=4)
    canvas.rect(x_fim_comum, 200, entrou * k, 52, AMBER, rx=4)

    canvas.text(
        x0,
        80,
        f"Julho, {br(jul['cities'], 0)} municípios",
        size=17,
        weight=800,
        fill=GRAY,
    )
    canvas.text(
        x_comum,
        190,
        f"Agosto, {br(aug['cities'], 0)} municípios",
        size=17,
        weight=800,
        fill=PAPER,
    )

    blocos = (
        (x0 + saiu * k / 2, 90, f"{br(saiu, 0)} saíram", saiu / jul["cities"], "julho"),
        (
            x_comum + comum * k / 2,
            90,
            f"{br(comum, 0)} em comum",
            comum / jul["cities"],
            "julho",
        ),
        (
            x_comum + comum * k / 2,
            200,
            f"{br(comum, 0)} em comum",
            ter["retention_pct"] / 100,
            "agosto",
        ),
        (
            x_fim_comum + entrou * k / 2,
            200,
            f"{br(entrou, 0)} entraram",
            entrou / aug["cities"],
            "agosto",
        ),
    )
    for cx, topo, titulo, fatia, onda in blocos:
        escuro = topo == 90 and cx < x_comum
        canvas.text(
            cx,
            topo + 24,
            titulo,
            size=17,
            weight=800,
            fill=PAPER if escuro else NAVY,
            anchor="middle",
        )
        canvas.text(
            cx,
            topo + 43,
            f"{br(fatia * 100)}% da lista de {onda}",
            size=13,
            fill=GRAY if escuro else NAVY,
            anchor="middle",
            family=MONO,
        )

    canvas.text(
        x0,
        282,
        f"Só {br(comum, 0)} municípios repetem. A interseção sobre a união é "
        f"{br(ter['jaccard_pct'])}%.",
        size=15,
        fill=GRAY,
    )
    canvas.line(x0, 302, 1130, 302, stroke=DARK_LINE)
    canvas.text(
        x0,
        328,
        f"{br(aug['singletons'], 0)} dos {br(aug['cities'], 0)} municípios de "
        "agosto receberam uma única entrevista",
        size=17,
        weight=800,
        fill=PAPER,
    )
    corte = x0 + aug["singleton_city_pct"] / 100 * largura_total
    canvas.rect(x0, 340, corte - x0, 32, CORAL, rx=4)
    canvas.rect(corte, 340, x0 + largura_total - corte, 32, DARK_DIM, rx=4)
    canvas.text(
        x0 + 14,
        362,
        f"{br(aug['singletons'], 0)} municípios com 1 entrevista, "
        f"{br(aug['singleton_city_pct'])}%",
        size=15,
        weight=700,
        fill=NAVY,
    )
    canvas.text(
        corte + 14,
        362,
        f"{br(aug['cities'] - aug['singletons'], 0)} municípios com 2 ou mais",
        size=15,
        fill=GRAY,
    )
    canvas.text(
        x0,
        394,
        f"Essas entrevistas isoladas são {br(aug['singleton_interview_pct'])}% da "
        f"amostra. Em julho eram {br(jul['singletons'], 0)} municípios, "
        f"{br(jul['singleton_city_pct'])}% da lista.",
        size=14,
        fill=GRAY,
    )
    return canvas.render()


# --------------------------------------------------------------------------
# 4. Linha do tempo do rastro documental
# --------------------------------------------------------------------------


def _pdf_hora(carimbo: str) -> str:
    """Converte D:20260803072934-03'00' em 07h29."""
    return f"{carimbo[10:12]}h{carimbo[12:14]}"


def _pdf_data(carimbo: str) -> str:
    """Converte D:20260505221402+00'00' em 05/05/2026."""
    return f"{carimbo[8:10]}/{carimbo[6:8]}/{carimbo[2:6]}"


def fig_linha_do_tempo(data: dict) -> str:
    trail = data["documents_trail"]
    nota = trail["invoice_august"]
    registro = trail["registration_august"]
    assinatura = trail["statistician_signature"]["august"]
    campo = trail["field"]["august"]
    arquivos = {(f["wave"], f["file"]): f for f in trail["files"]}
    municipios = arquivos[("august", "municipios.pdf")]
    fiscal = arquivos[("august", "nota_fiscal.pdf")]

    canvas = Canvas(
        FULL,
        360,
        aria=(
            "Linha do tempo de maio a agosto de 2026 com a nota fiscal, o registro "
            "no TSE, os três dias de campo e a divulgação da 8ª rodada"
        ),
    )
    eixo_y = 124
    x0, x1 = 80, 1120
    passo = (x1 - x0) / 90.0

    def dia(d: float) -> float:
        return x0 + d * passo

    canvas.line(x0, eixo_y, x1, eixo_y, stroke=DARK_LINE, width=2)
    for corte, nome, centro in (
        (27, "maio", 13),
        (57, "junho", 41.5),
        (88, "julho", 72),
        (None, "agosto", 89),
    ):
        if corte is not None:
            canvas.line(
                dia(corte), eixo_y - 9, dia(corte), eixo_y + 9, stroke=DARK_LINE
            )
        canvas.label(dia(centro), 146, nome, size=13, anchor="middle", fill=GRAY)

    canvas.label(x0, 40, _pdf_data(fiscal["created"]), size=14, fill=AMBER)
    canvas.text(
        x0, 62, "Nota fiscal emitida ao BTG Pactual", size=17, weight=800, fill=PAPER
    )
    vencimento = f"{nota['due'][8:10]}/{nota['due'][5:7]}"
    canvas.text(
        x0,
        83,
        f"R$ {br(nota['value_brl'], 2)}, vencimento em {vencimento}",
        size=15,
        fill=PAPER,
    )
    canvas.text(
        x0,
        103,
        f"descrição do serviço na nota: {nota['description_date']}",
        size=15,
        fill=LIME,
        weight=700,
    )
    canvas.line(x0, 109, x0, eixo_y - 10, stroke=AMBER, width=1.2)
    canvas.circle(x0, eixo_y, 9, AMBER, stroke=NAVY, stroke_width=2)

    x_venc = dia(31)
    canvas.circle(x_venc, eixo_y, 6, NAVY, stroke=AMBER, stroke_width=2.5)
    canvas.label(x_venc + 12, 118, f"{vencimento} vencimento", size=13, fill=GRAY)

    x_reg, x_campo = dia(84), dia(87)
    canvas.rect(x_reg - 10, eixo_y - 16, 1124 - x_reg + 10, 32, SKY, rx=5, opacity=0.22)

    canvas.line(x0, 196, x_campo, 196, stroke=AMBER, width=2)
    canvas.path(
        f"M {x0} 196 l 13 -6 l 0 12 Z M {x_campo:.0f} 196 l -13 -6 l 0 12 Z", fill=AMBER
    )
    canvas.number(560, 184, "87 dias", size=26, fill=LIME, anchor="end")
    canvas.text(
        572, 182, "entre a nota fiscal e o primeiro dia de campo", size=16, fill=PAPER
    )

    canvas.path(
        f"M {x_reg - 10:.0f} 204 L 1124 204 L 1144 232 L 36 232 Z",
        fill=SKY,
        opacity=0.1,
    )
    canvas.path(
        f"M {x_reg - 10:.0f} 204 L 36 232 M 1124 204 L 1144 232",
        fill="none",
        stroke=SKY,
        stroke_width=1,
        stroke_dasharray="4 4",
        opacity=0.5,
    )
    canvas.rect(36, 232, 1108, 124, DARK_PANEL, rx=8)
    canvas.label(52, 252, "a última semana, ampliada", size=13, fill=GRAY)

    d0, d1 = 70, 1120
    passo_d = (d1 - d0) / 8
    eixo_d = 330

    def dia_d(d: float) -> float:
        return d0 + d * passo_d

    canvas.line(d0, eixo_d, d1, eixo_d, stroke=DARK_LINE, width=2)
    for d, rotulo in (
        (0, "27/07"),
        (2, "29/07"),
        (4, "31/07"),
        (6, "02/08"),
        (8, "04/08"),
    ):
        canvas.label(dia_d(d), 352, rotulo, size=13, anchor="middle", fill=GRAY)

    x_28 = dia_d(1)
    canvas.circle(x_28, eixo_d, 8, AMBER, stroke=NAVY, stroke_width=2)
    canvas.label(x_28, 272, "28/07", size=14, fill=AMBER)
    canvas.text(
        x_28,
        292,
        f"Declaração do estatístico assinada, {assinatura[11:13]}h{assinatura[14:16]}",
        size=15,
        fill=PAPER,
    )
    canvas.text(x_28, 310, f"Registro no TSE {registro['id']}", size=14, fill=GRAY)

    xc0, xc1 = dia_d(4), dia_d(7)
    canvas.rect(xc0, eixo_d - 13, xc1 - xc0, 26, SKY, rx=4)
    canvas.text(
        (xc0 + xc1) / 2,
        eixo_d + 5,
        f"campo, {campo[0][:5]} a {campo[1][:5]}",
        size=15,
        weight=800,
        fill=NAVY,
        anchor="middle",
    )

    canvas.circle(dia_d(7.5), eixo_d, 8, LIME, stroke=NAVY, stroke_width=2)
    canvas.label(d1, 272, "03/08", size=14, fill=LIME, anchor="end")
    canvas.text(d1, 292, "Divulgação da 8ª rodada", size=15, fill=PAPER, anchor="end")
    canvas.text(
        d1,
        310,
        f"anexo de municípios gerado às {_pdf_hora(municipios['created'])}",
        size=14,
        fill=GRAY,
        anchor="end",
    )
    return canvas.render()


# --------------------------------------------------------------------------
# 5. Base do recorte contra margem de erro
# --------------------------------------------------------------------------


def fig_base_vs_margem(data: dict) -> str:
    aug = data["field_geography"]["august"]
    n_total = aug["interviews"]
    toplines = data["toplines"]["august"]
    rotulos = toplines["labels"]
    pct_pequeno = min(
        toplines["first"][rotulos.index("Daciolo")],
        toplines["first"][rotulos.index("Cury")],
    )
    pct_nordeste = data["profiles"]["august"]["region"][1]
    pct_desocupados = data["benchmarks"]["pnad_labour_2025"][
        "published_profile_august"
    ]["Desocupados"]
    cluster = next(
        r
        for r in data["series_dispersion"]["rows"]
        if r["series"].startswith("Lula como")
    )

    n_nordeste = round(n_total * pct_nordeste / 100)
    n_desocupados = round(n_total * pct_desocupados / 100)
    n_pequeno = round(n_total * pct_pequeno / 100)
    n_limite = round((1.96 * 0.5 / 0.10) ** 2)

    canvas = Canvas(
        FULL,
        440,
        aria=(
            "Curva da margem de erro contra o tamanho da base do recorte, em escala "
            "logarítmica, com os recortes que o relatório narra"
        ),
    )
    trama = canvas.hatch("bm-hatch", AMBER, 0.14)

    px0, plot_w = 100, 720
    py0, py1, y_max = 82, 372, 26.0
    log0, log1 = math.log10(15), math.log10(3000)

    def px(n: float) -> float:
        return px0 + (math.log10(n) - log0) / (log1 - log0) * plot_w

    def py(m: float) -> float:
        return py1 - m / y_max * (py1 - py0)

    canvas.text(
        100,
        30,
        "Quanto menor o recorte, maior a margem, e o relatório narra recortes minúsculos",
        size=18,
        weight=800,
    )
    canvas.text(
        100,
        52,
        "Curva da margem máxima de uma amostra aleatória simples, 1,96 × 0,5 ÷ √n, "
        "a 95% de confiança.",
        size=15,
        fill=MUTED,
    )

    canvas.rect(px0, py0, px(n_limite) - px0, py(10) - py0, trama, opacity=0.35)
    for marca in (0, 5, 10, 15, 20, 25):
        y = py(marca)
        canvas.line(px0, y, px0 + plot_w, y, stroke=LINE)
        canvas.label(px0 - 12, y + 5, "±" + br(marca, 0), size=13, anchor="end")
    for marca in (20, 50, 100, 200, 500, 1000, 2000):
        x = px(marca)
        canvas.line(x, py0, x, py1, stroke=LINE, opacity=0.6)
        canvas.label(x, 396, br(marca, 0), size=13, anchor="middle")
    canvas.text(
        px0 + plot_w / 2,
        424,
        "Tamanho da base do recorte, em entrevistas, escala logarítmica",
        size=15,
        fill=MUTED,
        anchor="middle",
    )

    canvas.line(
        px(n_limite),
        py0,
        px(n_limite),
        py1,
        stroke=AMBER,
        width=1.6,
        stroke_dasharray="6 5",
    )
    canvas.line(
        px0,
        py(10),
        px0 + plot_w,
        py(10),
        stroke=AMBER,
        width=1.6,
        stroke_dasharray="6 5",
    )
    for i, texto in enumerate(
        (f"abaixo de {br(n_limite, 0)} entrevistas", "a margem passa de ±10")
    ):
        _halo(canvas, px0 + 8, py(10) - 50 + i * 22, 200, 21)
        canvas.text(
            px0 + 14,
            py(10) - 34 + i * 22,
            texto,
            size=15,
            fill=AMBER,
            weight=700,
        )

    pontos = []
    n = 15.0
    while n <= 3000:
        pontos.append(f"{px(n):.1f},{py(min(_moe(n), y_max)):.1f}")
        n *= 1.06
    canvas.path("M " + " L ".join(pontos), fill="none", stroke=INK, stroke_width=3)

    def marcar(base, cor, linhas, dx, dy, anchor="start"):
        x, y = px(base), py(_moe(base))
        canvas.circle(x, y, 9, cor, stroke=WHITE, stroke_width=3)
        for i, (texto, tamanho, fill, peso) in enumerate(linhas):
            largura = len(texto) * tamanho * 0.5
            bx = x + dx if anchor == "start" else x + dx - largura
            _halo(canvas, bx - 7, y + dy + i * 20 - 14, largura + 14, 20)
            canvas.text(
                x + dx,
                y + dy + i * 20,
                texto,
                size=tamanho,
                fill=fill,
                weight=peso,
                anchor=anchor,
            )

    marcar(
        n_pequeno,
        AMBER,
        [
            ("Voto declarado em Cabo Daciolo (1%)", 16, INK, 800),
            (
                f"e em Augusto Cury (1%): n ≈ {br(n_pequeno, 0)}, margem "
                f"±{br(_moe(n_pequeno))}",
                15,
                MUTED,
                None,
            ),
        ],
        18,
        -26,
    )
    marcar(
        n_desocupados,
        AMBER,
        [
            (f"Desocupados, {br(pct_desocupados, 0)}% da amostra,", 16, INK, 800),
            (
                f"e o cluster {cluster['series'].split(' vota ')[0]}: n ≈ {br(n_desocupados, 0)}, "
                f"±{br(_moe(n_desocupados))}",
                15,
                MUTED,
                None,
            ),
        ],
        18,
        -32,
    )
    canvas.line(
        px(n_nordeste),
        py(_moe(n_nordeste)) - 10,
        px(n_nordeste),
        py(_moe(n_nordeste)) - 30,
        stroke=MUTED,
        stroke_dasharray="3 3",
    )
    marcar(
        n_nordeste,
        INK,
        [
            (
                f"Nordeste, {br(pct_nordeste, 0)}%: n ≈ {br(n_nordeste, 0)}, "
                f"±{br(_moe(n_nordeste))}",
                15,
                INK,
                700,
            )
        ],
        12,
        -34,
    )
    marcar(
        n_total,
        INK,
        [
            (
                f"Total nacional: n = {br(n_total, 0)}, margem ±{br(_moe(n_total), 2)}",
                15,
                INK,
                700,
            )
        ],
        -16,
        18,
        anchor="end",
    )

    canvas.rect(845, 86, 315, 234, PAPER, rx=8, stroke=LINE)
    canvas.text(865, 116, f"n ≈ {br(n_pequeno, 0)}", size=19, weight=800)
    canvas.text(865, 142, "Cada entrevista vale 5 pontos", size=15)
    canvas.text(865, 162, "percentuais. Uma leitura de 17%", size=15)
    canvas.text(865, 182, "descreve cerca de 3 pessoas.", size=15)
    canvas.line(865, 204, 1140, 204, stroke=LINE)
    canvas.text(865, 232, "Margem publicada", size=19, weight=800)
    canvas.text(865, 258, "A p. 114 publica margem para", size=15)
    canvas.text(865, 278, "as oito dimensões do perfil,", size=15)
    canvas.text(865, 298, "de ±3 a ±10. As páginas", size=15)
    canvas.text(865, 318, "seguintes narram sem ela.", size=15)
    return canvas.render()


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    figuras = {
        "uf_alocacao": fig_uf_alocacao(data),
        "margem_camadas": fig_margem_camadas(data),
        "territorio_rotacao": fig_territorio_rotacao(data),
        "linha_do_tempo": fig_linha_do_tempo(data),
        "base_vs_margem": fig_base_vs_margem(data),
    }
    write_fragments(OUTPUT, figuras)
    print(f"{OUTPUT}: {len(figuras)} figuras")


if __name__ == "__main__":
    main()
