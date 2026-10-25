#!/usr/bin/env python3
"""Mapa de previsão por estado do 2º turno de 2026, em imagem 1:1.

Grava `docs/assets/mapa_previsao_2t_2026.json` (uma linha por UF: 1º turno,
transporte, pesquisa estadual e as duas âncoras), a fonte HTML em
`docs/assets/og/mapa_previsao_2t_2026.html` e o PNG 2160×2160 em
`docs/img/og/mapa_previsao_2t_2026.png`.

Reprodução:
    python3 scripts/mapa-previsao-2t.py --hoje 2026-10-24
    python3 scripts/mapa-previsao-2t.py --hoje 2026-10-24 --sem-png
"""

from __future__ import annotations

import argparse
import json
from datetime import date

from mapa_previsao_2t.figura import FONTE_HTML, SAIDA_PNG, pagina, renderizar
from mapa_previsao_2t.motor import ROOT, build
from projecao_secoes_2t.fontes import save_json

SAIDA_JSON = ROOT / "docs/assets/mapa_previsao_2t_2026.json"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hoje", default="2026-10-24")
    parser.add_argument("--sem-png", action="store_true", help="só JSON e HTML")
    args = parser.parse_args()
    today = date.fromisoformat(args.hoje)
    data = build(today)
    save_json(SAIDA_JSON, data)
    FONTE_HTML.write_text(pagina(data), encoding="utf-8")
    report = {
        "json": str(SAIDA_JSON.relative_to(ROOT)),
        "html": str(FONTE_HTML.relative_to(ROOT)),
        "nacional": {
            k: round(v["flavio_pct"], 3)
            for k, v in data["nacional"].items()
            if "flavio_pct" in v
        },
        "lula_frente_projecao": sum(
            r["projecao"]["diferenca_pp"] < 0 for r in data["ufs"]
        ),
        "lula_frente_media": sum(r["media"]["diferenca_pp"] < 0 for r in data["ufs"]),
    }
    if not args.sem_png:
        renderizar()
        report["png"] = str(SAIDA_PNG.relative_to(ROOT))
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
