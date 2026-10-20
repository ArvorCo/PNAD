#!/usr/bin/env python3
"""Gera o relatório público de clima, bateria e abstenção no 1º turno de 2026.

Lê analysis/clima_1t_2026/clima.json (saída do motor, que este script não roda de novo) e
grava docs/clima_abstencao_1t_2026.html com o CSS e o JS ao lado. Todo número vem do JSON.
"""

import argparse
from pathlib import Path

from clima_1t.pagina.montagem import escrever
from clima_1t.pagina.util import Dados

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json",
        type=Path,
        help="JSON do motor (padrão: analysis/clima_1t_2026/clima.json)",
    )
    parser.add_argument(
        "--docs", type=Path, help="pasta de saída (padrão: docs/ do repositório)"
    )
    args = parser.parse_args()
    for caminho in escrever(Dados(args.json), args.docs):
        print(caminho)
