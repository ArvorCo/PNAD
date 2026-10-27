#!/usr/bin/env python3
"""Transporte em massa e ordem de chegada dos lotes no 2º turno de 2026.

Lê as linhas por seção (``secoes.json`` e o gzip fora do git), o cache do log
por seção (``data/outputs/logs_2t_capitulo/``) e o 2º turno de 2022 por município,
e grava ``analysis/apuracao_2t_2026/dados/angulo_transporte.json`` e ``.md``.
Rótulo: pede explicação, não prova irregularidade.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

from apuracao_2t_2026 import angulo_transporte as at


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--reps", type=int, default=at.REPS, help="reamostragens do IC")
    a = ap.parse_args()
    S = json.loads((at.DADOS / "secoes.json").read_text("utf-8"))
    t = at.carregar(S)
    d = {
        "gerado_em": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "script": "scripts/apuracao-2t-2026-angulo-transporte.py",
        "fontes": {
            "secoes": S["secoes"].get("arquivo"),
            "secoes_sha256": S["secoes"].get("sha256"),
            "logs_2t": "data/outputs/logs_2t_capitulo/metricas_2t.parquet",
            "logs_1t_amostra": "data/outputs/logs_2t_capitulo/amostra_1t.jsonl",
            "tse_2022": "data/outputs/apuracao_2t_2026/tse2022_2t_municipios.json",
        },
        **at.analisar(t["sec"], t["m22"], t["fim2"], t["fim1"], reps=a.reps),
    }
    (at.DADOS / "angulo_transporte.json").write_text(
        json.dumps(d, ensure_ascii=False, indent=1) + "\n", "utf-8"
    )
    (at.DADOS / "angulo_transporte.md").write_text(at.markdown(d), "utf-8")
    print(at.DADOS / "angulo_transporte.json")


if __name__ == "__main__":
    main()
