#!/usr/bin/env python3
"""Dataset aberto por seção dos dois turnos de 2026: CSV, dicionário e manifesto.

Lê `apuracao/data/secoes_2026.sqlite` e `secoes_2t_2026.sqlite` em modo somente
leitura e a camada pública do Politize-se, e grava em
`docs/assets/apuracao_2t/dataset/` o CSV comprimido (bytes reprodutíveis),
`DICIONARIO.md` e `manifesto.json`. Rótulo: sinal pede explicação, não prova
irregularidade; atipicidade estatística não é irregularidade.

Uso:
    python3 scripts/apuracao-2t-2026-dataset.py [--uf SP ...] [--saida PASTA]
                                                [--sem-hash-bancos]
"""

from __future__ import annotations

import argparse
from pathlib import Path

from apuracao_2t_2026 import dataset


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--uf", nargs="*", help="só estas UFs (amostra; padrão: todas)")
    ap.add_argument("--saida", type=Path, default=dataset.PASTA)
    ap.add_argument(
        "--sem-hash-bancos",
        action="store_true",
        help="não calcular o SHA-256 dos bancos (rascunho)",
    )
    a = ap.parse_args()
    ufs = [u.upper() for u in a.uf] if a.uf else None
    m = dataset.gerar(a.saida, ufs, hash_bancos=not a.sem_hash_bancos)
    print(
        f"{m['arquivo']}: {m['bytes']:,} bytes, {m['n_linhas']:,} linhas, "
        f"SHA-256 {m['sha256']}, {m['segundos']}s"
    )
    if m["partes_por_uf"]:
        print(f"partes por UF: {len(m['partes_por_uf'])} arquivos em dataset/uf/")


if __name__ == "__main__":
    main()
