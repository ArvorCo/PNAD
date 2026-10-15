#!/usr/bin/env python3
"""Extrai tempos, biometria e ocorrências dos logs e confere contra os BUs."""

import argparse

from apuracao_logs.processamento import executar


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--acompanhar", action="store_true")
    a = p.parse_args()
    executar(workers=a.workers, acompanhar=a.acompanhar)


if __name__ == "__main__":
    main()
