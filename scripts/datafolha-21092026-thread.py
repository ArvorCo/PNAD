#!/usr/bin/env python3
"""Gera docs/datafolha_21092026_thread.html: a camada Sudeste em cinco cards 1:1.

A onda nacional de setembro traz pouca novidade: o placar publicado quase nao
se move e a estrela continua sendo a reponderacao por renda. A novidade esta no
Sudeste, onde o instituto mediu governo do estado e Presidencia na mesma
entrevista em SP, RJ e MG. Cinco cards: a tese, as duas reguas, a transferencia
que o proprio instituto publicou, a leitura por estado e os limites.

Nada e digitado a mao. Placares, margens, cruzamentos, senado e contagem de
pauta vem de docs/assets/datafolha_21092026_sudeste.json,
docs/assets/datafolha_21092026_cobertura_sudeste.json e
docs/assets/datafolha_21092026_data.json.

Reproducao:
    python3 scripts/datafolha-21092026-sudeste.py
    python3 scripts/datafolha-21092026-cobertura-sudeste.py
    python3 scripts/datafolha-21092026-thread.py
"""

from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs/assets"
OUTPUT = ROOT / "docs/datafolha_21092026_thread.html"

S = json.loads((ASSETS / "datafolha_21092026_sudeste.json").read_text(encoding="utf-8"))
C = json.loads(
    (ASSETS / "datafolha_21092026_cobertura_sudeste.json").read_text(encoding="utf-8")
)
N = json.loads((ASSETS / "datafolha_21092026_data.json").read_text(encoding="utf-8"))

UFS = ("SP", "MG", "RJ")
LULA = "Lula (PT)"
FLAVIO = "Flavio Bolsonaro (PL)"
CURY = "Escritor Augusto Cury (AVANTE)"

ACHADOS = {a["id"]: a for a in S["achados"]}
REGIONAL = S["regional_contra_estadual"]
CRUZ = S["cruzamentos_publicados"]
NACIONAL_PUB = N["reweight"]["turnos"]["2t"]["publicado"]
NACIONAL_AJU = N["reweight"]["turnos"]["2t"]["cenarios"]["pessoas16_efetivo"][
    "ajustado"
]

INK = "#f4f2ea"
INK2 = "#ddd8ca"
MUTED = "#9a9789"
FAINT = "#8f8c7f"
LIME = "#cfe63c"
CYAN = "#45c9c2"
AMBER = "#f0a930"
GREEN = "#34b47e"
LULA_COR = "#e0483a"
LULA_TXT = "#ea6a5c"
FLAVIO_COR = "#3f8fd6"
GREY = "#939cae"
CHIP = "#0a0b09"
MONO = "IBM Plex Mono, monospace"
SANS = "IBM Plex Sans Condensed, Arial, sans-serif"

TEMA_ROTULO = {
    "crime_organizado": "crime organizado",
    "transporte_mobilidade": "transporte",
    "justica_eleitoral": "justiça eleitoral",
    "corrupcao_investigacao": "investigação",
    "seguranca_publica": "segurança pública",
    "financas_estaduais": "contas estaduais",
    "meio_ambiente_mineracao": "mineração",
    "infraestrutura_concessoes": "concessões",
    "campanha_eleitoral": "campanha",
    "pesquisa_eleitoral": "pesquisa",
}

# A escolha de qual tema destacar por estado e juizo editorial declarado aqui; a
# contagem de cada um vem do JSON de cobertura, nunca digitada a mao. Temas de
# campanha e de pesquisa ficam de fora: descrevem a propria corrida, nao a pauta
# de governo que o questionario poderia ter medido.
DESTAQUE_TEMA = {
    "SP": ["crime_organizado", "transporte_mobilidade"],
    "RJ": ["justica_eleitoral"],
    "MG": ["meio_ambiente_mineracao", "financas_estaduais"],
}

# A grafia do JSON de extracao e ASCII em alguns nomes proprios. A correcao e
# ortografica e nao toca em numero nenhum.
GRAFIA = {"Flavio Bolsonaro": "Flávio Bolsonaro"}


def fmt(v, n=0):
    return f"{v:,.{n}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def sgn(v, n=0):
    v = round(v, n)
    if v == 0:
        v = 0.0
    return ("+" if v > 0 else "") + fmt(v, n)


def esc(s):
    return html.escape(str(s))


def curto(nome: str) -> str:
    """Nome sem a sigla do partido, para caber no grafico."""
    limpo = nome.split(" (")[0]
    return GRAFIA.get(limpo, limpo)


# ------------------------------------------------------------------ leitura
def estado(uf: str) -> dict:
    e = S["estados"][uf]
    vao = e["vao"]["turno2"]
    return {
        "uf": uf,
        "n": e["n"],
        "governador": curto(vao["candidato_governador"]),
        "gov_pct": vao["governador_pct"],
        "flavio_pct": vao["presidenciavel_pct"],
        "vao": vao["vao_pp"],
        "margem": vao["margem_pp"],
        "flavio_1t": e["presidente"]["turno1"][FLAVIO],
        "lula_2t": e["presidente"]["turno2"][LULA],
    }


E = {uf: estado(uf) for uf in UFS}
N_ESTADUAL = sum(E[uf]["n"] for uf in UFS)
SENADO = ACHADOS["senado_da_direita_atras_do_topo"]["valores"]


def partido_pl(uf: str) -> dict:
    for linha in S["estados"][uf]["vao_por_recorte_turno2"]:
        if linha["dimensao"] == "partido" and linha["recorte"] == "PL":
            return linha
    raise KeyError(f"sem recorte PL em {uf}")


PL_MG = partido_pl("MG")
INVERSO_MG = S["estados"]["MG"]["vao"]["inverso_turno2"]


def cruzamento(uf: str, destino: str) -> dict:
    for bloco in CRUZ:
        if bloco["uf"] == uf and bloco["destino_pergunta"] == destino:
            return bloco
    raise KeyError(f"sem cruzamento {uf}/{destino}")


CRUZ_SP = cruzamento("SP", "presidente, 1o turno")["linhas"]["Tarcísio (REPUBLICANOS)"]
CRUZ_MG = cruzamento("MG", "presidente, 2o turno")["linhas"][
    "Cleitinho Azevedo (REPUBLICANOS)"
]
CRUZ_RJ = cruzamento("RJ", "presidente, 2o turno")["linhas"]["Eduardo Paes (PSD)"]
LINHAS_MEDIDAS = S["varredura_de_cruzamentos"]["linhas_medidas"]
# A linha do Rio que o dossie passou a publicar com base e intervalo: ela e
# pequena em pontos do eleitorado e mesmo assim tem o zero fora do intervalo.
RUAS_LULA = next(
    r
    for r in S["transferencia"]["RJ"]["incerteza_das_linhas_medidas"]
    if r["origem"].startswith("Douglas Ruas")
    and r["destino"] == LULA
    and r["turno"] == "2º turno"
)
# Dois numeros diferentes, que nao podem ser trocados um pelo outro: o
# eleitorado de Tarcisio que nao vota Flavio no 1o turno, e a parte desse
# eleitorado cujo destino o relatorio nao abre.
TARCISIO_FORA_FLAVIO = 100 - CRUZ_SP[FLAVIO]
TARCISIO_SEM_LINHA = 100 - sum(CRUZ_SP.values())


def temas(uf: str) -> list[tuple[str, int]]:
    """Rotulo e contagem dos temas destacados naquele estado, lidos da cobertura."""
    contagem = C["por_uf_tema"][uf]
    return [(TEMA_ROTULO[k], contagem[k]) for k in DESTAQUE_TEMA[uf]]


def frase_temas(uf: str) -> str:
    partes = [f"{valor} de {rotulo}" for rotulo, valor in temas(uf)]
    return " e ".join(partes) if len(partes) < 3 else ", ".join(partes)


# ------------------------------------------------------------------ SVG
def svg(body, width=1000, height=640, label=""):
    return (
        f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{esc(label)}" '
        f'xmlns="http://www.w3.org/2000/svg">{body}</svg>'
    )


def text(x, y, value, size=15, fill=MUTED, family=MONO, weight=400, anchor="start"):
    size = round(size * 1.12)
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" '
        f'font-family="{esc(family)}" font-weight="{weight}" '
        f'text-anchor="{anchor}">{esc(value)}</text>'
    )


def rect(x, y, w, h, fill, radius=3):
    return (
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(w, 0):.1f}" '
        f'height="{max(h, 0):.1f}" rx="{radius}" fill="{fill}"/>'
    )


def line(x1, y1, x2, y2, stroke, width=1, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
        f'stroke="{stroke}" stroke-width="{width}"{d}/>'
    )


def chip(x, y, rotulo, size=15, fill=INK, anchor="middle"):
    """Rotulo sobre fita colorida: retangulo escuro atras, senao o contraste cai."""
    largura = len(rotulo) * size * 0.68 + 16
    x0 = x - largura / 2 if anchor == "middle" else x - 8
    return rect(x0, y - size - 5, largura, size + 12, CHIP, 4) + text(
        x, y, rotulo, size, fill, MONO, 600, anchor
    )


# ------------------------------------------------------------------ vizes
def viz_tres_pares():
    """Governo do estado e Presidência no 2º turno, mesma amostra, três estados."""
    W, H = 1000, 640
    x0, x1 = 250, 880
    escala = 70

    def sx(v):
        return x0 + (x1 - x0) * v / escala

    out = [
        text(
            60,
            34,
            "2º TURNO ESTADUAL E 2º TURNO PRESIDENCIAL, MESMA ENTREVISTA",
            15,
            MUTED,
        )
    ]
    for marca in (20, 40, 60):
        out.append(line(sx(marca), 58, sx(marca), H - 116, "rgb(244 242 234 / 14%)"))
        out.append(text(sx(marca), H - 92, f"{marca}%", 14, FAINT, anchor="middle"))
    y = 106
    for uf in UFS:
        d = E[uf]
        out.append(text(60, y + 8, uf, 30, INK, SANS, 700))
        out.append(text(60, y + 36, f"n = {fmt(d['n'])}", 14, FAINT))
        out.append(text(60, y + 62, "vão " + sgn(d["vao"]), 15, AMBER))
        cor_gov = GREEN if d["vao"] >= 0 else GREY
        out.append(rect(x0, y - 16, sx(d["gov_pct"]) - x0, 38, cor_gov))
        out.append(
            text(x0 + 14, y + 10, f"{d['governador']}  {d['gov_pct']}", 19, CHIP)
        )
        out.append(rect(x0, y + 30, sx(d["flavio_pct"]) - x0, 38, FLAVIO_COR))
        out.append(text(x0 + 14, y + 56, f"Flávio  {d['flavio_pct']}", 19, CHIP))
        y += 170
    out.append(rect(60, H - 58, 18, 18, GREEN))
    out.append(text(86, H - 43, "governo do estado, 2º turno", 15, INK2))
    out.append(rect(430, H - 58, 18, 18, FLAVIO_COR))
    out.append(text(456, H - 43, "Flávio, Presidência, 2º turno", 15, INK2))
    out.append(
        text(
            60,
            H - 12,
            "Governador: SP p. 39, MG p. 40, RJ p. 38. Presidente: pp. 58, 94 e 76.",
            13,
            FAINT,
        )
    )
    return svg("".join(out), W, H, "Governo do estado e Presidência em SP, MG e RJ")


def viz_duas_reguas():
    """Recorte Sudeste do nacional contra a média das três estaduais."""
    W, H = 1000, 640
    x0, x1 = 230, 880
    lo, hi = 36, 54

    def sx(v):
        return x0 + (x1 - x0) * (v - lo) / (hi - lo)

    nac = REGIONAL["recorte_nacional"]
    med = REGIONAL["media_estadual"]
    out = [text(60, 34, "LULA E FLÁVIO NO SUDESTE, DUAS RÉGUAS, 2º TURNO", 15, MUTED)]
    for marca in range(38, 55, 4):
        out.append(line(sx(marca), 58, sx(marca), 396, "rgb(244 242 234 / 14%)"))
        out.append(text(sx(marca), 422, f"{marca}%", 14, FAINT, anchor="middle"))
    linhas = [
        ("Recorte Sudeste do nacional", f"n = {fmt(nac['base'])} · 15 a 17/09", nac),
        ("Três estaduais pelo TSE", f"n = {fmt(N_ESTADUAL)} · 8 a 10/09", med),
    ]
    y = 104
    for titulo, sub, bloco in linhas:
        out.append(text(60, y - 10, titulo, 19, INK, SANS, 600))
        out.append(text(60, y + 14, sub, 14, FAINT))
        for chave, cor, txt_cor, dy in (
            ("lula", LULA_COR, LULA_TXT, 44),
            ("flavio", FLAVIO_COR, FLAVIO_COR, 92),
        ):
            valor = bloco[chave]
            margem = bloco[f"margem_{chave}_pp"]
            yy = y + dy
            casas = 2 if valor % 1 else 0
            out.append(line(sx(valor - margem), yy, sx(valor + margem), yy, INK2, 5))
            for ponta in (valor - margem, valor + margem):
                out.append(line(sx(ponta), yy - 11, sx(ponta), yy + 11, INK2, 3))
            out.append(f'<circle cx="{sx(valor):.1f}" cy="{yy}" r="14" fill="{cor}"/>')
            rotulo = "Lula " if chave == "lula" else "Flávio "
            out.append(
                text(
                    sx(valor + margem) + 20,
                    yy + 7,
                    rotulo + fmt(valor, casas),
                    17,
                    txt_cor,
                    MONO,
                    600,
                )
            )
        y += 172
    contraste = REGIONAL["contraste"]
    base = 500
    out.append(
        text(60, base - 40, "DIFERENÇA ENTRE AS DUAS RÉGUAS, COM 95%", 15, MUTED)
    )
    zx0, zx1 = 230, 880
    zero = (zx0 + zx1) / 2

    def zx(v):
        return zero + (zx1 - zero) * v / 8

    out.append(line(zero, base - 24, zero, base + 44, "rgb(244 242 234 / 40%)", 2))
    out.append(text(zero, base + 66, "zero", 14, FAINT, anchor="middle"))
    ic = contraste["ic95"]
    out.append(line(zx(ic[0]), base + 14, zx(ic[1]), base + 14, AMBER, 7))
    out.append(text(zx(ic[0]) - 16, base + 20, fmt(ic[0], 2), 15, AMBER, anchor="end"))
    out.append(text(zx(ic[1]) + 16, base + 20, sgn(ic[1], 2), 15, AMBER))
    out.append(
        chip(
            zx(contraste["diferenca_das_diferencas_pp"]),
            base - 4,
            sgn(contraste["diferenca_das_diferencas_pp"], 3),
            15,
        )
    )
    out.append(
        text(
            60,
            H - 12,
            "O intervalo contém o zero. Cobertura do eleitorado do Sudeste: "
            f"{fmt(REGIONAL['cobertura_do_eleitorado_pct'], 2)}%.",
            13,
            FAINT,
        )
    )
    return svg("".join(out), W, H, "Recorte regional contra a média das estaduais")


def viz_fluxo():
    """Cruzamento publicado: fita sólida é medida, hachurada é o que não sai."""
    W, H = 1000, 640
    x0, x1 = 290, 826
    hatch = (
        '<defs><pattern id="naopub" width="12" height="12" '
        'patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
        '<rect width="12" height="12" fill="#2a2d29"/>'
        '<rect width="5" height="12" fill="#4a4e48"/></pattern></defs>'
    )
    out = [
        hatch,
        text(
            60,
            34,
            "VOTO PARA PRESIDENTE DENTRO DO ELEITORADO DE CADA GOVERNADOR",
            15,
            MUTED,
        ),
    ]
    blocos = [
        (
            "SP · Tarcísio",
            "1º turno · p. 4",
            [
                (CRUZ_SP[FLAVIO], FLAVIO_COR, f"Flávio {CRUZ_SP[FLAVIO]}"),
                (CRUZ_SP[LULA], LULA_COR, f"Lula {CRUZ_SP[LULA]}"),
                (CRUZ_SP[CURY], AMBER, f"Cury {CRUZ_SP[CURY]}"),
            ],
        ),
        (
            "MG · Cleitinho",
            "2º turno · p. 21",
            [
                (CRUZ_MG[FLAVIO], FLAVIO_COR, f"Flávio {CRUZ_MG[FLAVIO]}"),
                (CRUZ_MG[LULA], LULA_COR, f"Lula {CRUZ_MG[LULA]}"),
            ],
        ),
        (
            "RJ · Paes",
            "2º turno · p. 13",
            [
                (CRUZ_RJ[LULA], LULA_COR, f"Lula {CRUZ_RJ[LULA]}"),
                (CRUZ_RJ[FLAVIO], FLAVIO_COR, f"Flávio {CRUZ_RJ[FLAVIO]}"),
            ],
        ),
    ]
    y = 122
    for titulo, fonte, partes in blocos:
        out.append(text(60, y + 6, titulo, 21, INK, SANS, 600))
        out.append(text(60, y + 32, fonte, 14, FAINT))
        x = x0
        fora = 0
        for valor, cor, rotulo in partes:
            largura = (x1 - x0) * valor / 100
            out.append(rect(x, y - 18, largura, 46, cor))
            if largura > 150:
                out.append(text(x + 14, y + 12, rotulo, 18, CHIP, MONO, 600))
            else:
                # Fatia estreita: o rotulo desce, e cada uma desce um degrau a
                # mais, senao duas fatias vizinhas escrevem uma por cima da outra.
                fora += 1
                alvo = y + 24 + fora * 30
                out.append(
                    line(x + largura / 2, y + 30, x + largura / 2, alvo - 16, cor, 2)
                )
                out.append(chip(x + largura / 2, alvo, rotulo, 14))
            x += largura
        resto = x1 - x
        soma = sum(valor for valor, _, _ in partes)
        out.append(rect(x, y - 18, resto, 46, "url(#naopub)"))
        out.append(
            text(x1 + 16, y + 12, f"{100 - soma} sem linha", 15, INK2, MONO, 600)
        )
        y += 150
    out.append(rect(60, H - 96, 18, 18, FLAVIO_COR))
    out.append(
        text(86, H - 81, "fita sólida: linha publicada pelo instituto", 15, INK2)
    )
    out.append(rect(60, H - 60, 18, 18, "url(#naopub)"))
    out.append(
        text(
            86,
            H - 45,
            "fita hachurada: o resto da linha, que o relatório não abre",
            15,
            INK2,
        )
    )
    out.append(
        text(
            60,
            H - 12,
            f"{LINHAS_MEDIDAS} linhas medidas no relatório presidencial estadual. "
            "Leitura agregada.",
            13,
            FAINT,
        )
    )
    return svg("".join(out), W, H, "Cruzamento publicado entre governador e presidente")


def viz_por_estado():
    """Vão do governo e distância do melhor senador da direita, por estado."""
    W, H = 1000, 640
    zero = 520
    escala = 11

    def zx(v):
        return zero + v * escala

    out = [
        text(60, 34, "VÃO DO GOVERNO E DISTÂNCIA DO SENADO, EM PONTOS", 15, MUTED),
        line(zero, 58, zero, 456, "rgb(244 242 234 / 40%)", 2),
        text(zero, 480, "zero", 14, FAINT, anchor="middle"),
    ]
    # O rotulo do estado fica ACIMA das barras. Ao lado, a barra do senado, que
    # sempre corre para a esquerda, passava por cima do nome.
    y = 84
    for uf in ("MG", "SP", "RJ"):
        d = E[uf]
        sen = SENADO[uf]
        positivo = d["vao"] >= 0
        out.append(text(60, y + 6, uf, 26, INK, SANS, 700))
        out.append(text(124, y + 4, f"Senado: {curto(sen['candidato'])}", 14, FAINT))
        largura = abs(d["vao"]) * escala
        out.append(
            rect(
                zero if positivo else zero - largura,
                y + 18,
                largura,
                34,
                GREEN if positivo else FLAVIO_COR,
            )
        )
        out.append(
            text(
                zx(d["vao"]) + (14 if positivo else -14),
                y + 42,
                "governo " + sgn(d["vao"]),
                17,
                GREEN if positivo else FLAVIO_COR,
                MONO,
                600,
                "start" if positivo else "end",
            )
        )
        dist = sen["distancia_pp"]
        largura2 = abs(dist) * escala
        out.append(rect(zero - largura2, y + 58, largura2, 26, GREY))
        out.append(
            text(
                zero - largura2 - 14,
                y + 77,
                "senado " + sgn(dist),
                16,
                GREY,
                MONO,
                600,
                "end",
            )
        )
        y += 128
    out.append(
        text(60, 528, "PERGUNTAS TEMÁTICAS NOS TRÊS QUESTIONÁRIOS ESTADUAIS", 15, MUTED)
    )
    out.append(text(60, 594, "0", 46, AMBER, SANS, 900))
    out.append(
        text(
            120,
            578,
            "em 13 tabelas por estado: voto, rejeição, decisão, motivação e aprovação.",
            15,
            INK2,
        )
    )
    out.append(
        text(
            120,
            604,
            "No mesmo mês o grupo contratante publicou "
            f"{C['total_itens']} itens sobre os quatro estados.",
            15,
            INK2,
        )
    )
    return svg("".join(out), W, H, "Vão do governo e distância do senado por estado")


def viz_limites():
    """Os três achados que contrariam a tese, lado a lado."""
    W, H = 1000, 640
    x0, x1 = 310, 860

    def sx(v):
        return x0 + (x1 - x0) * v / 100

    rj = E["RJ"]
    out = [text(60, 34, "TRÊS CONTRAPROVAS, NA MESMA AMOSTRA", 15, MUTED)]
    linhas = [
        (
            "RJ · 2º turno",
            f"{rj['governador']} {rj['gov_pct']}",
            rj["gov_pct"],
            f"Flávio {rj['flavio_pct']}",
            rj["flavio_pct"],
            "o presidenciável está à frente do palanque estadual",
        ),
        (
            f"MG · quem prefere o PL (n = {PL_MG['base_governador']})",
            f"governo {PL_MG['governador']}",
            PL_MG["governador"],
            f"Flávio {PL_MG['flavio']}",
            PL_MG["flavio"],
            "na base partidária o nome nacional não depende do palanque",
        ),
        (
            "MG · vão inverso",
            f"Patrus {INVERSO_MG['presidenciavel_pct']}",
            INVERSO_MG["presidenciavel_pct"],
            f"Lula {INVERSO_MG['governador_pct']}",
            INVERSO_MG["governador_pct"],
            "Lula também rende acima da própria chapa, e por mais",
        ),
    ]
    y = 112
    for titulo, rot_a, val_a, rot_b, val_b, nota in linhas:
        out.append(text(60, y + 4, titulo, 19, INK, SANS, 600))
        out.append(text(60, y + 30, nota, 13, FAINT))
        out.append(line(sx(min(val_a, val_b)), y, sx(max(val_a, val_b)), y, INK2, 6))
        out.append(f'<circle cx="{sx(val_a):.1f}" cy="{y}" r="15" fill="{GREY}"/>')
        out.append(f'<circle cx="{sx(val_b):.1f}" cy="{y}" r="15" fill="{CYAN}"/>')
        a_esquerda = val_a < val_b
        out.append(
            text(
                sx(val_a) + (-26 if a_esquerda else 26),
                y + 7,
                rot_a,
                16,
                GREY,
                MONO,
                600,
                "end" if a_esquerda else "start",
            )
        )
        out.append(
            text(
                sx(val_b) + (26 if a_esquerda else -26),
                y + 7,
                rot_b,
                16,
                CYAN,
                MONO,
                600,
                "start" if a_esquerda else "end",
            )
        )
        y += 130
    out.append(text(60, 520, "O QUE FALTA PEDIR", 15, MUTED))
    out.append(
        text(
            60,
            558,
            "A matriz do voto para governador contra presidente contra senador,",
            18,
            INK2,
            SANS,
        )
    )
    out.append(text(60, 586, "com as bases e os pesos de cada célula.", 18, INK2, SANS))
    out.append(text(60, H - 12, "brasil.arvor.co/datafolha_21092026.html", 14, LIME))
    return svg("".join(out), W, H, "Contraprovas e o que falta pedir ao instituto")


# ------------------------------------------------------------------ cards
def build_cards() -> list[dict]:
    sp, mg, rj = E["SP"], E["MG"], E["RJ"]
    nac = REGIONAL["recorte_nacional"]
    med = REGIONAL["media_estadual"]
    contraste = REGIONAL["contraste"]
    sen_sp, sen_mg, sen_rj = SENADO["SP"], SENADO["MG"], SENADO["RJ"]
    return [
        {
            "kind": "tese",
            "tag": "tese",
            "metric": "3",
            "title": "O Sudeste não é um problema. São três.",
            "t": (
                f"No nacional quase nada se move: Lula {fmt(NACIONAL_PUB['lula'])} e "
                f"Flávio {fmt(NACIONAL_PUB['flavio'])} publicados, "
                f"{fmt(NACIONAL_AJU['lula'], 2)} e {fmt(NACIONAL_AJU['flavio'], 2)} "
                "na régua de renda da PNAD. A novidade está nos três estados que o "
                "instituto mediu por dentro, na mesma entrevista."
            ),
            "chips": [
                (
                    "g",
                    f"SP {sp['governador']} {sp['gov_pct']} x Flávio {sp['flavio_pct']}",
                ),
                (
                    "a",
                    f"MG {mg['governador']} {mg['gov_pct']} x Flávio {mg['flavio_pct']}",
                ),
                (
                    "b",
                    f"RJ Flávio {rj['flavio_pct']} x {rj['governador']} {rj['gov_pct']}",
                ),
            ],
            "viz": viz_tres_pares(),
            "copy": [
                (
                    "Post 1. O Datafolha completo de 21 de setembro traz pouca novidade "
                    f"nacional. O 2º turno publicado é Lula {fmt(NACIONAL_PUB['lula'])} e "
                    f"Flávio {fmt(NACIONAL_PUB['flavio'])}. Trocando só a distribuição de "
                    "renda da amostra pela distribuição medida pela PNAD de 2025, o mesmo "
                    f"2º turno vira Lula {fmt(NACIONAL_AJU['lula'], 2)} e Flávio "
                    f"{fmt(NACIONAL_AJU['flavio'], 2)}. Essa continua sendo a estrela do "
                    "laudo, e continua sendo sensibilidade sob régua comum, não previsão."
                ),
                "A novidade está no Sudeste. E o Sudeste não é um problema: são três.",
                (
                    "Na mesma entrevista, o instituto perguntou governo do estado e "
                    f"Presidência. Em São Paulo, {sp['governador']} tem {sp['gov_pct']} no "
                    f"2º turno estadual e Flávio tem {sp['flavio_pct']} no presidencial. "
                    f"Em Minas, {mg['governador']} tem {mg['gov_pct']} e Flávio tem "
                    f"{mg['flavio_pct']}. No Rio o sinal inverte: {rj['governador']} tem "
                    f"{rj['gov_pct']} e Flávio tem {rj['flavio_pct']}."
                ),
                (
                    "Três estados vizinhos, três geometrias. Em SP e em MG quem carrega a "
                    "chapa é o candidato ao governo. No RJ quem carrega é o presidenciável. "
                    "Qualquer frase sobre o Sudeste no singular morre nessa tabela."
                ),
                (
                    "A diferença entre cargos não prova erro do instituto: cargo, cédula e "
                    "incentivo são diferentes. Ela mede teto endereçável, não previsão. "
                    "Votar no governador não torna o eleitor disponível para o "
                    "presidenciável."
                ),
            ],
            "foot": "Datafolha · campo estadual 8 a 10/09/2026 · BR-04029/2026",
        },
        {
            "kind": "ponto",
            "tag": "aula",
            "metric": sgn(contraste["diferenca_das_diferencas_pp"], 2),
            "title": "Duas réguas para o mesmo Sudeste, e elas não se separam",
            "t": (
                f"O recorte regional da pesquisa nacional dá Lula {fmt(nac['lula'])} e "
                f"Flávio {fmt(nac['flavio'])}, com base {fmt(nac['base'])}. As três "
                "estaduais, ponderadas pelo eleitorado do TSE, dão "
                f"{fmt(med['lula'], 2)} e {fmt(med['flavio'], 2)}."
            ),
            "chips": [
                (
                    "c",
                    "margem da diferença "
                    f"{fmt(nac['margem_diferenca_pp'], 2)} no recorte",
                ),
                (
                    "c",
                    f"cobertura {fmt(REGIONAL['cobertura_do_eleitorado_pct'], 2)}%",
                ),
                (
                    "a",
                    f"IC95 de {fmt(contraste['ic95'][0], 2)} a "
                    f"{sgn(contraste['ic95'][1], 2)}",
                ),
            ],
            "viz": viz_duas_reguas(),
            "copy": [
                (
                    "Post 2. Aula curta sobre recorte regional. Quando uma pesquisa "
                    "nacional publica o resultado de uma região, ela está usando um pedaço "
                    f"da amostra. O recorte Sudeste desta onda tem base {fmt(nac['base'])} "
                    f"e dá Lula {fmt(nac['lula'])} contra Flávio {fmt(nac['flavio'])}. A "
                    "margem da diferença nesse pedaço é de "
                    f"{fmt(nac['margem_diferenca_pp'], 2)} pontos."
                ),
                (
                    "Existe uma segunda régua para a mesma região. O próprio instituto foi "
                    "a campo em SP, RJ e MG uma semana antes, com amostras estaduais que "
                    f"somam {fmt(N_ESTADUAL)} entrevistas. Ponderando os três estados pelo "
                    f"eleitorado do TSE, sai Lula {fmt(med['lula'], 2)} contra Flávio "
                    f"{fmt(med['flavio'], 2)}."
                ),
                (
                    "A diferença entre as duas leituras é de "
                    f"{fmt(contraste['diferenca_das_diferencas_pp'], 3)} ponto, com "
                    f"intervalo de 95% indo de {fmt(contraste['ic95'][0], 2)} a "
                    f"{sgn(contraste['ic95'][1], 2)}. O intervalo contém o zero com folga: "
                    "as duas réguas concordam."
                ),
                (
                    "É como pesar o mesmo saco de arroz na balança da feira e na da "
                    "farmácia. As duas marcaram quase o mesmo peso. Isso dá confiança nas "
                    "duas balanças. Não transforma a diferença entre elas em notícia."
                ),
                (
                    "Duas ressalvas andam junto com o número. Os campos são diferentes, 15 "
                    "a 17 de setembro no nacional e 8 a 10 nas estaduais. E as três "
                    f"estaduais cobrem {fmt(REGIONAL['cobertura_do_eleitorado_pct'], 2)}% "
                    "do eleitorado do Sudeste: o Espírito Santo não tem pesquisa do "
                    "instituto, e o voto capixaba não se deduz por subtração."
                ),
            ],
            "foot": "Recorte nacional p. 42 · estaduais pp. 58, 76 e 94 · pesos TSE",
        },
        {
            "kind": "ponto",
            "tag": "medição",
            "metric": str(LINHAS_MEDIDAS),
            "title": "A transferência, aqui, é medida",
            "t": (
                "O instituto publica, em texto corrido, o voto para presidente dentro do "
                "eleitorado de cada candidato a governador: SP na p. 4, RJ nas pp. 12 e "
                "13, MG nas pp. 20 e 21. Fita sólida é o que ele publicou; hachurada é o "
                "resto da linha, que ele não publica."
            ),
            "chips": [
                (
                    "a",
                    f"MG: Cleitinho dá {CRUZ_MG[FLAVIO]} a Flávio e {CRUZ_MG[LULA]} a Lula",
                ),
                (
                    "b",
                    f"SP: {fmt(TARCISIO_FORA_FLAVIO)} de cada 100 de Tarcísio "
                    "fora de Flávio",
                ),
                (
                    "l",
                    f"RJ: Paes dá {CRUZ_RJ[FLAVIO]} a Flávio e {CRUZ_RJ[LULA]} a Lula",
                ),
            ],
            "viz": viz_fluxo(),
            "copy": [
                (
                    "Post 3. Em quase toda auditoria a transferência de voto entre cargos "
                    "é estimativa nossa, com a prior declarada. Aqui não. O Datafolha "
                    "publica o voto para presidente dentro do eleitorado de cada candidato "
                    "a governador, em texto corrido: São Paulo na página 4, Rio nas "
                    "páginas 12 e 13, Minas nas páginas 20 e 21. São "
                    f"{LINHAS_MEDIDAS} linhas medidas."
                ),
                (
                    f"Minas. Quem vota em Cleitinho para governador dá {CRUZ_MG[FLAVIO]} a "
                    f"Flávio e {CRUZ_MG[LULA]} a Lula no 2º turno presidencial. Um em cada "
                    "quatro eleitores do candidato mais votado ao governo vota no "
                    "adversário do próprio campo para presidente."
                ),
                (
                    f"São Paulo. Quem vota em Tarcísio dá {CRUZ_SP[FLAVIO]} a Flávio no "
                    f"1º turno. São {fmt(TARCISIO_FORA_FLAVIO)} pontos desse eleitorado "
                    f"fora de Flávio, e o instituto abre parte deles: {CRUZ_SP[LULA]} "
                    f"vão a Lula e {CRUZ_SP[CURY]} a Cury. O destino dos outros "
                    f"{fmt(TARCISIO_SEM_LINHA)} o relatório não abre. Esses "
                    f"{CRUZ_SP[LULA]} viram piso do 2º turno: estimativa nossa não pode "
                    "ficar abaixo do que o instituto mediu."
                ),
                (
                    f"Rio. Quem vota em Paes dá {CRUZ_RJ[FLAVIO]} a Flávio e "
                    f"{CRUZ_RJ[LULA]} a Lula no 2º turno. É o cruzamento que mostra por "
                    "que o Rio inverte o sinal: o eleitorado do favorito ao governo é de "
                    "centro e de esquerda, e o presidenciável da direita vive fora dele."
                ),
                (
                    "Linha medida também tem intervalo: os "
                    f"{RUAS_LULA['valor_pct']}% de Ruas para Lula saem de "
                    f"{RUAS_LULA['n_subamostra']} entrevistas, de "
                    f"{fmt(RUAS_LULA['ic95_com_deff_pct'][0], 1)} a "
                    f"{fmt(RUAS_LULA['ic95_com_deff_pct'][1], 1)} com efeito de "
                    f"desenho, e valem {fmt(RUAS_LULA['pontos_do_eleitorado_pp'], 2)} "
                    "ponto do eleitorado."
                ),
                (
                    "Dois limites andam colados no número. A leitura é agregada: o "
                    "diagrama descreve blocos, não o percurso de pessoas. E o vão é teto "
                    "endereçável, não previsão. O que falta é a matriz completa, com bases "
                    "e pesos, que o instituto tem e não publica."
                ),
            ],
            "foot": "Relatório presidencial estadual · pp. 4, 12, 13, 20 e 21",
        },
        {
            "kind": "ordem",
            "tag": "juízo editorial",
            "metric": sgn(mg["vao"]),
            "title": "Minas primeiro, e o Senado não puxa ninguém",
            "t": (
                "Daqui em diante é juízo editorial desta casa, com o número ao lado de "
                "cada movimento. Minas tem o maior vão e o maior vazamento medido para "
                "Lula. São Paulo perde no 1º turno para outras direitas. No Rio quem "
                "sustenta a chapa é o presidenciável."
            ),
            "chips": [
                ("a", f"MG vão {sgn(mg['vao'])}, margem {fmt(mg['margem'], 2)}"),
                (
                    "g",
                    f"SP {curto(sen_sp['candidato'])} {sen_sp['voto1_pct']} x Flávio "
                    f"{sen_sp['flavio_turno1_pct']}",
                ),
                ("c", "0 pergunta temática nos três questionários"),
            ],
            "viz": viz_por_estado(),
            "copy": [
                (
                    "Post 4. Daqui em diante é juízo editorial desta casa, declarado como "
                    "tal, com o número ao lado de cada movimento."
                ),
                (
                    f"Minas é a prioridade. É o maior vão do Sudeste, {sgn(mg['vao'])} "
                    f"pontos, com margem de {fmt(mg['margem'], 2)}, e é onde o vazamento "
                    f"para Lula está medido: {CRUZ_MG[LULA]} de cada 100 eleitores de "
                    "Cleitinho. Voto casado com o candidato ao governo, no mesmo palanque "
                    f"e na mesma peça. São Paulo tem vão menor, {sgn(sp['vao'])}, e perde "
                    "no 1º turno para outras candidaturas de direita, o que se disputa com "
                    "programa e não com palanque. No Rio o problema é o oposto: quem "
                    "carrega a chapa é Flávio."
                ),
                (
                    "Senado. Nos três estados nenhum nome da direita puxa o topo. O melhor "
                    f"primeiro voto é {curto(sen_sp['candidato'])} com "
                    f"{sen_sp['voto1_pct']} em SP, contra {sen_sp['flavio_turno1_pct']} de "
                    f"Flávio; {curto(sen_mg['candidato'])} com {sen_mg['voto1_pct']} em "
                    f"MG, contra {sen_mg['flavio_turno1_pct']}; "
                    f"{curto(sen_rj['candidato'])} com {sen_rj['voto1_pct']} no RJ, contra "
                    f"{sen_rj['flavio_turno1_pct']}. De {abs(sen_sp['distancia_pp'])} a "
                    f"{abs(sen_rj['distancia_pp'])} pontos atrás."
                ),
                (
                    "Pauta. Os três questionários estaduais têm 13 tabelas cada e zero "
                    "pergunta temática: voto, rejeição, decisão, motivação e aprovação. No "
                    f"mesmo período o grupo que contratou publicou {C['total_itens']} "
                    f"itens sobre os quatro estados, entre eles {frase_temas('SP')} em SP, "
                    f"{frase_temas('RJ')} no RJ e {frase_temas('MG')} em MG. Não dizemos "
                    "que o veículo escondeu nada: os dois lados aparecem. A observação é "
                    "sobre o questionário. E a operação no transporte de SP só veio a "
                    "público em 17/09, sete dias depois de o campo estadual fechar."
                ),
            ],
            "foot": "Senado: SP pp. 42 a 44, RJ pp. 43 a 45, MG pp. 45 a 47",
        },
        {
            "kind": "limite",
            "tag": "limites",
            "metric": sgn(rj["vao"]),
            "title": "O que contraria a tese, e o que falta pedir",
            "t": (
                "O Rio inverte o sinal. Dentro da base do PL em Minas, Flávio bate o "
                "candidato ao governo. E Lula rende acima da própria chapa mineira por "
                "mais pontos do que a direita rende acima da dela."
            ),
            "chips": [
                ("b", f"RJ vão {sgn(rj['vao'])}"),
                (
                    "c",
                    f"MG, quem prefere o PL: governo {PL_MG['governador']} x Flávio "
                    f"{PL_MG['flavio']}",
                ),
                ("l", f"MG vão inverso {sgn(INVERSO_MG['vao_pp'])}"),
            ],
            "viz": viz_limites(),
            "copy": [
                "Post 5. Os limites, antes da conclusão, com o mesmo destaque do resto.",
                (
                    f"O Rio inverte o sinal: vão de {sgn(rj['vao'])}. O déficit ali é do "
                    "palanque estadual, não do presidenciável, e isso derruba qualquer "
                    "leitura regional única. Dentro de quem declara preferência pelo PL em "
                    f"Minas, Flávio faz {PL_MG['flavio']} e o candidato ao governo faz "
                    f"{PL_MG['governador']}: na base partidária o nome nacional não depende "
                    f"do palanque, ainda que a base seja pequena, "
                    f"{PL_MG['base_governador']} entrevistas. E Lula também rende acima da "
                    f"própria chapa em Minas, {INVERSO_MG['governador_pct']} contra "
                    f"{INVERSO_MG['presidenciavel_pct']} de Patrus, "
                    f"{sgn(INVERSO_MG['vao_pp'])} pontos, mais do que o vão da direita no "
                    "mesmo estado."
                ),
                (
                    "Mais limites. O Espírito Santo é outro instituto, outro método e "
                    "outro campo, e não fecha a conta do Sudeste. As margens saem de "
                    "amostragem aleatória simples, porque o efeito de desenho não é "
                    "publicado. E o que não está nas linhas publicadas é estimativa nossa "
                    "por ajuste proporcional iterativo: só os limites de Fréchet são "
                    "imunes à prior."
                ),
                (
                    "O que cobrar do instituto é uma coisa só: a matriz do voto para "
                    "governador contra o voto para presidente contra o voto para senador, "
                    "com as bases e os pesos de cada célula. Ele tem esse cruzamento, "
                    "porque publicou treze linhas dele."
                ),
                (
                    "Tudo está aberto, com fonte e página em cada número, em "
                    "https://brasil.arvor.co/datafolha_21092026.html#sudeste. Refaça a "
                    "conta."
                ),
            ],
            "foot": "Arvor Intelligence · Sudeste · setembro de 2026",
        },
    ]


KIND = {
    "tese": (LIME, "tese"),
    "ponto": (CYAN, "aula"),
    "ordem": (LIME, "ordem"),
    "limite": (AMBER, "limites"),
}

CSS = """
*,*::before,*::after{box-sizing:border-box}
:root{--bg:#0c0d0b;--bg2:#131512;--bg3:#191c18;--ink:#f4f2ea;--ink2:#ddd8ca;--muted:#9a9789;--faint:#8f8c7f;
  --lime:#cfe63c;--cyan:#45c9c2;--amber:#f0a930;--green:#34b47e;--lula:#ea6a5c;--flavio:#3f8fd6;
  --line:rgb(244 242 234 / 13%);--line2:rgb(244 242 234 / 26%);
  --display:Fraunces,Georgia,serif;--sans:"IBM Plex Sans Condensed",Arial,sans-serif;--mono:"IBM Plex Mono",ui-monospace,monospace;
  --wrap:min(1080px,calc(100% - 40px))}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);font-size:17px;line-height:1.62;-webkit-font-smoothing:antialiased}
.wrap{width:var(--wrap);margin:0 auto}
a{color:var(--cyan)}
.top{padding:34px 0 8px;display:flex;flex-wrap:wrap;gap:14px;align-items:center;justify-content:space-between}
.brand-lockup{display:flex;align-items:center;gap:11px;font-family:var(--mono);font-size:.76rem;letter-spacing:.13em;text-transform:uppercase;color:var(--muted)}
.brand-lockup img{width:26px;height:26px;border-radius:4px}
.top .back{font-family:var(--mono);font-size:.74rem;letter-spacing:.1em;text-transform:uppercase;color:var(--lime);text-decoration:none;border:1px solid var(--line2);border-radius:999px;padding:7px 15px}
h1{font-family:var(--display);font-size:clamp(2.3rem,6.4vw,4.4rem);line-height:.98;letter-spacing:-.028em;margin:18px 0 0;font-weight:900}
h1 em{display:block;font-style:italic;color:var(--lime);font-weight:500}
.deck{max-width:76ch;color:var(--ink2);margin:20px 0 0;font-size:1.06rem}
.howto{margin:26px 0 0;border:1px solid var(--line);border-left:3px solid var(--cyan);border-radius:4px;background:var(--bg3);padding:18px 20px;color:var(--ink2);font-size:.95rem}
.howto b{color:var(--ink)}
.rail{margin:30px 0 0;padding:11px 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
.rail .wrap{display:flex;gap:5px;align-items:center;overflow-x:auto;scrollbar-width:none}
.rail b{font-family:var(--mono);font-size:.68rem;letter-spacing:.13em;text-transform:uppercase;color:var(--faint);margin-right:8px;white-space:nowrap}
.rail a{width:26px;height:26px;flex:0 0 auto;display:grid;place-items:center;border-radius:5px;border:1px solid var(--line);color:var(--muted);text-decoration:none;font-family:var(--mono);font-size:.72rem}
.post{margin:52px 0 0}
.post-label{width:min(100%,760px);margin-left:auto;margin-right:auto;font-family:var(--mono);font-size:.72rem;letter-spacing:.13em;text-transform:uppercase;color:var(--faint);margin-bottom:11px}
.post-label b{color:var(--ink)}
/* O card e quadrado: 1:1, na largura de trabalho de 1080px, que e o que se anexa. */
.card{position:relative;aspect-ratio:1/1;width:min(100%,760px);margin:0 auto;border:1px solid var(--line2);border-radius:8px;overflow:hidden;background:#0a0b09;container-type:inline-size;display:flex;flex-direction:column}
.card::before{content:"";position:absolute;inset:0;background:radial-gradient(120% 80% at 100% 0%,rgb(69 201 194 / 9%) 0,transparent 55%),radial-gradient(90% 70% at 0% 100%,rgb(207 230 60 / 7%) 0,transparent 60%)}
.card>*{position:relative;z-index:2}
.stripe{position:absolute;inset:0 0 auto 0;height:4px;z-index:3;background:var(--accent)}
.card-head{display:flex;align-items:center;justify-content:space-between;gap:14px;padding:2.2cqw 2.6cqw 0}
.chead{display:flex;align-items:center;gap:9px}
.chead img{width:2.6cqw;height:2.6cqw;min-width:22px;min-height:22px;border-radius:4px}
.chead b{display:block;font-size:1.7cqw;line-height:1.2}
.chead span{display:block;font-family:var(--mono);font-size:1.3cqw;color:var(--muted)}
.pno{font-family:var(--mono);font-size:1.4cqw;color:var(--accent);letter-spacing:.1em}
.card-body{flex:1;min-height:0;display:grid;grid-template-rows:auto minmax(0,1fr);gap:1.5cqw;padding:1.4cqw 2.6cqw}
.said{display:grid;grid-template-columns:auto minmax(0,1fr);gap:0 2.4cqw;align-items:start}
.said .num{grid-row:1/3}
.lead-tag{display:inline-block;font-family:var(--mono);font-size:1.25cqw;letter-spacing:.09em;text-transform:uppercase;color:var(--accent);border:1px solid currentcolor;border-radius:999px;padding:.45cqw 1cqw}
.metric{font-family:var(--display);font-weight:900;font-size:5.6cqw;line-height:.95;letter-spacing:-.03em;color:var(--accent);margin:.8cqw 0 0;white-space:nowrap}
.card h2{font-family:var(--display);font-size:2.7cqw;line-height:1.1;margin:.6cqw 0 .7cqw;font-weight:700}
.card .t{font-size:1.55cqw;line-height:1.42;color:var(--ink2);margin:0}
.kchips{display:flex;flex-wrap:wrap;gap:.6cqw;margin-top:.9cqw}
.kchip{font-family:var(--mono);font-size:1.18cqw;border:1px solid currentcolor;border-radius:999px;padding:.4cqw .85cqw;white-space:nowrap}
.kchip.l{color:var(--lula)}.kchip.b{color:var(--flavio)}.kchip.a{color:var(--amber)}.kchip.c{color:var(--cyan)}.kchip.g{color:var(--green)}
.viz{border:1px solid var(--line);border-radius:6px;background:rgb(244 242 234 / 5%);padding:1.3cqw;min-width:0;min-height:0;display:flex;align-items:center;justify-content:center}
.viz svg{width:100%;height:100%;max-height:100%;display:block}
.card-foot{flex:0 0 auto;display:flex;justify-content:space-between;gap:12px;padding:1.2cqw 2.6cqw;font-family:var(--mono);font-size:1.15cqw;color:var(--faint);border-top:1px solid var(--line)}
.copy{margin:14px auto 0;width:min(100%,760px);border:1px solid var(--line);border-radius:6px;background:var(--bg2);padding:20px 22px;font-family:var(--mono);font-size:.9rem;line-height:1.72;color:var(--ink2);white-space:pre-wrap;position:relative}
.cc{position:absolute;top:12px;right:18px;font-size:.7rem;color:var(--faint);letter-spacing:.09em}
.copy-btn{margin:10px auto 0;display:block;width:min(100%,760px);text-align:left;font-family:var(--mono);font-size:.74rem;letter-spacing:.11em;text-transform:uppercase;background:transparent;color:var(--lime);border:1px solid var(--line2);border-radius:999px;padding:9px 18px;cursor:pointer}
.copy-btn:hover{border-color:var(--lime)}
footer{margin:72px 0 0;border-top:1px solid var(--line);padding:34px 0 60px;color:var(--muted);font-size:.92rem}
footer h2{font-family:var(--display);font-size:1.6rem;margin:0 0 10px;color:var(--ink)}
@media (width <= 720px){
  body{font-size:16px}
  .card{aspect-ratio:auto}
  .card-head{padding:16px 18px 0}
  .chead img{width:26px;height:26px}
  .chead b{font-size:.92rem}
  .chead span{font-size:.72rem}
  .pno{font-size:.8rem}
  .card-body{gap:16px;padding:16px 18px 20px}
  .said{grid-template-columns:1fr}
  .said .num{grid-row:auto}
  .lead-tag{font-size:.68rem;padding:5px 11px}
  .metric{font-size:2.5rem;margin:12px 0 4px}
  .card h2{font-size:1.5rem;margin-bottom:9px}
  .card .t{font-size:.98rem;line-height:1.55}
  .kchips{gap:7px;margin-top:13px}
  .kchip{font-size:.7rem;padding:4px 9px}
  .viz{padding:14px}
  .viz svg{height:auto}
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

# Hashtag e "#" colado numa palavra no inicio de um token. O "#" de fragmento de
# URL (datafolha_21092026.html#sudeste) e endereco, nao marcador de engajamento.
HASHTAG = re.compile(r"(?:^|\s)#\w")
EMOJI = re.compile(
    "[\U0001f000-\U0001faff\U00002600-\U000027bf\U0001f1e6-\U0001f1ff⬀-⯿]"
)
MIN_CHARS = 1000
MAX_CHARS = 1500


def check(cards: list[dict], page: str) -> None:
    """Portao do produto: tamanho, travessao, hashtag e emoji."""
    for traco in ("—", "–"):
        if traco in page:
            sys.exit(f"travessao encontrado na pagina: {traco!r}")
    for card in cards:
        corpo = "\n\n".join(card["copy"])
        tamanho = len(corpo)
        if not MIN_CHARS <= tamanho <= MAX_CHARS:
            sys.exit(f"post {card['tag']} com {tamanho} caracteres, fora da faixa")
        if "—" in corpo or "–" in corpo:
            sys.exit(f"travessao no post {card['tag']}")
        if HASHTAG.search(corpo):
            sys.exit(f"hashtag no post {card['tag']}")
        if EMOJI.search(corpo):
            sys.exit(f"emoji no post {card['tag']}")


def render_card(index: int, total: int, card: dict) -> str:
    accent, kind_label = KIND[card["kind"]]
    chips = "".join(
        f'<span class="kchip {tone}">{esc(label)}</span>'
        for tone, label in card["chips"]
    )
    body = "\n\n".join(card["copy"])
    return f"""
<section class="post" id="p{index}">
  <div class="post-label">Post {index}/{total} · <b>{esc(card["tag"])}</b> · {esc(kind_label)}</div>
  <div class="card" style="--accent:{accent}">
    <div class="stripe"></div>
    <div class="card-head">
      <div class="chead"><img src="img/arvor_logo.png" alt=""><div><b>Arvor Intelligence</b><span>brasil.arvor.co · Sudeste 2026</span></div></div>
      <div class="pno">{index:02d} / {total:02d}</div>
    </div>
    <div class="card-body">
      <div class="said">
        <div class="num"><span class="lead-tag">{esc(card["tag"])}</span><div class="metric">{esc(card["metric"])}</div></div>
        <div><h2>{esc(card["title"])}</h2><p class="t">{esc(card["t"])}</p><div class="kchips">{chips}</div></div>
      </div>
      <div class="viz">{card["viz"]}</div>
    </div>
    <div class="card-foot"><span>{esc(card["foot"])}</span><span>{index:02d}/{total:02d}</span></div>
  </div>
  <div class="copy" data-copy="{esc(body)}"><span class="cc">{len(body)} caracteres</span>{esc(body)}</div>
  <button class="copy-btn" onclick="cp(this)">Copiar texto</button>
</section>"""


def main() -> None:
    cards = build_cards()
    total = len(cards)
    posts = "".join(render_card(i + 1, total, c) for i, c in enumerate(cards))
    rail = "".join(f'<a href="#p{i + 1}">{i + 1}</a>' for i in range(total))
    page = f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Datafolha 21/09/2026: a thread do Sudeste em cinco cards · Arvor</title>
<meta name="description" content="Cinco cards quadrados e o texto pronto para publicar: o Sudeste medido por dentro em SP, RJ e MG, o recorte regional contra as tres estaduais, a transferencia que o proprio instituto publicou e os limites.">
<link rel="canonical" href="https://brasil.arvor.co/datafolha_21092026_thread.html">
<link rel="icon" href="favicon.ico" sizes="any">
<link rel="icon" href="img/favicon.svg" type="image/svg+xml">
<meta name="theme-color" content="#0c0d0b">
<meta property="og:type" content="article">
<meta property="og:locale" content="pt_BR">
<meta property="og:site_name" content="Arvor Intelligence">
<meta property="og:title" content="Datafolha 21/09/2026: a thread do Sudeste em cinco cards">
<meta property="og:description" content="O Sudeste nao e um problema, sao tres. Duas reguas para a mesma regiao, a transferencia medida pelo instituto e o que falta pedir. Texto pronto para publicar.">
<meta property="og:url" content="https://brasil.arvor.co/datafolha_21092026_thread.html">
<meta property="og:image" content="https://brasil.arvor.co/img/og/datafolha_21092026_thread.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@leonardodias">
<meta name="twitter:title" content="Datafolha 21/09/2026: a thread do Sudeste em cinco cards">
<meta name="twitter:description" content="O Sudeste nao e um problema, sao tres. Duas reguas, a transferencia medida e os limites.">
<meta name="twitter:image" content="https://brasil.arvor.co/img/og/datafolha_21092026_thread.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,500;0,9..144,700;0,9..144,900;1,9..144,500&amp;family=IBM+Plex+Mono:wght@400;500;700&amp;family=IBM+Plex+Sans+Condensed:wght@400;600;700&amp;display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<header class="wrap">
  <div class="top">
    <div class="brand-lockup"><img src="img/arvor_logo.png" alt="">Arvor Intelligence · thread</div>
    <a class="back" href="datafolha_21092026.html#sudeste">Abrir o dossie</a>
  </div>
  <h1>O Sudeste nao e um problema. <em>Sao tres.</em></h1>
  <p class="deck">A camada do Sudeste do Datafolha de 21 de setembro, em cinco cards quadrados. O nacional quase nao se move e a estrela continua sendo a regua de renda. A novidade esta em SP, RJ e MG, medidos por dentro na mesma entrevista: governo do estado, Senado e Presidencia. Cada card e a imagem do post e o texto embaixo e o post, pronto para copiar.</p>
  <div class="howto"><b>Como usar.</b> Cada card e um quadrado de 760 pixels na tela, 1:1 exato acima de 720 pixels de janela, e cabe no anexo de um post. O texto embaixo tem de 1.000 a 1.500 caracteres. Nenhum numero foi digitado a mao: todos vem de <code>datafolha_21092026_sudeste.json</code>, <code>datafolha_21092026_cobertura_sudeste.json</code> e <code>datafolha_21092026_data.json</code>.</div>
</header>
<nav class="rail" aria-label="Posts"><div class="wrap"><b>Posts</b>{rail}</div></nav>
<main class="wrap">{posts}</main>
<footer class="wrap">
  <h2>Reproducao</h2>
  <p>python3 scripts/datafolha-21092026-sudeste.py, python3 scripts/datafolha-21092026-cobertura-sudeste.py e python3 scripts/datafolha-21092026-thread.py. O dossie completo esta em <a href="datafolha_21092026.html#sudeste">datafolha_21092026.html</a>, o acervo em <a href="index.html">brasil.arvor.co</a> e a base publica em <a href="assets/datafolha_21092026_sudeste.json">datafolha_21092026_sudeste.json</a>.</p>
  <p>Sensibilidade sob regua comum e leitura descritiva de pesquisa. Nao e previsao eleitoral.</p>
</footer>
<script>{JS}</script>
</body>
</html>
"""
    check(cards, page)
    OUTPUT.write_text(page, encoding="utf-8")
    print(
        json.dumps(
            {
                "arquivo": str(OUTPUT.relative_to(ROOT)),
                "cards": total,
                "caracteres": [len("\n\n".join(c["copy"])) for c in cards],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
