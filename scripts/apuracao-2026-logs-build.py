#!/usr/bin/env python3
"""Gera a camada pública dos logs a partir dos originais já conferidos.

Sem argumentos: 1º turno, como antes (agregados, figuras e páginas). Com
`--pleito 3221`: agregados do 2º turno em `docs/assets/logs_urnas_2t_2026/` e
`analysis/apuracao_2t_2026/logs_urnas/`, mais a comparação seção a seção com o
1º turno (`comparacao_turnos.json` e `.md`). Páginas do 2º turno ficam para o
dossiê; este passo não as escreve.
"""

import argparse
import json
from dataclasses import replace
from pathlib import Path

from apuracao_logs.figuras import gerar
from apuracao_logs.pleito import PRIMEIRO, obter
from apuracao_logs.publicacao import montar
from apuracao_logs.turnos import gerar as comparar_turnos
from apuracao_logs.view import atualizar_paginas


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pleito", type=int, default=3220)
    p.add_argument("--raw", type=Path)
    p.add_argument("--metricas", type=Path)
    p.add_argument("--publico", type=Path)
    p.add_argument("--analise", type=Path)
    a = p.parse_args()
    if a.pleito == 3220:
        r = montar()
        gerar(r)
        atualizar_paginas(r)
        print(json.dumps(r["cobertura"], ensure_ascii=False))
        return
    pleito = obter(a.pleito)
    trocas = {
        k: v
        for k, v in (
            ("raw", a.raw),
            ("metricas", a.metricas),
            ("publico", a.publico),
            ("analise", a.analise),
        )
        if v is not None
    }
    pleito = replace(pleito, **trocas)
    r = montar(pleito)
    d = comparar_turnos(
        PRIMEIRO.publico, pleito.publico, pleito.metricas, pleito.analise
    )
    print(
        json.dumps(
            {
                "cobertura": r["cobertura"],
                "nos_dois_turnos": d["comparacao"]["secoes_nos_dois"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
