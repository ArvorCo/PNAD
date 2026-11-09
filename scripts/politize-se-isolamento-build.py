#!/usr/bin/env python3
"""Publica Isolation Forest reproduzível dos quatro níveis territoriais."""

import argparse
from pathlib import Path

from politize_se.isolamento import ORIGEM, SAIDA, publicar

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origem", type=Path, default=ORIGEM)
    parser.add_argument("--saida", type=Path, default=SAIDA)
    args = parser.parse_args()
    m = publicar(args.origem, args.saida)
    print(f"{m['secoes_usadas']} de {m['secoes_total']} seções elegíveis")
