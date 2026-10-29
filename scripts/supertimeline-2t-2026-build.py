#!/usr/bin/env python3
"""Desenha o dia do voto: cômputos, encerramentos e recebimentos do TSE."""

import argparse
import json

from apuracao_2t_2026.encerramento_dados import SAIDA
from apuracao_2t_2026.supertimeline_dados import gerar


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--so-dados", action="store_true")
    p.add_argument("--so-imagem", action="store_true")
    p.add_argument("--refazer", action="store_true")
    a = p.parse_args()
    d = (
        json.loads((SAIDA / "supertimeline.json").read_text())
        if a.so_imagem
        else gerar(a.refazer)
    )
    if not a.so_dados:
        from apuracao_2t_2026.supertimeline_figura import desenhar

        desenhar(d, SAIDA)


if __name__ == "__main__":
    main()
