#!/usr/bin/env python3
"""Gera a camada pública dos logs a partir dos originais já conferidos."""

import json

from apuracao_logs.figuras import gerar
from apuracao_logs.publicacao import montar
from apuracao_logs.view import atualizar_paginas

if __name__ == "__main__":
    r = montar()
    gerar(r)
    atualizar_paginas(r)
    print(json.dumps(r["cobertura"], ensure_ascii=False))
