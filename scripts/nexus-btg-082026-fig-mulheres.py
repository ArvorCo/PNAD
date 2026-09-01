#!/usr/bin/env python3
"""Figuras dos capítulos de mulheres e de regiões do dossiê BTG/Nexus de 03/08/2026.

Seis peças, na ordem em que o argumento se fecha:
  mulheres_cenarios  o achado 54-54-54-54: entre mulheres, Lula não se move ao
                     trocar de adversário. O que cresce é o branco e nulo.
  mulheres_tesoura   potencial de voto contra rejeição, espelhado. As séries se
                     cruzam entre mulheres e homens, e a folga declarada de
                     Flávio entre mulheres é de dois pontos.
  mulheres_material  o país material: seis indicadores, mulheres contra homens,
                     cada par na sua própria escala, com a razão ao lado.
  mulheres_paradoxo  o paradoxo de Simpson da renda: a razão agregada é maior do
                     que a razão dentro de qualquer nível de escolaridade.
  mulheres_regiao    a geografia da assimetria, com o degrau entre Sudeste e
                     Norte marcado dentro da figura.
  regioes_desloc     o deslocamento regional entre as duas ondas, com o Nordeste
                     destacado como o maior movimento da rodada.

Voto vem do relatório BTG/Nexus; população vem das duas bases de auditoria em
docs/assets. A ponta translúcida de cada barra da PNAD é o intervalo de 95% por
réplicas. A única trama de 45 graus da série marca a folga declarada de Flávio,
que é comparação entre duas perguntas diferentes, não medição.
"""

from __future__ import annotations

import json
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from svgkit import (  # noqa: E402
    AMBER,
    BLUE,
    CORAL,
    FULL,
    GRAY,
    INK,
    LIME,
    LINE,
    MUTED,
    NAVY,
    OLIVE,
    PAPER,
    RED,
    SKY,
    WHITE,
    Canvas,
    br,
    signed,
    write_fragments,
)

DATA = ROOT / "docs/assets/nexus_btg_082026_1_data.json"
MULHERES = ROOT / "docs/assets/nexus_btg_082026_1_mulheres.json"
OUTPUT = ROOT / "docs/assets/figuras/nexus_082026_mulheres.json"

# Nome longo para a coluna da esquerda, nome curto para caber dentro da barra.
ADVERSARIO = {
    "Lula x Flávio Bolsonaro": ("Flávio Bolsonaro", "Flávio"),
    "Lula x Romeu Zema": ("Romeu Zema", "Zema"),
    "Lula x Ronaldo Caiado": ("Ronaldo Caiado", "Caiado"),
    "Lula x Renan Santos": ("Renan Santos", "Renan"),
}

# Recorte regional publicado, transcrito no script de auditoria a partir das
# pp. 29 e 53 do relatório de 03/08. Ordem: Norte/Centro-Oeste, Nordeste,
# Sudeste, Sul, a mesma do perfil publicado (16, 28, 42, 14).
REGIOES = ["Norte/Centro-Oeste", "Nordeste", "Sudeste", "Sul"]
AGOSTO_1T = {
    "Norte/Centro-Oeste": (40, 34),
    "Nordeste": (48, 34),
    "Sudeste": (42, 35),
    "Sul": (27, 51),
}
AGOSTO_2T = {
    "Norte/Centro-Oeste": (44, 48),
    "Nordeste": (52, 39),
    "Sudeste": (47, 42),
    "Sul": (32, 57),
}
# Da onda de 27/07 só o Nordeste tem abertura regional transcrita nesta base.
JULHO_1T = {"Nordeste": (57, 24)}
JULHO_2T = {"Nordeste": (62, 30)}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def half_up(value: float, casas: int) -> float:
    """Arredonda meio para cima, como a leitura humana espera, e não meio para par."""
    passo = Decimal(1).scaleb(-casas)
    return float(Decimal(str(value)).quantize(passo, rounding=ROUND_HALF_UP))


def num(value: float, casas: int = 1) -> str:
    return br(half_up(value, casas), casas)


def barra_ic(
    canvas: Canvas,
    x0: float,
    y: float,
    altura: float,
    comprimento: float,
    meia: float,
    cor: str,
) -> float:
    """Barra com ponta translúcida: o intervalo de 95% desenhado na própria marca.

    Devolve onde o rótulo pode começar sem encostar no intervalo.
    """
    fim = x0 + comprimento
    if meia < 1.0:
        canvas.rect(x0, y, comprimento, altura, cor, rx=3)
        return fim
    canvas.rect(x0, y, comprimento - meia, altura, cor, rx=3)
    canvas.rect(fim - meia, y, 2 * meia, altura, cor, opacity=0.42)
    canvas.line(fim, y + 2, fim, y + altura - 2, stroke=cor, width=2)
    return fim + meia


def whisker(
    canvas: Canvas, x: float, y: float, meia: float, cor: str, cap: float = 6.0
) -> float:
    """Barra fina de intervalo de confiança sobre a marca de um pirulito."""
    if meia < 1.0:
        return x
    canvas.line(x - meia, y, x + meia, y, stroke=cor, width=2.2, opacity=0.55)
    canvas.line(
        x - meia, y - cap, x - meia, y + cap, stroke=cor, width=2.2, opacity=0.55
    )
    canvas.line(
        x + meia, y - cap, x + meia, y + cap, stroke=cor, width=2.2, opacity=0.55
    )
    return x + meia


def swatch(
    canvas: Canvas, x: float, y: float, cor: str, texto: str, fill: str, size: int = 14
) -> float:
    """Item de legenda: quadrado, rótulo, e devolve onde o próximo item começa."""
    canvas.rect(x, y - 11, 13, 13, cor, rx=2)
    canvas.text(x + 20, y, texto, size=size, fill=fill)
    return x + 20 + len(texto) * size * 0.56 + 22


# --------------------------------------------------------------------------- 1


def cenarios(ref: dict) -> str:
    """Quatro cenários de 2º turno entre mulheres, com Lula travado em 54."""
    canvas = Canvas(
        FULL,
        430,
        aria="Segundo turno entre mulheres nos quatro cenários: Lula fica em 54 em todos",
    )
    canvas.rect(0, 0, FULL, 430, NAVY)

    x0, esc = 270.0, 8.4
    canvas.label(40, 36, "2º turno entre mulheres · BTG/Nexus 03/08/2026", fill=GRAY)

    cursor = 706.0
    for cor, texto in (
        (RED, "Lula"),
        (SKY, "adversário"),
        (LIME, "branco e nulo"),
        (GRAY, "não sabe"),
    ):
        cursor = swatch(canvas, cursor, 36, cor, texto, WHITE)

    canvas.label(40, 88, "Lula contra", fill=GRAY)
    canvas.label(x0, 88, "% de intenção de voto no 2º turno", fill=GRAY)

    guia = x0 + 54 * esc
    canvas.line(
        guia,
        96,
        guia,
        358,
        stroke=WHITE,
        width=2.6,
        stroke_dasharray="7 5",
        opacity=0.9,
    )
    canvas.number(guia + 12, 84, "54", size=30, fill=WHITE)
    canvas.text(guia + 56, 84, "nos quatro cenários", size=15, fill=GRAY)

    topo = 104
    for indice, (chave, bloco) in enumerate(ref["runoff_cenarios"].items()):
        y = topo + indice * 72
        longo, curto = ADVERSARIO[chave]
        mulher, homem = bloco["mulheres"], bloco["homens"]

        canvas.text(40, y + 24, longo, size=17, fill=WHITE, weight="600")
        canvas.label(40, y + 44, f"p. {bloco['pagina']}", fill=MUTED, size=13)

        anda = x0
        for valor, cor, nome in zip(
            mulher, [RED, SKY, LIME, GRAY], ["Lula", curto, "B/N", "NS"], strict=False
        ):
            largura = valor * esc
            canvas.rect(anda, y, largura, 38, cor)
            centro = anda + largura / 2
            if cor == RED:
                canvas.text(
                    centro,
                    y + 26,
                    str(valor),
                    size=21,
                    fill=WHITE,
                    weight="700",
                    anchor="middle",
                )
            elif cor == SKY:
                canvas.text(
                    centro,
                    y + 25,
                    f"{nome} {valor}",
                    size=19,
                    fill=INK,
                    weight="700",
                    anchor="middle",
                )
            else:
                canvas.text(
                    centro,
                    y + 25,
                    str(valor),
                    size=17 if largura > 40 else 15,
                    fill=INK,
                    weight="700",
                    anchor="middle",
                )
            anda += largura

        canvas.rect(x0, y + 44, homem[0] * esc, 9, RED, opacity=0.45)
        canvas.text(
            x0 + homem[0] * esc + 10, y + 53, f"homens {homem[0]}", size=14, fill=GRAY
        )

    canvas.line(40, 388, 1140, 388, stroke=WHITE, width=1, opacity=0.18)
    canvas.text(
        40,
        412,
        "A linha fina é Lula entre homens. Ele não se mexe ao trocar de adversário: o que "
        "cresce é o branco e nulo, de 7 para 13. Margem por sexo: ±3, p. 114.",
        size=15,
        fill=GRAY,
    )
    return canvas.render()


# --------------------------------------------------------------------------- 2


def tesoura(ref: dict) -> str:
    """Potencial de voto contra rejeição, espelhado, com as séries se cruzando."""
    canvas = Canvas(
        FULL,
        400,
        aria="Potencial de voto e rejeição de Lula e Flávio entre mulheres e homens",
    )
    canvas.rect(0, 0, FULL, 400, WHITE)

    esquerda, direita, esc = 520.0, 660.0, 8.0
    potencial, rejeicao = ref["potencial_de_voto"], ref["rejeicao"]
    ja_recebe = ref["runoff_cenarios"]["Lula x Flávio Bolsonaro"]["mulheres"][1]

    canvas.text(
        esquerda - 14,
        46,
        "POTENCIAL DE VOTO",
        size=17,
        fill=MUTED,
        weight="700",
        anchor="end",
    )
    canvas.label(esquerda - 14, 66, f"% · p. {potencial['pagina']}", anchor="end")
    canvas.text(direita + 14, 46, "REJEIÇÃO", size=17, fill=MUTED, weight="700")
    canvas.label(direita + 14, 66, f"% · p. {rejeicao['pagina']}", fill=MUTED)

    linhas = {
        "mulheres": {"Lula": 130, "Flávio": 170},
        "homens": {"Lula": 270, "Flávio": 310},
    }
    tom = {
        ("mulheres", "Lula"): RED,
        ("homens", "Lula"): CORAL,
        ("mulheres", "Flávio"): BLUE,
        ("homens", "Flávio"): SKY,
    }

    for grupo, titulo_y in (("mulheres", 100), ("homens", 240)):
        canvas.number(590, titulo_y, grupo.upper(), size=20, fill=INK, anchor="middle")
        for nome, y in linhas[grupo].items():
            canvas.text(
                590,
                y + 6,
                nome,
                size=16,
                fill=RED if nome == "Lula" else BLUE,
                weight="700",
                anchor="middle",
            )
            cor = tom[(grupo, nome)]
            pot, rej = potencial[grupo][nome], rejeicao[grupo][nome]
            canvas.rect(esquerda - pot * esc, y - 15, pot * esc, 30, cor, rx=3)
            canvas.text(
                esquerda - 12,
                y + 7,
                str(pot),
                size=19,
                fill=WHITE,
                weight="700",
                anchor="end",
            )
            canvas.rect(direita, y - 15, rej * esc, 30, cor, rx=3)
            canvas.text(
                direita + 12, y + 7, str(rej), size=19, fill=WHITE, weight="700"
            )

    for nome in ("Lula", "Flávio"):
        cor = RED if nome == "Lula" else BLUE
        y1, y2 = linhas["mulheres"][nome], linhas["homens"][nome]
        canvas.line(
            esquerda - potencial["mulheres"][nome] * esc,
            y1,
            esquerda - potencial["homens"][nome] * esc,
            y2,
            stroke=cor,
            width=2.6,
            opacity=0.5,
        )
        canvas.line(
            direita + rejeicao["mulheres"][nome] * esc,
            y1,
            direita + rejeicao["homens"][nome] * esc,
            y2,
            stroke=cor,
            width=2.6,
            opacity=0.5,
        )

    trama = canvas.hatch("folga_flavio", INK, 0.18)
    y_flavio = linhas["mulheres"]["Flávio"]
    x_pot = esquerda - potencial["mulheres"]["Flávio"] * esc
    x_ja = esquerda - ja_recebe * esc
    canvas.rect(
        x_pot, y_flavio - 21, x_ja - x_pot, 42, trama, stroke=INK, stroke_width=1.2
    )
    canvas.line(x_ja, y_flavio - 21, x_ja, y_flavio + 21, stroke=INK, width=2.5)
    canvas.text(
        x_ja + 12,
        y_flavio + 36,
        f"{ja_recebe} = o que ele já recebe no 2º turno",
        size=14,
        fill=INK,
    )

    canvas.rect(40, 330, 1100, 62, PAPER, rx=6)
    canvas.rect(56, 349, 14, 14, trama, stroke=INK, stroke_width=1)
    canvas.text(
        82,
        361,
        f"Flávio já recebe {ja_recebe}% entre mulheres no 2º turno e declara "
        f"{potencial['mulheres']['Flávio']}% de potencial: sobram 2 pontos de folga.",
        size=17,
        fill=INK,
        weight="700",
    )
    canvas.text(
        82,
        383,
        f"A rejeição a ele entre mulheres é {rejeicao['mulheres']['Flávio']}%, contra "
        f"{rejeicao['mulheres']['Lula']}% de rejeição a Lula. Entre homens a ordem se inverte.",
        size=16,
        fill=MUTED,
    )
    return canvas.render()


# --------------------------------------------------------------------------- 3


def material(base: dict) -> str:
    """Seis indicadores materiais, mulheres contra homens, cada par na sua escala."""
    renda = base["renda_do_trabalho"]["por_sexo"]
    trabalho = base["forca_de_trabalho"]["por_sexo"]
    escola = base["escolaridade"]["por_sexo"]
    bolsa = base["bolsa_familia"]["por_sexo"]
    chefia = base["chefia_domiciliar"]["por_sexo_do_responsavel"]

    def par(bloco_m: dict, bloco_h: dict, campo: str) -> tuple:
        return (bloco_m[campo], bloco_h[campo])

    itens = [
        (
            "Renda média do trabalho",
            "R$ por mês, abr/2026",
            renda["mulheres"]["media_brl"],
            renda["homens"]["media_brl"],
            "reais",
            "menos",
            base["renda_do_trabalho"]["razao_media_mulher_homem"]["razao"],
        ),
        (
            "Participação na força de trabalho",
            "% das pessoas de 16+",
            *par(trabalho["mulheres"], trabalho["homens"], "taxa_de_participacao"),
            "pct",
            "menos",
            None,
        ),
        (
            "Ensino superior",
            "% das pessoas de 16+",
            escola["mulheres"]["distribuicao"]["Superior"],
            escola["homens"]["distribuicao"]["Superior"],
            "pct",
            "mais",
            None,
        ),
        (
            "Bolsa Família em nome próprio",
            "% das pessoas de 16+",
            *par(bolsa["mulheres"], bolsa["homens"], "recebe_pessoalmente"),
            "pct",
            "concentra",
            None,
        ),
        (
            "Chefia do domicílio",
            "% dos domicílios",
            *par(chefia["mulheres"], chefia["homens"], "chefia_pct"),
            "pct",
            "mais",
            None,
        ),
        (
            "Trabalho doméstico",
            "% dos ocupados",
            *par(trabalho["mulheres"], trabalho["homens"], "trabalho_domestico"),
            "pct",
            "concentra",
            None,
        ),
    ]
    cor_da_razao = {"menos": AMBER, "mais": OLIVE, "concentra": INK}
    tag_da_razao = {
        "menos": "abaixo deles",
        "mais": "acima deles",
        "concentra": "quase só ela",
    }

    canvas = Canvas(
        FULL,
        480,
        aria="Seis indicadores materiais de mulheres e homens de 16 anos ou mais",
    )
    canvas.rect(0, 0, FULL, 480, WHITE)
    canvas.label(
        40,
        36,
        "PNAD Contínua · trimestral 1ºT/2026 (renda, trabalho, escolaridade) "
        "e anual 2025 1ª visita (Bolsa Família, chefia)",
    )
    cursor = 40.0
    for cor, texto in ((RED, "mulheres"), (NAVY, "homens")):
        cursor = swatch(canvas, cursor, 62, cor, texto, INK, size=15)
    canvas.label(
        cursor + 4, 62, "ponta translúcida = intervalo de 95% por réplicas", fill=GRAY
    )

    colunas, linhas_y, largura_max = [40.0, 620.0], [84.0, 202.0, 320.0], 230.0

    for indice, item in enumerate(itens):
        titulo, unidade, bloco_m, bloco_h, tipo, sentido, razao_json = item
        valor_m = bloco_m.get("valor", bloco_m.get("pct"))
        valor_h = bloco_h.get("valor", bloco_h.get("pct"))
        razao = razao_json if razao_json is not None else valor_m / valor_h
        cx, cy = colunas[indice % 2], linhas_y[indice // 2]

        canvas.rect(cx, cy, 520, 106, PAPER if sentido == "mais" else WHITE, rx=8)
        canvas.rect(cx, cy, 520, 106, "none", rx=8, stroke=LINE, stroke_width=1)
        canvas.text(cx + 16, cy + 26, titulo, size=17, fill=INK, weight="700")
        canvas.label(cx + 504, cy + 26, unidade, anchor="end", fill=GRAY)
        canvas.line(cx + 372, cy + 18, cx + 372, cy + 92, stroke=LINE, width=1)

        maior = max(valor_m, valor_h)
        for ordem, (rotulo, valor, moe, cor) in enumerate(
            (
                ("mulheres", valor_m, bloco_m["moe"], RED),
                ("homens", valor_h, bloco_h["moe"], NAVY),
            )
        ):
            y = cy + 42 + ordem * 32
            comprimento = largura_max * valor / maior
            canvas.text(cx + 100, y + 17, rotulo, size=14, fill=MUTED, anchor="end")
            ponta = barra_ic(
                canvas, cx + 110, y, 24, comprimento, largura_max * moe / maior, cor
            )
            texto = ("R$ " + num(valor, 2)) if tipo == "reais" else num(valor, 1) + "%"
            if comprimento > 110:
                canvas.text(
                    cx + 110 + comprimento - 12,
                    y + 17,
                    texto,
                    size=17,
                    fill=WHITE,
                    weight="700",
                    anchor="end",
                )
            else:
                canvas.text(ponta + 10, y + 17, texto, size=17, fill=INK, weight="700")

        canvas.label(
            cx + 504,
            cy + 46,
            tag_da_razao[sentido],
            anchor="end",
            fill=cor_da_razao[sentido],
        )
        canvas.number(
            cx + 504,
            cy + 78,
            num(razao, 2) + "×",
            size=32,
            fill=cor_da_razao[sentido],
            anchor="end",
        )
        canvas.label(cx + 504, cy + 96, "mulher / homem", anchor="end", fill=GRAY)

    canvas.text(
        40,
        462,
        "Ela é mais escolarizada e chefia mais domicílios. Ainda assim, sua renda média do "
        f"trabalho é {num(100 - 100 * itens[0][6], 1)}% menor que a deles.",
        size=17,
        fill=INK,
        weight="600",
    )
    return canvas.render()


# --------------------------------------------------------------------------- 4


def paradoxo(base: dict) -> str:
    """Razão agregada acima da razão dentro de todo nível de escolaridade."""
    renda = base["renda_do_trabalho"]
    agregado = renda["razao_media_mulher_homem"]
    niveis = renda["por_escolaridade"]

    canvas = Canvas(
        FULL,
        380,
        aria="Razão de renda mulher sobre homem: agregada e dentro de cada nível de escolaridade",
    )
    canvas.rect(0, 0, FULL, 380, WHITE)
    canvas.line(725, 28, 725, 352, stroke=LINE, width=1)

    x_min, x_max, px_min, px_max = 0.60, 0.85, 90.0, 690.0
    escala = (px_max - px_min) / (x_max - x_min)

    def px(valor: float) -> float:
        return px_min + (valor - x_min) * escala

    canvas.label(40, 36, "razão entre a renda média do trabalho: mulher / homem")
    canvas.line(px_min, 84, px_max, 84, stroke=LINE, width=1.5)
    for passo in range(6):
        marca = x_min + passo * 0.05
        canvas.line(px(marca), 84, px(marca), 90, stroke=GRAY, width=1.5)
        canvas.label(px(marca), 74, num(marca, 2), anchor="middle")

    canvas.line(
        px(agregado["razao"]),
        96,
        px(agregado["razao"]),
        336,
        stroke=RED,
        width=1.6,
        opacity=0.35,
    )
    canvas.text(
        px_min,
        118,
        "Agregado: todas as ocupadas com rendimento",
        size=16,
        fill=INK,
        weight="700",
    )
    canvas.line(px_min, 142, px(agregado["razao"]), 142, stroke=RED, width=4)
    canvas.circle(px(agregado["razao"]), 142, 11, RED)
    fim = whisker(
        canvas, px(agregado["razao"]), 142, agregado["moe"] * escala, RED, cap=8
    )
    canvas.text(
        fim + 16, 150, num(agregado["razao"], 3), size=26, fill=RED, weight="700"
    )

    canvas.line(px_min, 166, px_max, 166, stroke=LINE, width=1)
    canvas.label(px_min, 188, "dentro de cada nível de escolaridade:", fill=MUTED)

    for indice, nome in enumerate(("Fundamental", "Médio", "Superior")):
        bloco = niveis[nome]["razao_mulher_homem"]
        y = 226 + indice * 46
        canvas.text(
            px_min, y - 19, f"Só entre quem tem {nome.lower()}", size=15, fill=INK
        )
        canvas.label(
            px_max,
            y - 19,
            f"R$ {num(niveis[nome]['mulheres']['valor'], 0)} × "
            f"R$ {num(niveis[nome]['homens']['valor'], 0)}",
            anchor="end",
        )
        canvas.line(px_min, y, px(bloco["razao"]), y, stroke=NAVY, width=3.5)
        canvas.circle(px(bloco["razao"]), y, 9, NAVY)
        fim = whisker(canvas, px(bloco["razao"]), y, bloco["moe"] * escala, NAVY, cap=7)
        canvas.text(
            fim + 14, y + 7, num(bloco["razao"], 3), size=20, fill=NAVY, weight="700"
        )

    canvas.text(
        px_min,
        366,
        "O agregado sobe por composição, não por paridade.",
        size=17,
        fill=RED,
        weight="700",
    )

    canvas.label(750, 36, "composição por escolaridade das ocupadas (%)")
    cores = {"Fundamental": LINE, "Médio": GRAY, "Superior": NAVY}
    letra = {"Fundamental": INK, "Médio": INK, "Superior": WHITE}
    for ordem, sexo in enumerate(("mulheres", "homens")):
        y = 96 + ordem * 80
        canvas.text(
            760, y - 10, sexo, size=16, fill=RED if ordem == 0 else NAVY, weight="700"
        )
        anda = 760.0
        for nome in ("Fundamental", "Médio", "Superior"):
            valor = niveis[nome]["composicao_pct"][sexo]["pct"]
            largura = 370 * valor / 100
            canvas.rect(anda, y, largura, 36, cores[nome])
            canvas.text(
                anda + largura / 2,
                y + 24,
                num(valor, 1),
                size=16,
                fill=letra[nome],
                weight="700",
                anchor="middle",
            )
            anda += largura

    cursor = 760.0
    for nome in ("Fundamental", "Médio", "Superior"):
        cursor = swatch(canvas, cursor, 266, cores[nome], nome.lower(), MUTED, size=14)

    superior_m = niveis["Superior"]["composicao_pct"]["mulheres"]["pct"]
    superior_h = niveis["Superior"]["composicao_pct"]["homens"]["pct"]
    canvas.text(
        760,
        304,
        f"{num(superior_m, 1)}% delas têm superior, contra {num(superior_h, 1)}% deles.",
        size=17,
        fill=INK,
        weight="700",
    )
    canvas.text(
        760, 330, "É essa composição, e não paridade salarial,", size=16, fill=MUTED
    )
    canvas.text(
        760, 352, "que empurra a razão agregada para cima.", size=16, fill=MUTED
    )
    return canvas.render()


# --------------------------------------------------------------------------- 5


def geografia(base: dict) -> str:
    """Renda, pobreza, Bolsa Família e peso demográfico das mulheres por região."""
    regioes = base["regiao"]["por_regiao"]
    ordem = sorted(
        regioes,
        key=lambda nome: regioes[nome]["renda_per_capita_media_brl"]["valor"],
        reverse=True,
    )

    canvas = Canvas(
        FULL, 430, aria="Renda, pobreza e Bolsa Família das mulheres adultas por região"
    )
    canvas.rect(0, 0, FULL, 430, WHITE)
    canvas.label(
        40,
        34,
        "Mulheres de 16 anos ou mais · PNAD Contínua anual 2025, 1ª visita · "
        "renda a preços de abr/2026 · ponta translúcida = intervalo de 95%",
    )
    canvas.text(
        40,
        62,
        "O degrau não é gradual: do Sul ao Nordeste a renda cai à metade e a "
        "dependência de transferência quase quintuplica.",
        size=17,
        fill=INK,
        weight="600",
    )

    colunas = [
        ("renda per capita média", "do domicílio (R$)", 190.0, 200.0, 3200.0, NAVY, 0),
        (
            "vive em domicílio de",
            "até 1 salário mínimo (%)",
            470.0,
            140.0,
            28.0,
            AMBER,
            1,
        ),
        ("vive em domicílio com", "Bolsa Família (%)", 700.0, 140.0, 38.0, OLIVE, 1),
        (
            "peso no total de mulheres",
            "adultas do país (%)",
            930.0,
            140.0,
            45.0,
            GRAY,
            1,
        ),
    ]
    chaves = [
        "renda_per_capita_media_brl",
        "ate_1_sm_pct",
        "bolsa_familia_pct",
        "mulheres_16_mais_pct",
    ]
    for titulo, sub, x, _l, _t, _c, _casas in colunas:
        canvas.label(x, 96, titulo, fill=MUTED)
        canvas.label(x, 114, sub, fill=MUTED)

    corte = 284.0
    for indice, nome in enumerate(ordem):
        y = 128.0 + indice * 50 + (44 if indice >= 3 else 0)
        bloco = regioes[nome]
        canvas.text(40, y + 19, nome, size=17, fill=INK, weight="700")
        for coluna, chave in zip(colunas, chaves, strict=False):
            _t, _s, x, largura, teto, cor, casas = coluna
            campo = bloco[chave]
            valor = campo.get("valor", campo.get("pct"))
            ponta = barra_ic(
                canvas,
                x,
                y,
                26,
                largura * valor / teto,
                largura * campo["moe"] / teto,
                cor,
            )
            canvas.text(
                ponta + 10, y + 19, num(valor, casas), size=17, fill=INK, weight="700"
            )

    canvas.line(40, corte, 1140, corte, stroke=INK, width=2)
    canvas.text(40, corte + 22, "o degrau", size=15, fill=INK, weight="700")
    canvas.text(
        118,
        corte + 22,
        "Norte e Nordeste concentram a pobreza feminina do país",
        size=15,
        fill=MUTED,
    )

    nordestinas = base["regiao"]["nordestinas_entre_as_mulheres_ate_1_sm"]
    canvas.text(
        40,
        418,
        f"{num(nordestinas['pct'], 1)}% das mulheres que vivem em domicílio de até um "
        "salário mínimo estão no Nordeste, que abriga "
        f"{num(regioes['Nordeste']['mulheres_16_mais_pct']['pct'], 1)}% das mulheres "
        "adultas do país.",
        size=16,
        fill=MUTED,
    )
    return canvas.render()


# --------------------------------------------------------------------------- 6


def deslocamento(data: dict) -> str:
    """Vantagem de Lula sobre Flávio por região, nas duas ondas e nos dois turnos."""
    gradiente = next(
        item
        for item in data["margin_leverage"]["margins"]
        if item["dimension"] == "region"
    )["gradient"]
    for nome, publicado in zip(REGIOES, gradiente, strict=False):
        lula, flavio = AGOSTO_2T[nome]
        if abs((lula - flavio) - publicado) > 0.4:
            raise SystemExit(f"crosstab regional divergente do JSON em {nome}")

    canvas = Canvas(
        FULL,
        420,
        aria="Vantagem de Lula sobre Flávio por região nas ondas de 27/07 e 03/08",
    )
    canvas.rect(0, 0, FULL, 420, NAVY)
    canvas.label(
        40, 34, "vantagem de Lula sobre Flávio, em pontos · recorte regional", fill=GRAY
    )

    canvas.circle(902, 30, 8, NAVY, stroke=WHITE, stroke_width=2.4)
    canvas.text(918, 35, "27/07", size=14, fill=WHITE)
    canvas.circle(990, 30, 9, CORAL)
    canvas.text(1006, 35, "03/08", size=14, fill=WHITE)

    zero, esc = 660.0, 11.5
    for marca in (-25, -20, -10, 0, 10, 20, 30):
        x = zero + marca * esc
        canvas.label(
            x, 74, signed(marca, 0) if marca else "0", anchor="middle", fill=GRAY
        )
        canvas.line(
            x, 82, x, 358, stroke=WHITE, width=1, opacity=0.10 if marca else 0.45
        )
    canvas.text(zero - 14, 60, "Flávio à frente", size=14, fill=SKY, anchor="end")
    canvas.text(zero + 14, 60, "Lula à frente", size=14, fill=CORAL)

    ordem = sorted(
        REGIOES, key=lambda nome: AGOSTO_1T[nome][0] - AGOSTO_1T[nome][1], reverse=True
    )
    topo = 110.0
    for indice, nome in enumerate(ordem):
        base_y = topo + indice * 68
        if nome == "Nordeste":
            canvas.rect(40, base_y - 24, 1100, 80, WHITE, rx=8, opacity=0.07)
            canvas.text(
                40, base_y + 26, "maior deslocamento da rodada", size=13, fill=LIME
            )
        canvas.text(40, base_y + 6, nome, size=17, fill=WHITE, weight="600")

        for turno, (rotulo, agosto, julho) in enumerate(
            (("1º turno", AGOSTO_1T, JULHO_1T), ("2º turno", AGOSTO_2T, JULHO_2T))
        ):
            y = base_y + turno * 34
            canvas.label(310, y + 5, rotulo, anchor="end", fill=GRAY)
            valor = agosto[nome][0] - agosto[nome][1]
            cor = CORAL if valor >= 0 else SKY
            x = zero + valor * esc

            if nome in julho:
                antes = julho[nome][0] - julho[nome][1]
                x_antes = zero + antes * esc
                canvas.line(x, y, x_antes, y, stroke=WHITE, width=2.4, opacity=0.55)
                meio = (x + x_antes) / 2
                canvas.rect(meio - 27, y - 26, 54, 21, NAVY, rx=4)
                canvas.text(
                    meio,
                    y - 10,
                    signed(valor - antes, 0),
                    size=17,
                    fill=LIME,
                    weight="700",
                    anchor="middle",
                )
                canvas.circle(x_antes, y, 9, NAVY, stroke=WHITE, stroke_width=2.4)
                canvas.rect(x_antes + 13, y - 11, 44, 22, NAVY)
                canvas.text(
                    x_antes + 16,
                    y + 6,
                    signed(antes, 0),
                    size=17,
                    fill=WHITE,
                    weight="700",
                )

            canvas.line(zero, y, x, y, stroke=cor, width=3.2)
            canvas.circle(x, y, 10, cor)
            canvas.rect(x + (12 if valor >= 0 else -56), y - 11, 44, 22, NAVY)
            canvas.text(
                x + (-18 if valor < 0 else 18),
                y + 6,
                signed(valor, 0),
                size=19,
                fill=WHITE,
                weight="700",
                anchor="end" if valor < 0 else "start",
            )

    canvas.line(40, 374, 1140, 374, stroke=WHITE, width=1, opacity=0.18)
    canvas.text(
        40,
        393,
        "Nesta base, a abertura regional de 27/07 está transcrita apenas para o Nordeste; "
        "as demais regiões entram só com a marca de 03/08.",
        size=14,
        fill=GRAY,
    )
    canvas.text(
        40,
        412,
        "Margem nacional publicada: ±2 pontos. O estrato do Nordeste, 28% da amostra, tem "
        "margem perto de ±4 por estimativa, e maior ainda na diferença entre ondas.",
        size=14,
        fill=GRAY,
    )
    return canvas.render()


def main() -> None:
    data, base = load(DATA), load(MULHERES)
    figuras = {
        "mulheres_cenarios": cenarios(base["nexus_referencia"]),
        "mulheres_tesoura": tesoura(base["nexus_referencia"]),
        "mulheres_material": material(base),
        "mulheres_paradoxo": paradoxo(base),
        "mulheres_regiao": geografia(base),
        "regioes_desloc": deslocamento(data),
    }
    write_fragments(OUTPUT, figuras)
    print(
        json.dumps(
            {"output": str(OUTPUT), "figuras": list(figuras)}, ensure_ascii=False
        )
    )


if __name__ == "__main__":
    main()
