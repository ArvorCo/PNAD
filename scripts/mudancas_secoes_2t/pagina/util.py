"""Formatação em pt-BR e acesso aos dados do laudo. Nada de número digitado à mão."""

from __future__ import annotations

import json
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
JSON_MOTOR = ROOT / "analysis" / "mudancas_secoes_2t" / "mudancas.json"
JSON_TRE = ROOT / "analysis" / "mudancas_secoes_2t" / "tre_noticias.json"
JSON_PAINEL = (
    ROOT
    / "data"
    / "originals"
    / "mudancas_secoes_2t"
    / "tse_painel_secoes_alteradas_20261018.json"
)
SLUG = "mudancas_secoes_abstencoes"
SITE = "https://brasil.arvor.co"

CORES = {
    "papel": "#f4f0e6",
    "painel": "#fffdf8",
    "tinta": "#192e2b",
    "cinza": "#535b54",
    "linha": "#d3d1c6",
    "flavio": "#1457aa",
    "lula": "#b02f21",
    "terceira": "#0f7f5f",
    "dourado": "#7d5b00",
    "verde_texto": "#0c7a72",
}
# Categorias com mudança real: cores neutras, sem relação com candidaturas.
COR_CATEGORIA = {
    "A": "#0c7a72",
    "B": "#7d5b00",
    "C": "#6b4a92",
    "D": "#535b54",
    "E": "#a9a28f",
    "X": "#8a8576",
}
VETADOS = ("—",)


def carregar(caminho: Path = JSON_MOTOR):
    return json.loads(caminho.read_text(encoding="utf-8"))


def limpa(texto) -> str:
    """Texto vindo de dado externo: sem travessão, nunca quebra o HTML."""
    s = "" if texto is None else str(texto)
    for v in VETADOS:
        s = s.replace(v, ", ")
    return s


def esc(texto) -> str:
    return escape(limpa(texto), quote=True)


def inteiro(x) -> str:
    return f"{round(x):,}".replace(",", ".")


def dec(x, casas: int = 2) -> str:
    return f"{x:,.{casas}f}".replace(",", "#").replace(".", ",").replace("#", ".")


def sinal(x, casas: int = 2) -> str:
    """Número com sinal explícito; o menos usa o caractere de subtração, não travessão."""
    if round(x, casas) == 0:
        return dec(0, casas)
    return ("+" if x > 0 else "−") + dec(abs(x), casas)


def pct(x, casas: int = 1) -> str:
    return dec(x, casas) + "%"


def pp(x, casas: int = 2) -> str:
    return sinal(x, casas) + " pp"


def ic(par, casas: int = 2, com_sinal: bool = True) -> str:
    f = sinal if com_sinal else dec
    return f"IC 95% de {f(par[0], casas)} a {f(par[1], casas)}"


def data_br(iso: str) -> str:
    """AAAA-MM-DD (ou ISO com hora) para DD/MM/AAAA."""
    d = iso[:10]
    return f"{d[8:10]}/{d[5:7]}/{d[0:4]}"


def lista_secoes(secoes: list[int]) -> str:
    """[126,127,128,129,130,131,132,224] vira '126 a 132, 224'."""
    s = sorted(secoes)
    partes, i = [], 0
    while i < len(s):
        j = i
        while j + 1 < len(s) and s[j + 1] == s[j] + 1:
            j += 1
        partes.append(
            str(s[i])
            if j == i
            else f"{s[i]} a {s[j]}" if j > i + 1 else f"{s[i]}, {s[j]}"
        )
        i = j + 1
    return ", ".join(partes)


def dias_br(iso: str) -> str:
    return data_br(iso)[:5]


_MIUDAS = {"de", "da", "do", "das", "dos", "e"}


def titulo_pt(texto: str) -> str:
    """Nome de município em caixa de título, com de, da, do e e em minúscula."""
    palavras = limpa(texto).lower().split()
    return " ".join(
        p if (i and p in _MIUDAS) else p[:1].upper() + p[1:]
        for i, p in enumerate(palavras)
    )
