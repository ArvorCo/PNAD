#!/usr/bin/env python3
"""Extrai últimas colunas Quaest para o acervo da previsão, com conferência visual.

Fontes são a listagem pública de mídias do próprio instituto. Os PDFs novos
ficam em data/originals/predicao_2026_102026. Cada tabela e ficha é renderizada;
OCR ambíguo usa a transcrição visual declarada do mesmo hash de PDF, sem
completar zeros. Documento alterado exige nova conferência antes de extrair.
"""

import csv
import io
import json
import os
import re
import subprocess
import sys
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import fitz
from predicao_2026.tse import ROOT, sha

SOURCE = ROOT / "analysis/predicao_2026/atualizacao_20261003/quaest_fontes.json"
CACHE = ROOT / "data/originals/predicao_2026_102026/ocr"
OUT = ROOT / "analysis/predicao_2026/estaduais"
QA = ROOT / "analysis/predicao_2026/atualizacao_20261003"
VERIFIED = json.loads((QA / "quaest_conferencia.json").read_text())
SECOND = json.loads((QA / "quaest_2t_paginas.json").read_text())
TURNOUT = json.loads((QA / "quaest_lv_paginas.json").read_text())

LABELS = {
    "Flávio": r"flavio.*bolsonaro",
    "Lula": r"lula.*pt",
    "Cury": r"augusto.*cury",
    "Caiado": r"caiado",
    "Renan": r"renan.*santos",
    "Zema": r"zema",
    "Samara": r"samara",
    "Grassi": r"grassi",
    "Edmilson": r"edmilson.*costa",
    "Hertz": r"hertz.*dias",
    "Pimenta": r"costa.*pimenta",
    "Clariana": r"clariana",
    "Avalanche": r"avalanche",
    "Indecisos": r"indecisos",
    "Branco/nulo": r"branco.*nulo",
}


def plain(text):
    return "".join(
        c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
    ).lower()


def ocr(doc, page, *, clip=None, suffix="", psm=6):
    CACHE.mkdir(parents=True, exist_ok=True)
    stem = Path(doc.name).stem + "_" + sha(Path(doc.name))[:12]
    png = CACHE / f"{stem}_p{page}_{suffix}.png"
    saved = png.with_suffix(".tsv")
    if not saved.exists():
        doc[page - 1].get_pixmap(matrix=fitz.Matrix(4, 4), clip=clip).save(png)
        run = subprocess.run(
            ["tesseract", str(png), "stdout", "-l", "por", "--psm", str(psm), "tsv"],
            env={**os.environ, "OMP_THREAD_LIMIT": "1"},
            text=True,
            capture_output=True,
            check=True,
        )
        saved.write_text(run.stdout, encoding="utf-8")
    return [
        r
        for r in csv.DictReader(io.StringIO(saved.read_text()), delimiter="\t")
        if r.get("text", "").strip()
    ]


def lines(words):
    groups = {}
    for w in words:
        key = tuple(w[k] for k in ("block_num", "par_num", "line_num"))
        groups.setdefault(key, []).append(w)
    return list(groups.values())


def integer(token):
    text = token.strip(" .,:;!()[]|+–—-=")
    if text.lower() == "o":
        return 0
    return int(text) if text.isdigit() and int(text) <= 100 else None


def last_column(doc, page):
    words = ocr(doc, page)
    labels = {}
    for row in lines(words):
        label = plain(" ".join(w["text"] for w in row))
        for name, pattern in LABELS.items():
            if re.search(pattern, label):
                labels[name] = (sum(int(w["top"]) for w in row) / len(row), row)
    if set(labels) != set(LABELS):
        raise ValueError(
            f"{Path(doc.name).name} p.{page}: rótulos ausentes {set(LABELS)-set(labels)}"
        )
    # A última coluna é identificada na linha dos candidatos, não por posição
    # fixa: relatórios têm duas, três ou quatro rodadas lado a lado.
    lead = labels["Flávio"][1]
    numbers = [
        int(w["left"]) for w in lead if re.fullmatch(r"\d{1,2}[.,+:-]?", w["text"])
    ]
    if not numbers:
        raise ValueError("Coluna da rodada não identificada")
    anchor = max(numbers)
    r = doc[page - 1].rect
    clip = fitz.Rect((anchor - 12) / 4, r.y0, min(r.x1, (anchor + 53) / 4), r.y1)
    values = ocr(doc, page, clip=clip, suffix=f"ultima_{anchor}", psm=6)
    result = {}
    for name, (top, _) in labels.items():
        choices = [
            w
            for w in values
            if abs(int(w["top"]) - top) < 20 and integer(w["text"]) is not None
        ]
        if len(choices) != 1:
            raise ValueError(
                f"{Path(doc.name).name} p.{page}: {name}, leitura ambígua {choices}"
            )
        result[name] = integer(choices[0]["text"])
    total = sum(result.values())
    if abs(total - 100) > 3:
        raise ValueError(f"Partição p.{page} não fecha: {total}")
    return result


def field_info(doc):
    words = ocr(doc, 2)
    text = " ".join(w["text"] for w in words)
    low = plain(text)
    field = re.search(r"(\d{1,2})\s*a\s*(\d{1,2}) de setembro de 2026", low)
    sample = re.search(r"([\d.]+) entrevistas", low)
    registry = re.search(r"BR[- ](\d{5})\s*/2026", text)
    if not field or not sample or not registry:
        raise ValueError(f"Ficha técnica ilegível: {Path(doc.name).name}: {text}")
    return {
        "campo": f"2026-09-{int(field[1]):02} a 2026-09-{int(field[2]):02}",
        "n": int(sample[1].replace(".", "")),
        "registro_tse": f"BR-{registry[1]}/2026",
        "ficha_ocr": text,
    }


def extract(source):
    if "erro" in source:
        return source
    path = ROOT / source["arquivo"]
    uf = re.search(r"(?:QUAEST\d+|QUAEST\+\d+\+)([A-Z]{2})", path.name)[1]
    pdf_hash = sha(path)
    if pdf_hash != VERIFIED["sha256_pdf"][uf]:
        raise ValueError(f"{uf}: PDF alterado, exige nova conferência visual")
    doc = fitz.open(path)
    candidates = []
    for i, page in enumerate(doc):
        title = plain(" ".join(page.get_text().split()))
        if (
            title.startswith("intencao de voto estimulada para presidente")
            and "comparativo das rodadas" in title
        ):
            candidates.append(i + 1)
    if len(candidates) != 1:
        raise ValueError(
            f"{path.name}: tabela presidencial não identificada {candidates}"
        )
    page = candidates[0]
    verified = dict(zip(VERIFIED["ordem"], VERIFIED["valores"][uf], strict=True))
    try:
        values = last_column(doc, page)
    except ValueError as exc:
        values = verified
        ocr_status = f"Transcrição visual declarada; OCR pendente: {exc}"
    else:
        if values != verified:
            raise ValueError(f"{uf}: OCR diverge da conferência visual")
        ocr_status = "OCR concorda integralmente com a conferência visual"
    ficha = field_info(doc)
    release = source["disponivel_no_site"][:10]
    result = {
        "uf": uf,
        "instituto": "Quaest",
        **ficha,
        "divulgacao": release,
        "divulgacao_tipo": "Limite conservador de disponibilidade: upload no site oficial; não é a data do campo",
        "url_pdf": source["url"],
        "arquivo": str(path.relative_to(ROOT)),
        "sha256_pdf": pdf_hash,
        "pres_1t": {"pagina": page, "valores": values},
        "conferencia": {
            "metodo": ocr_status,
            "arquivo": str((QA / "quaest_conferencia.json").relative_to(ROOT)),
            "sha256": sha(QA / "quaest_conferencia.json"),
        },
        "pres_2t": {
            "pagina": SECOND[uf]["pagina"],
            "cenarios": [SECOND[uf]["valores"]],
        },
        "comparecimento_compacto": TURNOUT[uf],
        "notas": [
            "Última coluna do comparativo; tabela completa, sem completar ausências com zero.",
            "OCR conferido visualmente; arredondamento da soma é normalizado pelo adaptador.",
            "Sem transporte automático de renda estadual ou de sinal de comparecimento de onda anterior; voto × hábito e segundo turno vêm desta mesma onda.",
        ],
    }
    for num in (2, page, page + 1):
        doc[num - 1].get_pixmap(matrix=fitz.Matrix(1.5, 1.5)).save(
            QA / f"quaest_{uf}_p{num}.png"
        )
    dest = OUT / f"quaest_{uf}_{ficha['campo'].split()[-1].replace('-', '')}.json"
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n")
    return {
        "uf": uf,
        "pagina": page,
        "arquivo": str(dest.relative_to(ROOT)),
        "campo": ficha["campo"],
        "n": ficha["n"],
        "soma": sum(values.values()),
        "lula": values["Lula"],
        "flavio": values["Flávio"],
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = json.loads(SOURCE.read_text())
    requested = sys.argv[1:]
    if requested:
        rows = [
            r for r in rows if any(uf in Path(r["arquivo"]).name for uf in requested)
        ]

    def guarded(row):
        try:
            result = extract(row)
        except Exception as exc:
            result = {"fonte": row["url"], "erro": str(exc)}
        print(json.dumps(result, ensure_ascii=False), flush=True)
        return result

    results = list(ThreadPoolExecutor(4).map(guarded, rows))
    (QA / "quaest_extracao.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=1) + "\n"
    )
    if any("erro" in r for r in results):
        raise SystemExit("Há leituras pendentes; não incorporar sem conferir a fonte")


if __name__ == "__main__":
    main()
