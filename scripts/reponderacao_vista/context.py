"""Dados, paleta e formatação compartilhados pelo gerador e seus gráficos."""

from __future__ import annotations

import importlib
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(ROOT / "scripts"))

from svgkit import br  # noqa: E402

coverage_html = importlib.import_module("reponderacao-cobertura").coverage_html
groups_view = importlib.import_module("reponderacao-grupos-view")
non_choice_view = importlib.import_module("reponderacao-nao-escolha-view")
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
    "rui": "Rui Costa Pimenta",
    "clariana": "Clariana Barão",
    "edmilson": "Edmilson Costa",
    "grassi": "Wilson Grassi",
    "hertz": "Hertz Dias",
    "ciro": "Ciro Gomes",
    "aldo": "Aldo Rebelo",
    "aecio": "Aécio Neves",
    "avalanche": "Leonardo Avalanche",
    "joaquim": "Joaquim Barbosa",
    "daciolo": "Cabo Daciolo",
    "hero": "Heró Bezerra",
    "outros_esquerda": "Demais candidaturas do grupo residual",
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

COR.update(groups_view.GROUP_COLORS)

COR_TXT.update(groups_view.GROUP_COLORS)

ROTULOS.update(groups_view.GROUP_LABELS)
COR.update(non_choice_view.COLORS)
COR_TXT.update(non_choice_view.COLORS)
ROTULOS.update(non_choice_view.LABELS)


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
