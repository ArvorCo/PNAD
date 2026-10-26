#!/usr/bin/env python3
"""Recupera e preserva logs oficiais das urnas com retomada por seção.

Padrão: 1º turno (pleito 3220, apuracao/data/secoes_2026.sqlite). No 2º turno, depois de a
coleta de BUs terminar (o catálogo é montado uma vez, na primeira execução):
  python3 scripts/apuracao-2026-logs-coletar.py --pleito 3221 \
    --origem apuracao/data/secoes_2t_2026.sqlite --db data/raw/tse_logs_2026/logs_2t.sqlite \
    --guardar compacto --rps 20 --workers 16

O modo compacto cabe no disco (cerca de 29 GB contra cerca de 89 GB dos ZIPs
inteiros, medido em AC) sem perder evidência: ver apuracao_logs/compacto.py.
"""

import argparse
from pathlib import Path

from apuracao_logs.coleta import DESTINO, ORIGEM, base_do_pleito, coletar


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", type=Path, default=DESTINO)
    p.add_argument("--limite", type=int, default=0)
    p.add_argument("--workers", type=int, default=32)
    p.add_argument("--rps", type=float, default=40)
    p.add_argument("--uf", action="append", default=[])
    p.add_argument("--origem", type=Path, default=ORIGEM)
    p.add_argument("--pleito", type=int, default=3220)
    p.add_argument(
        "--guardar",
        choices=("zip", "compacto"),
        default="zip",
        help="compacto: log do 2º turno com o prefixo do 1º turno por referência (compacto.py)",
    )
    p.add_argument(
        "--referencia-1t",
        type=Path,
        default=DESTINO,
        help="banco de logs do 1º turno usado como referência no modo compacto",
    )
    a = p.parse_args()
    if a.workers < 1 or not 0 < a.rps <= 60 or a.limite < 0:
        p.error("workers >= 1; 0 < rps <= 60; limite >= 0")
    if a.pleito not in (3220, 3221):
        p.error("pleito 3220 (1º turno) ou 3221 (2º turno)")
    if a.pleito != 3220 and a.db == DESTINO:
        p.error("fora do 1º turno, informe --db para não misturar com logs.sqlite")
    coletar(
        a.db,
        a.limite,
        a.workers,
        a.rps,
        [u.lower() for u in a.uf],
        a.origem,
        base_do_pleito(a.pleito),
        a.guardar,
        a.referencia_1t if a.guardar == "compacto" else None,
    )


if __name__ == "__main__":
    main()
