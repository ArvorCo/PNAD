#!/usr/bin/env python3
"""Gera o Agregador Arvor: toda pesquisa nacional sob a régua de renda da PNAD.

Lê ``docs/assets/reponderacao_pnad.json``, escrito por
``scripts/reponderacao-pnad.py``, e escreve a página, a folha de estilo e o CSV
de acompanhamento. Toda figura é SVG desenhado aqui, com os dados embutidos no
HTML: nada depende de JavaScript para pintar. O JavaScript só revela blocos ao
rolar, e a revelação fica presa à classe ``js`` posta no ``<head>``, de modo que
uma página sem script continua mostrando tudo.

A página é integralmente dirigida pelo JSON. Acrescentar um instituto, uma onda
ou uma opção de voto não exige tocar neste arquivo: basta rodar
``python3 scripts/reponderacao-pnad.py`` e depois este gerador.

Uso:
    python3 scripts/reponderacao-build.py
"""

from __future__ import annotations

import csv
import json
import math
import sys
from datetime import date
from html import escape as esc
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from svgkit import FULL, MONO, Canvas, br, inject  # noqa: E402

DOCS = ROOT / "docs"
ASSETS = DOCS / "assets"
DATA = ASSETS / "reponderacao_pnad.json"
PAGE = DOCS / "reponderacao_pnad.html"
SHEET = ASSETS / "reponderacao_pnad.css"
TABLE_CSV = ASSETS / "reponderacao_pnad.csv"
HOME_SVG = ASSETS / "reponderacao_home.svg"
TIP_SHEET = ASSETS / "reponderacao_tip.css"
TIP_SCRIPT = ASSETS / "reponderacao_tip.js"
INDEX = DOCS / "index.html"

# Paleta do papel da casa. Os tons de texto pequeno são os que passam em
# WCAG AA sobre o painel claro, medidos com scripts/contrast-audit.py.
INK = "#192e2b"
PAPER = "#f4f0e7"
PANEL = "#fffdf8"
LINE = "#c9c9bc"
MUTED = "#535b54"
GOLD = "#7d5b00"
GREEN = "#28705f"
RED = "#b84648"
RED_TXT = "#9c3439"
BLUE = "#3a6ea5"
BLUE_TXT = "#2f5c8a"

MESES = (
    "jan",
    "fev",
    "mar",
    "abr",
    "mai",
    "jun",
    "jul",
    "ago",
    "set",
    "out",
    "nov",
    "dez",
)
SHAPES = (
    "circulo",
    "quadrado",
    "triangulo",
    "losango",
    "triangulo_baixo",
    "cruz",
    "pentagono",
    "hexagono",
    "estrela",
    "gravata",
)
ROTULOS = {
    "lula": "Lula",
    "flavio": "Flávio",
    "caiado": "Caiado",
    "renan_santos": "Renan Santos",
    "zema": "Zema",
    "marcal": "Marçal",
    "cury": "Cury",
    "samara": "Samara",
    "outros": "Outros",
    "branco_nulo": "Branco e nulo",
    "indecisos": "Indecisos",
    "nao_sabe": "Não sabe",
    "nenhum": "Nenhum",
}
PAGINAS = {
    "2t": "2º turno",
    "1t": "1º turno",
    "2t_renda": "renda no 2º turno",
    "1t_renda": "renda no 1º turno",
    "2t_topline": "placar do 2º turno",
    "1t_topline": "placar do 1º turno",
    "perfil": "perfil da amostra",
    "perfil_renda": "perfil de renda",
    "topline": "placar publicado",
}
TURNOS = {"2t": "2º turno", "1t": "1º turno"}

D = json.loads(DATA.read_text(encoding="utf-8"))
BENCH = D["benchmark"]
METODO = D["metodo"]
AGG = D["agregador"]
CEN = BENCH["cenario_principal"]
CENARIOS = BENCH["cenarios"]
PESQUISAS = sorted(D["pesquisas"], key=lambda p: p["campo"]["fim"])
RECENTES = list(reversed(PESQUISAS))
INSTITUTOS = list(D["institutos"])
PAR = ("lula", "flavio")
COR = {"lula": RED, "flavio": BLUE}
COR_TXT = {"lula": RED_TXT, "flavio": BLUE_TXT}


def frase(texto: str) -> str:
    """Texto do JSON vira frase: inicial maiúscula e ponto final."""
    texto = texto.strip()
    if not texto:
        return texto
    texto = texto[0].upper() + texto[1:]
    return texto if texto[-1] in ".!?:" else texto + "."


def plural(quantidade: int, singular: str, muitos: str) -> str:
    return f"{br(quantidade, 0)} {singular if quantidade == 1 else muitos}"


def rotulo(chave: str) -> str:
    return ROTULOS.get(chave, chave.replace("_", " ").capitalize())


def forma(instituto: str) -> str:
    if instituto not in INSTITUTOS:
        INSTITUTOS.append(instituto)
    return SHAPES[INSTITUTOS.index(instituto) % len(SHAPES)]


def dia(texto: str) -> date:
    return date.fromisoformat(texto)


def curto(texto: str) -> str:
    d = dia(texto)
    return f"{d.day:02d}/{d.month:02d}"


def longo(texto: str) -> str:
    d = dia(texto)
    return f"{d.day} de {MESES[d.month - 1]}. de {d.year}"


def periodo(campo: dict) -> str:
    ini, fim = dia(campo["inicio"]), dia(campo["fim"])
    if ini.month == fim.month:
        return f"{ini.day} a {fim.day} de {MESES[fim.month - 1]}. de {fim.year}"
    return f"{curto(campo['inicio'])} a {curto(campo['fim'])}/{fim.year}"


def sinal(valor: float, casas: int = 2) -> str:
    valor = round(valor, casas)
    if valor == 0:
        valor = 0.0
    return ("+" if valor > 0 else "−" if valor < 0 else "") + br(abs(valor), casas)


def ajustado(turno: dict) -> dict:
    return turno["cenarios"][CEN]["ajustado"]


def gap(valores: dict) -> float:
    return valores["lula"] - valores["flavio"]


# --------------------------------------------------------------------------- #
# Marcadores por instituto
# --------------------------------------------------------------------------- #
def _poligono(cx: float, cy: float, r: float, lados: int, giro: float) -> str:
    pontos = []
    for i in range(lados):
        ang = giro + 2 * math.pi * i / lados
        pontos.append(f"{cx + r * math.sin(ang):.1f} {cy - r * math.cos(ang):.1f}")
    return "M" + "L".join(pontos) + "Z"


def _estrela(cx: float, cy: float, r: float) -> str:
    pontos = []
    for i in range(10):
        raio = r * 1.2 if i % 2 == 0 else r * 0.52
        ang = math.pi * i / 5
        pontos.append(
            f"{cx + raio * math.sin(ang):.1f} {cy - raio * math.cos(ang):.1f}"
        )
    return "M" + "L".join(pontos) + "Z"


# --------------------------------------------------------------------------- #
# Camada interativa: grupos com área de toque, ficha embutida na página
# --------------------------------------------------------------------------- #
TIPS: dict[str, str] = {}


def _tip_id(pesquisa: dict, turno: str) -> str:
    return f"{pesquisa['id']}|{turno}"


def registra_tip(chave: str, html: str) -> str:
    """Guarda a ficha de um alvo e devolve a chave usada no atributo data."""
    TIPS[chave] = html
    return chave


def abre_alvo(cv: Canvas, chave: str, rotulo: str) -> None:
    """Abre um grupo sensível ao ponteiro. O desenho continua sendo o do SVG."""
    cv.add(
        f'<g class="hit" role="img" aria-label="{esc(rotulo, quote=True)}"'
        f' data-k="{esc(chave, quote=True)}">'
    )


def fecha_alvo(cv: Canvas) -> None:
    cv.add("</g>")


def area_alvo(cv: Canvas, cx: float, cy: float, r: float) -> None:
    """Alvo circular transparente, maior que o marcador, para o ponteiro pegar."""
    cv.circle(cx, cy, r, "transparent", **{"class": "hit-area"})


def halo(cv: Canvas, cx: float, cy: float, r: float, cor: str) -> None:
    """Anel que só aparece no hover, para dizer qual ponto está sendo lido."""
    cv.circle(
        cx,
        cy,
        r,
        "none",
        stroke=cor,
        stroke_width=2,
        **{"class": "hit-halo"},
    )


def ficha_onda(pesquisa: dict, turno: str) -> str:
    """Ficha completa de uma onda: documento, placar publicado e reponderado."""
    t = pesquisa["turnos"][turno]
    adj = ajustado(t)
    pub = t["publicado"]
    linhas = [
        '<table class="tip-tab"><thead><tr><th></th>'
        + "".join(f"<th>{esc(rotulo(c))}</th>" for c in PAR)
        + "<th>dif.</th></tr></thead><tbody>"
    ]
    for nome, fonte, cls in (
        ("publicado", pub, "pub"),
        ("reponderado", adj, "adj"),
    ):
        linhas.append(
            f'<tr class="{cls}"><th scope="row">{nome}</th>'
            + "".join(f"<td>{br(fonte[c], 1)}</td>" for c in PAR)
            + f"<td>{sinal(gap(fonte), 1)}</td></tr>"
        )
    linhas.append("</tbody></table>")
    extras = [c for c in t["opcoes"] if c not in PAR and pub.get(c, 0) >= 1]
    corpo = [
        f'<p class="tip-head"><b>{esc(pesquisa["instituto"])}</b>'
        f"<span>{esc(TURNOS[turno])}</span></p>",
        f'<p class="tip-doc">campo {esc(periodo(pesquisa["campo"]))} · '
        f'n = {br(pesquisa["n"], 0)} · {esc(pesquisa.get("registro_tse") or "sem registro")}</p>',
        "".join(linhas),
        f'<p class="tip-nota">Margem de 95% da diferença publicada: ±{br(t.get("margem_diferenca_95", 0.0), 1)}.',
    ]
    desvio = pesquisa["desvio_ate_primeira_faixa"]
    if desvio >= 0:
        composicao = f"A amostra tem {br(desvio, 1)} pontos a mais na faixa mais pobre que a PNAD."
    else:
        composicao = f"A amostra tem {br(-desvio, 1)} pontos a menos na faixa mais pobre que a PNAD."
    corpo.append(f" {composicao} Prova de leitura: {br(t['residuo_max'], 2)}.</p>")
    if extras:
        itens = ", ".join(f"{esc(rotulo(c))} {br(pub[c], 1)}" for c in extras[:6])
        corpo.append(f'<p class="tip-nota">Também na cédula: {itens}.</p>')
    return "".join(corpo)


def resumo_onda(pesquisa: dict, turno: str) -> str:
    """Texto curto para leitor de tela, no aria-label do grupo."""
    t = pesquisa["turnos"][turno]
    adj = ajustado(t)
    return (
        f"{pesquisa['instituto']}, campo até {longo(pesquisa['campo']['fim'])}, "
        f"{TURNOS[turno]}: publicado Lula {br(t['publicado']['lula'], 1)} e "
        f"Flávio {br(t['publicado']['flavio'], 1)}; reponderado Lula "
        f"{br(adj['lula'], 1)} e Flávio {br(adj['flavio'], 1)}."
    )


def alvo_onda(cv: Canvas, pesquisa: dict, turno: str) -> str:
    """Abre o grupo de uma onda e devolve a chave da ficha."""
    chave = registra_tip(_tip_id(pesquisa, turno), ficha_onda(pesquisa, turno))
    abre_alvo(cv, chave, resumo_onda(pesquisa, turno))
    return chave


def marcador(
    cv: Canvas, shape: str, cx: float, cy: float, r: float, cor: str, cheio: bool
) -> None:
    """Ponto de pesquisa. Vazado é o publicado; preenchido é o reponderado."""
    fill = cor if cheio else PANEL
    stroke = PANEL if cheio else cor
    sw = 1.2 if cheio else 2.1
    kw = {"stroke": stroke, "stroke_width": sw, "stroke_linejoin": "round"}
    if shape == "quadrado":
        cv.rect(cx - r, cy - r, 2 * r, 2 * r, fill, **kw)
    elif shape == "triangulo":
        cv.path(
            f"M{cx:.1f} {cy - r * 1.2:.1f}L{cx + r * 1.1:.1f} {cy + r * 0.85:.1f}"
            f"L{cx - r * 1.1:.1f} {cy + r * 0.85:.1f}Z",
            fill=fill,
            **kw,
        )
    elif shape == "triangulo_baixo":
        cv.path(
            f"M{cx:.1f} {cy + r * 1.2:.1f}L{cx + r * 1.1:.1f} {cy - r * 0.85:.1f}"
            f"L{cx - r * 1.1:.1f} {cy - r * 0.85:.1f}Z",
            fill=fill,
            **kw,
        )
    elif shape == "losango":
        cv.path(
            f"M{cx:.1f} {cy - r * 1.25:.1f}L{cx + r * 1.25:.1f} {cy:.1f}"
            f"L{cx:.1f} {cy + r * 1.25:.1f}L{cx - r * 1.25:.1f} {cy:.1f}Z",
            fill=fill,
            **kw,
        )
    elif shape == "pentagono":
        cv.path(_poligono(cx, cy, r * 1.2, 5, 0), fill=fill, **kw)
    elif shape == "hexagono":
        cv.path(_poligono(cx, cy, r * 1.15, 6, 0), fill=fill, **kw)
    elif shape == "estrela":
        cv.path(_estrela(cx, cy, r), fill=fill, **kw)
    elif shape == "gravata":
        cv.path(
            f"M{cx - r:.1f} {cy - r:.1f}L{cx + r:.1f} {cy - r:.1f}"
            f"L{cx - r:.1f} {cy + r:.1f}L{cx + r:.1f} {cy + r:.1f}Z",
            fill=fill,
            **kw,
        )
    elif shape == "cruz":
        b = r * 0.48
        cv.path(
            f"M{cx - b:.1f} {cy - r:.1f}H{cx + b:.1f}V{cy - b:.1f}H{cx + r:.1f}"
            f"V{cy + b:.1f}H{cx + b:.1f}V{cy + r:.1f}H{cx - b:.1f}V{cy + b:.1f}"
            f"H{cx - r:.1f}V{cy - b:.1f}H{cx - b:.1f}Z",
            fill=fill,
            **kw,
        )
    else:
        cv.circle(cx, cy, r, fill, **kw)


def meses_no_intervalo(d0: date, d1: date) -> list[date]:
    ano, mes, saida = d0.year, d0.month, []
    while True:
        atual = date(ano, mes, 1)
        if atual > d1:
            return saida
        if atual >= d0:
            saida.append(atual)
        mes += 1
        if mes > 12:
            mes, ano = 1, ano + 1


def caminho(pontos: list[tuple[float, float]]) -> str:
    return "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in pontos)


# --------------------------------------------------------------------------- #
# Figura principal: série temporal publicada contra reponderada
# --------------------------------------------------------------------------- #
def serie_svg(ident: str, turno: str, compacta: bool = False) -> str:
    serie = AGG["serie"]
    datas = [dia(t) for t in serie["datas"]]
    pub, adj = serie[turno]["publicado"], serie[turno]["ajustado"]
    polls = [p for p in PESQUISAS if turno in p["turnos"]]

    valores: list[float] = []
    for fonte in (pub, adj):
        for chave in PAR:
            valores += [v for v in fonte[chave] if v is not None]
    for p in polls:
        t = p["turnos"][turno]
        for chave in PAR:
            valores.append(t["publicado"][chave])
            valores.append(ajustado(t)[chave])
    lo = math.floor((min(valores) - 2.0) / 5) * 5
    hi = math.ceil((max(valores) + 2.0) / 5) * 5

    legendas = 1 if compacta else (2 if len(INSTITUTOS) > 1 else 1)
    altura = 360 if compacta else 400 + 30 * legendas
    largura = FULL
    esq, dir_ = 54, largura - (168 if compacta else 190)
    topo, base = (30 if compacta else 44), altura - (
        46 if compacta else 46 + 30 * legendas
    )

    d0, d1 = datas[0], datas[-1]
    vao = max((d1 - d0).days, 1)
    folga = max(round(vao * 0.035), 3)

    def px(d: date) -> float:
        return esq + (dir_ - esq) * ((d - d0).days + folga) / (vao + folga * 2)

    def py(v: float) -> float:
        return base - (base - topo) * (v - lo) / (hi - lo)

    cv = Canvas(
        largura,
        altura,
        aria=(
            f"Série do {TURNOS[turno]}: intenção de voto publicada e reponderada "
            "pela distribuição de renda da PNAD."
        ),
    )
    cv.rect(0, 0, largura, altura, PANEL)

    passo = 5 if hi - lo <= 40 else 10
    grade = lo
    while grade <= hi:
        cv.line(esq, py(grade), dir_, py(grade), stroke=LINE, width=1)
        cv.label(esq - 10, py(grade) + 4, f"{grade}%", anchor="end", size=12)
        grade += passo
    cv.line(esq, base, dir_, base, stroke=INK, width=1.4)

    for m in meses_no_intervalo(d0, d1):
        x = px(m)
        cv.line(x, base, x, base + 6, stroke=INK, width=1)
        cv.label(
            x,
            base + 22,
            f"{MESES[m.month - 1]}/{str(m.year)[2:]}",
            anchor="middle",
            size=12,
        )

    for chave in PAR:
        for nome, dados in (("publicado", pub), ("ajustado", adj)):
            trecho: list[tuple[float, float]] = []
            for d, v in zip(datas, dados[chave], strict=True):
                if v is None:
                    if len(trecho) > 1:
                        _linha(cv, trecho, COR[chave], nome)
                    trecho = []
                    continue
                trecho.append((px(d), py(v)))
            if len(trecho) > 1:
                _linha(cv, trecho, COR[chave], nome)

    raio = 4.6 if compacta else (5.8 if len(polls) <= 8 else 4.4)
    alcance = max(raio * 2.0, 9.0)
    for p in polls:
        t = p["turnos"][turno]
        x = px(dia(p["campo"]["fim"]))
        shape = forma(p["instituto"])
        alvo_onda(cv, p, turno)
        cv.line(x, topo, x, base, stroke=INK, width=1, **{"class": "hit-cross"})
        for chave in PAR:
            y_pub, y_adj = py(t["publicado"][chave]), py(ajustado(t)[chave])
            cv.line(
                x, y_pub, x, y_adj, stroke=COR[chave], width=1.3, stroke_dasharray="2 3"
            )
            halo(cv, x, y_pub, raio + 4.5, COR[chave])
            halo(cv, x, y_adj, raio + 4.5, COR[chave])
            marcador(cv, shape, x, y_pub, raio, COR[chave], False)
            marcador(cv, shape, x, y_adj, raio, COR[chave], True)
            area_alvo(cv, x, y_pub, alcance)
            area_alvo(cv, x, y_adj, alcance)
        fecha_alvo(cv)

    _bloco_direita(cv, turno, pub, adj, dir_, topo, base, py, compacta)

    if not compacta:
        _legenda(cv, esq, base + 52, largura)
        if legendas > 1:
            _legenda_institutos(cv, esq, base + 82)
    return cv.render()


def _linha(cv: Canvas, pontos: list[tuple[float, float]], cor: str, tipo: str) -> None:
    if tipo == "publicado":
        cv.path(
            caminho(pontos),
            fill="none",
            stroke=cor,
            stroke_width=1.7,
            stroke_dasharray="7 5",
            opacity="0.7",
        )
    else:
        cv.path(
            caminho(pontos),
            fill="none",
            stroke=cor,
            stroke_width=3.6,
            stroke_linejoin="round",
            stroke_linecap="round",
        )


def _ultimo(dados: list) -> float | None:
    for v in reversed(dados):
        if v is not None:
            return v
    return None


def _bloco_direita(cv, turno, pub, adj, dir_, topo, base, py, compacta) -> None:
    """Rótulos de fim de linha: o número que o leitor leva sem ler o resto."""
    alto = 66
    blocos = []
    for chave in PAR:
        fim_adj, fim_pub = _ultimo(adj[chave]), _ultimo(pub[chave])
        if fim_adj is None:
            continue
        blocos.append((py(fim_adj), chave, fim_adj, fim_pub))
    blocos.sort()
    livre = topo
    postos = []
    for centro, chave, val_adj, val_pub in blocos:
        y = max(centro - alto / 2, livre)
        y = min(y, base - alto)
        livre = y + alto + 10
        postos.append((y, centro, chave, val_adj, val_pub))
    for y, centro, chave, val_adj, val_pub in postos:
        x = dir_ + 16
        cv.line(dir_, centro, x - 6, y + alto / 2, stroke=COR[chave], width=1.2)
        cv.text(
            x,
            y + 12,
            rotulo(chave).upper(),
            size=11,
            fill=COR_TXT[chave],
            weight=700,
            letter_spacing="0.09em",
        )
        cv.number(
            x,
            y + 43,
            br(val_adj, 1) + "%",
            size=30 if not compacta else 27,
            fill=COR_TXT[chave],
        )
        if val_pub is not None:
            cv.text(
                x,
                y + 59,
                f"publicado {br(val_pub, 1)}%",
                size=11.5,
                fill=MUTED,
                family=MONO,
            )


def _legenda(cv: Canvas, x0: float, y: float, largura: float) -> None:
    itens = [
        ("marcador_vazado", "ponto publicado pelo instituto", "FATO"),
        ("marcador_cheio", "ponto reponderado pela PNAD", "INFERÊNCIA"),
        ("linha_tracejada", "média Arvor publicada", "FATO"),
        ("linha_solida", "média Arvor reponderada", "INFERÊNCIA"),
    ]
    x = x0
    for tipo, texto, marca in itens:
        if tipo == "marcador_vazado":
            marcador(cv, "circulo", x + 8, y, 5.6, INK, False)
        elif tipo == "marcador_cheio":
            marcador(cv, "circulo", x + 8, y, 5.6, INK, True)
        elif tipo == "linha_tracejada":
            cv.line(x, y, x + 26, y, stroke=INK, width=1.7, stroke_dasharray="7 5")
        else:
            cv.line(x, y, x + 26, y, stroke=INK, width=3.6, stroke_linecap="round")
        cv.text(x + 34, y + 4, texto, size=12.5, fill=INK)
        largura_texto = 34 + len(texto) * 6.6
        cv.text(
            x + largura_texto + 8,
            y + 4,
            marca,
            size=10.5,
            fill=GOLD if marca == "INFERÊNCIA" else GREEN,
            weight=700,
            letter_spacing="0.08em",
        )
        x += largura_texto + 8 + len(marca) * 7.4 + 26
        if x > largura - 200:
            x, y = x0, y + 26


def _legenda_institutos(cv: Canvas, x0: float, y: float) -> None:
    x = x0
    for nome in INSTITUTOS:
        marcador(cv, forma(nome), x + 7, y, 5.6, INK, True)
        cv.text(x + 20, y + 4, nome, size=12.5, fill=INK)
        x += 20 + len(nome) * 7.2 + 26


# --------------------------------------------------------------------------- #
# Figura: manchete contra régua
# --------------------------------------------------------------------------- #
def gap_svg(ident: str, turno: str) -> str:
    polls = [p for p in PESQUISAS if turno in p["turnos"]]
    apertado = len(polls) > 14
    linha_alt = 48 if apertado else 66
    altura = 96 + linha_alt * len(polls) + 46
    largura = FULL
    esq = 300
    dir_ = largura - 44
    meio = (esq + dir_) / 2

    limite = 2.0
    for p in polls:
        t = p["turnos"][turno]
        limite = max(
            limite,
            abs(t["gap_publicado"]) + t["margem_diferenca_95"],
            abs(t["gap_ajustado"]),
        )
    limite = math.ceil(limite / 2) * 2

    def px(v: float) -> float:
        return meio + (dir_ - meio) * v / limite

    cv = Canvas(
        largura,
        altura,
        aria=(
            f"Diferença Lula menos Flávio no {TURNOS[turno]}, publicada e "
            "reponderada, com a margem de 95% da diferença."
        ),
    )
    cv.rect(0, 0, largura, altura, PANEL)
    hatch_red = cv.hatch(f"{ident}-hr", RED, 0.3)
    hatch_blue = cv.hatch(f"{ident}-hb", BLUE, 0.3)

    cv.text(
        meio - 18,
        26,
        "◀ Flávio à frente",
        size=12.5,
        fill=BLUE_TXT,
        weight=700,
        anchor="end",
    )
    cv.text(meio + 18, 26, "Lula à frente ▶", size=12.5, fill=RED_TXT, weight=700)
    for marca in range(-limite, limite + 1, 2):
        x = px(marca)
        cv.line(x, 40, x, altura - 46, stroke=LINE, width=1)
        cv.label(x, altura - 28, br(abs(marca), 0), anchor="middle", size=11.5)
    cv.line(meio, 40, meio, altura - 46, stroke=INK, width=1.6)
    cv.label(
        meio, altura - 12, "diferença em pontos percentuais", anchor="middle", size=11.5
    )

    y = 52
    for p in polls:
        t = p["turnos"][turno]
        alvo_onda(cv, p, turno)
        cv.rect(20, y, dir_ - 20, linha_alt, "transparent", **{"class": "hit-area"})
        cv.rect(
            20,
            y,
            dir_ - 20,
            linha_alt,
            "none",
            stroke=INK,
            stroke_width=1.5,
            **{"class": "hit-halo"},
        )
        cv.line(20, y, dir_, y, stroke=LINE, width=1)
        cv.text(
            20,
            y + (18 if apertado else 22),
            p["instituto"],
            size=13 if apertado else 14.5,
            fill=INK,
            weight=700,
        )
        campo = f"campo até {curto(p['campo']['fim'])}/{dia(p['campo']['fim']).year}"
        if apertado:
            cv.text(
                20,
                y + 34,
                f"{curto(p['campo']['fim'])} · n = {br(p['n'], 0)}",
                size=10.5,
                fill=MUTED,
                family=MONO,
            )
        else:
            cv.text(20, y + 39, campo, size=11, fill=MUTED, family=MONO)
            cv.text(
                20,
                y + 54,
                f"n = {br(p['n'], 0)} · {p['registro_tse']}",
                size=11,
                fill=MUTED,
                family=MONO,
            )

        barra = 11 if apertado else 13
        for nome, valor, altura_barra, deslocamento in (
            ("publicado", t["gap_publicado"], barra, 6 if apertado else 9),
            ("reponderado", t["gap_ajustado"], barra, 25 if apertado else 33),
        ):
            cor = RED if valor >= 0 else BLUE
            fill = (
                cor
                if nome == "publicado"
                else (hatch_red if valor >= 0 else hatch_blue)
            )
            x0, x1 = sorted((px(0), px(valor)))
            cv.rect(
                x0,
                y + deslocamento,
                x1 - x0,
                altura_barra,
                fill,
                stroke=cor,
                stroke_width=1,
            )
            cv.text(
                esq - 14,
                y + deslocamento + altura_barra - 2,
                nome,
                size=10.5 if apertado else 11,
                fill=MUTED,
                anchor="end",
                family=MONO,
            )
            fim = px(valor)
            ancora = "start" if valor >= 0 else "end"
            cv.text(
                fim + (8 if valor >= 0 else -8),
                y + deslocamento + altura_barra - 2,
                sinal(valor, 1),
                size=12 if apertado else 13,
                fill=RED_TXT if valor >= 0 else BLUE_TXT,
                weight=700,
                anchor=ancora,
                family=MONO,
            )

        margem = t["margem_diferenca_95"]
        ym = y + (6 if apertado else 9) + barra / 2
        a, b = px(t["gap_publicado"] - margem), px(t["gap_publicado"] + margem)
        cv.line(a, ym, b, ym, stroke=INK, width=1.4)
        cv.line(a, ym - 6, a, ym + 6, stroke=INK, width=1.4)
        cv.line(b, ym - 6, b, ym + 6, stroke=INK, width=1.4)
        fecha_alvo(cv)
        y += linha_alt

    cv.line(20, y, dir_, y, stroke=LINE, width=1)
    return cv.render()


# --------------------------------------------------------------------------- #
# Figura: painel por instituto
# --------------------------------------------------------------------------- #
def instituto_svg(nome: str, turno: str) -> str:
    polls = [p for p in PESQUISAS if p["instituto"] == nome and turno in p["turnos"]]
    largura, altura = 380, 258
    esq, dir_, topo, base = 44, largura - 16, 30, altura - 54
    cv = Canvas(
        largura, altura, aria=f"{nome}: {TURNOS[turno]} publicado e reponderado."
    )
    cv.rect(0, 0, largura, altura, PANEL)
    if not polls:
        cv.text(esq, topo + 40, "sem onda com esse turno", size=13, fill=MUTED)
        return cv.render()

    valores: list[float] = []
    for p in polls:
        t = p["turnos"][turno]
        for chave in PAR:
            valores += [t["publicado"][chave], ajustado(t)[chave]]
    lo = math.floor((min(valores) - 2) / 5) * 5
    hi = math.ceil((max(valores) + 2) / 5) * 5

    def py(v: float) -> float:
        return base - (base - topo) * (v - lo) / (hi - lo)

    def px(i: int) -> float:
        if len(polls) == 1:
            return (esq + dir_) / 2
        return esq + (dir_ - esq - 24) * i / (len(polls) - 1) + 12

    marca = lo
    while marca <= hi:
        cv.line(esq, py(marca), dir_, py(marca), stroke=LINE, width=1)
        cv.label(esq - 8, py(marca) + 4, f"{marca}", anchor="end", size=11)
        marca += 5
    cv.line(esq, base, dir_, base, stroke=INK, width=1.2)

    shape = forma(nome)
    for chave in PAR:
        pub = [
            (px(i), py(p["turnos"][turno]["publicado"][chave]))
            for i, p in enumerate(polls)
        ]
        adj = [
            (px(i), py(ajustado(p["turnos"][turno])[chave]))
            for i, p in enumerate(polls)
        ]
        if len(polls) > 1:
            _linha(cv, pub, COR[chave], "publicado")
            _linha(cv, adj, COR[chave], "ajustado")
        for indice, (ponto_pub, ponto_adj) in enumerate(zip(pub, adj, strict=True)):
            x, y_pub = ponto_pub
            y_adj = ponto_adj[1]
            alvo_onda(cv, polls[indice], turno)
            cv.line(
                x, y_pub, x, y_adj, stroke=COR[chave], width=1.2, stroke_dasharray="2 3"
            )
            halo(cv, x, y_pub, 9.0, COR[chave])
            halo(cv, x, y_adj, 9.0, COR[chave])
            marcador(cv, shape, x, y_pub, 4.6, COR[chave], False)
            marcador(cv, shape, x, y_adj, 4.6, COR[chave], True)
            area_alvo(cv, x, y_pub, 10.0)
            area_alvo(cv, x, y_adj, 10.0)
            fecha_alvo(cv)

    passo = max(1, math.ceil(len(polls) / 6))
    for i, p in enumerate(polls):
        if (len(polls) - 1 - i) % passo:
            continue
        cv.label(px(i), base + 20, curto(p["campo"]["fim"]), anchor="middle", size=11)
    ultimo = polls[-1]["turnos"][turno]
    cv.text(
        esq,
        altura - 12,
        f"{sinal(ultimo['gap_publicado'], 1)} publicado · {sinal(ultimo['gap_ajustado'], 1)} reponderado",
        size=12,
        fill=MUTED,
        family=MONO,
    )
    return cv.render()


# --------------------------------------------------------------------------- #
# Figura: composição de renda de cada pesquisa
# --------------------------------------------------------------------------- #
def ficha_faixa(pesquisa: dict, indice: int) -> str:
    """Ficha de uma faixa de renda: o que o instituto tinha e o que a PNAD mede."""
    renda = pesquisa["renda"]
    faixa = renda["faixas"][indice]
    amostra = renda["amostra_pct"][indice]
    corte = renda["cortes_brl_202604"][indice]
    piso = renda["cortes_brl_202604"][indice - 1] if indice else 0.0
    linhas = [
        f'<p class="tip-head"><b>{esc(faixa)}</b>'
        f'<span>{esc(pesquisa["instituto"])}</span></p>'
    ]
    if corte is None:
        regua = f"acima de R$ {br(piso, 0)}"
    elif indice == 0:
        regua = f"até R$ {br(corte, 0)}"
    else:
        regua = f"de R$ {br(piso, 0)} a R$ {br(corte, 0)}"
    linhas.append(
        f'<p class="tip-doc">na régua da PNAD, {esc(regua)} a preços de abr. de 2026</p>'
    )
    linhas.append(
        '<table class="tip-tab"><thead><tr><th></th><th>fatia</th></tr></thead><tbody>'
    )
    for nome, valor, cls in (
        ("amostra", amostra, "pub"),
        ("PNAD 16+", renda["pnad_pct"][CEN][indice], "adj"),
    ):
        linhas.append(
            f'<tr class="{cls}"><th scope="row">{nome}</th>'
            f"<td>{br(valor, 1)}%</td></tr>"
        )
    delta = amostra - renda["pnad_pct"][CEN][indice]
    linhas.append("</tbody></table>")
    lado = "acima" if delta >= 0 else "abaixo"
    linhas.append(
        f'<p class="tip-nota">A amostra está {br(abs(delta), 1)} pontos {lado} da '
        "régua oficial nesta faixa. A reponderação corrige exatamente isso, "
        "mantendo o voto medido dentro dela.</p>"
    )
    return "".join(linhas)


def renda_svg(pesquisa: dict) -> str:
    renda = pesquisa["renda"]
    faixas = renda["faixas"]
    amostra = renda["amostra_pct"]
    alvo = renda["pnad_pct"][CEN]
    largura = 566
    alto_grupo = 78
    altura = 66 + alto_grupo * len(faixas) + 34
    esq, dir_ = 210, largura - 78
    maximo = max(max(amostra), max(alvo), 10) * 1.06

    cv = Canvas(
        largura, altura, aria="Composição de renda: amostra do instituto contra a PNAD."
    )
    cv.rect(0, 0, largura, altura, PANEL)
    cv.text(
        16,
        24,
        "AMOSTRA DO INSTITUTO",
        size=10.5,
        fill=INK,
        weight=700,
        letter_spacing="0.08em",
    )
    cv.text(
        16,
        40,
        "PNAD PESSOAS 16+",
        size=10.5,
        fill=GREEN,
        weight=700,
        letter_spacing="0.08em",
    )

    y = 58
    for i, faixa in enumerate(faixas):
        chave = registra_tip(f"{pesquisa['id']}|renda|{i}", ficha_faixa(pesquisa, i))
        abre_alvo(
            cv,
            chave,
            f"{faixa}: amostra {br(amostra[i], 1)}%, PNAD {br(alvo[i], 1)}%.",
        )
        cv.rect(
            8, y, largura - 16, alto_grupo - 6, "transparent", **{"class": "hit-area"}
        )
        cv.rect(
            8,
            y,
            largura - 16,
            alto_grupo - 6,
            "none",
            stroke=GOLD,
            stroke_width=1.5,
            **{"class": "hit-halo"},
        )
        cv.text(16, y + 16, faixa, size=12.5, fill=INK)
        for nome, valor, cor, deslocamento in (
            ("amostra", amostra[i], INK, 26),
            ("pnad", alvo[i], GREEN, 48),
        ):
            comprimento = (dir_ - esq) * valor / maximo
            cv.rect(esq, y + deslocamento, comprimento, 16, cor)
            cv.text(
                esq + comprimento + 8,
                y + deslocamento + 13,
                br(valor, 1) + "%",
                size=12.5,
                fill=INK if nome == "amostra" else GREEN,
                weight=700,
                family=MONO,
            )
        delta = amostra[i] - alvo[i]
        cv.text(
            esq - 12,
            y + 39,
            sinal(delta, 1),
            size=13,
            fill=GOLD,
            weight=700,
            anchor="end",
            family=MONO,
        )
        fecha_alvo(cv)
        y += alto_grupo
    cv.label(16, altura - 12, "diferença em pontos, amostra menos PNAD", size=11.5)
    return cv.render()


def _afasta(alturas: dict[str, float], minimo: float) -> dict[str, float]:
    """Separa rótulos que caem quase na mesma linha, sem mover os pontos."""
    ordem = sorted(alturas.items(), key=lambda item: item[1])
    saida: dict[str, float] = {}
    anterior = None
    for chave, y in ordem:
        if anterior is not None and y - anterior < minimo:
            y = anterior + minimo
        saida[chave] = y
        anterior = y
    return saida


# --------------------------------------------------------------------------- #
# Figura: publicado para reponderado
# --------------------------------------------------------------------------- #
def slope_svg(pesquisa: dict) -> str:
    turnos = [t for t in ("2t", "1t") if t in pesquisa["turnos"]]
    largura = 566
    alto = 236
    altura = 26 + alto * len(turnos)
    cv = Canvas(
        largura, altura, aria="Placar publicado e placar reponderado pela renda."
    )
    cv.rect(0, 0, largura, altura, PANEL)

    for indice, turno in enumerate(turnos):
        t = pesquisa["turnos"][turno]
        base_y = 26 + alto * indice
        topo, chao = base_y + 44, base_y + 176
        x0, x1 = 176, largura - 176
        valores = [t["publicado"][c] for c in PAR] + [ajustado(t)[c] for c in PAR]
        lo = math.floor((min(valores) - 3) / 5) * 5
        hi = math.ceil((max(valores) + 3) / 5) * 5

        def py(v: float, topo=topo, chao=chao, lo=lo, hi=hi) -> float:
            return chao - (chao - topo) * (v - lo) / (hi - lo)

        cv.text(
            16,
            base_y + 16,
            TURNOS[turno].upper(),
            size=10.5,
            fill=INK,
            weight=700,
            letter_spacing="0.1em",
        )
        cv.line(x0, topo - 14, x0, chao + 14, stroke=LINE, width=1)
        cv.line(x1, topo - 14, x1, chao + 14, stroke=LINE, width=1)
        cv.label(x0, chao + 32, "publicado", anchor="middle", size=11.5)
        cv.label(x1, chao + 32, "reponderado", anchor="middle", size=11.5)

        rotulo_y = {
            lado: _afasta({c: py(fonte(t)[c]) for c in PAR}, 17)
            for lado, fonte in (
                ("pub", lambda t: t["publicado"]),
                ("adj", ajustado),
            )
        }
        for chave in PAR:
            a, b = t["publicado"][chave], ajustado(t)[chave]
            ya, yb = py(a), py(b)
            cv.line(
                x0, ya, x1, yb, stroke=COR[chave], width=3.4, stroke_linecap="round"
            )
            marcador(cv, "circulo", x0, ya, 6, COR[chave], False)
            marcador(cv, "circulo", x1, yb, 6, COR[chave], True)
            cv.text(
                x0 - 14,
                rotulo_y["pub"][chave] + 5,
                f"{rotulo(chave)} {br(a, 1)}",
                size=13.5,
                fill=COR_TXT[chave],
                weight=700,
                anchor="end",
            )
            cv.text(
                x1 + 14,
                rotulo_y["adj"][chave] + 5,
                f"{br(b, 1)} {rotulo(chave)}",
                size=13.5,
                fill=COR_TXT[chave],
                weight=700,
            )
        cv.text(
            (x0 + x1) / 2,
            base_y + 32,
            f"diferença {sinal(t['gap_publicado'], 1)} para {sinal(t['gap_ajustado'], 1)}",
            size=12.5,
            fill=MUTED,
            anchor="middle",
            family=MONO,
        )
    return cv.render()


# --------------------------------------------------------------------------- #
# Blocos de HTML
# --------------------------------------------------------------------------- #
def figura(
    ident: str, kicker: str, titulo: str, svg: str, nota: str, dica: bool = True
) -> str:
    aviso = (
        '<p class="dica">Passe o ponteiro sobre uma onda para abrir a ficha</p>'
        if dica
        else ""
    )
    return (
        f'<figure class="chart-shell reveal"><p class="kicker">{esc(kicker)}</p>'
        f"<h3>{esc(titulo)}</h3>{aviso}"
        f'<div class="fig wide" id="{ident}" tabindex="0" role="region"'
        f' aria-label="{esc(titulo, quote=True)}">{svg}</div>'
        f'<figcaption class="note">{nota}</figcaption></figure>'
    )


def tabela(cabeca: list[str], linhas: list[list[str]], cls: str = "") -> str:
    corpo = "".join(
        "<tr>" + "".join(f"<td>{c}</td>" for c in linha) + "</tr>" for linha in linhas
    )
    return (
        f'<div class="table-scroll" tabindex="0" role="region" aria-label="Tabela: {esc(cabeca[0])}">'
        f'<table class="{cls}"><thead><tr>'
        + "".join(f'<th scope="col">{esc(c)}</th>' for c in cabeca)
        + f"</tr></thead><tbody>{corpo}</tbody></table></div>"
    )


def capitulo(num: int, ident: str, titulo: str, chamada: str, corpo: str) -> str:
    return (
        f'<section id="{ident}" class="chapter"><div class="wrap">'
        f'<header class="chapter-head reveal"><span class="number">{num:02}</span>'
        f'<div><h2>{titulo}</h2><p class="lead">{chamada}</p></div></header>'
        f"{corpo}</div></section>"
    )


def selo(kind: str, texto: str) -> str:
    return f'<span class="stamp {kind}">{esc(texto)}</span>'


def placar(turno: str) -> str:
    ultimo = AGG["ultimo"][turno]
    if not ultimo["institutos"]:
        return ""
    simples, kernel = ultimo["media_simples"], ultimo["kernel"]
    blocos = []
    for nome, dados in (("Média simples", simples), ("Média Arvor", kernel)):
        for tipo, marca in (("publicado", "fato"), ("ajustado", "inferencia")):
            v = dados[tipo]
            blocos.append(
                f"<div>{selo(marca, 'publicado' if tipo == 'publicado' else 'reponderado')}"
                f"<span>{esc(nome)}</span>"
                f'<b><em class="lula">{br(v["lula"], 1)}</em> × '
                f'<em class="flavio">{br(v["flavio"], 1)}</em></b>'
                f"<small>diferença {sinal(gap(v), 1)} ponto"
                f"{'s' if abs(round(gap(v), 1)) != 1 else ''}</small></div>"
            )
    lista = ", ".join(ultimo["institutos"])
    return (
        f'<div class="ledger reveal">{"".join(blocos)}</div>'
        f'<p class="note">Média simples: última onda de cada instituto, peso igual. '
        f"Média Arvor: {esc(AGG['metodo']['kernel'])}. "
        f"Institutos na conta: {esc(lista)}. Cenário: {esc(CENARIOS[CEN])}.</p>"
    )


def chip_prova(pesquisa: dict) -> str:
    partes = []
    for turno, t in pesquisa["turnos"].items():
        ok = t["residuo_max"] <= 1.0
        partes.append(
            f'<span class="proof {"ok" if ok else "warn"}">prova de leitura '
            f"{TURNOS[turno]}: resíduo {br(t['residuo_max'], 2)} ponto"
            f"{'s' if round(t['residuo_max'], 2) != 1 else ''}</span>"
        )
    return "".join(partes)


def paginas_fonte(fonte: dict) -> str:
    itens = fonte.get("paginas") or {}
    if not itens:
        return "páginas não declaradas"
    return ", ".join(
        f"p. {valor} ({PAGINAS.get(chave, chave.replace('_', ' '))})"
        for chave, valor in itens.items()
    )


def cartao(pesquisa: dict) -> str:
    renda = pesquisa["renda"]
    alvo = renda["pnad_pct"][CEN]
    desvio = pesquisa["desvio_ate_primeira_faixa"]
    dossie = pesquisa.get("dossie")
    link_dossie = (
        f' · <a href="{esc(dossie, quote=True)}">dossiê completo</a>' if dossie else ""
    )
    url = (pesquisa["fonte"] or {}).get("url")
    link_pdf = (
        f' · <a href="{esc(url, quote=True)}">PDF do relatório</a>' if url else ""
    )

    cenarios = []
    for turno, t in pesquisa["turnos"].items():
        for nome, rotulo_cenario in CENARIOS.items():
            valores = t["cenarios"][nome]["ajustado"]
            cenarios.append(
                [
                    esc(TURNOS[turno]),
                    esc(rotulo_cenario),
                    br(valores["lula"], 1),
                    br(valores["flavio"], 1),
                    sinal(gap(valores), 1),
                    "principal" if nome == CEN else "robustez",
                ]
            )

    extras = ""
    t1 = pesquisa["turnos"].get("1t")
    if t1:
        outras = [c for c in t1["opcoes"] if c not in PAR]
        if outras:
            linhas = [
                [
                    esc(rotulo(c)),
                    br(t1["publicado"][c], 1),
                    br(ajustado(t1)[c], 1),
                    sinal(ajustado(t1)[c] - t1["publicado"][c], 1),
                ]
                for c in outras
            ]
            extras = "<h4>Demais opções do 1º turno</h4>" + tabela(
                ["Opção", "Publicado", "Reponderado", "Efeito"], linhas
            )

    return (
        f'<article class="poll reveal" id="pesquisa-{esc(pesquisa["id"], quote=True)}">'
        f'<header class="poll-head"><div><h3>{esc(pesquisa["instituto"])}, '
        f"campo de {esc(periodo(pesquisa['campo']))}</h3>"
        f'<p class="note">{esc(pesquisa["registro_tse"])} · contratante {esc(pesquisa["contratante"])} · '
        f"n = {br(pesquisa['n'], 0)} · {esc(pesquisa['metodo'])} · divulgação em "
        f"{esc(longo(pesquisa['divulgacao']))}{link_dossie}{link_pdf}</p>"
        f'<p class="note">Fonte: <code>{esc(pesquisa["fonte"]["pdf"] or "sem PDF arquivado")}</code>, '
        f"{esc(paginas_fonte(pesquisa['fonte']))}.</p></div>"
        f'<div class="proofs">{chip_prova(pesquisa)}</div></header>'
        f'<div class="split">'
        f'<div class="chart-shell"><p class="kicker">Composição de renda</p>'
        f"<h4>A amostra declara {br(renda['amostra_pct'][0], 1)}% na faixa mais baixa. "
        f"A PNAD mede {br(alvo[0], 1)}%.</h4>"
        '<p class="dica">Passe o ponteiro sobre uma faixa</p>'
        f'<div class="fig" tabindex="0" role="region" aria-label="Composição de renda">'
        f"{renda_svg(pesquisa)}</div>"
        f'<p class="note">Desvio na primeira faixa: {br(desvio, 1)} pontos. '
        f"{esc(renda['nota'])}</p></div>"
        f'<div class="chart-shell"><p class="kicker">Placar sob a régua</p>'
        f"<h4>Só a margem de renda muda.</h4>"
        f'<div class="fig" tabindex="0" role="region" aria-label="Placar sob a régua">'
        f"{slope_svg(pesquisa)}</div>"
        f'<p class="note">Ponto vazado é o publicado pelo instituto. Ponto cheio é a '
        f"reponderação Arvor, que é inferência.</p></div></div>"
        + tabela(
            ["Turno", "Cenário da PNAD", "Lula", "Flávio", "Diferença", "Uso"],
            cenarios,
            cls="scenarios",
        )
        + extras
        + "</article>"
    )


# --------------------------------------------------------------------------- #
# Capítulos
# --------------------------------------------------------------------------- #
def ch_segundo_turno() -> str:
    ultimo = AGG["ultimo"]["2t"]
    kernel = ultimo["kernel"]
    corpo = (
        figura(
            "segundo-turno-chart",
            "Série do 2º turno",
            "O que os institutos publicaram e o que a mesma amostra devolve sob a renda do IBGE.",
            serie_svg("s2t", "2t"),
            "Cada onda entra pela data final do campo. A linha fina e tracejada é a média "
            "das pesquisas como foram publicadas. A linha cheia é a mesma média depois de "
            "trocar uma margem, a de renda, pela distribuição da PNAD Contínua anual de 2025. "
            "A troca é nossa, e por isso a linha cheia é inferência declarada.",
        )
        + placar("2t")
        + '<p class="plain reveal">Publicado, a média Arvor marca Lula '
        + br(kernel["publicado"]["lula"], 1)
        + " e Flávio "
        + br(kernel["publicado"]["flavio"], 1)
        + ". Sob a régua oficial de renda, marca Lula "
        + br(kernel["ajustado"]["lula"], 1)
        + " e Flávio "
        + br(kernel["ajustado"]["flavio"], 1)
        + ". A diferença sai de "
        + sinal(gap(kernel["publicado"]), 1)
        + " para "
        + sinal(gap(kernel["ajustado"]), 1)
        + " ponto para Lula.</p>"
    )
    return capitulo(
        1,
        "segundo-turno",
        "O 2º turno sob a régua oficial",
        "Uma linha por candidato, publicada e reponderada, com todos os pontos de campo à vista.",
        corpo,
    )


def ch_primeiro_turno() -> str:
    polls = [p for p in PESQUISAS if "1t" in p["turnos"]]
    if not polls:
        return capitulo(
            2,
            "primeiro-turno",
            "O 1º turno",
            "Nenhuma onda auditada publicou cruzamento de renda no 1º turno até aqui.",
            '<p class="plain reveal">Assim que uma pesquisa publicar a tabela de renda do '
            "1º turno, ela entra aqui pelo mesmo caminho.</p>",
        )
    ultimas = {}
    for p in polls:
        ultimas[p["instituto"]] = p
    linhas = []
    for p in ultimas.values():
        t = p["turnos"]["1t"]
        for chave in t["opcoes"]:
            if chave in PAR:
                continue
            linhas.append(
                [
                    esc(p["instituto"]),
                    esc(curto(p["campo"]["fim"])),
                    esc(rotulo(chave)),
                    br(t["publicado"][chave], 1),
                    br(ajustado(t)[chave], 1),
                    sinal(ajustado(t)[chave] - t["publicado"][chave], 1),
                ]
            )
    corpo = (
        figura(
            "primeiro-turno-chart",
            "Série do 1º turno",
            "Lula e Flávio no 1º turno, publicado contra reponderado.",
            serie_svg("s1t", "1t"),
            "A série começa na primeira onda que publicou o cruzamento de renda do 1º turno. "
            "Antes disso não há linha, e a ausência é declarada em vez de interpolada.",
        )
        + placar("1t")
        + '<h3 class="reveal">As demais candidaturas sob a mesma troca</h3>'
        + tabela(
            ["Instituto", "Campo", "Opção", "Publicado", "Reponderado", "Efeito"],
            linhas,
        )
        + '<p class="note">Última onda de cada instituto. O efeito é a diferença entre o '
        "reponderado e o publicado, em pontos. Todas as ondas estão no CSV e no JSON. "
        "Quem não declarou renda fica fora da conta e entra pelo topline publicado.</p>"
    )
    return capitulo(
        2,
        "primeiro-turno",
        "O 1º turno",
        "A mesma conta aplicada à primeira volta, com todas as candidaturas medidas.",
        corpo,
    )


def ch_manchete() -> str:
    polls = [p for p in PESQUISAS if "2t" in p["turnos"]]
    viradas = sum(
        1
        for p in polls
        if p["turnos"]["2t"]["gap_publicado"] > 0 >= p["turnos"]["2t"]["gap_ajustado"]
    )
    dentro = sum(
        1
        for p in polls
        if abs(p["turnos"]["2t"]["gap_publicado"])
        <= p["turnos"]["2t"]["margem_diferenca_95"]
    )
    corpo = (
        figura(
            "manchete-chart",
            "Manchete contra régua",
            "A diferença publicada, a margem de 95% dessa diferença e a diferença reponderada.",
            gap_svg("gap2t", "2t"),
            "A barra cheia é a diferença que o instituto publicou, com o bigode marcando o "
            "intervalo de 95% da diferença sob amostragem aleatória simples. A barra hachurada "
            "é a mesma diferença depois da troca da margem de renda, e é inferência nossa. "
            "O registro no TSE de cada onda está na tabela de fontes.",
        )
        + '<div class="metrics three reveal">'
        f"<article><strong>{dentro} de {len(polls)}</strong>"
        "<p>ondas em que a diferença publicada cabe dentro da própria margem de 95%. "
        "Nelas a palavra <em>lidera</em> afirma mais do que a amostra sustenta.</p></article>"
        f"<article><strong>{viradas} de {len(polls)}</strong>"
        "<p>ondas em que a vantagem publicada não sobrevive à troca da margem de renda "
        "pela distribuição oficial.</p></article>"
        f"<article><strong>{br(BENCH['totais_milhoes'][CEN], 1)} mi</strong>"
        "<p>pessoas de 16 anos ou mais representadas no histograma da PNAD que serve "
        "de régua.</p></article></div>"
        '<div class="callout reveal"><p>Uma manchete que diz <em>lidera</em> precisa passar '
        "em dois testes independentes. O primeiro é de amostragem: o intervalo de 95% da "
        "diferença não pode conter o zero. O segundo é de composição: o sinal precisa "
        "sobreviver à troca da margem dominante pela régua oficial. Os dois testes são "
        "diferentes, e uma manchete pode falhar em um e passar no outro.</p></div>"
    )
    return capitulo(
        3,
        "manchete",
        "A manchete contra a régua",
        "Diferença publicada, incerteza da diferença e diferença reponderada, na mesma linha.",
        corpo,
    )


def _painel_instituto(nome: str, turno: str) -> str:
    ondas = sum(1 for p in PESQUISAS if p["instituto"] == nome and turno in p["turnos"])
    total = sum(1 for p in PESQUISAS if p["instituto"] == nome)
    if turno == "2t" and ondas < total:
        cobertura = f"{ondas} de {total} ondas cruzam o 2º turno por renda"
    elif turno == "1t" and not any(
        "2t" in p["turnos"] for p in PESQUISAS if p["instituto"] == nome
    ):
        cobertura = f"{plural(ondas, 'onda', 'ondas')}; o instituto não cruza o 2º turno por renda"
    else:
        cobertura = plural(ondas, "onda auditada", "ondas auditadas")
    return (
        f'<article class="panel reveal"><h3>{esc(nome)} <small>{TURNOS[turno]}</small></h3>'
        f'<div class="fig">{instituto_svg(nome, turno)}</div>'
        f'<p class="note">{cobertura}. Vazado é publicado, cheio é reponderado.</p></article>'
    )


def ch_institutos() -> str:
    so_1t = [
        nome
        for nome in INSTITUTOS
        if not any(p["instituto"] == nome and "2t" in p["turnos"] for p in PESQUISAS)
    ]
    paineis = "".join(
        _painel_instituto(nome, turno)
        for nome in INSTITUTOS
        for turno in ("2t", "1t")
        if any(p["instituto"] == nome and turno in p["turnos"] for p in PESQUISAS)
    )
    return capitulo(
        4,
        "institutos",
        "Instituto por instituto",
        "O mesmo desenho repetido em painéis pequenos, para comparar a distância entre a "
        "publicação e a régua dentro de cada casa.",
        f'<div class="grid-3">{paineis}</div>'
        '<p class="note">Cada instituto recebe um painel por turno que cruza por renda: '
        f"quem só publica o 1º turno por faixa de renda ({esc(', '.join(so_1t))}) "
        "aparece só com ele. Painéis com uma só onda mostram os pontos sem linha: com uma "
        "medida não há série. A escala vertical é própria de cada painel.</p>",
    )


def ch_pesquisas() -> str:
    return capitulo(
        5,
        "pesquisas",
        "Pesquisa por pesquisa",
        "Cada onda com a ficha do documento, a composição de renda, o efeito da troca e a "
        "prova de que a leitura do relatório está certa.",
        "".join(cartao(p) for p in RECENTES),
    )


def ch_metodo() -> str:
    limites = "".join(f"<li>{esc(frase(item))}</li>" for item in METODO["limites"])
    return capitulo(
        6,
        "metodo",
        "Como a conta é feita",
        "Uma margem trocada, uma régua só, e a prova de leitura antes de qualquer número derivado.",
        '<div class="split">'
        "<article><h3>A fórmula</h3>"
        f'<p class="formula">{esc(METODO["formula"])}</p>'
        "<p>O recomposto é o placar refeito com as bases de renda do próprio instituto. "
        "Se ele não devolve o placar publicado, a leitura do relatório está errada e nada "
        "derivado dela pode ser publicado. O contrafactual é o mesmo cruzamento com os "
        "pesos da PNAD no lugar dos pesos da amostra.</p>"
        f"<p>{esc(frase(METODO['margem_unica']))}</p></article>"
        "<article><h3>A régua</h3>"
        f"<p>{esc(BENCH['benchmark'])}, variável de rendimento domiciliar, "
        f"peso <code>{esc(BENCH['weight'])}</code>, pessoas de "
        f"{BENCH['min_age']} anos ou mais, "
        f"{br(BENCH['rows_read'], 0)} registros lidos.</p>"
        f"<p>Os cortes do cartão de renda de cada pesquisa são convertidos para reais de "
        f"{MESES[int(BENCH['price_month'][4:]) - 1]}. de {BENCH['price_month'][:4]} pelo IPCA, "
        "usando o salário mínimo do ano impresso no próprio cartão. Sem isso, cartão e cota "
        "ficam em réguas de anos diferentes.</p>"
        f"<p>Cenário principal: {esc(CENARIOS[CEN])}. Os outros dois cenários aparecem em "
        "cada ficha como teste de robustez.</p></article></div>"
        '<div class="split">'
        "<article><h3>As médias</h3>"
        f"<p>{esc(frase(AGG['metodo']['kernel']))} A meia-vida é de "
        f"{br(AGG['metodo']['meia_vida_dias'], 0)} dias sobre a data final do campo, "
        "de modo que uma onda de um mês atrás pesa cerca de um quarto de uma onda "
        "desta semana.</p>"
        f"<p>{esc(frase(AGG['metodo']['media_simples']))} As duas médias aparecem lado a lado "
        "porque respondem a perguntas diferentes: a simples mostra a fotografia mais "
        "recente de cada casa, a ponderada no tempo mostra a tendência.</p></article>"
        "<article><h3>Os limites</h3>"
        f'<ol class="method-list">{limites}</ol></article></div>'
        '<div class="callout reveal"><h3>Como acrescentar uma pesquisa</h3>'
        "<p>Um arquivo JSON por onda em <code>analysis/reponderacao/pesquisas/</code>, com o "
        "perfil de renda da amostra, o cruzamento do voto por faixa e o placar publicado, "
        "cada bloco com a página do relatório ao lado. Depois:</p>"
        "<pre><code>python3 scripts/reponderacao-pnad.py calcular\n"
        "python3 scripts/reponderacao-build.py</code></pre>"
        "<p>O primeiro comando refaz a conta e reescreve "
        "<code>docs/assets/reponderacao_pnad.json</code>. O segundo regenera esta página "
        "inteira, o CSV e o gráfico da capa. Nenhum número desta página é digitado à mão.</p>"
        "</div>",
    )


def ch_fontes() -> str:
    linhas = [
        [
            esc(p["instituto"]),
            esc(periodo(p["campo"])),
            esc(p["registro_tse"]),
            br(p["n"], 0),
            f'<code>{esc(p["fonte"]["pdf"] or "sem PDF arquivado")}</code>',
            esc(paginas_fonte(p["fonte"])),
        ]
        for p in RECENTES
    ]
    return capitulo(
        7,
        "fontes",
        "Fontes e dados abertos",
        "Cada número desta página sai de um relatório registrado no TSE e de um microdado "
        "público do IBGE.",
        tabela(
            ["Instituto", "Campo", "Registro TSE", "n", "Arquivo", "Páginas"],
            linhas,
        )
        + '<div class="downloads reveal">'
        '<a class="download" href="assets/reponderacao_pnad.json"><b>JSON completo</b>'
        "<span>toda a conta, cenário por cenário, onda por onda</span></a>"
        '<a class="download" href="assets/reponderacao_pnad.csv"><b>CSV do agregador</b>'
        "<span>uma linha por pesquisa e turno, publicado e reponderado</span></a>"
        '<a class="download" href="pnad.html"><b>A PNAD por dentro</b>'
        "<span>de onde vem a distribuição de renda usada como régua</span></a></div>"
        f'<p class="note">Régua: {esc(BENCH["benchmark"])}, arquivo '
        f'<code>{esc(BENCH["source"])}</code>. Preços de '
        f"{MESES[int(BENCH['price_month'][4:]) - 1]}. de {BENCH['price_month'][:4]}. "
        f"Conta gerada em {esc(longo(D['gerado_em'][:10]))}, referência de "
        f"{esc(longo(D['referencia']))}.</p>",
    )


# --------------------------------------------------------------------------- #
# Página
# --------------------------------------------------------------------------- #
CSS = """:root{--paper:#f4f0e7;--ink:#192e2b;--panel:#fffdf8;--line:#c9c9bc;
--muted:#535b54;--gold:#7d5b00;--green:#28705f;--red:#9c3439;--blue:#2f5c8a}
*{box-sizing:border-box}
html{scroll-behavior:smooth;scroll-padding-top:64px}
body{margin:0;background:var(--paper);color:var(--ink);
font-family:"Avenir Next",Avenir,"Trebuchet MS",sans-serif;font-size:17px;line-height:1.65;
overflow-x:hidden}
a{color:inherit;text-underline-offset:4px}
a:hover{color:var(--red)}
:focus-visible{outline:3px solid #bd5332;outline-offset:4px}
code{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:.86em;
background:#192e2b0e;padding:1px 5px}
pre{overflow:auto;padding:18px;background:#192e2b0e;font-size:13px;margin:18px 0}
pre code{background:none;padding:0}
.wrap{max-width:1240px;margin:auto;padding:0 44px}
.skip{position:absolute;left:20px;top:-100px;background:var(--panel);z-index:10;padding:10px}
.skip:focus{top:10px}
.masthead{display:flex;align-items:center;justify-content:space-between;padding:24px 44px;
border-bottom:1px solid var(--ink);font-size:12px;letter-spacing:.1em;text-transform:uppercase}
.masthead>a{font-size:23px;font-weight:800;text-decoration:none;letter-spacing:-1px}
.masthead>a span{font-size:12px;letter-spacing:.06em;font-weight:500}
.hero{padding:64px 0 30px;position:relative;overflow:hidden}
.hero:after{content:"%";position:absolute;right:10px;top:20px;font-family:Georgia,serif;
font-size:clamp(260px,34vw,520px);line-height:1;color:#192e2b0b;z-index:-1}
.eyebrow{text-transform:uppercase;letter-spacing:.13em;font-size:11px;font-weight:700}
.hero h1{font-family:Georgia,"Times New Roman",serif;font-size:clamp(54px,6.8vw,100px);
line-height:1.02;font-weight:400;letter-spacing:-.06em;margin:26px 0 40px;max-width:940px}
.hero em{font-weight:400;font-style:normal;color:var(--green)}
.hero-bottom{display:grid;grid-template-columns:2.2fr repeat(3,1fr);gap:40px;
border-top:2px solid var(--ink);padding-top:24px;align-items:start}
.hero-bottom>p{font-size:19px;line-height:1.55;margin:0}
.hero-bottom>div{border-left:1px solid var(--line);padding-left:24px}
.hero-bottom strong{display:block;font-family:Georgia,serif;font-size:40px;font-weight:400;
line-height:1.2}
.hero-bottom span{font-size:12px;display:block;margin-top:8px}
.toc{position:sticky;top:0;z-index:5;display:flex;gap:26px;justify-content:center;
padding:14px 24px;background:var(--ink);color:var(--paper);font-size:12px;overflow:auto;
white-space:nowrap}
.toc a{text-decoration:none}
.toc a:hover{color:#e8c266}
.chapter{padding:70px 0;border-bottom:1px solid var(--line)}
.chapter-head{display:grid;grid-template-columns:80px 1fr;gap:22px;margin-bottom:34px}
.number{font-family:Georgia,serif;font-size:55px;line-height:1;color:var(--green)}
h2{font-family:Georgia,serif;font-size:clamp(32px,3.2vw,46px);line-height:1.15;
letter-spacing:-.035em;font-weight:400;margin:0 0 18px;max-width:900px}
h3{font-size:19px;line-height:1.3;letter-spacing:-.02em;margin:0 0 14px}
h4{font-size:16px;line-height:1.35;margin:0 0 12px;font-weight:600}
p{margin:0 0 18px;max-width:1000px}
.lead{font-size:19px;max-width:920px;line-height:1.6;margin:0}
.note{font-size:12px;line-height:1.65;color:var(--muted);margin:14px 0;max-width:900px}
.plain{font-size:19px;line-height:1.55;padding:22px 26px;border-left:4px solid #d8a631;
background:var(--panel);margin:28px 0;max-width:none}
.callout{border-left:5px solid #d8a631;padding:24px 28px;margin:32px 0;background:var(--panel)}
.callout p:last-child{margin-bottom:0}
.formula{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:14.5px;
background:#192e2b0e;padding:16px 18px;line-height:1.6}
.split{display:grid;grid-template-columns:1fr 1fr;gap:40px;margin:32px 0}
.split>article,.split>div{min-width:0}
.grid-3{display:grid;grid-template-columns:repeat(3,1fr);gap:26px;margin:30px 0}
.metrics{display:grid;gap:28px;margin:34px 0}
.metrics.three{grid-template-columns:repeat(3,1fr)}
.metrics article{border-top:3px solid var(--green);padding-top:18px;min-width:0}
.metrics strong{font-family:Georgia,serif;font-size:42px;font-weight:400;line-height:1.2;
display:block;margin-bottom:14px}
.metrics p{font-size:14px}
.metrics em{font-style:italic}
.chart-shell{border:1px solid var(--line);padding:22px 24px;margin:28px 0;
background:var(--panel);min-width:0}
.chart-shell h3,.chart-shell h4{margin:4px 0 12px}
.fig{max-width:100%;overflow-x:auto}
.fig svg{width:100%;height:auto;display:block}
.kicker{font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);
margin:0 0 6px}
figure{margin:28px 0}
figcaption{margin-top:14px}
.ledger{display:grid;grid-template-columns:repeat(4,1fr);border:1px solid var(--line);
margin:30px 0;background:var(--panel)}
.ledger>div{padding:20px 22px;border-left:1px solid var(--line);min-width:0}
.ledger>div:first-child{border-left:0}
.ledger span{display:block;font-size:11px;letter-spacing:.1em;text-transform:uppercase;
color:var(--muted);margin-top:8px}
.ledger b{display:block;font-family:Georgia,serif;font-weight:400;font-size:32px;
line-height:1.15;margin:6px 0;font-variant-numeric:tabular-nums}
.ledger em{font-style:normal}
.ledger em.lula{color:var(--red)}
.ledger em.flavio{color:var(--blue)}
.ledger small{font-size:12px;color:var(--muted);line-height:1.5;display:block}
.stamp{display:inline-block;font-size:10px;letter-spacing:.09em;text-transform:uppercase;
padding:2px 7px;border:1px solid currentColor;border-radius:3px;color:var(--green)}
.stamp.inferencia{color:var(--gold);
background:repeating-linear-gradient(45deg,transparent 0 4px,#d8a63130 4px 6px)}
.proof{display:inline-block;font-size:11px;letter-spacing:.05em;padding:5px 10px;
border-radius:3px;margin:0 0 8px;border:1px solid currentColor}
.proof.ok{color:var(--green);background:#28705f12}
.proof.warn{color:var(--gold);background:#7d5b0012}
.poll{border-top:3px solid var(--ink);padding-top:22px;margin:0 0 56px}
.poll-head{display:grid;grid-template-columns:1fr auto;gap:20px;align-items:start}
.poll-head h3{font-family:Georgia,serif;font-size:29px;font-weight:400;letter-spacing:-.02em}
.proofs{display:flex;flex-direction:column;align-items:flex-end;gap:2px}
.panel{border-top:2px solid var(--ink);padding-top:16px;min-width:0}
.panel h3{font-size:16px}.panel h3 small{font:500 12px/1 var(--mono,monospace);color:#535b54;margin-left:6px;letter-spacing:.04em}
.table-scroll{max-width:100%;overflow:auto;margin:24px 0;border-top:2px solid currentColor}
table{width:100%;border-collapse:collapse;font-size:13px;line-height:1.45;
font-variant-numeric:tabular-nums}
th{text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.04em;
padding:14px 12px;vertical-align:bottom;background:#192e2b0d}
td{padding:12px;border-top:1px solid var(--line);vertical-align:top}
td:first-child{font-weight:600;min-width:120px}
tr:hover td{background:#8ea59417}
.method-list{padding-left:20px;max-width:900px}
.method-list li{margin:0 0 14px;padding-left:6px;font-size:15px;line-height:1.6}
.downloads{display:grid;grid-template-columns:repeat(3,1fr);gap:22px;margin:30px 0}
.download{display:block;padding:20px 22px;background:var(--panel);border:1px solid var(--line);
text-decoration:none}
.download b{display:block;font-size:17px;margin-bottom:6px}
.download span{font-size:13px;color:var(--muted)}
.download:hover{border-color:var(--ink)}
.footer{display:flex;justify-content:space-between;gap:20px;padding-top:34px;
padding-bottom:34px;font-size:11px;flex-wrap:wrap}
.footer b{font-size:14px}
.footer a{color:var(--muted)}
.js .reveal{opacity:0;transform:translateY(14px);
transition:opacity .55s ease,transform .55s ease}
.js .reveal.in,.js .reveal.visible{opacity:1;transform:none}
@media(max-width:1000px){
.hero-bottom{grid-template-columns:1fr 1fr;gap:22px}
.hero-bottom>p{grid-column:1/-1}
.grid-3,.downloads{grid-template-columns:1fr 1fr}
.metrics.three{grid-template-columns:1fr}
.toc{justify-content:flex-start}
}
@media(max-width:760px){
body{font-size:16px}
.wrap{padding:0 20px}
.masthead{padding:16px 20px}
.masthead>a span{display:none}
.hero{padding:30px 0 18px}
.hero h1{font-size:52px;margin:22px 0 28px}
.hero-bottom strong{font-size:34px}
.chapter{padding:44px 0}
.chapter-head{grid-template-columns:1fr;gap:12px}
.number{font-size:32px}
h2{font-size:33px}
.lead{font-size:16px}
.split,.grid-3,.downloads{grid-template-columns:1fr;gap:26px}
.ledger{grid-template-columns:1fr 1fr}
.ledger b{font-size:25px;white-space:nowrap}
.ledger>div:nth-child(odd){border-left:0}
.ledger>div:nth-child(n+3){border-top:1px solid var(--line)}
.poll-head{grid-template-columns:1fr}
.proofs{align-items:flex-start}
.poll-head h3{font-size:24px}
.fig svg{min-width:520px}
.fig.wide svg{min-width:700px}
.panel .fig svg{min-width:0}
.plain{font-size:17px;padding:18px 20px}
th,td{padding:11px 9px}
}
@media(prefers-reduced-motion:reduce){
html{scroll-behavior:auto}
.js .reveal{opacity:1;transform:none;transition:none}
}
@media print{.toc,.skip{display:none}.chapter{break-before:page}
.js .reveal{opacity:1;transform:none}}
"""

TIP_CSS = """/* ---- camada interativa: alvo, halo e ficha ------------------------------ */
.hit{cursor:pointer}
.hit-area{fill:transparent}
.hit-halo,.hit-cross{opacity:0;pointer-events:none;transition:opacity .12s ease}
.hit-cross{stroke-dasharray:3 4;stroke-opacity:.5}
.hit:hover .hit-halo,.hit.on .hit-halo{opacity:1}
.hit:hover .hit-cross,.hit.on .hit-cross{opacity:1}
.fig.lendo .hit:not(:hover):not(.on){opacity:.42;transition:opacity .12s ease}
#tip{position:fixed;z-index:60;max-inline-size:340px;padding:14px 16px;
background:#192e2b;color:#f4f0e7;border:1px solid #0f1f1d;
box-shadow:0 10px 30px rgba(15,31,29,.34);font-size:13.5px;line-height:1.5;
pointer-events:none;opacity:0;transform:translateY(4px);transition:opacity .12s ease,transform .12s ease}
#tip.on{opacity:1;transform:translateY(0)}
#tip p{margin:0 0 8px}
#tip p:last-child{margin-bottom:0}
.tip-head{display:flex;align-items:baseline;gap:10px;font-size:15px}
.tip-head b{font-weight:800;letter-spacing:.01em}
.tip-head span{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:11px;
letter-spacing:.14em;text-transform:uppercase;color:#b9c6bd}
.tip-doc{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:11.5px;color:#b9c6bd}
.tip-tab{width:100%;border-collapse:collapse;margin:2px 0 9px;
font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:12.5px}
.tip-tab th,.tip-tab td{padding:3px 0;text-align:right;font-weight:500}
.tip-tab thead th{color:#b9c6bd;font-size:11px;letter-spacing:.06em;
border-bottom:1px solid #3d554f;text-transform:uppercase}
.tip-tab tbody th{text-align:left;color:#b9c6bd;font-weight:500;padding-right:12px}
.tip-tab tr.adj td,.tip-tab tr.adj th{color:#ffd9a3}
.tip-tab tr.pub td{color:#fffdf8}
.tip-nota{font-size:12px;color:#b9c6bd}
.dica{display:inline-flex;align-items:center;gap:7px;margin-top:2px;
font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:11.5px;
letter-spacing:.06em;text-transform:uppercase;color:#535b54}
.dica::before{content:"";inline-size:9px;block-size:9px;border:2px solid #535b54;
border-radius:50%}
@media (hover:none){.dica::after{content:"toque"}}
"""

TIP_JS = """(function(){
var fichas={};
document.querySelectorAll('script.tips').forEach(function(no){
try{var d=JSON.parse(no.textContent);for(var k in d){fichas[k]=d[k];}}catch(e){}});
if(!Object.keys(fichas).length)return;

var caixa=document.createElement('div');
caixa.id='tip';caixa.setAttribute('role','status');caixa.hidden=true;
document.body.appendChild(caixa);
var atual=null;

function fecha(){
if(!atual)return;
atual.classList.remove('on');
var fig=atual.closest('.fig');if(fig)fig.classList.remove('lendo');
atual=null;caixa.classList.remove('on');
setTimeout(function(){if(!atual)caixa.hidden=true;},140);}

function posiciona(alvo){
var r=alvo.getBoundingClientRect();
var c=caixa.getBoundingClientRect();
var margem=12;
var x=r.left+r.width/2-c.width/2;
x=Math.max(margem,Math.min(x,window.innerWidth-c.width-margem));
var y=r.top-c.height-14;
if(y<margem)y=Math.min(r.bottom+14,window.innerHeight-c.height-margem);
caixa.style.left=Math.round(x)+'px';
caixa.style.top=Math.round(Math.max(margem,y))+'px';}

function abre(alvo){
var chave=alvo.getAttribute('data-k');
var html=fichas[chave];
if(!html)return;
if(atual===alvo){posiciona(alvo);return;}
fecha();
atual=alvo;
alvo.classList.add('on');
var fig=alvo.closest('.fig');if(fig)fig.classList.add('lendo');
caixa.innerHTML=html;
caixa.hidden=false;
posiciona(alvo);
requestAnimationFrame(function(){caixa.classList.add('on');});}

function alvoDe(ev){
var no=ev.target;
return no&&no.closest?no.closest('.hit'):null;}

document.addEventListener('pointerover',function(ev){
if(ev.pointerType==='touch')return;
var alvo=alvoDe(ev);
if(alvo)abre(alvo);else if(atual&&!ev.target.closest('#tip'))fecha();});

document.addEventListener('pointerdown',function(ev){
var alvo=alvoDe(ev);
if(alvo){abre(alvo);}else{fecha();}});

document.addEventListener('keydown',function(ev){if(ev.key==='Escape')fecha();});
window.addEventListener('scroll',function(){if(atual)posiciona(atual);},{passive:true});
window.addEventListener('resize',fecha);
})();"""

SCRIPT = """(function(){
var alvos=document.querySelectorAll('.reveal');
if(!('IntersectionObserver' in window)){
for(var i=0;i<alvos.length;i++){alvos[i].classList.add('in');}}
else{var obs=new IntersectionObserver(function(itens){
itens.forEach(function(item){if(item.isIntersecting){
item.target.classList.add('in');obs.unobserve(item.target);}});},
{rootMargin:'0px 0px -6% 0px'});
alvos.forEach(function(n){obs.observe(n);});}

})();"""


def head() -> str:
    ultimo = AGG["ultimo"]["2t"]["kernel"]
    titulo = "Agregador Arvor: a corrida sob a régua oficial de renda"
    descricao = (
        f"Toda pesquisa nacional reponderada pela distribuição de renda da PNAD Contínua "
        f"anual de 2025 do IBGE. Publicada, a média marca Lula {br(ultimo['publicado']['lula'], 1)} "
        f"e Flávio {br(ultimo['publicado']['flavio'], 1)} no 2º turno. Sob a régua oficial, "
        f"Lula {br(ultimo['ajustado']['lula'], 1)} e Flávio {br(ultimo['ajustado']['flavio'], 1)}."
    )
    og = "https://brasil.arvor.co/img/og/reponderacao_pnad.png"
    alt_card = (
        f"Agregador Arvor: {len(PESQUISAS)} ondas de {len(INSTITUTOS)} institutos "
        "reponderadas pela renda da PNAD, com uma margem trocada e o resto como "
        "o instituto ponderou."
    )
    return (
        '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "<script>document.documentElement.classList.add('js')</script>"
        f"<title>{esc(titulo)} · Arvor</title>"
        f'<meta name="description" content="{esc(descricao, quote=True)}">'
        '<link rel="canonical" href="https://brasil.arvor.co/reponderacao_pnad.html">'
        '<link rel="icon" href="favicon.ico" sizes="any">'
        '<link rel="icon" href="img/favicon.svg" type="image/svg+xml">'
        '<link rel="apple-touch-icon" href="img/favicon-180.png">'
        '<meta name="theme-color" content="#192e2b">'
        '<meta property="og:type" content="article">'
        '<meta property="og:locale" content="pt_BR">'
        '<meta property="og:site_name" content="Arvor Intelligence">'
        f'<meta property="og:title" content="{esc(titulo, quote=True)}">'
        f'<meta property="og:description" content="{esc(descricao, quote=True)}">'
        '<meta property="og:url" content="https://brasil.arvor.co/reponderacao_pnad.html">'
        f'<meta property="og:image" content="{og}">'
        f'<meta property="og:image:alt" content="{esc(alt_card, quote=True)}">'
        '<meta property="og:image:width" content="1200">'
        '<meta property="og:image:height" content="630">'
        '<meta name="twitter:card" content="summary_large_image">'
        f'<meta name="twitter:image" content="{og}">'
        f'<meta name="twitter:image:alt" content="{esc(alt_card, quote=True)}">'
        f'<meta name="twitter:title" content="{esc(titulo, quote=True)}">'
        f'<meta name="twitter:description" content="{esc(descricao, quote=True)}">'
        '<link rel="stylesheet" href="assets/reponderacao_pnad.css"><link rel="stylesheet" href="assets/reponderacao_tip.css">'
        "</head>"
    )


def hero() -> str:
    ultimo = AGG["ultimo"]["2t"]["kernel"]
    dif_pub, dif_adj = gap(ultimo["publicado"]), gap(ultimo["ajustado"])
    ondas = len(PESQUISAS)
    return (
        '<section class="hero"><div class="wrap">'
        f'<p class="eyebrow">Agregador Arvor · atualizado em {esc(longo(D["referencia"]))} · '
        "sensibilidade sob régua comum</p>"
        "<h1>A corrida sob<br>a régua <em>oficial.</em></h1>"
        '<div class="hero-bottom">'
        "<p>Todo instituto declara uma distribuição de renda para a amostra. O IBGE mede "
        "outra. Este agregador troca só essa margem, mantém tudo o que o instituto ponderou "
        "e mostra o placar dos dois jeitos, onda por onda.</p>"
        f"<div><strong>{ondas}</strong><span>ondas auditadas<br>com cruzamento de renda</span></div>"
        f"<div><strong>{sinal(dif_pub, 1)}</strong><span>diferença publicada<br>"
        "na média Arvor do 2º turno</span></div>"
        f"<div><strong>{sinal(dif_adj, 1)}</strong><span>diferença reponderada<br>"
        "pela renda da PNAD</span></div></div>"
        f'<p class="note">Régua: {esc(BENCH["benchmark"])}, pessoas de {BENCH["min_age"]} anos '
        f"ou mais, preços de {MESES[int(BENCH['price_month'][4:]) - 1]}. de "
        f"{BENCH['price_month'][:4]}. Diferença positiva favorece Lula. A reponderação é "
        "inferência declarada, não resultado de eleição.</p></div></section>"
    )


def toc() -> str:
    itens = [
        ("segundo-turno", "2º turno"),
        ("primeiro-turno", "1º turno"),
        ("manchete", "Manchete"),
        ("institutos", "Institutos"),
        ("pesquisas", "Pesquisas"),
        ("metodo", "Método"),
        ("fontes", "Fontes"),
    ]
    return (
        '<nav class="toc" aria-label="Seções">'
        + "".join(f'<a href="#{i}">{esc(t)}</a>' for i, t in itens)
        + "</nav>"
    )


def bloco_tips(chaves: list[str] | None = None) -> str:
    """Fichas dos alvos embutidas na própria página, sem depender de rede."""
    dados = TIPS if chaves is None else {k: TIPS[k] for k in chaves if k in TIPS}
    if not dados:
        return ""
    texto = json.dumps(dados, ensure_ascii=False, separators=(",", ":"))
    seguro = texto.replace("</", "<\\/")
    return f'<script type="application/json" class="tips">{seguro}</script>'


def build_html() -> str:
    corpo = "".join(
        [
            ch_segundo_turno(),
            ch_primeiro_turno(),
            ch_manchete(),
            ch_institutos(),
            ch_pesquisas(),
            ch_metodo(),
            ch_fontes(),
        ]
    )
    return (
        head() + '<body><a class="skip" href="#conteudo">Pular para o conteúdo</a>'
        '<header class="masthead"><a href="index.html">ARVOR <span>Intelligence</span></a>'
        "<span>Agregador de pesquisas</span></header>"
        '<main id="conteudo">'
        + hero()
        + toc()
        + corpo
        + '</main><footer class="wrap footer"><b>ARVOR Intelligence</b>'
        f"<span>Agregador de pesquisas reponderadas · referência de "
        f"{esc(longo(D['referencia']))}</span>"
        '<span><a href="index.html">Biblioteca</a> · <a href="pnad.html">A PNAD por dentro</a>'
        " · uso livre com crédito e link</span></footer>"
        + bloco_tips()
        + f"<script>{SCRIPT}</script>"
        '<script src="assets/reponderacao_tip.js" defer></script></body></html>'
    )


def placar_home() -> str:
    """Placar compacto da capa, com a mesma convenção de fato e inferência."""
    kernel = AGG["ultimo"]["2t"]["kernel"]
    pub, adj = kernel["publicado"], kernel["ajustado"]
    celulas = [
        (
            f"{br(pub['lula'], 1)} × {br(pub['flavio'], 1)}",
            "Média Arvor publicada, Lula × Flávio, 2º turno",
        ),
        (
            f"{br(adj['lula'], 1)} × {br(adj['flavio'], 1)}",
            "A mesma média sob a renda medida pela PNAD",
        ),
        (sinal(gap(pub), 1), "Diferença publicada, em pontos"),
        (sinal(gap(adj), 1), "Diferença sob a régua oficial"),
    ]
    return "".join(
        f"<div><b>{esc(valor)}</b><span>{esc(texto)}</span></div>"
        for valor, texto in celulas
    )


def write_csv() -> None:
    cabeca = [
        "id",
        "instituto",
        "contratante",
        "registro_tse",
        "campo_inicio",
        "campo_fim",
        "divulgacao",
        "n",
        "turno",
        "cenario",
        "lula_publicado",
        "lula_reponderado",
        "flavio_publicado",
        "flavio_reponderado",
        "gap_publicado",
        "gap_reponderado",
        "margem_diferenca_95",
        "residuo_max",
        "desvio_ate_primeira_faixa",
        "outras_opcoes_publicado",
        "outras_opcoes_reponderado",
    ]
    linhas = []
    for p in PESQUISAS:
        for turno, t in p["turnos"].items():
            adj = ajustado(t)
            outras = [c for c in t["opcoes"] if c not in PAR]
            linhas.append(
                [
                    p["id"],
                    p["instituto"],
                    p["contratante"],
                    p["registro_tse"],
                    p["campo"]["inicio"],
                    p["campo"]["fim"],
                    p["divulgacao"],
                    p["n"],
                    turno,
                    CEN,
                    round(t["publicado"]["lula"], 3),
                    round(adj["lula"], 3),
                    round(t["publicado"]["flavio"], 3),
                    round(adj["flavio"], 3),
                    round(t["gap_publicado"], 3),
                    round(t["gap_ajustado"], 3),
                    round(t["margem_diferenca_95"], 3),
                    round(t["residuo_max"], 3),
                    round(p["desvio_ate_primeira_faixa"], 3),
                    ";".join(f"{c}={round(t['publicado'][c], 3)}" for c in outras),
                    ";".join(f"{c}={round(adj[c], 3)}" for c in outras),
                ]
            )
    with TABLE_CSV.open("w", encoding="utf-8", newline="") as handle:
        escritor = csv.writer(handle)
        escritor.writerow(cabeca)
        escritor.writerows(linhas)


def build() -> None:
    html = build_html()
    if "—" in html:
        raise SystemExit("travessão encontrado no HTML gerado")
    SHEET.write_text(CSS, encoding="utf-8")
    TIP_SHEET.write_text(TIP_CSS, encoding="utf-8")
    TIP_SCRIPT.write_text(TIP_JS, encoding="utf-8")
    PAGE.write_text(html.replace("<section ", "\n<section ") + "\n", encoding="utf-8")
    write_csv()

    home = serie_svg("home2t", "2t", compacta=True)
    HOME_SVG.write_text(home + "\n", encoding="utf-8")
    chaves_home = [_tip_id(p, "2t") for p in PESQUISAS if "2t" in p["turnos"]]
    if INDEX.exists():
        for nome, fragmento in (
            ("reponderacao_home", home + bloco_tips(chaves_home)),
            ("reponderacao_home_placar", placar_home()),
        ):
            if inject(INDEX, {nome: fragmento}):
                print(f"Capa atualizada ({nome}):", INDEX)
            else:
                print(
                    f"Aviso: marcadores <!--FIG:{nome}--> ausentes em",
                    INDEX,
                    "· nada foi escrito na capa",
                )
    print("Página gerada:", PAGE)
    print("Folha de estilo:", SHEET)
    print("Camada interativa:", TIP_SHEET, "e", TIP_SCRIPT)
    print("Tabela:", TABLE_CSV)


if __name__ == "__main__":
    build()
