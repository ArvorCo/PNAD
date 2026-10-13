"""Recalcula a janela de uma página histórica na sua data de referência."""

import importlib
from datetime import date


def close(data, reference):
    polls = [
        p
        for p in data["pesquisas"]
        if p.get("divulgacao") and p["divulgacao"] <= reference
    ]
    return {
        **data,
        "referencia": reference,
        "pesquisas": polls,
        "institutos": sorted({p["instituto"] for p in polls}),
        "agregador": importlib.import_module("reponderacao-pnad").aggregate(
            polls, date.fromisoformat(reference)
        ),
    }
