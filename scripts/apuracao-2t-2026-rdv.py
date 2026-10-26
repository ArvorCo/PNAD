#!/usr/bin/env python3
"""RDV do 2º turno de 2026: grava ``analysis/apuracao_2t_2026/dados/rdv.json``.

Lê ``apuracao/data/rdv_2t_2026.sqlite`` (coleta de ``apuracao/scripts/rdv-coletar.ts``),
só para leitura, e pode rodar com a coleta em andamento: o JSON marca ``meta.parcial``.
A matriz presidente × governador sai como limites de Fréchet por seção, somados por
município e UF, porque o RDV não liga os votos de um eleitor nos dois cargos. Método e
limites em ``analysis/apuracao_2t_2026/RDV.md``.

    python3 scripts/apuracao-2t-2026-rdv.py
    python3 scripts/apuracao-2t-2026-rdv.py --rdv outro.sqlite --saida /tmp/rdv.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from apuracao_2t_2026 import rdv


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rdv", type=Path, default=rdv.RDV_DB)
    ap.add_argument("--secoes", type=Path, default=rdv.SECOES_DB)
    ap.add_argument("--saida", type=Path, default=rdv.SAIDA)
    a = ap.parse_args()
    dados = rdv.gerar(a.rdv, a.secoes)
    a.saida.parent.mkdir(parents=True, exist_ok=True)
    a.saida.write_text(
        json.dumps(dados, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    cob = dados["cobertura"]["total"]
    print(
        f"{a.saida}: tentadas {dados['meta']['secoes_tentadas']}, ok {cob.get('ok', 0)}, "
        f"confere {cob.get('confere', 0)}, diverge {cob.get('diverge', 0)}, "
        f"UFs com matriz {sorted(dados['cruzado_limites'])}"
    )


if __name__ == "__main__":
    main()
