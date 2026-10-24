#!/usr/bin/env python3
"""Gera o relatório público de clima, bateria e abstenção no 1º turno de 2026.

Lê a análise histórica em analysis/clima_1t_2026/clima.json sem recalculá-la, integra a
previsão corrente e a referência municipal do TSE e grava página, CSS, JS e downloads.
Mapa, tabelas e hashes usam a mesma rodada meteorológica, preservada em snapshot.
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
    dados = Dados(args.json)
    if args.docs is None:
        # Preserva a rodada meteorológica exata que alimentou o relatório.
        from clima_1t.pagina.util import PREVISAO_JSON, ROOT

        stamp = dados.previsao["gerado_em"].replace(":", "").replace("+", "_")
        snapshot = ROOT / "analysis/clima_1t_2026/previsoes" / f"{stamp}.json"
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        snapshot.write_bytes(PREVISAO_JSON.read_bytes())
    for caminho in escrever(dados, args.docs):
        print(caminho)
