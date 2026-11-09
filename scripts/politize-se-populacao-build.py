#!/usr/bin/env python3
"""Compara população residente, cadastro eleitoral e comparecimento municipal."""

import argparse

from politize_se import populacao_fontes

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--coletar",
        action="store_true",
        help="baixa e arquiva respostas oficiais do IBGE",
    )
    ap.add_argument("--so-fontes", action="store_true")
    args = ap.parse_args()
    if args.coletar:
        populacao_fontes.coletar()
    if not args.so_fontes:
        from politize_se.populacao import publicar

        publicar()
