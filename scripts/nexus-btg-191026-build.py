#!/usr/bin/env python3
"""Gera o dossiê da 18ª rodada Nexus no endereço solicitado pelo fim do campo."""

import json
import shutil

from nexus_191026.extract import PDF, ROOT, SLUG, extract
from nexus_191026.view import render


def main():
    data = extract()
    # Texto integral fica no arquivo-fonte local; o payload público guarda referências.
    data["catalog"] = [
        {"page": row["page"], "has_question": row["question"] is not None}
        for row in data["catalog"]
    ]
    (ROOT / f"docs/assets/{SLUG}_data.json").write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n"
    )
    (ROOT / f"docs/{SLUG}.html").write_text(render(data))
    shutil.copyfile(PDF, ROOT / f"docs/fontes/{SLUG}.pdf")
    shutil.copyfile(
        ROOT / "data/originals/poderdata_102026_19/relatorio.pdf",
        ROOT / "docs/fontes/poderdata_19102026.pdf",
    )
    print(f"Dossiê gerado: docs/{SLUG}.html; 11 perguntas, 128 páginas na fonte")


if __name__ == "__main__":
    main()
