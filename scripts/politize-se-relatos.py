#!/usr/bin/env python3
"""Exporta os relatos de seção do Politize-se para avaliação e troca o status de moderação.

    python3 scripts/politize-se-relatos.py                  # todos, JSON + CSV
    python3 scripts/politize-se-relatos.py --status novo    # só a fila de avaliação
    python3 scripts/politize-se-relatos.py --marcar lido 12 13
    python3 scripts/politize-se-relatos.py --marcar descartado 14

Saída em analysis/politize_se/relatos/ (ignorada pelo git; o texto nunca é publicado). Usa o
token do CLI do Supabase no keychain; nada de chave em arquivo.
"""

from __future__ import annotations

import argparse
import sys

from politize_se import relatos


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--status", choices=relatos.STATUS, help="exporta só esse status")
    ap.add_argument("--desde", type=int, help="exporta só ids maiores que este")
    ap.add_argument(
        "--marcar", nargs="+", metavar=("STATUS", "ID"), help="troca o status dos ids"
    )
    a = ap.parse_args(argv)
    token = relatos.token_cli()
    if a.marcar:
        status, *ids = a.marcar
        if not ids:
            ap.error("--marcar precisa de STATUS e ao menos um ID")
        feitos = relatos.consultar(
            relatos.sql_marcar([int(i) for i in ids], status), token
        )
        print(
            f"{len(feitos)} relato(s) marcado(s) como {status}: {', '.join(str(x['id']) for x in feitos)}"
        )
        return 0
    linhas = relatos.normalizar(
        relatos.consultar(relatos.sql_exportar(a.status, a.desde), token)
    )
    js, cs = relatos.gravar(linhas, sufixo=a.status or "")
    r = relatos.resumo(linhas)
    print(
        f"{r['total']} relato(s); por status {r['por_status']}; gravado em {js.relative_to(relatos.ROOT)} e {cs.name}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
