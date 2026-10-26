"""Capítulo ``logs`` do dossiê do 2º turno: grava ``analysis/apuracao_2t_2026/dados/logs.{json,md}``.

Lê só leitura os bancos de métricas dos dois turnos, os recortes públicos por zona,
``secoes.json`` e a amostra do 1º turno relida para a cadência
(``python3 -m apuracao_2t_2026.logs_amostra_1t``, a partir de ``scripts/``).

Uso: ``python3 scripts/apuracao-2t-2026-logs.py [--refazer] [--amostra-1t]``.
"""

from __future__ import annotations

import argparse
import json
import sys

from apuracao_2t_2026 import logs_amostra_1t
from apuracao_2t_2026.logs_analise import montar
from apuracao_2t_2026.logs_base import DADOS
from apuracao_2t_2026.logs_texto import markdown


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--refazer", action="store_true", help="relê os bancos de métricas")
    ap.add_argument(
        "--amostra-1t", action="store_true", help="completa a amostra do 1º turno antes"
    )
    a = ap.parse_args()
    if a.amostra_1t:
        logs_amostra_1t.executar()
    d = montar(a.refazer)
    (DADOS / "logs.json").write_text(
        json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    (DADOS / "logs.md").write_text(markdown(d), encoding="utf-8")
    print(f"gravado {DADOS / 'logs.json'} e logs.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
