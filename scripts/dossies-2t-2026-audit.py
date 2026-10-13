#!/usr/bin/env python3
"""Extrai fontes verificadas e calcula os dossiês Nexus 13/10 e Datafolha 08/10."""

from dossies_2t_2026.audit import write

if __name__ == "__main__":
    data = write()
    for name in ("datafolha", "nexus"):
        print(
            name,
            len(data[name]["tables"]),
            "perguntas cruzadas; fontes e recomposições verificadas",
        )
