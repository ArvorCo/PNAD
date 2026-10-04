#!/usr/bin/env python3
"""Predição de governador 2026: 1º turno, 2º turno e probabilidade de eleição.

Lê analysis/governador_2026/pesquisas/*.json, os arquivos do TSE de
analysis/governador_2026/ (opcionais) e a calibração de 2022 do Senado
(analysis/senado_2026/calibracao_2022.json; sem ela, a hipótese declarada) e
grava docs/assets/predicao_governador.json. Idempotente: mesma entrada e mesma
semente, mesma saída (exceto `gerado_em`).

Uso:
    python3 scripts/governador-2026-motor.py
    python3 scripts/governador-2026-motor.py --simulacoes 5000 --sem-sensibilidades
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from governador_2026 import base as B
from governador_2026 import motor as M
from governador_2026 import saida
from senado_2026 import calibracao as C
from senado_2026 import motor as SM

SAIDA = B.ROOT / "docs/assets/predicao_governador.json"
CALIBRACAO = B.ROOT / "analysis/governador_2026/calibracao_2022.json"
CASAS_DECIMAIS = 6


def arredondar(x):
    if isinstance(x, float):
        return round(x, CASAS_DECIMAIS)
    if isinstance(x, dict):
        return {k: arredondar(v) for k, v in x.items()}
    if isinstance(x, list):
        return [arredondar(v) for v in x]
    return x


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--simulacoes", type=int, default=M.SIMULACOES)
    ap.add_argument("--semente", type=int, default=M.SEMENTE)
    ap.add_argument("--mistura-uniforme", type=float, default=SM.MISTURA_UNIFORME)
    ap.add_argument("--sem-sensibilidades", action="store_true")
    ap.add_argument("--saida", type=Path, default=SAIDA)
    args = ap.parse_args()

    t0 = time.time()
    ondas = B.ler_pesquisas()
    tse = B.Tse()
    eleitorado = (B.ler_opcional(B.PASTA / "eleitorado_uf_2026.json") or {}).get(
        "ufs", {}
    )
    resultado = saida.prever(
        ondas,
        tse,
        eleitorado,
        C.ler(CALIBRACAO),
        simulacoes=args.simulacoes,
        semente=args.semente,
        mistura_uniforme=args.mistura_uniforme,
        sensibilidades=not args.sem_sensibilidades,
    )
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    args.saida.write_text(
        json.dumps(arredondar(resultado), ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )
    par = resultado["parametros"]
    print(
        f"{len(ondas)} ondas lidas; erro {par['erro']['fonte']}, "
        f"{par['escala_erro_pp']:.2f} pp para candidatura em 30%"
    )
    for uf, e in resultado["estados"].items():
        if e["favorito"] is None:
            print(f"{uf} {e['cobertura']:<12} -")
            continue
        p2 = e["pares_2t"][0] if e["pares_2t"] else None
        par_txt = ""
        if p2:
            a, b = p2["nomes"]
            par_txt = (
                f"  2T {a} {p2['projecao'][a]:.0f} x {b} {p2['projecao'][b]:.0f}"
                f" ({'medido' if p2['medido'] else 'transf.'}, p={p2['p_par']:.2f})"
            )
        print(
            f"{uf} {e['cobertura']:<8} {e['favorito']} p={e['p_favorito']:.2f} "
            f"1T={e['p_decide_1t']:.2f} {e['classe']}{par_txt}"
        )
    n = resultado["nacional"]
    print("decididos 1T:", n["decididos_1t"])
    for g, v in n["por_grupo"].items():
        print(f"{g}: {v['esperado']:.1f} {v['ic90']}")
    print(f"tempo: {time.time() - t0:.1f}s -> {args.saida}")


if __name__ == "__main__":
    main()
