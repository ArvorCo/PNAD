#!/usr/bin/env python3
"""Reconcile split-column territorial annex against interview and profile totals."""

import csv
import json
import re
from collections import Counter
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "data/pesquisas/datafolha/2026-09-11"


def extract(path):
    rows = []
    with fitz.open(path) as pdf:
        for page in range(4):
            words = pdf[page].get_text("words", sort=True)
            starts = [
                w for w in words if w[0] < 60 and w[4] in {"CO", "N", "NE", "S", "SE"}
            ]
            sectors = [w[4] for w in words if re.fullmatch(r"\d{15}", w[4])]
            counts = [
                int(v)
                for v in pdf[page + 5].get_text().splitlines()
                if v.strip().isdigit()
            ]
            assert len(starts) == len(sectors) == len(counts), (
                page,
                len(starts),
                len(sectors),
                len(counts),
            )
            for i, (start, sector, n) in enumerate(
                zip(starts, sectors, counts, strict=True)
            ):
                end = starts[i + 1][1] - 0.2 if i + 1 < len(starts) else 820
                strip = [w for w in words if start[1] - 0.2 <= w[1] < end]
                uf = [w[4] for w in strip if 90 < w[0] < 130]
                assert len(uf) == 1
                city = " ".join(w[4] for w in strip if 130 <= w[0] < 230)
                bairro = " ".join(w[4] for w in strip if 230 <= w[0] < 450)
                rows.append(
                    {
                        "pagina": page + 1,
                        "pagina_contagem": page + 6,
                        "regiao": start[4],
                        "uf": uf[0],
                        "municipio": city,
                        "codigo_municipio": sector[:7],
                        "bairro": bairro,
                        "setor": sector,
                        "entrevistas": n,
                    }
                )
        text = pdf[4].get_text(sort=True)
        # Counts are read from the annex, in its declared order, not inferred from vote bases.
        counts = [int(v) for v in re.findall(r"\s(\d+)\s*$", text, re.MULTILINE)]
        assert len(counts) == 19, counts
    assert sum(r["entrevistas"] for r in rows) == 2002
    return rows, counts


def main():
    rows, counts = extract(FOLDER / "bairros.pdf")
    municipalities = {r["codigo_municipio"] for r in rows}
    sectors = Counter(r["setor"] for r in rows)
    regions = Counter()
    for r in rows:
        regions[r["regiao"]] += r["entrevistas"]
    profiles = {
        "sexo": counts[:2],
        "idade": counts[2:7],
        "escolaridade": counts[7:10],
        "renda": counts[10:14],
        "regiao": counts[14:],
    }
    assert all(sum(v) == 2002 for v in profiles.values())
    assert [regions[k] for k in ["SE", "S", "NE", "CO", "N"]] == profiles["regiao"]
    comparisons = []
    for slug, path in [
        ("Julho", "data/originals/datafolha_072026/BairrosDatafolha072026.pdf"),
        ("Agosto", "data/originals/datafolha_082026/DatafolhaBairros082026.pdf"),
    ]:
        with fitz.open(ROOT / path) as pdf:
            old = set(re.findall(r"\b\d{15}\b", "\n".join(p.get_text() for p in pdf)))
        assert old
        oldcities = {s[:7] for s in old}
        same = set(sectors) & old
        comparisons.append(
            {
                "onda": slug,
                "fonte": path,
                "setores_anteriores": len(old),
                "setores_repetidos": len(same),
                "setores_novos_pct": 100 * (1 - len(same) / len(sectors)),
                "municipios_repetidos": len(municipalities & oldcities),
                "entrevistas_em_municipios_repetidos": sum(
                    r["entrevistas"] for r in rows if r["codigo_municipio"] in oldcities
                ),
            }
        )
    data = {
        "entrevistas": 2002,
        "municipios": len(municipalities),
        "setores": len(sectors),
        "linhas": len(rows),
        "setores_duplicados": [s for s, n in sectors.items() if n > 1],
        "ufs": sorted({r["uf"] for r in rows}),
        "regioes": dict(regions),
        "perfil_campo": profiles,
        "comparacoes": comparisons,
        "nota": "Colunas de locais nas páginas 1–4; contagens correspondentes nas páginas 6–9. Perfil de campo na página 5. Comparação por geocódigo de 15 dígitos, sem imputação de voto pela geografia.",
    }
    with (FOLDER / "territorio.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    (ROOT / "docs/assets/datafolha_14092026_territorio.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    )
    (ROOT / "docs/assets/datafolha_14092026_territorio.csv").write_bytes(
        (FOLDER / "territorio.csv").read_bytes()
    )
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
