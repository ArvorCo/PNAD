"""Coleta retomável do clima de 25/10/2026 por célula na Open-Meteo (rodar com nohup).

Uso: python3 scripts/clima-2t-modelo.py --fonte ifs   (ou --fonte era5 a partir de 31/10)
"""

from __future__ import annotations

import argparse
import json

from clima_2t import modelo

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--fonte", choices=sorted(modelo.MODELOS), default="ifs")
    ap.add_argument("--lote", type=int, default=100)
    a = ap.parse_args()
    print(json.dumps(modelo.coletar(a.fonte, a.lote), ensure_ascii=False), flush=True)
