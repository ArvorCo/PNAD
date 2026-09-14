#!/usr/bin/env python3
"""Audit the 14 Sep 2026 Nexus report; preserve measured and modelled layers."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import subprocess
from pathlib import Path

import fitz
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ROUND = ROOT / "data/pesquisas/nexus_btg/rodada14_2026-09-14"
OUT = ROOT / "docs/assets/nexus_btg_140926_data.json"
SOURCE = "fontes/nexus_btg_140926.pdf"
FIRST = [
    "lula",
    "flavio",
    "cury",
    "caiado",
    "renan_santos",
    "zema",
    "outros",
    "branco_nulo",
    "indecisos",
]
SECOND = ["lula", "flavio", "branco_nulo", "indecisos"]
INCOME = ["Até 1 S.M.", "De 1 até 2 S.M.", "De 2 até 5 S.M.", "Mais de 5 S.M."]
# p. 74, visually checked. Missing labels are zero as printed, not structural zeros.
MEASURED = {
    "Cury": [34, 42, 24, 1],
    "Caiado": [30, 53, 16, 1],
    "Renan": [4, 59, 36, 0],
    "Zema": [12, 75, 11, 2],
    "Samara": [76, 13, 11, 0],
}
SOURCES = [
    "Lula",
    "Flávio",
    "Cury",
    "Caiado",
    "Renan",
    "Zema",
    "Samara",
    "B/N",
    "NS/NR",
]
ROWS = np.array([42, 37, 6, 5, 2, 1, 1, 4, 2], dtype=float)
COLS = np.array([47, 46, 6, 1], dtype=float)
# Full retention of both finalist bases is fixed by modelling assumption.
# Only initial nonchoices are adjusted by IPF.
PRIOR = np.array(
    [[15, 15, 67, 3], [20, 20, 20, 40]],
    dtype=float,
)


def engine():
    spec = importlib.util.spec_from_file_location(
        "reweight_engine", ROOT / "scripts/reponderacao-pnad.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def extract():
    pdf = ROUND / "relatorio.pdf"
    subprocess.run(
        ["pdftotext", "-layout", str(pdf), str(ROUND / "relatorio.txt")], check=True
    )
    pages = (ROUND / "relatorio.txt").read_text().split("\f")[:155]
    # Entire annex preserved as text plus all percentage-bearing lines, not just selected claims.
    appendix = [
        {
            "page": i + 1,
            "text": p,
            "percentage_rows": [
                {
                    "label": re.split(r"\d+%", line)[0].strip(),
                    "values": [int(v) for v in re.findall(r"(\d+)%", line)],
                }
                for line in p.splitlines()
                if "%" in line
            ],
        }
        for i, p in enumerate(pages)
    ]
    (ROUND / "paginas.json").write_text(
        json.dumps(appendix, ensure_ascii=False, indent=2) + "\n"
    )
    return pages


def table(pages, page, labels, columns):
    result = []
    for label in labels:
        lines = [
            line
            for line in pages[page - 1].splitlines()
            if label in line and "%" in line
        ]
        if len(lines) != 1:
            raise ValueError(f"Page {page}: ambiguous label {label}: {lines}")
        vals = [int(v) for v in re.findall(r"(\d+)%", lines[0])]
        if len(vals) != columns:
            raise ValueError((page, label, vals))
        result.append(vals)
    return result


def transfer(prior=PRIOR):
    m = np.zeros((9, 4))
    for i, name in enumerate(SOURCES):
        if name in MEASURED:
            v = np.array(MEASURED[name], dtype=float)
            m[i] = ROWS[i] * v / v.sum()
    consolidated = [0, 1]
    m[0, 0], m[1, 1] = ROWS[0], ROWS[1]
    unknown = [7, 8]
    fixed = [2, 3, 4, 5, 6]
    residual = COLS - m[fixed + consolidated].sum(axis=0)
    if np.any(residual < 0):
        raise ValueError(
            "Measured rows and consolidated bases exceed destination margins"
        )
    sub = np.asarray(prior, dtype=float).copy()
    for _iteration in range(20000):
        sub *= (residual / sub.sum(axis=0))[None, :]
        sub *= (ROWS[unknown] / sub.sum(axis=1))[:, None]
        if np.max(np.abs(sub.sum(axis=0) - residual)) < 1e-10:
            break
    else:
        raise ValueError("IPF did not converge")
    m[unknown] = sub
    pool = m[fixed].sum(axis=0)
    return {
        "sources": SOURCES,
        "destinations": ["Lula", "Flávio", "B/N", "NS/NR"],
        "matrix": m.tolist(),
        "row_targets": ROWS.tolist(),
        "column_targets": COLS.tolist(),
        "measured_rows": fixed,
        "estimated_rows": unknown,
        "consolidated_rows": consolidated,
        "retention_assumption": "Lula e Flávio retêm 100% das bases; hipótese do modelo, não medição da Nexus.",
        "published_conditional": MEASURED,
        "prior_unknown": np.asarray(prior).tolist(),
        "iterations": _iteration + 1,
        "pool_points": pool.tolist(),
        "pool_ratio_flavio_lula": float(pool[1] / pool[0]),
        "net_consolidation": {"lula": 5, "flavio": 9, "ratio": 1.8},
        "note": "5 linhas medidas normalizadas para 100; 2 bases fixadas com retenção integral por hipótese; 2 origens estimadas por IPF. Origens com 0% impresso omitidas; Outros=1% representado por Samara=1%. Ganho líquido não mede fidelidade individual.",
    }


def main():
    pages = extract()
    eng = engine()
    poll = json.loads(
        (ROOT / "analysis/reponderacao/pesquisas/nexus_2026-09-07.json").read_text()
    )
    poll.update(
        id="nexus_2026-09-13",
        registro_tse="BR-04076/2026",
        campo={"inicio": "2026-09-11", "fim": "2026-09-13"},
        divulgacao="2026-09-14",
        n=2003,
        dossie="nexus_btg_140926.html",
        notas="14ª rodada. Relatório de 155 páginas.",
    )
    poll["fonte"] = {
        "pdf": str((ROUND / "relatorio.pdf").relative_to(ROOT)),
        "url": "https://brasil.arvor.co/" + SOURCE,
        "paginas": {"perfil_renda": 152, "1t_renda": 34, "2t_renda": 76},
    }
    poll["renda"][
        "nota"
    ] = "Perfil ponderado de renda da p. 152. O relatório declara PNADC anual 2025 visita 1 e TSE junho/2026 como referências (p. 4), sem publicar pesos ou bases brutas. Cortes em salários de 2026, coerentes com os cartões registrados de rodadas anteriores; o questionário registrado desta rodada não foi obtido. Teste em reais nominais depende dessa hipótese de continuidade. Renda familiar declarada não é idêntica à renda domiciliar efetiva da PNAD; pessoas 16+ não são cadastro eleitoral."
    income_profile = []
    for label in INCOME:
        lines = [line for line in pages[151].splitlines() if label in line]
        if len(lines) != 1:
            raise ValueError(f"Income profile label not unique: {label}")
        income_profile.append(int(re.findall(r"(\d+)%", lines[0])[-1]))
    if sum(income_profile) not in (99, 100, 101):
        raise ValueError("Income profile does not sum to 100 within rounding")
    poll["renda"]["amostra_pct"] = income_profile
    for ballot, page, options in [("1t", 34, FIRST), ("2t", 76, SECOND)]:
        poll["publicado"][ballot] = dict(
            zip(options, table(pages, page, ["TOTAL"], len(options))[0], strict=True)
        )
        poll["cruzamentos"][ballot] = {
            "opcoes": options,
            "linhas": table(pages, page, INCOME, len(options)),
            "nota": f"Extração programática da p. {page}, na ordem das faixas da p. 152.",
        }
    path = ROOT / "analysis/reponderacao/pesquisas/nexus_2026-09-13.json"
    path.write_text(json.dumps(poll, ensure_ascii=False, indent=2) + "\n")
    bench, ipca = eng.Benchmark(), eng.load_ipca()
    current = eng.process_poll(poll, bench, ipca)
    history = [
        eng.process_poll(json.loads(p.read_text()), bench, ipca)
        for p in sorted(path.parent.glob("nexus_*.json"))
    ]
    controls = {}
    for ballot, page in [("1t", 33), ("2t", 75)]:
        controls[ballot] = {}
        for label, labels, weights in [
            ("sexo", ["Feminino", "Masculino"], [53, 47]),
            (
                "escolaridade",
                ["Ensino Fundamental", "Ensino Médio", "Ensino Superior"],
                [34, 41, 25],
            ),
        ]:
            values = eng.compose(
                table(pages, page, labels, len(FIRST if ballot == "1t" else SECOND)),
                weights,
            )
            controls[ballot][label] = values
            expected = list(poll["publicado"][ballot].values())
            assert (
                max(abs(a - b) for a, b in zip(values[:2], expected[:2], strict=True))
                < 1.0
            )
    # All two-page profile tables with aligned numeric rows are machine-extracted.
    profile_tables = {}
    for page, cols in [
        (33, 9),
        (34, 9),
        *[(i, 4) for i in range(75, 85)],
        *[(i, 6) for i in range(110, 126)],
        (133, 6),
        (134, 6),
        (139, 3),
        (140, 3),
    ]:
        rows = []
        for line in pages[page - 1].splitlines():
            vals = [int(v) for v in re.findall(r"(\d+)%", line)]
            if len(vals) == cols:
                rows.append(
                    {"label": re.split(r"\d+%", line)[0].strip(), "values": vals}
                )
        profile_tables[str(page)] = rows
    # Fréchet bounds for changeable AND chooses Flávio in runoff, within each origin.
    bounds = []
    for name, share, change in [
        ("Cury", 6, 34),
        ("Caiado", 5, 51),
        ("Renan", 2, 34),
        ("Zema", 1, 70),
    ]:
        f = MEASURED[name][1]
        bounds.append(
            {
                "candidate": name,
                "share": share,
                "can_change": change,
                "runoff_flavio": f,
                "lower_pp": share * max(0, change + f - 100) / 100,
                "upper_pp": share * min(change, f) / 100,
            }
        )
    # Exact perturbation bound for printed income cells, holding public topline and weights fixed.
    src = np.array(current["renda"]["amostra_pct"])
    tgt = np.array(current["renda"]["pnad_pct"][eng.MAIN_SERIES])
    rounding_bound = float(np.abs(tgt - src).sum() / 100)
    pdf = fitz.open(ROUND / "relatorio.pdf")
    meta = {
        "filename_received": "NexusBTG_14092026.pdf",
        "bytes": (ROUND / "relatorio.pdf").stat().st_size,
        "sha256": hashlib.sha256((ROUND / "relatorio.pdf").read_bytes()).hexdigest(),
        "pages": len(pdf),
        "pdf_metadata": pdf.metadata,
        "field_end": "2026-09-13",
        "note": "Metadados editáveis; criação e modificação não provam instante de publicação nem irregularidade.",
    }
    (ROUND / "manifesto.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n"
    )
    transfer_main = transfer()
    alternatives = [
        transfer(np.array([[5, 30, 60, 5], [30, 10, 20, 40]])),
        transfer(np.array([[30, 5, 60, 5], [10, 30, 20, 40]])),
    ]
    data = {
        "source": meta,
        "poll": poll,
        "reweight": current,
        "history": history,
        "independent_controls": controls,
        "profile_tables": profile_tables,
        "transfer": transfer_main,
        "transfer_alternatives": alternatives,
        "useful_vote_bounds": bounds,
        "rounding_gap_bound_pp": rounding_bound,
        "income_latest_ipca_month": max(ipca),
        "published_history_pages": [21, 53],
        "published_history": {
            "dates": [
                "30/03",
                "27/04",
                "25/05",
                "15/06",
                "29/06",
                "13/07",
                "27/07",
                "03/08",
                "10/08",
                "17/08",
                "24/08",
                "31/08",
                "08/09",
                "14/09",
            ],
            "first_lula": [41, 41, 40, 42, 42, 40, 42, 41, 40, 41, 41, 39, 39, 42],
            "first_flavio": [38, 36, 35, 33, 34, 34, 33, 37, 35, 36, 37, 33, 35, 37],
            "second_lula": [46, 46, 47, 49, 47, 47, 47, 46, 47, 47, 46, 46, 45, 47],
            "second_flavio": [46, 45, 43, 43, 44, 44, 43, 45, 44, 44, 45, 45, 46, 46],
        },
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    # The public report is kept beside the public dossier for stable page citations.
    target = ROOT / "docs" / SOURCE
    target.parent.mkdir(exist_ok=True)
    target.write_bytes((ROUND / "relatorio.pdf").read_bytes())
    prints = ROOT / "docs/img/nexus_btg_140926"
    prints.mkdir(exist_ok=True)
    for page in [4, 34, 38, 41, 43, 74, 76, 95, 97, 152]:
        pdf[page - 1].get_pixmap(matrix=fitz.Matrix(1.4, 1.4)).save(
            prints / f"p{page}.png"
        )
    for ballot in ["1t", "2t"]:
        r = current["turnos"][ballot]
        print(ballot, r["recomposto"], r["cenarios"])
    print(
        "PNAD",
        current["renda"]["pnad_pct"],
        "bounds",
        bounds,
        "pool",
        transfer_main["pool_points"],
    )


if __name__ == "__main__":
    main()
