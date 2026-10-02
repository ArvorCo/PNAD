#!/usr/bin/env python3
"""Arquiva OCR página a página; a transcrição numérica exige conferência visual."""

import argparse
import hashlib
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    pdf = args.pdf.resolve()
    pdf.relative_to(ROOT)  # Toda saída permanece no workspace canônico.
    folder = pdf.parent / "ocr"
    folder.mkdir(exist_ok=True)
    with fitz.open(pdf) as doc:
        count = len(doc)

    def page(number):
        # Um documento independente por worker evita compartilhar o objeto fitz.
        with fitz.open(pdf) as doc:
            image = doc[number - 1].get_pixmap(matrix=fitz.Matrix(1.6, 1.6))
        result = subprocess.run(
            ["tesseract", "stdin", "stdout", "-l", "por", "--psm", "11"],
            input=image.tobytes("png"),
            capture_output=True,
            check=True,
        ).stdout.decode("utf-8")
        (folder / f"p{number:03}.txt").write_text(result)
        return f"PÁGINA {number}\n{result}"

    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        pages = list(pool.map(page, range(1, count + 1)))
    (pdf.parent / "ocr-paginas.txt").write_text("\f".join(pages) + "\f")
    metadata = {
        "pdf": str(pdf.relative_to(ROOT)),
        "paginas": count,
        "sha256": hashlib.sha256(pdf.read_bytes()).hexdigest(),
        "metodo": "Tesseract por, PSM 11, PyMuPDF escala 1.6, todas as páginas",
        "limite": "OCR é localizador, não prova numérica. Validar tabelas visualmente e recompor.",
    }
    (pdf.parent / "ocr-metadados.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n"
    )
    print(f"OCR arquivado: {count} páginas de {pdf.name}")


if __name__ == "__main__":
    main()
