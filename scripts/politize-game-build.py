#!/usr/bin/env python3
"""Politize: o jogo da conversa. Valida o roteiro e grava docs/politize_game/dados.js.

Uso::

    python3 scripts/politize-game-build.py          # valida e grava
    python3 scripts/politize-game-build.py --check  # só valida, sem gravar
"""

from __future__ import annotations

import argparse
import sys

from politize_game import roteiro


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="só valida")
    args = ap.parse_args(argv)
    try:
        payload = roteiro.montar() if args.check else roteiro.gravar()
    except roteiro.RoteiroInvalido as exc:
        print("Roteiro inválido:\n" + str(exc), file=sys.stderr)
        return 1
    n_op = sum(
        len(n["escuta"])
        + len(n["fecho"])
        + sum(len(o["opcoes"]) for o in n["objecoes"])
        for n in payload["npcs"]
    ) + sum(len(c["abordagem"]) for c in payload["cenarios"])
    print(
        f"ok: {len(payload['personagens'])} personagens, {len(payload['cenarios'])} cenários, "
        f"{len(payload['npcs'])} NPCs, {n_op} opções"
        + ("" if args.check else f" -> {roteiro.SAIDA.relative_to(roteiro.ROOT)}")
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
