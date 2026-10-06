"""Base da thread dos fiscais: caminhos, leitura dos dois JSONs e o recorte leve de
`fiscais.json` (só `resumo`, `criterios`, `destaques`, `por_uf`, `meta`, `rotulos`).

As primitivas SVG, o formato pt-BR e a verificação de texto vêm da super thread
(`thread_base`), para as duas threads seguirem a mesma regra da casa.
"""

from __future__ import annotations

import json
from functools import cache

from . import fiscais_cenarios as FC
from .thread_base import DADOS, ROOT

SLUG = "fiscais_thread"
DOSSIE = "apuracao_1o_turno_2026"
CAPITULO = f"{DOSSIE}.html#fiscais"
URL = f"https://brasil.arvor.co/{SLUG}.html"
OG = f"https://brasil.arvor.co/img/og/{SLUG}.png"
PNG_DIR = ROOT / "docs/img/apuracao_2026/fiscais_thread"
SAIDA = ROOT / "docs" / f"{SLUG}.html"
CHAVES_LEVES = (
    "resumo",
    "criterios",
    "destaques",
    "por_uf",
    "meta",
    "rotulos",
    "sensibilidade",
)


@cache
def fiscais() -> dict:
    """Recorte leve de fiscais.json: a thread não precisa das 13 mil seções."""
    F = json.loads((DADOS / "fiscais.json").read_text(encoding="utf-8"))
    return {k: F[k] for k in CHAVES_LEVES if k in F}


def cenarios() -> dict:
    J = FC.carregar()
    if J is None:
        raise FileNotFoundError(FC.CAMINHO)
    return J


__all__ = [
    "CAPITULO",
    "DOSSIE",
    "OG",
    "PNG_DIR",
    "SAIDA",
    "SLUG",
    "URL",
    "cenarios",
    "fiscais",
]
