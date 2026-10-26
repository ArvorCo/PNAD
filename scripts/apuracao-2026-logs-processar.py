#!/usr/bin/env python3
"""Extrai tempos, biometria e ocorrências dos logs e confere contra os BUs.

Padrão: 1º turno (pleito 3220), como antes. No 2º turno:
  python3 scripts/apuracao-2026-logs-processar.py --pleito 3221 --workers 10
lê `data/raw/tse_logs_2026/logs_2t.sqlite` (ZIP ou modo compacto), confere contra
`apuracao/data/secoes_2t_2026.sqlite` e grava `data/outputs/logs_urnas_2t_2026.sqlite`.
"""

import argparse
from dataclasses import replace
from pathlib import Path

from apuracao_logs.pleito import obter
from apuracao_logs.processamento import executar


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--acompanhar", action="store_true")
    p.add_argument("--pleito", type=int, default=3220)
    p.add_argument("--uf", action="append", default=[])
    p.add_argument("--limite", type=int, default=0)
    p.add_argument("--raw", type=Path, help="banco de originais (padrão do pleito)")
    p.add_argument("--metricas", type=Path, help="banco de métricas (padrão do pleito)")
    p.add_argument("--origem", type=Path, help="banco de BUs (padrão do pleito)")
    a = p.parse_args()
    pleito = obter(a.pleito)
    if a.origem:
        pleito = replace(pleito, origem=a.origem)
    executar(
        raw_path=a.raw,
        output=a.metricas,
        workers=a.workers,
        acompanhar=a.acompanhar,
        pleito=pleito,
        ufs=[u.lower() for u in a.uf],
        limite=a.limite,
    )


if __name__ == "__main__":
    main()
