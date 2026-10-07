#!/usr/bin/env python3
"""Gera docs/senado_2027.html a partir do JSON do motor e do template.

    python3 scripts/senado-2027-build.py
    python3 scripts/senado-2027-build.py --input outro.json --output /tmp/s.html

O build não recalcula nada: lê `docs/assets/senado_2027.json`, escrito por
`python3 scripts/senado-2027-motor.py`, e falha com mensagem clara se faltar.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from ga_tag import injetar
from senado_2027.pagina import figuras, texto, view

ROOT = Path(__file__).resolve().parents[1]
JSON_PADRAO = ROOT / "docs/assets/senado_2027.json"
TEMPLATE = ROOT / "docs/senado_2027.template.html"
PAGINA = ROOT / "docs/senado_2027.html"
ASSETS = ("senado_2027.css",)
CHAVES = ("elenco", "simulacao", "ranking", "agregados", "teste_pec8", "contexto")


def carregar(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(
            f"Falta {path}. O motor (scripts/senado-2027-motor.py) escreve esse JSON."
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    for chave in CHAVES:
        if chave not in data:
            raise SystemExit(f"{path} sem a chave obrigatória '{chave}'.")
    return data


def blocos(data: dict) -> dict[str, str]:
    """Os 18 placeholders de bloco."""
    return {
        "HERO": view.hero(data),
        "AVISO": view.aviso(data),
        "ORIGEM": view.origem(data),
        "REGUA": view.regua(data),
        "MAPA_81": figuras.dispersao_k_c(data)
        + figuras.curva_k(data)
        + figuras.dispersao_relatorios(data),
        "HEMICICLO": figuras.hemiciclo_c(data, alvo="C_imp")
        + figuras.hemiciclo_c(data, alvo="C_pec"),
        "RANKING": view.ranking(data),
        "TIPOS": view.tipos_frase(data) + figuras.tipos_de_caso(data),
        "CONTA": figuras.placar_cenarios(data)
        + figuras.distribuicao_votos(data, "flavio")
        + figuras.distribuicao_votos(data, "lula")
        + view.conta(data),
        "PIVOS": figuras.pivos(data) + view.pivos_frase(data),
        "TESTE_PEC8": figuras.teste_pec8(data) + view.teste_pec8(data),
        "RECOMENDACOES": view.recomendacoes(data),
        "FICHAS": view.fichas(data),
        "ANEXO": view.anexo(data),
        "ARBITRAGEM": view.arbitragem(data),
        "LIMITES": view.limites(data),
        "FONTES": view.fontes(data),
        "COMO_LEMOS": view.como_lemos(data),
    }


def render(data: dict, template: str) -> str:
    trocas = {**blocos(data), **texto.values(data)}
    for chave, valor in trocas.items():
        template = template.replace("{{" + chave + "}}", valor)
    # Carimbo de versão: o GitHub Pages e o navegador guardam CSS em cache.
    for nome in ASSETS:
        arquivo = ROOT / "docs/assets" / nome
        if arquivo.exists():
            versao = hashlib.sha256(arquivo.read_bytes()).hexdigest()[:10]
            template = template.replace(f'assets/{nome}"', f'assets/{nome}?v={versao}"')
    if "{{" in template:
        raise ValueError("Template incompleto: sobrou placeholder {{...}}")
    if "—" in template:
        raise ValueError("Travessão no texto público")
    return template


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, default=JSON_PADRAO)
    ap.add_argument("--output", type=Path, default=PAGINA)
    args = ap.parse_args()
    data = carregar(args.input)
    html = render(data, TEMPLATE.read_text(encoding="utf-8"))
    args.output.write_text(injetar(html), encoding="utf-8")
    print(f"{args.output} ({len(html) / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
