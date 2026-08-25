#!/usr/bin/env python3
"""Prints das tabelas originais do Datafolha BR-04496/2026.

Recorta paginas e regioes dos PDFs oficiais registrados no PesqEle para citacao
documental no dossie. Cada arquivo carrega o numero da pagina no nome, e o
dossie credita instituto, projeto e pagina ao lado de cada imagem.

Uso:
  python3 scripts/datafolha-082026-prints.py

Saida:
  docs/img/datafolha_082026/rel_pNN_*.png
"""

from __future__ import annotations

from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "originals" / "datafolha_082026"
IMG = ROOT / "docs" / "img" / "datafolha_082026"
IMG.mkdir(parents=True, exist_ok=True)

DPI = 150

# (arquivo, pagina, recorte em pontos ou None, nome de saida)
SHOTS = [
    ("DatafolhaRelatorio082026.pdf", 12, None, "rel_p12_decisao.png"),
    ("DatafolhaRelatorio082026.pdf", 13, None, "rel_p13_motivacao.png"),
    ("DatafolhaRelatorio082026.pdf", 14, None, "rel_p14_rejeicao.png"),
    ("DatafolhaRelatorio082026.pdf", 3, None, "rel_p03_margens.png"),
    ("DatafolhaRelatorio082026.pdf", 27, (30, 62, 566, 470), "rel_p27_perfil.png"),
    (
        "DatafolhaRelatorio082026.pdf",
        44,
        (26, 383, 816, 514),
        "rel_p44_turno2_bloco3.png",
    ),
    (
        "DatafolhaRelatorio082026.pdf",
        48,
        (26, 333, 816, 451),
        "rel_p48_definicao_bloco3.png",
    ),
    (
        "DatafolhaQuestionario082026.pdf",
        3,
        (30, 90, 566, 300),
        "quest_p03_nao_publicadas.png",
    ),
    (
        "DatafolhaQuestionario082026.pdf",
        3,
        (30, 292, 566, 500),
        "quest_p03_escalas.png",
    ),
    ("DatafolhaQuestionario082026.pdf", 5, (30, 604, 566, 786), "quest_p05_renda.png"),
    ("DatafolhaRegistroTSE082026.pdf", 2, (28, 55, 580, 260), "tse_p02_plano.png"),
]


def main() -> None:
    for filename, page_number, clip, output in SHOTS:
        document = fitz.open(SOURCE / filename)
        page = document[page_number - 1]
        rect = fitz.Rect(*clip) if clip else None
        pixmap = page.get_pixmap(dpi=DPI, clip=rect)
        pixmap.save(IMG / output)
        print(
            f"  {output}  ({pixmap.width}x{pixmap.height})  {filename} p.{page_number}"
        )
        document.close()


if __name__ == "__main__":
    main()
