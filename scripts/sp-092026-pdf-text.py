#!/usr/bin/env python3
"""Preserva texto nativo e OCR por página; OCR nunca é dado validado."""

import subprocess
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/pesquisas/estaduais/sp/2026-09"
for name in ["quaest", "parana"]:
    doc = fitz.open(BASE / f"fontes/{name}.pdf")
    with (BASE / f"derivados/{name}-paginas.txt").open("w") as out:
        for i, page in enumerate(doc):
            text = page.get_text()
            if name == "quaest":
                temp = BASE / f"derivados/{name}-ocr-temp.png"
                page.get_pixmap(matrix=fitz.Matrix(2, 2)).save(temp)
                text = subprocess.run(
                    ["tesseract", str(temp), "stdout", "--psm", "6"],
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout
                temp.unlink()
            out.write(
                f"\nPÁGINA {i + 1} | "
                + ("OCR NÃO VALIDADO" if name == "quaest" else "TEXTO NATIVO")
                + "\n"
                + text
            )
    print(name, len(doc), flush=True)
