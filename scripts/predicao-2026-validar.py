#!/usr/bin/env python3
"""Valida apenas o modelo de comparecimento, transportando 2018 para 2022."""

import json

from predicao_2026.validacao import backtest

if __name__ == "__main__":
    print(json.dumps(backtest()["metricas"], ensure_ascii=False, indent=2))
