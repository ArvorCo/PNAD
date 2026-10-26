"""Base da thread do dossiê da apuração do 2º turno: dados, formato e verificação.

As primitivas de SVG, a paleta e o formato pt-BR vêm da thread do 1º turno
(``apuracao_2026.thread_base``). Aqui ficam o leitor dos JSONs do 2º turno, os
caminhos de saída e a verificação de texto: todo número dos modelos sai de um
campo ``{nome}``; ``digitos_soltos`` acusa algarismo escrito à mão.
"""

from __future__ import annotations

import json
import re
from functools import cache
from pathlib import Path

from apuracao_2026.thread_base import EMOJI, PLACEHOLDER

ROOT = Path(__file__).resolve().parents[2]
DADOS = ROOT / "analysis/apuracao_2t_2026/dados"
MEMOS = ROOT / "analysis/apuracao_2t_2026"
SLUG = "apuracao_2T_2026_thread"
DOSSIE = "apuracao_2T_2026"
URL = f"https://brasil.arvor.co/{SLUG}.html"
URL_DOSSIE = f"https://brasil.arvor.co/{DOSSIE}.html"
OG = f"https://brasil.arvor.co/img/og/{SLUG}.png"
PNG_DIR = ROOT / "docs/img/apuracao_2t_thread"


@cache
def dado(nome: str):
    """Lê um JSON de ``dados/`` (ou um caminho relativo à raiz, se tiver barra)."""
    caminho = ROOT / nome if "/" in nome else DADOS / f"{nome}.json"
    return json.loads(caminho.read_text(encoding="utf-8"))


def tabela(bloco: dict) -> list[dict]:
    """Converte ``{"colunas": [...], "linhas": [[...]]}`` em lista de dicionários."""
    cols = bloco["colunas"]
    return [dict(zip(cols, linha, strict=True)) for linha in bloco["linhas"]]


def hhmm_min(s: str) -> float:
    """'17:07' ou '2026-10-25 17:07:09' em minutos do dia."""
    p = [int(x) for x in s.split(" ")[-1].split(":")]
    return p[0] * 60 + p[1] + (p[2] / 60 if len(p) > 2 else 0)


def min_hhmm(m: float) -> str:
    m = round(m)
    return f"{m // 60 % 24:02d}:{m % 60:02d}"


# ------------------------------------------------------------------ verificação

PERMITIDOS = re.compile(
    r"\b[12]º|\b(?:2002|2006|2010|2014|2018|2022|2026|2027)\b|brasil\.arvor\.co"
    r"|SHA-256|[a-z0-9_\-]+\.(?:json|py|md|html)|\bv4\b"
    # convenções estatísticas (nível de confiança e nome de percentil), não medições
    r"|\b(?:90|95)%|\b(?:10|90|99)º"
    # caminhos e identificadores de arquivo citados como fonte
    r"|[a-z]+(?:/[a-z0-9_]+)+|\b[a-z]+_[a-z0-9_]*\d[a-z0-9_]*"
)
PROIBIDOS = {"travessão": "—", "meia-risca": "–", "hashtag": "#"}
PALAVRAS_PROIBIDAS = ("fraude", "fraudul", "comunista", "ladrão", "ladrao", "roubo")


def digitos_soltos(modelo: str) -> list[str]:
    """Algarismos do modelo fora dos campos ``{...}`` e da lista de permitidos."""
    limpo = PLACEHOLDER.sub("", modelo)
    limpo = PERMITIDOS.sub("", limpo)
    return re.findall(r"\S*\d\S*", limpo)


def problemas_de_texto(texto: str) -> list[str]:
    out = [nome for nome, c in PROIBIDOS.items() if c in texto]
    if EMOJI.search(texto):
        out.append("emoji")
    baixo = texto.lower()
    out += [p for p in PALAVRAS_PROIBIDAS if p in baixo]
    return out
