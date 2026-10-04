#!/usr/bin/env python3
"""Gera docs/predicao_senado.html a partir do JSON do motor e do template.

    python3 scripts/senado-2026-build.py
    python3 scripts/senado-2026-build.py --input tests/fixtures/predicao_senado_exemplo.json --output /tmp/p.html

O build não recalcula nada: lê `docs/assets/predicao_senado.json`, escrito pelo
motor, e falha com mensagem clara se o arquivo faltar.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from predicao_2026.base import module
from senado_2026.pagina import alertas, hemiciclo, texto, view

ROOT = Path(__file__).resolve().parents[1]
JSON_PADRAO = ROOT / "docs/assets/predicao_senado.json"
TEMPLATE = ROOT / "docs/predicao_senado.template.html"
PAGINA = ROOT / "docs/predicao_senado.html"


def carregar(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(
            f"Falta {path}. O motor (scripts/senado_2026/motor.py) escreve esse JSON; "
            "para desenvolver a página use --input tests/fixtures/predicao_senado_exemplo.json."
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    for chave in ("estados", "senado_2027"):
        if chave not in data:
            raise SystemExit(f"{path} sem a chave obrigatória '{chave}'.")
    return data


def render(data: dict, template: str) -> str:
    campo_do_partido = module("voto_util_base").PARTIDO_CAMPO
    trocas = {
        "AVISO": alertas.aviso(data),
        "HERO": view.hero_cartoes(data),
        "HEMICICLO": hemiciclo.render(data, campo_do_partido),
        "PROBABILIDADES": texto.probabilidades_bloco(data),
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
    # Carimbo de versão nos assets próprios: o GitHub Pages e o navegador guardam
    # JS e CSS em cache, e sem isso uma correção de interação demora a chegar.
    for nome in ("predicao_senado.js", "predicao_senado.css"):
        arquivo = ROOT / "docs/assets" / nome
        if arquivo.exists():
            versao = hashlib.sha256(arquivo.read_bytes()).hexdigest()[:10]
            template = template.replace(
                f"assets/{nome}\"", f"assets/{nome}?v={versao}\""
            )
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
