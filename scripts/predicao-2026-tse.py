#!/usr/bin/env python3
"""Compacta comparecimento 2022 e perfil final 2026 do TSE, sem extrair CSVs."""

import argparse

from predicao_2026.tse import build

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--kappa", type=float, default=100)
    build(p.parse_args().kappa)
