#!/usr/bin/env python3
"""Predição do Senado 2027: probabilidade de eleição por estado e composição.

Lê analysis/senado_2026/pesquisas/*.json, os arquivos do TSE da pasta
analysis/senado_2026/ (opcionais) e a calibração de 2022
(analysis/senado_2026/calibracao_2022.json, gerada por
scripts/senado-2026-calibracao.py; sem ela, usa a hipótese declarada) e grava
docs/assets/predicao_senado.json. Idempotente: mesma entrada e mesma semente,
mesma saída (exceto `gerado_em`).

Uso:
    python3 scripts/senado-2026-motor.py
    python3 scripts/senado-2026-motor.py --simulacoes 5000 --sem-sensibilidades
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from senado_2026 import base as B
from senado_2026 import calibracao as C
from senado_2026 import motor as M
from senado_2026 import saida

SAIDA = B.ROOT / "docs/assets/predicao_senado.json"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--simulacoes", type=int, default=M.SIMULACOES)
    ap.add_argument("--semente", type=int, default=M.SEMENTE)
    ap.add_argument("--mistura-uniforme", type=float, default=M.MISTURA_UNIFORME)
    ap.add_argument("--sem-sensibilidades", action="store_true")
    ap.add_argument("--saida", type=Path, default=SAIDA)
    args = ap.parse_args()

    t0 = time.time()
    ondas = B.ler_pesquisas()
    tse = B.Tse()
    senadores = B.ler_opcional(B.PASTA / "senadores_2022.json")
    eleitorado = (B.ler_opcional(B.PASTA / "eleitorado_uf_2026.json") or {}).get(
        "ufs", {}
    )
    resultado = saida.prever(
        ondas,
        tse,
        senadores,
        eleitorado,
        C.ler(),
        simulacoes=args.simulacoes,
        semente=args.semente,
        mistura_uniforme=args.mistura_uniforme,
        sensibilidades=not args.sem_sensibilidades,
    )
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    args.saida.write_text(
        json.dumps(resultado, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    par = resultado["parametros"]
    print(
        f"{len(ondas)} ondas lidas; erro {par['erro']['fonte']}, "
        f"{par['escala_erro_pp']:.2f} pp para candidatura em 30%"
    )
    for uf, e in resultado["estados"].items():
        probs = {p["nome"]: p["p_eleito"] for p in e["probabilidades"]}
        dupla = " + ".join(f"{n} ({probs[n]:.2f})" for n in e["eleitos_provaveis"])
        p = e["p_dupla_mais_provavel"]
        print(
            f"{uf} {e['cobertura']:<12} {dupla or '-'}"
            + (f"  dupla {p:.2f}" if p is not None else "")
        )
    s27 = resultado["senado_2027"]
    for g, v in s27["por_grupo"].items():
        print(f"{g}: {v['esperado']:.1f} {v['ic90']}")
    print(f"tempo: {time.time() - t0:.1f}s -> {args.saida}")


if __name__ == "__main__":
    main()
