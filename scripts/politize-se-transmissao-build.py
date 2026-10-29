#!/usr/bin/env python3
"""Gera a camada de intervalo até o recebimento e o gráfico por local."""

import argparse
import json

from politize_se.transmissao import SAIDA, gerar


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--so-dados", action="store_true")
    p.add_argument("--so-imagem", action="store_true")
    a = p.parse_args()
    d = json.loads((SAIDA / "indice.json").read_text()) if a.so_imagem else gerar()
    if not a.so_dados:
        from politize_se.transmissao_figura import desenhar

        desenhar(d)


if __name__ == "__main__":
    main()
