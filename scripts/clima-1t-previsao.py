"""Previsão do tempo para o 2º turno (25/10/2026) nas células dos locais de votação.

Uso:
    python3 scripts/clima-1t-previsao.py               # baixa, aplica a regra, grava se mudou
    python3 scripts/clima-1t-previsao.py --reindexar   # refaz o índice de células do cadastro
    python3 scripts/clima-1t-previsao.py --aceitar-parcial

Grava ``docs/assets/fiscais_mapa/clima/previsao.json``. Leva cerca de 5 minutos (2.239
células em lotes de 100, abaixo de 600 por minuto). Sai com código 2 quando a previsão
fica incompleta e o arquivo anterior, completo, é mantido.
"""

from __future__ import annotations

import argparse
import json

from clima_1t import previsao


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument(
        "--reindexar", action="store_true", help="refaz o índice do cadastro"
    )
    ap.add_argument("--aceitar-parcial", action="store_true")
    ap.add_argument("--lote", type=int, default=100)
    ap.add_argument("--prazo", type=float, default=540, help="segundos até desistir")
    args = ap.parse_args()
    if args.reindexar:
        idx = previsao.reindexar()
        print(f"índice: {len(idx['celulas'])} células")
    doc, escreveu = previsao.gerar(args.lote, args.prazo, args.aceitar_parcial)
    resumo = {
        "gravado": escreveu,
        "coleta": doc.get("coleta"),
        "pais": doc.get("resumo", {}).get("pais"),
    }
    print(json.dumps(resumo, ensure_ascii=False, indent=1))
    completa = (doc.get("coleta") or {}).get("completa")
    return 0 if completa or args.aceitar_parcial else 2


if __name__ == "__main__":
    raise SystemExit(main())
