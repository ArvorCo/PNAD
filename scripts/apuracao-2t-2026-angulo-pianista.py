#!/usr/bin/env python3
"""Ângulo do pianista no 2º turno de 2026: a célula comparecimento +5 pp e salto de
biometria tem no log a marca da liberação de eleitor ausente?

Relê os logs originais das seções da célula e dos controles (vizinhas sem sinal,
salto de biometria sem alta de comparecimento, a própria seção no 1º turno) com o
leitor versão 12 e grava ``analysis/apuracao_2t_2026/dados/angulo_pianista.json`` e
``.md``. Métricas por seção ficam em cache em
``data/outputs/apuracao_2t_2026/angulo_pianista_metricas.json.gz`` (``--refazer``
relê). Rótulo: sinal pede explicação, não prova irregularidade.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from apuracao_2t_2026 import angulo_pianista as A
from apuracao_2t_2026.angulo_pianista_texto import markdown


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--saida", type=Path, default=A.DADOS)
    p.add_argument("--refazer", action="store_true")
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--reps", type=int, default=A.REPS)
    a = p.parse_args()
    d = A.analisar(refazer=a.refazer, workers=a.workers, reps=a.reps)
    a.saida.mkdir(parents=True, exist_ok=True)
    (a.saida / "angulo_pianista.json").write_text(
        json.dumps(d, ensure_ascii=False, indent=1, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    (a.saida / "angulo_pianista.md").write_text(markdown(d), encoding="utf-8")
    g = d["grupos"]["celula"]
    print(
        json.dumps(
            {
                "celula": d["celula"],
                "marca_2t": g["marca_2t"],
                "marca_nova": g["marca_nova"],
                "marca_forte_2t": g["marca_forte_2t"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
