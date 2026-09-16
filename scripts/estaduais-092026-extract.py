#!/usr/bin/env python3
"""Extrai as tabelas dos relatorios estaduais Quaest de agosto e setembro de 2026.

Os PDFs sao imagem: o texto nativo traz apenas titulo e enunciado, e todo numero
esta rasterizado. O extrator faz duas passagens de OCR na mesma pagina, uma livre
para os rotulos e outra restrita a digitos para os valores, casa as duas por
coordenada vertical e so aceita a leitura quando a soma da tabela fecha em 100.

Pagina que nao fecha entra em `pendencias.json` e vai para transcricao manual
declarada em `analysis/estaduais_092026/manual.json`, com a pagina de origem ao
lado, exatamente como manda o metodo da casa para relatorio em imagem.

Reproducao:
    python3 scripts/estaduais-092026-extract.py
    python3 scripts/estaduais-092026-extract.py --uf BA --page 75 --show
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import subprocess
import unicodedata
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data/originals/estaduais_092026"
OCR = SRC / "ocr"
OUT = ROOT / "analysis/estaduais_092026"
ZOOM = 4.0

# Arquivo recebido do site do instituto -> UF, onda e data de fim de campo.
REPORTS = {
    "QUAEST1AC2708.pdf": ("AC", 1, "2026-08-27"),
    "QUAEST1AL2408.pdf": ("AL", 1, "2026-08-24"),
    "QUAEST1AM2508.pdf": ("AM", 1, "2026-08-25"),
    "QUAEST1AP2508.pdf": ("AP", 1, "2026-08-25"),
    "QUAEST1BA2708.pdf": ("BA", 1, "2026-08-27"),
    "QUAEST1CE0409.pdf": ("CE", 1, "2026-09-04"),
    "QUAEST1MA2408.pdf": ("MA", 1, "2026-08-24"),
    "QUAEST1PAR012908.pdf": ("PA", 1, "2026-08-29"),
    "QUAEST1PB2508.pdf": ("PB", 1, "2026-08-25"),
    "QUAEST1PE2508.pdf": ("PE", 1, "2026-08-25"),
    "QUAEST1RN2408.pdf": ("RN", 1, "2026-08-24"),
    "QUAEST1RO2508.pdf": ("RO", 1, "2026-08-25"),
    "QUAEST1RR2708.pdf": ("RR", 1, "2026-08-27"),
    "QUAEST1TO2508.pdf": ("TO", 1, "2026-08-25"),
    "QUAEST2PE0809.pdf": ("PE", 2, "2026-09-08"),
    "QUAEST2SP0809.pdf": ("SP", 2, "2026-09-08"),
    "QUAEST2RJ0809.pdf": ("RJ", 2, "2026-09-08"),
    "QUAEST2MG0809.pdf": ("MG", 2, "2026-09-08"),
    "QUAEST2DF0809.pdf": ("DF", 2, "2026-09-08"),
}

# Chave interna -> padrao do titulo nativo. O `(?! ?\|)` exclui os recortes.
PATTERNS = {
    "pres_1t": r"^Inten..o de voto estimulada para presidente \(1. turno\)(?:.*Cen.rio I)?(?! ?\|)(?!I)",
    "pres_1t_renda": r"presidente \(1. turno\).*\| Renda",
    "pres_1t_escala": r"presidente \(1. turno\).*\| Identifica..o pol.tica",
    "pres_1t_religiao": r"presidente \(1. turno\).*\| Religi..o",
    "pres_2t": r"^Inten..o de voto para presidente \(2. turno\)(?! ?\|)",
    "gov_1t": r"^Inten..o de voto estimulada para governador(?:.*Cen.rio I)?(?! ?\|)(?!I)",
    "gov_2t": r"^Inten..o de voto para governador \(2. turno\)(?! ?\|)",
    "aliado": r"fosse aliado de Lula",
    "apoio": r"personalidades apoiasse um candidato",
    "lula_aprovacao": r"^Aprova..o do governo Lula(?! ?\|)",
    "lula_avaliacao": r"^Avalia..o do governo Lula(?! ?\|)",
    "problema": r"maior problema do estado",
    "informacao": r"Como voc. se informa sobre pol.tica",
    "escala": r"escala de posi..es pol.ticas",
    "perfil_renda": r"^Soma da renda de todos os moradores",
    "perfil_religiao": r"^Religi..o$",
    "perfil_idade": r"^Idade$",
}

# Tabelas cuja soma fecha em 100. As demais sao multiplas ou liquidas.
CLOSED = {
    "pres_1t",
    "pres_2t",
    "gov_1t",
    "gov_2t",
    "aliado",
    "lula_aprovacao",
    "lula_avaliacao",
    "problema",
    "informacao",
    "escala",
    "perfil_renda",
    "perfil_religiao",
    "perfil_idade",
}


def strip_accents(value: str) -> str:
    return "".join(
        c
        for c in unicodedata.normalize("NFD", value)
        if unicodedata.category(c) != "Mn"
    )


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def tesseract(png: Path, digits: bool) -> list[dict]:
    env = os.environ.copy()
    env["OMP_THREAD_LIMIT"] = "1"
    cmd = ["tesseract", str(png), "stdout", "-l", "por", "--psm", "6", "tsv"]
    if digits:
        cmd = [*cmd[:-1], "-c", "tessedit_char_whitelist=0123456789", "tsv"]
    result = subprocess.run(cmd, env=env, capture_output=True, check=True)
    text = result.stdout.decode("utf-8", "replace")
    words = []
    for row in csv.DictReader(
        io.StringIO(text), delimiter="\t", quoting=csv.QUOTE_NONE
    ):
        raw = (row.get("text") or "").strip()
        if not raw:
            continue
        try:
            words.append(
                {
                    "text": raw,
                    "left": int(row["left"]),
                    "top": int(row["top"]),
                    "width": int(row["width"]),
                    "height": int(row["height"]),
                    "conf": float(row["conf"]),
                    "line": (
                        int(row["block_num"]),
                        int(row["par_num"]),
                        int(row["line_num"]),
                    ),
                }
            )
        except (KeyError, ValueError):
            continue
    return words


def render(pdf: Path, page: int) -> Path:
    png = OCR / f"{pdf.stem}_p{page:03d}.png"
    if not png.exists():
        with fitz.open(pdf) as doc:
            doc[page - 1].get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM)).save(png)
    return png


def read_page(pdf: Path, page: int) -> dict:
    cache = OCR / f"{pdf.stem}_p{page:03d}.json"
    if cache.exists():
        return json.loads(cache.read_text())
    png = render(pdf, page)
    with fitz.open(pdf) as doc:
        native = " ".join(str(doc[page - 1].get_text()).split())
    payload = {
        "page": page,
        "native": native,
        "words": tesseract(png, digits=False),
        "digits": tesseract(png, digits=True),
    }
    cache.write_text(json.dumps(payload, ensure_ascii=False))
    return payload


def value_column(digits: list[dict]) -> list[dict]:
    """Isola a coluna de valores.

    O tesseract funde o numero com a barra ao lado, entao a largura da caixa nao
    serve de ancora e o alinhamento util e a borda esquerda. Os numeros de uma
    mesma coluna caem numa faixa de poucos pixels; ruido de eixo e de logotipo
    cai longe. Agrupamos por intervalo e ficamos com o maior grupo.
    """
    if not digits:
        return []
    ordered = sorted(digits, key=lambda d: d["left"])
    groups, current = [], [ordered[0]]
    for digit in ordered[1:]:
        if digit["left"] - current[-1]["left"] <= 40:
            current.append(digit)
        else:
            groups.append(current)
            current = [digit]
    groups.append(current)
    picked = max(groups, key=len)
    picked.sort(key=lambda d: d["top"])
    return picked


def parse_rows(payload: dict) -> list[dict]:
    """Casa rotulo e valor por faixa vertical, dentro da coluna de valores.

    O tesseract costuma ler o numero na mesma linha do rotulo, como em
    "Lula (PT) 25 o". Esse numero e mais confiavel que o da coluna isolada, que
    as vezes captura ruido do eixo ou da barra, entao ele tem precedencia.
    """
    lines: dict[str, list[dict]] = {}
    for word in payload["words"]:
        lines.setdefault("-".join(str(x) for x in word["line"]), []).append(word)
    labels = []
    for words in lines.values():
        words.sort(key=lambda w: w["left"])
        top = min(w["top"] for w in words)
        bottom = max(w["top"] + w["height"] for w in words)
        label = " ".join(w["text"] for w in words)
        label = re.sub(r"[|_\u2014\u2013=~]+", " ", label)
        label = re.sub(r"\s+", " ", label).strip(" .:-")
        if not re.search(r"[A-Za-zÀ-ÿ]{3}", label):
            continue
        proprio = None
        for token in reversed(label.split()):
            if token.isdigit() and len(token) <= 3:
                proprio = int(token)
                break
        limpo = re.sub(r"\s*\d{1,3}\s*[A-Za-z]{0,3}\s*$", "", label).strip(" .:-")
        if not re.search(r"[A-Za-zÀ-ÿ]{3}", limpo):
            limpo = label
        labels.append(
            {"label": limpo, "top": top, "bottom": bottom, "proprio": proprio}
        )
    rows = []
    for digit in value_column(payload["digits"]):
        centre = digit["top"] + digit["height"] / 2
        hits = [
            lab
            for lab in labels
            if lab["top"] - digit["height"] * 0.7
            <= centre
            <= lab["bottom"] + digit["height"] * 0.7
        ]
        if not hits:
            continue
        hits.sort(key=lambda lab: abs((lab["top"] + lab["bottom"]) / 2 - centre))
        escolhido = hits[0]
        valor = escolhido["proprio"]
        if valor is None:
            valor = int(digit["text"])
        rows.append({"label": escolhido["label"], "value": valor, "top": digit["top"]})
    rows.sort(key=lambda r: r["top"])
    return [{"label": r["label"], "value": r["value"]} for r in rows]


def clean_table(rows: list[dict], key: str) -> list[dict]:
    drop = ("globo", "quaest", "data you", "se a elei", "fonte", "base")
    out = []
    for row in rows:
        low = strip_accents(row["label"]).lower()
        if any(d in low for d in drop) or len(low) < 2:
            continue
        out.append(row)
    if key.startswith(("pres_1t", "gov_1t")):
        # O titulo sobe como primeira linha quando o OCR o funde com a tabela.
        out = [
            r
            for r in out
            if "intencao de voto" not in strip_accents(r["label"]).lower()
        ]
    return out


def locate(pdf: Path) -> dict[str, int]:
    found: dict[str, int] = {}
    with fitz.open(pdf) as doc:
        for index in range(doc.page_count):
            title = " ".join(str(doc[index].get_text()).split())
            if not title:
                continue
            for key, pattern in PATTERNS.items():
                if key in found:
                    continue
                if re.search(pattern, title):
                    found[key] = index + 1
    return found


def extract_report(item: tuple[str, tuple[str, int, str]]) -> dict:
    filename, (uf, wave, field_end) = item
    pdf = SRC / filename
    pages = locate(pdf)
    tables, pending = {}, []
    for key, page in pages.items():
        payload = read_page(pdf, page)
        rows = clean_table(parse_rows(payload), key)
        total = sum(r["value"] for r in rows)
        ok = True
        if key in CLOSED:
            ok = 97 <= total <= 103 and len(rows) >= 2
        if not ok:
            pending.append({"key": key, "page": page, "sum": total, "rows": rows})
            continue
        tables[key] = {"page": page, "rows": rows, "sum": total}
    return {
        "uf": uf,
        "wave": wave,
        "field_end": field_end,
        "file": filename,
        "sha256": sha256(pdf),
        "bytes": pdf.stat().st_size,
        "pages": pages,
        "tables": tables,
        "pending": pending,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--uf")
    parser.add_argument("--page", type=int)
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args()

    OCR.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)

    items = [(f, meta) for f, meta in REPORTS.items() if (SRC / f).exists()]
    if args.uf:
        items = [(f, m) for f, m in items if m[0] == args.uf]
    if args.page and args.uf:
        pdf = SRC / items[0][0]
        payload = read_page(pdf, args.page)
        print(payload["native"][:160])
        for row in clean_table(parse_rows(payload), "livre"):
            print(f"  {row['value']:>4}  {row['label']}")
        return

    with ProcessPoolExecutor(max_workers=max(1, (os.cpu_count() or 4) - 1)) as pool:
        results = list(pool.map(extract_report, items))

    pendencias = []
    for result in results:
        key = f"{result['uf']}_w{result['wave']}"
        (OUT / f"{key}.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=1)
        )
        for item in result["pending"]:
            pendencias.append(
                {
                    "uf": result["uf"],
                    "wave": result["wave"],
                    "file": result["file"],
                    **{k: item[k] for k in ("key", "page", "sum")},
                }
            )
        print(
            f"{result['uf']} w{result['wave']}: {len(result['tables'])} tabelas, "
            f"{len(result['pending'])} pendentes"
        )
    (OUT / "pendencias.json").write_text(
        json.dumps(pendencias, ensure_ascii=False, indent=1)
    )
    print(f"pendencias: {len(pendencias)}")


if __name__ == "__main__":
    main()
