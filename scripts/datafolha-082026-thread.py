#!/usr/bin/env python3
"""Monta a thread educativa da auditoria Datafolha de agosto de 2026.

A thread ensina o leitor a ler uma pesquisa: o que e amostra, margem,
estratificacao, cota e ponderacao; como refazer a reponderacao por renda com
uma media ponderada de tres linhas; e o que exigir de transparencia. Cada card
sai em 16:9 com o texto copiavel logo abaixo.

Todos os numeros vem de analysis/datafolha_082026/*.json, produzidos pelos
scripts de auditoria. Nada e digitado a mao aqui alem do texto.

Uso:
  python3 scripts/datafolha-082026-thread.py

Saida:
  docs/datafolha_082026_thread.html
"""

from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis" / "datafolha_082026"
OUTPUT = ROOT / "docs" / "datafolha_082026_thread.html"
PHOTOS = "img/quaest_082026/web"

INK = "#f4f2ea"
MUTED = "#9a9789"
FAINT = "#8f8c7f"  # medido contra o painel do card, WCAG AA
LIME = "#cfe63c"
CYAN = "#45c9c2"
AMBER = "#f0a930"
GREEN = "#34b47e"
LULA = "#e0483a"
LULA_TXT = "#ea6a5c"  # a mesma cor, clareada para texto pequeno
FLAVIO = "#3f8fd6"
GREY = "#939cae"  # medido contra o painel do card, WCAG AA

MONO = "IBM Plex Mono, monospace"
SANS = "IBM Plex Sans Condensed, Arial, sans-serif"
DISPLAY = "Fraunces, Georgia, serif"

KIND = {
    "tese": (LIME, "a tese"),
    "aula": (CYAN, "aula"),
    "conta": (AMBER, "a conta"),
    "fato": (FLAVIO, "fato publicado"),
    "acao": (GREEN, "o que fazer"),
}


# --------------------------------------------------------------- desenho


def svg(body: str, width: int = 660, height: int = 372, label: str = "") -> str:
    return (
        f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{html.escape(label)}">'
        f"{body}</svg>"
    )


def text(x, y, value, size=13, fill=MUTED, family=MONO, weight=400, anchor="start"):
    return (
        f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" fill="{fill}" '
        f'font-weight="{weight}" text-anchor="{anchor}">{html.escape(str(value))}</text>'
    )


def rect(x, y, w, h, fill, radius=3, opacity=1.0):
    return (
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(w, 0):.1f}" height="{h:.1f}" '
        f'rx="{radius}" fill="{fill}" opacity="{opacity}"/>'
    )


def line(x1, y1, x2, y2, stroke, width=1, dash=None):
    extra = f' stroke-dasharray="{dash}"' if dash else ""
    return (
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
        f'stroke="{stroke}" stroke-width="{width}"{extra}/>'
    )


def viz_bignum(spec):
    parts = [text(0, 22, spec["title"], size=12, fill=FAINT)]
    y = 88
    for item in spec["rows"]:
        parts.append(
            text(
                0,
                y,
                item["value"],
                size=56,
                fill=item.get("color", INK),
                family=DISPLAY,
                weight=700,
            )
        )
        parts.append(text(0, y + 28, item["label"], size=15, fill=MUTED, family=SANS))
        y += 112
    return svg("".join(parts), height=y - 60, label=spec["title"])


def viz_stack(spec):
    """Duas reguas empilhadas: perfil da pesquisa contra perfil oficial."""
    parts = [text(0, 20, spec["title"], size=12, fill=FAINT)]
    width = 660
    palette = [LULA, AMBER, FLAVIO, GREEN]
    top = 52
    for block in spec["blocks"]:
        parts.append(
            text(0, top - 8, block["label"], size=14, fill=INK, family=SANS, weight=700)
        )
        x = 0.0
        for index, (name, value) in enumerate(block["parts"]):
            w = width * value / 100
            parts.append(rect(x, top, w, 54, palette[index % len(palette)]))
            if w > 62:
                parts.append(
                    text(
                        x + w / 2,
                        top + 27,
                        f"{value:.1f}%",
                        size=16,
                        fill="#0c0d0b",
                        family=SANS,
                        weight=700,
                        anchor="middle",
                    )
                )
                parts.append(
                    text(
                        x + w / 2,
                        top + 45,
                        name,
                        size=11,
                        fill="#0c0d0b",
                        family=MONO,
                        anchor="middle",
                    )
                )
            x += w
        top += 108
    for index, item in enumerate(spec.get("foot", [])):
        parts.append(
            text(
                0,
                top + 18 + index * 26,
                item,
                size=16,
                fill=INK if index == 0 else LIME,
                family=SANS,
                weight=700,
            )
        )
    height = top + 18 + 26 * max(len(spec.get("foot", [])) - 1, 0) + 12
    return svg("".join(parts), height=height, label=spec["title"])


def viz_calc(spec):
    """A media ponderada linha a linha, com a multiplicacao visivel."""
    parts = [text(0, 18, spec["title"], size=12, fill=FAINT)]
    cols = [0, 176, 300, 424, 560]
    heads = spec["heads"]
    parts.append(line(0, 32, 660, 32, "rgba(244,242,234,.22)"))
    for index, head in enumerate(heads):
        anchor = "start" if index == 0 else "end"
        x = cols[index] if index == 0 else cols[index] + 96
        parts.append(text(x, 50, head, size=11, fill=FAINT, anchor=anchor))
    y = 78
    for row in spec["rows"]:
        parts.append(
            text(cols[0], y, row["label"], size=14, fill=INK, family=SANS, weight=600)
        )
        for index, value in enumerate(row["cells"], start=1):
            color = row.get("color", MUTED) if index == len(row["cells"]) else MUTED
            parts.append(
                text(cols[index] + 96, y, value, size=14, fill=color, anchor="end")
            )
        y += 34
    parts.append(line(0, y - 20, 660, y - 20, "rgba(244,242,234,.22)"))
    total = spec["total"]
    parts.append(
        text(
            cols[0], y + 12, total["label"], size=15, fill=INK, family=SANS, weight=700
        )
    )
    parts.append(
        text(
            cols[-1] + 96,
            y + 12,
            total["value"],
            size=22,
            fill=total.get("color", LIME),
            family=DISPLAY,
            weight=700,
            anchor="end",
        )
    )
    for index, item in enumerate(spec.get("foot", [])):
        parts.append(
            text(
                0,
                y + 56 + index * 26,
                item,
                size=15,
                fill=INK if index == 0 else LIME,
                family=SANS,
                weight=700,
            )
        )
    height = y + 56 + 26 * max(len(spec.get("foot", [])) - 1, 0) + 12
    return svg("".join(parts), height=height, label=spec["title"])


def viz_series(spec):
    """As quatro ondas, placar publicado contra placar sob a regua comum."""
    parts = [text(0, 18, spec["title"], size=12, fill=FAINT)]
    left, right, top, bottom = 46, 596, 54, 250
    span = right - left
    lo, hi = -6.0, 8.0

    def px(value):
        return bottom - (value - lo) / (hi - lo) * (bottom - top)

    parts.append(line(left, px(0), right, px(0), "rgba(244,242,234,.35)", 1, "4 4"))
    parts.append(text(0, px(0) + 4, "empate", size=11, fill=FAINT))
    for level in (8, 4, -4):
        parts.append(text(0, px(level) + 4, f"{level:+d}", size=11, fill=FAINT))
    step = span / (len(spec["waves"]) - 1)
    pub = [
        (left + index * step, px(w["publicado"]))
        for index, w in enumerate(spec["waves"])
    ]
    adj = [
        (left + index * step, px(w["ajustado"]))
        for index, w in enumerate(spec["waves"])
    ]
    parts.append(
        '<polyline fill="none" stroke="%s" stroke-width="3" points="%s"/>'
        % (LULA, " ".join(f"{x:.1f},{y:.1f}" for x, y in pub))
    )
    parts.append(
        '<polyline fill="none" stroke="%s" stroke-width="3" stroke-dasharray="7 5" points="%s"/>'
        % (LIME, " ".join(f"{x:.1f},{y:.1f}" for x, y in adj))
    )
    for index, wave in enumerate(spec["waves"]):
        x = left + index * step
        parts.append(
            f'<circle cx="{x:.1f}" cy="{px(wave["publicado"]):.1f}" r="6" fill="{LULA}"/>'
        )
        parts.append(
            f'<circle cx="{x:.1f}" cy="{px(wave["ajustado"]):.1f}" r="6" fill="{LIME}"/>'
        )
        anchor = "end" if index == len(spec["waves"]) - 1 else "middle"
        parts.append(
            text(
                x,
                px(wave["publicado"]) - 15,
                f'Lula +{wave["publicado"]:.0f}',
                size=12,
                fill=LULA_TXT,
                family=SANS,
                weight=700,
                anchor=anchor,
            )
        )
        parts.append(
            text(
                x,
                px(wave["ajustado"]) + 23,
                wave["rotulo"],
                size=12,
                fill=LIME,
                family=SANS,
                weight=700,
                anchor=anchor,
            )
        )
        parts.append(
            text(x, bottom + 27, wave["label"], size=12, fill=MUTED, anchor=anchor)
        )
    parts.append(
        text(
            0,
            306,
            "Linha cheia: o que foi publicado.",
            size=15,
            fill=INK,
            family=SANS,
            weight=700,
        )
    )
    parts.append(
        text(
            0,
            332,
            "Linha tracejada: a mesma pesquisa sob a renda do IBGE.",
            size=15,
            fill=LIME,
            family=SANS,
            weight=700,
        )
    )
    return svg("".join(parts), height=346, label=spec["title"])


def viz_checklist(spec):
    parts = [text(0, 20, spec["title"], size=12, fill=FAINT)]
    y = 54
    for index, item in enumerate(spec["items"], start=1):
        parts.append(
            f'<circle cx="12" cy="{y - 5}" r="11" fill="none" stroke="{CYAN}" stroke-width="1.6"/>'
        )
        parts.append(text(12, y, str(index), size=12, fill=CYAN, anchor="middle"))
        parts.append(
            text(36, y - 2, item[0], size=15, fill=INK, family=SANS, weight=700)
        )
        parts.append(text(36, y + 19, item[1], size=13, fill=MUTED, family=SANS))
        y += 54
    return svg("".join(parts), height=y - 26, label=spec["title"])


def viz_dumbbell(spec):
    parts = [text(0, 20, spec["title"], size=12, fill=FAINT)]
    left, right = 150, 620
    lo, hi = spec.get("min", 0), spec.get("max", 100)

    def px(value):
        return left + (value - lo) / (hi - lo) * (right - left)

    y = 62
    for row in spec["rows"]:
        parts.append(
            text(0, y + 5, row["label"], size=14, fill=INK, family=SANS, weight=600)
        )
        a, b = px(row["a"]), px(row["b"])
        parts.append(line(min(a, b), y, max(a, b), y, "rgba(244,242,234,.22)", 6))
        parts.append(f'<circle cx="{a:.1f}" cy="{y}" r="8" fill="{GREY}"/>')
        parts.append(
            f'<circle cx="{b:.1f}" cy="{y}" r="8" fill="{row.get("color", LIME)}"/>'
        )
        parts.append(
            text(
                a,
                y - 16,
                row["a_label"],
                size=12,
                fill=GREY,
                family=MONO,
                anchor="middle",
            )
        )
        label_color = LULA_TXT if row.get("color") == LULA else row.get("color", LIME)
        parts.append(
            text(
                b,
                y + 26,
                row["b_label"],
                size=12,
                fill=label_color,
                family=MONO,
                anchor="middle",
            )
        )
        y += 74
    for index, item in enumerate(spec.get("foot", [])):
        parts.append(
            text(
                0,
                y + 18 + index * 26,
                item,
                size=15,
                fill=INK if index == 0 else LIME,
                family=SANS,
                weight=700,
            )
        )
    height = y + 18 + 26 * max(len(spec.get("foot", [])) - 1, 0) + 12
    return svg("".join(parts), height=height, label=spec["title"])


def viz_ladder(spec):
    """Escada de passos: cada degrau e uma etapa da conta."""
    parts = [text(0, 20, spec["title"], size=12, fill=FAINT)]
    y = 46
    for index, step in enumerate(spec["steps"], start=1):
        parts.append(rect(0, y, 660, 60, "rgba(244,242,234,.05)", 4))
        parts.append(rect(0, y, 4, 60, step.get("color", CYAN), 0))
        parts.append(text(20, y + 26, f"passo {index}", size=11, fill=FAINT))
        parts.append(
            text(20, y + 46, step["label"], size=15, fill=INK, family=SANS, weight=700)
        )
        parts.append(
            text(
                640,
                y + 38,
                step["value"],
                size=20,
                fill=step.get("color", CYAN),
                family=DISPLAY,
                weight=700,
                anchor="end",
            )
        )
        y += 72
    return svg("".join(parts), height=y - 8, label=spec["title"])


RENDER = {
    "bignum": viz_bignum,
    "stack": viz_stack,
    "calc": viz_calc,
    "series": viz_series,
    "checklist": viz_checklist,
    "dumbbell": viz_dumbbell,
    "ladder": viz_ladder,
}


# --------------------------------------------------------------- conteudo


def rotulo_gap(gap: float) -> str:
    """Rotulo curto do saldo ajustado, com empate declarado abaixo de meio ponto."""
    if abs(gap) < 0.5:
        return "empate"
    lider = "Lula" if gap > 0 else "Flávio"
    return f"{lider} +{abs(gap):.1f}".replace(".", ",")


NOME_FAIXA = {
    "ate2": "Até 2 SM",
    "de2a5": "2 a 5 SM",
    "de5a10": "5 a 10 SM",
    "mais5": "Mais de 5 SM",
    "mais10": "Mais de 10 SM",
}


def build_cards(renda, fundo, audit):
    """Monta os dezoito cards a partir dos JSON de auditoria."""
    waves = renda["waves"]
    agosto = waves[-1]
    faixas = [NOME_FAIXA[band] for band in agosto["bands"]]
    peso_df = {
        NOME_FAIXA[band]: agosto["source_profile_pct"][band] for band in agosto["bands"]
    }
    peso_pn = {
        NOME_FAIXA[band]: agosto["target_profile_pct"][band] for band in agosto["bands"]
    }
    # Cada linha do relatorio soma 99 a 101 por arredondamento; renormalizamos.
    voto = {}
    for band, row in zip(agosto["bands"], agosto["rows"]):
        soma = sum(row)
        voto[NOME_FAIXA[band]] = (100 * row[0] / soma, 100 * row[1] / soma)
    bases = dict(zip(faixas, agosto["bases"]))
    base_total = sum(agosto["bases"])
    publicado = {
        item[0]: item[1]
        for item in zip(("lula", "flavio", "branco", "indeciso"), agosto["published"])
    }
    ajustado = agosto["adjusted"]

    def linhas_calc(pesos, indice):
        rows = []
        for faixa, peso in pesos.items():
            valor = voto[faixa][indice]
            rows.append(
                {
                    "label": faixa,
                    "cells": [
                        f"{peso:.2f}%",
                        f"{valor:.1f}",
                        f"{peso * valor / 100:.2f}",
                    ],
                    "color": LIME,
                }
            )
        return rows

    total_df_lula = sum(peso_df[f] * voto[f][0] / 100 for f in peso_df)
    total_pn_lula = sum(peso_pn[f] * voto[f][0] / 100 for f in peso_pn)
    total_pn_flavio = sum(peso_pn[f] * voto[f][1] / 100 for f in peso_pn)
    total_df_flavio = sum(peso_df[f] * voto[f][1] / 100 for f in peso_df)

    return [
        {
            "kind": "tese",
            "kicker": "mesma pesquisa, duas eleições",
            "photo": f"{PHOTOS}/banca.jpg",
            "pos": "center 40%",
            "tag": "datafolha · 18–19/08/2026 · n = 2.058 · BR-04496/2026",
            "metric": "47×43 vira 44,2×46,0",
            "title": "A manchete depende de uma régua",
            "lead": "A Folha e a Globo publicaram: Lula 47, Flávio 43 no segundo turno. O número está certo. O que ele significa depende de uma escolha que a manchete não conta: qual retrato do Brasil a pesquisa usa para pesar as respostas.",
            "chips": [
                ("l", "50% até 2 SM na pesquisa"),
                ("c", "35,4% na PNAD do IBGE"),
                ("a", "sensibilidade, não recontagem"),
            ],
            "viz": {
                "type": "bignum",
                "title": "segundo turno, 18 e 19 de agosto de 2026",
                "rows": [
                    {
                        "value": "47 × 43",
                        "label": "publicado pelo instituto",
                        "color": INK,
                    },
                    {
                        "value": "44,2 × 46,0",
                        "label": "com a distribuição de renda do IBGE",
                        "color": LIME,
                    },
                ],
            },
            "foot": [
                "arvor intelligence · brasil.arvor.co",
                "relatório completo, p. 22 do anexo",
            ],
            "copy": [
                "A Folha e a Globo publicaram no dia 21: Lula 47, Flávio 43 no segundo turno. O número está certo. Eu conferi célula por célula.",
                "O que ele significa depende de uma escolha que nenhuma manchete conta. Toda pesquisa pesa as respostas para que a amostra pareça com o país. Para isso, ela precisa de um retrato do país. E o retrato de renda que o Datafolha usa não é o do IBGE.",
                "O Datafolha apresenta um Brasil em que 50% dos eleitores vivem com até dois salários mínimos no domicílio. A PNAD Contínua, a maior pesquisa domiciliar do país, mede 35,4%.",
                "Troque só isso. Nada mais. O mesmo relatório devolve Lula 44,2 e Flávio 46,0.",
                "Nesta thread eu mostro a conta inteira, com os números na tela, para você refazer sozinho.",
                "E, no caminho, ensino o suficiente de estatística para você nunca mais precisar acreditar numa manchete de pesquisa: o que é amostra, por que a margem da capa não serve para comparar dois candidatos, como uma amostra nacional é sorteada e o que exatamente acontece quando um instituto pondera.",
                "Dezoito posts. Nenhum documento sigiloso. Nenhuma conta que não caiba numa planilha.",
            ],
        },
        {
            "kind": "fato",
            "kicker": "a ficha",
            "photo": f"{PHOTOS}/urna-maquina.jpg",
            "tag": "tudo isto é público e qualquer um baixa",
            "metric": "51 páginas",
            "title": "Comece pelo documento, não pela notícia",
            "lead": "Toda pesquisa registrada no TSE publica o relatório completo, o questionário aplicado, o plano amostral, a lista de municípios e a nota fiscal. Está no PesqEle, é grátis e não exige cadastro.",
            "chips": [
                ("c", "PesqEle é público"),
                ("b", "questionário aplicado"),
                ("a", "R$ 307.641,60"),
            ],
            "viz": {
                "type": "checklist",
                "title": "o que existe e quase ninguém abre",
                "items": [
                    (
                        "Relatório completo, 51 páginas",
                        "As 22 primeiras viram notícia. As 29 do anexo trazem 14 tabelas cruzadas.",
                    ),
                    (
                        "Questionário aplicado, 8 páginas",
                        "A ordem, o texto exato e os cartões mostrados ao entrevistado.",
                    ),
                    (
                        "Registro no TSE",
                        "Plano amostral, cotas declaradas, fonte dos dados e valor pago.",
                    ),
                    (
                        "Anexo de bairros",
                        "Município, bairro e setor censitário de cada entrevista.",
                    ),
                ],
            },
            "foot": ["pesqele-divulgacao.tse.jus.br", "registro BR-04496/2026"],
            "copy": [
                "Antes de qualquer conta, a ficha. Datafolha, registro TSE BR-04496/2026. Campo em 18 e 19 de agosto de 2026. 2.058 entrevistas presenciais em pontos de fluxo, em 128 municípios. Contrataram a Folha de S.Paulo e a TV Globo, por R$ 307.641,60.",
                "Tudo isso é público. O sistema chama PesqEle, é do Tribunal Superior Eleitoral, é grátis e não pede cadastro. De lá saem o relatório completo de 51 páginas, o questionário aplicado com 8 páginas, o plano amostral, a lista de municípios e bairros e as notas fiscais.",
                "É muita transparência, e é bom que seja. O problema não é falta de documento. É que a cobertura para na página 2 e o país inteiro discute duas linhas de um arquivo de cinquenta e uma páginas.",
                "O relatório tem duas partes. As vinte e duas primeiras páginas são a apresentação, e é de lá que sai a notícia. As vinte e nove seguintes são o anexo de tabelas cruzadas: catorze tabelas, cada uma repartida por onze recortes, de renda a religião.",
                "As outras quarenta e nove páginas estão abertas há dias e continuam abertas agora. Nesta thread nós vamos até elas.",
            ],
        },
        {
            "kind": "aula",
            "kicker": "aula 1",
            "photo": f"{PHOTOS}/feira.jpg",
            "tag": "o que é uma pesquisa, sem jargão",
            "metric": "2.058 para 158 milhões",
            "title": "A colher e a panela",
            "lead": "Você não precisa tomar a sopa inteira para saber se está salgada. Precisa mexer bem e provar uma colher. Pesquisa é isso: 2.058 pessoas para falar de 158 milhões de eleitores.",
            "chips": [
                ("c", "amostra"),
                ("b", "universo"),
                ("a", "mexer bem = sortear"),
            ],
            "viz": {
                "type": "ladder",
                "title": "por que 2.058 pessoas conseguem falar do país",
                "steps": [
                    {
                        "label": "Mexer a panela é sortear",
                        "value": "aleatório",
                        "color": CYAN,
                    },
                    {
                        "label": "Se o sorteio é honesto, a colher representa",
                        "value": "amostra",
                        "color": CYAN,
                    },
                    {
                        "label": "Quanto maior a colher, menor o erro",
                        "value": "±2 p.p.",
                        "color": LIME,
                    },
                    {
                        "label": "Colher mal mexida não representa nada",
                        "value": "viés",
                        "color": LULA,
                    },
                ],
            },
            "foot": [
                "eleitorado residente no Brasil: 157.846.602",
                "TSE, competência junho de 2026",
            ],
            "copy": [
                "Aula 1. Como 2.058 pessoas falam por 158 milhões de eleitores.",
                "Você não precisa tomar a sopa inteira para saber se está salgada. Precisa mexer bem e provar uma colher. É exatamente isso que uma pesquisa faz.",
                "O segredo não é o tamanho da colher, é o mexer. Se o sorteio é honesto, uma colher pequena diz muito sobre a panela. Se a panela não foi mexida, nem uma tigela inteira serve.",
                "Daí vem a diferença entre dois erros que costumam ser confundidos.",
                "Erro de amostragem é o azar do sorteio. Ele encolhe quando a amostra cresce e é o que a margem de erro mede.",
                "Viés é a panela mal mexida: quando um tipo de gente tem mais chance de cair na colher do que outro. Esse não encolhe com amostra maior. Só encolhe com desenho melhor, ou com correção declarada.",
                "Um exemplo de viés que você reconhece na hora: entrevistar só em ponto de fluxo, no meio da tarde, num dia útil. Quem está trabalhando dentro de um escritório fechado tem menos chance de ser abordado que quem circula na rua. Aumentar a amostra de 2 mil para 20 mil não conserta isso. Só o desenho conserta, ou uma correção declarada depois.",
                "Guarde essa distinção entre erro de sorteio e viés. A thread inteira depende dela.",
            ],
        },
        {
            "kind": "aula",
            "kicker": "aula 2",
            "photo": f"{PHOTOS}/urna-fila.jpg",
            "tag": "a margem que a capa não traz",
            "metric": "±2 não é ±2",
            "title": "A margem da diferença é maior",
            "lead": "A capa diz margem de dois pontos. Isso vale para cada número sozinho. Comparar dois candidatos tem incerteza maior, porque quando um sobe o outro tende a cair, e o erro dos dois se soma.",
            "chips": [
                ("b", "cada número: ±2"),
                ("l", "a diferença: ±4,10"),
                ("a", "o intervalo cruza zero"),
            ],
            "viz": {
                "type": "dumbbell",
                "title": "intervalo de 95% para a diferença Lula menos Flávio",
                "min": -3,
                "max": 12,
                "rows": [
                    {
                        "label": "2º turno, 4 pts",
                        "a": -0.10,
                        "b": 8.10,
                        "a_label": "−0,10",
                        "b_label": "+8,10",
                        "color": LULA,
                    },
                    {
                        "label": "1º turno, 6 pts",
                        "a": 2.34,
                        "b": 9.66,
                        "a_label": "+2,34",
                        "b_label": "+9,66",
                        "color": FLAVIO,
                    },
                ],
                "foot": [
                    "O intervalo do 2º turno inclui o zero.",
                    "O do 1º turno não inclui. Só um dos dois é liderança.",
                ],
            },
            "foot": [
                "aproximação de amostragem aleatória simples",
                "o instituto não publica o efeito de desenho",
            ],
            "copy": [
                "Aula 2. A margem de erro da capa não serve para comparar dois candidatos.",
                "Quando a pesquisa diz margem de dois pontos, isso vale para cada número isolado. Lula 47 quer dizer algo entre 45 e 49.",
                "Comparar dois candidatos é outra conta. Se um sobe, o outro tende a cair: os dois erros andam juntos e a incerteza da diferença fica maior que a de cada parte.",
                "Para 47 contra 43, com 2.058 entrevistas, a margem da diferença é de 4,095 pontos. O intervalo da vantagem de quatro pontos vai de −0,10 a +8,10.",
                "Ele inclui o zero. Isso não prova empate no eleitorado. Prova que esta amostra não separa os dois com 95% de confiança.",
                "No primeiro turno, 39 contra 33, a mesma conta dá de +2,34 a +9,66. Não inclui o zero. Ali existe liderança medida.",
                "A conta, para quem quiser conferir: a variância da diferença entre duas proporções da mesma pesquisa é a soma das duas menos o quadrado da diferença, tudo dividido pelo tamanho da amostra. Com 0,47 e 0,43 em 2.058 entrevistas, dá 4,095 pontos a 95%.",
                "Uma pesquisa, duas situações diferentes, uma manchete só. Aprenda a pedir a margem da diferença, e repare em quem nunca a publica.",
            ],
        },
        {
            "kind": "aula",
            "kicker": "aula 3",
            "photo": f"{PHOTOS}/rodoviaria_fabriciano.jpg",
            "tag": "como uma amostra nacional é montada",
            "metric": "estrato, sorteio, cota",
            "title": "Ninguém sorteia 2.058 brasileiros no vácuo",
            "lead": "O Datafolha divide o país em estratos por região e por natureza do município, sorteia cidades com probabilidade proporcional ao tamanho, depois bairros e pontos, e no ponto aplica cotas de gênero e idade. Isso é boa prática e está declarado.",
            "chips": [
                ("c", "estratificação"),
                ("b", "PPT"),
                ("a", "cota no ponto de fluxo"),
            ],
            "viz": {
                "type": "ladder",
                "title": "o caminho até o entrevistado, como declarado no TSE",
                "steps": [
                    {
                        "label": "Estratos: 5 regiões × capital, RM ou interior",
                        "value": "1",
                        "color": CYAN,
                    },
                    {
                        "label": "Sorteio de municípios com prob. proporcional ao tamanho",
                        "value": "2",
                        "color": CYAN,
                    },
                    {
                        "label": "Sorteio de bairros e pontos de abordagem",
                        "value": "3",
                        "color": CYAN,
                    },
                    {
                        "label": "No ponto, cotas de gênero e faixa etária",
                        "value": "4",
                        "color": AMBER,
                    },
                ],
            },
            "foot": [
                "registro BR-04496/2026, plano amostral",
                "128 municípios, 288 setores censitários",
            ],
            "copy": [
                "Aula 3. Estratificação e cota, que é como uma amostra nacional nasce.",
                "Ninguém sorteia 2.058 brasileiros de uma lista única. O país é dividido em estratos: as cinco regiões, cruzadas com capital, região metropolitana e interior. Dentro de cada estrato sorteiam-se municípios com probabilidade proporcional ao tamanho, ou seja, cidade grande tem mais chance de entrar. Depois sorteiam-se bairros e pontos de abordagem. Só então o entrevistador aborda alguém.",
                "No ponto entra a cota: o entrevistador precisa preencher um número de homens e de mulheres, e de cada faixa de idade. Isso impede que a amostra vire só quem tem tempo de parar na rua.",
                "Tudo isso está declarado no registro do TSE, e é boa prática. Vale dizer com todas as letras: o desenho do Datafolha é sério.",
                "Nesta onda foram 128 municípios e 288 setores censitários, com média de 7,15 entrevistas por setor. Isso tem uma consequência que quase nunca é dita: sete pessoas do mesmo quarteirão se parecem mais entre si do que sete pessoas sorteadas em sete cidades. Amostra em conglomerado tem incerteza maior que a fórmula da capa supõe, e o instituto não publica o quanto.",
                "O que fica de fora da cota é o que mais interessa aqui. Renda não é cota. Renda entra depois, na ponderação. E é aí que a régua importa.",
            ],
        },
        {
            "kind": "aula",
            "kicker": "aula 4",
            "photo": f"{PHOTOS}/supermercado.jpg",
            "tag": "o passo que decide o placar",
            "metric": "peso",
            "title": "Ponderar é corrigir a colher pela panela",
            "lead": "Se o campo trouxe gente demais de um tipo e de menos de outro, o instituto multiplica cada resposta por um número para que o retrato final tenha a cara do país. É legítimo, é padrão e é necessário. Só que exige um retrato do país para comparar.",
            "chips": [
                ("c", "ponderar é legítimo"),
                ("a", "depende do benchmark"),
                ("b", "renda não é cota"),
            ],
            "viz": {
                "type": "ladder",
                "title": "como um peso é construído",
                "steps": [
                    {
                        "label": "O campo trouxe 52% até 2 salários",
                        "value": "obtido",
                        "color": GREY,
                    },
                    {
                        "label": "A referência escolhida diz 49%",
                        "value": "alvo",
                        "color": AMBER,
                    },
                    {
                        "label": "Peso da faixa: alvo dividido por obtido",
                        "value": "0,94",
                        "color": CYAN,
                    },
                    {
                        "label": "Troque a referência e o peso muda junto",
                        "value": "0,68",
                        "color": LIME,
                    },
                ],
            },
            "foot": [
                "49% é a referência declarada ao TSE",
                "35,4% é a PNADC anual 2025 do IBGE",
            ],
            "copy": [
                "Aula 4. Ponderação, o passo silencioso que decide o placar.",
                "Nenhuma pesquisa de rua sai perfeita do campo. Vem gente demais de um tipo e de menos de outro. O instituto então multiplica cada entrevista por um número, o peso, para que o retrato final tenha a cara do país.",
                "O peso é simples de entender. Se o campo trouxe 52% de eleitores de até dois salários mínimos e a referência diz que o país tem 49%, a faixa recebe peso 0,94: cada resposta dela vale um pouco menos. Se a referência dissesse 35%, o peso seria 0,68, e o mesmo grupo pesaria muito menos.",
                "Repare no que acabou de acontecer. A pesquisa é a mesma, as respostas são as mesmas, o campo é o mesmo. O resultado muda porque a referência mudou.",
                "Ponderar é legítimo, padrão e necessário. Não é truque. Mas depende inteiramente de qual retrato do país você escolhe como verdadeiro.",
                "E há um detalhe de calendário que vale registrar. O registro no TSE declara que a referência de renda usada vem da PNAD anual de 2024. A PNAD anual de 2025 já estava publicada quando o campo foi a campo, em agosto de 2026. Além disso, o cartão de renda mostrado ao entrevistado usa reais de 2026: dois salários mínimos são R$ 3.242 hoje e eram R$ 2.824 em 2024. A régua da pergunta e a régua da cota estão em anos diferentes.",
                "É essa escolha que ninguém discute na manchete. Vamos discutir agora.",
            ],
        },
        {
            "kind": "conta",
            "kicker": "a régua",
            "photo": f"{PHOTOS}/feira_caruaru.jpg",
            "tag": "duas fotografias do mesmo país",
            "metric": "50% × 35,4%",
            "title": "O Brasil da pesquisa e o Brasil do IBGE",
            "lead": "O perfil publicado na página 5 do anexo diz que metade do eleitorado vive com até dois salários mínimos no domicílio. A PNAD Contínua anual mais recente, que visitou 152.488 domicílios, mede 35,4% entre pessoas de 16 anos ou mais.",
            "chips": [
                ("l", "Datafolha 52,0%"),
                ("c", "PNADC 35,4%"),
                ("a", "diferença de 16,5 pontos"),
            ],
            "viz": {
                "type": "stack",
                "title": "distribuição de renda domiciliar, em salários mínimos",
                "blocks": [
                    {
                        "label": "Como a pesquisa distribui o eleitorado",
                        "parts": [
                            ("até 2 SM", 51.97),
                            ("2 a 5", 35.48),
                            ("mais de 5", 12.55),
                        ],
                    },
                    {
                        "label": "Como o IBGE mede o país",
                        "parts": [
                            ("até 2 SM", 35.43),
                            ("2 a 5", 39.22),
                            ("mais de 5", 25.35),
                        ],
                    },
                ],
                "foot": [
                    "A faixa mais pobre pesa 16,5 pontos a mais na pesquisa.",
                    "A faixa acima de 5 salários pesa metade do que o IBGE mede.",
                ],
            },
            "foot": ["Datafolha, anexo p. 5 e 22", "IBGE, PNADC anual 2025, visita 1"],
            "copy": [
                "A régua. Aqui está a escolha inteira, em dois números.",
                "O Datafolha apresenta um eleitorado em que 52,0% das rendas informadas ficam até dois salários mínimos, 35,5% entre dois e cinco, e 12,6% acima de cinco.",
                "A PNAD Contínua anual do IBGE, que visitou 152.488 domicílios e pergunta rendimento fonte por fonte, mede 35,4%, 39,2% e 25,4% entre pessoas de 16 anos ou mais.",
                "São 16,5 pontos de diferença na faixa mais pobre. E a faixa acima de cinco salários aparece na pesquisa com metade do peso que o IBGE mede.",
                "Duas explicações honestas para isso, e as duas importam. Primeira: renda declarada de improviso na rua não é a mesma coisa que rendimento domiciliar levantado com questionário longo em casa. Segunda: a referência que o instituto declarou ao TSE vem da PNAD de 2024, e a de 2025 já estava publicada quando o campo foi a campo.",
                "A PNAD anual de 2025 que usamos como referência entrevistou 408.364 pessoas em 152.488 domicílios. Não é uma pesquisa concorrente do Datafolha: é a base estatística com que o próprio país mede desemprego, pobreza e renda.",
                "Nada disso é fraude, e é importante dizer com todas as letras. É uma escolha de régua, declarada e legítima. Só que ela decide o placar, e por isso merece estar na manchete tanto quanto o placar.",
            ],
        },
        {
            "kind": "conta",
            "kicker": "a conta, passo 1",
            "photo": f"{PHOTOS}/eleicao-rua.jpg",
            "tag": "os números estão na página 22 do anexo",
            "metric": "3 linhas",
            "title": "A tabela inteira cabe num cartão",
            "lead": "O relatório publica o segundo turno por faixa de renda. São três linhas. Com elas e com os pesos, qualquer pessoa refaz o placar nacional numa planilha.",
            "chips": [
                ("l", "até 2 SM: Lula 55, Flávio 35"),
                ("b", "2 a 5: Lula 37, Flávio 51"),
                ("b", "+5: Lula 39, Flávio 54"),
            ],
            "viz": {
                "type": "calc",
                "title": "segundo turno por faixa de renda, relatório p. 22 do anexo",
                "heads": [
                    "faixa de renda",
                    "base ponderada",
                    "Lula",
                    "Flávio",
                    "não escolhe",
                ],
                "rows": [
                    {
                        "label": faixa,
                        "cells": [
                            f"{bases[faixa]:,}".replace(",", "."),
                            str(agosto["rows"][index][0]),
                            str(agosto["rows"][index][1]),
                            str(agosto["rows"][index][2] + agosto["rows"][index][3]),
                        ],
                        "color": MUTED,
                    }
                    for index, faixa in enumerate(faixas)
                ],
                "total": {
                    "label": "soma das bases",
                    "value": f"{base_total:,}".replace(",", "."),
                    "color": INK,
                },
                "foot": [
                    "Quem ganha menos vota mais em Lula. Quem ganha mais vota mais em Flávio.",
                    "Então o peso de cada faixa decide o placar nacional.",
                ],
            },
            "foot": [
                "74 entrevistados não informaram renda",
                "e por isso ficam fora desta tabela",
            ],
            "copy": [
                "A conta, passo 1. A tabela que faz tudo funcionar tem três linhas.",
                "O relatório publica o segundo turno separado por faixa de renda familiar, na página 22 do anexo de tabelas cruzadas.",
                "Até 2 salários mínimos, base ponderada 1.031: Lula 55, Flávio 35.",
                "De 2 a 5 salários, base 704: Lula 37, Flávio 51.",
                "Acima de 5 salários, base 249: Lula 39, Flávio 54.",
                "Repare no padrão, porque é ele que torna a régua decisiva. Quem ganha menos vota mais em Lula. Quem ganha mais vota mais em Flávio. A inversão acontece já na segunda faixa.",
                "Quando o voto varia tanto entre as faixas, o peso que você dá a cada faixa não é detalhe técnico. É o resultado.",
                "A coluna que sobra, de quem não escolhe ninguém, também tem padrão: 9% na faixa mais pobre, 12% na do meio, 7% na mais rica.",
                "E um detalhe honesto: 74 entrevistados não informaram renda e por isso não aparecem em nenhuma das três linhas. A soma das bases dá 1.984, não 2.058.",
                "Guarde estes nove números. No próximo post nós os usamos.",
            ],
        },
        {
            "kind": "conta",
            "kicker": "a conta, passo 2",
            "photo": f"{PHOTOS}/antena.jpg",
            "tag": "primeiro, provar que a leitura está certa",
            "metric": "46,9 × 43,2",
            "title": "A média ponderada devolve o placar publicado",
            "lead": "Multiplique o voto de cada faixa pelo peso dela na pesquisa e some. Se a conta estiver certa, ela tem que reproduzir o número que o instituto publicou. Reproduz.",
            "chips": [
                ("c", "peso × voto, soma"),
                ("b", "publicado: 47"),
                ("a", "recomposto: 46,9"),
            ],
            "viz": {
                "type": "calc",
                "title": "média ponderada com os pesos da própria pesquisa, voto em Lula",
                "heads": [
                    "faixa de renda",
                    "peso na pesquisa",
                    "voto em Lula",
                    "contribuição",
                ],
                "rows": linhas_calc(peso_df, 0),
                "total": {
                    "label": "soma das contribuições",
                    "value": f"{total_df_lula:.2f}",
                    "color": LIME,
                },
                "foot": [
                    "O instituto publicou 47. A conta devolve 46,9.",
                    "A leitura da tabela está correta, e agora dá para mexer nela.",
                ],
            },
            "foot": [
                "percentuais renormalizados por linha",
                "arredondamento do relatório é de 1 ponto",
            ],
            "copy": [
                "A conta, passo 2. Antes de mudar qualquer coisa, é preciso provar que a leitura está certa.",
                "A regra é a média ponderada, que você já usa sem saber. É a mesma conta da média do boletim quando cada prova vale um peso diferente.",
                "Multiplique o voto de cada faixa pelo peso daquela faixa e some tudo.",
                "Com os pesos da própria pesquisa: 51,97% vezes 55,6 dá 28,9. Mais 35,48% vezes 37, que dá 13,1. Mais 12,55% vezes 39, que dá 4,9.",
                "Soma: 46,9.",
                "O Datafolha publicou 47. A diferença é arredondamento das células impressas.",
                "Isso é o controle de qualidade da auditoria. Se a recomposição não batesse com o publicado, qualquer conta derivada estaria errada e nada do que vem a seguir valeria. Ela bate.",
                "Se ficou abstrato, pense no boletim da escola. Você tirou 8 na prova que vale 50% da nota, 6 na que vale 30% e 4 na que vale 20%. A média não é 6, que seria a média simples. É 8 vezes 0,5, mais 6 vezes 0,3, mais 4 vezes 0,2, que dá 6,6. O peso muda o resultado sem mudar nenhuma nota.",
                "É exatamente a mesma conta. As faixas de renda são as provas, o voto é a nota e o peso é quanto cada faixa vale no país.",
                "Agora dá para trocar uma peça e ver o que acontece.",
            ],
        },
        {
            "kind": "conta",
            "kicker": "a conta, passo 3",
            "photo": f"{PHOTOS}/fluxo_25demarco.jpg",
            "tag": "troque só os pesos, não toque no resto",
            "metric": "44,1 × 46,2",
            "title": "Os mesmos votos, a régua do IBGE",
            "lead": "Não se muda nenhuma resposta, nenhuma célula, nenhum entrevistado. Muda-se apenas quanto cada faixa de renda pesa, usando a distribuição da PNAD Contínua. A soma vira outra.",
            "chips": [
                ("c", "mesmas respostas"),
                ("a", "outros pesos"),
                ("l", "outro resultado"),
            ],
            "viz": {
                "type": "calc",
                "title": "a mesma média ponderada com os pesos do IBGE, voto em Lula",
                "heads": [
                    "faixa de renda",
                    "peso na PNADC",
                    "voto em Lula",
                    "contribuição",
                ],
                "rows": linhas_calc(peso_pn, 0),
                "total": {
                    "label": "soma das contribuições",
                    "value": f"{total_pn_lula:.2f}",
                    "color": LIME,
                },
                "foot": [
                    f"Lula sai de {total_df_lula:.2f} para {total_pn_lula:.2f}.",
                    f"Flávio, de {total_df_flavio:.2f} para {total_pn_flavio:.2f}.",
                ],
            },
            "foot": [
                "PNADC anual 2025, visita 1, VD5001",
                "pessoas de 16 anos ou mais",
            ],
            "copy": [
                "A conta, passo 3. Agora troque uma coisa só.",
                "Nenhuma resposta muda. Nenhuma célula da tabela muda. Nenhum entrevistado é acrescentado ou removido. Muda apenas quanto cada faixa de renda pesa no total, usando a distribuição da PNAD Contínua no lugar da distribuição da pesquisa.",
                "35,43% vezes 55,6 dá 19,7. Mais 39,22% vezes 37, que dá 14,5. Mais 25,35% vezes 39, que dá 9,9.",
                "Soma: 44,1. Lula caiu 2,8 pontos.",
                "Fazendo o mesmo com a coluna de Flávio: 46,2. Ele subiu 3,0.",
                "É toda a magia. Uma média ponderada de três linhas, que cabe numa planilha e leva dois minutos.",
                "Vale repetir o que não mudou, porque é isso que dá força ao exercício: as três linhas de voto continuam idênticas às que o instituto imprimiu. Ninguém foi reentrevistado, nenhum número foi corrigido, nenhuma resposta foi descartada.",
                "A pergunta que fica não é técnica, é editorial: qual das duas réguas descreve melhor o eleitorado brasileiro de 2026? Uma responde por uma pergunta rápida em ponto de fluxo, a outra por um questionário domiciliar de 152 mil casas.",
            ],
        },
        {
            "kind": "conta",
            "kicker": "a conta, passo 4",
            "photo": f"{PHOTOS}/urna-fila.jpg",
            "pos": "center 35%",
            "tag": "o resultado, ancorado no que o instituto publicou",
            "metric": "44,19 × 45,97",
            "title": "O segundo turno troca de sinal",
            "lead": "Para não trocar o placar do instituto pelo nosso, ancoramos: partimos do 47 e do 43 publicados e aplicamos apenas a diferença que a troca de régua produziu. Nada é inventado, e a origem continua sendo o número oficial.",
            "chips": [
                ("l", "Lula 47 → 44,19"),
                ("b", "Flávio 43 → 45,97"),
                ("a", "saldo −1,78"),
            ],
            "viz": {
                "type": "ladder",
                "title": "do publicado ao reponderado, em quatro linhas",
                "steps": [
                    {
                        "label": "Placar publicado pelo instituto",
                        "value": f"{publicado['lula']:.0f} × {publicado['flavio']:.0f}",
                        "color": GREY,
                    },
                    {
                        "label": "Recomposto com os pesos da pesquisa",
                        "value": f"{total_df_lula:.2f} × {total_df_flavio:.2f}".replace(
                            ".", ","
                        ),
                        "color": CYAN,
                    },
                    {
                        "label": "Recomposto com os pesos do IBGE",
                        "value": f"{total_pn_lula:.2f} × {total_pn_flavio:.2f}".replace(
                            ".", ","
                        ),
                        "color": AMBER,
                    },
                    {
                        "label": "Publicado mais a diferença da troca",
                        "value": f"{ajustado['lula']:.2f} × {ajustado['flavio']:.2f}".replace(
                            ".", ","
                        ),
                        "color": LIME,
                    },
                ],
            },
            "foot": [
                "fórmula aberta: publicado + (PNADC − recomposto)",
                "docs e scripts em brasil.arvor.co",
            ],
            "copy": [
                "A conta, passo 4. O resultado, e a blindagem que ele exige.",
                "Não trocamos o placar do instituto pelo nosso. Ancoramos. Partimos do 47 e do 43 publicados e somamos apenas a diferença que a troca de régua produziu.",
                "Lula: 47 menos 2,81 dá 44,19.",
                "Flávio: 43 mais 2,97 dá 45,97.",
                "A vantagem publicada de quatro pontos para Lula vira uma vantagem de 1,78 ponto para Flávio.",
                "A fórmula inteira é esta: publicado mais a diferença entre a recomposição com a régua do IBGE e a recomposição com a régua da pesquisa. Ela está no script, o script está público, e o resultado é conferível por qualquer pessoa com uma planilha.",
                "Por que ancorar em vez de publicar direto o 44,08 contra 46,22 da recomposição? Porque a recomposição usa só uma margem e o instituto pondera por várias ao mesmo tempo. Ancorando, o número que sai continua sendo o do instituto mais o efeito isolado da troca, e não uma pesquisa nossa.",
                "E vale repetir: isto é análise de sensibilidade, não recontagem. Mede de qual régua o placar depende, não quem está ganhando a eleição.",
            ],
        },
        {
            "kind": "conta",
            "kicker": "a série",
            "photo": f"{PHOTOS}/congresso.jpg",
            "tag": "quatro ondas, a mesma régua nas quatro",
            "metric": "4 de 4",
            "title": "A eleição que não foi noticiada",
            "lead": "Maio, junho, julho e agosto renderam quatro manchetes iguais: Lula à frente por quatro a cinco pontos. Aplique a mesma distribuição de renda do IBGE às quatro e a vantagem some nas quatro.",
            "chips": [
                ("l", "publicado: +4, +4, +5, +4"),
                ("c", "sob a régua: −2,81 a −1,78"),
                ("a", "nenhuma onda com Lula à frente"),
            ],
            "viz": {
                "type": "series",
                "title": "saldo Lula menos Flávio no 2º turno, em pontos",
                "waves": [
                    {
                        "label": "20–21/mai",
                        "publicado": 4,
                        "ajustado": -2.811,
                        "rotulo": "Flávio +2,8",
                    },
                    {
                        "label": "17–18/jun",
                        "publicado": 4,
                        "ajustado": -0.164,
                        "rotulo": "empate",
                    },
                    {
                        "label": "22–23/jul",
                        "publicado": 5,
                        "ajustado": -0.005,
                        "rotulo": "empate",
                    },
                    {
                        "label": "18–19/ago",
                        "publicado": 4,
                        "ajustado": -1.784,
                        "rotulo": "Flávio +1,8",
                    },
                ],
            },
            "foot": [
                "mesma fórmula e mesmo benchmark nas quatro ondas",
                "relatórios de maio, junho, julho e agosto",
            ],
            "copy": [
                "A série. Aqui a coisa deixa de ser um número e vira uma narrativa inteira.",
                "As quatro últimas ondas do Datafolha renderam quatro manchetes iguais: Lula lidera o segundo turno por quatro a cinco pontos. Estabilidade, dizem. Vantagem consolidada.",
                "Aplique a mesma distribuição de renda do IBGE às quatro, com a mesma fórmula, sem escolher onda.",
                "Maio: Flávio +2,81.",
                "Junho: empate, Flávio +0,16.",
                "Julho: empate exato.",
                "Agosto: Flávio +1,78.",
                "Em nenhuma das quatro Lula fica à frente. E a leitura de tendência também muda: sob esta régua, o desafiante perdeu cerca de um ponto entre maio e agosto, em vez de estar correndo atrás de uma vantagem consolidada.",
                "São duas eleições diferentes, e a diferença não é acadêmica. Uma disputa em que o presidente lidera com folga desde maio e uma disputa empatada desde maio produzem decisões opostas sobre aliança, agenda e prioridade de recurso, dos dois lados. Só uma das duas está sendo noticiada.",
                "E repare no que este exercício não faz: ele não escolhe a onda que dá o resultado desejado. São as quatro ondas disponíveis, com a mesma fórmula e o mesmo benchmark, publicadas juntas.",
            ],
        },
        {
            "kind": "aula",
            "kicker": "o limite",
            "photo": f"{PHOTOS}/praca_conselheiro_pena.jpg",
            "tag": "o que este número é e o que ele não é",
            "metric": "sensibilidade",
            "title": "Não é recontagem, e dizer isso é parte do método",
            "lead": "Reponderar uma margem publicada mostra de qual régua o resultado depende. Não identifica o resultado verdadeiro do eleitorado, porque a ponderação real do instituto é conjunta e não é pública.",
            "chips": [
                ("a", "quatro limites declarados"),
                ("c", "falsificável"),
                ("b", "sem microdados"),
            ],
            "viz": {
                "type": "checklist",
                "title": "os quatro limites, declarados antes de qualquer conclusão",
                "items": [
                    (
                        "Não há microdados nem pesos individuais",
                        "Sem eles, interações entre renda e outras margens não são identificáveis.",
                    ),
                    (
                        "Renda de rua não é renda do IBGE",
                        "Uma pergunta rápida em ponto de fluxo capta menos que um questionário domiciliar.",
                    ),
                    (
                        "Uma margem por vez",
                        "Ajustar renda não corrige escolaridade, idade, região ou religião ao mesmo tempo.",
                    ),
                    (
                        "Tendência sob uma régua, não a eleição",
                        "A série mostra dependência do benchmark, não quem está ganhando.",
                    ),
                ],
            },
            "foot": [
                "as limitações estão no JSON público",
                "analysis/datafolha_082026",
            ],
            "copy": [
                "O limite. Esta é a parte que separa auditoria de propaganda, e ela vem antes da conclusão, não depois.",
                "O que fizemos é análise de sensibilidade: trocar uma peça e medir o efeito. Ela responde a uma pergunta precisa e estreita, que é de qual régua o placar depende.",
                "Ela não responde quem está ganhando a eleição, e por quatro motivos que declaramos antes de qualquer número.",
                "Um: não existem microdados nem pesos individuais públicos. Sem eles não dá para saber como renda interage com escolaridade, idade e região dentro da ponderação real do instituto, que é conjunta.",
                "Dois: renda declarada de improviso na rua não é idêntica ao rendimento domiciliar levantado pelo IBGE com questionário longo.",
                "Três: ajustamos uma margem por vez. As outras ficam como estão.",
                "Quatro: a série mostra tendência sob uma régua comum, não a tendência real da eleição.",
                "Quem publica sensibilidade como se fosse recontagem está fazendo a mesma coisa que a manchete que critica.",
            ],
        },
        {
            "kind": "conta",
            "kicker": "a robustez",
            "photo": f"{PHOTOS}/antena.jpg",
            "pos": "center 60%",
            "tag": "o achado sobrevive ao arredondamento",
            "metric": "100%",
            "title": "Não é sorte do arredondamento",
            "lead": "As células do relatório vêm arredondadas em número inteiro. Perturbando cada uma em meio ponto e refazendo a conta dez mil vezes, o sinal se mantém em todos os sorteios. E, das cinco margens testadas, quatro não mudam nada.",
            "chips": [
                ("a", "10.000 simulações"),
                ("c", "100% invertem"),
                ("b", "69,2% do caminho basta"),
            ],
            "viz": {
                "type": "dumbbell",
                "title": "efeito de cada margem no saldo do 2º turno, em pontos",
                "min": -3,
                "max": 6,
                "rows": [
                    {
                        "label": "Sexo",
                        "a": 4.0,
                        "b": 4.10,
                        "a_label": "publicado",
                        "b_label": "+4,10",
                        "color": GREY,
                    },
                    {
                        "label": "Idade",
                        "a": 4.0,
                        "b": 3.95,
                        "a_label": "publicado",
                        "b_label": "+3,95",
                        "color": GREY,
                    },
                    {
                        "label": "Região",
                        "a": 4.0,
                        "b": 4.00,
                        "a_label": "publicado",
                        "b_label": "+4,00",
                        "color": GREY,
                    },
                    {
                        "label": "Escolaridade",
                        "a": 4.0,
                        "b": 5.09,
                        "a_label": "publicado",
                        "b_label": "+5,09",
                        "color": FLAVIO,
                    },
                    {
                        "label": "Renda",
                        "a": 4.0,
                        "b": -1.78,
                        "a_label": "publicado",
                        "b_label": "−1,78",
                        "color": LIME,
                    },
                ],
                "foot": [
                    "Quatro margens preservam a liderança publicada.",
                    "Só a renda troca o sinal.",
                ],
            },
            "foot": [
                "10.000 sorteios com células perturbadas em ±0,5",
                "intervalo simulado: −1,96 a −1,61",
            ],
            "copy": [
                "A robustez. Toda conta boa precisa passar por um teste que poderia derrubá-la.",
                "As tabelas do relatório vêm arredondadas em número inteiro. Um 55 pode ser qualquer coisa entre 54,5 e 55,5. Isso poderia, sozinho, explicar uma inversão apertada.",
                "Então perturbamos cada célula em meio ponto para cima ou para baixo, renormalizamos as linhas e refizemos a conta dez mil vezes.",
                "Flávio fica à frente em 100% dos sorteios. O intervalo simulado do saldo vai de −1,96 a −1,61. O achado não é sorte de arredondamento.",
                "Segundo teste, mais duro. Fizemos o mesmo exercício com as outras quatro margens que o relatório publica.",
                "Sexo: o saldo vai de +4 para +4,10. Idade: +3,95. Região: +4,00. Escolaridade: +5,09, ou seja, amplia a vantagem de Lula.",
                "Quatro das cinco margens preservam a liderança publicada. Só a renda troca o sinal. Não estamos escolhendo a margem que dá o resultado que queremos: estamos relatando a única que muda alguma coisa.",
            ],
        },
        {
            "kind": "acao",
            "kicker": "conheça o país",
            "photo": f"{PHOTOS}/feira.jpg",
            "pos": "center 55%",
            "tag": "a régua está pública e é de graça",
            "metric": "brasil.arvor.co",
            "title": "Ler pesquisa começa por conhecer o Brasil",
            "lead": "Ninguém consegue julgar se um retrato do país está certo sem saber como o país é. A PNAD Contínua do IBGE é pública, gratuita e cobre renda, escolaridade, trabalho, cor e região. Nós processamos os microdados e publicamos o resultado aberto.",
            "chips": [
                ("c", "PNADC é pública"),
                ("b", "microdados abertos"),
                ("a", "nosso ensaio é gratuito"),
            ],
            "viz": {
                "type": "checklist",
                "title": "o que você descobre sobre o Brasil em vinte minutos",
                "items": [
                    (
                        "Quanto o brasileiro realmente ganha",
                        "Renda domiciliar por faixa de salário mínimo, por estado e por região.",
                    ),
                    (
                        "Quem estudou até onde",
                        "Escolaridade da população de 16 anos ou mais, que é o universo eleitoral.",
                    ),
                    (
                        "Onde as pessoas moram e trabalham",
                        "Capital, região metropolitana e interior; ocupação e informalidade.",
                    ),
                    (
                        "Como isso muda a leitura de qualquer pesquisa",
                        "Com o perfil oficial na mão, você confere a régua de qualquer instituto.",
                    ),
                ],
            },
            "foot": [
                "brasil.arvor.co · O Brasil em Números",
                "IBGE, PNAD Contínua, microdados",
            ],
            "copy": [
                "Conheça o país. Esta é a parte que nenhuma thread de pesquisa costuma dizer.",
                "Você não consegue julgar se o retrato de um instituto está certo sem saber como o Brasil é de verdade. E o Brasil de verdade está público.",
                "A PNAD Contínua do IBGE é a maior pesquisa domiciliar do país. Ela visita mais de 150 mil domicílios, pergunta rendimento fonte por fonte, escolaridade, ocupação, cor e região, e publica os microdados de graça.",
                "O problema é que microdado bruto tem quase dois gigabytes e não abre no Excel. Por isso nós processamos e publicamos o resultado aberto, com o código à vista, em brasil.arvor.co.",
                "Lá está quanto o brasileiro realmente ganha por faixa de salário mínimo, quem estudou até onde entre os eleitores de 16 anos ou mais, e onde as pessoas moram e trabalham.",
                "A edição que usamos aqui, a anual de 2025, entrevistou 408.364 pessoas em 152.488 domicílios.",
                "Com esse perfil na mão você confere a régua de qualquer instituto, em qualquer eleição, sem depender de ninguém. Inclusive de nós.",
                "E vale para muito além de pesquisa eleitoral. O mesmo hábito serve para orçamento público, inflação, emprego e dívida: os dados oficiais estão publicados, e quase toda discussão nacional acontece sem que ninguém abra a planilha.",
            ],
        },
        {
            "kind": "acao",
            "kicker": "como ler uma manchete",
            "photo": f"{PHOTOS}/banca.jpg",
            "pos": "center 60%",
            "tag": "seis perguntas antes de acreditar",
            "metric": "6 perguntas",
            "title": "O checklist que cabe no bolso",
            "lead": "Não é preciso ser estatístico. É preciso fazer seis perguntas, e todas têm resposta pública. Se alguma delas não tiver, isso também é informação.",
            "chips": [
                ("c", "leva dois minutos"),
                ("b", "tudo é público"),
                ("a", "vale para qualquer instituto"),
            ],
            "viz": {
                "type": "checklist",
                "title": "antes de compartilhar qualquer pesquisa",
                "items": [
                    (
                        "A margem é da diferença ou de cada número?",
                        "Vantagem de 4 pontos com margem de 2 não é liderança estabelecida.",
                    ),
                    (
                        "Qual é o retrato do país usado para pesar?",
                        "Procure renda, escolaridade e o ano da fonte no registro do TSE.",
                    ),
                    (
                        "O que aparece no anexo e não na manchete?",
                        "Os cruzamentos costumam contar uma história mais rica que o topline.",
                    ),
                    (
                        "O instituto publicou o efeito de desenho?",
                        "Amostra por conglomerado tem incerteza maior que a fórmula da capa.",
                    ),
                    (
                        "Quais perguntas foram feitas e não publicadas?",
                        "Compare o questionário registrado com o relatório divulgado.",
                    ),
                    (
                        "A manchete usa verbo de causa?",
                        "Derrapa, dispara e reage costumam descrever ruído de uma onda.",
                    ),
                ],
            },
            "foot": [
                "cada pergunta tem resposta no PesqEle",
                "e as seis levam menos de dez minutos",
            ],
            "copy": [
                "Como ler uma manchete de pesquisa. Seis perguntas, todas com resposta pública.",
                "Um. A margem citada é de cada número ou da diferença entre dois? Vantagem de quatro pontos com margem de dois não é liderança estabelecida.",
                "Dois. Qual retrato do país foi usado para pesar as respostas? Procure renda e escolaridade no registro do TSE, e olhe o ano da fonte.",
                "Três. O que está no anexo e não virou manchete? Os cruzamentos quase sempre contam uma história mais rica que o topline.",
                "Quatro. O instituto publicou o efeito de desenho? Amostra colhida em conglomerados tem incerteza maior que a fórmula simples da capa.",
                "Cinco. Quais perguntas foram aplicadas e não publicadas? Basta comparar o questionário registrado com o relatório divulgado.",
                "Seis. A manchete usa verbo de causa? Derrapa, dispara e reage quase sempre descrevem oscilação dentro da margem.",
                "Seis perguntas, dez minutos, nenhuma conta difícil. É o suficiente para você parar de ser leitor de manchete e virar leitor de pesquisa.",
            ],
        },
        {
            "kind": "acao",
            "kicker": "o que exigir",
            "photo": f"{PHOTOS}/congresso.jpg",
            "pos": "center 45%",
            "tag": "transparência que custa quase nada",
            "metric": "5 itens",
            "title": "O que falta, e é barato entregar",
            "lead": "O Datafolha já publica muito mais do que a maioria. Os cinco itens abaixo custam pouco, não expõem nenhum entrevistado e encerrariam metade das discussões públicas sobre pesquisa no Brasil.",
            "chips": [
                ("c", "não expõe ninguém"),
                ("b", "custo baixo"),
                ("a", "vale para todos os institutos"),
            ],
            "viz": {
                "type": "checklist",
                "title": "cinco itens que resolveriam a discussão",
                "items": [
                    (
                        "O efeito de desenho de cada estimativa",
                        "Uma linha por tabela, e a margem passa a ser a verdadeira.",
                    ),
                    (
                        "A distribuição de pesos",
                        "Média, mínimo, máximo e dispersão, sem identificar ninguém.",
                    ),
                    (
                        "O ano e a tabela exata do benchmark",
                        "Qual PNAD, qual variável, qual universo, qual data de referência.",
                    ),
                    (
                        "As perguntas aplicadas e não publicadas",
                        "Ou o dado, ou a razão de não publicar.",
                    ),
                    (
                        "O cruzamento do voto de 1º com o de 2º turno",
                        "É a única forma de medir transferência sem estimar nada.",
                    ),
                ],
            },
            "foot": [
                "nenhum item exige microdado individual",
                "e todos cabem em duas páginas do relatório",
            ],
            "copy": [
                "O que exigir dos institutos. E é preciso começar reconhecendo: o Datafolha publica muito mais do que a maioria. Relatório completo, questionário, plano amostral, municípios e notas fiscais.",
                "Faltam cinco coisas. Nenhuma delas expõe qualquer entrevistado e todas cabem em duas páginas.",
                "O efeito de desenho de cada estimativa. Uma linha por tabela, e a margem publicada passa a ser a margem verdadeira.",
                "A distribuição dos pesos. Média, mínimo, máximo e dispersão. Isso mostra quanto trabalho o peso está fazendo, sem identificar ninguém.",
                "O ano e a tabela exata do benchmark de renda e escolaridade. Qual PNAD, qual variável, qual universo.",
                "As perguntas que foram aplicadas e não publicadas, ou a razão de não publicar.",
                "E o cruzamento do voto de primeiro turno com o de segundo, que é a única forma de medir transferência sem estimar nada.",
                "Isso não é ataque a instituto. É a diferença entre uma pesquisa que pode ser conferida e uma pesquisa em que é preciso acreditar.",
            ],
        },
        {
            "kind": "tese",
            "kicker": "o fecho",
            "photo": f"{PHOTOS}/eleicao-rua.jpg",
            "pos": "center 55%",
            "tag": "a conta está aberta, refaça",
            "metric": "refaça a conta",
            "title": "A verdade não estava escondida",
            "lead": "Nada nesta thread foi vazado, hackeado ou obtido em off. Tudo saiu de arquivos que qualquer pessoa baixa de graça, com uma média ponderada de três linhas. O que faltava não era acesso. Era conta.",
            "chips": [
                ("c", "51 páginas públicas"),
                ("b", "três linhas de conta"),
                ("a", "código aberto"),
            ],
            "viz": {
                "type": "bignum",
                "title": "o que foi preciso para chegar aqui",
                "rows": [
                    {
                        "value": "0",
                        "label": "documentos sigilosos usados",
                        "color": INK,
                    },
                    {"value": "3", "label": "linhas de média ponderada", "color": LIME},
                ],
            },
            "foot": [
                "dossiê completo em brasil.arvor.co",
                "scripts e dados abertos, sem paywall",
            ],
            "copy": [
                "O fecho.",
                "Nada nesta thread foi vazado, hackeado ou conseguido em off. Cada número saiu de um arquivo público, baixado de graça do sistema do TSE, e de uma média ponderada de três linhas que cabe numa planilha.",
                "O que faltava não era acesso. Era conta.",
                "É por isso que este trabalho é publicado com os scripts abertos e com as limitações declaradas antes das conclusões. Se algum número aqui estiver errado, ele é falsificável em vinte minutos, e é assim que tem de ser.",
                "A disputa que importa não é entre pessoas. É entre uma leitura pública que cabe numa manchete e uma leitura pública que exige dez minutos de aritmética. A primeira é barata de produzir e cara de desfazer. A segunda está ao alcance de qualquer eleitor que decida olhar.",
                "Quanto mais gente aprender a abrir o anexo, conferir a régua e refazer a média, menos poder tem quem depende de que ninguém confira.",
                "Se você chegou até aqui, já sabe mais sobre leitura de pesquisa do que a maior parte de quem comenta pesquisa. Use isso na próxima manchete que aparecer, inclusive nas nossas.",
                "O dossiê completo, com dezesseis capítulos, está em brasil.arvor.co. Os dados e os scripts também. Refaça a conta.",
            ],
        },
    ]


# --------------------------------------------------------------- pagina

CSS = """
*,*::before,*::after{box-sizing:border-box}
:root{
  --bg:#0c0d0b;--bg2:#131512;--bg3:#191c18;--ink:#f4f2ea;--ink2:#ddd8ca;
  --muted:#9a9789;--faint:#868376;--lime:#cfe63c;--cyan:#45c9c2;--amber:#f0a930;
  --green:#34b47e;--lula:#e0483a;--flavio:#3f8fd6;
  --line:rgb(244 242 234 / 13%);--line2:rgb(244 242 234 / 26%);
  --display:Fraunces,Georgia,serif;--sans:"IBM Plex Sans Condensed",Arial,sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,monospace;--wrap:min(1180px,calc(100% - 40px));
}
html{scroll-behavior:smooth;-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);
  font-size:17px;line-height:1.62;-webkit-font-smoothing:antialiased}
.wrap{width:var(--wrap);margin:0 auto}
a{color:var(--cyan)}
.top{padding:34px 0 8px;display:flex;flex-wrap:wrap;gap:14px;align-items:center;justify-content:space-between}
.brand-lockup{display:flex;align-items:center;gap:11px;font-family:var(--mono);
  font-size:.76rem;letter-spacing:.13em;text-transform:uppercase;color:var(--muted)}
.brand-lockup img{width:26px;height:26px;border-radius:4px}
.top .back{font-family:var(--mono);font-size:.74rem;letter-spacing:.1em;text-transform:uppercase;
  color:var(--lime);text-decoration:none;border:1px solid var(--line2);border-radius:999px;padding:7px 15px}
h1{font-family:var(--display);font-size:clamp(2.3rem,6.4vw,4.4rem);line-height:.98;
  letter-spacing:-.028em;margin:18px 0 0;font-weight:900}
h1 em{display:block;font-style:italic;color:var(--lime);font-weight:500}
.deck{max-width:76ch;color:var(--ink2);margin:20px 0 0;font-size:1.06rem}
.howto{margin:26px 0 0;border:1px solid var(--line);border-left:3px solid var(--cyan);
  border-radius:4px;background:var(--bg3);padding:18px 20px;color:var(--ink2);font-size:.95rem}
.howto b{color:var(--ink)}
.legend{display:flex;flex-wrap:wrap;gap:9px;margin:20px 0 0}
.legend span{font-family:var(--mono);font-size:.68rem;letter-spacing:.12em;text-transform:uppercase;
  border:1px solid currentcolor;border-radius:999px;padding:5px 11px}
.rail{position:sticky;top:0;z-index:30;margin:30px 0 0;padding:11px 0;
  background:rgb(12 13 11 / 93%);backdrop-filter:blur(10px);border-top:1px solid var(--line);
  border-bottom:1px solid var(--line)}
.rail .wrap{display:flex;gap:5px;align-items:center;overflow-x:auto;scrollbar-width:none}
.rail .wrap::-webkit-scrollbar{display:none}
.rail b{font-family:var(--mono);font-size:.68rem;letter-spacing:.13em;text-transform:uppercase;
  color:var(--faint);margin-right:8px;white-space:nowrap}
.rail a{width:26px;height:26px;flex:0 0 auto;display:grid;place-items:center;border-radius:5px;
  border:1px solid var(--line);color:var(--muted);text-decoration:none;
  font-family:var(--mono);font-size:.72rem}
.rail a:hover{color:var(--ink);border-color:var(--line2)}
.post{margin:52px 0 0;scroll-margin-top:64px}
.post-label{font-family:var(--mono);font-size:.72rem;letter-spacing:.13em;text-transform:uppercase;
  color:var(--faint);margin-bottom:11px}
.post-label b{color:var(--ink)}
.card{position:relative;aspect-ratio:16/9;border:1px solid var(--line2);border-radius:8px;
  overflow:hidden;background:#0a0b09;container-type:inline-size;display:flex;flex-direction:column}
.card::before{content:"";position:absolute;inset:0;background-image:var(--photo);
  background-size:cover;background-position:var(--pos,center);opacity:.30}
.card::after{content:"";position:absolute;inset:0;
  background:linear-gradient(102deg,rgb(10 11 9 / 96%) 0 46%,rgb(10 11 9 / 78%) 68%,rgb(10 11 9 / 88%) 100%)}
.card>*{position:relative;z-index:2}
.stripe{position:absolute;inset:0 0 auto 0;height:4px;z-index:3;background:var(--accent)}
.card-head{display:flex;align-items:center;justify-content:space-between;gap:14px;
  padding:2.2cqw 2.6cqw 0}
.chead{display:flex;align-items:center;gap:9px}
.chead img{width:2.6cqw;height:2.6cqw;min-width:22px;min-height:22px;border-radius:4px}
.chead b{display:block;font-size:1.35cqw;line-height:1.2}
.chead span{display:block;font-family:var(--mono);font-size:1.05cqw;color:var(--muted)}
.pno{font-family:var(--mono);font-size:1.15cqw;color:var(--accent);letter-spacing:.1em}
.card-body{flex:1;min-height:0;display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.18fr);
  gap:2.4cqw;padding:1.6cqw 2.6cqw;align-items:stretch}
.card-body>.said{display:flex;flex-direction:column;justify-content:center;min-width:0}
.lead-tag{display:inline-block;font-family:var(--mono);font-size:1.02cqw;letter-spacing:.09em;
  text-transform:uppercase;color:var(--accent);border:1px solid currentcolor;
  border-radius:999px;padding:.45cqw 1cqw}
.metric{font-family:var(--display);font-weight:900;font-size:3.5cqw;line-height:.98;
  letter-spacing:-.03em;color:var(--accent);margin:1.1cqw 0 .2cqw}
.card h2{font-family:var(--display);font-size:2.05cqw;line-height:1.1;margin:0 0 .9cqw;font-weight:700}
.card .t{font-size:1.28cqw;line-height:1.5;color:var(--ink2);margin:0}
.kchips{display:flex;flex-wrap:wrap;gap:.6cqw;margin-top:1.2cqw}
.kchip{font-family:var(--mono);font-size:1cqw;border:1px solid currentcolor;border-radius:999px;
  padding:.4cqw .85cqw;white-space:nowrap}
.kchip.l{color:var(--lula)}.kchip.b{color:var(--flavio)}.kchip.a{color:var(--amber)}
.kchip.c{color:var(--cyan)}.kchip.g{color:var(--green)}
.viz{border:1px solid var(--line);border-radius:6px;background:rgb(244 242 234 / 5%);padding:1.6cqw;
  min-width:0;display:flex;align-items:center;justify-content:center}
.viz svg{width:100%;height:auto;display:block}
.card-foot{flex:0 0 auto;display:flex;justify-content:space-between;gap:12px;
  padding:1.3cqw 2.6cqw;font-family:var(--mono);font-size:1cqw;color:var(--faint);
  border-top:1px solid var(--line)}
.copy{margin:14px 0 0;border:1px solid var(--line);border-radius:6px;background:var(--bg2);
  padding:20px 22px;font-family:var(--mono);font-size:.9rem;line-height:1.72;color:var(--ink2);
  white-space:pre-wrap;position:relative}
.cc{position:absolute;top:12px;right:18px;font-size:.7rem;color:var(--faint);letter-spacing:.09em}
.copy-btn{margin-top:10px;font-family:var(--mono);font-size:.74rem;letter-spacing:.11em;
  text-transform:uppercase;background:transparent;color:var(--lime);border:1px solid var(--line2);
  border-radius:999px;padding:9px 18px;cursor:pointer}
.copy-btn:hover{border-color:var(--lime)}
footer{margin:72px 0 0;border-top:1px solid var(--line);padding:34px 0 60px;color:var(--muted);font-size:.92rem}
footer h2{font-family:var(--display);font-size:1.6rem;margin:0 0 10px;color:var(--ink)}
footer p{max-width:78ch}
/* No celular o card 16:9 fica pequeno demais para ler. Ele deixa de ser
   proporcional e passa a empilhar, com tipografia em pixel. O card 16:9 para
   anexar continua exato na largura de trabalho, acima de 720px. */
@media (width <= 720px){
  body{font-size:16px}
  .card{aspect-ratio:auto}
  .card-head{padding:16px 18px 0}
  .chead img{width:26px;height:26px}
  .chead b{font-size:.92rem}
  .chead span{font-size:.72rem}
  .pno{font-size:.8rem}
  .card-body{grid-template-columns:minmax(0,1fr);gap:16px;padding:16px 18px 20px}
  .lead-tag{font-size:.68rem;padding:5px 11px}
  .metric{font-size:2.5rem;margin:12px 0 4px}
  .card h2{font-size:1.5rem;margin-bottom:9px}
  .card .t{font-size:.98rem;line-height:1.55}
  .kchips{gap:7px;margin-top:13px}
  .kchip{font-size:.7rem;padding:4px 9px}
  .viz{padding:14px}
  .card-foot{padding:12px 18px;font-size:.68rem;flex-direction:column;gap:4px}
  .copy{padding:16px 15px;font-size:.84rem}
  .cc{position:static;display:block;text-align:right;margin-bottom:8px}
}
"""

JS = """
function cp(button){
  const node = button.previousElementSibling;
  const text = node.getAttribute('data-copy') || node.innerText;
  navigator.clipboard.writeText(text).then(() => {
    const original = button.textContent;
    button.textContent = 'copiado';
    setTimeout(() => { button.textContent = original; }, 1600);
  });
}
"""


def render_card(index, total, card):
    accent, kind_label = KIND[card["kind"]]
    viz = RENDER[card["viz"]["type"]](card["viz"])
    chips = "".join(
        f'<span class="kchip {tone}">{html.escape(label)}</span>'
        for tone, label in card["chips"]
    )
    body = "\n\n".join(card["copy"])
    style = f'--accent:{accent};--photo:url(\'{card["photo"]}\')'
    if card.get("pos"):
        style += f';--pos:{card["pos"]}'
    return f"""
<section class="post" id="p{index}">
  <div class="post-label">Post {index}/{total} · {html.escape(kind_label)} · <b>{html.escape(card["kicker"])}</b></div>
  <div class="card" style="{style}">
    <span class="stripe" aria-hidden="true"></span>
    <div class="card-head">
      <div class="chead"><img src="img/arvor_logo.png" alt="Arvor"><div><b>Arvor Intelligence</b><span>@leonardodias · perícia eleitoral</span></div></div>
      <div class="pno">{index}/{total}</div>
    </div>
    <div class="card-body">
      <div class="said">
        <span class="lead-tag">{html.escape(card["tag"])}</span>
        <p class="metric">{html.escape(card["metric"])}</p>
        <h2>{html.escape(card["title"])}</h2>
        <p class="t">{html.escape(card["lead"])}</p>
        <div class="kchips">{chips}</div>
      </div>
      <div class="viz">{viz}</div>
    </div>
    <div class="card-foot"><span>{html.escape(card["foot"][0])}</span><span>{html.escape(card["foot"][1])}</span></div>
  </div>
  <div class="copy" data-copy="{html.escape(body)}"><span class="cc">{len(body)} chars</span>{html.escape(body)}</div>
  <button class="copy-btn" onclick="cp(this)">Copiar texto</button>
</section>"""


def main() -> None:
    renda = json.loads((ANALYSIS / "historico_renda.json").read_text(encoding="utf-8"))
    fundo = json.loads((ANALYSIS / "aprofundamento.json").read_text(encoding="utf-8"))
    audit = json.loads((ANALYSIS / "audit.json").read_text(encoding="utf-8"))
    cards = build_cards(renda, fundo, audit)
    total = len(cards)

    rail = "".join(f'<a href="#p{i}">{i}</a>' for i in range(1, total + 1))
    legend = "".join(
        f'<span style="color:{color}">{label}</span>' for color, label in KIND.values()
    )
    posts = "".join(
        render_card(i, total, card) for i, card in enumerate(cards, start=1)
    )

    page = f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Datafolha 08/2026: a thread que ensina a ler a pesquisa · Arvor</title>
<meta name="description" content="Thread educativa da auditoria Datafolha BR-04496/2026: o que é amostra, margem, estratificação e ponderação, a reponderação por renda refeita passo a passo com a PNAD do IBGE, e a série de quatro ondas que muda a narrativa da eleição.">
<link rel="canonical" href="https://brasil.arvor.co/datafolha_082026_thread.html">
<link rel="icon" href="favicon.ico" sizes="any">
<link rel="icon" href="img/favicon.svg" type="image/svg+xml">
<meta name="theme-color" content="#0c0d0b">
<meta property="og:type" content="article">
<meta property="og:locale" content="pt_BR">
<meta property="og:site_name" content="Arvor Intelligence">
<meta property="og:title" content="A thread que ensina a ler uma pesquisa eleitoral">
<meta property="og:description" content="Dezoito cards: margem da diferença, estratificação, ponderação e a conta de três linhas que leva o segundo turno de 47×43 para 44,2×46,0.">
<meta property="og:url" content="https://brasil.arvor.co/datafolha_082026_thread.html">
<meta property="og:image" content="https://brasil.arvor.co/img/og/datafolha_082026_thread.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@leonardodias">
<meta name="twitter:title" content="A thread que ensina a ler uma pesquisa eleitoral">
<meta name="twitter:description" content="Do que é uma amostra até a média ponderada que troca o sinal do segundo turno. Dezoito cards com o texto pronto.">
<meta name="twitter:image" content="https://brasil.arvor.co/img/og/datafolha_082026_thread.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,500;0,9..144,700;0,9..144,900;1,9..144,500&amp;family=IBM+Plex+Mono:wght@400;600&amp;family=IBM+Plex+Sans+Condensed:wght@400;600;700&amp;display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
<header class="top">
  <div class="brand-lockup"><img src="img/arvor_logo.png" alt="Arvor"><span>Arvor Intelligence · perícia eleitoral</span></div>
  <a class="back" href="datafolha_082026.html">Ir para o dossiê completo</a>
</header>
<h1>Uma pesquisa não mente.<em>Ela depende de uma régua.</em></h1>
<p class="deck">Thread da auditoria do <b>Datafolha de 18 e 19 de agosto de 2026</b>, registro TSE BR-04496/2026, 2.058 entrevistas. Dezoito cards que ensinam o suficiente de estatística para você ler qualquer pesquisa sozinho, e que refazem, com os números na tela, a conta que leva o segundo turno publicado de <b>47 × 43</b> para <b>44,2 × 46,0</b> quando a distribuição de renda vem do IBGE.</p>
<div class="howto"><b>Como usar.</b> Cada bloco traz o card 16:9 para anexar e, logo abaixo, o texto exato do post com a contagem de caracteres. O botão copia sem formatação. Aula ensina o conceito. Fato publicado vem com a página do relatório. A conta vem com a fórmula aberta e o resultado conferível.</div>
<div class="legend">{legend}</div>
</div>
<nav class="rail" aria-label="Ir para o post"><div class="wrap"><b>18 posts</b>{rail}</div></nav>
<div class="wrap">
{posts}
</div>
<footer><div class="wrap">
  <h2>Refaça a conta</h2>
  <p>Todos os números desta thread saem de arquivos públicos do sistema PesqEle do Tribunal Superior Eleitoral e dos microdados da PNAD Contínua do IBGE. O dossiê completo, com dezesseis capítulos, está em <a href="datafolha_082026.html">brasil.arvor.co/datafolha_082026.html</a>, e o retrato do país que serve de régua está em <a href="pnad.html">O Brasil em Números</a>.</p>
  <p>Reponderar uma margem publicada é análise de sensibilidade: mostra de qual régua o resultado depende, não identifica o resultado verdadeiro do eleitorado. Sem microdados, pesos individuais e efeito de desenho, nenhum exercício aqui substitui a apuração oficial nem permite acusar fabricação de dados.</p>
  <p>Fotografias de bancos livres do Wikimedia Commons, com autoria e licença creditadas no dossiê. Nenhum instituto, veículo, partido ou campanha financiou ou revisou esta thread.</p>
</div></footer>
<script>{JS}</script>
</body>
</html>
"""
    OUTPUT.write_text(page, encoding="utf-8")
    print(f"OK: {OUTPUT.relative_to(ROOT)}  ({total} posts, {len(page)} bytes)")
    for index, card in enumerate(cards, start=1):
        size = len("\n\n".join(card["copy"]))
        flag = "  <-- longo" if size > 2000 else ""
        print(f"  {index:>2}. {card['kicker']:<24} {size:>5} chars{flag}")


if __name__ == "__main__":
    main()
