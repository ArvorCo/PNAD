"""Clima, bateria e abstenção no 1º turno de 2026: coleta e análises.

Uso:
    python3 scripts/clima-1t.py --coletar     # baixa o que falta da Open-Meteo (retomável)
    python3 scripts/clima-1t.py --analisar    # consolida, cruza e grava as saídas
    python3 scripts/clima-1t.py --tudo        # as duas coisas
    python3 scripts/clima-1t.py --analisar --reps 2000

Contrato das saídas em ``analysis/clima_1t_2026/CONTRATO.md``.
"""

from __future__ import annotations

import argparse
import json

from clima_1t import coleta, grade, relatorio


def coletar(lote: int) -> dict:
    locais = grade.ler_locais()
    celulas = grade.celulas(locais, grade.PASSO_ARCHIVE)
    estado = coleta.coletar_archive(celulas, lote=lote)
    doc = coleta.consolidar_archive(celulas)
    estado["cobertura"] = {
        k: v for k, v in doc["cobertura"].items() if k != "faltando_chaves"
    }
    print(json.dumps(estado, ensure_ascii=False, indent=1))
    return estado


def analisar(reps: int) -> None:
    relatorio.executar(reps=reps)


def main() -> None:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--coletar", action="store_true", help="baixa da Open-Meteo")
    ap.add_argument("--analisar", action="store_true", help="cruza e grava as saídas")
    ap.add_argument("--tudo", action="store_true", help="coleta e análise")
    ap.add_argument("--reps", type=int, default=2000, help="réplicas do bootstrap")
    ap.add_argument("--lote", type=int, default=100, help="coordenadas por requisição")
    args = ap.parse_args()
    if not (args.coletar or args.analisar or args.tudo):
        ap.error("escolha --coletar, --analisar ou --tudo")
    if args.coletar or args.tudo:
        coletar(args.lote)
    if args.analisar or args.tudo:
        analisar(args.reps)


if __name__ == "__main__":
    main()
