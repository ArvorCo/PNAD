#!/usr/bin/env python3
"""Gera dados e imagem dos encerramentos do segundo turno de 2026."""

import argparse
import json

from apuracao_2t_2026.encerramento_dados import SAIDA, gerar


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--so-dados", action="store_true")
    p.add_argument("--so-imagem", action="store_true")
    p.add_argument(
        "--refazer-logs",
        action="store_true",
        help="relê métricas e eventos, sem reutilizar o agregado conferido",
    )
    a = p.parse_args()
    d = (
        json.loads((SAIDA / "dados.json").read_text())
        if a.so_imagem
        else gerar(refazer_logs=a.refazer_logs)
    )
    if not a.so_dados:
        from apuracao_2t_2026.encerramento_figura import desenhar

        desenhar(d, SAIDA)
    for r in d["linhas"]:
        print(
            r["hora"],
            r["secoes"],
            round(r["encerradas_pct"], 4),
            r["restantes"],
            r["flavio_pct"],
        )


if __name__ == "__main__":
    main()
