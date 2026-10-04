#!/usr/bin/env python3
"""Gera docs/predicao_governador.html a partir do JSON do motor e do template.

    python3 scripts/governador-2026-build.py
    python3 scripts/governador-2026-build.py --input outro.json --output /tmp/p.html

O build não recalcula nada: lê `docs/assets/predicao_governador.json`, escrito
pelo motor, e falha com mensagem clara se o arquivo faltar.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from governador_2026.pagina import texto, view

ROOT = Path(__file__).resolve().parents[1]
JSON_PADRAO = ROOT / "docs/assets/predicao_governador.json"
TEMPLATE = ROOT / "docs/predicao_governador.template.html"
PAGINA = ROOT / "docs/predicao_governador.html"
ASSETS_PROPRIOS = (
    "predicao_senado.js",
    "predicao_senado.css",
    "predicao_governador.css",
)


def carregar(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(
            f"Falta {path}. O motor (scripts/governador-2026-motor.py) escreve esse JSON."
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    for chave in ("estados", "nacional"):
        if chave not in data:
            raise SystemExit(f"{path} sem a chave obrigatória '{chave}'.")
    return data


def render(data: dict, template: str) -> str:
    trocas = {
        "HERO": view.hero_cartoes(data),
        "RESUMO": view.resumo_30s(data),
        "CORRIDAS": view.corridas(data),
        "SEGUNDOS_TURNOS": view.segundos_turnos(data),
        "MAPA": view.mapa_secao(data),
        "FICHAS": view.fichas(data),
        "TABELA": view.tabela(data),
        "COMO_LEMOS": texto.como_lemos(data),
        "LIMITES": texto.limites(data),
        "FONTES": view.fontes(data),
        **texto.values(data),
    }
    for chave, valor in trocas.items():
        template = template.replace("{{" + chave + "}}", valor)
    # Carimbo de versão nos assets próprios: GitHub Pages e navegador guardam
    # JS e CSS em cache, e sem isso uma correção demora a chegar.
    for nome in ASSETS_PROPRIOS:
        arquivo = ROOT / "docs/assets" / nome
        if arquivo.exists():
            versao = hashlib.sha256(arquivo.read_bytes()).hexdigest()[:10]
            template = template.replace(f'assets/{nome}"', f'assets/{nome}?v={versao}"')
    if "{{" in template or "—" in template:
        raise ValueError("Template incompleto ou travessão no texto público")
    return template


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, default=JSON_PADRAO)
    ap.add_argument("--output", type=Path, default=PAGINA)
    args = ap.parse_args()
    data = carregar(args.input)
    html = render(data, TEMPLATE.read_text(encoding="utf-8"))
    args.output.write_text(html, encoding="utf-8")
    print(f"{args.output} ({len(html) / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
