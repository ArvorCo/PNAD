"""Extração decimal da 18ª rodada Nexus, com fonte fixa e controles."""

import hashlib
import json
import re
from pathlib import Path

import pymupdf
from dossies_2t_2026.audit import reweight
from dossies_2t_2026.nexus import KEYS, PROFILE, SPECS, TITLES

from .context import SPECIAL

ROOT = Path(__file__).resolve().parents[2]
SLUG = "nexus_btg_18102026"
PDF = ROOT / "data/originals/nexus_102026_19/relatorio.pdf"
SHA256 = "f6ee08157b9906a8abd4fca2a7a418b329e8895043019bc871b81f12b1eabb45"
PAGES = {
    "polarizacao": (13, 14),
    "interesse": (8, 9),
    "presenca": (17, 18),
    "voto": (42, 43),
    "expectativa": (52, 53),
    "potencial_lula": (89, 90),
    "potencial_flavio": (91, 92),
    "avaliacao": (104, 105),
    "aprovacao": (111, 112),
}
CURRENT_PROFILE = {
    **PROFILE,
    "religiao": dict(zip(PROFILE["religiao"], [48, 31, 9, 13], strict=True)),
    "renda": dict(zip(PROFILE["renda"], [21, 16, 40, 23], strict=True)),
    "ocupacao": dict(zip(PROFILE["ocupacao"], [45, 17, 3, 35], strict=True)),
    "municipio": dict(zip(PROFILE["municipio"], [26, 13, 61], strict=True)),
}
EXTRA = {
    "campanha": (
        (63, 64),
        "Interesse pela campanha entre turnos",
        ["Aumentou", "Está o mesmo", "Diminuiu", "NS/NR"],
    ),
    "escala": (
        (78, 79),
        "Aprovação ao fim da escala 6x1",
        ["Aprova", "Desaprova", "NS/NR"],
    ),
}
TOKEN = re.compile(r"(\d+(?:,\d+)?)%")


def matrix(text, count, page):
    rows = []
    for line in text.splitlines():
        matches = list(TOKEN.finditer(line))
        if not matches:
            continue
        label = line[: matches[0].start()].strip()
        if not label or not re.search(r"[a-zA-ZÀ-ÿ]", label):
            continue
        values = [float(m[1].replace(",", ".")) for m in matches]
        if len(values) != count or abs(sum(values) - 100) > 0.4:
            raise ValueError(f"Página {page}: linha incompatível {label}: {values}")
        rows.append({"original_label": label, "values": values})
    return rows


def extract():
    if hashlib.sha256(PDF.read_bytes()).hexdigest() != SHA256:
        raise ValueError("O PDF não corresponde à fonte auditada")
    tables, catalog, controls = {}, [], {}
    specs = {k: (pages, TITLES[k], SPECS[k][2]) for k, pages in PAGES.items()}
    specs.update(EXTRA)
    with pymupdf.open(PDF) as doc:
        for key, (pages, title, options) in specs.items():
            segments = {}
            for page, names in zip(pages, KEYS, strict=True):
                rows = matrix(doc[page - 1].get_text(sort=True), len(options), page)
                if len(rows) != len(names):
                    raise ValueError(
                        f"Página {page}: {len(rows)} linhas, esperadas {len(names)}"
                    )
                for name, row in zip(names, rows, strict=True):
                    record = {
                        "page": page,
                        "original_label": row["original_label"],
                        "responses": dict(zip(options, row["values"], strict=True)),
                        "base_ponderada": None,
                    }
                    if name in segments:
                        assert record["responses"] == segments[name]["responses"]
                    else:
                        segments[name] = record
            tables[key] = {
                "title": title,
                "pages": pages,
                "segments": segments,
                "universe": "Total da amostra; percentuais dentro de cada segmento. Bases dos grupos não publicadas.",
            }
            controls[key] = {}
            for dim, weights in CURRENT_PROFILE.items():
                recomposed = {
                    option: sum(
                        segments[n]["responses"][option] * w for n, w in weights.items()
                    )
                    / sum(weights.values())
                    for option in options
                }
                residual = max(
                    abs(v - segments["total"]["responses"][k])
                    for k, v in recomposed.items()
                )
                if residual > 1.5:
                    raise ValueError(f"Recomposição {key}/{dim}: {residual}")
                controls[key][dim] = {
                    "recomposto": recomposed,
                    "residuo_max_pp": residual,
                }
        for i, page in enumerate(doc):
            text = page.get_text(sort=True)
            question = text.split("Pergunta:", 1)[1] if "Pergunta:" in text else None
            if question:
                question = re.sub(r"<\d+>\s*$", "", question).strip()
            catalog.append(
                {
                    "page": i + 1,
                    "question": re.sub(r"\s+", " ", question) if question else None,
                    "text": text,
                }
            )
    return {
        "slug": SLUG,
        "release": "2026-10-19",
        "field": ["2026-10-16", "2026-10-18"],
        "n": 2002,
        "registry": "BR-04499/2026",
        "source": {
            "sha256": SHA256,
            "pages": 128,
            "url": json.loads((PDF.parent / "fonte.json").read_text())["arquivos"][0][
                "url"
            ],
        },
        "profile": CURRENT_PROFILE,
        "special": SPECIAL,
        "tables": tables,
        "controls": controls,
        "catalog": catalog,
        "reweight": reweight("nexus_2026-10-18"),
        "transfer": {
            "Flávio no 1º turno": [97.8, 1.6, 0.3, 0.3],
            "Lula no 1º turno": [2.1, 97.4, 0.3, 0.1],
            "Outras candidaturas": [50.5, 32.4, 15, 2],
            "Não compareceu no 1º turno": [44.1, 49.3, 4.4, 2.1],
        },
    }
