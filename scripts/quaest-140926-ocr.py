#!/usr/bin/env python3
"""OCR index of both reports. Machine readings are evidence locators, not validated tables."""

import csv
import io
import json
import os
import subprocess
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]


def page_ocr(task):
    folder, number = task
    folder = Path(folder)
    out = folder / "ocr" / f"p{number:03}.json"
    if out.exists():
        return number
    with fitz.open(folder / "relatorio.pdf") as doc:
        p = doc[number - 1]
        native = p.get_text()
        pix = p.get_pixmap(matrix=fitz.Matrix(2, 2))
        png = folder / "ocr" / f"p{number:03}.png"
        pix.save(png)
    env = os.environ.copy()
    env["OMP_THREAD_LIMIT"] = "1"
    result = subprocess.run(
        ["tesseract", str(png), "stdout", "-l", "por", "--psm", "11", "tsv"],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    words = [
        {
            k: (
                int(v)
                if k in ["left", "top", "width", "height"]
                else float(v) if k == "conf" else v
            )
            for k, v in r.items()
            if k in ["text", "left", "top", "width", "height", "conf"]
        }
        for r in csv.DictReader(io.StringIO(result.stdout), delimiter="\t")
        if r.get("text", "").strip()
    ]
    out.write_text(
        json.dumps(
            {
                "page": number,
                "native": native,
                "width": pix.width,
                "height": pix.height,
                "words": words,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    png.unlink()
    return number


def main():
    for date in ["2026-09-14", "2026-09-07"]:
        folder = ROOT / "data/pesquisas/quaest" / date
        (folder / "ocr").mkdir(exist_ok=True)
        with fitz.open(folder / "relatorio.pdf") as pdf:
            n = len(pdf)
        with ProcessPoolExecutor(max_workers=4) as pool:
            for i, _ in enumerate(
                pool.map(page_ocr, [(str(folder), n) for n in range(1, n + 1)]), 1
            ):
                if i % 25 == 0:
                    print(date, i, flush=True)
        pages = []
        for i in range(1, n + 1):
            d = json.loads((folder / "ocr" / f"p{i:03}.json").read_text())
            lines = {}
            for w in d["words"]:
                lines.setdefault(round(w["top"] / 15) * 15, []).append(w)
            txt = "\n".join(
                " ".join(w["text"] for w in sorted(ws, key=lambda w: w["left"]))
                for y, ws in sorted(lines.items())
            )
            pages.append(f"\nPÁGINA {i} | OCR NÃO VALIDADO\n{txt}")
        (folder / "ocr-paginas.txt").write_text("\n".join(pages))
        print(date, "completed", n, flush=True)


if __name__ == "__main__":
    main()
