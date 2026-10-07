"""Arquétipo do local: a primeira regra que bate, na ordem do contrato.

As regras leem os valores publicados (uma casa decimal), para que o número que o app
mostra e o arquétipo nunca se contradigam. ``frente`` e ``atras`` são o resto (com
Flávio à frente ou atrás por mais de 6 pontos) e por isso não servem de arquétipo
secundário: o secundário é a próxima regra específica que bate, ou ``None``.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

Regra = tuple[str, str, Callable[[Mapping[str, Any]], bool]]


def _ge(valor: float | None, limite: float) -> bool:
    return valor is not None and valor >= limite


def _fertil(m: Mapping[str, Any]) -> bool:
    t, bn = m.get("terceira_v"), m.get("bn_v")
    return t is not None and bn is not None and t + bn >= 12


def _pendulo(m: Mapping[str, Any]) -> bool:
    return m.get("margem_v") is not None and abs(m["margem_v"]) <= 6


def _frente(m: Mapping[str, Any]) -> bool:
    return m.get("margem_v") is not None and m["margem_v"] > 6


REGRAS: tuple[Regra, ...] = (
    ("fortaleza", "Fortaleza", lambda m: _ge(m.get("flavio_v"), 60)),
    ("muro", "Muro", lambda m: _ge(m.get("lula_v"), 65)),
    ("pendulo", "Pêndulo", _pendulo),
    ("reencontro", "Reencontro", lambda m: _ge(m.get("reencontro_a"), 5)),
    ("fertil", "Terreno fértil", _fertil),
    ("dormindo", "Dormindo", lambda m: _ge(m.get("abst_a"), 28)),
    ("abaixo_do_perfil", "Abaixo do perfil", lambda m: _ge(m.get("vao_perfil_pp"), 5)),
    ("frente", "Na frente", _frente),
    ("atras", "Atrás", lambda m: True),
)
CODIGOS = tuple(r[0] for r in REGRAS)
NOMES = {r[0]: r[1] for r in REGRAS}
RESTO = {"frente", "atras"}


def classificar(m: Mapping[str, Any]) -> tuple[str, str | None]:
    """(arquétipo, secundário). ``m`` traz os valores já arredondados a uma casa."""
    primario = None
    for codigo, _, regra in REGRAS:
        if not regra(m):
            continue
        if primario is None:
            primario = codigo
            continue
        if codigo in RESTO:
            break
        return primario, codigo
    return primario or "atras", None
