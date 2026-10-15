#!/usr/bin/env python3
"""Recupera e preserva logs oficiais do 1º turno com retomada por seção."""

import argparse
from pathlib import Path

from apuracao_logs.coleta import DESTINO, coletar


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", type=Path, default=DESTINO)
    p.add_argument("--limite", type=int, default=0)
    p.add_argument("--workers", type=int, default=32)
    p.add_argument("--rps", type=float, default=40)
    p.add_argument("--uf", action="append", default=[])
    a = p.parse_args()
    if a.workers < 1 or not 0 < a.rps <= 60 or a.limite < 0:
        p.error("workers >= 1; 0 < rps <= 60; limite >= 0")
    coletar(a.db, a.limite, a.workers, a.rps, [u.lower() for u in a.uf])


if __name__ == "__main__":
    main()
