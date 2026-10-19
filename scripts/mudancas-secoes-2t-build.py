#!/usr/bin/env python3
"""Gera o laudo público de mudanças de local de votação entre os turnos e abstenção.

Lê analysis/mudancas_secoes_2t/mudancas.json (saída do motor, que este script não roda
de novo) e grava docs/mudancas_secoes_abstencoes.html com o CSS e o JS ao lado.
"""

import argparse
from pathlib import Path

from mudancas_secoes_2t.pagina.contexto import Contexto
from mudancas_secoes_2t.pagina.montagem import escrever

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json",
        type=Path,
        help="JSON do motor (padrão: analysis/mudancas_secoes_2t/mudancas.json)",
    )
    parser.add_argument(
        "--docs", type=Path, help="pasta de saída (padrão: docs/ do repositório)"
    )
    args = parser.parse_args()
    for caminho in escrever(Contexto(args.json), args.docs):
        print(caminho)
