#!/usr/bin/env python3
"""Indexa pistas de presença em todas as fontes locais, sem inferir ausência pelo OCR."""

import hashlib
import json
import re
from pathlib import Path

import pymupdf
from reponderacao_vista.historico_2t import history
from reponderacao_vista.historico_projecao import evidence

ROOT = Path(__file__).resolve().parents[1]
PATTERN = re.compile(
    r"comparecimento|comparecer|certeza de que irei|chance.{0,30}ir votar|costuma.{0,25}votar",
    re.IGNORECASE,
)


def build():
    cache, rows = {}, []
    for poll in history():
        ref = poll["fonte_historico"]
        path = ref.get("pdf") or ref.get("arquivo")
        if path not in cache:
            data = {"arquivo": path, "pistas": [], "paginas_com_pouco_texto": []}
            if path and (ROOT / path).is_file() and path.lower().endswith(".pdf"):
                data["sha256"] = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
                with pymupdf.open(ROOT / path) as document:
                    data["paginas"] = len(document)
                    for number, page in enumerate(document, 1):
                        text = page.get_text()
                        if len(text.strip()) < 140:
                            data["paginas_com_pouco_texto"].append(number)
                        found = PATTERN.search(text)
                        if found:
                            start = max(0, found.start() - 60)
                            data["pistas"].append(
                                {
                                    "pagina": number,
                                    "trecho": text[start : found.end() + 180],
                                }
                            )
            cache[path] = data
        rows.append(
            {
                "id": poll["id"],
                "instituto": poll["instituto"],
                "tratamento": evidence()["ondas"]
                .get(poll["id"], {})
                .get("tipo", "neutro"),
                **cache[path],
            }
        )
    output = ROOT / "analysis/reponderacao/historico_2t/presenca_acervo.json"
    payload = {
        "data": "2026-10-21",
        "limite": "Índice automático de texto, não prova de ausência de perguntas. Páginas gráficas requerem inspeção visual. Só transcrições explicitamente conferidas em presenca.json alteram o cenário. Perguntas sobre presença no 1º turno não são transportadas ao 2º.",
        "ondas": rows,
    }
    output.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n"
    )
    print(f"{len(rows)} versões indexadas; {len(cache)} fontes distintas")


if __name__ == "__main__":
    build()
